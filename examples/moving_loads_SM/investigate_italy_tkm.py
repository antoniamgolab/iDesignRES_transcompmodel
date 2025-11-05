"""
Investigate high TKM in Italy - check if it's from international freight only.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import yaml
import pickle
from collections import defaultdict

# Load the case study
case_study_name = 'case_20251103_114421'
input_dir = f'input_data/{case_study_name}'
results_dir = f'results/{case_study_name}'

print(f"Loading case study: {case_study_name}")
print("=" * 80)

# Load input data from YAML files
print("Loading GeographicElement.yaml...")
with open(f'{input_dir}/GeographicElement.yaml', 'r', encoding='utf-8') as f:
    geo_elements = yaml.safe_load(f)

print("Loading Odpair.yaml...")
with open(f'{input_dir}/Odpair.yaml', 'r', encoding='utf-8') as f:
    odpairs = yaml.safe_load(f)

print("Loading Path.yaml...")
with open(f'{input_dir}/Path.yaml', 'r', encoding='utf-8') as f:
    paths = yaml.safe_load(f)

# Find the most recent f_dict.yaml file
import glob
f_dict_files = glob.glob(f'{results_dir}/*_f_dict.yaml')
if not f_dict_files:
    print(f"ERROR: No f_dict.yaml files found in {results_dir}")
    sys.exit(1)

# Use the most recent file
f_dict_file = sorted(f_dict_files)[-1]
print(f"Loading flow data from: {f_dict_file}")
with open(f_dict_file, 'r', encoding='utf-8') as f:
    f_data_raw = yaml.safe_load(f)

# Convert f_data from string keys to tuple keys
f_data = {}
for key_str, value in f_data_raw.items():
    # Parse key like "(0, 0, 1, 0)" into tuple (0, 0, 1, 0)
    key_tuple = eval(key_str)
    # Convert value to float
    f_data[key_tuple] = float(value)

print(f"Loaded {len(f_data)} flow entries")
print("=" * 80)

# Create country lookup
country_lookup = {}
for geo in geo_elements:
    if geo['type'] == 'node' and 'nuts2_region' in geo and geo['nuts2_region']:
        country_lookup[geo['id']] = {
            'country': geo['country'],
            'nuts2': geo['nuts2_region'],
            'lat': geo['coordinate_lat']
        }

# Create origin/destination lookup
od_lookup = {}
for od in odpairs:
    od_lookup[od['id']] = {
        'origin': od['from'],
        'destination': od['to']
    }

# Create path lookup
path_lookup = {}
for path in paths:
    path_lookup[path['id']] = {
        'sequence': path['sequence'],
        'distance_from_previous': path['distance_from_previous']
    }

print("\nAnalyzing freight flows through Italian NUTS2 regions...")
print("-" * 80)

# Track TKM by Italian region and OD pair type
italy_tkm = defaultdict(lambda: {
    'international': 0,  # Both origin and destination outside Italy
    'domestic': 0,        # Both origin and destination in Italy
    'import': 0,          # Destination in Italy, origin outside
    'export': 0,          # Origin in Italy, destination outside
    'od_pairs': defaultdict(lambda: {'flow': 0, 'tkm': 0})
})

italy_node_ids = {geo['id'] for geo in geo_elements
                  if geo.get('type') == 'node'
                  and geo.get('country') == 'IT'
                  and 'nuts2_region' in geo
                  and geo['nuts2_region']}

print(f"Found {len(italy_node_ids)} Italian NUTS2 nodes")
print(f"Total flow entries to process: {len(f_data)}")

# Debug counters
processed_flows = 0
flows_through_italy = 0

for key, flow_value in f_data.items():
    if flow_value < 0.01:
        continue

    processed_flows += 1

    odpair_id, path_id, mode_id, year_idx = key

    # Get OD pair info
    if odpair_id not in od_lookup:
        continue

    od_info = od_lookup[odpair_id]
    origin_id = od_info['origin']
    dest_id = od_info['destination']

    # Get origin and destination countries
    origin_country = country_lookup.get(origin_id, {}).get('country', 'UNKNOWN')
    dest_country = country_lookup.get(dest_id, {}).get('country', 'UNKNOWN')

    # Classify OD pair type
    od_type = None
    if origin_country == 'IT' and dest_country == 'IT':
        od_type = 'domestic'
    elif origin_country == 'IT' and dest_country != 'IT':
        od_type = 'export'
    elif origin_country != 'IT' and dest_country == 'IT':
        od_type = 'import'
    elif origin_country != 'IT' and dest_country != 'IT':
        od_type = 'international'
    else:
        continue

    # Get path info
    if path_id not in path_lookup:
        continue

    path_info = path_lookup[path_id]
    sequence = path_info['sequence']
    distance_from_previous = path_info['distance_from_previous']

    # Calculate TKM passing through each node
    has_italy_node = False
    for i, node_id in enumerate(sequence):
        if node_id not in italy_node_ids:
            continue

        has_italy_node = True

        # Get the segment distance TO this node
        segment_distance = distance_from_previous[i]
        tkm_segment = flow_value * segment_distance

        node_info = country_lookup[node_id]
        nuts2 = node_info['nuts2']

        # Add to the appropriate category
        italy_tkm[nuts2][od_type] += tkm_segment

        # Track individual OD pairs
        od_key = f"{origin_country}-{dest_country}"
        italy_tkm[nuts2]['od_pairs'][od_key]['flow'] += flow_value
        italy_tkm[nuts2]['od_pairs'][od_key]['tkm'] += tkm_segment

    if has_italy_node:
        flows_through_italy += 1

print(f"\nProcessed {processed_flows} non-zero flows")
print(f"Flows passing through Italy: {flows_through_italy}")

# Print results sorted by total TKM
print("\nItalian NUTS2 regions sorted by total TKM:")
print("-" * 80)
print(f"{'NUTS2':<8} {'Lat':>6} {'Intl':>12} {'Import':>12} {'Export':>12} {'Domestic':>12} {'Total':>12}")
print("-" * 80)

sorted_regions = sorted(italy_tkm.items(),
                       key=lambda x: sum([x[1]['international'], x[1]['import'],
                                         x[1]['export'], x[1]['domestic']]),
                       reverse=True)

for nuts2, data in sorted_regions:
    lat = next((g['coordinate_lat'] for g in geo_elements
                if g.get('nuts2_region') == nuts2), 0)

    total = data['international'] + data['import'] + data['export'] + data['domestic']

    print(f"{nuts2:<8} {lat:>6.2f} {data['international']:>12.0f} {data['import']:>12.0f} "
          f"{data['export']:>12.0f} {data['domestic']:>12.0f} {total:>12.0f}")

# Show top regions with their OD pair breakdown
print("\n" + "=" * 80)
print("TOP 5 ITALIAN REGIONS - OD PAIR BREAKDOWN")
print("=" * 80)

for nuts2, data in sorted_regions[:5]:
    lat = next((g['coordinate_lat'] for g in geo_elements
                if g.get('nuts2_region') == nuts2), 0)

    total = data['international'] + data['import'] + data['export'] + data['domestic']

    print(f"\n{nuts2} (Latitude: {lat:.2f}°N) - Total TKM: {total:,.0f}")
    print("-" * 80)

    # Sort OD pairs by TKM
    od_sorted = sorted(data['od_pairs'].items(),
                      key=lambda x: x[1]['tkm'],
                      reverse=True)

    print(f"{'OD Pair':<20} {'TKM':>15} {'Flow (tonnes)':>15}")
    print("-" * 80)
    for od_key, od_data in od_sorted[:10]:
        if od_data['tkm'] > 0:
            print(f"{od_key:<20} {od_data['tkm']:>15,.0f} {od_data['flow']:>15,.0f}")

# Summary statistics
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

total_italy_tkm = {
    'international': sum(d['international'] for d in italy_tkm.values()),
    'import': sum(d['import'] for d in italy_tkm.values()),
    'export': sum(d['export'] for d in italy_tkm.values()),
    'domestic': sum(d['domestic'] for d in italy_tkm.values())
}

grand_total = sum(total_italy_tkm.values())

print(f"\nTotal TKM passing through Italian NUTS2 regions:")
print(f"  International (non-IT to non-IT): {total_italy_tkm['international']:>15,.0f} ({100*total_italy_tkm['international']/grand_total:.1f}%)")
print(f"  Import (non-IT to IT):            {total_italy_tkm['import']:>15,.0f} ({100*total_italy_tkm['import']/grand_total:.1f}%)")
print(f"  Export (IT to non-IT):            {total_italy_tkm['export']:>15,.0f} ({100*total_italy_tkm['export']/grand_total:.1f}%)")
print(f"  Domestic (IT to IT):              {total_italy_tkm['domestic']:>15,.0f} ({100*total_italy_tkm['domestic']/grand_total:.1f}%)")
print(f"  {'TOTAL':>34} {grand_total:>15,.0f}")

if total_italy_tkm['domestic'] > 0:
    print(f"\nWARNING: Domestic Italian freight is included in the results!")
    print(f"         This accounts for {100*total_italy_tkm['domestic']/grand_total:.1f}% of TKM in Italian regions.")
