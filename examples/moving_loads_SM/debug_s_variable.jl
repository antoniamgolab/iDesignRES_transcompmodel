# Debug script to investigate why energy consumption (s) is 0
# Run this after SM_core_model.jl has completed

using Pkg
Pkg.activate(joinpath(@__DIR__, "../.."))

using YAML, JuMP, Gurobi, Printf, Dates

include(joinpath(@__DIR__, "../../src/TransComp.jl"))
using .TransComp

function analyze_s_variable(model, data_structures)
    println("\n5. S VARIABLE ANALYSIS:")
    println("-" ^ 40)

    s_dict = model[:s]
    println("  Total s variables: $(length(s_dict))")

    # Get first index structure
    first_idx = first(eachindex(s_dict))
    println("  Index structure: $(typeof(first_idx))")
    println("  First index: $first_idx")

    # Get actual axes for mapping indices to values
    modeled_years = data_structures["modeled_years"]

    # Count non-zero values
    nonzero_count = 0
    total_s = 0.0
    s_by_year = Dict{Int,Float64}()
    max_s_val = 0.0
    max_s_idx = nothing

    for idx in eachindex(s_dict)
        val = value(s_dict[idx])
        if val > 1e-9  # Very small threshold
            nonzero_count += 1
            total_s += val

            if val > max_s_val
                max_s_val = val
                max_s_idx = idx
            end

            # Convert index to actual year
            year_idx = idx[1]
            if year_idx <= length(modeled_years)
                year = modeled_years[year_idx]
                s_by_year[year] = get(s_by_year, year, 0.0) + val
            end
        end
    end

    println("  Non-zero s values: $nonzero_count")
    println("  Total s sum: $(round(total_s, digits=2)) kWh")
    println("  Max s value: $(round(max_s_val, digits=4)) kWh at index $max_s_idx")

    println("\n  S by year:")
    for year in sort(collect(keys(s_by_year)))
        println("    $year: $(round(s_by_year[year], digits=2)) kWh")
    end

    # Also check if ANY s value is > 0 at all
    println("\n  Checking first 1000 s values (even tiny ones):")
    count = 0
    for idx in eachindex(s_dict)
        val = value(s_dict[idx])
        if val > 0
            count += 1
            if count <= 10
                println("    idx=$idx, val=$val")
            end
        end
        if count > 1000
            break
        end
    end
    println("  Found $count positive s values (out of first 1000+)")

    return nonzero_count, total_s, s_by_year
end

function analyze_soc_variable(model, data_structures)
    println("\n6. SOC VARIABLE ANALYSIS:")
    println("-" ^ 40)

    soc_dict = model[:soc]
    println("  Total soc variables: $(length(soc_dict))")

    modeled_years = data_structures["modeled_years"]

    # Check for any negative or very small positive SOC values
    min_soc = Inf
    max_soc = -Inf
    soc_count = 0
    zero_soc_count = 0
    soc_by_year = Dict{Int,Float64}()

    for idx in eachindex(soc_dict)
        val = value(soc_dict[idx])
        soc_count += 1

        if val < min_soc
            min_soc = val
        end
        if val > max_soc
            max_soc = val
        end
        if abs(val) < 1e-6
            zero_soc_count += 1
        else
            # Aggregate by year
            year_idx = idx[1]
            if year_idx <= length(modeled_years)
                year = modeled_years[year_idx]
                soc_by_year[year] = get(soc_by_year, year, 0.0) + val
            end
        end
    end

    println("  Min SOC: $(round(min_soc, digits=4))")
    println("  Max SOC: $(round(max_soc, digits=4))")
    println("  Zero SOC count: $zero_soc_count / $soc_count")

    println("\n  SOC by year (sum):")
    for year in sort(collect(keys(soc_by_year)))
        println("    $year: $(round(soc_by_year[year], digits=2)) kWh")
    end
end

function analyze_flow_variable(model, data_structures)
    println("\n7. FLOW BY TECHNOLOGY:")
    println("-" ^ 40)

    f_dict = model[:f]
    tv_list = data_structures["techvehicle_list"]
    modeled_years = data_structures["modeled_years"]
    flow_by_tech_year = Dict{Int, Dict{Int,Float64}}()  # tech -> year -> flow

    for idx in eachindex(f_dict)
        val = value(f_dict[idx])
        if val > 1e-6
            year_idx = idx[1]
            year = modeled_years[year_idx]

            # idx[3] is tv_id index
            tv_idx = idx[3]
            if tv_idx <= length(tv_list)
                tech_id = tv_list[tv_idx].technology.id

                if !haskey(flow_by_tech_year, tech_id)
                    flow_by_tech_year[tech_id] = Dict{Int,Float64}()
                end
                flow_by_tech_year[tech_id][year] = get(flow_by_tech_year[tech_id], year, 0.0) + val * 1000  # Convert to tonnes
            end
        end
    end

    for (tech_id, year_data) in sort(collect(flow_by_tech_year))
        tech_name = tech_id == 0 ? "ICEV" : "BEV"
        println("\n  $tech_name (tech $tech_id):")
        for year in sort(collect(keys(year_data)))
            println("    $year: $(round(year_data[year], digits=0)) tonnes")
        end
    end
