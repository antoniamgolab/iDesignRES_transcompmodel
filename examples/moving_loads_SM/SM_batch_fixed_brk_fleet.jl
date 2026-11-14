"""
SM_batch_fixed_brk_fleet.jl - Unconstrained charging with fleet fixed to breaks-only results

Takes the fleet composition (h, h_exist, h_plus, h_minus) from the breaks-only runs
and re-runs the UNCONSTRAINED model (no constraint_charging_at_breaks_only).
This isolates the pure spatial reallocation effect: with the SAME fleet, does the
unconstrained model produce lower fuel costs than the breaks-only model?

Results saved to: results/uncertainty_scenarios_fixed_brk_fleet/
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

# Breaks-only fleet sources
BRK_RESULTS_BASE = joinpath(script_dir, "results", "uncertainty_scenarios_breaks_only")
BRK_CASE_PREFIXES = Dict(
    "scenario_000" => "scenario_000_cs_2026-02-14_20-51-10",
    "scenario_001" => "scenario_001_cs_2026-02-14_22-29-10",
    "scenario_002" => "scenario_002_cs_2026-02-14_23-47-28",
    "scenario_003" => "scenario_003_cs_2026-02-15_01-16-54",
)

# Input data (same as original unconstrained scenarios)
case_folders = [
    "uncertainty_scenarios/scenario_000",
    "uncertainty_scenarios/scenario_001",
    "uncertainty_scenarios/scenario_002",
    "uncertainty_scenarios/scenario_003",
]

results_base = joinpath(script_dir, "results", "uncertainty_scenarios_fixed_brk_fleet_v4")

relevant_vars = ["f", "h", "h_plus", "h_exist", "h_minus", "s",
                  "q_fuel_infr_plus", "soc", "travel_time", "extra_break_time"]

# ============================================================================
# BATCH PROCESSING
# ============================================================================

@info "="^80
@info "FIXED BRK-FLEET + UNCONSTRAINED CHARGING EXPERIMENT"
@info "Fleet source: breaks-only results"
@info "Charging: unconstrained (no breaks-only constraint)"
@info "Scenarios: $(length(case_folders))"
@info "="^80

batch_start_time = time()
batch_results = Dict()

for (case_idx, folder) in enumerate(case_folders)
    scenario_name = split(folder, ['/', '\\'])[end]

    @info "\n" * "="^80
    @info "SCENARIO $(case_idx)/$(length(case_folders)): $scenario_name (FIXED BRK FLEET)"
    @info "="^80

    case_start_time = time()

    try
        input_path = joinpath(script_dir, "input_data", folder)
        if !isdir(input_path)
            @error "Input folder not found: $input_path"
            batch_results[scenario_name] = Dict("status" => "FAILED", "error" => "Input not found")
            continue
        end

        # Check if results already exist
        results_check_path = joinpath(results_base, scenario_name)
        if isdir(results_check_path) && !isempty(readdir(results_check_path))
            @info "Results already exist for $scenario_name - SKIPPING"
            batch_results[scenario_name] = Dict("status" => "SKIPPED", "reason" => "Already calculated")
            continue
        end

        # Step 1: Read input data
        @info "Step 1/7: Reading input data..."
        t_start = time()
        data_dict = get_input_data(input_path)
        t_read = time() - t_start
        @info "Input data loaded in $(round(t_read, digits=2))s"

        # Step 2: Parse data
        @info "Step 2/7: Parsing data structures..."
        t_start = time()
        data_structures = parse_data(data_dict)
        t_parse = time() - t_start
        @info "Data parsed in $(round(t_parse, digits=2))s"

        # Step 3: Create model
        timestamp = Dates.format(now(), "yyyy-mm-dd_HH-MM-SS")
        case_name = "$(scenario_name)_ff_$(timestamp)"

        @info "Step 3/7: Creating optimization model..."
        t_start = time()
        model, data_structures = create_model(data_structures, case_name, include_vars=relevant_vars)
        t_create = time() - t_start
        @info "Model created in $(round(t_create, digits=2))s"
        @info "Variables: $(num_variables(model))"

        # Step 4: Solver config (MUST match SM_batch.jl exactly for comparable objectives)
        set_optimizer_attribute(model, "Method", 2)           # Barrier method
        set_optimizer_attribute(model, "MIPFocus", 1)         # Focus on feasibility
        set_optimizer_attribute(model, "Cuts", 1)             # Conservative cuts
        set_optimizer_attribute(model, "MIPGap", 0.01)        # 1% gap
        set_optimizer_attribute(model, "NumericFocus", 3)     # Maximum numerical precision
        set_optimizer_attribute(model, "ScaleFlag", 2)        # Aggressive auto-scaling
        set_optimizer_attribute(model, "FeasibilityTol", 1e-5)
        set_optimizer_attribute(model, "OptimalityTol", 1e-5)
        set_optimizer_attribute(model, "IntFeasTol", 1e-4)
        set_optimizer_attribute(model, "Crossover", -1)       # Enable crossover for exact vertex solution
        set_optimizer_attribute(model, "BarConvTol", 1e-8)    # Tight barrier convergence

        # Step 5: Add constraints (SAME as unconstrained — NO constraint_charging_at_breaks_only)
        @info "Step 5/7: Adding constraints (unconstrained charging)..."
        t_constraints_start = time()

        constraint_mandatory_breaks(model, data_structures)
        @info "  ✓ mandatory_breaks"

        constraint_fueling_demand(model, data_structures)
        @info "  ✓ fueling_demand"

        constraint_fueling_infrastructure(model, data_structures)
        @info "  ✓ fueling_infrastructure"

        constraint_fueling_infrastructure_expansion_shift(model, data_structures)
        @info "  ✓ fueling_infrastructure_expansion_shift"

        constraint_soc_track(model, data_structures)
        @info "  ✓ soc_track"

        constraint_soc_max(model, data_structures)
        @info "  ✓ soc_max"

        constraint_travel_time_track(model, data_structures)
        @info "  ✓ travel_time_track"

        constraint_mode_shift(model, data_structures)
        @info "  ✓ mode_shift"

        if !isempty(data_structures["max_mode_share_list"])
            constraint_max_mode_share(model, data_structures)
            @info "  ✓ max_mode_share"
        end

        constraint_demand_coverage(model, data_structures)
        @info "  ✓ demand_coverage"

        constraint_vehicle_sizing(model, data_structures)
        @info "  ✓ vehicle_sizing"

        constraint_vehicle_aging(model, data_structures)
        @info "  ✓ vehicle_aging"

        constraint_vehicle_stock_shift(model, data_structures)
        @info "  ✓ vehicle_stock_shift"

        # No BEV in 2020
        y_init = data_structures["y_init"]
        odpairs = data_structures["odpair_list"]
        techvehicles = data_structures["techvehicle_list"]
        g_init = data_structures["g_init"]
        time_step = data_structures["time_step"]
        bev_tvs = [tv for tv in techvehicles if tv.technology.id == 1]
        for tv in bev_tvs
            for r in odpairs
                for g in g_init:time_step:y_init
                    @constraint(model, model[:h_plus][y_init, r.id, tv.id, g] == 0)
                end
            end
        end
        @info "  ✓ no_bev_2020"

        t_constraints = time() - t_constraints_start
        @info "All constraints added in $(round(t_constraints, digits=2))s"

        # Step 6: FIX FLEET to breaks-only values
        @info "Step 6/7: Fixing fleet to breaks-only values..."
        t_fix_start = time()

        brk_results_dir = joinpath(BRK_RESULTS_BASE, scenario_name)
        brk_case_prefix = BRK_CASE_PREFIXES[scenario_name]

        fix_counts = fix_fleet_from_results!(
            model, data_structures,
            brk_results_dir, brk_case_prefix;
            fix_tv_ids=nothing  # Fix ALL vehicles (BEV + ICEV)
        )

        t_fix = time() - t_fix_start
        @info "Fleet fixed in $(round(t_fix, digits=2))s"
        @info "Fix counts: $fix_counts"

        # Objective WITH fuel costs (we want the optimizer to minimize fuel costs)
        @info "Step 6.5/7: Adding objective (WITH fuel costs)..."
        t_start = time()
        objective(model, data_structures, true)
        t_obj = time() - t_start
        @info "Objective added in $(round(t_obj, digits=2))s"

        GC.gc()

        # Step 7: Solve
        @info "Step 7/7: Solving..."
        t_start = time()
        optimize!(model)
        t_optimize = time() - t_start
        @info "Optimization complete in $(round(t_optimize, digits=2))s"
        @info "Termination: $(termination_status(model))"

        status = termination_status(model)
        if status != MOI.OPTIMAL && status != MOI.LOCALLY_SOLVED && status != MOI.ALMOST_OPTIMAL
            @error "Model not solved! Status: $status"
            if status == MOI.INFEASIBLE
                @info "Computing IIS to diagnose infeasibility..."
                try
                    compute_conflict!(model)
                    iis_file = joinpath(results_base, "$(scenario_name)_iis.ilp")
                    mkpath(dirname(iis_file))
                    MOI.write_to_file(backend(model), iis_file)
                    @info "IIS written to: $iis_file"
                catch iis_err
                    @warn "Could not compute IIS: $iis_err"
                end
            end
            batch_results[scenario_name] = Dict("status" => "FAILED", "error" => "Solver: $status")
            continue
        end

        # Save results
        results_file_path = normpath(joinpath(results_base, scenario_name))
        mkpath(results_file_path)

        # Direct save of key variables
        @info "Saving results..."
        for (var_name, dict_name) in [
            (:s, "s_dict"), (:f, "f_dict"), (:h, "h_dict"),
            (:h_plus, "h_plus_dict"), (:h_exist, "h_exist_dict"), (:h_minus, "h_minus_dict"),
            (:q_fuel_infr_plus, "q_fuel_infr_plus_dict"),
            (:soc, "soc_dict"), (:travel_time, "travel_time_dict"),
            (:extra_break_time, "extra_break_time_dict"),
        ]
            if haskey(model.obj_dict, var_name)
                results_dict = Dict{String, Float64}()
                for idx in eachindex(model[var_name])
                    val = value(model[var_name][idx])
                    if !isnan(val) && abs(val) > 1e-6
                        results_dict[string(idx)] = val
                    end
                end
                YAML.write_file(joinpath(results_file_path, "$(case_name)_$(dict_name).yaml"), results_dict)
                @info "  ✓ $dict_name: $(length(results_dict)) entries"
            end
        end

        # Save summary stats (including objective value)
        summary_stats = Dict(
            "objective_value" => objective_value(model),
            "termination_status" => string(termination_status(model)),
            "solve_time" => round(time() - case_start_time, digits=2),
            "case_name" => case_name,
        )
        YAML.write_file(joinpath(results_file_path, "summary_stats.yaml"), summary_stats)
        @info "  ✓ summary_stats saved"

        case_elapsed = time() - case_start_time
        batch_results[scenario_name] = Dict(
            "status" => "SUCCESS",
            "total_time" => case_elapsed,
            "objective_value" => objective_value(model),
            "termination_status" => termination_status(model)
        )

        @info "COMPLETE: $scenario_name ($(round(case_elapsed/60, digits=1))m, obj=$(round(objective_value(model), digits=0)))"

    catch e
        case_elapsed = time() - case_start_time
        @error "FAILED: $scenario_name" exception=(e, catch_backtrace())
        batch_results[scenario_name] = Dict("status" => "FAILED", "total_time" => case_elapsed, "error" => string(e))
    end

    GC.gc()
end

# ============================================================================
# SUMMARY
# ============================================================================

batch_elapsed = time() - batch_start_time

@info "\n" * "="^80
@info "FIXED BRK-FLEET BATCH COMPLETE"
@info "Total time: $(round(batch_elapsed/60, digits=1)) minutes"

for scenario_name in sort(collect(keys(batch_results)))
    r = batch_results[scenario_name]
    if r["status"] == "SUCCESS"
        @info "  $scenario_name: SUCCESS ($(round(r["total_time"]/60, digits=1))m, obj=$(round(r["objective_value"], digits=0)))"
    elseif r["status"] == "FAILED"
        @info "  $scenario_name: FAILED - $(get(r, "error", "unknown"))"
    else
        @info "  $scenario_name: SKIPPED"
    end
end
@info "="^80
