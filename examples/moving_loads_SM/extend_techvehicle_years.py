"""
Extend TechVehicle.yaml from 31 to 41 years
============================================

This script extends all year-dependent arrays in TechVehicle.yaml
by repeating the last value to reach 41 elements.

Author: Claude Code
Date: 2025-10-21
"""

import yaml
from pathlib import Path
import sys


def extend_techvehicle(input_file: Path, output_file: Path, target_length: int = 41):
    """
    Extend TechVehicle.yaml arrays to target length.

    Parameters:
    -----------
    input_file : Path
        Input TechVehicle.yaml file
    output_file : Path
        Output TechVehicle.yaml file
    target_length : int
        Target number of years (default: 41)
    """
    print(f"Loading {input_file}...")
    with open(input_file, 'r') as f:
        tech_vehicles = yaml.safe_load(f)

    # Arrays that need to be extended (year-dependent parameters)
    year_dependent_arrays = [
        'W',  # Vehicle capacity
        'AnnualRange',  # Annual mileage
        'spec_cons',  # Specific consumption
        'tank_capacity',  # Battery/tank capacity
        'peak_fueling',  # Charging power
        'capex',  # Capital expenditure
        'fix_opex',  # Fixed operational expenditure
        'var_opex',  # Variable operational expenditure
    ]

    print(f"\nExtending TechVehicle arrays from current length to {target_length} years...")

    for tv in tech_vehicles:
        tv_id = tv.get('id', 'unknown')

        for array_name in year_dependent_arrays:
            if array_name in tv:
                current_array = tv[array_name]
                current_length = len(current_array)

                if current_length < target_length:
                    # Extend by repeating the last value
                    last_value = current_array[-1]
                    extension = [last_value] * (target_length - current_length)
                    tv[array_name] = current_array + extension

                    if tv_id == 0:  # Only print for first TechVehicle to avoid spam
                        print(f"  Extended '{array_name}': {current_length} -> {target_length} elements")
                elif current_length > target_length:
                    print(f"  WARNING: TechVehicle {tv_id}, '{array_name}' has {current_length} elements (more than {target_length})")

    # Save extended data
    print(f"\nSaving to {output_file}...")
    with open(output_file, 'w') as f:
        yaml.dump(tech_vehicles, f, default_flow_style=False, sort_keys=False)

    print(f"\n✓ Successfully extended TechVehicle.yaml to {target_length} years!")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extend_techvehicle_years.py <case_directory> [target_years]")
        print("\nExample:")
        print("  python extend_techvehicle_years.py input_data/case_20251021_090315 41")
        sys.exit(1)

    case_dir = Path(sys.argv[1])
    target_years = int(sys.argv[2]) if len(sys.argv) > 2 else 41

    input_file = case_dir / "TechVehicle.yaml"

    if not input_file.exists():
        print(f"ERROR: {input_file} not found!")
        sys.exit(1)

    # Create backup
    backup_file = case_dir / "TechVehicle.yaml.backup"
    print(f"Creating backup: {backup_file}")
    import shutil
    shutil.copy2(input_file, backup_file)

    # Extend in place
    extend_techvehicle(input_file, input_file, target_years)

    print(f"\nBackup saved to: {backup_file}")
    print(f"TechVehicle.yaml updated in place: {input_file}")
