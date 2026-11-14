# Core Model: 12 constraints (with travel time tracking + mandatory breaks)
# Constraints:
# 1. constraint_demand_coverage
# 2. constraint_vehicle_sizing
# 3. constraint_vehicle_aging
# 4. constraint_vehicle_stock_shift
# 5. constraint_flow_shift (DISABLED)
# 6. constraint_fueling_infrastructure
# 7. constraint_fueling_infrastructure_expansion_shift
# 8. constraint_soc_track
# 9. constraint_soc_max
# 10. constraint_fueling_demand  <-- CRITICAL: links s to f × spec_cons × path_length
# 11. constraint_travel_time_track  <-- Tracks cumulative travel time along route
# 12. constraint_mandatory_breaks  <-- Enforces EU driver break regulations (4.5h → 45min)

using Pkg
Pkg.activate(joinpath(@__DIR__, "../.."))

using YAML, JuMP, Gurobi, Printf, Dates

include(joinpath(@__DIR__, "../../src/TransComp.jl"))
using .TransComp

# ============================================================================
# CONFIGURATION
# ============================================================================

# DEBUG MODE: Set to true for fast debugging (20 OD pairs)
DEBUG_MODE = true
DEBUG_ODPAIRS = 20

script_dir = @__DIR__
folder = "case_20251107_214315_uni_uni"
input_path = joinpath(@__DIR__, "input_data", folder)

timestamp = Dates.format(now(), "yyyymmdd_HHMMSS")
case = "core_model_$timestamp"

# Results storage
results_dir = joinpath(@__DIR__, "results", "core_model")
if !isdir(results_dir)
    mkpath(results_dir)
end

# Variables needed for SOC tracking and travel time tracking
# Added q_fuel_infr_plus_by_route for infrastructure expansion constraint
# Added travel_time for travel time tracking along routes
# Added extra_break_time for mandatory break slack (allows break time even without charging)
relevant_vars = ["f", "h", "h_plus", "h_exist", "h_minus", "s", "q_fuel_infr_plus", "q_fuel_infr_plus_by_route", "soc", "travel_time", "extra_break_time"]

# ============================================================================
# LOAD AND PARSE DATA
# ============================================================================
println("\n" * "=" ^ 80)
println("CORE MODEL: 8 Constraints (SOC-based, with infrastructure expansion limits)")
println("=" ^ 80)

@info "Loading input data..."
t_start = time()
data_dict = get_input_data(input_path)
@info "[OK] Input data loaded in $(round(time() - t_start, digits=2))s"

# DEBUG MODE: Limit OD pairs BEFORE parsing
if DEBUG_MODE
    original_count = length(data_dict["Odpair"])
    data_dict["Odpair"] = data_dict["Odpair"][1:min(DEBUG_ODPAIRS, original_count)]
    @warn "DEBUG: Reduced OD pairs from $original_count to $(length(data_dict["Odpair"]))"
end

@info "Parsing data structures..."
t_start = time()
data_structures = parse_data(data_dict)
@info "[OK] Data parsed in $(round(time() - t_start, digits=2))s"

num_odpairs = length(data_structures["odpair_list"])
@info "Using $num_odpairs OD pairs"

# ============================================================================
# CREATE MODEL
# ============================================================================
@info "Creating model..."
t_start = time()
model, data_structures = create_model(data_structures, case, include_vars=relevant_vars)
@info "[OK] Model created in $(round(time() - t_start, digits=2))s"
@info "Number of variables: $(num_variables(model))"

# ============================================================================
# CONFIGURE SOLVER
# ============================================================================
set_optimizer_attribute(model, "Method", 2)
set_optimizer_attribute(model, "MIPFocus", 1)
set_optimizer_attribute(model, "MIPGap", 0.01)
set_optimizer_attribute(model, "NumericFocus", 3)
set_optimizer_attribute(model, "ScaleFlag", 2)
set_optimizer_attribute(model, "FeasibilityTol", 1e-5)
set_optimizer_attribute(model, "OptimalityTol", 1e-5)
set_optimizer_attribute(model, "Crossover", 0)
set_optimizer_attribute(model, "BarConvTol", 1e-6)

