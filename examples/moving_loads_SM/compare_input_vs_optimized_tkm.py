"""
Compare input demand (F) vs optimized flows (f) to identify where TKM goes to zero.
This will help determine if the issue is in the optimization or data structure.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import yaml
from collections import defaultdict

# Load data
case_study_name = 'case_20251103_114421'
input_dir = f'input_data/{case_study_name}'
results_dir = f'results/{case_study_name}'

print("=" * 80)
print("COMPARING INPUT DEMAND (F) vs OPTIMIZED FLOWS (f)")
print("=" * 80)

# Load geographic elements
print("\nLoading GeographicElement.yaml...")
with open(f'{input_dir}/GeographicElement.yaml', 'r', encoding='utf-8') as f:
    geo_elements = yaml.safe_load(f)

# Load OD pairs (contains input demand F)
print("Loading Odpair.yaml...")
with open(f'{input_dir}/Odpair.yaml', 'r', encoding='utf-8') as f:
    odpairs = yaml.safe_load(f)

# Load paths
print("Loading Path.yaml...")
with open(f'{input_dir}/Path.yaml', 'r', encoding='utf-8') as f:
    paths = yaml.safe_load(f)

# Load optimized flows
import glob
f_dict_files = glob.glob(f'{results_dir}/*_f_dict.yaml')
f_dict_file = sorted(f_dict_files)[-1]
print(f"Loading optimized flows from: {f_dict_file}")
with open(f_dict_file, 'r', encoding='utf-8') as f:
    f_data_raw = yaml.safe_load(f)

# Convert optimized flows
f_optimized = {}
for key_str, value in f_data_raw.items():
    key_tuple = eval(key_str)
    f_optimized[key_tuple] = float(value)

print(f"Loaded {len(f_optimized)} optimized flow entries")
print("=" * 80)

# Create lookups
nuts2_lookup = {}
all_nodes_lookup = {}
for geo in geo_elements:
    all_nodes_lookup[geo['id']] = {
        'type': geo['type'],
        'country': geo.get('country', 'NONE'),
        'name': geo.get('name', f"node_{geo['id']}")
    }

    if geo['type'] == 'node' and 'nuts2_region' in geo and geo['nuts2_region']:
        nuts2_lookup[geo['id']] = {
            'nuts2': geo['nuts2_region'],
            'lat': geo['coordinate_lat'],
            'country': geo['country']
        }

od_lookup = {}
for od in odpairs:
    od_lookup[od['id']] = {
        'origin': od['from'],
        'destination': od['to'],
        'F': od['F'],  # Input demand by year
        'path_id': od.get('path_id', None)
    }

path_lookup = {}
for path in paths:
    path_lookup[path['id']] = {
        'sequence': path['sequence'],
        'distance_from_previous': path['distance_from_previous']
    }

print(f"\nNUTS2 nodes: {len(nuts2_lookup)}")
print(f"Total nodes: {len(all_nodes_lookup)}")
print(f"OD pairs: {len(od_lookup)}")
print(f"Paths: {len(path_lookup)}")

# ============================================================================
# PART 1: Analyze INPUT DEMAND (F) - TKM by NUTS2
# ============================================================================
print("\n" + "=" * 80)
print("PART 1: INPUT DEMAND (F) - TKM BY NUTS2 REGION")
print("=" * 80)

tkm_input_nuts2 = defaultdict(lambda: {'road': 0, 'rail': 0, 'country': '', 'nuts2': ''})

# For input demand, we need to assume mode split or check if paths have mode info
# Let's calculate total TKM from input demand through NUTS2 nodes
for od in odpairs:
    odpair_id = od['id']
    origin_id = od['from']
    dest_id = od['to']
    F_values = od['F']  # List of demand by year
    path_id = od.get('path_id')

    if path_id is None or path_id not in path_lookup:
        continue

    path_info = path_lookup[path_id]
    sequence = path_info['sequence']
    distance_from_previous = path_info['distance_from_previous']

    # Use first year's demand for comparison
    if F_values and len(F_values) > 0:
        demand = F_values[0]  # First year

        # Calculate TKM through each NUTS2 node
        for i, node_id in enumerate(sequence):
            if node_id not in nuts2_lookup:
                continue

            node_info = nuts2_lookup[node_id]
            nuts2 = node_info['nuts2']

            segment_distance = distance_from_previous[i]
            tkm_segment = demand * segment_distance

            # For input, we don't know mode, so put in 'road' category
            tkm_input_nuts2[nuts2]['road'] += tkm_segment
            tkm_input_nuts2[nuts2]['country'] = node_info['country']
            tkm_input_nuts2[nuts2]['nuts2'] = nuts2

print(f"\nNUTS2 regions with INPUT demand TKM: {len(tkm_input_nuts2)}")

if tkm_input_nuts2:
    # Sort by total TKM
    input_sorted = sorted(
        [(nuts2, data['road'] + data['rail'], data['country'])
         for nuts2, data in tkm_input_nuts2.items()],
        key=lambda x: x[1],
        reverse=True
    )

    print(f"\nTop 10 NUTS2 regions by INPUT demand TKM:")
    print("-" * 80)
    print(f"{'NUTS2':<10} {'Country':<10} {'TKM':>20}")
    print("-" * 80)
    for nuts2, tkm, country in input_sorted[:10]:
        print(f"{nuts2:<10} {country:<10} {tkm:>20,.0f}")

# ============================================================================
# PART 2: Analyze OPTIMIZED FLOWS (f) - TKM by NUTS2
# ============================================================================
print("\n" + "=" * 80)
print("PART 2: OPTIMIZED FLOWS (f) - TKM BY NUTS2 REGION")
print("=" * 80)

tkm_optimized_nuts2 = defaultdict(lambda: {'road': 0, 'rail': 0, 'country': '', 'nuts2': ''})

for key, flow_value in f_optimized.items():
    if flow_value < 0.01:
        continue

    odpair_id, path_id, mode_id, year_idx = key

    if path_id not in path_lookup:
        continue

    path_info = path_lookup[path_id]
    sequence = path_info['sequence']
    distance_from_previous = path_info['distance_from_previous']

    mode_name = 'rail' if mode_id == 2 else 'road'

    # Calculate TKM through each NUTS2 node
    for i, node_id in enumerate(sequence):
        if node_id not in nuts2_lookup:
            continue

        node_info = nuts2_lookup[node_id]
        nuts2 = node_info['nuts2']

        segment_distance = distance_from_previous[i]
        tkm_segment = flow_value * segment_distance

        tkm_optimized_nuts2[nuts2][mode_name] += tkm_segment
        tkm_optimized_nuts2[nuts2]['country'] = node_info['country']
        tkm_optimized_nuts2[nuts2]['nuts2'] = nuts2

print(f"\nNUTS2 regions with OPTIMIZED flow TKM: {len(tkm_optimized_nuts2)}")

if tkm_optimized_nuts2:
    # Sort by total TKM
    optimized_sorted = sorted(
        [(nuts2, data['road'] + data['rail'], data['country'])
         for nuts2, data in tkm_optimized_nuts2.items()],
        key=lambda x: x[1],
        reverse=True
    )

    print(f"\nTop 10 NUTS2 regions by OPTIMIZED flow TKM:")
    print("-" * 80)
    print(f"{'NUTS2':<10} {'Country':<10} {'TKM':>20}")
    print("-" * 80)
    for nuts2, tkm, country in optimized_sorted[:10]:
        print(f"{nuts2:<10} {country:<10} {tkm:>20,.0f}")

# ============================================================================
# PART 3: Check which node types are actually used
# ============================================================================
print("\n" + "=" * 80)
print("PART 3: NODE TYPE USAGE ANALYSIS")
print("=" * 80)

# Check input paths
input_node_types = defaultdict(int)
input_nodes_used = set()

for od in odpairs:
    path_id = od.get('path_id')
    if path_id is None or path_id not in path_lookup:
        continue

    sequence = path_lookup[path_id]['sequence']
    for node_id in sequence:
        input_nodes_used.add(node_id)
        if node_id in all_nodes_lookup:
            node_type = all_nodes_lookup[node_id]['type']
            input_node_types[node_type] += 1

print("\nNode types in INPUT paths:")
for node_type, count in sorted(input_node_types.items()):
    print(f"  {node_type}: {count}")

# Check optimized paths
optimized_node_types = defaultdict(int)
optimized_nodes_used = set()
optimized_paths_used = set()

for key, flow_value in f_optimized.items():
    if flow_value < 0.01:
        continue

    odpair_id, path_id, mode_id, year_idx = key

    if path_id not in path_lookup:
        continue

    optimized_paths_used.add(path_id)
    sequence = path_lookup[path_id]['sequence']

    for node_id in sequence:
        optimized_nodes_used.add(node_id)
        if node_id in all_nodes_lookup:
            node_type = all_nodes_lookup[node_id]['type']
            optimized_node_types[node_type] += 1

print("\nNode types in OPTIMIZED flow paths:")
for node_type, count in sorted(optimized_node_types.items()):
    print(f"  {node_type}: {count}")

print(f"\nUnique nodes in INPUT paths: {len(input_nodes_used)}")
print(f"Unique nodes in OPTIMIZED paths: {len(optimized_nodes_used)}")
print(f"Unique paths in OPTIMIZED flows: {len(optimized_paths_used)}")

# Check NUTS2 nodes specifically
nuts2_in_input = len([n for n in input_nodes_used if n in nuts2_lookup])
nuts2_in_optimized = len([n for n in optimized_nodes_used if n in nuts2_lookup])

print(f"\nNUTS2 nodes in INPUT paths: {nuts2_in_input}")
print(f"NUTS2 nodes in OPTIMIZED paths: {nuts2_in_optimized}")

# ============================================================================
# PART 4: Sample path comparison
# ============================================================================
print("\n" + "=" * 80)
print("PART 4: SAMPLE PATH ANALYSIS")
print("=" * 80)

# Take first 5 paths with optimized flow and check their structure
sample_count = 0
for key, flow_value in f_optimized.items():
    if flow_value < 0.01:
        continue

    odpair_id, path_id, mode_id, year_idx = key

    if path_id not in path_lookup:
        continue

    path_info = path_lookup[path_id]
    sequence = path_info['sequence']

    # Count node types in this path
    node_types_in_path = defaultdict(int)
    nuts2_count = 0

    for node_id in sequence:
        if node_id in all_nodes_lookup:
            node_type = all_nodes_lookup[node_id]['type']
            node_types_in_path[node_type] += 1
        if node_id in nuts2_lookup:
            nuts2_count += 1

    print(f"\nPath {path_id} (flow: {flow_value:.1f} tonnes):")
    print(f"  Total nodes: {len(sequence)}")
    print(f"  NUTS2 nodes: {nuts2_count}")
    print(f"  Node types: {dict(node_types_in_path)}")

    sample_count += 1
    if sample_count >= 5:
        break

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("SUMMARY AND DIAGNOSIS")
print("=" * 80)

total_input_tkm = sum(data['road'] + data['rail'] for data in tkm_input_nuts2.values())
total_optimized_tkm = sum(data['road'] + data['rail'] for data in tkm_optimized_nuts2.values())

print(f"\nTotal TKM through NUTS2 regions:")
print(f"  INPUT demand (F):      {total_input_tkm:>20,.0f}")
print(f"  OPTIMIZED flows (f):   {total_optimized_tkm:>20,.0f}")
print(f"  Difference:            {total_input_tkm - total_optimized_tkm:>20,.0f}")

if total_input_tkm > 0 and total_optimized_tkm == 0:
    print("\nDIAGNOSIS: Optimization re-routes ALL freight away from NUTS2 nodes!")
    print("This suggests the model found cheaper/faster paths through non-NUTS2 nodes.")
elif total_input_tkm == 0:
    print("\nDIAGNOSIS: Input paths already don't use NUTS2 nodes!")
    print("The issue is in the path definitions, not the optimization.")
else:
    pct_retained = 100 * total_optimized_tkm / total_input_tkm
    print(f"\nOptimization retains {pct_retained:.1f}% of TKM through NUTS2 nodes")
