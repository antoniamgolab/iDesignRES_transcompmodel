"""
Analyze mandatory breaks separately for single-node vs multi-node paths.
"""

import yaml
import os
import pandas as pd

case_name = "case_20251028_091344_var_var"
input_folder = os.path.join("input_data", case_name)

# Load paths and breaks
with open(os.path.join(input_folder, "Path.yaml")) as f:
    paths = yaml.safe_load(f)

with open(os.path.join(input_folder, "MandatoryBreaks.yaml")) as f:
    breaks = yaml.safe_load(f)

# Create lookup for path info
path_info = {}
for p in paths:
    path_info[p['id']] = {
        'origin': p['origin'],
        'destination': p['destination'],
        'length': p['length'],
        'num_nodes': len(p['sequence']),
        'is_self_loop': p['origin'] == p['destination'],
        'cumulative_distance': p['cumulative_distance']
    }

# Categorize breaks by path type
df_breaks = pd.DataFrame(breaks)
df_breaks['num_nodes'] = df_breaks['path_id'].map(lambda pid: path_info[pid]['num_nodes'])
df_breaks['is_self_loop'] = df_breaks['path_id'].map(lambda pid: path_info[pid]['is_self_loop'])
df_breaks['path_length'] = df_breaks['path_id'].map(lambda pid: path_info[pid]['length'])

print("="*80)
print("MANDATORY BREAKS BY PATH TYPE")
print("="*80)

# Analysis for multi-node paths
print("\n1. MULTI-NODE PATHS (num_nodes > 1):")
multi_node_breaks = df_breaks[df_breaks['num_nodes'] > 1].copy()
print(f"   Total breaks on multi-node paths: {len(multi_node_breaks)}")
if len(multi_node_breaks) > 0:
    print(f"   Breaks at node_idx=0: {(multi_node_breaks['latest_node_idx'] == 0).sum()} "
          f"({100*(multi_node_breaks['latest_node_idx'] == 0).sum()/len(multi_node_breaks):.1f}%)")
    print(f"   Breaks with cumulative_time=0: {(multi_node_breaks['cumulative_driving_time'] == 0).sum()} "
          f"({100*(multi_node_breaks['cumulative_driving_time'] == 0).sum()/len(multi_node_breaks):.1f}%)")

    print(f"\n   Statistics for multi-node path breaks:")
    print(f"     Avg node_idx: {multi_node_breaks['latest_node_idx'].mean():.2f}")
    print(f"     Max node_idx: {multi_node_breaks['latest_node_idx'].max()}")
    print(f"     Avg cumulative_time: {multi_node_breaks['cumulative_driving_time'].mean():.2f}h")
    print(f"     Max cumulative_time: {multi_node_breaks['cumulative_driving_time'].max():.2f}h")

    # Show examples
    print(f"\n   Examples of breaks on multi-node paths:")
    for _, row in multi_node_breaks.head(10).iterrows():
        print(f"     Path {row['path_id']} (break {row['break_number']}): "
              f"node_idx={row['latest_node_idx']}, "
              f"num_nodes={row['num_nodes']}, "
              f"cum_dist={row['cumulative_distance']:.1f}km, "
              f"cum_time={row['cumulative_driving_time']:.2f}h")

# Analysis for single-node paths
print("\n2. SINGLE-NODE PATHS (num_nodes = 1):")
single_node_breaks = df_breaks[df_breaks['num_nodes'] == 1].copy()
print(f"   Total breaks on single-node paths: {len(single_node_breaks)}")
if len(single_node_breaks) > 0:
    print(f"   Breaks at node_idx=0: {(single_node_breaks['latest_node_idx'] == 0).sum()} "
          f"({100*(single_node_breaks['latest_node_idx'] == 0).sum()/len(single_node_breaks):.1f}%)")
    print(f"   Breaks with cumulative_time=0: {(single_node_breaks['cumulative_driving_time'] == 0).sum()} "
          f"({100*(single_node_breaks['cumulative_driving_time'] == 0).sum()/len(single_node_breaks):.1f}%)")

    print(f"\n   Examples of breaks on single-node paths:")
    for _, row in single_node_breaks.head(5).iterrows():
        print(f"     Path {row['path_id']} (break {row['break_number']}): "
              f"node_idx={row['latest_node_idx']}, "
              f"path_length={row['path_length']:.1f}km, "
              f"cum_dist={row['cumulative_distance']:.1f}km, "
              f"cum_time={row['cumulative_driving_time']:.2f}h")

# Check specific multi-node paths that should have proper breaks
print("\n3. DETAILED CHECK: Path 29 (0->47, 2 nodes, 841.3km):")
path29_breaks = df_breaks[df_breaks['path_id'] == 29]
if len(path29_breaks) > 0:
    print(f"   Number of breaks: {len(path29_breaks)}")
    for _, row in path29_breaks.iterrows():
        print(f"     Break {row['break_number']}: "
              f"node_idx={row['latest_node_idx']}, "
              f"cum_dist={row['cumulative_distance']:.1f}km, "
              f"cum_time={row['cumulative_driving_time']:.2f}h")

    # Show what we'd expect
    print(f"\n   Expected for 841.3km at 80km/h (10.5h total):")
    print(f"     Break 1: node_idx=0 or 1, cum_time≈4.5h, cum_dist≈360km")
    print(f"     Break 2: node_idx=1, cum_time≈9.0h, cum_dist≈720km")
else:
    print("   No breaks found for path 29!")

print("\n4. DETAILED CHECK: Path 30 (0->48, 2 nodes, 860.0km):")
path30_breaks = df_breaks[df_breaks['path_id'] == 30]
if len(path30_breaks) > 0:
    print(f"   Number of breaks: {len(path30_breaks)}")
    for _, row in path30_breaks.iterrows():
        print(f"     Break {row['break_number']}: "
              f"node_idx={row['latest_node_idx']}, "
              f"cum_dist={row['cumulative_distance']:.1f}km, "
              f"cum_time={row['cumulative_driving_time']:.2f}h")
else:
    print("   No breaks found for path 30!")

print("\n" + "="*80)
print("CONCLUSION")
print("="*80)

if len(multi_node_breaks) > 0:
    at_origin = (multi_node_breaks['latest_node_idx'] == 0).sum()
    if at_origin == len(multi_node_breaks):
        print("ALL breaks on multi-node paths are at node_idx=0!")
        print("This means the algorithm is failing even for paths with proper node sequences.")
    elif at_origin > 0.9 * len(multi_node_breaks):
        print(f"Most breaks ({at_origin}/{len(multi_node_breaks)}) on multi-node paths are at node_idx=0.")
        print("The algorithm is mostly failing.")
    else:
        print(f"Mixed results: {at_origin} breaks at origin, {len(multi_node_breaks)-at_origin} elsewhere.")
        print("Need to understand the pattern.")
else:
    print("No breaks found for multi-node paths!")
