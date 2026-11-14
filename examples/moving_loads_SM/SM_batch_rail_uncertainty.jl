"""
SM_batch_rail_uncertainty.jl - Batch processing for rail uncertainty scenarios

Runs optimization on all 24 rail uncertainty scenarios.

WITHOUT the constraint_charging_at_breaks_only constraint - BEVs can charge anywhere.
"""

using Pkg
Pkg.activate(joinpath(@__DIR__, "../.."))  # Activate the project environment

using YAML, JuMP, Gurobi, Printf, ProgressMeter, Dates

include(joinpath(@__DIR__, "../../src/TransComp.jl"))
using .TransComp

# ============================================================================
# CONFIGURATION
# ============================================================================

# Path to rail uncertainty scenarios
rail_uncertainty_dir = joinpath(@__DIR__, "input_data", "uncertainty_scenarios_rail")

# Get all scenario folders automatically
all_folders = filter(isdir, [joinpath(rail_uncertainty_dir, d) for d in readdir(rail_uncertainty_dir)])
case_folders = [basename(f) for f in all_folders if startswith(basename(f), "scenario_")]
sort!(case_folders)  # Sort alphabetically for consistent ordering

@info "Found $(length(case_folders)) rail uncertainty scenarios"
@info "Rail scenarios generated from: input_data/case_*_rail_base"
@info "Each scenario includes both road and rail modes"

# Variables to include in the model
relevant_vars = ["f", "h", "h_plus", "h_exist", "h_minus", "s", "q_fuel_infr_plus", "soc", "travel_time", "extra_break_time"]

# ============================================================================
# BATCH PROCESSING LOOP
# ============================================================================

@info "="^80
@info "RAIL UNCERTAINTY BATCH PROCESSING"
@info "Total scenarios: $(length(case_folders))"
@info "NO constraint_charging_at_breaks_only - BEVs can charge anywhere"
@info "="^80

batch_start_time = time()
batch_results = Dict()

