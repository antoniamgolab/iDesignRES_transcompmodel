"""
Create a complete NUTS-3 case by:
1. Copying a working case folder as a base
2. Generating only the NUTS-3-specific files (Odpair, Path, GeographicElement, etc.)
3. Overwriting those specific files in the copied case

This avoids having to recreate all the auxiliary files from scratch.
"""
import pandas as pd
import yaml
import os
import shutil
from datetime import datetime
from preprocessing_fix_for_nuts3 import (
    create_nuts3_paths_from_traffic,
    create_simplified_spatial_flexibility
)

print("="*80)
print("NUTS-3 CASE GENERATOR")
print("="*80)

# ============================================================================
# ADJUSTABLE PARAMETERS - CHANGE THESE FOR DIFFERENT RUNS
# ============================================================================
BASE_CASE = "input_data/case_1_20251014_134333"  # Working case to copy from
MAX_ODPAIRS = 1000  # None = all OD-pairs, or set to number (e.g., 100) for testing
LONG_HAUL_THRESHOLD = 300  # Minimum distance in km for long-haul (300 km default)
# ============================================================================

# Step 1: Copy base case
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
new_case_name = f"case_nuts3_{timestamp}"
new_case_dir = f"input_data/{new_case_name}"

print(f"\n1. Copying base case from {BASE_CASE}...")
shutil.copytree(BASE_CASE, new_case_dir)
print(f"   Created: {new_case_dir}")

# Step 2: Load NUTS-3 data
print("\n2. Loading NUTS-3 aggregated data...")
truck_traffic = pd.read_csv("data/Trucktraffic_NUTS3/01_Trucktrafficflow.csv")
network_nodes = pd.read_csv("data/Trucktraffic_NUTS3/03_network-nodes.csv")
network_edges = pd.read_csv("data/Trucktraffic_NUTS3/04_network-edges.csv")

print(f"   Traffic: {len(truck_traffic):,} rows")
print(f"   Nodes: {len(network_nodes):,}")
print(f"   Edges: {len(network_edges):,}")

# Step 3: Generate NUTS-3 specific data
print(f"\n3. Generating NUTS-3 OD-pairs and paths...")
if MAX_ODPAIRS:
    print(f"   [TEST MODE] Limited to {MAX_ODPAIRS} OD-pairs")

odpair_list, path_list, initial_vehicle_stock = create_nuts3_paths_from_traffic(
    truck_traffic=truck_traffic,
    network_nodes=network_nodes,
    network_edges=network_edges,
    max_odpairs=MAX_ODPAIRS
)

print(f"   Created {len(odpair_list)} OD-pairs")
print(f"   Created {len(path_list)} paths")
print(f"   Created {len(initial_vehicle_stock)} vehicle stock entries")

# Step 4: Create supporting structures
print("\n4. Creating supporting data structures...")

spatial_flex_range_list = create_simplified_spatial_flexibility(
    path_list=path_list,
    max_flexibility=5
)
print(f"   Spatial flexibility: {len(spatial_flex_range_list)} entries")

mandatory_breaks_list = []
print(f"   Mandatory breaks: {len(mandatory_breaks_list)} entries (skipped)")

# Step 5: Update GeographicElement to use NUTS-3 nodes
print("\n5. Creating NUTS-3 geographic elements...")

# Read carbon price from original file to maintain consistency
with open(f"{BASE_CASE}/GeographicElement.yaml", 'r') as f:
    original_geo = yaml.safe_load(f)
    if original_geo and len(original_geo) > 0:
        carbon_price = original_geo[0].get('carbon_price', [30.0 + i * 5.7 for i in range(21)])
    else:
        carbon_price = [30.0 + i * 5.7 for i in range(21)]

geographic_elements = []
for _, node in network_nodes.iterrows():
    geographic_elements.append({
        'id': int(node['Network_Node_ID']),
        'name': f"NUTS3_{node['ETISplus_Zone_ID']}",
        'type': 'node',
        'coordinate_lat': float(node['Network_Node_Y']),
        'coordinate_long': float(node['Network_Node_X']),
        'country': 'XX',  # Placeholder
        'nuts3_region': int(node['ETISplus_Zone_ID']),
        'from': 999999,
        'to': 999999,
        'length': 0.0,
        'carbon_price': carbon_price
    })
print(f"   Geographic elements: {len(geographic_elements)}")

# Step 6: Convert to native types
print("\n6. Converting to native Python types...")

def convert_to_native(obj):
    """Convert NumPy types to native Python types"""
    import numpy as np

    if isinstance(obj, dict):
        return {k: convert_to_native(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_native(item) for item in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj

# Step 7: Save only the modified files
print("\n7. Overwriting NUTS-3-specific files...")

files_to_update = {
    "Odpair": odpair_list,
    "Path": path_list,
    "InitialVehicleStock": initial_vehicle_stock,
    "MandatoryBreaks": mandatory_breaks_list,
    "SpatialFlexibilityEdges": spatial_flex_range_list,
    "GeographicElement": geographic_elements,
}

for name, data in files_to_update.items():
    filepath = os.path.join(new_case_dir, f"{name}.yaml")
    clean_data = convert_to_native(data)
    with open(filepath, 'w') as f:
        yaml.dump(clean_data, f, default_flow_style=False, sort_keys=False)
    file_size = os.path.getsize(filepath)
    print(f"   [OK] {name}.yaml ({file_size:,} bytes)")

# Step 8: Summary
print("\n" + "="*80)
print("SUCCESS!")
print("="*80)
print(f"\nCase folder: {new_case_dir}")
print(f"\nData summary:")
print(f"  OD-pairs: {len(odpair_list):,}")
print(f"  Paths: {len(path_list):,}")
print(f"  Geographic nodes: {len(geographic_elements):,}")
print(f"  Vehicle stock: {len(initial_vehicle_stock):,}")
print(f"  Spatial flexibility: {len(spatial_flex_range_list):,}")

print(f"\nTo use this case:")
print(f'1. Update SM.jl line 11 to: folder = "{new_case_name}"')
print(f'2. Run: julia SM.jl')

print(f"\nTo generate full dataset (all OD-pairs):")
print(f"1. Change MAX_ODPAIRS = None in this script")
print(f"2. Run: python create_nuts3_case.py")
