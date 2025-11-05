"""
Investigate why TKM drops 94.5% between input and output.
The issue might be in how distance_from_previous is calculated or aggregated.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import yaml
from collections import defaultdict
import numpy as np

# Load data
case_study_name = 'case_20251103_114421'
input_dir = f'input_data/{case_study_name}'
results_dir = f'results/{case_study_name}'

print("=" * 80)
print("INVESTIGATING PATH AGGREGATION AND TKM CALCULATION")
print("=" * 80)

# Load data
print("\nLoading data files...")
with open(f'{input_dir}/GeographicElement.yaml', 'r', encoding='utf-8') as f:
    geo_elements = yaml.safe_load(f)

with open(f'{input_dir}/Odpair.yaml', 'r', encoding='utf-8') as f:
    odpairs = yaml.safe_load(f)

with open(f'{input_dir}/Path.yaml', 'r', encoding='utf-8') as f:
    paths = yaml.safe_load(f)

import glob
f_dict_files = glob.glob(f'{results_dir}/*_f_dict.yaml')
f_dict_file = sorted(f_dict_files)[-1]
with open(f_dict_file, 'r', encoding='utf-8') as f:
    f_data_raw = yaml.safe_load(f)

print("Data loaded successfully")

# Create lookups
path_lookup = {}
for path in paths:
    total_distance = sum(path['distance_from_previous'])
    path_lookup[path['id']] = {
        'sequence': path['sequence'],
        'distance_from_previous': path['distance_from_previous'],
        'total_distance': total_distance,
        'num_nodes': len(path['sequence'])
    }

od_lookup = {}
for od in odpairs:
    od_lookup[od['id']] = {
        'origin': od['from'],
        'destination': od['to'],
        'F': od['F'],
        'path_id': od.get('path_id')
    }

print("\n" + "=" * 80)
print("PATH STRUCTURE ANALYSIS")
print("=" * 80)

# Analyze path lengths
path_lengths = []
path_distances = []

for path_id, info in path_lookup.items():
    path_lengths.append(info['num_nodes'])
    path_distances.append(info['total_distance'])

print(f"\nTotal paths: {len(path_lookup)}")
print(f"\nPath lengths (number of nodes):")
print(f"  Min:     {min(path_lengths)}")
print(f"  Max:     {max(path_lengths)}")
print(f"  Mean:    {np.mean(path_lengths):.1f}")
print(f"  Median:  {np.median(path_lengths):.1f}")

print(f"\nPath total distances (km):")
print(f"  Min:     {min(path_distances):.1f}")
print(f"  Max:     {max(path_distances):.1f}")
print(f"  Mean:    {np.mean(path_distances):.1f}")
print(f"  Median:  {np.median(path_distances):.1f}")

# Count paths by length
length_distribution = defaultdict(int)
for length in path_lengths:
    length_distribution[length] += 1

print(f"\nPath length distribution:")
for length in sorted(length_distribution.keys())[:20]:  # Show first 20
    count = length_distribution[length]
    pct = 100 * count / len(path_lengths)
    print(f"  {length:3d} nodes: {count:5d} paths ({pct:5.1f}%)")

# ============================================================================
# Compare INPUT tonnage vs OPTIMIZED tonnage
# ============================================================================
print("\n" + "=" * 80)
print("TONNAGE COMPARISON (INPUT F vs OPTIMIZED f)")
print("=" * 80)

# Calculate total INPUT tonnage (F, first year)
total_input_tonnage = 0
for od in odpairs:
    F_values = od['F']
    if F_values and len(F_values) > 0:
        total_input_tonnage += F_values[0]

print(f"\nTotal INPUT tonnage (F, year 0): {total_input_tonnage:,.0f} tonnes")

# Calculate total OPTIMIZED tonnage (f, aggregated across all years/modes/techvehicles)
# We need to be careful not to double-count flows
unique_odpair_tonnage = defaultdict(float)

for key_str, value in f_data_raw.items():
    flow_value = float(value)

    if flow_value < 0.01:
        continue

    key_tuple = eval(key_str)
    year, (product_id, odpair_id, path_id), (mode_id, techvehicle_id), generation = key_tuple

    # For a fair comparison with input F, we should sum across all years/modes/techvehicles for each OD pair
    unique_odpair_tonnage[odpair_id] += flow_value

total_output_tonnage = sum(unique_odpair_tonnage.values())

print(f"Total OPTIMIZED tonnage (f, all years/modes/techvehicles): {total_output_tonnage:,.0f} tonnes")
print(f"Difference: {total_output_tonnage - total_input_tonnage:,.0f} tonnes ({100*(total_output_tonnage - total_input_tonnage)/total_input_tonnage:+.1f}%)")

# ============================================================================
# Calculate INPUT TKM and OUTPUT TKM using SAME method
# ============================================================================
print("\n" + "=" * 80)
print("TKM CALCULATION COMPARISON")
print("=" * 80)

# INPUT TKM (F * total distance for each OD pair)
total_input_tkm = 0
for od in odpairs:
    F_values = od['F']
    path_id = od.get('path_id')

    if F_values and len(F_values) > 0 and path_id and path_id in path_lookup:
        demand = F_values[0]
        distance = path_lookup[path_id]['total_distance']
        tkm = demand * distance
        total_input_tkm += tkm

print(f"\nINPUT TKM (F × total path distance): {total_input_tkm/1e9:.3f} billion")

# OUTPUT TKM (f × total distance for each flow)
total_output_tkm = 0
for key_str, value in f_data_raw.items():
    flow_value = float(value)

    if flow_value < 0.01:
        continue

    key_tuple = eval(key_str)
    year, (product_id, odpair_id, path_id), (mode_id, techvehicle_id), generation = key_tuple

    if path_id in path_lookup:
        distance = path_lookup[path_id]['total_distance']
        tkm = flow_value * distance
        total_output_tkm += tkm

print(f"OUTPUT TKM (f × total path distance): {total_output_tkm/1e9:.3f} billion")
print(f"Difference: {(total_output_tkm - total_input_tkm)/1e9:.3f} billion ({100*(total_output_tkm - total_input_tkm)/total_input_tkm:+.1f}%)")

# ============================================================================
# Investigate distance_from_previous usage
# ============================================================================
print("\n" + "=" * 80)
print("DISTANCE_FROM_PREVIOUS ANALYSIS")
print("=" * 80)

# Sample 10 paths and show their distance_from_previous structure
print("\nSample paths (first 10 with flow > 100 tonnes):")

sample_count = 0
for key_str, value in f_data_raw.items():
    flow_value = float(value)

    if flow_value < 100:
        continue

    key_tuple = eval(key_str)
    year, (product_id, odpair_id, path_id), (mode_id, techvehicle_id), generation = key_tuple

    if path_id not in path_lookup:
        continue

    path_info = path_lookup[path_id]
    sequence = path_info['sequence']
    distances = path_info['distance_from_previous']
    total_dist = path_info['total_distance']

    print(f"\nPath {path_id} (flow: {flow_value:.1f} tonnes):")
    print(f"  Nodes: {len(sequence)}")
    print(f"  Sequence: {sequence}")
    print(f"  distance_from_previous: {distances}")
    print(f"  Total distance: {total_dist:.1f} km")
    print(f"  TKM (flow × total): {flow_value * total_dist:,.0f}")

    # Calculate TKM using distance_from_previous method (as done in visualization)
    tkm_by_segment = []
    for i, dist in enumerate(distances):
        segment_tkm = flow_value * dist
        tkm_by_segment.append(segment_tkm)

    print(f"  TKM by segment: {[f'{tkm:,.0f}' for tkm in tkm_by_segment]}")
    print(f"  Sum of segment TKM: {sum(tkm_by_segment):,.0f}")

    sample_count += 1
    if sample_count >= 10:
        break

# ============================================================================
# CONCLUSION
# ============================================================================
print("\n" + "=" * 80)
print("ROOT CAUSE ANALYSIS")
print("=" * 80)

print("\nKey findings:")
print(f"1. INPUT tonnage (F):    {total_input_tonnage/1e6:>8.2f} million tonnes")
print(f"2. OUTPUT tonnage (f):   {total_output_tonnage/1e6:>8.2f} million tonnes")
print(f"   Tonnage ratio:        {100*total_output_tonnage/total_input_tonnage:>7.1f}%")
print()
print(f"3. INPUT TKM:            {total_input_tkm/1e9:>8.3f} billion")
print(f"4. OUTPUT TKM:           {total_output_tkm/1e9:>8.3f} billion")
print(f"   TKM ratio:            {100*total_output_tkm/total_input_tkm:>7.1f}%")

if total_output_tonnage / total_input_tonnage > 10:
    print("\nThe optimized tonnage is MUCH HIGHER than input tonnage!")
    print("This suggests the optimization is creating flows across multiple years/modes/techvehicles")
    print("that sum to more than the original input demand F.")
    print("\nThe TKM calculation multiplies this inflated tonnage by distance,")
    print("resulting in a TKM value that may not be directly comparable to input F.")
