# Simple diagnostic to check SOC values directly from model results
# Run this AFTER SM.jl completes

# Get data structures
odpair_list = data_structures["odpair_list"]
techvehicle_list = data_structures["techvehicle_list"]
g_init = data_structures["g_init"]
y_init = data_structures["y_init"]
fueling_infr_list = data_structures["fueling_infr_types_list"]

# Find BEV
bev_tv = nothing
global bev_tv
for tv in techvehicle_list
    if tv.technology.fuel.name == "electricity"
        global bev_tv = tv
        break
    end
end

if bev_tv === nothing
    @warn "SOC Check: No BEV found - skipping"
    return
end

# Find charging infrastructure (silent)

infr_charging_id = nothing
global infr_charging_id
for infr_data in fueling_infr_list
    # Check if fuel is a string or an object
    fuel_name = typeof(infr_data.fuel) == String ? infr_data.fuel : infr_data.fuel.name
    if fuel_name == "electricity"
        global infr_charging_id = infr_data.id
        break
    end
end

if infr_charging_id === nothing
    @warn "SOC Check: No charging infrastructure found - skipping SOC validation"
    return
end

f_l = (bev_tv.technology.fuel.id, infr_charging_id)

# Check first OD pair, first path
first_odpair = odpair_list[1]
first_path = first_odpair.paths[1]
origin_node = first_path.sequence[1].id

test_year = 2030

# Collect results silently
violations = 0
checks_performed = 0

for gen in g_init:test_year
    # Get flow
    key_f = (test_year, (0, first_odpair.id, first_path.id), (bev_tv.vehicle_type.mode.id, bev_tv.id), gen)

    try
        flow_val = value(model[:f][key_f...])

        if flow_val > 0.0001
            # Calculate expected number of vehicles
            idx_gen = gen - g_init + 1
            W_gen = bev_tv.W[idx_gen]
            annual_range_gen = bev_tv.AnnualRange[idx_gen]
            tank_cap_gen = bev_tv.tank_capacity[idx_gen]

            num_vehicles = (first_path.length / (W_gen * annual_range_gen)) * 1000 * flow_val
            expected_fleet_cap = tank_cap_gen * num_vehicles

            # Get SOC at origin
            key_soc = (test_year, (0, first_odpair.id, first_path.id, origin_node), bev_tv.id, f_l, gen)

            try
                soc_val = value(model[:soc][key_soc...])

                global checks_performed += 1

                # Check match - vehicles can arrive with 50-100% of tank capacity
                min_allowed_cap = expected_fleet_cap * 0.5
                max_allowed_cap = expected_fleet_cap
                in_range = (soc_val >= min_allowed_cap - 0.1) && (soc_val <= max_allowed_cap + 0.1)

                if !in_range
                    global violations += 1
                end
            catch e
                # Silent - SOC variable doesn't exist for this combination
            end
        end
    catch e
        # Skip if variable doesn't exist
    end
end

# Print summary
if checks_performed > 0
    if violations == 0
        println("✓ SOC Check: All $(checks_performed) checks passed (50-100% range)")
    else
        println("✗ SOC Check: $(violations)/$(checks_performed) violations (outside 50-100% range)")
    end
else
    println("⚠ SOC Check: No data to validate")
end
