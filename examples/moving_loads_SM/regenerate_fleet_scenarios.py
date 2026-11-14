"""
Regenerate TechVehicle.yaml for fleet verification scenarios with updated ICCT 2023 costs.

This script:
1. Generates new TechVehicle parameters using SM_preprocessing.py (with updated costs)
2. Updates TechVehicle.yaml in scenario_000, scenario_001, scenario_002
3. Applies the tech_cost_multiplier (0.7, 1.0, 1.3) to BEV capital costs
"""

import sys
import yaml
from pathlib import Path

# Add parent directory to path
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from SM_preprocessing import SMParameterGenerator

# Scenario configurations
SCENARIOS = {
    'scenario_000': {'tech_cost_multiplier': 0.7, 'label': 'Low Cost (0.7x)'},
    'scenario_001': {'tech_cost_multiplier': 1.0, 'label': 'Baseline (1.0x)'},
    'scenario_002': {'tech_cost_multiplier': 1.3, 'label': 'High Cost (1.3x)'},
}

def apply_tech_cost_multiplier(tech_vehicles: list, multiplier: float) -> list:
    """
    Apply technology cost multiplier to BEV capital costs.

    The multiplier is applied uniformly to all years (not time-dependent).
    """
    for tv in tech_vehicles:
        # Identify BEV by technology id (1) or name
        is_bev = (tv.get('technology') == 1) or ('bev' in tv.get('name', '').lower())

        if is_bev and 'capital_cost' in tv:
            original_costs = tv['capital_cost']
            tv['capital_cost'] = [c * multiplier for c in original_costs]
            print(f"    Applied {multiplier}x to BEV capital_cost ({len(original_costs)} values)")
            print(f"    Sample: 2023={original_costs[0]:,.0f} -> {tv['capital_cost'][0]:,.0f}")

    return tech_vehicles


def main():
    print("=" * 80)
    print("REGENERATING TECHVEHICLE.YAML FOR FLEET VERIFICATION SCENARIOS")
    print("Using updated ICCT 2023 capital costs")
    print("=" * 80)

    # Step 1: Generate new TechVehicle parameters from SM_preprocessing
    print("\nStep 1: Generating base TechVehicle parameters...")
    generator = SMParameterGenerator()
    base_tech_vehicles = generator.generate_tech_vehicle_params(num_generations=41 + 12)

    # Print base costs for verification
    # capital_cost array is indexed starting from 2020 (index 0 = 2020)
    print("\nBase capital costs (before multiplier):")
    for tv in base_tech_vehicles:
        name = tv['name']
        costs = tv['capital_cost']
        print(f"  {name}: {len(costs)} values")
        # Index: 2020=0, 2023=3, 2030=10, 2040=20
        if len(costs) > 20:
            print(f"    2020 (idx 0):  {costs[0]:,.0f} EUR")
            print(f"    2023 (idx 3):  {costs[3]:,.0f} EUR")
            print(f"    2030 (idx 10): {costs[10]:,.0f} EUR")
            print(f"    2040 (idx 20): {costs[20]:,.0f} EUR")

    # Step 2: Update each scenario
    scenarios_dir = script_dir / 'input_data' / 'uncertainty_scenarios'

    for scenario_id, config in SCENARIOS.items():
        print(f"\nStep 2: Processing {scenario_id} (tech_cost = {config['tech_cost_multiplier']}x)...")

        scenario_path = scenarios_dir / scenario_id
        if not scenario_path.exists():
            print(f"  [WARN] Scenario folder not found: {scenario_path}")
            continue

        # Create a copy of base tech vehicles
        import copy
        scenario_tech_vehicles = copy.deepcopy(base_tech_vehicles)

        # Apply tech cost multiplier
        scenario_tech_vehicles = apply_tech_cost_multiplier(
            scenario_tech_vehicles,
            config['tech_cost_multiplier']
        )

        # Write to TechVehicle.yaml
        tv_path = scenario_path / 'TechVehicle.yaml'

        # Backup original
        backup_path = scenario_path / 'TechVehicle.yaml.backup_old_costs'
        if tv_path.exists() and not backup_path.exists():
            import shutil
            shutil.copy(tv_path, backup_path)
            print(f"  Backed up original to {backup_path.name}")

        # Write new file
        with open(tv_path, 'w') as f:
            yaml.dump(scenario_tech_vehicles, f, default_flow_style=False, allow_unicode=True)

        print(f"  [OK] Updated {tv_path}")

    print("\n" + "=" * 80)
    print("REGENERATION COMPLETE")
    print("=" * 80)
    print("\nNew capital costs (ICCT 2023):")
    print("  ICEV: 152k (2023) -> 167k (2030+)")
    print("  BEV:  457k (2023) -> 222k (2030) -> 202k (2040+)")
    print("\nScenario multipliers applied:")
    for scenario_id, config in SCENARIOS.items():
        mult = config['tech_cost_multiplier']
        bev_2040 = 202000 * mult
        print(f"  {scenario_id}: {mult}x -> BEV 2040 = {bev_2040:,.0f} EUR")
    print("\nYou can now re-run SM_fleet_verification.jl to verify fleet behavior.")


if __name__ == "__main__":
    main()
