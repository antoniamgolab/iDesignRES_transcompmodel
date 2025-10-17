"""
Create a single-flow SM-preprocessing.ipynb that automatically handles both:
- resolution = "original" → Uses original preprocessing
- resolution = "reduced" → Uses NUTS-3 preprocessing fix

This makes the notebook work seamlessly for both cases.
"""
import json
import shutil
from datetime import datetime

NOTEBOOK_PATH = "SM-preprocessing.ipynb"
BACKUP_PATH = f"SM-preprocessing_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ipynb"

print("="*80)
print("MAKING SM-PREPROCESSING.IPYNB AUTO-DETECT NUTS-3")
print("="*80)

# Backup
print(f"\n1. Creating backup: {BACKUP_PATH}")
shutil.copy(NOTEBOOK_PATH, BACKUP_PATH)
print("   [OK]")

# Load notebook
print(f"\n2. Loading notebook...")
with open(NOTEBOOK_PATH, 'r', encoding='utf-8') as f:
    nb = json.load(f)
print(f"   [OK] {len(nb['cells'])} cells")

# Find resolution cell
resolution_cell_idx = None
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell.get('source', []))
        if 'resolution = "original"' in source or 'resolution = "reduced"' in source:
            resolution_cell_idx = i
            print(f"\n3. Found resolution cell: {i}")
            break

# Find OD-pair creation cell
odpair_cell_idx = None
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell.get('source', []))
        if ('odpair_list = []' in source or 'from pyproj import Geod' in source) and 'for' in source:
            odpair_cell_idx = i
            print(f"   Found OD-pair creation cell: {i}")
            break

# Find spatial flexibility cell
spatial_cell_idx = None
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell.get('source', []))
        if 'spatial_flex_range_list = []' in source and 'combinations' in source:
            spatial_cell_idx = i
            print(f"   Found spatial flexibility cell: {i}")
            break

# Find mandatory breaks cell
breaks_cell_idx = None
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell.get('source', []))
        if 'mandatory_breaks_list' in source and len(source) > 100:
            breaks_cell_idx = i
            print(f"   Found mandatory breaks cell: {i}")
            break

print("\n4. Creating auto-detect cells...")

# Create import cell (insert after resolution cell)
import_cell = {
    'cell_type': 'code',
    'execution_count': None,
    'metadata': {},
    'outputs': [],
    'source': [
        '# Import NUTS-3 fix (only used if resolution="reduced")\n',
        'import sys\n',
        'sys.path.append(\'.\')\n',
        'from preprocessing_fix_for_nuts3 import (\n',
        '    create_nuts3_paths_from_traffic,\n',
        '    create_simplified_spatial_flexibility\n',
        ')\n',
        'print(f"Resolution: {resolution}")\n',
        'print(f"Data folder: {folder}")'
    ]
}