end

function main()
    # Configuration
    script_dir = @__DIR__
    folder = "case_20251107_214315_uni_uni"
    input_path = joinpath(@__DIR__, "input_data", folder)

    # Load data
    println("\n" * "=" ^ 80)
    println("DEBUG: Investigating s variable (energy consumption)")
    println("=" ^ 80)

    data_dict = get_input_data(input_path)
    data_structures = parse_data(data_dict)

    # Check key data structures
    println("\n1. DATA STRUCTURES CHECK:")
    println("-" ^ 40)
    println("  fueling_infr_types_list: $(length(data_structures["fueling_infr_types_list"])) items")
    for fit in data_structures["fueling_infr_types_list"]
        println("    - id: $(fit.id), fuel: $(fit.fuel.name), type: $(fit.fueling_type)")
    end

    println("\n  techvehicle_list: $(length(data_structures["techvehicle_list"])) vehicles")
    for tv in data_structures["techvehicle_list"]
        println("    - id: $(tv.id), tech: $(tv.technology.id) ($(tv.technology.name)), fuel: $(tv.technology.fuel.name)")
        println("      tank_capacity[1]: $(tv.tank_capacity[1]) kWh")
        println("      spec_cons[1]: $(tv.spec_cons[1]) kWh/km")
    end

    # Check path lengths
    println("\n2. PATH LENGTH CHECK:")
    println("-" ^ 40)
    path_list = data_structures["path_list"]
    path_lengths = [p.length for p in path_list]
    println("  Number of paths: $(length(path_list))")
    println("  Min path length: $(round(minimum(path_lengths), digits=1)) km")
    println("  Max path length: $(round(maximum(path_lengths), digits=1)) km")
    println("  Mean path length: $(round(sum(path_lengths)/length(path_lengths), digits=1)) km")

    # For BEV: tank_capacity = 1187 kWh, spec_cons = 2.06 kWh/km
    # Range on 50% charge = 1187 * 0.5 / 2.06 = 288 km
    bev_tv = data_structures["techvehicle_list"][findfirst(tv -> tv.technology.id == 1, data_structures["techvehicle_list"])]
    bev_range_50pct = bev_tv.tank_capacity[1] * 0.5 / bev_tv.spec_cons[1]
    println("\n  BEV range at 50% SOC: $(round(bev_range_50pct, digits=1)) km")
    paths_needing_charge = count(p -> p.length > bev_range_50pct, path_list)
    println("  Paths longer than BEV 50% range: $paths_needing_charge / $(length(path_list))")

    # Create and solve model
    println("\n3. RUNNING MODEL (simplified for debug)...")
    println("-" ^ 40)

    relevant_vars = ["f", "h", "h_plus", "h_exist", "h_minus", "s", "q_fuel_infr_plus", "q_fuel_infr_plus_by_route", "soc"]
    model, data_structures = create_model(data_structures, "debug_s", include_vars=relevant_vars)

    # Add constraints
    constraint_demand_coverage(model, data_structures)
    constraint_vehicle_sizing(model, data_structures)
    constraint_vehicle_aging(model, data_structures)
    constraint_vehicle_stock_shift(model, data_structures)
    constraint_fueling_infrastructure(model, data_structures)
    constraint_fueling_infrastructure_expansion_shift(model, data_structures)
    constraint_soc_track(model, data_structures)
    constraint_soc_max(model, data_structures)

    # Add objective
    objective(model, data_structures, true)

    # Solver settings
    set_optimizer_attribute(model, "Method", 2)
    set_optimizer_attribute(model, "Crossover", 0)
    set_optimizer_attribute(model, "MIPGap", 0.01)
    set_optimizer_attribute(model, "NumericFocus", 3)

    # Solve
    optimize!(model)

    println("\n4. SOLUTION ANALYSIS:")
    println("-" ^ 40)
    println("  Status: $(termination_status(model))")
    println("  Objective: $(round(objective_value(model)/1e9, digits=4)) billion EUR")

    # Analyze variables
    analyze_s_variable(model, data_structures)
    analyze_soc_variable(model, data_structures)
    analyze_flow_variable(model, data_structures)

    println("\n" * "=" ^ 80)
    println("DEBUG COMPLETE")
    println("=" ^ 80)
end

main()
