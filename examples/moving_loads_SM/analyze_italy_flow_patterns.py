"""
Comprehensive analysis of ALL flows involving Italy:
- Imports (X→IT)
- Exports (IT→X)
- Domestic (IT→IT)
- Transit (X→Y passing through IT)
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
print("COMPREHENSIVE ITALY FLOW PATTERNS ANALYSIS")
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
# Categorize ALL flows by Italy involvement
# ============================================================================
print("\n" + "=" * 80)
print("ALL FLOW PATTERNS (year 2030)")
print("=" * 80)

flow_categories = {
    'imports': [],      # X→IT
    'exports': [],      # IT→X
    'domestic': [],     # IT→IT
    'transit': [],      # X→Y (neither X nor Y is IT, but path goes through IT)
    'no_italy': []      # X→Y (doesn't touch IT at all)
}

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

    mode_name = 'rail' if mode_id == 2 else 'road'

    # Check if path passes through Italy
    passes_through_italy = any(
        nuts2_lookup.get(node_id, {}).get('country') == 'IT'
        for node_id in path_info['sequence']
    )

    # Calculate TKM in Italy
    tkm_in_italy = 0
    for i, node_id in enumerate(path_info['sequence']):
        if node_id in nuts2_lookup and nuts2_lookup[node_id]['country'] == 'IT':
            segment_distance = path_info['distance_from_previous'][i]
            tkm_in_italy += flow_value_tonnes * segment_distance

    flow_data = {
        'origin': origin_country,
        'dest': dest_country,
        'flow_kt': flow_value_kt,
        'flow_tonnes': flow_value_tonnes,
        'mode': mode_name,
        'tkm_in_italy': tkm_in_italy
    }

    # Categorize
    if origin_country == 'IT' and dest_country == 'IT':
        flow_categories['domestic'].append(flow_data)
    elif origin_country == 'IT':
        flow_categories['exports'].append(flow_data)
    elif dest_country == 'IT':
        flow_categories['imports'].append(flow_data)
    elif passes_through_italy:
        flow_categories['transit'].append(flow_data)
    else:
        flow_categories['no_italy'].append(flow_data)

# ============================================================================
# Summary statistics
# ============================================================================
print(f"\n{'Category':<20} {'# Flows':>10} {'Total Tonnes':>18} {'Total TKM in IT':>20}")
print("-" * 80)

for category, flows in flow_categories.items():
    count = len(flows)
    total_tonnes = sum(f['flow_tonnes'] for f in flows)
    total_tkm = sum(f['tkm_in_italy'] for f in flows)

    print(f"{category:<20} {count:>10} {total_tonnes:>18,.0f} {total_tkm:>20,.0f}")

print("-" * 80)

# ============================================================================
# Detailed breakdown by category
# ============================================================================

for category_name in ['imports', 'exports', 'domestic', 'transit']:
    flows = flow_categories[category_name]

    if not flows:
        print(f"\n{'='*80}")
        print(f"{category_name.upper()}: NONE FOUND")
        print(f"{'='*80}")
        continue

    print(f"\n{'='*80}")
    print(f"{category_name.upper()} - Top 10 flows")
    print(f"{'='*80}")

    flows.sort(key=lambda x: x['tkm_in_italy'], reverse=True)

    print(f"\n{'Rank':<6} {'Origin':>6} {'Dest':>6} {'Mode':<8} {'Flow (kt)':>12} {'TKM in IT':>15}")
    print("-" * 60)

    for i, f in enumerate(flows[:10], 1):
        print(f"{i:<6} {f['origin']:>6} {f['dest']:>6} {f['mode']:<8} {f['flow_kt']:>12.2f} {f['tkm_in_italy']:>15,.0f}")

# ============================================================================
# CONCLUSION
# ============================================================================
print("\n" + "=" * 80)
print("ANSWER TO YOUR QUESTION")
print("=" * 80)

exports = flow_categories['exports']
imports = flow_categories['imports']
corridor_countries = ['IT', 'AT', 'DE', 'DK', 'NO', 'SE']

if not exports:
    print("\n✓ Italy has NO EXPORTS (IT→X flows) in the optimized solution!")
    print("  All Italian TKM comes from IMPORTS only.")
else:
    # Check where exports go
    export_destinations = defaultdict(float)
    for f in exports:
        export_destinations[f['dest']] += f['tkm_in_italy']

    corridor_export_tkm = sum(tkm for dest, tkm in export_destinations.items() if dest in corridor_countries)
    non_corridor_export_tkm = sum(tkm for dest, tkm in export_destinations.items() if dest not in corridor_countries)

    total_export_tkm = corridor_export_tkm + non_corridor_export_tkm

    print(f"\nItaly EXPORTS:")
    print(f"  To corridor countries: {corridor_export_tkm/1e9:.2f}B TKM ({100*corridor_export_tkm/total_export_tkm:.1f}%)")
    print(f"  To non-corridor: {non_corridor_export_tkm/1e9:.2f}B TKM ({100*non_corridor_export_tkm/total_export_tkm:.1f}%)")

if imports:
    import_origins = defaultdict(float)
    for f in imports:
        import_origins[f['origin']] += f['tkm_in_italy']

    corridor_import_tkm = sum(tkm for orig, tkm in import_origins.items() if orig in corridor_countries)
    non_corridor_import_tkm = sum(tkm for orig, tkm in import_origins.items() if orig not in corridor_countries)

    total_import_tkm = corridor_import_tkm + non_corridor_import_tkm

    print(f"\nItaly IMPORTS:")
    print(f"  From corridor countries: {corridor_import_tkm/1e9:.2f}B TKM ({100*corridor_import_tkm/total_import_tkm:.1f}%)")
    print(f"  From non-corridor: {non_corridor_import_tkm/1e9:.2f}B TKM ({100*non_corridor_import_tkm/total_import_tkm:.1f}%)")
