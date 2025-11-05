"""
VALIDATION: Check if NUTS3 aggregation fix preserved intermediate routing

This script validates that the fix to aggregate_raw_data_to_nuts3.py successfully
preserves routes through Austria and Switzerland for Germany→Italy freight.

Expected outcome:
- BEFORE FIX: 100% "direct" routes (no intermediate nodes)
- AFTER FIX: Routes should pass through Austrian/Swiss NUTS3 regions
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import pandas as pd
import ast
from collections import defaultdict

print("="*80)
print("VALIDATING NUTS3 AGGREGATION FIX")
print("="*80)

# ==============================================================================
# LOAD FIXED NUTS3 DATA
# ==============================================================================

print("\nLoading FIXED NUTS3 aggregated data...")

nodes = pd.read_csv('data/Trucktraffic_NUTS3/03_network-nodes.csv')
edges = pd.read_csv('data/Trucktraffic_NUTS3/04_network-edges.csv')
traffic = pd.read_csv('data/Trucktraffic_NUTS3/01_Trucktrafficflow.csv')

print(f"  Nodes: {len(nodes):,}")
print(f"  Edges: {len(edges):,}")
print(f"  Traffic flows: {len(traffic):,}")

# Create mappings
zone_to_country = dict(zip(nodes['ETISplus_Zone_ID'], nodes['Country']))
zone_to_node = dict(zip(nodes['ETISplus_Zone_ID'], nodes['Network_Node_ID']))

# Build edge lookup
edge_countries = {}
for _, edge in edges.iterrows():
    node_a_id = edge['Network_Node_A_ID']
    node_b_id = edge['Network_Node_B_ID']

    # Find zones for these nodes
    zone_a = nodes[nodes['Network_Node_ID'] == node_a_id]['ETISplus_Zone_ID'].iloc[0] if len(nodes[nodes['Network_Node_ID'] == node_a_id]) > 0 else None
    zone_b = nodes[nodes['Network_Node_ID'] == node_b_id]['ETISplus_Zone_ID'].iloc[0] if len(nodes[nodes['Network_Node_ID'] == node_b_id]) > 0 else None

    country_a = zone_to_country.get(zone_a)
    country_b = zone_to_country.get(zone_b)

    countries = set()
    if country_a:
        countries.add(country_a)
    if country_b:
        countries.add(country_b)

    edge_countries[edge['Network_Edge_ID']] = countries

print(f"\n  Mapped {len(edge_countries)} edges to countries")

# ==============================================================================
# ANALYZE GERMANY → ITALY ROUTES
# ==============================================================================

print("\n" + "="*80)
print("ANALYZING GERMANY → ITALY ROUTES (AFTER FIX)")
print("="*80)

# Filter for Germany → Italy
traffic['origin_country'] = traffic['ID_origin_region'].map(zone_to_country)
traffic['dest_country'] = traffic['ID_destination_region'].map(zone_to_country)

de_to_it = traffic[
    (traffic['origin_country'] == 'DE') &
    (traffic['dest_country'] == 'IT')
].copy()

print(f"\nFound {len(de_to_it):,} Germany → Italy OD-pairs")
print(f"Total freight flow (2030): {de_to_it['Traffic_flow_trucks_2030'].sum():,.0f} trucks")

# Analyze routes
routes_via_austria = []
routes_via_switzerland = []
routes_via_both = []
routes_via_neither = []
routes_no_data = []

for idx, row in de_to_it.iterrows():
    origin_zone = row['ID_origin_region']
    dest_zone = row['ID_destination_region']
    flow = row['Traffic_flow_trucks_2030']
    edge_path_str = row['Edge_path_E_road']

    if pd.isna(edge_path_str) or edge_path_str == '':
        routes_no_data.append((origin_zone, dest_zone, flow))
        continue

    # Parse edge path
    try:
        if edge_path_str.startswith('['):
            edge_path = ast.literal_eval(edge_path_str)
        else:
            edge_path = [int(x.strip()) for x in edge_path_str.split(',') if x.strip()]
    except:
        routes_no_data.append((origin_zone, dest_zone, flow))
        continue

    # Check which countries this route passes through
    countries_on_route = set()
    for edge_id in edge_path:
        if edge_id in edge_countries:
            countries_on_route.update(edge_countries[edge_id])

    passes_austria = 'AT' in countries_on_route
    passes_switzerland = 'CH' in countries_on_route

    if passes_austria and passes_switzerland:
        routes_via_both.append((origin_zone, dest_zone, flow, countries_on_route))
    elif passes_austria:
        routes_via_austria.append((origin_zone, dest_zone, flow, countries_on_route))
    elif passes_switzerland:
        routes_via_switzerland.append((origin_zone, dest_zone, flow, countries_on_route))
    else:
        routes_via_neither.append((origin_zone, dest_zone, flow, countries_on_route))

# ==============================================================================
# RESULTS
# ==============================================================================

print("\n" + "="*80)
print("VALIDATION RESULTS")
print("="*80)

total_routes = len(de_to_it)
total_flow_austria = sum(r[2] for r in routes_via_austria)
total_flow_switzerland = sum(r[2] for r in routes_via_switzerland)
total_flow_both = sum(r[2] for r in routes_via_both)
total_flow_neither = sum(r[2] for r in routes_via_neither)
total_flow_all = total_flow_austria + total_flow_switzerland + total_flow_both + total_flow_neither

if total_flow_all == 0:
    print("\n ERROR: No route data found in Edge_path_E_road column!")
    print("This means the traffic data doesn't have edge path information.")
    sys.exit(1)

print(f"\nTotal Germany → Italy OD-pairs: {total_routes:,}")
print(f"  With route data: {total_routes - len(routes_no_data):,}")
print(f"  Without route data: {len(routes_no_data):,}")

print(f"\n{'Route Type':<40} {'Count':>10} {'Flow (trucks)':>18} {'%':>8}")
print("-" * 80)
print(f"{'Via Austria only':<40} {len(routes_via_austria):>10,} {total_flow_austria:>18,.0f} {100*total_flow_austria/total_flow_all:>7.1f}%")
print(f"{'Via Switzerland only':<40} {len(routes_via_switzerland):>10,} {total_flow_switzerland:>18,.0f} {100*total_flow_switzerland/total_flow_all:>7.1f}%")
print(f"{'Via both Austria and Switzerland':<40} {len(routes_via_both):>10,} {total_flow_both:>18,.0f} {100*total_flow_both/total_flow_all:>7.1f}%")
print(f"{'Via neither (direct)':<40} {len(routes_via_neither):>10,} {total_flow_neither:>18,.0f} {100*total_flow_neither/total_flow_all:>7.1f}%")
print("-" * 80)
print(f"{'TOTAL':<40} {len(de_to_it) - len(routes_no_data):>10,} {total_flow_all:>18,.0f} {100.0:>7.1f}%")

# ==============================================================================
# VALIDATION VERDICT
# ==============================================================================

print("\n" + "="*80)
print("VALIDATION VERDICT")
print("="*80)

austria_pct = 100 * (total_flow_austria + total_flow_both) / total_flow_all if total_flow_all > 0 else 0
switzerland_pct = 100 * (total_flow_switzerland + total_flow_both) / total_flow_all if total_flow_all > 0 else 0
direct_pct = 100 * total_flow_neither / total_flow_all if total_flow_all > 0 else 0

print(f"""
EXPECTED OUTCOME (from raw data analysis):
  - ~54.5% of Germany→Italy freight passes through Austria
  - ~66.3% passes through Switzerland
  - ~20.8% passes through both
  - 0% direct routes

