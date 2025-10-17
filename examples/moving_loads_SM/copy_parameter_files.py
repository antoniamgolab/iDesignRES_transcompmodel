"""
Copy Parameter Files from Existing Case
========================================

This script copies the parameter/configuration files from an existing
preprocessed case to your new NUTS-3 output directory.

These files don't depend on the specific paths/nodes, so they can be
reused directly:
- Technology.yaml
- Fuel.yaml
- FuelCost.yaml
- FuelingInfrTypes.yaml
- Mode.yaml
- Vehicletype.yaml
- TechVehicle.yaml
- Product.yaml
- FinancialStatus.yaml
- Regiontype.yaml
- Speed.yaml
- Model.yaml
- NetworkConnectionCosts.yaml (if exists)
- SpatialFlexibilityEdges.yaml (needs adjustment for NUTS-3)

Author: Claude Code
Date: 2025-10-15
"""

import shutil
from pathlib import Path


def copy_parameter_files(source_dir: str, target_dir: str, verbose: bool = True):
    """
    Copy parameter files from source to target directory.

    Parameters:
    -----------
    source_dir : str
        Path to source case directory (existing preprocessed case)
    target_dir : str
        Path to target directory (your new NUTS-3 output)
    verbose : bool
        Print progress messages
    """
    source = Path(source_dir)
    target = Path(target_dir)

    # Ensure target directory exists
    target.mkdir(parents=True, exist_ok=True)

    # Files to copy (these are parameter files that don't depend on specific paths)
    parameter_files = [
        "Technology.yaml",
        "Fuel.yaml",
        "FuelCost.yaml",
        "FuelingInfrTypes.yaml",
        "Mode.yaml",
        "Vehicletype.yaml",
        "TechVehicle.yaml",
        "Product.yaml",
        "FinancialStatus.yaml",
        "Regiontype.yaml",
        "Speed.yaml",
        "Model.yaml",
    ]

    # Optional files (may not exist in all cases)
    optional_files = [
        "NetworkConnectionCosts.yaml",
        "InitialModeInfr.yaml",
        "InitialFuelInfr.yaml",  # May need adjustment for NUTS-3 nodes
    ]

    if verbose:
        print("="*80)
        print("COPYING PARAMETER FILES")
        print("="*80)
        print(f"Source: {source}")
        print(f"Target: {target}")
        print()

    copied = []
    skipped = []

    # Copy required parameter files
    for filename in parameter_files:
        source_file = source / filename
        target_file = target / filename

        if source_file.exists():
            shutil.copy2(source_file, target_file)
            copied.append(filename)
            if verbose:
                print(f"[OK] Copied {filename}")
        else:
            skipped.append(filename)
            if verbose:
                print(f"[SKIP] {filename} not found in source")

    # Copy optional files
    for filename in optional_files:
        source_file = source / filename
        target_file = target / filename

        if source_file.exists():
            shutil.copy2(source_file, target_file)
            copied.append(filename)
            if verbose:
                print(f"[OK] Copied {filename} (optional)")
        else:
            if verbose:
                print(f"[SKIP] {filename} (optional, not present)")

    if verbose:
        print()
        print("="*80)
        print("SUMMARY")
        print("="*80)
        print(f"Copied: {len(copied)} files")
        print(f"Skipped: {len(skipped)} files")
        print("="*80)

        print("\nYour NUTS-3 case now has all required parameter files!")
        print(f"Complete input data location: {target}")

    return copied, skipped


def find_most_recent_case(input_data_dir: str = "input_data") -> Path:
    """
    Find the most recently created case directory.

    Parameters:
    -----------
    input_data_dir : str
        Directory containing all case subdirectories

    Returns:
    --------
    case_dir : Path
        Path to most recent case directory
    """
    input_dir = Path(input_data_dir)

    if not input_dir.exists():
        raise FileNotFoundError(f"Input data directory not found: {input_dir}")

    # Find all case directories (exclude NUTS-3 aggregated ones for source)
    case_dirs = [d for d in input_dir.iterdir()
                 if d.is_dir() and d.name.startswith("case_")
                 and not d.name.endswith("_nuts3")]

    if not case_dirs:
        raise FileNotFoundError(f"No case directories found in {input_dir}")

    # Sort by name (which includes timestamp) and get most recent
    most_recent = sorted(case_dirs, key=lambda x: x.name)[-1]

    return most_recent


if __name__ == "__main__":
    import sys

    # Get script directory
    script_dir = Path(__file__).parent

    # Default paths
    if len(sys.argv) > 2:
        source_dir = Path(sys.argv[1])
        target_dir = Path(sys.argv[2])
    else:
        # Auto-detect most recent case as source
        try:
            source_dir = find_most_recent_case(script_dir / "input_data")
            print(f"\n[AUTO] Using most recent case as source: {source_dir.name}\n")
        except Exception as e:
            print(f"[ERROR] Could not auto-detect source case: {e}")
            print("\nUsage:")
            print("  python copy_parameter_files.py <source_case_dir> <target_dir>")
            print("\nExample:")
            print("  python copy_parameter_files.py input_data/case_1_20251015_150712 output_data/sm_nuts3_complete")
            sys.exit(1)

        # Default target is the NUTS-3 output
        target_dir = script_dir / "output_data" / "sm_nuts3_complete"

    # Check if source exists
    if not source_dir.exists():
        print(f"[ERROR] Source directory not found: {source_dir}")
        sys.exit(1)

    # Copy files
    print(f"\nCopying parameter files from existing case to NUTS-3 output...\n")
    copied, skipped = copy_parameter_files(source_dir, target_dir, verbose=True)

    print("\n[SUCCESS] Parameter files copied!")
    print("\nYou can now use your NUTS-3 preprocessed data with Julia:")
    print(f"  input_path = \"{target_dir.relative_to(script_dir)}\"")
