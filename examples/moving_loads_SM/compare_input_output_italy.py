"""
Direct comparison of INPUT demand (F) vs OPTIMIZED flows (f) for Italian regions.
This will show exactly where the discrepancy lies.
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
print("INPUT vs OUTPUT COMPARISON FOR ITALY")
print("=" * 80)

# Load geographic elements
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
print("=" * 80)

# Create lookups
nuts2_lookup = {}
for geo in geo_elements:
    if geo['type'] == 'node' and 'nuts2_region' in geo and geo['nuts2_region']:
        nuts2_lookup[geo['id']] = {
            'nuts2': geo['nuts2_region'],
            'lat': geo['coordinate_lat'],
            'country': geo['country']
        }

path_lookup = {}
for path in paths:
    path_lookup[path['id']] = {
        'sequence': path['sequence'],
        'distance_from_previous': path['distance_from_previous']
    }

od_lookup = {}
for od in odpairs:
    od_lookup[od['id']] = {
        'origin': od['from'],
        'destination': od['to']
    }

# ============================================================================
# PART 1: Calculate INPUT TKM (from F in Odpair.yaml)
# ============================================================================
print("\nPART 1: Calculating INPUT demand TKM...")

input_tkm_by_nuts2 = defaultdict(float)

for od in odpairs:
    path_id = od.get('path_id')
    F_values = od['F']

    if path_id is None or path_id not in path_lookup:
        continue

    # Use first year
    if F_values and len(F_values) > 0:
        demand = F_values[0]

        path_info = path_lookup[path_id]
        sequence = path_info['sequence']
        distance_from_previous = path_info['distance_from_previous']

        # Calculate TKM through each NUTS2 node
        for i, node_id in enumerate(sequence):
            if node_id not in nuts2_lookup:
                continue

            nuts2 = nuts2_lookup[node_id]['nuts2']
            segment_distance = distance_from_previous[i]
            tkm_segment = demand * segment_distance

            input_tkm_by_nuts2[nuts2] += tkm_segment

# ============================================================================
# PART 2: Calculate OUTPUT TKM (from optimized f)
# ============================================================================
print("PART 2: Calculating OPTIMIZED flow TKM...")

output_tkm_by_nuts2 = defaultdict(float)

for key_str, value in f_data_raw.items():
    flow_value = float(value)

    if flow_value < 0.01:
        continue

    # CORRECT key parsing
    key_tuple = eval(key_str)
    year, (product_id, odpair_id, path_id), (mode_id, techvehicle_id), generation = key_tuple

    if path_id not in path_lookup:
        continue

    path_info = path_lookup[path_id]
    sequence = path_info['sequence']
    distance_from_previous = path_info['distance_from_previous']

    # Calculate TKM through each NUTS2 node
    for i, node_id in enumerate(sequence):
        if node_id not in nuts2_lookup:
            continue

        nuts2 = nuts2_lookup[node_id]['nuts2']
        segment_distance = distance_from_previous[i]
        tkm_segment = flow_value * segment_distance

        output_tkm_by_nuts2[nuts2] += tkm_segment

# ============================================================================
# PART 3: Compare Italian regions
# ============================================================================
print("\n" + "=" * 80)
print("COMPARISON: ITALIAN NUTS2 REGIONS")
print("=" * 80)

italian_comparison = []

for nuts2 in set(list(input_tkm_by_nuts2.keys()) + list(output_tkm_by_nuts2.keys())):
    # Check if Italian
    is_italian = False
    lat = 0
    for node_id, info in nuts2_lookup.items():
        if info['nuts2'] == nuts2:
            is_italian = (info['country'] == 'IT')
            lat = info['lat']
            break

    if not is_italian:
        continue

    input_tkm = input_tkm_by_nuts2.get(nuts2, 0)
    output_tkm = output_tkm_by_nuts2.get(nuts2, 0)
    difference = output_tkm - input_tkm
    pct_change = 100 * difference / input_tkm if input_tkm > 0 else 0

    italian_comparison.append({
        'nuts2': nuts2,
        'lat': lat,
        'input': input_tkm,
        'output': output_tkm,
        'diff': difference,
        'pct': pct_change
    })

# Sort by input TKM
italian_comparison.sort(key=lambda x: x['input'], reverse=True)

print(f"\n{'NUTS2':<10} {'Latitude':>10} {'INPUT TKM':>18} {'OUTPUT TKM':>18} {'Difference':>18} {'Change %':>10}")
print("-" * 95)

total_input_italy = 0
total_output_italy = 0

for region in italian_comparison:
    print(f"{region['nuts2']:<10} {region['lat']:>10.2f} {region['input']:>18,.0f} {region['output']:>18,.0f} {region['diff']:>18,.0f} {region['pct']:>9.1f}%")
    total_input_italy += region['input']
    total_output_italy += region['output']

print("-" * 95)
print(f"{'TOTAL':<10} {' ':>10} {total_input_italy:>18,.0f} {total_output_italy:>18,.0f} {total_output_italy - total_input_italy:>18,.0f} {100*(total_output_italy - total_input_italy)/total_input_italy:>9.1f}%")

# ============================================================================
# PART 4: Overall summary
# ============================================================================
print("\n" + "=" * 80)
print("OVERALL SUMMARY")
print("=" * 80)

total_input_all = sum(input_tkm_by_nuts2.values())
total_output_all = sum(output_tkm_by_nuts2.values())

print(f"\nALL NUTS2 regions:")
print(f"  INPUT TKM:   {total_input_all/1e9:>8.2f} billion")
print(f"  OUTPUT TKM:  {total_output_all/1e9:>8.2f} billion")
print(f"  Difference:  {(total_output_all - total_input_all)/1e9:>8.2f} billion ({100*(total_output_all - total_input_all)/total_input_all:>6.1f}%)")

print(f"\nITALIAN NUTS2 regions:")
print(f"  INPUT TKM:   {total_input_italy/1e9:>8.2f} billion ({100*total_input_italy/total_input_all:>5.1f}% of total)")
print(f"  OUTPUT TKM:  {total_output_italy/1e9:>8.2f} billion ({100*total_output_italy/total_output_all:>5.1f}% of total)")
print(f"  Difference:  {(total_output_italy - total_input_italy)/1e9:>8.2f} billion ({100*(total_output_italy - total_input_italy)/total_input_italy:>6.1f}%)")

# ============================================================================
# CONCLUSION
# ============================================================================
print("\n" + "=" * 80)
print("KEY INSIGHT")
print("=" * 80)

if abs(total_output_all - total_input_all) / total_input_all < 0.01:
    print("\nThe TOTAL TKM is nearly identical between input and output.")
    print("This suggests freight is being RE-ROUTED rather than eliminated.")
else:
    print(f"\nThe TOTAL TKM changed by {100*(total_output_all - total_input_all)/total_input_all:.1f}%.")

if abs(total_output_italy - total_input_italy) / total_input_italy > 0.1:
    reduction_pct = 100 * (total_input_italy - total_output_italy) / total_input_italy
    print(f"\nItaly lost {reduction_pct:.1f}% of its TKM in the optimization.")
    print("This TKM was likely re-routed through other countries or modes.")

print("\n" + "=" * 80)
