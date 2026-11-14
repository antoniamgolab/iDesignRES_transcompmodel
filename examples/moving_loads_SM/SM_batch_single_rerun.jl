"""
SM_batch_single_rerun.jl - Run ONE scenario to get corrected s_dict with proper tuple keys.

Purpose: After fixing create_p_r_k_g_set() to return sorted vectors instead of Sets,
re-running one scenario produces s_dict files where the geo attribution is correct.
Since all 4 uncertainty scenarios share the same Odpair.yaml and Path.yaml,
the prkg ordering is identical — so one run validates the fix for all.

Also saves prkg_ordering.txt so Python post-processing can verify the ordering
matches sorted() (which it should, now that the fix is in place).

Usage:
    julia SM_batch_single_rerun.jl
"""

using Pkg
Pkg.activate(joinpath(@__DIR__, "../.."))  # Activate the project environment

using YAML, JuMP, Gurobi, Printf, ProgressMeter, Dates

include(joinpath(@__DIR__, "../../src/TransComp.jl"))
using .TransComp

# ============================================================================
# CONFIGURATION: Run only scenario_000 (Go RES)
# ============================================================================

folder = "uncertainty_scenarios/scenario_000"
label = "Go RES (EUR500/tCO2) - RERUN with fixed prkg ordering"

relevant_vars = ["f", "h", "h_plus", "h_exist", "h_minus", "s", "q_fuel_infr_plus", "q_fuel_infr_plus_by_route", "soc", "travel_time", "extra_break_time"]

@info "="^80
@info "SINGLE SCENARIO RERUN: $folder"
@info label
@info "="^80

case_start_time = time()

# ================================================================
# Step 1: Setup paths
# ================================================================
script_dir = @__DIR__
input_path = joinpath(script_dir, "input_data", folder)

if !isdir(input_path)
    error("Input folder not found: $input_path")
end

@info "Input path: $input_path"

scenario_name = split(folder, ['/', '\\'])[end]
timestamp = Dates.format(now(), "yyyy-mm-dd_HH-MM-SS")
case_name = "$(scenario_name)_rerun_$timestamp"

# ================================================================
# Step 2: Read and parse input data
# ================================================================
@info "Step 1/5: Reading input data..."
t_start = time()
data_dict = get_input_data(input_path)
t_read = time() - t_start
@info "  Input data loaded in $(round(t_read, digits=2)) seconds"

@info "Step 2/5: Parsing data structures..."
t_start = time()
data_structures = parse_data(data_dict)
t_parse = time() - t_start
@info "  Data parsed in $(round(t_parse, digits=2)) seconds"

# ================================================================
# Step 3: Create optimization model
# ================================================================
@info "Step 3/5: Creating optimization model..."
@info "Memory before model creation: $(round(Sys.free_memory()/1024^3, digits=2)) GB free"
t_start = time()
model, data_structures = create_model(data_structures, case_name, include_vars=relevant_vars)
t_create = time() - t_start
@info "  Model created in $(round(t_create, digits=2)) seconds"
@info "Memory after model creation: $(round(Sys.free_memory()/1024^3, digits=2)) GB free"
@info "Number of variables: $(num_variables(model))"

# ================================================================
# VERIFY AND SAVE prkg ordering (must be after create_model)
# ================================================================
p_r_k_g_pairs = data_structures["p_r_k_g_pairs"]
@info "p_r_k_g_pairs type: $(typeof(p_r_k_g_pairs)), length: $(length(p_r_k_g_pairs))"
@info "First 5 entries: $(collect(Iterators.take(p_r_k_g_pairs, 5)))"

prkg_vec = collect(p_r_k_g_pairs)
is_sorted = issorted(prkg_vec)
@info "p_r_k_g_pairs is sorted: $is_sorted"

if !is_sorted
    @warn "p_r_k_g_pairs is NOT sorted! The fix in support_functions.jl may not be applied."
    @warn "Check that create_p_r_k_g_set returns sort(collect(Set(...))) instead of Set(...)"
end

ordering_file = joinpath(script_dir, "prkg_ordering_elsevier.txt")
open(ordering_file, "w") do io
    for (i, t) in enumerate(prkg_vec)
        println(io, "$i\t$t")
    end
