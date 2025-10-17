# CONSTRAINT: Mandatory Driver Breaks
# =====================================
# This constraint enforces EU driver break regulations:
# - After 4.5 hours of driving, drivers must take a 45-minute break
# - Travel time must account for these mandatory breaks

# Add this function to model_functions.jl

"""
    constraint_mandatory_breaks(model::JuMP.Model, data_structures::Dict)

Enforce mandatory driver break regulations along routes.

This constraint ensures that:
1. Travel time includes mandatory break time (45 min per 4.5h driving)
2. Vehicles must have sufficient time to complete routes including breaks
3. Break times are accounted for in total elapsed time calculations

Based on EU Regulation (EC) No 561/2006:
- Maximum 4.5 hours continuous driving
- Mandatory 45-minute break after 4.5 hours
- Multiple breaks required for longer routes

# Arguments
- `model::JuMP.Model`: The optimization model
- `data_structures::Dict`: Dictionary containing all model data

# Data Requirements
- `data_structures["mandatory_break_list"]`: List of MandatoryBreak structs
- `data_structures["travel_time"]`: Travel time variable (if it exists)
- `data_structures["path_list"]`: List of Path objects
- `data_structures["techvehicle_list"]`: List of TechVehicle objects

# Constraint Logic
For each mandatory break:
- At the break location (latest_geo_id), the cumulative travel time must be
  at least the time_with_breaks value
- This ensures breaks are taken and accounted for in scheduling

# Example
```julia
# In SM.jl, after adding other constraints:
constraint_mandatory_breaks(model, data_structures)
```
"""
function constraint_mandatory_breaks(model::JuMP.Model, data_structures::Dict)

    # Extract data from data_structures
    mandatory_breaks = data_structures["mandatory_break_list"]
    y_init = data_structures["y_init"]
    Y_end = data_structures["Y_end"]
    g_init = data_structures["g_init"]
    techvehicle_list = data_structures["techvehicle_list"]
    odpair_list = data_structures["odpair_list"]
    product_list = data_structures["product_list"]
    f_l_pairs = data_structures["f_l_not_by_route"]

    # Check if travel_time variable exists
    if !haskey(model.obj_dict, :travel_time)
        @warn "travel_time variable not found. Skipping mandatory breaks constraint."
        return
    end

    # Create lookup dictionaries for efficient access
    # path_id -> list of breaks for that path
    breaks_by_path = Dict{Int, Array{Any,1}}()
    for mb in mandatory_breaks
        if !haskey(breaks_by_path, mb.path_id)
            breaks_by_path[mb.path_id] = []
        end
        push!(breaks_by_path[mb.path_id], mb)
    end

    println("Adding mandatory breaks constraints...")
    println("  Total breaks to enforce: $(length(mandatory_breaks))")
    println("  Paths with breaks: $(length(breaks_by_path))")

    # Constraint counter
    num_constraints = 0

    # ==============================================================================
    # CONSTRAINT 1: Minimum travel time at break locations
    # ==============================================================================
    # For each break, ensure that the travel time at the break location is at least
    # the required time including the break duration

    for odpair in odpair_list
        p = odpair.product

        for path in odpair.paths
            # Check if this path has any mandatory breaks
            if !haskey(breaks_by_path, path.id)
                continue  # No breaks required for this path
            end

            breaks_for_path = breaks_by_path[path.id]

            # For each mandatory break on this path
            for mb in breaks_for_path
                break_geo_id = mb.latest_geo_id
                break_node_idx = mb.latest_node_idx

                # Verify that this geo_id exists in the path sequence
                geo_found = false
                for (idx, geo_element) in enumerate(path.sequence)
                    if geo_element.id == break_geo_id
                        geo_found = true
                        break
                    end
                end

                if !geo_found
                    @warn "Break location geo_id=$(break_geo_id) not found in path $(path.id) sequence"
                    continue
                end

                # Add constraint for each year, tech vehicle, fuel-infrastructure pair, and generation
                for y in y_init:Y_end
                    for tv in techvehicle_list
                        for f_l in f_l_pairs
                            # Check fuel type matches
                            if tv.technology.fuel.id == f_l[1]
                                for g in g_init:min(y, Y_end)  # g <= y

                                    # Key for travel_time variable
                                    key_tt = (y, (p.id, odpair.id, path.id, break_geo_id), tv.id, f_l, g)

                                    # Key for flow variable
                                    key_f = (y, (p.id, odpair.id, path.id), (tv.vehicle_type.mode.id, tv.id), g)

                                    # Calculate minimum travel time required
                                    # This is: driving_time + break_time
                                    # = (cumulative_distance / speed) + (break_number × 0.75h)

                                    # Get number of vehicles
                                    num_vehicles = (
                                        path.length / (tv.W[g-g_init+1] * tv.AnnualRange[g-g_init+1])
                                    ) * 1000 * model[:f][key_f...]

                                    # Minimum travel time per vehicle at this break location
                                    # From the MandatoryBreak data: time_with_breaks
                                    min_time_per_vehicle = mb.time_with_breaks

                                    # Total fleet minimum travel time
                                    min_fleet_travel_time = min_time_per_vehicle * num_vehicles

                                    # Add constraint: travel_time at break location >= minimum required time
                                    @constraint(
                                        model,
                                        model[:travel_time][key_tt...] >= min_fleet_travel_time
                                    )

                                    num_constraints += 1
                                end
                            end
                        end
                    end
                end
            end
        end
    end

    # ==============================================================================
    # OPTIONAL CONSTRAINT 2: Enforce breaks in travel_time_track constraint
    # ==============================================================================
    # Alternative approach: Modify constraint_travel_time_track to add break time
    # when travel_time passes through a break location

    # This would require:
    # 1. Identifying when cumulative driving time exceeds 4.5h multiples
    # 2. Adding 0.75h to travel_time at those locations
    # 3. Coordinating with constraint_travel_time_track

    # For now, this is handled implicitly by CONSTRAINT 1 above

    # ==============================================================================
    # OPTIONAL CONSTRAINT 3: Ensure charging can occur during breaks
    # ==============================================================================
    # If you want to enforce that charging can ONLY occur during breaks:

    # for odpair in odpair_list
    #     p = odpair.product
    #     for path in odpair.paths
    #         if haskey(breaks_by_path, path.id)
    #             break_locations = Set([mb.latest_geo_id for mb in breaks_by_path[path.id]])
    #
    #             for geo in path.sequence
    #                 if geo.id ∉ break_locations
    #                     # Prevent charging at non-break locations
    #                     for y in y_init:Y_end
    #                         for tv in techvehicle_list
    #                             for f_l in f_l_pairs
    #                                 if tv.technology.fuel.id == f_l[1]
    #                                     for g in g_init:min(y, Y_end)
    #                                         key_s = (y, (p.id, odpair.id, path.id, geo.id), tv.id, f_l, g)
    #                                         @constraint(model, model[:s][key_s...] == 0)
    #                                     end
    #                                 end
    #                             end
    #                         end
    #                     end
    #                 end
    #             end
    #         end
    #     end
    # end

    println("✓ Mandatory breaks constraint added: $(num_constraints) constraints created")
