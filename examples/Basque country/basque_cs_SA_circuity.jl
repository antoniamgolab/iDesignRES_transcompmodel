using YAML, JuMP, Gurobi, Printf, ProgressMeter

include(joinpath(@__DIR__, "../../src/TransComp.jl"))

using .TransComp
using Dates

# Dictionary to store timing results for all files
timing_results = Dict{String, Dict{String, Float64}}()

# Define list of YAML files to run
yaml_files = [
    "data/td_ONENODE_balanced_expansion_24092025_Base.yaml",
    # "data/td_ONENODE_balanced_expansion_alpha_1_4_coarse_resolution.yaml",
    # "data/td_ONENODE_balanced_expansion_alpha_1_4_fine_resolution.yaml",
    # "data/td_ONENODE_concentrated_expansion_alpha_1_4_fine_resolution.yaml",
    # "data/td_ONENODE_concentrated_expansion_alpha_1_4_baseline_resolution.yaml",
    # "data/td_ONENODE_concentrated_expansion_alpha_1_4_coarse_resolution.yaml",
    # "data/td_ONENODE_distributed_expansion_alpha_1_4_fine_resolution.yaml",
    # "data/td_ONENODE_distributed_expansion_alpha_1_4_baseline_resolution.yaml",
    # "data/td_ONENODE_distributed_expansion_alpha_1_4_coarse_resolution.yaml",
    # "data/td_ONENODE_distributed_expansion_alpha_2_2_detour_reduction.yaml",
    # "data/td_ONENODE_distributed_expansion_alpha_2_4_detour_reduction.yaml",
    # "data/td_ONENODE_distributed_expansion_alpha_1_0_detour_reduction.yaml",
    # # "data/td_ONENODE_balanced_expansion_171125_alpha_1_2.yaml",
    # "data/td_ONENODE_distributed_expansion_alpha_1_2_detour_reduction.yaml",
    # "data/td_ONENODE_distributed_expansion_alpha_1_4_detour_reduction.yaml",
    # "data/td_ONENODE_distributed_expansion_alpha_1_6_detour_reduction.yaml",
    # "data/td_ONENODE_distributed_expansion_alpha_1_8_detour_reduction.yaml",
    # "data/td_ONENODE_distributed_expansion_alpha_2_0_detour_reduction.yaml",
    # Add more files here as needed
]

# Get script directory
script_dir = @__DIR__

