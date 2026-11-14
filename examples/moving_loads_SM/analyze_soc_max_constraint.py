"""
Quick analysis to compare SOC values between runs with and without soc_max constraint
"""

import yaml
import re
from pathlib import Path
from collections import defaultdict

base_path = Path("C:/Users/simuser/Documents/AntoniaGolab/Scand_Med_analysis/SM_baby_2/iDesignRES_transcompmodel/examples/moving_loads_SM")

# Two runs to compare
run_without_soc_max = "case_20251110_160304_var_var_cs_2025-11-17_15-52-22"  # soc_max commented
run_with_soc_max = "case_20251110_160304_var_var_cs_2025-11-18_10-44-39"     # soc_max active

case_name = "case_20251110_160304_var_var"
input_dir = base_path / "input_data" / case_name
results_dir = base_path / "results" / case_name

# Analysis parameters
target_year = 2056
bev_id = 1
target_generation = 2056
selected_path_id = 1566

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

print("="*100)
print("COMPARING SOC VALUES: WITH vs WITHOUT soc_max CONSTRAINT")
print("="*100)
print(f"\nPath: {selected_path_id}, Year: {target_year}, Generation: {target_generation}\n")

# Load input data (needed for tank capacity and path info)
with open(input_dir / "Path.yaml", 'r', encoding='utf-8') as f:
    paths = yaml.safe_load(f)
with open(input_dir / "TechVehicle.yaml", 'r', encoding='utf-8') as f:
    techvehicles = yaml.safe_load(f)
with open(input_dir / "Model.yaml", 'r', encoding='utf-8') as f:
    model_data = yaml.safe_load(f)
with open(input_dir / "GeographicElement.yaml", 'r', encoding='utf-8') as f:
    geo_elements = yaml.safe_load(f)

path_dict = {p['id']: p for p in paths}
tv_dict = {tv['id']: tv for tv in techvehicles}
geo_dict = {g['id']: g for g in geo_elements}

selected_path = path_dict[selected_path_id]
bev = tv_dict[bev_id]

# Get BEV parameters
y_init = model_data["y_init"]
pre_y = model_data["pre_y"]
g_init = y_init - pre_y
gen_idx = target_generation - g_init

tank_capacity = bev['tank_capacity'][gen_idx]
W = bev['W'][gen_idx]
AnnualRange = bev['AnnualRange'][gen_idx]

# Get path sequence
sequence = selected_path['sequence']
geo_ids = []
for item in sequence:
    if isinstance(item, dict):
        geo_ids.append(item['id'])
    else:
        geo_ids.append(item)

print(f"Path length: {selected_path['length']:.2f} km")
print(f"Number of nodes: {len(geo_ids)}")
print(f"Tank capacity per vehicle: {tank_capacity:.2f} kWh")
print(f"Geographic sequence: {geo_ids}\n")

