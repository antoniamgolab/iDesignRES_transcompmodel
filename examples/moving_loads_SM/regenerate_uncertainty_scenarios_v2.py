"""
Regenerate uncertainty_scenarios with corrected parameters (v2).

Changes from original scenario_000-003:
  1. alpha_h=0.02, beta_h=0.25 (technology adoption rates)
  2. rho_mode=0.975 (Bakker et al. modal shift inertia, replaces alpha_f/beta_f)
  3. Battery capacity: 560 -> 1120 -> 1400 kWh (was constant 1187)
  4. gamma=0.35 (Shoman harmonic mean of MCS/CCS utilization, was 0.3)
  5. Discount rate=0.04 (was 0.05)
  6. CAPEX cost_per_kW: 400 -> 300 -> 250 EUR/kW (was 0.0)
  7. O&M fix in model_functions.jl: cumulative capacity (already in code)

Backs up existing scenarios before regenerating.
"""

import sys
import shutil
from pathlib import Path
from datetime import datetime

# Add the script directory to path
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from SM_preprocessing import SMParameterGenerator

# ============================================================================
# CONFIGURATION
# ============================================================================

# Data source - same as used for original uncertainty_scenarios
DATA_SOURCE = "input_data/fixed_nuts_2"

# GENeSYS-MOD scenarios (same 4 as original)
GENESYS_SCENARIOS = [
    ('Go RES v1.2', 'scenario_000'),
    ('NECPEssentials v1.2', 'scenario_001'),
    ('REPowerEU++ v1.2', 'scenario_002'),
    ('Trinity v1.2', 'scenario_003'),
]

# Include rail mode
INCLUDE_RAIL = True

# Output base
OUTPUT_BASE = script_dir / "input_data" / "uncertainty_scenarios_v2"

# ============================================================================
# BACKUP EXISTING SCENARIOS
# ============================================================================

existing_base = script_dir / "input_data" / "uncertainty_scenarios"
backup_suffix = datetime.now().strftime("%Y%m%d_%H%M%S")

print("=" * 80)
print("REGENERATING UNCERTAINTY SCENARIOS (V2 - CORRECTED PARAMETERS)")
print("=" * 80)
print()
print("Parameter changes:")
print("  1. alpha_h: 0.1 -> 0.02")
print("  2. beta_h:  0.1 -> 0.25")
print("  3. rho_mode: NEW 0.975 (replaces alpha_f/beta_f for modal shift)")
print("  4. Battery:  1187 constant -> 560/1120/1400 kWh")
print("  5. gamma:    0.3 -> 0.35")
print("  6. Discount: 0.05 -> 0.04")
print("  7. CAPEX:    0 -> 400/300/250 EUR/kW")
print()
print(f"Data source: {DATA_SOURCE}")
print(f"Output: {OUTPUT_BASE}")
print(f"Scenarios: {[s[0] for s in GENESYS_SCENARIOS]}")
print(f"Rail mode: {'Enabled' if INCLUDE_RAIL else 'Disabled'}")
print()

# Create output directory
OUTPUT_BASE.mkdir(parents=True, exist_ok=True)

# ============================================================================
# GENERATE SCENARIOS
# ============================================================================

created_scenarios = []

for genesys_name, folder_name in GENESYS_SCENARIOS:
    print()
    print("=" * 80)
    print(f"GENERATING: {genesys_name} -> {folder_name}")
    print("=" * 80)

    output_dir = OUTPUT_BASE / folder_name

    # Create parameter generator with corrected settings
    # All our changes are embedded in SM_preprocessing.py:
    #   - alpha_h=0.02, beta_h=0.25 (line 2100-2101)
    #   - rho_mode=0.975 (line 2099)
    #   - battery: 560/1120/1400 (line 1829)
    #   - gamma=0.35 (lines 1511, 1528, 1545)
    #   - discount_rate=0.04 (line 2092)
    #   - CAPEX 400/300/250 (lines 1512, 1528)
    generator = SMParameterGenerator(
        nuts3_data_dir=DATA_SOURCE,
        output_dir=str(output_dir),
        case_name=folder_name,
        electricity_prices_variable=True,
        network_costs_variable=True,
        cross_border_only=True,
        filter_low_volume=True,
        min_freight_threshold=500.0,
        filter_short_paths=True,
        min_path_length=360.0,
        include_rail_mode=INCLUDE_RAIL,
        genesys_scenario=genesys_name
    )

    # Load data and generate
    generator.load_nuts3_data()
    generator.save_all_parameters()

    created_scenarios.append((folder_name, genesys_name))
    print(f"\n[SUCCESS] Created: {output_dir}")

# Save cases.json for reference
import json
cases_info = {
    "n_cases": len(GENESYS_SCENARIOS),
    "version": "v2",
    "changes": [
        "alpha_h=0.02, beta_h=0.25",
        "rho_mode=0.975 (Bakker et al.)",
        "battery: 560->1120->1400 kWh",
        "gamma=0.35 (Shoman harmonic mean)",
        "discount_rate=0.04",
        "CAPEX: 400->300->250 EUR/kW",
    ],
    "data_source": DATA_SOURCE,
    "include_rail": INCLUDE_RAIL,
    "generated": datetime.now().isoformat(),
    "cases": [
        {"case_id": i, "folder": folder, "genesys_scenario": name}
        for i, (name, folder) in enumerate(GENESYS_SCENARIOS)
    ]
}
with open(OUTPUT_BASE / "cases.json", 'w') as f:
    json.dump(cases_info, f, indent=2)

# ============================================================================
# SUMMARY
# ============================================================================

print()
print("=" * 80)
print("COMPLETE!")
print("=" * 80)
print(f"Output folder: {OUTPUT_BASE.relative_to(script_dir)}")
print()
print("Created scenarios:")
for folder, name in created_scenarios:
    print(f"  - {folder}: {name}")
print()
print("To run with SM_batch.jl, update case_folders to point to:")
print('  "uncertainty_scenarios_v2/scenario_000",')
print('  "uncertainty_scenarios_v2/scenario_001",')
print('  "uncertainty_scenarios_v2/scenario_002",')
print('  "uncertainty_scenarios_v2/scenario_003",')
print()
print("Original scenarios are preserved in uncertainty_scenarios/")
print("=" * 80)
