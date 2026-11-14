"""
SM_batch_at33_surcharge.jl - AT33 surcharge sensitivity analysis

Runs 7 scenarios testing the effect of surcharges on AT33 (Tirol):
- 3 electricity price surcharges: +0.01, +0.02, +0.04 EUR/kWh
- 3 network cost surcharges: +2, +5, +10 EUR/kW/yr

Based on Go RES (scenario_000) as baseline.
Uses same constraints as SM_batch.jl (mandatory breaks, NO charging-at-breaks-only).
"""

using Pkg
Pkg.activate(joinpath(@__DIR__, "../.."))

using YAML, JuMP, Gurobi, Printf, Dates

include(joinpath(@__DIR__, "../../src/TransComp.jl"))
using .TransComp

# ============================================================================
# CONFIGURATION
# ============================================================================

surcharge_dir = joinpath(@__DIR__, "input_data", "at_surcharge_targeted")

case_folders = filter(isdir, [joinpath(surcharge_dir, d) for d in readdir(surcharge_dir)])
case_names = [basename(f) for f in case_folders]
sort!(case_names)

@info "Found $(length(case_names)) AT surcharge scenarios: $(case_names)"

relevant_vars = ["f", "h", "h_plus", "h_exist", "h_minus", "s", "q_fuel_infr_plus", "soc", "travel_time", "extra_break_time"]

# ============================================================================
# BATCH PROCESSING
# ============================================================================

