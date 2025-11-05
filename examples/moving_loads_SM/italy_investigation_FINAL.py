"""
FINAL Italy TKM investigation with correct 1000x scaling factor.
Answers the question: Does the Italy TKM peak come from international freight?
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
print("FINAL ITALY TKM INVESTIGATION (with 1000x scaling)")
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

print(f"\nNUTS2 nodes: {len(nuts2_lookup)}")

# ============================================================================
# Calculate TKM by NUTS2 region with CORRECT scaling
# ============================================================================
print("\n" + "=" * 80)
print("TKM BY NUTS2 REGION (OPTIMIZED FLOWS, year 2030)")
print("=" * 80)

tkm_by_nuts2_mode = defaultdict(lambda: {'road': 0, 'rail': 0, 'lat': 0, 'country': '', 'nuts2': ''})

SCALING_FACTOR = 1000  # f is in kilotonnes, need to convert to tonnes

for key_str, value in f_data_raw.items():
    flow_value_kt = float(value)

    if flow_value_kt < 0.00001:
        continue

    key_tuple = eval(key_str)
    year, (product_id, odpair_id, path_id), (mode_id, techvehicle_id), generation = key_tuple

    # Focus on year 2030 for this analysis
    if year != 2030:
        continue

    if path_id not in path_lookup:
        continue

    flow_value_tonnes = flow_value_kt * SCALING_FACTOR  # Convert to tonnes
    path_info = path_lookup[path_id]
    sequence = path_info['sequence']
    distance_from_previous = path_info['distance_from_previous']

    mode_name = 'rail' if mode_id == 2 else 'road'

    # Calculate TKM for each NUTS2 node in the path
    for i, node_id in enumerate(sequence):
        if node_id not in nuts2_lookup:
            continue

        node_info = nuts2_lookup[node_id]
        nuts2 = node_info['nuts2']

        segment_distance = distance_from_previous[i]
        tkm_segment = flow_value_tonnes * segment_distance

        tkm_by_nuts2_mode[nuts2][mode_name] += tkm_segment
        tkm_by_nuts2_mode[nuts2]['lat'] = node_info['lat']
        tkm_by_nuts2_mode[nuts2]['country'] = node_info['country']
        tkm_by_nuts2_mode[nuts2]['nuts2'] = nuts2

# Calculate totals
total_tkm_all = sum(data['road'] + data['rail'] for data in tkm_by_nuts2_mode.values())

# Italian regions only
italian_regions_tkm = {nuts2: data for nuts2, data in tkm_by_nuts2_mode.items() if data['country'] == 'IT'}
total_italy_tkm = sum(data['road'] + data['rail'] for data in italian_regions_tkm.values())

print(f"\nTotal TKM through ALL NUTS2 regions (2030): {total_tkm_all/1e9:.2f} billion")
print(f"Total TKM through Italian regions (2030): {total_italy_tkm/1e9:.2f} billion")
print(f"Italy's share: {100*total_italy_tkm/total_tkm_all:.1f}%")

# Top Italian regions
print(f"\nTop 10 Italian NUTS2 regions by TKM (year 2030):")
print("-" * 80)
print(f"{'Rank':<6} {'NUTS2':<10} {'Latitude':>10} {'Road TKM':>15} {'Rail TKM':>15} {'Total TKM':>15} {'Rail %':>8}")
print("-" * 80)

italian_sorted = sorted(
    [(nuts2, data['lat'], data['road'], data['rail'], data['road'] + data['rail'])
     for nuts2, data in italian_regions_tkm.items()],
    key=lambda x: x[4],
    reverse=True
)

for i, (nuts2, lat, road_tkm, rail_tkm, total_tkm) in enumerate(italian_sorted[:10], 1):
    rail_pct = 100 * rail_tkm / total_tkm if total_tkm > 0 else 0
    print(f"{i:<6} {nuts2:<10} {lat:>10.2f} {road_tkm:>15,.0f} {rail_tkm:>15,.0f} {total_tkm:>15,.0f} {rail_pct:>7.1f}%")

# ============================================================================
# OD PAIR ANALYSIS FOR ITALIAN REGIONS
# ============================================================================
print("\n" + "=" * 80)
print("OD PAIR BREAKDOWN FOR ITALIAN REGIONS (year 2030)")
print("=" * 80)

od_contributions = defaultdict(lambda: {'road': 0, 'rail': 0})

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

    flow_value_tonnes = flow_value_kt * SCALING_FACTOR
    path_info = path_lookup[path_id]
    sequence = path_info['sequence']
    distance_from_previous = path_info['distance_from_previous']

    mode_name = 'rail' if mode_id == 2 else 'road'

    # Check if path passes through ANY Italian NUTS2 region
    for i, node_id in enumerate(sequence):
        if node_id in nuts2_lookup and nuts2_lookup[node_id]['country'] == 'IT':
            segment_distance = distance_from_previous[i]
            tkm_segment = flow_value_tonnes * segment_distance

            od_key = f"{origin_country}->{dest_country}"
            od_contributions[od_key][mode_name] += tkm_segment
            break  # Only count once per OD pair

# Categorize OD pairs
international_transit = {}  # X->Y (neither X nor Y is IT)
italian_domestic = {}       # IT->IT
italian_export = {}         # IT->X
italian_import = {}         # X->IT

for od_key, modes in od_contributions.items():
    total_tkm = modes['road'] + modes['rail']

    if '->' in od_key:
        origin_c, dest_c = od_key.split('->')

        if origin_c == 'IT' and dest_c == 'IT':
            italian_domestic[od_key] = total_tkm
        elif origin_c == 'IT':
            italian_export[od_key] = total_tkm
        elif dest_c == 'IT':
            italian_import[od_key] = total_tkm
        else:
            international_transit[od_key] = total_tkm

print(f"\nTKM through Italian regions by OD pair type (year 2030):")
print("-" * 80)
print(f"{'Category':<40} {'TKM (billions)':>18} {'Percentage':>12}")
print("-" * 80)

categories = [
    ("International transit (X->Y, no IT)", international_transit),
    ("Italian imports (X->IT)", italian_import),
    ("Italian exports (IT->X)", italian_export),
    ("Italian domestic (IT->IT)", italian_domestic),
]

for cat_name, cat_data in categories:
    total = sum(cat_data.values())
    pct = 100 * total / total_italy_tkm if total_italy_tkm > 0 else 0
    print(f"{cat_name:<40} {total/1e9:>18.2f} {pct:>11.1f}%")

print("-" * 80)
print(f"{'TOTAL':<40} {total_italy_tkm/1e9:>18.2f} {100.0:>11.1f}%")

# Show top international transit flows
if international_transit:
    print(f"\nTop 10 INTERNATIONAL TRANSIT flows (X->Y) through Italy:")
    print("-" * 60)
    sorted_transit = sorted(international_transit.items(), key=lambda x: x[1], reverse=True)
    for i, (od_key, tkm) in enumerate(sorted_transit[:10], 1):
        pct = 100 * tkm / total_italy_tkm
        print(f"{i:>3}. {od_key:<20} {tkm/1e6:>12,.1f} M TKM ({pct:>5.1f}%)")

# ============================================================================
# ANSWER TO THE QUESTION
# ============================================================================
print("\n" + "=" * 80)
print("ANSWER: WHERE DOES THE ITALY TKM PEAK COME FROM?")
print("=" * 80)

international_total = sum(international_transit.values())
international_pct = 100 * international_total / total_italy_tkm if total_italy_tkm > 0 else 0

print(f"\nFor year 2030:")
print(f"  - Peak region: {italian_sorted[0][0]} (Lombardy, northern Italy)")
print(f"  - Peak latitude: {italian_sorted[0][1]:.2f}°N")
print(f"  - Peak TKM: {italian_sorted[0][4]/1e6:.1f} million")
print(f"\n  - International transit (X->Y): {international_total/1e9:.2f}B TKM ({international_pct:.1f}%)")

if international_pct > 50:
    print(f"\n✓ YES: The Italy TKM peak is PRIMARILY from international freight")
    print(f"        ({international_pct:.1f}% of Italian TKM is transit traffic)")
elif international_pct > 20:
    print(f"\n⚠️  MIXED: International transit accounts for {international_pct:.1f}% of Italian TKM")
else:
    print(f"\n✗ NO: International transit is only {international_pct:.1f}% of Italian TKM")
    print(f"       Most TKM comes from imports ({100*sum(italian_import.values())/total_italy_tkm:.1f}%)")