def analyze_run(result_timestamp, label):
    print(f"\n{'='*100}")
    print(f"{label}: {result_timestamp}")
    print(f"{'='*100}")

    # Load results
    with open(results_dir / f"{result_timestamp}_soc_dict.yaml", 'r', encoding='utf-8') as f:
        soc_dict = yaml.safe_load(f)
    with open(results_dir / f"{result_timestamp}_s_dict.yaml", 'r', encoding='utf-8') as f:
        s_dict = yaml.safe_load(f)
    with open(results_dir / f"{result_timestamp}_f_dict.yaml", 'r', encoding='utf-8') as f:
        f_dict = yaml.safe_load(f)

    # Extract flow
    flow = 0
    for key_str, value in f_dict.items():
        parsed = parse_f_key(key_str)
        if (parsed and
            parsed['year'] == target_year and
            parsed['path'] == selected_path_id and
            parsed['techvehicle'] == bev_id and
            parsed['generation'] == target_generation):
            val = float(value) if isinstance(value, str) else value
            flow = val
            break

    # Calculate num_vehicles
    num_vehicles = (selected_path['length'] / (W * AnnualRange)) * 1000 * flow
    total_tank_capacity = tank_capacity * num_vehicles

    print(f"\nFlow: {flow:.6f}")
    print(f"Number of vehicles: {num_vehicles:.6f}")
    print(f"Total tank capacity: {total_tank_capacity:.2f} kWh")

    # Extract SOC values
    soc_values = {}
    for key_str, value in soc_dict.items():
        parsed = parse_soc_key(key_str)
        if (parsed and
            parsed['year'] == target_year and
            parsed['path'] == selected_path_id and
            parsed['techvehicle'] == bev_id and
            parsed['generation'] == target_generation):
            geo_id = parsed['geo']
            val = float(value) if isinstance(value, str) else value
            soc_values[geo_id] = val

    # Extract charging values
    charging_values = defaultdict(float)
    for key_str, value in s_dict.items():
        parsed = parse_s_key(key_str)
        if (parsed and
            parsed['year'] == target_year and
            parsed['path'] == selected_path_id and
            parsed['techvehicle'] == bev_id and
            parsed['generation'] == target_generation):
            geo_id = parsed['geo']
            val = float(value) if isinstance(value, str) else value
            charging_values[geo_id] += val * 1000  # Convert MWh to kWh

    # Create arrays
    soc_array = [soc_values.get(geo_id, 0) for geo_id in geo_ids]
    charging_array = [charging_values.get(geo_id, 0) for geo_id in geo_ids]

    # Print node-by-node
    print(f"\n{'Node':<6} {'Geo_ID':<8} {'Geo_Name':<15} {'SOC (kWh)':<15} {'SOC % Tank':<12} {'Charging (kWh)':<15}")
    print("-" * 100)

    max_soc_pct = 0
    max_soc_node = 0

    for i, geo_id in enumerate(geo_ids):
        geo_name = geo_dict.get(geo_id, {}).get('name', f'Geo_{geo_id}')
        soc_pct = (soc_array[i] / total_tank_capacity * 100) if total_tank_capacity > 0 else 0

        if soc_pct > max_soc_pct:
            max_soc_pct = soc_pct
            max_soc_node = i

        violation = " [EXCEEDS 100%!]" if soc_pct > 100 else ""
        print(f"{i:<6} {geo_id:<8} {geo_name:<15} {soc_array[i]:<15.2f} {soc_pct:<12.2f}{violation} {charging_array[i]:<15.2f}")

    print(f"\n{'='*100}")
    print(f"MAX SOC PERCENTAGE: {max_soc_pct:.2f}% at node {max_soc_node}")
    print(f"ORIGIN SOC: {soc_array[0]:.2f} kWh ({soc_array[0]/total_tank_capacity*100:.2f}%)")
    print(f"DESTINATION SOC: {soc_array[-1]:.2f} kWh ({soc_array[-1]/total_tank_capacity*100:.2f}%)")
    print(f"{'='*100}")

    return {
        'soc_array': soc_array,
        'charging_array': charging_array,
        'total_tank_capacity': total_tank_capacity,
        'max_soc_pct': max_soc_pct,
        'max_soc_node': max_soc_node
    }

# Analyze both runs
results_without = analyze_run(run_without_soc_max, "RUN WITHOUT soc_max (Nov 17)")
results_with = analyze_run(run_with_soc_max, "RUN WITH soc_max (Nov 18)")

# Final comparison
print(f"\n{'='*100}")
print("SUMMARY COMPARISON")
print(f"{'='*100}")
print(f"\nWithout soc_max constraint:")
print(f"  Max SOC percentage: {results_without['max_soc_pct']:.2f}% at node {results_without['max_soc_node']}")
print(f"\nWith soc_max constraint:")
print(f"  Max SOC percentage: {results_with['max_soc_pct']:.2f}% at node {results_with['max_soc_node']}")

if results_with['max_soc_pct'] <= 100:
    print(f"\n[OK] soc_max constraint is WORKING - SOC never exceeds 100%")
else:
    print(f"\n[WARNING] soc_max constraint may NOT be active - SOC still exceeds 100%")

print(f"\n{'='*100}")
