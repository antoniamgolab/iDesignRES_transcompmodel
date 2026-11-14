"""
SM_batch_genesys.jl - Batch processing for GENeSYS-MOD electricity price scenarios

This script runs the transport model for each GENeSYS-MOD scenario.
GENeSYS scenarios should be created first using: python regenerate_genesys_scenarios.py

GENeSYS-MOD scenarios:
- Go RES v1.2: Most ambitious, highest electricity prices, €500/tCO₂ in 2040
- NECPEssentials v1.2: Moderate ambition, €250/tCO₂ in 2040
- REPowerEU++ v1.2: Self-sufficient EU, €350/tCO₂ in 2040
- Trinity v1.2: Lowest ambition, €400/tCO₂ in 2040
"""

using Pkg
Pkg.activate(joinpath(@__DIR__, "../.."))  # Activate the project environment

using YAML, JuMP, Gurobi, Printf, ProgressMeter, Dates

include(joinpath(@__DIR__, "../../src/TransComp.jl"))
using .TransComp

# ============================================================================
# CONFIGURATION: GENeSYS-MOD Scenarios
# ============================================================================

# DEBUG MODE: Set to true for fast debugging
DEBUG_MODE = false
DEBUG_ODPAIRS = 20

# GENeSYS scenario folders (created by regenerate_genesys_scenarios.py)
case_folders = [
    "genesys_scenarios/go_res",       # Go RES v1.2 - Most ambitious
    "genesys_scenarios/necp",         # NECPEssentials v1.2 - Moderate
    "genesys_scenarios/repower",      # REPowerEU++ v1.2 - Self-sufficient
    "genesys_scenarios/trinity",      # Trinity v1.2 - Lowest ambition
]

# Case labels
case_labels = Dict(
    "genesys_scenarios/go_res" => "Go RES v1.2 (€500/tCO₂)",
    "genesys_scenarios/necp" => "NECPEssentials v1.2 (€250/tCO₂)",
    "genesys_scenarios/repower" => "REPowerEU++ v1.2 (€350/tCO₂)",
    "genesys_scenarios/trinity" => "Trinity v1.2 (€400/tCO₂)",
)

# Variables to include in the model
relevant_vars = ["f", "h", "h_plus", "h_exist", "h_minus", "s", "q_fuel_infr_plus", "q_fuel_infr_plus_by_route", "soc", "travel_time", "extra_break_time"]

# ============================================================================
# BATCH PROCESSING LOOP
# ============================================================================

# Limit to first scenario in DEBUG_MODE
if DEBUG_MODE
    case_folders = case_folders[1:1]
    @warn "DEBUG MODE: Running only 1 scenario with $DEBUG_ODPAIRS OD pairs"
end

@info "="^80
@info "GENESYS-MOD SCENARIO ANALYSIS: $(length(case_folders)) scenarios"
@info "="^80

batch_start_time = time()
batch_results = Dict()

