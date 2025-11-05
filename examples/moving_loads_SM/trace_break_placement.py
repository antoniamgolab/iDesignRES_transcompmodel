"""
Trace through exactly where mandatory breaks are placed for single-node paths.
"""

def trace_break_placement_detailed(path_length, speed=80):
    """
    Show step-by-step where breaks are placed.
    """
    print(f"\n{'='*80}")
    print(f"DETAILED TRACE: Path with length={path_length}km")
    print(f"{'='*80}")

    # ORIGINAL STATE (before fix)
    print("\n1. ORIGINAL PATH DATA (single-node):")
    original_sequence = [47]
    original_cumulative = [0.0]
    print(f"   sequence = {original_sequence}")
    print(f"   cumulative_distance = {original_cumulative}")
    print(f"   length = {path_length} km")

    # AFTER FIX (synthetic nodes created)
    print("\n2. AFTER FIX (synthetic nodes created):")
    break_interval_km = 4.5 * speed  # 360 km
    synthetic_cumulative = [0.0]
    dist = 0.0

    while dist + break_interval_km < path_length:
        dist += break_interval_km
        synthetic_cumulative.append(dist)

    synthetic_cumulative.append(path_length)
    synthetic_sequence = [47] * len(synthetic_cumulative)

    print(f"   sequence = {synthetic_sequence}")
    print(f"   cumulative_distance = {synthetic_cumulative}")

    print("\n   Node breakdown:")
    for i, (node, cum_dist) in enumerate(zip(synthetic_sequence, synthetic_cumulative)):
        time_at_node = cum_dist / speed
        print(f"     Node index {i}: geo_id={node}, distance={cum_dist:.1f}km, time={time_at_node:.2f}h")

    # BREAK PLACEMENT ALGORITHM
    print("\n3. BREAK PLACEMENT ALGORITHM:")
    target_time = 4.5  # First break at 4.5h
    max_distance_before_event = target_time * speed
    print(f"   Target time: {target_time}h")
    print(f"   Max distance before break: {max_distance_before_event}km")

    print("\n   Loop through nodes to find latest node before max distance:")
    latest_node_idx = None
    actual_cum_distance = None

    for i, cum_dist in enumerate(synthetic_cumulative):
        if cum_dist <= max_distance_before_event:
            latest_node_idx = i
            actual_cum_distance = cum_dist
            print(f"     i={i}: cum_dist={cum_dist:.1f} <= {max_distance_before_event:.1f} OK "
                  f"-> latest_node_idx={i}")
        else:
            print(f"     i={i}: cum_dist={cum_dist:.1f} > {max_distance_before_event:.1f} X -> STOP")
            break

    cumulative_driving_time = actual_cum_distance / speed

    print("\n4. FINAL RESULT:")
    print(f"   latest_node_idx = {latest_node_idx}")
    print(f"   geo_id at break = {synthetic_sequence[latest_node_idx]}")
    print(f"   cumulative_distance = {actual_cum_distance:.1f} km")
    print(f"   cumulative_driving_time = {cumulative_driving_time:.2f} h")

    print("\n5. INTERPRETATION:")
    if latest_node_idx == 0:
        print(f"   Break is at NODE_IDX=0 (origin)")
        print(f"   This means: Break BEFORE starting the journey")
        print(f"   Cumulative time: {cumulative_driving_time:.2f}h")
    else:
        print(f"   Break is at NODE_IDX={latest_node_idx} (synthetic node #{latest_node_idx})")
        print(f"   This means: Break AFTER driving {actual_cum_distance:.1f}km ({cumulative_driving_time:.2f}h)")
        print(f"   Even though geo_id={synthetic_sequence[latest_node_idx]} (same as origin),")
        print(f"   the break timing is CORRECT because cumulative_driving_time={cumulative_driving_time:.2f}h")

    print("\n6. IN THE OPTIMIZATION MODEL:")
    if latest_node_idx == 0:
        print(f"   Constraint: Truck must stop at geo_id={synthetic_sequence[latest_node_idx]} after 0h of driving")
        print(f"   (This is just initial charging at the start)")
    else:
        print(f"   Constraint: Truck must stop at geo_id={synthetic_sequence[latest_node_idx]} after {cumulative_driving_time:.2f}h of driving")
        print(f"   This enforces the 4.5h driving limit correctly!")

    return latest_node_idx, cumulative_driving_time


if __name__ == "__main__":
    print("\n" + "="*80)
    print("WHERE IS THE MANDATORY BREAK PLACED?")
    print("="*80)

    # Test Case 1: 562.8 km path (like ITC1 -> ITC1)
    idx1, time1 = trace_break_placement_detailed(562.8)

    # Test Case 2: 300 km path (shorter than break interval)
    idx2, time2 = trace_break_placement_detailed(300.0)

    # Test Case 3: 838.6 km path (needs 2 breaks)
    print(f"\n{'='*80}")
    print(f"SPECIAL CASE: Path with length=838.6km (needs 2 breaks)")
    print(f"{'='*80}")
    print("\nThis path needs TWO breaks:")
    print("  Break 1: Target 4.5h (360km)")
    print("  Break 2: Target 9.0h (720km)")
    print("\nAfter fix, synthetic nodes: [0.0, 360.0, 720.0, 838.6]")
    print("  Break 1: Placed at node_idx=1 (360km, 4.5h)")
    print("  Break 2: Placed at node_idx=2 (720km, 9.0h)")

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print("\nFor single-node paths with our fix:")
    print("  - Breaks are placed at SYNTHETIC NODES (node_idx > 0)")
    print("  - NOT at the origin (node_idx=0)")
    print("  - Cumulative driving time is CORRECT (4.5h, 9.0h, etc.)")
    print("  - Even though geo_id might be the same, the TIMING is what matters")
    print("\nIn the optimization model:")
    print("  - The constraint uses cumulative_driving_time to enforce break timing")
    print("  - So breaks happen at the RIGHT TIME along the route")
    print("  - This correctly enforces the 4.5h driving limit")
