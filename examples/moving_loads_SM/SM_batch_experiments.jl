"""
SM_batch_experiments.jl - Experimental batch processing with configurable options

This script allows running experiments to diagnose why results are identical:
1. Disable mandatory breaks constraint (test if constraint-dominated)
2. Multiply electricity/network costs by a factor (test if costs are too small)
"""

using Pkg
Pkg.activate(joinpath(@__DIR__, "../.."))

using YAML, JuMP, Gurobi, Printf, ProgressMeter, Dates

include(joinpath(@__DIR__, "../../src/TransComp.jl"))
using .TransComp

# ============================================================================
# EXPERIMENT CONFIGURATION
# ============================================================================

# Experiment 1: Disable mandatory breaks?
DISABLE_MANDATORY_BREAKS = false  # Set to true to skip constraint_mandatory_breaks

# Experiment 2: Disable SOC tracking?
DISABLE_SOC_TRACKING = true  # Set to true to skip SOC constraints (battery range limits)

# Experiment 3: Cost multipliers
ELECTRICITY_COST_MULTIPLIER = 1.0  # Multiply all electricity prices by this factor
NETWORK_COST_MULTIPLIER = 1.0      # Multiply all network connection costs by this factor

# Case folders to process
case_folders = [
    "case_20251107_194948_var_var",    # Base Case (Variable Prices and Costs)
    "case_20251107_214135_var_uni",    # Uniform Network Costs
    "case_20251107_214220_uni_var",    # Uniform Electricity Prices
    "case_20251107_214315_uni_uni"     # Uniform Prices and Costs
]

# Case labels
case_labels = Dict(
    "case_20251107_194948_var_var" => "Base Case (Var. Prices and Costs)",
    "case_20251107_214135_var_uni" => "Uniform Network Costs",
    "case_20251107_214220_uni_var" => "Uniform Electricity Prices",
    "case_20251107_214315_uni_uni" => "Uniform Prices and Costs"
)

# Variables to include
relevant_vars = ["f", "h", "h_plus", "h_exist", "h_minus", "s", "q_fuel_infr_plus", "soc", "travel_time", "extra_break_time"]

# ============================================================================
# HELPER FUNCTION: Modify cost data
# ============================================================================

function apply_cost_multipliers!(data_dict, elec_mult, network_mult)
    """Apply cost multipliers to electricity and network costs"""

    if elec_mult != 1.0
        @info "Applying electricity cost multiplier: ×$(elec_mult)"

        # Multiply FuelCost.yaml entries
        if haskey(data_dict, "FuelCost")
            fuel_costs = data_dict["FuelCost"]
            for entry in fuel_costs
                if haskey(entry, "cost_per_kWh")
                    costs = entry["cost_per_kWh"]
                    if isa(costs, Array)
                        entry["cost_per_kWh"] = [c * elec_mult for c in costs]
                    elseif isa(costs, Dict)
                        for (year, cost) in costs
                            costs[year] = cost * elec_mult
                        end
                    end
                end
            end
            @info "  ✓ Multiplied FuelCost entries by $(elec_mult)"
        end
    end

    if network_mult != 1.0
        @info "Applying network cost multiplier: ×$(network_mult)"

        # Multiply NetworkConnectionCosts.yaml entries
        if haskey(data_dict, "NetworkConnectionCosts")
            network_costs = data_dict["NetworkConnectionCosts"]
            for entry in network_costs
                if haskey(entry, "network_cost_per_kW")
                    costs = entry["network_cost_per_kW"]
                    if isa(costs, Array)
                        entry["network_cost_per_kW"] = [c * network_mult for c in costs]
                    elseif isa(costs, Dict)
                        for (year, cost) in costs
                            costs[year] = cost * network_mult
                        end
                    end
                end
            end
            @info "  ✓ Multiplied NetworkConnectionCosts entries by $(network_mult)"
        end
    end
end

# ============================================================================
# BATCH PROCESSING LOOP
# ============================================================================

@info "="^80
@info "EXPERIMENTAL BATCH PROCESSING: $(length(case_folders)) cases"
@info "="^80
@info "Experiment Settings:"
@info "  Disable mandatory breaks: $(DISABLE_MANDATORY_BREAKS)"
@info "  Electricity cost multiplier: ×$(ELECTRICITY_COST_MULTIPLIER)"
@info "  Network cost multiplier: ×$(NETWORK_COST_MULTIPLIER)"
@info "="^80

batch_start_time = time()
batch_results = Dict()

