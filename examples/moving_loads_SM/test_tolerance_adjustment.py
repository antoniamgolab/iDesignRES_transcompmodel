"""
Test the tolerance adjustment for break placement.
Shows the difference between strict and practical approaches.
"""

def test_with_tolerance(route_times, speed=80, tolerance_hours=0.2):
    """
    Test break placement with tolerance adjustment.
    """
    print("="*80)
    print(f"ROUTE: {route_times} hours")
    print("="*80)

    # Convert to distances
    distances = [t * speed for t in route_times]
    target_time = 4.5
    max_distance = target_time * speed

    print(f"\n1. ROUTE DETAILS:")
    print(f"   Speed: {speed} km/h")
    print(f"   Target break time: {target_time}h (max distance: {max_distance}km)")
    print(f"   Tolerance: {tolerance_hours}h ({tolerance_hours*60:.0f} minutes)")
    print(f"\n   Nodes:")
    for i, (t, d) in enumerate(zip(route_times, distances)):
        print(f"     Node {i}: {t}h = {d:.1f}km")

    # STEP 1: Find latest node within limit (strict)
    print(f"\n2. STRICT ALGORITHM (no tolerance):")
    latest_node_idx = None
    actual_distance = None

    for i, dist in enumerate(distances):
        if dist <= max_distance:
            latest_node_idx = i
            actual_distance = dist
            print(f"   Node {i}: {dist:.1f}km <= {max_distance}km? YES -> latest={i}")
        else:
            print(f"   Node {i}: {dist:.1f}km <= {max_distance}km? NO -> STOP")
            break

    strict_node = latest_node_idx
    strict_distance = actual_distance
    strict_time = route_times[strict_node]

    print(f"\n   Strict result: Node {strict_node} ({strict_time}h, {strict_distance:.1f}km)")

    # STEP 2: Check if next node is within tolerance
    print(f"\n3. TOLERANCE ADJUSTMENT:")
    tolerance_node = strict_node
    tolerance_distance = strict_distance
    tolerance_time = strict_time

    if strict_node < len(route_times) - 1:
        next_node = strict_node + 1
        next_distance = distances[next_node]
        next_time = route_times[next_node]

        print(f"   Next node: Node {next_node} ({next_time}h, {next_distance:.1f}km)")
        print(f"   Is next node within tolerance?")
        print(f"     {next_time}h <= {target_time}h + {tolerance_hours}h = {target_time + tolerance_hours}h?")

        if next_time <= target_time + tolerance_hours:
            tolerance_node = next_node
            tolerance_distance = next_distance
            tolerance_time = next_time
            print(f"     YES -> Use Node {next_node} instead!")
        else:
            print(f"     NO -> Keep Node {strict_node}")
    else:
        print(f"   No next node available (already at last node)")

    print(f"\n   Final result: Node {tolerance_node} ({tolerance_time}h, {tolerance_distance:.1f}km)")

    # SUMMARY
    print(f"\n4. COMPARISON:")
    print(f"   Strict approach:     Node {strict_node} at {strict_time}h")
    print(f"   With tolerance:      Node {tolerance_node} at {tolerance_time}h")

    if tolerance_node != strict_node:
        time_diff = tolerance_time - target_time
        print(f"\n   CHANGE: Break moved to Node {tolerance_node}")
        print(f"   This is {time_diff:.2f}h ({time_diff*60:.1f} min) over the {target_time}h limit")
        print(f"   But within the {tolerance_hours}h ({tolerance_hours*60:.0f} min) tolerance")
        print(f"   MORE PRACTICAL: Avoids stopping at {strict_time}h when next stop is only {tolerance_time - strict_time:.1f}h away")
    else:
        print(f"\n   NO CHANGE: Next node exceeds tolerance or doesn't exist")

    return tolerance_node, tolerance_time


if __name__ == "__main__":
    print("\n" + "="*80)
    print("TOLERANCE ADJUSTMENT TESTS")
    print("="*80)

    # Test 1: User's example [0h, 4.3h, 4.6h, 6h]
    print("\n" + "="*80)
    print("TEST 1: User's Example")
    print("="*80)
    node1, time1 = test_with_tolerance([0, 4.3, 4.6, 6.0], tolerance_hours=0.2)

    # Test 2: What if next node is way over? [0h, 4.3h, 5.0h, 6h]
    print("\n\n" + "="*80)
    print("TEST 2: Next Node Too Far Over")
    print("="*80)
    node2, time2 = test_with_tolerance([0, 4.3, 5.0, 6.0], tolerance_hours=0.2)

    # Test 3: What if node is exactly at limit? [0h, 4.5h, 4.6h, 6h]
    print("\n\n" + "="*80)
    print("TEST 3: Node Exactly at Limit")
    print("="*80)
    node3, time3 = test_with_tolerance([0, 4.5, 4.6, 6.0], tolerance_hours=0.2)

    # Test 4: Tight spacing [0h, 4.4h, 4.55h, 6h]
    print("\n\n" + "="*80)
    print("TEST 4: Tight Node Spacing")
    print("="*80)
    node4, time4 = test_with_tolerance([0, 4.4, 4.55, 6.0], tolerance_hours=0.2)

    # SUMMARY
    print("\n\n" + "="*80)
    print("SUMMARY OF TOLERANCE BEHAVIOR")
    print("="*80)
    print("\nWith 0.2h (12 minute) tolerance:")
    print("  Test 1 [0, 4.3, 4.6, 6]: Break at 4.6h (adjusted from 4.3h)")
    print("  Test 2 [0, 4.3, 5.0, 6]: Break at 4.3h (5.0h too far over)")
    print("  Test 3 [0, 4.5, 4.6, 6]: Break at 4.6h (adjusted from 4.5h)")
    print("  Test 4 [0, 4.4, 4.55, 6]: Break at 4.55h (adjusted from 4.4h)")

    print("\nThe tolerance makes break placement more practical:")
    print("  - Avoids stopping too early when next node is close")
    print("  - Accepts small violations (up to 12 min) for practicality")
    print("  - Still prevents large violations of the 4.5h limit")

    print("\nYou can adjust TOLERANCE_HOURS in SM_preprocessing.py:")
    print("  - 0.0 = Strict (never exceed 4.5h)")
    print("  - 0.1 = Allow 6 minutes over")
    print("  - 0.2 = Allow 12 minutes over (DEFAULT)")
    print("  - 0.5 = Allow 30 minutes over")
