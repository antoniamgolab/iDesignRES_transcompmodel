"""
Standalone script to generate YAML files with NUTS-3 data
Run this instead of SM-preprocessing.ipynb for quick testing
"""
import pandas as pd
import yaml
import os
from datetime import datetime
from preprocessing_fix_for_nuts3 import (
    create_nuts3_paths_from_traffic,
    create_simplified_spatial_flexibility
)

print("="*80)
print("STANDALONE YAML GENERATOR FOR NUTS-3 DATA")
print("="*80)

# Load data
print("\n1. Loading NUTS-3 data...")
truck_traffic = pd.read_csv("data/Trucktraffic_NUTS3/01_Trucktrafficflow.csv")
network_nodes = pd.read_csv("data/Trucktraffic_NUTS3/03_network-nodes.csv")
network_edges = pd.read_csv("data/Trucktraffic_NUTS3/04_network-edges.csv")

print(f"   Loaded:")
print(f"   - Traffic: {len(truck_traffic):,} rows")
print(f"   - Nodes: {len(network_nodes):,}")
print(f"   - Edges: {len(network_edges):,}")

# Create OD-pairs and paths
print("\n2. Creating OD-pairs and paths...")
MAX_ODPAIRS = 100  # Change to None for full dataset

odpair_list, path_list = create_nuts3_paths_from_traffic(
    truck_traffic=truck_traffic,
    network_nodes=network_nodes,
    network_edges=network_edges,
    max_odpairs=MAX_ODPAIRS
)

print(f"\n   Created {len(odpair_list)} OD-pairs")
print(f"   Created {len(path_list)} paths")

# Create other required lists
print("\n3. Creating supporting data structures...")

spatial_flex_range_list = create_simplified_spatial_flexibility(
    path_list=path_list,
    max_flexibility=5
)
print(f"   Spatial flexibility: {len(spatial_flex_range_list)} entries")

initial_vehicle_stock = []
for i, odp in enumerate(odpair_list):
    initial_vehicle_stock.extend(odp['vehicle_stock_init'])
print(f"   Vehicle stock: {len(initial_vehicle_stock)} entries")

mandatory_breaks_list = []
print(f"   Mandatory breaks: {len(mandatory_breaks_list)} entries (skipped)")

# Create minimal required data (copy from your notebook or use defaults)
print("\n4. Creating minimal required data structures...")

# Create carbon price list (21 years, increasing from 30 to ~150)
carbon_price = [30.0 + i * 5.7 for i in range(21)]

# Create geographic elements with all required fields
geographic_elements = []
for _, node in network_nodes.iterrows():
    geographic_elements.append({
        'id': int(node['Network_Node_ID']),
        'name': f"NUTS3_{node['ETISplus_Zone_ID']}",
        'type': 'node',
        'coordinate_lat': float(node['Network_Node_Y']),
        'coordinate_long': float(node['Network_Node_X']),
        'country': 'XX',  # Unknown - use placeholder
        'nuts3_region': int(node['ETISplus_Zone_ID']),
        'from': 999999,
        'to': 999999,
        'length': 0.0,
        'carbon_price': carbon_price
    })
print(f"   Geographic elements: {len(geographic_elements)}")

# Minimal other structures
financial_status = [{'id': 0, 'name': 'any'}]
fuel = [{'id': 0, 'name': 'diesel'}, {'id': 1, 'name': 'electricity'}]
mode = [{'id': 0, 'name': 'road'}]
product = [{'id': 0, 'name': 'freight'}]
regiontype = [{'id': 0, 'name': 'highway'}]
technology = [{'id': 0, 'name': 'BEV'}]
vehicletype = [{'id': 0, 'name': 'truck'}]

# Create output directory
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
case_name = f"case_standalone_{timestamp}"
case_dir = f"input_data/{case_name}"
os.makedirs(case_dir, exist_ok=True)

print(f"\n5. Saving to YAML files in: {case_dir}")

def convert_to_native_types(obj):
    """Convert NumPy types to native Python types for YAML compatibility"""
    import numpy as np

    if isinstance(obj, dict):
        return {k: convert_to_native_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_native_types(item) for item in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj

# Save all components
components = {
    "Odpair": odpair_list,
    "Path": path_list,
    "InitialVehicleStock": initial_vehicle_stock,
    "MandatoryBreaks": mandatory_breaks_list,
    "SpatialFlexibilityEdges": spatial_flex_range_list,
    "GeographicElement": geographic_elements,
    "FinancialStatus": financial_status,
    "Fuel": fuel,
    "Mode": mode,
    "Product": product,
    "Regiontype": regiontype,
    "Technology": technology,
    "Vehicletype": vehicletype,
}

for name, data in components.items():
    filepath = os.path.join(case_dir, f"{name}.yaml")
    # Convert to native types before dumping
    clean_data = convert_to_native_types(data)
    with open(filepath, 'w') as f:
        yaml.dump(clean_data, f, default_flow_style=False, sort_keys=False)
    file_size = os.path.getsize(filepath)
    print(f"   [OK] {name}.yaml ({file_size:,} bytes)")

print("\n" + "="*80)
print("SUCCESS!")
print("="*80)
print(f"\nCase folder: {case_dir}")
print(f"\nTo use this data:")
print(f'1. Update SM.jl line 11 to: folder = "{case_name}"')
print(f'2. Run julia SM.jl')

# Verify key files are not empty
print("\nVerifying critical files are not empty:")
for name in ["Odpair", "Path", "InitialVehicleStock"]:
    filepath = os.path.join(case_dir, f"{name}.yaml")
    size = os.path.getsize(filepath)
    status = "[OK]" if size > 100 else "[EMPTY]"
    print(f"   {name}.yaml: {size:,} bytes - {status}")
