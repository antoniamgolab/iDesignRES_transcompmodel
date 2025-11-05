"""
Verification script to check that mandatory break constraints are satisfied.
"""

# Check if mandatory breaks data exists
if !haskey(data_structures, "mandatory_break_list")
    @warn "No mandatory breaks data found. Skipping verification."
else
    mandatory_break_list = data_structures["mandatory_break_list"]
    path_dict = Dict(path.id => path for path in data_structures["path_list"])
    techvehicle_list = data_structures["techvehicle_list"]
    odpair_list = data_structures["odpair_list"]
    product_list = data_structures["product_list"]

    if length(data_structures["fueling_infr_types_list"]) > 0
        f_l_pairs = data_structures["f_l_not_by_route"]
    else
        f_l_pairs = []
    end

    y_init = data_structures["y_init"]
    Y_end = data_structures["Y_end"]
    g_init = data_structures["g_init"]

    # Group breaks by path_id for easier processing
    breaks_by_path = Dict()
    for mb in mandatory_break_list
        if !haskey(breaks_by_path, mb.path_id)
            breaks_by_path[mb.path_id] = []
        end
        push!(breaks_by_path[mb.path_id], mb)
    end

    # If no mandatory breaks, exit early
    if length(mandatory_break_list) == 0
        println("⚠ Mandatory Breaks: None defined")
        return
    end

    # Check results for a sample year
    test_year = 2030

    if test_year < y_init || test_year > Y_end
        @warn "Test year $test_year is outside model horizon [$y_init, $Y_end]"
    else

        global violations = 0
        global checks_performed = 0
        global extra_break_total = 0.0

        for (path_id, breaks) in breaks_by_path
            path = path_dict[path_id]

            # Find which odpair uses this path
            odpair_with_path = findfirst(r -> any(p -> p.id == path_id, r.paths), odpair_list)
            if odpair_with_path === nothing
                continue
            end

            odpair = odpair_list[odpair_with_path]
            product = odpair.product

            for mb in breaks
                geo_id = mb.latest_geo_id
                required_time = mb.time_with_breaks

                # Check if this geo_id is in the path sequence
                geo_idx = findfirst(g -> g.id == geo_id, path.sequence)
                if geo_idx === nothing
                    continue
                end

                # Check travel_time for this location
                if haskey(model.obj_dict, :travel_time)
                    for tv in techvehicle_list
                        for g in g_init:test_year  # Check all generations up to test year
                            # travel_time no longer has f_l dimension
                            key = (test_year, (product.id, odpair.id, path_id, geo_id), tv.id, g)

                            # Try to get travel_time value - skip if key doesn't exist
                            try
                                actual_time = value(model[:travel_time][key...])
                                global checks_performed += 1

                                # Calculate number of vehicles for this key
                                flow_key = (test_year, (product.id, odpair.id, path_id), (tv.vehicle_type.mode.id, tv.id), g)

                                # Try to get flow value - skip if key doesn't exist
                                flow_val = 0.0
                                try
                                    flow_val = value(model[:f][flow_key...])
                                catch
                                    continue  # Skip if flow not defined for this combination
                                end

                                num_vehicles = (path.length / (tv.W[g-g_init+1] * tv.AnnualRange[g-g_init+1])) * 1000 * flow_val
                                required_fleet_time = required_time * num_vehicles

                                if actual_time < required_fleet_time - 1e-6
                                    global violations += 1
                                end

                                # Check extra break time if available (also no longer has f_l dimension)
                                if haskey(model.obj_dict, :extra_break_time)
                                    try
                                        extra_time = value(model[:extra_break_time][key...])
                                        if extra_time > 1e-6
                                            global extra_break_total += extra_time
                                            # println("        Extra break time: $(round(extra_time, digits=3))h")
                                        end
                                    catch
                                        # Extra break time not defined for this key, skip
                                    end
                                end
                            catch e
                                # Key doesn't exist in travel_time variable, skip
                                continue
                            end
                        end
                    end
                end
            end
        end

        # Print compact summary
        if checks_performed > 0
            if violations == 0
                println("✓ Mandatory Breaks: All $(checks_performed) checks passed")
            else
                println("✗ Mandatory Breaks: $(violations)/$(checks_performed) violations found")
            end
        else
            println("⚠ Mandatory Breaks: No checks performed")
        end
    end
end
