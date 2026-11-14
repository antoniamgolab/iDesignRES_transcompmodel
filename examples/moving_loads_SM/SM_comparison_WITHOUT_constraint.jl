"""
SM_comparison_WITHOUT_constraint.jl - Baseline run WITHOUT constraint_charging_at_breaks_only

This script runs the model WITHOUT the charging-at-breaks constraint for comparison.
"""

using Pkg
Pkg.activate(joinpath(@__DIR__, "../.."))  # Activate the project environment

using YAML, JuMP, Gurobi, Printf, ProgressMeter, Dates

include(joinpath(@__DIR__, "../../src/TransComp.jl"))
using .TransComp

# ============================================================================
# CONFIGURATION
# ============================================================================

case_folder = "case_20251212_164653"
case_label = "BASELINE: Without charging-at-breaks constraint (ICCT diesel price)"

# Variables to include in the model
relevant_vars = ["f", "h", "h_plus", "h_exist", "h_minus", "s", "q_fuel_infr_plus", "soc", "travel_time", "extra_break_time"]

# ============================================================================
# MAIN SCRIPT
# ============================================================================

@info "="^80
@info "BASELINE RUN: WITHOUT constraint_charging_at_breaks_only"
@info "Case: $case_folder"
@info "="^80

case_start_time = time()

# ================================================================
# Step 1: Setup paths
# ================================================================
script_dir = @__DIR__
input_path = joinpath(script_dir, "input_data", case_folder)

if !isdir(input_path)
    error("Input folder not found: $input_path")
end

@info "Input path: $input_path"

# Generate output case name with timestamp
timestamp = Dates.format(now(), "yyyy-mm-dd_HH-MM-SS")
case_name = "comparison_WITHOUT_constraint_$timestamp"

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

# Check mandatory breaks data
if haskey(data_structures, "mandatory_break_list")
    mb_list = data_structures["mandatory_break_list"]
    @info "  Found $(length(mb_list)) mandatory breaks"
    paths_with_breaks = Set(mb.path_id for mb in mb_list)
    @info "  Paths with mandatory breaks: $(length(paths_with_breaks))"
else
    @warn "No mandatory breaks data found!"
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
@info "Memory after model creation: $(round(Sys.free_memory()/1024^3, digits=2)) GB free"
@info "Number of variables: $(num_variables(model))"

# ================================================================
# Step 4: Configure solver
# ================================================================
@info "Step 3.5/5: Configuring solver parameters..."
set_optimizer_attribute(model, "Method", 2)           # Barrier method
set_optimizer_attribute(model, "MIPFocus", 1)         # Focus on feasibility
set_optimizer_attribute(model, "Cuts", 1)             # Conservative cuts
set_optimizer_attribute(model, "MIPGap", 0.01)        # 1% gap
set_optimizer_attribute(model, "NumericFocus", 3)     # Maximum numerical precision
set_optimizer_attribute(model, "ScaleFlag", 2)        # Aggressive auto-scaling
set_optimizer_attribute(model, "FeasibilityTol", 1e-5)
set_optimizer_attribute(model, "OptimalityTol", 1e-5)
set_optimizer_attribute(model, "IntFeasTol", 1e-4)
set_optimizer_attribute(model, "Crossover", 0)        # Skip crossover
set_optimizer_attribute(model, "BarConvTol", 1e-6)    # Faster convergence
@info "✓ Solver configured"

# ================================================================
# Step 5: Add constraints - NO charging_at_breaks_only constraint
# ================================================================
@info "Step 4/5: Adding constraints..."
@info ">>> NOTE: NOT adding constraint_charging_at_breaks_only <<<"
t_constraints_start = time()

# Mandatory breaks
t_start = time()
constraint_mandatory_breaks(model, data_structures)
t_mandatory_breaks = time() - t_start
@info "✓ Mandatory breaks constraint added in $(round(t_mandatory_breaks, digits=2))s"

# *** SKIPPING constraint_charging_at_breaks_only ***
@info "⊘ SKIPPING constraint_charging_at_breaks_only (baseline run)"

# Fueling infrastructure constraints
t_start = time()
constraint_fueling_infrastructure(model, data_structures)
t_fueling_infra = time() - t_start
@info "✓ Fueling infrastructure constraint added in $(round(t_fueling_infra, digits=2))s"

t_start = time()
constraint_fueling_infrastructure_expansion_shift(model, data_structures)
t_fueling_infra_expansion_shift = time() - t_start
@info "✓ Fueling infrastructure expansion shift constraint added in $(round(t_fueling_infra_expansion_shift, digits=2))s"

# BEV-specific constraints
# NOTE: Enabling SOC tracking - no initial BEVs, so should be feasible
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

# Mode shift constraints
t_start = time()
constraint_mode_shift(model, data_structures)
t_mode_shift = time() - t_start
@info "✓ Mode shift constraint added in $(round(t_mode_shift, digits=2))s"

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

t_constraints = time() - t_constraints_start
@info "Total constraint time: $(round(t_constraints, digits=2))s"

# ================================================================
# Step 6: Add objective function
# ================================================================
@info "Step 4.5/5: Adding objective..."
t_start = time()
objective(model, data_structures, false)
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
# Step 8: Check results
# ================================================================
@info "="^80
@info "RESULTS (BASELINE - WITHOUT constraint)"
@info "="^80
@info "Termination status: $(termination_status(model))"

if termination_status(model) == MOI.OPTIMAL || termination_status(model) == MOI.LOCALLY_SOLVED
    @info "Objective value: $(objective_value(model))"

    # Save results
    @info "Saving results to file..."
    results_file_path = normpath(joinpath(script_dir, "results", "comparison_charging_constraint"))
    if !isdir(results_file_path)
        mkpath(results_file_path)
    end
    save_results(model, case_name, data_structures, true, results_file_path, "comparison_WITHOUT")
    @info "✓ Results saved to: $results_file_path"
elseif termination_status(model) == MOI.INFEASIBLE
    @warn "Model is INFEASIBLE!"
    @info "Computing IIS (Irreducible Infeasible Subsystem)..."
    compute_conflict!(model)

    @info "Conflicting constraints:"
    for (F, S) in list_of_constraint_types(model)
        for ci in all_constraints(model, F, S)
            if MOI.get(model, MOI.ConstraintConflictStatus(), ci) == MOI.IN_CONFLICT
                @info "  $(ci)"
            end
        end
    end
else
    @warn "Termination status: $(termination_status(model))"
end

case_elapsed = time() - case_start_time

@info "="^80
@info "BASELINE RUN COMPLETE (WITHOUT constraint)"
@info "  Total time: $(round(case_elapsed/60, digits=2)) minutes"
@info "="^80
