"""
SM_batch_surcharge_v3.jl - AT33/ITH1 surcharge runs (Figure 8) on the corrected model (2026-10-13)

Input folder from ENV INPUT_FOLDER (relative to input_data/, built by make_surcharge_v3.py:
old surcharge deltas added to uncertainty_scenarios_v2_night). Results: results/surcharge_v3/<RUN_LABEL>/.

(based on:) 
Identical to SM_batch_night.jl (corrected objective, night/day prices, 30% markup), but
kappa_pwr / kappa_space are read from ENV (KAPPA_PWR, KAPPA_SPACE; "Inf" = no cap) and
results go to results/kappa_sensitivity_v3/<RUN_LABEL>/. Gurobi threads from ENV GRB_THREADS.
Replaces SM_batch_kappa_sensitivity.jl / SM_batch_kspace_sensitivity.jl for the revision.


Same as SM_batch_omfix.jl, but with input uncertainty_scenarios_v2_night: FuelCost uses
price = 1.3*(tax + wholesale*f) [30% markup as in paper, was 1.5] with per-country night (CCS) / day (MCS) factors from
ENTSO-E day-ahead prices 2023-2025 (night 22-06), replacing the old 1.075 (CCS) / 0.97 (MCS).
Results: results/uncertainty_scenarios_v2_night/

(previous header:)

Identical to SM_batch.jl, but run with the corrected src/model_functions.jl: annual charger
O&M and grid fees are charged once per modeled year on the capacity installed up to that
year (previously summed over every year since 2020), and O&M only for the matching fuel.
Results: results/uncertainty_scenarios_v2_omfix/

This script runs multiple case studies sequentially, each with its own input data folder.
Results are saved separately for each case.
"""

using Pkg
Pkg.activate(joinpath(@__DIR__, "../.."))  # Activate the project environment

using YAML, JuMP, Gurobi, Printf, ProgressMeter, Dates

include(joinpath(@__DIR__, "../../src/TransComp.jl"))
using .TransComp

# ============================================================================
# CONFIGURATION: Define the list of cases to run
# ============================================================================

# DEBUG MODE: Set to true for fast debugging (small OD pair set, 1 scenario)
DEBUG_MODE = false
DEBUG_ODPAIRS = 20  # Only used when DEBUG_MODE = true

# Full 4-scenario run with kappa = 0.5
case_folders = [
    get(ENV, "INPUT_FOLDER", "uncertainty_scenarios_v2_night/scenario_000"),
]
RESULTS_SUBDIR = "uncertainty_scenarios_v2"  # folder name already distinct -> results/uncertainty_scenarios_v2_night

case_labels = Dict(
    "uncertainty_scenarios_v2/scenario_000" => "Go RES",
    "uncertainty_scenarios_v2/scenario_001" => "NECPEssentials",
    "uncertainty_scenarios_v2/scenario_002" => "REPowerEU++",
    "uncertainty_scenarios_v2/scenario_003" => "Trinity",
)

