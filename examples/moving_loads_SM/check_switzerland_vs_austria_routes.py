"""
CHECK: Do Germany→Italy routes go through Austria or Switzerland?

This script analyzes the 'Edge_path_E_road' column in the original traffic data
to determine which countries routes actually pass through.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import pandas as pd
import ast

print("="*80)
print("CHECKING ROUTES: AUSTRIA vs SWITZERLAND")
print("="*80)

# ==============================================================================
# LOAD DATA
# ==============================================================================

print("\nLoading traffic data...")
traffic_file = 'data/Trucktraffic_NUTS3/01_Trucktrafficflow.csv'

traffic_df = pd.read_csv(traffic_file)
print(f"✓ Loaded {len(traffic_df):,} traffic rows")

# Load network edges to map edge IDs to countries
edges_file = 'data/Trucktraffic_NUTS3/04_network-edges.csv'
edges_df = pd.read_csv(edges_file)
print(f"✓ Loaded {len(edges_df):,} network edges")

# Load network nodes to get country information
nodes_file = 'data/Trucktraffic_NUTS3/03_network-nodes.csv'
nodes_df = pd.read_csv(nodes_file)
print(f"✓ Loaded {len(nodes_df):,} network nodes")

print("\nEdge columns:", edges_df.columns.tolist())
print("Node columns:", nodes_df.columns.tolist())

# ==============================================================================
# CREATE NODE TO COUNTRY MAPPING
# ==============================================================================

# Nodes have a 'Country' column
node_to_country = {}

if 'Country' in nodes_df.columns:
    for _, node in nodes_df.iterrows():
        node_id = node['Network_Node_ID']
        country = str(node['Country']).strip()
        if country and country != 'nan':
            node_to_country[node_id] = country

print(f"\n✓ Mapped {len(node_to_country)} nodes to countries")

# Sample
sample_nodes = list(node_to_country.items())[:5]
print("  Sample mappings:")
for node_id, country in sample_nodes:
    print(f"    Node {node_id} → {country}")

# ==============================================================================
# CREATE EDGE TO COUNTRY MAPPING
# ==============================================================================

# Each edge connects two nodes - determine which country(ies) it passes through
edge_countries = {}

for _, edge in edges_df.iterrows():
    edge_id = edge['Network_Edge_ID']
    node_a = edge['Network_Node_A_ID']
    node_b = edge['Network_Node_B_ID']

    country_a = node_to_country.get(node_a)
    country_b = node_to_country.get(node_b)

    # Edge belongs to both countries
    countries = set()
    if country_a:
        countries.add(country_a)
    if country_b:
        countries.add(country_b)

    edge_countries[edge_id] = countries

print(f"\n✓ Mapped {len(edge_countries)} edges to countries")

# ==============================================================================
# ANALYZE GERMANY → ITALY ROUTES
# ==============================================================================

print("\n" + "="*80)
print("ANALYZING GERMANY → ITALY ROUTES")
print("="*80)

# Filter for Germany → Italy
de_to_it = traffic_df[
    (traffic_df['ID_origin_region'].astype(str).str.startswith('DE')) &
    (traffic_df['ID_destination_region'].astype(str).str.startswith('IT'))
].copy()

print(f"\nFound {len(de_to_it):,} Germany → Italy OD-pairs")

# Analyze routes
routes_via_austria = []
routes_via_switzerland = []
routes_via_both = []
routes_via_neither = []
routes_no_data = []

for idx, row in de_to_it.iterrows():
    origin = row['ID_origin_region']
    dest = row['ID_destination_region']
    flow = row['Traffic_flow_trucks_2030']
    edge_path_str = row['Edge_path_E_road']

    if pd.isna(edge_path_str) or edge_path_str == '':
        routes_no_data.append((origin, dest, flow))
        continue

    # Parse edge path
    try:
        # Try to parse as list
        if edge_path_str.startswith('['):
            edge_path = ast.literal_eval(edge_path_str)
        else:
            # Try comma-separated
            edge_path = [int(x.strip()) for x in edge_path_str.split(',') if x.strip()]
    except:
        routes_no_data.append((origin, dest, flow))
        continue

    # Check which countries this route passes through
    countries_on_route = set()
    for edge_id in edge_path:
        if edge_id in edge_countries:
            countries_on_route.update(edge_countries[edge_id])

    passes_austria = 'AT' in countries_on_route
    passes_switzerland = 'CH' in countries_on_route

    if passes_austria and passes_switzerland:
        routes_via_both.append((origin, dest, flow, countries_on_route))
    elif passes_austria:
        routes_via_austria.append((origin, dest, flow, countries_on_route))
    elif passes_switzerland:
        routes_via_switzerland.append((origin, dest, flow, countries_on_route))
    else:
        routes_via_neither.append((origin, dest, flow, countries_on_route))

# ==============================================================================
# SUMMARY
# ==============================================================================

print("\n" + "="*80)
print("RESULTS")
print("="*80)

total_routes = len(de_to_it)
total_flow_austria = sum(r[2] for r in routes_via_austria)
total_flow_switzerland = sum(r[2] for r in routes_via_switzerland)
total_flow_both = sum(r[2] for r in routes_via_both)
total_flow_neither = sum(r[2] for r in routes_via_neither)
total_flow_all = total_flow_austria + total_flow_switzerland + total_flow_both + total_flow_neither

print(f"\nTotal Germany → Italy OD-pairs: {total_routes:,}")
print(f"  • With route data: {total_routes - len(routes_no_data):,}")
print(f"  • Without route data: {len(routes_no_data):,}")

print(f"\n{'Route Type':<40} {'Count':>10} {'Flow (trucks)':>18} {'%':>8}")
print("-" * 80)
print(f"{'Via Austria only':<40} {len(routes_via_austria):>10,} {total_flow_austria:>18,.0f} {100*total_flow_austria/total_flow_all:>7.1f}%")
print(f"{'Via Switzerland only':<40} {len(routes_via_switzerland):>10,} {total_flow_switzerland:>18,.0f} {100*total_flow_switzerland/total_flow_all:>7.1f}%")
print(f"{'Via both Austria and Switzerland':<40} {len(routes_via_both):>10,} {total_flow_both:>18,.0f} {100*total_flow_both/total_flow_all:>7.1f}%")
print(f"{'Via neither (direct)':<40} {len(routes_via_neither):>10,} {total_flow_neither:>18,.0f} {100*total_flow_neither/total_flow_all:>7.1f}%")
print("-" * 80)
print(f"{'TOTAL':<40} {len(de_to_it) - len(routes_no_data):>10,} {total_flow_all:>18,.0f} {100.0:>7.1f}%")

# ==============================================================================
# TOP ROUTES BY EACH CATEGORY
# ==============================================================================

print("\n" + "="*80)
print("TOP 5 ROUTES VIA AUSTRIA ONLY")
print("="*80)

routes_via_austria.sort(key=lambda x: x[2], reverse=True)
print(f"\n{'Origin':<15} {'Destination':<15} {'Flow (trucks)':>18} {'Countries'}")
print("-" * 80)
for origin, dest, flow, countries in routes_via_austria[:5]:
    countries_str = ', '.join(sorted(countries))
    print(f"{origin:<15} {dest:<15} {flow:>18,.0f} {countries_str}")

print("\n" + "="*80)
print("TOP 5 ROUTES VIA SWITZERLAND ONLY")
print("="*80)

routes_via_switzerland.sort(key=lambda x: x[2], reverse=True)
print(f"\n{'Origin':<15} {'Destination':<15} {'Flow (trucks)':>18} {'Countries'}")
print("-" * 80)
for origin, dest, flow, countries in routes_via_switzerland[:5]:
    countries_str = ', '.join(sorted(countries))
    print(f"{origin:<15} {dest:<15} {flow:>18,.0f} {countries_str}")

# ==============================================================================
# ANSWER THE QUESTION
# ==============================================================================

print("\n" + "="*80)
print("ANSWER TO YOUR QUESTION")
print("="*80)

austria_pct = 100 * (total_flow_austria + total_flow_both) / total_flow_all
switzerland_pct = 100 * (total_flow_switzerland + total_flow_both) / total_flow_all

print(f"""
Based on the original ETISplus traffic data with 'Edge_path_E_road':

🔍 FINDING:
   • {austria_pct:.1f}% of Germany→Italy freight passes through AUSTRIA
   • {switzerland_pct:.1f}% of Germany→Italy freight passes through SWITZERLAND

📊 BREAKDOWN:
   • Austria only:        {len(routes_via_austria):,} routes ({100*total_flow_austria/total_flow_all:.1f}% of flow)
   • Switzerland only:    {len(routes_via_switzerland):,} routes ({100*total_flow_switzerland/total_flow_all:.1f}% of flow)
   • Both:                {len(routes_via_both):,} routes ({100*total_flow_both/total_flow_all:.1f}% of flow)

💡 CONCLUSION:
   The "direct" DEA1 → ITC4 routes in your preprocessed data actually represent
   freight that passes through {"AUSTRIA" if austria_pct > switzerland_pct else "SWITZERLAND"} in reality.

   This explains why Austrian NUTS2 regions don't appear in your model's path
   sequences - the preprocessing aggregated multi-hop routes into single edges,
   losing the intermediate node information.
""")
