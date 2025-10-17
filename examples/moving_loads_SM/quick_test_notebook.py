"""
Quick test to see if the notebook's auto-detect logic would work
"""
import pandas as pd
from preprocessing_fix_for_nuts3 import create_nuts3_paths_from_traffic

# Simulate notebook environment
resolution = "reduced"
folder = "data/Trucktraffic_NUTS3/" if resolution == "reduced" else "data/Trucktraffic/"

print("="*80)
print("TESTING AUTO-DETECT LOGIC")
print("="*80)
print(f"Resolution: {resolution}")
print(f"Folder: {folder}")

# Load data (just like notebook does)
print("\nLoading data...")
truck_traffic = pd.read_csv(folder + "01_Trucktrafficflow.csv", nrows=1000)
network_nodes = pd.read_csv(folder + "03_network-nodes.csv")
network_edges = pd.read_csv(folder + "04_network-edges.csv")

# Apply notebook's filtering
print("Filtering long-haul traffic...")
truck_traffic['Total_distance'] = (
    truck_traffic['Distance_from_origin_region_to_E_road'] +
    truck_traffic['Distance_within_E_road'] +
    truck_traffic['Distance_from_E_road_to_destination_region']
)

long_haul_truck_traffic = truck_traffic[
    (truck_traffic['Total_distance'] >= 300) &
    (truck_traffic['Traffic_flow_trucks_2030'] > 0)
]
print(f"Long-haul traffic: {len(long_haul_truck_traffic)} rows")

# Set variables like notebook would
filtered_network_nodes = network_nodes
filtered_network_edges = network_edges

# Test auto-detect logic
print("\n" + "="*80)
if resolution == "reduced":
    print("USING NUTS-3 PREPROCESSING")
    print("="*80)

    MAX_ODPAIRS = 10  # Small test

    # Auto-detect (like the patched cell does)
    traffic_var = long_haul_truck_traffic if "long_haul_truck_traffic" in dir() else truck_traffic
    nodes_var = filtered_network_nodes if "filtered_network_nodes" in dir() else network_nodes
    edges_var = filtered_network_edges if "filtered_network_edges" in dir() else network_edges

    print(f"Using: {len(traffic_var):,} traffic rows, {len(nodes_var):,} nodes, {len(edges_var):,} edges")

    # Create OD-pairs
    odpair_list, path_list = create_nuts3_paths_from_traffic(
        truck_traffic=traffic_var,
        network_nodes=nodes_var,
        network_edges=edges_var,
        max_odpairs=MAX_ODPAIRS
    )

    print(f"\n[SUCCESS] Created {len(odpair_list)} OD-pairs and {len(path_list)} paths")

    if len(odpair_list) > 0:
        print("\nSample OD-pair:")
        print(f"  From: {odpair_list[0]['from']}")
        print(f"  To: {odpair_list[0]['to']}")
        print(f"  Traffic: {odpair_list[0]['F'][0]:,.0f}")
    else:
        print("\n[ERROR] No OD-pairs created!")

else:
    print("USING ORIGINAL HIGH-RESOLUTION PREPROCESSING")
    print("(Would use original code)")

print("\n" + "="*80)
print("If you see 'Created X OD-pairs' with X > 0, the logic works!")
print("If X = 0, there's a data filtering issue.")
