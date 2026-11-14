# Minimal Comparison: constraint_fueling_demand vs constraint_soc_track + constraint_soc_max
# Purpose: Compare BEV shares and energy consumption with minimal constraints
# Based on SM_fleet_verification_compare.jl structure

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
results_dir = joinpath(@__DIR__, "results", "fueling_vs_soc_minimal")
if !isdir(results_dir)
    mkpath(results_dir)
end

# Store comparison results
comparison_results = Dict()

# ============================================================================
# FUNCTION TO RUN A MODEL CONFIGURATION
# ============================================================================
function run_config(config_name::String, use_fueling_demand::Bool, use_soc_constraints::Bool)
    println("\n" * "=" ^ 80)
    println("RUNNING: $config_name")
    println("  constraint_fueling_demand: $use_fueling_demand")
    println("  constraint_soc_track + soc_max: $use_soc_constraints")
    println("=" ^ 80)

    timestamp = Dates.format(now(), "yyyymmdd_HHMMSS")
    case = "$(folder)_$(config_name)_$timestamp"

    # Variables needed - include soc and travel_time for SOC tracking
    relevant_vars = if use_soc_constraints
        ["f", "h", "h_plus", "h_exist", "h_minus", "s", "q_fuel_infr_plus", "soc", "travel_time"]
    else
        ["f", "h", "h_plus", "h_exist", "h_minus", "s", "q_fuel_infr_plus"]
    end

    # Step 1: Load data
    @info "Loading input data..."
    t_start = time()
    data_dict = get_input_data(input_path)
    t_read = time() - t_start
    @info "[OK] Input data loaded in $(round(t_read, digits=2))s"

    # Step 2: Parse data
    @info "Parsing data structures..."
    t_start = time()
    data_structures = parse_data(data_dict)
    t_parse = time() - t_start
    @info "[OK] Data parsed in $(round(t_parse, digits=2))s"

    # Step 3: Create model
    @info "Creating model with variables: $(join(relevant_vars, ", "))"
    t_start = time()
    model, data_structures = create_model(data_structures, case, include_vars=relevant_vars)
    t_create = time() - t_start
    @info "[OK] Model created in $(round(t_create, digits=2))s"
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
    # ADD CONSTRAINTS - Minimal set from fleet verification
    # ============================================================================
    @info "Adding constraints..."

    # Core demand constraint
    t_start = time()
    constraint_demand_coverage(model, data_structures)
    @info "[OK] constraint_demand_coverage added in $(round(time() - t_start, digits=2))s"

    # Vehicle sizing (h >= flow/capacity)
    t_start = time()
    constraint_vehicle_sizing(model, data_structures)
    @info "[OK] constraint_vehicle_sizing added in $(round(time() - t_start, digits=2))s"

    # Vehicle aging (h = h_exist - h_minus + h_plus)
    t_start = time()
    constraint_vehicle_aging(model, data_structures)
    @info "[OK] constraint_vehicle_aging added in $(round(time() - t_start, digits=2))s"

    # Vehicle stock shift (fleet growth rate limited)
    t_start = time()
    constraint_vehicle_stock_shift(model, data_structures)
    @info "[OK] constraint_vehicle_stock_shift added in $(round(time() - t_start, digits=2))s"

    # Fueling infrastructure (always needed for both configs)
    t_start = time()
    constraint_fueling_infrastructure(model, data_structures)
    @info "[OK] constraint_fueling_infrastructure added in $(round(time() - t_start, digits=2))s"

    # CONFIG-SPECIFIC CONSTRAINTS
    if use_fueling_demand
        t_start = time()
        constraint_fueling_demand(model, data_structures)
        @info "[OK] constraint_fueling_demand added in $(round(time() - t_start, digits=2))s"
    else
        @info "[SKIP] constraint_fueling_demand"
    end

    if use_soc_constraints
        t_start = time()
        constraint_soc_track(model, data_structures)
        @info "[OK] constraint_soc_track added in $(round(time() - t_start, digits=2))s"

        t_start = time()
        constraint_soc_max(model, data_structures)
        @info "[OK] constraint_soc_max added in $(round(time() - t_start, digits=2))s"

        t_start = time()
        constraint_travel_time_track(model, data_structures)
        @info "[OK] constraint_travel_time_track added in $(round(time() - t_start, digits=2))s"
    else
        @info "[SKIP] constraint_soc_track, constraint_soc_max, constraint_travel_time_track"
    end

    # Step 5: Add objective WITH fuel costs
    @info "Adding objective function (WITH fuel costs)..."
    t_start = time()
    objective(model, data_structures, true)  # true = include fuel costs
    t_obj = time() - t_start
    @info "[OK] Objective added in $(round(t_obj, digits=2))s"

    # Step 6: Optimize
    @info "Solving..."
    GC.gc()
    t_start = time()
    optimize!(model)
    t_solve = time() - t_start
    @info "[OK] Solved in $(round(t_solve, digits=2))s"

    # Print solution summary
    solution_summary(model)

    # ============================================================================
    # EXTRACT RESULTS
    # ============================================================================
    obj_val = objective_value(model)
    @info "Objective value: $(round(obj_val/1e9, digits=2)) billion EUR"

    # Get modeled years and tech vehicles
    modeled_years = data_structures["modeled_years"]
    g_init = data_structures["g_init"]
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
                tech = tv.technology.id  # 0 = ICEV, 1 = BEV
                if !haskey(fleet_by_tech_year[tech], year)
                    fleet_by_tech_year[tech][year] = 0.0
                end
                fleet_by_tech_year[tech][year] += val
            end
        end
    end

    # Extract fueled energy by year
    fueled_energy_by_year = Dict{Int,Float64}()
    if haskey(model.obj_dict, :s)
        s_dict = model[:s]
        for idx in eachindex(s_dict)
            var = s_dict[idx]
            val = value(var)
            if val > 1e-6
                # First index is year
                year = idx[1]
                if !haskey(fueled_energy_by_year, year)
                    fueled_energy_by_year[year] = 0.0
                end
                fueled_energy_by_year[year] += val
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

    # Calculate total energy
    total_energy_kwh = sum(values(fueled_energy_by_year))

    result = Dict(
        "config_name" => config_name,
        "use_fueling_demand" => use_fueling_demand,
        "use_soc_constraints" => use_soc_constraints,
        "objective_value" => obj_val,
        "solve_time" => t_solve,
        "fleet_by_tech_year" => fleet_by_tech_year,
        "fueled_energy_by_year" => fueled_energy_by_year,
        "bev_share_by_year" => bev_share_by_year,
        "total_energy_kwh" => total_energy_kwh,
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
# RUN BOTH CONFIGURATIONS
# ============================================================================
println("\n" * "=" ^ 80)
println("COMPARISON: constraint_fueling_demand vs SOC constraints")
println("Using MINIMAL constraint set from fleet verification")
println("=" ^ 80)

# Config 1: WITH fueling_demand, WITHOUT SOC constraints
results_fueling = run_config("fueling_demand", true, false)
comparison_results["fueling_demand"] = results_fueling

GC.gc()

# Config 2: WITHOUT fueling_demand, WITH SOC constraints
results_soc = run_config("soc_only", false, true)
comparison_results["soc_only"] = results_soc

# ============================================================================
# COMPARISON SUMMARY
# ============================================================================
println("\n" * "=" ^ 80)
println("COMPARISON SUMMARY")
println("=" ^ 80)

# Years to compare
years = [2020, 2024, 2028, 2032, 2036, 2040, 2044, 2048, 2052, 2056, 2060]

println("\n" * "-" ^ 70)
println("BEV SHARE COMPARISON (%)")
println("-" ^ 70)
@printf("%-6s | %20s | %20s | %12s\n", "Year", "Fueling Demand", "SOC Only", "Difference")
println("-" ^ 70)

for year in years
    bev_fuel = get(results_fueling["bev_share_by_year"], year, 0.0)
    bev_soc = get(results_soc["bev_share_by_year"], year, 0.0)
    diff = bev_soc - bev_fuel
    @printf("%4d   | %18.1f%% | %18.1f%% | %+10.1f%%\n", year, bev_fuel, bev_soc, diff)
end
println("-" ^ 70)

println("\n" * "-" ^ 70)
println("FUELED ENERGY COMPARISON (GWh)")
println("-" ^ 70)
@printf("%-6s | %20s | %20s | %12s\n", "Year", "Fueling Demand", "SOC Only", "Difference")
println("-" ^ 70)

total_fuel = 0.0
total_soc = 0.0
for year in years
    energy_fuel = get(results_fueling["fueled_energy_by_year"], year, 0.0) / 1e6  # kWh to GWh
    energy_soc = get(results_soc["fueled_energy_by_year"], year, 0.0) / 1e6
    diff = energy_soc - energy_fuel
    total_fuel += energy_fuel
    total_soc += energy_soc
    @printf("%4d   | %18.2f | %18.2f | %+10.2f\n", year, energy_fuel, energy_soc, diff)
end
println("-" ^ 70)
@printf("TOTAL  | %18.2f | %18.2f | %+10.2f\n", total_fuel, total_soc, total_soc - total_fuel)
println("-" ^ 70)

println("\n" * "-" ^ 70)
println("OBJECTIVE VALUE COMPARISON")
println("-" ^ 70)
obj_fuel = results_fueling["objective_value"] / 1e9
obj_soc = results_soc["objective_value"] / 1e9
diff_pct = (obj_soc - obj_fuel) / obj_fuel * 100
@printf("Fueling Demand: %12.2f billion EUR\n", obj_fuel)
@printf("SOC Only:       %12.2f billion EUR\n", obj_soc)
@printf("Difference:     %12.2f billion EUR (%+.1f%%)\n", obj_soc - obj_fuel, diff_pct)
println("-" ^ 70)

println("\n" * "-" ^ 70)
println("MODEL SIZE COMPARISON")
println("-" ^ 70)
@printf("Fueling Demand: %12d variables\n", results_fueling["num_variables"])
@printf("SOC Only:       %12d variables\n", results_soc["num_variables"])
println("-" ^ 70)

# Save comparison summary
comparison_file = joinpath(results_dir, "comparison_summary.yaml")
YAML.write_file(comparison_file, comparison_results)
@info "[OK] Comparison summary saved to $comparison_file"

println("\n" * "=" ^ 80)
println("COMPARISON COMPLETE")
println("Results saved to: $results_dir")
println("=" ^ 80)
