"""
Fix for spatial_flex_range_list generation

This fixes the issue where all 70 subsets are created even when
the driving range covers the entire path.

CORRECTED LOGIC:
- If driving range >= total path distance: Create only 1 subset with all nodes
- If driving range < total path distance: Create maximal subsets from each starting position
"""

# Replace the section starting from "for tech_id, year_ranges in tech_ranges.items():"

CORRECTED_CODE = """
    for tech_id, year_ranges in tech_ranges.items():
        for g, max_range in year_ranges:
            # Build only maximal consecutive subsets that fit within range
            # A maximal subset is one where adding the next edge would exceed max_range
            valid_subsets = []

            # Check if entire path fits within driving range
            total_path_distance = sum(dist for _, dist in edges_list)

            if total_path_distance <= max_range:
                # Entire path fits - create only ONE subset with all edges
                valid_subsets.append(tuple(edges_list))
            else:
                # Path doesn't fit - create maximal subsets from each starting position
                start_idx = 0
                while start_idx < len(edges_list):
                    current_distance = 0
                    current_subset = []

                    # Extend from start_idx as far as possible within max_range
                    for end_idx in range(start_idx, len(edges_list)):
                        edge, distance = edges_list[end_idx]

                        # Check if we can add this edge
                        if current_distance + distance <= max_range:
                            current_subset.append((edge, distance))
                            current_distance += distance
                        else:
                            # Cannot add this edge, stop here
                            break

                    # Add the maximal subset starting from start_idx
                    if current_subset:
                        valid_subsets.append(tuple(current_subset))

                    # Move to next starting position
                    start_idx += 1

            # Create entries with proper IDs for each valid subset
            for subset_idx, subset in enumerate(valid_subsets):
                # CHANGED: Extract node sequence from edges
                # For edges [(n1,n2), (n2,n3), (n3,n4)], nodes are [n1, n2, n3, n4]
                node_sequence = []
                if subset:
                    # Add first node from first edge
                    node_sequence.append(subset[0][0][0])
                    # Add second node from each edge
                    for (edge, dist) in subset:
                        node_sequence.append(edge[1])

                spatial_flex_range_list.append({
                    "id": spatial_flex_id,  # Global unique ID
                    "subset_id": subset_idx,  # ID within this path-gen-tech combo
                    "path": path["id"],
                    "generation": g,
                    "tech_vehicle": tech_id,
                    "sequence": node_sequence,  # CHANGED: Node sequence instead of edges
                    "length": float(sum(dist for _, dist in subset)),  # Total distance of subset
                    "total_nb": len(node_sequence),  # CHANGED: Number of nodes instead of edges
                })
                spatial_flex_id += 1
"""

print("=" * 80)
print("SPATIAL FLEX FIX - KEY CHANGES")
print("=" * 80)
print("\nThe fix adds this check before creating subsets:")
print("""
    # Check if entire path fits within driving range
    total_path_distance = sum(dist for _, dist in edges_list)

    if total_path_distance <= max_range:
        # Entire path fits - create only ONE subset with all edges
        valid_subsets.append(tuple(edges_list))
    else:
        # Path doesn't fit - create maximal subsets from each starting position
        ... (original logic)
""")
print("\n" + "=" * 80)
print("EXPECTED RESULTS AFTER FIX:")
print("=" * 80)
print("\nFor path 0 (361.90 km), generation 2010, driving range 388.89 km:")
print("  BEFORE: 70 subsets (one starting from each node)")
print("  AFTER:  1 subset (entire path)")
print("\nFor path with 400km total, generation X, driving range 300km:")
print("  BEFORE: ~many subsets")
print("  AFTER:  Multiple maximal subsets (e.g., [[1,2,3], [2,3,4]])")
print("\n" + "=" * 80)
print("\nTo apply this fix:")
print("1. Copy the CORRECTED_CODE from above")
print("2. In SM-preprocessing.ipynb, find the cell with spatial_flex_range_list code")
print("3. Replace the section starting with 'for tech_id, year_ranges...'")
print("4. Run the cell again")
print("=" * 80)