# ============================================================================
# ADD CONSTRAINTS (10 core constraints)
# ============================================================================
@info "Adding constraints (10 core constraints)..."

# 1. Demand coverage
t_start = time()
constraint_demand_coverage(model, data_structures)
@info "[1/9] constraint_demand_coverage added in $(round(time() - t_start, digits=2))s"

# 2. Vehicle sizing
t_start = time()
constraint_vehicle_sizing(model, data_structures)
@info "[2/9] constraint_vehicle_sizing added in $(round(time() - t_start, digits=2))s"

# 3. Vehicle aging
t_start = time()
constraint_vehicle_aging(model, data_structures)
@info "[3/9] constraint_vehicle_aging added in $(round(time() - t_start, digits=2))s"

# 4. Vehicle stock shift (limits technology transition rate) - NOW INCLUDES y_init!
t_start = time()
constraint_vehicle_stock_shift(model, data_structures)
@info "[4/9] constraint_vehicle_stock_shift added in $(round(time() - t_start, digits=2))s"

# ADDITIONAL: Force model to USE existing vehicles before buying new ones
# The issue: model routes all flow through Gen 2020 and ignores existing fleet
# Fix: Constrain flow to use existing generations proportionally

y_init = data_structures["y_init"]
odpairs = data_structures["odpair_list"]
techvehicles = data_structures["techvehicle_list"]
g_init = data_structures["g_init"]
time_step = data_structures["time_step"]

# No BEV purchases in 2020 (keep this constraint for realistic initial year)
bev_tvs = [tv for tv in techvehicles if tv.technology.id == 1]
@info "Adding constraint: No BEV purchases in 2020"
for tv in bev_tvs
    for r in odpairs
        for g in g_init:time_step:y_init
            @constraint(model, model[:h_plus][y_init, r.id, tv.id, g] == 0)
        end
    end
end
@info "  Constrained h_plus[2020, *, BEV, *] = 0"

# NOTE: NOT limiting ICEV purchases in 2020
# The pre_age_sell fix (constraint h_minus=0 for vehicles at/before lifetime) should:
# - Force model to USE existing fleet (can't sell them)
# - Only buy NEW vehicles to cover capacity gaps
# Let's see how many new vehicles the model actually needs
@info "No ICEV purchase limit in 2020 - relying on pre_age_sell fix to force existing fleet usage"

# ==============================================================================
# TEST: h == factor * f (instead of h >= factor * f) in constraint_vehicle_sizing
# ==============================================================================
# This should force existing vehicles (h_exist) to carry flow proportional to h
# If feasible: existing fleet will be used
# If infeasible: there's a conflict between h_exist and demand
# ==============================================================================
@info "TEST: Using h == factor * f constraint (changed in model_functions.jl)"

# NOTE: The core fix for fleet utilization is in model_functions.jl
# Changed pre_age_sell constraint from (y-g) < Lifetime to (y-g) <= Lifetime
# This prevents selling vehicles AT their lifetime (e.g., Gen 2008 in 2020)
# Now the model MUST use existing vehicles, can't just sell them and buy new

# 5. Flow shift (limits how fast transport volume can shift between technologies)
# NOTE: DISABLED - investigating initial vehicle stock vs demand issue first
# t_start = time()
# constraint_flow_shift(model, data_structures)
# @info "[5/9] constraint_flow_shift added in $(round(time() - t_start, digits=2))s"
@info "[5/9] constraint_flow_shift DISABLED (investigating stock vs demand)"

# 6. Fueling infrastructure
t_start = time()
constraint_fueling_infrastructure(model, data_structures)
@info "[6/9] constraint_fueling_infrastructure added in $(round(time() - t_start, digits=2))s"

# 7. Fueling infrastructure expansion shift (limits infra expansion rate)
t_start = time()
constraint_fueling_infrastructure_expansion_shift(model, data_structures)
@info "[7/9] constraint_fueling_infrastructure_expansion_shift added in $(round(time() - t_start, digits=2))s"

