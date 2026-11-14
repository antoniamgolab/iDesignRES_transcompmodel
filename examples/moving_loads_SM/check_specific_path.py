"""
Check specific problematic paths to see if break logic is correct
"""

import yaml
import os

case_folder = "case_20251106_112933"
input_path = os.path.join("input_data", case_folder)

def load_yaml(filename):
    filepath = os.path.join(input_path, filename)
    with open(filepath, 'r') as f:
        return yaml.safe_load(f)

paths = load_yaml('Path.yaml')
breaks = load_yaml('MandatoryBreaks.yaml')

# Check the most problematic paths
problem_path_ids = [5409, 5289, 5129]

print("="*80)
print("DETAILED ANALYSIS OF PROBLEMATIC PATHS")
print("="*80)

for path_id in problem_path_ids:
    path = next((p for p in paths if p['id'] == path_id), None)
    if not path:
        print(f"\nPath {path_id} not found!")
        continue

    path_breaks = [b for b in breaks if b['path_id'] == path_id]

    print(f"\n{'-'*80}")
    print(f"PATH {path_id}")
    print(f"{'-'*80}")
    print(f"Total length: {path['length']:.1f} km")
    print(f"Sequence nodes: {path['sequence']}")
    print(f"Number of segments: {len(path['sequence']) - 1}")

    # Calculate expected breaks
    expected_breaks = int(path['length'] / 360)
    print(f"\nExpected breaks (360 km threshold): {expected_breaks}")
    print(f"Actual break entries: {len(path_breaks)}")

    if path_breaks:
        print(f"\nBreak entries for this path:")
        for i, b in enumerate(path_breaks, 1):
            print(f"  {i}. Break #{b['break_number']} at node {b['latest_node_idx']} "
                  f"(geo_id={b['latest_geo_id']})")
            print(f"     Cumulative dist: {b['cumulative_distance']:.1f} km")
            print(f"     Time with breaks: {b['time_with_breaks']:.2f}h")
            print(f"     Total driving time: {b['total_driving_time']:.2f}h")
    else:
        print("\n  NO BREAK ENTRIES for this path!")

    # Check if breaks match expected
    if len(path_breaks) < expected_breaks:
        print(f"\n  *** WARNING: Missing {expected_breaks - len(path_breaks)} break entries! ***")
        print(f"  *** This path needs {expected_breaks} breaks but only has {len(path_breaks)} ***")

print("\n" + "="*80)
print("EXPLANATION")
print("="*80)
print("""
If a path has very long segments (e.g., 900 km) but only a few nodes,
the preprocessing might only create break entries at the nodes that exist.

For example:
- Path with 2 nodes: A --900km--> B
- Only 1 place to put a break: at node B
- But the driver needs 2 breaks during the 900 km journey!

This means the mandatory break constraint is UNDER-constraining the model,
allowing less break time than legally required.

The extra_break_time you're seeing might actually be the model compensating
for this under-constraint, especially for BEV charging needs.
""")