end


# ==============================================================================
# ALTERNATIVE IMPLEMENTATION: Integration with travel_time_track
# ==============================================================================
# Instead of a separate constraint, you could modify constraint_travel_time_track
# to automatically add break time when appropriate

"""
ALTERNATIVE: Modify constraint_travel_time_track to include break time

In constraint_travel_time_track (around line 3450 in model_functions.jl),
after calculating travel_time for a segment, check if a break is required:

```julia
# Existing code calculates:
# travel_time[current] = travel_time[previous] + driving_time + charging_time

# ADD: Check if break is required at current location
break_time = 0.0
cumulative_driving_time = (path.cumulative_distance[i] / speed)

# Check if we've passed a multiple of 4.5 hours
num_breaks_needed = floor(cumulative_driving_time / 4.5)
if num_breaks_needed > 0
    # Check if this is a break location
    for mb in breaks_by_path[path.id]
        if mb.latest_geo_id == geo_curr.id && mb.break_number <= num_breaks_needed
            break_time = 0.75  # 45 minutes in hours
            break
        end
    end
end

# Modified constraint:
@constraint(
    model,
    model[:travel_time][y, (p.id, r.id, path.id, geo_curr.id), tv.id, f_l, g] ==
    model[:travel_time][y, (p.id, r.id, path.id, geo_prev.id), tv.id, f_l, g]
    + (distance_increment / speed) * numbers_vehicles
    + model[:s][y, (p.id, r.id, path.id, geo_curr.id), tv.id, f_l, g] * 1000 / tv.peak_fueling[g-g_init+1]
    + break_time * numbers_vehicles  # ADD THIS LINE
)
```
"""


# ==============================================================================
# USAGE IN SM.jl
# ==============================================================================
# Add this line in SM.jl after adding other constraints:

"""
# Timing: Add mandatory breaks constraint
@info "Step 4.11/5: Adding mandatory breaks constraint..."
t_start = time()
constraint_mandatory_breaks(model, data_structures)
t_mandatory_breaks = time() - t_start
@info "✓ Mandatory breaks constraint added in $(round(t_mandatory_breaks, digits=2)) seconds"
"""


# ==============================================================================
# VALIDATION
# ==============================================================================
# After optimization, verify that breaks are enforced:

"""
# Check that travel time at break locations >= required time
for mb in mandatory_breaks_list
    path = path_dict[mb.path_id]
    geo_id = mb.latest_geo_id

    for y in years
        for tv in techvehicles
            for f_l in f_l_pairs
                for g in generations
                    key_tt = (y, (0, odpair_id, path.id, geo_id), tv.id, f_l, g)
                    key_f = (y, (0, odpair_id, path.id), (1, tv.id), g)

                    if haskey(model[:travel_time].data, key_tt)
                        tt_val = value(model[:travel_time][key_tt...])
                        flow_val = value(model[:f][key_f...])

                        if flow_val > 0.01
                            num_vehicles = (path.length / (W * annual_range)) * 1000 * flow_val
                            min_time = mb.time_with_breaks * num_vehicles

                            if tt_val < min_time - 0.01
                                println("VIOLATION: Break $(mb.break_number) on path $(path.id)")
                                println("  Required: $(min_time), Actual: $(tt_val)")
                            end
                        end
                    end
                end
            end
        end
    end
end
"""
