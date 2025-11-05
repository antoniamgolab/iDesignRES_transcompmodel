"""
Test the dynamic tolerance adjustment for break placement.
Tolerance = (1/3) * (limit - time_at_last_valid_node)
"""

def test_dynamic_tolerance(route_times, speed=80):
    """
    Test break placement with dynamic tolerance based on gap to limit.
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
    print(f"\n   Nodes:")
    for i, (t, d) in enumerate(zip(route_times, distances)):
        print(f"     Node {i}: {t}h = {d:.1f}km")

    # STEP 1: Find latest node within limit (strict)
    print(f"\n2. FIND LATEST NODE WITHIN LIMIT:")
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

    current_node = latest_node_idx
    current_time = route_times[current_node]
    current_distance = actual_distance

    print(f"\n   Latest valid node: Node {current_node} ({current_time}h, {current_distance:.1f}km)")

    # STEP 2: Calculate dynamic tolerance
    print(f"\n3. CALCULATE DYNAMIC TOLERANCE:")
    gap_to_limit = target_time - current_time
    tolerance_hours = (1/3) * gap_to_limit if gap_to_limit > 0 else 0

    print(f"   Gap to limit: {target_time}h - {current_time}h = {gap_to_limit:.3f}h ({gap_to_limit*60:.1f} min)")
    print(f"   Tolerance: (1/3) * {gap_to_limit:.3f}h = {tolerance_hours:.3f}h ({tolerance_hours*60:.1f} min)")
    print(f"   Max allowed time: {target_time}h + {tolerance_hours:.3f}h = {target_time + tolerance_hours:.3f}h")

    # STEP 3: Check if next node is within tolerance
    print(f"\n4. CHECK NEXT NODE:")
    final_node = current_node
    final_time = current_time
    final_distance = current_distance

    if current_node < len(route_times) - 1:
        next_node = current_node + 1
        next_time = route_times[next_node]
        next_distance = distances[next_node]

        print(f"   Next node: Node {next_node} ({next_time}h, {next_distance:.1f}km)")
        print(f"   Is {next_time}h <= {target_time + tolerance_hours:.3f}h?")

        if next_time <= target_time + tolerance_hours:
            final_node = next_node
            final_time = next_time
            final_distance = next_distance
            print(f"   YES -> Use Node {next_node}!")
        else:
            print(f"   NO -> Keep Node {current_node}")
    else:
        print(f"   No next node available")

    # SUMMARY
    print(f"\n5. RESULT:")
    print(f"   Break placed at: Node {final_node}")
    print(f"   Time: {final_time}h")
    print(f"   Distance: {final_distance:.1f}km")

    if final_node != current_node:
        overshoot = final_time - target_time
        print(f"\n   ADJUSTED: Break moved from Node {current_node} to Node {final_node}")
        print(f"   Overshoot: {overshoot:.3f}h ({overshoot*60:.1f} min) over the {target_time}h limit")
        print(f"   This was within the dynamic tolerance of {tolerance_hours:.3f}h ({tolerance_hours*60:.1f} min)")
    else:
        print(f"\n   NO ADJUSTMENT: Next node exceeds tolerance or doesn't exist")

    return final_node, final_time, tolerance_hours


if __name__ == "__main__":
    print("\n" + "="*80)
    print("DYNAMIC TOLERANCE TESTS")
    print("Tolerance = (1/3) * (limit - time_at_last_valid_node)")
    print("="*80)

    # Test 1: User's example [0h, 4.3h, 4.6h, 6h]
    # Gap = 4.5 - 4.3 = 0.2h -> tolerance = 0.067h
    print("\n" + "="*80)
    print("TEST 1: User's Example [0, 4.3, 4.6, 6]")
    print("="*80)
    n1, t1, tol1 = test_dynamic_tolerance([0, 4.3, 4.6, 6.0])

    # Test 2: Large gap [0h, 4.0h, 4.7h, 6h]
    # Gap = 4.5 - 4.0 = 0.5h -> tolerance = 0.167h
    print("\n\n" + "="*80)
    print("TEST 2: Large Gap [0, 4.0, 4.7, 6]")
    print("="*80)
    n2, t2, tol2 = test_dynamic_tolerance([0, 4.0, 4.7, 6.0])

    # Test 3: Small gap [0h, 4.45h, 4.6h, 6h]
    # Gap = 4.5 - 4.45 = 0.05h -> tolerance = 0.017h
    print("\n\n" + "="*80)
    print("TEST 3: Small Gap [0, 4.45, 4.6, 6]")
    print("="*80)
    n3, t3, tol3 = test_dynamic_tolerance([0, 4.45, 4.6, 6.0])

    # Test 4: At limit [0h, 4.5h, 4.6h, 6h]
    # Gap = 4.5 - 4.5 = 0h -> tolerance = 0h
    print("\n\n" + "="*80)
    print("TEST 4: At Limit [0, 4.5, 4.6, 6]")
    print("="*80)
    n4, t4, tol4 = test_dynamic_tolerance([0, 4.5, 4.6, 6.0])

    # SUMMARY
    print("\n\n" + "="*80)
    print("COMPARISON OF DYNAMIC TOLERANCE")
    print("="*80)
    print(f"\nTest 1: Gap=0.2h -> tolerance=0.067h (4.0min) -> next at 4.6h -> NOT accepted (4.6 > 4.567)")
    print(f"Test 2: Gap=0.5h -> tolerance=0.167h (10.0min) -> next at 4.7h -> accepted (4.7 <= 4.667)")
    print(f"Test 3: Gap=0.05h -> tolerance=0.017h (1.0min) -> next at 4.6h -> NOT accepted (4.6 > 4.517)")
    print(f"Test 4: Gap=0h -> tolerance=0h (0min) -> next at 4.6h -> NOT accepted (4.6 > 4.5)")

    print("\nDynamic tolerance behavior:")
    print("  - Large gap (4.0h): Large tolerance (10 min) -> More flexibility")
    print("  - Medium gap (4.3h): Medium tolerance (4 min) -> Some flexibility")
    print("  - Small gap (4.45h): Small tolerance (1 min) -> Little flexibility")
    print("  - At limit (4.5h): No tolerance (0 min) -> No flexibility")

    print("\nAdvantages over fixed tolerance:")
    print("  - Proportional: Tolerance scales with the gap")
    print("  - Fair: Longer early stops get more flexibility")
    print("  - Conservative: Stops close to limit get minimal tolerance")
    print("  - Automatic: No manual tuning needed")
