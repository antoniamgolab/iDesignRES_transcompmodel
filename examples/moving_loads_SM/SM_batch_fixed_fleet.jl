"""
SM_batch_fixed_fleet.jl - Fixed fleet experiment for AT surcharge sensitivity

Fixes the ENTIRE fleet composition (h, h_exist, h_plus, h_minus) to baseline
scenario_002 (REPowerEU++) values and re-runs with AT surcharges. This isolates
the pure charging reallocation effect: with the same vehicles, does the model
shift WHERE BEVs charge when Austrian electricity costs increase?

Currently runs a single extreme scenario (+0.50 EUR/kWh on AT nodes 2,3) to verify
the approach. Can be extended to all surcharge levels once validated.
"""

using Pkg
Pkg.activate(joinpath(@__DIR__, "../.."))

using YAML, JuMP, Gurobi, Printf, Dates
import MathOptInterface as MOI

include(joinpath(@__DIR__, "../../src/TransComp.jl"))
using .TransComp

# ============================================================================
# CONFIGURATION
# ============================================================================

script_dir = @__DIR__

# Baseline fleet source: scenario_002 (REPowerEU++) road-only results
BASELINE_RESULTS_DIR = joinpath(script_dir, "results", "uncertainty_scenarios", "scenario_002")
BASELINE_CASE_PREFIX = "scenario_002_cs_2026-02-11_12-48-36"

# Surcharge scenarios to run
surcharge_dir = joinpath(script_dir, "input_data", "at_surcharge_scenarios")
scenarios_to_run = ["at_elec_extreme"]  # +0.50 EUR/kWh on AT nodes 2,3

results_base = joinpath(script_dir, "results", "at_surcharge_fixed_fleet")

relevant_vars = ["f", "h", "h_plus", "h_exist", "h_minus", "s", "q_fuel_infr_plus", "soc", "travel_time", "extra_break_time"]

# ============================================================================
# BATCH PROCESSING
# ============================================================================

@info "="^80
@info "FIXED FLEET + AT SURCHARGE EXPERIMENT"
@info "Fleet source: $BASELINE_CASE_PREFIX"
@info "Scenarios: $(scenarios_to_run)"
@info "="^80

batch_start_time = time()
batch_results = Dict()

