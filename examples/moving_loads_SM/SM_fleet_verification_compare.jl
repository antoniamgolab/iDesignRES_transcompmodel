# Fleet Verification Comparison Script
# Purpose: Compare system costs WITH and WITHOUT fuel costs (constraint_fueling_demand)
# Runs each scenario twice: once without fuel costs, once with fuel costs

using Pkg
Pkg.activate(joinpath(@__DIR__, "../.."))

using YAML, JuMP, Gurobi, Printf, Dates

include(joinpath(@__DIR__, "../../src/TransComp.jl"))
using .TransComp

# ============================================================================
# CONFIGURATION
# ============================================================================
script_dir = @__DIR__
scenarios_to_run = ["scenario_000", "scenario_001", "scenario_002"]

# Results storage
results_dir = joinpath(@__DIR__, "results", "fleet_verification_compare")
if !isdir(results_dir)
    mkpath(results_dir)
end

# Store comparison results
comparison_results = Dict()

# ============================================================================
# FUNCTION TO RUN A SINGLE SCENARIO
# ============================================================================
function run_scenario(scenario::String, include_fuel_costs::Bool, results_dir::String)
    println("\n" * "="^80)
    config_name = include_fuel_costs ? "WITH fuel costs" : "WITHOUT fuel costs"
    println("RUNNING: $scenario - $config_name")
    println("="^80)

    input_path = joinpath(@__DIR__, "input_data", "uncertainty_scenarios", scenario)

    if !isdir(input_path)
        @warn "Scenario directory not found: $input_path"
        return nothing
    end

    suffix = include_fuel_costs ? "with_fuel" : "no_fuel"
    timestamp = Dates.format(now(), "yyyymmdd_HHMMSS")
    case = "fleet_$(scenario)_$(suffix)_$timestamp"

    # Variables needed - ALWAYS include 's' for energy consumption
    relevant_vars = ["f", "h", "h_plus", "h_exist", "h_minus", "s"]

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

    # Step 3: Create model with variables including 's'
    @info "Creating model with variables: $(join(relevant_vars, ", "))"
    t_start = time()
    model, data_structures = create_model(data_structures, case, include_vars=relevant_vars)
    t_create = time() - t_start
    @info "[OK] Model created in $(round(t_create, digits=2))s"

    # Verify 's' variable was created
    if haskey(model.obj_dict, :s)
        @info "[OK] Variable 's' (energy consumption) successfully created"
    else
        @warn "Variable 's' was NOT created - fuel costs will not be included!"
    end

    @info "Number of variables: $(num_variables(model))"

    # Step 4: Configure solver
    set_optimizer_attribute(model, "Method", 2)
    set_optimizer_attribute(model, "MIPFocus", 1)
    set_optimizer_attribute(model, "MIPGap", 0.01)
    set_optimizer_attribute(model, "NumericFocus", 3)
    set_optimizer_attribute(model, "ScaleFlag", 2)
    set_optimizer_attribute(model, "Crossover", 0)

    # ============================================================================
    # ADD CONSTRAINTS
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

    # Fueling demand - ONLY if include_fuel_costs is true
    if include_fuel_costs
        t_start = time()
        constraint_fueling_demand(model, data_structures)
        @info "[OK] constraint_fueling_demand added in $(round(time() - t_start, digits=2))s"
    else
        @info "[SKIP] constraint_fueling_demand (running without fuel costs)"
    end

    @info "Total constraints: $(num_constraints(model; count_variable_in_set_constraints=false))"

    # Step 5: Add objective
    @info "Adding objective function..."
    t_start = time()
    objective(model, data_structures, false)
    t_obj = time() - t_start
    @info "[OK] Objective added in $(round(t_obj, digits=2))s"

    # Step 6: Optimize
    @info "Solving..."
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
    @info "Objective value: $(obj_val)"

    # Get modeled years
    modeled_years = data_structures["modeled_years"]
    tv_list = data_structures["techvehicle_list"]

    # Extract fleet by techvehicle and year
    fleet_by_tv_year = Dict()
    for tv in tv_list
        fleet_by_tv_year[tv.id] = Dict()
        for year in modeled_years
            fleet_by_tv_year[tv.id][year] = 0.0
        end
    end

    for (key, var) in model[:h].data
        y = key[1]
        tv_id = key[3]
        val = value(var)
        if haskey(fleet_by_tv_year, tv_id) && haskey(fleet_by_tv_year[tv_id], y)
            fleet_by_tv_year[tv_id][y] += val
        end
    end

    # Save results
    scenario_results_dir = joinpath(results_dir, scenario, suffix)
    if !isdir(scenario_results_dir)
        mkpath(scenario_results_dir)
    end
    save_results(model, case, data_structures, true, scenario_results_dir, scenario)
    @info "[OK] Results saved to $scenario_results_dir"

    GC.gc()

    return Dict(
        "objective_value" => obj_val,
        "fleet_by_tv_year" => fleet_by_tv_year,
        "has_s_variable" => haskey(model.obj_dict, :s),
        "num_variables" => num_variables(model),
        "num_constraints" => num_constraints(model; count_variable_in_set_constraints=false)
    )
end

# ============================================================================
# RUN ALL SCENARIOS - BOTH CONFIGURATIONS
# ============================================================================
for scenario in scenarios_to_run
    comparison_results[scenario] = Dict()

    # Run WITHOUT fuel costs first
    result_no_fuel = run_scenario(scenario, false, results_dir)
    if result_no_fuel !== nothing
        comparison_results[scenario]["no_fuel"] = result_no_fuel
    end

    # Run WITH fuel costs
    result_with_fuel = run_scenario(scenario, true, results_dir)
    if result_with_fuel !== nothing
        comparison_results[scenario]["with_fuel"] = result_with_fuel
    end
