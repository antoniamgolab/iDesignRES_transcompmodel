# Detailed diagnostic for travel time constraint violation
# Run this AFTER SM.jl completes

println("\n" * "="^80)
println("DETAILED TRAVEL TIME DEBUG")
println("="^80)

# Check if model solved successfully
if termination_status(model) != MOI.OPTIMAL
    println("⚠️  MODEL DID NOT SOLVE OPTIMALLY!")
    println("  Termination status: $(termination_status(model))")
    println("  Primal status: $(primal_status(model))")
    println("  Cannot validate travel times - no solution available.")
    println("="^80)
    return
end

# Get data structures
odpair_list = data_structures["odpair_list"]
techvehicle_list = data_structures["techvehicle_list"]
g_init = data_structures["g_init"]
y_init = data_structures["y_init"]
speed_list = data_structures["speed_list"]
travel_speed = speed_list[1].travel_speed

println("  Travel speed: $(travel_speed) km/h")

# Find a non-zero flow to test
global test_year = nothing
global test_tv_id = nothing
global test_gen = nothing

println("  Searching for non-zero flows (preferring vehicle-based modes)...")
for (f_key, f_var) in model[:f].data
    flow_val = value(f_var)
    if flow_val > 1e-6
        # Extract techvehicle_id
        tv_id = f_key[3][2]

        # Check if this techvehicle exists in the list (i.e., not a rail dummy)
        tv_idx = findfirst(tv -> tv.id == tv_id, techvehicle_list)

        if tv_idx !== nothing
            # Found a vehicle-based mode (road)
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

# Find a valid path
global test_odpair = nothing
global test_path = nothing

for odpair in odpair_list
    for path in odpair.paths
        if length(path.sequence) >= 2
            global first_geo_id = path.sequence[1].id
            last_geo_id = path.sequence[end].id

            if first_geo_id == last_geo_id
                continue
            end

            # Find techvehicle - skip if not found (e.g., rail dummy vehicle)
            tv_idx = findfirst(tv -> tv.id == test_tv_id, techvehicle_list)
            if tv_idx === nothing
                # This is likely a rail mode flow (dummy techvehicle not in list)
                # Travel time constraint doesn't apply to non-vehicle modes, so skip
                continue
            end

            tv_obj = techvehicle_list[tv_idx]
            mode_id = tv_obj.vehicle_type.mode.id

            key_test_tt = (test_year, (0, odpair.id, path.id, first_geo_id), test_tv_id, test_gen)
            key_test_f = (test_year, (0, odpair.id, path.id), (mode_id, test_tv_id), test_gen)

            if haskey(model[:travel_time].data, key_test_tt) && haskey(model[:f].data, key_test_f)
                flow_val = value(model[:f][key_test_f...])
                if flow_val > 1e-6
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

if test_odpair === nothing || test_path === nothing
    println("  ⚠️  No valid paths found!")
    return
end

# Get techvehicle details (should always exist here since we pre-filtered)
tv_idx_final = findfirst(tv -> tv.id == test_tv_id, techvehicle_list)
if tv_idx_final === nothing
    println("  ⚠️  ERROR: TechVehicle $(test_tv_id) not found (should not happen after filtering)")
    return
end
test_tv = techvehicle_list[tv_idx_final]
mode_id = test_tv.vehicle_type.mode.id
idx_gen = test_gen - g_init + 1

println("\n" * "="^80)
println("TEST PATH DETAILS")
println("="^80)
println("  Year: $(test_year), Generation: $(test_gen)")
println("  Tech vehicle: $(test_tv.name) (id=$(test_tv_id))")
println("  Mode: $(test_tv.vehicle_type.mode.name) (id=$(mode_id))")
println("  OD-pair: $(test_odpair.id)")
println("  Path: $(test_path.id)")
println("  Path total length: $(test_path.length) km")
println("  Number of nodes: $(length(test_path.sequence))")
println()

