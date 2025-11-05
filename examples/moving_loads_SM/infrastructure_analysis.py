"""
Fueling Infrastructure Analysis for TransComp Model Results

This module provides functions to analyze fueling infrastructure capacity
expansion and utilization from TransComp model output data.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Tuple, Optional


def get_infrastructure_data(input_data, output_data):
    """
    Extract and organize infrastructure data from input and output.

    Parameters:
    -----------
    input_data : dict
        Input data containing InitialFuelInfr, FuelingInfrTypes, Fuel, Model

    output_data : dict
        Output data containing q_fuel_infr_plus (capacity additions) and s (energy consumption)

    Returns:
    --------
    dict with keys:
        - fuel_list: dict mapping fuel_id to fuel data
        - fueling_infr_types_list: dict mapping infr_id to infrastructure type data
        - fueling_type_to_id: dict mapping fueling type string to ID
        - initial_fueling_infr: dict mapping (fuel_name, infr_id, geo_id) to initial capacity
        - investment_years: list of investment years
    """

    # Create fuel lookup
    fuel_list = {d["id"]: d for d in input_data["Fuel"]}

    # Create infrastructure types lookup
    fueling_infr_types_list = {d["id"]: d for d in input_data["FuelingInfrTypes"]}

    # Map fueling_type string to infrastructure type ID
    fueling_type_to_id = {}
    for infr_id, infr_data in fueling_infr_types_list.items():
        fueling_type_str = infr_data["fueling_type"]
        fueling_type_to_id[fueling_type_str] = infr_id

    # Get initial fueling infrastructure
    # Key by (fuel_name, infr_type_id, geo_id) for easy lookup
    initial_fueling_infr = {}
    for d in input_data["InitialFuelInfr"]:
        fuel_name = d["fuel"]
        fueling_type_str = d["type"]
        geo_id = d["allocation"]

        # Map fueling_type string to infrastructure type ID
        infr_type_id = fueling_type_to_id.get(fueling_type_str)
        if infr_type_id is not None:
            key = (fuel_name, infr_type_id, geo_id)
            initial_fueling_infr[key] = d

    # Get investment period and years
    y_init = input_data["Model"]["y_init"]
    Y = input_data["Model"]["Y"]
    time_step = input_data["Model"]["time_step"]
    investment_period = input_data["Model"]["investment_period"]
    Y_end = y_init + (Y - 1) * time_step
    investment_years = list(range(y_init, Y_end + 1, investment_period))

    return {
        'fuel_list': fuel_list,
        'fueling_infr_types_list': fueling_infr_types_list,
        'fueling_type_to_id': fueling_type_to_id,
        'initial_fueling_infr': initial_fueling_infr,
        'investment_years': investment_years,
        'y_init': y_init,
        'Y_end': Y_end
    }


def calculate_capacity_by_year_and_type(input_data, output_data):
    """
    Calculate infrastructure capacity additions by year and infrastructure type.

    Parameters:
    -----------
    input_data : dict
        Input data dictionary

    output_data : dict
        Output data dictionary containing 'q_fuel_infr_plus'

    Returns:
    --------
    capacity_by_type_year : dict
        Nested dict: {(fuel_name, infr_type_str): {year: capacity_kW}}

    infra_data : dict
        Infrastructure metadata from get_infrastructure_data()
    """

    infra_data = get_infrastructure_data(input_data, output_data)
    fuel_list = infra_data['fuel_list']
    fueling_infr_types_list = infra_data['fueling_infr_types_list']

    # Aggregate capacity additions by year and infrastructure type
    capacity_by_type_year = {}

    for key, value in output_data["q_fuel_infr_plus"].items():
        year = key[0]
        f_l = key[1]  # (fuel_id, infr_id)
        fuel_id = f_l[0]
        infr_id = f_l[1]

        # Get fuel name
        fuel_name = fuel_list[fuel_id]["name"]

        # Get infrastructure type
        infr_type_str = fueling_infr_types_list[infr_id]["fueling_type"]

        # Create composite key
        type_key = (fuel_name, infr_type_str)

        if type_key not in capacity_by_type_year:
            capacity_by_type_year[type_key] = {}

        if year not in capacity_by_type_year[type_key]:
            capacity_by_type_year[type_key][year] = 0.0

        capacity_by_type_year[type_key][year] += value

    return capacity_by_type_year, infra_data


def calculate_capacity_by_geographic_element(input_data, output_data, year, fuel_name=None,
                                            include_utilization=True):
    """
    Calculate total infrastructure capacity by geographic element for a specific year.

    Parameters:
    -----------
    input_data : dict
        Input data dictionary

    output_data : dict
        Output data dictionary

    year : int
        Year to calculate capacity for

    fuel_name : str, optional
        Filter by specific fuel (e.g., 'electricity', 'diesel'). If None, include all fuels.

    include_utilization : bool, optional
        Whether to calculate utilization rates. Default: True
        Requires 's' variable in output_data.

    Returns:
    --------
    df_capacity : pd.DataFrame
        DataFrame with columns: geo_id, geo_name, fuel, infrastructure_type,
                                initial_capacity_kW, added_capacity_kW, total_capacity_kW,
                                energy_consumed_kWh (if include_utilization=True),
                                utilization_rate (if include_utilization=True),
                                lat, lon, country
    """

    infra_data = get_infrastructure_data(input_data, output_data)
    fuel_list = infra_data['fuel_list']
    fueling_infr_types_list = infra_data['fueling_infr_types_list']
    initial_fueling_infr = infra_data['initial_fueling_infr']
    investment_years = infra_data['investment_years']

    # Get geographic elements
    geographic_element_list = {d["id"]: d for d in input_data["GeographicElement"]}

    # Extract energy consumption by year, geo_id, fuel_id, infr_id if requested
    energy_by_location = {}
    if include_utilization and 's' in output_data:
        for key, value in output_data['s'].items():
            s_year = key[0]
            # Try to extract geo_id (might be at different positions depending on model version)
            # Common structures: (year, geo_id, ?, (fuel_id, infr_id)) or (year, ?, geo_id, (fuel_id, infr_id))
            if len(key) >= 4:
                f_l = key[3]  # (fuel_id, infr_id)
                fuel_id = f_l[0]
                infr_id = f_l[1]

                # Try to find geo_id - it's typically an integer in position 1 or 2
                geo_id = None
                if isinstance(key[1], int):
                    geo_id = key[1]
                elif len(key) > 2 and isinstance(key[2], int):
                    geo_id = key[2]

                if geo_id is not None:
                    energy_key = (s_year, geo_id, fuel_id, infr_id)
                    if energy_key not in energy_by_location:
                        energy_by_location[energy_key] = 0.0
                    energy_by_location[energy_key] += value

    records = []

    for geo_id, geo_data in geographic_element_list.items():
        for infr_id, infr_data in fueling_infr_types_list.items():
            for fuel_id, fuel_data in fuel_list.items():
                current_fuel_name = fuel_data["name"]

                # Skip if fuel_name filter is specified and doesn't match
                if fuel_name is not None and current_fuel_name != fuel_name:
                    continue

                # Check if this fuel-infrastructure combination is valid
                if infr_data["fuel"] != current_fuel_name:
                    continue

                # Get initial capacity
                initial_key = (current_fuel_name, infr_id, geo_id)
                initial_capacity = 0.0
                if initial_key in initial_fueling_infr:
                    initial_capacity = initial_fueling_infr[initial_key]["installed_kW"]

                # Sum capacity additions up to the specified year
                added_capacity = 0.0
                f_l = (fuel_id, infr_id)
                for inv_year in investment_years:
                    if inv_year <= year:
                        key_q = (inv_year, f_l, geo_id)
                        if key_q in output_data["q_fuel_infr_plus"]:
                            added_capacity += output_data["q_fuel_infr_plus"][key_q]

                total_capacity = initial_capacity + added_capacity

                # Get energy consumption for this year/location/fuel/infr
                energy_consumed = 0.0
                if include_utilization:
                    energy_key = (year, geo_id, fuel_id, infr_id)
                    energy_consumed = energy_by_location.get(energy_key, 0.0)

                # Calculate utilization rate
                # utilization = actual_energy / (capacity * 8760 hours)
                utilization_rate = None
                if include_utilization and total_capacity > 0:
                    max_possible_energy = total_capacity * 8760  # kWh
                    utilization_rate = energy_consumed / max_possible_energy if max_possible_energy > 0 else 0.0

                # Only include if there's some capacity
                if total_capacity > 0:
                    record = {
                        'geo_id': geo_id,
                        'geo_name': geo_data.get('name', 'Unknown'),
                        'fuel': current_fuel_name,
                        'infrastructure_type': infra_data['fueling_infr_types_list'][infr_id]['fueling_type'],
                        'initial_capacity_kW': initial_capacity,
                        'added_capacity_kW': added_capacity,
                        'total_capacity_kW': total_capacity,
                        'lat': geo_data.get('coordinate_lat'),
                        'lon': geo_data.get('coordinate_long'),
                        'country': geo_data.get('country', 'Unknown')
                    }

                    if include_utilization:
                        record['energy_consumed_kWh'] = energy_consumed
                        record['utilization_rate'] = utilization_rate
                        record['utilization_pct'] = utilization_rate * 100 if utilization_rate is not None else None

                    records.append(record)

    df_capacity = pd.DataFrame(records)

    return df_capacity


def calculate_energy_consumption_by_infrastructure(input_data, output_data):
    """
    Calculate energy consumption by infrastructure type from the s variable.

    Parameters:
    -----------
    input_data : dict
        Input data dictionary

    output_data : dict
        Output data dictionary containing 's' (energy supply variable)

    Returns:
    --------
    energy_by_infr : dict
        Dict mapping (fuel_name, infr_type_str) to total energy consumption in kWh
    """

    infra_data = get_infrastructure_data(input_data, output_data)
    fuel_list = infra_data['fuel_list']
    fueling_infr_types_list = infra_data['fueling_infr_types_list']

    energy_by_infr = {}

    # The s variable has keys: (year, ..., ..., (fuel_id, infr_id))
    for key, value in output_data['s'].items():
        # Extract fuel and infrastructure from the last element
        f_l = key[3]  # (fuel_id, infr_id)
        fuel_id = f_l[0]
        infr_id = f_l[1]

        fuel_name = fuel_list[fuel_id]["name"]
        infr_type_str = fueling_infr_types_list[infr_id]["fueling_type"]

        type_key = (fuel_name, infr_type_str)

        if type_key not in energy_by_infr:
            energy_by_infr[type_key] = 0.0

        energy_by_infr[type_key] += value

    return energy_by_infr


def plot_capacity_expansion_by_type(capacity_by_type_year, infra_data, figsize=(14, 8)):
    """
    Create stacked bar chart showing capacity expansion by infrastructure type and year.

    Parameters:
    -----------
    capacity_by_type_year : dict
        From calculate_capacity_by_year_and_type()

    infra_data : dict
        Infrastructure metadata

    figsize : tuple
        Figure size

    Returns:
    --------
    fig, ax : matplotlib figure and axes
    """

    # Prepare data for plotting
    years = sorted(set(year for type_data in capacity_by_type_year.values()
                      for year in type_data.keys()))

    # Create a DataFrame for easier plotting
    plot_data = {}
    for (fuel_name, infr_type_str), year_data in capacity_by_type_year.items():
        label = f"{fuel_name} - {infr_type_str}"
        plot_data[label] = [year_data.get(year, 0) / 1000 for year in years]  # Convert to MW

    df_plot = pd.DataFrame(plot_data, index=years)

    # Create plot
    fig, ax = plt.subplots(figsize=figsize)
    df_plot.plot(kind='bar', stacked=False, ax=ax, width=0.8)

    ax.set_xlabel('Year')
    ax.set_ylabel('Capacity Addition (MW)')
    ax.set_title('Infrastructure Capacity Expansion by Type and Year')
    ax.legend(title='Infrastructure Type', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()

    return fig, ax


def print_infrastructure_summary(capacity_by_type_year, energy_by_infr=None):
    """
    Print summary statistics for infrastructure.

    Parameters:
    -----------
    capacity_by_type_year : dict
        From calculate_capacity_by_year_and_type()

    energy_by_infr : dict, optional
        From calculate_energy_consumption_by_infrastructure()
    """

    print("=" * 80)
    print("INFRASTRUCTURE CAPACITY EXPANSION SUMMARY")
    print("=" * 80)

    for (fuel_name, infr_type_str), year_data in sorted(capacity_by_type_year.items()):
        total_capacity = sum(year_data.values())
        years_with_expansion = sorted(year_data.keys())

        print(f"\n{fuel_name} - {infr_type_str}:")
        print(f"  Total capacity added: {total_capacity / 1000:,.2f} MW ({total_capacity:,.0f} kW)")
        print(f"  Years with expansion: {years_with_expansion}")

    if energy_by_infr:
        print("\n" + "=" * 80)
        print("ENERGY CONSUMPTION BY INFRASTRUCTURE TYPE")
        print("=" * 80)

        for (fuel_name, infr_type_str), energy_kwh in sorted(energy_by_infr.items()):
            print(f"\n{fuel_name} - {infr_type_str}:")
            print(f"  Total energy: {energy_kwh / 1e6:,.2f} GWh ({energy_kwh:,.0f} kWh)")

    print("=" * 80)


def calculate_utilization_by_country_over_time(input_data, output_data, fuel_name=None,
                                              years=None):
    """
    Calculate infrastructure utilization by country for each year over time.

    This function tracks the development of infrastructure capacity and utilization
    by country from the initial year through the final year of the model.

    Parameters:
    -----------
    input_data : dict
        Input data dictionary

    output_data : dict
        Output data dictionary

    fuel_name : str, optional
        Filter by specific fuel (e.g., 'electricity', 'diesel'). If None, include all fuels.

    years : list, optional
        List of years to analyze. If None, uses all investment years.

    Returns:
    --------
    df_utilization : pd.DataFrame
        DataFrame with columns: year, country, fuel, infrastructure_type,
                                initial_capacity_kW, added_capacity_kW, total_capacity_kW,
                                energy_consumed_kWh, utilization_rate, utilization_pct
    """

    infra_data = get_infrastructure_data(input_data, output_data)
    fuel_list = infra_data['fuel_list']
    fueling_infr_types_list = infra_data['fueling_infr_types_list']
    initial_fueling_infr = infra_data['initial_fueling_infr']
    investment_years = infra_data['investment_years']

    if years is None:
        years = investment_years

    # Get geographic elements
    geographic_element_list = {d["id"]: d for d in input_data["GeographicElement"]}

    # Extract energy consumption by year, geo_id, fuel_id, infr_id
    energy_by_location = {}
    if 's' in output_data:
        for key, value in output_data['s'].items():
            s_year = key[0]
            if len(key) >= 4:
                f_l = key[3]  # (fuel_id, infr_id)
                fuel_id = f_l[0]
                infr_id = f_l[1]

                # Try to find geo_id - it's typically an integer in position 1 or 2
                geo_id = None
                if isinstance(key[1], int):
                    geo_id = key[1]
                elif len(key) > 2 and isinstance(key[2], int):
                    geo_id = key[2]

                if geo_id is not None:
                    energy_key = (s_year, geo_id, fuel_id, infr_id)
                    if energy_key not in energy_by_location:
                        energy_by_location[energy_key] = 0.0
                    energy_by_location[energy_key] += value

    # Aggregate by country, year, fuel, and infrastructure type
    records = []

    for year in years:
        # Aggregate by country for this year
        country_data = {}

        for geo_id, geo_data in geographic_element_list.items():
            country = geo_data.get('country', 'Unknown')

            for infr_id, infr_data in fueling_infr_types_list.items():
                for fuel_id, fuel_data in fuel_list.items():
                    current_fuel_name = fuel_data["name"]

                    # Skip if fuel_name filter is specified and doesn't match
                    if fuel_name is not None and current_fuel_name != fuel_name:
                        continue

                    # Check if this fuel-infrastructure combination is valid
                    if infr_data["fuel"] != current_fuel_name:
                        continue

                    infr_type_str = infr_data["fueling_type"]

                    # Create country aggregation key
                    country_key = (country, current_fuel_name, infr_type_str)

                    if country_key not in country_data:
                        country_data[country_key] = {
                            'initial_capacity_kW': 0.0,
                            'added_capacity_kW': 0.0,
                            'energy_consumed_kWh': 0.0
                        }

                    # Get initial capacity
                    initial_key = (current_fuel_name, infr_id, geo_id)
                    if initial_key in initial_fueling_infr:
                        country_data[country_key]['initial_capacity_kW'] += initial_fueling_infr[initial_key]["installed_kW"]

                    # Sum capacity additions up to this year
                    f_l = (fuel_id, infr_id)
                    for inv_year in investment_years:
                        if inv_year <= year:
                            key_q = (inv_year, f_l, geo_id)
                            if key_q in output_data["q_fuel_infr_plus"]:
                                country_data[country_key]['added_capacity_kW'] += output_data["q_fuel_infr_plus"][key_q]

                    # Get energy consumption for this year/location
                    energy_key = (year, geo_id, fuel_id, infr_id)
                    energy_consumed = energy_by_location.get(energy_key, 0.0)
                    country_data[country_key]['energy_consumed_kWh'] += energy_consumed

        # Create records for each country
        for (country, fuel_name_key, infr_type_str), data in country_data.items():
            total_capacity = data['initial_capacity_kW'] + data['added_capacity_kW']

            # Only include if there's some capacity
            if total_capacity > 0:
                # Calculate utilization rate
                max_possible_energy = total_capacity * 8760  # kWh
                utilization_rate = data['energy_consumed_kWh'] / max_possible_energy if max_possible_energy > 0 else 0.0

                records.append({
                    'year': year,
                    'country': country,
                    'fuel': fuel_name_key,
                    'infrastructure_type': infr_type_str,
                    'initial_capacity_kW': data['initial_capacity_kW'],
                    'added_capacity_kW': data['added_capacity_kW'],
                    'total_capacity_kW': total_capacity,
                    'energy_consumed_kWh': data['energy_consumed_kWh'],
                    'utilization_rate': utilization_rate,
                    'utilization_pct': utilization_rate * 100
                })

    df_utilization = pd.DataFrame(records)

    # Sort by year and country
    if len(df_utilization) > 0:
        df_utilization = df_utilization.sort_values(['year', 'country', 'fuel', 'infrastructure_type'])

    return df_utilization


def analyze_infrastructure(input_data, output_data, show_plot=True, verbose=True):
    """
    Complete infrastructure analysis workflow.

    This is a convenience function that runs the full analysis and optionally
    displays plots and prints summaries.

    Parameters:
    -----------
    input_data : dict
        Input data dictionary from YAML

    output_data : dict
        Output data dictionary from optimization results

    show_plot : bool, optional
        Whether to display plots. Default: True

    verbose : bool, optional
        Whether to print detailed summaries. Default: True

    Returns:
    --------
    capacity_by_type_year : dict
        Capacity additions by type and year

    energy_by_infr : dict
        Energy consumption by infrastructure type

    infra_data : dict
        Infrastructure metadata
    """

    # Calculate capacity expansion
    capacity_by_type_year, infra_data = calculate_capacity_by_year_and_type(
        input_data, output_data
    )

    # Calculate energy consumption
    energy_by_infr = calculate_energy_consumption_by_infrastructure(
        input_data, output_data
    )

    # Print summary
    if verbose:
        print_infrastructure_summary(capacity_by_type_year, energy_by_infr)

    # Plot
    if show_plot:
        fig, ax = plot_capacity_expansion_by_type(capacity_by_type_year, infra_data)
        plt.show()

    return capacity_by_type_year, energy_by_infr, infra_data


def analyze_charging_infrastructure(input_data, output_data, years_to_analyze=None,
                                   show_plot=True, verbose=True):
    """
    Specialized analysis for electric vehicle charging infrastructure.

    This function focuses specifically on slow and fast charging stations,
    tracking cumulative capacity growth and energy consumption.

    Parameters:
    -----------
    input_data : dict
        Input data dictionary

    output_data : dict
        Output data dictionary

    years_to_analyze : list, optional
        List of years to analyze. If None, uses all investment years.

    show_plot : bool, optional
        Whether to display plots. Default: True

    verbose : bool, optional
        Whether to print summaries. Default: True

    Returns:
    --------
    df_charging : pd.DataFrame
        DataFrame with charging infrastructure data by year
    """

    infra_data = get_infrastructure_data(input_data, output_data)
    fuel_list = infra_data['fuel_list']
    fueling_infr_types_list = infra_data['fueling_infr_types_list']
    initial_fueling_infr = infra_data['initial_fueling_infr']
    investment_years = infra_data['investment_years']

    if years_to_analyze is None:
        years_to_analyze = investment_years

    # Find electricity fuel ID and charging infrastructure IDs
    electricity_fuel_id = None
    for fuel_id, fuel_data in fuel_list.items():
        if fuel_data["name"] == "electricity":
            electricity_fuel_id = fuel_id
            break

    if electricity_fuel_id is None:
        print("Warning: No electricity fuel found!")
        return None

    slow_charging_id = None
    fast_charging_id = None
    for infr_id, infr_data in fueling_infr_types_list.items():
        if "slow" in infr_data["fueling_type"].lower() and infr_data["fuel"] == "electricity":
            slow_charging_id = infr_id
        elif "fast" in infr_data["fueling_type"].lower() and infr_data["fuel"] == "electricity":
            fast_charging_id = infr_id

    # Calculate capacity additions by year
    slow_capacity_by_year = {}
    fast_capacity_by_year = {}

    for key, value in output_data["q_fuel_infr_plus"].items():
        year = key[0]
        f_l = key[1]
        fuel_id = f_l[0]
        infr_id = f_l[1]

        if fuel_id == electricity_fuel_id:
            if infr_id == slow_charging_id:
                slow_capacity_by_year[year] = slow_capacity_by_year.get(year, 0) + value
            elif infr_id == fast_charging_id:
                fast_capacity_by_year[year] = fast_capacity_by_year.get(year, 0) + value

    # Get initial capacity
    initial_slow = 0
    initial_fast = 0

    for key, value in initial_fueling_infr.items():
        fuel_name, infr_id, geo_id = key
        if fuel_name == 'electricity':
            if infr_id == slow_charging_id:
                initial_slow += value['installed_kW']
            elif infr_id == fast_charging_id:
                initial_fast += value['installed_kW']

    # Calculate cumulative capacity
    years = sorted(set(list(slow_capacity_by_year.keys()) + list(fast_capacity_by_year.keys())))

    charging_data = []
    cumulative_slow = initial_slow
    cumulative_fast = initial_fast

    for year in years:
        slow_added = slow_capacity_by_year.get(year, 0)
        fast_added = fast_capacity_by_year.get(year, 0)

        cumulative_slow += slow_added
        cumulative_fast += fast_added

        charging_data.append({
            'year': year,
            'slow_added_kW': slow_added,
            'fast_added_kW': fast_added,
            'slow_cumulative_kW': cumulative_slow,
            'fast_cumulative_kW': cumulative_fast,
            'total_cumulative_kW': cumulative_slow + cumulative_fast
        })

    df_charging = pd.DataFrame(charging_data)

    if verbose:
        print("=" * 80)
        print("ELECTRIC VEHICLE CHARGING INFRASTRUCTURE ANALYSIS")
        print("=" * 80)
        print(f"\nInitial Capacity:")
        print(f"  Slow charging: {initial_slow:,.0f} kW ({initial_slow/1000:.1f} MW)")
        print(f"  Fast charging: {initial_fast:,.0f} kW ({initial_fast/1000:.1f} MW)")
        print(f"\nTotal Additions:")
        print(f"  Slow charging: {sum(slow_capacity_by_year.values()):,.0f} kW")
        print(f"  Fast charging: {sum(fast_capacity_by_year.values()):,.0f} kW")
        if len(df_charging) > 0:
            final_row = df_charging.iloc[-1]
            print(f"\nFinal Total Capacity ({final_row['year']}):")
            print(f"  Slow charging: {final_row['slow_cumulative_kW']:,.0f} kW")
            print(f"  Fast charging: {final_row['fast_cumulative_kW']:,.0f} kW")
            print(f"  Total: {final_row['total_cumulative_kW']:,.0f} kW")
        print("=" * 80)

    if show_plot and len(df_charging) > 0:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        # Plot cumulative capacity
        ax1.plot(df_charging['year'], df_charging['slow_cumulative_kW'] / 1000,
                marker='o', label='Slow Charging', linewidth=2)
        ax1.plot(df_charging['year'], df_charging['fast_cumulative_kW'] / 1000,
                marker='s', label='Fast Charging', linewidth=2)
        ax1.set_xlabel('Year')
        ax1.set_ylabel('Cumulative Capacity (MW)')
        ax1.set_title('Cumulative Charging Infrastructure Capacity')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Plot annual additions
        x = np.arange(len(df_charging))
        width = 0.35
        ax2.bar(x - width/2, df_charging['slow_added_kW'] / 1000,
               width, label='Slow Charging')
        ax2.bar(x + width/2, df_charging['fast_added_kW'] / 1000,
               width, label='Fast Charging')
        ax2.set_xlabel('Year')
        ax2.set_ylabel('Capacity Addition (MW)')
        ax2.set_title('Annual Charging Infrastructure Additions')
        ax2.set_xticks(x)
        ax2.set_xticklabels(df_charging['year'])
        ax2.legend()
        ax2.grid(True, alpha=0.3, axis='y')

        plt.tight_layout()
        plt.show()

    return df_charging


# Example usage
if __name__ == "__main__":
    """
    Example of how to use this module in your own scripts.
    """

    # Run complete infrastructure analysis
    # capacity_by_type_year, energy_by_infr, infra_data = analyze_infrastructure(
    #     input_data, output_data, show_plot=True, verbose=True
    # )

    # Analyze charging infrastructure specifically
    # df_charging = analyze_charging_infrastructure(
    #     input_data, output_data, show_plot=True, verbose=True
    # )

    # Get capacity by geographic element for a specific year with utilization
    # df_geo_capacity = calculate_capacity_by_geographic_element(
    #     input_data, output_data, year=2040, fuel_name='electricity',
    #     include_utilization=True
    # )
    # print(df_geo_capacity[['geo_name', 'total_capacity_kW', 'utilization_pct']])

    # Analyze by country
    # df_by_country = df_geo_capacity.groupby('country').agg({
    #     'total_capacity_kW': 'sum',
    #     'energy_consumed_kWh': 'sum'
    # })
    # df_by_country['avg_utilization_pct'] = (
    #     df_by_country['energy_consumed_kWh'] / (df_by_country['total_capacity_kW'] * 8760) * 100
    # )

    # Track utilization development by country over time (2020-2060)
    # df_util_over_time = calculate_utilization_by_country_over_time(
    #     input_data, output_data, fuel_name='electricity'
    # )
    # # Plot utilization for a specific country
    # country_data = df_util_over_time[df_util_over_time['country'] == 'DE']
    # plt.plot(country_data['year'], country_data['utilization_pct'], marker='o')
    # plt.xlabel('Year')
    # plt.ylabel('Utilization (%)')
    # plt.title('Infrastructure Utilization in Germany')
    # plt.grid(True)
    # plt.show()

    print("Infrastructure analysis module loaded.")
    print("Import this module and use analyze_infrastructure() or individual functions.")