# Create smart OD-pair cell
smart_odpair_cell = {
    'cell_type': 'code',
    'execution_count': None,
    'metadata': {},
    'outputs': [],
    'source': [
        '# ============================================================================\n',
        '# OD-PAIR AND PATH CREATION (AUTO-DETECTS RESOLUTION)\n',
        '# ============================================================================\n',
        'if resolution == "reduced":\n',
        '    print("="*80)\n',
        '    print("USING NUTS-3 PREPROCESSING")\n',
        '    print("="*80)\n',
        '    \n',
        '    # ADJUSTABLE PARAMETERS\n',
        '    MAX_ODPAIRS = None  # Change to number (e.g., 100) for testing\n',
        '    \n',
        '    # Auto-detect variables\n',
        '    traffic_var = long_haul_truck_traffic if "long_haul_truck_traffic" in dir() else filtered_truck_traffic if "filtered_truck_traffic" in dir() else truck_traffic\n',
        '    nodes_var = filtered_network_nodes if "filtered_network_nodes" in dir() else network_nodes\n',
        '    edges_var = filtered_network_edges if "filtered_network_edges" in dir() else network_edges\n',
        '    \n',
        '    print(f"Using: {len(traffic_var):,} traffic rows, {len(nodes_var):,} nodes, {len(edges_var):,} edges")\n',
        '    if MAX_ODPAIRS:\n',
        '        print(f"[TEST MODE] Limiting to {MAX_ODPAIRS} OD-pairs")\n',
        '    \n',
        '    # Create with NUTS-3 fix\n',
        '    odpair_list, path_list = create_nuts3_paths_from_traffic(\n',
        '        truck_traffic=traffic_var,\n',
        '        network_nodes=nodes_var,\n',
        '        network_edges=edges_var,\n',
        '        max_odpairs=MAX_ODPAIRS\n',
        '    )\n',
        '    \n',
        '    print(f"[OK] Created {len(odpair_list)} OD-pairs and {len(path_list)} paths")\n',
        '    \n',
        '    # Create vehicle stock\n',
        '    initial_vehicle_stock = []\n',
        '    for odp in odpair_list:\n',
        '        initial_vehicle_stock.extend(odp["vehicle_stock_init"])\n',
        '    print(f"[OK] Created {len(initial_vehicle_stock)} vehicle stock entries")\n',
        '    \n',
        'else:\n',
        '    print("="*80)\n',
        '    print("USING ORIGINAL HIGH-RESOLUTION PREPROCESSING")\n',
        '    print("="*80)\n',
        '    \n',
        '    # Original preprocessing code\n',
        '    from pyproj import Geod\n',
        '    initial_vehicle_stock = []\n',
        '    init_veh_stock_id = 0\n',
        '    odpair_list = []\n',
        '    path_list = []\n',
        '    odpair_id = 0\n',
        '    path_id = 0\n',
        '    total_rows = len(long_haul_truck_traffic)\n',
        '    \n',
        '    # Progress tracking\n',
        '    import time\n',
        '    start_time = time.time()\n',
        '    last_report = 0\n',
        '    \n',
        '    for index, row in long_haul_truck_traffic.iterrows():\n',
        '        # Progress reporting every 10%\n',
        '        progress = (index + 1) / total_rows\n',
        '        if progress - last_report >= 0.1:\n',
        '            elapsed = time.time() - start_time\n',
        '            print(f"Progress: {progress*100:.0f}% ({index+1}/{total_rows}) - {elapsed:.1f}s")\n',
        '            last_report = progress\n',
        '        \n',
        '        edge_path = row["Edge_path_E_road"]\n',
        '        if not edge_path or len(edge_path) == 0:\n',
        '            continue\n',
        '        \n',
        '        # Convert edge path to node sequence\n',
        '        node_sequence = []\n',
        '        for edge_id in edge_path:\n',
        '            edge = filtered_network_edges[filtered_network_edges["Edge_ID"] == edge_id]\n',
        '            if not edge.empty:\n',
        '                node_a = int(edge["Network_Node_A_ID"].iloc[0])\n',
        '                node_b = int(edge["Network_Node_B_ID"].iloc[0])\n',
        '                if not node_sequence or node_sequence[-1] != node_a:\n',
        '                    node_sequence.append(node_a)\n',
        '                node_sequence.append(node_b)\n',
        '        \n',
        '        if len(node_sequence) < 2:\n',
        '            continue\n',
        '        \n',
        '        # Calculate distances\n',
        '        distances_from_prev = [0]\n',
        '        cumulative_dist = [0]\n',
        '        total_dist = 0\n',
        '        \n',
        '        for i in range(1, len(node_sequence)):\n',
        '            prev_node = node_sequence[i-1]\n',
        '            curr_node = node_sequence[i]\n',
        '            \n',
        '            edge = filtered_network_edges[\n',
        '                ((filtered_network_edges["Network_Node_A_ID"] == prev_node) & \n',
        '                 (filtered_network_edges["Network_Node_B_ID"] == curr_node)) |\n',
        '                ((filtered_network_edges["Network_Node_A_ID"] == curr_node) & \n',
        '                 (filtered_network_edges["Network_Node_B_ID"] == prev_node))\n',
        '            ]\n',
        '            \n',
        '            if not edge.empty:\n',
        '                dist = edge["Distance"].iloc[0]\n',
        '                distances_from_prev.append(dist)\n',
        '                total_dist += dist\n',
        '                cumulative_dist.append(total_dist)\n',
        '            else:\n',
        '                distances_from_prev.append(0)\n',
        '                cumulative_dist.append(total_dist)\n',
        '        \n',
        '        # Create path\n',
        '        path = {\n',
        '            "id": path_id,\n',
        '            "origin": node_sequence[0],\n',
        '            "destination": node_sequence[-1],\n',
        '            "length": total_dist,\n',
        '            "sequence": node_sequence,\n',
        '            "distance_from_previous": distances_from_prev,\n',
        '            "cumulative_distance": cumulative_dist\n',
        '        }\n',
        '        path_list.append(path)\n',
        '        \n',
        '        # Create OD-pair\n',
        '        F_values = [row["Traffic_flow_trucks_2030"]] * 21  # 21 years\n',
        '        vehicle_stock_init = list(range(init_veh_stock_id, init_veh_stock_id + 21))\n',
        '        init_veh_stock_id += 21\n',
        '        \n',
        '        odpair = {\n',
        '            "id": odpair_id,\n',
        '            "path_id": path_id,\n',
        '            "from": node_sequence[0],\n',
        '            "to": node_sequence[-1],\n',
        '            "product": "freight",\n',
        '            "purpose": "long-haul",\n',
        '            "region_type": "highway",\n',
        '            "financial_status": "any",\n',
        '            "F": F_values,\n',
        '            "vehicle_stock_init": vehicle_stock_init,\n',
        '            "travel_time_budget": 0.0\n',
        '        }\n',
        '        odpair_list.append(odpair)\n',
        '        \n',
        '        for veh_id in vehicle_stock_init:\n',
        '            initial_vehicle_stock.append({\n',
        '                "id": veh_id,\n',
        '                "odpair_id": odpair_id,\n',
        '                "vehicle_type": "truck",\n',
        '                "technology": "BEV"\n',
        '            })\n',
        '        \n',
        '        odpair_id += 1\n',
        '        path_id += 1\n',
        '    \n',
        '    print(f"[OK] Created {len(odpair_list)} OD-pairs and {len(path_list)} paths")\n',
        '    print(f"[OK] Created {len(initial_vehicle_stock)} vehicle stock entries")'
    ]
}

