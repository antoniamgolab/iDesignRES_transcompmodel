"""
Investigate where the "missing" TKM is going - analyze flows through non-NUTS2 nodes.
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
print("ANALYZING NON-NUTS2 ROUTING IN OPTIMIZED FLOWS")
print("=" * 80)

# Load data
print("\nLoading data files...")
with open(f'{input_dir}/GeographicElement.yaml', 'r', encoding='utf-8') as f:
    geo_elements = yaml.safe_load(f)

with open(f'{input_dir}/Path.yaml', 'r', encoding='utf-8') as f:
    paths = yaml.safe_load(f)

import glob
f_dict_files = glob.glob(f'{results_dir}/*_f_dict.yaml')
f_dict_file = sorted(f_dict_files)[-1]
with open(f_dict_file, 'r', encoding='utf-8') as f:
    f_data_raw = yaml.safe_load(f)

print("Data loaded successfully")

# Create lookups
all_nodes = {}
nuts2_nodes = set()

for geo in geo_elements:
    node_id = geo['id']
    all_nodes[node_id] = {
        'type': geo['type'],
        'country': geo.get('country', 'NONE'),
        'nuts2': geo.get('nuts2_region', None),
        'name': geo.get('name', f"node_{node_id}")
    }

    if geo['type'] == 'node' and 'nuts2_region' in geo and geo['nuts2_region']:
        nuts2_nodes.add(node_id)

path_lookup = {}
for path in paths:
    path_lookup[path['id']] = {
        'sequence': path['sequence'],
        'distance_from_previous': path['distance_from_previous']
    }

print(f"\nTotal nodes in network: {len(all_nodes)}")
print(f"NUTS2 nodes: {len(nuts2_nodes)}")
print(f"Non-NUTS2 nodes: {len(all_nodes) - len(nuts2_nodes)}")
print("=" * 80)

# Analyze node types in network
node_type_counts = defaultdict(int)
for node_id, info in all_nodes.items():
    node_type_counts[info['type']] += 1

print("\nNode types in network:")
for node_type, count in sorted(node_type_counts.items()):
    print(f"  {node_type}: {count}")

# Calculate TKM through NUTS2 vs non-NUTS2 nodes
print("\n" + "=" * 80)
print("CALCULATING TKM BY NODE TYPE")
print("=" * 80)

tkm_nuts2 = 0
tkm_non_nuts2 = 0
tkm_by_node_type = defaultdict(float)

flows_processed = 0
for key_str, value in f_data_raw.items():
    flow_value = float(value)

    if flow_value < 0.01:
        continue

    flows_processed += 1
    if flows_processed % 20000 == 0:
        print(f"  Processed {flows_processed} flows...")

    # CORRECT key parsing
    key_tuple = eval(key_str)
    year, (product_id, odpair_id, path_id), (mode_id, techvehicle_id), generation = key_tuple

    if path_id not in path_lookup:
        continue

    path_info = path_lookup[path_id]
    sequence = path_info['sequence']
    distance_from_previous = path_info['distance_from_previous']

    # Calculate TKM for EACH node in path
    for i, node_id in enumerate(sequence):
        if node_id not in all_nodes:
            continue

        segment_distance = distance_from_previous[i]
        tkm_segment = flow_value * segment_distance

        # Categorize by NUTS2 vs non-NUTS2
        if node_id in nuts2_nodes:
            tkm_nuts2 += tkm_segment
        else:
            tkm_non_nuts2 += tkm_segment

        # Also track by node type
        node_type = all_nodes[node_id]['type']
        tkm_by_node_type[node_type] += tkm_segment

print(f"\nProcessed {flows_processed} non-zero flows")
print("\n" + "=" * 80)
print("TKM BY NODE CATEGORY")
print("=" * 80)

total_tkm = tkm_nuts2 + tkm_non_nuts2

print(f"\nNUTS2 nodes:        {tkm_nuts2/1e9:>8.2f} billion TKM ({100*tkm_nuts2/total_tkm:>5.1f}%)")
print(f"Non-NUTS2 nodes:    {tkm_non_nuts2/1e9:>8.2f} billion TKM ({100*tkm_non_nuts2/total_tkm:>5.1f}%)")
print(f"TOTAL:              {total_tkm/1e9:>8.2f} billion TKM")

print("\n" + "=" * 80)
print("TKM BY NODE TYPE")
print("=" * 80)

for node_type in sorted(tkm_by_node_type.keys()):
    tkm = tkm_by_node_type[node_type]
    pct = 100 * tkm / total_tkm
    print(f"{node_type:<20} {tkm/1e9:>8.2f} billion TKM ({pct:>5.1f}%)")

# Sample some paths to see what they look like
print("\n" + "=" * 80)
print("SAMPLE PATH ANALYSIS (first 5 paths with significant flow)")
print("=" * 80)

sample_count = 0
for key_str, value in f_data_raw.items():
    flow_value = float(value)

    if flow_value < 100:  # At least 100 tonnes
        continue

    key_tuple = eval(key_str)
    year, (product_id, odpair_id, path_id), (mode_id, techvehicle_id), generation = key_tuple

    if path_id not in path_lookup:
        continue

    path_info = path_lookup[path_id]
    sequence = path_info['sequence']

    # Count node types in this path
    nuts2_count = 0
    non_nuts2_count = 0
    node_types_in_path = defaultdict(int)

    for node_id in sequence:
        if node_id in nuts2_nodes:
            nuts2_count += 1
        else:
            non_nuts2_count += 1

        if node_id in all_nodes:
            node_type = all_nodes[node_id]['type']
            node_types_in_path[node_type] += 1

    print(f"\nPath {path_id} (flow: {flow_value:.1f} tonnes, mode: {mode_id}, year: {year}):")
    print(f"  Total nodes: {len(sequence)}")
    print(f"  NUTS2 nodes: {nuts2_count}")
    print(f"  Non-NUTS2 nodes: {non_nuts2_count}")
    print(f"  Node types: {dict(node_types_in_path)}")

    # Show first few nodes
    print(f"  First 5 nodes in sequence:")
    for i, node_id in enumerate(sequence[:5]):
        if node_id in all_nodes:
            info = all_nodes[node_id]
            is_nuts2 = "NUTS2" if node_id in nuts2_nodes else "non-NUTS2"
            print(f"    {i+1}. Node {node_id} ({info['type']}, {is_nuts2}): {info.get('nuts2', 'N/A')}")

    sample_count += 1
    if sample_count >= 5:
        break

print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)

if tkm_non_nuts2 > tkm_nuts2:
    pct_non_nuts2 = 100 * tkm_non_nuts2 / total_tkm
    print(f"\n{pct_non_nuts2:.1f}% of TKM flows through NON-NUTS2 nodes.")
    print("The optimization is routing freight through synthetic/highway nodes")
    print("instead of NUTS2 regional nodes.")
    print("\nThis explains why the latitude visualizations show much lower TKM")
    print("than the input demand - most freight is not passing through NUTS2 nodes!")
else:
    print("\nMost TKM flows through NUTS2 nodes as expected.")
