"""
Create battery capacity sensitivity scenarios by scaling the BEV tank_capacity
and peak_fueling arrays in TechVehicle.yaml around the current scenario_000 baseline.

Baseline (per build year, linear from 2008):
    2020: 560 kWh    2035: 1120 kWh    2050: 1400 kWh    2060: 1587 kWh

Sweep: symmetric +/-30%
    bat_low_70pct:   x0.70  -> 2020: 392,  2035:  784,  2050:  980 kWh
    bat_baseline:    x1.00  -> 2020: 560,  2035: 1120,  2050: 1400 kWh
    bat_high_130pct: x1.30  -> 2020: 728,  2035: 1456,  2050: 1820 kWh

peak_fueling (kW) is scaled by the same factor so charging time stays roughly
constant across the sweep (bigger battery -> bigger pack -> higher peak rate).

OVERWRITES input_data/battery_sensitivity/ with the three new folders.
"""
import shutil
from pathlib import Path
import yaml

BASE = Path(__file__).resolve().parent
SRC_FOLDER = BASE / "input_data" / "uncertainty_scenarios_v2" / "scenario_000"
OUT_ROOT = BASE / "input_data" / "battery_sensitivity"

SCENARIOS = [
    ("bat_low_70pct",  0.70, "Low: -30% (392 / 784 / 980 kWh at 2020 / 2035 / 2050)"),
    ("bat_baseline",   1.00, "Baseline: 560 / 1120 / 1400 kWh at 2020 / 2035 / 2050"),
    ("bat_high_130pct", 1.30, "High: +30% (728 / 1456 / 1820 kWh at 2020 / 2035 / 2050)"),
]

BEV_NAME = "BEV"  # TechVehicle name we scale


def scale_techvehicle(tv_data, factor):
    """Return new TechVehicle list with BEV tank_capacity and peak_fueling scaled."""
    out = []
    for tv in tv_data:
        if tv.get("name") == BEV_NAME and tv.get("vehicle_type") == "long-haul truck":
            tv = dict(tv)
            tv["tank_capacity"] = [v * factor for v in tv["tank_capacity"]]
            tv["peak_fueling"] = [v * factor for v in tv["peak_fueling"]]
        out.append(tv)
    return out


def main():
    if not SRC_FOLDER.is_dir():
        raise FileNotFoundError(f"Source folder not found: {SRC_FOLDER}")

    # Wipe and recreate the output root
    if OUT_ROOT.exists():
        print(f"Removing existing {OUT_ROOT}...")
        shutil.rmtree(OUT_ROOT)
    OUT_ROOT.mkdir(parents=True)

    # Read the source TechVehicle.yaml once
    tv_path = SRC_FOLDER / "TechVehicle.yaml"
    with open(tv_path) as f:
        tv_data = yaml.safe_load(f)

    # Show baseline values for reference
    for tv in tv_data:
        if tv.get("name") == BEV_NAME and tv.get("vehicle_type") == "long-haul truck":
            tc = tv["tank_capacity"]
            print(f"Baseline BEV tank_capacity[gen 13={2020}] = {tc[12]:.1f} kWh "
                  f"(2008-build): {tc[0]:.1f}, (2035-build): {tc[27]:.1f}, "
                  f"(2050-build): {tc[42]:.1f}")
            break

    for folder_name, factor, description in SCENARIOS:
        dst = OUT_ROOT / folder_name
        print(f"\nCreating {folder_name} (factor={factor}) ...")

        # Copy ALL files from the source scenario
        shutil.copytree(SRC_FOLDER, dst)

        # Overwrite TechVehicle.yaml with scaled values
        scaled_tv = scale_techvehicle(tv_data, factor)
        with open(dst / "TechVehicle.yaml", "w") as f:
            yaml.safe_dump(scaled_tv, f, sort_keys=False)

        # Write metadata
        anchors = {}
        for tv in scaled_tv:
            if tv.get("name") == BEV_NAME and tv.get("vehicle_type") == "long-haul truck":
                tc = tv["tank_capacity"]
                anchors = {2020: tc[12], 2035: tc[27], 2050: tc[42]}
                break
        with open(dst / "case_metadata.yaml", "w") as f:
            yaml.safe_dump({
                "base_scenario": "scenario_000 (Go RES, uncertainty_scenarios_v2)",
                "modification": "BEV tank_capacity AND peak_fueling scaled by factor",
                "factor": factor,
                "description": description,
                "bev_tank_capacity_kwh_anchors": {y: round(v, 1) for y, v in anchors.items()},
            }, f, sort_keys=False)
        print(f"  -> 2020-build: {anchors.get(2020, 0):.1f} kWh, "
              f"2035-build: {anchors.get(2035, 0):.1f} kWh, "
              f"2050-build: {anchors.get(2050, 0):.1f} kWh")

    print(f"\nDone. Three folders written under {OUT_ROOT}")


if __name__ == "__main__":
    main()
