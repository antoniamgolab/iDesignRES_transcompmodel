"""
Calculate distance-based metrics using actual highway kilometers from network data

This approach uses:
- Electricity consumption (MWh) from model results
- Actual highway kilometers from highway_km_per_nuts2.csv

No load assumptions needed!
"""

import pandas as pd
import numpy as np


# NUTS2 to Country mapping (for aggregating highway km by country)
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


def combine_with_highway_km(df_comparison, highway_km_file='highway_km_per_nuts2.csv',
                            cluster_codes=None):
    """
    Combine electrification data with actual highway kilometers

    Parameters:
    -----------
    df_comparison : pd.DataFrame
        Electrification data with columns: case, country, year, electricity
    highway_km_file : str
        Path to highway kilometers CSV
    cluster_codes : list
        List of NUTS2 codes in the cluster

    Returns:
    --------
    pd.DataFrame with highway km and distance-based metrics
    """

    print(f"\n{'='*80}")
    print("COMBINING ELECTRIFICATION WITH ACTUAL HIGHWAY KILOMETERS")
    print('='*80)

    # Load highway kilometers
    print(f"\n1. Loading highway kilometers from {highway_km_file}...")
    highway_df = pd.read_csv(highway_km_file)
    print(f"   Loaded {len(highway_df)} NUTS-2 regions")
    print(f"   Total highway km in dataset: {highway_df['highway_km'].sum():,.1f} km")

    # Filter to cluster if specified
    if cluster_codes:
        highway_cluster = highway_df[highway_df['NUTS2_CODE'].isin(cluster_codes)].copy()
        print(f"\n2. Filtered to {len(highway_cluster)} regions in cluster")
    else:
        highway_cluster = highway_df.copy()

    # Add country column
    highway_cluster['country'] = highway_cluster['NUTS2_CODE'].map(NUTS2_TO_COUNTRY)

    # Remove rows where country mapping failed
    before = len(highway_cluster)
    highway_cluster = highway_cluster[highway_cluster['country'].notna()]
    after = len(highway_cluster)
    if before != after:
        print(f"   Removed {before - after} regions without country mapping")

    # Aggregate highway km by country
    print("\n3. Aggregating highway kilometers by country...")
    highway_by_country = highway_cluster.groupby('country').agg({
        'highway_km': 'sum'
    }).reset_index()

    print("\n   Highway km by country:")
    for _, row in highway_by_country.iterrows():
        print(f"      {row['country']}: {row['highway_km']:,.1f} km")

    # Merge with electrification data
    print("\n4. Merging with electrification data...")
    combined = df_comparison.merge(
        highway_by_country,
        on='country',
        how='left'
    )

    print(f"   Merged shape: {combined.shape}")

    # Calculate distance-based metrics
    print("\n5. Calculating distance-based metrics...")

    # Convert electricity to kWh
    combined['electricity_kWh'] = combined['electricity'] * 1000

    # kWh per km of highway
    combined['kWh_per_km'] = combined['electricity_kWh'] / combined['highway_km']

    # kWh per 60 km
    combined['kWh_per_60km'] = combined['kWh_per_km'] * 60

    # kWh per 100 km (for reference)
    combined['kWh_per_100km'] = combined['kWh_per_km'] * 100

    # Handle any division by zero
    combined['kWh_per_km'] = combined['kWh_per_km'].replace([np.inf, -np.inf], np.nan)
    combined['kWh_per_60km'] = combined['kWh_per_60km'].replace([np.inf, -np.inf], np.nan)
    combined['kWh_per_100km'] = combined['kWh_per_100km'].replace([np.inf, -np.inf], np.nan)

    print(f"   Calculated distance metrics for {len(combined)} records")

    # Display example
    print("\n6. Example calculation:")
    row = combined.iloc[0]
    print(f"   Country: {row['country']}")
    print(f"   Year: {row['year']}")
    print(f"   Case: {row['case']}")
    print(f"   Electricity: {row['electricity']:,.0f} MWh = {row['electricity_kWh']:,.0f} kWh")
    print(f"   Highway km: {row['highway_km']:,.1f} km")
    print(f"   → kWh per km: {row['kWh_per_km']:.2f}")
    print(f"   → kWh per 60 km: {row['kWh_per_60km']:.2f}")
    print(f"   → kWh per 100 km: {row['kWh_per_100km']:.2f}")

    return combined