end

# ============================================================================
# COMPARISON SUMMARY
# ============================================================================
println("\n" * "="^80)
println("COMPARISON SUMMARY: System Costs WITH vs WITHOUT Fuel Costs")
println("="^80)

# Tech cost multipliers
tech_cost_by_scenario = Dict(
    "scenario_000" => 0.7,
    "scenario_001" => 1.0,
    "scenario_002" => 1.3
)

# Print header
println("\n" * "-"^80)
@printf("%-15s %12s %18s %18s %15s\n", "Scenario", "Tech Cost", "No Fuel (B EUR)", "With Fuel (B EUR)", "Difference (%)")
println("-"^80)

summary_data = []

for scenario in scenarios_to_run
    if haskey(comparison_results, scenario)
        tech_cost = get(tech_cost_by_scenario, scenario, "?")

        no_fuel_obj = get(comparison_results[scenario], "no_fuel", Dict())
        with_fuel_obj = get(comparison_results[scenario], "with_fuel", Dict())

        no_fuel_val = get(no_fuel_obj, "objective_value", NaN)
        with_fuel_val = get(with_fuel_obj, "objective_value", NaN)

        if !isnan(no_fuel_val) && !isnan(with_fuel_val)
            diff_pct = (with_fuel_val - no_fuel_val) / no_fuel_val * 100
            @printf("%-15s %12.1fx %18.2f %18.2f %+14.2f%%\n",
                    scenario, tech_cost, no_fuel_val/1e9, with_fuel_val/1e9, diff_pct)

            push!(summary_data, Dict(
                "scenario" => scenario,
                "tech_cost" => tech_cost,
                "no_fuel_obj" => no_fuel_val,
                "with_fuel_obj" => with_fuel_val,
                "difference_pct" => diff_pct
            ))
        end
    end
end
println("-"^80)

# Print variable verification
println("\n" * "-"^80)
println("VARIABLE VERIFICATION (s variable for energy consumption)")
println("-"^80)
@printf("%-15s %15s %15s %15s %15s\n", "Scenario", "No Fuel: s?", "No Fuel: vars", "With Fuel: s?", "With Fuel: vars")
println("-"^80)

for scenario in scenarios_to_run
    if haskey(comparison_results, scenario)
        no_fuel = get(comparison_results[scenario], "no_fuel", Dict())
        with_fuel = get(comparison_results[scenario], "with_fuel", Dict())

        no_fuel_s = get(no_fuel, "has_s_variable", false) ? "YES" : "NO"
        with_fuel_s = get(with_fuel, "has_s_variable", false) ? "YES" : "NO"
        no_fuel_vars = get(no_fuel, "num_variables", 0)
        with_fuel_vars = get(with_fuel, "num_variables", 0)

        @printf("%-15s %15s %15d %15s %15d\n", scenario, no_fuel_s, no_fuel_vars, with_fuel_s, with_fuel_vars)
    end
end
println("-"^80)

# Print BEV share comparison
println("\n" * "-"^80)
println("BEV SHARE COMPARISON at 2056")
println("-"^80)
@printf("%-15s %15s %15s\n", "Scenario", "No Fuel (%)", "With Fuel (%)")
println("-"^80)

for scenario in scenarios_to_run
    if haskey(comparison_results, scenario)
        no_fuel = get(comparison_results[scenario], "no_fuel", Dict())
        with_fuel = get(comparison_results[scenario], "with_fuel", Dict())

        no_fuel_fleet = get(no_fuel, "fleet_by_tv_year", Dict())
        with_fuel_fleet = get(with_fuel, "fleet_by_tv_year", Dict())

        # BEV share at 2056
        no_fuel_bev = get(get(no_fuel_fleet, 1, Dict()), 2056, 0.0)
        no_fuel_icev = get(get(no_fuel_fleet, 0, Dict()), 2056, 0.0)
        no_fuel_total = no_fuel_bev + no_fuel_icev
        no_fuel_share = no_fuel_total > 0 ? (no_fuel_bev / no_fuel_total * 100) : 0.0

        with_fuel_bev = get(get(with_fuel_fleet, 1, Dict()), 2056, 0.0)
        with_fuel_icev = get(get(with_fuel_fleet, 0, Dict()), 2056, 0.0)
        with_fuel_total = with_fuel_bev + with_fuel_icev
        with_fuel_share = with_fuel_total > 0 ? (with_fuel_bev / with_fuel_total * 100) : 0.0

        @printf("%-15s %14.1f%% %14.1f%%\n", scenario, no_fuel_share, with_fuel_share)
    end
end
println("-"^80)

# Save comparison to YAML
comparison_yaml_path = joinpath(results_dir, "comparison_summary.yaml")
YAML.write_file(comparison_yaml_path, comparison_results)
@info "[OK] Comparison saved to $comparison_yaml_path"

# Save summary to CSV-like format
summary_csv_path = joinpath(results_dir, "comparison_summary.csv")
open(summary_csv_path, "w") do io
    println(io, "scenario,tech_cost,no_fuel_obj_eur,with_fuel_obj_eur,difference_pct")
    for row in summary_data
        println(io, "$(row["scenario"]),$(row["tech_cost"]),$(row["no_fuel_obj"]),$(row["with_fuel_obj"]),$(row["difference_pct"])")
    end
end
@info "[OK] Summary CSV saved to $summary_csv_path"

println("\n" * "="^80)
println("FLEET VERIFICATION COMPARISON COMPLETE")
println("="^80)
