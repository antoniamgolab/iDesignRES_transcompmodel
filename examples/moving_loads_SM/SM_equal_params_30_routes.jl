# Comparison: SOC constraints vs Fueling Demand
# WITH EQUAL VEHICLE PARAMETERS: BEV uses ICEV's spec_cons, W, AnnualRange
# REDUCED MODEL: Only first 30 OD pairs for faster testing

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
results_dir = joinpath(@__DIR__, "results", "equal_params_30_routes")
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
end

# ============================================================================
# FUNCTION TO EQUALIZE VEHICLE PARAMETERS
# Copy ICEV's spec_cons, W, AnnualRange to BEV
# ============================================================================
function equalize_vehicle_params!(data_structures::Dict)
    tv_list = data_structures["techvehicle_list"]

    # Find ICEV (tech_id = 0) and BEV (tech_id = 1)
    icev = nothing
    bev = nothing
    for tv in tv_list
        if tv.technology.id == 0
            icev = tv
        elseif tv.technology.id == 1
            bev = tv
        end
    end

    if icev === nothing || bev === nothing
        @error "Could not find both ICEV and BEV in techvehicle_list"
        return
    end

    println("\n" * "=" ^ 60)
    println("EQUALIZING VEHICLE PARAMETERS")
    println("=" ^ 60)

    # Print original values
    println("\nOriginal Values:")
    println("  ICEV (Tech 0):")
    println("    spec_cons[1]: $(icev.spec_cons[1])")
    println("    W[1]: $(icev.W[1])")
    println("    AnnualRange[1]: $(icev.AnnualRange[1])")
    println("    tank_capacity[1]: $(icev.tank_capacity[1])")

    println("  BEV (Tech 1):")
    println("    spec_cons[1]: $(bev.spec_cons[1])")
    println("    W[1]: $(bev.W[1])")
    println("    AnnualRange[1]: $(bev.AnnualRange[1])")
    println("    tank_capacity[1]: $(bev.tank_capacity[1])")

    # Copy ICEV parameters to BEV
    println("\nCopying ICEV parameters to BEV...")

    # spec_cons
    for i in 1:length(bev.spec_cons)
        if i <= length(icev.spec_cons)
            bev.spec_cons[i] = icev.spec_cons[i]
        else
            bev.spec_cons[i] = icev.spec_cons[end]
        end
    end

    # W (payload)
    for i in 1:length(bev.W)
        if i <= length(icev.W)
            bev.W[i] = icev.W[i]
        else
            bev.W[i] = icev.W[end]
        end
    end

    # AnnualRange
    for i in 1:length(bev.AnnualRange)
        if i <= length(icev.AnnualRange)
            bev.AnnualRange[i] = icev.AnnualRange[i]
        else
            bev.AnnualRange[i] = icev.AnnualRange[end]
        end
    end

    # Also equalize tank_capacity for fair comparison
    for i in 1:length(bev.tank_capacity)
        if i <= length(icev.tank_capacity)
            bev.tank_capacity[i] = icev.tank_capacity[i]
        else
            bev.tank_capacity[i] = icev.tank_capacity[end]
        end
    end

    # Print new values
    println("\nNew Values (after equalization):")
    println("  BEV (Tech 1) now uses ICEV parameters:")
    println("    spec_cons[1]: $(bev.spec_cons[1])")
    println("    W[1]: $(bev.W[1])")
    println("    AnnualRange[1]: $(bev.AnnualRange[1])")
    println("    tank_capacity[1]: $(bev.tank_capacity[1])")
    println("=" ^ 60)
end

