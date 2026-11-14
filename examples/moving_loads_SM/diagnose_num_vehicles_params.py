"""
Diagnose the num_vehicles calculation parameters to find the source of the 12.9% SOC discrepancy.

This script checks the actual parameter values used in:
num_vehicles = (path.length / (W × AnnualRange)) × 1000 × f

Specifically investigating if wrong array indices or parameter values are being used.
"""

import yaml
import re

base_path = "C:/Users/simuser/Documents/AntoniaGolab/Scand_Med_analysis/SM_baby_2/iDesignRES_transcompmodel/examples/moving_loads_SM"
case_name = "case_20251110_160646_reverse"
result_timestamp = "case_20251110_160646_reverse_cs_2025-11-17_14-09-45"

input_dir = f"{base_path}/input_data/{case_name}"
results_dir = f"{base_path}/results/{case_name}"

# Parameters
g_init = 2020
target_year = 2056
bev_id = 1

def parse_soc_key(key_str):
    """Parse soc_dict key: (year, (product, odpair, path, geo), techvehicle, generation)"""
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

def parse_f_key(key_str):
    """Parse f_dict key: (year, (product, odpair, path), (mode, techvehicle), generation)"""
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
print(f"DIAGNOSING num_vehicles CALCULATION PARAMETERS")
print(f"{'='*100}\n")

# Load input data
print("Loading input data...")
with open(f"{input_dir}/Path.yaml", 'r', encoding='utf-8') as f:
    paths = yaml.safe_load(f)
with open(f"{input_dir}/TechVehicle.yaml", 'r', encoding='utf-8') as f:
    techvehicles = yaml.safe_load(f)

# Load results
print("Loading results...")
with open(f"{results_dir}/{result_timestamp}_soc_dict.yaml", 'r', encoding='utf-8') as f:
    soc_dict = yaml.safe_load(f)
with open(f"{results_dir}/{result_timestamp}_f_dict.yaml", 'r', encoding='utf-8') as f:
    f_dict = yaml.safe_load(f)

print(f"Loaded {len(paths)} paths, {len(techvehicles)} techvehicles\n")

# Build lookups
path_dict = {p['id']: p for p in paths}
tv_dict = {tv['id']: tv for tv in techvehicles}

# Get BEV info
bev = tv_dict[bev_id]
print(f"BEV TechVehicle (id={bev_id}):")
print(f"  W array length: {len(bev['W'])}")
print(f"  AnnualRange array length: {len(bev['AnnualRange'])}")
print(f"  tank_capacity array length: {len(bev['tank_capacity'])}\n")

# Show array indexing
print(f"Array indexing for target_year={target_year}, g_init={g_init}:")
gen_idx = target_year - g_init
print(f"  Generation index (g - g_init): {gen_idx}")
print(f"  Julia 1-indexed: g - g_init + 1 = {gen_idx + 1}")
print(f"  Python 0-indexed: g - g_init = {gen_idx}\n")

# Get parameters for target year
tank_capacity = bev['tank_capacity'][gen_idx]
W = bev['W'][gen_idx]
AnnualRange = bev['AnnualRange'][gen_idx]

print(f"BEV parameters at index {gen_idx} (generation {target_year}):")
print(f"  tank_capacity[{gen_idx}] = {tank_capacity:.4f} kWh")
print(f"  W[{gen_idx}] = {W:.4f} tonnes")
print(f"  AnnualRange[{gen_idx}] = {AnnualRange:.4f} km\n")

# Also check if there's an off-by-one error - check adjacent indices
if gen_idx > 0:
    print(f"Adjacent parameters (checking for off-by-one errors):")
    print(f"  W[{gen_idx-1}] = {bev['W'][gen_idx-1]:.4f} tonnes")
    print(f"  W[{gen_idx}] = {bev['W'][gen_idx]:.4f} tonnes (current)")
    if gen_idx + 1 < len(bev['W']):
        print(f"  W[{gen_idx+1}] = {bev['W'][gen_idx+1]:.4f} tonnes")
    print()
    print(f"  AnnualRange[{gen_idx-1}] = {bev['AnnualRange'][gen_idx-1]:.4f} km")
    print(f"  AnnualRange[{gen_idx}] = {bev['AnnualRange'][gen_idx]:.4f} km (current)")
    if gen_idx + 1 < len(bev['AnnualRange']):
        print(f"  AnnualRange[{gen_idx+1}] = {bev['AnnualRange'][gen_idx+1]:.4f} km")
    print()

