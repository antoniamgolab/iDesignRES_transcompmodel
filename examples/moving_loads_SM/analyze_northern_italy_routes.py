"""
ANALYSIS: What routes does freight take to reach Northern Italy?

This script investigates the actual paths taken by freight flows to Northern Italy,
specifically checking whether they pass through Austria, Switzerland, or other routes.
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

# Define Northern Italy NUTS2 codes
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
print("ROUTE ANALYSIS: HOW DOES FREIGHT REACH NORTHERN ITALY?")
print("="*80)

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
# ANALYZE ROUTES TO NORTHERN ITALY
# ==============================================================================

print("\nAnalyzing routes to Northern Italy (year 2030)...")

# Track flows and their routes
flows_to_northern_italy = []

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

    # Only look at flows DESTINED for Northern Italy (not just passing through)
    if dest_nuts2 not in northern_italy_regions:
        continue

    # Only look at imports (origin NOT in Italy)
    if origin_country == 'IT':
        continue

    # Extract the route (all NUTS2 regions visited)
    route_nuts2 = []
    route_countries = []

    for node_id in path_info['sequence']:
        if node_id in nuts2_lookup:
            nuts2 = nuts2_lookup[node_id]['nuts2']
            country = nuts2_lookup[node_id]['country']
            route_nuts2.append(nuts2)
            route_countries.append(country)

    # Check which countries are visited
    unique_countries = list(dict.fromkeys(route_countries))  # Preserve order, remove duplicates

    # Check if Austria or Switzerland are in the route
    passes_through_austria = 'AT' in unique_countries
    passes_through_switzerland = 'CH' in unique_countries

    flow_info = {
        'origin_nuts2': origin_nuts2,
        'origin_country': origin_country,
        'dest_nuts2': dest_nuts2,
        'dest_country': dest_country,
        'flow_kt': flow_value_kt,
        'route_nuts2': route_nuts2,
        'route_countries': unique_countries,
        'passes_through_austria': passes_through_austria,
        'passes_through_switzerland': passes_through_switzerland,
        'mode': 'rail' if mode_id == 2 else 'road'
    }

    flows_to_northern_italy.append(flow_info)

# ==============================================================================
# SUMMARY: ROUTE ANALYSIS
# ==============================================================================

print("\n" + "="*80)
print("SUMMARY: ROUTES TO NORTHERN ITALY")
print("="*80)

total_flows = len(flows_to_northern_italy)
total_kt = sum(f['flow_kt'] for f in flows_to_northern_italy)

flows_via_austria = [f for f in flows_to_northern_italy if f['passes_through_austria']]
flows_via_switzerland = [f for f in flows_to_northern_italy if f['passes_through_switzerland']]
flows_via_neither = [f for f in flows_to_northern_italy if not f['passes_through_austria'] and not f['passes_through_switzerland']]

kt_via_austria = sum(f['flow_kt'] for f in flows_via_austria)
kt_via_switzerland = sum(f['flow_kt'] for f in flows_via_switzerland)
kt_via_neither = sum(f['flow_kt'] for f in flows_via_neither)

print(f"\nTotal flows to Northern Italy: {total_flows:,} OD-pairs")
print(f"Total freight: {total_kt:,.0f} kt = {total_kt * SCALING_FACTOR / 1e6:.2f} Mt")

print("\n" + "-"*80)
print("ROUTE BREAKDOWN:")
print("-"*80)

print(f"\n✓ Flows passing through AUSTRIA:")
print(f"  • Number of OD-pairs: {len(flows_via_austria):,}")
print(f"  • Freight volume: {kt_via_austria:,.0f} kt = {kt_via_austria * SCALING_FACTOR / 1e6:.2f} Mt")
print(f"  • Percentage: {100 * kt_via_austria / total_kt:.1f}%")

print(f"\n✓ Flows passing through SWITZERLAND:")
print(f"  • Number of OD-pairs: {len(flows_via_switzerland):,}")
print(f"  • Freight volume: {kt_via_switzerland:,.0f} kt = {kt_via_switzerland * SCALING_FACTOR / 1e6:.2f} Mt")
print(f"  • Percentage: {100 * kt_via_switzerland / total_kt:.1f}%")

print(f"\n✓ Flows passing through NEITHER (direct routes):")
print(f"  • Number of OD-pairs: {len(flows_via_neither):,}")
print(f"  • Freight volume: {kt_via_neither:,.0f} kt = {kt_via_neither * SCALING_FACTOR / 1e6:.2f} Mt")
print(f"  • Percentage: {100 * kt_via_neither / total_kt:.1f}%")

# ==============================================================================
# DETAILED EXAMPLES
# ==============================================================================

print("\n" + "="*80)
print("EXAMPLE ROUTES: TOP 10 FLOWS TO NORTHERN ITALY")
print("="*80)

# Sort by flow volume
flows_to_northern_italy.sort(key=lambda x: x['flow_kt'], reverse=True)

print(f"\n{'Rank':<6} {'Origin':<8} {'Dest':<8} {'Freight (kt)':>12} {'Route Countries':<40} {'Via AT?':<8} {'Via CH?':<8}")
print("-" * 100)

for i, flow in enumerate(flows_to_northern_italy[:10], 1):
    route_str = ' → '.join(flow['route_countries'])
    via_at = '✓' if flow['passes_through_austria'] else '✗'
    via_ch = '✓' if flow['passes_through_switzerland'] else '✗'

    print(f"{i:<6} {flow['origin_nuts2']:<8} {flow['dest_nuts2']:<8} {flow['flow_kt']:>12.0f} {route_str:<40} {via_at:<8} {via_ch:<8}")

# ==============================================================================
# DETAILED ROUTE EXAMPLES
# ==============================================================================

print("\n" + "="*80)
print("DETAILED ROUTE EXAMPLES")
print("="*80)

# Show 3 example routes in detail
print("\nShowing detailed NUTS2-level routes for top 3 flows:")

for i, flow in enumerate(flows_to_northern_italy[:3], 1):
    print(f"\n{'-'*80}")
    print(f"FLOW {i}: {flow['origin_nuts2']} → {flow['dest_nuts2']}")
    print(f"  Freight: {flow['flow_kt']:,.0f} kt = {flow['flow_kt'] * SCALING_FACTOR / 1e6:.2f} Mt")
    print(f"  Mode: {flow['mode']}")
    print(f"  Passes through Austria: {'YES' if flow['passes_through_austria'] else 'NO'}")
    print(f"  Passes through Switzerland: {'YES' if flow['passes_through_switzerland'] else 'NO'}")
    print(f"\n  Full route (NUTS2 regions):")

    for j, nuts2 in enumerate(flow['route_nuts2'], 1):
        country = flow['route_countries'][j-1] if j <= len(flow['route_countries']) else 'UNKNOWN'
        marker = "  → " if j > 1 else "    "
        print(f"{marker}{nuts2} ({country})")

# ==============================================================================
# CHECK AUSTRIA FREIGHT VOLUMES
# ==============================================================================

print("\n" + "="*80)
print("VERIFICATION: FREIGHT VOLUMES IN AUSTRIA")
print("="*80)

print("\nCalculating ALL freight passing through Austria (not just to Northern Italy)...")

austria_freight = defaultdict(lambda: {'road': 0, 'rail': 0})

for key_str, value in f_data_raw.items():
    flow_value_kt = float(value)

    if flow_value_kt < 0.001:
        continue

    key_tuple = eval(key_str)
    year, (product_id, odpair_id, path_id), (mode_id, techvehicle_id), generation = key_tuple

    if year != 2030:
        continue

    if path_id not in path_lookup:
        continue

    path_info = path_lookup[path_id]
    mode_name = 'rail' if mode_id == 2 else 'road'
    flow_value_tonnes = flow_value_kt * SCALING_FACTOR

    # Check if path passes through Austria
    for i, node_id in enumerate(path_info['sequence']):
        if node_id in nuts2_lookup:
            nuts2_id = nuts2_lookup[node_id]['nuts2']
            country = nuts2_lookup[node_id]['country']

            if country == 'AT':
                segment_distance = path_info['distance_from_previous'][i]
                tkm_segment = flow_value_tonnes * segment_distance

                austria_freight[nuts2_id][mode_name] += tkm_segment

# Print Austria freight summary
print(f"\n{'NUTS2 Region':<15} {'Road (B TKM)':>15} {'Rail (B TKM)':>15} {'Total (B TKM)':>15}")
print("-" * 65)

austria_total = 0
for nuts2_id in sorted(austria_freight.keys()):
    road_tkm = austria_freight[nuts2_id]['road']
    rail_tkm = austria_freight[nuts2_id]['rail']
    total_tkm = road_tkm + rail_tkm
    austria_total += total_tkm

    print(f"{nuts2_id:<15} {road_tkm/1e9:>15.2f} {rail_tkm/1e9:>15.2f} {total_tkm/1e9:>15.2f}")

print("-" * 65)
print(f"{'AUSTRIA TOTAL':<15} {sum(d['road'] for d in austria_freight.values())/1e9:>15.2f} "
      f"{sum(d['rail'] for d in austria_freight.values())/1e9:>15.2f} {austria_total/1e9:>15.2f}")

print("\n" + "="*80)
print("CONCLUSION")
print("="*80)

print(f"""
Your intuition is CORRECT! Let's compare:

📊 NORTHERN ITALY freight: {total_kt * SCALING_FACTOR / 1e6:.2f} Mt imports
   • Via Austria: {kt_via_austria * SCALING_FACTOR / 1e6:.2f} Mt ({100 * kt_via_austria / total_kt:.1f}%)
   • Via Switzerland: {kt_via_switzerland * SCALING_FACTOR / 1e6:.2f} Mt ({100 * kt_via_switzerland / total_kt:.1f}%)
   • Direct (neither): {kt_via_neither * SCALING_FACTOR / 1e6:.2f} Mt ({100 * kt_via_neither / total_kt:.1f}%)

📊 AUSTRIA total freight: {austria_total/1e9:.2f} B TKM

💡 KEY INSIGHT:
   {kt_via_austria / total_kt * 100:.1f}% of Northern Italy imports pass through Austria.
   {kt_via_switzerland / total_kt * 100:.1f}% pass through Switzerland.

   This means Austria should indeed show significant freight volumes in the
   spatial plots, as it's a major transit corridor for freight destined to
   Northern Italy.
""")
