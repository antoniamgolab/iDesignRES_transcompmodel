using Pkg
Pkg.activate(joinpath(@__DIR__, "../.."))  # Activate the project environment

using YAML, JuMP, Gurobi, Printf, ProgressMeter

include(joinpath(@__DIR__, "../../src/TransComp.jl"))

using .TransComp
using Dates

# ============================================================================
# CONFIGURATION: List of cases to run
# ============================================================================

# Define all cases to run
case_folders = [
    "case_20251030_113213_var_var",      # Case 1: Variable electricity + Variable network
    "case_20251030_113248_var_uni",      # Case 2: Variable electricity + Uniform network
    "case_20251030_113325_uni_var",      # Case 3: Uniform electricity + Variable network
    "case_20251030_113500_uni_uni",      # Case 4: Uniform electricity + Uniform network
    "case_20251030_113642_var_var_rev",  # Case 5: Variable electricity (REVERSED) + Variable network
]

# Variables to include in the model
relevant_vars = ["f", "h", "h_plus", "h_exist", "h_minus", "s", "q_fuel_infr_plus", "soc", "travel_time", "extra_break_time"]

# ============================================================================

# FUNCTION: Run a single case
# ============================================================================

function run_single_case(folder::String, relevant_vars::Vector{String})
    """
    Run optimization for a single case.
    Returns nothing to ensure all references are dropped.
    """

    @info "=" ^ 80
    @info "STARTING CASE: $folder"
    @info "=" ^ 80

    script_dir = @__DIR__
    input_path = joinpath(script_dir, "input_data", folder)
    println("Input path: $input_path")

    timestamp = Dates.format(now(), "yyyy-mm-dd_HH-MM-SS")
    case = "$(folder)_cs_$timestamp"

    # ========================================================================
    # Step 1: Read input data
    # ========================================================================
    @info "Step 1/5: Reading input data..."
    @info "Memory before loading: $(round(Sys.free_memory()/1024^3, digits=2)) GB free"
    t_start = time()
    data_dict = get_input_data(input_path)
    t_read = time() - t_start
    @info "✓ Input data loaded in $(round(t_read, digits=2)) seconds"

    # ========================================================================
    # Step 2: Parse data structures
    # ========================================================================
    @info "Step 2/5: Parsing data structures..."
    t_start = time()
    data_structures = parse_data(data_dict)
    t_parse = time() - t_start
    @info "✓ Data parsed in $(round(t_parse, digits=2)) seconds"

    # Clear data_dict to free memory
    data_dict = nothing
    GC.gc()

    # ========================================================================
    # Step 3: Create model
    # ========================================================================
    @info "Step 3/5: Creating optimization model..."
    @info "Memory before model creation: $(round(Sys.free_memory()/1024^3, digits=2)) GB free"
    t_start = time()
    model, data_structures = create_model(data_structures, case, include_vars=relevant_vars)
    t_create = time() - t_start
    @info "✓ Model created in $(round(t_create, digits=2)) seconds"
    @info "Memory after model creation: $(round(Sys.free_memory()/1024^3, digits=2)) GB free"
    @info "Number of variables: $(num_variables(model))"

    # ========================================================================
    # Step 3.5: Configure solver
    # ========================================================================
    @info "Step 3.5/5: Configuring solver parameters..."
    set_optimizer_attribute(model, "NodeFileStart", 0.5)
    set_optimizer_attribute(model, "NodeFileDir", ".")
    set_optimizer_attribute(model, "Presolve", 2)
    set_optimizer_attribute(model, "MIPFocus", 1)
    set_optimizer_attribute(model, "Cuts", 1)
    set_optimizer_attribute(model, "MIPGap", 0.01)
    set_optimizer_attribute(model, "TimeLimit", 7200)
    set_optimizer_attribute(model, "Threads", 4)
    @info "✓ Solver configured"

    # ========================================================================
    # Step 4: Add constraints
    # ========================================================================
    @info "Step 4/5: Adding constraints..."
    @info "Memory before constraints: $(round(Sys.free_memory()/1024^3, digits=2)) GB free"

    t_start = time()
    constraint_vehicle_stock_shift(model, data_structures)
    t_vehicle_stock_shift = time() - t_start
    @info "✓ Vehicle stock shift: $(round(t_vehicle_stock_shift, digits=2))s"

    t_start = time()
    constraint_mandatory_breaks(model, data_structures)
    t_mandatory_breaks = time() - t_start
    @info "✓ Mandatory breaks: $(round(t_mandatory_breaks, digits=2))s"

    t_start = time()
    constraint_fueling_demand(model, data_structures)
    t_fueling_demand = time() - t_start
    @info "✓ Fueling demand: $(round(t_fueling_demand, digits=2))s"

    t_start = time()
    constraint_fueling_infrastructure(model, data_structures)
    t_fueling_infra = time() - t_start
    @info "✓ Fueling infrastructure: $(round(t_fueling_infra, digits=2))s"

    t_start = time()
    constraint_fueling_infrastructure_expansion_shift(model, data_structures)
    t_fueling_infra_expansion_shift = time() - t_start
    @info "✓ Fueling infrastructure expansion: $(round(t_fueling_infra_expansion_shift, digits=2))s"

    t_start = time()
    constraint_soc_track(model, data_structures)
    t_soc_track = time() - t_start
    @info "✓ SOC tracking: $(round(t_soc_track, digits=2))s"

    t_start = time()
    constraint_soc_max(model, data_structures)
    t_soc = time() - t_start
    @info "✓ SOC max: $(round(t_soc, digits=2))s"

    t_start = time()
    constraint_travel_time_track(model, data_structures)
    t_travel_time_track = time() - t_start
    @info "✓ Travel time tracking: $(round(t_travel_time_track, digits=2))s"

    t_start = time()
    constraint_mode_shift(model, data_structures)
    t_mode_shift = time() - t_start
    @info "✓ Mode shift: $(round(t_mode_shift, digits=2))s"

    t_start = time()
    if !isempty(data_structures["max_mode_share_list"])
        constraint_max_mode_share(model, data_structures)
        t_max_mode_share = time() - t_start
        @info "✓ Max mode share: $(round(t_max_mode_share, digits=2))s"
    else
        t_max_mode_share = 0.0
        @info "✓ Max mode share: skipped (no constraints)"
    end

    t_start = time()
    constraint_demand_coverage(model, data_structures)
    t_constraints = time() - t_start
    @info "✓ Demand coverage: $(round(t_constraints, digits=2))s"

    t_start = time()
    constraint_vehicle_sizing(model, data_structures)
    t_vehicle_sizing = time() - t_start
    @info "✓ Vehicle sizing: $(round(t_vehicle_sizing, digits=2))s"

    t_start = time()
    constraint_vehicle_aging(model, data_structures)
    t_vehicle_aging = time() - t_start
    @info "✓ Vehicle aging: $(round(t_vehicle_aging, digits=2))s"

    @info "Memory after constraints: $(round(Sys.free_memory()/1024^3, digits=2)) GB free"

    # ========================================================================
    # Step 4.5: Add objective
    # ========================================================================
    @info "Step 4.5/5: Adding objective..."
    t_obj_start = time()
    objective(model, data_structures, false)
    t_obj = time() - t_obj_start
    @info "✓ Objective added in $(round(t_obj, digits=2)) seconds"

    # Force garbage collection before optimization
    GC.gc()
    @info "Memory before optimization: $(round(Sys.free_memory()/1024^3, digits=2)) GB free"

    # ========================================================================
    # Step 5: Optimize
    # ========================================================================
    @info "Step 5/5: Solving optimization problem..."
    t_start = time()
    optimize!(model)
    t_optimize = time() - t_start
    @info "✓ Optimization complete in $(round(t_optimize, digits=2)) seconds"

    # ========================================================================
    # Run diagnostics
    # ========================================================================
    @info "Running diagnostics..."
    try
        include("check_soc_simple.jl")
        include("check_travel_time_detailed_debug.jl")
        include("check_mandatory_breaks.jl")
        @info "✓ Diagnostics completed"
    catch e
        @warn "Diagnostics failed (non-critical):" exception=(e, catch_backtrace())
    end

    # ========================================================================
    # Save results
    # ========================================================================
    solution_summary(model)

    @info "Saving results to file..."
    results_file_path = normpath(joinpath(@__DIR__, "results/", folder))
    if !isdir(results_file_path)
        mkpath(results_file_path)
    end
    save_results(model, case, data_structures, true, results_file_path, folder)
    @info "✓ Results saved successfully"

    # ========================================================================
    # Timing summary
    # ========================================================================
    @info "=" ^ 80
    @info "TIMING SUMMARY FOR $folder:"
    @info "  Data loading:         $(round(t_read, digits=2))s"
    @info "  Data parsing:         $(round(t_parse, digits=2))s"
    @info "  Model creation:       $(round(t_create, digits=2))s"
    @info "  Constraint setup:"
    @info "    - Demand coverage:  $(round(t_constraints, digits=2))s"
    @info "    - Vehicle fleet:    $(round(t_vehicle_sizing + t_vehicle_aging + t_vehicle_stock_shift, digits=2))s"
    @info "    - Fuel infra:       $(round(t_fueling_demand + t_fueling_infra + t_fueling_infra_expansion_shift, digits=2))s"
    @info "    - BEV constraints:  $(round(t_soc_track + t_soc + t_travel_time_track + t_mandatory_breaks, digits=2))s"
    @info "    - Mode shift:       $(round(t_mode_shift, digits=2))s"
    @info "    - Max mode share:   $(round(t_max_mode_share, digits=2))s"
    @info "  Objective function:   $(round(t_obj, digits=2))s"
    @info "  Optimization:         $(round(t_optimize, digits=2))s"
    t_constraint_total = t_constraints + t_vehicle_sizing + t_vehicle_aging + t_vehicle_stock_shift +
                         t_fueling_demand + t_fueling_infra + t_fueling_infra_expansion_shift +
                         t_soc_track + t_soc + t_travel_time_track + t_mandatory_breaks + t_mode_shift + t_max_mode_share
    total_time = t_read + t_parse + t_create + t_constraint_total + t_obj + t_optimize
    @info "  TOTAL TIME:           $(round(total_time, digits=2))s ($(round(total_time/60, digits=2)) minutes)"
    @info "=" ^ 80

    # ========================================================================
    # CRITICAL: Clear all variables to free memory
    # ========================================================================
    @info "Cleaning up memory..."
    model = nothing
    data_structures = nothing

    # Force aggressive garbage collection
    GC.gc()
    GC.gc()  # Call twice for thorough cleanup

    @info "Memory after cleanup: $(round(Sys.free_memory()/1024^3, digits=2)) GB free"
    @info "=" ^ 80
    @info "CASE COMPLETE: $folder"
    @info "=" ^ 80
    @info ""

    return nothing