end
@info "Saved prkg ordering to: $ordering_file ($(length(prkg_vec)) entries)"

# ================================================================
# Step 4: Configure solver
# ================================================================
@info "Step 3.5/5: Configuring solver parameters..."
set_optimizer_attribute(model, "Method", 2)
set_optimizer_attribute(model, "MIPFocus", 1)
set_optimizer_attribute(model, "Cuts", 1)
set_optimizer_attribute(model, "MIPGap", 0.01)
set_optimizer_attribute(model, "NumericFocus", 3)
set_optimizer_attribute(model, "ScaleFlag", 2)
set_optimizer_attribute(model, "FeasibilityTol", 1e-5)
set_optimizer_attribute(model, "OptimalityTol", 1e-5)
set_optimizer_attribute(model, "IntFeasTol", 1e-4)
set_optimizer_attribute(model, "Crossover", -1)
set_optimizer_attribute(model, "BarConvTol", 1e-8)
@info "  Solver configured"

# ================================================================
# Step 5: Add constraints (same as SM_batch.jl)
# ================================================================
@info "Step 4/5: Adding constraints..."
t_constraints_start = time()

constraint_mandatory_breaks(model, data_structures)
@info "  + Mandatory breaks"

constraint_fueling_demand(model, data_structures)
@info "  + Fueling demand"

constraint_fueling_infrastructure(model, data_structures)
@info "  + Fueling infrastructure"

constraint_fueling_infrastructure_expansion_shift(model, data_structures)
@info "  + Fueling infrastructure expansion shift"

constraint_soc_track(model, data_structures)
@info "  + SOC tracking"

constraint_soc_max(model, data_structures)
@info "  + SOC max"

constraint_travel_time_track(model, data_structures)
@info "  + Travel time tracking"

constraint_mode_shift(model, data_structures)
@info "  + Mode shift"

if !isempty(data_structures["max_mode_share_list"])
    constraint_max_mode_share(model, data_structures)
    @info "  + Max mode share"
end

constraint_demand_coverage(model, data_structures)
@info "  + Demand coverage"

constraint_vehicle_sizing(model, data_structures)
@info "  + Vehicle sizing"

constraint_vehicle_aging(model, data_structures)
@info "  + Vehicle aging"

constraint_vehicle_stock_shift(model, data_structures)
@info "  + Vehicle stock shift"

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
@info "  + No BEV in 2020"

t_constraints = time() - t_constraints_start
@info "  All constraints added in $(round(t_constraints, digits=2))s"

# ================================================================
# Step 6: Objective
# ================================================================
@info "Step 4.5/5: Adding objective..."
t_start = time()
objective(model, data_structures, true)
t_obj = time() - t_start
@info "  Objective added in $(round(t_obj, digits=2))s"

GC.gc()

# ================================================================
# Step 7: Solve
# ================================================================
@info "Step 5/5: Solving..."
t_start = time()
optimize!(model)
t_optimize = time() - t_start
@info "  Optimization complete in $(round(t_optimize/60, digits=2)) minutes"
@info "  Status: $(termination_status(model))"
@info "  Objective: $(objective_value(model))"

# ================================================================
# Step 8: Save results
# ================================================================
results_file_path = normpath(joinpath(script_dir, "results", replace(folder, "uncertainty_scenarios" => "uncertainty_scenarios_v2")))
if !isdir(results_file_path)
    mkpath(results_file_path)
end

@info "Saving results to: $results_file_path"

modeled_years_save = data_structures["modeled_years"]
modeled_generations_save = data_structures["modeled_generations"]
p_r_k_pairs = data_structures["p_r_k_pairs"]
techvehicle_ids = data_structures["techvehicle_ids"]

# ---- f (SparseAxisArray, safe with eachindex) ----
f_results = Dict{String, Float64}()
if haskey(model.obj_dict, :f)
    @info "  Extracting f..."
    for idx in eachindex(model[:f])
        val = value(model[:f][idx])
        if !isnan(val) && abs(val) > 1e-6
            f_results[string(idx)] = val
        end
    end
    YAML.write_file(joinpath(results_file_path, "$(case_name)_f_dict.yaml"), f_results)
    @info "  Saved $(length(f_results)) f values"
end

