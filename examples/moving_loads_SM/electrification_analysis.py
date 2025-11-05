"""
Electrification Analysis for TransComp Model Results

This module provides functions to analyze electrification rates by country
from TransComp model output data.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


def calculate_electrification_by_country(input_data, output_data, years_to_plot=None):
    """
    Calculate electrification percentages by country from flow data.

    Parameters:
    -----------
    input_data : dict
        Input data dictionary containing:
        - 'Fuel': list of fuel definitions
        - 'TechVehicle': list of techvehicle definitions
        - 'Technology': list of technology definitions
        - 'GeographicElement': list of nodes and edges with country info
        - 'Odpair': list of origin-destination pairs

    output_data : dict
        Output data dictionary containing:
        - 'f': flow results dict with keys (year, (product, odpair, path), (mode, techvehicle), gen_year)

    years_to_plot : list, optional
        List of years to analyze. Default: [2030, 2050]

    Returns:
    --------
    df_electrification : pd.DataFrame
        DataFrame with columns: country, year, electrification_pct, total_fuel, electricity

    fuel_by_country : dict
        Nested dict structure: {country: {year: {fuel_name: consumption}}}

    skip_counters : dict
        Dictionary with counts of skipped entries by reason
    """

    if years_to_plot is None:
        years_to_plot = [2030, 2050]

    # Structure: {country: {year: {fuel: total_consumption}}}
    fuel_by_country = {}

    # Get fuel types from input data - create BOTH id-based and name-based lookups
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
        'fuel_not_found': 0
    }

    entries_processed = 0

    # Process flow data
    for key, flow_value in output_data['f'].items():
        # Unpack the 4-element key: (year, (product, odpair, path), (mode, techvehicle), generation_year)
        year, p_r_k, mv, generation_year = key

        # Only process years we're interested in
        if year not in years_to_plot:
            skip_counters['wrong_year'] += 1
            continue

        # Extract individual components from tuples
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

        country = origin_node.get("country", "Unknown")
        if country == "Unknown":
            skip_counters['country_unknown'] += 1
            continue

        # Get techvehicle and fuel information using the techvehicle_id
        techvehicle = techvehicle_list.get(techvehicle_id)
        if techvehicle is None:
            skip_counters['techvehicle_not_found'] += 1
            continue

        tech_id = techvehicle["technology"]
        technology = technology_list.get(tech_id)
        if technology is None:
            skip_counters['technology_not_found'] += 1
            continue

        # Handle technology["fuel"] which can be a string name, ID, or dict
        tech_fuel = technology["fuel"]
        fuel = None
        fuel_name = None

        if isinstance(tech_fuel, dict):
            # It's a dict with id and possibly name
            fuel = fuel_list_by_id.get(tech_fuel["id"])
            fuel_name = fuel["name"] if fuel else None
        elif isinstance(tech_fuel, str):
            # It's a string - could be a name like "electricity" or "diesel"
            fuel = fuel_list_by_name.get(tech_fuel)
            fuel_name = tech_fuel
        elif isinstance(tech_fuel, int):
            # It's an ID
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
                    'electricity': electricity
                })

    df_electrification = pd.DataFrame(df_electrification)

    return df_electrification, fuel_by_country, skip_counters


def plot_electrification_scatter(df_electrification, years_to_plot=None, figsize=(14, 6)):
    """
    Create scatter plots showing electrification percentage by country.

    Parameters:
    -----------
    df_electrification : pd.DataFrame
        DataFrame from calculate_electrification_by_country()

    years_to_plot : list, optional
        List of years to plot. Default: [2030, 2050]

    figsize : tuple, optional
        Figure size. Default: (14, 6)

    Returns:
    --------
    fig, axes : matplotlib figure and axes
    """

    if years_to_plot is None:
        years_to_plot = [2030, 2050]

    if len(df_electrification) == 0:
        print("[WARNING] No electrification data to plot!")
        return None, None

    # Create scatter plots
    fig, axes = plt.subplots(1, len(years_to_plot), figsize=figsize)

    # Handle single year case
    if len(years_to_plot) == 1:
        axes = [axes]

    for idx, year in enumerate(years_to_plot):
        ax = axes[idx]

        # Filter data for this year
        year_data = df_electrification[df_electrification['year'] == year].sort_values('country')

        if len(year_data) == 0:
            ax.text(0.5, 0.5, f'No data for {year}',
                    ha='center', va='center', transform=ax.transAxes)
            ax.set_title(f'Year {year}')
            continue

        # Create scatter plot
        x_pos = np.arange(len(year_data))
        ax.scatter(x_pos, year_data['electrification_pct'], alpha=0.6, s=100)

        # Set labels
        ax.set_xticks(x_pos)
        ax.set_xticklabels(year_data['country'], rotation=45, ha='right')
        ax.set_ylabel('Electrification %')
        ax.set_title(f'Battery-Electric Fueling by Country ({year})')
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, 100)

    plt.tight_layout()

    return fig, axes


def print_electrification_summary(df_electrification, years_to_plot=None):
    """
    Print summary statistics for electrification data.

    Parameters:
    -----------
    df_electrification : pd.DataFrame
        DataFrame from calculate_electrification_by_country()

    years_to_plot : list, optional
        List of years to summarize. Default: [2030, 2050]
    """

    if years_to_plot is None:
        years_to_plot = [2030, 2050]

    print("=" * 80)
    print("ELECTRIFICATION SUMMARY")
    print("=" * 80)

    for year in years_to_plot:
        year_data = df_electrification[df_electrification['year'] == year]
        if len(year_data) > 0:
            print(f"\nYear {year}:")
            print(f"  Countries: {len(year_data)}")
            print(f"  Average electrification: {year_data['electrification_pct'].mean():.2f}%")
            min_idx = year_data['electrification_pct'].idxmin()
            max_idx = year_data['electrification_pct'].idxmax()
            print(f"  Min: {year_data['electrification_pct'].min():.2f}% ({year_data.loc[min_idx, 'country']})")
            print(f"  Max: {year_data['electrification_pct'].max():.2f}% ({year_data.loc[max_idx, 'country']})")
        else:
            print(f"\nYear {year}: No data")

    print("=" * 80)


def analyze_electrification(input_data, output_data, years_to_plot=None,
                            show_plot=True, verbose=True):
    """
    Complete electrification analysis workflow.

    This is a convenience function that runs the full analysis and optionally
    displays plots and prints summaries.

    Parameters:
    -----------
    input_data : dict
        Input data dictionary from YAML

    output_data : dict
        Output data dictionary from optimization results

    years_to_plot : list, optional
        Years to analyze. Default: [2030, 2050]

    show_plot : bool, optional
        Whether to display the scatter plot. Default: True

    verbose : bool, optional
        Whether to print detailed summaries. Default: True

    Returns:
    --------
    df_electrification : pd.DataFrame
        Electrification data by country and year
    """

    if years_to_plot is None:
        years_to_plot = [2030, 2050]

    # Calculate electrification
    df_electrification, fuel_by_country, skip_counters = calculate_electrification_by_country(
        input_data, output_data, years_to_plot
    )

    if verbose:
        print(f"\nProcessing Summary:")
        print(f"  Total flow entries: {len(output_data['f'])}")
        print(f"  Entries processed: {sum(fuel_by_country[c][y][f] > 0 for c in fuel_by_country for y in fuel_by_country[c] for f in fuel_by_country[c][y])}")
        print(f"  Skip reasons:")
        for reason, count in skip_counters.items():
            if count > 0:
                print(f"    {reason}: {count}")

        print(f"\nCountries found: {sorted(fuel_by_country.keys())}")

    # Print summary
    if verbose:
        print_electrification_summary(df_electrification, years_to_plot)

    # Plot
    if show_plot:
        fig, axes = plot_electrification_scatter(df_electrification, years_to_plot)
        if fig is not None:
            plt.show()

    return df_electrification


def calculate_electrification_by_nuts2(input_data, output_data, years_to_plot=None):
    """
    Calculate electrification percentages by NUTS2 region from flow data.

    Parameters:
    -----------
    input_data : dict
        Input data dictionary containing:
        - 'Fuel': list of fuel definitions
        - 'TechVehicle': list of techvehicle definitions
        - 'Technology': list of technology definitions
        - 'GeographicElement': list of nodes and edges with NUTS2 region info
        - 'Odpair': list of origin-destination pairs

    output_data : dict
        Output data dictionary containing:
        - 'f': flow results dict with keys (year, (product, odpair, path), (mode, techvehicle), gen_year)

    years_to_plot : list, optional
        List of years to analyze. Default: [2030, 2050]

    Returns:
    --------
    df_electrification : pd.DataFrame
        DataFrame with columns: nuts2_region, country, year, electrification_pct, total_fuel, electricity

    fuel_by_nuts2 : dict
        Nested dict structure: {nuts2_region: {year: {fuel_name: consumption}}}

    skip_counters : dict
        Dictionary with counts of skipped entries by reason
    """

    if years_to_plot is None:
        years_to_plot = [2030, 2050]

    # Structure: {nuts2_region: {year: {fuel: total_consumption}}}
    fuel_by_nuts2 = {}

    # Also track country for each NUTS2 region
    nuts2_to_country = {}

    # Get fuel types from input data - create BOTH id-based and name-based lookups
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
        'nuts2_unknown': 0,
        'techvehicle_not_found': 0,
        'technology_not_found': 0,
        'fuel_not_found': 0
    }

    entries_processed = 0

    # Process flow data
    for key, flow_value in output_data['f'].items():
        # Unpack the 4-element key: (year, (product, odpair, path), (mode, techvehicle), generation_year)
        year, p_r_k, mv, generation_year = key

        # Only process years we're interested in
        if year not in years_to_plot:
            skip_counters['wrong_year'] += 1
            continue

        # Extract individual components from tuples
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

        country = origin_node.get("country", "Unknown")
        if country == "Unknown":
            skip_counters['country_unknown'] += 1
            continue

        # Get NUTS2 region
        nuts2_region = origin_node.get("nuts2_region", "Unknown")
        if nuts2_region == "Unknown":
            skip_counters['nuts2_unknown'] += 1
            continue

        # Store country mapping
        if nuts2_region not in nuts2_to_country:
            nuts2_to_country[nuts2_region] = country

        # Get techvehicle and fuel information using the techvehicle_id
        techvehicle = techvehicle_list.get(techvehicle_id)
        if techvehicle is None:
            skip_counters['techvehicle_not_found'] += 1
            continue

        tech_id = techvehicle["technology"]
        technology = technology_list.get(tech_id)
        if technology is None:
            skip_counters['technology_not_found'] += 1
            continue

        # Handle technology["fuel"] which can be a string name, ID, or dict
        tech_fuel = technology["fuel"]
        fuel = None
        fuel_name = None

        if isinstance(tech_fuel, dict):
            # It's a dict with id and possibly name
            fuel = fuel_list_by_id.get(tech_fuel["id"])
            fuel_name = fuel["name"] if fuel else None
        elif isinstance(tech_fuel, str):
            # It's a string - could be a name like "electricity" or "diesel"
            fuel = fuel_list_by_name.get(tech_fuel)
            fuel_name = tech_fuel
        elif isinstance(tech_fuel, int):
            # It's an ID
            fuel = fuel_list_by_id.get(tech_fuel)
            fuel_name = fuel["name"] if fuel else None

        if fuel is None or fuel_name is None:
            skip_counters['fuel_not_found'] += 1
            continue

        # Aggregate by NUTS2 region, year, and fuel
        if nuts2_region not in fuel_by_nuts2:
            fuel_by_nuts2[nuts2_region] = {}
        if year not in fuel_by_nuts2[nuts2_region]:
            fuel_by_nuts2[nuts2_region][year] = {}
        if fuel_name not in fuel_by_nuts2[nuts2_region][year]:
            fuel_by_nuts2[nuts2_region][year][fuel_name] = 0.0

        fuel_by_nuts2[nuts2_region][year][fuel_name] += flow_value
        entries_processed += 1

    # Calculate electrification percentages
    df_electrification = []
    for nuts2_region, years_data in fuel_by_nuts2.items():
        country = nuts2_to_country.get(nuts2_region, "Unknown")
        for year, fuels_data in years_data.items():
            total_fuel = sum(fuels_data.values())
            electricity = fuels_data.get("electricity", 0.0)
            if total_fuel > 0:
                electrification_pct = (electricity / total_fuel) * 100
                df_electrification.append({
                    'nuts2_region': nuts2_region,
                    'country': country,
                    'year': year,
                    'electrification_pct': electrification_pct,
                    'total_fuel': total_fuel,
                    'electricity': electricity
                })

    df_electrification = pd.DataFrame(df_electrification)

    return df_electrification, fuel_by_nuts2, skip_counters


# Example usage
if __name__ == "__main__":
    """
    Example of how to use this module in your own scripts.
    """

    # Example: Load your data
    # import yaml
    # with open('input.yaml', 'r') as f:
    #     input_data = yaml.safe_load(f)
    #
    # import pickle
    # with open('output.pkl', 'rb') as f:
    #     output_data = pickle.load(f)

    # Run the analysis
    # df = analyze_electrification(input_data, output_data, years_to_plot=[2030, 2050])

    # Or use individual functions for more control:
    # df, fuel_by_country, skip_counters = calculate_electrification_by_country(
    #     input_data, output_data, years_to_plot=[2030, 2050]
    # )
    # fig, axes = plot_electrification_scatter(df, years_to_plot=[2030, 2050])
    # print_electrification_summary(df, years_to_plot=[2030, 2050])

    print("Electrification analysis module loaded.")
    print("Import this module and use analyze_electrification() or individual functions.")
