module TransComp
using YAML, JuMP, Gurobi, Printf
include("structs.jl")
include("model_functions.jl")
include("other_functions.jl")

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
export constraint_fueling_demand

end
