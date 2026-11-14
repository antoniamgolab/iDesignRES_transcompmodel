"""
SM_batch_eem.jl - Batch processing for EEM paper scenarios
(German electricity market zone splitting)

Scenario matrix: 1 baseline + 3 spread levels × 3 timings = 10 scenarios
- DE_unified: Baseline (single German price zone, Go RES)
- DE_split_{low,mid,high}_from{2020,2032,2040}: Zone split variants

Prerequisites:
  python create_eem_scenarios.py
"""

using Pkg
Pkg.activate(joinpath(@__DIR__, "../.."))  # Activate the project environment

using YAML, JuMP, Gurobi, Printf, ProgressMeter, Dates

include(joinpath(@__DIR__, "../../src/TransComp.jl"))
using .TransComp

# ============================================================================
# CONFIGURATION
# ============================================================================

DEBUG_MODE = false
DEBUG_ODPAIRS = 20

# EEM scenario folders (10 scenarios)
case_folders = [
    "eem_scenarios/DE_unified",              # Baseline (single zone)
    # Low spread (5%)
    "eem_scenarios/DE_split_low_from2020",
    "eem_scenarios/DE_split_low_from2032",
    "eem_scenarios/DE_split_low_from2040",
    # Mid spread (10%)
    "eem_scenarios/DE_split_mid_from2020",
    "eem_scenarios/DE_split_mid_from2032",
    "eem_scenarios/DE_split_mid_from2040",
    # High spread (20%)
    "eem_scenarios/DE_split_high_from2020",
    "eem_scenarios/DE_split_high_from2032",
    "eem_scenarios/DE_split_high_from2040",
]

case_labels = Dict(
    "eem_scenarios/DE_unified"              => "Baseline: single German zone (Go RES)",
    "eem_scenarios/DE_split_low_from2020"   => "Low (5%): split from 2020",
    "eem_scenarios/DE_split_low_from2032"   => "Low (5%): split from 2032",
    "eem_scenarios/DE_split_low_from2040"   => "Low (5%): split from 2040",
    "eem_scenarios/DE_split_mid_from2020"   => "Mid (10%): split from 2020",
    "eem_scenarios/DE_split_mid_from2032"   => "Mid (10%): split from 2032",
    "eem_scenarios/DE_split_mid_from2040"   => "Mid (10%): split from 2040",
    "eem_scenarios/DE_split_high_from2020"  => "High (20%): split from 2020",
    "eem_scenarios/DE_split_high_from2032"  => "High (20%): split from 2032",
    "eem_scenarios/DE_split_high_from2040"  => "High (20%): split from 2040",
)

# Variables to include in the model
relevant_vars = ["f", "h", "h_plus", "h_exist", "h_minus", "s", "q_fuel_infr_plus", "q_fuel_infr_plus_by_route", "soc", "travel_time", "extra_break_time"]

# ============================================================================
# BATCH PROCESSING LOOP
# ============================================================================

if DEBUG_MODE
    case_folders = case_folders[1:1]
    @warn "DEBUG MODE: Running only 1 scenario with $DEBUG_ODPAIRS OD pairs"
end

