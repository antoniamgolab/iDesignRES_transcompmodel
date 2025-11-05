"""
TRACE: How does the preprocessing create the DEA1 → ITC4 path?

This script recreates the path generation logic to understand why
direct routes like DEA1 → ITC4 are created without intermediate nodes.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import yaml
from collections import deque

# ==============================================================================
# LOAD PREPROCESSED DATA
# ==============================================================================

case_study_name = 'case_20251103_114421'
input_dir = f'input_data/{case_study_name}'

print("="*80)
print("TRACING PATH GENERATION: DEA1 → ITC4")
print("="*80)

# Load geographic elements (nodes and edges)
with open(f'{input_dir}/GeographicElement.yaml', 'r', encoding='utf-8') as f:
    geo_elements = yaml.safe_load(f)

# Load paths
with open(f'{input_dir}/Path.yaml', 'r', encoding='utf-8') as f:
    paths = yaml.safe_load(f)

# Load OD-pairs
with open(f'{input_dir}/Odpair.yaml', 'r', encoding='utf-8') as f:
    odpairs = yaml.safe_load(f)

# ==============================================================================
# BUILD NODE AND EDGE LOOKUPS
# ==============================================================================

nodes = {}
edges = {}
nuts2_lookup = {}

for geo in geo_elements:
    if geo['type'] == 'node':
        nodes[geo['id']] = geo
        if 'nuts2_region' in geo and geo['nuts2_region']:
            nuts2_lookup[geo['nuts2_region']] = geo['id']

    elif geo['type'] == 'edge':
        edges[geo['id']] = geo

print(f"\nLoaded:")
print(f"  • {len(nodes)} nodes")
print(f"  • {len(edges)} edges")
print(f"  • {len(nuts2_lookup)} NUTS2 regions")

# ==============================================================================
# BUILD ADJACENCY GRAPH
# ==============================================================================

print("\nBuilding adjacency graph from edges...")

adjacency = {}
edge_lookup = {}

for edge_id, edge in edges.items():
    node_a = edge['node_a']
    node_b = edge['node_b']
    distance = edge.get('length', 0)

    # Add to adjacency (bidirectional)
    if node_a not in adjacency:
        adjacency[node_a] = []
    adjacency[node_a].append(node_b)

    if node_b not in adjacency:
        adjacency[node_b] = []
    adjacency[node_b].append(node_a)

    # Add to edge lookup
    edge_lookup[(node_a, node_b)] = distance
    edge_lookup[(node_b, node_a)] = distance

print(f"  • Built adjacency for {len(adjacency)} nodes")
print(f"  • Total edges (bidirectional): {len(edge_lookup)}")

# ==============================================================================
# FIND DEA1 AND ITC4 NODES
# ==============================================================================

dea1_node = nuts2_lookup.get('DEA1')
itc4_node = nuts2_lookup.get('ITC4')

print(f"\nTarget nodes:")
print(f"  • DEA1 node ID: {dea1_node}")
print(f"  • ITC4 node ID: {itc4_node}")

if dea1_node is None or itc4_node is None:
    print("ERROR: Could not find DEA1 or ITC4 nodes!")
    sys.exit(1)

# ==============================================================================
# SIMULATE BFS PATH FINDING (AS IN PREPROCESSING)
# ==============================================================================

def find_path_bfs(origin, dest, adjacency, max_depth=5):
    """Simulate the _find_nuts2_path function from preprocessing."""
    if origin == dest:
        return [origin]

    # BFS
    queue = deque([(origin, [origin])])
    visited = {origin}

    paths_explored = 0
    max_path_length = 0

    while queue:
        node, path = queue.popleft()
        paths_explored += 1

        if len(path) > max_depth:
            continue

        max_path_length = max(max_path_length, len(path))

        if node == dest:
            return path, paths_explored, max_path_length

        for neighbor in adjacency.get(node, []):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))

    # No path found - return direct connection (THIS IS THE ISSUE!)
    return [origin, dest], paths_explored, max_path_length

print("\n" + "="*80)
print("RUNNING BFS WITH max_depth=5 (as in preprocessing)")
print("="*80)

result = find_path_bfs(dea1_node, itc4_node, adjacency, max_depth=5)

if len(result) == 3:
    path, paths_explored, max_path_length = result
    print(f"\n✓ Path found with {len(path)} nodes:")
    for i, node_id in enumerate(path):
        node_info = nodes[node_id]
        nuts2 = node_info.get('nuts2_region', 'UNKNOWN')
        country = node_info.get('country', 'UNKNOWN')
        marker = "  → " if i > 0 else "    "
        print(f"{marker}Node {node_id}: {nuts2} ({country})")

    print(f"\n  BFS explored {paths_explored} paths")
    print(f"  Maximum path length reached: {max_path_length}")
else:
    path = result
    print(f"\n✗ No path found within max_depth=5")
    print(f"  Fallback: Direct connection with {len(path)} nodes")

# ==============================================================================
# TRY WITH INCREASED max_depth
# ==============================================================================

print("\n" + "="*80)
print("TRYING WITH max_depth=10")
print("="*80)

result_10 = find_path_bfs(dea1_node, itc4_node, adjacency, max_depth=10)

if len(result_10) == 3:
    path_10, paths_explored_10, max_path_length_10 = result_10
    print(f"\n✓ Path found with {len(path_10)} nodes:")
    for i, node_id in enumerate(path_10):
        node_info = nodes[node_id]
        nuts2 = node_info.get('nuts2_region', 'UNKNOWN')
        country = node_info.get('country', 'UNKNOWN')
        marker = "  → " if i > 0 else "    "
        print(f"{marker}Node {node_id}: {nuts2} ({country})")

    print(f"\n  BFS explored {paths_explored_10} paths")
    print(f"  Maximum path length reached: {max_path_length_10}")
else:
    path_10 = result_10
    print(f"\n✗ Still no path found within max_depth=10")
    print(f"  Fallback: Direct connection with {len(path_10)} nodes")

# ==============================================================================
# CHECK IF DIRECT EDGE EXISTS
# ==============================================================================

print("\n" + "="*80)
print("CHECKING NETWORK TOPOLOGY")
print("="*80)

direct_edge_exists = (dea1_node, itc4_node) in edge_lookup
print(f"\nDirect edge DEA1 → ITC4 exists: {direct_edge_exists}")

if direct_edge_exists:
    print(f"  Distance: {edge_lookup[(dea1_node, itc4_node)]:.1f} km")

# Check connectivity
dea1_neighbors = adjacency.get(dea1_node, [])
itc4_neighbors = adjacency.get(itc4_node, [])

print(f"\nDEA1 neighbors: {len(dea1_neighbors)} nodes")
for neighbor in dea1_neighbors[:5]:
    neighbor_nuts2 = nodes[neighbor].get('nuts2_region', 'UNKNOWN')
    neighbor_country = nodes[neighbor].get('country', 'UNKNOWN')
    print(f"  • Node {neighbor}: {neighbor_nuts2} ({neighbor_country})")
if len(dea1_neighbors) > 5:
    print(f"  ... and {len(dea1_neighbors) - 5} more")

print(f"\nITC4 neighbors: {len(itc4_neighbors)} nodes")
for neighbor in itc4_neighbors[:5]:
    neighbor_nuts2 = nodes[neighbor].get('nuts2_region', 'UNKNOWN')
    neighbor_country = nodes[neighbor].get('country', 'UNKNOWN')
    print(f"  • Node {neighbor}: {neighbor_nuts2} ({neighbor_country})")
if len(itc4_neighbors) > 5:
    print(f"  ... and {len(itc4_neighbors) - 5} more")

# ==============================================================================
# CHECK EXISTING PATH IN INPUT DATA
# ==============================================================================

print("\n" + "="*80)
print("CHECKING ACTUAL PATH IN INPUT DATA")
print("="*80)

# Find OD-pair DEA1 → ITC4
dea1_to_itc4_odpairs = []

for odpair in odpairs:
    origin_id = odpair['from']
    dest_id = odpair['to']

    origin_nuts2 = nodes.get(origin_id, {}).get('nuts2_region')
    dest_nuts2 = nodes.get(dest_id, {}).get('nuts2_region')

    if origin_nuts2 == 'DEA1' and dest_nuts2 == 'ITC4':
        dea1_to_itc4_odpairs.append(odpair)

print(f"\nFound {len(dea1_to_itc4_odpairs)} OD-pairs from DEA1 to ITC4")

if dea1_to_itc4_odpairs:
    # Show first OD-pair
    odpair = dea1_to_itc4_odpairs[0]
    print(f"\nExample OD-pair:")
    print(f"  • OD-pair ID: {odpair['id']}")
    print(f"  • From node: {odpair['from']} (DEA1)")
    print(f"  • To node: {odpair['to']} (ITC4)")

    # Find associated paths
    odpair_paths = [p for p in paths if p['odpair'] == odpair['id']]

    print(f"\n  Associated paths: {len(odpair_paths)}")

    if odpair_paths:
        path = odpair_paths[0]
        print(f"\n  Path ID {path['id']}:")
        print(f"    • Length: {path['length']:.1f} km")
        print(f"    • Sequence ({len(path['sequence'])} nodes):")

        for i, node_id in enumerate(path['sequence']):
            node_nuts2 = nodes.get(node_id, {}).get('nuts2_region', 'UNKNOWN')
            node_country = nodes.get(node_id, {}).get('country', 'UNKNOWN')
            segment_dist = path['distance_from_previous'][i]
            marker = "  → " if i > 0 else "    "
            print(f"    {marker}Node {node_id}: {node_nuts2} ({node_country}) [{segment_dist:.1f} km]")

# ==============================================================================
# CONCLUSION
# ==============================================================================

print("\n" + "="*80)
print("CONCLUSION")
print("="*80)

if len(path) == 2:
    print("""
❌ ROOT CAUSE IDENTIFIED:

The BFS path finding in SM_preprocessing_nuts2_complete.py:742-773
uses max_depth=5, which means it will only explore paths up to 5 nodes long.

If no path is found within this depth limit (or if nodes are not connected
in the network graph), it falls back to creating a DIRECT 2-NODE PATH:

    return [origin, dest]  # Line 773

This is why we see routes like DEA1 → ITC4 without intermediate Austrian
nodes - the BFS either:
  1. Cannot find a path within 5 hops, OR
  2. The nodes are not connected in the NUTS-2 aggregated network

The distance on this direct edge is then distributed using the ORIGINAL
traffic distance from the ETISplus data, which IS accurate (it includes
the real-world distance through Austria/Switzerland).

IMPACT:
  • Freight TKM is correctly calculated (accurate distances)
  • BUT intermediate Austrian nodes don't appear in the route
  • This explains why Austria shows lower TKM than Northern Italy
  • The "route" is a simplified network path, not a geographic route
""")
else:
    print(f"""
✓ Path found with {len(path)} nodes.

This suggests that BFS successfully found a route through the network.
Check if this path includes Austrian nodes as expected.
""")
