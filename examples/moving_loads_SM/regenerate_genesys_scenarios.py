"""
Regenerate GENeSYS-MOD Scenarios with Broken Paths Filter
==========================================================

This script generates 4 scenarios with different GENeSYS-MOD electricity price scenarios:
1. Go RES v1.2 - Most ambitious, highest electricity prices
2. NECPEssentials v1.2 - Moderate ambition
3. REPowerEU++ v1.2 - Self-sufficient EU
4. Trinity v1.2 - Lowest ambition, lowest electricity prices

The broken paths filter (added Jan 2025) excludes paths that failed E-road routing.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add the script directory to path
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from SM_preprocessing import SMParameterGenerator

# ============================================================================
# CONFIGURATION
# ============================================================================

# Data source: fixed_international_nuts_2 (100% international routes with fixed distances)
DATA_SOURCE = "input_data/fixed_international_nuts_2"

# GENeSYS-MOD scenarios
GENESYS_SCENARIOS = [
    ('Go RES v1.2', 'go_res'),
    ('NECPEssentials v1.2', 'necp'),
    ('REPowerEU++ v1.2', 'repower'),
    ('Trinity v1.2', 'trinity'),
]

# Output folder
OUTPUT_FOLDER = "genesys_scenarios"

# ============================================================================
# GENERATE SCENARIOS
# ============================================================================

print("=" * 80)
print("GENERATING GENESYS-MOD ELECTRICITY PRICE SCENARIOS")
print("=" * 80)
print(f"Data source: {DATA_SOURCE}")
print(f"Scenarios: {[s[0] for s in GENESYS_SCENARIOS]}")
print()

output_base = script_dir / "input_data" / OUTPUT_FOLDER
output_base.mkdir(parents=True, exist_ok=True)

created_scenarios = []

for genesys_name, folder_name in GENESYS_SCENARIOS:
    print()
    print("=" * 80)
    print(f"GENERATING: {genesys_name}")
    print("=" * 80)

    case_name = f"{folder_name}"
    output_dir = output_base / folder_name

    # Create parameter generator with this GENeSYS scenario
    generator = SMParameterGenerator(
        nuts3_data_dir=DATA_SOURCE,
        output_dir=str(output_dir),
        case_name=case_name,
        electricity_prices_variable=True,
        network_costs_variable=True,
        cross_border_only=True,
        filter_low_volume=True,
        min_freight_threshold=500.0,
        filter_short_paths=True,
        min_path_length=360.0,
        genesys_scenario=genesys_name
    )

    # Load data (applies all filters including broken paths)
    generator.load_nuts3_data()

    # Generate all parameter files
    generator.save_all_parameters()

    created_scenarios.append((folder_name, genesys_name))
    print(f"\n[SUCCESS] Created: {output_dir}")

# ============================================================================
# SUMMARY
# ============================================================================

print()
print("=" * 80)
print("COMPLETE!")
print("=" * 80)
print(f"Output folder: input_data/{OUTPUT_FOLDER}/")
print()
print("Created scenarios:")
for folder, name in created_scenarios:
    print(f"  - {folder}: {name}")
print()
print("Next step: Run the Julia batch script:")
print("  julia SM_batch_genesys.jl")
print("=" * 80)
