"""
Analyze where the imports TO Italy come from.
Which countries are sending freight to Italy?
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
print("ITALY IMPORT ORIGINS ANALYSIS")
print("=" * 80)

# Load data
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

# Create lookups
nuts2_lookup = {}
for geo in geo_elements:
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
        'destination': od['to']
    }

path_lookup = {}
for path in paths:
    path_lookup[path['id']] = {
        'sequence': path['sequence'],
        'distance_from_previous': path['distance_from_previous']
    }

SCALING_FACTOR = 1000

# ============================================================================
# Analyze imports TO Italy by origin country
# ============================================================================
print("\n" + "=" * 80)
print("IMPORTS TO ITALY BY ORIGIN COUNTRY (year 2030)")
print("=" * 80)

import_by_origin = defaultdict(lambda: {'road': 0, 'rail': 0})

for key_str, value in f_data_raw.items():
    flow_value_kt = float(value)

    if flow_value_kt < 0.00001:
        continue

    key_tuple = eval(key_str)
    year, (product_id, odpair_id, path_id), (mode_id, techvehicle_id), generation = key_tuple

    if year != 2030:
        continue

    if odpair_id not in od_lookup or path_id not in path_lookup:
        continue

    od_info = od_lookup[odpair_id]
    origin_id = od_info['origin']
    dest_id = od_info['destination']

    # Get countries
    origin_country = nuts2_lookup.get(origin_id, {}).get('country', 'UNKNOWN')
    dest_country = nuts2_lookup.get(dest_id, {}).get('country', 'UNKNOWN')

    # Only look at imports TO Italy
    if dest_country != 'IT':
        continue

    flow_value_tonnes = flow_value_kt * SCALING_FACTOR
    path_info = path_lookup[path_id]
    sequence = path_info['sequence']
    distance_from_previous = path_info['distance_from_previous']

    mode_name = 'rail' if mode_id == 2 else 'road'

    # Calculate TKM through Italian NUTS2 nodes only
    for i, node_id in enumerate(sequence):
        if node_id in nuts2_lookup and nuts2_lookup[node_id]['country'] == 'IT':
            segment_distance = distance_from_previous[i]
            tkm_segment = flow_value_tonnes * segment_distance
            import_by_origin[origin_country][mode_name] += tkm_segment
            break  # Only count once per flow

# Calculate totals
total_import_tkm = sum(data['road'] + data['rail'] for data in import_by_origin.values())

print(f"\nTotal import TKM to Italy: {total_import_tkm/1e9:.2f} billion")
print(f"\nImports by origin country:")
print("-" * 80)
print(f"{'Origin':<15} {'Road TKM':>18} {'Rail TKM':>18} {'Total TKM':>18} {'% of Total':>12}")
print("-" * 80)

sorted_origins = sorted(
    [(country, data['road'], data['rail'], data['road'] + data['rail'])
     for country, data in import_by_origin.items()],
    key=lambda x: x[3],
    reverse=True
)

for origin, road_tkm, rail_tkm, total_tkm in sorted_origins:
    pct = 100 * total_tkm / total_import_tkm if total_import_tkm > 0 else 0
    print(f"{origin:<15} {road_tkm:>18,.0f} {rail_tkm:>18,.0f} {total_tkm:>18,.0f} {pct:>11.1f}%")

print("-" * 80)
print(f"{'TOTAL':<15} {sum(x[1] for x in sorted_origins):>18,.0f} {sum(x[2] for x in sorted_origins):>18,.0f} {total_import_tkm:>18,.0f} {100.0:>11.1f}%")

# ============================================================================
# Analyze specific OD pairs
# ============================================================================
print("\n" + "=" * 80)
print("TOP 20 SPECIFIC IMPORT FLOWS TO ITALY (year 2030)")
print("=" * 80)

od_pair_details = []

for key_str, value in f_data_raw.items():
    flow_value_kt = float(value)

    if flow_value_kt < 0.00001:
        continue

    key_tuple = eval(key_str)
    year, (product_id, odpair_id, path_id), (mode_id, techvehicle_id), generation = key_tuple

    if year != 2030:
        continue

    if odpair_id not in od_lookup or path_id not in path_lookup:
        continue

    od_info = od_lookup[odpair_id]
    origin_id = od_info['origin']
    dest_id = od_info['destination']

    origin_country = nuts2_lookup.get(origin_id, {}).get('country', 'UNKNOWN')
    dest_country = nuts2_lookup.get(dest_id, {}).get('country', 'UNKNOWN')

    # Only imports to Italy
    if dest_country != 'IT':
        continue

    origin_nuts2 = nuts2_lookup.get(origin_id, {}).get('nuts2', 'UNKNOWN')
    dest_nuts2 = nuts2_lookup.get(dest_id, {}).get('nuts2', 'UNKNOWN')

    flow_value_tonnes = flow_value_kt * SCALING_FACTOR
    path_info = path_lookup[path_id]

    mode_name = 'rail' if mode_id == 2 else 'road'

    # Calculate TKM through Italian nodes
    tkm_in_italy = 0
    for i, node_id in enumerate(path_info['sequence']):
        if node_id in nuts2_lookup and nuts2_lookup[node_id]['country'] == 'IT':
            segment_distance = path_info['distance_from_previous'][i]
            tkm_in_italy += flow_value_tonnes * segment_distance

    if tkm_in_italy > 0:
        od_pair_details.append({
            'origin_country': origin_country,
            'origin_nuts2': origin_nuts2,
            'dest_nuts2': dest_nuts2,
            'mode': mode_name,
            'tkm': tkm_in_italy,
            'flow': flow_value_tonnes
        })

# Sort by TKM
od_pair_details.sort(key=lambda x: x['tkm'], reverse=True)

print(f"\n{'Rank':<6} {'Origin':>8} {'Orig NUTS2':<12} {'Dest NUTS2':<12} {'Mode':<8} {'Flow (t)':>12} {'TKM (M)':>12} {'% of Total':>12}")
print("-" * 100)

for i, od in enumerate(od_pair_details[:20], 1):
    pct = 100 * od['tkm'] / total_import_tkm if total_import_tkm > 0 else 0
    print(f"{i:<6} {od['origin_country']:>8} {od['origin_nuts2']:<12} {od['dest_nuts2']:<12} {od['mode']:<8} {od['flow']:>12,.0f} {od['tkm']/1e6:>12.1f} {pct:>11.2f}%")

# ============================================================================
# Analyze which Italian regions receive the most imports
# ============================================================================
print("\n" + "=" * 80)
print("ITALIAN REGIONS RECEIVING IMPORTS (year 2030)")
print("=" * 80)

import_by_italian_region = defaultdict(float)

for key_str, value in f_data_raw.items():
    flow_value_kt = float(value)

    if flow_value_kt < 0.00001:
        continue

    key_tuple = eval(key_str)
    year, (product_id, odpair_id, path_id), (mode_id, techvehicle_id), generation = key_tuple

    if year != 2030:
        continue

    if odpair_id not in od_lookup or path_id not in path_lookup:
        continue

    od_info = od_lookup[odpair_id]
    dest_id = od_info['destination']

    dest_country = nuts2_lookup.get(dest_id, {}).get('country', 'UNKNOWN')

    if dest_country != 'IT':
        continue

    dest_nuts2 = nuts2_lookup.get(dest_id, {}).get('nuts2', 'UNKNOWN')

    flow_value_tonnes = flow_value_kt * SCALING_FACTOR
    path_info = path_lookup[path_id]

    # Calculate TKM through Italian nodes
    for i, node_id in enumerate(path_info['sequence']):
        if node_id in nuts2_lookup and nuts2_lookup[node_id]['country'] == 'IT':
            segment_distance = path_info['distance_from_previous'][i]
            tkm_segment = flow_value_tonnes * segment_distance

            # Attribute to destination region
            import_by_italian_region[dest_nuts2] += tkm_segment

print(f"\nTop 15 Italian NUTS2 destinations for imports:")
print("-" * 60)
print(f"{'Rank':<6} {'NUTS2':<12} {'TKM (millions)':>18} {'% of Total':>12}")
print("-" * 60)

sorted_dest = sorted(import_by_italian_region.items(), key=lambda x: x[1], reverse=True)

for i, (nuts2, tkm) in enumerate(sorted_dest[:15], 1):
    pct = 100 * tkm / total_import_tkm if total_import_tkm > 0 else 0
    print(f"{i:<6} {nuts2:<12} {tkm/1e6:>18.1f} {pct:>11.1f}%")

# ============================================================================
# Summary
# ============================================================================
print("\n" + "=" * 80)
print("SUMMARY: WHERE DO ITALY'S IMPORTS COME FROM?")
print("=" * 80)

if sorted_origins:
    top_3_origins = sorted_origins[:3]
    top_3_total = sum(x[3] for x in top_3_origins)
    top_3_pct = 100 * top_3_total / total_import_tkm if total_import_tkm > 0 else 0

    print(f"\nTop 3 origin countries:")
    for i, (origin, road, rail, total) in enumerate(top_3_origins, 1):
        pct = 100 * total / total_import_tkm
        print(f"  {i}. {origin}: {total/1e9:.2f}B TKM ({pct:.1f}%)")

    print(f"\nTop 3 countries account for {top_3_pct:.1f}% of import TKM to Italy")

if sorted_dest:
    top_dest = sorted_dest[0]
    print(f"\nTop destination region: {top_dest[0]} ({top_dest[1]/1e9:.2f}B TKM)")
