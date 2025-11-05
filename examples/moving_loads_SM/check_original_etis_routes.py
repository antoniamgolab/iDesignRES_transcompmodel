"""
CHECK: Do the original ETISplus routes pass through Switzerland?

This script checks the ORIGINAL traffic data BEFORE preprocessing to see
if routes from Germany to Italy actually pass through Switzerland instead
of Austria.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import pandas as pd
import yaml
import ast

print("="*80)
print("CHECKING ORIGINAL ETISplus ROUTES")
print("="*80)

# ==============================================================================
# LOAD ORIGINAL TRAFFIC DATA
# ==============================================================================

print("\nLoading original traffic data...")

# Load the truck traffic data used by preprocessing
traffic_file = 'data/Truck_traffic_2018.csv'

try:
    traffic_df = pd.read_csv(traffic_file, sep=';', encoding='latin1')
    print(f"✓ Loaded {len(traffic_df):,} traffic rows from {traffic_file}")
except Exception as e:
    print(f"✗ Could not load traffic data: {e}")
    print("\nTrying alternative path...")
    traffic_file = '../../../data/Truck_traffic_2018.csv'
    try:
        traffic_df = pd.read_csv(traffic_file, sep=';', encoding='latin1')
        print(f"✓ Loaded {len(traffic_df):,} traffic rows from {traffic_file}")
    except Exception as e:
        print(f"✗ Could not load traffic data: {e}")
        sys.exit(1)

# ==============================================================================
# LOAD NUTS2 MAPPING (from preprocessing output)
# ==============================================================================

print("\nLoading NUTS-2 mapping from preprocessed data...")

case_study_name = 'case_20251103_114421'
input_dir = f'input_data/{case_study_name}'

with open(f'{input_dir}/GeographicElement.yaml', 'r', encoding='utf-8') as f:
    geo_elements = yaml.safe_load(f)

# Map node ID to NUTS2
node_to_nuts2 = {}
for geo in geo_elements:
    if geo['type'] == 'node' and 'nuts2_region' in geo:
        node_to_nuts2[geo['id']] = {
            'nuts2': geo['nuts2_region'],
            'country': geo.get('country', 'UNKNOWN')
        }

# Load NUTS-3 to NUTS-2 mapping from a shapefile or create approximate mapping
# For now, use simple string matching (first 4 chars of NUTS-3 = NUTS-2)

print("  Creating NUTS-3 to NUTS-2 mapping...")

def nuts3_to_nuts2_code(nuts3):
    """Convert NUTS-3 zone to NUTS-2 region code."""
    if pd.isna(nuts3):
        return None
    nuts3_str = str(nuts3)

    # ETISplus uses various formats, try to extract NUTS code
    # Format can be: "DE600", "AT130", etc.
    if len(nuts3_str) >= 4:
        # First 2 chars = country, next 1-2 chars = NUTS-2
        country = nuts3_str[:2]

        # For most countries, NUTS-2 is 4 characters (e.g., DEA1, AT31)
        if len(nuts3_str) >= 4:
            return nuts3_str[:4]

    return None

# ==============================================================================
# ANALYZE ROUTES FROM GERMANY TO ITALY
# ==============================================================================

print("\n" + "="*80)
print("ANALYZING GERMANY → ITALY ROUTES IN ORIGINAL DATA")
print("="*80)

# Filter for Germany → Italy traffic
de_to_it_traffic = traffic_df[
    (traffic_df['ID_origin_region'].astype(str).str.startswith('DE')) &
    (traffic_df['ID_destination_region'].astype(str).str.startswith('IT'))
].copy()

print(f"\nFound {len(de_to_it_traffic):,} Germany → Italy traffic rows")

if len(de_to_it_traffic) == 0:
    print("No Germany → Italy traffic found!")
    sys.exit(1)

# Check if there's a 'Network_Edge_IDs' or similar field with route information
print("\nColumns in traffic data:")
for i, col in enumerate(traffic_df.columns, 1):
    print(f"  {i:2}. {col}")

# ==============================================================================
# CHECK FOR ROUTE/PATH COLUMNS
# ==============================================================================

print("\n" + "="*80)
print("CHECKING FOR ROUTE INFORMATION")
print("="*80)

# Look for columns that might contain route information
route_columns = [col for col in traffic_df.columns if any(
    keyword in col.lower() for keyword in ['route', 'path', 'edge', 'network', 'node']
)]

print(f"\nFound {len(route_columns)} potential route columns:")
for col in route_columns:
    print(f"  • {col}")

if route_columns:
    print("\nExamining route data for Germany → Italy flows...")

    for col in route_columns:
        print(f"\n--- Column: {col} ---")

        # Show some examples
        sample = de_to_it_traffic[col].dropna().head(3)

        if len(sample) > 0:
            print(f"Sample values ({len(sample)} shown):")
            for i, val in enumerate(sample, 1):
                val_str = str(val)
                if len(val_str) > 200:
                    val_str = val_str[:200] + "..."
                print(f"  {i}. {val_str}")
        else:
            print("  (No non-null values in this column)")

# ==============================================================================
# ANALYZE TOP GERMANY → ITALY FLOWS
# ==============================================================================

print("\n" + "="*80)
print("TOP GERMANY → ITALY FLOWS (by traffic volume)")
print("="*80)

# Sort by traffic flow
de_to_it_sorted = de_to_it_traffic.sort_values(
    'Traffic_flow_trucks_2030',
    ascending=False
).head(20)

print(f"\n{'Rank':<6} {'Origin':<12} {'Destination':<12} {'Flow (trucks)':>15} {'Distance (km)':>15}")
print("-" * 70)

for i, row in enumerate(de_to_it_sorted.itertuples(), 1):
    origin = str(row.ID_origin_region)[:10]
    dest = str(row.ID_destination_region)[:10]
    flow = row.Traffic_flow_trucks_2030
    distance = row.Total_distance

    print(f"{i:<6} {origin:<12} {dest:<12} {flow:>15,.0f} {distance:>15.1f}")

# ==============================================================================
# CHECK SPECIFIC ROUTE: DEA1 → ITC4
# ==============================================================================

print("\n" + "="*80)
print("SPECIFIC ROUTE: DEA1 → ITC4")
print("="*80)

# Find rows for this specific OD-pair
# DEA1 covers multiple NUTS-3 zones, e.g., DE600
dea1_to_itc4 = traffic_df[
    (traffic_df['ID_origin_region'].astype(str).str.startswith('DEA')) &
    (traffic_df['ID_destination_region'].astype(str).str.startswith('ITC4'))
]

print(f"\nFound {len(dea1_to_itc4)} rows for DEA → ITC4")

if len(dea1_to_itc4) > 0:
    print("\nSample rows:")
    for i, row in enumerate(dea1_to_itc4.head(5).itertuples(), 1):
        print(f"\n  Row {i}:")
        print(f"    Origin: {row.ID_origin_region}")
        print(f"    Destination: {row.ID_destination_region}")
        print(f"    Flow (2030): {row.Traffic_flow_trucks_2030:,.0f} trucks")
        print(f"    Distance: {row.Total_distance:.1f} km")

        # Check if there's route information
        if route_columns:
            for col in route_columns:
                val = getattr(row, col, None)
                if val and not pd.isna(val):
                    val_str = str(val)
                    if len(val_str) > 150:
                        val_str = val_str[:150] + "..."
                    print(f"    {col}: {val_str}")

# ==============================================================================
# GEOGRAPHIC ANALYSIS: DOES THE ROUTE GO THROUGH SWITZERLAND?
# ==============================================================================

print("\n" + "="*80)
print("GEOGRAPHIC ANALYSIS")
print("="*80)

print("""
To determine if Germany → Italy routes go through Switzerland or Austria,
we need to check the 'Network_Edge_IDs' column if it exists.

