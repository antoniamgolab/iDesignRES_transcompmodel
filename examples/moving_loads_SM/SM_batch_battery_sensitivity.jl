"""
SM_batch_battery_sensitivity.jl - Battery capacity sensitivity analysis

Runs scenario_000 (Go RES) with the BEV tank_capacity (and peak_fueling) array
scaled +/- 30% around the current baseline (560 / 1120 / 1400 kWh at 2020 / 2035 / 2050).

Pre-requisite: Run create_battery_sensitivity_v2.py first to generate input data.

Scenarios:
  - bat_low_70pct:   x0.70 (392 / 784  / 980  kWh at 2020 / 2035 / 2050)
  - bat_baseline:    x1.00 (560 / 1120 / 1400 kWh at 2020 / 2035 / 2050)
  - bat_high_130pct: x1.30 (728 / 1456 / 1820 kWh at 2020 / 2035 / 2050)
"""

using Pkg
Pkg.activate(joinpath(@__DIR__, "../.."))  # Activate the project environment

using YAML, JuMP, Gurobi, Printf, ProgressMeter, Dates

include(joinpath(@__DIR__, "../../src/TransComp.jl"))
using .TransComp

# ============================================================================
# CONFIGURATION
# ============================================================================

case_folders = [
    "battery_sensitivity/bat_low_70pct",
    "battery_sensitivity/bat_baseline",
    "battery_sensitivity/bat_high_130pct",
]

case_labels = Dict(
    "battery_sensitivity/bat_low_70pct"   => "Low -30% (392/784/980 kWh at 2020/2035/2050)",
    "battery_sensitivity/bat_baseline"    => "Baseline (560/1120/1400 kWh at 2020/2035/2050)",
    "battery_sensitivity/bat_high_130pct" => "High +30% (728/1456/1820 kWh at 2020/2035/2050)",
)

relevant_vars = ["f", "h", "h_plus", "h_exist", "h_minus", "s", "q_fuel_infr_plus", "q_fuel_infr_plus_by_route", "soc", "travel_time", "extra_break_time"]

# ============================================================================
# BATCH PROCESSING LOOP
# ============================================================================

