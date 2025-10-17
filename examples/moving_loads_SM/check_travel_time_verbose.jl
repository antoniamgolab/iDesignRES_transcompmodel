# Verbose travel time diagnostic to identify which check is failing
# Run this AFTER SM.jl completes

println("\n" * "="^80)
println("VERBOSE TRAVEL TIME DIAGNOSTIC")
println("="^80)

# Get data structures
odpair_list = data_structures["odpair_list"]
techvehicle_list = data_structures["techvehicle_list"]
g_init = data_structures["g_init"]
y_init = data_structures["y_init"]
fueling_infr_list = data_structures["fueling_infr_types_list"]
speed_list = data_structures["speed_list"]
travel_speed = speed_list[1].travel_speed

println("  Travel speed: $(travel_speed) km/h")
println("  g_init: $(g_init), y_init: $(y_init)")

# Find BEV and charging infrastructure
bev_tv = findfirst(tv -> tv.technology.fuel.name == "electricity", techvehicle_list)
if bev_tv === nothing
    println("⚠️  No BEV found - skipping")
else
    bev_tv = techvehicle_list[bev_tv]
    println("  BEV: $(bev_tv.name) (id=$(bev_tv.id))")

    infr_charging = findfirst(infr ->
        (typeof(infr.fuel) == String ? infr.fuel : infr.fuel.name) == "electricity",
        fueling_infr_list
    )
    if infr_charging === nothing
        println("⚠️  No charging infrastructure found - skipping")
    else
        f_l = (bev_tv.technology.fuel.id, fueling_infr_list[infr_charging].id)
        println("  Charging infr: f_l = $(f_l)")

        # Test parameters
        test_year = 2030
        test_gen = 2025
        first_odpair = odpair_list[1]
        first_path = first_odpair.paths[1]
        origin_node = first_path.sequence[1].id
        dest_node = first_path.sequence[end].id

        println("  Test year: $(test_year), generation: $(test_gen)")
        println("  OD-pair: $(first_odpair.id)")
        println("  Path: $(first_path.id) (length=$(first_path.length) km)")
        println("  Path nodes: $(length(first_path.sequence))")
        println("  Origin node: $(origin_node), Dest node: $(dest_node)")

        # Check if single-node path (boundary route)
        if length(first_path.sequence) == 1
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
            key_tt_origin = (test_year, (0, first_odpair.id, first_path.id, origin_node), bev_tv.id, f_l, test_gen)
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
            println()

            # Check 2: Destination travel time >= driving time
            println("CHECK 2: Destination travel time >= expected driving time")
            checks_total += 1
            key_tt_dest = (test_year, (0, first_odpair.id, first_path.id, dest_node), bev_tv.id, f_l, test_gen)
            key_f = (test_year, (0, first_odpair.id, first_path.id), (bev_tv.vehicle_type.mode.id, bev_tv.id), test_gen)
            try
                tt_dest = value(model[:travel_time][key_tt_dest...])
                flow_val = value(model[:f][key_f...])
                idx_gen = test_gen - g_init + 1
                num_vehicles = (first_path.length / (bev_tv.W[idx_gen] * bev_tv.AnnualRange[idx_gen])) * 1000 * flow_val
                expected_tt = (first_path.length / travel_speed) * num_vehicles

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
            println()

            # Check 3: Travel time increases monotonically along path
            println("CHECK 3: Travel time increases monotonically along path")
            checks_total += 1
            monotonic_pass = true
            try
                println("  Path sequence ($(length(first_path.sequence)) nodes):")
                prev_tt = 0.0
                for i in 1:length(first_path.sequence)
                    geo_id = first_path.sequence[i].id
                    key_tt = (test_year, (0, first_odpair.id, first_path.id, geo_id), bev_tv.id, f_l, test_gen)
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

            # Print summary
            println()
            println("="^80)
            if checks_passed == checks_total
                println("RESULT: ✓ All $(checks_total) checks passed")
            else
                println("RESULT: ✗ $(checks_passed)/$(checks_total) checks passed")
            end
            println("="^80)
        end
    end
end
