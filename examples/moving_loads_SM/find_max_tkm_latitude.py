"""
Find the maximum TKM in the latitude visualization and identify where it's allocated.
This will analyze the stacked curve (road + rail TKM) by latitude.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import yaml
from collections import defaultdict

# Load data
case_study_name = 'case_20251103_114421'
input_dir = f'input_data/{case_study_name}'
results_dir = f'results/{case_study_name}'

print(f"Finding maximum TKM location in latitude visualization")
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

print(f"\nCalculating TKM by latitude and mode (as done in notebook)...")
print("=" * 80)

# Track TKM by NUTS2 region and mode
# This replicates the notebook calculation
tkm_by_nuts2_mode = defaultdict(lambda: {'road': 0, 'rail': 0, 'lat': 0, 'country': '', 'nuts2': ''})

flows_processed = 0
for key, flow_value in f_data.items():
    if flow_value < 0.01:
        continue

    flows_processed += 1
    if flows_processed % 20000 == 0:
        print(f"  Processed {flows_processed} flows...")

    odpair_id, path_id, mode_id, year_idx = key

    # Get path info
    if path_id not in path_lookup:
        continue

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
print(f"Found TKM for {len(tkm_by_nuts2_mode)} NUTS2 regions")
print("=" * 80)

# Calculate total TKM (road + rail) for each NUTS2 region
regions_with_tkm = []
for nuts2, data in tkm_by_nuts2_mode.items():
    total_tkm = data['road'] + data['rail']
    if total_tkm > 0:
        regions_with_tkm.append({
            'nuts2': nuts2,
            'country': data['country'],
            'lat': data['lat'],
            'road_tkm': data['road'],
            'rail_tkm': data['rail'],
            'total_tkm': total_tkm,
            'rail_pct': 100 * data['rail'] / total_tkm if total_tkm > 0 else 0
        })

# Sort by total TKM
regions_with_tkm.sort(key=lambda x: x['total_tkm'], reverse=True)

print(f"\nTop 20 NUTS2 regions by total TKM (road + rail):")
print("=" * 80)
print(f"{'Rank':<6} {'NUTS2':<10} {'Country':<8} {'Latitude':>10} {'Road TKM':>15} {'Rail TKM':>15} {'Total TKM':>15} {'Rail %':>8}")
print("-" * 80)

for i, region in enumerate(regions_with_tkm[:20], 1):
    print(f"{i:<6} {region['nuts2']:<10} {region['country']:<8} {region['lat']:>10.2f} "
          f"{region['road_tkm']:>15,.0f} {region['rail_tkm']:>15,.0f} "
          f"{region['total_tkm']:>15,.0f} {region['rail_pct']:>7.1f}%")

# Find the maximum
if regions_with_tkm:
    max_region = regions_with_tkm[0]

    print("\n" + "=" * 80)
    print("MAXIMUM TKM LOCATION")
    print("=" * 80)
    print(f"NUTS2 Region:  {max_region['nuts2']}")
    print(f"Country:       {max_region['country']}")
    print(f"Latitude:      {max_region['lat']:.4f}°N")
    print(f"Road TKM:      {max_region['road_tkm']:>15,.0f}")
    print(f"Rail TKM:      {max_region['rail_tkm']:>15,.0f}")
    print(f"TOTAL TKM:     {max_region['total_tkm']:>15,.0f}")
    print(f"Rail Share:    {max_region['rail_pct']:.1f}%")

    # Now analyze which OD pairs contribute to this region
    print("\n" + "=" * 80)
    print(f"OD PAIRS CONTRIBUTING TO {max_region['nuts2']}")
    print("=" * 80)

    # Re-analyze to get OD pair breakdown for this specific region
    od_contributions = defaultdict(lambda: {'road': 0, 'rail': 0})

    for key, flow_value in f_data.items():
        if flow_value < 0.01:
            continue

        odpair_id, path_id, mode_id, year_idx = key

        # Get OD info
        if odpair_id not in od_lookup:
            continue

        od_info = od_lookup[odpair_id]
        origin_id = od_info['origin']
        dest_id = od_info['destination']
        origin_country = nuts2_lookup.get(origin_id, {}).get('country', 'UNK')
        dest_country = nuts2_lookup.get(dest_id, {}).get('country', 'UNK')

        # Get path info
        if path_id not in path_lookup:
            continue

        path_info = path_lookup[path_id]
        sequence = path_info['sequence']
        distance_from_previous = path_info['distance_from_previous']

        mode_name = 'rail' if mode_id == 2 else 'road'

        # Check if this path passes through our max region
        for i, node_id in enumerate(sequence):
            if node_id not in nuts2_lookup:
                continue

            if nuts2_lookup[node_id]['nuts2'] == max_region['nuts2']:
                segment_distance = distance_from_previous[i]
                tkm_segment = flow_value * segment_distance

                od_key = f"{origin_country}->{dest_country}"
                od_contributions[od_key][mode_name] += tkm_segment
                break  # Only count once per path

    # Sort OD pairs by total contribution
    od_sorted = []
    for od_key, modes in od_contributions.items():
        total = modes['road'] + modes['rail']
        od_sorted.append({
            'od': od_key,
            'road': modes['road'],
            'rail': modes['rail'],
            'total': total
        })

    od_sorted.sort(key=lambda x: x['total'], reverse=True)

    print(f"\nTop 15 OD pairs passing through {max_region['nuts2']}:")
    print("-" * 80)
    print(f"{'OD Pair':<20} {'Road TKM':>15} {'Rail TKM':>15} {'Total TKM':>15} {'% of Region':>12}")
    print("-" * 80)

    for od in od_sorted[:15]:
        pct = 100 * od['total'] / max_region['total_tkm']
        print(f"{od['od']:<20} {od['road']:>15,.0f} {od['rail']:>15,.0f} "
              f"{od['total']:>15,.0f} {pct:>11.1f}%")

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    # Check if this is international freight
    italy_ods = sum(od['total'] for od in od_sorted if 'IT->' in od['od'] or '->IT' in od['od'])
    non_italy_ods = max_region['total_tkm'] - italy_ods

    print(f"\nBreakdown of TKM in {max_region['nuts2']} ({max_region['country']}):")
    print(f"  OD pairs involving Italy (IT->X or X->IT): {italy_ods:>15,.0f} ({100*italy_ods/max_region['total_tkm']:.1f}%)")
    print(f"  OD pairs NOT involving Italy:              {non_italy_ods:>15,.0f} ({100*non_italy_ods/max_region['total_tkm']:.1f}%)")

else:
    print("\nNo regions with TKM found!")
