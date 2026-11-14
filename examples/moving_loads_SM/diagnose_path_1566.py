"""
Diagnose issues with path 1566:
1. Negative consumption at origin
2. SOC exceeding 100% tank capacity at node 2
"""

import yaml
import re
from pathlib import Path

base_path = Path("C:/Users/simuser/Documents/AntoniaGolab/Scand_Med_analysis/SM_baby_2/iDesignRES_transcompmodel/examples/moving_loads_SM")

# Case to analyze
case_name = "case_20251110_160304_var_var"
result_timestamp = "case_20251110_160304_var_var_cs_2025-11-18_10-44-39"

input_dir = base_path / "input_data" / case_name
results_dir = base_path / "results" / case_name

# Parameters
target_year = 2056
bev_id = 1
target_generation = 2056
path_id = 1566

def parse_soc_key(key_str):
    pattern = r'\((\d+),\s*\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\),\s*(\d+),\s*(\d+)\)'
    match = re.match(pattern, key_str)
    if match:
        return {
            'year': int(match.group(1)),
            'product': int(match.group(2)),
            'odpair': int(match.group(3)),
            'path': int(match.group(4)),
            'geo': int(match.group(5)),
            'techvehicle': int(match.group(6)),
            'generation': int(match.group(7))
        }
    return None

def parse_s_key(key_str):
    pattern = r'\((\d+),\s*\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\),\s*(\d+),\s*\((\d+),\s*(\d+)\),\s*(\d+)\)'
    match = re.match(pattern, key_str)
    if match:
        return {
            'year': int(match.group(1)),
            'product': int(match.group(2)),
            'odpair': int(match.group(3)),
            'path': int(match.group(4)),
            'geo': int(match.group(5)),
            'techvehicle': int(match.group(6)),
            'fuel': int(match.group(7)),
            'infra': int(match.group(8)),
            'generation': int(match.group(9))
        }
    return None

def parse_f_key(key_str):
    pattern = r'\((\d+),\s*\((\d+),\s*(\d+),\s*(\d+)\),\s*\((\d+),\s*(\d+)\),\s*(\d+)\)'
    match = re.match(pattern, key_str)
    if match:
        return {
            'year': int(match.group(1)),
            'product': int(match.group(2)),
            'odpair': int(match.group(3)),
            'path': int(match.group(4)),
            'mode': int(match.group(5)),
            'techvehicle': int(match.group(6)),
            'generation': int(match.group(7))
        }
    return None

print(f"\n{'='*100}")
print(f"DIAGNOSING PATH {path_id} - Year {target_year}, Generation {target_generation}")
print(f"{'='*100}\n")

# Load input data
print("Loading input data...")
with open(input_dir / "Path.yaml", 'r', encoding='utf-8') as f:
    paths = yaml.safe_load(f)
with open(input_dir / "TechVehicle.yaml", 'r', encoding='utf-8') as f:
    techvehicles = yaml.safe_load(f)
with open(input_dir / "Model.yaml", 'r', encoding='utf-8') as f:
    model_data = yaml.safe_load(f)

# Calculate g_init
y_init = model_data["y_init"]
pre_y = model_data["pre_y"]
g_init = y_init - pre_y

# Load results
print("Loading results...")
with open(results_dir / f"{result_timestamp}_soc_dict.yaml", 'r', encoding='utf-8') as f:
    soc_dict = yaml.safe_load(f)
with open(results_dir / f"{result_timestamp}_s_dict.yaml", 'r', encoding='utf-8') as f:
    s_dict = yaml.safe_load(f)
with open(results_dir / f"{result_timestamp}_f_dict.yaml", 'r', encoding='utf-8') as f:
    f_dict = yaml.safe_load(f)

# Get path and BEV info
path_dict = {p['id']: p for p in paths}
tv_dict = {tv['id']: tv for tv in techvehicles}

path = path_dict[path_id]
bev = tv_dict[bev_id]

