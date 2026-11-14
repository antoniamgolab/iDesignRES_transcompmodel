"""
Analyze Path 2111 - the path with giant 1038km edge causing huge extra_break_time
"""

import yaml

# Path 2111 data from your analysis
distances = [0.0, 3.525955475332367, 13.457492910761179, 10.329722259975348,
             10.064265710277656, 18.379980669285743, 36.51181717254974,
             1038.7430205561802, 85.73092396323673]

cumulative = [0.0, 3.525955475332367, 16.983448386093546, 27.313170646068894,
              37.37743635634655, 55.75741702563229, 92.26923419818203,
              1131.0122547543622, 1216.743178717599]

print("="*80)
print("PATH 2111 ANALYSIS - WHY 736h EXTRA_BREAK_TIME?")
print("="*80)

# Constants
avg_speed = 80  # km/h
break_threshold_km = 360  # km (4.5h × 80km/h)
break_duration = 0.75  # hours (45 min)

print(f"\nPath segments:")
for i, dist in enumerate(distances):
    if i == 0:
        continue
    print(f"  Segment {i}: {dist:.1f} km (cumulative: {cumulative[i]:.1f} km)")
    if dist > 500:
        print(f"    [!] GIANT EDGE! {dist:.1f} km")

giant_edge = 1038.7  # km
print(f"\n{'='*80}")
print(f"THE GIANT EDGE: {giant_edge:.1f} km")
print(f"{'='*80}")

# How many breaks needed?
driving_time = giant_edge / avg_speed
breaks_needed = int(giant_edge / break_threshold_km)

print(f"\nDriving time for this edge: {driving_time:.2f}h ({driving_time*60:.0f} min)")
print(f"Breaks needed every {break_threshold_km}km: {breaks_needed}")
print(f"Break locations:")

for b in range(1, breaks_needed + 1):
    km = b * break_threshold_km
    time = km / avg_speed
    time_with_breaks = time + (b * break_duration)
    print(f"  Break #{b}: at {km} km, after {time:.2f}h driving, total time {time_with_breaks:.2f}h")

# The problem: where can these breaks be placed?
print(f"\n{'='*80}")
print(f"THE PROBLEM")
print(f"{'='*80}")

print(f"\nThis edge goes from Node 6 to Node 7 (1038km in one jump)")
print(f"There are NO intermediate nodes to place the {breaks_needed} breaks!")
print(f"\nWhat the preprocessing does:")
print(f"  - It assigns ALL {breaks_needed} breaks to Node 7 (the destination)")
print(f"  - This creates {breaks_needed} separate constraints on travel_time at Node 7")

print(f"\n{'='*80}")
print(f"MODEL CONSTRAINTS AT NODE 7")
print(f"{'='*80}")

# Calculate what constraints are created
print(f"\nThe model creates these constraints for Node 7:")
for b in range(1, breaks_needed + 1):
    km = b * break_threshold_km
    time = km / avg_speed
    time_with_breaks = time + (b * break_duration)
    print(f"  Constraint #{b}: travel_time[..., node_7, ...] >= {time_with_breaks:.2f}h × num_vehicles")

# The strongest constraint dominates
strongest = breaks_needed * break_threshold_km / avg_speed + breaks_needed * break_duration
print(f"\nThe strongest constraint requires: {strongest:.2f}h")
print(f"This is for traveling {breaks_needed * break_threshold_km} km")

# But the ACTUAL edge is longer
actual_time = giant_edge / avg_speed
actual_with_breaks = actual_time + (breaks_needed * break_duration)
print(f"\nBut the ACTUAL edge is {giant_edge:.1f} km")
print(f"Actual driving time: {actual_time:.2f}h")
print(f"With {breaks_needed} breaks: {actual_with_breaks:.2f}h")

# The gap
gap = actual_with_breaks - strongest
print(f"\nGap between constraint and reality: {gap:.2f}h")
print(f"This gap might be part of the extra_break_time issue")

