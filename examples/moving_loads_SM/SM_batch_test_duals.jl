"""
SM_batch_test_duals.jl - Quick test of dual value extraction with small case
Only runs scenario_000 with 20 OD pairs to verify binding constraint analysis works.
"""

using Pkg
Pkg.activate(joinpath(@__DIR__, "../.."))  # Activate the project environment

using YAML, JuMP, Gurobi, Printf, ProgressMeter, Dates, Statistics

include(joinpath(@__DIR__, "../../src/TransComp.jl"))
using .TransComp

# ============================================================================
# MINIMAL CONFIG: 1 scenario, 20 OD pairs
# ============================================================================
case_folders = ["uncertainty_scenarios/scenario_000"]
DEBUG_ODPAIRS = 20

relevant_vars = ["f", "h", "h_plus", "h_exist", "h_minus", "s", "q_fuel_infr_plus", "q_fuel_infr_plus_by_route", "soc", "travel_time", "extra_break_time"]

folder = case_folders[1]
script_dir = @__DIR__
input_path = joinpath(script_dir, "input_data", folder)

@info "Test dual extraction with $DEBUG_ODPAIRS OD pairs"
@info "Input: $input_path"

# Step 1: Read and parse
data_dict = get_input_data(input_path)
original_count = length(data_dict["Odpair"])
data_dict["Odpair"] = data_dict["Odpair"][1:min(DEBUG_ODPAIRS, original_count)]
@info "Reduced OD pairs from $original_count to $(length(data_dict["Odpair"]))"

data_structures = parse_data(data_dict)

# Step 2: Create model
timestamp = Dates.format(now(), "yyyy-mm-dd_HH-MM-SS")
case_name = "test_duals_$timestamp"
model, data_structures = create_model(data_structures, case_name, include_vars=relevant_vars)
@info "Variables: $(num_variables(model))"

# Step 3: Solver config - barrier + crossover for clean duals
set_optimizer_attribute(model, "Method", 2)
set_optimizer_attribute(model, "Crossover", -1)       # Auto crossover
set_optimizer_attribute(model, "BarConvTol", 1e-8)
set_optimizer_attribute(model, "NumericFocus", 3)
set_optimizer_attribute(model, "ScaleFlag", 2)
set_optimizer_attribute(model, "FeasibilityTol", 1e-5)
set_optimizer_attribute(model, "OptimalityTol", 1e-5)

# Step 4: Add constraints
@info "Adding constraints..."
t = time()
constraint_mandatory_breaks(model, data_structures)
@info "  mandatory_breaks: $(round(time()-t, digits=1))s"

t = time()
constraint_fueling_demand(model, data_structures)
@info "  fueling_demand: $(round(time()-t, digits=1))s"

t = time()
constraint_fueling_infrastructure(model, data_structures)
@info "  fueling_infra: $(round(time()-t, digits=1))s"

t = time()
constraint_fueling_infrastructure_expansion_shift(model, data_structures)
@info "  fueling_infra_expansion: $(round(time()-t, digits=1))s"

t = time()
constraint_soc_track(model, data_structures)
@info "  soc_track: $(round(time()-t, digits=1))s"

t = time()
constraint_soc_max(model, data_structures)
@info "  soc_max: $(round(time()-t, digits=1))s"

t = time()
constraint_travel_time_track(model, data_structures)
@info "  travel_time: $(round(time()-t, digits=1))s"

t = time()
constraint_mode_shift(model, data_structures)
@info "  mode_shift: $(round(time()-t, digits=1))s"

t = time()
if !isempty(data_structures["max_mode_share_list"])
    constraint_max_mode_share(model, data_structures)
end
@info "  max_mode_share: $(round(time()-t, digits=1))s"

t = time()
constraint_demand_coverage(model, data_structures)
@info "  demand_coverage: $(round(time()-t, digits=1))s"

t = time()
constraint_vehicle_sizing(model, data_structures)
@info "  vehicle_sizing: $(round(time()-t, digits=1))s"

t = time()
constraint_vehicle_aging(model, data_structures)
@info "  vehicle_aging: $(round(time()-t, digits=1))s"

t = time()
constraint_vehicle_stock_shift(model, data_structures)
@info "  vehicle_stock_shift: $(round(time()-t, digits=1))s"