# 8. SOC tracking
t_start = time()
constraint_soc_track(model, data_structures)
@info "[8/12] constraint_soc_track added in $(round(time() - t_start, digits=2))s"

# 9. SOC max
t_start = time()
constraint_soc_max(model, data_structures)
@info "[9/12] constraint_soc_max added in $(round(time() - t_start, digits=2))s"

# 10. Fueling demand (links total energy charged to flow × spec_cons × path_length)
# This is CRITICAL: without it, the s variable for BEV is not properly constrained
t_start = time()
constraint_fueling_demand(model, data_structures)
@info "[10/12] constraint_fueling_demand added in $(round(time() - t_start, digits=2))s"

# 11. Travel time tracking (tracks cumulative travel time along each route)
# travel_time[node] = travel_time[prev] + driving_time + charging_time
t_start = time()
constraint_travel_time_track(model, data_structures)
@info "[11/12] constraint_travel_time_track added in $(round(time() - t_start, digits=2))s"

# 12. Mandatory breaks (enforces EU driver break regulations: 4.5h driving → 45min break)
# travel_time at break locations must account for break duration
t_start = time()
constraint_mandatory_breaks(model, data_structures)
@info "[12/12] constraint_mandatory_breaks added in $(round(time() - t_start, digits=2))s"

# ============================================================================
# ADD OBJECTIVE (WITH fuel costs)
# ============================================================================
@info "Adding objective function (WITH fuel costs)..."
t_start = time()
objective(model, data_structures, true)
@info "[OK] Objective added in $(round(time() - t_start, digits=2))s"

# ============================================================================
# OPTIMIZE
# ============================================================================
@info "Solving..."
GC.gc()
t_start = time()
optimize!(model)
t_solve = time() - t_start
@info "[OK] Solved in $(round(t_solve, digits=2))s"

solution_summary(model)

# Check if model is infeasible and compute IIS
if termination_status(model) == MOI.INFEASIBLE
    @warn "Model is INFEASIBLE - computing IIS..."

    # Get the underlying Gurobi optimizer properly
    inner_optimizer = JuMP.unsafe_backend(model)

    # Compute IIS using the optimizer's model pointer
    Gurobi.GRBcomputeIIS(inner_optimizer.inner)

    # Write IIS to file
    iis_file = "iis_analysis.ilp"
    Gurobi.GRBwrite(inner_optimizer.inner, iis_file)
    @info "IIS written to $iis_file"

    @info "Check the IIS file to identify conflicting constraints"
    error("Model is infeasible - see IIS file for details")
end

# ============================================================================
# EXTRACT RESULTS
# ============================================================================
obj_val = objective_value(model)
@info "Objective value: $(round(obj_val/1e9, digits=4)) billion EUR"

modeled_years = data_structures["modeled_years"]
tv_list = data_structures["techvehicle_list"]

# Extract fleet by technology (0=ICEV, 1=BEV) and year
# NOTE: h uses NAMED axes, so idx[1] is the ACTUAL year (2020, 2024...), not a position
# This is different from s and f which use CartesianIndex
h_dict = model[:h]
fleet_by_tech_year = Dict(0 => Dict{Int,Float64}(), 1 => Dict{Int,Float64}())

# DEBUG: Track h by generation for year 2020
h_by_generation_2020 = Dict{Int, Float64}()

for idx in eachindex(h_dict)
    var = h_dict[idx]
    val = value(var)
    if val > 1e-6
        year = idx[1]  # Already the actual year for h variable
        tv_id = idx[3]  # Already the actual techvehicle ID
        gen = idx[4]    # Generation

        tv_idx = findfirst(tv -> tv.id == tv_id, tv_list)
        if tv_idx !== nothing
            tv = tv_list[tv_idx]
            tech = tv.technology.id
            if !haskey(fleet_by_tech_year[tech], year)
                fleet_by_tech_year[tech][year] = 0.0
            end
            fleet_by_tech_year[tech][year] += val

            # DEBUG: Track by generation for 2020, ICEV only
            if year == 2020 && tech == 0
                if !haskey(h_by_generation_2020, gen)
                    h_by_generation_2020[gen] = 0.0
                end
                h_by_generation_2020[gen] += val
            end
        end
    end
