"""
Patch existing uncertainty_scenarios to create v2 with corrected parameters.

Copies ALL files from scenario_000-003 (preserving OD pairs, paths, breaks, etc.)
then overwrites ONLY the files affected by the 7 parameter changes:
  1. Model.yaml: alpha_h=0.02, beta_h=0.25, rho_mode=0.975, discount_rate=0.04
  2. TechVehicle.yaml: battery capacity 560->1120->1400 kWh
  3. FuelingInfrTypes.yaml: gamma=0.35, CAPEX 400->300->250 EUR/kW
"""

import shutil
import yaml
import json
import numpy as np
from pathlib import Path
from datetime import datetime

script_dir = Path(__file__).parent

OLD_BASE = script_dir / "input_data" / "uncertainty_scenarios"
NEW_BASE = script_dir / "input_data" / "uncertainty_scenarios_v2"

SCENARIOS = ["scenario_000", "scenario_001", "scenario_002", "scenario_003"]

# ============================================================================
# Helper: linear interpolation (same as SM_preprocessing._extrapolate_years)
# ============================================================================
def extrapolate_years(known_values: dict, full_years: list) -> dict:
    known_years = sorted(known_values.keys())
    known_vals = [known_values[y] for y in known_years]
    result = {}
    for year in full_years:
        if year in known_values:
            result[year] = known_values[year]
        elif year < known_years[0]:
            slope = (known_vals[1] - known_vals[0]) / (known_years[1] - known_years[0])
            result[year] = known_vals[0] + slope * (year - known_years[0])
        elif year > known_years[-1]:
            slope = (known_vals[-1] - known_vals[-2]) / (known_years[-1] - known_years[-2])
            result[year] = known_vals[-1] + slope * (year - known_years[-1])
        else:
            for i in range(len(known_years) - 1):
                if known_years[i] <= year <= known_years[i + 1]:
                    frac = (year - known_years[i]) / (known_years[i + 1] - known_years[i])
                    result[year] = known_vals[i] + frac * (known_vals[i + 1] - known_vals[i])
                    break
    return result


print("=" * 80)
print("PATCHING SCENARIOS: uncertainty_scenarios -> uncertainty_scenarios_v2")
print("=" * 80)
print()
print("Changes applied:")
print("  1. Model.yaml: alpha_h=0.02, beta_h=0.25, rho_mode=0.975, discount_rate=0.04")
print("  2. TechVehicle.yaml: BEV battery 560->1120->1400 kWh")
print("  3. FuelingInfrTypes.yaml: gamma=0.35, CAPEX 400->300->250 EUR/kW")
print()