# Variables to include in the model (adjust based on your needs)
# Added q_fuel_infr_plus_by_route for infrastructure expansion constraint
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
@info "BATCH PROCESSING: $(length(case_folders)) cases"
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
        # Extract just the scenario name (last part of path) to avoid / in filenames
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

        # DEBUG MODE: Limit OD pairs BEFORE parsing (so all derived structures are consistent)
        if DEBUG_MODE
            original_count = length(data_dict["Odpair"])
            data_dict["Odpair"] = data_dict["Odpair"][1:min(DEBUG_ODPAIRS, original_count)]
            @warn "DEBUG: Reduced OD pairs from $original_count to $(length(data_dict["Odpair"])) BEFORE parsing"
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
        set_optimizer_attribute(model, "Threads", parse(Int, get(ENV, "GRB_THREADS", "0")))
        set_optimizer_attribute(model, "Method", 2)           # Barrier method
        set_optimizer_attribute(model, "NumericFocus", 3)     # Maximum numerical precision
        set_optimizer_attribute(model, "ScaleFlag", 2)        # Aggressive auto-scaling
        set_optimizer_attribute(model, "FeasibilityTol", 1e-5)
        set_optimizer_attribute(model, "OptimalityTol", 1e-5)
        set_optimizer_attribute(model, "Crossover", 0)        # Suppress crossover (LP, no vertex needed)
        set_optimizer_attribute(model, "BarConvTol", 1e-8)    # Tight barrier convergence
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

        # Fueling demand constraint (CRITICAL: links s to f × spec_cons × path_length)
        t_start = time()
        constraint_fueling_demand(model, data_structures)
        t_fueling_demand = time() - t_start
        @info "✓ Fueling demand constraint added in $(round(t_fueling_demand, digits=2))s"

        t_start = time()
        constraint_fueling_infrastructure(model, data_structures)
        t_fueling_infra = time() - t_start
        @info "✓ Fueling infrastructure constraint added in $(round(t_fueling_infra, digits=2))s"

        # ================================================================
        # Infrastructure expansion pace constraint (κ · B_e cap)
        # Eq. 11: q_plus[y,e] ≤ κ · B_e for all investment years and locations
        # B_e = annual truck-breaks at location e (base year)
        # κ = 0.5 kW per (truck-break/yr) per investment period
        # ================================================================
        kappa_infra = parse(Float64, get(ENV, "KAPPA_PWR", "0.5"))

        mandatory_breaks = data_structures["mandatory_break_list"]
        _odpairs_kappa = data_structures["odpair_list"]
        _geo_list_kappa = data_structures["geographic_element_list"]
        _payload_kappa = data_structures["techvehicle_list"][1].W[1]

        breaks_by_path = Dict{Int, Vector{Int}}()
        for mb in mandatory_breaks
            if !haskey(breaks_by_path, mb.path_id)
                breaks_by_path[mb.path_id] = Int[]
            end
            push!(breaks_by_path[mb.path_id], mb.latest_geo_id)
        end

        B_e = Dict{Int, Float64}()
        for geo in _geo_list_kappa
            B_e[geo.id] = 0.0
        end
        for r in _odpairs_kappa
            F_base = r.F[1]
            truck_trips = F_base / _payload_kappa
            for k in r.paths
                break_geos = get(breaks_by_path, k.id, Int[])
                for geo_id in break_geos
                    B_e[geo_id] = get(B_e, geo_id, 0.0) + truck_trips
                end
            end
        end

        _inv_years_kappa = collect(data_structures["y_init"]:data_structures["investment_period"]:data_structures["Y_end"])
        _f_l_pairs_kappa = haskey(data_structures, "f_l_not_by_route") ? data_structures["f_l_not_by_route"] : data_structures["f_l_pairs"]

        # Electric f_l pairs for kappa constraint
        _elec_fl = [f_l for f_l in _f_l_pairs_kappa if f_l[1] == 0]

        # Build charger power lookup (needed by both kappa and kappa_space)
        kappa_space = parse(Float64, get(ENV, "KAPPA_SPACE", "0.0005"))  # charge points per (truck-break/yr) per period
        _fueling_infr_types = data_structures["fueling_infr_types_list"]
        _charger_power = Dict{Int, Float64}()
        for fit in _fueling_infr_types
            _charger_power[fit.id] = fit.fueling_power[1]  # kW per charge point
        end

        # CRITICAL VERIFICATION
        println("\nKAPPA CONSTRAINT SETUP:")
        println("  _f_l_pairs_kappa = $(_f_l_pairs_kappa)")
        println("  _elec_fl = $(_elec_fl)")
        println("  typeof _elec_fl elements: $(isempty(_elec_fl) ? "EMPTY!" : typeof(first(_elec_fl)))")
        println("  _charger_power = $(_charger_power)")
        println("  _inv_years_kappa = $(_inv_years_kappa)")
        println("  kappa_infra = $(kappa_infra), kappa_space = $(kappa_space)")
        if isempty(_elec_fl)
            @error "NO ELECTRIC F_L PAIRS FOUND! kappa_space constraint will be trivially satisfied!"
        end
        # Test variable access
        _test_geo = first(_geo_list_kappa)
        _test_y = first(_inv_years_kappa)
        for f_l in _elec_fl
            _test_var = model[:q_fuel_infr_plus][_test_y, f_l, _test_geo.id]
            println("  Test: q_fuel_infr_plus[$(  _test_y), $(f_l), $(_test_geo.id)] = $(typeof(_test_var))")
        end

        # ================================================================
        # κ constraint: limits total kW per node per period
        # ================================================================
        n_kappa_constraints = 0
        for geo in _geo_list_kappa
            cap_kw = kappa_infra * B_e[geo.id]
            if cap_kw > 0 && isfinite(cap_kw)
                for y in _inv_years_kappa
                    @constraint(model,
                        sum(model[:q_fuel_infr_plus][y, f_l, geo.id] for f_l in _elec_fl) <= cap_kw)
                    n_kappa_constraints += 1
                end
            end
        end

        max_B = maximum(values(B_e))
        @info "Kappa constraint: kappa=$(kappa_infra), $(n_kappa_constraints) constraints, max cap=$(round(kappa_infra * max_B / 1000, digits=1)) MW"

        # ================================================================
        # Charge point space constraint (both CCS and MCS):
        # sum(q_plus[f_l] / P_charger[f_l]) <= kappa_space * B_e
        # Limits total charge points (CCS + MCS) per node per period.
        # Uses explicit AffExpr construction (generator syntax had issues).
        # ================================================================
        n_space_constraints = 0
        _space_con_refs = Dict{Tuple{Int,Int}, JuMP.ConstraintRef}()
        for geo in _geo_list_kappa
            max_cp = kappa_space * B_e[geo.id]
            if max_cp > 0 && isfinite(max_cp)
                for y in _inv_years_kappa
                    _space_expr = AffExpr(0.0)
                    for f_l in _elec_fl
                        add_to_expression!(_space_expr, 1.0 / _charger_power[f_l[2]], model[:q_fuel_infr_plus][y, f_l, geo.id])
                    end
                    con = @constraint(model, _space_expr <= max_cp)
                    _space_con_refs[(y, geo.id)] = con
                    n_space_constraints += 1
                end
            end
        end

        max_cp_any = kappa_space * max_B
        @info "Space constraint: kappa_space=$(kappa_space), $(n_space_constraints) constraints, max charge points=$(round(max_cp_any, digits=0))/period"

        # DEBUG: B_e diagnostics
        println("\n" * "="^60)
        println("DEBUG: B_e AND CONSTRAINT DIAGNOSTICS")
        println("="^60)
        _geo_name_dbg = Dict(geo.id => string(geo.name) for geo in _geo_list_kappa)
        sorted_be_dbg = sort(collect(B_e), by=x->x[2], rev=true)
        println("Top 15 nodes by B_e:")
        for (gid, be) in sorted_be_dbg[1:min(15, length(sorted_be_dbg))]
            cap_kw = kappa_infra * be
            cap_cp = kappa_space * be
            println("  geo=$(gid) ($(_geo_name_dbg[gid])): B_e=$(round(be, digits=0)), kW_cap=$(round(cap_kw/1000, digits=1))MW, cp_cap=$(round(cap_cp, digits=2))/period, max_cp_8periods=$(round(cap_cp*8, digits=0))")
        end
        # Check specific nodes
        for gid in [8, 9]  # DE21, DE22
            be = get(B_e, gid, 0.0)
            println("CHECK geo=$(gid) ($(_geo_name_dbg[gid])): B_e=$(round(be, digits=1)), cap_cp=$(round(kappa_space*be, digits=3))")
        end
        zero_be = length([1 for (_, be) in B_e if be == 0.0])
        nonzero_be = length(B_e) - zero_be
        println("Nodes with B_e=0: $(zero_be)/$(length(B_e)) -- THESE HAVE NO CONSTRAINTS!")
        println("Nodes with B_e>0: $(nonzero_be) -- constraints applied")
        println("_elec_fl = $(_elec_fl)")
        println("_charger_power = $(_charger_power)")
        println("n_kappa_constraints = $(n_kappa_constraints), n_space_constraints = $(n_space_constraints)")
        println("="^60)

        # ================================================================
        # CCS overnight-only constraint:
        # CCS (slow) charging is only allowed at nodes where a route has an overnight rest.
        # At all other nodes, s[..., CCS, ...] = 0 for that route.
        # ================================================================
        _mb_raw = data_dict["MandatoryBreaks"]

        # Build set of (path_id, geo_id) that are REST stops (break_duration >= 8h)
        rest_stops = Set{Tuple{Int,Int}}()
        for mb in _mb_raw
            if mb["break_duration"] >= 8.0  # 9h rest
                push!(rest_stops, (mb["path_id"], mb["latest_geo_id"]))
            end
        end
        @info "Rest stops: $(length(rest_stops)) (path, geo) pairs identified as overnight rests"

        # Find CCS f_l pair
        _ccs_fl = nothing
        for f_l in _elec_fl
            if f_l[2] == 1  # infr_type=1 = slow/CCS
                _ccs_fl = f_l
                break
            end
        end

        if _ccs_fl !== nothing
            _p_r_k_g_pairs = data_structures["p_r_k_g_pairs"]
            _techvehicles = data_structures["techvehicle_list"]
            _modeled_years = data_structures["modeled_years"]
            _modeled_gens = data_structures["modeled_generations"]
            _g_init = data_structures["g_init"]
            _timestep = data_structures["time_step"]

            n_ccs_blocked = 0
            for y in _modeled_years
                for prkg in _p_r_k_g_pairs
                    path_id = prkg[3]
                    geo_id = prkg[4]

                    # If this (path, geo) is NOT a rest stop, block CCS
                    if !((path_id, geo_id) in rest_stops)
                        for tv in _techvehicles
                            if tv.technology.fuel.id == _ccs_fl[1]
                                for g in _g_init:_timestep:y
                                    @constraint(model,
                                        model[:s][y, prkg, tv.id, _ccs_fl, g] == 0)
                                    n_ccs_blocked += 1
                                end
                            end
                        end
                    end
                end
            end
            @info "CCS overnight-only: $(n_ccs_blocked) constraints blocking CCS at non-rest nodes"
        end

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

        # Mode shift constraints — DISABLED for infeasibility testing
        # t_start = time()
        # constraint_mode_shift(model, data_structures)
        # t_mode_shift = time() - t_start
        # @info "✓ Mode shift constraint added in $(round(t_mode_shift, digits=2))s"
        @info "⊘ Mode shift constraint DISABLED (testing)"

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
        # Step 7.5: Basic solution summary + IIS if infeasible
        # ================================================================
        println("\n" * "="^80)
        println("SOLUTION STATUS")
        println("="^80)
        println("  Termination: $(termination_status(model))")

        if termination_status(model) == MOI.INFEASIBLE
            @warn "Model is INFEASIBLE — computing IIS..."
            try
                compute_conflict!(model)
                println("\nIIS (Irreducible Infeasible Subsystem):")
                println("="^80)
                iis_count = 0
                for (F, S) in list_of_constraint_types(model)
                    for con in all_constraints(model, F, S)
                        status = MOI.get(model, MOI.ConstraintConflictStatus(), con)
                        if status == MOI.IN_CONFLICT
                            iis_count += 1
                            if iis_count <= 50
                                println("  CONFLICT [$iis_count]: $con")
                            end
                        end
                    end
                end
                println("  Total conflicting constraints: $iis_count")
                println("="^80)
            catch e
                @warn "IIS computation failed: $e"
            end
            batch_results[folder] = Dict(
                "status" => "FAILED",
                "total_time" => time() - case_start_time,
                "error" => "INFEASIBLE"
            )
            continue  # Skip saving results for infeasible model
        end

        println("  Objective:   $(objective_value(model))")
        println("="^80)

        # ================================================================
        # POST-SOLVE: Verify constraints at key nodes
        # ================================================================
        println("\n" * "="^60)
        println("POST-SOLVE: CONSTRAINT VERIFICATION (year=2040)")
        println("="^60)
        _check_year = 2040
        _check_geos = [8, 9, 2, 58]  # DE21, DE22, AT33, ITH1
        for gid in _check_geos
            be = get(B_e, gid, 0.0)
            cap_cp = kappa_space * be
            cap_kw = kappa_infra * be
            println("  geo=$(gid) ($(_geo_name_dbg[gid])), B_e=$(round(be, digits=0))")
            for f_l in _elec_fl
                actual_kw = value(model[:q_fuel_infr_plus][_check_year, f_l, gid])
                actual_cp = actual_kw / _charger_power[f_l[2]]
                label = f_l[2] == 1 ? "CCS" : "MCS"
                println("    $(label) $(f_l): $(round(actual_kw, digits=1)) kW = $(round(actual_cp, digits=2)) cp")
            end
            # Space constraint check (total charge points)
            total_cp = sum(value(model[:q_fuel_infr_plus][_check_year, f_l, gid]) / _charger_power[f_l[2]] for f_l in _elec_fl)
            println("    κ_space: $(round(total_cp, digits=2)) cp / $(round(cap_cp, digits=3)) cap = $(round(total_cp/max(cap_cp,1e-9), digits=2))x")
            total_kw = sum(value(model[:q_fuel_infr_plus][_check_year, f_l, gid]) for f_l in _elec_fl)
            println("    κ (kW):  $(round(total_kw, digits=0)) kW / $(round(cap_kw, digits=0)) cap = $(round(total_kw/max(cap_kw,1e-9), digits=2))x")
        end
        println("="^60)

        # ================================================================
        # Step 8: Save results
        # ================================================================
        @info "Saving results to file..."
        results_file_path = normpath(joinpath(script_dir, "results", "surcharge_v3", get(ENV, "RUN_LABEL", "baseline")))
        if !isdir(results_file_path)
            mkpath(results_file_path)
        end
        # Extract just the scenario name (last part of path) for log filenames
        # Use split to handle both / and \ separators on Windows
        scenario_name = split(folder, ['/', '\\'])[end]
        # DIRECT SAVE - bypass problematic save_results function
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

        # Save s (energy) variable - iterate with actual tuple keys
        s_results = Dict{String, Float64}()
        if haskey(model.obj_dict, :s)
            @info "  Extracting s variable..."
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

        # Save soc (state of charge) variable - iterate with actual tuple keys
        soc_results = Dict{String, Float64}()
        if haskey(model.obj_dict, :soc)
            @info "  Extracting soc variable..."
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

        # Save travel_time variable - iterate with actual tuple keys
        travel_time_results = Dict{String, Float64}()
        if haskey(model.obj_dict, :travel_time)
            @info "  Extracting travel_time variable..."
            p_r_k_g_pairs_tt = data_structures["p_r_k_g_pairs"]
            tv_ids_tt = data_structures["techvehicle_ids"]
            for y in modeled_years_save, prkg in p_r_k_g_pairs_tt, tv in tv_ids_tt, g in modeled_generations_save
                if g <= y
                    val = value(model[:travel_time][y, prkg, tv, g])
                    if !isnan(val) && abs(val) > 1e-6
                        travel_time_results[string((y, prkg, tv, g))] = val
                    end
                end
            end
            YAML.write_file(joinpath(results_file_path, "$(case_name)_travel_time_dict.yaml"), travel_time_results)
            @info "  ✓ Saved $(length(travel_time_results)) travel_time values"
        end

        # Save extra_break_time variable - iterate with actual tuple keys
        extra_break_time_results = Dict{String, Float64}()
        if haskey(model.obj_dict, :extra_break_time)
            @info "  Extracting extra_break_time variable..."
            p_r_k_g_pairs_bt = data_structures["p_r_k_g_pairs"]
            tv_ids_bt = data_structures["techvehicle_ids"]
            for y in modeled_years_save, prkg in p_r_k_g_pairs_bt, tv in tv_ids_bt, g in modeled_generations_save
                if g <= y
                    val = value(model[:extra_break_time][y, prkg, tv, g])
                    if !isnan(val) && abs(val) > 1e-6
                        extra_break_time_results[string((y, prkg, tv, g))] = val
                    end
                end
            end
            YAML.write_file(joinpath(results_file_path, "$(case_name)_extra_break_time_dict.yaml"), extra_break_time_results)
            @info "  ✓ Saved $(length(extra_break_time_results)) extra_break_time values"
        end

        # Save q_fuel_infr_plus (infrastructure) variable
        # NOTE: eachindex on DenseAxisArray returns CartesianIndex with 1-based POSITIONAL indices
        # Mapping: year = y_init + (yi-1)*step, f_l = sorted(f_l_pairs)[fi], geo_id = pos-1
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

        # Extract energy charged by year
        @info "DEBUG: Extracting energy data from s..."
        energy_by_year = Dict{Int,Float64}()
        s_dict = model[:s]
        for idx in eachindex(s_dict)
            var = s_dict[idx]
            val = value(var)
            if val > 1e-6
                year = idx[1]  # idx[1] IS the year, not an index
                if !haskey(energy_by_year, year)
                    energy_by_year[year] = 0.0
                end
                energy_by_year[year] += val
            end
        end
        @info "DEBUG: Energy extraction done"

        # Extract tonnes transported by technology and year
        @info "DEBUG: Extracting tonnes data from f..."
        tonnes_by_tech_year = Dict(0 => Dict{Int,Float64}(), 1 => Dict{Int,Float64}())
        f_dict = model[:f]
        for idx in eachindex(f_dict)
            var = f_dict[idx]
            val = value(var)
            if val > 1e-6
                year = idx[1]
                m_tv = idx[3]
                tv_id = m_tv[2]
                tv_idx = findfirst(tv -> tv.id == tv_id, tv_list)
                if tv_idx !== nothing
                    tv = tv_list[tv_idx]
                    tech = tv.technology.id
                    tonnes = val * 1000  # f is in 1000 tonnes
                    if !haskey(tonnes_by_tech_year[tech], year)
                        tonnes_by_tech_year[tech][year] = 0.0
                    end
                    tonnes_by_tech_year[tech][year] += tonnes
                end
            end
        end

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

        # Calculate and display tonnes summary for key years
        @info "Tonnes transported by technology:"
        for year in [2020, 2030, 2040, 2050, 2060]
            if year in modeled_years
                icev_t = get(tonnes_by_tech_year[0], year, 0.0)
                bev_t = get(tonnes_by_tech_year[1], year, 0.0)
                total_t = icev_t + bev_t
                bev_pct = total_t > 0 ? round(bev_t / total_t * 100, digits=1) : 0.0
                @info "  $year: ICEV=$(round(Int, icev_t/1e6))Mt, BEV=$(round(Int, bev_t/1e6))Mt, BEV%=$bev_pct%"
            end
        end

        # Display energy charged
        @info "Energy charged (GWh):"
        for year in [2020, 2030, 2040, 2050, 2060]
            if year in modeled_years
                energy = get(energy_by_year, year, 0.0)
                @info "  $year: $(round(energy/1e6, digits=2)) GWh"
            end
        end

        # Save summary statistics to YAML
        summary_stats = Dict(
            "case" => folder,
            "objective_value" => objective_value(model),
            "fleet_by_year" => Dict(
                year => Dict(
                    "ICEV" => get(fleet_by_tech_year[0], year, 0.0),
                    "BEV" => get(fleet_by_tech_year[1], year, 0.0)
                ) for year in modeled_years
            ),
            "tonnes_by_year" => Dict(
                year => Dict(
                    "ICEV" => get(tonnes_by_tech_year[0], year, 0.0),
                    "BEV" => get(tonnes_by_tech_year[1], year, 0.0)
                ) for year in modeled_years
            ),
            "energy_by_year" => energy_by_year
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
@info "BATCH PROCESSING COMPLETE"
@info "="^80
@info "Total batch time: $(round(batch_elapsed/60, digits=2)) minutes ($(round(batch_elapsed/3600, digits=2)) hours)"
@info ""
@info "Results summary:"
@info "-"^100
@info @sprintf("%-4s | %-45s | %8s | %12s | %10s | %10s", "#", "Scenario", "Status", "Obj (B EUR)", "BEV% 2040", "BEV% 2060")
@info "-"^100
for (idx, folder) in enumerate(case_folders)
    result = batch_results[folder]
    status = result["status"]
    elapsed = get(result, "total_time", 0.0)

    # Extract scenario name (last part of path)
    scenario_name = split(folder, "/")[end]

    if status == "SUCCESS"
        obj_val = get(result, "objective_value", 0.0)
        bev_2040 = get(result, "bev_share_2040", 0.0)
        bev_2060 = get(result, "bev_share_2060", 0.0)
        @info @sprintf("%-4d | %-45s | %8s | %12.2f | %9.1f%% | %9.1f%%",
                       idx, scenario_name, "✓ OK", obj_val/1e9, bev_2040, bev_2060)
    elseif status == "FAILED"
        error_msg = get(result, "error", "Unknown error")
        @info @sprintf("%-4d | %-45s | %8s | %12s | %10s | %10s",
                       idx, scenario_name, "✗ FAIL", "-", "-", "-")
    else
        reason = get(result, "reason", "Unknown")
        @info @sprintf("%-4d | %-45s | %8s | %12s | %10s | %10s",
                       idx, scenario_name, "⊘ SKIP", "-", "-", "-")
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
@info "All cases processed. Results saved in 'results/' subdirectories."
@info "="^80
