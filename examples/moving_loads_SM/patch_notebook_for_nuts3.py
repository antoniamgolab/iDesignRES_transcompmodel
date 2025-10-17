"""
Automatically patch SM-preprocessing.ipynb to work with NUTS-3 data

This script:
1. Backs up your original notebook
2. Inserts the NUTS-3 preprocessing fix at the right locations
3. Preserves all other cells and parameters
"""
import json
import shutil
from datetime import datetime

NOTEBOOK_PATH = "SM-preprocessing.ipynb"
BACKUP_PATH = f"SM-preprocessing_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ipynb"

print("="*80)
print("PATCHING SM-PREPROCESSING.IPYNB FOR NUTS-3 DATA")
print("="*80)

# Step 1: Backup
print(f"\n1. Creating backup: {BACKUP_PATH}")
shutil.copy(NOTEBOOK_PATH, BACKUP_PATH)
print("   [OK] Backup created")

# Step 2: Load notebook
print(f"\n2. Loading {NOTEBOOK_PATH}")
with open(NOTEBOOK_PATH, 'r', encoding='utf-8') as f:
    nb = json.load(f)
print(f"   [OK] Loaded {len(nb['cells'])} cells")

# Step 3: Find cells to replace
print("\n3. Analyzing notebook structure...")

# Find import cell (usually near the top)
import_cell_idx = None
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell.get('source', []))
        if 'import pandas' in source or 'import numpy' in source:
            import_cell_idx = i + 1  # Insert after imports
            break

# Find OD-pair creation cell
odpair_cell_idx = None
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell.get('source', []))
        if 'odpair_list = []' in source or 'from pyproj import Geod' in source:
            odpair_cell_idx = i
            print(f"   Found OD-pair creation cell: {i}")
            break

# Find spatial flexibility cell
spatial_flex_cell_idx = None
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell.get('source', []))
        if 'spatial_flex_range_list = []' in source and 'combinations' in source:
            spatial_flex_cell_idx = i
            print(f"   Found spatial flexibility cell: {i}")
            break

# Find mandatory breaks cell
mandatory_breaks_cell_idx = None
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell.get('source', []))
        if 'mandatory_breaks_list' in source and ('calculate' in source.lower() or 'create' in source.lower()):
            mandatory_breaks_cell_idx = i
            print(f"   Found mandatory breaks cell: {i}")
            break

# Step 4: Create replacement cells
print("\n4. Creating NUTS-3 replacement cells...")

# Import cell
import_fix_cell = {
    'cell_type': 'code',
    'execution_count': None,
    'metadata': {},
    'outputs': [],
    'source': [
        '# ============================================================================\n',
        '# NUTS-3 PREPROCESSING FIX\n',
        '# ============================================================================\n',
        'import sys\n',
        'sys.path.append(\'.\')\n',
        'from preprocessing_fix_for_nuts3 import (\n',
        '    create_nuts3_paths_from_traffic,\n',
        '    create_simplified_spatial_flexibility\n',
        ')\n',
        'print("Loaded NUTS-3 preprocessing functions")'
    ]
}

# OD-pair replacement cell
odpair_fix_cell = {
    'cell_type': 'code',
    'execution_count': None,
    'metadata': {},
    'outputs': [],
    'source': [
        '# ============================================================================\n',
        '# CREATE OD-PAIRS AND PATHS FOR NUTS-3 DATA\n',
        '# ============================================================================\n',
        'print("="*80)\n',
        'print("CREATING NUTS-3 OD-PAIRS AND PATHS")\n',
        'print("="*80)\n',
        '\n',
        '# ADJUSTABLE PARAMETERS\n',
        'MAX_ODPAIRS = 100  # Change this to None for full dataset\n',
        '\n',
        '# Auto-detect traffic variable\n',
        'traffic_var = None\n',
        'for var_name in [\'long_haul_truck_traffic\', \'filtered_truck_traffic\', \'truck_traffic\']:\n',
        '    if var_name in dir():\n',
        '        traffic_var = eval(var_name)\n',
        '        print(f"Using traffic data: {var_name} ({len(traffic_var):,} rows)")\n',
        '        break\n',
        '\n',
        '# Auto-detect nodes variable\n',
        'nodes_var = None\n',
        'for var_name in [\'filtered_network_nodes\', \'network_nodes\']:\n',
        '    if var_name in dir():\n',
        '        nodes_var = eval(var_name)\n',
        '        print(f"Using network nodes: {var_name} ({len(nodes_var):,} nodes)")\n',
        '        break\n',
        '\n',
        '# Auto-detect edges variable\n',
        'edges_var = None\n',
        'for var_name in [\'filtered_network_edges\', \'network_edges\']:\n',
        '    if var_name in dir():\n',
        '        edges_var = eval(var_name)\n',
        '        print(f"Using network edges: {var_name} ({len(edges_var):,} edges)")\n',
        '        break\n',
        '\n',
        '# Create OD-pairs and paths\n',
        'if MAX_ODPAIRS:\n',
        '    print(f"\\n[TEST MODE] Limiting to {MAX_ODPAIRS} OD-pairs")\n',
        'else:\n',
        '    print(f"\\n[FULL MODE] Processing ALL OD-pairs")\n',
        '\n',
        'odpair_list, path_list = create_nuts3_paths_from_traffic(\n',
        '    truck_traffic=traffic_var,\n',
        '    network_nodes=nodes_var,\n',
        '    network_edges=edges_var,\n',
        '    max_odpairs=MAX_ODPAIRS\n',
        ')\n',
        '\n',
        'print(f"\\n[OK] Created {len(odpair_list)} OD-pairs")\n',
        'print(f"[OK] Created {len(path_list)} paths")\n',
        '\n',
        '# Create initial vehicle stock\n',
        'initial_vehicle_stock = []\n',
        'for i, odp in enumerate(odpair_list):\n',
        '    initial_vehicle_stock.extend(odp[\'vehicle_stock_init\'])\n',
        '\n',
        'print(f"[OK] Created {len(initial_vehicle_stock)} vehicle stock entries")'
    ]
}

