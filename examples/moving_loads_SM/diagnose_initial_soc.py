"""
Diagnose the initial SOC discrepancy by verifying the constraint calculation step by step.

The initial SOC constraint should enforce:
    soc[origin] == tank_capacity * num_vehicles

where:
    num_vehicles = (path.length / (W * AnnualRange)) * 1000 * f[...]

This script verifies each step of this calculation.
"""

import yaml
import re

base_path = "C:/Users/simuser/Documents/AntoniaGolab/Scand_Med_analysis/SM_baby_2/iDesignRES_transcompmodel/examples/moving_loads_SM"

# Use var_var run, path 2228, year 2056
case_name = "case_20251110_160304_var_var"
result_timestamp = "case_20251110_160304_var_var_cs_2025-11-16_17-02-00"
input_dir = f"{base_path}/input_data/{case_name}"
results_dir = f"{base_path}/results/{case_name}"

year = 2056
path_id = 2228
tv_id = 1  # BEV
g_init = 2020

print(f"\n{'='*100}")
print(f"INITIAL SOC CONSTRAINT VERIFICATION")
print(f"Path {path_id}, Year {year}, BEV (techvehicle {tv_id})")
print(f"{'='*100}\n")

# Load input data
print("Loading input data...")
with open(f"{input_dir}/Path.yaml", 'r') as f:
    paths = yaml.safe_load(f)
with open(f"{input_dir}/TechVehicle.yaml", 'r') as f:
    techvehicles = yaml.safe_load(f)

# Load results
print("Loading results...")
with open(f"{results_dir}/{result_timestamp}_f_dict.yaml", 'r') as f:
    f_dict = yaml.safe_load(f)
with open(f"{results_dir}/{result_timestamp}_soc_dict.yaml", 'r') as f:
    soc_dict = yaml.safe_load(f)

# Get path info
path_info = next(p for p in paths if p['id'] == path_id)
sequence = path_info['sequence']
path_length = path_info['length']

# Get origin geo ID
if isinstance(sequence[0], dict):
    origin_geo = sequence[0]['id']
else:
    origin_geo = sequence[0]

print(f"\nPath Information:")
print(f"  Path ID: {path_id}")
print(f"  Length: {path_length:.2f} km")
print(f"  Origin geo ID: {origin_geo}")
print(f"  Number of nodes: {len(sequence)}")

# Get BEV parameters
tv_info = next(tv for tv in techvehicles if tv['id'] == tv_id)
g_index = year - g_init
W = tv_info['W'][g_index]
spec_cons = tv_info['spec_cons'][g_index]
tank_capacity = tv_info['tank_capacity'][g_index]
annual_range = tv_info['AnnualRange'][g_index]

print(f"\nBEV Parameters (Year {year}, generation index {g_index}):")
print(f"  W (load factor): {W} t/vehicle")
print(f"  spec_cons: {spec_cons} kWh/km")
print(f"  tank_capacity: {tank_capacity} kWh")
print(f"  AnnualRange: {annual_range} km/year")

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

# Find ALL flow entries for this path (could be multiple generations)
print(f"\n{'='*100}")
print(f"FLOW ENTRIES FOR PATH {path_id}, YEAR {year}, BEV")
print(f"{'='*100}\n")

flow_entries = []
for key_str, value in f_dict.items():
    parsed = parse_f_key(key_str)
    if parsed and parsed['year'] == year and parsed['path'] == path_id and parsed['techvehicle'] == tv_id:
        val = float(value) if isinstance(value, str) else value
        if val > 0.01:  # Only show non-trivial flows
            flow_entries.append({
                'key': key_str,
                'parsed': parsed,
                'value': val
            })

print(f"Found {len(flow_entries)} flow entries for path {path_id}:")
for entry in flow_entries:
    p = entry['parsed']
    print(f"\n  Key: {entry['key']}")
    print(f"  Flow: {entry['value']:.2f} tonnes/year")
    print(f"  Product: {p['product']}, OD pair: {p['odpair']}, Mode: {p['mode']}, Generation: {p['generation']}")

# Now calculate SOC for EACH generation and compare
print(f"\n{'='*100}")
print(f"SOC CALCULATION AND VERIFICATION BY GENERATION")
print(f"{'='*100}\n")