# ---- h, h_plus, h_exist, h_minus (Vector-based axes, safe with eachindex) ----
for varname in [:h, :h_plus, :h_exist, :h_minus]
    if haskey(model.obj_dict, varname)
        @info "  Extracting $varname..."
        results = Dict{String, Float64}()
        for idx in eachindex(model[varname])
            val = value(model[varname][idx])
            if !isnan(val) && abs(val) > 1e-6
                results[string(idx)] = val
            end
        end
        YAML.write_file(joinpath(results_file_path, "$(case_name)_$(varname)_dict.yaml"), results)
        @info "  Saved $(length(results)) $varname values"
    end
end

# ---- s (DenseAxisArray with p_r_k_g_pairs axis) ----
# Iterate with actual tuple keys to get correct geo attribution
s_results = Dict{String, Float64}()
if haskey(model.obj_dict, :s)
    @info "  Extracting s with actual tuple keys..."
    p_r_k_g_pairs_s = data_structures["p_r_k_g_pairs"]
    f_l_pairs = haskey(data_structures, "f_l_pairs") ? data_structures["f_l_pairs"] : nothing
    if f_l_pairs !== nothing
        for y in modeled_years_save, prkg in p_r_k_g_pairs_s, tv_id in techvehicle_ids, fl in f_l_pairs, g in modeled_generations_save
            val = value(model[:s][y, prkg, tv_id, fl, g])
            if !isnan(val) && abs(val) > 1e-6
                s_results[string((y, prkg, tv_id, fl, g))] = val
            end
        end
    else
        for y in modeled_years_save, prkg in p_r_k_g_pairs_s, tv_id in techvehicle_ids, g in modeled_generations_save
            val = value(model[:s][y, prkg, tv_id, g])
            if !isnan(val) && abs(val) > 1e-6
                s_results[string((y, prkg, tv_id, g))] = val
            end
        end
    end
    YAML.write_file(joinpath(results_file_path, "$(case_name)_s_dict.yaml"), s_results)
    @info "  Saved $(length(s_results)) s values"
end

# ---- soc (DenseAxisArray with p_r_k_g_pairs axis) ----
soc_results = Dict{String, Float64}()
if haskey(model.obj_dict, :soc)
    @info "  Extracting soc with actual tuple keys..."
    p_r_k_g_pairs_soc = data_structures["p_r_k_g_pairs"]
    for y in modeled_years_save, prkg in p_r_k_g_pairs_soc, tv in techvehicle_ids, g in modeled_generations_save
        if g <= y
            val = value(model[:soc][y, prkg, tv, g])
            if !isnan(val) && abs(val) > 1e-6
                soc_results[string((y, prkg, tv, g))] = val
            end
        end
    end
    YAML.write_file(joinpath(results_file_path, "$(case_name)_soc_dict.yaml"), soc_results)
    @info "  Saved $(length(soc_results)) soc values"
end

# ---- travel_time (DenseAxisArray with p_r_k_g_pairs axis) ----
travel_time_results = Dict{String, Float64}()
if haskey(model.obj_dict, :travel_time)
    @info "  Extracting travel_time with actual tuple keys..."
    p_r_k_g_pairs_tt = data_structures["p_r_k_g_pairs"]
    for y in modeled_years_save, prkg in p_r_k_g_pairs_tt, tv in techvehicle_ids, g in modeled_generations_save
        if g <= y
            val = value(model[:travel_time][y, prkg, tv, g])
            if !isnan(val) && abs(val) > 1e-6
                travel_time_results[string((y, prkg, tv, g))] = val
            end
        end
    end
    YAML.write_file(joinpath(results_file_path, "$(case_name)_travel_time_dict.yaml"), travel_time_results)
    @info "  Saved $(length(travel_time_results)) travel_time values"
end

# ---- extra_break_time (DenseAxisArray with p_r_k_g_pairs axis) ----
extra_break_time_results = Dict{String, Float64}()
if haskey(model.obj_dict, :extra_break_time)
    @info "  Extracting extra_break_time with actual tuple keys..."
    p_r_k_g_pairs_bt = data_structures["p_r_k_g_pairs"]
    for y in modeled_years_save, prkg in p_r_k_g_pairs_bt, tv in techvehicle_ids, g in modeled_generations_save
        if g <= y
            val = value(model[:extra_break_time][y, prkg, tv, g])
            if !isnan(val) && abs(val) > 1e-6
                extra_break_time_results[string((y, prkg, tv, g))] = val
            end
        end
    end
    YAML.write_file(joinpath(results_file_path, "$(case_name)_extra_break_time_dict.yaml"), extra_break_time_results)
    @info "  Saved $(length(extra_break_time_results)) extra_break_time values"
