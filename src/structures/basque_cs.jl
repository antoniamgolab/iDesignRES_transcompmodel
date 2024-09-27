using YAML, JuMP, Gurobi, Printf
include("structs.jl")

# Reading the data 
data = YAML.load_file("temp_data/transport_data.yaml")
# println(keys(data))

# "Mode", "Product", "Vehicletype", "Technology", "Path", "Fuel", "Odpair", "Node", "TechVehicle"
modes = [Mode(mode["id"], mode["name"]) for mode in data["Mode"]]
products = [Product(product["id"], product["name"]) for product in data["Product"]]
nodes = [Node(node["id"], node["name"]) for node in data["Node"]]
paths = [Path(path["id"], path["name"], path[raw"length"],[nodes[findfirst(n -> n.name == node, nodes)] for node in path["nodes"]]) for path in data["Path"]]
odpairs = [Odpair(odpair["id"], nodes[findfirst(nodes -> nodes.name == odpair["from"], nodes)], nodes[findfirst(nodes -> nodes.name == odpair["to"], nodes)], [paths[findfirst(p -> p.id == odpair["path_id"], paths)]], odpair["F"], products[findfirst(p -> p.name == odpair["product"], products)]) for odpair in data["Odpair"]]
fuels = [Fuel(fuel["id"], fuel["name"], fuel["cost_per_kWh"]) for fuel in data["Fuel"]]
technologies = [Technology(technology["id"], technology["name"], fuels[findfirst(f -> f.name == technology["fuel"], fuels)]) for technology in data["Technology"]]
vehicletypes = [Vehicletype(vehicletype["id"], vehicletype["name"], modes[findfirst(m -> m.name == vehicletype["mode"], modes)]) for vehicletype in data["Vehicletype"]]
techvehicles = [TechVehicle(techvehicle["id"], techvehicle["name"], vehicletypes[findfirst(v -> v.name == techvehicle["vehicle_type"], vehicletypes)], technologies[findfirst(t -> t.name == techvehicle["technology"], technologies)], techvehicle["capital_cost"], techvehicle["W"], techvehicle["spec_cons"], techvehicle["Lifetime"], techvehicle["AnnualRange"], [products[findfirst(p -> p.name == prod, products)] for prod in techvehicle["products"]]) for techvehicle in data["TechVehicle"]]

#odpairs = odpairs[1:206]
#print(odpairs)
# ----------------------------- VEHICLE STOCK SIZING -----------------------------
# similar to test case B 


# --- model initialization ---
Y = data["Model"]["Y"] # year
G = data["Model"]["Y"]# vehicle generation
v_t_pairs = Set((tv.vehicle_type.id, tv.technology.id) for tv in techvehicles)
p_r_k_pairs = Set((r.product.id, r.id, k.id) for r in odpairs for k in r.paths)
model = Model(Gurobi.Optimizer)

# --- decision variables ---
# @variable(model, f[[y for y in 1:Y], [p.id for p in products], [k.id for k in paths], v_t_pairs, [g for g in 1:G]] >= 0)
@variable(model, f[[y for y in 1:Y], p_r_k_pairs, v_t_pairs, [g for g in 1:G]] >= 0)
@variable(model, h[[y for y in 1:Y], [r.id for r in odpairs], v_t_pairs, [g for g in 1:G]] >= 0, Int)
@variable(model, h_exist[[y for y in 1:Y], [r.id for r in odpairs], v_t_pairs, [g for g in 1:G]] >= 0, Int)
@variable(model, h_plus[[y for y in 1:Y], [r.id for r in odpairs], v_t_pairs, [g for g in 1:G]] >= 0, Int)
@variable(model, h_minus[[y for y in 1:Y], [r.id for r in odpairs], v_t_pairs, [g for g in 1:G]] >= 0, Int)

# --- constraints ---
# @constraint(model, [y in 1:Y, r in odpairs], sum(f[y, r.product.id, k.id, (v.vehicle_type.id, v.technology.id), g] for k in r.paths for v in techvehicles for g in 1:G) == r.F[y]) 

@constraint(model, [y in 1:Y, r in odpairs], sum(f[y, (r.product.id, r.id, k.id), (v.vehicle_type.id, v.technology.id), g] for k in r.paths for v in techvehicles for g in 1:G) == r.F[y]) 
@constraint(model, [y in 1:Y, r in odpairs, v in techvehicles, g in 1:G], h[y, r.id, (v.vehicle_type.id, v.technology.id), g] >= sum((k.length/(v.W[y]* v.AnnualRange[y])) * f[y, (r.product.id, r.id, k.id), (v.vehicle_type.id, v.technology.id), g] for k in r.paths))

for r in odpairs
    for v in techvehicles
        for y in 1:Y
            for g in 1:G
                if y >= g
                    @constraint(model, h[y, r.id, (v.vehicle_type.id, v.technology.id), g] == h_exist[y, r.id, (v.vehicle_type.id, v.technology.id), g] + h_plus[y, r.id, (v.vehicle_type.id, v.technology.id), g] - h_minus[y, r.id, (v.vehicle_type.id, v.technology.id), g])
                    if y == 1
                        @constraint(model, h_exist[y, r.id, (v.vehicle_type.id, v.technology.id), g] == 0)
                    else
                        @constraint(model, h_exist[y, r.id, (v.vehicle_type.id, v.technology.id), g] == h[y-1, r.id, (v.vehicle_type.id, v.technology.id), g])
                    end
                    if y != g
                        @constraint(model, h_plus[y, r.id, (v.vehicle_type.id, v.technology.id), g] == 0)
                    end

                    if y - g == v.Lifetime[g]    # vehicles are replaced after their lifetime
                        # println("")
                        @constraint(model, h_minus[y, r.id, (v.vehicle_type.id, v.technology.id), g] == h_plus[y-v.Lifetime[g], r.id, (v.vehicle_type.id, v.technology.id), g])
                    else
                        @constraint(model, h_minus[y, r.id, (v.vehicle_type.id, v.technology.id), g] == 0)
                    end
                elseif y < g    # there can be no vehicles at year y that are of generation g = y - 1
                    @constraint(model, h[y, r.id, (v.vehicle_type.id, v.technology.id), g] == 0)
                    @constraint(model, h_exist[y, r.id, (v.vehicle_type.id, v.technology.id), g] == 0)
                    @constraint(model, h_plus[y, r.id, (v.vehicle_type.id, v.technology.id), g] == 0)
                    @constraint(model, h_minus[y, r.id, (v.vehicle_type.id, v.technology.id), g] == 0)
                end 
            end 
        end
    end