for (case_idx, folder_name) in enumerate(scenarios_to_run)
    @info "\n" * "="^80
    @info "SCENARIO $(case_idx)/$(length(scenarios_to_run)): $folder_name (FIXED FLEET)"
    @info "="^80

    case_start_time = time()

    try
        input_path = joinpath(surcharge_dir, folder_name)
        if !isdir(input_path)
            @error "Input folder not found: $input_path"
            batch_results[folder_name] = Dict("status" => "FAILED", "error" => "Input not found")
            continue
        end

        # Check if results already exist
        results_check_path = joinpath(results_base, folder_name)
        if isdir(results_check_path) && !isempty(readdir(results_check_path))
            @info "Results already exist for $folder_name - SKIPPING"
            batch_results[folder_name] = Dict("status" => "SKIPPED", "reason" => "Already calculated")
            continue
        end

        # Step 1: Read input data
        @info "Step 1/6: Reading input data..."
        t_start = time()
        data_dict = get_input_data(input_path)
        t_read = time() - t_start
        @info "Input data loaded in $(round(t_read, digits=2))s"

        # Step 2: Parse data
        @info "Step 2/6: Parsing data structures..."
        t_start = time()
        data_structures = parse_data(data_dict)
        t_parse = time() - t_start
        @info "Data parsed in $(round(t_parse, digits=2))s"

        # Step 3: Create model
        timestamp = Dates.format(now(), "mmdd_HHMM")
        case_name = "ff_$(timestamp)"

        @info "Step 3/6: Creating optimization model..."
        t_start = time()
        model, data_structures = create_model(data_structures, case_name, include_vars=relevant_vars)
        t_create = time() - t_start
        @info "Model created in $(round(t_create, digits=2))s"
        @info "Variables: $(num_variables(model))"

        # Step 4: Solver config (LP - no MIP settings needed)
        set_optimizer_attribute(model, "Method", 2)        # Barrier
        set_optimizer_attribute(model, "NumericFocus", 3)
        set_optimizer_attribute(model, "ScaleFlag", 2)
        set_optimizer_attribute(model, "FeasibilityTol", 1e-5)
        set_optimizer_attribute(model, "OptimalityTol", 1e-5)
        set_optimizer_attribute(model, "Crossover", 0)
        set_optimizer_attribute(model, "BarConvTol", 1e-6)

        # Step 5: Add constraints (same as SM_batch_at_surcharge.jl)
        @info "Step 4/6: Adding constraints..."
        t_constraints_start = time()

        constraint_mandatory_breaks(model, data_structures)
        constraint_fueling_infrastructure(model, data_structures)
        constraint_fueling_infrastructure_expansion_shift(model, data_structures)
        constraint_soc_track(model, data_structures)
        constraint_soc_max(model, data_structures)
        constraint_travel_time_track(model, data_structures)
        constraint_demand_coverage(model, data_structures)
        constraint_vehicle_sizing(model, data_structures)
        constraint_vehicle_aging(model, data_structures)
        constraint_vehicle_stock_shift(model, data_structures)

        t_constraints = time() - t_constraints_start
        @info "Constraints added in $(round(t_constraints, digits=2))s"

        # Step 5b: FIX ENTIRE FLEET to baseline values
        @info "Step 5/6: Fixing fleet (h, h_exist, h_plus, h_minus) to baseline..."
        t_fix_start = time()

        # Fix ALL tech vehicles (both BEV tv_id=1 and ICEV tv_id=0)
        fix_counts = fix_fleet_from_results!(
            model, data_structures,
            BASELINE_RESULTS_DIR, BASELINE_CASE_PREFIX;
            fix_tv_ids=nothing  # Fix ALL vehicles (BEV + ICEV)
        )

        t_fix = time() - t_fix_start
        @info "Fleet fixed in $(round(t_fix, digits=2))s"
        @info "Fix counts: $fix_counts"

        # Objective (WITHOUT fuel costs, same as road-only surcharge runs)
        @info "Step 5.5/6: Adding objective..."
        t_start = time()
        objective(model, data_structures, false)
        t_obj = time() - t_start
        @info "Objective added in $(round(t_obj, digits=2))s"

        GC.gc()

        # Step 6: Solve
        @info "Step 6/6: Solving..."
        t_start = time()
        optimize!(model)
        t_optimize = time() - t_start
        @info "Optimization complete in $(round(t_optimize, digits=2))s"
        @info "Termination: $(termination_status(model))"

        # Check for infeasibility
        status = termination_status(model)
        if status != MOI.OPTIMAL && status != MOI.LOCALLY_SOLVED && status != MOI.ALMOST_OPTIMAL
            @error "Model not solved! Status: $status"
            if status == MOI.INFEASIBLE
                @info "Computing IIS to diagnose infeasibility..."
                try
                    compute_conflict!(model)
                    iis_file = joinpath(results_base, "$(folder_name)_iis.ilp")
                    mkpath(dirname(iis_file))
                    MOI.write_to_file(backend(model), iis_file)
                    @info "IIS written to: $iis_file"
                catch iis_err
                    @warn "Could not compute IIS: $iis_err"
                end
            end
            batch_results[folder_name] = Dict("status" => "FAILED", "error" => "Solver: $status")
            continue
        end

        # Save results
        results_file_path = normpath(joinpath(results_base, folder_name))
        mkpath(results_file_path)
        save_results(model, case_name, data_structures, true, results_file_path, folder_name)
        @info "Results saved to: $results_file_path"

        case_elapsed = time() - case_start_time
        batch_results[folder_name] = Dict(
            "status" => "SUCCESS",
            "total_time" => case_elapsed,
            "objective_value" => objective_value(model),
            "termination_status" => termination_status(model)
        )

        @info "COMPLETE: $folder_name ($(round(case_elapsed/60, digits=1))m, obj=$(round(objective_value(model), digits=0)))"

    catch e
        case_elapsed = time() - case_start_time
        @error "FAILED: $folder_name" exception=(e, catch_backtrace())
        batch_results[folder_name] = Dict("status" => "FAILED", "total_time" => case_elapsed, "error" => string(e))
    end

    GC.gc()
end

# ============================================================================
# SUMMARY
# ============================================================================

batch_elapsed = time() - batch_start_time

@info "\n" * "="^80
@info "FIXED FLEET BATCH COMPLETE"
@info "Total time: $(round(batch_elapsed/60, digits=1)) minutes"

for folder_name in sort(collect(keys(batch_results)))
    r = batch_results[folder_name]
    if r["status"] == "SUCCESS"
        @info "  $folder_name: SUCCESS ($(round(r["total_time"]/60, digits=1))m, obj=$(round(r["objective_value"], digits=0)))"
    elseif r["status"] == "FAILED"
        @info "  $folder_name: FAILED - $(get(r, "error", "unknown"))"
    else
        @info "  $folder_name: SKIPPED"
    end
end
@info "="^80
