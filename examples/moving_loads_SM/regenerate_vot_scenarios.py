"""
Regenerate VoT Sensitivity Scenarios with Broken Paths Filter
==============================================================

This script:
1. Generates a new base case using SM_preprocessing.py with the broken paths filter
2. Creates VoT sensitivity scenarios from that base case

The broken paths filter (added Jan 2025) excludes ~412 paths (0.69% of freight)
that failed E-road routing and only have origin + destination regions.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add the script directory to path
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from SM_preprocessing import SMParameterGenerator
from create_vot_sensitivity_scenarios import create_vot_scenarios

# ============================================================================
# CONFIGURATION
# ============================================================================

# Data source: fixed_international_nuts_2 (100% international routes with fixed distances)
DATA_SOURCE = "input_data/fixed_international_nuts_2"

# Case name for the new base case
BASE_CASE_NAME = f"case_{datetime.now().strftime('%Y%m%d_%H%M%S')}_base_filtered"

# VoT values to test (EUR/hour)
VOT_VALUES = [10, 20, 30, 45, 60]

# ============================================================================
# STEP 1: Generate base case with broken paths filter
# ============================================================================

print("=" * 80)
print("STEP 1: GENERATING BASE CASE WITH BROKEN PATHS FILTER")
print("=" * 80)
print(f"Data source: {DATA_SOURCE}")
print(f"Base case name: {BASE_CASE_NAME}")
print()

# Create parameter generator with the fixed international NUTS2 data
generator = SMParameterGenerator(
    nuts3_data_dir=DATA_SOURCE,
    case_name=BASE_CASE_NAME,
    electricity_prices_variable=True,
    network_costs_variable=True,
    cross_border_only=True,  # Only international routes
    filter_low_volume=True,
    min_freight_threshold=500.0,
    filter_short_paths=True,
    min_path_length=360.0,
    genesys_scenario='Go RES v1.2'
)

# Load data (this applies all filters including broken paths)
generator.load_nuts3_data()

# Generate all parameter files
generator.save_all_parameters()

print()
print(f"[SUCCESS] Base case generated: {generator.output_dir}")
print()

# ============================================================================
# STEP 2: Create VoT sensitivity scenarios
# ============================================================================

print("=" * 80)
print("STEP 2: CREATING VOT SENSITIVITY SCENARIOS")
print("=" * 80)

# Create VoT scenarios from the new base case
created_scenarios = create_vot_scenarios(
    base_case_name=BASE_CASE_NAME,
    vot_values=VOT_VALUES,
    output_folder="vot_sensitivity"
)

print()
print("=" * 80)
print("COMPLETE!")
print("=" * 80)
print(f"Base case: input_data/{BASE_CASE_NAME}")
print(f"VoT scenarios created in: input_data/vot_sensitivity/")
print()
print("Created scenarios:")
for scenario in created_scenarios:
    print(f"  - {scenario}")
print()
print("Next step: Run the Julia batch script:")
print("  julia SM_batch_vot_sensitivity.jl")
print("=" * 80)
