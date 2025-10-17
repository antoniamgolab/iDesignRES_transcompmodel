"""
Diagnose SM-preprocessing Issues with Aggregated Data
======================================================

This script helps identify why SM-preprocessing.ipynb produces empty
Odpair.yaml and Path.yaml files when using aggregated NUTS-3 data.
"""

import pandas as pd
import numpy as np

print("="*80)
print("DIAGNOSING SM-PREPROCESSING WITH AGGREGATED DATA")
print("="*80)

# Load aggregated data
print("\n1. Loading aggregated truck traffic data...")
truck_traffic = pd.read_csv("data/Trucktraffic_NUTS3/01_Trucktrafficflow.csv")
print(f"   Total rows: {len(truck_traffic):,}")
print(f"   Columns: {truck_traffic.columns.tolist()}")

# Calculate total distance
print("\n2. Calculating Total_distance...")
truck_traffic['Total_distance'] = (
    truck_traffic['Distance_from_origin_region_to_E_road'] +
    truck_traffic['Distance_within_E_road'] +
    truck_traffic['Distance_from_E_road_to_destination_region']
)
print(f"   Total_distance calculated")

# Check for typical filtering conditions
print("\n3. Checking data quality...")
print(f"   Rows with NaN in Total_distance: {truck_traffic['Total_distance'].isna().sum()}")
print(f"   Rows with NaN in Traffic_flow_trucks_2030: {truck_traffic['Traffic_flow_trucks_2030'].isna().sum()}")
print(f"   Rows with zero distance: {(truck_traffic['Total_distance'] == 0).sum()}")
print(f"   Rows with zero traffic: {(truck_traffic['Traffic_flow_trucks_2030'] == 0).sum()}")

# Typical filtering conditions from SM-preprocessing
print("\n4. Applying typical filters...")

# Filter 1: Remove zero/NaN distances
filtered = truck_traffic[
    (truck_traffic['Total_distance'] > 0) &
    (~truck_traffic['Total_distance'].isna())
]
print(f"   After removing zero/NaN distances: {len(filtered):,} rows ({100*len(filtered)/len(truck_traffic):.1f}%)")

# Filter 2: Remove zero/NaN traffic
filtered = filtered[
    (filtered['Traffic_flow_trucks_2030'] > 0) &
    (~filtered['Traffic_flow_trucks_2030'].isna())
]
print(f"   After removing zero/NaN traffic: {len(filtered):,} rows ({100*len(filtered)/len(truck_traffic):.1f}%)")

# Filter 3: Check if Edge_path_E_road is valid
print(f"\n5. Checking Edge_path_E_road...")
if 'Edge_path_E_road' in filtered.columns:
    # Check for empty paths
    empty_paths = filtered['Edge_path_E_road'].isna().sum()
    print(f"   Rows with NaN Edge_path_E_road: {empty_paths}")

    # Check for "[]" string
    if filtered['Edge_path_E_road'].dtype == object:
        empty_str_paths = (filtered['Edge_path_E_road'] == "[]").sum()
        print(f"   Rows with '[]' Edge_path_E_road: {empty_str_paths}")

# Filter 4: Check origin/destination validity
print(f"\n6. Checking origin/destination IDs...")
if 'ID_origin_region' in filtered.columns and 'ID_destination_region' in filtered.columns:
    same_od = (filtered['ID_origin_region'] == filtered['ID_destination_region']).sum()
    print(f"   Rows with same origin and destination: {same_od}")

    nan_origin = filtered['ID_origin_region'].isna().sum()
    nan_dest = filtered['ID_destination_region'].isna().sum()
    print(f"   Rows with NaN origin: {nan_origin}")
    print(f"   Rows with NaN destination: {nan_dest}")

# Summary statistics
print(f"\n7. Final filtered data statistics...")
print(f"   Total rows after filtering: {len(filtered):,}")
print(f"   Unique O-D pairs: {filtered.groupby(['ID_origin_region', 'ID_destination_region']).ngroups:,}")
print(f"   Total traffic (2030): {filtered['Traffic_flow_trucks_2030'].sum():,.0f}")
print(f"   Average distance: {filtered['Total_distance'].mean():.2f} km")
print(f"   Distance range: {filtered['Total_distance'].min():.2f} - {filtered['Total_distance'].max():.2f} km")

# Check if this explains the empty output
print("\n" + "="*80)
print("DIAGNOSIS")
print("="*80)

if len(filtered) == 0:
    print("\n[CRITICAL] ALL DATA WAS FILTERED OUT!")
    print("This explains why Odpair.yaml and Path.yaml are empty.")
    print("\nPossible causes:")
    print("  1. Edge_path_E_road contains invalid/empty paths")
    print("  2. All routes have zero distance or traffic")
    print("  3. SM-preprocessing.ipynb has additional filters not checked here")
    print("\nRECOMMENDATION:")
    print("  Check your SM-preprocessing.ipynb for filtering conditions")
    print("  and adjust them for aggregated data.")
elif len(filtered) < 10:
    print(f"\n[WARNING] Only {len(filtered)} rows remain after filtering!")
    print("This may be too few for meaningful optimization.")
else:
    print(f"\n[OK] {len(filtered):,} valid routes found.")
    print("The empty Odpair.yaml might be due to other issues in SM-preprocessing.ipynb")

    # Save sample for inspection
    print("\nSaving sample data for inspection...")
    filtered.head(20).to_csv("filtered_truck_traffic_sample.csv", index=False)
    print("  Saved to: filtered_truck_traffic_sample.csv")

# Load network data
print("\n8. Checking network data...")
try:
    nodes = pd.read_csv("data/Trucktraffic_NUTS3/03_network-nodes.csv")
    edges = pd.read_csv("data/Trucktraffic_NUTS3/04_network-edges.csv")
    print(f"   Network nodes: {len(nodes):,}")
    print(f"   Network edges: {len(edges):,}")

    # Check if O-D regions exist in nodes
    if 'ETISplus_Zone_ID' in nodes.columns:
        valid_regions = set(nodes['ETISplus_Zone_ID'])

        invalid_origins = (~filtered['ID_origin_region'].isin(valid_regions)).sum()
        invalid_dests = (~filtered['ID_destination_region'].isin(valid_regions)).sum()

        print(f"\n   Origins not in network: {invalid_origins}")
        print(f"   Destinations not in network: {invalid_dests}")

        if invalid_origins > 0 or invalid_dests > 0:
            print("\n   [WARNING] Some O-D regions don't exist in the network!")
            print("   This could cause preprocessing to fail.")
except Exception as e:
    print(f"   [ERROR] Could not load network data: {e}")

print("\n" + "="*80)
print("NEXT STEPS")
print("="*80)
print("""
If data was filtered out:
  1. Open SM-preprocessing.ipynb
  2. Find the cell where truck_traffic is filtered
  3. Check conditions like:
     - Minimum distance threshold
     - Minimum traffic threshold
     - Valid Edge_path_E_road requirement
  4. Adjust filters for aggregated data (may need lower thresholds)

If data looks OK:
  1. Check if SM-preprocessing.ipynb has errors during path/OD generation
  2. Look at the console output when running the notebook
  3. Check if there are issues with node/edge matching
""")