# Smart spatial flexibility cell
smart_spatial_cell = {
    'cell_type': 'code',
    'execution_count': None,
    'metadata': {},
    'outputs': [],
    'source': [
        '# ============================================================================\n',
        '# SPATIAL FLEXIBILITY (AUTO-DETECTS RESOLUTION)\n',
        '# ============================================================================\n',
        'if resolution == "reduced":\n',
        '    MAX_FLEXIBILITY = 5\n',
        '    spatial_flex_range_list = create_simplified_spatial_flexibility(\n',
        '        path_list=path_list,\n',
        '        max_flexibility=MAX_FLEXIBILITY\n',
        '    )\n',
        '    print(f"[OK] Created {len(spatial_flex_range_list)} spatial flexibility entries (NUTS-3)")\n',
        '    \n',
        'else:\n',
        '    # Original spatial flexibility code\n',
        '    from itertools import combinations\n',
        '    spatial_flex_range_list = []\n',
        '    spatial_flex_id = 0\n',
        '    \n',
        '    for path in path_list:\n',
        '        sequence = path["sequence"]\n',
        '        for i in range(len(sequence)):\n',
        '            for j in range(i, min(i + 6, len(sequence))):\n',
        '                spatial_flex_range_list.append({\n',
        '                    "id": spatial_flex_id,\n',
        '                    "odpair_id": path["id"],\n',
        '                    "path_id": path["id"],\n',
        '                    "from_id": sequence[i],\n',
        '                    "to_id": sequence[j],\n',
        '                    "flexibility_score": 1.0\n',
        '                })\n',
        '                spatial_flex_id += 1\n',
        '    \n',
        '    print(f"[OK] Created {len(spatial_flex_range_list)} spatial flexibility entries (Original)")'
    ]
}

# Smart mandatory breaks cell
smart_breaks_cell = {
    'cell_type': 'code',
    'execution_count': None,
    'metadata': {},
    'outputs': [],
    'source': [
        '# ============================================================================\n',
        '# MANDATORY BREAKS (AUTO-DETECTS RESOLUTION)\n',
        '# ============================================================================\n',
        'if resolution == "reduced":\n',
        '    mandatory_breaks_list = []\n',
        '    print("[OK] Skipping mandatory breaks for NUTS-3")\n',
        '    \n',
        'else:\n',
        '    # Original mandatory breaks calculation\n',
        '    try:\n',
        '        from mandatory_breaks_calculation import create_mandatory_breaks_list\n',
        '        mandatory_breaks_list = create_mandatory_breaks_list(path_list, speed=80)\n',
        '        print(f"[OK] Created {len(mandatory_breaks_list)} mandatory break entries")\n',
        '    except Exception as e:\n',
        '        print(f"[WARNING] Mandatory breaks failed: {e}")\n',
        '        mandatory_breaks_list = []'
    ]
}

# Apply patches
print("\n5. Applying auto-detect patches...")
new_cells = []

for i, cell in enumerate(nb['cells']):
    if i == resolution_cell_idx + 1:
        # Insert import after resolution cell
        new_cells.append(cell)
        new_cells.append(import_cell)
        print(f"   [OK] Inserted import at {i+1}")
    elif i == odpair_cell_idx:
        # Replace OD-pair cell
        new_cells.append(smart_odpair_cell)
        print(f"   [OK] Replaced OD-pair cell {i}")
    elif i == spatial_cell_idx:
        # Replace spatial cell
        new_cells.append(smart_spatial_cell)
        print(f"   [OK] Replaced spatial flexibility cell {i}")
    elif i == breaks_cell_idx:
        # Replace breaks cell
        new_cells.append(smart_breaks_cell)
        print(f"   [OK] Replaced mandatory breaks cell {i}")
    else:
        new_cells.append(cell)

nb['cells'] = new_cells

# Save
print("\n6. Saving...")
with open(NOTEBOOK_PATH, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("\n" + "="*80)
print("SUCCESS!")
print("="*80)
print(f"\nNotebook is now auto-detecting!")
print(f"Backup: {BACKUP_PATH}")
print("\nUsage:")
print('  - Set resolution = "reduced"  → NUTS-3 (1,675 nodes)')
print('  - Set resolution = "original" → Full resolution (17,435 nodes)')
print("\nJust run all cells - it will automatically use the right preprocessing!")
