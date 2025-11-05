"""
Combine electrification data (df_comparison) with traffic metrics to calculate MWh/TKM

This creates a comprehensive table showing:
- Electrification (MWh) by year, country, and scenario
- Traffic metrics (TKM) by country
- Efficiency metric: MWh/TKM

Input:
- df_comparison: From sub_border_regions_cross_case analysis (electrification by year)
- nuts2_traffic_metrics.csv: Traffic metrics per NUTS2 region

Output:
- Combined dataframe with MWh/TKM calculations
"""

import pandas as pd
import numpy as np

# =============================================================================
# CLUSTER DEFINITIONS
# =============================================================================

CLUSTER_DE_DK_SE = ['DEF0', 'DK01', 'DK02', 'DK03', 'DK04', 'DK05', 'SE22', 'SE23']
CLUSTER_AT_DE_IT = ['AT31', 'AT32', 'AT33', 'AT34', 'DE14', 'DE21', 'DE22', 'DE27', 'ITH1', 'ITH3']

# NUTS2 to Country mapping for clusters
NUTS2_TO_COUNTRY = {
    # Germany-Denmark-Sweden
    'DEF0': 'DE',
    'DK01': 'DK', 'DK02': 'DK', 'DK03': 'DK', 'DK04': 'DK', 'DK05': 'DK',
    'SE22': 'SE', 'SE23': 'SE',
    # Austria-Germany-Italy
    'AT31': 'AT', 'AT32': 'AT', 'AT33': 'AT', 'AT34': 'AT',
    'DE14': 'DE', 'DE21': 'DE', 'DE22': 'DE', 'DE27': 'DE',
    'ITH1': 'IT', 'ITH3': 'IT'
}

# =============================================================================
# FUNCTION: Combine electrification with traffic metrics
# =============================================================================

def combine_electrification_traffic(df_comparison, traffic_metrics_file='nuts2_traffic_metrics.csv',
                                    cluster_name='Germany-Denmark-Sweden', cluster_codes=None):
    """
    Combine electrification data with traffic metrics and calculate MWh/TKM

    Parameters:
    -----------
    df_comparison : pd.DataFrame
        Electrification data with columns: case, country, year, electricity, etc.
    traffic_metrics_file : str
        Path to traffic metrics CSV
    cluster_name : str
        Name of cluster for labeling
    cluster_codes : list
        List of NUTS2 codes in the cluster

    Returns:
    --------
    pd.DataFrame with combined data and MWh/TKM calculations
    """

    print(f"\n{'='*80}")
    print(f"COMBINING ELECTRIFICATION & TRAFFIC METRICS: {cluster_name}")
    print('='*80)

    # Load traffic metrics
    print(f"\n1. Loading traffic metrics from {traffic_metrics_file}...")
    traffic_df = pd.read_csv(traffic_metrics_file)
    print(f"   Loaded {len(traffic_df)} NUTS-2 regions")

    # Filter to cluster
    if cluster_codes is None:
        cluster_codes = CLUSTER_DE_DK_SE

    traffic_cluster = traffic_df[traffic_df['NUTS2_CODE'].isin(cluster_codes)].copy()
    print(f"   Filtered to {len(traffic_cluster)} regions in cluster")

    # Add country column
    traffic_cluster['country'] = traffic_cluster['NUTS2_CODE'].map(NUTS2_TO_COUNTRY)

    # Aggregate traffic metrics by country
    print("\n2. Aggregating traffic metrics by country...")
    traffic_by_country = traffic_cluster.groupby('country').agg({
        'origin_tonnes': 'sum',
        'destination_tonnes': 'sum',
        'through_tonnes': 'sum',
        'total_tonnes': 'sum',
        'origin_tkm': 'sum',
        'destination_tkm': 'sum',
        'through_tkm': 'sum',
        'total_tkm': 'sum'
    }).reset_index()

    print("   Traffic by country:")
    print(traffic_by_country[['country', 'total_tonnes', 'total_tkm']].to_string(index=False))

    # Check df_comparison structure
    print("\n3. Checking electrification data structure...")
    print(f"   Shape: {df_comparison.shape}")
    print(f"   Columns: {df_comparison.columns.tolist()}")
    print(f"   Countries: {sorted(df_comparison['country'].unique())}")
    print(f"   Years: {sorted(df_comparison['year'].unique())}")
    print(f"   Cases: {sorted(df_comparison['case'].unique())}")

    # Merge electrification with traffic metrics
    print("\n4. Merging electrification data with traffic metrics...")
    combined = df_comparison.merge(
        traffic_by_country,
        on='country',
        how='left'
    )

    print(f"   Merged shape: {combined.shape}")

    # Calculate MWh/TKM metrics
    print("\n5. Calculating MWh/TKM efficiency metrics...")

    # MWh per TKM (electricity consumption efficiency)
    combined['MWh_per_TKM'] = combined['electricity'] / combined['total_tkm']

    # Also calculate per origin and destination TKM separately
    combined['MWh_per_origin_TKM'] = combined['electricity'] / combined['origin_tkm']
    combined['MWh_per_dest_TKM'] = combined['electricity'] / combined['destination_tkm']

    # Handle division by zero or NaN
    combined['MWh_per_TKM'] = combined['MWh_per_TKM'].replace([np.inf, -np.inf], np.nan)
    combined['MWh_per_origin_TKM'] = combined['MWh_per_origin_TKM'].replace([np.inf, -np.inf], np.nan)
    combined['MWh_per_dest_TKM'] = combined['MWh_per_dest_TKM'].replace([np.inf, -np.inf], np.nan)

    # Add cluster name
    combined['cluster'] = cluster_name

    # Sort by case, year, country
    combined = combined.sort_values(['case', 'year', 'country']).reset_index(drop=True)

    print(f"   Calculated MWh/TKM for {len(combined)} records")

    return combined, traffic_by_country


