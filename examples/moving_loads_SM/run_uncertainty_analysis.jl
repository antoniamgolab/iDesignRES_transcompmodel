"""
Auto-generated batch script for uncertainty analysis scenarios
Generated: 2026-01-06T11:38:39.799950

Script location: examples/moving_loads_SM/input_data/uncertainty_scenarios/run_uncertainty_analysis.jl
Repository root: ../../../../ (4 levels up)
Working dir: examples/moving_loads_SM/ (2 levels up)
"""

using Pkg
# Script is in input_data/uncertainty_scenarios/, go up 2 levels to examples/moving_loads_SM/
# Use abspath to resolve relative paths properly
working_dir = abspath(joinpath(@__DIR__, "..", ".."))
# Go up 4 levels to repository root (where Project.toml is)
repo_root = abspath(joinpath(@__DIR__, "..", "..", "..", ".."))
Pkg.activate(repo_root)

using YAML, JuMP, Gurobi, Printf, Dates

include(joinpath(repo_root, "src", "TransComp.jl"))
using .TransComp

# ============================================================================
# UNCERTAINTY ANALYSIS SCENARIOS
# ============================================================================

scenario_folders = [
    "scenario_000",
    "scenario_001",
    "scenario_002",
    "scenario_003",
    "scenario_004",
    "scenario_005",
    "scenario_006",
    "scenario_007",
    "scenario_008",
    "scenario_009",
    "scenario_010",
    "scenario_011",
    "scenario_012",
    "scenario_013",
    "scenario_014",
    "scenario_015",
    "scenario_016",
    "scenario_017",
    "scenario_018",
    "scenario_019",
    "scenario_020",
    "scenario_021",
    "scenario_022",
    "scenario_023"
]

# Variables to include
relevant_vars = ["f", "h", "h_plus", "h_exist", "h_minus", "s", "q_fuel_infr_plus", "soc", "travel_time", "extra_break_time"]

# Results storage
results_summary = Dict()

@info "=" ^ 80
@info "UNCERTAINTY ANALYSIS: $(length(scenario_folders)) scenarios"
@info "=" ^ 80

batch_start = time()

for (idx, folder) in enumerate(scenario_folders)
    @info "\n" * "=" ^ 80
    @info "SCENARIO $idx/$(length(scenario_folders)): $folder"
    @info "=" ^ 80

    scenario_start = time()

    try
        # Scenario folders are in input_data/uncertainty_scenarios/
        input_path = abspath(joinpath(@__DIR__, folder))

        if !isdir(input_path)
            @warn "Folder not found: $input_path - SKIPPING"
            results_summary[folder] = Dict("status" => "SKIPPED", "reason" => "Folder not found")
            continue
        end

        # Generate unique case name
        timestamp = Dates.format(now(), "yyyy-mm-dd_HH-MM-SS")
        case_name = "$(folder)_$timestamp"

        # Load and parse data
        @info "Loading input data..."
        data_dict = get_input_data(input_path)
        data_structures = parse_data(data_dict)

        # Create model
        @info "Creating model..."
        model, data_structures = create_model(data_structures, case_name, include_vars=relevant_vars)

        # Configure solver
        set_optimizer_attribute(model, "Method", 2)
        set_optimizer_attribute(model, "MIPFocus", 1)
        set_optimizer_attribute(model, "Cuts", 1)
        set_optimizer_attribute(model, "MIPGap", 0.01)
        set_optimizer_attribute(model, "NumericFocus", 3)
        set_optimizer_attribute(model, "ScaleFlag", 2)
        set_optimizer_attribute(model, "FeasibilityTol", 1e-5)
        set_optimizer_attribute(model, "OptimalityTol", 1e-5)
        set_optimizer_attribute(model, "Crossover", 0)
        set_optimizer_attribute(model, "BarConvTol", 1e-6)

        # Add constraints
        @info "Adding constraints..."
        constraint_mandatory_breaks(model, data_structures)
        constraint_fueling_infrastructure(model, data_structures)
        constraint_fueling_infrastructure_expansion_shift(model, data_structures)
        constraint_soc_track(model, data_structures)
        constraint_soc_max(model, data_structures)
        constraint_travel_time_track(model, data_structures)
        constraint_mode_shift(model, data_structures)
        if !isempty(data_structures["max_mode_share_list"])
            constraint_max_mode_share(model, data_structures)
        end
        constraint_demand_coverage(model, data_structures)
        constraint_vehicle_sizing(model, data_structures)
        constraint_vehicle_aging(model, data_structures)
        constraint_vehicle_stock_shift(model, data_structures)

        # Add objective
        @info "Adding objective..."
        objective(model, data_structures, false)

        GC.gc()

        # Solve
        @info "Solving..."
        optimize!(model)

        scenario_elapsed = time() - scenario_start

        # Save results (to examples/moving_loads_SM/results/uncertainty_analysis/)
        results_path = abspath(joinpath(working_dir, "results", "uncertainty_analysis", folder))
        @info "Creating results directory: $results_path"
        mkpath(results_path)
        @info "Saving results to: $results_path"
        save_results(model, case_name, data_structures, true, results_path, folder)

        results_summary[folder] = Dict(
            "status" => "SUCCESS",
            "runtime_seconds" => scenario_elapsed,
            "objective_value" => objective_value(model),
            "termination_status" => string(termination_status(model)),
            "results_path" => results_path
        )

        @info "Scenario $folder completed in $(round(scenario_elapsed/60, digits=1)) minutes"
        @info "Objective: $(objective_value(model))"

    catch e
        scenario_elapsed = time() - scenario_start
        @error "FAILED: $folder"
        @error sprint(showerror, e, catch_backtrace())

        results_summary[folder] = Dict(
            "status" => "FAILED",
            "runtime_seconds" => scenario_elapsed,
            "error" => string(e)
        )
    end

    GC.gc()
end

batch_elapsed = time() - batch_start

# Save summary
@info "\n" * "=" ^ 80
@info "UNCERTAINTY ANALYSIS COMPLETE"
@info "Total time: $(round(batch_elapsed/60, digits=1)) minutes"
@info "=" ^ 80

# Write results summary to YAML
summary_path = abspath(joinpath(working_dir, "results", "uncertainty_analysis", "batch_summary.yaml"))
mkpath(dirname(summary_path))
YAML.write_file(summary_path, results_summary)
@info "Summary saved to: $summary_path"

# Print summary
for (folder, result) in results_summary
    status = result["status"]
    if status == "SUCCESS"
        @info "  $folder: SUCCESS ($(round(result["runtime_seconds"]/60, digits=1))m)"
    elseif status == "FAILED"
        @info "  $folder: FAILED - $(get(result, "error", "Unknown"))"
    else
        @info "  $folder: SKIPPED"
    end
end
