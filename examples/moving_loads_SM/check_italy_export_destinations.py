"""
Check where Italy's EXPORTS go - are they to corridor countries or beyond?
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
print("ITALY EXPORT DESTINATIONS ANALYSIS")
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
corridor_countries = ['IT', 'AT', 'DE', 'DK', 'NO', 'SE']

# ============================================================================
# Analyze EXPORTS FROM Italy by destination country
# ============================================================================
print("\n" + "=" * 80)
print("EXPORTS FROM ITALY BY DESTINATION COUNTRY (year 2030)")
print("=" * 80)

export_by_destination = defaultdict(lambda: {'road': 0, 'rail': 0})

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

    # Only look at exports FROM Italy
    if origin_country != 'IT':
        continue

    flow_value_tonnes = flow_value_kt * SCALING_FACTOR
    path_info = path_lookup[path_id]

    mode_name = 'rail' if mode_id == 2 else 'road'

    # Calculate TKM through Italian NUTS2 nodes only
    for i, node_id in enumerate(path_info['sequence']):
        if node_id in nuts2_lookup and nuts2_lookup[node_id]['country'] == 'IT':
            segment_distance = path_info['distance_from_previous'][i]
            tkm_segment = flow_value_tonnes * segment_distance
            export_by_destination[dest_country][mode_name] += tkm_segment
            break  # Only count once per flow

# Calculate totals
total_export_tkm = sum(data['road'] + data['rail'] for data in export_by_destination.values())

print(f"\nTotal export TKM from Italy: {total_export_tkm/1e9:.2f} billion")
print(f"\nExports by destination country:")
print("-" * 80)
print(f"{'Destination':<15} {'Road TKM':>18} {'Rail TKM':>18} {'Total TKM':>18} {'% of Total':>12} {'In Corridor?':>15}")
print("-" * 80)

sorted_destinations = sorted(
    [(country, data['road'], data['rail'], data['road'] + data['rail'])
     for country, data in export_by_destination.items()],
    key=lambda x: x[3],
    reverse=True
)

corridor_export_tkm = 0
non_corridor_export_tkm = 0

for dest, road_tkm, rail_tkm, total_tkm in sorted_destinations:
    pct = 100 * total_tkm / total_export_tkm if total_export_tkm > 0 else 0
    in_corridor = "YES" if dest in corridor_countries else "NO"

    if dest in corridor_countries:
        corridor_export_tkm += total_tkm
    else:
        non_corridor_export_tkm += total_tkm

    print(f"{dest:<15} {road_tkm:>18,.0f} {rail_tkm:>18,.0f} {total_tkm:>18,.0f} {pct:>11.1f}% {in_corridor:>15}")

print("-" * 80)
print(f"{'TOTAL':<15} {sum(x[1] for x in sorted_destinations):>18,.0f} {sum(x[2] for x in sorted_destinations):>18,.0f} {total_export_tkm:>18,.0f} {100.0:>11.1f}%")

# ============================================================================
# Summary by corridor membership
# ============================================================================
print("\n" + "=" * 80)
print("SUMMARY: CORRIDOR vs NON-CORRIDOR DESTINATIONS")
print("=" * 80)

print(f"\nExports to CORRIDOR countries (IT, AT, DE, DK, NO, SE):")
print(f"  TKM: {corridor_export_tkm/1e9:.2f} billion ({100*corridor_export_tkm/total_export_tkm:.1f}%)")

print(f"\nExports to NON-CORRIDOR countries:")
print(f"  TKM: {non_corridor_export_tkm/1e9:.2f} billion ({100*non_corridor_export_tkm/total_export_tkm:.1f}%)")

# ============================================================================
# Check specific OD pairs
# ============================================================================
print("\n" + "=" * 80)
print("TOP 20 SPECIFIC EXPORT FLOWS FROM ITALY (year 2030)")
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

    # Only exports from Italy
    if origin_country != 'IT':
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
            'origin_nuts2': origin_nuts2,
            'dest_country': dest_country,
            'dest_nuts2': dest_nuts2,
            'mode': mode_name,
            'tkm': tkm_in_italy,
            'flow': flow_value_tonnes,
            'in_corridor': dest_country in corridor_countries
        })

# Sort by TKM
od_pair_details.sort(key=lambda x: x['tkm'], reverse=True)

print(f"\n{'Rank':<6} {'Orig NUTS2':<12} {'Dest':>6} {'Dest NUTS2':<12} {'Mode':<8} {'Flow (t)':>12} {'TKM (M)':>12} {'% of Total':>12} {'Corridor?':>10}")
print("-" * 110)

for i, od in enumerate(od_pair_details[:20], 1):
    pct = 100 * od['tkm'] / total_export_tkm if total_export_tkm > 0 else 0
    in_corr = "YES" if od['in_corridor'] else "NO"
    print(f"{i:<6} {od['origin_nuts2']:<12} {od['dest_country']:>6} {od['dest_nuts2']:<12} {od['mode']:<8} {od['flow']:>12,.0f} {od['tkm']/1e6:>12.1f} {pct:>11.2f}% {in_corr:>10}")

print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)

print(f"""
The freight FROM Italy goes to:
  - Corridor countries: {100*corridor_export_tkm/total_export_tkm:.1f}%
  - Non-corridor countries: {100*non_corridor_export_tkm/total_export_tkm:.1f}%

This tells us whether Italian exports stay within the Scandinavian-Mediterranean
corridor or extend to other European countries.
""")
