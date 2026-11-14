"""
SM_batch_baseline_diagnostic.jl

Runs the κᵖʷʳ = 0.5, κˢᵖᵃᶜᵉ = 0.0005 baseline THREE times to diagnose
whether the 887 vs 953 discrepancy at ITH1 comes from:

  (a) Solver non-determinism: run-a vs run-b (same script, twice)
  (b) Constraint ordering:     run-a vs run-c (same params, reversed constraint order)

All three runs save to results/baseline_canonical/.

Configuration mirrors SM_batch_kappa_sensitivity.jl exactly (same scenario,
same constraints, same solver settings, same kappa values).
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
kappa_infra  = 0.5
kappa_space  = 0.0005

# Three runs: (label, constraints reversed?)
runs = [
    ("run_a_clean",     false),
    ("run_b_clean",     false),
    ("run_c_reordered", true),
]

relevant_vars = ["f", "h", "h_plus", "h_exist", "h_minus", "s", "q_fuel_infr_plus",
                 "soc", "travel_time", "extra_break_time"]

# ============================================================================
# MAIN LOOP
# ============================================================================
@info "="^80
@info "BASELINE DIAGNOSTIC: 3 runs of κᵖʷʳ=$kappa_infra, κˢᵖᵃᶜᵉ=$kappa_space"
@info "="^80

batch_start = time()

for (run_label, reverse_constraints) in runs
    @info "\n" * "="^80
    @info "$run_label  (reverse_constraints=$reverse_constraints)"
    @info "="^80
    case_start = time()

    try
        script_dir = @__DIR__
        input_path = joinpath(script_dir, "input_data", input_folder)
        timestamp  = Dates.format(now(), "yyyy-mm-dd_HH-MM-SS")
        case_name  = "$(run_label)_$timestamp"

        @info "Loading input..."
        data_dict = get_input_data(input_path)
        data_structures = parse_data(data_dict)

        @info "Creating model..."
        model, data_structures = create_model(data_structures, case_name, include_vars=relevant_vars)
        @info "Variables: $(num_variables(model))"

        # Solver (identical to both existing batches)
        set_optimizer_attribute(model, "Method",         2)
        set_optimizer_attribute(model, "NumericFocus",   3)
        set_optimizer_attribute(model, "ScaleFlag",      2)
        set_optimizer_attribute(model, "FeasibilityTol", 1e-5)
        set_optimizer_attribute(model, "OptimalityTol",  1e-5)
        set_optimizer_attribute(model, "Crossover",      0)
        set_optimizer_attribute(model, "BarConvTol",     1e-8)
        set_optimizer_attribute(model, "Threads",        32)

        # Constraints (in order or reversed)
        constraint_list = [
            (constraint_mandatory_breaks,        "mandatory_breaks"),
            (constraint_fueling_demand,          "fueling_demand"),
            (constraint_fueling_infrastructure,  "fueling_infrastructure"),
            (constraint_soc_track,               "soc_track"),
            (constraint_soc_max,                 "soc_max"),
            (constraint_travel_time_track,       "travel_time_track"),
            (constraint_demand_coverage,         "demand_coverage"),
            (constraint_vehicle_sizing,          "vehicle_sizing"),
            (constraint_vehicle_aging,           "vehicle_aging"),
            (constraint_vehicle_stock_shift,     "vehicle_stock_shift"),
        ]
        if reverse_constraints
            constraint_list = reverse(constraint_list)
        end
        for (fn, name) in constraint_list
            @info "  Adding constraint: $name"
            fn(model, data_structures)
        end

        # No initial-period BEV (matches main batches)
        techvehicles = data_structures["techvehicle_list"]
        bev_tvs     = [tv for tv in techvehicles if tv.technology.id == 1]
        odpairs     = data_structures["odpair_list"]
        y_init      = data_structures["y_init"]
        g_init      = data_structures["g_init"]
        time_step   = data_structures["time_step"]
        for tv in bev_tvs, r in odpairs, g in g_init:time_step:y_init
            @constraint(model, model[:h_plus][y_init, r.id, tv.id, g] == 0)
        end

        # ──────────────── KAPPA + SPACE CONSTRAINTS ────────────────
        mandatory_breaks = data_structures["mandatory_break_list"]
        _geo_list   = data_structures["geographic_element_list"]
        _payload    = techvehicles[1].W[1]

        breaks_by_path = Dict{Int, Vector{Int}}()
        for mb in mandatory_breaks
            push!(get!(breaks_by_path, mb.path.id, Int[]), mb.latest_geo.id)
        end

        B_e = Dict{Int, Float64}(geo.id => 0.0 for geo in _geo_list)
        for r in odpairs
            F_base      = r.F[1]
            truck_trips = F_base / _payload
            for k in r.paths
                for gid in get(breaks_by_path, k.id, Int[])
                    B_e[gid] += truck_trips
                end
            end
        end

        inv_years = collect(y_init:data_structures["investment_period"]:data_structures["Y_end"])
        f_l_pairs = haskey(data_structures, "f_l_not_by_route") ? data_structures["f_l_not_by_route"] : data_structures["f_l_pairs"]
        _elec_fl  = [fl for fl in f_l_pairs if fl[1] == 0]

        # Per-charger power for kappa_space
        _charger_power = Dict{Int, Float64}()
        for fit in data_structures["fueling_infr_types_list"]
            _charger_power[fit.id] = fit.fueling_power[1]
        end

        # kappa_infra: q_plus ≤ kappa_infra * B_e
        for geo in _geo_list
            cap_kw = kappa_infra * B_e[geo.id]
            if cap_kw > 0
                for y in inv_years
                    @constraint(model,
                        sum(model[:q_fuel_infr_plus][y, fl, geo.id] for fl in _elec_fl) <= cap_kw)
                end
            end
        end

        # kappa_space: Σ q_plus[fl] / P_charger[fl] ≤ kappa_space * B_e
        for geo in _geo_list
            max_cp = kappa_space * B_e[geo.id]
            if max_cp > 0
                for y in inv_years
                    expr = AffExpr(0.0)
                    for fl in _elec_fl
                        add_to_expression!(expr, 1.0 / _charger_power[fl[2]], model[:q_fuel_infr_plus][y, fl, geo.id])
                    end
                    @constraint(model, expr <= max_cp)
                end
            end
        end

        @info "Optimizing..."
        optimize!(model)

        status = termination_status(model)
        obj    = objective_value(model)
        @info "Status: $status, Objective: $(round(obj/1e9, digits=4)) bn EUR"

        # Save results
        results_path = joinpath(script_dir, "results", "baseline_canonical", run_label)
        mkpath(results_path)

        # q_fuel_infr_plus
        q_results = Dict{String, Float64}()
        modeled_years = inv_years
        for y in modeled_years, fl in _elec_fl, gid in [geo.id for geo in _geo_list]
            val = value(model[:q_fuel_infr_plus][y, fl, gid])
            if !isnan(val) && abs(val) > 1e-6
                q_results["CartesianIndex($(findfirst(==(y), modeled_years)), $(fl[2]), $(gid+1))"] = val
            end
        end
        YAML.write_file(joinpath(results_path, "$(case_name)_q_fuel_infr_plus_dict.yaml"), q_results)

        # Summary
        summary = Dict(
            "label"           => run_label,
            "reverse_constraints" => reverse_constraints,
            "kappa_infra"     => kappa_infra,
            "kappa_space"     => kappa_space,
            "objective_value" => obj,
            "termination_status" => string(status),
            "solve_time"      => time() - case_start,
            "case_name"       => case_name,
        )
        YAML.write_file(joinpath(results_path, "summary_stats.yaml"), summary)
        @info "Saved to $results_path"

    catch e
        @error "FAILED: $e"
        showerror(stdout, e, catch_backtrace())
    end

    @info "Run time: $(round((time()-case_start)/60, digits=1)) min"
end

@info "\nTotal batch time: $(round((time()-batch_start)/60, digits=1)) min"
