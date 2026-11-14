"""
Investigate if extra_break_time is caused by very long edges
with multiple mandatory breaks at the same node
"""

import yaml
import pandas as pd
from collections import defaultdict
import os

# Load the data
print("="*80)
print("INVESTIGATING LONG EDGES AND MANDATORY BREAKS")
print("="*80)

# Use the most recent case folder
case_folder = "case_20251106_112933"
input_path = os.path.join("input_data", case_folder)

print(f"Loading data from: {input_path}")

# Load necessary data files
def load_yaml(filename):
    filepath = os.path.join(input_path, filename)
    with open(filepath, 'r') as f:
        return yaml.safe_load(f)

data = {}
data['GeographicElement'] = load_yaml('GeographicElement.yaml')
data['Path'] = load_yaml('Path.yaml')
data['MandatoryBreaks'] = load_yaml('MandatoryBreaks.yaml')

print(f"Loaded {len(data['GeographicElement'])} geographic elements")
print(f"Loaded {len(data['Path'])} paths")
print(f"Loaded {len(data['MandatoryBreaks'])} mandatory breaks")

# =============================================================================
# 1. CHECK FOR VERY LONG EDGES (from Path segments)
# =============================================================================
print("\n" + "="*80)
print("1. CHECKING FOR VERY LONG EDGE SEGMENTS IN PATHS")
print("="*80)

# Extract edge information from paths
# Each path has a sequence of nodes and we need to calculate edge lengths
all_edges = []

for path in data['Path']:
    sequence = path['sequence']
    if len(sequence) < 2:
        continue

    # Calculate cumulative distances and segment lengths
    # Since we don't have individual edge objects, we'll look at path segments
    # For now, just analyze the path as a whole
    path_length = path['length']
    num_segments = len(sequence) - 1

    if num_segments > 0:
        avg_segment = path_length / num_segments
        all_edges.append({
            'path_id': path['id'],
            'num_segments': num_segments,
            'path_length': path_length,
            'avg_segment_length': avg_segment
        })

edge_df = pd.DataFrame(all_edges)
edge_df = edge_df.sort_values('avg_segment_length', ascending=False)

print(f"\nTotal paths analyzed: {len(edge_df)}")
print(f"Max average segment length: {edge_df['avg_segment_length'].max():.1f} km")
print(f"Mean average segment length: {edge_df['avg_segment_length'].mean():.1f} km")
print(f"Paths with avg segment > 360 km: {(edge_df['avg_segment_length'] > 360).sum()}")
print(f"Paths with avg segment > 720 km: {(edge_df['avg_segment_length'] > 720).sum()}")

print("\nTop 20 paths with longest average segment lengths:")
print(edge_df.head(20).to_string(index=False))

# =============================================================================
# 2. CHECK MANDATORY BREAKS PER NODE
# =============================================================================
print("\n" + "="*80)
print("2. CHECKING MANDATORY BREAKS PER GEO_ID")
print("="*80)

mandatory_breaks = data['MandatoryBreaks']
print(f"\nTotal mandatory break entries: {len(mandatory_breaks)}")

# Group by latest_geo_id to find nodes with multiple break entries
breaks_by_geo = defaultdict(list)
for mb in mandatory_breaks:
    breaks_by_geo[mb['latest_geo_id']].append(mb)

# Find nodes with multiple break entries
multi_break_nodes = {geo_id: breaks for geo_id, breaks in breaks_by_geo.items()
                     if len(breaks) > 1}

print(f"Nodes with multiple break entries: {len(multi_break_nodes)}")

if multi_break_nodes:
    print("\nNodes with MULTIPLE mandatory break entries:")
    print("-"*80)
    for geo_id, breaks in sorted(multi_break_nodes.items(),
                                  key=lambda x: len(x[1]),
                                  reverse=True)[:15]:
        print(f"\nNode {geo_id}: {len(breaks)} break entries")
        # Check if these are from different paths or same path
        path_ids = [mb['path_id'] for mb in breaks]
        unique_paths = len(set(path_ids))
        print(f"  From {unique_paths} different path(s)")

        for i, mb in enumerate(breaks[:5], 1):  # Show first 5
            print(f"  Break {i}: path_id={mb['path_id']}, "
                  f"break_number={mb['break_number']}, "
                  f"cumulative_dist={mb['cumulative_distance']:.1f} km, "
                  f"time_with_breaks={mb['time_with_breaks']:.2f}h")
        if len(breaks) > 5:
            print(f"  ... and {len(breaks)-5} more break entries")