end

# Print generation breakdown for 2020
println("\n" * "=" ^ 80)
println("DEBUG: ICEV FLEET BY GENERATION IN 2020")
println("=" ^ 80)
for gen in sort(collect(keys(h_by_generation_2020)))
    println("  Generation $gen: $(round(h_by_generation_2020[gen], digits=1)) vehicles")
end
println("  TOTAL: $(round(sum(values(h_by_generation_2020)), digits=1)) vehicles")
println("=" ^ 80)

# DEBUG: Check h_exist values for 2020 by generation
println("\nDEBUG: h_exist BY GENERATION IN 2020")
println("=" ^ 80)
h_exist_dict = model[:h_exist]
h_exist_by_gen_2020 = Dict{Int, Float64}()
for idx in eachindex(h_exist_dict)
    var = h_exist_dict[idx]
    val = value(var)
    if val > 1e-6
        year = idx[1]
        tv_id = idx[3]
        gen = idx[4]
        tv_idx = findfirst(tv -> tv.id == tv_id, tv_list)
        if tv_idx !== nothing && year == 2020
            tv = tv_list[tv_idx]
            if tv.technology.id == 0  # ICEV only
                if !haskey(h_exist_by_gen_2020, gen)
                    h_exist_by_gen_2020[gen] = 0.0
                end
                h_exist_by_gen_2020[gen] += val
            end
        end
    end
end
if isempty(h_exist_by_gen_2020)
    println("  No h_exist values found for 2020!")
else
    for gen in sort(collect(keys(h_exist_by_gen_2020)))
        println("  Generation $gen: $(round(h_exist_by_gen_2020[gen], digits=1)) vehicles (h_exist)")
    end
    println("  TOTAL h_exist: $(round(sum(values(h_exist_by_gen_2020)), digits=1)) vehicles")
end
println("=" ^ 80)

# DEBUG: Check what the initial vehicle stock SHOULD be
println("\nDEBUG: INITIAL VEHICLE STOCK FROM DATA")
println("=" ^ 80)
init_stock_by_gen = Dict{Int, Float64}()
for r in data_structures["odpair_list"]
    for ivs in r.vehicle_stock_init
        tv = ivs.techvehicle
        if tv.technology.id == 0  # ICEV
            gen = ivs.year_of_purchase
            if !haskey(init_stock_by_gen, gen)
                init_stock_by_gen[gen] = 0.0
            end
            init_stock_by_gen[gen] += ivs.stock
        end
    end
end
for gen in sort(collect(keys(init_stock_by_gen)))
    println("  Generation $gen: $(round(init_stock_by_gen[gen], digits=1)) vehicles (InitialVehicleStock)")
end
println("  TOTAL from InitialVehicleStock: $(round(sum(values(init_stock_by_gen)), digits=1)) vehicles")
println("=" ^ 80)

# DEBUG: Check flow (f) by generation for 2020
println("\nDEBUG: FLOW (f) BY GENERATION IN 2020")
println("=" ^ 80)
f_dict = model[:f]
f_by_gen_2020 = Dict{Int, Float64}()
for idx in eachindex(f_dict)
    var = f_dict[idx]
    val = value(var)
    if val > 1e-6
        year = idx[1]
        if year == 2020
            gen = idx[4]  # generation
            if !haskey(f_by_gen_2020, gen)
                f_by_gen_2020[gen] = 0.0
            end
            f_by_gen_2020[gen] += val
        end
    end
end
for gen in sort(collect(keys(f_by_gen_2020)))
    println("  Generation $gen: $(round(f_by_gen_2020[gen], digits=1)) kilo-tonnes")
end
println("  TOTAL: $(round(sum(values(f_by_gen_2020)), digits=1)) kilo-tonnes")
println("=" ^ 80)