# Find SOC values at origins
soc_at_origins = {}
for key_str, value in soc_dict.items():
    parsed = parse_soc_key(key_str)
    if not parsed:
        continue

    if (parsed['year'] != target_year or parsed['techvehicle'] != bev_id):
        continue

    path_id = parsed['path']
    geo_id = parsed['geo']
    generation = parsed['generation']

    if path_id not in path_dict:
        continue

    path = path_dict[path_id]
    sequence = path['sequence']

    # Get origin geo ID
    if isinstance(sequence[0], dict):
        origin_id = sequence[0]['id']
    else:
        origin_id = sequence[0]

    # Only check at origins
    if geo_id == origin_id:
        val = float(value) if isinstance(value, str) else value
        soc_at_origins[(path_id, generation)] = {
            'soc': val,
            'path': path
        }

print(f"\n{'='*100}")
print(f"DETAILED PARAMETER VERIFICATION FOR SAMPLE PATHS")
print(f"{'='*100}\n")

# Sample first 5 paths to analyze in detail
sample_keys = sorted(soc_at_origins.keys())[:5]

for path_id, generation in sample_keys:
    data = soc_at_origins[(path_id, generation)]
    actual_soc = data['soc']
    path = data['path']
    path_length = path['length']

    # Find corresponding f value
    f_value = None
    for key_str, value in f_dict.items():
        parsed = parse_f_key(key_str)
        if (parsed and
            parsed['year'] == target_year and
            parsed['path'] == path_id and
            parsed['techvehicle'] == bev_id and
            parsed['generation'] == generation):
            f_value = float(value) if isinstance(value, str) else value
            break

    if f_value is None:
        print(f"Path {path_id}: No f value found, skipping\n")
        continue

    # Calculate expected SOC using the constraint formula
    num_vehicles = (path_length / (W * AnnualRange)) * 1000 * f_value
    expected_soc = tank_capacity * num_vehicles

    # Compare
    diff = actual_soc - expected_soc
    diff_pct = (diff / expected_soc * 100) if expected_soc > 0 else 0
    ratio = actual_soc / expected_soc if expected_soc > 0 else 0

    print(f"Path {path_id}, Gen {generation}:")
    print(f"  Path length:               {path_length:>12.4f} km")
    print(f"  W (payload):               {W:>12.4f} tonnes")
    print(f"  AnnualRange:               {AnnualRange:>12.4f} km")
    print(f"  W × AnnualRange:           {W * AnnualRange:>12.4f} tonne·km")
    print(f"  Flow (f):                  {f_value:>12.8f}")
    print(f"  ")
    print(f"  Num vehicles calculated:   {num_vehicles:>12.8f}")
    print(f"  = (path_length / (W × AnnualRange)) × 1000 × f")
    print(f"  = ({path_length:.4f} / {W * AnnualRange:.4f}) × 1000 × {f_value:.8f}")
    print(f"  = {path_length / (W * AnnualRange):.8f} × 1000 × {f_value:.8f}")
    print(f"  ")
    print(f"  Tank capacity:             {tank_capacity:>12.4f} kWh")
    print(f"  Expected SOC:              {expected_soc:>12.4f} kWh")
    print(f"  Actual SOC:                {actual_soc:>12.4f} kWh")
    print(f"  ")
    print(f"  Difference:                {diff:>12.4f} kWh ({diff_pct:+.4f}%)")
    print(f"  Ratio (actual/expected):   {ratio:>12.6f}")
    print()

