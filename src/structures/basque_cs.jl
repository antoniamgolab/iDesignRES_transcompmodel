using YAML, JuMP, Gurobi, Printf
include("structs.jl")
include("model_functions.jl")
include("other_functions.jl")

# Reading the data 
data = YAML.load_file(
    "C:/Users/Antonia/Documents/external sources/transport_data_years_v5/transport_data_years_v47.yaml",
)
case = "region_dep_costs"
file = "C:/Users/Antonia/Documents/external sources/transport_data_years_v5/transport_data_years_v47.yaml"
@info "Initialization ..."
data_structures = get_input_data(file)
model, data_structures = create_model(data_structures, case)
@info "Model created successfully"

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

constraint_monetary_budget(model::Model, data_structures::Dict)

@info "Policy related constraints created successfully"

@info "Constraints created successfully"

objective(model, data_structures)

set_optimizer_attribute(model, "ScaleFlag", 2)
set_optimizer_attribute(model, "NumericFocus", 1)
set_optimizer_attribute(model, "PreSparsify", 2)
set_optimizer_attribute(model, "Crossover", 0)
println("Solution .... ")
optimize!(model)
solution_summary(model)

save_results(model, case)

@info "Results saved successfully"