else:
    print("\nNo nodes with multiple break entries found")

# =============================================================================
# 3. CHECK IF BREAK LOGIC PROPERLY HANDLES VERY LONG EDGES
# =============================================================================
print("\n" + "="*80)
print("3. CHECKING BREAK LOGIC ON LONG EDGES")
print("="*80)

# Analyze paths that cross very long edges
paths = data['Path']
break_threshold = 360  # km

print(f"\nBreak threshold: {break_threshold} km (4.5h at 80 km/h)")

# Find paths with segments requiring multiple breaks
problematic_paths = []

for path in paths:
    path_id = path['id']
    sequence = path['sequence']
    length = path['length']

    # Get breaks for this path
    path_breaks = [mb for mb in mandatory_breaks if mb['path_id'] == path_id]

    if not path_breaks:
        continue

    # Calculate expected vs actual breaks
    expected_breaks = int(length / break_threshold)
    actual_breaks = len(path_breaks)
    max_break_number = max([mb['break_number'] for mb in path_breaks]) if path_breaks else 0

    # Check if there's a discrepancy
    if expected_breaks != actual_breaks or expected_breaks != max_break_number:
        problematic_paths.append({
            'path_id': path_id,
            'length': length,
            'num_nodes': len(sequence),
            'expected_breaks': expected_breaks,
            'actual_break_entries': actual_breaks,
            'max_break_number': max_break_number,
            'breaks': path_breaks
        })

if problematic_paths:
    print(f"\nFound {len(problematic_paths)} paths where break count may be incorrect:")
    print("-"*80)

    for pp in sorted(problematic_paths, key=lambda x: x['length'], reverse=True)[:10]:
        print(f"\nPath {pp['path_id']}: {pp['length']:.1f} km, {pp['num_nodes']} nodes")
        print(f"  Expected breaks: {pp['expected_breaks']}")
        print(f"  Actual break entries: {pp['actual_break_entries']}")
        print(f"  Max break_number: {pp['max_break_number']}")
        print(f"  Difference: {pp['expected_breaks'] - pp['actual_break_entries']} breaks missing")

        # Show the break entries
        for mb in pp['breaks']:
            print(f"    Break at node {mb['latest_node_idx']} (geo_id={mb['latest_geo_id']}): "
                  f"break #{mb['break_number']}, "
                  f"cum_dist={mb['cumulative_distance']:.1f} km, "
                  f"time={mb['time_with_breaks']:.2f}h")
else:
    print("\n[OK] No problematic paths found - break logic appears consistent")

# =============================================================================
# 4. ANALYZE BREAK DISTRIBUTION
# =============================================================================
print("\n" + "="*80)
print("4. BREAK DISTRIBUTION ANALYSIS")
print("="*80)

break_numbers = [mb['break_number'] for mb in mandatory_breaks]
print(f"\nBreak number distribution:")
break_dist = pd.Series(break_numbers).value_counts().sort_index()
for bn, count in break_dist.items():
    print(f"  Break #{bn}: {count} entries")

# Check cumulative distances at breaks
cum_dists = [mb['cumulative_distance'] for mb in mandatory_breaks]
print(f"\nCumulative distance at break locations:")
print(f"  Min: {min(cum_dists):.1f} km")
print(f"  Max: {max(cum_dists):.1f} km")
print(f"  Mean: {sum(cum_dists)/len(cum_dists):.1f} km")
print(f"  Breaks at > 720 km: {sum(1 for d in cum_dists if d > 720)}")

print("\n" + "="*80)
print("INVESTIGATION COMPLETE")
print("="*80)