# Calculate what parameter change would cause 0.871 ratio
print(f"\n{'='*100}")
print(f"REVERSE ENGINEERING THE 12.9% DISCREPANCY")
print(f"{'='*100}\n")

observed_ratio = 0.870968  # 1 - 0.129032
print(f"Observed ratio (actual/expected): {observed_ratio:.6f}")
print(f"This means actual SOC = {observed_ratio:.6f} × expected SOC\n")

print(f"Since expected SOC = tank_capacity × num_vehicles")
print(f"And num_vehicles = (path_length / (W × AnnualRange)) × 1000 × f\n")

print(f"For actual to be {observed_ratio:.6f} × expected, one of these must be true:")
print(f"  1. tank_capacity is {observed_ratio:.6f}× what we expect")
print(f"  2. path_length is {observed_ratio:.6f}× what we expect")
print(f"  3. f is {observed_ratio:.6f}× what we expect")
print(f"  4. W × AnnualRange is {1/observed_ratio:.6f}× what we expect (1.1481×)")
print(f"     - W could be {1/observed_ratio:.6f}× larger")
print(f"     - AnnualRange could be {1/observed_ratio:.6f}× larger")
print(f"     - Or some combination\n")

# Check if using wrong index would give this ratio
print(f"Checking if wrong array index could cause this ratio:")
if gen_idx > 0:
    W_prev = bev['W'][gen_idx-1]
    AR_prev = bev['AnnualRange'][gen_idx-1]
    ratio_W = W_prev / W
    ratio_AR = AR_prev / AnnualRange
    ratio_combined = (W_prev * AR_prev) / (W * AnnualRange)

    print(f"  If using index {gen_idx-1} instead of {gen_idx}:")
    print(f"    W[{gen_idx-1}] / W[{gen_idx}] = {W_prev:.4f} / {W:.4f} = {ratio_W:.6f}")
    print(f"    AR[{gen_idx-1}] / AR[{gen_idx}] = {AR_prev:.4f} / {AnnualRange:.4f} = {ratio_AR:.6f}")
    print(f"    (W × AR)[{gen_idx-1}] / (W × AR)[{gen_idx}] = {ratio_combined:.6f}")
    print(f"    Would give actual/expected ratio = 1/{ratio_combined:.6f} = {1/ratio_combined:.6f}")

    if abs(1/ratio_combined - observed_ratio) < 0.001:
        print(f"    ✓ THIS MATCHES THE OBSERVED RATIO!")
        print(f"    The model is using index {gen_idx-1} instead of {gen_idx}!")
    else:
        print(f"    Does not match observed ratio {observed_ratio:.6f}")

if gen_idx + 1 < len(bev['W']):
    W_next = bev['W'][gen_idx+1]
    AR_next = bev['AnnualRange'][gen_idx+1]
    ratio_W = W_next / W
    ratio_AR = AR_next / AnnualRange
    ratio_combined = (W_next * AR_next) / (W * AnnualRange)

    print(f"\n  If using index {gen_idx+1} instead of {gen_idx}:")
    print(f"    W[{gen_idx+1}] / W[{gen_idx}] = {W_next:.4f} / {W:.4f} = {ratio_W:.6f}")
    print(f"    AR[{gen_idx+1}] / AR[{gen_idx}] = {AR_next:.4f} / {AnnualRange:.4f} = {ratio_AR:.6f}")
    print(f"    (W × AR)[{gen_idx+1}] / (W × AR)[{gen_idx}] = {ratio_combined:.6f}")
    print(f"    Would give actual/expected ratio = 1/{ratio_combined:.6f} = {1/ratio_combined:.6f}")

    if abs(1/ratio_combined - observed_ratio) < 0.001:
        print(f"    ✓ THIS MATCHES THE OBSERVED RATIO!")
        print(f"    The model is using index {gen_idx+1} instead of {gen_idx}!")
    else:
        print(f"    Does not match observed ratio {observed_ratio:.6f}")

print(f"\n{'='*100}\n")