gen_idx = target_generation - g_init
tank_capacity = bev['tank_capacity'][gen_idx]
W = bev['W'][gen_idx]
AnnualRange = bev['AnnualRange'][gen_idx]
spec_cons = bev['spec_cons'][gen_idx]

print(f"\nPath {path_id}:")
print(f"  Length: {path['length']:.2f} km")
print(f"  Number of nodes: {len(path['sequence'])}")

print(f"\nBEV parameters (generation {target_generation}, index {gen_idx}):")
print(f"  Tank capacity: {tank_capacity:.2f} kWh")
print(f"  W: {W:.2f} tonnes")
print(f"  Annual range: {AnnualRange:.2f} km")
print(f"  Specific consumption: {spec_cons:.4f} kWh/tonne-km")

# Get flow for this path
f_value = None
for key_str, value in f_dict.items():
    parsed = parse_f_key(key_str)
    if (parsed and
        parsed['year'] == target_year and
        parsed['path'] == path_id and
        parsed['techvehicle'] == bev_id and
        parsed['generation'] == target_generation):
        f_value = float(value) if isinstance(value, str) else value
        break

if f_value is None:
    print(f"\nERROR: No flow found for this path!")
    exit()

print(f"\nFlow: {f_value:.6f}")

# Calculate number of vehicles
num_vehicles = (path['length'] / (W * AnnualRange)) * 1000 * f_value
total_tank_capacity = tank_capacity * num_vehicles

print(f"Number of vehicles: {num_vehicles:.6f}")
print(f"Total tank capacity: {total_tank_capacity:.2f} kWh")

# Get sequence
sequence = path['sequence']
geo_ids = []
for item in sequence:
    if isinstance(item, dict):
        geo_ids.append(item['id'])
    else:
        geo_ids.append(item)

print(f"\nGeographic sequence: {geo_ids}")

# Extract SOC and charging values
soc_values = {}
charging_values = {}

for key_str, value in soc_dict.items():
    parsed = parse_soc_key(key_str)
    if (parsed and
        parsed['year'] == target_year and
        parsed['path'] == path_id and
        parsed['techvehicle'] == bev_id and
        parsed['generation'] == target_generation):
        geo_id = parsed['geo']
        val = float(value) if isinstance(value, str) else value
        soc_values[geo_id] = val  # Already in kWh

for key_str, value in s_dict.items():
    parsed = parse_s_key(key_str)
    if (parsed and
        parsed['year'] == target_year and
        parsed['path'] == path_id and
        parsed['techvehicle'] == bev_id and
        parsed['generation'] == target_generation):
        geo_id = parsed['geo']
        val = float(value) if isinstance(value, str) else value
        if geo_id not in charging_values:
            charging_values[geo_id] = 0
        charging_values[geo_id] += val * 1000  # Convert from MWh to kWh

# Create ordered arrays
soc_array = [soc_values.get(geo_id, 0) for geo_id in geo_ids]
charging_array = [charging_values.get(geo_id, 0) for geo_id in geo_ids]

print(f"\n{'='*100}")
print(f"NODE-BY-NODE ANALYSIS")
print(f"{'='*100}\n")

print(f"{'Node':<6} {'Geo ID':<8} {'SOC (kWh)':<15} {'Charging (kWh)':<15} {'SOC % Tank':<12} {'Issue?':<20}")
print("-" * 100)

for i, geo_id in enumerate(geo_ids):
    soc = soc_array[i]
    charging = charging_array[i]
    soc_pct = (soc / total_tank_capacity * 100) if total_tank_capacity > 0 else 0

    issue = ""
    if soc > total_tank_capacity:
        issue = "SOC > 100%"
    if soc < 0:
        issue = "SOC < 0"

    print(f"{i:<6} {geo_id:<8} {soc:>12.2f} {charging:>12.2f} {soc_pct:>10.1f}% {issue:<20}")

