"""
Calculate Levelized Costs from Fleet Verification Results
Based on: fleet size (h), energy consumed (s), and total system cost (objective value)
Uses data from comparison_summary.yaml which contains fleet_by_tv_year directly.
"""

import yaml
import os
import pandas as pd
import numpy as np

# Results directory
results_dir = os.path.join(os.path.dirname(__file__), 'results', 'fleet_verification_compare')

# Load comparison summary - contains all the data we need
with open(os.path.join(results_dir, 'comparison_summary.yaml'), 'r') as f:
    comparison = yaml.safe_load(f)

# Scenario metadata
scenarios = ['scenario_000', 'scenario_001', 'scenario_002']
tech_costs = {'scenario_000': 0.7, 'scenario_001': 1.0, 'scenario_002': 1.3}

# Years modeled
years = [2020, 2024, 2028, 2032, 2036, 2040, 2044, 2048, 2052, 2056, 2060]
time_step = 4  # years per period

print("=" * 80)
print("LEVELIZED COST ANALYSIS")
print("=" * 80)

# Store results
results_data = []

for scenario in scenarios:
    print(f"\n{'='*60}")
    print(f"SCENARIO: {scenario} (Tech Cost = {tech_costs[scenario]}x)")
    print("=" * 60)

    for config in ['no_fuel', 'with_fuel']:
        config_label = "Without Fuel Costs" if config == 'no_fuel' else "With Fuel Costs"
        print(f"\n--- {config_label} ---")

        # Get data from comparison summary
        scenario_data = comparison[scenario][config]
        obj_value = float(scenario_data['objective_value'])
        fleet_by_tv_year = scenario_data['fleet_by_tv_year']

        # Calculate total fleet-years (sum of fleet * time_step for each period)
        # fleet_by_tv_year is {0: {year: value}, 1: {year: value}} where 0=ICEV, 1=BEV
        total_fleet_years = 0
        fleet_by_tech = {0: 0.0, 1: 0.0}  # ICEV=0, BEV=1

        for tv_id in [0, 1]:
            tv_fleet = fleet_by_tv_year.get(tv_id, {})
            for year, fleet_size in tv_fleet.items():
                # Each year's fleet is active for time_step years
                fs = float(fleet_size)
                total_fleet_years += fs * time_step
                fleet_by_tech[tv_id] += fs * time_step

        # Calculate average fleet size per year
        avg_fleet = total_fleet_years / (len(years) * time_step)

        # Calculate levelized cost per vehicle-year
        eur_per_vehicle_year = obj_value / total_fleet_years if total_fleet_years > 0 else 0

        # Calculate BEV share of fleet-years
        total_fleet = fleet_by_tech[0] + fleet_by_tech[1]
        bev_share = fleet_by_tech[1] / total_fleet * 100 if total_fleet > 0 else 0

        # For energy consumption, we need to load s_dict from the with_fuel runs
        total_energy_mwh = 0
        energy_by_tech = {0: 0.0, 1: 0.0}

        if config == 'with_fuel':
            scenario_dir = os.path.join(results_dir, scenario, config)
            # Filter for s_dict specifically (not h_minus_dict or h_plus_dict which also contain 's_dict')
            s_files = [f for f in os.listdir(scenario_dir) if '_s_dict' in f and f.endswith('.yaml')]
            if s_files:
                with open(os.path.join(scenario_dir, s_files[0]), 'r') as f:
                    s_dict = yaml.safe_load(f)

                for key, value in s_dict.items():
                    # Values are stored as strings
                    val = float(value)
                    total_energy_mwh += val
                    # Parse key to get tv_id - format: "(year, path_tuple, tv_id, ...)"
                    # Key format: (2024, (0, 1508, 1508, 10), 0, (1, 0), 2020)
                    # The tv_id is the 3rd element (after the path tuple)
                    parts = str(key).split('),')
                    if len(parts) >= 2:
                        tv_part = parts[1].strip().lstrip(' ')
                        try:
                            tv_id = int(tv_part.split(',')[0].strip())
                            energy_by_tech[tv_id] += val
                        except:
                            pass

        # Convert to TWh for readability
        total_energy_twh = total_energy_mwh / 1e6

        # Calculate EUR per MWh (if energy data available)
        eur_per_mwh = obj_value / total_energy_mwh if total_energy_mwh > 0 else 0

        print(f"  Objective Value: {obj_value/1e9:.2f} billion EUR")
        print(f"  Total Fleet-Years: {total_fleet_years:,.0f}")
        print(f"  Average Fleet Size: {avg_fleet:,.0f} vehicles")
        print(f"  - ICEV fleet-years: {fleet_by_tech[0]:,.0f}")
        print(f"  - BEV fleet-years: {fleet_by_tech[1]:,.0f}")
        print(f"  - BEV Share: {bev_share:.1f}%")

        if total_energy_mwh > 0:
            print(f"  Total Energy: {total_energy_twh:.2f} TWh")
            print(f"  - ICEV energy: {energy_by_tech[0]/1e6:.2f} TWh")
            print(f"  - BEV energy: {energy_by_tech[1]/1e6:.2f} TWh")

        print(f"\n  LEVELIZED COSTS:")
        print(f"  - EUR per vehicle-year: {eur_per_vehicle_year:,.0f} EUR")
        if total_energy_mwh > 0:
            print(f"  - EUR per MWh: {eur_per_mwh:,.2f} EUR/MWh")
            print(f"  - EUR per kWh: {eur_per_mwh/1000:.4f} EUR/kWh")

        # Store for comparison table
        results_data.append({
            'scenario': scenario,
            'tech_cost': tech_costs[scenario],
            'config': config,
            'objective_eur': obj_value,
            'total_fleet_years': total_fleet_years,
            'avg_fleet': avg_fleet,
            'icev_fleet_years': fleet_by_tech[0],
            'bev_fleet_years': fleet_by_tech[1],
            'bev_share_pct': bev_share,
            'total_energy_twh': total_energy_twh,
            'eur_per_vehicle_year': eur_per_vehicle_year,
            'eur_per_mwh': eur_per_mwh if total_energy_mwh > 0 else None
        })