ACTUAL OUTCOME (after fix):
  - {austria_pct:.1f}% passes through Austria
  - {switzerland_pct:.1f}% passes through Switzerland
  - {direct_pct:.1f}% direct routes (no intermediate countries)

VERDICT:
""")

if direct_pct > 50:
    print("  ❌ FAIL - Routes are still mostly direct (no intermediate routing)")
    print("     The fix did NOT work correctly.")
    print("\n  REASON: The Edge_path_E_road column in traffic data may not contain")
    print("          the actual edge sequences, OR the network topology doesn't")
    print("          connect German and Italian NUTS3 regions through Austria/Switzerland.")
elif direct_pct > 10:
    print("  ⚠️  PARTIAL - Some routes preserve intermediate routing, but many are still direct")
    print("     The fix partially worked.")
elif austria_pct > 40 and switzerland_pct > 40:
    print("  ✅ SUCCESS - Routes now pass through Austria and/or Switzerland")
    print("     The fix successfully preserved intermediate routing!")
else:
    print("  ⚠️  UNCLEAR - Routes have intermediate countries but percentages don't match expected")
    print("     The fix may have worked, but network structure differs from expectations.")

# ==============================================================================
# SAMPLE ROUTES
# ==============================================================================

print("\n" + "="*80)
print("SAMPLE ROUTES")
print("="*80)

if routes_via_austria:
    print("\nTop 5 routes via AUSTRIA:")
    routes_via_austria.sort(key=lambda x: x[2], reverse=True)
    for i, (origin, dest, flow, countries) in enumerate(routes_via_austria[:5], 1):
        countries_str = ' → '.join(countries)
        print(f"  {i}. Zone {origin} → {dest}")
        print(f"     Flow: {flow:,.0f} trucks")
        print(f"     Countries: {countries_str}")

if routes_via_switzerland:
    print("\nTop 5 routes via SWITZERLAND:")
    routes_via_switzerland.sort(key=lambda x: x[2], reverse=True)
    for i, (origin, dest, flow, countries) in enumerate(routes_via_switzerland[:5], 1):
        countries_str = ' → '.join(countries)
        print(f"  {i}. Zone {origin} → {dest}")
        print(f"     Flow: {flow:,.0f} trucks")
        print(f"     Countries: {countries_str}")

if routes_via_neither and len(routes_via_neither) > 0:
    print("\nTop 5 DIRECT routes (no intermediate countries):")
    routes_via_neither.sort(key=lambda x: x[2], reverse=True)
    for i, (origin, dest, flow, countries) in enumerate(routes_via_neither[:5], 1):
        countries_str = ' → '.join(countries) if countries else "No countries!"
        print(f"  {i}. Zone {origin} → {dest}")
        print(f"     Flow: {flow:,.0f} trucks")
        print(f"     Countries: {countries_str}")

print("\n" + "="*80)