# Calculate consumption
print(f"\n{'='*100}")
print(f"CONSUMPTION ANALYSIS")
print(f"{'='*100}\n")

print(f"{'Segment':<15} {'Consumption (kWh)':<20} {'Issue?':<30}")
print("-" * 70)

for i in range(len(soc_array) - 1):
    # Energy balance: SOC[i+1] = SOC[i] - consumption[i->i+1] + charging[i+1]
    # Therefore: consumption[i->i+1] = SOC[i] - SOC[i+1] + charging[i+1]
    # NOTE: Charging happens at the ARRIVAL node (i+1), not departure node (i)
    consumption = soc_array[i] - soc_array[i+1] + charging_array[i+1]

    issue = ""
    if consumption < 0:
        issue = "NEGATIVE consumption!"

    print(f"Node {i}->{i+1:<5} {consumption:>15.2f} {issue:<30}")

# Check 50% constraint at destination
print(f"\n{'='*100}")
print(f"50% DESTINATION CONSTRAINT CHECK")
print(f"{'='*100}\n")

expected_soc_dest = 0.5 * tank_capacity * num_vehicles
actual_soc_dest = soc_array[-1]

print(f"Expected SOC at destination (50%): {expected_soc_dest:.2f} kWh")
print(f"Actual SOC at destination:         {actual_soc_dest:.2f} kWh")
print(f"Difference:                        {(actual_soc_dest - expected_soc_dest):.2f} kWh")
print(f"Ratio (actual/expected):           {(actual_soc_dest / expected_soc_dest):.8f}")

tolerance = 1e-3
if abs(actual_soc_dest - expected_soc_dest) < tolerance:
    print(f"\n[OK] 50% constraint SATISFIED")
else:
    print(f"\n[ERROR] 50% constraint VIOLATED")

# Check initial SOC constraint at origin
print(f"\n{'='*100}")
print(f"INITIAL SOC CONSTRAINT CHECK")
print(f"{'='*100}\n")

expected_soc_origin = tank_capacity * num_vehicles  # Should be 100% at origin
actual_soc_origin = soc_array[0]

print(f"Expected SOC at origin (100%): {expected_soc_origin:.2f} kWh")
print(f"Actual SOC at origin:          {actual_soc_origin:.2f} kWh")
print(f"Difference:                    {(actual_soc_origin - expected_soc_origin):.2f} kWh")
print(f"Ratio (actual/expected):       {(actual_soc_origin / expected_soc_origin):.8f}")

if abs(actual_soc_origin - expected_soc_origin) < tolerance:
    print(f"\n[OK] Initial SOC constraint SATISFIED")
else:
    print(f"\n[ERROR] Initial SOC constraint VIOLATED")

# Energy balance check
print(f"\n{'='*100}")
print(f"OVERALL ENERGY BALANCE")
print(f"{'='*100}\n")

total_charging = sum(charging_array)
total_consumption = sum(soc_array[i] - soc_array[i+1] + charging_array[i+1] for i in range(len(soc_array) - 1))
net_soc_change = soc_array[-1] - soc_array[0]

print(f"Initial SOC:       {soc_array[0]:.2f} kWh")
print(f"Final SOC:         {soc_array[-1]:.2f} kWh")
print(f"Net SOC change:    {net_soc_change:.2f} kWh")
print(f"Total charging:    {total_charging:.2f} kWh")
print(f"Total consumption: {total_consumption:.2f} kWh")
print(f"\nEnergy balance check:")
print(f"  Initial + Charging - Consumption = Final?")
print(f"  {soc_array[0]:.2f} + {total_charging:.2f} - {total_consumption:.2f} = {(soc_array[0] + total_charging - total_consumption):.2f}")
print(f"  Expected: {soc_array[-1]:.2f}")
print(f"  Difference: {abs(soc_array[-1] - (soc_array[0] + total_charging - total_consumption)):.6f} kWh")

print(f"\n{'='*100}\n")
