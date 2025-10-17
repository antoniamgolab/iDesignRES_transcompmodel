"""
Quick test to verify the preprocessing fix works
"""
import pandas as pd
from preprocessing_fix_for_nuts3 import create_nuts3_paths_from_traffic

# Load NUTS-3 data
print("Loading data...")
truck_traffic = pd.read_csv("data/Trucktraffic_NUTS3/01_Trucktrafficflow.csv")
network_nodes = pd.read_csv("data/Trucktraffic_NUTS3/03_network-nodes.csv")
network_edges = pd.read_csv("data/Trucktraffic_NUTS3/04_network-edges.csv")

print(f"Loaded:")
print(f"  Traffic: {len(truck_traffic):,} rows")
print(f"  Nodes: {len(network_nodes):,}")
print(f"  Edges: {len(network_edges):,}")

# Test with 10 OD-pairs
print("\nCreating 10 OD-pairs...")
odpair_list, path_list = create_nuts3_paths_from_traffic(
    truck_traffic=truck_traffic,
    network_nodes=network_nodes,
    network_edges=network_edges,
    max_odpairs=10
)

print(f"\nResults:")
print(f"  OD-pairs: {len(odpair_list)}")
print(f"  Paths: {len(path_list)}")

if len(odpair_list) > 0:
    print(f"\nFirst OD-pair:")
    print(f"  From: {odpair_list[0]['from']}")
    print(f"  To: {odpair_list[0]['to']}")
    print(f"  Traffic 2030: {odpair_list[0]['F'][0]:,.0f}")

    print(f"\nFirst path:")
    print(f"  Length: {path_list[0]['length']:.2f} km")
    print(f"  Nodes: {path_list[0]['sequence']}")
else:
    print("\n[ERROR] No OD-pairs created!")
