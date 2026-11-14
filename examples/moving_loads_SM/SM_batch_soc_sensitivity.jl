"""
SM_batch_soc_sensitivity.jl - SOC init/final sensitivity analysis

Runs scenario_000 (Go RES) with different SOC_init / SOC_final combinations.
Uses kappa = 0.5 for all runs.
"""

using Pkg
Pkg.activate(joinpath(@__DIR__, "../.."))

using YAML, JuMP, Gurobi, Printf, Dates

include(joinpath(@__DIR__, "../../src/TransComp.jl"))
using .TransComp

# ============================================================================
# CONFIGURATION
# ============================================================================

input_folder = "uncertainty_scenarios_v2/scenario_000"
kappa_infra = 0.5

# SOC sensitivity runs: (soc_init, soc_final, label)
soc_runs = [
    (0.5, 0.5, "base_50_50"),
    (0.3, 0.5, "low_start_30_50"),
    (0.7, 0.5, "high_start_70_50"),
    (0.5, 0.3, "low_end_50_30"),
    (0.5, 0.7, "high_end_50_70"),
    (0.3, 0.7, "tight_30_70"),
    (0.7, 0.3, "loose_70_30"),
]

relevant_vars = ["f", "h", "h_plus", "h_exist", "h_minus", "s", "q_fuel_infr_plus", "soc", "travel_time", "extra_break_time"]

# ============================================================================
# BATCH LOOP
# ============================================================================

@info "="^80
@info "SOC SENSITIVITY ANALYSIS: $(length(soc_runs)) runs"
@info "="^80

batch_start_time = time()
batch_results = Dict()