@info "="^80
@info "EEM PAPER: GERMAN ZONE SPLITTING ANALYSIS - $(length(case_folders)) scenarios"
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
            @warn "Run 'python create_eem_scenarios.py' first"
            batch_results[folder] = Dict("status" => "SKIPPED", "reason" => "Folder not found")
            continue
        end

        @info "Input path: $input_path"

        # Generate output case name
        scenario_name_for_case = replace(folder, "/" => "_", "\\" => "_")
        timestamp = Dates.format(now(), "yyyy-mm-dd_HH-MM-SS")
        case_name = "eem_$(scenario_name_for_case)_$timestamp"

        # ================================================================
        # Step 2: Read and parse input data
        # ================================================================
        @info "Step 1/5: Reading input data..."
        t_start = time()
        data_dict = get_input_data(input_path)
        t_read = time() - t_start
        @info "Input data loaded in $(round(t_read, digits=2)) seconds"

        if DEBUG_MODE
            original_count = length(data_dict["Odpair"])
            data_dict["Odpair"] = data_dict["Odpair"][1:min(DEBUG_ODPAIRS, original_count)]
            @warn "DEBUG: Reduced OD pairs from $original_count to $(length(data_dict["Odpair"]))"
        end

        @info "Step 2/5: Parsing data structures..."
        t_start = time()
        data_structures = parse_data(data_dict)
        t_parse = time() - t_start
        @info "Data parsed in $(round(t_parse, digits=2)) seconds"
        @info "OD pairs: $(length(data_structures["odpair_list"]))"

        # ================================================================
        # Step 3: Create optimization model
        # ================================================================
        @info "Step 3/5: Creating optimization model..."
        @info "Memory before model creation: $(round(Sys.free_memory()/1024^3, digits=2)) GB free"
        t_start = time()
        model, data_structures = create_model(data_structures, case_name, include_vars=relevant_vars)
        t_create = time() - t_start
        println("prkg first 10: ", collect(data_structures["p_r_k_g_pairs"])[1:10])
        @info "Model created in $(round(t_create, digits=2)) seconds"
        @info "Number of variables: $(num_variables(model))"
        q = model[:q_fuel_infr_plus]
        println("q_fuel_infr_plus axes:")        
         # Save the full ordering to a file
        open("prkg_ordering.txt", "w") do f
            for (i, t) in enumerate(collect(data_structures["p_r_k_g_pairs"]))
                println(f, "$i\t$t")
            end
        end
        println("Saved $(length(data_structures["p_r_k_g_pairs"])) entries to
        prkg_ordering.txt")                                                                                                                                                                               
        println("  Axis 1 (years): ", JuMP.Containers.axes(q)[1]) 
        println("  Axis 2 (f_l):   ", JuMP.Containers.axes(q)[2])
        println("  Axis 3 (geo):   ", JuMP.Containers.axes(q)[3])

        println("Sample eachindex: ", first(eachindex(model[:q_fuel_infr_plus])))
        println("Sample key:       ", first(keys(model[:q_fuel_infr_plus])))
        # ================================================================
        # Step 4: Configure solver
        # ================================================================
        @info "Configuring solver parameters..."
        set_optimizer_attribute(model, "Method", 2)           # Barrier method
        set_optimizer_attribute(model, "MIPFocus", 1)         # Focus on feasibility
        set_optimizer_attribute(model, "Cuts", 1)             # Conservative cuts
        set_optimizer_attribute(model, "MIPGap", 0.01)        # 1% gap
        set_optimizer_attribute(model, "NumericFocus", 3)     # Maximum numerical precision
        set_optimizer_attribute(model, "ScaleFlag", 2)        # Aggressive auto-scaling
        set_optimizer_attribute(model, "FeasibilityTol", 1e-5)
        set_optimizer_attribute(model, "OptimalityTol", 1e-5)
        set_optimizer_attribute(model, "IntFeasTol", 1e-4)
        # set_optimizer_attribute(model, "Crossover", 0)        # Skip crossover
        set_optimizer_attribute(model, "BarConvTol", 1e-6)

        # ================================================================
        # Step 5: Add constraints
        # ================================================================
        @info "Step 4/5: Adding constraints..."
        t_constraints_start = time()

        constraint_mandatory_breaks(model, data_structures)
        @info "  Mandatory breaks constraint added"

        constraint_fueling_demand(model, data_structures)
        @info "  Fueling demand constraint added"

        constraint_fueling_infrastructure(model, data_structures)
        @info "  Fueling infrastructure constraint added"

        constraint_fueling_infrastructure_expansion_shift(model, data_structures)
        @info "  Fueling infrastructure expansion shift constraint added"

        constraint_soc_track(model, data_structures)
        @info "  SOC tracking constraints added"

        constraint_soc_max(model, data_structures)
        @info "  SOC max constraints added"

        constraint_travel_time_track(model, data_structures)
        @info "  Travel time tracking constraint added"

        # Mode shift constraints (included if mode share constraints exist)
        constraint_mode_shift(model, data_structures)
        @info "  Mode shift constraint added"

        if !isempty(data_structures["max_mode_share_list"])
            constraint_max_mode_share(model, data_structures)
            @info "  Max mode share constraint added"
        end

        constraint_demand_coverage(model, data_structures)
        @info "  Demand coverage constraint added"

        constraint_vehicle_sizing(model, data_structures)
        @info "  Vehicle sizing constraint added"

        constraint_vehicle_aging(model, data_structures)
        @info "  Vehicle aging constraint added"

        constraint_vehicle_stock_shift(model, data_structures)
        @info "  Vehicle stock shift constraint added"

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
        @info "  No BEV purchases in 2020 constraint added"

        t_constraints = time() - t_constraints_start

        # ================================================================
        # Step 6: Add objective function
        # ================================================================
        @info "Step 4.5/5: Adding objective..."
        t_start = time()
        objective(model, data_structures, true)
        t_obj = time() - t_start
        @info "Objective added in $(round(t_obj, digits=2)) seconds"

        GC.gc()

        # ================================================================
        # Step 7: Solve
        # ================================================================
        @info "Step 5/5: Solving optimization problem..."
        t_start = time()
        optimize!(model)
        t_optimize = time() - t_start
        @info "Optimization complete in $(round(t_optimize, digits=2)) seconds"

        # ================================================================
        # Step 8: Save results
        # ================================================================
        @info "Saving results..."
        results_file_path = normpath(joinpath(script_dir, "results", folder))
        if !isdir(results_file_path)
            mkpath(results_file_path)
        end

        # Save all key variables
        for var_name in ["f", "h", "h_plus", "h_exist", "h_minus", "s", "soc",
                         "travel_time", "extra_break_time",
                         "q_fuel_infr_plus", "q_fuel_infr_plus_by_route"]
            if haskey(model.obj_dict, Symbol(var_name))
                var_results = Dict{String, Float64}()
                var_ref = model[Symbol(var_name)]
                for idx in eachindex(var_ref)
                    val = value(var_ref[idx])
                    if !isnan(val) && abs(val) > 1e-6
                        var_results[string(idx)] = val
                    end
                end
                YAML.write_file(joinpath(results_file_path, "$(case_name)_$(var_name)_dict.yaml"), var_results)
                @info "  Saved $(length(var_results)) $(var_name) values"
            end
        end

        # Fleet statistics
        modeled_years = data_structures["modeled_years"]
        tv_list = data_structures["techvehicle_list"]
        h_dict = model[:h]
        fleet_by_tech_year = Dict(0 => Dict{Int,Float64}(), 1 => Dict{Int,Float64}())
        for idx in eachindex(h_dict)
            var = h_dict[idx]
            val = value(var)
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

        @info "Fleet development:"
        for year in [2020, 2032, 2040, 2048, 2060]
            if year in modeled_years
                icev = get(fleet_by_tech_year[0], year, 0.0)
                bev = get(fleet_by_tech_year[1], year, 0.0)
                total = icev + bev
                bev_pct = total > 0 ? round(bev / total * 100, digits=1) : 0.0
                @info "  $year: ICEV=$(round(Int, icev)), BEV=$(round(Int, bev)), BEV%=$bev_pct%"
            end
        end

        # Save summary
        summary_stats = Dict(
            "case" => folder,
            "label" => get(case_labels, folder, folder),
            "objective_value" => objective_value(model),
            "termination_status" => string(termination_status(model)),
            "fleet_by_year" => Dict(
                year => Dict(
                    "ICEV" => get(fleet_by_tech_year[0], year, 0.0),
                    "BEV" => get(fleet_by_tech_year[1], year, 0.0)
                ) for year in modeled_years
            )
        )
        YAML.write_file(joinpath(results_file_path, "summary_stats.yaml"), summary_stats)

        case_elapsed = time() - case_start_time
        batch_results[folder] = Dict(
            "status" => "SUCCESS",
            "total_time" => case_elapsed,
            "objective_value" => objective_value(model),
            "termination_status" => termination_status(model),
            "bev_share_2040" => let
                icev = get(fleet_by_tech_year[0], 2040, 0.0)
                bev = get(fleet_by_tech_year[1], 2040, 0.0)
                total = icev + bev
                total > 0 ? round(bev / total * 100, digits=1) : 0.0
            end
        )

        @info "CASE COMPLETE: $folder ($(round(case_elapsed/60, digits=2)) min)"

    catch e
        case_elapsed = time() - case_start_time
        @error "ERROR processing case: $folder"
        @error "Exception: $e"
        @error sprint(showerror, e, catch_backtrace())
        batch_results[folder] = Dict("status" => "FAILED", "total_time" => case_elapsed, "error" => string(e))
    end

    GC.gc()
end

# ============================================================================
# BATCH SUMMARY
# ============================================================================

batch_elapsed = time() - batch_start_time

@info "\n" * "="^80
@info "EEM ZONE SPLITTING ANALYSIS COMPLETE"
@info "="^80
@info "Total batch time: $(round(batch_elapsed/60, digits=2)) min ($(round(batch_elapsed/3600, digits=2)) h)"
@info ""
@info "Results:"
@info "-"^80
for (idx, folder) in enumerate(case_folders)
    result = get(batch_results, folder, Dict("status" => "UNKNOWN"))
    status = result["status"]
    label = get(case_labels, folder, folder)
    if status == "SUCCESS"
        obj = get(result, "objective_value", 0.0)
        bev = get(result, "bev_share_2040", 0.0)
        @info "  $(idx). $label"
        @info "     Obj: $(round(obj/1e9, digits=2))B EUR | BEV 2040: $(bev)%"
    else
        @info "  $(idx). $label -- $status"
    end
end
@info "="^80
