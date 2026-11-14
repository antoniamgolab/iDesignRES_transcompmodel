"""
Compare: constraint_fueling_demand vs SOC-only constraints
- Config A: WITH constraint_fueling_demand (spatial charging infrastructure)
- Config B: WITHOUT constraint_fueling_demand (SOC tracking only)
"""

using Pkg
Pkg.activate(joinpath(@__DIR__, "../.."))

using YAML, JuMP, Gurobi, Printf, ProgressMeter, Dates

include(joinpath(@__DIR__, "../../src/TransComp.jl"))
using .TransComp

script_dir = @__DIR__
folder = "case_20251107_214315_uni_uni"
input_path = joinpath(@__DIR__, "input_data", folder)

# Results storage
results_dir = joinpath(script_dir, "results", "fueling_vs_soc_comparison")
if !isdir(results_dir)
    mkpath(results_dir)
end

# Store results for comparison
comparison_results = Dict()

function run_model_config(config_name::String, use_fueling_demand::Bool)
    @info "=" ^ 80
    @info "Running Configuration: $config_name"
    @info "  constraint_fueling_demand: $use_fueling_demand"
    @info "=" ^ 80

    timestamp = Dates.format(now(), "yyyy-mm-dd_HH-MM-SS")
    case = "$(folder)_$(config_name)_$timestamp"

    # Reading input data
    @info "Reading input data..."
    data_dict = get_input_data(input_path)
    data_structures = parse_data(data_dict)

    # Create model
    relevant_vars = ["f", "h", "h_plus", "h_exist", "h_minus", "s", "q_fuel_infr_plus", "soc", "travel_time", "extra_break_time"]
    model, data_structures = create_model(data_structures, case, include_vars=relevant_vars)

    # Configure solver
    set_optimizer_attribute(model, "Method", 2)
    set_optimizer_attribute(model, "MIPFocus", 1)
    set_optimizer_attribute(model, "Cuts", 1)
    set_optimizer_attribute(model, "MIPGap", 0.01)
    set_optimizer_attribute(model, "NumericFocus", 3)
    set_optimizer_attribute(model, "ScaleFlag", 2)
    set_optimizer_attribute(model, "FeasibilityTol", 1e-5)
    set_optimizer_attribute(model, "OptimalityTol", 1e-5)
    set_optimizer_attribute(model, "IntFeasTol", 1e-4)
    set_optimizer_attribute(model, "Crossover", 0)
    set_optimizer_attribute(model, "BarConvTol", 1e-6)

    # Add constraints
    constraint_mandatory_breaks(model, data_structures)

    # CONDITIONAL: Add fueling demand constraint
    if use_fueling_demand
        @info "Adding constraint_fueling_demand..."
        constraint_fueling_demand(model, data_structures)
    else
        @info "SKIPPING constraint_fueling_demand (SOC-only mode)"
    end

    constraint_fueling_infrastructure(model, data_structures)
    constraint_fueling_infrastructure_expansion_shift(model, data_structures)

    # SOC constraints (always included)
    @info "Adding SOC constraints..."
    constraint_soc_track(model, data_structures)
    constraint_soc_max(model, data_structures)
    constraint_travel_time_track(model, data_structures)

    # Mode constraints
    constraint_mode_shift(model, data_structures)
    if !isempty(data_structures["max_mode_share_list"])
        constraint_max_mode_share(model, data_structures)
    end

    # Core constraints
    constraint_demand_coverage(model, data_structures)
    constraint_vehicle_sizing(model, data_structures)
    constraint_vehicle_aging(model, data_structures)
    constraint_vehicle_stock_shift(model, data_structures)

    # Objective with fuel costs
    objective(model, data_structures, true)

    GC.gc()

    # Solve
    @info "Solving optimization..."
    t_start = time()
    optimize!(model)
    solve_time = time() - t_start
    @info "Solved in $(round(solve_time, digits=2)) seconds"

    # Extract results
    obj_value = objective_value(model)
    @info "Objective value: $(round(obj_value/1e9, digits=2)) billion EUR"

    # Extract fleet by technology and year
    h_dict = model[:h]
    fleet_by_tv_year = Dict(0 => Dict{Int,Float64}(), 1 => Dict{Int,Float64}())

    for idx in eachindex(h_dict)
        var = h_dict[idx]
        val = value(var)
        if val > 1e-6
            # idx is a tuple: (year, odpair_id, tv_id, gen)
            year = idx[1]
            tv_id = idx[3]

            # Find techvehicle to get technology type
            tv_idx = findfirst(tv -> tv.id == tv_id, data_structures["techvehicle_list"])
            if tv_idx !== nothing
                tv = data_structures["techvehicle_list"][tv_idx]
                tech = tv.technology.id  # 0 = ICEV, 1 = BEV
                if !haskey(fleet_by_tv_year[tech], year)
                    fleet_by_tv_year[tech][year] = 0.0
                end
                fleet_by_tv_year[tech][year] += val
            end
        end
    end

    # Extract fueled energy (s variable)
    fueled_energy_by_year = Dict{Int,Float64}()
    if haskey(model, :s)
        s_dict = model[:s]
        for idx in eachindex(s_dict)
            var = s_dict[idx]
            val = value(var)
            if val > 1e-6
                # idx is a tuple, first element is the year
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
    for year in keys(fleet_by_tv_year[0])
        icev = get(fleet_by_tv_year[0], year, 0.0)
        bev = get(fleet_by_tv_year[1], year, 0.0)
        total = icev + bev
        if total > 0
            bev_share_by_year[year] = bev / total * 100
        else
            bev_share_by_year[year] = 0.0
        end
    end

    # Store results
    result = Dict(
        "config_name" => config_name,
        "use_fueling_demand" => use_fueling_demand,
        "objective_value" => obj_value,
        "solve_time" => solve_time,
        "fleet_by_tv_year" => fleet_by_tv_year,
        "fueled_energy_by_year" => fueled_energy_by_year,
        "bev_share_by_year" => bev_share_by_year,
        "num_variables" => num_variables(model)
    )

    # Save individual results
    results_file = joinpath(results_dir, "$(config_name)_results.yaml")
    YAML.write_file(results_file, result)
    @info "Saved results to $results_file"

    return result