# DEBUG: Check h_plus (new purchases) by generation for 2020
println("\nDEBUG: h_plus (NEW PURCHASES) BY GENERATION IN 2020")
println("=" ^ 80)
h_plus_dict = model[:h_plus]
h_plus_by_gen_2020 = Dict{Int, Float64}()
for idx in eachindex(h_plus_dict)
    var = h_plus_dict[idx]
    val = value(var)
    if val > 1e-6
        year = idx[1]
        tv_id = idx[3]
        gen = idx[4]
        tv_idx = findfirst(tv -> tv.id == tv_id, tv_list)
        if tv_idx !== nothing && year == 2020
            tv = tv_list[tv_idx]
            if tv.technology.id == 0  # ICEV only
                if !haskey(h_plus_by_gen_2020, gen)
                    h_plus_by_gen_2020[gen] = 0.0
                end
                h_plus_by_gen_2020[gen] += val
            end
        end
    end
end
for gen in sort(collect(keys(h_plus_by_gen_2020)))
    println("  Generation $gen: $(round(h_plus_by_gen_2020[gen], digits=1)) vehicles purchased")
end
println("  TOTAL: $(round(sum(values(h_plus_by_gen_2020)), digits=1)) vehicles")
println("=" ^ 80)

# DEBUG: Check h_minus (sold/retired) by generation for 2020
println("\nDEBUG: h_minus (SOLD/RETIRED) BY GENERATION IN 2020")
println("=" ^ 80)
h_minus_dict = model[:h_minus]
h_minus_by_gen_2020 = Dict{Int, Float64}()
for idx in eachindex(h_minus_dict)
    var = h_minus_dict[idx]
    val = value(var)
    if val > 1e-6
        year = idx[1]
        tv_id = idx[3]
        gen = idx[4]
        tv_idx = findfirst(tv -> tv.id == tv_id, tv_list)
        if tv_idx !== nothing && year == 2020
            tv = tv_list[tv_idx]
            if tv.technology.id == 0  # ICEV only
                if !haskey(h_minus_by_gen_2020, gen)
                    h_minus_by_gen_2020[gen] = 0.0
                end
                h_minus_by_gen_2020[gen] += val
            end
        end
    end
end
if isempty(h_minus_by_gen_2020)
    println("  No vehicles sold/retired in 2020")
else
    for gen in sort(collect(keys(h_minus_by_gen_2020)))
        println("  Generation $gen: $(round(h_minus_by_gen_2020[gen], digits=1)) vehicles sold/retired")
    end
    println("  TOTAL: $(round(sum(values(h_minus_by_gen_2020)), digits=1)) vehicles")
end
println("=" ^ 80)

# Calculate fleet summary
fleet_summary = Dict{Int, Dict{String, Float64}}()
for year in modeled_years
    icev = get(fleet_by_tech_year[0], year, 0.0)
    bev = get(fleet_by_tech_year[1], year, 0.0)
    total = icev + bev
    bev_share = total > 0 ? (bev / total * 100) : 0.0
    fleet_summary[year] = Dict(
        "ICEV" => icev,
        "BEV" => bev,
        "Total" => total,
        "BEV_share_pct" => bev_share
    )
end

# Extract energy charged by year
# NOTE: idx is a CartesianIndex - idx[1] is the POSITION in modeled_years, not the year itself
energy_by_year = Dict{Int,Float64}()
s_dict = model[:s]
for idx in eachindex(s_dict)
    var = s_dict[idx]
    val = value(var)
    if val > 1e-6
        year_idx = idx[1]
        year = modeled_years[year_idx]  # Convert index to actual year
        if !haskey(energy_by_year, year)
            energy_by_year[year] = 0.0
        end
        energy_by_year[year] += val
    end
end

# Extract tonnes transported by technology and year
tonnes_by_tech_year = Dict(0 => Dict{Int,Float64}(), 1 => Dict{Int,Float64}())
f_dict = model[:f]
odpair_list = data_structures["odpair_list"]
odpair_dict = Dict(r.id => r for r in odpair_list)

