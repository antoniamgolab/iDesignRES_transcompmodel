using YAML, JuMP, Gurobi, Printf, ProgressMeter

include(joinpath(@__DIR__, "../../src/TransComp.jl"))

# reading input data
# Get the path to the YAML file

using .TransComp

script_dir = @__DIR__   # Directory of the current script
# folder = "case_10k_test"  # 10K TEST: 10,000 OD-pairs for performance testing
# folder = "case_20251016_202612"  # 10K TEST: 10,000 OD-pairs - TOO LARGE without optimizations
# folder = "case_20251017_082948"  # 100 OD-pairs with corrected formula - TESTING Strategy 1
# folder = "case_20251016_152355"  # TEST CASE: 100 OD-pairs >= 360km (mandatory breaks guaranteed)
# folder = "sm_nuts3_complete"  # FULL CASE: All OD-pairs (uncomment to use full dataset)
folder = "case_20251017_105556"  # NUTS-2 aggregated with FIXED mandatory breaks (360km + cross-border)
input_path = joinpath(@__DIR__, "input_data", folder)  # Use the actual case directory name
println("Constructed file path: $input_path")

relevant_vars = ["f", "h", "h_plus", "h_exist", "h_minus", "s", "q_fuel_infr_plus", "soc", "travel_time", "extra_break_time"]
using Dates

timestamp = Dates.format(now(), "yyyy-mm-dd_HH-MM-SS")
case = "$(folder)_cs_$timestamp"

file = input_path
@info file


# reading input data and initializing the model
@info "=" ^ 80
@info "Starting model run at $(Dates.format(now(), "yyyy-mm-dd HH:MM:SS"))"
@info "=" ^ 80

# Timing: Read input datarg
@info "Step 1/5: Reading input data..."
t_start = time()
data_dict = get_input_data(file)
t_read = time() - t_start
@info "✓ Input data loaded in $(round(t_read, digits=2)) seconds"

# Timing: Parse data structures
@info "Step 2/5: Parsing data structures..."
t_start = time()
data_structures = parse_data(data_dict)
t_parse = time() - t_start
@info "✓ Data parsed in $(round(t_parse, digits=2)) seconds"

# Timing: Create model
@info "Step 3/5: Creating optimization model..."
t_start = time()
# Only create the f variable - that's all we need for constraint_demand_coverage
# This dramatically reduces model size and speeds up everything
model, data_structures = create_model(data_structures, case, include_vars=relevant_vars)
t_create = time() - t_start
@info "✓ Model created in $(round(t_create, digits=2)) seconds"

# Configure Gurobi solver for optimal performance
# These settings balance solution quality with solve speed
@info "Step 3.5/5: Configuring solver parameters..."
# set_optimizer_attribute(model, "Presolve", 2)           # Aggressive presolve reduces problem size
# set_optimizer_attribute(model, "MIPFocus", 1)           # Focus on finding good feasible solutions
# set_optimizer_attribute(model, "Heuristics", 0.1)       # Moderate heuristics (default is 0.05)
# set_optimizer_attribute(model, "NumericFocus", 1)       # Enhanced numerical stability
set_optimizer_attribute(model, "TimeLimit", 3600)       # 1 hour time limit
# Note: MIPGap, Cuts, and other parameters left at default for faster convergence
# Note: Threads will use Gurobi's default (all available cores)
@info "✓ Solver parameters configured (balanced for speed)"

# ============================================================================
# CONSTRAINT SETUP - Organized by dependency and logical grouping
# ============================================================================
t_start = time()
constraint_mandatory_breaks(model, data_structures)
t_mandatory_breaks = time() - t_start
@info "✓ Mandatory breaks constraint added in $(round(t_mandatory_breaks, digits=2)) seconds"

# --- Core Flow and Demand Constraints ---
@info "Step 4.1/5: Adding core demand coverage constraint..."
t_start = time()
constraint_demand_coverage(model, data_structures)
t_constraints = time() - t_start
@info "✓ Demand coverage constraint added in $(round(t_constraints, digits=2)) seconds"

# --- Vehicle Fleet Constraints ---
@info "Step 4.2/5: Adding vehicle fleet constraints..."
t_start = time()
constraint_vehicle_sizing(model, data_structures)
t_vehicle_sizing = time() - t_start
@info "✓ Vehicle sizing constraint added in $(round(t_vehicle_sizing, digits=2)) seconds"

t_start = time()
constraint_vehicle_aging(model, data_structures)
t_vehicle_aging = time() - t_start
@info "✓ Vehicle aging constraint added in $(round(t_vehicle_aging, digits=2)) seconds"

