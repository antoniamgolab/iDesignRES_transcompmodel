# Fleet Verification Script
# Purpose: Test vehicle fleet constraints only to verify substitution behavior
# Uses only: constraint_demand_coverage, constraint_vehicle_sizing, constraint_vehicle_aging, constraint_vehicle_stock_shift
# Runs 3 scenarios varying only by tech_cost_multiplier (0.7, 1.0, 1.3)

using Pkg
Pkg.activate(joinpath(@__DIR__, "../.."))

using YAML, JuMP, Gurobi, Printf, Dates

include(joinpath(@__DIR__, "../../src/TransComp.jl"))
using .TransComp

# ============================================================================
# CONFIGURATION
# ============================================================================
script_dir = @__DIR__
scenarios_to_run = ["scenario_000", "scenario_001", "scenario_002"]  # Only tech_cost differs: 0.7, 1.0, 1.3

# Variables needed for fleet + fuel demand constraints
# Added 's' for energy/fuel consumption (used by constraint_fueling_demand)
relevant_vars = ["f", "h", "h_plus", "h_exist", "h_minus", "s"]

# Results storage
results_dir = joinpath(@__DIR__, "results", "fleet_verification")
if !isdir(results_dir)
    mkpath(results_dir)
end

# ============================================================================
# RUN EACH SCENARIO
# ============================================================================
all_fleet_results = Dict()

for scenario in scenarios_to_run
    println("\n" * "="^80)
    println("RUNNING SCENARIO: $scenario")
    println("="^80)

    input_path = joinpath(@__DIR__, "input_data", "uncertainty_scenarios", scenario)

    if !isdir(input_path)
        @warn "Scenario directory not found: $input_path"
        continue
    end

    timestamp = Dates.format(now(), "yyyy-mm-dd_HH-MM-SS")
    case = "fleet_verify_$(scenario)_$timestamp"

    # Step 1: Load data
    @info "Loading input data..."
    t_start = time()
    data_dict = get_input_data(input_path)
    t_read = time() - t_start
    @info "✓ Input data loaded in $(round(t_read, digits=2))s"

    # Step 2: Parse data
    @info "Parsing data structures..."
    t_start = time()
    data_structures = parse_data(data_dict)
    t_parse = time() - t_start
    @info "✓ Data parsed in $(round(t_parse, digits=2))s"

    # Step 3: Create model with minimal variables
    @info "Creating model..."
    t_start = time()
    model, data_structures = create_model(data_structures, case, include_vars=relevant_vars)
    t_create = time() - t_start
    @info "✓ Model created in $(round(t_create, digits=2))s"
    @info "Number of variables: $(num_variables(model))"

    # Step 4: Configure solver
    set_optimizer_attribute(model, "Method", 2)
    set_optimizer_attribute(model, "MIPFocus", 1)
    set_optimizer_attribute(model, "MIPGap", 0.01)
    set_optimizer_attribute(model, "NumericFocus", 3)
    set_optimizer_attribute(model, "ScaleFlag", 2)
    set_optimizer_attribute(model, "Crossover", 0)

    # ============================================================================
    # ADD FLEET CONSTRAINTS + FUELING DEMAND
    # ============================================================================
    @info "Adding fleet constraints + fueling demand..."

    # Core demand constraint
    t_start = time()
    constraint_demand_coverage(model, data_structures)
    @info "✓ constraint_demand_coverage added in $(round(time() - t_start, digits=2))s"

    # Vehicle sizing (h >= flow/capacity)
    t_start = time()
    constraint_vehicle_sizing(model, data_structures)
    @info "✓ constraint_vehicle_sizing added in $(round(time() - t_start, digits=2))s"

    # Vehicle aging (h = h_exist - h_minus + h_plus)
    t_start = time()
    constraint_vehicle_aging(model, data_structures)
    @info "✓ constraint_vehicle_aging added in $(round(time() - t_start, digits=2))s"

    # Vehicle stock shift (fleet growth rate limited)
    t_start = time()
    constraint_vehicle_stock_shift(model, data_structures)
    @info "✓ constraint_vehicle_stock_shift added in $(round(time() - t_start, digits=2))s"

    # Fueling demand (links flow f to energy consumption s via specific consumption)
    t_start = time()
    constraint_fueling_demand(model, data_structures)
    @info "✓ constraint_fueling_demand added in $(round(time() - t_start, digits=2))s"

    @info "Total constraints: $(num_constraints(model; count_variable_in_set_constraints=false))"

    # Step 5: Add objective
    @info "Adding objective function..."
    t_start = time()
    objective(model, data_structures, false)
    @info "✓ Objective added in $(round(time() - t_start, digits=2))s"

    # Step 6: Optimize
    @info "Solving..."
    t_start = time()
    optimize!(model)
    t_solve = time() - t_start
    @info "✓ Solved in $(round(t_solve, digits=2))s"

    # Print solution summary
    solution_summary(model)

    # ============================================================================
    # EXTRACT FLEET COMPOSITION
    # ============================================================================
    @info "Extracting fleet composition..."

    # Get modeled years from data_structures
    modeled_years = data_structures["modeled_years"]

    # Get techvehicle list
    tv_list = data_structures["techvehicle_list"]

    # Extract h (total fleet) by techvehicle and year
    # h is indexed by (y, odpair_id, tv_id, g)
    fleet_by_tv_year = Dict()
    for tv in tv_list
        fleet_by_tv_year[tv.id] = Dict()
        for year in modeled_years
            fleet_by_tv_year[tv.id][year] = 0.0
        end
    end

    # Sum h values across all odpairs and generations
    for (key, var) in model[:h].data
        y = key[1]      # year
        r_id = key[2]   # odpair_id
        tv_id = key[3]  # techvehicle_id
        g = key[4]      # generation (purchase year)
        val = value(var)

        if haskey(fleet_by_tv_year, tv_id) && haskey(fleet_by_tv_year[tv_id], y)
            fleet_by_tv_year[tv_id][y] += val
        end
    end

    # Also extract h_plus (new purchases) by techvehicle and year
    purchases_by_tv_year = Dict()
    for tv in tv_list
        purchases_by_tv_year[tv.id] = Dict()
        for year in modeled_years
            purchases_by_tv_year[tv.id][year] = 0.0
        end
    end

    for (key, var) in model[:h_plus].data
        y = key[1]      # year
        r_id = key[2]   # odpair_id
        tv_id = key[3]  # techvehicle_id
        g = key[4]      # generation
        val = value(var)

        if haskey(purchases_by_tv_year, tv_id) && haskey(purchases_by_tv_year[tv_id], y)
            purchases_by_tv_year[tv_id][y] += val
        end
    end

    # Store results
    all_fleet_results[scenario] = Dict(
        "objective_value" => objective_value(model),
        "fleet_by_tv_year" => fleet_by_tv_year,
        "purchases_by_tv_year" => purchases_by_tv_year,
        "techvehicles" => Dict(tv.id => tv.name for tv in tv_list)
    )

    # Print fleet summary
    println("\n" * "-"^60)
    println("FLEET COMPOSITION for $scenario")
    println("-"^60)

    # Create table header
    tv_names = Dict(tv.id => tv.name for tv in tv_list)
    tv_ids = sort(collect(keys(tv_names)))

    # Print header
    print(@sprintf("%-8s", "Year"))
    for tv_id in tv_ids
        print(@sprintf("%15s", tv_names[tv_id][1:min(14,length(tv_names[tv_id]))]))
    end
    println()

    # Print data for every 4th year (since timestep is 4)
    for year in modeled_years[1:4:end]
        print(@sprintf("%-8d", year))
        for tv_id in tv_ids
            val = fleet_by_tv_year[tv_id][year]
            print(@sprintf("%15.0f", val))
        end
        println()
    end

    # Save results
    scenario_results_dir = joinpath(results_dir, scenario)
    if !isdir(scenario_results_dir)
        mkpath(scenario_results_dir)
    end
    save_results(model, case, data_structures, true, scenario_results_dir, scenario)

    @info "✓ Results saved to $scenario_results_dir"

    GC.gc()
