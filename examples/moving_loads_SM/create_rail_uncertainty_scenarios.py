"""
Create Uncertainty Scenarios with Rail Mode
============================================

Two-step process:
1. Generate a base case with rail mode enabled using SM_preprocessing.py
2. Use the existing uncertainty pipeline to create 24 scenarios from that base case

This generates scenarios properly with rail integrated throughout the preprocessing.
"""

import os
import sys
import shutil
from pathlib import Path
from datetime import datetime

# Add parent to path for imports
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))
sys.path.insert(0, str(script_dir / 'uncertainty_analysis'))


def step1_create_rail_base_case():
    """
    Step 1: Create a base case with rail mode enabled.
    Uses SM_preprocessing.py with include_rail_mode=True.
    """
    from SM_preprocessing import SMParameterGenerator

    print("=" * 70)
    print("STEP 1: CREATE RAIL BASE CASE")
    print("=" * 70)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = script_dir / "input_data" / f"case_{timestamp}_rail_base"

    print(f"\nCreating rail base case at: {output_dir}")
    print("Settings:")
    print("  - include_rail_mode: True")
    print("  - electricity_prices_variable: True (var_var)")
    print("  - network_costs_variable: True (var_var)")

    generator = SMParameterGenerator(
        nuts3_data_dir="input_data/fixed_nuts_2",  # Use default NUTS-2 data with Austria routing
        output_dir=str(output_dir),
        case_name=f"case_{timestamp}_rail_base",
        electricity_prices_variable=True,
        network_costs_variable=True,
        reverse_electricity_prices=False,
        include_rail_mode=True,  # ENABLE RAIL
        filter_low_volume=True,
        min_freight_threshold=1000.0
    )

    generator.run()

    print(f"\n[OK] Rail base case created: {output_dir}")
    return output_dir


def step2_create_uncertainty_scenarios(base_case_path: Path):
    """
    Step 2: Use the uncertainty pipeline to create 24 scenarios.
    """
    from uncertainty_analysis.run_genesys_pipeline import run_genesys_pipeline

    print("\n" + "=" * 70)
    print("STEP 2: CREATE UNCERTAINTY SCENARIOS FROM RAIL BASE CASE")
    print("=" * 70)

    genesys_data_path = script_dir / "data" / "GENeSYS-MOD_EU-EnVis-2060_v1.2.0_native" / "output_endogenous_fuelcosts.csv"

    # Output to a temporary location first
    output_base_path = script_dir

    print(f"\nBase case: {base_case_path}")
    print(f"GENeSYS data: {genesys_data_path}")
    print(f"Output: {output_base_path / 'input_data' / 'uncertainty_scenarios_rail'}")

    # Run the pipeline
    result = run_genesys_pipeline(
        base_case_path=base_case_path,
        genesys_data_path=genesys_data_path,
        output_base_path=output_base_path,
        design='factorial',
        charging_markups=[0.15, 0.30],
        tech_multipliers=[0.7, 1.0, 1.3],
        run_model=False  # Don't run model, just create scenarios
    )

    # Rename output folder to uncertainty_scenarios_rail
    default_output = output_base_path / "input_data" / "uncertainty_scenarios"
    rail_output = output_base_path / "input_data" / "uncertainty_scenarios_rail"

    # Remove old rail scenarios if they exist
    if rail_output.exists():
        print(f"\nRemoving old rail scenarios: {rail_output}")
        shutil.rmtree(rail_output)

    if default_output.exists():
        # Move the generated scenarios to rail folder
        shutil.move(str(default_output), str(rail_output))
        print(f"\n[OK] Scenarios moved to: {rail_output}")

    return result


def main():
    """Main entry point - Full regeneration method."""
    import argparse

    parser = argparse.ArgumentParser(description='Create rail uncertainty scenarios')
    parser.add_argument('--skip-base', action='store_true',
                       help='Skip base case generation (use existing rail base case)')
    parser.add_argument('--base-case', type=Path, default=None,
                       help='Path to existing rail base case (requires --skip-base)')

    args = parser.parse_args()

    if args.skip_base:
        if args.base_case is None:
            # Find the most recent rail base case
            input_data_dir = script_dir / "input_data"
            rail_bases = sorted([
                d for d in input_data_dir.iterdir()
                if d.is_dir() and 'rail_base' in d.name
            ], key=lambda x: x.name, reverse=True)

            if not rail_bases:
                print("ERROR: No existing rail base case found. Run without --skip-base first.")
                return
            base_case = rail_bases[0]
            print(f"Using most recent rail base case: {base_case}")
        else:
            base_case = args.base_case
    else:
        # Full regeneration - create base case first
        base_case = step1_create_rail_base_case()

    # Create the 24 uncertainty scenarios
    step2_create_uncertainty_scenarios(base_case)

    print("\n" + "=" * 70)
    print("RAIL UNCERTAINTY SCENARIOS COMPLETE")
    print("=" * 70)
    print(f"\nScenarios created in: {script_dir / 'input_data' / 'uncertainty_scenarios_rail'}")
    print("\nTo run the optimization:")
    print("  julia SM_batch_rail_uncertainty.jl")


if __name__ == "__main__":
    main()
