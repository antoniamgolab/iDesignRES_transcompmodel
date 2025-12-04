using YAML, JuMP, Gurobi, Printf, ProgressMeter

include(joinpath(@__DIR__, "../../src/TransComp.jl"))

using .TransComp
using Dates

# ============================================================================
# CONFIGURATION: Specify which input files to run
# ============================================================================

# List of YAML input files to process (relative to the data/ directory)
INPUT_FILES = [
    #"input_rq2_undershoot_baseline_20251114_corr.yaml",
    # Add more files here as needed
    # "input_rq2_scenario_2.yaml",
    # "input_rq2_scenario_3.yaml",
    "input_rq2_baseline_20250906_ES213_45pct.yaml",
    "input_rq2_baseline_20250906_ES213_15pct.yaml",
    # "input_rq2_baseline_20250906.yaml"
]

# Optional: Custom case name prefix (leave empty to use default timestamp)
CASE_NAME_PREFIX = "cs_rq2"  # Will create: cs_rq2_2025-11-22_10-30-45

# ============================================================================

script_dir = @__DIR__

println("\n" * "="^80)
println("Running basque_cs_rq2 for multiple input files")
println("="^80)
println("Total files to process: $(length(INPUT_FILES))\n")

# Loop through each input file
for (file_idx, input_filename) in enumerate(INPUT_FILES)
    println("\n" * "─"^80)
    println("Processing file $file_idx of $(length(INPUT_FILES)): $input_filename")
    println("─"^80)

    # Construct full path to input file
    yaml_file_path = normpath(joinpath(@__DIR__, "data", input_filename))
    println("Constructed file path: $yaml_file_path")

    # Check if file exists
    if !isfile(yaml_file_path)
        @warn "File not found: $yaml_file_path - Skipping..."
        continue
    end

    # Generate case name with timestamp
    timestamp = Dates.format(now(), "yyyy-mm-dd_HH-MM-SS")
    case = isempty(CASE_NAME_PREFIX) ? "cs_$timestamp" : "$(CASE_NAME_PREFIX)_$timestamp"

    println("Case name: $case")

    try
        # -------- Initialize model --------
        @info "Initialization ..."
        data_dict = get_input_data(yaml_file_path)
        data_structures = parse_data(data_dict)
        model, data_structures = create_model(data_structures, case)
        @info "Model created successfully"

        # -------- Objective --------
        objective(model, data_structures, true)
        @info "Objective function added successfully"

        # -------- Constraints --------
        constraint_to_fast_charging(model, data_structures)
        @info "Constraint for fueling infrastructure expansion and shift created successfully"

        constraint_slow_fast_expansion(model, data_structures)
        @info "Constraint for slow and fast expansion created successfully"

        constraint_trip_ratio(model, data_structures)
        @info "Constraint for trip ratio created successfully"

        constraint_maximum_fueling_infrastructure_by_year(model, data_structures)
        constraint_maximum_fueling_infrastructure(model, data_structures)
        @info "Constraint for maximum fueling infrastructure created successfully"

        constraint_monetary_budget(model, data_structures)
        @info "Policy related constraints created successfully"

        constraint_fueling_infrastructure(model, data_structures)

        constraint_demand_coverage(model, data_structures)
        @info "Constraint for demand coverage created successfully"

        constraint_vehicle_sizing(model, data_structures)
        @info "Constraint for vehicle stock sizing created successfully"

        constraint_vehicle_aging(model, data_structures)
        @info "Constraint for vehicle aging created successfully"

        constraint_fueling_demand(model, data_structures)
        @info "Constraint for fueling demand created successfully"

        constraint_vehicle_stock_shift(model, data_structures)
        @info "Constraint for vehicle stock shift created successfully"

        constraint_vehicle_stock_shift_vehicle_type(model, data_structures)
        @info "Constraint for vehicle stock shift by vehicle type created successfully"

        constraint_market_share(model, data_structures)
        @info "Constraint for market share created successfully"

        # -------- Alternative constraints --------
        if data_structures["detour_time_reduction_list"] != []
            constraint_def_n_fueling(model, data_structures)
            @info "Constraint for VOT and detour time created successfully"
        end

        @info "Constraints created successfully"

        # -------- Solver settings --------
        set_optimizer_attribute(model, "Presolve", 2)
        set_optimizer_attribute(model, "MIPFocus", 1)
        set_optimizer_attribute(model, "Cuts", 3)
        set_optimizer_attribute(model, "MIPGap", 0.0001)
        set_optimizer_attribute(model, "NumericFocus", 1)
        set_optimizer_attribute(model, "Heuristics", 1)
        set_optimizer_attribute(model, "PreSparsify", 0)
        set_optimizer_attribute(model, "FeasibilityTol", 1e-3)
        set_optimizer_attribute(model, "Threads", 64)
        set_optimizer_attribute(model, "TimeLimit", 3600 * 30)
        set_optimizer_attribute(model, "PreSOS1BigM", 0)
        set_optimizer_attribute(model, "ScaleFlag", 2)

        # -------- Solve --------
        println("\n" * "▶"^40)
        println("Starting optimization for: $input_filename")
        println("▶"^40)

        optimize!(model)
        solution_summary(model)

        # -------- Save results --------
        results_file_path = normpath(joinpath(@__DIR__, "results/"))
        save_results(model, case, data_structures, true, results_file_path)

        @info "Results saved successfully for $input_filename"
        @info "Model solved successfully for $input_filename"

        println("\n" * "✓"^40)
        println("Completed: $input_filename (file $file_idx of $(length(INPUT_FILES)))")
        println("✓"^40)

    catch e
        @error "Failed to process $input_filename" exception=(e, catch_backtrace())
        println("\n" * "✗"^40)
        println("FAILED: $input_filename")
        println("Error: $e")
        println("✗"^40)

        # Continue with next file instead of stopping
        continue
    end

    # Add a small delay between runs to allow system cleanup
    if file_idx < length(INPUT_FILES)
        println("\nPreparing for next file...")
        sleep(2)
    end
end

println("\n" * "="^80)
println("All files processed!")
println("Total files attempted: $(length(INPUT_FILES))")
println("="^80)
