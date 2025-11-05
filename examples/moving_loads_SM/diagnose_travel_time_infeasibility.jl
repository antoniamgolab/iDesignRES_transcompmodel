"""
Diagnostic script to identify potential issues with constraint_travel_time_track
Specifically looks for paths with multiple nodes that might cause infeasibility
"""

println("="^80)
println("TRAVEL TIME CONSTRAINT INFEASIBILITY DIAGNOSIS")
println("="^80)

# Extract data
path_list = data_structures["path_list"]
odpair_list = data_structures["odpair_list"]
techvehicle_list = data_structures["techvehicle_list"]
speed = data_structures["speed_list"][1].travel_speed

println("\nAnalyzing $(length(path_list)) paths...")
println()

# Categorize paths
problematic_paths = []
short_multinode_paths = []
zero_distance_segments = []

for path in path_list
    num_nodes = length(path.sequence)
    total_length = path.length

    # Check for paths with multiple nodes
    if num_nodes > 2
        # Calculate sum of segment distances
        segment_sum = sum(path.distance_from_previous[2:end])

        # Check if it's a short path (potential boundary crossing)
        if total_length < 50  # Less than 50 km
            push!(short_multinode_paths, (
                id = path.id,
                length = total_length,
                num_nodes = num_nodes,
                segment_sum = segment_sum,
                dist_from_prev = path.distance_from_previous,
                sequence_ids = [g.id for g in path.sequence]
            ))
        end

        # Check for mismatch between total and sum of segments
        if abs(segment_sum - total_length) > 0.1
            push!(problematic_paths, (
                id = path.id,
                length = total_length,
                segment_sum = segment_sum,
                mismatch = segment_sum - total_length,
                num_nodes = num_nodes,
                dist_from_prev = path.distance_from_previous
            ))
        end

        # Check for zero or near-zero distance segments
        for i in 2:length(path.distance_from_previous)
            if path.distance_from_previous[i] < 0.01
                push!(zero_distance_segments, (
                    path_id = path.id,
                    segment = i,
                    distance = path.distance_from_previous[i],
                    total_length = total_length,
                    num_nodes = num_nodes
                ))
            end
        end
    end
end

println("="^80)
println("FINDINGS")
println("="^80)

println("\n1. SHORT MULTI-NODE PATHS (< 50 km with 3+ nodes):")
println("   Count: $(length(short_multinode_paths))")
if length(short_multinode_paths) > 0
    println("\n   First 10 examples:")
    for (i, p) in enumerate(short_multinode_paths[1:min(10, end)])
        println("\n   Path $(p.id):")
        println("     Total length: $(round(p.length, digits=2)) km")
        println("     Num nodes: $(p.num_nodes)")
        println("     Sum of segments: $(round(p.segment_sum, digits=2)) km")
        println("     Sequence: $(p.sequence_ids)")
        println("     Distance from previous: $(round.(p.dist_from_prev, digits=2))")

        # Calculate accumulated travel time per vehicle
        accum_time = 0.0
        for i in 2:length(p.dist_from_prev)
            segment_dist = p.dist_from_prev[i]
            segment_time = segment_dist / speed  # Hours per vehicle
            accum_time += segment_time
            println("       Segment $(i-1)→$(i): $(round(segment_dist, digits=2)) km, " *
                    "$(round(segment_time, digits=2)) h/vehicle, " *
                    "accum: $(round(accum_time, digits=2)) h/vehicle")
        end

        if p.num_nodes > 5
            println("     ⚠️  MANY NODES: $(p.num_nodes) nodes create $(p.num_nodes-1) chained constraints")
        end
    end
end

println("\n\n2. PATHS WITH DISTANCE MISMATCH (sum of segments ≠ total length):")
println("   Count: $(length(problematic_paths))")
if length(problematic_paths) > 0
    println("\n   First 10 examples:")
    for (i, p) in enumerate(problematic_paths[1:min(10, end)])
        println("\n   Path $(p.id):")
        println("     Total length: $(round(p.length, digits=2)) km")
        println("     Sum of segments: $(round(p.segment_sum, digits=2)) km")
        println("     Mismatch: $(round(p.mismatch, digits=2)) km")
        println("     Num nodes: $(p.num_nodes)")
        println("     Distance from previous: $(round.(p.dist_from_prev, digits=2))")
        println("     ⚠️  This creates inconsistent distance calculations!")
    end
