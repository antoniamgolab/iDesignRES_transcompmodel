"""
Analyze which OD pairs are being attributed to Italian latitude range in visualizations.
This will help identify if there's incorrect mapping of flows to regions.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import yaml
from collections import defaultdict

# Load data
case_study_name = 'case_20251103_114421'
input_dir = f'input_data/{case_study_name}'
results_dir = f'results/{case_study_name}'

print(f"Analyzing latitude attribution for Italy")
print("=" * 80)

# Load geographic elements
print("Loading GeographicElement.yaml...")
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
print(f"Loading flow data from: {f_dict_file}")
with open(f_dict_file, 'r', encoding='utf-8') as f:
    f_data_raw = yaml.safe_load(f)

# Convert f_data
f_data = {}
for key_str, value in f_data_raw.items():
    key_tuple = eval(key_str)
    f_data[key_tuple] = float(value)

print(f"Loaded {len(f_data)} flow entries")
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

# Define Italian latitude range (from your data)
ITALY_LAT_MIN = 38.90
ITALY_LAT_MAX = 46.66

print(f"\nAnalyzing flows attributed to Italian latitude range ({ITALY_LAT_MIN:.2f}-{ITALY_LAT_MAX:.2f}°N)")
print("=" * 80)

# Track TKM by latitude and OD pair
tkm_by_lat_and_od = defaultdict(lambda: defaultdict(float))
total_tkm_in_italy_range = 0
flows_checked = 0

# Analyze flows - replicate the notebook calculation
for key, flow_value in f_data.items():
    if flow_value < 0.01:
        continue

    flows_checked += 1
    if flows_checked % 10000 == 0:
        print(f"  Processed {flows_checked} flows...")

    odpair_id, path_id, mode_id, year_idx = key

    # Get OD pair info
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

    # Calculate TKM for each node (as done in the notebook)
    for i, node_id in enumerate(sequence):
        if node_id not in nuts2_lookup:
            continue

        node_info = nuts2_lookup[node_id]
        lat = node_info['lat']

        # Check if this node is in Italian latitude range
        if ITALY_LAT_MIN <= lat <= ITALY_LAT_MAX:
            segment_distance = distance_from_previous[i]
            tkm_segment = flow_value * segment_distance

            od_key = f"{origin_country}->{dest_country}"
            tkm_by_lat_and_od[lat][od_key] += tkm_segment
            total_tkm_in_italy_range += tkm_segment

print(f"\n\nTotal TKM in Italian latitude range: {total_tkm_in_italy_range:,.0f}")
print("=" * 80)

# Summarize by OD pair across all latitudes in Italy range
od_pair_summary = defaultdict(float)
for lat_dict in tkm_by_lat_and_od.values():
    for od_key, tkm in lat_dict.items():
        od_pair_summary[od_key] += tkm

print(f"\nTop 20 OD pairs contributing to Italian latitude range TKM:")
print("-" * 80)
print(f"{'Rank':<6} {'OD Pair':<20} {'TKM':>15} {'% of Total':>12}")
print("-" * 80)

sorted_od = sorted(od_pair_summary.items(), key=lambda x: x[1], reverse=True)
for i, (od_key, tkm) in enumerate(sorted_od[:20], 1):
    pct = 100 * tkm / total_tkm_in_italy_range if total_tkm_in_italy_range > 0 else 0
    print(f"{i:<6} {od_key:<20} {tkm:>15,.0f} {pct:>11.1f}%")

# Now check which specific latitudes have the highest TKM
print(f"\n\nTop 20 specific latitudes with highest TKM:")
print("-" * 80)
print(f"{'Rank':<6} {'Latitude':<12} {'Country':<10} {'NUTS2':<10} {'TKM':>15}")
print("-" * 80)

lat_totals = {}
lat_info = {}
for lat, od_dict in tkm_by_lat_and_od.items():
    total = sum(od_dict.values())
    lat_totals[lat] = total
    # Find the NUTS2 region and country at this latitude
    for geo_id, info in nuts2_lookup.items():
        if abs(info['lat'] - lat) < 0.001:
            lat_info[lat] = (info['country'], info['nuts2'])
            break

sorted_lats = sorted(lat_totals.items(), key=lambda x: x[1], reverse=True)
for i, (lat, tkm) in enumerate(sorted_lats[:20], 1):
    country, nuts2 = lat_info.get(lat, ('?', '?'))
    print(f"{i:<6} {lat:<12.4f} {country:<10} {nuts2:<10} {tkm:>15,.0f}")

# For the top latitude, show detailed OD breakdown
if sorted_lats:
    top_lat, top_tkm = sorted_lats[0]
    country, nuts2 = lat_info.get(top_lat, ('?', '?'))

    print(f"\n\nDetailed breakdown for highest TKM latitude: {top_lat:.4f}°N ({country} - {nuts2})")
    print("=" * 80)
    print(f"{'OD Pair':<20} {'TKM':>15} {'% of Latitude':>15}")
    print("-" * 80)

    lat_od_dict = tkm_by_lat_and_od[top_lat]
    sorted_lat_od = sorted(lat_od_dict.items(), key=lambda x: x[1], reverse=True)

    for od_key, tkm in sorted_lat_od[:15]:
        pct = 100 * tkm / top_tkm if top_tkm > 0 else 0
        print(f"{od_key:<20} {tkm:>15,.0f} {pct:>14.1f}%")

print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)

# Check if any flows are actually from/to Italy
italy_flows = sum(tkm for od_key, tkm in od_pair_summary.items()
                  if 'IT->' in od_key or '->IT' in od_key)
non_italy_flows = total_tkm_in_italy_range - italy_flows

print(f"\nTKM in Italian latitude range:")
print(f"  From/To Italy (IT->X or X->IT):  {italy_flows:>15,.0f} ({100*italy_flows/total_tkm_in_italy_range:.1f}%)")
print(f"  Through Italy (X->Y, no IT):     {non_italy_flows:>15,.0f} ({100*non_italy_flows/total_tkm_in_italy_range:.1f}%)")
print(f"  TOTAL:                           {total_tkm_in_italy_range:>15,.0f}")

if non_italy_flows > italy_flows:
    print(f"\nWARNING: Most TKM in Italian latitude range is from non-Italian OD pairs!")
    print(f"This suggests flows are being incorrectly attributed to Italian latitudes")
    print(f"even though they don't originate or terminate in Italy.")
