"""
SM_batch_vot_breaks_experiment.jl
=================================

Conference paper experiment: VOT × charging restriction interaction.

For each VoT level (10, 20, 30, 45, 60 EUR/h), runs TWO models:

  Phase A — BREAKS-ONLY: Charging restricted to mandatory break locations.
            Fleet is endogenously optimized. This determines the fleet composition.
            → results/vot_breaks_experiment/vot_XX/breaks_only/

  Phase B — FIXED-FLEET, ALL LOCATIONS: Takes the fleet from Phase A,
            removes the breaks-only constraint, and re-optimizes charging
            allocation across all locations.
            → results/vot_breaks_experiment/vot_XX/fixed_fleet_all_locations/

The delta between Phase A and Phase B isolates the pure spatial flexibility
value for each VoT level: same fleet, only the charging freedom changes.

Input data: vot_sensitivity_v2/vot_XX (created by create_vot_sensitivity_scenarios.py)

Total runs: 5 VoT × 2 phases = 10 optimization runs
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

# VoT levels to test
VOT_VALUES = [10, 20, 30, 45, 60]

# Input folders (created by create_vot_sensitivity_scenarios.py)
INPUT_BASE = "vot_sensitivity_v2"

# Output base
RESULTS_BASE = joinpath(script_dir, "results", "vot_breaks_experiment")

# Variables to save
relevant_vars = ["f", "h", "h_plus", "h_exist", "h_minus", "s",
                  "q_fuel_infr_plus", "q_fuel_infr_plus_by_route",
                  "soc", "travel_time", "extra_break_time"]

# DEBUG MODE
DEBUG_MODE = false
DEBUG_ODPAIRS = 20

# ============================================================================
# HELPER: Configure solver (consistent across all runs)
# ============================================================================
function configure_solver!(model)
    set_optimizer_attribute(model, "Method", 2)           # Barrier method
    set_optimizer_attribute(model, "MIPFocus", 1)         # Focus on feasibility
    set_optimizer_attribute(model, "Cuts", 1)             # Conservative cuts
    set_optimizer_attribute(model, "MIPGap", 0.01)        # 1% gap
    set_optimizer_attribute(model, "NumericFocus", 3)     # Maximum numerical precision
    set_optimizer_attribute(model, "ScaleFlag", 2)        # Aggressive auto-scaling
    set_optimizer_attribute(model, "FeasibilityTol", 1e-5)
    set_optimizer_attribute(model, "OptimalityTol", 1e-5)
    set_optimizer_attribute(model, "IntFeasTol", 1e-4)
    set_optimizer_attribute(model, "Crossover", -1)       # Enable crossover
    set_optimizer_attribute(model, "BarConvTol", 1e-8)    # Tight barrier convergence
end

# ============================================================================
# HELPER: Add standard constraints (shared between Phase A and Phase B)
# ============================================================================
function add_standard_constraints!(model, data_structures)
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
    @info "  ✓ no_bev_2020"
end

# ============================================================================
# HELPER: Save all result variables to YAML
# ============================================================================
function save_all_results(model, data_structures, results_path, case_name)
    if !isdir(results_path)
        mkpath(results_path)
    end

    var_names = [
        (:f, "f_dict"),
        (:h, "h_dict"),
        (:h_plus, "h_plus_dict"),
        (:h_exist, "h_exist_dict"),
        (:h_minus, "h_minus_dict"),
        (:s, "s_dict"),
        (:soc, "soc_dict"),
        (:travel_time, "travel_time_dict"),
        (:extra_break_time, "extra_break_time_dict"),
        (:q_fuel_infr_plus, "q_fuel_infr_plus_dict"),
        (:q_fuel_infr_plus_by_route, "q_fuel_infr_plus_by_route_dict"),
    ]

    for (sym, suffix) in var_names
        if haskey(model.obj_dict, sym)
            results = Dict{String, Float64}()
            for idx in eachindex(model[sym])
                val = value(model[sym][idx])
                if !isnan(val) && abs(val) > 1e-6
                    results[string(idx)] = val
                end
            end
            YAML.write_file(joinpath(results_path, "$(case_name)_$(suffix).yaml"), results)
            @info "  ✓ Saved $(length(results)) $(sym) values"
        end
    end
end

# ============================================================================
# HELPER: Extract fleet statistics
# ============================================================================
function extract_fleet_stats(model, data_structures)
    modeled_years = data_structures["modeled_years"]
    tv_list = data_structures["techvehicle_list"]

    fleet_by_tech_year = Dict(0 => Dict{Int,Float64}(), 1 => Dict{Int,Float64}())
    h_dict = model[:h]
    for idx in eachindex(h_dict)
        val = value(h_dict[idx])
        if val > 1e-6
            year = idx[1]
            tv_id = idx[3]
            tv_idx = findfirst(tv -> tv.id == tv_id, tv_list)
            if tv_idx !== nothing
                tech = tv_list[tv_idx].technology.id
                if !haskey(fleet_by_tech_year[tech], year)
                    fleet_by_tech_year[tech][year] = 0.0
                end
                fleet_by_tech_year[tech][year] += val
            end
        end
    end

    # Extract energy by year
    energy_by_year = Dict{Int,Float64}()
    if haskey(model.obj_dict, :s)
        s_dict = model[:s]
        for idx in eachindex(s_dict)
            val = value(s_dict[idx])
            if val > 1e-6
                year = idx[1]
                if !haskey(energy_by_year, year)
                    energy_by_year[year] = 0.0
                end
                energy_by_year[year] += val
            end
        end
    end

    return fleet_by_tech_year, energy_by_year
end

# ============================================================================
# MAIN EXPERIMENT
# ============================================================================

@info "="^80
@info "VOT × BREAKS EXPERIMENT"
@info "VoT levels: $(VOT_VALUES) EUR/h"
@info "Phases: A (breaks-only) + B (fixed-fleet, all locations)"
@info "Total runs: $(length(VOT_VALUES) * 2)"
@info "="^80

experiment_start = time()

# Store results for summary
all_results = Dict{String, Dict}()

for vot in VOT_VALUES
    scenario_name = "vot_$(lpad(vot, 2, '0'))"
    input_folder = "$INPUT_BASE/$scenario_name"
    input_path = joinpath(script_dir, "input_data", input_folder)

    @info "\n" * "="^80
    @info "VOT = $vot EUR/h ($scenario_name)"
    @info "="^80

    if !isdir(input_path)
        @error "Input folder not found: $input_path"
        @error "Run 'python create_vot_sensitivity_scenarios.py' first!"
        all_results["$(scenario_name)_A"] = Dict("status" => "FAILED", "error" => "Input not found")
        all_results["$(scenario_name)_B"] = Dict("status" => "FAILED", "error" => "Phase A not available")
        continue
    end

    # ==================================================================
    # PHASE A: BREAKS-ONLY (fleet endogenous)
    # ==================================================================
    phase_a_results_path = joinpath(RESULTS_BASE, scenario_name, "breaks_only")
    phase_a_already_done = isdir(phase_a_results_path) && !isempty(readdir(phase_a_results_path))

    phase_a_case_name = ""

    if phase_a_already_done && !DEBUG_MODE
        @info "Phase A already done for $scenario_name — skipping"
        # Find the case prefix from existing results
        existing_files = readdir(phase_a_results_path)
        h_files = filter(f -> endswith(f, "_h_dict.yaml"), existing_files)
        if !isempty(h_files)
            phase_a_case_name = replace(h_files[1], "_h_dict.yaml" => "")
        end
        all_results["$(scenario_name)_A"] = Dict("status" => "SKIPPED", "reason" => "Already calculated")
    else
        @info "--- Phase A: BREAKS-ONLY (fleet endogenous) ---"
        t_phase_a = time()

        try
            # Read and parse input data
            data_dict = get_input_data(input_path)
            if DEBUG_MODE
                original_count = length(data_dict["Odpair"])
                data_dict["Odpair"] = data_dict["Odpair"][1:min(DEBUG_ODPAIRS, original_count)]
                @warn "DEBUG: Reduced OD pairs from $original_count to $(length(data_dict["Odpair"]))"
            end
            data_structures = parse_data(data_dict)

            # Verify VoT
            if !isempty(data_structures["financial_status_list"])
                @info "VoT value: $(data_structures["financial_status_list"][1].VoT) EUR/hour"
            end

            # Create model
            timestamp = Dates.format(now(), "yyyy-mm-dd_HH-MM-SS")
            phase_a_case_name = "$(scenario_name)_brk_$(timestamp)"
            model, data_structures = create_model(data_structures, phase_a_case_name, include_vars=relevant_vars)
            @info "Model: $(num_variables(model)) variables"

            # Configure solver
            configure_solver!(model)

            # Add constraints (standard + breaks-only)
            @info "Adding constraints (with breaks-only)..."
            add_standard_constraints!(model, data_structures)

            constraint_charging_at_breaks_only(model, data_structures)
            @info "  ✓ charging_at_breaks_only"

            # Objective
            objective(model, data_structures, true)
            @info "  ✓ objective"

            GC.gc()

            # Solve
            @info "Solving Phase A..."
            optimize!(model)

            phase_a_elapsed = time() - t_phase_a
            @info "Phase A solved in $(round(phase_a_elapsed/60, digits=2)) min"
            @info "Status: $(termination_status(model))"
            @info "Objective: $(objective_value(model))"

            # Save results
            save_all_results(model, data_structures, phase_a_results_path, phase_a_case_name)

            # Extract statistics
            fleet_stats, energy_stats = extract_fleet_stats(model, data_structures)

            # Save summary
            summary = Dict(
                "vot" => vot,
                "phase" => "breaks_only",
                "objective_value" => objective_value(model),
                "termination_status" => string(termination_status(model)),
                "solve_time_seconds" => phase_a_elapsed,
                "fleet_by_year" => Dict(
                    y => Dict("ICEV" => get(fleet_stats[0], y, 0.0), "BEV" => get(fleet_stats[1], y, 0.0))
                    for y in data_structures["modeled_years"]
                ),
                "energy_by_year" => energy_stats
            )
            YAML.write_file(joinpath(phase_a_results_path, "summary_stats.yaml"), summary)

            all_results["$(scenario_name)_A"] = Dict(
                "status" => "SUCCESS",
                "objective" => objective_value(model),
                "time" => phase_a_elapsed,
                "bev_2040" => get(fleet_stats[1], 2040, 0.0),
                "total_2040" => get(fleet_stats[0], 2040, 0.0) + get(fleet_stats[1], 2040, 0.0)
            )

            # Print fleet summary
            @info "Fleet summary:"
            for year in [2032, 2040, 2048, 2056]
                if year in data_structures["modeled_years"]
                    icev = get(fleet_stats[0], year, 0.0)
                    bev = get(fleet_stats[1], year, 0.0)
                    total = icev + bev
                    bev_pct = total > 0 ? round(bev / total * 100, digits=1) : 0.0
                    @info "  $year: ICEV=$(round(Int, icev)), BEV=$(round(Int, bev)), BEV%=$(bev_pct)%"
                end
            end

            model = nothing  # Free memory
            GC.gc()

        catch e
            @error "Phase A FAILED for $scenario_name: $e"
            @error sprint(showerror, e, catch_backtrace())
            all_results["$(scenario_name)_A"] = Dict("status" => "FAILED", "error" => string(e))
            all_results["$(scenario_name)_B"] = Dict("status" => "FAILED", "error" => "Phase A failed")
            GC.gc()
            continue  # Skip Phase B if Phase A failed
        end
    end

    # ==================================================================
    # PHASE B: FIXED-FLEET, ALL LOCATIONS (no breaks-only constraint)
    # ==================================================================
    phase_b_results_path = joinpath(RESULTS_BASE, scenario_name, "fixed_fleet_all_locations")
    phase_b_already_done = isdir(phase_b_results_path) && !isempty(readdir(phase_b_results_path))

    if phase_b_already_done && !DEBUG_MODE
        @info "Phase B already done for $scenario_name — skipping"
        all_results["$(scenario_name)_B"] = Dict("status" => "SKIPPED", "reason" => "Already calculated")
        continue
    end

    if isempty(phase_a_case_name)
        @error "No Phase A case prefix found for $scenario_name — cannot run Phase B"
        all_results["$(scenario_name)_B"] = Dict("status" => "FAILED", "error" => "No Phase A results")
        continue
    end

    @info "--- Phase B: FIXED-FLEET, ALL LOCATIONS ---"
    t_phase_b = time()

    try
        # Read and parse input data (same input as Phase A)
        data_dict = get_input_data(input_path)
        if DEBUG_MODE
            original_count = length(data_dict["Odpair"])
            data_dict["Odpair"] = data_dict["Odpair"][1:min(DEBUG_ODPAIRS, original_count)]
        end
        data_structures = parse_data(data_dict)

        # Create model
        timestamp = Dates.format(now(), "yyyy-mm-dd_HH-MM-SS")
        phase_b_case_name = "$(scenario_name)_ff_$(timestamp)"
        model, data_structures = create_model(data_structures, phase_b_case_name, include_vars=relevant_vars)
        @info "Model: $(num_variables(model)) variables"

        # Configure solver
        configure_solver!(model)

        # Add constraints (standard — NO breaks-only constraint)
        @info "Adding constraints (NO breaks-only)..."
        add_standard_constraints!(model, data_structures)
        # NOTE: constraint_charging_at_breaks_only is NOT added here

        # FIX FLEET to Phase A values
        @info "Fixing fleet to Phase A (breaks-only) values..."
        fix_counts = fix_fleet_from_results!(
            model, data_structures,
            phase_a_results_path, phase_a_case_name;
            fix_tv_ids=nothing  # Fix ALL vehicles (BEV + ICEV)
        )
        @info "Fleet fix counts: $fix_counts"

        # Objective
        objective(model, data_structures, true)
        @info "  ✓ objective"

        GC.gc()

        # Solve
        @info "Solving Phase B..."
        optimize!(model)

        phase_b_elapsed = time() - t_phase_b
        @info "Phase B solved in $(round(phase_b_elapsed/60, digits=2)) min"
        @info "Status: $(termination_status(model))"
        @info "Objective: $(objective_value(model))"

        # Save results
        save_all_results(model, data_structures, phase_b_results_path, phase_b_case_name)

        # Extract statistics
        fleet_stats, energy_stats = extract_fleet_stats(model, data_structures)

        # Save summary
        summary = Dict(
            "vot" => vot,
            "phase" => "fixed_fleet_all_locations",
            "objective_value" => objective_value(model),
            "termination_status" => string(termination_status(model)),
            "solve_time_seconds" => phase_b_elapsed,
            "fleet_source" => "breaks_only (Phase A)",
            "fleet_case_prefix" => phase_a_case_name,
            "fleet_by_year" => Dict(
                y => Dict("ICEV" => get(fleet_stats[0], y, 0.0), "BEV" => get(fleet_stats[1], y, 0.0))
                for y in data_structures["modeled_years"]
            ),
            "energy_by_year" => energy_stats
        )
        YAML.write_file(joinpath(phase_b_results_path, "summary_stats.yaml"), summary)

        all_results["$(scenario_name)_B"] = Dict(
            "status" => "SUCCESS",
            "objective" => objective_value(model),
            "time" => phase_b_elapsed,
        )

        # Print delta
        if haskey(all_results, "$(scenario_name)_A") && all_results["$(scenario_name)_A"]["status"] == "SUCCESS"
            obj_a = all_results["$(scenario_name)_A"]["objective"]
            obj_b = objective_value(model)
            delta = obj_a - obj_b
            delta_pct = delta / obj_a * 100
            @info "SPATIAL FLEXIBILITY VALUE (VoT=$vot):"
            @info "  Breaks-only (A):      $(round(obj_a/1e9, digits=3)) B EUR"
            @info "  All-locations (B):     $(round(obj_b/1e9, digits=3)) B EUR"
            @info "  Savings:               $(round(delta/1e6, digits=1)) M EUR ($(round(delta_pct, digits=3))%)"
        end

        model = nothing
        GC.gc()

    catch e
        @error "Phase B FAILED for $scenario_name: $e"
        @error sprint(showerror, e, catch_backtrace())
        all_results["$(scenario_name)_B"] = Dict("status" => "FAILED", "error" => string(e))
        GC.gc()
    end
end

# ============================================================================
# EXPERIMENT SUMMARY
# ============================================================================

experiment_elapsed = time() - experiment_start

@info "\n" * "="^80
@info "VOT × BREAKS EXPERIMENT COMPLETE"
@info "="^80
@info "Total time: $(round(experiment_elapsed/60, digits=2)) min ($(round(experiment_elapsed/3600, digits=2)) hours)"
@info ""

# Summary table
@info "-"^110
@info @sprintf("%-6s | %-12s | %-12s | %-12s | %-12s | %-10s | %-10s",
               "VoT", "Phase A Obj", "Phase B Obj", "Delta (MEUR)", "Delta (%)", "Status A", "Status B")
@info "-"^110

for vot in VOT_VALUES
    scenario_name = "vot_$(lpad(vot, 2, '0'))"
    res_a = get(all_results, "$(scenario_name)_A", Dict("status" => "MISSING"))
    res_b = get(all_results, "$(scenario_name)_B", Dict("status" => "MISSING"))

    status_a = res_a["status"]
    status_b = res_b["status"]

    if status_a == "SUCCESS" && status_b == "SUCCESS"
        obj_a = res_a["objective"]
        obj_b = res_b["objective"]
        delta = obj_a - obj_b
        delta_pct = delta / obj_a * 100
        @info @sprintf("%-6d | %12.3f | %12.3f | %12.1f | %11.3f%% | %-10s | %-10s",
                       vot, obj_a/1e9, obj_b/1e9, delta/1e6, delta_pct, "OK", "OK")
    else
        @info @sprintf("%-6d | %12s | %12s | %12s | %12s | %-10s | %-10s",
                       vot, "-", "-", "-", "-", status_a, status_b)
    end
end
@info "-"^110

# Save experiment summary to YAML
experiment_summary = Dict(
    "experiment" => "vot_breaks_interaction",
    "vot_values" => VOT_VALUES,
    "total_time_seconds" => experiment_elapsed,
    "results" => all_results
)
mkpath(RESULTS_BASE)
YAML.write_file(joinpath(RESULTS_BASE, "experiment_summary.yaml"), experiment_summary)
@info "Experiment summary saved to: $(joinpath(RESULTS_BASE, "experiment_summary.yaml"))"

@info "="^80
@info "Results saved in: $RESULTS_BASE"
@info "  vot_XX/breaks_only/           — Phase A (fleet + charging at breaks)"
@info "  vot_XX/fixed_fleet_all_locations/ — Phase B (same fleet, charging anywhere)"
@info "="^80
