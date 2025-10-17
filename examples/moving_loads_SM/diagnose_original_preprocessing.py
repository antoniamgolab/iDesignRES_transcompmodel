"""
Diagnose why SM-preprocessing.ipynb produces empty YAML files
with the original high-resolution network data
"""
import pandas as pd
import numpy as np

print("="*80)
print("DIAGNOSING ORIGINAL PREPROCESSING")
print("="*80)

# Load original data
print("\n1. Loading original truck traffic data...")
folder = "data/Trucktraffic/"

print("   Loading 01_Trucktrafficflow.csv (this may take a minute - 2.6GB file)...")
truck_traffic = pd.read_csv(folder + "01_Trucktrafficflow.csv", nrows=10000)  # Load first 10k rows for testing
print(f"   Loaded (sample): {len(truck_traffic):,} rows")
print(f"   Columns: {truck_traffic.columns.tolist()}")

nuts_3_to_nodes = pd.read_csv(folder + "02_NUTS-3-Regions.csv")
print(f"   NUTS-3 regions: {len(nuts_3_to_nodes):,}")

network_nodes = pd.read_csv(folder + "03_network-nodes.csv")
print(f"   Network nodes: {len(network_nodes):,}")

network_edges = pd.read_csv(folder + "04_network-edges.csv")
print(f"   Network edges: {len(network_edges):,}")

# Check sample traffic data
print("\n2. Inspecting sample truck traffic...")
print(f"   First row:")
for col in truck_traffic.columns[:10]:  # First 10 columns
    print(f"     {col}: {truck_traffic[col].iloc[0]}")

# Check if Edge_path_E_road exists and has data
print("\n3. Checking Edge_path_E_road column...")
if 'Edge_path_E_road' in truck_traffic.columns:
    print("   [OK] Edge_path_E_road column exists")

    # Check data types
    sample_path = truck_traffic['Edge_path_E_road'].iloc[0]
    print(f"   Sample value type: {type(sample_path)}")
    print(f"   Sample value: {str(sample_path)[:100]}")

    # Check for empty paths
    empty_count = truck_traffic['Edge_path_E_road'].isna().sum()
    print(f"   Empty paths: {empty_count} / {len(truck_traffic)}")

    # Try to parse a sample path
    if not pd.isna(sample_path):
        print(f"\n4. Testing edge path parsing...")
        try:
            if isinstance(sample_path, str):
                # Try parsing as string
                if sample_path.startswith('['):
                    import ast
                    parsed = ast.literal_eval(sample_path)
                    print(f"   [OK] Parsed as list: {len(parsed)} edges")
                    print(f"   Sample edges: {parsed[:5]}")
                else:
                    print(f"   [WARNING] Edge path is string but not a list: {sample_path[:50]}")
            elif isinstance(sample_path, list):
                print(f"   [OK] Already a list: {len(sample_path)} edges")
                print(f"   Sample edges: {sample_path[:5]}")
            else:
                print(f"   [WARNING] Unknown type: {type(sample_path)}")
        except Exception as e:
            print(f"   [ERROR] Failed to parse: {e}")
else:
    print("   [ERROR] Edge_path_E_road column NOT found!")
    print(f"   Available columns with 'edge' or 'path': {[c for c in truck_traffic.columns if 'edge' in c.lower() or 'path' in c.lower()]}")

# Check distances
print("\n5. Checking distance columns...")
dist_cols = ['Distance_from_origin_region_to_E_road',
             'Distance_within_E_road',
             'Distance_from_E_road_to_destination_region']

for col in dist_cols:
    if col in truck_traffic.columns:
        print(f"   {col}: mean={truck_traffic[col].mean():.2f} km")
    else:
        print(f"   [ERROR] {col} NOT FOUND")

# Calculate total distance
if all(col in truck_traffic.columns for col in dist_cols):
    truck_traffic['Total_distance'] = (
        truck_traffic[dist_cols[0]] +
        truck_traffic[dist_cols[1]] +
        truck_traffic[dist_cols[2]]
    )
    print(f"\n   Total distance: mean={truck_traffic['Total_distance'].mean():.2f} km")
    print(f"   Zero distances: {(truck_traffic['Total_distance'] == 0).sum()}")
    print(f"   NaN distances: {truck_traffic['Total_distance'].isna().sum()}")

# Check traffic flow
print("\n6. Checking traffic flow...")
if 'Traffic_flow_trucks_2030' in truck_traffic.columns:
    print(f"   Traffic flow 2030: mean={truck_traffic['Traffic_flow_trucks_2030'].mean():.2f}")
    print(f"   Zero traffic: {(truck_traffic['Traffic_flow_trucks_2030'] == 0).sum()}")
    print(f"   NaN traffic: {truck_traffic['Traffic_flow_trucks_2030'].isna().sum()}")

# Check how many valid routes exist
print("\n7. Checking valid routes...")
valid = truck_traffic[
    (truck_traffic['Total_distance'] > 0) &
    (truck_traffic['Traffic_flow_trucks_2030'] > 0) &
    (~truck_traffic['Edge_path_E_road'].isna()) &
    (truck_traffic['Edge_path_E_road'] != '[]')
]
print(f"   Valid routes (non-zero distance, traffic, and path): {len(valid):,} / {len(truck_traffic):,}")

print("\n" + "="*80)
print("DIAGNOSIS COMPLETE")
print("="*80)
print("\nKey findings:")
print(f"  - Data files loaded successfully")
print(f"  - Sample size: {len(truck_traffic):,} rows")
print(f"  - Valid routes in sample: {len(valid):,}")
print("\nIf valid routes > 0, the original preprocessing should work!")
print("If valid routes = 0, there may be a data format issue.")
