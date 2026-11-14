# Comparison: SOC constraints vs Fueling Demand constraint
# FULL MODEL: All OD pairs

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

# Results storage
results_dir = joinpath(@__DIR__, "results", "soc_vs_fueling_full")
if !isdir(results_dir)
    mkpath(results_dir)
end

# Store comparison results
comparison_results = Dict()

# ============================================================================
# FUNCTION TO RUN SOC CONSTRAINTS MODEL
# ============================================================================
function run_soc_constraints(config_name::String)
    println("\n" * "=" ^ 80)
    println("RUNNING: $config_name (SOC constraints: soc_track + soc_max) - FULL MODEL")
    println("=" ^ 80)

    timestamp = Dates.format(now(), "yyyymmdd_HHMMSS")
    case = "$(folder)_$(config_name)_full_$timestamp"

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

    num_odpairs = length(data_structures["odpair_list"])
    @info "Using ALL $num_odpairs OD pairs"

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
    # ADD CONSTRAINTS - SOC BASED
    # ============================================================================
    @info "Adding constraints (SOC-based)..."

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

    # SOC CONSTRAINTS (instead of fueling_demand)
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
    return extract_results(model, data_structures, config_name, t_solve, "soc_constraints", num_odpairs)
end

# ============================================================================
# FUNCTION TO RUN FUELING DEMAND MODEL
# ============================================================================
function run_fueling_demand(config_name::String)
    println("\n" * "=" ^ 80)
    println("RUNNING: $config_name (Fueling Demand constraint) - FULL MODEL")
    println("=" ^ 80)

    timestamp = Dates.format(now(), "yyyymmdd_HHMMSS")
    case = "$(folder)_$(config_name)_full_$timestamp"

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

    num_odpairs = length(data_structures["odpair_list"])
    @info "Using ALL $num_odpairs OD pairs"

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
    # ADD CONSTRAINTS - FUELING DEMAND BASED
    # ============================================================================
    @info "Adding constraints (Fueling demand-based)..."

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

    # FUELING DEMAND CONSTRAINT (instead of SOC constraints)
    t_start = time()
    constraint_fueling_demand(model, data_structures)
    @info "[OK] constraint_fueling_demand added in $(round(time() - t_start, digits=2))s"

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
    return extract_results(model, data_structures, config_name, t_solve, "fueling_demand", num_odpairs)
end

# ============================================================================
# FUNCTION TO EXTRACT RESULTS
# ============================================================================
function extract_results(model, data_structures, config_name, t_solve, constraint_type, num_odpairs)
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
        "num_odpairs" => num_odpairs,
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
println("COMPARISON: SOC constraints vs Fueling Demand constraint")
println("FULL MODEL: All OD pairs")
println("=" ^ 80)

# Config 1: SOC constraints (soc_track + soc_max)
results_soc = run_soc_constraints("soc_constraints")
comparison_results["soc_constraints"] = results_soc

GC.gc()

# Config 2: Fueling Demand constraint
results_fueling = run_fueling_demand("fueling_demand")
comparison_results["fueling_demand"] = results_fueling

# ============================================================================
# COMPARISON SUMMARY
# ============================================================================
println("\n" * "=" ^ 80)
println("COMPARISON SUMMARY (FULL MODEL)")
println("=" ^ 80)

years = [2020, 2024, 2028, 2032, 2036, 2040, 2044, 2048, 2052, 2056, 2060]

println("\n" * "-" ^ 70)
println("BEV SHARE COMPARISON (%)")
println("-" ^ 70)
@printf("%-6s | %20s | %20s | %10s\n", "Year", "SOC Constraints", "Fueling Demand", "Difference")
println("-" ^ 70)

for year in years
    bev_soc = get(results_soc["bev_share_by_year"], year, 0.0)
    bev_fueling = get(results_fueling["bev_share_by_year"], year, 0.0)
    diff = bev_fueling - bev_soc
    @printf("%4d   | %18.1f%% | %18.1f%% | %+9.1f%%\n", year, bev_soc, bev_fueling, diff)
end
println("-" ^ 70)

println("\n" * "-" ^ 70)
println("OBJECTIVE VALUE COMPARISON")
println("-" ^ 70)
obj_soc = results_soc["objective_value"] / 1e9
obj_fueling = results_fueling["objective_value"] / 1e9
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
    energy_soc = get(results_soc["total_energy_by_year"], year, 0.0)
    energy_fueling = get(results_fueling["total_energy_by_year"], year, 0.0)
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