# Spatial flexibility replacement cell
spatial_flex_fix_cell = {
    'cell_type': 'code',
    'execution_count': None,
    'metadata': {},
    'outputs': [],
    'source': [
        '# ============================================================================\n',
        '# CREATE SPATIAL FLEXIBILITY FOR NUTS-3 DATA\n',
        '# ============================================================================\n',
        'print("="*80)\n',
        'print("CREATING SPATIAL FLEXIBILITY")\n',
        'print("="*80)\n',
        '\n',
        '# ADJUSTABLE PARAMETER\n',
        'MAX_FLEXIBILITY = 5  # Adjust this to change spatial flexibility range\n',
        '\n',
        'spatial_flex_range_list = create_simplified_spatial_flexibility(\n',
        '    path_list=path_list,\n',
        '    max_flexibility=MAX_FLEXIBILITY\n',
        ')\n',
        '\n',
        'print(f"[OK] Created {len(spatial_flex_range_list)} spatial flexibility entries")'
    ]
}

# Mandatory breaks replacement cell
mandatory_breaks_fix_cell = {
    'cell_type': 'code',
    'execution_count': None,
    'metadata': {},
    'outputs': [],
    'source': [
        '# ============================================================================\n',
        '# MANDATORY BREAKS (SIMPLIFIED FOR NUTS-3)\n',
        '# ============================================================================\n',
        'print("="*80)\n',
        'print("HANDLING MANDATORY BREAKS")\n',
        'print("="*80)\n',
        '\n',
        '# For NUTS-3 aggregated network, skip mandatory breaks\n',
        'mandatory_breaks_list = []\n',
        'print("[OK] Skipping mandatory breaks for NUTS-3 simplified network")\n',
        '\n',
        '# Uncomment to try calculating:\n',
        '# try:\n',
        '#     from mandatory_breaks_calculation import create_mandatory_breaks_list\n',
        '#     mandatory_breaks_list = create_mandatory_breaks_list(path_list, speed=80)\n',
        '#     print(f"[OK] Created {len(mandatory_breaks_list)} entries")\n',
        '# except Exception as e:\n',
        '#     print(f"[WARNING] Mandatory breaks failed: {e}")\n',
        '#     mandatory_breaks_list = []'
    ]
}

# Step 5: Apply patches
print("\n5. Applying patches...")
new_cells = []

for i, cell in enumerate(nb['cells']):
    # Add import fix after imports
    if i == import_cell_idx and import_cell_idx is not None:
        new_cells.append(cell)
        new_cells.append(import_fix_cell)
        print(f"   [OK] Inserted NUTS-3 import at cell {i+1}")
    # Replace OD-pair cell
    elif i == odpair_cell_idx and odpair_cell_idx is not None:
        new_cells.append(odpair_fix_cell)
        print(f"   [OK] Replaced OD-pair creation cell {i}")
    # Replace spatial flexibility cell
    elif i == spatial_flex_cell_idx and spatial_flex_cell_idx is not None:
        new_cells.append(spatial_flex_fix_cell)
        print(f"   [OK] Replaced spatial flexibility cell {i}")
    # Replace mandatory breaks cell
    elif i == mandatory_breaks_cell_idx and mandatory_breaks_cell_idx is not None:
        new_cells.append(mandatory_breaks_fix_cell)
        print(f"   [OK] Replaced mandatory breaks cell {i}")
    else:
        new_cells.append(cell)

nb['cells'] = new_cells

# Step 6: Save patched notebook
print(f"\n6. Saving patched notebook...")
with open(NOTEBOOK_PATH, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
print(f"   [OK] Saved {NOTEBOOK_PATH}")

# Step 7: Summary
print("\n" + "="*80)
print("SUCCESS!")
print("="*80)
print(f"\nPatched notebook: {NOTEBOOK_PATH}")
print(f"Backup saved to: {BACKUP_PATH}")
print("\nNext steps:")
print("1. Open SM-preprocessing.ipynb in Jupyter")
print("2. Run all cells")
print("3. Adjust MAX_ODPAIRS parameter as needed")
print("4. YAML files will be generated with NUTS-3 data")
print("\nTo revert: restore from backup file")
