"""
Corridor Analysis at NUTS2 Region Level

This script analyzes specific cross-border corridors using the exact NUTS2 regions
defined for each corridor, rather than aggregating by entire countries.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from electrification_analysis import calculate_electrification_by_nuts2


def analyze_corridors_nuts2(input_data_dict, output_data_dict, corridors_definition,
                             years_to_plot=None, verbose=True):
    """
    Analyze specific cross-border corridors at NUTS2 region level.

    Parameters:
    -----------
    input_data_dict : dict
        Dictionary mapping scenario names to input_data dicts
        Format: {scenario_name: input_data, ...}

    output_data_dict : dict
        Dictionary mapping scenario names to output_data dicts
        Format: {scenario_name: output_data, ...}

    corridors_definition : dict
        Dictionary defining corridors with specific NUTS2 regions
        Format: {
            'corridor_name': {
                'country1': ['NUTS2_code1', 'NUTS2_code2', ...],
                'country2': ['NUTS2_code3', 'NUTS2_code4', ...]
            }
        }

    years_to_plot : list, optional
        Years to analyze. Default: [2030, 2040]

    verbose : bool
        Whether to print detailed output

    Returns:
    --------
    df_corridor_analysis : pd.DataFrame
        Corridor-level analysis with deltas
    """

    if years_to_plot is None:
        years_to_plot = [2030, 2040]

    # Step 1: Calculate NUTS2-level electrification for all scenarios
    nuts2_results = {}

    for scenario_name, input_data in input_data_dict.items():
        output_data = output_data_dict[scenario_name]

        if verbose:
            print(f"Calculating NUTS2-level electrification for: {scenario_name}")

        df_nuts2, _, skip_counters = calculate_electrification_by_nuts2(
            input_data, output_data, years_to_plot
        )

        nuts2_results[scenario_name] = df_nuts2

        if verbose:
            print(f"  Found {len(df_nuts2)} NUTS2-year combinations")
            print(f"  Skip counters: {skip_counters}")

    # Step 2: Analyze each corridor
    corridor_analysis = []

    # Identify reference scenario (typically the first one)
    scenario_names = list(input_data_dict.keys())
    reference_scenario = scenario_names[0]

    if verbose:
        print(f"\nUsing '{reference_scenario}' as reference scenario")
        print("\n" + "=" * 80)
        print("CORRIDOR ANALYSIS (NUTS2 LEVEL)")
        print("=" * 80)

    for corridor_name, countries_regions in corridors_definition.items():
        if verbose:
            print(f"\n{corridor_name} Corridor:")
            print("-" * 60)

        # Get all NUTS2 regions in this corridor
        corridor_nuts2_list = []
        for country, regions in countries_regions.items():
            corridor_nuts2_list.extend(regions)

        if verbose:
            print(f"  Regions: {corridor_nuts2_list}")

        # Analyze by year
        for year in years_to_plot:
            # Get reference data for this corridor
            ref_df = nuts2_results[reference_scenario]
            ref_corridor = ref_df[
                (ref_df['nuts2_region'].isin(corridor_nuts2_list)) &
                (ref_df['year'] == year)
            ]

            if len(ref_corridor) == 0:
                if verbose:
                    print(f"  {year}: No reference data found for corridor regions")
                continue

            ref_total_elec = ref_corridor['electricity'].sum()
            ref_total_fuel = ref_corridor['total_fuel'].sum()
            ref_avg_pct = (ref_total_elec / ref_total_fuel * 100) if ref_total_fuel > 0 else 0

            # Compare with other scenarios
            for scenario_name in scenario_names:
                if scenario_name == reference_scenario:
                    # Still record reference values
                    corridor_analysis.append({
                        'corridor': corridor_name,
                        'year': year,
                        'scenario': scenario_name,
                        'num_regions': len(ref_corridor),
                        'ref_electricity_MWh': ref_total_elec,
                        'case_electricity_MWh': ref_total_elec,
                        'delta_electricity_MWh': 0.0,
                        'ref_total_fuel_MWh': ref_total_fuel,
                        'case_total_fuel_MWh': ref_total_fuel,
                        'delta_total_fuel_MWh': 0.0,
                        'ref_avg_electrification_pct': ref_avg_pct,
                        'case_avg_electrification_pct': ref_avg_pct,
                        'delta_electrification_pct': 0.0
                    })
                    continue

                # Get case scenario data
                case_df = nuts2_results[scenario_name]
                case_corridor = case_df[
                    (case_df['nuts2_region'].isin(corridor_nuts2_list)) &
                    (case_df['year'] == year)
                ]

                if len(case_corridor) == 0:
                    if verbose:
                        print(f"  {year} - {scenario_name}: No data found")
                    continue

                case_total_elec = case_corridor['electricity'].sum()
                case_total_fuel = case_corridor['total_fuel'].sum()
                case_avg_pct = (case_total_elec / case_total_fuel * 100) if case_total_fuel > 0 else 0

                delta_elec = case_total_elec - ref_total_elec
                delta_fuel = case_total_fuel - ref_total_fuel
                delta_pct = case_avg_pct - ref_avg_pct

                corridor_analysis.append({
                    'corridor': corridor_name,
                    'year': year,
                    'scenario': scenario_name,
                    'num_regions': len(case_corridor),
                    'ref_electricity_MWh': ref_total_elec,
                    'case_electricity_MWh': case_total_elec,
                    'delta_electricity_MWh': delta_elec,
                    'ref_total_fuel_MWh': ref_total_fuel,
                    'case_total_fuel_MWh': case_total_fuel,
                    'delta_total_fuel_MWh': delta_fuel,
                    'ref_avg_electrification_pct': ref_avg_pct,
                    'case_avg_electrification_pct': case_avg_pct,
                    'delta_electrification_pct': delta_pct
                })

                if verbose:
                    print(f"  {year} - {scenario_name}:")
                    print(f"    Regions analyzed: {len(case_corridor)}")
                    print(f"    Electricity:      {ref_total_elec:>10.2f} → {case_total_elec:>10.2f} "
                          f"(Δ {delta_elec:+10.2f} MWh)")
                    print(f"    Total Fuel:       {ref_total_fuel:>10.2f} → {case_total_fuel:>10.2f} "
                          f"(Δ {delta_fuel:+10.2f} MWh)")
                    print(f"    Avg Electrif.:    {ref_avg_pct:>10.2f}% → {case_avg_pct:>10.2f}% "
                          f"(Δ {delta_pct:+10.2f} pp)")

    df_corridor_analysis = pd.DataFrame(corridor_analysis)

    return df_corridor_analysis, nuts2_results


def plot_corridor_analysis(df_corridor, scenario_labels=None, years_to_plot=None,
                           reference_scenario=None, figsize=(16, 12)):
    """
    Create visualization of corridor analysis results.

    Parameters:
    -----------
    df_corridor : pd.DataFrame
        Output from analyze_corridors_nuts2()

    scenario_labels : dict, optional
        Mapping from scenario names to display labels

    years_to_plot : list, optional
        Years to plot. Default: [2030, 2040]

    reference_scenario : str, optional
        Name of reference scenario to exclude from plots

    figsize : tuple
        Figure size

    Returns:
    --------
    fig : matplotlib Figure
    """

    if years_to_plot is None:
        years_to_plot = sorted(df_corridor['year'].unique())

    if scenario_labels is None:
        scenario_labels = {s: s for s in df_corridor['scenario'].unique()}

    # Exclude reference scenario if specified
    if reference_scenario:
        df_plot = df_corridor[df_corridor['scenario'] != reference_scenario].copy()
    else:
        df_plot = df_corridor.copy()

    # Apply labels
    df_plot['scenario_label'] = df_plot['scenario'].map(scenario_labels)

    fig, axes = plt.subplots(2, 2, figsize=figsize)

    for year_idx, year in enumerate(years_to_plot):
        year_data = df_plot[df_plot['year'] == year]

        if len(year_data) == 0:
            continue

        # Electricity delta by corridor
        ax1 = axes[year_idx, 0]
        pivot_elec = year_data.pivot(index='corridor', columns='scenario_label',
                                      values='delta_electricity_MWh')

        x = np.arange(len(pivot_elec.index))
        width = 0.25

        for i, scenario in enumerate(pivot_elec.columns):
            offset = (i - len(pivot_elec.columns)/2 + 0.5) * width
            bars = ax1.bar(x + offset, pivot_elec[scenario], width, label=scenario, alpha=0.8)

            # Add value labels
            for j, v in enumerate(pivot_elec[scenario]):
                if not pd.isna(v):
                    ax1.text(j + offset, v, f'{v:+.0f}', ha='center',
                            va='bottom' if v > 0 else 'top', fontsize=7)

        ax1.set_xlabel('Corridor')
        ax1.set_ylabel('Δ Electricity (MWh)')
        ax1.set_title(f'Corridor Electricity Deltas ({year})', fontweight='bold')
        ax1.set_xticks(x)
        ax1.set_xticklabels(pivot_elec.index, rotation=45, ha='right')
        ax1.legend()
        ax1.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax1.grid(axis='y', alpha=0.3)

        # Electrification delta by corridor
        ax2 = axes[year_idx, 1]
        pivot_pct = year_data.pivot(index='corridor', columns='scenario_label',
                                     values='delta_electrification_pct')

        for i, scenario in enumerate(pivot_pct.columns):
            offset = (i - len(pivot_pct.columns)/2 + 0.5) * width
            bars = ax2.bar(x + offset, pivot_pct[scenario], width, label=scenario, alpha=0.8)

            # Add value labels
            for j, v in enumerate(pivot_pct[scenario]):
                if not pd.isna(v):
                    ax2.text(j + offset, v, f'{v:+.1f}', ha='center',
                            va='bottom' if v > 0 else 'top', fontsize=7)

        ax2.set_xlabel('Corridor')
        ax2.set_ylabel('Δ Electrification (%)')
        ax2.set_title(f'Corridor Electrification Rate Deltas ({year})', fontweight='bold')
        ax2.set_xticks(x)
        ax2.set_xticklabels(pivot_pct.index, rotation=45, ha='right')
        ax2.legend()
        ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax2.grid(axis='y', alpha=0.3)

    plt.tight_layout()

    return fig


if __name__ == "__main__":
    print("Corridor analysis module (NUTS2 level) loaded.")
    print("\nExample usage:")
    print("""
    from corridor_analysis_nuts2 import analyze_corridors_nuts2, plot_corridor_analysis

    # Define corridors with specific NUTS2 regions
    corridors = {
        'Austria-Germany': {
            'AT': ['AT31', 'AT32', 'AT33', 'AT34'],
            'DE': ['DE14', 'DE21', 'DE22', 'DE27']
        },
        'Austria-Italy': {
            'AT': ['AT32', 'AT33'],
            'IT': ['ITH1', 'ITH3']
        }
    }

    # Prepare scenario dictionaries
    input_data_dict = {
        'reference': input_data_ref,
        'scenario1': input_data_s1,
        'scenario2': input_data_s2
    }

    output_data_dict = {
        'reference': output_data_ref,
        'scenario1': output_data_s1,
        'scenario2': output_data_s2
    }

    # Run analysis
    df_corridor, nuts2_results = analyze_corridors_nuts2(
        input_data_dict,
        output_data_dict,
        corridors,
        years_to_plot=[2030, 2040],
        verbose=True
    )

    # Plot results
    scenario_labels = {
        'reference': 'Reference',
        'scenario1': 'Scenario 1',
        'scenario2': 'Scenario 2'
    }

    fig = plot_corridor_analysis(
        df_corridor,
        scenario_labels=scenario_labels,
        reference_scenario='reference'
    )

    plt.savefig('corridor_analysis_nuts2.png', dpi=300, bbox_inches='tight')
    plt.show()

    # Export results
    df_corridor.to_csv('corridor_analysis_nuts2.csv', index=False)
    """)
