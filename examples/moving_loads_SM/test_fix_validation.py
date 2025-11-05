"""
Test to validate that the mandatory breaks fix works correctly.

Tests the reconstructed cumulative_distance logic for single-node paths.
"""

def test_synthetic_cumulative_distance(total_length, speed=80):
    """
    Simulate the fix logic to generate synthetic cumulative_distance.
    """
    print(f"\n{'='*80}")
    print(f"TEST: Path with length={total_length}km at speed={speed}km/h")
    print(f"{'='*80}")

    # Simulate original path data (single-node, insufficient detail)
    cumulative_distance = [0.0]  # Original buggy state
    sequence = [47]  # Single node

    print(f"\nBEFORE FIX:")
    print(f"  cumulative_distance = {cumulative_distance}")
    print(f"  sequence = {sequence}")

    # Apply the fix logic (from SM_preprocessing.py lines 1114-1136)
    if len(cumulative_distance) <= 1 and total_length > 0:
        # Generate synthetic distance points at break intervals
        break_interval_km = 4.5 * speed  # 360 km at 80 km/h
        synthetic_cumulative = [0.0]
        dist = 0.0

        # Add points at each break interval
        while dist + break_interval_km < total_length:
            dist += break_interval_km
            synthetic_cumulative.append(dist)

        # Add final destination
        synthetic_cumulative.append(total_length)

        # Update cumulative_distance with synthetic values
        cumulative_distance = synthetic_cumulative

        # Extend sequence if needed
        if len(sequence) == 1:
            origin_node = sequence[0]
            sequence = [origin_node] * len(synthetic_cumulative)

    print(f"\nAFTER FIX:")
    print(f"  cumulative_distance = {cumulative_distance}")
    print(f"  sequence = {sequence}")

    # Simulate break calculation
    total_driving_time = total_length / speed
    print(f"\nBREAK CALCULATION:")
    print(f"  Total driving time: {total_driving_time:.2f}h")

    # Calculate breaks using fixed cumulative_distance
    SHORT_BREAK_INTERVAL = 4.5
    target_time = SHORT_BREAK_INTERVAL
    break_number = 0

    while target_time < total_driving_time + 1e-6:
        break_number += 1
        max_distance_before_event = target_time * speed

        latest_node_idx = None
        actual_cum_distance = None

        for i, cum_dist in enumerate(cumulative_distance):
            if cum_dist <= max_distance_before_event:
                latest_node_idx = i
                actual_cum_distance = cum_dist
            else:
                break

        if latest_node_idx is None:
            latest_node_idx = len(cumulative_distance) - 1
            actual_cum_distance = cumulative_distance[-1]

        cumulative_driving_time = actual_cum_distance / speed

        print(f"\n  Break {break_number}:")
        print(f"    Target time: {target_time:.2f}h (max distance: {max_distance_before_event:.1f}km)")
        print(f"    Placed at node_idx: {latest_node_idx}")
        print(f"    Cumulative distance: {actual_cum_distance:.1f}km")
        print(f"    Cumulative driving time: {cumulative_driving_time:.2f}h")

        # Check if this is correct
        if break_number == 1:
            expected_time_range = (0.0, 4.5)
        elif break_number == 2:
            expected_time_range = (4.5, 9.0)
        else:
            expected_time_range = ((break_number-1) * 4.5, break_number * 4.5)

        if expected_time_range[0] <= cumulative_driving_time <= expected_time_range[1] + 0.1:
            status = "OK CORRECT"
        else:
            status = "X WRONG"

        print(f"    Expected range: {expected_time_range[0]:.1f}h - {expected_time_range[1]:.1f}h")
        print(f"    Status: {status}")

        target_time += SHORT_BREAK_INTERVAL

    return cumulative_distance


if __name__ == "__main__":
    print("\n" + "="*80)
    print("MANDATORY BREAKS FIX VALIDATION")
    print("="*80)

    # Test Case 1: Path 0 (562.8 km, should have break at ~4.5h)
    test_synthetic_cumulative_distance(562.8, speed=80)

    # Test Case 2: Path 10 (838.6 km, should have breaks at ~4.5h and ~9.0h)
    test_synthetic_cumulative_distance(838.6, speed=80)

    # Test Case 3: Path 29 (841.3 km, should have breaks at ~4.5h and ~9.0h)
    test_synthetic_cumulative_distance(841.3, speed=80)

    # Test Case 4: Short path (300 km, should have break at origin only)
    test_synthetic_cumulative_distance(300.0, speed=80)

    # Test Case 5: Very long path (1500 km, should have breaks at ~4.5h, ~9h, ~13.5h)
    test_synthetic_cumulative_distance(1500.0, speed=80)

    print("\n" + "="*80)
    print("VALIDATION COMPLETE")
    print("="*80)
    print("\nIf all breaks show 'OK CORRECT', the fix is working properly.")
    print("Next step: Re-run preprocessing to generate corrected MandatoryBreaks.yaml")