# ============================================================================
# FUNCTION TO RUN SOC CONSTRAINTS MODEL
# ============================================================================
function run_soc_constraints(config_name::String, equalize_params::Bool)
    println("\n" * "=" ^ 80)
    println("RUNNING: $config_name (SOC constraints: soc_track + soc_max)")
    if equalize_params
        println("  WITH EQUAL PARAMETERS: BEV uses ICEV's spec_cons, W, AnnualRange")
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

    # Step 2.6: EQUALIZE PARAMETERS if requested
    if equalize_params
        equalize_vehicle_params!(data_structures)
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

    # Add constraints
    @info "Adding constraints (SOC-based)..."

    constraint_demand_coverage(model, data_structures)
    constraint_vehicle_sizing(model, data_structures)
    constraint_vehicle_aging(model, data_structures)
    constraint_vehicle_stock_shift(model, data_structures)
    constraint_fueling_infrastructure(model, data_structures)

    # SOC CONSTRAINTS
    constraint_soc_track(model, data_structures)
    constraint_soc_max(model, data_structures)
    constraint_travel_time_track(model, data_structures)

    # Add objective WITH fuel costs
    @info "Adding objective function (WITH fuel costs)..."
    objective(model, data_structures, true)

    # Optimize
    @info "Solving..."
    GC.gc()
    t_start = time()
    optimize!(model)
    t_solve = time() - t_start
    @info "[OK] Solved in $(round(t_solve, digits=2))s"

    solution_summary(model)

    return extract_results(model, data_structures, config_name, t_solve, "soc_constraints", equalize_params)
end

# ============================================================================
# FUNCTION TO RUN FUELING DEMAND MODEL
# ============================================================================
function run_fueling_demand(config_name::String, equalize_params::Bool)
    println("\n" * "=" ^ 80)
    println("RUNNING: $config_name (Fueling Demand constraint)")
    if equalize_params
        println("  WITH EQUAL PARAMETERS: BEV uses ICEV's spec_cons, W, AnnualRange")
    end
    println("=" ^ 80)

    timestamp = Dates.format(now(), "yyyymmdd_HHMMSS")
    case = "$(folder)_$(config_name)_30routes_$timestamp"

    # Variables needed
    relevant_vars = ["f", "h", "h_plus", "h_exist", "h_minus", "s", "q_fuel_infr_plus"]

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

    # Step 2.6: EQUALIZE PARAMETERS if requested
    if equalize_params
        equalize_vehicle_params!(data_structures)
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

    # Add constraints
    @info "Adding constraints (Fueling demand-based)..."

    constraint_demand_coverage(model, data_structures)
    constraint_vehicle_sizing(model, data_structures)
    constraint_vehicle_aging(model, data_structures)
    constraint_vehicle_stock_shift(model, data_structures)
    constraint_fueling_infrastructure(model, data_structures)

    # FUELING DEMAND CONSTRAINT
    constraint_fueling_demand(model, data_structures)

    # Add objective WITH fuel costs
    @info "Adding objective function (WITH fuel costs)..."
    objective(model, data_structures, true)

    # Optimize
    @info "Solving..."
    GC.gc()
    t_start = time()
    optimize!(model)
    t_solve = time() - t_start
    @info "[OK] Solved in $(round(t_solve, digits=2))s"

    solution_summary(model)

    return extract_results(model, data_structures, config_name, t_solve, "fueling_demand", equalize_params)
end