for (case_idx, folder) in enumerate(case_folders)
    @info "\n" * "="^80
    @info "CASE $(case_idx)/$(length(case_folders)): $folder"
    if haskey(case_labels, folder)
        @info "Label: $(case_labels[folder])"
    end
    @info "="^80

    case_start_time = time()

    try
        # ================================================================
        # Step 1: Setup paths
        # ================================================================
        script_dir = @__DIR__
        input_path = joinpath(script_dir, "input_data", folder)

        if !isdir(input_path)
            @warn "Input folder not found: $input_path - SKIPPING"
            batch_results[folder] = Dict("status" => "SKIPPED", "reason" => "Folder not found")
            continue
        end

        @info "Input path: $input_path"

        # Generate output case name with SHORT experiment suffix
        timestamp = Dates.format(now(), "yyyymmdd_HHMM")
        experiment_suffix = ""
        if DISABLE_MANDATORY_BREAKS
            experiment_suffix *= "_nb"  # Shortened from "_nobreaks"
        end
        if DISABLE_SOC_TRACKING
            experiment_suffix *= "_ns"  # "no soc"
        end
        if ELECTRICITY_COST_MULTIPLIER != 1.0
            experiment_suffix *= "_e$(Int(ELECTRICITY_COST_MULTIPLIER))"  # Shortened from "_elecx"
        end
        if NETWORK_COST_MULTIPLIER != 1.0
            experiment_suffix *= "_n$(Int(NETWORK_COST_MULTIPLIER))"  # Shortened from "_netx"
        end
        case_name = "$(folder)$(experiment_suffix)_$timestamp"

        # ================================================================
        # Step 2: Read and modify input data
        # ================================================================
        @info "Step 1/5: Reading input data..."
        t_start = time()
        data_dict = get_input_data(input_path)
        t_read = time() - t_start
        @info "✓ Input data loaded in $(round(t_read, digits=2)) seconds"

        # Apply cost multipliers if specified
        if ELECTRICITY_COST_MULTIPLIER != 1.0 || NETWORK_COST_MULTIPLIER != 1.0
            apply_cost_multipliers!(data_dict, ELECTRICITY_COST_MULTIPLIER, NETWORK_COST_MULTIPLIER)
        end

        @info "Step 2/5: Parsing data structures..."
        t_start = time()
        data_structures = parse_data(data_dict)
        t_parse = time() - t_start
        @info "✓ Data parsed in $(round(t_parse, digits=2)) seconds"

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
        set_optimizer_attribute(model, "Method", 2)
        set_optimizer_attribute(model, "MIPFocus", 1)
        set_optimizer_attribute(model, "Cuts", 1)
        set_optimizer_attribute(model, "MIPGap", 0.01)
        set_optimizer_attribute(model, "NumericFocus", 3)
        set_optimizer_attribute(model, "ScaleFlag", 2)
        set_optimizer_attribute(model, "FeasibilityTol", 1e-5)
        set_optimizer_attribute(model, "OptimalityTol", 1e-5)
        set_optimizer_attribute(model, "IntFeasTol", 1e-4)
        set_optimizer_attribute(model, "Crossover", 0)
        set_optimizer_attribute(model, "BarConvTol", 1e-6)
        @info "✓ Solver configured"

        # ================================================================
        # Step 5: Add constraints
        # ================================================================
        @info "Step 4/5: Adding constraints..."
        t_constraints_start = time()

        # EXPERIMENTAL: Optionally skip mandatory breaks
        if DISABLE_MANDATORY_BREAKS
            @warn "⚠️  SKIPPING mandatory breaks constraint (experimental)"
            t_mandatory_breaks = 0.0
        else
            t_start = time()
            constraint_mandatory_breaks(model, data_structures)
            t_mandatory_breaks = time() - t_start
            @info "✓ Mandatory breaks constraint added in $(round(t_mandatory_breaks, digits=2))s"
        end

        # Fueling infrastructure constraints
        t_start = time()
        constraint_fueling_demand(model, data_structures)
        t_fueling_demand = time() - t_start
        @info "✓ Fueling demand constraint added in $(round(t_fueling_demand, digits=2))s"

        t_start = time()
        constraint_fueling_infrastructure(model, data_structures)
        t_fueling_infra = time() - t_start
        @info "✓ Fueling infrastructure constraint added in $(round(t_fueling_infra, digits=2))s"

        t_start = time()
        constraint_fueling_infrastructure_expansion_shift(model, data_structures)
        t_fueling_infra_expansion_shift = time() - t_start
        @info "✓ Fueling infrastructure expansion shift constraint added in $(round(t_fueling_infra_expansion_shift, digits=2))s"

        # BEV-specific constraints
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

        # ================================================================
        # Step 6: Add objective function
        # ================================================================
        @info "Step 4.5/5: Adding objective..."
        t_start = time()
        objective(model, data_structures, false)
        t_obj = time() - t_start
        @info "✓ Objective added in $(round(t_obj, digits=2)) seconds"

        GC.gc()

        # ================================================================
        # Step 7: Solve optimization problem
        # ================================================================
        @info "Step 5/5: Solving optimization problem..."
        t_start = time()
        optimize!(model)
        t_optimize = time() - t_start
        @info "✓ Optimization complete in $(round(t_optimize, digits=2)) seconds"

        # ================================================================
        # Step 8: Save results
        # ================================================================
        @info "Saving results to file..."
        # Use simpler directory: results/exp_suffix/ instead of results/folder_exp_suffix/
        experiment_dir = if experiment_suffix != ""
            "exp$(experiment_suffix)"
        else
            folder
        end
        results_file_path = normpath(joinpath(script_dir, "results", experiment_dir))
        if !isdir(results_file_path)
            mkpath(results_file_path)
        end
        save_results(model, case_name, data_structures, true, results_file_path, folder)
        @info "✓ Results saved to: $results_file_path"

        # ================================================================
        # Store results
        # ================================================================
        case_elapsed = time() - case_start_time

        batch_results[folder] = Dict(
            "status" => "SUCCESS",
            "total_time" => case_elapsed,
            "t_read" => t_read,
            "t_parse" => t_parse,
            "t_create" => t_create,
            "t_constraints" => t_constraints,
            "t_obj" => t_obj,
            "t_optimize" => t_optimize,
            "objective_value" => objective_value(model),
            "termination_status" => termination_status(model),
            "experiment_suffix" => experiment_suffix
        )

        @info "="^80
        @info "CASE COMPLETE: $folder"
        @info "  Total time: $(round(case_elapsed/60, digits=2)) minutes"
        @info "  Status: $(termination_status(model))"
        @info "  Objective value: $(objective_value(model))"
        @info "  Output suffix: $(experiment_suffix)"
        @info "="^80

    catch e
        case_elapsed = time() - case_start_time
        @error "ERROR processing case: $folder"
        @error "Exception: $e"
        @error sprint(showerror, e, catch_backtrace())

        batch_results[folder] = Dict(
            "status" => "FAILED",
            "total_time" => case_elapsed,
            "error" => string(e)
        )

        @info "="^80
        @info "CASE FAILED: $folder - Continuing with next case..."
        @info "="^80
    end

    GC.gc()