print(f"\n{'='*80}")
print(f"WHY 736h EXTRA_BREAK_TIME?")
print(f"{'='*80}")

print(f"""
The 736h is likely NOT from this one edge, but from:

1. ACCUMULATED over multiple years/vehicles/generations
   - If this route is used by 10 vehicles × 11 years = 110 instances
   - Each needing ~6-7h of slack
   - Total: ~700h cumulative

2. OR the travel_time variable is accumulating across the path
   - travel_time grows as you traverse nodes
   - At node 7, it includes ALL previous travel + this giant edge
   - Multiple constraints at node 7 might require massive slack

3. OR there's an interaction with the penalty:
   - extra_break_time penalty (3.0 × VoT) is too weak
   - Model finds it cheaper to use huge slack than to avoid this route

Let's check the mandatory breaks data for this path...
""")

# Load mandatory breaks for path 2111
case_folder = "case_20251106_112933"
import os
breaks_file = os.path.join("input_data", case_folder, "MandatoryBreaks.yaml")

if os.path.exists(breaks_file):
    with open(breaks_file, 'r') as f:
        all_breaks = yaml.safe_load(f)

    path_2111_breaks = [b for b in all_breaks if b['path_id'] == 2111]

    print(f"\n{'='*80}")
    print(f"MANDATORY BREAKS DATA FOR PATH 2111")
    print(f"{'='*80}")
    print(f"\nFound {len(path_2111_breaks)} mandatory break entries:")

    for i, mb in enumerate(path_2111_breaks, 1):
        print(f"\nBreak {i}:")
        print(f"  break_number: {mb['break_number']}")
        print(f"  latest_node_idx: {mb['latest_node_idx']}")
        print(f"  latest_geo_id: {mb['latest_geo_id']}")
        print(f"  cumulative_distance: {mb['cumulative_distance']:.1f} km")
        print(f"  total_driving_time: {mb['total_driving_time']:.2f}h")
        print(f"  time_with_breaks: {mb['time_with_breaks']:.2f}h")

    # Check if multiple breaks at same node
    from collections import defaultdict
    breaks_by_node = defaultdict(list)
    for mb in path_2111_breaks:
        breaks_by_node[mb['latest_geo_id']].append(mb)

    print(f"\n{'='*80}")
    print(f"BREAKS BY NODE")
    print(f"{'='*80}")
    for geo_id, breaks in breaks_by_node.items():
        print(f"\nNode {geo_id}: {len(breaks)} break(s)")
        for mb in breaks:
            print(f"  - Break #{mb['break_number']}: {mb['time_with_breaks']:.2f}h at {mb['cumulative_distance']:.1f}km")

        if len(breaks) > 1:
            print(f"  [!] MULTIPLE BREAKS AT SAME NODE!")
            print(f"  This creates {len(breaks)} constraints on the same travel_time variable")

else:
    print("\n[INFO] MandatoryBreaks.yaml not found")

print(f"\n{'='*80}")
print(f"SOLUTION")
print(f"{'='*80}")

print("""
Option 1: FIX THE NETWORK DATA
  - If this 1038km edge is an error, add intermediate nodes
  - If it's a ferry, it should be handled differently (no driver breaks on ferry)

Option 2: FILTER THIS PATH
  - Exclude paths with edges > 800km from the analysis
  - These are likely ferries or data errors

Option 3: IMPROVE PREPROCESSING
  - When an edge is > 720km (needs 2+ breaks), create virtual intermediate nodes
  - Distribute breaks across these virtual nodes instead of stacking at one node

Option 4: ADD UPPER BOUND
  - Set maximum extra_break_time to 10h per path
  - This prevents unrealistic slack accumulation

Recommended: Check if node-to-node connection is a FERRY
  - Ferry routes shouldn't have driver break requirements
  - Add ferry flag to edges and skip mandatory breaks for ferries
""")