@info "="^80
@info "BATTERY CAPACITY SENSITIVITY ANALYSIS: $(length(case_folders)) scenarios"
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
            batch_results[folder] = Dict("status" => "SKIPPED", "reason" => "Folder not found")
            continue
        end

        @info "Input path: $input_path"

        # Generate output case name with timestamp
        scenario_name_for_case = split(folder, ['/', '\\'])[end]
        timestamp = Dates.format(now(), "yyyy-mm-dd_HH-MM-SS")
        case_name = "$(scenario_name_for_case)_cs_$timestamp"

        # ================================================================
        # Step 2: Read and parse input data
        # ================================================================
        @info "Step 1/5: Reading input data..."
        t_start = time()
        data_dict = get_input_data(input_path)
        t_read = time() - t_start
        @info "✓ Input data loaded in $(round(t_read, digits=2)) seconds"

        @info "Step 2/5: Parsing data structures..."
        t_start = time()
        data_structures = parse_data(data_dict)
        t_parse = time() - t_start
        @info "✓ Data parsed in $(round(t_parse, digits=2)) seconds"

        # Log battery capacity for verification
        tv_list_check = data_structures["techvehicle_list"]
        for tv in tv_list_check
            if tv.technology.id == 1  # BEV
                caps = tv.tank_capacity
                @info "  BEV tank_capacity: gen1=$(round(caps[1], digits=0)) kWh, gen13(~2020)=$(round(caps[13], digits=0)) kWh, gen28(~2035)=$(round(caps[28], digits=0)) kWh, gen53(2060)=$(round(caps[end], digits=0)) kWh"
            end
        end

        # ================================================================
        # Step 3: Create optimization model
        # ================================================================
        @info "Step 3/5: Creating optimization model..."
        @info "Memory before model creation: $(round(Sys.free_memory()/1024^3, digits=2)) GB free"
        t_start = time()
        model, data_structures = create_model(data_structures, case_name, include_vars=relevant_vars)
        t_create = time() - t_start
        @info "✓ Model created in $(round(t_create, digits=2)) seconds"
        @info "Number of variables: $(num_variables(model))"

        # ================================================================
        # Step 4: Configure solver
        # ================================================================
        @info "Step 3.5/5: Configuring solver parameters..."
        set_optimizer_attribute(model, "Method", 2)           # Barrier method
        set_optimizer_attribute(model, "NumericFocus", 3)
        set_optimizer_attribute(model, "ScaleFlag", 2)
        set_optimizer_attribute(model, "FeasibilityTol", 1e-5)
        set_optimizer_attribute(model, "OptimalityTol", 1e-5)
        set_optimizer_attribute(model, "Crossover", 0)          # Suppress crossover
        set_optimizer_attribute(model, "BarConvTol", 1e-8)
        @info "✓ Solver configured"

        # ================================================================
        # Step 5: Add constraints
        # ================================================================
        @info "Step 4/5: Adding constraints..."
        t_constraints_start = time()

        constraint_mandatory_breaks(model, data_structures)
        @info "✓ Mandatory breaks"

        constraint_fueling_demand(model, data_structures)
        @info "✓ Fueling demand"

        constraint_fueling_infrastructure(model, data_structures)
        @info "✓ Fueling infrastructure"

        constraint_fueling_infrastructure_expansion_shift(model, data_structures)
        @info "✓ Fueling infrastructure expansion"

        constraint_soc_track(model, data_structures)
        @info "✓ SOC tracking"

        constraint_soc_max(model, data_structures)
        @info "✓ SOC max"

        constraint_travel_time_track(model, data_structures)
        @info "✓ Travel time tracking"

        constraint_mode_shift(model, data_structures)
        @info "✓ Mode shift"

        if !isempty(data_structures["max_mode_share_list"])
            constraint_max_mode_share(model, data_structures)
            @info "✓ Max mode share"
        end

        constraint_demand_coverage(model, data_structures)
        @info "✓ Demand coverage"

        constraint_vehicle_sizing(model, data_structures)
        @info "✓ Vehicle sizing"

        constraint_vehicle_aging(model, data_structures)
        @info "✓ Vehicle aging"

        constraint_vehicle_stock_shift(model, data_structures)
        @info "✓ Vehicle stock shift"

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
        @info "✓ No BEV in 2020"

        # ================================================================
        # KAPPA power cap + KAPPA space cap + CCS overnight-only
        # (matches SM_batch.jl exactly)
        # ================================================================
        kappa_infra = 0.5
        kappa_space = 0.0005

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
        B_e = Dict{Int, Float64}(geo.id => 0.0 for geo in _geo_list)
        for r in odpairs
            F_base = r.F[1]
            truck_trips = F_base / _payload
            for k in r.paths
                for gid in get(breaks_by_path, k.id, Int[])
                    B_e[gid] += truck_trips
                end
            end
        end
        inv_years = collect(y_init:data_structures["investment_period"]:data_structures["Y_end"])
        f_l_pairs = haskey(data_structures, "f_l_not_by_route") ? data_structures["f_l_not_by_route"] : data_structures["f_l_pairs"]
        _elec_fl = [f_l for f_l in f_l_pairs if f_l[1] == 0]

        # Power cap
        for geo in _geo_list
            cap_kw = kappa_infra * B_e[geo.id]
            if cap_kw > 0
                for y in inv_years
                    @constraint(model,
                        sum(model[:q_fuel_infr_plus][y, fl, geo.id] for fl in _elec_fl) <= cap_kw)
                end
            end
        end
        @info "✓ Kappa power cap (kappa_infra=$kappa_infra)"

        # Space cap
        _charger_power = Dict{Int, Float64}()
        for fit in data_structures["fueling_infr_types_list"]
            _charger_power[fit.id] = fit.fueling_power[1]
        end
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
        @info "✓ Kappa space cap (kappa_space=$kappa_space)"

        # CCS overnight-only
        _ccs_fl = nothing
        for fl in _elec_fl
            if fl[2] == 1
                _ccs_fl = fl
                break
            end
        end
        _mb_raw = data_dict["MandatoryBreaks"]
        rest_stops_ccs = Set{Tuple{Int,Int}}()
        for mb in _mb_raw
            if mb["break_duration"] >= 8.0
                push!(rest_stops_ccs, (mb["path_id"], mb["latest_geo_id"]))
            end
        end
        if _ccs_fl !== nothing
            _prkg = data_structures["p_r_k_g_pairs"]
            _my = data_structures["modeled_years"]
            n_ccs_blocked = 0
            for y in _my
                for prkg in _prkg
                    if !((prkg[3], prkg[4]) in rest_stops_ccs)
                        for tv in techvehicles
                            if tv.technology.fuel.id == _ccs_fl[1]
                                for g in g_init:time_step:y
                                    @constraint(model, model[:s][y, prkg, tv.id, _ccs_fl, g] == 0)
                                    n_ccs_blocked += 1
                                end
                            end
                        end
                    end
                end
            end
            @info "✓ CCS overnight-only ($n_ccs_blocked constraints)"
        end

        t_constraints = time() - t_constraints_start

        # ================================================================
        # Step 6: Objective function
        # ================================================================
        @info "Step 4.5/5: Adding objective..."
        t_start = time()
        objective(model, data_structures, true)
        t_obj = time() - t_start
        @info "✓ Objective added in $(round(t_obj, digits=2)) seconds"

        GC.gc()

        # ================================================================
        # Step 7: Solve
        # ================================================================
        @info "Step 5/5: Solving optimization problem..."
        t_start = time()
        optimize!(model)
        t_optimize = time() - t_start
        @info "✓ Optimization complete in $(round(t_optimize, digits=2)) seconds"

        # ================================================================
        # Step 8: Save results
        # ================================================================
        results_file_path = normpath(joinpath(script_dir, "results", "battery_sensitivity", scenario_name_for_case))
        if !isdir(results_file_path)
            mkpath(results_file_path)
        end

        @info "Saving results to: $results_file_path"

        modeled_years_save = data_structures["modeled_years"]
        modeled_generations_save = data_structures["modeled_generations"]

        # Save h (vehicle stock)
        h_results = Dict{String, Float64}()
        if haskey(model.obj_dict, :h)
            for idx in eachindex(model[:h])
                val = value(model[:h][idx])
                if !isnan(val) && abs(val) > 1e-6
                    h_results[string(idx)] = val
                end
            end
            YAML.write_file(joinpath(results_file_path, "$(case_name)_h_dict.yaml"), h_results)
            @info "  ✓ Saved $(length(h_results)) h values"
        end

        # Save f (flow)
        f_results = Dict{String, Float64}()
        if haskey(model.obj_dict, :f)
            for idx in eachindex(model[:f])
                val = value(model[:f][idx])
                if !isnan(val) && abs(val) > 1e-6
                    f_results[string(idx)] = val
                end
            end
            YAML.write_file(joinpath(results_file_path, "$(case_name)_f_dict.yaml"), f_results)
            @info "  ✓ Saved $(length(f_results)) f values"
        end

        # Save q_fuel_infr_plus (infrastructure)
        q_infr_results = Dict{String, Float64}()
        if haskey(model.obj_dict, :q_fuel_infr_plus)
            for idx in eachindex(model[:q_fuel_infr_plus])
                val = value(model[:q_fuel_infr_plus][idx])
                if !isnan(val) && abs(val) > 1e-6
                    q_infr_results[string(idx)] = val
                end
            end
            YAML.write_file(joinpath(results_file_path, "$(case_name)_q_fuel_infr_plus_dict.yaml"), q_infr_results)
            @info "  ✓ Saved $(length(q_infr_results)) q_fuel_infr_plus values"
        end

        # Save s (energy)
        s_results = Dict{String, Float64}()
        if haskey(model.obj_dict, :s)
            p_r_k_g_pairs = data_structures["p_r_k_g_pairs"]
            techvehicle_ids = data_structures["techvehicle_ids"]
            f_l_pairs = haskey(data_structures, "f_l_pairs") ? data_structures["f_l_pairs"] : nothing
            if f_l_pairs !== nothing
                for y in modeled_years_save, prkg in p_r_k_g_pairs, tv_id in techvehicle_ids, fl in f_l_pairs, g in modeled_generations_save
                    val = value(model[:s][y, prkg, tv_id, fl, g])
                    if !isnan(val) && abs(val) > 1e-6
                        s_results[string((y, prkg, tv_id, fl, g))] = val
                    end
                end
            else
                for y in modeled_years_save, prkg in p_r_k_g_pairs, tv_id in techvehicle_ids, g in modeled_generations_save
                    val = value(model[:s][y, prkg, tv_id, g])
                    if !isnan(val) && abs(val) > 1e-6
                        s_results[string((y, prkg, tv_id, g))] = val
                    end
                end
            end
            YAML.write_file(joinpath(results_file_path, "$(case_name)_s_dict.yaml"), s_results)
            @info "  ✓ Saved $(length(s_results)) s values"
        end

        # Save soc
        soc_results = Dict{String, Float64}()
        if haskey(model.obj_dict, :soc)
            p_r_k_g_pairs_soc = data_structures["p_r_k_g_pairs"]
            tv_ids_soc = data_structures["techvehicle_ids"]
            for y in modeled_years_save, prkg in p_r_k_g_pairs_soc, tv in tv_ids_soc, g in modeled_generations_save
                if g <= y
                    val = value(model[:soc][y, prkg, tv, g])
                    if !isnan(val) && abs(val) > 1e-6
                        soc_results[string((y, prkg, tv, g))] = val
                    end
                end
            end
            YAML.write_file(joinpath(results_file_path, "$(case_name)_soc_dict.yaml"), soc_results)
            @info "  ✓ Saved $(length(soc_results)) soc values"
        end

        # ================================================================
        # Extract key statistics
        # ================================================================
        tv_list = data_structures["techvehicle_list"]
        modeled_years = data_structures["modeled_years"]

        # Fleet by technology
        h_dict = model[:h]
        fleet_by_tech_year = Dict(0 => Dict{Int,Float64}(), 1 => Dict{Int,Float64}())
        for idx in eachindex(h_dict)
            val = value(h_dict[idx])
            if val > 1e-6
                year = idx[1]
                tv_id = idx[3]
                tv_idx = findfirst(tv -> tv.id == tv_id, tv_list)
                if tv_idx !== nothing
                    tech = tv_list[tv_idx].technology.id
                    fleet_by_tech_year[tech][year] = get(fleet_by_tech_year[tech], year, 0.0) + val
                end
            end
        end

        # Tonnes by technology
        tonnes_by_tech_year = Dict(0 => Dict{Int,Float64}(), 1 => Dict{Int,Float64}())
        f_dict = model[:f]
        for idx in eachindex(f_dict)
            val = value(f_dict[idx])
            if val > 1e-6
                year = idx[1]
                m_tv = idx[3]
                tv_id = m_tv[2]
                tv_idx = findfirst(tv -> tv.id == tv_id, tv_list)
                if tv_idx !== nothing
                    tech = tv_list[tv_idx].technology.id
                    tonnes_by_tech_year[tech][year] = get(tonnes_by_tech_year[tech], year, 0.0) + val * 1000
                end
            end
        end

        # Energy by year
        energy_by_year = Dict{Int,Float64}()
        s_var = model[:s]
        for idx in eachindex(s_var)
            val = value(s_var[idx])
            if val > 1e-6
                year = idx[1]
                energy_by_year[year] = get(energy_by_year, year, 0.0) + val
            end
        end

        # Infrastructure by year
        infra_by_year = Dict{Int,Float64}()
        if haskey(model.obj_dict, :q_fuel_infr_plus)
            q_var = model[:q_fuel_infr_plus]
            for idx in eachindex(q_var)
                val = value(q_var[idx])
                if val > 1e-6
                    year_idx = idx[1]
                    fl = idx[2]
                    # Only electric (fl mapping where fuel=0)
                    if fl == (0, 1) || fl == (0, 2)
                        year = modeled_years[findfirst(==(year_idx), 1:length(modeled_years))]
                        infra_by_year[year] = get(infra_by_year, year, 0.0) + val
                    end
                end
            end
        end

        # Display summary
        println("\n" * "="^80)
        println("RESULTS SUMMARY: $(case_labels[folder])")
        println("="^80)
        @info "Fleet development (vehicles):"
        for year in [2020, 2028, 2032, 2040, 2048, 2056, 2060]
            if year in modeled_years
                icev = get(fleet_by_tech_year[0], year, 0.0)
                bev = get(fleet_by_tech_year[1], year, 0.0)
                total = icev + bev
                bev_pct = total > 0 ? round(bev / total * 100, digits=1) : 0.0
                @info "  $year: ICEV=$(round(Int, icev)), BEV=$(round(Int, bev)), BEV%=$bev_pct%"
            end
        end

        @info "Energy charged (GWh):"
        for year in [2028, 2032, 2040, 2048, 2056, 2060]
            if year in modeled_years
                energy = get(energy_by_year, year, 0.0)
                @info "  $year: $(round(energy/1e6, digits=2)) GWh"
            end
        end

        # Save summary statistics
        summary_stats = Dict(
            "case" => folder,
            "label" => case_labels[folder],
            "objective_value" => objective_value(model),
            "termination_status" => string(termination_status(model)),
            "fleet_by_year" => Dict(
                year => Dict("ICEV" => get(fleet_by_tech_year[0], year, 0.0),
                            "BEV" => get(fleet_by_tech_year[1], year, 0.0))
                for year in modeled_years
            ),
            "tonnes_by_year" => Dict(
                year => Dict("ICEV" => get(tonnes_by_tech_year[0], year, 0.0),
                            "BEV" => get(tonnes_by_tech_year[1], year, 0.0))
                for year in modeled_years
            ),
            "energy_by_year" => energy_by_year,
        )
        YAML.write_file(joinpath(results_file_path, "summary_stats.yaml"), summary_stats)
        @info "✓ Summary statistics saved"

        # Store for batch summary
        case_elapsed = time() - case_start_time
        batch_results[folder] = Dict(
            "status" => "SUCCESS",
            "total_time" => case_elapsed,
            "objective_value" => objective_value(model),
            "termination_status" => termination_status(model),
            "bev_share_2032" => let
                i = get(fleet_by_tech_year[0], 2032, 0.0); b = get(fleet_by_tech_year[1], 2032, 0.0)
                t = i + b; t > 0 ? round(b/t*100, digits=1) : 0.0
            end,
            "bev_share_2040" => let
                i = get(fleet_by_tech_year[0], 2040, 0.0); b = get(fleet_by_tech_year[1], 2040, 0.0)
                t = i + b; t > 0 ? round(b/t*100, digits=1) : 0.0
            end,
            "bev_share_2048" => let
                i = get(fleet_by_tech_year[0], 2048, 0.0); b = get(fleet_by_tech_year[1], 2048, 0.0)
                t = i + b; t > 0 ? round(b/t*100, digits=1) : 0.0
            end,
            "bev_share_2060" => let
                i = get(fleet_by_tech_year[0], 2060, 0.0); b = get(fleet_by_tech_year[1], 2060, 0.0)
                t = i + b; t > 0 ? round(b/t*100, digits=1) : 0.0
            end,
            "energy_2040" => get(energy_by_year, 2040, 0.0),
        )

        @info "CASE COMPLETE: $folder in $(round(case_elapsed/60, digits=2)) minutes"

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