end

# ============================================================================
# BATCH SUMMARY
# ============================================================================

batch_elapsed = time() - batch_start_time

@info "\n" * "="^80
@info "EXPERIMENTAL BATCH PROCESSING COMPLETE"
@info "="^80
@info "Experiment Settings:"
@info "  Disable mandatory breaks: $(DISABLE_MANDATORY_BREAKS)"
@info "  Electricity cost multiplier: ×$(ELECTRICITY_COST_MULTIPLIER)"
@info "  Network cost multiplier: ×$(NETWORK_COST_MULTIPLIER)"
@info ""
@info "Total batch time: $(round(batch_elapsed/60, digits=2)) minutes ($(round(batch_elapsed/3600, digits=2)) hours)"
@info ""
@info "Results summary:"
for (idx, folder) in enumerate(case_folders)
    result = batch_results[folder]
    status = result["status"]
    elapsed = get(result, "total_time", 0.0)

    if status == "SUCCESS"
        obj_val = get(result, "objective_value", "N/A")
        @info "  [$idx] $folder: ✓ SUCCESS ($(round(elapsed/60, digits=1))m, obj=$(round(obj_val, digits=0)))"
    elseif status == "FAILED"
        error_msg = get(result, "error", "Unknown error")
        @info "  [$idx] $folder: ✗ FAILED ($(round(elapsed/60, digits=1))m) - $(first(error_msg, 60))"
    else
        reason = get(result, "reason", "Unknown")
        @info "  [$idx] $folder: ⊘ SKIPPED - $reason"
    end
end

@info "="^80
@info "All cases processed. Results saved with experiment suffix."
@info "Compare objective values to see if costs now matter!"
@info "="^80