for (soc_init, soc_final, soc_label) in soc_runs
    @info "\n" * "="^80
    @info "SOC_init=$(soc_init), SOC_final=$(soc_final) [$soc_label]"
    @info "="^80

    case_start_time = time()

    try
        script_dir = @__DIR__
        input_path = joinpath(script_dir, "input_data", input_folder)

        timestamp = Dates.format(now(), "yyyy-mm-dd_HH-MM-SS")
        case_name = "$(soc_label)_cs_$timestamp"

        # Read and parse
        @info "Loading input data..."
        data_dict = get_input_data(input_path)

        # Override SOC parameters
        data_dict["Model"]["soc_init"] = soc_init
        data_dict["Model"]["soc_final"] = soc_final

        data_structures = parse_data(data_dict)

        # Create model
        @info "Creating model..."
        model, data_structures = create_model(data_structures, case_name, include_vars=relevant_vars)
        @info "Variables: $(num_variables(model))"

        # Solver
        set_optimizer_attribute(model, "Method", 2)
        set_optimizer_attribute(model, "NumericFocus", 3)
        set_optimizer_attribute(model, "ScaleFlag", 2)
        set_optimizer_attribute(model, "FeasibilityTol", 1e-5)
        set_optimizer_attribute(model, "OptimalityTol", 1e-5)
        set_optimizer_attribute(model, "Crossover", 0)
        set_optimizer_attribute(model, "BarConvTol", 1e-8)

        # Constraints
        @info "Adding constraints..."
        constraint_mandatory_breaks(model, data_structures)
        constraint_fueling_demand(model, data_structures)
        constraint_fueling_infrastructure(model, data_structures)
        constraint_soc_track(model, data_structures)
        constraint_soc_max(model, data_structures)
        constraint_travel_time_track(model, data_structures)
        constraint_demand_coverage(model, data_structures)
        constraint_vehicle_sizing(model, data_structures)
        constraint_vehicle_aging(model, data_structures)
        constraint_vehicle_stock_shift(model, data_structures)

        # No BEV in 2020
        y_init = data_structures["y_init"]
        odpairs = data_structures["odpair_list"]
        techvehicles = data_structures["techvehicle_list"]
        g_init = data_structures["g_init"]
        time_step = data_structures["time_step"]
        Y_end = data_structures["Y_end"]
        bev_tvs = [tv for tv in techvehicles if tv.technology.id == 1]
        for tv in bev_tvs, r in odpairs, g in g_init:time_step:y_init
            @constraint(model, model[:h_plus][y_init, r.id, tv.id, g] == 0)
        end

        # Kappa constraint
        mandatory_breaks = data_structures["mandatory_break_list"]
        _geo_list = data_structures["geographic_element_list"]
        _payload = techvehicles[1].W[1]

        breaks_by_path = Dict{Int, Vector{Int}}()
        for mb in mandatory_breaks
            if !haskey(breaks_by_path, mb.path_id)
                breaks_by_path[mb.path_id] = Int[]
            end
            push!(breaks_by_path[mb.path_id], mb.latest_geo_id)
        end

        B_e = Dict{Int, Float64}()
        for geo in _geo_list
            B_e[geo.id] = 0.0
        end
        for r in odpairs
            F_base = r.F[1]
            truck_trips = F_base / _payload
            for k in r.paths
                for geo_id in get(breaks_by_path, k.id, Int[])
                    B_e[geo_id] = get(B_e, geo_id, 0.0) + truck_trips
                end
            end
        end

        inv_years = collect(y_init:data_structures["investment_period"]:Y_end)
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

        # Charge point space constraint (both CCS and MCS)
        kappa_space = 0.0005
        _fueling_infr_types_ks = data_structures["fueling_infr_types_list"]
        _charger_power_ks = Dict{Int, Float64}()
        for fit in _fueling_infr_types_ks
            _charger_power_ks[fit.id] = fit.fueling_power[1]
        end
        for geo in _geo_list
            max_cp = kappa_space * B_e[geo.id]
            if max_cp > 0
                for y in inv_years
                    _space_expr = AffExpr(0.0)
                    for f_l in _elec_fl
                        add_to_expression!(_space_expr, 1.0 / _charger_power_ks[f_l[2]], model[:q_fuel_infr_plus][y, f_l, geo.id])
                    end
                    @constraint(model, _space_expr <= max_cp)
                end
            end
        end

        # ================================================================
        # CCS overnight-only constraint (matches SM_batch.jl):
        # CCS (slow) charging only allowed at nodes that are overnight rest stops.
        # ================================================================
        _ccs_fl = nothing
        for f_l in _elec_fl
            if f_l[2] == 1
                _ccs_fl = f_l
                break
            end
        end
        _mb_raw_ccs = data_dict["MandatoryBreaks"]
        rest_stops_ccs = Set{Tuple{Int,Int}}()
        for mb in _mb_raw_ccs
            if mb["break_duration"] >= 8.0
                push!(rest_stops_ccs, (mb["path_id"], mb["latest_geo_id"]))
            end
        end
        @info "Rest stops: $(length(rest_stops_ccs)) (path, geo) pairs identified as overnight rests"
        if _ccs_fl !== nothing
            _prkg_ccs = data_structures["p_r_k_g_pairs"]
            _my_ccs = data_structures["modeled_years"]
            _gi_ccs = data_structures["g_init"]
            _ts_ccs = data_structures["time_step"]
            n_ccs_blocked = 0
            for y in _my_ccs
                for prkg in _prkg_ccs
                    if !((prkg[3], prkg[4]) in rest_stops_ccs)
                        for tv in techvehicles
                            if tv.technology.fuel.id == _ccs_fl[1]
                                for g in _gi_ccs:_ts_ccs:y
                                    @constraint(model, model[:s][y, prkg, tv.id, _ccs_fl, g] == 0)
                                    n_ccs_blocked += 1
                                end
                            end
                        end
                    end
                end
            end
            @info "CCS overnight-only: $(n_ccs_blocked) constraints blocking CCS at non-rest nodes"
        end

        # Objective
        @info "Adding objective..."
        objective(model, data_structures, true)
        GC.gc()

        # Solve
        @info "Solving..."
        t_solve = time()
        optimize!(model)
        solve_time = time() - t_solve
        @info "Solved in $(round(solve_time, digits=1))s — $(termination_status(model))"

        if termination_status(model) != MOI.OPTIMAL
            @warn "Not optimal: $(termination_status(model))"
            batch_results[soc_label] = Dict("status" => "FAILED", "error" => string(termination_status(model)))
            continue
        end

        # Save results
        results_path = joinpath(script_dir, "results", "soc_sensitivity", soc_label)
        mkpath(results_path)

        # Save s and q_fuel_infr_plus
        s_results = Dict{String, Float64}()
        p_r_k_g_pairs = data_structures["p_r_k_g_pairs"]
        tv_ids = data_structures["techvehicle_ids"]
        modeled_years = data_structures["modeled_years"]
        modeled_generations = data_structures["modeled_generations"]
        f_l_save = haskey(data_structures, "f_l_pairs") ? data_structures["f_l_pairs"] : nothing
        if f_l_save !== nothing
            for y in modeled_years, prkg in p_r_k_g_pairs, tv_id in tv_ids, fl in f_l_save, g in modeled_generations
                val = value(model[:s][y, prkg, tv_id, fl, g])
                if !isnan(val) && abs(val) > 1e-6
                    s_results[string((y, prkg, tv_id, fl, g))] = val
                end
            end
        end
        YAML.write_file(joinpath(results_path, "$(case_name)_s_dict.yaml"), s_results)

        q_results = Dict{String, Float64}()
        for idx in eachindex(model[:q_fuel_infr_plus])
            val = value(model[:q_fuel_infr_plus][idx])
            if !isnan(val) && abs(val) > 1e-6
                q_results[string(idx)] = val
            end
        end
        YAML.write_file(joinpath(results_path, "$(case_name)_q_fuel_infr_plus_dict.yaml"), q_results)

        # Fleet stats
        tv_list = data_structures["techvehicle_list"]
        fleet_by_tech_year = Dict(0 => Dict{Int,Float64}(), 1 => Dict{Int,Float64}())
        for idx in eachindex(model[:h])
            val = value(model[:h][idx])
            if val > 1e-6
                year = idx[1]; tv_id = idx[3]
                tv_idx = findfirst(tv -> tv.id == tv_id, tv_list)
                if tv_idx !== nothing
                    tech = tv_list[tv_idx].technology.id
                    fleet_by_tech_year[tech][year] = get(fleet_by_tech_year[tech], year, 0.0) + val
                end
            end
        end

        tonnes_by_tech_year = Dict(0 => Dict{Int,Float64}(), 1 => Dict{Int,Float64}())
        for idx in eachindex(model[:f])
            val = value(model[:f][idx])
            if val > 1e-6
                year = idx[1]; m_tv = idx[3]; tv_id = m_tv[2]
                tv_idx = findfirst(tv -> tv.id == tv_id, tv_list)
                if tv_idx !== nothing
                    tech = tv_list[tv_idx].technology.id
                    tonnes_by_tech_year[tech][year] = get(tonnes_by_tech_year[tech], year, 0.0) + val * 1000
                end
            end
        end

        summary = Dict(
            "soc_init" => soc_init,
            "soc_final" => soc_final,
            "label" => soc_label,
            "objective_value" => objective_value(model),
            "solve_time" => solve_time,
            "fleet_by_year" => Dict(y => Dict("ICEV" => get(fleet_by_tech_year[0], y, 0.0), "BEV" => get(fleet_by_tech_year[1], y, 0.0)) for y in modeled_years),
            "tonnes_by_year" => Dict(y => Dict("ICEV" => get(tonnes_by_tech_year[0], y, 0.0), "BEV" => get(tonnes_by_tech_year[1], y, 0.0)) for y in modeled_years),
        )
        YAML.write_file(joinpath(results_path, "summary_stats.yaml"), summary)

        obj = objective_value(model)
        bev_2040 = let i=get(fleet_by_tech_year[0],2040,0.0); b=get(fleet_by_tech_year[1],2040,0.0); t=i+b; t>0 ? round(b/t*100,digits=1) : 0.0 end
        bev_2048 = let i=get(fleet_by_tech_year[0],2048,0.0); b=get(fleet_by_tech_year[1],2048,0.0); t=i+b; t>0 ? round(b/t*100,digits=1) : 0.0 end
        @info "Result: obj=$(round(obj/1e9, digits=2)) bn, BEV%2040=$bev_2040%, BEV%2048=$bev_2048%"

        batch_results[soc_label] = Dict(
            "status" => "SUCCESS", "soc_init" => soc_init, "soc_final" => soc_final,
            "objective" => obj, "bev_2040" => bev_2040, "bev_2048" => bev_2048,
            "solve_time" => solve_time
        )

    catch e
        @error "FAILED: $e"
        @error sprint(showerror, e, catch_backtrace())
        batch_results[soc_label] = Dict("status" => "FAILED", "error" => string(e))
    end

    GC.gc()
end

# ============================================================================
# SUMMARY
# ============================================================================
batch_elapsed = time() - batch_start_time

println("\n" * "="^90)
println("SOC SENSITIVITY RESULTS")
println("="^90)
@printf("%-20s | %6s | %6s | %12s | %10s | %10s | %8s\n",
    "Run", "Init", "Final", "Obj (bn EUR)", "BEV% 2040", "BEV% 2048", "Time(s)")
println("-"^80)
for (soc_init, soc_final, label) in soc_runs
    r = get(batch_results, label, Dict("status" => "MISSING"))
    if r["status"] == "SUCCESS"
        @printf("%-20s | %5.0f%% | %5.0f%% | %12.2f | %9.1f%% | %9.1f%% | %7.0f\n",
            label, soc_init*100, soc_final*100,
            r["objective"]/1e9, r["bev_2040"], r["bev_2048"], r["solve_time"])
    else
        @printf("%-20s | %5.0f%% | %5.0f%% | %12s | %10s | %10s | %8s\n",
            label, soc_init*100, soc_final*100, "FAILED", "-", "-", "-")
    end
end
println("="^90)
println("Total time: $(round(batch_elapsed/60, digits=1)) minutes")
println("Results in: results/soc_sensitivity/")
println("="^90)
