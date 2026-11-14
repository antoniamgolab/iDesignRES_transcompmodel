"""
Patch v2 scenarios to add rail mode.

Copies uncertainty_scenarios_v2 to uncertainty_scenarios_v2_rail,
then adds rail to Mode.yaml, creates InitialModeInfr.yaml, and MaxModeShare.yaml.
All other files remain identical.
"""

import shutil
import yaml
import json
from pathlib import Path
from datetime import datetime

script_dir = Path(__file__).parent

OLD_BASE = script_dir / "input_data" / "uncertainty_scenarios_v2"
NEW_BASE = script_dir / "input_data" / "uncertainty_scenarios_v2_rail"

SCENARIOS = ["scenario_000", "scenario_001", "scenario_002", "scenario_003"]

NUM_YEARS = 41  # 2020-2060

# Rail parameters from manuscript / SM_preprocessing.py
RAIL_COST_PER_TKM = 0.06  # EUR/tkm (updated from main_v2.pdf)
RAIL_TERMINAL_COST = 4.0   # EUR/tonne (updated from main_v2.pdf)
MAX_RAIL_SHARE = 0.30       # 30% cap

print("=" * 80)
print("PATCHING SCENARIOS: Add rail mode")
print("=" * 80)

for scenario in SCENARIOS:
    old_dir = OLD_BASE / scenario
    new_dir = NEW_BASE / scenario

    if not old_dir.exists():
        print(f"  SKIP: {old_dir} not found")
        continue

    print(f"\n--- {scenario} ---")

    # Copy entire directory
    if new_dir.exists():
        shutil.rmtree(new_dir)
    shutil.copytree(old_dir, new_dir)
    print(f"  Copied {old_dir.name} -> {new_dir.name}")

    # 1. Patch Mode.yaml: add rail mode
    mode_path = new_dir / "Mode.yaml"
    with open(mode_path) as f:
        modes = yaml.safe_load(f)

    # Add rail mode (id=2)
    rail_mode = {
        'id': 2,
        'name': 'rail',
        'quantify_by_vehs': False,
        'costs_per_ukm': [RAIL_COST_PER_TKM] * NUM_YEARS,
        'emission_factor': [0] * NUM_YEARS,  # electrified rail
        'infrastructure_expansion_costs': [0.0] * NUM_YEARS,
        'infrastructure_om_costs': [0.1] * NUM_YEARS,
        'waiting_time': [0.0] * NUM_YEARS,
        'terminal_cost_per_tonne': [RAIL_TERMINAL_COST] * NUM_YEARS,
    }

    # Check if rail already exists
    if not any(m['id'] == 2 for m in modes):
        modes.append(rail_mode)

    with open(mode_path, 'w') as f:
        yaml.dump(modes, f, default_flow_style=False, sort_keys=False)
    print(f"  Mode.yaml: added rail (cost={RAIL_COST_PER_TKM} EUR/tkm, terminal={RAIL_TERMINAL_COST} EUR/t)")

    # 2. Create/update InitialModeInfr.yaml
    # Load geographic elements to create entries for all nodes
    with open(new_dir / "GeographicElement.yaml") as f:
        geo_data = yaml.safe_load(f)

    init_mode_infr = []
    infr_id = 0
    for geo in geo_data:
        if geo.get('type') == 'node':
            # Road (mode 1): large initial capacity
            init_mode_infr.append({
                'id': infr_id,
                'mode': 1,
                'allocation': geo['id'],
                'installed_ukm': 1e12,  # effectively unlimited road capacity
            })
            infr_id += 1
            # Rail (mode 2): zero initial capacity (must be built)
            init_mode_infr.append({
                'id': infr_id,
                'mode': 2,
                'allocation': geo['id'],
                'installed_ukm': 0.0,
            })
            infr_id += 1

    with open(new_dir / "InitialModeInfr.yaml", 'w') as f:
        yaml.dump(init_mode_infr, f, default_flow_style=False, sort_keys=False)
    print(f"  InitialModeInfr.yaml: {len(init_mode_infr)} entries ({infr_id//2} nodes x 2 modes)")

    # 3. Create MaxModeShare.yaml (30% rail cap)
    time_step = 4
    modeled_years = list(range(2020, 2061, time_step))
    max_mode_share = []
    for idx, year in enumerate(modeled_years):
        max_mode_share.append({
            'id': idx,
            'year': year,
            'mode': 2,
            'share': MAX_RAIL_SHARE,
        })

    with open(new_dir / "MaxModeShare.yaml", 'w') as f:
        yaml.dump(max_mode_share, f, default_flow_style=False, sort_keys=False)
    print(f"  MaxModeShare.yaml: {len(max_mode_share)} entries (rail max {MAX_RAIL_SHARE*100:.0f}%)")

# Save metadata
meta = {
    "version": "v2_rail",
    "created": datetime.now().isoformat(),
    "base": "uncertainty_scenarios_v2 (road-only with v2 parameter corrections)",
    "changes": {
        "Mode.yaml": f"Added rail mode (id=2, cost={RAIL_COST_PER_TKM} EUR/tkm, terminal={RAIL_TERMINAL_COST} EUR/t)",
        "InitialModeInfr.yaml": "Created with zero initial rail capacity",
        "MaxModeShare.yaml": f"Rail capped at {MAX_RAIL_SHARE*100:.0f}%",
    },
}
NEW_BASE.mkdir(parents=True, exist_ok=True)
with open(NEW_BASE / "patch_info.json", 'w') as f:
    json.dump(meta, f, indent=2)

print("\n" + "=" * 80)
print("COMPLETE!")
print("=" * 80)
print(f"Output: {NEW_BASE.relative_to(script_dir)}")
print(f"To run: update SM_batch.jl case_folders to uncertainty_scenarios_v2_rail/")
print(f"Enable constraint_mode_shift and constraint_max_mode_share in SM_batch.jl")
print("=" * 80)