def display_highway_distance_summary(combined_df):
    """
    Display summary of highway-based distance metrics
    """

    print(f"\n{'='*80}")
    print("HIGHWAY-BASED DISTANCE METRICS SUMMARY")
    print('='*80)

    # Summary by country
    print("\n" + "-"*80)
    print("BY COUNTRY (average across all years and scenarios):")
    print("-"*80)

    summary = combined_df.groupby('country').agg({
        'highway_km': 'first',  # Same for all years
        'electricity_kWh': 'mean',
        'kWh_per_km': 'mean',
        'kWh_per_60km': 'mean',
        'kWh_per_100km': 'mean'
    }).round(2)

    print(summary)

    # By year and case
    print("\n" + "-"*80)
    print("kWh per 60 km BY YEAR AND SCENARIO:")
    print("-"*80)

    pivot = combined_df.pivot_table(
        values='kWh_per_60km',
        index=['country', 'year'],
        columns='case',
        aggfunc='mean'
    ).round(2)

    print(pivot)

    # Interpretation
    print("\n" + "-"*80)
    print("INTERPRETATION:")
    print("-"*80)
    print("""
These metrics show energy consumption normalized by highway infrastructure:

- kWh_per_km: Total electricity (kWh) / Total highway km in region
- kWh_per_60km: Energy consumed per 60 km of highway
- kWh_per_100km: Energy consumed per 100 km of highway

This represents the AVERAGE energy consumption across the entire highway network,
not per-vehicle consumption. It combines:
- Traffic volume (how much freight moves)
- Energy efficiency (how efficient the trucks are)
- Network utilization (how heavily roads are used)

Higher values = more energy consumed per km of highway infrastructure.
""")


# =============================================================================
# NOTEBOOK CELL - Copy this into your notebook
# =============================================================================

"""
# After you have df_comparison from sub_border_regions_cross_case analysis:

from distance_metrics_from_highway_km import combine_with_highway_km, display_highway_distance_summary

# Define cluster codes
CLUSTER_DE_DK_SE = ['DEF0', 'DK01', 'DK02', 'DK03', 'DK04', 'DK05', 'SE22', 'SE23']

# Combine with highway km
combined_with_highways = combine_with_highway_km(
    df_comparison,
    highway_km_file='highway_km_per_nuts2.csv',
    cluster_codes=CLUSTER_DE_DK_SE
)

# Display summary
display_highway_distance_summary(combined_with_highways)

# Show results
display(combined_with_highways[[
    'case', 'country', 'year',
    'electricity', 'highway_km',
    'kWh_per_km', 'kWh_per_60km', 'kWh_per_100km'
]].head(15))

# Visualize kWh per 60 km over time
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(12, 6))

years = sorted(combined_with_highways['year'].unique())
countries = sorted(combined_with_highways['country'].unique())
cases = sorted(combined_with_highways['case'].unique())

# Plot one scenario
baseline_case = cases[0]
baseline_data = combined_with_highways[combined_with_highways['case'] == baseline_case]

for country in countries:
    country_data = baseline_data[baseline_data['country'] == country]
    ax.plot(country_data['year'], country_data['kWh_per_60km'],
           marker='o', label=country, linewidth=2, markersize=8)

ax.set_xlabel('Year', fontsize=12, fontweight='bold')
ax.set_ylabel('kWh per 60 km of highway', fontsize=12, fontweight='bold')
ax.set_title(f'Energy Consumption per 60 km of Highway\\n({baseline_case} scenario)',
            fontsize=13, fontweight='bold')
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('energy_per_60km_highway.png', dpi=300, bbox_inches='tight')
plt.show()
"""


# =============================================================================
# Example: Combine both TKM-based and highway-based metrics
# =============================================================================

"""
# If you want BOTH traffic-based (MWh/TKM) AND highway-based (kWh/60km) metrics:

from combine_electrification_traffic_metrics import combine_electrification_traffic
from distance_metrics_from_highway_km import combine_with_highway_km

# First get TKM-based metrics
combined_with_traffic, _ = combine_electrification_traffic(
    df_comparison,
    cluster_name='Germany-Denmark-Sweden',
    cluster_codes=CLUSTER_DE_DK_SE
)

# Then add highway-based metrics
highway_df = pd.read_csv('highway_km_per_nuts2.csv')
highway_cluster = highway_df[highway_df['NUTS2_CODE'].isin(CLUSTER_DE_DK_SE)].copy()
highway_cluster['country'] = highway_cluster['NUTS2_CODE'].map(NUTS2_TO_COUNTRY)
highway_by_country = highway_cluster.groupby('country')['highway_km'].sum().reset_index()

# Merge
combined_full = combined_with_traffic.merge(highway_by_country, on='country', how='left')

# Calculate both metrics
combined_full['kWh_per_km_highway'] = (combined_full['electricity'] * 1000) / combined_full['highway_km']
combined_full['kWh_per_60km'] = combined_full['kWh_per_km_highway'] * 60

# Now you have BOTH:
# - MWh_per_TKM (freight efficiency)
# - kWh_per_60km (infrastructure utilization)

display(combined_full[[
    'case', 'country', 'year',
    'electricity', 'total_tkm', 'highway_km',
    'MWh_per_TKM', 'kWh_per_60km'
]].head(15))
"""


if __name__ == "__main__":
    print("="*80)
    print("HIGHWAY-BASED DISTANCE METRICS CALCULATOR")
    print("="*80)
    print("\nThis module calculates distance-based metrics using actual highway km.")
    print("\nNo load assumptions needed - uses real road network infrastructure.")
    print("\nImport this in your notebook after creating df_comparison.")