for entry in flow_entries:
    p = entry['parsed']
    flow_tonnes = entry['value']
    product_id = p['product']
    odpair_id = p['odpair']
    generation = p['generation']

    print(f"\n{'-'*100}")
    print(f"Generation {generation}")
    print(f"{'-'*100}\n")

    # Step 1: Calculate num_vehicles using constraint formula
    # num_vehicles = (path.length / (W[g] * AnnualRange[g])) * 1000 * f[...]
    # Note: g_index for this generation
    gen_index = generation - g_init
    W_gen = tv_info['W'][gen_index]
    annual_range_gen = tv_info['AnnualRange'][gen_index]
    tank_capacity_gen = tv_info['tank_capacity'][gen_index]

    print(f"Step 1: Calculate num_vehicles")
    print(f"  Formula: (path_length / (W * AnnualRange)) * 1000 * flow")
    print(f"  path_length = {path_length:.2f} km")
    print(f"  W[{gen_index}] = {W_gen} t/vehicle")
    print(f"  AnnualRange[{gen_index}] = {annual_range_gen} km/year")
    print(f"  flow = {flow_tonnes:.2f} tonnes/year")

    denominator = W_gen * annual_range_gen
    print(f"  Denominator (W × AnnualRange) = {denominator:.2f}")

    num_vehicles = (path_length / denominator) * 1000 * flow_tonnes
    print(f"  num_vehicles = ({path_length:.2f} / {denominator:.2f}) × 1000 × {flow_tonnes:.2f}")
    print(f"  num_vehicles = {num_vehicles:.6f}")

    # Step 2: Calculate expected SOC from constraint
    # soc[origin] == tank_capacity * num_vehicles
    print(f"\nStep 2: Calculate expected SOC")
    print(f"  Formula: tank_capacity * num_vehicles")
    print(f"  tank_capacity[{gen_index}] = {tank_capacity_gen} kWh")
    print(f"  num_vehicles = {num_vehicles:.6f}")

    expected_soc_kwh = tank_capacity_gen * num_vehicles
    expected_soc_gwh = expected_soc_kwh / 1e6

    print(f"  expected_soc = {tank_capacity_gen} × {num_vehicles:.6f}")
    print(f"  expected_soc = {expected_soc_kwh:.2f} kWh = {expected_soc_gwh:.6f} GWh")

    # Step 3: Get actual SOC from results
    # soc_key format: (year, (product, odpair, path, geo), techvehicle, generation)
    soc_key = f"({year}, ({product_id}, {odpair_id}, {path_id}, {origin_geo}), {tv_id}, {generation})"

    print(f"\nStep 3: Get actual SOC from results")
    print(f"  SOC key: {soc_key}")

    if soc_key in soc_dict:
        actual_soc_kwh = soc_dict[soc_key]
        actual_soc_kwh = float(actual_soc_kwh) if isinstance(actual_soc_kwh, str) else actual_soc_kwh
        actual_soc_gwh = actual_soc_kwh / 1e6
        print(f"  actual_soc = {actual_soc_kwh:.2f} kWh = {actual_soc_gwh:.6f} GWh")
    else:
        print(f"  ERROR: SOC key not found in results!")
        actual_soc_kwh = None
        actual_soc_gwh = None

    # Step 4: Compare
    if actual_soc_kwh is not None:
        print(f"\nStep 4: Verification")
        diff_kwh = actual_soc_kwh - expected_soc_kwh
        diff_gwh = actual_soc_gwh - expected_soc_gwh
        diff_pct = (diff_kwh / expected_soc_kwh * 100) if expected_soc_kwh > 0 else 0

        print(f"  Expected SOC: {expected_soc_kwh:>15,.2f} kWh ({expected_soc_gwh:.6f} GWh)")
        print(f"  Actual SOC:   {actual_soc_kwh:>15,.2f} kWh ({actual_soc_gwh:.6f} GWh)")
        print(f"  Difference:   {diff_kwh:>15,.2f} kWh ({diff_gwh:.6f} GWh)")
        print(f"  Diff %:       {diff_pct:>15,.2f}%")

        tolerance_kwh = 1.0  # 1 Wh tolerance
        if abs(diff_kwh) < tolerance_kwh:
            print(f"\n  ✓ CONSTRAINT SATISFIED (within {tolerance_kwh} kWh tolerance)")
        else:
            print(f"\n  ✗ CONSTRAINT VIOLATION (exceeds {tolerance_kwh} kWh tolerance)")
            print(f"     The optimizer produced SOC that does NOT match the constraint formula!")

print(f"\n{'='*100}\n")
