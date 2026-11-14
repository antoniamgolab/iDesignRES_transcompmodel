"""
Validate Network Topology - Check if DE->IT routes can physically pass through Austria

This script checks if the NUTS-2 network topology allows valid routing from
Germany to Italy through Austria, or if there are impossible direct connections.
"""
import yaml
from pathlib import Path
from collections import deque


def load_geographic_elements(case_dir):
    """Load GeographicElement.yaml from a case directory"""
    geo_file = Path(case_dir) / "GeographicElement.yaml"

    with open(geo_file, 'r', encoding='utf-8') as f:
        geo_elements = yaml.safe_load(f)

    return geo_elements


def analyze_network_topology(geo_elements):
    """Analyze network connectivity between DE, AT, IT"""

    print("="*80)
    print("NETWORK TOPOLOGY VALIDATION")
    print("="*80)

    # Separate nodes and edges
    nodes = [g for g in geo_elements if g['type'] == 'node']
    edges = [g for g in geo_elements if g['type'] == 'edge']

    print(f"\nTotal nodes: {len(nodes)}")
    print(f"Total edges: {len(edges)}")

    # Group nodes by country
    nodes_by_country = {}
    node_to_country = {}

    for node in nodes:
        country = node.get('country', 'XX')
        node_id = node['id']

        if country not in nodes_by_country:
            nodes_by_country[country] = []
        nodes_by_country[country].append(node_id)
        node_to_country[node_id] = country

    print(f"\nNodes by country:")
    for country in sorted(nodes_by_country.keys()):
        print(f"  {country}: {len(nodes_by_country[country])} nodes")

    # Build adjacency list
    adjacency = {}
    for edge in edges:
        from_node = edge.get('from_node')
        to_node = edge.get('to_node')

        if from_node is not None and to_node is not None:
            # Bidirectional edges
            if from_node not in adjacency:
                adjacency[from_node] = []
            if to_node not in adjacency:
                adjacency[to_node] = []

            adjacency[from_node].append(to_node)
            adjacency[to_node].append(from_node)

    print(f"\nAdjacency list built: {len(adjacency)} nodes with edges")

    # Check for direct DE-IT edges (should not exist!)
    print("\n" + "="*80)
    print("CHECKING FOR IMPOSSIBLE DIRECT CONNECTIONS:")
    print("="*80)

    direct_de_it_edges = []
    for edge in edges:
        from_node = edge.get('from_node')
        to_node = edge.get('to_node')

        from_country = node_to_country.get(from_node)
        to_country = node_to_country.get(to_node)

        if (from_country == 'DE' and to_country == 'IT') or (from_country == 'IT' and to_country == 'DE'):
            direct_de_it_edges.append((from_node, to_node, from_country, to_country))

    if direct_de_it_edges:
        print(f"\n⚠️  FOUND {len(direct_de_it_edges)} DIRECT DE-IT EDGES (PHYSICALLY IMPOSSIBLE!):")
        for from_n, to_n, from_c, to_c in direct_de_it_edges[:10]:
            print(f"    {from_c} node {from_n} ←→ {to_c} node {to_n}")
    else:
        print(f"\n✓ No direct DE-IT edges found (good!)")

    # Check DE-AT, AT-IT connectivity
    print("\n" + "="*80)
    print("CHECKING CORRIDOR CONNECTIVITY:")
    print("="*80)

    # DE-AT connections
    de_at_edges = []
    for edge in edges:
        from_node = edge.get('from_node')
        to_node = edge.get('to_node')

        from_country = node_to_country.get(from_node)
        to_country = node_to_country.get(to_node)

        if (from_country == 'DE' and to_country == 'AT') or (from_country == 'AT' and to_country == 'DE'):
            de_at_edges.append((from_node, to_node))

    # AT-IT connections
    at_it_edges = []
    for edge in edges:
        from_node = edge.get('from_node')
        to_node = edge.get('to_node')

        from_country = node_to_country.get(from_node)
        to_country = node_to_country.get(to_node)

        if (from_country == 'AT' and to_country == 'IT') or (from_country == 'IT' and to_country == 'AT'):
            at_it_edges.append((from_node, to_node))

    print(f"\nDE ←→ AT connections: {len(de_at_edges)}")
    if de_at_edges:
        print(f"  Examples: {de_at_edges[:5]}")
    else:
        print(f"  ⚠️  NO DE-AT CONNECTIONS! Germany and Austria are DISCONNECTED!")

    print(f"\nAT ←→ IT connections: {len(at_it_edges)}")
    if at_it_edges:
        print(f"  Examples: {at_it_edges[:5]}")
    else:
        print(f"  ⚠️  NO AT-IT CONNECTIONS! Austria and Italy are DISCONNECTED!")

    # Try to find a path from DE to IT
    print("\n" + "="*80)
    print("PATHFINDING TEST: DE → IT")
    print("="*80)

    if 'DE' not in nodes_by_country or 'IT' not in nodes_by_country:
        print("\n⚠️  Missing DE or IT nodes!")
        return

    # Pick first DE and IT nodes
    de_node = nodes_by_country['DE'][0]
    it_node = nodes_by_country['IT'][0]

    print(f"\nFinding path from DE node {de_node} to IT node {it_node}...")

    # BFS pathfinding
    queue = deque([(de_node, [de_node])])
    visited = {de_node}
    path_found = None

    while queue and not path_found:
        node, path = queue.popleft()

        if len(path) > 10:  # Max depth
            continue

        if node == it_node:
            path_found = path
            break

        for neighbor in adjacency.get(node, []):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))

    if path_found:
        print(f"\n✓ Path found! Length: {len(path_found)} nodes")
        print(f"\nPath details:")
        for i, node_id in enumerate(path_found):
            country = node_to_country.get(node_id, 'XX')
            print(f"  {i+1}. Node {node_id} ({country})")

        # Check if path goes through Austria
        countries_in_path = [node_to_country.get(n, 'XX') for n in path_found]
        if 'AT' in countries_in_path:
            print(f"\n✓ Path correctly routes through Austria!")
        else:
            print(f"\n⚠️  Path does NOT go through Austria!")
            print(f"   Countries in path: {' → '.join(countries_in_path)}")
    else:
        print(f"\n✗ NO PATH FOUND from DE to IT!")
        print(f"   Network is disconnected or path > 10 hops")

    print("\n" + "="*80)


def main():
    """Main function"""
    # Check most recent case directory
    input_data_dir = Path("input_data")

    # Find all case directories
    case_dirs = [d for d in input_data_dir.iterdir() if d.is_dir() and d.name.startswith("case_")]

    if not case_dirs:
        print("No case directories found in input_data/")
        return

    # Use most recent case
    most_recent = max(case_dirs, key=lambda d: d.stat().st_mtime)

    print(f"\nAnalyzing: {most_recent}")
    print("="*80)

    geo_elements = load_geographic_elements(most_recent)
    analyze_network_topology(geo_elements)


if __name__ == "__main__":
    main()
