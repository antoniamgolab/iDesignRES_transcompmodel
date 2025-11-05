"""
VALIDATION: Check if max_depth=15 fix successfully increased Austria routing

This script validates that increasing max_depth from 5 to 15 resulted in
significantly more Germany→Italy routes passing through Austrian AT3 regions.

Run on: input_data/case_20251104_122034/
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import yaml
from collections import defaultdict

print("="*80)
print("VALIDATING max_depth=15 ROUTING FIX")
print("="*80)

# ==============================================================================
# LOAD NEW PREPROCESSED DATA (max_depth=15)
# ==============================================================================

case_dir = 'input_data/case_20251104_122034'

print(f"\nAnalyzing case: {case_dir}")

# Load data
with open(f'{case_dir}/GeographicElement.yaml', 'r', encoding='utf-8') as f:
    geo_elements = yaml.safe_load(f)

with open(f'{case_dir}/Path.yaml', 'r', encoding='utf-8') as f:
    paths = yaml.safe_load(f)

with open(f'{case_dir}/Odpair.yaml', 'r', encoding='utf-8') as f:
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
        'destination': od['to'],
        'demand': od.get('F', [0])[0]  # First year demand
    }

path_lookup = {}
for path in paths:
    path_lookup[path['id']] = {
        'sequence': path['sequence'],
        'length': path['length'],
        'origin': path['origin'],
        'destination': path['destination']
    }

# ==============================================================================
# IDENTIFY AUSTRIAN NODES
# ==============================================================================

austrian_nodes = set()
austrian_nuts2_regions = set()
for node_id, nuts2 in node_to_nuts2.items():
    if nuts2.startswith('AT'):
        austrian_nodes.add(node_id)
        austrian_nuts2_regions.add(nuts2)

print(f"\n{'Austrian Regions in Dataset:':}")
print(f"  Austrian NUTS2 regions: {sorted(austrian_nuts2_regions)}")
print(f"  Austrian node IDs: {sorted(austrian_nodes)}")

# ==============================================================================
# ANALYZE ALL ROUTES BY PATH LENGTH
# ==============================================================================

print("\n" + "="*80)
print("PATH LENGTH DISTRIBUTION")
print("="*80)

length_distribution = defaultdict(int)
for path in paths:
    num_nodes = len(path['sequence'])
    length_distribution[num_nodes] += 1

print(f"\n{'Nodes per path':<20} {'Count':>10} {'Percentage':>12}")
print("-" * 44)
for num_nodes in sorted(length_distribution.keys()):
    count = length_distribution[num_nodes]
    pct = 100 * count / len(paths)
    print(f"{num_nodes:<20} {count:>10,} {pct:>11.1f}%")

max_path_length = max(length_distribution.keys())
multi_hop_count = sum(count for nodes, count in length_distribution.items() if nodes > 2)
multi_hop_pct = 100 * multi_hop_count / len(paths)

print("-" * 44)
print(f"{'TOTAL':<20} {len(paths):>10,} {100.0:>11.1f}%")
print(f"\nMaximum path length: {max_path_length} nodes")
print(f"Multi-hop paths (3+ nodes): {multi_hop_count:,} ({multi_hop_pct:.1f}%)")

# ==============================================================================
# ANALYZE GERMANY → ITALY ROUTES
# ==============================================================================

print("\n" + "="*80)
print("GERMANY → ITALY ROUTING ANALYSIS")
print("="*80)

# Find paths from Germany to Italy
de_to_it_paths = []

for odpair in odpairs:
    path_id = odpair['path_id']
    if path_id not in path_lookup:
        continue

    path_info = path_lookup[path_id]
    origin_id = odpair['from']
    dest_id = odpair['to']

    origin_nuts2 = node_to_nuts2.get(origin_id)
    dest_nuts2 = node_to_nuts2.get(dest_id)
    origin_country = node_to_country.get(origin_id)
    dest_country = node_to_country.get(dest_id)

    if origin_country == 'DE' and dest_country == 'IT':
        # Extract countries and NUTS2 regions in route
        route_countries = []
        route_nuts2_regions = []
        for node_id in path_info['sequence']:
            country = node_to_country.get(node_id)
            nuts2 = node_to_nuts2.get(node_id)
            if country and country not in route_countries:
                route_countries.append(country)
            if nuts2:
                route_nuts2_regions.append(nuts2)

        # Check if route passes through Austria
        passes_through_austria = any(node_id in austrian_nodes for node_id in path_info['sequence'])
        austrian_regions_on_route = [n for n in route_nuts2_regions if n.startswith('AT')]

        de_to_it_paths.append({
            'path_id': path_id,
            'odpair_id': odpair['id'],
            'origin_nuts2': origin_nuts2,
            'dest_nuts2': dest_nuts2,
            'sequence': path_info['sequence'],
            'route_countries': route_countries,
            'route_nuts2_regions': route_nuts2_regions,
            'num_nodes': len(path_info['sequence']),
            'length': path_info['length'],
            'passes_through_austria': passes_through_austria,
            'austrian_regions': austrian_regions_on_route,
            'demand': odpair.get('F', [0])[0]
        })

print(f"\nFound {len(de_to_it_paths)} Germany → Italy paths")

if len(de_to_it_paths) == 0:
    print("\nWARNING: No Germany → Italy paths found!")
    sys.exit(0)

# ==============================================================================
# ROUTING BREAKDOWN
# ==============================================================================

print("\n" + "="*80)
print("ROUTING BREAKDOWN")
print("="*80)

# Categorize paths
paths_via_austria = [p for p in de_to_it_paths if p['passes_through_austria']]
paths_direct = [p for p in de_to_it_paths if p['num_nodes'] == 2]
paths_multi_hop_no_austria = [p for p in de_to_it_paths if p['num_nodes'] > 2 and not p['passes_through_austria']]

print(f"\n{'Route Type':<40} {'Count':>10} {'Percentage':>12}")
print("-" * 64)
print(f"{'Via Austria (AT3x)':<40} {len(paths_via_austria):>10,} {100*len(paths_via_austria)/len(de_to_it_paths):>11.1f}%")
print(f"{'Multi-hop without Austria':<40} {len(paths_multi_hop_no_austria):>10,} {100*len(paths_multi_hop_no_austria)/len(de_to_it_paths):>11.1f}%")
print(f"{'Direct 2-node paths':<40} {len(paths_direct):>10,} {100*len(paths_direct)/len(de_to_it_paths):>11.1f}%")
print("-" * 64)
print(f"{'TOTAL':<40} {len(de_to_it_paths):>10,} {100.0:>11.1f}%")

# Node count statistics for DE→IT
node_counts = [p['num_nodes'] for p in de_to_it_paths]
avg_nodes = sum(node_counts) / len(node_counts)
two_node_paths = len([n for n in node_counts if n == 2])

print(f"\n{'Path Structure Statistics:':}")
print(f"  Average nodes per path: {avg_nodes:.2f}")
print(f"  2-node paths: {two_node_paths} ({100*two_node_paths/len(de_to_it_paths):.1f}%)")
print(f"  Multi-node paths (3+): {len(de_to_it_paths) - two_node_paths} ({100*(len(de_to_it_paths)-two_node_paths)/len(de_to_it_paths):.1f}%)")

# Calculate freight through Austria
freight_via_austria = sum(p['demand'] for p in paths_via_austria)
total_freight = sum(p['demand'] for p in de_to_it_paths)
print(f"\n{'Freight Volume:':}")
print(f"  Via Austria: {freight_via_austria:,.0f} trucks ({100*freight_via_austria/total_freight:.1f}%)")
print(f"  Total DE→IT: {total_freight:,.0f} trucks")

# ==============================================================================
# AUSTRIAN REGIONS USAGE
# ==============================================================================

print("\n" + "="*80)
print("AUSTRIAN NUTS2 REGIONS IN ROUTES")
print("="*80)

austrian_region_usage = defaultdict(int)
for path_info in paths_via_austria:
    for region in path_info['austrian_regions']:
        austrian_region_usage[region] += 1

print(f"\n{'NUTS2 Region':<20} {'Appearances in Routes':>25}")
print("-" * 47)
for region in sorted(austrian_region_usage.keys()):
    count = austrian_region_usage[region]
    print(f"{region:<20} {count:>25,}")
print("-" * 47)
print(f"{'TOTAL':<20} {sum(austrian_region_usage.values()):>25,}")

# ==============================================================================
# SAMPLE ROUTES VIA AUSTRIA
# ==============================================================================

print("\n" + "="*80)
print("SAMPLE ROUTES VIA AUSTRIA")
print("="*80)

if paths_via_austria:
    # Sort by demand (highest first)
    paths_via_austria.sort(key=lambda x: x['demand'], reverse=True)

    print(f"\nTop 10 routes via Austria (by demand):")
    for i, path_info in enumerate(paths_via_austria[:10], 1):
        print(f"\n{i}. Path {path_info['path_id']}: {path_info['origin_nuts2']} → {path_info['dest_nuts2']}")
        print(f"   Length: {path_info['length']:.1f} km")
        print(f"   Nodes: {path_info['num_nodes']}")
        print(f"   Demand: {path_info['demand']:,.0f} trucks")
        print(f"   Countries: {' → '.join(path_info['route_countries'])}")
        print(f"   Austrian regions: {', '.join(path_info['austrian_regions'])}")
        # Show first few NUTS2 regions in sequence
        sample_nuts2 = path_info['route_nuts2_regions'][:8]
        if len(path_info['route_nuts2_regions']) > 8:
            sample_nuts2.append('...')
        print(f"   Route: {' → '.join(sample_nuts2)}")
else:
    print("\n❌ NO ROUTES VIA AUSTRIA FOUND!")

# ==============================================================================
# COMPARISON WITH PREVIOUS RUN (max_depth=5)
# ==============================================================================

print("\n" + "="*80)
print("COMPARISON: max_depth=5 vs max_depth=15")
print("="*80)

print("""
PREVIOUS RUN (max_depth=5, case: input_data/fixed_nuts_2):
  - Germany→Italy paths via Austria: 14 (1.9%)
  - Average nodes per path: ~2.5
  - Maximum path length: 5 nodes
  - Multi-hop paths: 28.6%

