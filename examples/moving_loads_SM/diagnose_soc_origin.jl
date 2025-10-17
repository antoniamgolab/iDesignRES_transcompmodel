# Diagnostic script to check SOC values at origin for different generations
# Add this AFTER optimize!(model) in SM.jl

println("\n" * "="^80)
println("SOC ORIGIN DIAGNOSTIC")
println("="^80)

# Get data from data_structures (it's a Dict with string keys)
odpair_list = data_structures["odpair_list"]
path_list = data_structures["path_list"]
techvehicle_list = data_structures["techvehicle_list"]
y_init = data_structures["y_init"]
Y_end = data_structures["Y_end"]
g_init = data_structures["g_init"]

first_odpair = odpair_list[1]
first_path = first_odpair.paths[1]
origin_node = first_path.sequence[1].id
println("Path ID: $(first_path.id)")
println("Origin node ID: $origin_node")
println("Path length: $(first_path.length) km")

# Find the BEV (electric vehicle) - it's the one with electricity as fuel
bev_tv = nothing
global bev_tv  # Declare as global to avoid scoping issues
for tv in techvehicle_list
    if tv.technology.fuel.name == "electricity"
        global bev_tv = tv
        break
    end
end

if bev_tv === nothing
    println("ERROR: No BEV (electric vehicle) found in techvehicle_list!")
    println("Available vehicles:")
    for tv in techvehicle_list
        println("  - $(tv.name): fuel = $(tv.technology.fuel.name)")
    end
    error("BEV not found")
end

println("Vehicle: $(bev_tv.name)")
println("Fuel: $(bev_tv.technology.fuel.name)")
println("Tank capacity by generation: $(bev_tv.tank_capacity)")

# Get fuel-infrastructure pair for electricity
fuel_electricity_id = bev_tv.technology.fuel.id
# Find the charging infrastructure for electricity
infr_charging_id = nothing
global infr_charging_id
fueling_infr_list = data_structures["fueling_infr_types_list"]
for infr_data in fueling_infr_list
    if infr_data.fuel == "electricity"
        global infr_charging_id = infr_data.id
        break
    end
end

if infr_charging_id === nothing
    println("ERROR: No charging infrastructure found for electricity!")
    error("Charging infrastructure not found")
end

f_l = (fuel_electricity_id, infr_charging_id)
println("Fuel-infrastructure pair: $f_l")

# Check SOC values at origin for year 2030, different generations
test_year = 2030
println("\nChecking SOC at origin for year $test_year:")
println("="^80)
println("Gen    Flow(1000t)  NumVeh   TankCap   FleetCap   SOC(kWh)   Match?")
println("-"^80)

for gen in g_init:test_year
    # Get flow value
    key_f = (test_year, (0, first_odpair.id, first_path.id), (bev_tv.vehicle_type.mode.id, bev_tv.id), gen)

    try
        flow_val = value(model[:f][key_f...])

        if flow_val > 0.001  # Only check if there's actual flow
            # Calculate number of vehicles (same formula as constraint)
            idx_gen = gen - g_init + 1
            W_gen = bev_tv.W[idx_gen]
            annual_range_gen = bev_tv.AnnualRange[idx_gen]
            tank_cap_gen = bev_tv.tank_capacity[idx_gen]

            num_vehicles = (first_path.length / (W_gen * annual_range_gen)) * 1000 * flow_val
            fleet_capacity = tank_cap_gen * num_vehicles

            # Get actual SOC value from model
            key_soc = (test_year, (0, first_odpair.id, first_path.id, origin_node), bev_tv.id, f_l, gen)

            try
                soc_val = value(model[:soc][key_soc...])

                # Check if they match
                match = abs(soc_val - fleet_capacity) < 0.1 ? "✓" : "✗"

                println("$gen    $(round(flow_val, digits=4))    $(round(num_vehicles, digits=2))    $(round(tank_cap_gen, digits=2))    $(round(fleet_capacity, digits=2))    $(round(soc_val, digits=2))    $match")
            catch
                println("$gen    $(round(flow_val, digits=4))    $(round(num_vehicles, digits=2))    $(round(tank_cap_gen, digits=2))    $(round(fleet_capacity, digits=2))    NO SOC VAR    ✗")
            end
        end
    catch
        # Variable doesn't exist or no flow
        continue
    end
end

println("="^80)
println("\nIf SOC values don't match Fleet Capacity, there's a problem with constraint_soc_track!")
println("Expected: SOC at origin = tank_capacity * num_vehicles")
println("="^80)

# Also check a few nodes along the route
println("\n" * "="^80)
println("SOC TRACKING ALONG ROUTE (Gen 2030, First 5 nodes)")
println("="^80)
println("Node   GeoID     Dist(km)  SOC(kWh)  Expected    Match?")
println("-"^80)

gen_test = 2030
if gen_test <= test_year
    key_f = (test_year, (0, first_odpair.id, first_path.id), (bev_tv.vehicle_type.mode.id, bev_tv.id), gen_test)

    try
        flow_val = value(model[:f][key_f...])

        if flow_val > 0.001
            idx_gen = gen_test - g_init + 1
            W_gen = bev_tv.W[idx_gen]
            annual_range_gen = bev_tv.AnnualRange[idx_gen]
            tank_cap_gen = bev_tv.tank_capacity[idx_gen]
            spec_cons_gen = bev_tv.spec_cons[idx_gen]

            num_vehicles = (first_path.length / (W_gen * annual_range_gen)) * 1000 * flow_val

            prev_soc = nothing

            for i in 1:min(5, length(first_path.sequence))
                geo_id = first_path.sequence[i].id
                cum_dist = first_path.cumulative_distance[i]

                key_soc = (test_year, (0, first_odpair.id, first_path.id, geo_id), bev_tv.id, f_l, gen_test)

                try
                    soc_val = value(model[:soc][key_soc...])

                    if i == 1
                        # Origin - should equal fleet capacity
                        expected = tank_cap_gen * num_vehicles
                        match = abs(soc_val - expected) < 0.1 ? "✓" : "✗"
                        println("$i      $geo_id    $(round(cum_dist, digits=2))    $(round(soc_val, digits=2))    $(round(expected, digits=2))    $match (origin)")
                    else
                        # Along route - check energy balance
                        dist_increment = first_path.distance_from_previous[i]
                        energy_consumed = dist_increment * spec_cons_gen * num_vehicles

                        # Check for charging
                        key_s = (test_year, (0, first_odpair.id, first_path.id, geo_id), bev_tv.id, f_l, gen_test)
                        charging = 0.0
                        try
                            charging = value(model[:s][key_s...]) * 1000  # Convert MWh to kWh
                        catch
                            charging = 0.0
                        end

                        expected = prev_soc - energy_consumed + charging
                        match = abs(soc_val - expected) < 0.1 ? "✓" : "✗"
                        println("$i      $geo_id    $(round(cum_dist, digits=2))    $(round(soc_val, digits=2))    $(round(expected, digits=2))    $match")
                    end

                    prev_soc = soc_val
                catch
                    println("$i      $geo_id    $(round(cum_dist, digits=2))    NO SOC VAR")
                end
            end
        end
    catch
        println("No flow or variable doesn't exist for gen $gen_test")
    end
end

println("="^80)