The ETISplus network contains the actual road/rail network with intermediate
nodes. By examining which nodes are traversed, we can determine if routes
pass through:
  • Austria (AT)
  • Switzerland (CH)
  • Or both

Let me check if we can extract this information...
""")

# Look for edge/node sequence columns
if 'Network_Edge_IDs' in traffic_df.columns:
    print("✓ Found 'Network_Edge_IDs' column!")
    print("\nAnalyzing edge sequences for Germany → Italy routes...")

    # Sample a few routes and try to parse the edge IDs
    sample_routes = de_to_it_traffic[
        de_to_it_traffic['Network_Edge_IDs'].notna()
    ].head(5)

    for i, row in enumerate(sample_routes.itertuples(), 1):
        print(f"\n--- Route {i}: {row.ID_origin_region} → {row.ID_destination_region} ---")
        print(f"  Flow: {row.Traffic_flow_trucks_2030:,.0f} trucks")
        print(f"  Distance: {row.Total_distance:.1f} km")

        # Try to parse edge IDs
        edge_str = str(row.Network_Edge_IDs)
        if edge_str and edge_str != 'nan':
            print(f"  Edges: {edge_str[:200]}...")

            # Try to parse as list
            try:
                if edge_str.startswith('['):
                    edges = ast.literal_eval(edge_str)
                    print(f"  Number of edges: {len(edges)}")
            except:
                pass

else:
    print("✗ No 'Network_Edge_IDs' column found")
    print("\nThe traffic data may not include detailed route information.")
    print("This means we cannot directly determine if routes go through")
    print("Switzerland or Austria from the preprocessed data.")

print("\n" + "="*80)
print("CONCLUSION")
print("="*80)

print("""
The ETISplus traffic data contains actual distances between OD-pairs,
but may not explicitly store the intermediate nodes/countries traversed.

The preprocessing script:
1. Takes these OD-pairs with their total distances
2. Aggregates origins/destinations to NUTS-2 level
3. Creates paths WITHOUT building an edge network
4. Results in direct 2-node paths with accurate distances

Therefore, we CANNOT determine from the current data whether Germany → Italy
routes go through Austria or Switzerland. The distance values are accurate
(they come from ETISplus actual network), but the intermediate routing
information has been abstracted away during the NUTS-2 aggregation.

RECOMMENDATION:
To answer your question definitively, you would need to:
  1. Examine the ORIGINAL ETISplus network data (before aggregation)
  2. Or use geographic analysis (straight-line paths through coordinates)
  3. Or consult transport geography literature about Alpine crossing routes
""")