CURRENT RUN (max_depth=15, case: case_20251104_122034):
""")

print(f"  - Germany→Italy paths via Austria: {len(paths_via_austria)} ({100*len(paths_via_austria)/len(de_to_it_paths):.1f}%)")
print(f"  - Average nodes per path: {avg_nodes:.2f}")
print(f"  - Maximum path length: {max_path_length} nodes")
print(f"  - Multi-hop paths: {multi_hop_pct:.1f}%")

# ==============================================================================
# VALIDATION VERDICT
# ==============================================================================

print("\n" + "="*80)
print("VALIDATION VERDICT")
print("="*80)

improvement_factor = len(paths_via_austria) / 14  # Previous was 14 paths
austria_pct = 100 * len(paths_via_austria) / len(de_to_it_paths)

print(f"""
EXPECTED OUTCOME:
  - Significantly more routes via Austria (target: >100 paths, >15%)
  - Maximum path length > 5 nodes
  - More multi-hop routing overall

ACTUAL OUTCOME:
  - Routes via Austria: {len(paths_via_austria)} paths ({austria_pct:.1f}%)
  - Improvement: {improvement_factor:.1f}x increase from previous run
  - Maximum path length: {max_path_length} nodes
  - Multi-hop routing: {multi_hop_pct:.1f}%

VERDICT:
""")

if len(paths_via_austria) > 100 and austria_pct > 15:
    print("  ✅ EXCELLENT SUCCESS!")
    print("     • Dramatic improvement in Austrian routing")
    print("     • BFS now explores longer paths successfully")
    print("     • Routes realistically pass through AT3 regions")
elif len(paths_via_austria) > 50 and austria_pct > 7:
    print("  ✅ SUCCESS!")
    print("     • Significant improvement in Austrian routing")
    print("     • max_depth=15 allows longer path exploration")
    print(f"     • {improvement_factor:.1f}x more routes via Austria than before")
elif len(paths_via_austria) > 14:
    print("  ⚠️  PARTIAL SUCCESS")
    print("     • Some improvement over max_depth=5")
    print("     • But routes may still be limited by:")
    print("        - Corridor filtering too restrictive")
    print("        - Network connectivity gaps")
    print("        - max_depth=15 still insufficient for some long routes")
else:
    print("  ❌ NO IMPROVEMENT")
    print("     • Austrian routing not significantly improved")
    print("     • Possible issues:")
    print("        - max_depth change not applied correctly")
    print("        - Network topology issues")
    print("        - Corridor filtering excluding Austrian routes")

print("\n" + "="*80)
