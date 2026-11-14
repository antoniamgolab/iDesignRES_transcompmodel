"""
Check if the condition at line 3624 (geo_id == origin_id) is ever true.

This script verifies whether p_r_k_g_pairs actually contains entries where
geo_id matches the origin of the path (path.sequence[0]).
"""

import yaml
from collections import defaultdict

base_path = "C:/Users/simuser/Documents/AntoniaGolab/Scand_Med_analysis/SM_baby_2/iDesignRES_transcompmodel/examples/moving_loads_SM"
case_name = "case_20251110_160304_var_var"
input_dir = f"{base_path}/input_data/{case_name}"

print(f"\n{'='*100}")
print(f"CHECKING IF geo_id == origin_id CONDITION IS EVER TRUE")
print(f"{'='*100}\n")

# Load input data
print("Loading input data...")
with open(f"{input_dir}/Path.yaml", 'r') as f:
    paths = yaml.safe_load(f)

with open(f"{input_dir}/Odpair.yaml", 'r') as f:
    odpairs = yaml.safe_load(f)

# Build path lookup
path_dict = {p['id']: p for p in paths}

print(f"Loaded {len(paths)} paths, {len(odpairs)} OD pairs\n")

# Simulate p_r_k_g_pairs construction
# p_r_k_g_pairs = (product_id, odpair_id, path_id, geo_id)
# It should contain all geo nodes along each path for each odpair

print("Constructing p_r_k_g_pairs set (simulating Julia's create_p_r_k_g_pairs)...")
p_r_k_g_pairs = set()

# In this case, all odpairs have product='freight' which has ID=0
# We'll map the product string to ID, or just use 0 for all
for odpair in odpairs:
    # Product is a string like 'freight' in YAML, maps to Product ID 0
    product_id = 0  # Hardcoded since all odpairs use 'freight' = product ID 0
    odpair_id = odpair['id']

    # In YAML, each odpair has path_id (singular)
    # Julia converts this to paths=[single_path] (array with one element)
    if 'path_id' not in odpair:
        continue

    path_id = odpair['path_id']
    if path_id not in path_dict:
        continue

    path = path_dict[path_id]
    sequence = path['sequence']

    # Add entry for each geo in the sequence
    for geo in sequence:
        # Handle both dict and int formats
        if isinstance(geo, dict):
            geo_id = geo['id']
        else:
            geo_id = geo

        p_r_k_g_pairs.add((product_id, odpair_id, path_id, geo_id))

print(f"Created p_r_k_g_pairs with {len(p_r_k_g_pairs):,} entries\n")

# Now check: for how many entries is geo_id == origin_id?
print(f"{'='*100}")
print(f"CHECKING CONDITION: geo_id == origin_id")
print(f"{'='*100}\n")

origin_checks = 0
origin_matches = 0
sample_matches = []

for entry in p_r_k_g_pairs:
    product_id, odpair_id, path_id, geo_id = entry

    origin_checks += 1

    path = path_dict[path_id]
    sequence = path['sequence']

    # Get origin geo ID
    if isinstance(sequence[0], dict):
        origin_id = sequence[0]['id']
    else:
        origin_id = sequence[0]

    # Check if condition is true
    if geo_id == origin_id:
        origin_matches += 1

        if len(sample_matches) < 10:
            sample_matches.append((path_id, geo_id, origin_id))

print(f"Total checks: {origin_checks:,}")
print(f"Origin matches: {origin_matches:,}")
print(f"Percentage: {100 * origin_matches / origin_checks:.2f}%\n")

if origin_matches > 0:
    print(f"✓ CONDITION IS TRUE for {origin_matches:,} entries")
    print(f"  This means the initial SOC constraint IS being applied")
    print(f"\n  Sample matches (path_id, geo_id, origin_id):")
    for match in sample_matches:
        print(f"    {match}")
else:
    print(f"✗ CONDITION IS NEVER TRUE!")
    print(f"  This means the initial SOC equality constraint is NEVER applied!")
    print(f"  This explains why SOC values don't match the expected formula")

    # Show why
    print(f"\n  Let's check a few examples:")
    count = 0
    for entry in list(p_r_k_g_pairs)[:5]:
        product_id, odpair_id, path_id, geo_id = entry
        path = path_dict[path_id]
        sequence = path['sequence']

        if isinstance(sequence[0], dict):
            origin_id = sequence[0]['id']
        else:
            origin_id = sequence[0]

        print(f"    Path {path_id}: geo_id={geo_id}, origin_id={origin_id}, match={geo_id == origin_id}")
        count += 1
        if count >= 5:
            break

print(f"\n{'='*100}\n")