# ============================================================================
# FUNCTION TO EXTRACT RESULTS
# ============================================================================
function extract_results(model, data_structures, config_name, t_solve, constraint_type, equalize_params)
    obj_val = objective_value(model)
    @info "Objective value: $(round(obj_val/1e9, digits=4)) billion EUR"

    modeled_years = data_structures["modeled_years"]
    tv_list = data_structures["techvehicle_list"]

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

    # Extract total energy charged (s variable)
    total_energy_by_year = Dict{Int,Float64}()
    s_dict = model[:s]
    for idx in eachindex(s_dict)
        var = s_dict[idx]
        val = value(var)
        if val > 1e-6
            year = idx[1]
            if !haskey(total_energy_by_year, year)
                total_energy_by_year[year] = 0.0
            end
            total_energy_by_year[year] += val
        end
    end

    result = Dict(
        "config_name" => config_name,
        "constraint_type" => constraint_type,
        "equalize_params" => equalize_params,
        "num_odpairs" => MAX_ODPAIRS,
        "objective_value" => obj_val,
        "solve_time" => t_solve,
        "fleet_by_tech_year" => fleet_by_tech_year,
        "bev_share_by_year" => bev_share_by_year,
        "total_energy_by_year" => total_energy_by_year,
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
println("COMPARISON: SOC constraints vs Fueling Demand")
println("WITH EQUAL VEHICLE PARAMETERS (BEV uses ICEV's spec_cons, W, AnnualRange)")
println("REDUCED MODEL: $MAX_ODPAIRS OD pairs")
println("=" ^ 80)

# Config 1: SOC constraints with equal parameters
results_soc_equal = run_soc_constraints("soc_equal_params", true)
comparison_results["soc_equal_params"] = results_soc_equal

GC.gc()

# Config 2: Fueling Demand with equal parameters
results_fueling_equal = run_fueling_demand("fueling_equal_params", true)
comparison_results["fueling_equal_params"] = results_fueling_equal

# ============================================================================
# COMPARISON SUMMARY
# ============================================================================
println("\n" * "=" ^ 80)
println("COMPARISON SUMMARY ($MAX_ODPAIRS OD pairs)")
println("WITH EQUAL PARAMETERS: BEV uses ICEV's spec_cons, W, AnnualRange")
println("=" ^ 80)

years = [2020, 2024, 2028, 2032, 2036, 2040, 2044, 2048, 2052, 2056, 2060]

println("\n" * "-" ^ 70)
println("BEV SHARE COMPARISON (%)")
println("-" ^ 70)
@printf("%-6s | %20s | %20s | %10s\n", "Year", "SOC Constraints", "Fueling Demand", "Difference")
println("-" ^ 70)

for year in years
    bev_soc = get(results_soc_equal["bev_share_by_year"], year, 0.0)
    bev_fueling = get(results_fueling_equal["bev_share_by_year"], year, 0.0)
    diff = bev_fueling - bev_soc
    @printf("%4d   | %18.1f%% | %18.1f%% | %+9.1f%%\n", year, bev_soc, bev_fueling, diff)
end
println("-" ^ 70)

println("\n" * "-" ^ 70)
println("OBJECTIVE VALUE COMPARISON")
println("-" ^ 70)
obj_soc = results_soc_equal["objective_value"] / 1e9
obj_fueling = results_fueling_equal["objective_value"] / 1e9
obj_diff = obj_fueling - obj_soc
@printf("SOC Constraints:   %12.4f billion EUR\n", obj_soc)
@printf("Fueling Demand:    %12.4f billion EUR\n", obj_fueling)
@printf("Difference:        %12.4f billion EUR (%+.2f%%)\n", obj_diff, (obj_diff/obj_soc)*100)
println("-" ^ 70)

println("\n" * "-" ^ 70)
println("TOTAL ENERGY CHARGED COMPARISON (kWh)")
println("-" ^ 70)
@printf("%-6s | %20s | %20s | %15s\n", "Year", "SOC Constraints", "Fueling Demand", "Difference")
println("-" ^ 70)

for year in years
    energy_soc = get(results_soc_equal["total_energy_by_year"], year, 0.0)
    energy_fueling = get(results_fueling_equal["total_energy_by_year"], year, 0.0)
    diff = energy_fueling - energy_soc
    @printf("%4d   | %18.1f | %18.1f | %+14.1f\n", year, energy_soc, energy_fueling, diff)
end
println("-" ^ 70)

# Save comparison summary
comparison_file = joinpath(results_dir, "comparison_summary.yaml")
YAML.write_file(comparison_file, comparison_results)
@info "[OK] Comparison summary saved to $comparison_file"

println("\n" * "=" ^ 80)
println("COMPARISON COMPLETE")
println("Results saved to: $results_dir")
println("=" ^ 80)
