# Comparison: SOC constraints with EQUAL tank capacities
# REDUCED MODEL: Only first 30 OD pairs for faster testing
# Using ORIGINAL capital costs

using Pkg
Pkg.activate(joinpath(@__DIR__, "../.."))

using YAML, JuMP, Gurobi, Printf, Dates

include(joinpath(@__DIR__, "../../src/TransComp.jl"))
using .TransComp

# ============================================================================
# CONFIGURATION
# ============================================================================
script_dir = @__DIR__
folder = "case_20251107_214315_uni_uni"
input_path = joinpath(@__DIR__, "input_data", folder)

# NUMBER OF OD PAIRS TO USE (reduced for testing)
MAX_ODPAIRS = 30

# Results storage
results_dir = joinpath(@__DIR__, "results", "equal_tank_30_routes")
if !isdir(results_dir)
    mkpath(results_dir)
end

# Store comparison results
comparison_results = Dict()

# ============================================================================
# FUNCTION TO REDUCE OD PAIRS
# ============================================================================
function reduce_odpairs!(data_structures::Dict, max_pairs::Int)
    odpairs = data_structures["odpair_list"]
    original_count = length(odpairs)

    if original_count <= max_pairs
        @info "OD pairs ($original_count) already <= $max_pairs, no reduction needed"
        return
    end

    # Keep only first max_pairs
    reduced_odpairs = odpairs[1:max_pairs]
    data_structures["odpair_list"] = reduced_odpairs

    # Also need to update path_list to only include paths from these OD pairs
    kept_path_ids = Set{Int}()
    for r in reduced_odpairs
        for path in r.paths
            push!(kept_path_ids, path.id)
        end
    end

    original_paths = data_structures["path_list"]
    reduced_paths = filter(p -> p.id in kept_path_ids, original_paths)
    data_structures["path_list"] = reduced_paths

    @info "Reduced OD pairs: $original_count -> $(length(reduced_odpairs))"
    @info "Reduced paths: $(length(original_paths)) -> $(length(reduced_paths))"

    # Update p_r_k_pairs and p_r_k_g_pairs
    # These will be regenerated in create_model, but we need to update them here
    # for any pre-processing that uses them
end

# ============================================================================
# FUNCTION TO EQUALIZE TANK CAPACITIES
# ============================================================================
function equalize_tank_capacities!(data_structures::Dict, target_capacity::Float64)
    @info "Equalizing tank capacities to $(target_capacity) kWh..."
    tv_list = data_structures["techvehicle_list"]

    for tv in tv_list
        tech_id = tv.technology.id
        original_capacity = tv.tank_capacity[1]
        @info "  TechVehicle $(tv.id): Tech $(tech_id), Original tank: $(original_capacity) kWh"
        for i in 1:length(tv.tank_capacity)
            tv.tank_capacity[i] = target_capacity
        end
        @info "  -> New tank capacity: $(tv.tank_capacity[1]) kWh"
    end
end