end

# Run both configurations
@info "=" ^ 80
@info "COMPARISON: constraint_fueling_demand vs SOC-only"
@info "=" ^ 80

# Config A: WITH constraint_fueling_demand
results_with_fueling = run_model_config("with_fueling_demand", true)
comparison_results["with_fueling_demand"] = results_with_fueling

GC.gc()

# Config B: WITHOUT constraint_fueling_demand (SOC-only)
results_soc_only = run_model_config("soc_only", false)
comparison_results["soc_only"] = results_soc_only

# Compare and print summary
@info "\n" * "=" ^ 80
@info "COMPARISON SUMMARY"
@info "=" ^ 80

years = [2020, 2024, 2028, 2032, 2036, 2040, 2044, 2048, 2052, 2056, 2060]

println("\n" * "=" * 80)
println("BEV SHARE COMPARISON (%)")
println("=" * 80)
println("Year  | With Fueling Demand | SOC-Only  | Difference")
println("-" * 60)
for year in years
    bev_with = get(results_with_fueling["bev_share_by_year"], year, 0.0)
    bev_soc = get(results_soc_only["bev_share_by_year"], year, 0.0)
    diff = bev_soc - bev_with
    @printf("%4d  | %18.1f%% | %8.1f%% | %+8.1f%%\n", year, bev_with, bev_soc, diff)
end

println("\n" * "=" * 80)
println("FUELED ENERGY COMPARISON (MWh)")
println("=" * 80)
println("Year  | With Fueling Demand | SOC-Only  | Difference")
println("-" * 60)
total_fueled_with = 0.0
total_fueled_soc = 0.0
for year in years
    energy_with = get(results_with_fueling["fueled_energy_by_year"], year, 0.0) / 1000  # kWh to MWh
    energy_soc = get(results_soc_only["fueled_energy_by_year"], year, 0.0) / 1000
    diff = energy_soc - energy_with
    total_fueled_with += energy_with
    total_fueled_soc += energy_soc
    @printf("%4d  | %18.1f | %9.1f | %+9.1f\n", year, energy_with, energy_soc, diff)
end
println("-" * 60)
@printf("TOTAL | %18.1f | %9.1f | %+9.1f\n", total_fueled_with, total_fueled_soc, total_fueled_soc - total_fueled_with)

println("\n" * "=" * 80)
println("OBJECTIVE VALUE COMPARISON (Billion EUR)")
println("=" * 80)
obj_with = results_with_fueling["objective_value"] / 1e9
obj_soc = results_soc_only["objective_value"] / 1e9
@printf("With Fueling Demand: %.2f B EUR\n", obj_with)
@printf("SOC-Only:            %.2f B EUR\n", obj_soc)
@printf("Difference:          %.2f B EUR (%.2f%%)\n", obj_soc - obj_with, (obj_soc - obj_with) / obj_with * 100)

println("\n" * "=" * 80)
println("MODEL SIZE COMPARISON")
println("=" * 80)
@printf("With Fueling Demand: %d variables\n", results_with_fueling["num_variables"])
@printf("SOC-Only:            %d variables\n", results_soc_only["num_variables"])

# Save comparison summary
comparison_summary = Dict(
    "with_fueling_demand" => results_with_fueling,
    "soc_only" => results_soc_only
)
summary_file = joinpath(results_dir, "comparison_summary.yaml")
YAML.write_file(summary_file, comparison_summary)
@info "Saved comparison summary to $summary_file"

println("\n" * "=" * 80)
println("COMPARISON COMPLETE")
println("=" * 80)
println("Results saved to: $results_dir")
