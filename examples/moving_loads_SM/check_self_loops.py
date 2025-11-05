"""
Check why we have self-loop paths in international routing data.
"""

import yaml
import os

case = 'case_20251028_091344_var_var'
input_folder = os.path.join('input_data', case)

# Load data
with open(os.path.join(input_folder, 'Path.yaml')) as f:
    paths = yaml.safe_load(f)

with open(os.path.join(input_folder, 'GeographicElement.yaml')) as f:
    geo = yaml.safe_load(f)

# Create node lookup
node_lookup = {g['id']: g for g in geo}

print("="*80)
print("SELF-LOOP ANALYSIS")
print("="*80)

# Find self-loops
self_loops = [p for p in paths if p['origin'] == p['destination']]
non_self_loops = [p for p in paths if p['origin'] != p['destination']]

print(f"\nTotal paths: {len(paths)}")
print(f"Self-loops (origin==destination): {len(self_loops)} ({100*len(self_loops)/len(paths):.1f}%)")
print(f"Different origin/dest: {len(non_self_loops)} ({100*len(non_self_loops)/len(paths):.1f}%)")

# Check countries for self-loops
print("\n" + "="*80)
print("SELF-LOOP PATHS WITH COUNTRY INFO")
print("="*80)

for p in self_loops[:10]:
    node_id = p['origin']
    node = node_lookup.get(node_id, {})

    print(f"\nPath {p['id']}:")
    print(f"  Origin/Dest node: {node_id}")
    print(f"  Node name: {node.get('name', '?')}")
    print(f"  Country: {node.get('country', '?')}")
    print(f"  Path length: {p['length']:.1f} km")
    print(f"  Sequence: {p['sequence']}")
    print(f"  Cumulative distance: {p['cumulative_distance']}")

# Check countries for non-self-loops
print("\n" + "="*80)
print("SAMPLE NON-SELF-LOOP PATHS")
print("="*80)

for p in non_self_loops[:5]:
    origin_node = node_lookup.get(p['origin'], {})
    dest_node = node_lookup.get(p['destination'], {})

    print(f"\nPath {p['id']}: {p['origin']} -> {p['destination']}")
    print(f"  Origin: {origin_node.get('name', '?')} ({origin_node.get('country', '?')})")
    print(f"  Destination: {dest_node.get('name', '?')} ({dest_node.get('country', '?')})")
    print(f"  Path length: {p['length']:.1f} km")
    print(f"  Sequence length: {len(p['sequence'])} nodes")
    print(f"  Cumulative distance: {p['cumulative_distance']}")

# Check if all routes are international
print("\n" + "="*80)
print("DOMESTIC vs INTERNATIONAL")
print("="*80)

domestic_count = 0
international_count = 0
unknown_count = 0

for p in paths:
    origin_node = node_lookup.get(p['origin'], {})
    dest_node = node_lookup.get(p['destination'], {})

    origin_country = origin_node.get('country')
    dest_country = dest_node.get('country')

    if origin_country and dest_country:
        if origin_country == dest_country:
            domestic_count += 1
        else:
            international_count += 1
    else:
        unknown_count += 1

print(f"\nDomestic routes (same country): {domestic_count}")
print(f"International routes (different countries): {international_count}")
print(f"Unknown (missing country info): {unknown_count}")

# Conclusion
print("\n" + "="*80)
print("CONCLUSION")
print("="*80)

if domestic_count > 0:
    print(f"\nYou have {domestic_count} DOMESTIC routes in the data!")
    print("This suggests cross_border_only filter was NOT active during preprocessing.")
    print("\nTo use only international routes, re-run preprocessing with:")
    print("  cross_border_only=True")
elif len(self_loops) > 0:
    print(f"\nYou have {len(self_loops)} self-loop paths but they appear to be international.")
    print("This might be due to aggregation artifacts.")
    print("The fix we implemented should handle these correctly.")
else:
    print("\nAll routes are international with proper multi-node sequences.")
    print("No issues detected!")
