"""
Compare actual cost values across cases to understand magnitude of differences
"""
import yaml
from pathlib import Path
import pandas as pd
import numpy as np


def compare_fuel_costs():
    """Compare FuelCost.yaml values across cases"""
    cases = [
        ('case_20251107_194948_var_var', 'Variable Prices'),
        ('case_20251107_214220_uni_var', 'Uniform Prices'),
    ]

    print("="*80)
    print("FUEL COST COMPARISON (Electricity Prices)")
    print("="*80)

    for case_name, label in cases:
        file_path = Path('input_data') / case_name / 'FuelCost.yaml'

        if not file_path.exists():
            print(f"\n{label} ({case_name}): FILE NOT FOUND")
            continue

        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        print(f"\n{label} ({case_name}):")
        print(f"  Number of entries: {len(data)}")

        if data:
            # Show first few entries
            for i, entry in enumerate(data[:5]):
                location = entry.get('location', 'N/A')
                fuel = entry.get('fuel', 'N/A')
                costs = entry.get('cost_per_kWh', [])
                print(f"  Entry {i+1}:")
                print(f"    Location: {location}")
                print(f"    Fuel: {fuel}")
                if costs:
                    if isinstance(costs, list):
                        print(f"    Costs (first 3 years): {costs[:3]}")
                    else:
                        sample_years = sorted(costs.keys())[:3]
                        sample_costs = {year: costs[year] for year in sample_years}
                        print(f"    Costs (sample years): {sample_costs}")

            # Summary statistics
            all_costs = []
            for entry in data:
                costs = entry.get('cost_per_kWh', [])
                if isinstance(costs, list):
                    all_costs.extend(costs)
                else:
                    all_costs.extend(costs.values())

            if all_costs:
                print(f"\n  Cost statistics:")
                print(f"    Min: {min(all_costs):.6f}")
                print(f"    Max: {max(all_costs):.6f}")
                print(f"    Mean: {np.mean(all_costs):.6f}")
                print(f"    Std Dev: {np.std(all_costs):.6f}")


def compare_network_costs():
    """Compare NetworkConnectionCosts.yaml values across cases"""
    cases = [
        ('case_20251107_194948_var_var', 'Variable Network'),
        ('case_20251107_214135_var_uni', 'Uniform Network'),
    ]

    print("\n" + "="*80)
    print("NETWORK CONNECTION COST COMPARISON")
    print("="*80)

    for case_name, label in cases:
        file_path = Path('input_data') / case_name / 'NetworkConnectionCosts.yaml'

        if not file_path.exists():
            print(f"\n{label} ({case_name}): FILE NOT FOUND")
            continue

        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        print(f"\n{label} ({case_name}):")
        print(f"  Number of entries: {len(data)}")

        if data:
            # Show first few entries
            for i, entry in enumerate(data[:5]):
                location = entry.get('location', 'N/A')
                costs = entry.get('cost_per_kW', [])
                print(f"  Entry {i+1}:")
                print(f"    Location: {location}")
                if costs:
                    if isinstance(costs, list):
                        print(f"    Costs (first 3 years): {costs[:3]}")
                    else:
                        sample_years = sorted(costs.keys())[:3]
                        sample_costs = {year: costs[year] for year in sample_years}
                        print(f"    Costs (sample years): {sample_costs}")

            # Summary statistics
            all_costs = []
            for entry in data:
                costs = entry.get('cost_per_kW', [])
                if isinstance(costs, list):
                    all_costs.extend(costs)
                else:
                    all_costs.extend(costs.values())

            if all_costs:
                print(f"\n  Cost statistics:")
                print(f"    Min: {min(all_costs):.6f}")
                print(f"    Max: {max(all_costs):.6f}")
                print(f"    Mean: {np.mean(all_costs):.6f}")
                print(f"    Std Dev: {np.std(all_costs):.6f}")


def main():
    compare_fuel_costs()
    compare_network_costs()

    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)
    print("\nIf costs are identical between var/uni versions, that explains identical results.")
    print("If costs differ significantly, check if model is actually using these values.")


if __name__ == "__main__":
    main()