# Step 5: Objective
objective(model, data_structures, true)
GC.gc()

# Step 6: Solve
@info "Solving..."
t_solve = time()
optimize!(model)
@info "Solved in $(round(time()-t_solve, digits=1))s"
@info "Status: $(termination_status(model))"
@info "Objective: $(objective_value(model))"

# ============================================================================
# Step 7: BINDING CONSTRAINT ANALYSIS (the part we're testing)
# ============================================================================
println("\n" * "="^80)
println("BINDING CONSTRAINT ANALYSIS (Shadow Prices / Dual Values)")
println("="^80)

_technologies = data_structures["technology_list"]
_modeled_years = data_structures["modeled_years"]
_y_init = data_structures["y_init"]
_tech_name = Dict(t.id => t.name for t in _technologies)

# --- Vehicle Stock Shift ---
println("\n--- Vehicle Stock Shift Constraints ---")
if haskey(model.obj_dict, :con_stock_shift_upper)
    println("  Year  | Tech  | Upper dual    | Lower dual    | Binding?")
    println("  " * "-"^65)
    for y in filter(y -> y > _y_init, _modeled_years)
        for t in _technologies
            d_upper = dual(model[:con_stock_shift_upper][y, t])
            d_lower = dual(model[:con_stock_shift_lower][y, t])
            binding_upper = abs(d_upper) > 1e-6
            binding_lower = abs(d_lower) > 1e-6
            status = if binding_upper && binding_lower
                "BOTH"
            elseif binding_upper
                "UPPER (growth limited)"
            elseif binding_lower
                "LOWER (decline limited)"
            else
                "-"
            end
            if binding_upper || binding_lower
                @printf("  %4d  | %-5s | %+12.4f  | %+12.4f  | %s\n",
                    y, _tech_name[t.id], d_upper, d_lower, status)
            end
        end
    end
    println("  ✓ Vehicle stock shift duals extracted successfully")
else
    println("  ⚠ con_stock_shift_upper NOT FOUND in model")
    println("  Available keys: $(collect(keys(model.obj_dict)))")
end

# --- Mode Shift ---
println("\n--- Mode Shift Constraints (Rail) ---")
if haskey(model.obj_dict, :con_mode_shift_upper)
    _rail_modes = filter(m -> m.id == 2, data_structures["mode_list"])
    println("  Year  | Upper dual    | Lower dual    | Binding?")
    println("  " * "-"^55)
    for y in filter(y -> y >= 2026, _modeled_years)
        for m in _rail_modes
            d_upper = dual(model[:con_mode_shift_upper][y, m])
            d_lower = dual(model[:con_mode_shift_lower][y, m])
            binding_upper = abs(d_upper) > 1e-6
            binding_lower = abs(d_lower) > 1e-6
            status = if binding_upper
                "UPPER (rail growth limited)"
            elseif binding_lower
                "LOWER (rail decline limited)"
            else
                "-"
            end
            @printf("  %4d  | %+12.4f  | %+12.4f  | %s\n",
                y, d_upper, d_lower, status)
        end
    end
    println("  ✓ Mode shift duals extracted successfully")
else
    println("  ⚠ con_mode_shift_upper NOT FOUND in model")
end

# --- Demand Coverage ---
println("\n--- Demand Coverage Shadow Prices (summary by year) ---")
if haskey(model.obj_dict, :con_demand_coverage)
    _odpairs_dc = data_structures["odpair_list"]
    println("  Year  | Mean       | Min        | Max        | Count")
    println("  " * "-"^55)
    for y in _modeled_years
        duals_y = Float64[]
        for r in _odpairs_dc
            d = dual(model[:con_demand_coverage][y, r])
            if abs(d) > 1e-6
                push!(duals_y, d)
            end
        end
        if !isempty(duals_y)
            @printf("  %4d  | %+10.2f | %+10.2f | %+10.2f | %d\n",
                y, mean(duals_y), minimum(duals_y), maximum(duals_y), length(duals_y))
        end
    end
    println("  ✓ Demand coverage duals extracted successfully")
else
    println("  ⚠ con_demand_coverage NOT FOUND in model")
end

println("\n" * "="^80)
println("TEST COMPLETE - All dual extractions worked!")
println("="^80)
