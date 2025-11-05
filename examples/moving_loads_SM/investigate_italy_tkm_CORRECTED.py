"""
CORRECTED VERSION: Investigate Italy TKM peak with proper key parsing.
This uses the correct f_data key structure:
(year, (product_id, odpair_id, path_id), (mode_id, techvehicle_id), generation)
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
print("INVESTIGATING ITALY TKM PEAK - CORRECTED VERSION")
print("=" * 80)

# Load geographic elements
print("\nLoading GeographicElement.yaml...")
with open(f'{input_dir}/GeographicElement.yaml', 'r', encoding='utf-8') as f:
    geo_elements = yaml.safe_load(f)

# Load OD pairs
print("Loading Odpair.yaml...")
with open(f'{input_dir}/Odpair.yaml', 'r', encoding='utf-8') as f:
    odpairs = yaml.safe_load(f)

# Load paths
print("Loading Path.yaml...")
with open(f'{input_dir}/Path.yaml', 'r', encoding='utf-8') as f:
    paths = yaml.safe_load(f)

# Load flows
import glob
f_dict_files = glob.glob(f'{results_dir}/*_f_dict.yaml')
f_dict_file = sorted(f_dict_files)[-1]
print(f"Loading optimized flows from: {f_dict_file}")
with open(f_dict_file, 'r', encoding='utf-8') as f:
    f_data_raw = yaml.safe_load(f)

print(f"Loaded {len(f_data_raw)} flow entries")
print("=" * 80)

# Create lookups
nuts2_lookup = {}
for geo in geo_elements:
    if geo['type'] == 'node' and 'nuts2_region' in geo and geo['nuts2_region']:
        nuts2_lookup[geo['id']] = {
            'nuts2': geo['nuts2_region'],
            'lat': geo['coordinate_lat'],
            'lon': geo['coordinate_long'],
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
print(f"OD pairs: {len(od_lookup)}")
print(f"Paths: {len(path_lookup)}")

# Italian latitude range
ITALY_LAT_MIN = 38.90
ITALY_LAT_MAX = 46.66

print(f"\nItalian latitude range: {ITALY_LAT_MIN:.2f} - {ITALY_LAT_MAX:.2f}°N")
print("=" * 80)

# Analyze optimized flows with CORRECT key parsing
print("\nAnalyzing optimized flows with CORRECT key structure...")
print("Key structure: (year, (product_id, odpair_id, path_id), (mode_id, techvehicle_id), generation)")
print("=" * 80)

tkm_by_nuts2_mode = defaultdict(lambda: {'road': 0, 'rail': 0, 'lat': 0, 'country': '', 'nuts2': ''})
flows_processed = 0
flows_skipped_no_path = 0
flows_skipped_low_value = 0
unique_paths_used = set()

for key_str, value in f_data_raw.items():
    flow_value = float(value)

    if flow_value < 0.01:
        flows_skipped_low_value += 1
        continue

    # CORRECT key parsing
    key_tuple = eval(key_str)
    year, (product_id, odpair_id, path_id), (mode_id, techvehicle_id), generation = key_tuple

    flows_processed += 1
    if flows_processed % 20000 == 0:
        print(f"  Processed {flows_processed} flows...")

    # Get path info using CORRECT path_id
    if path_id not in path_lookup:
        flows_skipped_no_path += 1
        continue

    unique_paths_used.add(path_id)
    path_info = path_lookup[path_id]
    sequence = path_info['sequence']
    distance_from_previous = path_info['distance_from_previous']

    # Mode name
    mode_name = 'rail' if mode_id == 2 else 'road'

    # Calculate TKM for each NUTS2 node in the path
    for i, node_id in enumerate(sequence):
        if node_id not in nuts2_lookup:
            continue

        node_info = nuts2_lookup[node_id]
        nuts2 = node_info['nuts2']

        # Get TKM segment
        segment_distance = distance_from_previous[i]
        tkm_segment = flow_value * segment_distance

        # Add to totals
        tkm_by_nuts2_mode[nuts2][mode_name] += tkm_segment
        tkm_by_nuts2_mode[nuts2]['lat'] = node_info['lat']
        tkm_by_nuts2_mode[nuts2]['country'] = node_info['country']
        tkm_by_nuts2_mode[nuts2]['nuts2'] = nuts2

print(f"\nProcessed {flows_processed} non-zero flows")
print(f"Skipped {flows_skipped_low_value} flows (< 0.01 tonnes)")
print(f"Skipped {flows_skipped_no_path} flows (path not found)")
print(f"Unique paths used: {len(unique_paths_used)}")
print(f"NUTS2 regions with TKM: {len(tkm_by_nuts2_mode)}")
print("=" * 80)

# Calculate total TKM through ALL NUTS2 regions
total_tkm_all = sum(data['road'] + data['rail'] for data in tkm_by_nuts2_mode.values())
print(f"\nTotal TKM through ALL NUTS2 regions: {total_tkm_all/1e9:.2f} billion")

# Calculate total TKM through Italian NUTS2 regions
italian_regions_tkm = defaultdict(lambda: {'road': 0, 'rail': 0, 'lat': 0, 'nuts2': ''})
for nuts2, data in tkm_by_nuts2_mode.items():
    if data['country'] == 'IT':
        italian_regions_tkm[nuts2] = data

total_italy_tkm = sum(data['road'] + data['rail'] for data in italian_regions_tkm.values())
print(f"Total TKM through Italian NUTS2 regions: {total_italy_tkm/1e9:.2f} billion")
print(f"Italy's share of total TKM: {100*total_italy_tkm/total_tkm_all:.1f}%")

# Top Italian regions
print(f"\nTop 10 Italian NUTS2 regions by TKM:")
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

# Now analyze OD pairs contributing to Italian regions
print("\n" + "=" * 80)
print("OD PAIR ANALYSIS FOR ITALIAN REGIONS")
print("=" * 80)

od_contributions = defaultdict(lambda: {'road': 0, 'rail': 0})

for key_str, value in f_data_raw.items():
    flow_value = float(value)

    if flow_value < 0.01:
        continue

    # CORRECT key parsing
    key_tuple = eval(key_str)
    year, (product_id, odpair_id, path_id), (mode_id, techvehicle_id), generation = key_tuple

    # Get OD info
    if odpair_id not in od_lookup:
        continue

    od_info = od_lookup[odpair_id]
    origin_id = od_info['origin']
    dest_id = od_info['destination']

    # Get origin and destination countries
    origin_country = nuts2_lookup.get(origin_id, {}).get('country', 'UNKNOWN')
    dest_country = nuts2_lookup.get(dest_id, {}).get('country', 'UNKNOWN')

    # Get path info
    if path_id not in path_lookup:
        continue

    path_info = path_lookup[path_id]
    sequence = path_info['sequence']
    distance_from_previous = path_info['distance_from_previous']

    mode_name = 'rail' if mode_id == 2 else 'road'

    # Check if this path passes through ANY Italian NUTS2 region
    passes_through_italy = False
    for i, node_id in enumerate(sequence):
        if node_id in nuts2_lookup and nuts2_lookup[node_id]['country'] == 'IT':
            passes_through_italy = True
            segment_distance = distance_from_previous[i]
            tkm_segment = flow_value * segment_distance

            od_key = f"{origin_country}->{dest_country}"
            od_contributions[od_key][mode_name] += tkm_segment

# Categorize and sort OD pairs
international_only = {}  # X->Y (neither X nor Y is IT)
italian_domestic = {}    # IT->IT
italian_export = {}      # IT->X
italian_import = {}      # X->IT

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
            international_only[od_key] = total_tkm

print(f"\nOD pair breakdown for flows through Italian NUTS2 regions:")
print("-" * 80)
print(f"International freight (X->Y, no IT):  {sum(international_only.values())/1e9:>8.2f}B TKM ({100*sum(international_only.values())/total_italy_tkm:>5.1f}%)")
print(f"Italian domestic (IT->IT):            {sum(italian_domestic.values())/1e9:>8.2f}B TKM ({100*sum(italian_domestic.values())/total_italy_tkm:>5.1f}%)")
print(f"Italian exports (IT->X):              {sum(italian_export.values())/1e9:>8.2f}B TKM ({100*sum(italian_export.values())/total_italy_tkm:>5.1f}%)")
print(f"Italian imports (X->IT):              {sum(italian_import.values())/1e9:>8.2f}B TKM ({100*sum(italian_import.values())/total_italy_tkm:>5.1f}%)")
print("-" * 80)
print(f"TOTAL:                                {total_italy_tkm/1e9:>8.2f}B TKM")

# Show top international OD pairs
if international_only:
    print(f"\nTop 15 INTERNATIONAL OD pairs (X->Y, no IT) through Italian regions:")
    print("-" * 80)
    sorted_international = sorted(international_only.items(), key=lambda x: x[1], reverse=True)
    for i, (od_key, tkm) in enumerate(sorted_international[:15], 1):
        pct = 100 * tkm / total_italy_tkm
        print(f"{i:>3}. {od_key:<15} {tkm:>15,.0f} TKM ({pct:>5.1f}%)")

# CONCLUSION
print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)

if sum(international_only.values()) > total_italy_tkm * 0.5:
    print("\nThe Italy TKM peak is PRIMARILY from international freight (non-Italian OD pairs)")
    print("passing through Italy as a transit corridor.")
elif sum(italian_domestic.values()) > total_italy_tkm * 0.5:
    print("\nThe Italy TKM peak is PRIMARILY from domestic Italian freight (IT->IT).")
else:
    print("\nThe Italy TKM peak is a MIX of international transit, imports, exports, and domestic flows.")

print(f"\nKey finding: {100*sum(international_only.values())/total_italy_tkm:.1f}% of TKM through Italian regions")
print(f"comes from international freight that does NOT originate or terminate in Italy.")

# Save detailed results
output_file = 'italy_tkm_analysis_CORRECTED.txt'
with open(output_file, 'w', encoding='utf-8') as f:
    f.write("=" * 80 + "\n")
    f.write("ITALY TKM INVESTIGATION - CORRECTED VERSION\n")
    f.write("=" * 80 + "\n\n")
    f.write(f"Total TKM through Italian NUTS2 regions: {total_italy_tkm/1e9:.2f} billion\n\n")
    f.write(f"International transit (X->Y, no IT): {sum(international_only.values())/1e9:.2f}B ({100*sum(international_only.values())/total_italy_tkm:.1f}%)\n")
    f.write(f"Domestic (IT->IT): {sum(italian_domestic.values())/1e9:.2f}B ({100*sum(italian_domestic.values())/total_italy_tkm:.1f}%)\n")
    f.write(f"Exports (IT->X): {sum(italian_export.values())/1e9:.2f}B ({100*sum(italian_export.values())/total_italy_tkm:.1f}%)\n")
    f.write(f"Imports (X->IT): {sum(italian_import.values())/1e9:.2f}B ({100*sum(italian_import.values())/total_italy_tkm:.1f}%)\n\n")
    f.write("Top Italian regions by TKM:\n")
    f.write("-" * 80 + "\n")
    for i, (nuts2, lat, road_tkm, rail_tkm, total_tkm) in enumerate(italian_sorted[:10], 1):
        f.write(f"{i}. {nuts2} ({lat:.2f}°N): {total_tkm/1e6:.1f}M TKM\n")

print(f"\nDetailed results saved to: {output_file}")
