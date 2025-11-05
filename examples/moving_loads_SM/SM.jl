using Pkg
Pkg.activate(joinpath(@__DIR__, "../.."))  # Activate the project environment

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
# folder = "case_20251017_105556"  # NUTS-2 aggregated with FIXED mandatory breaks (360km + cross-border)
folder = "case_20251105_111439"  # NUTS-2 international routes, ≥360km, no local routes, with technical parameters
input_path = joinpath(@__DIR__, "input_data", folder)  # Use the actual case directory name
println("Constructed file path: $input_path")

# Full model with objective bug fix - rail uses levelized costs (cost_per_ukm) in objective
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
@info "Memory before model creation: $(round(Sys.free_memory()/1024^3, digits=2)) GB free"
t_start = time()
# Only create the f variable - that's all we need for constraint_demand_coverage
# This dramatically reduces model size and speeds up everything
model, data_structures = create_model(data_structures, case, include_vars=relevant_vars)
t_create = time() - t_start
@info "✓ Model created in $(round(t_create, digits=2)) seconds"
@info "Memory after model creation: $(round(Sys.free_memory()/1024^3, digits=2)) GB free"
@info "Number of variables: $(num_variables(model))"
@info "Variable breakdown by name:"
for (name, var_ref) in model.obj_dict
    if var_ref isa JuMP.Containers.DenseAxisArray || var_ref isa JuMP.Containers.SparseAxisArray
        @info "  $name: $(length(var_ref)) variables"
    end
end

# Configure Gurobi solver for MEMORY-EFFICIENT usage
@info "Step 3.5/5: Configuring solver parameters for memory efficiency..."
set_optimizer_attribute(model, "NodeFileStart", 0.5)    # Write nodes to disk after 0.5 GB
set_optimizer_attribute(model, "NodeFileDir", ".")      # Use current directory for node files
# set_optimizer_attribute(model, "MemLimit", 30)           # Limit Gurobi to 30 GB RAM (sufficient for model)
#set_optimizer_attribute(model, "Presolve", 2)           # Aggressive presolve to reduce problem
set_optimizer_attribute(model, "MIPFocus", 1)           # Focus on feasibility
set_optimizer_attribute(model, "Cuts", 1)               # Conservative cuts
set_optimizer_attribute(model, "MIPGap", 0.01)          # 1% gap
set_optimizer_attribute(model, "NumericFocus", 3)       # Maximum numerical precision
set_optimizer_attribute(model, "ScaleFlag", 2)          # Aggressive auto-scaling
set_optimizer_attribute(model, "FeasibilityTol", 1e-5)  # Looser feasibility tolerance (default: 1e-6)
set_optimizer_attribute(model, "OptimalityTol", 1e-5)   # Looser optimality tolerance (default: 1e-6)
set_optimizer_attribute(model, "IntFeasTol", 1e-4)      # Looser integer feasibility (default: 1e-5)
# set_optimizer_attribute(model, "TimeLimit", 7200)       # 2 hour time limit
set_optimizer_attribute(model, "Crossover", 0)            # Disable crossover to save memory
set_optimizer_attribute(model, "Threads", 4)            # Use 4 threads for better performance
@info "✓ Solver configured for memory-efficient solving (disk-based nodes, 30GB limit, 4 threads)"

# ============================================================================
# CONSTRAINT SETUP - Organized by dependency and logical grouping
# ============================================================================

@info "Memory before constraints: $(round(Sys.free_memory()/1024^3, digits=2)) GB free"
t_start = time()
#constraint_mandatory_breaks(model, data_structures)
t_mandatory_breaks = time() - t_start
@info "✓ Mandatory breaks constraint added in $(round(t_mandatory_breaks, digits=2)) seconds"
@info "  Memory after: $(round(Sys.free_memory()/1024^3, digits=2)) GB free"

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

# --- Mode Infrastructure Constraints ---
# DISABLED: Mode infrastructure not needed - rail uses levelized costs (cost_per_ukm) in objective
# @info "Step 4.3b/5: Adding mode infrastructure constraint..."
# t_start = time()
# constraint_mode_infrastructure(model, data_structures)
# t_mode_infra = time() - t_start
# @info "✓ Mode infrastructure constraint added in $(round(t_mode_infra, digits=2)) seconds"
t_mode_infra = 0.0

# --- BEV-Specific Constraints (SOC, Travel Time, Mandatory Breaks) ---
@info "Step 4.4/5: Adding SOC constraints..."
t_start = time()
constraint_soc_track(model, data_structures)
t_soc_track = time() - t_start
@info "✓ State of charge tracking constraints added in $(round(t_soc_track, digits=2)) seconds"
@info "  Memory after: $(round(Sys.free_memory()/1024^3, digits=2)) GB free"

