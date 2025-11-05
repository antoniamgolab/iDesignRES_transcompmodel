"""
Analyze the Path.yaml structure to understand self-loops vs multi-node paths.
"""

import yaml
import os

case_name = "case_20251028_091344_var_var"
path_file = os.path.join("input_data", case_name, "Path.yaml")

print("="*80)
print("PATH STRUCTURE ANALYSIS")
print("="*80)

with open(path_file) as f:
    paths = yaml.safe_load(f)

total = len(paths)
self_loops = sum(1 for p in paths if p['origin'] == p['destination'])
multi_node = sum(1 for p in paths if len(p['sequence']) > 1)
single_node = sum(1 for p in paths if len(p['sequence']) == 1)

print(f"\nTotal paths: {total}")
print(f"\nBy origin/destination:")
print(f"  Self-loops (origin==destination): {self_loops} ({100*self_loops/total:.1f}%)")
print(f"  Different origin/dest: {total-self_loops} ({100*(total-self_loops)/total:.1f}%)")

print(f"\nBy sequence length:")
print(f"  Single node: {single_node} ({100*single_node/total:.1f}%)")
print(f"  Multi-node: {multi_node} ({100*multi_node/total:.1f}%)")

# Check path lengths
zero_length = sum(1 for p in paths if p['length'] == 0.0)
nonzero_length = total - zero_length

print(f"\nBy path length:")
print(f"  Zero length: {zero_length} ({100*zero_length/total:.1f}%)")
print(f"  Non-zero length: {nonzero_length} ({100*nonzero_length/total:.1f}%)")

# Show examples of different types
print("\n" + "="*80)
print("EXAMPLES")
print("="*80)

print("\n1. Self-loops with single node:")
self_loop_single = [p for p in paths if p['origin'] == p['destination'] and len(p['sequence']) == 1]
for p in self_loop_single[:3]:
    print(f"  Path {p['id']}: {p['origin']}->{p['destination']}, "
          f"sequence={p['sequence']}, length={p['length']:.1f}km")

print("\n2. Self-loops with multiple nodes (if any):")
self_loop_multi = [p for p in paths if p['origin'] == p['destination'] and len(p['sequence']) > 1]
if self_loop_multi:
    for p in self_loop_multi[:3]:
        print(f"  Path {p['id']}: {p['origin']}->{p['destination']}, "
              f"sequence={p['sequence']}, length={p['length']:.1f}km")
else:
    print("  None found")

print("\n3. Different origin/dest with multiple nodes (if any):")
diff_multi = [p for p in paths if p['origin'] != p['destination'] and len(p['sequence']) > 1]
if diff_multi:
    for p in diff_multi[:3]:
        print(f"  Path {p['id']}: {p['origin']}->{p['destination']}, "
              f"sequence={p['sequence']}, length={p['length']:.1f}km, "
              f"cumulative_distance={p['cumulative_distance']}")
else:
    print("  None found")

print("\n4. Different origin/dest with single node (if any):")
diff_single = [p for p in paths if p['origin'] != p['destination'] and len(p['sequence']) == 1]
if diff_single:
    for p in diff_single[:3]:
        print(f"  Path {p['id']}: {p['origin']}->{p['destination']}, "
              f"sequence={p['sequence']}, length={p['length']:.1f}km")
else:
    print("  None found")

# Check non-zero length paths
print("\n5. Non-zero length paths:")
nonzero_paths = [p for p in paths if p['length'] > 0]
if nonzero_paths:
    for p in nonzero_paths[:5]:
        print(f"  Path {p['id']}: {p['origin']}->{p['destination']}, "
              f"sequence={p['sequence']}, length={p['length']:.1f}km, "
              f"cumulative_distance={p['cumulative_distance']}")
else:
    print("  None found - ALL paths have zero length!")

print("\n" + "="*80)
print("CONCLUSION")
print("="*80)

if self_loops == total and single_node == total and zero_length == total:
    print("ALL paths are self-loops with single nodes and zero length.")
    print("This explains why all mandatory breaks are at node_idx=0.")
    print("\nROOT CAUSE: No real multi-node paths exist in the data!")
elif nonzero_length > 0:
    print(f"{nonzero_length} paths have non-zero length.")
    print("Need to investigate why mandatory breaks aren't using these.")
else:
    print("Mixed path structure - need further investigation.")