println("\n" * "="^100)
println("BATTERY CAPACITY SENSITIVITY ANALYSIS — SUMMARY")
println("="^100)
@info "Total batch time: $(round(batch_elapsed/60, digits=2)) minutes ($(round(batch_elapsed/3600, digits=2)) hours)"

println()
@printf("%-4s | %-35s | %8s | %12s | %10s | %10s | %10s | %10s\n",
    "#", "Scenario", "Status", "Obj (B EUR)", "BEV% 2032", "BEV% 2040", "BEV% 2048", "BEV% 2060")
println("-"^110)

for (idx, folder) in enumerate(case_folders)
    result = batch_results[folder]
    status = result["status"]
    scenario_name = split(folder, "/")[end]

    if status == "SUCCESS"
        obj_val = get(result, "objective_value", 0.0)
        bev_32 = get(result, "bev_share_2032", 0.0)
        bev_40 = get(result, "bev_share_2040", 0.0)
        bev_48 = get(result, "bev_share_2048", 0.0)
        bev_60 = get(result, "bev_share_2060", 0.0)
        @printf("%-4d | %-35s | %8s | %12.2f | %9.1f%% | %9.1f%% | %9.1f%% | %9.1f%%\n",
                idx, scenario_name, "✓ OK", obj_val/1e9, bev_32, bev_40, bev_48, bev_60)
    else
        @printf("%-4d | %-35s | %8s | %12s | %10s | %10s | %10s | %10s\n",
                idx, scenario_name, "✗ FAIL", "-", "-", "-", "-", "-")
    end
end
println("="^110)

# Key comparison
println("\nKEY COMPARISON (BEV fleet share %):")
println("-"^80)
baseline_result = get(batch_results, case_folders[1], nothing)
if baseline_result !== nothing && baseline_result["status"] == "SUCCESS"
    baseline_40 = baseline_result["bev_share_2040"]
    baseline_60 = baseline_result["bev_share_2060"]
    for (idx, folder) in enumerate(case_folders)
        result = batch_results[folder]
        if result["status"] == "SUCCESS"
            label = case_labels[folder]
            bev_40 = result["bev_share_2040"]
            bev_60 = result["bev_share_2060"]
            delta_40 = bev_40 - baseline_40
            delta_60 = bev_60 - baseline_60
            if idx == 1
                @printf("  %-40s  2040: %5.1f%%        2060: %5.1f%%\n", label, bev_40, bev_60)
            else
                @printf("  %-40s  2040: %5.1f%% (%+.1f)  2060: %5.1f%% (%+.1f)\n",
                        label, bev_40, delta_40, bev_60, delta_60)
            end
        end
    end
end
