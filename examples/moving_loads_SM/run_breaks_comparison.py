"""
Generate Mandatory Breaks vs No-Breaks Comparison Scenarios
===========================================================

Creates two scenario sets for comparison:
1. WITH mandatory breaks constraint - charging only at break locations
2. WITHOUT mandatory breaks constraint - charging allowed anywhere

Uses Go RES v1.2 scenario as the base (highest carbon price = most BEV adoption)
"""

import sys
import shutil
from pathlib import Path
from datetime import datetime

script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))
sys.path.insert(0, str(script_dir / "uncertainty_analysis"))

from SM_preprocessing import SMParameterGenerator

# ============================================================================
# CONFIGURATION
# ============================================================================

DATA_SOURCE = "input_data/fixed_international_nuts_2"
OUTPUT_BASE = script_dir / "input_data" / "breaks_comparison"
GENESYS_SCENARIO = "Go RES v1.2"  # Use highest carbon price scenario

# Thresholds matching the GENeSYS scenarios
VOLUME_THRESHOLD = 100.0  # trucks/year
MIN_PATH_LENGTH = 360.0   # km
CHARGING_MARKUP = 0.30    # 30%

# ============================================================================
# GENERATE BASE SCENARIO
# ============================================================================

print("=" * 80)
print("MANDATORY BREAKS COMPARISON ANALYSIS")
print("=" * 80)
print(f"Data source: {DATA_SOURCE}")
print(f"GENeSYS scenario: {GENESYS_SCENARIO}")
print(f"Volume threshold: {VOLUME_THRESHOLD} trucks/year")
print(f"Charging markup: {CHARGING_MARKUP*100:.0f}%")
print()

OUTPUT_BASE.mkdir(parents=True, exist_ok=True)

# Create two scenarios: with_breaks and without_breaks
scenarios = [
    ("with_breaks", True),
    ("without_breaks", False)
]

for scenario_name, include_breaks in scenarios:
    print()
    print("=" * 80)
    print(f"GENERATING: {scenario_name}")
    print("=" * 80)

    output_dir = OUTPUT_BASE / scenario_name

    # Create parameter generator
    generator = SMParameterGenerator(
        nuts3_data_dir=DATA_SOURCE,
        output_dir=str(output_dir),
        case_name=scenario_name,
        electricity_prices_variable=True,
        network_costs_variable=True,
        cross_border_only=True,
        filter_low_volume=True,
        min_freight_threshold=VOLUME_THRESHOLD,
        filter_short_paths=True,
        min_path_length=MIN_PATH_LENGTH,
        genesys_scenario=GENESYS_SCENARIO
    )

    # Load data
    generator.load_nuts3_data()

    # Generate all parameter files
    generator.save_all_parameters()

    # For "without_breaks" scenario, we need to modify MandatoryBreaks.yaml
    # to have no breaks (empty list)
    if not include_breaks:
        breaks_file = output_dir / "MandatoryBreaks.yaml"
        if breaks_file.exists():
            # Write empty mandatory breaks file (just an empty list)
            with open(breaks_file, 'w') as f:
                f.write("[]\n")
            print(f"  -> Cleared MandatoryBreaks.yaml (charging anywhere)")

    print(f"\n[SUCCESS] Created: {output_dir}")

# ============================================================================
# APPLY CARBON PRICES (same as GENeSYS pipeline)
# ============================================================================

print()
print("=" * 80)
print("APPLYING CARBON PRICES")
print("=" * 80)

# Carbon price trajectory for Go RES v1.2
CARBON_PRICES = {
    2020: 30, 2024: 73, 2028: 115, 2032: 158, 2036: 329,
    2040: 500, 2044: 625, 2048: 750, 2052: 875, 2056: 1000, 2060: 1000
}

for scenario_name, _ in scenarios:
    output_dir = OUTPUT_BASE / scenario_name
    geo_file = output_dir / "GeographicElement.yaml"

    if geo_file.exists():
        import yaml
        with open(geo_file, 'r') as f:
            geo_data = yaml.safe_load(f)

        # Add carbon prices to each geographic element
        if 'geographic_element' in geo_data:
            for elem in geo_data['geographic_element']:
                elem['carbon_price'] = CARBON_PRICES

        with open(geo_file, 'w') as f:
            yaml.dump(geo_data, f, default_flow_style=False, sort_keys=False)

        print(f"  -> Applied carbon prices to {scenario_name}")

# ============================================================================
# SUMMARY
# ============================================================================

print()
print("=" * 80)
print("COMPLETE!")
print("=" * 80)
print(f"Output folder: input_data/breaks_comparison/")
print()
print("Created scenarios:")
print("  - with_breaks: Charging ONLY at mandatory break locations")
print("  - without_breaks: Charging allowed ANYWHERE along route")
print()
print("Next step: Run the Julia comparison script:")
print("  julia input_data/run_breaks_comparison.jl")
print("=" * 80)
