# MANDATORY BREAKS CALCULATION FOR SM-PREPROCESSING
# Based on EU driving regulations: 4.5 hours driving → 45 min break

import numpy as np

# Parameters
MAX_DRIVING_TIME = 4.5  # hours
BREAK_DURATION = 45 / 60  # 45 minutes in hours
AVERAGE_SPEED = 80  # km/h (adjust based on your speed data)

def calculate_mandatory_breaks(path, speed=80):
    """
    Calculate where mandatory breaks must be taken along a path.

    Parameters:
    -----------
    path : dict
        Path object with 'sequence' (list of nodes), 'cumulative_distance' (list of km),
        'id', and 'length' (total path length in km)
    speed : float
        Average travel speed in km/h

    Returns:
    --------
    list of dicts (one per break) with flat structure:
        'path_id': path identifier
        'path_length': total path length in km
        'total_driving_time': total driving time in hours for entire path (excluding breaks)
        'break_number': break number (1, 2, 3, ...)
        'latest_node_idx': index in path.sequence where break must occur by
        'latest_geo_id': geographic ID of the node
        'cumulative_distance': distance traveled up to this break point (km)
        'cumulative_driving_time': driving time up to this break point (hours, excluding breaks)
        'time_with_breaks': total elapsed time AFTER taking this break (hours)
    """

    sequence = path['sequence']
    cumulative_distance = path['cumulative_distance']
    path_id = path['id']
    total_length = path['length']

    # Calculate total driving time (no breaks)
    total_driving_time = total_length / speed

    # Calculate number of breaks required
    # After 4.5h driving → 1 break, after 9h → 2 breaks, etc.
    num_breaks_required = int(np.floor(total_driving_time / MAX_DRIVING_TIME))

    break_list = []

    for break_num in range(1, num_breaks_required + 1):
        # Maximum cumulative driving time before this break must occur
        max_time_before_break = break_num * MAX_DRIVING_TIME
        max_distance_before_break = max_time_before_break * speed

        # Find the latest node where this break can occur
        # (the node just before exceeding max_distance_before_break)
        latest_node_idx = None
        latest_geo_id = None
        actual_cum_distance = None

        for i, cum_dist in enumerate(cumulative_distance):
            if cum_dist <= max_distance_before_break:
                latest_node_idx = i
                latest_geo_id = sequence[i]['id'] if isinstance(sequence[i], dict) else sequence[i]
                actual_cum_distance = cum_dist
            else:
                break  # Exceeded max distance

        # If we couldn't find a node (shouldn't happen), use the last node
        if latest_node_idx is None and len(sequence) > 0:
            latest_node_idx = len(sequence) - 1
            latest_geo_id = sequence[latest_node_idx]['id'] if isinstance(sequence[latest_node_idx], dict) else sequence[latest_node_idx]
            actual_cum_distance = cumulative_distance[latest_node_idx] if latest_node_idx < len(cumulative_distance) else total_length

        # Calculate cumulative time at this point
        cumulative_driving_time = actual_cum_distance / speed

        # Total elapsed time including ALL breaks (including this one)
        # After break 1: driving_time + 1 break = driving + 0.75h
        # After break 2: driving_time + 2 breaks = driving + 1.5h
        time_with_breaks = cumulative_driving_time + break_num * BREAK_DURATION

        # Create flat entry - one per break
        break_list.append({
            'path_id': path_id,
            'path_length': total_length,
            'total_driving_time': total_driving_time,
            'break_number': break_num,
            'latest_node_idx': latest_node_idx,
            'latest_geo_id': latest_geo_id,
            'cumulative_distance': actual_cum_distance,
            'cumulative_driving_time': cumulative_driving_time,
            'time_with_breaks': time_with_breaks  # Total time AFTER taking this break
        })

    return break_list


def create_mandatory_breaks_list(path_list, speed=80):
    """
    Create a flat list of mandatory break information for all paths.

    Parameters:
    -----------
    path_list : list
        List of path objects
    speed : float
        Average travel speed in km/h

    Returns:
    --------
    list of dicts - flat structure, one entry per break across all paths
    Each dict contains: path_id, path_length, total_driving_time, break_number,
                        latest_node_idx, latest_geo_id, cumulative_distance,
                        cumulative_driving_time, time_with_breaks
    """

    mandatory_breaks_list = []

    for path in path_list:
        # Returns a list of break entries for this path
        breaks_for_path = calculate_mandatory_breaks(path, speed)
        # Extend (not append) to keep flat structure
        mandatory_breaks_list.extend(breaks_for_path)

    return mandatory_breaks_list


# EXAMPLE USAGE IN SM-PREPROCESSING.ipynb:
# ==========================================

# After you have created path_list, add this code:

"""
# Calculate mandatory breaks for all paths
speed = 80  # km/h - adjust based on your Speed data
mandatory_breaks_list = create_mandatory_breaks_list(path_list, speed=speed)

# Print summary
print(f"\\nMANDATORY BREAKS SUMMARY:")
print(f"="*80)
print(f"Total break entries: {len(mandatory_breaks_list)}")

# Group by path for display
from collections import defaultdict
breaks_by_path = defaultdict(list)
for entry in mandatory_breaks_list:
    breaks_by_path[entry['path_id']].append(entry)

for path_id, breaks in breaks_by_path.items():
    first_entry = breaks[0]
    print(f"\\nPath {path_id}:")
    print(f"  Length: {first_entry['path_length']:.2f} km")
    print(f"  Driving time: {first_entry['total_driving_time']:.2f} hours")
    print(f"  Breaks required: {len(breaks)}")

    if len(breaks) > 0:
        print(f"  Break locations:")
        for entry in breaks:
            print(f"    Break {entry['break_number']}: Latest at node {entry['latest_node_idx']} "
                  f"(geo_id={entry['latest_geo_id']}) at {entry['cumulative_distance']:.2f} km "
                  f"({entry['cumulative_driving_time']:.2f}h driving, "
                  f"{entry['time_with_breaks']:.2f}h with breaks)")

# Export to YAML for Julia model (already flat structure!)
import yaml
output_path = os.path.join(output_dir, 'MandatoryBreaks.yaml')
with open(output_path, 'w') as f:
    yaml.dump(mandatory_breaks_list, f, default_flow_style=False)

print(f"\\n✓ Saved {len(mandatory_breaks_list)} mandatory break entries to {output_path}")
"""

# ALTERNATIVE: Add breaks info directly to path objects
# ======================================================

"""
# If you want to add break information directly to each path object:

for path in path_list:
    breaks_for_path = calculate_mandatory_breaks(path, speed=80)

    # Add break information to path object
    path['mandatory_breaks'] = breaks_for_path  # List of break entries
    path['num_breaks_required'] = len(breaks_for_path)

print("✓ Added mandatory break information to all path objects")
"""


# EXAMPLE OUTPUT:
# ===============
# For a path of 361.9 km at 80 km/h:
# - Total driving time: 361.9 / 80 = 4.52 hours
# - Number of breaks: floor(4.52 / 4.5) = 1 break
# - Break must occur by: 4.5 * 80 = 360 km
# - Find node closest to but not exceeding 360 km

# For a path of 800 km at 80 km/h:
# - Total driving time: 800 / 80 = 10 hours
# - Number of breaks: floor(10 / 4.5) = 2 breaks
# - Break 1 must occur by: 360 km (4.5h)
# - Break 2 must occur by: 720 km (9.0h total driving)


# VERIFICATION EXAMPLE (matching your question):
# ===============================================
"""
Route: [1, 2, 3, 4, 5]
Assume distances: [0, 90, 180, 270, 360] km at node [1, 2, 3, 4, 5]
Speed: 80 km/h

At node 1: 0 km, 0h driving
At node 2: 90 km, 1.125h driving
At node 3: 180 km, 2.25h driving
At node 4: 270 km, 3.375h driving
At node 5: 360 km, 4.5h driving

Wait, that's only 4.5h, let's extend:
At node 6: 450 km, 5.625h driving
At node 7: 540 km, 6.75h driving
At node 8: 630 km, 7.875h driving
At node 9: 720 km, 9.0h driving

The function will find:
- Break 1: Must occur by 360 km (4.5h) → node 5
  - cumulative_driving_time = 4.5h
  - time_with_breaks = 4.5 + 1×0.75 = 5.25h ✓

- Break 2: Must occur by 720 km (9.0h) → node 9
  - cumulative_driving_time = 9.0h
  - time_with_breaks = 9.0 + 2×0.75 = 10.5h ✓

So yes, this matches your requirement:
- At node where 4.5h is reached: total time = 4.5h + 45min = 5.25h
- At node where 9.0h is reached: total time = 9.0h + 90min = 10.5h
"""


# TEST CODE (uncomment to test):
# ================================
"""
# Create a test path
test_path = {
    'id': 'test_path_1',
    'sequence': [
        {'id': 1}, {'id': 2}, {'id': 3}, {'id': 4}, {'id': 5},
        {'id': 6}, {'id': 7}, {'id': 8}, {'id': 9}
    ],
    'cumulative_distance': [0, 90, 180, 270, 360, 450, 540, 630, 720],
    'length': 720
}

# Calculate breaks
breaks_info = calculate_mandatory_breaks(test_path, speed=80)

print("TEST RESULTS:")
print(f"Path length: {breaks_info['total_length']} km")
print(f"Total driving time: {breaks_info['total_driving_time']:.2f} hours")
print(f"Breaks required: {breaks_info['num_breaks_required']}")
print()

for bn in breaks_info['break_nodes']:
    print(f"Break {bn['break_number']}:")
    print(f"  Latest node: {bn['latest_node_idx']} (geo_id={bn['latest_geo_id']})")
    print(f"  Distance: {bn['cumulative_distance']} km")
    print(f"  Driving time: {bn['cumulative_driving_time']:.2f}h")
    print(f"  Total time (with breaks): {bn['time_with_breaks']:.2f}h")
    print()

# Expected output:
# Break 1:
#   Latest node: 4 (geo_id=5)
#   Distance: 360 km
#   Driving time: 4.50h
#   Total time (with breaks): 5.25h

# Break 2:
#   Latest node: 8 (geo_id=9)
#   Distance: 720 km
#   Driving time: 9.00h
#   Total time (with breaks): 10.50h
"""