end

# ============================================================================
# COMPARE FLEET ACROSS SCENARIOS
# ============================================================================
println("\n" * "="^80)
println("FLEET COMPARISON ACROSS SCENARIOS")
println("="^80)

# Tech cost multipliers from cases.json (hardcoded to avoid JSON dependency)
tech_cost_by_scenario = Dict(
    "scenario_000" => 0.7,
    "scenario_001" => 1.0,
    "scenario_002" => 1.3
)

# Print comparison header
println("\nTech Cost Multiplier by Scenario:")
for scenario in scenarios_to_run
    tech_cost = get(tech_cost_by_scenario, scenario, "unknown")
    println("  $scenario: tech_cost_multiplier = $tech_cost")
end

# Compare fleet at key years
key_years = [2020, 2032, 2040, 2048, 2056]

println("\n" * "-"^80)
println("BEV FLEET (tv_id=1) by Year and Scenario")
println("-"^80)

print(@sprintf("%-12s", "Scenario"))
for year in key_years
    print(@sprintf("%12d", year))
end
println()

for scenario in scenarios_to_run
    if haskey(all_fleet_results, scenario)
        print(@sprintf("%-12s", scenario))
        for year in key_years
            bev_fleet = get(all_fleet_results[scenario]["fleet_by_tv_year"][1], year, 0.0)
            print(@sprintf("%12.0f", bev_fleet))
        end
        println()
    end
end

println("\n" * "-"^80)
println("ICEV FLEET (tv_id=0) by Year and Scenario")
println("-"^80)

print(@sprintf("%-12s", "Scenario"))
for year in key_years
    print(@sprintf("%12d", year))
end
println()

for scenario in scenarios_to_run
    if haskey(all_fleet_results, scenario)
        print(@sprintf("%-12s", scenario))
        for year in key_years
            icev_fleet = get(all_fleet_results[scenario]["fleet_by_tv_year"][0], year, 0.0)
            print(@sprintf("%12.0f", icev_fleet))
        end
        println()
    end
end

println("\n" * "-"^80)
println("BEV SHARE by Year and Scenario")
println("-"^80)

print(@sprintf("%-12s", "Scenario"))
for year in key_years
    print(@sprintf("%12d", year))
end
println()

for scenario in scenarios_to_run
    if haskey(all_fleet_results, scenario)
        print(@sprintf("%-12s", scenario))
        for year in key_years
            bev_fleet = get(all_fleet_results[scenario]["fleet_by_tv_year"][1], year, 0.0)
            icev_fleet = get(all_fleet_results[scenario]["fleet_by_tv_year"][0], year, 0.0)
            total = bev_fleet + icev_fleet
            bev_share = total > 0 ? (bev_fleet / total * 100) : 0.0
            print(@sprintf("%11.1f%%", bev_share))
        end
        println()
    end
end

# Save summary as YAML
summary_path = joinpath(results_dir, "fleet_verification_summary.yaml")
YAML.write_file(summary_path, all_fleet_results)
@info "✓ Summary saved to $summary_path"

println("\n" * "="^80)
println("FLEET VERIFICATION COMPLETE")
println("="^80)
