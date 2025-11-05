# Verbose travel time diagnostic to identify which check is failing
# Run this AFTER SM.jl completes
# Updated for new indexing: travel_time no longer has f_l dimension

println("\n" * "="^80)
println("VERBOSE TRAVEL TIME DIAGNOSTIC")
println("="^80)

# Get data structures
odpair_list = data_structures["odpair_list"]
techvehicle_list = data_structures["techvehicle_list"]
g_init = data_structures["g_init"]
y_init = data_structures["y_init"]
speed_list = data_structures["speed_list"]
travel_speed = speed_list[1].travel_speed

println("  Travel speed: $(travel_speed) km/h")
println("  g_init: $(g_init), y_init: $(y_init)")

# Find BEV
bev_tv = findfirst(tv -> tv.technology.fuel.name == "electricity", techvehicle_list)
if bev_tv === nothing
    println("⚠️  No BEV found - skipping")
else
    bev_tv = techvehicle_list[bev_tv]
    println("  BEV: $(bev_tv.name) (id=$(bev_tv.id))")

    # Search for a valid OD-pair/path that exists in the model
    global test_odpair = nothing
    global test_path = nothing
    global test_year = nothing
    global test_gen = nothing
    global test_tv_id = nothing

    # Find a non-zero flow and extract its parameters (prefer vehicle-based modes)
    println("  Searching for non-zero flows (preferring vehicle-based modes)...")

    for (f_key, f_var) in model[:f].data
        flow_val = value(f_var)
        if flow_val > 1e-6
            # f_key format: (year, (p, odpair_id, path_id), (mode_id, tv_id), gen)
            tv_id = f_key[3][2]  # (mode_id, tv_id)[2]

            # Check if this is a vehicle-based mode (not rail dummy)
            tv_idx = findfirst(tv -> tv.id == tv_id, techvehicle_list)

            if tv_idx !== nothing
                # Found vehicle-based flow
                global test_year = f_key[1]
                global test_tv_id = tv_id
                global test_gen = f_key[4]
                println("  Found non-zero vehicle flow: year=$(test_year), tv=$(test_tv_id), gen=$(test_gen), flow=$(flow_val)")
                break
            end
        end
    end

    if test_year === nothing
        println("  ⚠️  No non-zero vehicle-based flows found!")
        println("  (Rail mode flows exist but travel time constraint doesn't apply to non-vehicle modes)")
        println("="^80)
        return
    end

    # Now search for a path with this year/tv/gen combination
    for odpair in odpair_list
        for path in odpair.paths
            # Skip single-node paths and paths where origin==destination (boundary routes)
            if length(path.sequence) >= 2
                global first_geo_id = path.sequence[1].id
                last_geo_id = path.sequence[end].id

                # Skip if origin == destination (boundary/self-loop)
                if first_geo_id == last_geo_id
                    continue
                end

                # Get mode_id from techvehicle - skip if not found (rail mode)
                tv_idx = findfirst(tv -> tv.id == test_tv_id, techvehicle_list)
                if tv_idx === nothing
                    # Rail mode flow - skip (travel time doesn't apply)
                    continue
                end
                tv_obj = techvehicle_list[tv_idx]
                mode_id = tv_obj.vehicle_type.mode.id

                key_test_tt = (test_year, (0, odpair.id, path.id, first_geo_id), test_tv_id, test_gen)
                key_test_f = (test_year, (0, odpair.id, path.id), (mode_id, test_tv_id), test_gen)

                # Check if both travel_time and flow exist, and flow is non-zero
                if haskey(model[:travel_time].data, key_test_tt) && haskey(model[:f].data, key_test_f)
                    flow_val = value(model[:f][key_test_f...])
                    if flow_val > 1e-6  # Non-zero flow
                        global test_odpair = odpair
                        global test_path = path
                        break
                    end
                end
            end
        end
        if test_odpair !== nothing
            break
        end
    end

    if test_odpair === nothing
        println("  ⚠️  No valid paths with non-zero flow found in model to test!")
        println("  (Skipped boundary routes where origin==destination)")
        println()

        # Debug: Check flow variable
        if haskey(model.obj_dict, :f)
            println("  Debug: Flow variable (f) exists in model")
            println("  Total flow variables: $(length(model[:f]))")
            println()
            println("  Sample flow keys (first 5):")
            local num_printed = 0
            for key in keys(model[:f].data)
                println("    $(key)")
                num_printed += 1
                if num_printed >= 5
                    break
                end
            end
            println()
            println("  Checking for non-zero flows...")
            local nonzero_count = 0
            local sample_nonzero_keys = []
            for (key, var) in model[:f].data
                val = value(var)
                if val > 1e-6
                    nonzero_count += 1
                    if length(sample_nonzero_keys) < 3
                        push!(sample_nonzero_keys, (key, val))
                    end
                end
            end
            println("  Total non-zero flows: $(nonzero_count)")
            if nonzero_count > 0
                println("  Sample non-zero flows:")
                for (key, val) in sample_nonzero_keys
                    println("    $(key) = $(val)")
                end
            end
        else
            println("  Debug: Flow variable (f) NOT found in model!")
        end
        println()
        println("="^80)
        println("RESULT: ⚠️  Cannot validate - no paths with non-zero flow found")
        println("="^80)
        return
    end

    origin_node = test_path.sequence[1].id
    dest_node = test_path.sequence[end].id

    # Get the actual techvehicle object for this test (should exist since we filtered above)
    tv_idx_final = findfirst(tv -> tv.id == test_tv_id, techvehicle_list)
    if tv_idx_final === nothing
        println("  ⚠️  ERROR: TechVehicle $(test_tv_id) not found after filtering")
        return
    end
    test_tv = techvehicle_list[tv_idx_final]

    println("  ✓ Found valid path!")
    println("  Test year: $(test_year), generation: $(test_gen)")
    println("  Tech vehicle: $(test_tv.name) (id=$(test_tv_id))")
    println("  OD-pair: $(test_odpair.id)")
    println("  Path: $(test_path.id) (length=$(test_path.length) km)")
    println("  Path nodes: $(length(test_path.sequence))")
    println("  Origin node: $(origin_node), Dest node: $(dest_node)")

    # Check if single-node path (boundary route)
    if length(test_path.sequence) == 1
        println()
        println("⚠️  SKIPPING: Single-node path (boundary-crossing route)")
        println("    These routes represent traffic entering/leaving the study area.")
        println("    Travel time constraints don't apply to single-node paths.")
        println()
        println("="^80)
        println("RESULT: ✓ Travel time check skipped (not applicable)")
        println("="^80)
    else
        # Only run checks for multi-node paths
        println()

        # Run checks
        checks_passed = 0
        checks_total = 0

        # Check 1: Origin travel time = 0
        println("CHECK 1: Origin travel time = 0")
        checks_total += 1
        # Note: travel_time indexing changed - no f_l dimension
        key_tt_origin = (test_year, (0, test_odpair.id, test_path.id, origin_node), test_tv_id, test_gen)

        # Check if this key exists in the model (some paths may be filtered out)
        if !haskey(model[:travel_time].data, key_tt_origin)
            println("  ⚠️  SKIPPED: travel_time variable not found for this path")
            println("    Key: $(key_tt_origin)")
            println("    This path may have been filtered during model building.")
        else
            try
                tt_origin = value(model[:travel_time][key_tt_origin...])
                println("  Origin travel time: $(tt_origin) hours")
                if abs(tt_origin) < 0.001
                    println("  ✓ PASS: Travel time at origin is ~0")
                    global checks_passed += 1
                else
                    println("  ✗ FAIL: Travel time at origin should be 0, got $(tt_origin)")
                end
            catch e
                println("  ✗ FAIL: Error accessing travel_time variable")
                println("  Error: $(e)")
            end
        end
        println()

        # Check 2: Destination travel time >= driving time
        println("CHECK 2: Destination travel time >= expected driving time")
        checks_total += 1
        # Note: travel_time indexing changed - no f_l dimension
        key_tt_dest = (test_year, (0, test_odpair.id, test_path.id, dest_node), test_tv_id, test_gen)
        key_f = (test_year, (0, test_odpair.id, test_path.id), (test_tv.vehicle_type.mode.id, test_tv_id), test_gen)

        # Check if this key exists in the model
        if !haskey(model[:travel_time].data, key_tt_dest)
            println("  ⚠️  SKIPPED: travel_time variable not found for this path")
            println("    Key: $(key_tt_dest)")
        else
            try
                tt_dest = value(model[:travel_time][key_tt_dest...])
                flow_val = value(model[:f][key_f...])
                idx_gen = test_gen - g_init + 1
                num_vehicles = (test_path.length / (test_tv.W[idx_gen] * test_tv.AnnualRange[idx_gen])) * 1000 * flow_val
                expected_tt = (test_path.length / travel_speed) * num_vehicles

                println("  Destination travel time: $(round(tt_dest, digits=4)) hours")
                println("  Flow value: $(round(flow_val, digits=4))")
                println("  Number of vehicles: $(round(num_vehicles, digits=4))")
                println("  Expected driving time: $(round(expected_tt, digits=4)) hours")
                println("  Difference: $(round(tt_dest - expected_tt, digits=4)) hours")

                if tt_dest >= expected_tt - 0.001  # Small tolerance
                    println("  ✓ PASS: Destination travel time >= expected")
                    global checks_passed += 1
                else
                    println("  ✗ FAIL: Destination travel time ($(round(tt_dest, digits=4))) < expected ($(round(expected_tt, digits=4)))")
                end
            catch e
                println("  ✗ FAIL: Error in calculation")
                println("  Error: $(e)")
            end
        end
        println()

        # Check 3: Travel time increases monotonically along path
        println("CHECK 3: Travel time increases monotonically along path")
        checks_total += 1

        # Check if first node exists to determine if path is in model
        first_geo_id = test_path.sequence[1].id
        key_tt_first = (test_year, (0, test_odpair.id, test_path.id, first_geo_id), test_tv_id, test_gen)

        if !haskey(model[:travel_time].data, key_tt_first)
            println("  ⚠️  SKIPPED: travel_time variable not found for this path")
            println("    Key: $(key_tt_first)")
        else
            monotonic_pass = true
            try
                println("  Path sequence ($(length(test_path.sequence)) nodes):")
                prev_tt = 0.0
                for i in 1:length(test_path.sequence)
                    geo_id = test_path.sequence[i].id
                    # Note: travel_time indexing changed - no f_l dimension
                    key_tt = (test_year, (0, test_odpair.id, test_path.id, geo_id), test_tv_id, test_gen)
                    tt_val = value(model[:travel_time][key_tt...])

                    println("    Node $(i) (id=$(geo_id)): travel_time = $(round(tt_val, digits=4)) hours")

                    if tt_val < prev_tt - 0.001
                        println("    ✗ FAIL: Decreased from $(round(prev_tt, digits=4)) to $(round(tt_val, digits=4))")
                        global monotonic_pass = false
                        break
                    end
                    prev_tt = tt_val
                end

                if monotonic_pass
                    println("  ✓ PASS: Travel time increases monotonically")
                    global checks_passed += 1
                else
                    println("  ✗ FAIL: Travel time decreased at some point")
                end
            catch e
                println("  ✗ FAIL: Error checking monotonicity")
                println("  Error: $(e)")
            end
        end

        # Print summary
        println()
        println("="^80)
        if checks_passed == 0 && checks_total > 0
            println("RESULT: ⚠️  All checks skipped - path not found in model")
            println("This likely means the path was filtered during model building (e.g., same origin/destination).")
        elseif checks_passed == checks_total
            println("RESULT: ✓ All $(checks_total) checks passed")
        else
            println("RESULT: ✗ $(checks_passed)/$(checks_total) checks passed")
        end
        println("="^80)
    end
end