# Vehicle parameters
println("VEHICLE PARAMETERS:")
println("  W (capacity): $(test_tv.W[idx_gen]) t")
println("  AnnualRange: $(test_tv.AnnualRange[idx_gen]) km/year")
println("  Peak fueling rate: $(test_tv.peak_fueling[idx_gen]) kW or kg/h")
println()

# Path sequence details
println("PATH SEQUENCE DETAILS:")
for i in 1:length(test_path.sequence)
    geo = test_path.sequence[i]
    println("  Node $(i): geo_id=$(geo.id), name=$(geo.name), cumulative_length=$(geo.length) km")
end

println("\nPATH DISTANCE_FROM_PREVIOUS:")
for i in 1:length(test_path.sequence)
    if hasfield(typeof(test_path), :distance_from_previous) && length(test_path.distance_from_previous) >= i
        println("  Segment $(i): distance_from_previous[$(i)] = $(test_path.distance_from_previous[i]) km")
    else
        println("  ⚠️  distance_from_previous field not found or too short!")
    end
end

# Check for zero-length path (boundary route)
origin_geo = test_path.sequence[1]
dest_geo = test_path.sequence[end]
is_boundary = (origin_geo.id == dest_geo.id) || (abs(dest_geo.length - origin_geo.length) < 1e-6)

if is_boundary
    println("\n⚠️  BOUNDARY ROUTE DETECTED:")
    println("  Origin geo_id = $(origin_geo.id), Dest geo_id = $(dest_geo.id)")
    println("  Cumulative distance in sequence: $(dest_geo.length - origin_geo.length) km")
    println("  Total path.length: $(test_path.length) km")
    if hasfield(typeof(test_path), :distance_from_previous) && length(test_path.distance_from_previous) >= 2
        println("  distance_from_previous[2]: $(test_path.distance_from_previous[2]) km")
    end
    println("  This is a boundary-crossing route where origin==destination.")
    println("  The constraint uses path.distance_from_previous, NOT cumulative geo.length!")
end
println()

# Get flow value
key_f = (test_year, (0, test_odpair.id, test_path.id), (mode_id, test_tv_id), test_gen)
flow_val = value(model[:f][key_f...])
println("FLOW DETAILS:")
println("  Flow value (f): $(flow_val) (1000 tkm)")
println()

# Calculate expected values for each segment
println("="^80)
println("SEGMENT-BY-SEGMENT ANALYSIS")
println("="^80)

global cumulative_expected_tt = 0.0