end

# ---- q_fuel_infr_plus (safe with eachindex - geo axis uses actual ids) ----
q_infr_results = Dict{String, Float64}()
if haskey(model.obj_dict, :q_fuel_infr_plus)
    @info "  Extracting q_fuel_infr_plus..."
    for idx in eachindex(model[:q_fuel_infr_plus])
        val = value(model[:q_fuel_infr_plus][idx])
        if !isnan(val) && abs(val) > 1e-6
            q_infr_results[string(idx)] = val
        end
    end
    YAML.write_file(joinpath(results_file_path, "$(case_name)_q_fuel_infr_plus_dict.yaml"), q_infr_results)
    @info "  Saved $(length(q_infr_results)) q_fuel_infr_plus values"
end

# ---- q_fuel_infr_plus_by_route ----
q_infr_route_results = Dict{String, Float64}()
if haskey(model.obj_dict, :q_fuel_infr_plus_by_route)
    @info "  Extracting q_fuel_infr_plus_by_route..."
    for idx in eachindex(model[:q_fuel_infr_plus_by_route])
        val = value(model[:q_fuel_infr_plus_by_route][idx])
        if !isnan(val) && abs(val) > 1e-6
            q_infr_route_results[string(idx)] = val
        end
    end
    YAML.write_file(joinpath(results_file_path, "$(case_name)_q_fuel_infr_plus_by_route_dict.yaml"), q_infr_route_results)
    @info "  Saved $(length(q_infr_route_results)) q_fuel_infr_plus_by_route values"
end

# ================================================================
# Summary stats
# ================================================================
modeled_years = data_structures["modeled_years"]
tv_list = data_structures["techvehicle_list"]

fleet_by_tech_year = Dict(0 => Dict{Int,Float64}(), 1 => Dict{Int,Float64}())
for idx in eachindex(model[:h])
    val = value(model[:h][idx])
    if val > 1e-6
        year, tv_id = idx[1], idx[3]
        tv_idx = findfirst(tv -> tv.id == tv_id, tv_list)
        if tv_idx !== nothing
            tech = tv_list[tv_idx].technology.id
            fleet_by_tech_year[tech][year] = get(fleet_by_tech_year[tech], year, 0.0) + val
        end
    end
end

@info "Fleet summary:"
for year in [2020, 2032, 2040, 2048, 2060]
    if year in modeled_years
        icev = get(fleet_by_tech_year[0], year, 0.0)
        bev = get(fleet_by_tech_year[1], year, 0.0)
        total = icev + bev
        bev_pct = total > 0 ? round(bev / total * 100, digits=1) : 0.0
        @info "  $year: ICEV=$(round(Int, icev)), BEV=$(round(Int, bev)), BEV%=$bev_pct%"
    end
end

summary_stats = Dict(
    "case" => folder,
    "label" => label,
    "objective_value" => objective_value(model),
    "termination_status" => string(termination_status(model)),
    "prkg_is_sorted" => is_sorted,
    "prkg_count" => length(p_r_k_g_pairs),
    "fleet_by_year" => Dict(
        year => Dict("ICEV" => get(fleet_by_tech_year[0], year, 0.0), "BEV" => get(fleet_by_tech_year[1], year, 0.0))
        for year in modeled_years
    ),
)
YAML.write_file(joinpath(results_file_path, "summary_stats.yaml"), summary_stats)

case_elapsed = time() - case_start_time
@info "="^80
@info "RERUN COMPLETE"
@info "  Time: $(round(case_elapsed/60, digits=2)) minutes"
@info "  Status: $(termination_status(model))"
@info "  Objective: $(objective_value(model))"
@info "  prkg sorted: $is_sorted"
@info "  Results: $results_file_path"
@info "  Ordering: $ordering_file"
@info "="^80
