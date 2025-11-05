"""
VALIDATION: Check if preprocessing fix preserved routing through Austria

This script validates that the fixes to SM_preprocessing_nuts2_complete.py successfully
preserve routes through Austrian NUTS2 regions for Germany→Italy freight.

Run AFTER preprocessing with: ~/miniconda3/envs/transcomp/python.exe SM_preprocessing_nuts2_complete.py
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import yaml
import glob
from collections import defaultdict

print("="*80)
print("VALIDATING PREPROCESSING ROUTING FIX")
print("="*80)

# ==============================================================================
# LOAD PREPROCESSED DATA
# ==============================================================================

# Find most recent case
case_dirs = glob.glob('input_data/case_*')
if not case_dirs:
    print("\nERROR: No case directories found in input_data/")
    print("Please run SM_preprocessing_nuts2_complete.py first")
    sys.exit(1)

latest_case = sorted(case_dirs)[-1]
case_name = latest_case.split('/')[-1]

print(f"\nAnalyzing case: {case_name}")

# Load data
with open(f'{latest_case}/GeographicElement.yaml', 'r', encoding='utf-8') as f:
    geo_elements = yaml.safe_load(f)

with open(f'{latest_case}/Path.yaml', 'r', encoding='utf-8') as f:
    paths = yaml.safe_load(f)

with open(f'{latest_case}/Odpair.yaml', 'r', encoding='utf-8') as f:
    odpairs = yaml.safe_load(f)

print(f"  Nodes: {len([g for g in geo_elements if g['type'] == 'node'])}")
print(f"  Edges: {len([g for g in geo_elements if g['type'] == 'edge'])}")
print(f"  Paths: {len(paths)}")
print(f"  OD-pairs: {len(odpairs)}")

# Create lookups
node_to_nuts2 = {}
node_to_country = {}
for geo in geo_elements:
    if geo['type'] == 'node' and 'nuts2_region' in geo:
        node_to_nuts2[geo['id']] = geo['nuts2_region']
        node_to_country[geo['id']] = geo.get('country', 'UNKNOWN')

od_lookup = {}
for od in odpairs:
    od_lookup[od['id']] = {
        'origin': od['from'],
        'destination': od['to']
    }

path_lookup = {}
for path in paths:
    path_lookup[path['id']] = {
        'sequence': path['sequence'],
        'length': path['length'],
        'odpair': path['odpair']
    }

# ==============================================================================
# ANALYZE GERMANY → ITALY ROUTES
# ==============================================================================

print("\n" + "="*80)
print("ANALYZING GERMANY → ITALY ROUTES")
print("="*80)

# Find paths from Germany to Italy
de_to_it_paths = []

for path in paths:
    odpair_id = path['odpair']
    if odpair_id not in od_lookup:
        continue

    od_info = od_lookup[odpair_id]
    origin_id = od_info['origin']
    dest_id = od_info['destination']

    origin_nuts2 = node_to_nuts2.get(origin_id)
    dest_nuts2 = node_to_nuts2.get(dest_id)
    origin_country = node_to_country.get(origin_id)
    dest_country = node_to_country.get(dest_id)

    if origin_country == 'DE' and dest_country == 'IT':
        # Extract countries in route
        route_countries = []
        for node_id in path['sequence']:
            country = node_to_country.get(node_id)
            if country and country not in route_countries:
                route_countries.append(country)

        de_to_it_paths.append({
            'path_id': path['id'],
            'origin_nuts2': origin_nuts2,
            'dest_nuts2': dest_nuts2,
            'sequence': path['sequence'],
            'route_countries': route_countries,
            'num_nodes': len(path['sequence']),
            'length': path['length']
        })

print(f"\nFound {len(de_to_it_paths)} Germany → Italy paths")

if len(de_to_it_paths) == 0:
    print("\nWARNING: No Germany → Italy paths found!")
    print("This may indicate:")
    print("  1. Corridor filtering excluded these routes")
    print("  2. No cross-border traffic in this case")
    print("  3. Data loading issue")
    sys.exit(0)

# ==============================================================================
# ROUTING ANALYSIS
# ==============================================================================

print("\n" + "="*80)
print("ROUTING ANALYSIS")
print("="*80)

# Categorize paths
paths_via_austria = []
paths_via_other = []
paths_direct = []

for path_info in de_to_it_paths:
    route_countries = path_info['route_countries']

    if 'AT' in route_countries:
        paths_via_austria.append(path_info)
    elif len(route_countries) > 2:  # More than just DE and IT
        paths_via_other.append(path_info)
    else:
        paths_direct.append(path_info)

print(f"\nRoute breakdown:")
print(f"  Paths via Austria: {len(paths_via_austria)} ({100*len(paths_via_austria)/len(de_to_it_paths):.1f}%)")
print(f"  Paths via other countries: {len(paths_via_other)} ({100*len(paths_via_other)/len(de_to_it_paths):.1f}%)")
print(f"  Direct paths (DE → IT only): {len(paths_direct)} ({100*len(paths_direct)/len(de_to_it_paths):.1f}%)")

# Node count statistics
node_counts = [p['num_nodes'] for p in de_to_it_paths]
avg_nodes = sum(node_counts) / len(node_counts)
two_node_paths = len([n for n in node_counts if n == 2])

print(f"\nPath structure:")
print(f"  Average nodes per path: {avg_nodes:.2f}")
print(f"  2-node paths (direct): {two_node_paths} ({100*two_node_paths/len(de_to_it_paths):.1f}%)")
print(f"  Multi-node paths (3+): {len(de_to_it_paths) - two_node_paths} ({100*(len(de_to_it_paths)-two_node_paths)/len(de_to_it_paths):.1f}%)")

# ==============================================================================
# SAMPLE ROUTES
# ==============================================================================

print("\n" + "="*80)
print("SAMPLE ROUTES")
print("="*80)

if paths_via_austria:
    print("\nTop 5 routes via AUSTRIA:")
    for i, path_info in enumerate(paths_via_austria[:5], 1):
        print(f"\n  {i}. Path {path_info['path_id']}: {path_info['origin_nuts2']} → {path_info['dest_nuts2']}")
        print(f"     Length: {path_info['length']:.1f} km")
        print(f"     Nodes: {path_info['num_nodes']}")
        print(f"     Countries: {' → '.join(path_info['route_countries'])}")

if paths_direct:
    print("\nSample DIRECT routes (no intermediate countries):")
    for i, path_info in enumerate(paths_direct[:3], 1):
        print(f"\n  {i}. Path {path_info['path_id']}: {path_info['origin_nuts2']} → {path_info['dest_nuts2']}")
        print(f"     Length: {path_info['length']:.1f} km")
        print(f"     Nodes: {path_info['num_nodes']}")
        print(f"     Countries: {' → '.join(path_info['route_countries'])}")

# ==============================================================================
# VALIDATION VERDICT
# ==============================================================================

print("\n" + "="*80)
print("VALIDATION VERDICT")
print("="*80)

print(f"""
EXPECTED OUTCOME (after fixes):
  - Most Germany→Italy paths should pass through Austria (AT3x NUTS2 regions)
  - Average nodes per path should be > 2 (not all direct)
  - Paths should have 3+ nodes showing intermediate routing