# NOTE: f uses NAMED tuples, so idx[1] is the ACTUAL year (2020, 2024...)
# idx structure: (year, (product_id, odpair_id, path_id), (mode_id, techvehicle_id), generation)
for idx in eachindex(f_dict)
    var = f_dict[idx]
    val = value(var)
    if val > 1e-6
        year = idx[1]  # Already the actual year
        # idx[3] = (mode_id, techvehicle_id) tuple
        m_tv = idx[3]
        tv_id = m_tv[2]  # techvehicle_id is the second element

        tv_idx = findfirst(tv -> tv.id == tv_id, tv_list)
        if tv_idx !== nothing
            tv = tv_list[tv_idx]
            tech = tv.technology.id

            # f is in 1000 tonnes, so multiply by 1000 to get tonnes
            tonnes = val * 1000

            if !haskey(tonnes_by_tech_year[tech], year)
                tonnes_by_tech_year[tech][year] = 0.0
            end
            tonnes_by_tech_year[tech][year] += tonnes
        end
    end
end

# Calculate tonnes summary
tonnes_summary = Dict{Int, Dict{String, Float64}}()
for year in modeled_years
    icev_tonnes = get(tonnes_by_tech_year[0], year, 0.0)
    bev_tonnes = get(tonnes_by_tech_year[1], year, 0.0)
    total_tonnes = icev_tonnes + bev_tonnes
    bev_share = total_tonnes > 0 ? (bev_tonnes / total_tonnes * 100) : 0.0
    tonnes_summary[year] = Dict(
        "ICEV_tonnes" => icev_tonnes,
        "BEV_tonnes" => bev_tonnes,
        "Total_tonnes" => total_tonnes,
        "BEV_share_pct" => bev_share
    )
end

# Save all results to YAML
results = Dict(
    "case" => case,
    "folder" => folder,
    "num_odpairs" => num_odpairs,
    "num_variables" => num_variables(model),
    "objective_value" => obj_val,
    "objective_value_billion_EUR" => obj_val / 1e9,
    "solve_time" => t_solve,
    "constraints" => [
        "constraint_demand_coverage",
        "constraint_vehicle_sizing",
        "constraint_vehicle_aging",
        "constraint_vehicle_stock_shift",
        "constraint_flow_shift",
        "constraint_fueling_infrastructure",
        "constraint_fueling_infrastructure_expansion_shift",
        "constraint_soc_track",
        "constraint_soc_max"
    ],
    "fleet_by_year" => fleet_summary,
    "tonnes_by_year" => tonnes_summary,
    "energy_by_year" => energy_by_year
)
YAML.write_file(joinpath(results_dir, "core_model_results.yaml"), results)

# Print summary
println("\n" * "=" ^ 80)
println("FLEET DEVELOPMENT SUMMARY")
println("=" ^ 80)
@printf("%-6s | %12s | %12s | %12s | %10s\n", "Year", "ICEV", "BEV", "Total", "BEV %")
println("-" ^ 60)
for year in modeled_years
    data = fleet_summary[year]
    @printf("%4d   | %12.1f | %12.1f | %12.1f | %8.1f%%\n",
            year, data["ICEV"], data["BEV"], data["Total"], data["BEV_share_pct"])
end
println("-" ^ 60)

println("\n" * "=" ^ 80)
println("TONNES TRANSPORTED BY TECHNOLOGY")
println("=" ^ 80)
@printf("%-6s | %15s | %15s | %15s | %10s\n", "Year", "ICEV (t)", "BEV (t)", "Total (t)", "BEV %")
println("-" ^ 70)
for year in modeled_years
    data = tonnes_summary[year]
    @printf("%4d   | %15.0f | %15.0f | %15.0f | %8.1f%%\n",
            year, data["ICEV_tonnes"], data["BEV_tonnes"], data["Total_tonnes"], data["BEV_share_pct"])
end
println("-" ^ 70)

println("\n" * "=" ^ 80)
println("ENERGY CHARGED BY YEAR (kWh)")
println("=" ^ 80)
for year in modeled_years
    energy = get(energy_by_year, year, 0.0)
    @printf("%4d: %15.1f kWh\n", year, energy)
end

println("\n" * "=" ^ 80)
println("RESULTS SAVED")
println("=" ^ 80)
println("Results directory: $results_dir")
println("  - core_model_results.yaml")

GC.gc()
println("\n[DONE] Core model run complete!")