for scenario in SCENARIOS:
    old_dir = OLD_BASE / scenario
    new_dir = NEW_BASE / scenario

    if not old_dir.exists():
        print(f"  SKIP: {old_dir} not found")
        continue

    print(f"--- {scenario} ---")

    # Step 1: Copy entire directory
    if new_dir.exists():
        shutil.rmtree(new_dir)
    shutil.copytree(old_dir, new_dir)
    print(f"  Copied {old_dir} -> {new_dir}")

    # Step 2: Patch Model.yaml
    model_path = new_dir / "Model.yaml"
    with open(model_path) as f:
        model = yaml.safe_load(f)

    old_vals = {
        'alpha_h': model.get('alpha_h'),
        'beta_h': model.get('beta_h'),
        'discount_rate': model.get('discount_rate'),
        'rho_mode': model.get('rho_mode'),
    }

    model['alpha_h'] = 0.02
    model['beta_h'] = 0.25
    model['discount_rate'] = 0.04
    model['rho_mode'] = 0.975

    with open(model_path, 'w') as f:
        yaml.dump(model, f, default_flow_style=False, sort_keys=False)

    print(f"  Model.yaml: alpha_h {old_vals['alpha_h']}->{model['alpha_h']}, "
          f"beta_h {old_vals['beta_h']}->{model['beta_h']}, "
          f"discount {old_vals['discount_rate']}->{model['discount_rate']}, "
          f"rho_mode {old_vals['rho_mode']}->{model['rho_mode']}")

    # Step 3: Patch TechVehicle.yaml
    tv_path = new_dir / "TechVehicle.yaml"
    with open(tv_path) as f:
        tech_vehicles = yaml.safe_load(f)

    for tv in tech_vehicles:
        if tv['technology'] == 1:  # BEV
            old_cap = tv['tank_capacity'][0]
            n_gens = len(tv['tank_capacity'])
            gen_years = list(range(2008, 2008 + n_gens))

            # New battery trajectory: 560 (2020) -> 1120 (2035) -> 1400 (2050)
            new_caps_dict = extrapolate_years({2020: 560, 2035: 1120, 2050: 1400}, gen_years)
            new_caps = [float(round(new_caps_dict[y], 1)) for y in gen_years]
            tv['tank_capacity'] = new_caps

            print(f"  TechVehicle.yaml BEV: {old_cap} constant -> "
                  f"{new_caps[0]:.0f}(2008)/{new_caps[12]:.0f}(2020)/"
                  f"{new_caps[27]:.0f}(2035)/{new_caps[42]:.0f}(2050)")

    with open(tv_path, 'w') as f:
        yaml.dump(tech_vehicles, f, default_flow_style=False, sort_keys=False)

    # Step 4: Patch FuelingInfrTypes.yaml
    fit_path = new_dir / "FuelingInfrTypes.yaml"
    with open(fit_path) as f:
        fuel_infr = yaml.safe_load(f)

    years = list(range(2020, 2061))
    capex_trajectory = extrapolate_years({2020: 400, 2035: 300, 2050: 250}, years)
    capex_list = [float(round(capex_trajectory[y], 2)) for y in years]

    for fit in fuel_infr:
        if fit['fuel'] == 'electricity':
            old_gamma = fit['gamma'][0]
            old_capex = fit['cost_per_kW'][0]

            # Update gamma
            fit['gamma'] = [0.35] * len(fit['gamma'])

            # Update CAPEX - match length of existing cost_per_kW
            n = len(fit['cost_per_kW'])
            if n == len(capex_list):
                fit['cost_per_kW'] = capex_list
            else:
                # Interpolate to match length
                fit_years = list(range(2020, 2020 + n))
                fit_capex = extrapolate_years({2020: 400, 2035: 300, 2050: 250}, fit_years)
                fit['cost_per_kW'] = [float(round(fit_capex[y], 2)) for y in fit_years]

            print(f"  FuelingInfrTypes {fit['fueling_type']}: "
                  f"gamma {old_gamma}->{fit['gamma'][0]}, "
                  f"CAPEX {old_capex}->{fit['cost_per_kW'][0]}/{fit['cost_per_kW'][-1]}")
        elif fit['fuel'] == 'diesel':
            # Also update diesel gamma for consistency
            old_gamma = fit['gamma'][0]
            fit['gamma'] = [0.35] * len(fit['gamma'])
            print(f"  FuelingInfrTypes {fit['fueling_type']}: gamma {old_gamma}->{fit['gamma'][0]}")

    with open(fit_path, 'w') as f:
        yaml.dump(fuel_infr, f, default_flow_style=False, sort_keys=False)

    print()

# Save metadata
meta = {
    "version": "v2",
    "created": datetime.now().isoformat(),
    "base": "uncertainty_scenarios (scenario_000-003)",
    "method": "patch (copy + overwrite 3 files)",
    "changes": {
        "Model.yaml": {
            "alpha_h": "0.1 -> 0.02",
            "beta_h": "0.1 -> 0.25",
            "discount_rate": "0.05 -> 0.04",
            "rho_mode": "NEW: 0.975 (Bakker et al.)",
        },
        "TechVehicle.yaml": {
            "BEV_tank_capacity": "1187 constant -> 560/1120/1400 kWh interpolated",
        },
        "FuelingInfrTypes.yaml": {
            "gamma": "0.3 -> 0.35 (Shoman harmonic mean MCS/CCS)",
            "cost_per_kW": "0.0 -> 400/300/250 EUR/kW (Table 4)",
        },
    },
    "preserved_from_original": [
        "Odpair.yaml (2244 OD pairs)",
        "Path.yaml (corrected distances from Feb 2026 fix)",
        "MandatoryBreaks.yaml",
        "GeographicElement.yaml",
        "FuelCost.yaml",
        "InitialFuelInfr.yaml",
        "InitialVehicleStock.yaml",
        "all other input files",
    ],
}
with open(NEW_BASE / "patch_info.json", 'w') as f:
    json.dump(meta, f, indent=2)

print("=" * 80)
print("COMPLETE!")
print("=" * 80)
print(f"Output: {NEW_BASE.relative_to(script_dir)}")
print(f"Scenarios: {SCENARIOS}")
print()
print("Files changed per scenario: Model.yaml, TechVehicle.yaml, FuelingInfrTypes.yaml")
print("All other files: exact copies from original uncertainty_scenarios/")
print("=" * 80)