for (case_idx, folder) in enumerate(case_folders)
    @info "\n" * "="^80
    @info "SCENARIO $(case_idx)/$(length(case_folders)): $folder"
    @info "="^80

    case_start_time = time()

    try
        # ================================================================
        # Step 1: Setup paths
        # ================================================================
        script_dir = @__DIR__
        input_path = joinpath(rail_uncertainty_dir, folder)

        if !isdir(input_path)
            @warn "Input folder not found: $input_path - SKIPPING"
            batch_results[folder] = Dict("status" => "SKIPPED", "reason" => "Folder not found")
            continue
        end

        # Check if results already exist - SKIP if already calculated
        results_check_path = joinpath(script_dir, "results", "rail", folder)
        if isdir(results_check_path) && !isempty(readdir(results_check_path))
            @info "Results already exist for $folder - SKIPPING"
            batch_results[folder] = Dict("status" => "SKIPPED", "reason" => "Already calculated")
            continue
        end

        @info "Input path: $input_path"

        # Generate output case name with SHORT timestamp (avoid Windows path length limit)
        timestamp = Dates.format(now(), "mmdd_HHMM")
        # Use short case name to avoid path length issues
        case_name = "rail_$timestamp"

        # ================================================================
        # Step 2: Read and parse input data
        # ================================================================
        @info "Step 1/5: Reading input data..."
        t_start = time()
        data_dict = get_input_data(input_path)
        t_read = time() - t_start
        @info "Input data loaded in $(round(t_read, digits=2)) seconds"

        @info "Step 2/5: Parsing data structures..."
        t_start = time()
        data_structures = parse_data(data_dict)
        t_parse = time() - t_start
        @info "Data parsed in $(round(t_parse, digits=2)) seconds"

        # ================================================================
        # Step 3: Create optimization model
        # ================================================================
        @info "Step 3/5: Creating optimization model..."
        @info "Memory before model creation: $(round(Sys.free_memory()/1024^3, digits=2)) GB free"
        t_start = time()
        model, data_structures = create_model(data_structures, case_name, include_vars=relevant_vars)
        t_create = time() - t_start
        @info "Model created in $(round(t_create, digits=2)) seconds"
        @info "Memory after model creation: $(round(Sys.free_memory()/1024^3, digits=2)) GB free"
        @info "Number of variables: $(num_variables(model))"

        # ================================================================
        # Step 4: Configure solver
        # ================================================================
        @info "Step 3.5/5: Configuring solver parameters..."
        set_optimizer_attribute(model, "Method", 2)           # Barrier method
        set_optimizer_attribute(model, "MIPFocus", 1)         # Focus on feasibility
        set_optimizer_attribute(model, "Cuts", 1)             # Conservative cuts
        set_optimizer_attribute(model, "MIPGap", 0.01)        # 1% gap
        set_optimizer_attribute(model, "NumericFocus", 3)     # Maximum numerical precision
        set_optimizer_attribute(model, "ScaleFlag", 2)        # Aggressive auto-scaling
        set_optimizer_attribute(model, "FeasibilityTol", 1e-5)
        set_optimizer_attribute(model, "OptimalityTol", 1e-5)
        set_optimizer_attribute(model, "IntFeasTol", 1e-4)
        set_optimizer_attribute(model, "Crossover", 0)        # Skip crossover
        set_optimizer_attribute(model, "BarConvTol", 1e-6)    # Faster convergence
        @info "Solver configured"

        # ================================================================
        # Step 5: Add constraints (NO constraint_charging_at_breaks_only)
        # ================================================================
        @info "Step 4/5: Adding constraints..."
        @info "NOTE: NOT adding constraint_charging_at_breaks_only - BEVs can charge anywhere"
        t_constraints_start = time()

        # Mandatory breaks (enforces break duration, NOT charging location)
        t_start = time()
        constraint_mandatory_breaks(model, data_structures)
        t_mandatory_breaks = time() - t_start
        @info "Mandatory breaks constraint added in $(round(t_mandatory_breaks, digits=2))s"

        # Fueling infrastructure constraints
        t_start = time()
        constraint_fueling_infrastructure(model, data_structures)
        t_fueling_infra = time() - t_start
        @info "Fueling infrastructure constraint added in $(round(t_fueling_infra, digits=2))s"

        t_start = time()
        constraint_fueling_infrastructure_expansion_shift(model, data_structures)
        t_fueling_infra_expansion_shift = time() - t_start
        @info "Fueling infrastructure expansion shift constraint added in $(round(t_fueling_infra_expansion_shift, digits=2))s"

        # BEV-specific constraints
        t_start = time()
        constraint_soc_track(model, data_structures)
        t_soc_track = time() - t_start
        @info "State of charge tracking constraints added in $(round(t_soc_track, digits=2))s"

        t_start = time()
        constraint_soc_max(model, data_structures)
        t_soc = time() - t_start
        @info "State of charge max constraints added in $(round(t_soc, digits=2))s"

        t_start = time()
        constraint_travel_time_track(model, data_structures)
        t_travel_time_track = time() - t_start
        @info "Travel time tracking constraint added in $(round(t_travel_time_track, digits=2))s"

        # Mode shift constraints
        t_start = time()
        constraint_mode_shift(model, data_structures)
        t_mode_shift = time() - t_start
        @info "Mode shift constraint added in $(round(t_mode_shift, digits=2))s"

        # Max mode share constraints
        t_start = time()
        if !isempty(data_structures["max_mode_share_list"])
            constraint_max_mode_share(model, data_structures)
            t_max_mode_share = time() - t_start
            @info "Max mode share constraint added in $(round(t_max_mode_share, digits=2))s"
        else
            t_max_mode_share = 0.0
            @info "Skipping max mode share constraint (no constraints defined)"
        end

        # Core demand constraints
        t_start = time()
        constraint_demand_coverage(model, data_structures)
        t_demand_coverage = time() - t_start
        @info "Demand coverage constraint added in $(round(t_demand_coverage, digits=2))s"

        # Vehicle fleet constraints
        t_start = time()
        constraint_vehicle_sizing(model, data_structures)
        t_vehicle_sizing = time() - t_start
        @info "Vehicle sizing constraint added in $(round(t_vehicle_sizing, digits=2))s"

        t_start = time()
        constraint_vehicle_aging(model, data_structures)
        t_vehicle_aging = time() - t_start
        @info "Vehicle aging constraint added in $(round(t_vehicle_aging, digits=2))s"

        t_start = time()
        constraint_vehicle_stock_shift(model, data_structures)
        t_vehicle_stock_shift = time() - t_start
        @info "Vehicle stock shift constraint added in $(round(t_vehicle_stock_shift, digits=2))s"

        t_constraints = time() - t_constraints_start

        # ================================================================
        # Step 6: Add objective function
        # ================================================================
        @info "Step 4.5/5: Adding objective..."
        t_start = time()
        objective(model, data_structures, false)
        t_obj = time() - t_start
        @info "Objective added in $(round(t_obj, digits=2)) seconds"

        GC.gc()  # Force garbage collection

        # ================================================================
        # Step 7: Solve optimization problem
        # ================================================================
        @info "Step 5/5: Solving optimization problem..."
        t_start = time()
        optimize!(model)
        t_optimize = time() - t_start
        @info "Optimization complete in $(round(t_optimize, digits=2)) seconds"

        # ================================================================
        # Step 8: Save results
        # ================================================================
        @info "Saving results to file..."
        # Use shorter path: results/rail/{folder}/ to avoid Windows path length limit
        results_file_path = normpath(joinpath(script_dir, "results", "rail", folder))
        if !isdir(results_file_path)
            mkpath(results_file_path)
        end
        save_results(model, case_name, data_structures, true, results_file_path, folder)
        @info "Results saved to: $results_file_path"

        # ================================================================
        # Store timing summary for this case
        # ================================================================
        case_elapsed = time() - case_start_time

        batch_results[folder] = Dict(
            "status" => "SUCCESS",
            "total_time" => case_elapsed,
            "t_read" => t_read,
            "t_parse" => t_parse,
            "t_create" => t_create,
            "t_constraints" => t_constraints,
            "t_obj" => t_obj,
            "t_optimize" => t_optimize,
            "objective_value" => objective_value(model),
            "termination_status" => termination_status(model)
        )

        @info "="^80
        @info "SCENARIO COMPLETE: $folder"
        @info "  Total time: $(round(case_elapsed/60, digits=2)) minutes"
        @info "  Status: $(termination_status(model))"
        @info "  Objective value: $(objective_value(model))"
        @info "="^80

    catch e
        case_elapsed = time() - case_start_time
        @error "ERROR processing scenario: $folder"
        @error "Exception: $e"
        @error sprint(showerror, e, catch_backtrace())

        batch_results[folder] = Dict(
            "status" => "FAILED",
            "total_time" => case_elapsed,
            "error" => string(e)
        )

        @info "="^80
        @info "SCENARIO FAILED: $folder - Continuing with next scenario..."
        @info "="^80
    end

    # Memory cleanup between cases
    GC.gc()
