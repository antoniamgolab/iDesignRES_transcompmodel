"""Quick script to regenerate the 24 uncertainty scenarios with updated capital costs."""
import os
import sys
from pathlib import Path

# Set working directory
script_dir = Path(__file__).parent
os.chdir(script_dir)

# Add uncertainty_analysis to path
sys.path.insert(0, str(script_dir / 'uncertainty_analysis'))

from genesys_scenario_sampler import GENeSYSScenarioSampler
from yaml_modifier_genesys import YAMLModifierGENeSYS
from batch_runner import BatchRunner

def main():
    print("=" * 80)
    print("REGENERATING 24 UNCERTAINTY SCENARIOS WITH UPDATED CAPITAL COSTS")
    print("=" * 80)

    base_case_path = script_dir / 'input_data' / 'case_nuts2_complete'
    genesys_data_path = script_dir / 'data' / 'GENeSYS-MOD_EU-EnVis-2060_v1.2.0_native' / 'output_endogenous_fuelcosts.csv'
    scenarios_path = script_dir / 'input_data' / 'uncertainty_scenarios'
    results_path = script_dir / 'results' / 'uncertainty_scenarios'

    # Check paths
    if not base_case_path.exists():
        raise FileNotFoundError(f"Base case not found: {base_case_path}")
    if not genesys_data_path.exists():
        raise FileNotFoundError(f"GENeSYS data not found: {genesys_data_path}")

    print(f"\nBase case: {base_case_path}")
    print(f"GENeSYS data: {genesys_data_path}")
    print(f"Output: {scenarios_path}")

    # Step 1: Load GENeSYS data
    print("\n=== STEP 1: Loading GENeSYS-MOD Scenario Data ===")
    sampler = GENeSYSScenarioSampler(genesys_data_path, seed=42)

    print("\nGENeSYS Scenario Multipliers (relative to Go RES v1.2):")
    for name, mult in sampler.get_scenario_multipliers().items():
        print(f"  {name}: {mult:.3f}x")

    # Step 2: Generate factorial design
    print("\n=== STEP 2: Generating Cases (factorial design) ===")
    charging_markups = [0.15, 0.30]
    tech_multipliers = [0.7, 1.0, 1.3]

    cases = sampler.generate_discrete_genesys_cases(
        charging_markups=charging_markups,
        tech_multipliers=tech_multipliers
    )

    print(f"\nFactorial design:")
    print(f"  4 GENeSYS scenarios × {len(charging_markups)} charging markup × {len(tech_multipliers)} tech = {len(cases)} cases")

    # Save cases
    cases_json = scenarios_path / "cases.json"
    scenarios_path.mkdir(parents=True, exist_ok=True)
    sampler.save_cases(cases, cases_json)

    # Step 3: Create scenario folders
    print("\n=== STEP 3: Creating Scenario Input Folders ===")
    modifier = YAMLModifierGENeSYS(base_case_path, scenarios_path, sampler)
    scenario_folders = modifier.apply_all_cases(cases)

    print(f"\nCreated {len(scenario_folders)} scenario folders")

    # Step 4: Generate Julia batch script
    print("\n=== STEP 4: Generating Julia Batch Script ===")
    runner = BatchRunner(
        scenario_folders=scenario_folders,
        results_base_path=results_path
    )
    julia_script = runner.generate_julia_batch_script(script_dir)
    print(f"\nJulia batch script: {julia_script}")

    # Summary
    print("\n" + "=" * 80)
    print("PIPELINE COMPLETE - 24 SCENARIOS REGENERATED")
    print("=" * 80)
    print(f"\nOutputs:")
    print(f"  Cases JSON:        {cases_json}")
    print(f"  Scenario folders:  {scenarios_path}")
    print(f"  Julia script:      {julia_script}")

    # Print case summary
    print("\n=== Case Summary ===")
    print(f"{'ID':>4} | {'GENeSYS Scenario':<22} | {'Elec':>6} | {'ChgMk':>6} | {'Tech':>5}")
    print("-" * 60)
    for c in cases:
        print(f"{c.case_id:4d} | {c.genesys_scenario:<22} | "
              f"{c.electricity_price_multiplier:6.3f} | "
              f"{c.charging_markup:6.0%} | {c.tech_cost_multiplier:5.2f}")

if __name__ == "__main__":
    main()
