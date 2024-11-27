using YAML, JuMP, Gurobi, Printf
include("structs.jl")
include("model_functions.jl")
include("other_functions.jl")

# reading input data
# Get the path to the YAML file

script_dir = @__DIR__   # Directory of the current script
yaml_file_path = normpath(
    joinpath(@__DIR__, "../../examples/Basque country/data/transport_data_years_v47.yaml"),
)
println("Constructed file path: $yaml_file_path")

# TODO: deleting this
# data = YAML.load_file(
#     "C:/Users/Antonia/Documents/external sources/transport_data_years_v5/transport_data_years_v47.yaml",
# )
case = "region_dep_costs"

# file = "C:/Users/Antonia/Documents/external sources/transport_data_years_v5/transport_data_years_v47.yaml"

file = yaml_file_path
@info file

# reading input data and initializing the model
@info "Initialization ..."
data_structures = get_input_data(file)
model, data_structures = create_model(data_structures, case)
@info "Model created successfully"

# -------- constraints --------
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

constraint_monetary_budget(model, data_structures)
@info "Policy related constraints created successfully"

@info "Constraints created successfully"

# -------- objective --------
objective(model, data_structures)

# -------- model solution and saving of results --------
set_optimizer_attribute(model, "ScaleFlag", 2)
set_optimizer_attribute(model, "NumericFocus", 1)
set_optimizer_attribute(model, "PreSparsify", 2)
set_optimizer_attribute(model, "Crossover", 0)
println("Solution .... ")
optimize!(model)
solution_summary(model)

results_file_path = normpath(joinpath(@__DIR__, "../../examples/Basque country/results/"))
save_results(model, case, results_file_path)

@info "Results saved successfully"