end

# ============================================================================
# BATCH SUMMARY
# ============================================================================

batch_elapsed = time() - batch_start_time

@info "\n" * "="^80
@info "RAIL UNCERTAINTY BATCH PROCESSING COMPLETE"
@info "="^80
@info "Total batch time: $(round(batch_elapsed/60, digits=2)) minutes ($(round(batch_elapsed/3600, digits=2)) hours)"
@info ""
@info "Results summary:"

# Count successes and failures
n_success = count(r -> r.second["status"] == "SUCCESS", batch_results)
n_failed = count(r -> r.second["status"] == "FAILED", batch_results)
n_skipped = count(r -> r.second["status"] == "SKIPPED", batch_results)

@info "  Successful: $n_success"
@info "  Failed: $n_failed"
@info "  Skipped: $n_skipped"
@info ""

# Show details for each scenario
for (idx, folder) in enumerate(case_folders)
    result = get(batch_results, folder, Dict("status" => "UNKNOWN"))
    status = result["status"]
    elapsed = get(result, "total_time", 0.0)

    if status == "SUCCESS"
        obj_val = get(result, "objective_value", "N/A")
        @info "  [$idx] $folder: SUCCESS ($(round(elapsed/60, digits=1))m, obj=$(round(obj_val, digits=0)))"
    elseif status == "FAILED"
        error_msg = get(result, "error", "Unknown error")
        @info "  [$idx] $folder: FAILED ($(round(elapsed/60, digits=1))m) - $(first(error_msg, 60))"
    else
        reason = get(result, "reason", "Unknown")
        @info "  [$idx] $folder: SKIPPED - $reason"
    end
end

@info "="^80
@info "All scenarios processed."
@info "Results saved in 'results/rail/' subdirectories."
@info "="^80

# Save batch summary to file
summary_file = joinpath(@__DIR__, "results", "rail", "batch_summary.txt")
mkpath(dirname(summary_file))
open(summary_file, "w") do io
    println(io, "Rail Uncertainty Batch Summary")
    println(io, "==============================")
    println(io, "Run completed: $(Dates.format(now(), "yyyy-mm-dd HH:MM:SS"))")
    println(io, "Total time: $(round(batch_elapsed/60, digits=2)) minutes")
    println(io, "")
    println(io, "Scenarios: $(length(case_folders))")
    println(io, "  Successful: $n_success")
    println(io, "  Failed: $n_failed")
    println(io, "  Skipped: $n_skipped")
    println(io, "")
    println(io, "Detailed results:")
    for (idx, folder) in enumerate(case_folders)
        result = get(batch_results, folder, Dict("status" => "UNKNOWN"))
        status = result["status"]
        elapsed = get(result, "total_time", 0.0)
        if status == "SUCCESS"
            obj_val = get(result, "objective_value", 0.0)
            println(io, "  $folder: SUCCESS ($(round(elapsed/60, digits=1))m, obj=$(round(obj_val, digits=0)))")
        elseif status == "FAILED"
            println(io, "  $folder: FAILED ($(round(elapsed/60, digits=1))m)")
        else
            println(io, "  $folder: SKIPPED")
        end
    end
end
@info "Batch summary saved to: $summary_file"