end

# @objective(model, Min, sum(h_plus[y, r.id, (v.vehicle_type.id, v.technology.id), g]* v.capital_cost[g] for y in 1:Y for r in odpairs for v in techvehicles for g in 1:G)  + sum(f[y, p.id, k.id, (v.vehicle_type.id, v.technology.id), g] * k.length * v.technology.fuel.cost_per_kWh[g] for y in 1:Y for p in products for k in paths for v in techvehicles for g in 1:G))
# @objective(model, Min, sum(h_plus[y, r.id, (v.vehicle_type.id, v.technology.id), g]* v.capital_cost[g] for y in 1:Y for r in odpairs for v in techvehicles for g in 1:G))
@objective(model, Min, sum(sum(sum(h_plus[y, r.id, (v.vehicle_type.id, v.technology.id), g]) * v.capital_cost[g] + sum(f[y, (r.product.id, r.id, k.id), (v.vehicle_type.id, v.technology.id), g] for k in r.paths) for v in techvehicles for r in odpairs for y in 1:Y for g in 1:G)))

optimize!(model)
solution_summary(model)

# if case in ["B"]
solved_h = value.(h)
solved_h_plus = value.(h_plus)
solved_h_minus = value.(h_minus)
solved_h_exist = value.(h_exist)
solved_f = value.(f)

for y in 1:Y
        # println("h in year ",r.id , " ", sum(solved_h[:, r.id, :, :]), " h_plus in year ",r.id , " ", sum(solved_h_plus[:, r.id, :, :]), " h_minus in year ",r.id , " ", sum(solved_h_minus[:, r.id, :, :]), " h_exist in year ",y , " ", sum(solved_h_exist[y, r.id, :, :])," f in year ",y , " ", sum(solved_f[:, r.id, :, :]))
    println("h in year ",y , " ", sum(solved_h[y, :, :, :]), " h_plus in year ",y , " ", sum(solved_h_plus[y, :, :, :]), " h_minus in year ",y , " ", sum(solved_h_minus[y, :, :, :]), " h_exist in year ",y , " ", sum(solved_h_exist[y, :, :, :])," f in year ",y , " ", sum(solved_f[y, :, :, :]))
end
# end



using YAML

# Writing the solved decision variables to YAML
solved_data = Dict()
solved_data["h"] = value.(h)
solved_data["h_plus"] = value.(h_plus)
solved_data["h_minus"] = value.(h_minus)
solved_data["h_exist"] = value.(h_exist)
solved_data["f"] = value.(f)

output_file = "solved_data.yaml"
open("solution.yaml", "w") do file
    YAML.dump(file, solved_data)
end

print("done")

f_dict = Dict()
for y in 1:Y, (p, r, k) in p_r_k_pairs, (v, t) in v_t_pairs, g in 1:G
    f_dict[(y, (p, r, k), (v, t), g)] = value(f[y, (p, r, k), (v, t), g])
end

# Dictionary for 'h' variable
h_dict = Dict()
for y in 1:Y, r in odpairs, (v, t) in v_t_pairs, g in 1:G
    h_dict[(y, r.id, (v, t), g)] = value(h[y, r.id, (v, t), g])
end

# Dictionary for 'h_exist' variable
h_exist_dict = Dict()
for y in 1:Y, r in odpairs, (v, t) in v_t_pairs, g in 1:G
    h_exist_dict[(y, r.id, (v, t), g)] = value(h_exist[y, r.id, (v, t), g])
end

# Dictionary for 'h_plus' variable
h_plus_dict = Dict()
for y in 1:Y, r in odpairs, (v, t) in v_t_pairs, g in 1:G
    h_plus_dict[(y, r.id, (v, t), g)] = value(h_plus[y, r.id, (v, t), g])
end

# Dictionary for 'h_minus' variable
h_minus_dict = Dict()
for y in 1:Y, r in odpairs, (v, t) in v_t_pairs, g in 1:G
    h_minus_dict[(y, r.id, (v, t), g)] = value(h_minus[y, r.id, (v, t), g])
end

function stringify_keys(dict::Dict)
    return Dict(
        string(k) => (v isa Float64 ? @sprintf("%.6f", v) : string(v)) 
        for (k, v) in dict)
end

# Convert the keys of each dictionary to strings
f_dict_str = stringify_keys(f_dict)
h_dict_str = stringify_keys(h_dict)
h_exist_dict_str = stringify_keys(h_exist_dict)
h_plus_dict_str = stringify_keys(h_plus_dict)
h_minus_dict_str = stringify_keys(h_minus_dict)

# Save the dictionaries to YAML files
YAML.write_file("f_dict.yaml", f_dict_str)
YAML.write_file("h_dict.yaml", h_dict_str)
YAML.write_file("h_exist_dict.yaml", h_exist_dict_str)
YAML.write_file("h_plus_dict.yaml", h_plus_dict_str)
YAML.write_file("h_minus_dict.yaml", h_minus_dict_str)