ACTUAL OUTCOME:
  - {len(paths_via_austria)} paths via Austria ({100*len(paths_via_austria)/len(de_to_it_paths):.1f}%)
  - Average nodes per path: {avg_nodes:.2f}
  - Multi-node paths: {len(de_to_it_paths) - two_node_paths} ({100*(len(de_to_it_paths)-two_node_paths)/len(de_to_it_paths):.1f}%)
  - Direct 2-node paths: {two_node_paths} ({100*two_node_paths/len(de_to_it_paths):.1f}%)

VERDICT:
""")

if len(paths_via_austria) > 0.5 * len(de_to_it_paths) and avg_nodes > 2.5:
    print("  ✅ SUCCESS - Routes now preserve intermediate routing through Austria!")
    print("     The fix worked correctly.")
elif len(paths_via_austria) > 0.2 * len(de_to_it_paths):
    print("  ⚠️  PARTIAL SUCCESS - Some routes preserve intermediate routing")
    print("     The fix partially worked, but many paths are still direct.")
elif avg_nodes > 2.5:
    print("  ⚠️  PARTIAL - Multi-node paths exist but don't pass through Austria")
    print("     Paths may be routed through other countries or BFS depth limit hit.")
else:
    print("  ❌ FAIL - Routes are still mostly direct 2-node paths")
    print("     The fix did not work. Possible reasons:")
    print("       - edge_lookup is still empty (intra-regional edges not added)")
    print("       - BFS depth limit (max_depth=5) is too restrictive")
    print("       - Corridor filtering excluded all multi-hop paths")

print("\n" + "="*80)