# ============================================================================
# FUNCTION TO RUN A MODEL CONFIGURATION
# ============================================================================
function run_config(config_name::String, equalize_tanks::Bool, target_tank_capacity::Float64)
    println("\n" * "=" ^ 80)
    println("RUNNING: $config_name (30 OD pairs)")
    println("  Tank capacity equalization: $equalize_tanks")
    if equalize_tanks
        println("  Target tank capacity: $target_tank_capacity kWh")
    end
    println("=" ^ 80)

    timestamp = Dates.format(now(), "yyyymmdd_HHMMSS")
    case = "$(folder)_$(config_name)_30routes_$timestamp"

    # Variables needed for SOC tracking
    relevant_vars = ["f", "h", "h_plus", "h_exist", "h_minus", "s", "q_fuel_infr_plus", "soc", "travel_time"]

    # Step 1: Load data
    @info "Loading input data..."
    t_start = time()
    data_dict = get_input_data(input_path)
    @info "[OK] Input data loaded in $(round(time() - t_start, digits=2))s"

    # Step 2: Parse data
    @info "Parsing data structures..."
    t_start = time()
    data_structures = parse_data(data_dict)
    @info "[OK] Data parsed in $(round(time() - t_start, digits=2))s"

    # Step 2.5: REDUCE OD PAIRS
    reduce_odpairs!(data_structures, MAX_ODPAIRS)

    # Step 2.6: EQUALIZE TANK CAPACITIES if requested
    if equalize_tanks
        equalize_tank_capacities!(data_structures, target_tank_capacity)
    end

    # Print tank capacities for verification
    tv_list = data_structures["techvehicle_list"]
    println("\nTank Capacities:")
    for tv in tv_list
        println("  TV $(tv.id) (Tech $(tv.technology.id)): $(tv.tank_capacity[1]) kWh")
    end

    # Step 3: Create model
    @info "Creating model..."
    t_start = time()
    model, data_structures = create_model(data_structures, case, include_vars=relevant_vars)
    @info "[OK] Model created in $(round(time() - t_start, digits=2))s"
    @info "Number of variables: $(num_variables(model))"

    # Step 4: Configure solver
    set_optimizer_attribute(model, "Method", 2)
    set_optimizer_attribute(model, "MIPFocus", 1)
    set_optimizer_attribute(model, "MIPGap", 0.01)
    set_optimizer_attribute(model, "NumericFocus", 3)
    set_optimizer_attribute(model, "ScaleFlag", 2)
    set_optimizer_attribute(model, "FeasibilityTol", 1e-5)
    set_optimizer_attribute(model, "OptimalityTol", 1e-5)
    set_optimizer_attribute(model, "Crossover", 0)
    set_optimizer_attribute(model, "BarConvTol", 1e-6)

    # ============================================================================
    # ADD CONSTRAINTS
    # ============================================================================
    @info "Adding constraints..."

    t_start = time()
    constraint_demand_coverage(model, data_structures)
    @info "[OK] constraint_demand_coverage added in $(round(time() - t_start, digits=2))s"

    t_start = time()
    constraint_vehicle_sizing(model, data_structures)
    @info "[OK] constraint_vehicle_sizing added in $(round(time() - t_start, digits=2))s"

    t_start = time()
    constraint_vehicle_aging(model, data_structures)
    @info "[OK] constraint_vehicle_aging added in $(round(time() - t_start, digits=2))s"

    t_start = time()
    constraint_vehicle_stock_shift(model, data_structures)
    @info "[OK] constraint_vehicle_stock_shift added in $(round(time() - t_start, digits=2))s"

    t_start = time()
    constraint_fueling_infrastructure(model, data_structures)
    @info "[OK] constraint_fueling_infrastructure added in $(round(time() - t_start, digits=2))s"

    # SOC CONSTRAINTS
    t_start = time()
    constraint_soc_track(model, data_structures)
    @info "[OK] constraint_soc_track added in $(round(time() - t_start, digits=2))s"

    t_start = time()
    constraint_soc_max(model, data_structures)
    @info "[OK] constraint_soc_max added in $(round(time() - t_start, digits=2))s"

    t_start = time()
    constraint_travel_time_track(model, data_structures)
    @info "[OK] constraint_travel_time_track added in $(round(time() - t_start, digits=2))s"

    # Step 5: Add objective WITH fuel costs
    @info "Adding objective function (WITH fuel costs)..."
    t_start = time()
    objective(model, data_structures, true)
    @info "[OK] Objective added in $(round(time() - t_start, digits=2))s"

    # Step 6: Optimize
    @info "Solving..."
    GC.gc()
    t_start = time()
    optimize!(model)
    t_solve = time() - t_start
    @info "[OK] Solved in $(round(t_solve, digits=2))s"

    solution_summary(model)

    # ============================================================================
    # EXTRACT RESULTS
    # ============================================================================
    obj_val = objective_value(model)
    @info "Objective value: $(round(obj_val/1e9, digits=4)) billion EUR"

    modeled_years = data_structures["modeled_years"]

    # Extract fleet by technology (0=ICEV, 1=BEV) and year
    fleet_by_tech_year = Dict(0 => Dict{Int,Float64}(), 1 => Dict{Int,Float64}())

    h_dict = model[:h]
    for idx in eachindex(h_dict)
        var = h_dict[idx]
        val = value(var)
        if val > 1e-6
            year = idx[1]
            tv_id = idx[3]

            tv_idx = findfirst(tv -> tv.id == tv_id, tv_list)
            if tv_idx !== nothing
                tv = tv_list[tv_idx]
                tech = tv.technology.id
                if !haskey(fleet_by_tech_year[tech], year)
                    fleet_by_tech_year[tech][year] = 0.0
                end
                fleet_by_tech_year[tech][year] += val
            end
        end
    end

    # Calculate BEV share by year
    bev_share_by_year = Dict{Int,Float64}()
    for year in modeled_years
        icev = get(fleet_by_tech_year[0], year, 0.0)
        bev = get(fleet_by_tech_year[1], year, 0.0)
        total = icev + bev
        bev_share_by_year[year] = total > 0 ? (bev / total * 100) : 0.0
    end

    result = Dict(
        "config_name" => config_name,
        "num_odpairs" => MAX_ODPAIRS,
        "equalize_tanks" => equalize_tanks,
        "target_tank_capacity" => equalize_tanks ? target_tank_capacity : "original",
        "objective_value" => obj_val,
        "solve_time" => t_solve,
        "fleet_by_tech_year" => fleet_by_tech_year,
        "bev_share_by_year" => bev_share_by_year,
        "num_variables" => num_variables(model)
    )

    # Save individual results
    results_file = joinpath(results_dir, "$(config_name)_results.yaml")
    YAML.write_file(results_file, result)
    @info "[OK] Saved results to $results_file"

    GC.gc()
    return result
