"""
SM_batch_at_surcharge_rail.jl - Austrian surcharge sensitivity with rail modal shift

Runs 6 scenarios testing the effect of surcharges on Austrian border nodes,
WITH rail modal shift option (max 30% rail share).
- 3 electricity price surcharges: +0.01, +0.02, +0.04 EUR/kWh
- 3 network cost surcharges: +2, +5, +10 EUR/kW/yr

Based on REPowerEU++ (scenario_002) as baseline.
Uses same constraints as SM_batch_rail.jl (mandatory breaks, mode shift, NO charging-at-breaks-only).
"""

using Pkg
Pkg.activate(joinpath(@__DIR__, "../.."))

using YAML, JuMP, Gurobi, Printf, Dates

include(joinpath(@__DIR__, "../../src/TransComp.jl"))
using .TransComp

# ============================================================================
# CONFIGURATION
# ============================================================================

surcharge_dir = joinpath(@__DIR__, "input_data", "at_surcharge_scenarios_rail")

case_folders = filter(isdir, [joinpath(surcharge_dir, d) for d in readdir(surcharge_dir)])
case_names = [basename(f) for f in case_folders]
sort!(case_names)

@info "Found $(length(case_names)) AT surcharge+rail scenarios: $(case_names)"

relevant_vars = ["f", "h", "h_plus", "h_exist", "h_minus", "s", "q_fuel_infr_plus", "soc", "travel_time", "extra_break_time"]

# ============================================================================
# BATCH PROCESSING
# ============================================================================

@info "="^80
@info "AT SURCHARGE + RAIL BATCH PROCESSING"
@info "Total scenarios: $(length(case_names))"
@info "="^80

batch_start_time = time()
batch_results = Dict()

for (case_idx, folder_name) in enumerate(case_names)
    @info "\n" * "="^80
    @info "SCENARIO $(case_idx)/$(length(case_names)): $folder_name"
    @info "="^80

    case_start_time = time()

    try
        script_dir = @__DIR__
        input_path = joinpath(surcharge_dir, folder_name)

        # Overwrite existing results (re-running with Crossover=-1)
        results_check_path = joinpath(script_dir, "results", "at_surcharge_rail", folder_name)
        if isdir(results_check_path) && !isempty(readdir(results_check_path))
            @info "Overwriting existing results for $folder_name"
        end

        # Step 1: Read input data
        @info "Step 1/5: Reading input data..."
        t_start = time()
        data_dict = get_input_data(input_path)
        t_read = time() - t_start
        @info "Input data loaded in $(round(t_read, digits=2))s"

        # Step 2: Parse data
        @info "Step 2/5: Parsing data structures..."
        t_start = time()
        data_structures = parse_data(data_dict)
        t_parse = time() - t_start
        @info "Data parsed in $(round(t_parse, digits=2))s"

        # Step 3: Create model
        timestamp = Dates.format(now(), "mmdd_HHMM")
        case_name = "atr_$(timestamp)"

        @info "Step 3/5: Creating optimization model..."
        t_start = time()
        model, data_structures = create_model(data_structures, case_name, include_vars=relevant_vars)
        t_create = time() - t_start
        @info "Model created in $(round(t_create, digits=2))s"
        @info "Variables: $(num_variables(model))"

        # Step 4: Solver config
        set_optimizer_attribute(model, "Method", 2)
        set_optimizer_attribute(model, "MIPFocus", 1)
        set_optimizer_attribute(model, "Cuts", 1)
        set_optimizer_attribute(model, "MIPGap", 0.01)
        set_optimizer_attribute(model, "NumericFocus", 3)
        set_optimizer_attribute(model, "ScaleFlag", 2)
        set_optimizer_attribute(model, "FeasibilityTol", 1e-5)
        set_optimizer_attribute(model, "OptimalityTol", 1e-5)
        set_optimizer_attribute(model, "IntFeasTol", 1e-4)
        set_optimizer_attribute(model, "Crossover", -1)       # Enable crossover for exact vertex solution
        set_optimizer_attribute(model, "BarConvTol", 1e-8)    # Tight barrier convergence

        # Step 5: Add constraints (same as SM_batch_rail.jl)
        @info "Step 4/5: Adding constraints..."
        t_constraints_start = time()

        constraint_mandatory_breaks(model, data_structures)
        constraint_fueling_demand(model, data_structures)
        constraint_fueling_infrastructure(model, data_structures)
        constraint_fueling_infrastructure_expansion_shift(model, data_structures)
        constraint_soc_track(model, data_structures)
        constraint_soc_max(model, data_structures)
        constraint_travel_time_track(model, data_structures)

        # Modal shift constraints (key difference from road-only surcharge)
        constraint_mode_shift(model, data_structures)
        if !isempty(data_structures["max_mode_share_list"])
            constraint_max_mode_share(model, data_structures)
            @info "Max mode share constraint added (30% rail cap)"
        end

        constraint_demand_coverage(model, data_structures)
        constraint_vehicle_sizing(model, data_structures)
        constraint_vehicle_aging(model, data_structures)
        constraint_vehicle_stock_shift(model, data_structures)

        # No BEV purchases in 2020
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

        t_constraints = time() - t_constraints_start
        @info "Constraints added in $(round(t_constraints, digits=2))s"

        # Objective (WITH fuel costs, same as rail batch)
        @info "Step 4.5/5: Adding objective..."
        t_start = time()
        objective(model, data_structures, true)
        t_obj = time() - t_start
        @info "Objective added in $(round(t_obj, digits=2))s"

        GC.gc()

        # Step 6: Solve
        @info "Step 5/5: Solving..."
        t_start = time()
        optimize!(model)
        t_optimize = time() - t_start
        @info "Optimization complete in $(round(t_optimize, digits=2))s"

        # Step 7: Save results
        results_file_path = normpath(joinpath(script_dir, "results", "at_surcharge_rail", folder_name))
        mkpath(results_file_path)
        save_results(model, case_name, data_structures, true, results_file_path, folder_name)
        summary_stats = Dict(
            "objective_value" => objective_value(model),
            "termination_status" => string(termination_status(model)),
            "case_name" => case_name,
        )
        YAML.write_file(joinpath(results_file_path, "summary_stats.yaml"), summary_stats)
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
@info "AT SURCHARGE + RAIL BATCH COMPLETE"
@info "Total time: $(round(batch_elapsed/60, digits=1)) minutes"

n_success = count(r -> r.second["status"] == "SUCCESS", batch_results)
n_failed = count(r -> r.second["status"] == "FAILED", batch_results)
n_skipped = count(r -> r.second["status"] == "SKIPPED", batch_results)
@info "Success: $n_success, Failed: $n_failed, Skipped: $n_skipped"

for folder_name in sort(collect(keys(batch_results)))
    r = batch_results[folder_name]
    if r["status"] == "SUCCESS"
        @info "  $folder_name: SUCCESS ($(round(r["total_time"]/60, digits=1))m, obj=$(round(r["objective_value"], digits=0)))"
    elseif r["status"] == "FAILED"
        @info "  $folder_name: FAILED"
    else
        @info "  $folder_name: SKIPPED"
    end
end
@info "="^80