@info "="^80
@info "AT33 SURCHARGE BATCH PROCESSING"
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
        case_name = "a3_$(timestamp)"

        @info "Step 3/5: Creating optimization model..."
        t_start = time()
        model, data_structures = create_model(data_structures, case_name, include_vars=relevant_vars)
        t_create = time() - t_start
        @info "Model created in $(round(t_create, digits=2))s"
        @info "Variables: $(num_variables(model))"

        # Step 4: Solver config (same as SM_batch.jl)
        set_optimizer_attribute(model, "Method", 2)           # Barrier
        set_optimizer_attribute(model, "NumericFocus", 3)
        set_optimizer_attribute(model, "ScaleFlag", 2)
        set_optimizer_attribute(model, "FeasibilityTol", 1e-5)
        set_optimizer_attribute(model, "OptimalityTol", 1e-5)
        set_optimizer_attribute(model, "Crossover", 0)        # No crossover
        set_optimizer_attribute(model, "BarConvTol", 1e-8)

        # Step 5: Add constraints (matching SM_batch.jl)
        @info "Step 4/5: Adding constraints..."
        t_constraints_start = time()

        constraint_mandatory_breaks(model, data_structures)
        constraint_fueling_demand(model, data_structures)
        constraint_fueling_infrastructure(model, data_structures)

        # κ constraint (kW deployment pace)
        kappa_infra = 0.5
        mandatory_breaks = data_structures["mandatory_break_list"]
        _geo_list = data_structures["geographic_element_list"]
        _payload = data_structures["techvehicle_list"][1].W[1]

        breaks_by_path_k = Dict{Int, Vector{Int}}()
        for mb in mandatory_breaks
            if !haskey(breaks_by_path_k, mb.path_id)
                breaks_by_path_k[mb.path_id] = Int[]
            end
            push!(breaks_by_path_k[mb.path_id], mb.latest_geo_id)
        end

        B_e = Dict{Int, Float64}()
        for geo in _geo_list
            B_e[geo.id] = 0.0
        end
        _odpairs = data_structures["odpair_list"]
        for r in _odpairs
            truck_trips = r.F[1] / _payload
            for k in r.paths
                for geo_id in get(breaks_by_path_k, k.id, Int[])
                    B_e[geo_id] = get(B_e, geo_id, 0.0) + truck_trips
                end
            end
        end

        inv_years = collect(data_structures["y_init"]:data_structures["investment_period"]:data_structures["Y_end"])
        f_l_pairs = haskey(data_structures, "f_l_not_by_route") ? data_structures["f_l_not_by_route"] : data_structures["f_l_pairs"]
        _elec_fl = [f_l for f_l in f_l_pairs if f_l[1] == 0]

        for geo in _geo_list
            cap_kw = kappa_infra * B_e[geo.id]
            if cap_kw > 0
                for y in inv_years
                    @constraint(model,
                        sum(model[:q_fuel_infr_plus][y, f_l, geo.id] for f_l in _elec_fl) <= cap_kw)
                end
            end
        end

        # κ_space constraint (charge points, MCS+CCS, AffExpr)
        kappa_space = 0.0005
        _charger_power = Dict{Int, Float64}()
        for fit in data_structures["fueling_infr_types_list"]
            _charger_power[fit.id] = fit.fueling_power[1]
        end
        for geo in _geo_list
            max_cp = kappa_space * B_e[geo.id]
            if max_cp > 0
                for y in inv_years
                    _space_expr = AffExpr(0.0)
                    for f_l in _elec_fl
                        add_to_expression!(_space_expr, 1.0 / _charger_power[f_l[2]], model[:q_fuel_infr_plus][y, f_l, geo.id])
                    end
                    @constraint(model, _space_expr <= max_cp)
                end
            end
        end

        # CCS overnight-only constraint
        _mb_raw = data_dict["MandatoryBreaks"]
        rest_stops = Set{Tuple{Int,Int}}()
        for mb in _mb_raw
            if mb["break_duration"] >= 8.0
                push!(rest_stops, (mb["path_id"], mb["latest_geo_id"]))
            end
        end
        _ccs_fl = nothing
        for f_l in _elec_fl
            if f_l[2] == 1
                _ccs_fl = f_l
                break
            end
        end
        if _ccs_fl !== nothing
            _p_r_k_g_pairs = data_structures["p_r_k_g_pairs"]
            _modeled_years = data_structures["modeled_years"]
            _g_init = data_structures["g_init"]
            _timestep = data_structures["time_step"]
            techvehicles = data_structures["techvehicle_list"]
            n_ccs_blocked = 0
            for y in _modeled_years
                for prkg in _p_r_k_g_pairs
                    path_id = prkg[3]; geo_id = prkg[4]
                    if !((path_id, geo_id) in rest_stops)
                        for tv in techvehicles
                            if tv.technology.fuel.id == _ccs_fl[1]
                                for g in _g_init:_timestep:y
                                    @constraint(model, model[:s][y, prkg, tv.id, _ccs_fl, g] == 0)
                                    n_ccs_blocked += 1
                                end
                            end
                        end
                    end
                end
            end
            @info "CCS overnight-only: $(n_ccs_blocked) constraints"
        end

        # BEV-specific constraints
        constraint_soc_track(model, data_structures)
        constraint_soc_max(model, data_structures)
        constraint_travel_time_track(model, data_structures)
        constraint_demand_coverage(model, data_structures)
        constraint_vehicle_sizing(model, data_structures)
        constraint_vehicle_aging(model, data_structures)
        constraint_vehicle_stock_shift(model, data_structures)

        # No BEV in 2020
        y_init = data_structures["y_init"]
        g_init = data_structures["g_init"]
        time_step = data_structures["time_step"]
        bev_tvs = [tv for tv in techvehicles if tv.technology.id == 1]
        for tv in bev_tvs, r in _odpairs, g in g_init:time_step:y_init
            @constraint(model, model[:h_plus][y_init, r.id, tv.id, g] == 0)
        end

        t_constraints = time() - t_constraints_start
        @info "Constraints added in $(round(t_constraints, digits=2))s"

        # Objective (with fuel costs)
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
        results_file_path = normpath(joinpath(script_dir, "results", "at33_surcharge", folder_name))
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
@info "AT33 SURCHARGE BATCH COMPLETE"
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
