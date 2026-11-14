"""
Verify initial SOC constraint using CORRECT generation-specific parameters.

Previous bug: Used target_year parameters for ALL generations.
Fix: Use the actual generation's parameters (tank_capacity[gen], W[gen], AnnualRange[gen])
"""

import yaml
import re
from collections import defaultdict

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
print(f"VERIFYING INITIAL SOC CONSTRAINT WITH CORRECT GENERATION-SPECIFIC PARAMETERS")
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
print(f"  Array lengths: W={len(bev['W'])}, AnnualRange={len(bev['AnnualRange'])}, tank_capacity={len(bev['tank_capacity'])}\n")

# Find SOC values at origins for target year and BEV
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
            'soc': val,  # Already in kWh
            'path': path
        }

print(f"Found {len(soc_at_origins)} SOC values at origins for year {target_year}\n")

# Get unique generations
generations = sorted(set(gen for _, gen in soc_at_origins.keys()))
print(f"Generations present: {generations}\n")

# For each generation, show parameters
print(f"{'='*100}")
print(f"GENERATION-SPECIFIC PARAMETERS")
print(f"{'='*100}\n")

for generation in generations:
    gen_idx = generation - g_init  # Python 0-indexed

    if gen_idx < 0 or gen_idx >= len(bev['tank_capacity']):
        print(f"Generation {generation}: INDEX OUT OF RANGE (gen_idx={gen_idx})")
        continue

    tank_cap = bev['tank_capacity'][gen_idx]
    W = bev['W'][gen_idx]
    AR = bev['AnnualRange'][gen_idx]

    print(f"Generation {generation} (index {gen_idx}):")
    print(f"  tank_capacity[{gen_idx}] = {tank_cap:.4f} kWh")
    print(f"  W[{gen_idx}] = {W:.4f} tonnes")
    print(f"  AnnualRange[{gen_idx}] = {AR:.4f} km")
    print()

# Verify SOC for sample paths, using CORRECT generation parameters
print(f"{'='*100}")
print(f"VERIFYING INITIAL SOC VALUES (using correct generation parameters)")
print(f"{'='*100}\n")

violations = []
sample_keys = sorted(soc_at_origins.keys())[:20]

for path_id, generation in sample_keys:
    data = soc_at_origins[(path_id, generation)]
    actual_soc = data['soc']
    path = data['path']
    path_length = path['length']

    # Use CORRECT generation-specific parameters
    gen_idx = generation - g_init
    if gen_idx < 0 or gen_idx >= len(bev['tank_capacity']):
        print(f"Path {path_id}, Gen {generation}: INDEX OUT OF RANGE, skipping\n")
        continue

    tank_capacity = bev['tank_capacity'][gen_idx]
    W = bev['W'][gen_idx]
    AnnualRange = bev['AnnualRange'][gen_idx]

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
        print(f"Path {path_id}, Gen {generation}: No f value found, skipping\n")
        continue

    # Calculate expected SOC using generation-specific parameters
    num_vehicles = (path_length / (W * AnnualRange)) * 1000 * f_value
    expected_soc = tank_capacity * num_vehicles

    # Compare
    diff = actual_soc - expected_soc
    diff_pct = (diff / expected_soc * 100) if expected_soc > 0 else 0
    ratio = actual_soc / expected_soc if expected_soc > 0 else 0

    print(f"Path {path_id}, Generation {generation} (index {gen_idx}):")
    print(f"  Path length:              {path_length:>12.4f} km")
    print(f"  W[{gen_idx}]:                    {W:>12.4f} tonnes")
    print(f"  AnnualRange[{gen_idx}]:          {AnnualRange:>12.4f} km")
    print(f"  tank_capacity[{gen_idx}]:        {tank_capacity:>12.4f} kWh")
    print(f"  Flow (f):                 {f_value:>12.8f}")
    print(f"  ")
    print(f"  Num vehicles:             {num_vehicles:>12.8f}")
    print(f"  Expected SOC:             {expected_soc:>12.4f} kWh")
    print(f"  Actual SOC:               {actual_soc:>12.4f} kWh")
    print(f"  ")
    print(f"  Difference:               {diff:>12.4f} kWh ({diff_pct:+.4f}%)")
    print(f"  Ratio (actual/expected):  {ratio:>12.8f}")

    tolerance = 1e-3
    if abs(diff) < tolerance:
        print(f"  [OK] Constraint satisfied")
    else:
        print(f"  [ERROR] Constraint VIOLATED")
        violations.append({
            'path_id': path_id,
            'generation': generation,
            'expected': expected_soc,
            'actual': actual_soc,
            'diff': diff,
            'diff_pct': diff_pct,
            'ratio': ratio
        })

    print()

# Summary
print(f"\n{'='*100}")
print(f"SUMMARY")
print(f"{'='*100}\n")

print(f"Total SOC values at origins: {len(soc_at_origins)}")
print(f"Checks performed:            {len(sample_keys)}")
print(f"Violations found:            {len(violations)}\n")

if violations:
    print(f"VIOLATIONS DETECTED:")

    # Check if all violations have the same ratio
    ratios = [v['ratio'] for v in violations]
    if len(set(f"{r:.6f}" for r in ratios)) == 1:
        print(f"  All violations have IDENTICAL ratio: {ratios[0]:.8f}")
        print(f"  This suggests a SYSTEMATIC error, not random discrepancy")
    else:
        print(f"  Ratios vary: min={min(ratios):.8f}, max={max(ratios):.8f}")

    print(f"\n  Sample violations:")
    for v in violations[:5]:
        print(f"    Path {v['path_id']}, Gen {v['generation']}: ratio={v['ratio']:.8f} ({v['diff_pct']:+.4f}%)")
else:
    print(f"[OK] All initial SOC constraints satisfied!")

print(f"\n{'='*100}\n")
