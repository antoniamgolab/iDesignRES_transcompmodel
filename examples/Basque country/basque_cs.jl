using YAML, JuMP, Gurobi, Printf

include(joinpath(@__DIR__, "../../src/TransComp.jl"))

# reading input data
# Get the path to the YAML file

using .TransComp

script_dir = @__DIR__   # Directory of the current script
yaml_file_path = normpath(joinpath(@__DIR__, "data/transport_data_years_v64.yaml"))
println("Constructed file path: $yaml_file_path")

using Dates

timestamp = Dates.format(now(), "yyyy-mm-dd_HH-MM-SS")
case = "testing_$timestamp"

file = yaml_file_path
@info file

# reading input data and initializing the model
@info "Initialization ..."
data_dict = get_input_data(file)
data_structures = parse_data(data_dict)
model, data_structures = create_model(data_structures, case, Gurobi.Optimizer)
@info "Model created successfully"

# -------- constraints --------
# constraint_monetary_budget(model, data_structures)
@info "Policy related constraints created successfully"

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

constraint_mode_shift(model, data_structures)
@info "Constraint for mode shift created successfully"

constraint_fueling_infrastructure(model, data_structures)
@info "Constraint for fueling infrastructure created successfully"

constraint_mode_infrastructure(model, data_structures)
@info "Constraint for mode infrastructure created successfully"

@info "Constraints created successfully"
if haskey(data_structures, "detour_time_reduction_list")
    @info "Detour time reduction is added"
else
    @info "Detour time reduction is not added"
end

# -------- constraints (alternative) --------
if data_structures["detour_time_reduction_list"] != []
    constraint_detour_time(model, data_structures)
    constraint_lin_z_nalpha(model, data_structures)
    constraint_detour_time_capacity_reduction(model, data_structures)
    constraint_def_n_fueling(model, data_structures)
    (model, data_structures)
    @info "Detour time reduction constraint is added"
end

# -------- objective --------
objective(model, data_structures)

# -------- model solution and saving of results --------
# set_optimizer_attribute(model, "ScaleFlag", 2)
# set_optimizer_attribute(model, "Presolve", 0)
set_optimizer_attribute(model, "MIPFocus", 2)
set_optimizer_attribute(model, "MIPGap", 10^(-9))
set_optimizer_attribute(model, "Crossover", 0)

println("Solution .... ")
optimize!(model)
solution_summary(model)

results_file_path = normpath(joinpath(@__DIR__, "results/"))
save_results(model, case, data_structures, true, results_file_path)

@info "Results saved successfully"