end

println("\n\n3. ZERO-DISTANCE SEGMENTS:")
println("   Count: $(length(zero_distance_segments))")
if length(zero_distance_segments) > 0
    println("\n   First 10 examples:")
    for (i, s) in enumerate(zero_distance_segments[1:min(10, end)])
        println("     Path $(s.path_id), segment $(s.segment-1)→$(s.segment): " *
                "$(round(s.distance, digits=4)) km " *
                "(total path: $(round(s.total_length, digits=2)) km)")
    end
    println("\n   ⚠️  Zero-distance segments still create constraints but add no driving time!")
end

println("\n="^80)
println("CONSTRAINT ANALYSIS")
println("="^80)

# Count total constraints created
total_constraints = 0
for path in path_list
    num_nodes = length(path.sequence)
    if num_nodes > 1
        # One constraint per non-origin node, per year, per techvehicle, per generation
        # This is a rough estimate
        total_constraints += (num_nodes - 1)
    end
end

println("\nApproximate travel_time constraints from path structure:")
println("  Paths: $(length(path_list))")
println("  Base constraints from nodes: ~$(total_constraints)")
println("  (multiply by years × techvehicles × generations for actual count)")

# Find the path with most nodes
max_nodes_path = argmax(p -> length(p.sequence), path_list)
println("\nPath with most nodes: $(max_nodes_path.id)")
println("  Nodes: $(length(max_nodes_path.sequence))")
println("  Length: $(round(max_nodes_path.length, digits=2)) km")
println("  Creates $(length(max_nodes_path.sequence) - 1) chained constraints per (year, tv, gen)")

println("\n="^80)
println("POTENTIAL INFEASIBILITY SOURCES")
println("="^80)

println("\n1. OVER-CONSTRAINED PATHS:")
println("   - Paths with many nodes create long chains of equality constraints")
println("   - Each node adds: travel_time[i] = travel_time[i-1] + driving + charging + breaks")
println("   - If any constraint in the chain conflicts, entire path becomes infeasible")

println("\n2. BOUNDARY PATHS WITH MULTIPLE INTERMEDIATE NODES:")
println("   - Short total distance but many nodes accumulate travel time")
println("   - Example: 5 km path with 5 nodes → each adds ~0.1h but may conflict with breaks")

println("\n3. DISTANCE MISMATCHES:")
println("   - If sum(distance_from_previous) ≠ path.length")
println("   - Constraint uses distance_from_previous, but other parts might use path.length")
println("   - Creates inconsistency")

println("\n4. MANDATORY BREAKS CONFLICT:")
println("   - Mandatory breaks look at path.length to determine required break time")
println("   - But travel_time is accumulated from distance_from_previous segments")
println("   - If these don't match, infeasibility can occur")

println("\n="^80)
println("RECOMMENDATIONS")
println("="^80)

if length(short_multinode_paths) > 0
    println("\n✓ Found $(length(short_multinode_paths)) short multi-node paths")
    println("  These are likely boundary crossings with intermediate waypoints")
    println()
    println("  OPTION 1: Simplify path sequences")
    println("    - For short paths (< 50 km), use only origin and destination nodes")
    println("    - Remove intermediate waypoints that don't have infrastructure")
    println()
    println("  OPTION 2: Relax travel_time equality constraints")
    println("    - Change == to >= for intermediate nodes")
    println("    - Only enforce strict equality at final destination")
    println()
    println("  OPTION 3: Skip travel_time constraints for very short paths")
    println("    - If path.length < threshold (e.g., 10 km)")
    println("    - These paths don't meaningfully contribute to travel time")
end

if length(problematic_paths) > 0
    println("\n⚠️  Found $(length(problematic_paths)) paths with distance mismatches")
    println("  FIX: Ensure distance_from_previous values sum to path.length")
    println("  Re-run preprocessing to correct these")
end

if length(zero_distance_segments) > 0
    println("\n⚠️  Found $(length(zero_distance_segments)) zero-distance segments")
    println("  These create unnecessary constraints that don't add travel time")
    println("  FIX: Remove nodes with zero distance from previous node")
end

println("\n="^80)