end

# ============================================================================
# MAIN EXECUTION: Loop through all cases
# ============================================================================

@info "=" ^ 80
@info "MULTI-CASE OPTIMIZATION RUN"
@info "Starting at $(Dates.format(now(), "yyyy-mm-dd HH:MM:SS"))"
@info "Number of cases to run: $(length(case_folders))"
@info "=" ^ 80
@info ""

total_start_time = time()

for (i, folder) in enumerate(case_folders)
    @info ""
    @info "#" ^ 80
    @info "# CASE $i of $(length(case_folders)): $folder"
    @info "#" ^ 80
    @info ""

    case_start_time = time()

    try
        run_single_case(folder, relevant_vars)
        case_elapsed = time() - case_start_time
        @info "✓ Case $i completed successfully in $(round(case_elapsed/60, digits=2)) minutes"
    catch e
        @error "ERROR in case $i ($folder):" exception=(e, catch_backtrace())
        @warn "Continuing to next case..."
    end

    # Small pause between cases to allow system cleanup
    sleep(5)
end

total_elapsed = time() - total_start_time

@info ""
@info "=" ^ 80
@info "ALL CASES COMPLETE"
@info "Total execution time: $(round(total_elapsed/60, digits=2)) minutes ($(round(total_elapsed/3600, digits=2)) hours)"
@info "Completed at $(Dates.format(now(), "yyyy-mm-dd HH:MM:SS"))"
@info "=" ^ 80