# Loop through each YAML file
for (file_idx, yaml_file) in enumerate(yaml_files)
    println("\n" * "="^80)
    println("Processing file $file_idx of $(length(yaml_files))")
    println("="^80)

    # Construct full file path
    yaml_file_path = normpath(joinpath(@__DIR__, yaml_file))
    println("File path: $yaml_file_path")

    # Check if file exists
    if !isfile(yaml_file_path)
        @warn "File not found: $yaml_file_path - Skipping..."
        continue
    end

    # Create unique case name with timestamp and file identifier
    timestamp = Dates.format(now(), "yyyy-mm-dd_HH-MM-SS")
    file_name = splitext(basename(yaml_file))[1]  # Get filename without extension
    case = "cs_SA_$(file_name)_$timestamp"

    @info "Starting case: $case"

    try
        # Initialize timing dictionary for this file
        file_timing = Dict{String, Float64}()
        total_start = time()

        # Reading input data and initializing the model
        @info "Initialization ..."
        init_start = time()
        data_dict = get_input_data(yaml_file_path)
        data_structures = parse_data(data_dict)
        model, data_structures = create_model(data_structures, case)
        file_timing["initialization"] = time() - init_start
        @info "Model created successfully ($(round(file_timing["initialization"], digits=2))s)"

        # -------- constraints --------
        @info "Creating constraints ..."
        constraints_start = time()
        constraint_vot_dt(model, data_structures)

        constraint_to_fast_charging(model, data_structures)
        constraint_fueling_infrastructure_expansion_shift(model, data_structures)
        constraint_q_fuel_abs(model, data_structures)

        constraint_slow_fast_expansion(model, data_structures)
        @info "Constraint for slow and fast expansion created successfully"

        constraint_trip_ratio(model, data_structures)
        @info "Constraint for trip ratio created successfully"

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

        # ------- constraints (alternative) --------
        if data_structures["detour_time_reduction_list"] != []
            constraint_detour_time(model, data_structures)
            constraint_def_n_fueling(model, data_structures)
            constraint_sum_x(model, data_structures)
            @info "Constraint for VOT and detour time created successfully"
            constraint_n_fueling_upper_bound(model, data_structures)
            constraint_a(model, data_structures)
        end

        @info "Constraints created successfully"
        file_timing["constraints"] = time() - constraints_start
        @info "Constraints time: $(round(file_timing["constraints"], digits=2))s"

        # -------- objective --------
        objective_start = time()
        objective(model, data_structures, false)
        file_timing["objective"] = time() - objective_start
        @info "Objective function added successfully ($(round(file_timing["objective"], digits=2))s)"

        # -------- model solution and saving of results --------
        set_optimizer_attribute(model, "Presolve", 2)
        set_optimizer_attribute(model, "MIPFocus", 1)
        set_optimizer_attribute(model, "Cuts", 3)
        set_optimizer_attribute(model, "MIPGap", 0.00001)
        set_optimizer_attribute(model, "NumericFocus", 1)
        set_optimizer_attribute(model, "Heuristics", 1)
        set_optimizer_attribute(model, "PreSparsify", 0)
        set_optimizer_attribute(model, "FeasibilityTol", 1e-3)
        set_optimizer_attribute(model, "TimeLimit", 3600 * 30)
        set_optimizer_attribute(model, "PreSOS1BigM", 0)
        set_optimizer_attribute(model, "ScaleFlag", 2)

        println("Solving model for: $case")
        solve_start = time()
        optimize!(model)
        file_timing["solve"] = time() - solve_start
        solution_summary(model)
        @info "Solve time: $(round(file_timing["solve"], digits=2))s"

        # Save results
        save_start = time()
        results_file_path = normpath(joinpath(@__DIR__, "results/"))
        save_results(model, case, data_structures, true, results_file_path)
        file_timing["save_results"] = time() - save_start

        # Calculate total time
        file_timing["total"] = time() - total_start

        # Store timing results for this file
        timing_results[file_name] = file_timing

        @info "Results saved successfully for $case ($(round(file_timing["save_results"], digits=2))s)"
        @info "Total time for file $file_idx: $(round(file_timing["total"], digits=2))s"

    catch e
        @error "Error processing file: $yaml_file" exception=(e, catch_backtrace())
        println("Continuing to next file...")
        continue
    end

    println("\n")
end

println("\n" * "="^80)
println("Sensitivity analysis completed!")
println("Processed $(length(yaml_files)) files")
println("="^80)

# Print timing summary table
if !isempty(timing_results)
    println("\n" * "="^80)
    println("TIMING SUMMARY")
    println("="^80)
    println()

    # Print header
    @printf("%-50s %12s %12s %12s %12s %12s\n",
            "File", "Init (s)", "Constr (s)", "Obj (s)", "Solve (s)", "Total (s)")
    println("-"^80)

    # Variables to accumulate totals
    total_init = 0.0
    total_constr = 0.0
    total_obj = 0.0
    total_solve = 0.0
    total_time = 0.0

    # Print each file's timing
    for file_name in sort(collect(keys(timing_results)))
        timings = timing_results[file_name]

        # Shorten file name if too long
        display_name = length(file_name) > 45 ? file_name[1:42] * "..." : file_name

        init_time = get(timings, "initialization", 0.0)
        constr_time = get(timings, "constraints", 0.0)
        obj_time = get(timings, "objective", 0.0)
        solve_time = get(timings, "solve", 0.0)
        total = get(timings, "total", 0.0)

        @printf("%-50s %12.2f %12.2f %12.2f %12.2f %12.2f\n",
                display_name, init_time, constr_time, obj_time, solve_time, total)

        # Accumulate totals
        global total_init += init_time
        global total_constr += constr_time
        global total_obj += obj_time
        global total_solve += solve_time
        global total_time += total
    end

    # Print totals
    println("-"^80)
    @printf("%-50s %12.2f %12.2f %12.2f %12.2f %12.2f\n",
            "TOTAL", total_init, total_constr, total_obj, total_solve, total_time)
    println("="^80)

    # Print average times
    n_files = length(timing_results)
    println("\nAVERAGE TIMES PER FILE:")
    @printf("  Initialization: %.2f s\n", total_init / n_files)
    @printf("  Constraints:    %.2f s\n", total_constr / n_files)
    @printf("  Objective:      %.2f s\n", total_obj / n_files)
    @printf("  Solve:          %.2f s\n", total_solve / n_files)
    @printf("  Total:          %.2f s\n", total_time / n_files)
    println()
end
