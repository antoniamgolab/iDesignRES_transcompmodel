using YAML, JuMP, Gurobi, Printf, ProgressMeter

include(joinpath(@__DIR__, "../../src/TransComp.jl"))

using .TransComp
using Dates

# Define list of YAML files to run
# yaml_files = [
#     "data/td_ONENODE_balanced_expansion_24092025_Base.yaml",
#     "data/td_ONENODE_balanced_expansion_24092025_Absolute_-3.yaml",
#     "data/td_ONENODE_balanced_expansion_24092025_Absolute_+3.yaml",
#     "data/td_ONENODE_balanced_expansion_24092025_Compressed_0.5x.yaml",
#     # Add more files here as needed
# ]
yaml_files = [
    "data/td_ONENODE_balanced_expansion_24092025_Compressed_0.75x.yaml",
    "data/td_ONENODE_balanced_expansion_24092025_Expanded_1.25x.yaml",
    "data/td_ONENODE_balanced_expansion_24092025_Expanded_1.5x.yaml",
    "data/td_ONENODE_balanced_expansion_24092025_Absolute_-3.yaml",
    "data/td_ONENODE_balanced_expansion_24092025_Absolute_+3.yaml",
    "data/td_ONENODE_balanced_expansion_24092025_Compressed_0.5x.yaml",

    # Add more files here as needed
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
        # Reading input data and initializing the model
        @info "Initialization ..."
        data_dict = get_input_data(yaml_file_path)
        data_structures = parse_data(data_dict)
        model, data_structures = create_model(data_structures, case)
        @info "Model created successfully"

        # -------- constraints --------
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

        # -------- objective --------
        objective(model, data_structures, false)
        @info "Objective function added successfully"

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
        optimize!(model)
        solution_summary(model)

        # Save results
        results_file_path = normpath(joinpath(@__DIR__, "results/"))
        save_results(model, case, data_structures, true, results_file_path)

        @info "Results saved successfully for $case"
        @info "Model solved successfully for file $file_idx of $(length(yaml_files))"

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