for (case_idx, folder) in enumerate(case_folders)
    @info "\n" * "="^80
    @info "CASE $(case_idx)/$(length(case_folders)): $folder"
    if haskey(case_labels, folder)
        @info "Label: $(case_labels[folder])"
    end
    @info "="^80

    case_start_time = time()

    try
        # ================================================================
        # Step 1: Setup paths
        # ================================================================
        script_dir = @__DIR__
        input_path = joinpath(script_dir, "input_data", folder)

        if !isdir(input_path)
            @warn "Input folder not found: $input_path - SKIPPING"
            @warn "Run 'python regenerate_genesys_scenarios.py' first to create scenarios"
            batch_results[folder] = Dict("status" => "SKIPPED", "reason" => "Folder not found")
            continue
        end

        @info "Input path: $input_path"

        # Generate output case name with timestamp
        scenario_name_for_case = split(folder, ['/', '\\'])[end]
        timestamp = Dates.format(now(), "yyyy-mm-dd_HH-MM-SS")
        case_name = "$(scenario_name_for_case)_genesys_$timestamp"

        # ================================================================
        # Step 2: Read and parse input data
        # ================================================================
        @info "Step 1/5: Reading input data..."
        t_start = time()
        data_dict = get_input_data(input_path)
        t_read = time() - t_start
        @info "✓ Input data loaded in $(round(t_read, digits=2)) seconds"

        # DEBUG MODE: Limit OD pairs
        if DEBUG_MODE
            original_count = length(data_dict["Odpair"])
            data_dict["Odpair"] = data_dict["Odpair"][1:min(DEBUG_ODPAIRS, original_count)]
            @warn "DEBUG: Reduced OD pairs from $original_count to $(length(data_dict["Odpair"]))"
        end

        @info "Step 2/5: Parsing data structures..."
        t_start = time()
        data_structures = parse_data(data_dict)
        t_parse = time() - t_start
        @info "✓ Data parsed in $(round(t_parse, digits=2)) seconds"

        # ================================================================
        # Step 3: Create optimization model
        # ================================================================
        @info "Step 3/5: Creating optimization model..."
        @info "Memory before model creation: $(round(Sys.free_memory()/1024^3, digits=2)) GB free"
        t_start = time()
        model, data_structures = create_model(data_structures, case_name, include_vars=relevant_vars)
        t_create = time() - t_start
        @info "✓ Model created in $(round(t_create, digits=2)) seconds"
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
        @info "✓ Solver configured"

        # ================================================================
        # Step 5: Add constraints
        # ================================================================
        @info "Step 4/5: Adding constraints..."
        t_constraints_start = time()

        # Mandatory breaks
        t_start = time()
        constraint_mandatory_breaks(model, data_structures)
        t_mandatory_breaks = time() - t_start
        @info "✓ Mandatory breaks constraint added in $(round(t_mandatory_breaks, digits=2))s"

        # Fueling demand constraint
        t_start = time()
        constraint_fueling_demand(model, data_structures)
        t_fueling_demand = time() - t_start
        @info "✓ Fueling demand constraint added in $(round(t_fueling_demand, digits=2))s"

        t_start = time()
        constraint_fueling_infrastructure(model, data_structures)
        t_fueling_infra = time() - t_start
        @info "✓ Fueling infrastructure constraint added in $(round(t_fueling_infra, digits=2))s"

        t_start = time()
        constraint_fueling_infrastructure_expansion_shift(model, data_structures)
        t_fueling_infra_expansion_shift = time() - t_start
        @info "✓ Fueling infrastructure expansion shift constraint added in $(round(t_fueling_infra_expansion_shift, digits=2))s"

        # BEV-specific constraints
        t_start = time()
        constraint_soc_track(model, data_structures)
        t_soc_track = time() - t_start
        @info "✓ State of charge tracking constraints added in $(round(t_soc_track, digits=2))s"

        t_start = time()
        constraint_soc_max(model, data_structures)
        t_soc = time() - t_start
        @info "✓ State of charge max constraints added in $(round(t_soc, digits=2))s"

        t_start = time()
        constraint_travel_time_track(model, data_structures)
        t_travel_time_track = time() - t_start
        @info "✓ Travel time tracking constraint added in $(round(t_travel_time_track, digits=2))s"

        # Mode shift constraints
        t_start = time()
        constraint_mode_shift(model, data_structures)
        t_mode_shift = time() - t_start
        @info "✓ Mode shift constraint added in $(round(t_mode_shift, digits=2))s"

        # Max mode share constraints
        t_start = time()
        if !isempty(data_structures["max_mode_share_list"])
            constraint_max_mode_share(model, data_structures)
            t_max_mode_share = time() - t_start
            @info "✓ Max mode share constraint added in $(round(t_max_mode_share, digits=2))s"
        else
            t_max_mode_share = 0.0
            @info "⊘ Skipping max mode share constraint (no constraints defined)"
        end

        # Core demand constraints
        t_start = time()
        constraint_demand_coverage(model, data_structures)
        t_demand_coverage = time() - t_start
        @info "✓ Demand coverage constraint added in $(round(t_demand_coverage, digits=2))s"

        # Vehicle fleet constraints
        t_start = time()
        constraint_vehicle_sizing(model, data_structures)
        t_vehicle_sizing = time() - t_start
        @info "✓ Vehicle sizing constraint added in $(round(t_vehicle_sizing, digits=2))s"

        t_start = time()
        constraint_vehicle_aging(model, data_structures)
        t_vehicle_aging = time() - t_start
        @info "✓ Vehicle aging constraint added in $(round(t_vehicle_aging, digits=2))s"

        t_start = time()
        constraint_vehicle_stock_shift(model, data_structures)
        t_vehicle_stock_shift = time() - t_start
        @info "✓ Vehicle stock shift constraint added in $(round(t_vehicle_stock_shift, digits=2))s"

        # No BEV purchases in 2020 (realistic: BEV long-haul trucks not available yet)
        t_start = time()
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
        t_no_bev_2020 = time() - t_start
        @info "✓ No BEV purchases in 2020 constraint added in $(round(t_no_bev_2020, digits=2))s"

        t_constraints = time() - t_constraints_start

        # ================================================================
        # Step 6: Add objective function (WITH fuel costs)
        # ================================================================
        @info "Step 4.5/5: Adding objective..."
        t_start = time()
        objective(model, data_structures, true)  # true = include fuel costs
        t_obj = time() - t_start
        @info "✓ Objective added in $(round(t_obj, digits=2)) seconds"

        GC.gc()  # Force garbage collection

        # ================================================================
        # Step 7: Solve optimization problem
        # ================================================================
        @info "Step 5/5: Solving optimization problem..."
        t_start = time()
        optimize!(model)
        t_optimize = time() - t_start
        @info "✓ Optimization complete in $(round(t_optimize, digits=2)) seconds"

        # ================================================================
        # Step 8: Save results
        # ================================================================
        @info "Saving results to file..."
        results_file_path = normpath(joinpath(script_dir, "results", folder))
        if !isdir(results_file_path)
            mkpath(results_file_path)
        end
        scenario_name = split(folder, ['/', '\\'])[end]
        @info "Saving results directly..."

        modeled_years_save = data_structures["modeled_years"]
        modeled_generations_save = data_structures["modeled_generations"]
        p_r_k_pairs = data_structures["p_r_k_pairs"]
        m_tv_pairs_save = data_structures["m_tv_pairs"]
        g_init_save = data_structures["g_init"]

        # Save f (flow) variable
        f_results = Dict{String, Float64}()
        if haskey(model.obj_dict, :f)
            @info "  Extracting f variable..."
            for idx in eachindex(model[:f])
                val = value(model[:f][idx])
                if !isnan(val) && abs(val) > 1e-6
                    f_results[string(idx)] = val
                end
            end
            YAML.write_file(joinpath(results_file_path, "$(case_name)_f_dict.yaml"), f_results)
            @info "  ✓ Saved $(length(f_results)) f values"
        end

        # Save h (vehicle stock) variable
        h_results = Dict{String, Float64}()
        if haskey(model.obj_dict, :h)
            @info "  Extracting h variable..."
            for idx in eachindex(model[:h])
                val = value(model[:h][idx])
                if !isnan(val) && abs(val) > 1e-6
                    h_results[string(idx)] = val
                end
            end
            YAML.write_file(joinpath(results_file_path, "$(case_name)_h_dict.yaml"), h_results)
            @info "  ✓ Saved $(length(h_results)) h values"
        end

        # Save s (energy) variable
        s_results = Dict{String, Float64}()
        if haskey(model.obj_dict, :s)
            @info "  Extracting s variable..."
            for idx in eachindex(model[:s])
                val = value(model[:s][idx])
                if !isnan(val) && abs(val) > 1e-6
                    s_results[string(idx)] = val
                end
            end
            YAML.write_file(joinpath(results_file_path, "$(case_name)_s_dict.yaml"), s_results)
            @info "  ✓ Saved $(length(s_results)) s values"
        end

        # Save h_plus (new purchases) variable
        h_plus_results = Dict{String, Float64}()
        if haskey(model.obj_dict, :h_plus)
            @info "  Extracting h_plus variable..."
            for idx in eachindex(model[:h_plus])
                val = value(model[:h_plus][idx])
                if !isnan(val) && abs(val) > 1e-6
                    h_plus_results[string(idx)] = val
                end
            end
            YAML.write_file(joinpath(results_file_path, "$(case_name)_h_plus_dict.yaml"), h_plus_results)
            @info "  ✓ Saved $(length(h_plus_results)) h_plus values"
        end

        # Save h_exist variable
        h_exist_results = Dict{String, Float64}()
        if haskey(model.obj_dict, :h_exist)
            @info "  Extracting h_exist variable..."
            for idx in eachindex(model[:h_exist])
                val = value(model[:h_exist][idx])
                if !isnan(val) && abs(val) > 1e-6
                    h_exist_results[string(idx)] = val
                end
            end
            YAML.write_file(joinpath(results_file_path, "$(case_name)_h_exist_dict.yaml"), h_exist_results)
            @info "  ✓ Saved $(length(h_exist_results)) h_exist values"
        end

        # Save h_minus variable
        h_minus_results = Dict{String, Float64}()
        if haskey(model.obj_dict, :h_minus)
            @info "  Extracting h_minus variable..."
            for idx in eachindex(model[:h_minus])
                val = value(model[:h_minus][idx])
                if !isnan(val) && abs(val) > 1e-6
                    h_minus_results[string(idx)] = val
                end
            end
            YAML.write_file(joinpath(results_file_path, "$(case_name)_h_minus_dict.yaml"), h_minus_results)
            @info "  ✓ Saved $(length(h_minus_results)) h_minus values"
        end

        # Save soc (state of charge) variable
        soc_results = Dict{String, Float64}()
        if haskey(model.obj_dict, :soc)
            @info "  Extracting soc variable..."
            for idx in eachindex(model[:soc])
                val = value(model[:soc][idx])
                if !isnan(val) && abs(val) > 1e-6
                    soc_results[string(idx)] = val
                end
            end
            YAML.write_file(joinpath(results_file_path, "$(case_name)_soc_dict.yaml"), soc_results)
            @info "  ✓ Saved $(length(soc_results)) soc values"
        end

        # Save travel_time variable
        travel_time_results = Dict{String, Float64}()
        if haskey(model.obj_dict, :travel_time)
            @info "  Extracting travel_time variable..."
            for idx in eachindex(model[:travel_time])
                val = value(model[:travel_time][idx])
                if !isnan(val) && abs(val) > 1e-6
                    travel_time_results[string(idx)] = val
                end
            end
            YAML.write_file(joinpath(results_file_path, "$(case_name)_travel_time_dict.yaml"), travel_time_results)
            @info "  ✓ Saved $(length(travel_time_results)) travel_time values"
        end

        # Save extra_break_time variable
        extra_break_time_results = Dict{String, Float64}()
        if haskey(model.obj_dict, :extra_break_time)
            @info "  Extracting extra_break_time variable..."
            for idx in eachindex(model[:extra_break_time])
                val = value(model[:extra_break_time][idx])
                if !isnan(val) && abs(val) > 1e-6
                    extra_break_time_results[string(idx)] = val
                end
            end
            YAML.write_file(joinpath(results_file_path, "$(case_name)_extra_break_time_dict.yaml"), extra_break_time_results)
            @info "  ✓ Saved $(length(extra_break_time_results)) extra_break_time values"
        end

        # Save q_fuel_infr_plus (infrastructure) variable
        q_infr_results = Dict{String, Float64}()
        if haskey(model.obj_dict, :q_fuel_infr_plus)
            @info "  Extracting q_fuel_infr_plus variable..."
            for idx in eachindex(model[:q_fuel_infr_plus])
                val = value(model[:q_fuel_infr_plus][idx])
                if !isnan(val) && abs(val) > 1e-6
                    q_infr_results[string(idx)] = val
                end
            end
            YAML.write_file(joinpath(results_file_path, "$(case_name)_q_fuel_infr_plus_dict.yaml"), q_infr_results)
            @info "  ✓ Saved $(length(q_infr_results)) q_fuel_infr_plus values"
        end

        # Save q_fuel_infr_plus_by_route variable
        q_infr_route_results = Dict{String, Float64}()
        if haskey(model.obj_dict, :q_fuel_infr_plus_by_route)
            @info "  Extracting q_fuel_infr_plus_by_route variable..."
            for idx in eachindex(model[:q_fuel_infr_plus_by_route])
                val = value(model[:q_fuel_infr_plus_by_route][idx])
                if !isnan(val) && abs(val) > 1e-6
                    q_infr_route_results[string(idx)] = val
                end
            end
            YAML.write_file(joinpath(results_file_path, "$(case_name)_q_fuel_infr_plus_by_route_dict.yaml"), q_infr_route_results)
            @info "  ✓ Saved $(length(q_infr_route_results)) q_fuel_infr_plus_by_route values"
        end

        @info "✓ All results saved to: $results_file_path"

        # ================================================================
        # Extract and display key statistics
        # ================================================================
        @info "Extracting key statistics..."

        modeled_years = data_structures["modeled_years"]
        tv_list = data_structures["techvehicle_list"]

        # Extract fleet by technology (0=ICEV, 1=BEV) and year
        @info "DEBUG: Extracting fleet data from h..."
        h_dict = model[:h]
        fleet_by_tech_year = Dict(0 => Dict{Int,Float64}(), 1 => Dict{Int,Float64}())
        for idx in eachindex(h_dict)
            var = h_dict[idx]
            val = value(var)
            if val > 1e-6
                year = idx[1]
                tv_id = idx[3]
                gen = idx[4]
                tv_idx = findfirst(tv -> tv.id == tv_id, tv_list)
                if tv_idx !== nothing
                    tv = tv_list[tv_idx]
                    tech = tv.technology.id
                    if !haskey(fleet_by_tech_year[tech], year)
                        fleet_by_tech_year[tech][year] = 0.0
                    end
                    fleet_by_tech_year[tech][year] += val
                end
            end
        end
        @info "DEBUG: Fleet extraction done"

        # Calculate and display fleet summary for key years
        @info "Fleet development (vehicles):"
        for year in [2020, 2030, 2040, 2050, 2060]
            if year in modeled_years
                icev = get(fleet_by_tech_year[0], year, 0.0)
                bev = get(fleet_by_tech_year[1], year, 0.0)
                total = icev + bev
                bev_pct = total > 0 ? round(bev / total * 100, digits=1) : 0.0
                @info "  $year: ICEV=$(round(Int, icev)), BEV=$(round(Int, bev)), BEV%=$bev_pct%"
            end
        end

        # Save summary statistics to YAML
        summary_stats = Dict(
            "case" => folder,
            "genesys_scenario" => get(case_labels, folder, folder),
            "objective_value" => objective_value(model),
            "fleet_by_year" => Dict(
                year => Dict(
                    "ICEV" => get(fleet_by_tech_year[0], year, 0.0),
                    "BEV" => get(fleet_by_tech_year[1], year, 0.0)
                ) for year in modeled_years
            )
        )
        YAML.write_file(joinpath(results_file_path, "summary_stats.yaml"), summary_stats)
        @info "✓ Summary statistics saved"

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
            "termination_status" => termination_status(model),
            "bev_share_2040" => let
                icev = get(fleet_by_tech_year[0], 2040, 0.0)
                bev = get(fleet_by_tech_year[1], 2040, 0.0)
                total = icev + bev
                total > 0 ? round(bev / total * 100, digits=1) : 0.0
            end,
            "bev_share_2060" => let
                icev = get(fleet_by_tech_year[0], 2060, 0.0)
                bev = get(fleet_by_tech_year[1], 2060, 0.0)
                total = icev + bev
                total > 0 ? round(bev / total * 100, digits=1) : 0.0
            end
        )

        @info "="^80
        @info "CASE COMPLETE: $folder"
        @info "  Total time: $(round(case_elapsed/60, digits=2)) minutes"
        @info "  Status: $(termination_status(model))"
        @info "  Objective value: $(objective_value(model))"
        @info "="^80

    catch e
        case_elapsed = time() - case_start_time
        @error "ERROR processing case: $folder"
        @error "Exception: $e"
        @error sprint(showerror, e, catch_backtrace())

        batch_results[folder] = Dict(
            "status" => "FAILED",
            "total_time" => case_elapsed,
            "error" => string(e)
        )

        @info "="^80
        @info "CASE FAILED: $folder - Continuing with next case..."
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
@info "GENESYS-MOD SCENARIO ANALYSIS COMPLETE"
@info "="^80
@info "Total batch time: $(round(batch_elapsed/60, digits=2)) minutes ($(round(batch_elapsed/3600, digits=2)) hours)"
@info ""
@info "Results summary:"
@info "-"^100
@info @sprintf("%-4s | %-30s | %8s | %12s | %10s | %10s", "#", "Scenario", "Status", "Obj (B EUR)", "BEV% 2040", "BEV% 2060")
@info "-"^100
for (idx, folder) in enumerate(case_folders)
    result = get(batch_results, folder, Dict("status" => "UNKNOWN"))
    status = result["status"]
    elapsed = get(result, "total_time", 0.0)

    # Extract scenario name (last part of path)
    scenario_name = split(folder, "/")[end]

    if status == "SUCCESS"
        obj_val = get(result, "objective_value", 0.0)
        bev_2040 = get(result, "bev_share_2040", 0.0)
        bev_2060 = get(result, "bev_share_2060", 0.0)
        @info @sprintf("%-4d | %-30s | %8s | %12.2f | %9.1f%% | %9.1f%%",
                       idx, scenario_name, "OK", obj_val/1e9, bev_2040, bev_2060)
    elseif status == "FAILED"
        @info @sprintf("%-4d | %-30s | %8s | %12s | %10s | %10s",
                       idx, scenario_name, "FAIL", "-", "-", "-")
    else
        @info @sprintf("%-4d | %-30s | %8s | %12s | %10s | %10s",
                       idx, scenario_name, "SKIP", "-", "-", "-")
    end
end
@info "-"^100

# Summary statistics across all successful cases
successful_cases = [r for (f, r) in batch_results if r["status"] == "SUCCESS"]
if !isempty(successful_cases)
    bev_2040_values = [r["bev_share_2040"] for r in successful_cases]
    bev_2060_values = [r["bev_share_2060"] for r in successful_cases]
    @info ""
    @info "BEV Share Summary (across $(length(successful_cases)) successful cases):"
    @info "  2040: min=$(minimum(bev_2040_values))%, max=$(maximum(bev_2040_values))%, mean=$(round(sum(bev_2040_values)/length(bev_2040_values), digits=1))%"
    @info "  2060: min=$(minimum(bev_2060_values))%, max=$(maximum(bev_2060_values))%, mean=$(round(sum(bev_2060_values)/length(bev_2060_values), digits=1))%"
end

@info "="^80
@info "Total batch time: $(round(batch_elapsed/60, digits=2)) minutes ($(round(batch_elapsed/3600, digits=2)) hours)"
@info "All cases processed. Results saved in 'results/genesys_scenarios/' subdirectories."
@info "="^80
