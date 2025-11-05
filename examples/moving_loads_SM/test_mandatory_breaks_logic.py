"""
Test the _calculate_mandatory_breaks_advanced function with user's example.

User's example:
- Travel times at nodes: [0h (origin), 0.5h, 1.5h, 3h, 4.2h, 5.4h (destination)]
- With a 4.5h limit, the break should be at the 4.2h node
"""

def _calculate_mandatory_breaks_advanced_test(path, speed=80):
    """
    Test version of the function from SM_preprocessing.py (lines 1090-1198)
    """
    sequence = path['sequence']
    cumulative_distance = path['cumulative_distance']
    path_id = path['id']
    total_length = path['length']

    # 1. Compute total travel time (hours)
    total_driving_time = total_length / speed

    # 2. Determine number of drivers based on EU rule
    num_drivers = 1 if total_driving_time <= 54 else 2

    # 3. Regulatory constants
    SHORT_BREAK_INTERVAL = 4.5       # hours between breaks
    SHORT_BREAK_DURATION = 0.75      # 45 minutes
    DAILY_DRIVING_LIMIT = 9 * num_drivers
    DAILY_REST_DURATION = 9          # hours
    MAX_DRIVING_TIME = DAILY_DRIVING_LIMIT

    # 4. Initialize counters
    break_list = []
    break_number = 0

    # 5. Generate target stop times (in hours of driving)
    target_time = SHORT_BREAK_INTERVAL
    daily_counter = 0.0

    print(f"\n{'='*80}")
    print(f"TESTING PATH {path_id}")
    print(f"{'='*80}")
    print(f"Total length: {total_length:.1f} km")
    print(f"Total driving time: {total_driving_time:.2f} hours")
    print(f"Number of drivers: {num_drivers}")
    print(f"\nNode sequence and cumulative distances:")
    for i, (node, dist) in enumerate(zip(sequence, cumulative_distance)):
        time_at_node = dist / speed
        print(f"  Node {i}: geo_id={node}, distance={dist:.1f} km, time={time_at_node:.2f}h")

    print(f"\n{'='*80}")
    print("BREAK CALCULATION")
    print(f"{'='*80}")

    while target_time < total_driving_time + 1e-6:
        print(f"\n--- Break {break_number + 1} ---")
        print(f"Target time: {target_time:.2f}h")

        # Decide event type
        if daily_counter + SHORT_BREAK_INTERVAL > MAX_DRIVING_TIME:
            event_type = 'R'
            event_name = 'rest'
            event_duration = DAILY_REST_DURATION
            charging_type = 'slow'
            daily_counter = 0.0
        else:
            event_type = 'B'
            event_name = 'break'
            event_duration = SHORT_BREAK_DURATION
            charging_type = 'fast'
            daily_counter += SHORT_BREAK_INTERVAL

        break_number += 1

        # Find corresponding node index for this event
        max_distance_before_event = target_time * speed
        print(f"Max distance before event: {max_distance_before_event:.1f} km")

        latest_node_idx = None
        latest_geo_id = None
        actual_cum_distance = None

        for i, cum_dist in enumerate(cumulative_distance):
            if cum_dist <= max_distance_before_event:
                latest_node_idx = i
                node = sequence[i]
                latest_geo_id = node if isinstance(node, int) else node['id']
                actual_cum_distance = cum_dist
                print(f"  Checking node {i}: dist={cum_dist:.1f} <= {max_distance_before_event:.1f} OK -> latest_node_idx={i}")
            else:
                print(f"  Checking node {i}: dist={cum_dist:.1f} > {max_distance_before_event:.1f} X -> STOP")
                break

        # Safety fallback
        if latest_node_idx is None and len(sequence) > 0:
            latest_node_idx = len(sequence) - 1
            node = sequence[latest_node_idx]
            latest_geo_id = node if isinstance(node, int) else node['id']
            actual_cum_distance = cumulative_distance[-1]
            print(f"  FALLBACK: Using last node {latest_node_idx}")

        cumulative_driving_time = actual_cum_distance / speed
        time_with_breaks = cumulative_driving_time + event_duration

        print(f"\nResult:")
        print(f"  latest_node_idx: {latest_node_idx}")
        print(f"  latest_geo_id: {latest_geo_id}")
        print(f"  actual_cum_distance: {actual_cum_distance:.1f} km")
        print(f"  cumulative_driving_time: {cumulative_driving_time:.2f}h")
        print(f"  event_type: {event_type}")

        # Append entry
        break_list.append({
            'path_id': path_id,
            'path_length': total_length,
            'total_driving_time': total_driving_time,
            'num_drivers': num_drivers,
            'break_number': break_number,
            'event_type': event_type,
            'event_name': event_name,
            'latest_node_idx': latest_node_idx,
            'latest_geo_id': latest_geo_id,
            'cumulative_distance': actual_cum_distance,
            'cumulative_driving_time': cumulative_driving_time,
            'time_with_breaks': time_with_breaks,
            'charging_type': charging_type
        })

        # Increment target_time and continue
        target_time += SHORT_BREAK_INTERVAL

    return break_list


# Test with user's example
test_path = {
    'id': 'test_route',
    'sequence': [1, 2, 3, 4, 5, 6],  # 6 nodes
    'cumulative_distance': [0, 40, 120, 240, 336, 432],  # km (corresponds to times 0, 0.5, 1.5, 3, 4.2, 5.4h at 80 km/h)
    'length': 432  # Total distance
}

print("\n" + "="*80)
print("TEST: User's Example")
print("="*80)
print("Expected behavior:")
print("  - With 4.5h limit and nodes at [0h, 0.5h, 1.5h, 3h, 4.2h, 5.4h]")
print("  - Break should be at 4.2h node (node index 4)")
print("="*80)

breaks = _calculate_mandatory_breaks_advanced_test(test_path, speed=80)

print("\n" + "="*80)
print("SUMMARY OF BREAKS")
print("="*80)
for b in breaks:
    print(f"Break {b['break_number']}: "
          f"node_idx={b['latest_node_idx']}, "
          f"geo_id={b['latest_geo_id']}, "
          f"cum_dist={b['cumulative_distance']:.1f}km, "
          f"cum_time={b['cumulative_driving_time']:.2f}h, "
          f"type={b['event_type']}")

print("\n" + "="*80)
print("VERIFICATION")
print("="*80)
if len(breaks) > 0:
    first_break = breaks[0]
    if first_break['latest_node_idx'] == 4:
        print("OK CORRECT: First break is at node index 4 (the 4.2h node)")
        print(f"  cumulative_driving_time = {first_break['cumulative_driving_time']:.2f}h")
        print(f"  This is the latest node before exceeding 4.5h")
    else:
        print(f"X WRONG: First break is at node index {first_break['latest_node_idx']}")
        print(f"  Expected: node index 4")
        print(f"  cumulative_driving_time = {first_break['cumulative_driving_time']:.2f}h")
else:
    print("X ERROR: No breaks generated!")
