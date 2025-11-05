"""
ANALYSIS: Where does Northern Italy's freight come from?

This script investigates the origin and type of freight passing through
Northern Italian NUTS2 regions.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import yaml
from collections import defaultdict
import glob

# ==============================================================================
# CONFIGURATION
# ==============================================================================

case_study_name = 'case_20251103_114421'
input_dir = f'input_data/{case_study_name}'
results_dir = f'results/{case_study_name}'

# Define Northern Italy NUTS2 codes (approximate)
# These are the regions showing high freight in your spatial plots
northern_italy_regions = [
    'ITC1',  # Piemonte
    'ITC2',  # Valle d'Aosta
    'ITC3',  # Liguria
    'ITC4',  # Lombardia (Milan area - major hub)
    'ITH1',  # Provincia Autonoma Bolzano/Bozen
    'ITH2',  # Provincia Autonoma Trento
    'ITH3',  # Veneto (Venice area)
    'ITH4',  # Friuli-Venezia Giulia
    'ITH5',  # Emilia-Romagna
]

print("="*80)
print("NORTHERN ITALY FREIGHT ORIGIN ANALYSIS")
print("="*80)
print(f"\nAnalyzing freight in Northern Italy regions: {', '.join(northern_italy_regions)}")

# ==============================================================================
# LOAD DATA
# ==============================================================================

print("\nLoading data...")

with open(f'{input_dir}/GeographicElement.yaml', 'r', encoding='utf-8') as f:
    geo_elements = yaml.safe_load(f)

with open(f'{input_dir}/Odpair.yaml', 'r', encoding='utf-8') as f:
    odpairs = yaml.safe_load(f)

with open(f'{input_dir}/Path.yaml', 'r', encoding='utf-8') as f:
    paths = yaml.safe_load(f)

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
            'country': geo.get('country', 'UNKNOWN')
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

# ==============================================================================
# ANALYZE FLOWS THROUGH NORTHERN ITALY
# ==============================================================================

print("\nAnalyzing flows through Northern Italy (year 2030)...")

# Categorize all flows passing through Northern Italy
flow_categories = {
    'import_from_corridor': defaultdict(lambda: {'road': 0, 'rail': 0, 'flows': []}),    # From DE, AT, etc. TO Northern IT
    'import_from_other': defaultdict(lambda: {'road': 0, 'rail': 0, 'flows': []}),       # From non-corridor TO Northern IT
    'export_to_corridor': defaultdict(lambda: {'road': 0, 'rail': 0, 'flows': []}),      # FROM Northern IT to DE, AT, etc.
    'export_to_other': defaultdict(lambda: {'road': 0, 'rail': 0, 'flows': []}),         # FROM Northern IT to non-corridor
    'domestic_within_north': defaultdict(lambda: {'road': 0, 'rail': 0, 'flows': []}),   # Within Northern IT
    'domestic_from_south': defaultdict(lambda: {'road': 0, 'rail': 0, 'flows': []}),     # From Southern IT to Northern IT
    'domestic_to_south': defaultdict(lambda: {'road': 0, 'rail': 0, 'flows': []}),       # From Northern IT to Southern IT
    'transit': defaultdict(lambda: {'road': 0, 'rail': 0, 'flows': []}),                 # Neither origin nor dest in IT
}

corridor_countries = ['IT', 'AT', 'DE', 'DK', 'NO', 'SE']

for key_str, value in f_data_raw.items():
    flow_value_kt = float(value)

    if flow_value_kt < 0.001:
        continue

    key_tuple = eval(key_str)
    year, (product_id, odpair_id, path_id), (mode_id, techvehicle_id), generation = key_tuple

    if year != 2030:
        continue

    if odpair_id not in od_lookup or path_id not in path_lookup:
        continue

    od_info = od_lookup[odpair_id]
    path_info = path_lookup[path_id]

    origin_id = od_info['origin']
    dest_id = od_info['destination']

    # Get origin and destination info
    origin_nuts2 = nuts2_lookup.get(origin_id, {}).get('nuts2', 'UNKNOWN')
    dest_nuts2 = nuts2_lookup.get(dest_id, {}).get('nuts2', 'UNKNOWN')
    origin_country = nuts2_lookup.get(origin_id, {}).get('country', 'UNKNOWN')
    dest_country = nuts2_lookup.get(dest_id, {}).get('country', 'UNKNOWN')

    # Check if path passes through Northern Italy
    passes_through_north_italy = any(
        nuts2_lookup.get(node_id, {}).get('nuts2') in northern_italy_regions
        for node_id in path_info['sequence']
    )

    if not passes_through_north_italy:
        continue

    # Calculate TKM in Northern Italy only
    flow_value_tonnes = flow_value_kt * SCALING_FACTOR
    mode_name = 'rail' if mode_id == 2 else 'road'

    tkm_in_north_italy = 0
    for i, node_id in enumerate(path_info['sequence']):
        node_nuts2 = nuts2_lookup.get(node_id, {}).get('nuts2')
        if node_nuts2 in northern_italy_regions:
            segment_distance = path_info['distance_from_previous'][i]
            tkm_in_north_italy += flow_value_tonnes * segment_distance

    if tkm_in_north_italy == 0:
        continue

    flow_info = {
        'origin_nuts2': origin_nuts2,
        'origin_country': origin_country,
        'dest_nuts2': dest_nuts2,
        'dest_country': dest_country,
        'flow_kt': flow_value_kt,
        'tkm_in_north_italy': tkm_in_north_italy
    }

    # Categorize the flow
    origin_in_north_italy = origin_nuts2 in northern_italy_regions
    dest_in_north_italy = dest_nuts2 in northern_italy_regions

    if origin_in_north_italy and dest_in_north_italy:
        # Domestic within Northern Italy
        flow_categories['domestic_within_north'][origin_nuts2][mode_name] += tkm_in_north_italy
        flow_categories['domestic_within_north'][origin_nuts2]['flows'].append(flow_info)

    elif origin_country == 'IT' and not origin_in_north_italy and dest_in_north_italy:
        # From Southern Italy to Northern Italy
        flow_categories['domestic_from_south'][dest_nuts2][mode_name] += tkm_in_north_italy
        flow_categories['domestic_from_south'][dest_nuts2]['flows'].append(flow_info)

    elif origin_in_north_italy and dest_country == 'IT' and not dest_in_north_italy:
        # From Northern Italy to Southern Italy
        flow_categories['domestic_to_south'][origin_nuts2][mode_name] += tkm_in_north_italy
        flow_categories['domestic_to_south'][origin_nuts2]['flows'].append(flow_info)

    elif dest_in_north_italy and origin_country != 'IT':
        # Import TO Northern Italy
        if origin_country in corridor_countries:
            flow_categories['import_from_corridor'][dest_nuts2][mode_name] += tkm_in_north_italy
            flow_categories['import_from_corridor'][dest_nuts2]['flows'].append(flow_info)
        else:
            flow_categories['import_from_other'][dest_nuts2][mode_name] += tkm_in_north_italy
            flow_categories['import_from_other'][dest_nuts2]['flows'].append(flow_info)

    elif origin_in_north_italy and dest_country != 'IT':
        # Export FROM Northern Italy
        if dest_country in corridor_countries:
            flow_categories['export_to_corridor'][origin_nuts2][mode_name] += tkm_in_north_italy
            flow_categories['export_to_corridor'][origin_nuts2]['flows'].append(flow_info)
        else:
            flow_categories['export_to_other'][origin_nuts2][mode_name] += tkm_in_north_italy
            flow_categories['export_to_other'][origin_nuts2]['flows'].append(flow_info)

    elif origin_country != 'IT' and dest_country != 'IT':
        # Transit through Northern Italy
        # Assign to the first Northern Italian region encountered
        first_north_italy_region = None
        for node_id in path_info['sequence']:
            node_nuts2 = nuts2_lookup.get(node_id, {}).get('nuts2')
            if node_nuts2 in northern_italy_regions:
                first_north_italy_region = node_nuts2
                break

        if first_north_italy_region:
            flow_categories['transit'][first_north_italy_region][mode_name] += tkm_in_north_italy
            flow_categories['transit'][first_north_italy_region]['flows'].append(flow_info)

# ==============================================================================
# SUMMARY STATISTICS
# ==============================================================================

print("\n" + "="*80)
print("SUMMARY: FREIGHT TKM IN NORTHERN ITALY BY FLOW TYPE")
print("="*80)

category_labels = {
    'import_from_corridor': 'Imports from Corridor Countries (DE, AT, DK, SE, NO)',
    'import_from_other': 'Imports from Other Countries',
    'export_to_corridor': 'Exports to Corridor Countries',
    'export_to_other': 'Exports to Other Countries',
    'domestic_within_north': 'Domestic: Within Northern Italy',
    'domestic_from_south': 'Domestic: From Southern to Northern Italy',
    'domestic_to_south': 'Domestic: From Northern to Southern Italy',
    'transit': 'Transit (Neither origin nor destination in Italy)',
}

total_tkm_all_categories = 0
category_totals = {}

for category, label in category_labels.items():
    data = flow_categories[category]

    total_road = sum(v['road'] for v in data.values())
    total_rail = sum(v['rail'] for v in data.values())
    total = total_road + total_rail

    category_totals[category] = total
    total_tkm_all_categories += total

print(f"\n{'Category':<55} {'Road (B TKM)':>15} {'Rail (B TKM)':>15} {'Total (B TKM)':>15} {'%':>8}")
print("-" * 110)

for category, label in category_labels.items():
    data = flow_categories[category]

    total_road = sum(v['road'] for v in data.values())
    total_rail = sum(v['rail'] for v in data.values())
    total = total_road + total_rail

    pct = 100 * total / total_tkm_all_categories if total_tkm_all_categories > 0 else 0

    print(f"{label:<55} {total_road/1e9:>15.2f} {total_rail/1e9:>15.2f} {total/1e9:>15.2f} {pct:>7.1f}%")

print("-" * 110)
print(f"{'TOTAL':<55} {sum(sum(v['road'] for v in flow_categories[c].values()) for c in category_labels)/1e9:>15.2f} "
      f"{sum(sum(v['rail'] for v in flow_categories[c].values()) for c in category_labels)/1e9:>15.2f} "
      f"{total_tkm_all_categories/1e9:>15.2f} {100.0:>7.1f}%")

# ==============================================================================
# TOP NORTHERN ITALY REGIONS BY FREIGHT VOLUME
# ==============================================================================

print("\n" + "="*80)
print("TOP NORTHERN ITALY REGIONS BY TOTAL FREIGHT TKM")
print("="*80)

# Aggregate by region
region_totals = defaultdict(lambda: {'road': 0, 'rail': 0})

for category_data in flow_categories.values():
    for region, data in category_data.items():
        region_totals[region]['road'] += data['road']
        region_totals[region]['rail'] += data['rail']

# Sort by total
sorted_regions = sorted(
    [(region, data['road'], data['rail'], data['road'] + data['rail'])
     for region, data in region_totals.items()],
    key=lambda x: x[3],
    reverse=True
)

print(f"\n{'NUTS2':<10} {'Road (B TKM)':>15} {'Rail (B TKM)':>15} {'Total (B TKM)':>15}")
print("-" * 60)

for region, road_tkm, rail_tkm, total_tkm in sorted_regions:
    print(f"{region:<10} {road_tkm/1e9:>15.2f} {rail_tkm/1e9:>15.2f} {total_tkm/1e9:>15.2f}")

# ==============================================================================
# DETAILED BREAKDOWN FOR TOP REGION
# ==============================================================================

if sorted_regions:
    top_region = sorted_regions[0][0]

    print("\n" + "="*80)
    print(f"DETAILED BREAKDOWN FOR TOP REGION: {top_region}")
    print("="*80)

    print(f"\n{'Flow Type':<55} {'TKM (B)':>15} {'% of Region':>12}")
    print("-" * 85)

    region_total = sum(
        flow_categories[cat][top_region]['road'] + flow_categories[cat][top_region]['rail']
        for cat in category_labels.keys()
        if top_region in flow_categories[cat]
    )

    for category, label in category_labels.items():
        if top_region in flow_categories[category]:
            cat_data = flow_categories[category][top_region]
            cat_total = cat_data['road'] + cat_data['rail']
            pct = 100 * cat_total / region_total if region_total > 0 else 0

            print(f"{label:<55} {cat_total/1e9:>15.2f} {pct:>11.1f}%")

# ==============================================================================
# CONCLUSION
# ==============================================================================

print("\n" + "="*80)
print("ANSWER TO YOUR QUESTION")
print("="*80)

# Find dominant category
dominant_category = max(category_totals.items(), key=lambda x: x[1])
dominant_label = category_labels[dominant_category[0]]
dominant_pct = 100 * dominant_category[1] / total_tkm_all_categories

print(f"""
The freight volumes in Northern Italy come primarily from:

🔍 DOMINANT SOURCE: {dominant_label}
   → {dominant_pct:.1f}% of all Northern Italy freight TKM

📊 BREAKDOWN:
   • Imports from corridor: {100*category_totals['import_from_corridor']/total_tkm_all_categories:.1f}%
   • Domestic from south: {100*category_totals['domestic_from_south']/total_tkm_all_categories:.1f}%
   • Within North Italy: {100*category_totals['domestic_within_north']/total_tkm_all_categories:.1f}%
   • Exports to corridor: {100*category_totals['export_to_corridor']/total_tkm_all_categories:.1f}%
   • Transit: {100*category_totals['transit']/total_tkm_all_categories:.1f}%

💡 INTERPRETATION:
   The high freight volumes you see in Northern Italy spatial plots are
   predominantly {dominant_label.lower()}.

   This explains why Northern Italy shows as a major freight hotspot -
   it's a key entry/destination point for corridor freight flows.
""")