for i in 2:length(test_path.sequence)
    geo_curr = test_path.sequence[i]
    geo_prev = test_path.sequence[i-1]

    # Distance for this segment - USE THE SAME METHOD AS THE CONSTRAINT!
    distance_increment = test_path.distance_from_previous[i]

    println("\nSEGMENT $(i-1)->$(i): geo_$(geo_prev.id) -> geo_$(geo_curr.id)")
    println("  Distance increment (distance_from_previous[$(i)]): $(distance_increment) km")
    println("  (cumulative geo.length: $(geo_prev.length) -> $(geo_curr.length))")

    # Number of vehicles for this segment
    num_vehicles_segment = (distance_increment / (test_tv.W[idx_gen] * test_tv.AnnualRange[idx_gen])) * 1000 * flow_val
    println("  Number of vehicles: $(round(num_vehicles_segment, digits=4))")

    # Driving time for this segment
    driving_time_segment = (distance_increment / travel_speed) * num_vehicles_segment
    println("  Driving time: $(round(driving_time_segment, digits=4)) hours")

    global cumulative_expected_tt += driving_time_segment
    println("  Cumulative expected driving time: $(round(cumulative_expected_tt, digits=4)) hours")

    # Get actual travel times
    key_tt_prev = (test_year, (0, test_odpair.id, test_path.id, geo_prev.id), test_tv_id, test_gen)
    key_tt_curr = (test_year, (0, test_odpair.id, test_path.id, geo_curr.id), test_tv_id, test_gen)

    tt_prev = value(model[:travel_time][key_tt_prev...])
    tt_curr = value(model[:travel_time][key_tt_curr...])

    println("  Actual travel_time at node $(i-1): $(round(tt_prev, digits=4)) hours")
    println("  Actual travel_time at node $(i): $(round(tt_curr, digits=4)) hours")
    println("  Actual increment: $(round(tt_curr - tt_prev, digits=4)) hours")

    # Check for charging
    charging_sum = 0.0
    if haskey(model.obj_dict, :s)
        # Sum charging time across all compatible infrastructure
        f_l_pairs = data_structures["f_l_pairs"]
        for f_l in f_l_pairs
            if test_tv.technology.fuel.id == f_l[1]
                key_s = (test_year, (0, test_odpair.id, test_path.id, geo_curr.id), test_tv_id, f_l, test_gen)
                try
                    s_val = value(model[:s][key_s...])
                    if s_val > 1e-6
                        charging_time_this_fl = s_val * 1000 / test_tv.peak_fueling[idx_gen]
                        println("    Charging (f_l=$(f_l)): $(round(s_val, digits=4)) (1000 kWh), time=$(round(charging_time_this_fl, digits=4)) hours")
                        charging_sum += charging_time_this_fl
                    end
                catch e
                    # Key not found or access error - skip
                end
            end
        end
    end
    println("  Total charging time: $(round(charging_sum, digits=4)) hours")

    # Check for extra breaks (no longer has f_l dimension)
    extra_break_sum = 0.0
    if haskey(model.obj_dict, :extra_break_time)
        key_eb = (test_year, (0, test_odpair.id, test_path.id, geo_curr.id), test_tv_id, test_gen)
        try
            eb_val = value(model[:extra_break_time][key_eb...])
            if eb_val > 1e-6
                println("    Extra break time: $(round(eb_val, digits=4)) hours")
                extra_break_sum = eb_val
            end
        catch e
            # Key not found or access error - skip
        end
    end
    println("  Total extra break time: $(round(extra_break_sum, digits=4)) hours")

    # Expected vs actual
    expected_increment = driving_time_segment + charging_sum + extra_break_sum
    actual_increment = tt_curr - tt_prev
    slack = actual_increment - expected_increment

    println("  Expected total increment: $(round(expected_increment, digits=4)) hours")
    println("  Actual total increment: $(round(actual_increment, digits=4)) hours")
    println("  Slack (actual - expected): $(round(slack, digits=6)) hours")

    if slack < -1e-4
        println("  ⚠️  VIOLATION: Actual < Expected by $(round(abs(slack), digits=4)) hours!")
    elseif abs(slack) < 1e-4
        println("  ✓ Constraint satisfied (within tolerance)")
    else
        println("  ✓ Constraint satisfied (slack = $(round(slack, digits=4)) hours)")
    end
end

println("\n" * "="^80)
println("FINAL SUMMARY")
println("="^80)
println("  Total expected driving time: $(round(cumulative_expected_tt, digits=4)) hours")

origin_geo = test_path.sequence[1]
dest_geo = test_path.sequence[end]
key_tt_origin = (test_year, (0, test_odpair.id, test_path.id, origin_geo.id), test_tv_id, test_gen)
key_tt_dest = (test_year, (0, test_odpair.id, test_path.id, dest_geo.id), test_tv_id, test_gen)

tt_origin = value(model[:travel_time][key_tt_origin...])
tt_dest = value(model[:travel_time][key_tt_dest...])

println("  Actual travel_time at origin: $(round(tt_origin, digits=4)) hours")
println("  Actual travel_time at destination: $(round(tt_dest, digits=4)) hours")
println("  Difference: $(round(tt_dest - cumulative_expected_tt, digits=4)) hours")

if tt_dest < cumulative_expected_tt - 1e-4
    println("  ✗ VIOLATION: Travel time is less than minimum driving time!")
else
    println("  ✓ PASS: Travel time >= minimum driving time")
end

println("="^80)
