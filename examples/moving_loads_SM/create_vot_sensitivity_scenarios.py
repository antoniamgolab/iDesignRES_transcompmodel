"""
Create VoT (Value of Time) Sensitivity Scenarios
=================================================

This script creates multiple scenarios with different Value of Time (VoT) values
for sensitivity analysis.

VoT values based on literature review:
- 10 EUR/hour: Low estimate (older studies, developing regions)
- 20 EUR/hour: Lower bound of modern estimates
- 30 EUR/hour: Baseline (current model value, consistent with Eurostat/ICCT)
- 45 EUR/hour: Higher estimate (reflects driver wages + opportunity cost)
- 60 EUR/hour: Upper bound (premium freight, time-critical deliveries)

Reference: Frey et al. (2022), ICCT reports, Eurostat transport statistics
"""

import yaml
import shutil
from pathlib import Path
from typing import List


# VoT values to test (EUR/hour)
VOT_VALUES = [10, 20, 30, 45, 60]

# Default base case - uses a recent complete case
DEFAULT_BASE_CASE = "case_20251212_095040"


def create_vot_scenarios(
    base_case_name: str = DEFAULT_BASE_CASE,
    vot_values: List[int] = VOT_VALUES,
    output_folder: str = "vot_sensitivity"
) -> List[str]:
    """
    Create VoT sensitivity scenarios by copying base case and modifying VoT.

    Parameters:
    -----------
    base_case_name : str
        Name of the base case folder in input_data/
    vot_values : List[int]
        List of VoT values to test
    output_folder : str
        Name of output folder under input_data/

    Returns:
    --------
    List[str]
        List of created scenario folder names
    """
    script_dir = Path(__file__).parent
    input_data_dir = script_dir / "input_data"
    base_case_path = input_data_dir / base_case_name
    output_base = input_data_dir / output_folder

    # Validate base case exists
    if not base_case_path.exists():
        raise ValueError(f"Base case not found: {base_case_path}")

    # Create output folder
    output_base.mkdir(parents=True, exist_ok=True)

    created_scenarios = []

    print("=" * 80)
    print("CREATING VOT SENSITIVITY SCENARIOS")
    print("=" * 80)
    print(f"Base case: {base_case_name}")
    print(f"VoT values: {vot_values} EUR/hour")
    print(f"Output: {output_base}")
    print()

    for vot in vot_values:
        scenario_name = f"vot_{vot:02d}"
        scenario_path = output_base / scenario_name

        print(f"Creating scenario: {scenario_name} (VoT = {vot} EUR/hour)...")

        # Copy all files from base case
        if scenario_path.exists():
            shutil.rmtree(scenario_path)
        shutil.copytree(base_case_path, scenario_path)

        # Modify FinancialStatus.yaml
        fs_path = scenario_path / "FinancialStatus.yaml"
        if fs_path.exists():
            with open(fs_path, 'r') as f:
                financial_status = yaml.safe_load(f)

            # Update VoT value
            for fs in financial_status:
                fs['VoT'] = vot

            with open(fs_path, 'w') as f:
                yaml.dump(financial_status, f, default_flow_style=False, allow_unicode=True)

            print(f"  Updated FinancialStatus.yaml: VoT = {vot}")
        else:
            print(f"  [WARN] FinancialStatus.yaml not found in {scenario_path}")

        created_scenarios.append(scenario_name)

    # Create scenarios.json for tracking
    scenarios_json = {
        "base_case": base_case_name,
        "parameter": "VoT",
        "unit": "EUR/hour",
        "scenarios": {
            name: {"vot": vot}
            for name, vot in zip(created_scenarios, vot_values)
        }
    }

    import json
    with open(output_base / "scenarios.json", 'w') as f:
        json.dump(scenarios_json, f, indent=2)

    print()
    print("=" * 80)
    print(f"Created {len(created_scenarios)} VoT sensitivity scenarios:")
    for name, vot in zip(created_scenarios, vot_values):
        print(f"  {name}: VoT = {vot} EUR/hour")
    print()
    print(f"Scenarios saved to: {output_base}")
    print(f"Run with: julia SM_batch_vot_sensitivity.jl")
    print("=" * 80)

    return created_scenarios


if __name__ == "__main__":
    import sys

    # Parse command line arguments
    base_case = DEFAULT_BASE_CASE
    if len(sys.argv) > 1:
        base_case = sys.argv[1]

    # Create scenarios
    create_vot_scenarios(base_case_name=base_case)
