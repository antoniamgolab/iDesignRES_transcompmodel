"""
Check SOC values at each node along a route to see if they properly decrease with distance
"""

import yaml
import re

base_path = "C:/Users/simuser/Documents/AntoniaGolab/Scand_Med_analysis/SM_baby_2/iDesignRES_transcompmodel/examples/moving_loads_SM"

# Use var_var run, path 2228 (first path with high BEV flow)
case_name = "case_20251110_160304_var_var"
result_timestamp = "case_20251110_160304_var_var_cs_2025-11-16_17-02-00"
input_dir = f"{base_path}/input_data/{case_name}"
results_dir = f"{base_path}/results/{case_name}"

year = 2056
path_id = 2228  # First path with high BEV flow
tv_id = 1  # BEV

print(f"\n{'='*100}")
print(f"SOC PROGRESSION ALONG ROUTE - Path {path_id}, Year {year}, BEV")
print(f"{'='*100}\n")

# Load input data
with open(f"{input_dir}/Path.yaml", 'r') as f:
    paths = yaml.safe_load(f)
with open(f"{input_dir}/TechVehicle.yaml", 'r') as f:
    techvehicles = yaml.safe_load(f)

# Load results
with open(f"{results_dir}/{result_timestamp}_f_dict.yaml", 'r') as f:
    f_dict = yaml.safe_load(f)
with open(f"{results_dir}/{result_timestamp}_soc_dict.yaml", 'r') as f:
    soc_dict = yaml.safe_load(f)
with open(f"{results_dir}/{result_timestamp}_s_dict.yaml", 'r') as f:
    s_dict = yaml.safe_load(f)

# Get path info
path_info = next(p for p in paths if p['id'] == path_id)
sequence = path_info['sequence']
path_length = path_info['length']
distances_from_prev = path_info['distance_from_previous']

print(f"Path length: {path_length:.2f} km")
print(f"Number of nodes: {len(sequence)}")
print(f"Sequence: {sequence}\n")

# Get BEV parameters
tv_info = next(tv for tv in techvehicles if tv['id'] == tv_id)
g_init = 2020
g_index = year - g_init
W = tv_info['W'][g_index]
spec_cons = tv_info['spec_cons'][g_index]
tank_capacity = tv_info['tank_capacity'][g_index]
annual_range = tv_info['AnnualRange'][g_index]

print(f"BEV Parameters:")
print(f"  W: {W} t/vehicle")
print(f"  spec_cons: {spec_cons} kWh/km")
print(f"  tank_capacity: {tank_capacity} kWh")
print(f"  annual_range: {annual_range} km/year\n")

# Parse f_dict keys
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

# Find flow for this path
flow_tonnes = 0
product_id = None
region_id = None
generation = None

for key_str, value in f_dict.items():
    parsed = parse_f_key(key_str)
    if parsed and parsed['year'] == year and parsed['path'] == path_id and parsed['techvehicle'] == tv_id:
        val = float(value) if isinstance(value, str) else value
        if val > 1.0:
            flow_tonnes = val
            product_id = parsed['product']
            region_id = parsed['odpair']
            generation = parsed['generation']
            break

print(f"Flow: {flow_tonnes:.2f} tonnes/year")
print(f"Product: {product_id}, OD pair: {region_id}, Generation: {generation}\n")

# Calculate num_vehicles
num_vehicles = (path_length / (W * annual_range)) * 1000 * flow_tonnes
print(f"Number of vehicles: {num_vehicles:.6f}\n")

# Check SOC and charging at each node
print(f"{'='*100}")
print(f"SOC PROGRESSION NODE BY NODE")
print(f"{'='*100}\n")

print(f"{'Node':<6} {'Geo ID':<10} {'Dist(km)':<12} {'Cumul(km)':<12} {'SOC(GWh)':<15} {'Charging(GWh)':<15} {'Expected SOC':<15}")
print(f"{'-'*100}")

cumulative_distance = 0
previous_soc = None

for i, geo_id in enumerate(sequence):
    # Get SOC at this node
    soc_key = f"({year}, ({product_id}, {region_id}, {path_id}, {geo_id}), {tv_id}, {generation})"
    actual_soc = soc_dict.get(soc_key, 0)
    # Convert to float if string
    actual_soc = float(actual_soc) if isinstance(actual_soc, str) else actual_soc
    actual_soc_gwh = actual_soc / 1e6  # Convert to GWh

    # Get charging at this node
    charging_at_node = 0
    for fuel_id in range(1, 10):
        for infr_id in range(1, 10):
            s_key = f"({year}, ({product_id}, {region_id}, {path_id}, {geo_id}), {tv_id}, ({fuel_id}, {infr_id}), {generation})"
            if s_key in s_dict:
                charging_val = s_dict[s_key]
                # Convert to float if string
                charging_val = float(charging_val) if isinstance(charging_val, str) else charging_val
                charging_at_node += charging_val / 1000  # Convert MWh to GWh

    # Calculate expected SOC
    if i == 0:
        # Origin - should be tank_capacity * num_vehicles
        expected_soc_gwh = (tank_capacity * num_vehicles) / 1e6
    else:
        # Should be previous SOC - energy consumed + charging
        distance_increment = distances_from_prev[i]
        cumulative_distance += distance_increment
        energy_consumed = (distance_increment * spec_cons * num_vehicles) / 1e6  # GWh
        expected_soc_gwh = previous_soc - energy_consumed + charging_at_node

    print(f"{i:<6} {geo_id:<10} {distances_from_prev[i]:>10.2f} {cumulative_distance:>10.2f} {actual_soc_gwh:>13.6f} {charging_at_node:>13.6f} {expected_soc_gwh:>13.6f}")

    previous_soc = expected_soc_gwh

print(f"\n{'='*100}")
print(f"ANALYSIS")
print(f"{'='*100}\n")

# Check if all SOC values are zero
all_zero = all(
    soc_dict.get(f"({year}, ({product_id}, {region_id}, {path_id}, {geo_id}), {tv_id}, {generation})", 0) == 0
    for geo_id in sequence
)

if all_zero:
    print("*** ALL SOC values along the route are ZERO ***")
    print("This suggests the SOC variable is not being properly set/calculated by the optimizer")
else:
    print("SOC values are non-zero - checking if they decrease properly with distance...")

    # Check if SOC decreases monotonically (when no charging)
    soc_values = []
    for geo_id in sequence:
        soc_key = f"({year}, ({product_id}, {region_id}, {path_id}, {geo_id}), {tv_id}, {generation})"
        soc_val = soc_dict.get(soc_key, 0)
        # Convert to float if string
        soc_val = float(soc_val) if isinstance(soc_val, str) else soc_val
        soc_values.append(soc_val)

    print(f"\nSOC values: {[f'{s/1e6:.6f}' for s in soc_values]}")

    decreasing = all(soc_values[i] >= soc_values[i+1] for i in range(len(soc_values)-1))
    if decreasing:
        print("SOC decreases monotonically along the route (as expected)")
    else:
        print("SOC does NOT decrease monotonically - there may be an issue")

print(f"\n{'='*100}\n")