# =============================================================================
# FUNCTION: Display summary statistics
# =============================================================================

def display_summary(combined_df, cluster_name='Germany-Denmark-Sweden'):
    """
    Display summary statistics for combined data
    """

    print("\n" + "="*80)
    print(f"SUMMARY: {cluster_name}")
    print("="*80)

    # Overall statistics
    print("\nOVERALL STATISTICS:")
    print("-"*80)

    summary_stats = combined_df.groupby('country').agg({
        'total_tkm': 'first',  # Same for all years
        'electricity': 'mean',  # Average across years/cases
        'MWh_per_TKM': 'mean'
    }).round(2)

    print(summary_stats)

    # By year and case
    print("\n" + "-"*80)
    print("MWh/TKM BY YEAR AND SCENARIO:")
    print("-"*80)

    pivot_table = combined_df.pivot_table(
        values='MWh_per_TKM',
        index=['country', 'year'],
        columns='case',
        aggfunc='mean'
    ).round(4)

    print(pivot_table)

    # Total electrification by year
    print("\n" + "-"*80)
    print("TOTAL CLUSTER ELECTRIFICATION (MWh) BY YEAR:")
    print("-"*80)

    total_by_year = combined_df.groupby(['case', 'year'])['electricity'].sum().unstack()
    print(total_by_year.round(0))

    # Efficiency improvement over time
    print("\n" + "-"*80)
    print("AVERAGE MWh/TKM BY YEAR (across all countries):")
    print("-"*80)

    efficiency_by_year = combined_df.groupby(['case', 'year'])['MWh_per_TKM'].mean().unstack()
    print(efficiency_by_year.round(4))


# =============================================================================
# FUNCTION: Export results
# =============================================================================

def export_results(combined_df, cluster_name, output_prefix='electrification_traffic_combined'):
    """
    Export combined results to CSV files
    """

    print("\n" + "="*80)
    print("EXPORTING RESULTS")
    print("="*80)

    # Clean cluster name for filename
    cluster_slug = cluster_name.lower().replace('-', '_').replace(' ', '_')

    # 1. Full dataset
    output_full = f"{output_prefix}_{cluster_slug}.csv"
    combined_df.to_csv(output_full, index=False)
    print(f"[OK] Full dataset saved to: {output_full}")

    # 2. Summary table (MWh/TKM by country, year, case)
    output_summary = f"{output_prefix}_{cluster_slug}_summary.csv"
    summary_cols = ['cluster', 'case', 'country', 'year', 'electricity', 'total_tkm', 'MWh_per_TKM']
    combined_df[summary_cols].to_csv(output_summary, index=False)
    print(f"[OK] Summary saved to: {output_summary}")

    # 3. Pivot table (MWh/TKM by year/case)
    output_pivot = f"{output_prefix}_{cluster_slug}_pivot.csv"
    pivot = combined_df.pivot_table(
        values='MWh_per_TKM',
        index=['country', 'year'],
        columns='case',
        aggfunc='mean'
    )
    pivot.to_csv(output_pivot)
    print(f"[OK] Pivot table saved to: {output_pivot}")

    return output_full, output_summary, output_pivot


# =============================================================================
# MAIN EXECUTION (for standalone use)
# =============================================================================

if __name__ == "__main__":
    print("="*80)
    print("ELECTRIFICATION & TRAFFIC METRICS COMBINER")
    print("="*80)
    print("\nThis script is meant to be imported in a notebook.")
    print("Use it after running sub_border_regions_cross_case analysis.")
    print("\nExample usage:")
    print("""
    # In your notebook:
    from combine_electrification_traffic_metrics import *

    # After getting df_comparison from analyze_sub_region_cross_case_preloaded():
    combined_de_dk_se, traffic_summary = combine_electrification_traffic(
        df_comparison,
        cluster_name='Germany-Denmark-Sweden',
        cluster_codes=CLUSTER_DE_DK_SE
    )

    # Display summary
    display_summary(combined_de_dk_se)

    # Export results
    export_results(combined_de_dk_se, 'Germany-Denmark-Sweden')
    """)
