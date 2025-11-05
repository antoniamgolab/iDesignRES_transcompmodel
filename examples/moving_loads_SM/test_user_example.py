"""
Test user's specific example: Route with nodes at [0h, 4.3h, 4.6h, 6h]
"""

def test_user_route_example():
    print("="*80)
    print("USER'S EXAMPLE: Route with nodes at [0h, 4.3h, 4.6h, 6h]")
    print("="*80)

    # Convert times to distances (at 80 km/h)
    speed = 80  # km/h
    times = [0, 4.3, 4.6, 6.0]
    distances = [t * speed for t in times]

    print("\n1. ROUTE DATA:")
    print(f"   Speed: {speed} km/h")
    print(f"   Node times: {times} hours")
    print(f"   Node distances: {[f'{d:.1f}' for d in distances]} km")
    print("\n   Node details:")
    for i, (t, d) in enumerate(zip(times, distances)):
        print(f"     Node {i}: {t}h = {d:.1f} km")

    # Simulate break placement algorithm
    print("\n2. BREAK PLACEMENT ALGORITHM:")
    target_time = 4.5  # First mandatory break at 4.5h
    max_distance = target_time * speed

    print(f"   Target break time: {target_time}h")
    print(f"   Max distance before break: {max_distance} km")

    print("\n   Loop through nodes to find LATEST node before max distance:")
    latest_node_idx = None
    actual_distance = None

    for i, dist in enumerate(distances):
        if dist <= max_distance:
            latest_node_idx = i
            actual_distance = dist
            actual_time = times[i]
            print(f"     Node {i}: {dist:.1f}km ({times[i]}h) <= {max_distance}km? "
                  f"YES -> latest_node_idx={i}")
        else:
            print(f"     Node {i}: {dist:.1f}km ({times[i]}h) <= {max_distance}km? "
                  f"NO -> STOP (exceeds limit)")
            break

    print("\n3. RESULT:")
    print(f"   Break placed at: node_idx={latest_node_idx}")
    print(f"   Cumulative distance: {actual_distance:.1f} km")
    print(f"   Cumulative driving time: {actual_time:.1f} h")

    print("\n4. INTERPRETATION:")
    print(f"   The driver must take a break at Node {latest_node_idx}")
    print(f"   This is BEFORE the 4.5h limit (at {actual_time}h)")
    print(f"   The algorithm finds the LATEST possible node that doesn't exceed 4.5h")

    print("\n5. WHY NOT NODE 2?")
    print(f"   Node 2 is at 4.6h ({distances[2]:.1f}km)")
    print(f"   This EXCEEDS the 4.5h limit ({max_distance}km)")
    print(f"   So the driver must stop earlier, at Node 1 (4.3h)")

    print("\n6. IN PRACTICE:")
    print(f"   - Driver leaves origin (Node 0) at time 0")
    print(f"   - Driver reaches Node 1 at 4.3h -> MUST take mandatory break here")
    print(f"   - Break duration: 0.75h (45 minutes)")
    print(f"   - Driver continues to Node 2 at 4.6h (0.3h more driving)")
    print(f"   - Driver reaches destination (Node 3) at 6h")

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"For route [0h, 4.3h, 4.6h, 6h]:")
    print(f"  Break is at Node 1 (4.3h, {distances[1]:.1f}km)")
    print(f"  NOT at Node 2 (4.6h would exceed the 4.5h limit)")
    print(f"\nThe algorithm ensures the driver stops BEFORE exceeding the legal limit.")


if __name__ == "__main__":
    test_user_route_example()

    print("\n\n" + "="*80)
    print("ADDITIONAL TEST: What if nodes were at [0h, 4.5h, 4.6h, 6h]?")
    print("="*80)

    speed = 80
    times2 = [0, 4.5, 4.6, 6.0]
    distances2 = [t * speed for t in times2]
    target_time = 4.5
    max_distance = target_time * speed

    print(f"\nNode times: {times2} hours")
    print(f"Node distances: {[f'{d:.1f}' for d in distances2]} km")
    print(f"Max distance before break: {max_distance} km")

    print("\nLoop through nodes:")
    for i, (t, d) in enumerate(zip(times2, distances2)):
        if d <= max_distance:
            print(f"  Node {i}: {d:.1f}km ({t}h) <= {max_distance}km? YES -> latest_node_idx={i}")
        else:
            print(f"  Node {i}: {d:.1f}km ({t}h) <= {max_distance}km? NO -> STOP")
            break

    print(f"\nResult: Break at Node 1 (EXACTLY at 4.5h, {distances2[1]:.1f}km)")
    print("The algorithm accepts nodes AT the limit (<=, not <)")