# Create comparison table
print("\n" + "=" * 100)
print("LEVELIZED COST COMPARISON TABLE")
print("=" * 100)

df = pd.DataFrame(results_data)

# Print summary table
print("\n--- Cost per Vehicle-Year ---")
print(f"{'Scenario':<15} {'Tech Cost':<12} {'No Fuel (EUR)':<18} {'With Fuel (EUR)':<18} {'Difference':<12}")
print("-" * 75)

for scenario in scenarios:
    no_fuel = df[(df['scenario'] == scenario) & (df['config'] == 'no_fuel')]['eur_per_vehicle_year'].values[0]
    with_fuel = df[(df['scenario'] == scenario) & (df['config'] == 'with_fuel')]['eur_per_vehicle_year'].values[0]
    diff = with_fuel - no_fuel
    diff_pct = diff / no_fuel * 100
    print(f"{scenario:<15} {tech_costs[scenario]:<12.1f}x {no_fuel:>15,.0f} {with_fuel:>15,.0f} {diff:>+10,.0f} ({diff_pct:+.1f}%)")

print("\n--- BEV Share (%) ---")
print(f"{'Scenario':<15} {'Tech Cost':<12} {'No Fuel (%)':<18} {'With Fuel (%)':<18}")
print("-" * 60)

for scenario in scenarios:
    no_fuel = df[(df['scenario'] == scenario) & (df['config'] == 'no_fuel')]['bev_share_pct'].values[0]
    with_fuel = df[(df['scenario'] == scenario) & (df['config'] == 'with_fuel')]['bev_share_pct'].values[0]
    print(f"{scenario:<15} {tech_costs[scenario]:<12.1f}x {no_fuel:>15.1f}% {with_fuel:>15.1f}%")

print("\n--- Total Energy Consumed (TWh) - With Fuel Costs Only ---")
print(f"{'Scenario':<15} {'Tech Cost':<12} {'Total (TWh)':<15} {'ICEV (TWh)':<15} {'BEV (TWh)':<15}")
print("-" * 70)

for scenario in scenarios:
    row = df[(df['scenario'] == scenario) & (df['config'] == 'with_fuel')].iloc[0]
    icev_twh = row['icev_fleet_years'] / row['total_fleet_years'] * row['total_energy_twh'] if row['total_fleet_years'] > 0 else 0
    bev_twh = row['bev_fleet_years'] / row['total_fleet_years'] * row['total_energy_twh'] if row['total_fleet_years'] > 0 else 0
    print(f"{scenario:<15} {tech_costs[scenario]:<12.1f}x {row['total_energy_twh']:>12.2f} {icev_twh:>12.2f} {bev_twh:>12.2f}")

# Save to CSV
output_csv = os.path.join(results_dir, 'levelized_costs_comparison.csv')
df.to_csv(output_csv, index=False)
print(f"\n[OK] Results saved to: {output_csv}")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
