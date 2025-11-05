"""
Border Region Electrification Analysis

This module extends the electrification_analysis to filter results to only
border NUTS2 regions.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Optional, Set


def load_border_region_codes(border_codes_file: str = "border_nuts2_codes.txt") -> Set[str]:
    """
    Load border region codes from file.

    Parameters:
    -----------
    border_codes_file : str
        Path to text file containing border NUTS2 codes (one per line)

    Returns:
    --------
    set of border region codes
    """
    with open(border_codes_file, 'r') as f:
        codes = {line.strip() for line in f if line.strip()}
    return codes


def calculate_electrification_by_country_border_only(
    input_data,
    output_data,
    border_nuts2_codes: Set[str],
    years_to_plot=None
):
    """
    Calculate electrification percentages by country from flow data,
    filtering to only border NUTS2 regions.

    This is a modified version of calculate_electrification_by_country that
    only considers flows originating from border regions.

    Parameters:
    -----------
    input_data : dict
        Input data dictionary containing Fuel, TechVehicle, Technology, GeographicElement, Odpair

    output_data : dict
        Output data dictionary containing 'f' (flow results)

    border_nuts2_codes : set
        Set of NUTS2 region codes to include (border regions)

    years_to_plot : list, optional
        List of years to analyze. Default: [2030, 2050]

    Returns:
    --------
    df_electrification : pd.DataFrame
        DataFrame with columns: country, year, electrification_pct, total_fuel, electricity,
                                with additional 'region_type' column set to 'border'

    fuel_by_country : dict
        Nested dict structure: {country: {year: {fuel_name: consumption}}}

    skip_counters : dict
        Dictionary with counts of skipped entries by reason
    """

    if years_to_plot is None:
        years_to_plot = [2030, 2050]

    # Structure: {country: {year: {fuel: total_consumption}}}
    fuel_by_country = {}

    # Get fuel types from input data
    fuel_list_by_id = {}
    fuel_list_by_name = {}
    for fuel in input_data["Fuel"]:
        fuel_list_by_id[fuel["id"]] = fuel
        fuel_list_by_name[fuel["name"]] = fuel

    techvehicle_list = {}
    for tv in input_data["TechVehicle"]:
        techvehicle_list[tv["id"]] = tv

    technology_list = {}
    for tech in input_data["Technology"]:
        technology_list[tech["id"]] = tech

    # Create geographic element lookup
    geographic_element_list = {}
    for item in input_data.get("GeographicElement", []):
        geographic_element_list[item["id"]] = item

    skip_counters = {
        'wrong_year': 0,
        'odpair_not_found': 0,
        'origin_not_found': 0,
        'origin_not_node_type': 0,
        'country_unknown': 0,
        'techvehicle_not_found': 0,
        'technology_not_found': 0,
        'fuel_not_found': 0,
        'not_border_region': 0  # NEW counter
    }

    entries_processed = 0

    # Process flow data
    for key, flow_value in output_data['f'].items():
        # Unpack the 4-element key
        year, p_r_k, mv, generation_year = key

        # Only process years we're interested in
        if year not in years_to_plot:
            skip_counters['wrong_year'] += 1
            continue

        # Extract individual components
        product_id, odpair_id, path_id = p_r_k
        mode_id, techvehicle_id = mv

        # Get odpair information
        odpair = next((od for od in input_data["Odpair"] if od["id"] == odpair_id), None)
        if odpair is None:
            skip_counters['odpair_not_found'] += 1
            continue

        # Get origin node
        origin_node_id = odpair["from"]
        origin_node = geographic_element_list.get(origin_node_id)
        if origin_node is None:
            skip_counters['origin_not_found'] += 1
            continue

        if origin_node["type"] != "node":
            skip_counters['origin_not_node_type'] += 1
            continue

        # NEW: Filter by NUTS2 region - skip if not in border regions
        origin_nuts2 = origin_node.get("nuts2_region")
        if origin_nuts2 not in border_nuts2_codes:
            skip_counters['not_border_region'] += 1
            continue

        country = origin_node.get("country", "Unknown")
        if country == "Unknown":
            skip_counters['country_unknown'] += 1
            continue

        # Get techvehicle and fuel information
        techvehicle = techvehicle_list.get(techvehicle_id)
        if techvehicle is None:
            skip_counters['techvehicle_not_found'] += 1
            continue

        tech_id = techvehicle["technology"]
        technology = technology_list.get(tech_id)
        if technology is None:
            skip_counters['technology_not_found'] += 1
            continue

        # Handle technology["fuel"]
        tech_fuel = technology["fuel"]
        fuel = None
        fuel_name = None

        if isinstance(tech_fuel, dict):
            fuel = fuel_list_by_id.get(tech_fuel["id"])
            fuel_name = fuel["name"] if fuel else None
        elif isinstance(tech_fuel, str):
            fuel = fuel_list_by_name.get(tech_fuel)
            fuel_name = tech_fuel
        elif isinstance(tech_fuel, int):
            fuel = fuel_list_by_id.get(tech_fuel)
            fuel_name = fuel["name"] if fuel else None

        if fuel is None or fuel_name is None:
            skip_counters['fuel_not_found'] += 1
            continue

        # Aggregate by country, year, and fuel
        if country not in fuel_by_country:
            fuel_by_country[country] = {}
        if year not in fuel_by_country[country]:
            fuel_by_country[country][year] = {}
        if fuel_name not in fuel_by_country[country][year]:
            fuel_by_country[country][year][fuel_name] = 0.0

        fuel_by_country[country][year][fuel_name] += flow_value
        entries_processed += 1

    # Calculate electrification percentages
    df_electrification = []
    for country, years_data in fuel_by_country.items():
        for year, fuels_data in years_data.items():
            total_fuel = sum(fuels_data.values())
            electricity = fuels_data.get("electricity", 0.0)
            if total_fuel > 0:
                electrification_pct = (electricity / total_fuel) * 100
                df_electrification.append({
                    'country': country,
                    'year': year,
                    'electrification_pct': electrification_pct,
                    'total_fuel': total_fuel,
                    'electricity': electricity,
                    'region_type': 'border'  # Mark as border region data
                })

    df_electrification = pd.DataFrame(df_electrification)

    return df_electrification, fuel_by_country, skip_counters


def compare_border_vs_all_electrification(
    input_data,
    output_data,
    border_nuts2_codes: Set[str],
    years_to_plot=None
):
    """
    Compare electrification rates between border regions and all regions.

    Parameters:
    -----------
    input_data : dict
        Input data dictionary

    output_data : dict
        Output data dictionary

    border_nuts2_codes : set
        Set of border NUTS2 region codes

    years_to_plot : list, optional
        Years to analyze

    Returns:
    --------
    df_comparison : pd.DataFrame
        Combined DataFrame with both border and all regions data
    """
    from electrification_analysis import calculate_electrification_by_country

    if years_to_plot is None:
        years_to_plot = [2030, 2050]

    # Calculate for all regions
    df_all, _, skip_all = calculate_electrification_by_country(
        input_data, output_data, years_to_plot
    )
    df_all['region_type'] = 'all'

    # Calculate for border regions only
    df_border, _, skip_border = calculate_electrification_by_country_border_only(
        input_data, output_data, border_nuts2_codes, years_to_plot
    )
    df_border['region_type'] = 'border'

    # Combine
    df_comparison = pd.concat([df_all, df_border], ignore_index=True)

    return df_comparison


def plot_border_vs_all_comparison(df_comparison, years_to_plot=None, figsize=(16, 6)):
    """
    Create comparison plots showing border vs all regions electrification.

    Parameters:
    -----------
    df_comparison : pd.DataFrame
        Output from compare_border_vs_all_electrification()

    years_to_plot : list, optional
        Years to plot

    figsize : tuple
        Figure size

    Returns:
    --------
    fig, axes : matplotlib figure and axes
    """
    if years_to_plot is None:
        years_to_plot = [2030, 2050]

    fig, axes = plt.subplots(1, len(years_to_plot), figsize=figsize)

    if len(years_to_plot) == 1:
        axes = [axes]

    for idx, year in enumerate(years_to_plot):
        ax = axes[idx]

        # Filter data for this year
        year_data = df_comparison[df_comparison['year'] == year]

        if len(year_data) == 0:
            ax.text(0.5, 0.5, f'No data for {year}',
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title(f'Year {year}')
            continue

        # Pivot data for easier plotting
        pivot_data = year_data.pivot_table(
            index='country',
            columns='region_type',
            values='electrification_pct',
            aggfunc='mean'
        )

        # Create grouped bar chart
        x = np.arange(len(pivot_data))
        width = 0.35

        if 'all' in pivot_data.columns:
            ax.bar(x - width/2, pivot_data['all'], width,
                  label='All regions', alpha=0.8, color='steelblue')

        if 'border' in pivot_data.columns:
            ax.bar(x + width/2, pivot_data['border'], width,
                  label='Border regions only', alpha=0.8, color='coral')

        ax.set_xlabel('Country')
        ax.set_ylabel('Electrification %')
        ax.set_title(f'Electrification Comparison ({year})')
        ax.set_xticks(x)
        ax.set_xticklabels(pivot_data.index, rotation=45, ha='right')
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        ax.set_ylim(0, 100)

    plt.tight_layout()

    return fig, axes


def analyze_border_region_electrification(
    input_data,
    output_data,
    border_nuts2_codes: Optional[Set[str]] = None,
    border_codes_file: str = "border_nuts2_codes.txt",
    years_to_plot=None,
    show_plot=True,
    verbose=True
):
    """
    Complete border region electrification analysis workflow.

    Parameters:
    -----------
    input_data : dict
        Input data dictionary

    output_data : dict
        Output data dictionary

    border_nuts2_codes : set, optional
        Set of border region codes. If None, loads from file.

    border_codes_file : str
        Path to border codes file (used if border_nuts2_codes is None)

    years_to_plot : list, optional
        Years to analyze

    show_plot : bool
        Whether to display comparison plots

    verbose : bool
        Whether to print summaries

    Returns:
    --------
    df_comparison : pd.DataFrame
        Combined comparison data
    """
    if years_to_plot is None:
        years_to_plot = [2030, 2050]

    # Load border codes if not provided
    if border_nuts2_codes is None:
        border_nuts2_codes = load_border_region_codes(border_codes_file)
        if verbose:
            print(f"Loaded {len(border_nuts2_codes)} border region codes from {border_codes_file}")

    # Calculate comparison
    df_comparison = compare_border_vs_all_electrification(
        input_data, output_data, border_nuts2_codes, years_to_plot
    )

    if verbose:
        print("\n" + "=" * 80)
        print("BORDER REGION ELECTRIFICATION ANALYSIS")
        print("=" * 80)

        for year in years_to_plot:
            year_data = df_comparison[df_comparison['year'] == year]

            if len(year_data) > 0:
                print(f"\nYear {year}:")

                all_data = year_data[year_data['region_type'] == 'all']
                border_data = year_data[year_data['region_type'] == 'border']

                if len(all_data) > 0:
                    print(f"  All regions:")
                    print(f"    Countries: {len(all_data)}")
                    print(f"    Average electrification: {all_data['electrification_pct'].mean():.2f}%")
                    print(f"    Total electricity: {all_data['electricity'].sum():.2f} MWh")

                if len(border_data) > 0:
                    print(f"  Border regions only:")
                    print(f"    Countries: {len(border_data)}")
                    print(f"    Average electrification: {border_data['electrification_pct'].mean():.2f}%")
                    print(f"    Total electricity: {border_data['electricity'].sum():.2f} MWh")

                    # Show difference
                    if len(all_data) > 0:
                        all_avg = all_data['electrification_pct'].mean()
                        border_avg = border_data['electrification_pct'].mean()
                        diff = border_avg - all_avg
                        print(f"  Difference (border - all): {diff:+.2f} percentage points")

        print("=" * 80)

    # Plot comparison
    if show_plot:
        fig, axes = plot_border_vs_all_comparison(df_comparison, years_to_plot)
        plt.show()

    return df_comparison


# Example usage
if __name__ == "__main__":
    """
    Example showing how to use the border region electrification analysis.
    """
    print("Border region electrification analysis module loaded.")
    print("\nExample usage:")
    print("""
    from border_region_electrification_analysis import analyze_border_region_electrification

    # Load your data
    # input_data, output_data = read_data(...)

    # Analyze border regions
    df_comparison = analyze_border_region_electrification(
        input_data,
        output_data,
        border_codes_file="border_nuts2_codes.txt",
        years_to_plot=[2030, 2040, 2050],
        show_plot=True,
        verbose=True
    )

    # Access border-only data
    df_border_only = df_comparison[df_comparison['region_type'] == 'border']
    """)
