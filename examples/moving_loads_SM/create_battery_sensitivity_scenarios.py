"""
Create battery capacity sensitivity scenarios.

Copies scenario_000 input data and modifies TechVehicle.yaml with different
BEV battery capacity trajectories to assess sensitivity of results.

Scenarios:
  - bat_constant_1187: Current assumption (constant 1187 kWh) - baseline
  - bat_low_400_800:   Conservative growth (400 → 800 → 1000 kWh)
  - bat_mid_400_1000:  Mid growth (400 → 1000 → 1200 kWh)
  - bat_high_600_1200: Optimistic growth (600 → 1200 → 1500 kWh)
"""

import yaml
import shutil
from pathlib import Path
import numpy as np

BASE = Path(__file__).resolve().parent
SOURCE = BASE / "input_data" / "uncertainty_scenarios" / "scenario_000"
OUTPUT_DIR = BASE / "input_data" / "battery_sensitivity"

# Battery capacity scenarios: {name: {2020: kWh, 2035: kWh, 2050: kWh}}
# These anchor points get linearly interpolated across all 53 generations (2008-2060)
SCENARIOS = {
    "bat_constant_1187": {2020: 1187, 2035: 1187, 2050: 1187},   # current (baseline)
    "bat_low_400_800":   {2020: 400,  2035: 800,  2050: 1000},   # conservative
    "bat_mid_400_1000":  {2020: 400,  2035: 1000, 2050: 1200},   # mid
    "bat_high_600_1200": {2020: 600,  2035: 1200, 2050: 1500},   # optimistic
}


def interpolate_battery_capacity(anchors: dict, years: list) -> list:
    """Linearly interpolate/extrapolate battery capacity for generation years."""
    known_years = sorted(anchors.keys())
    known_vals = [anchors[y] for y in known_years]
    return list(np.interp(years, known_years, known_vals))


def create_scenario(name: str, bev_anchors: dict):
    """Copy scenario_000 and modify BEV tank_capacity in TechVehicle.yaml."""
    dest = OUTPUT_DIR / name

    if dest.exists():
        shutil.rmtree(dest)

    # Copy all files from scenario_000
    shutil.copytree(SOURCE, dest)

    # Read TechVehicle.yaml
    tv_path = dest / "TechVehicle.yaml"
    with open(tv_path) as f:
        tech_vehicles = yaml.safe_load(f)

    # Generation years: 53 elements from 2008 to 2060
    num_generations = len(tech_vehicles[0]["tank_capacity"])
    gen_years = list(range(2008, 2008 + num_generations))

    # Compute new battery capacities
    new_capacities = interpolate_battery_capacity(bev_anchors, gen_years)

    # Update BEV techvehicle (technology == 1)
    for tv in tech_vehicles:
        if tv["technology"] == 1:  # BEV
            old_caps = tv["tank_capacity"]
            tv["tank_capacity"] = [float(round(c, 1)) for c in new_capacities]
            print(f"  {name}: BEV tank_capacity updated")
            print(f"    Old: {old_caps[0]:.0f} (2008) -> {old_caps[12]:.0f} (2020) -> {old_caps[-1]:.0f} (2060)")
            print(f"    New: {new_capacities[0]:.0f} (2008) -> {new_capacities[12]:.0f} (2020) -> {new_capacities[-1]:.0f} (2060)")

    # Write updated TechVehicle.yaml
    with open(tv_path, "w") as f:
        yaml.dump(tech_vehicles, f, default_flow_style=False, allow_unicode=True)

    # Write metadata
    meta = {
        "base_scenario": "scenario_000 (Go RES v1.2)",
        "modification": "BEV battery capacity sensitivity",
        "bev_battery_anchors_kWh": bev_anchors,
        "description": f"Battery capacity: {bev_anchors}",
    }
    with open(dest / "case_metadata.yaml", "w") as f:
        yaml.dump(meta, f, default_flow_style=False)

    print(f"  -> Created: {dest}")


if __name__ == "__main__":
    print(f"Source: {SOURCE}")
    print(f"Output: {OUTPUT_DIR}")
    print(f"Source exists: {SOURCE.exists()}")
    print()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for name, anchors in SCENARIOS.items():
        print(f"\nCreating scenario: {name}")
        create_scenario(name, anchors)

    print(f"\n{'='*60}")
    print(f"Created {len(SCENARIOS)} battery sensitivity scenarios")
    print(f"Ready to run with SM_batch_battery_sensitivity.jl")
