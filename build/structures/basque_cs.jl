module BasqueCS

using YAML, JuMP, Gurobi, Printf
include("structs.jl")
include("model_functions.jl")
include("other_functions.jl")

export constraint_fueling_demand

"""
	constraint_fueling_demand(model::JuMP.Model, data_structures::Dict)

Constraints for fueling demand at nodes and edges.

# Arguments
- model::JuMP.Model: JuMP model
- data_structures::Dict: dictionary with the input data
"""
function constraint_fueling_demand(model::JuMP.Model, data_structures::Dict)
    y_init = data_structures["y_init"]
    Y_end = data_structures["Y_end"]
    g_init = data_structures["g_init"]
    odpairs = data_structures["odpair_list"]
    techvehicles = data_structures["techvehicle_list"]
    gamma = data_structures["gamma"]
    paths = data_structures["path_list"]
    products = data_structures["product_list"]
    r_k_pairs = data_structures["r_k_pairs"]

    @constraint(
        model,
        [y in y_init:Y_end, p in products, r_k in r_k_pairs, v in techvehicles],
        sum(
            model[:s_e][y, (p.id, r_k[1], r_k[2], el), v.id] for
            el ∈ paths[findfirst(k0 -> k0.id == r_k[2], paths)].sequence if
            typeof(el) == Int
        ) + sum(
            model[:s_n][y, (p.id, r_k[1], r_k[2], el), v.id] for
            el ∈ paths[findfirst(k0 -> k0.id == r_k[2], paths)].sequence if
            typeof(el) == String
        ) >= sum(
            (
                (gamma * v.spec_cons[g-g_init+1]) /
                (v.W[g-g_init+1] * paths[findfirst(p0 -> p0.id == r_k[2], paths)].length)
            ) * model[:f][y, (p.id, r_k[1], r_k[2]), (tv.vehicle_type.mode.id, tv.id), g]
            for g ∈ g_init:y for tv ∈ techvehicles if tv.vehicle_type.id == v.id
        )
    )
end

# reading input data
data = YAML.load_file(
    "C:/Users/Antonia/Documents/external sources/transport_data_years_v5/transport_data_years_v47.yaml",
)
case = "region_dep_costs"
file = "C:/Users/Antonia/Documents/external sources/transport_data_years_v5/transport_data_years_v47.yaml"

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

constraint_monetary_budget(model::Model, data_structures::Dict)
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

save_results(model, case)

@info "Results saved successfully"
export constraint_vehicle_sizing

end
