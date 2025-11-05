using Pkg
Pkg.activate(joinpath(@__DIR__, "../.."))

using YAML, JuMP, Gurobi

include(joinpath(@__DIR__, "../../src/TransComp.jl"))
using .TransComp

# Read input data
script_dir = @__DIR__
folder = "case_20251102_093733"
input_path = joinpath(@__DIR__, "input_data", folder)
println("Loading data from: $input_path")

# Read and parse data
data_dict = get_input_data(input_path)
data_structures = parse_data(data_dict)

# Create model with same variables as SM.jl
relevant_vars = ["f", "h", "h_plus", "h_exist", "h_minus", "s", "q_fuel_infr_plus", "soc", "travel_time", "extra_break_time"]
using Dates
timestamp = Dates.format(now(), "yyyy-mm-dd_HH-MM-SS")
case = "$(folder)_iis_$timestamp"

model, data_structures = create_model(data_structures, case, include_vars=relevant_vars)

# Add all constraints (same as SM.jl)
constraint_mandatory_breaks(model, data_structures)
constraint_fueling_demand(model, data_structures)
constraint_fueling_infrastructure(model, data_structures)
constraint_fueling_infrastructure_expansion_shift(model, data_structures)
constraint_soc_track(model, data_structures)
constraint_soc_max(model, data_structures)
constraint_travel_time_track(model, data_structures)
constraint_mode_shift(model, data_structures)
if !isempty(data_structures["max_mode_share_list"])
    constraint_max_mode_share(model, data_structures)
end
constraint_demand_coverage(model, data_structures)
constraint_vehicle_sizing(model, data_structures)
constraint_vehicle_aging(model, data_structures)
constraint_vehicle_stock_shift(model, data_structures)

# Add objective
objective(model, data_structures, false)

# Configure solver
set_optimizer_attribute(model, "Presolve", 0)  # Disable presolve for IIS
set_optimizer_attribute(model, "Threads", 4)

# Try to optimize
println("\nAttempting to solve model...")
optimize!(model)

# Check if infeasible
if termination_status(model) == MOI.INFEASIBLE
    println("\n" * "="^80)
    println("MODEL IS INFEASIBLE - Computing IIS (Irreducible Inconsistent Subsystem)")
    println("="^80)

    # Compute IIS
    Gurobi.GRBcomputeIIS(backend(model).optimizer.model)
    Gurobi.GRBwrite(backend(model).optimizer.model, "model_iis.ilp")

    println("\n✓ IIS written to model_iis.ilp")
    println("\nTo analyze the IIS:")
    println("  1. Open model_iis.ilp in a text editor")
    println("  2. Look for constraints marked with 'IIS'")
    println("  3. These are the minimal set of conflicting constraints")
else
    println("\nModel status: ", termination_status(model))
    println("Model is not infeasible!")
end