t_start = time()
constraint_vehicle_stock_shift(model, data_structures)
t_vehicle_stock_shift = time() - t_start
@info "✓ Vehicle stock shift constraint added in $(round(t_vehicle_stock_shift, digits=2)) seconds"

# --- Fueling Infrastructure Constraints ---
@info "Step 4.3/5: Adding fueling infrastructure constraints..."
t_start = time()
constraint_fueling_demand(model, data_structures)
t_fueling_demand = time() - t_start
@info "✓ Fueling demand constraint added in $(round(t_fueling_demand, digits=2)) seconds"

t_start = time()
constraint_fueling_infrastructure(model, data_structures)
t_fueling_infra = time() - t_start
@info "✓ Fueling infrastructure constraint added in $(round(t_fueling_infra, digits=2)) seconds"

t_start = time()
constraint_fueling_infrastructure_expansion_shift(model, data_structures)
t_fueling_infra_expansion_shift = time() - t_start
@info "✓ Fueling infrastructure expansion shift constraint added in $(round(t_fueling_infra_expansion_shift, digits=2)) seconds"

# --- BEV-Specific Constraints (SOC, Travel Time, Mandatory Breaks) ---
@info "Step 4.4/5: Adding BEV-specific constraints..."
t_start = time()
constraint_soc_track(model, data_structures)
t_soc_track = time() - t_start
@info "✓ State of charge tracking constraints added in $(round(t_soc_track, digits=2)) seconds"

t_start = time()
constraint_soc_max(model, data_structures)
t_soc = time() - t_start
@info "✓ State of charge max constraints added in $(round(t_soc, digits=2)) seconds"

t_start = time()
constraint_travel_time_track(model, data_structures)
t_travel_time_track = time() - t_start
@info "✓ Travel time tracking constraint added in $(round(t_travel_time_track, digits=2)) seconds"


# Timing: Add objective
@info "Step 4.5/5: Adding objective..."
t_obj_start = time()
objective(model, data_structures, false)
t_obj = time() - t_obj_start
@info "✓ Objective added in $(round(t_obj, digits=2)) seconds"

# Timing: Optimize
@info "Step 5/5: Solving optimization problem..."
t_start = time()
optimize!(model)
t_optimize = time() - t_start
@info "✓ Optimization complete in $(round(t_optimize, digits=2)) seconds"

# Run diagnostics
include("check_soc_simple.jl")
include("check_travel_time_verbose.jl")  # Verbose version to identify which check fails
include("check_mandatory_breaks.jl")
# include("check_spatial_flexibility.jl")  # Removed - constraint not in use
# Summary
@info "=" ^ 80
@info "TIMING SUMMARY:"
@info "  Data loading:         $(round(t_read, digits=2))s"
@info "  Data parsing:         $(round(t_parse, digits=2))s"
@info "  Model creation:       $(round(t_create, digits=2))s"
@info "  Constraint setup:"
@info "    - Demand coverage:  $(round(t_constraints, digits=2))s"
@info "    - Vehicle fleet:    $(round(t_vehicle_sizing + t_vehicle_aging + t_vehicle_stock_shift, digits=2))s"
@info "    - Fuel infra:       $(round(t_fueling_demand + t_fueling_infra + t_fueling_infra_expansion_shift, digits=2))s"
@info "    - BEV constraints:  $(round(t_soc_track + t_soc + t_travel_time_track + t_mandatory_breaks, digits=2))s"
@info "  Objective function:   $(round(t_obj, digits=2))s"
@info "  Optimization:         $(round(t_optimize, digits=2))s"
t_constraint_total = t_constraints + t_vehicle_sizing + t_vehicle_aging + t_vehicle_stock_shift +
                     t_fueling_demand + t_fueling_infra + t_fueling_infra_expansion_shift +
                     t_soc_track + t_soc + t_travel_time_track + t_mandatory_breaks
total_time = t_read + t_parse + t_create + t_constraint_total + t_obj + t_optimize
@info "  TOTAL TIME:           $(round(total_time, digits=2))s ($(round(total_time/60, digits=2)) minutes)"
@info "=" ^ 80

solution_summary(model)

# Save results - only saves variables that were actually defined (in this case, only 'f')
@info "Saving results to file..."
results_file_path = normpath(joinpath(@__DIR__, "results/", folder))
if !isdir(results_file_path)
    mkpath(results_file_path)
end
save_results(model, case, data_structures, true, results_file_path, folder)
@info "✓ Results saved successfully"