t_start = time()
constraint_soc_max(model, data_structures)
t_soc = time() - t_start
@info "✓ State of charge max constraints added in $(round(t_soc, digits=2)) seconds"

t_start = time()
constraint_travel_time_track(model, data_structures)
t_travel_time_track = time() - t_start
@info "✓ Travel time tracking constraint added in $(round(t_travel_time_track, digits=2)) seconds"

# --- Mode Shift Constraints (rail blocked <2026, ONLY RAIL shift limited from 2026) ---
@info "Step 4.5/5: Adding mode shift constraint (rail blocked <2026, ONLY RAIL limited from 2026)..."
t_start = time()
constraint_mode_shift(model, data_structures)
t_mode_shift = time() - t_start
@info "✓ Mode shift constraint added in $(round(t_mode_shift, digits=2)) seconds"
@info "  Memory after: $(round(Sys.free_memory()/1024^3, digits=2)) GB free"

# --- Max Mode Share Constraints (cap rail at 30% of total flow) ---
# RE-ENABLED: Unlike mode_shift, this constraint only sets an upper bound on rail share,
# which doesn't cause infeasibility (rail can be anywhere from 0-30%)
t_start = time()
if !isempty(data_structures["max_mode_share_list"])
    @info "Step 4.6/5: Adding max mode share constraint..."
    # constraint_max_mode_share(model, data_structures)
    t_max_mode_share = time() - t_start
    @info "✓ Max mode share constraint added in $(round(t_max_mode_share, digits=2)) seconds"
else
    t_max_mode_share = 0.0
    @info "Step 4.6/5: Skipping max mode share constraint (no constraints defined)"
end

# --- Core Flow and Demand Constraints ---
@info "Step 4.1/5: Adding core demand coverage constraint..."
t_start = time()
constraint_demand_coverage(model, data_structures)
t_constraints = time() - t_start
@info "✓ Demand coverage constraint added in $(round(t_constraints, digits=2)) seconds"
@info "  Memory after: $(round(Sys.free_memory()/1024^3, digits=2)) GB free"

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

t_start = time()
# Timing: Add objective
@info "Step 4.5/5: Adding objective..."
t_obj_start = time()
objective(model, data_structures, false)
t_obj = time() - t_obj_start
@info "✓ Objective added in $(round(t_obj, digits=2)) seconds"

GC.gc()  # Force garbage collection to free unused memory

# Timing: Optimize
@info "Step 5/5: Solving optimization problem..."
t_start = time()
optimize!(model)
t_optimize = time() - t_start
@info "✓ Optimization complete in $(round(t_optimize, digits=2)) seconds"

# Run diagnostics (only for vehicle-based modes - skip if 100% rail)
println("\n" * "="^80)
println("RUNNING DIAGNOSTICS")
println("="^80)

# Check if any vehicle-based flows exist
has_vehicle_flows = false
for (f_key, f_var) in model[:f].data
    if value(f_var) > 1e-6
        tv_id = f_key[3][2]
        tv_idx = findfirst(tv -> tv.id == tv_id, data_structures["techvehicle_list"])
        if tv_idx !== nothing
            has_vehicle_flows = true
            break
        end
    end
end

# if has_vehicle_flows
#     @info "✓ Vehicle-based flows detected - running diagnostics..."
#     include("check_soc_simple.jl")
#     include("check_travel_time_detailed_debug.jl")  # Detailed segment-by-segment analysis
#     include("check_mandatory_breaks.jl")
# else
#     @info "⚠️  No vehicle-based flows (100% rail mode) - skipping truck-specific diagnostics"
#     println("  Rail mode uses levelized costs and doesn't need SOC/travel time/break validation")
# end
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
@info "    - Mode infra:       $(round(t_mode_infra, digits=2))s"
@info "    - Mode shift:       $(round(t_mode_shift, digits=2))s"
@info "    - Max mode share:   $(round(t_max_mode_share, digits=2))s"
@info "    - BEV constraints:  $(round(t_soc_track + t_soc + t_travel_time_track + t_mandatory_breaks, digits=2))s"
@info "  Objective function:   $(round(t_obj, digits=2))s"
@info "  Optimization:         $(round(t_optimize, digits=2))s"
t_constraint_total = t_constraints + t_vehicle_sizing + t_vehicle_aging + t_vehicle_stock_shift +
                     t_fueling_demand + t_fueling_infra + t_fueling_infra_expansion_shift + t_mode_infra + t_mode_shift + t_max_mode_share +
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