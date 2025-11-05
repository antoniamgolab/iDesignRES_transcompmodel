"""
Sub-Border Region Analysis

This module defines geographic clusters of border NUTS2 regions and provides
functionality to analyze electrification by sub-border region groups.

Example sub-regions:
- Austria-Germany-Italy cluster: Regions around Austria with adjacent IT and DE regions
- Germany-Denmark-Sweden cluster: All of Denmark with adjacent German and Swedish regions (Öresund connection)
- Denmark-Germany cluster: Partial Denmark regions connecting to Germany
- Norway-Sweden cluster: Regions connecting Norway and Sweden
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Set, Optional
from border_region_electrification_analysis import (
    load_border_region_codes,
    calculate_electrification_by_country_border_only
)


# Define sub-border region clusters
SUB_BORDER_REGIONS = {
    'Austria-Germany-Italy': {
        'description': 'NUTS2 regions around Austria with adjacent German and Italian regions',
        'regions': {
            # Austrian regions
            'AT31', 'AT32', 'AT33', 'AT34',
            # German regions adjacent to Austria
            'DE14', 'DE21', 'DE22', 'DE27',
            # Italian regions adjacent to Austria
            'ITH1', 'ITH3'
        },
        'countries': {'AT', 'DE', 'IT'},
        'color': 'steelblue'
    },
    'Germany-Denmark-Sweden': {
        'description': 'Cross-border cluster including all of Denmark with adjacent German and Swedish regions',
        'regions': {
            # All Danish regions
            'DK01', 'DK02', 'DK03', 'DK04', 'DK05',
            # German region bordering Denmark (Schleswig-Holstein)
            'DEF0',
            # Swedish regions connected to Denmark (Öresund bridge connection)
            'SE22', 'SE23'
        },
        'countries': {'DK', 'DE', 'SE'},
        'color': 'coral'
    },
    'Denmark-Germany': {
        'description': 'NUTS2 regions connecting Denmark and Germany (partial Denmark)',
        'regions': {'DEF0', 'DK03'},
        'countries': {'DK', 'DE'},
        'color': 'lightcoral'
    },
    'Norway-Sweden': {
        'description': 'NUTS2 regions connecting Norway and Sweden',
        'regions': {'NO08', 'SE23'},
        'countries': {'NO', 'SE'},
        'color': 'mediumseagreen'
    }
}


def get_sub_border_region_info() -> pd.DataFrame:
    """
    Get information about defined sub-border regions as a DataFrame.

    Returns:
    --------
    pd.DataFrame with columns: cluster_name, description, num_regions, countries
    """
    data = []
    for cluster_name, cluster_info in SUB_BORDER_REGIONS.items():
        data.append({
            'cluster_name': cluster_name,
            'description': cluster_info['description'],
            'num_regions': len(cluster_info['regions']),
            'countries': ', '.join(sorted(cluster_info['countries'])),
            'regions': ', '.join(sorted(cluster_info['regions']))
        })

    return pd.DataFrame(data)


def calculate_electrification_by_sub_border_region(
    input_data,
    output_data,
    sub_region_name: str,
    years_to_plot=None
):
    """
    Calculate electrification for a specific sub-border region cluster.

    Parameters:
    -----------
    input_data : dict
        Input data dictionary

    output_data : dict
        Output data dictionary

    sub_region_name : str
        Name of sub-border region cluster (e.g., 'Austria-Germany-Italy')

    years_to_plot : list, optional
        Years to analyze. Default: [2030, 2050]

    Returns:
    --------
    df_electrification : pd.DataFrame
        Electrification data with additional 'sub_region' column

    fuel_by_country : dict
        Fuel consumption by country

    skip_counters : dict
        Skip reasons counter
    """
    if sub_region_name not in SUB_BORDER_REGIONS:
        raise ValueError(f"Unknown sub-region: {sub_region_name}. "
                        f"Available: {list(SUB_BORDER_REGIONS.keys())}")

    sub_region_codes = SUB_BORDER_REGIONS[sub_region_name]['regions']

    df_electrification, fuel_by_country, skip_counters = \
        calculate_electrification_by_country_border_only(
            input_data, output_data, sub_region_codes, years_to_plot
        )

    # Add sub-region identifier
    df_electrification['sub_region'] = sub_region_name
    df_electrification['region_type'] = f'border_{sub_region_name}'

    return df_electrification, fuel_by_country, skip_counters


def calculate_electrification_all_sub_regions(
    input_data,
    output_data,
    years_to_plot=None,
    verbose=True
):
    """
    Calculate electrification for all defined sub-border regions.

    Parameters:
    -----------
    input_data : dict
        Input data dictionary

    output_data : dict
        Output data dictionary

    years_to_plot : list, optional
        Years to analyze

    verbose : bool
        Print progress

    Returns:
    --------
    df_all_sub_regions : pd.DataFrame
        Combined electrification data for all sub-regions

    results_by_sub_region : dict
        Dictionary mapping sub-region name to its results
    """
    if years_to_plot is None:
        years_to_plot = [2030, 2050]

    all_dfs = []
    results_by_sub_region = {}

    for sub_region_name in SUB_BORDER_REGIONS.keys():
        if verbose:
            print(f"Processing sub-region: {sub_region_name}...")

        df, fuel_by_country, skip_counters = calculate_electrification_by_sub_border_region(
            input_data, output_data, sub_region_name, years_to_plot
        )

        all_dfs.append(df)
        results_by_sub_region[sub_region_name] = {
            'df': df,
            'fuel_by_country': fuel_by_country,
            'skip_counters': skip_counters
        }

        if verbose:
            print(f"  Found {len(df)} country-year combinations")

    df_all_sub_regions = pd.concat(all_dfs, ignore_index=True)

    return df_all_sub_regions, results_by_sub_region


def plot_sub_region_comparison(
    df_sub_regions,
    years_to_plot=None,
    figsize=(18, 6)
):
    """
    Create comparison plots across sub-border regions.

    Parameters:
    -----------
    df_sub_regions : pd.DataFrame
        Output from calculate_electrification_all_sub_regions()

    years_to_plot : list, optional
        Years to plot

    figsize : tuple
        Figure size

    Returns:
    --------
    fig, axes : matplotlib figure and axes
    """
    if years_to_plot is None:
        years_to_plot = sorted(df_sub_regions['year'].unique())

    fig, axes = plt.subplots(1, len(years_to_plot), figsize=figsize)

    if len(years_to_plot) == 1:
        axes = [axes]

    for idx, year in enumerate(years_to_plot):
        ax = axes[idx]

        # Filter data for this year
        year_data = df_sub_regions[df_sub_regions['year'] == year]

        if len(year_data) == 0:
            ax.text(0.5, 0.5, f'No data for {year}',
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title(f'Year {year}')
            continue

        # Get unique sub-regions and countries
        sub_regions = sorted(year_data['sub_region'].unique())

        # Create grouped data
        for i, sub_region in enumerate(sub_regions):
            sub_data = year_data[year_data['sub_region'] == sub_region]

            # Get color for this sub-region
            color = SUB_BORDER_REGIONS[sub_region].get('color', f'C{i}')

            # Plot each country in this sub-region
            countries = sorted(sub_data['country'].unique())
            x_pos = np.arange(len(countries)) + i * 0.25

            values = [sub_data[sub_data['country'] == c]['electrification_pct'].values[0]
                     if len(sub_data[sub_data['country'] == c]) > 0 else 0
                     for c in countries]

            ax.bar(x_pos, values, width=0.2, label=sub_region,
                  alpha=0.8, color=color)

        # Set labels
        ax.set_xlabel('Country')
        ax.set_ylabel('Electrification %')
        ax.set_title(f'Sub-Border Region Comparison ({year})')

        # Set x-ticks at middle of grouped bars
        all_countries = sorted(year_data['country'].unique())
        n_sub_regions = len(sub_regions)
        x_center = np.arange(len(all_countries)) + (n_sub_regions - 1) * 0.25 / 2
        ax.set_xticks(x_center)
        ax.set_xticklabels(all_countries, rotation=45, ha='right')

        ax.legend(loc='upper left', fontsize=8)
        ax.grid(True, alpha=0.3, axis='y')
        ax.set_ylim(0, 100)

    plt.tight_layout()

    return fig, axes


def plot_single_sub_region_detail(
    df_sub_regions,
    sub_region_name: str,
    years_to_plot=None,
    figsize=(14, 5)
):
    """
    Create detailed plot for a single sub-border region.

    Parameters:
    -----------
    df_sub_regions : pd.DataFrame
        Electrification data

    sub_region_name : str
        Name of sub-region to plot

    years_to_plot : list, optional
        Years to plot

    figsize : tuple
        Figure size

    Returns:
    --------
    fig, axes : matplotlib figure and axes
    """
    if sub_region_name not in SUB_BORDER_REGIONS:
        raise ValueError(f"Unknown sub-region: {sub_region_name}")

    # Filter to this sub-region
    sub_data = df_sub_regions[df_sub_regions['sub_region'] == sub_region_name].copy()

    if len(sub_data) == 0:
        print(f"No data found for sub-region: {sub_region_name}")
        return None, None

    if years_to_plot is None:
        years_to_plot = sorted(sub_data['year'].unique())

    fig, axes = plt.subplots(1, 2, figsize=figsize)

    # Plot 1: Electrification by country and year
    ax1 = axes[0]
    countries = sorted(sub_data['country'].unique())
    x = np.arange(len(countries))
    width = 0.35

    for i, year in enumerate(years_to_plot):
        year_data = sub_data[sub_data['year'] == year]
        values = [year_data[year_data['country'] == c]['electrification_pct'].values[0]
                 if len(year_data[year_data['country'] == c]) > 0 else 0
                 for c in countries]

        offset = width * (i - len(years_to_plot)/2 + 0.5)
        ax1.bar(x + offset, values, width, label=f'{year}', alpha=0.8)

    ax1.set_xlabel('Country')
    ax1.set_ylabel('Electrification %')
    ax1.set_title(f'{sub_region_name}\nElectrification by Country')
    ax1.set_xticks(x)
    ax1.set_xticklabels(countries)
    ax1.legend()
    ax1.grid(True, alpha=0.3, axis='y')
    ax1.set_ylim(0, 100)

    # Plot 2: Total electricity consumption
    ax2 = axes[1]
    for country in countries:
        country_data = sub_data[sub_data['country'] == country]
        if len(country_data) > 0:
            ax2.plot(country_data['year'], country_data['electricity'],
                    marker='o', label=country, linewidth=2)

    ax2.set_xlabel('Year')
    ax2.set_ylabel('Electricity Consumption (MWh)')
    ax2.set_title(f'{sub_region_name}\nElectricity Consumption Over Time')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # Add region info
    region_info = SUB_BORDER_REGIONS[sub_region_name]
    info_text = f"Regions: {', '.join(sorted(region_info['regions']))}"
    fig.text(0.5, 0.02, info_text, ha='center', fontsize=9, style='italic')

    plt.tight_layout()
    plt.subplots_adjust(bottom=0.12)

    return fig, axes


def summarize_sub_region_results(
    df_sub_regions,
    years_to_plot=None,
    verbose=True
):
    """
    Print summary statistics for each sub-border region.

    Parameters:
    -----------
    df_sub_regions : pd.DataFrame
        Combined sub-region electrification data

    years_to_plot : list, optional
        Years to summarize

    verbose : bool
        Print detailed output
    """
    if years_to_plot is None:
        years_to_plot = sorted(df_sub_regions['year'].unique())

    print("\n" + "=" * 80)
    print("SUB-BORDER REGION ELECTRIFICATION SUMMARY")
    print("=" * 80)

    for sub_region_name in sorted(df_sub_regions['sub_region'].unique()):
        sub_data = df_sub_regions[df_sub_regions['sub_region'] == sub_region_name]
        region_info = SUB_BORDER_REGIONS[sub_region_name]

        print(f"\n{sub_region_name}")
        print("-" * 80)
        print(f"Description: {region_info['description']}")
        print(f"NUTS2 Regions: {', '.join(sorted(region_info['regions']))}")
        print(f"Countries: {', '.join(sorted(region_info['countries']))}")

        for year in years_to_plot:
            year_data = sub_data[sub_data['year'] == year]

            if len(year_data) > 0:
                print(f"\n  Year {year}:")
                print(f"    Countries with data: {len(year_data)}")
                print(f"    Average electrification: {year_data['electrification_pct'].mean():.2f}%")
                print(f"    Total electricity: {year_data['electricity'].sum():.2f} MWh")
                print(f"    Total fuel consumption: {year_data['total_fuel'].sum():.2f} MWh")

                if verbose:
                    print(f"    By country:")
                    for _, row in year_data.iterrows():
                        print(f"      {row['country']}: {row['electrification_pct']:.2f}% "
                             f"({row['electricity']:.2f} / {row['total_fuel']:.2f} MWh)")

    print("\n" + "=" * 80)


def analyze_sub_border_regions(
    input_data,
    output_data,
    years_to_plot=None,
    sub_region_name: Optional[str] = None,
    show_plots=True,
    verbose=True
):
    """
    Complete workflow for sub-border region analysis.

    Parameters:
    -----------
    input_data : dict
        Input data dictionary

    output_data : dict
        Output data dictionary

    years_to_plot : list, optional
        Years to analyze. Default: [2030, 2050]

    sub_region_name : str, optional
        Analyze only this specific sub-region. If None, analyze all.

    show_plots : bool
        Whether to display plots

    verbose : bool
        Print summaries

    Returns:
    --------
    df_results : pd.DataFrame
        Combined results for requested sub-regions

    results_by_sub_region : dict (only if sub_region_name is None)
        Detailed results by sub-region
    """
    if years_to_plot is None:
        years_to_plot = [2030, 2050]

    if sub_region_name is not None:
        # Analyze single sub-region
        df_results, fuel_by_country, skip_counters = \
            calculate_electrification_by_sub_border_region(
                input_data, output_data, sub_region_name, years_to_plot
            )

        if verbose:
            print(f"\nAnalyzing sub-region: {sub_region_name}")
            summarize_sub_region_results(df_results, years_to_plot, verbose=True)

        if show_plots:
            fig, axes = plot_single_sub_region_detail(
                df_results, sub_region_name, years_to_plot
            )
            if fig is not None:
                plt.show()

        return df_results

    else:
        # Analyze all sub-regions
        df_results, results_by_sub_region = \
            calculate_electrification_all_sub_regions(
                input_data, output_data, years_to_plot, verbose=verbose
            )

        if verbose:
            summarize_sub_region_results(df_results, years_to_plot, verbose=True)

        if show_plots:
            # Overview comparison
            fig1, axes1 = plot_sub_region_comparison(df_results, years_to_plot)
            plt.show()

            # Detailed plots for each sub-region
            for sub_name in SUB_BORDER_REGIONS.keys():
                fig2, axes2 = plot_single_sub_region_detail(
                    df_results, sub_name, years_to_plot
                )
                if fig2 is not None:
                    plt.show()

        return df_results, results_by_sub_region


# Example usage
if __name__ == "__main__":
    print("Sub-Border Region Analysis Module")
    print("=" * 80)

    # Display defined sub-regions
    df_info = get_sub_border_region_info()
    print("\nDefined Sub-Border Regions:")
    print(df_info.to_string(index=False))

    print("\n" + "=" * 80)
    print("Example usage:")
    print("""
    from sub_border_regions import analyze_sub_border_regions

    # Analyze all sub-border regions
    df_all, results = analyze_sub_border_regions(
        input_data,
        output_data,
        years_to_plot=[2030, 2040, 2050],
        show_plots=True,
        verbose=True
    )

    # Analyze only Austria-Germany-Italy cluster
    df_austria = analyze_sub_border_regions(
        input_data,
        output_data,
        years_to_plot=[2030, 2040, 2050],
        sub_region_name='Austria-Germany-Italy',
        show_plots=True,
        verbose=True
    )

    # Get sub-region information
    from sub_border_regions import get_sub_border_region_info
    df_info = get_sub_border_region_info()
    print(df_info)
    """)