end

# ============================================================================
# RUN COMPARISON
# ============================================================================
println("\n" * "=" ^ 80)
println("COMPARISON: SOC constraints with ORIGINAL vs EQUAL tank capacities")
println("REDUCED MODEL: $MAX_ODPAIRS OD pairs")
println("=" ^ 80)

# Config 1: Original tank capacities (ICEV=5529, BEV=1187)
results_original = run_config("soc_original_tanks", false, 0.0)
comparison_results["original"] = results_original

GC.gc()

# Config 2: Equal tank capacities - use BEV's capacity (1187) for both
results_equal_bev = run_config("soc_equal_bev_tank", true, 1187.0)
comparison_results["equal_bev_tank"] = results_equal_bev

GC.gc()

# Config 3: Equal tank capacities - use ICEV's capacity (5529) for both
results_equal_icev = run_config("soc_equal_icev_tank", true, 5529.0)
comparison_results["equal_icev_tank"] = results_equal_icev

# ============================================================================
# COMPARISON SUMMARY
# ============================================================================
println("\n" * "=" ^ 80)
println("COMPARISON SUMMARY ($MAX_ODPAIRS OD pairs)")
println("=" ^ 80)

years = [2020, 2024, 2028, 2032, 2036, 2040, 2044, 2048, 2052, 2056, 2060]

println("\n" * "-" ^ 90)
println("BEV SHARE COMPARISON (%)")
println("-" ^ 90)
@printf("%-6s | %18s | %18s | %18s\n", "Year", "Original Tanks", "Equal (BEV=1187)", "Equal (ICEV=5529)")
println("-" ^ 90)

for year in years
    bev_orig = get(results_original["bev_share_by_year"], year, 0.0)
    bev_eq_bev = get(results_equal_bev["bev_share_by_year"], year, 0.0)
    bev_eq_icev = get(results_equal_icev["bev_share_by_year"], year, 0.0)
    @printf("%4d   | %16.1f%% | %16.1f%% | %16.1f%%\n", year, bev_orig, bev_eq_bev, bev_eq_icev)
end
println("-" ^ 90)

println("\n" * "-" ^ 90)
println("OBJECTIVE VALUE COMPARISON")
println("-" ^ 90)
obj_orig = results_original["objective_value"] / 1e9
obj_eq_bev = results_equal_bev["objective_value"] / 1e9
obj_eq_icev = results_equal_icev["objective_value"] / 1e9
@printf("Original Tanks:     %12.4f billion EUR\n", obj_orig)
@printf("Equal (BEV=1187):   %12.4f billion EUR\n", obj_eq_bev)
@printf("Equal (ICEV=5529):  %12.4f billion EUR\n", obj_eq_icev)
println("-" ^ 90)

# Save comparison summary
comparison_file = joinpath(results_dir, "comparison_summary.yaml")
YAML.write_file(comparison_file, comparison_results)
@info "[OK] Comparison summary saved to $comparison_file"

println("\n" * "=" ^ 80)
println("COMPARISON COMPLETE")
println("Results saved to: $results_dir")
println("=" ^ 80)
