using YAML, JuMP, Gurobi, Printf
include("structs.jl")

# Reading the data 
data = YAML.load_file("temp_data/transport_data_years_v5.yaml")
# println(keys(data))

# "Mode", "Product", "Vehicletype", "Technology", "Path", "Fuel", "Odpair", "Node", "TechVehicle"
modes = [Mode(mode["id"], mode["name"]) for mode in data["Mode"]]
products = [Product(product["id"], product["name"]) for product in data["Product"]]
nodes = [Node(node["id"], node["name"]) for node in data["Node"]]
paths = [Path(path["id"], path["name"], path[raw"length"],[nodes[findfirst(n -> n.name == node, nodes)] for node in path["nodes"]]) for path in data["Path"]]
fuels = [Fuel(fuel["id"], fuel["name"], fuel["cost_per_kWh"]) for fuel in data["Fuel"]]
technologies = [Technology(technology["id"], technology["name"], fuels[findfirst(f -> f.name == technology["fuel"], fuels)]) for technology in data["Technology"]]
vehicletypes = [Vehicletype(vehicletype["id"], vehicletype["name"], modes[findfirst(m -> m.name == vehicletype["mode"], modes)]) for vehicletype in data["Vehicletype"]]
techvehicles = [TechVehicle(techvehicle["id"], techvehicle["name"], vehicletypes[findfirst(v -> v.name == techvehicle["vehicle_type"], vehicletypes)], technologies[findfirst(t -> t.name == techvehicle["technology"], technologies)], techvehicle["capital_cost"], techvehicle["W"], techvehicle["spec_cons"], techvehicle["Lifetime"], techvehicle["AnnualRange"], [products[findfirst(p -> p.name == prod, products)] for prod in techvehicle["products"]]) for techvehicle in data["TechVehicle"]]
initvehiclestocks = [InitialVehicleStock(initvehiclestock["id"], techvehicles[findfirst(tv -> tv.id == initvehiclestock["techvehicle"], techvehicles)], initvehiclestock["year_of_purchase"], initvehiclestock["stock"]) for initvehiclestock in data["InitialVehicleStock"]]

odpairs = [Odpair(odpair["id"], nodes[findfirst(nodes -> nodes.name == odpair["from"], nodes)], nodes[findfirst(nodes -> nodes.name == odpair["to"], nodes)], [paths[findfirst(p -> p.id == odpair["path_id"], paths)]], odpair["F"], products[findfirst(p -> p.name == odpair["product"], products)], [initvehiclestocks[findfirst(ivs -> ivs.id == vsi, initvehiclestocks)] for vsi in odpair["vehicle_stock_init"]]) for odpair in data["Odpair"]]

println("Data read successfully")
odpairs = odpairs[1:1]
#print(odpairs)
# ----------------------------- VEHICLE STOCK SIZING -----------------------------
# similar to test case B 


# --- model initialization ---
Y = data["Model"]["Y"] # year
y_init = data["Model"]["y_init"] # initial year
pre_y = data["Model"]["pre_y"] # years before the initial year
G = pre_y + Y
g_init = y_init - pre_y
Y_end = y_init+Y - 1
v_t_pairs = Set((tv.vehicle_type.id, tv.technology.id) for tv in techvehicles)
p_r_k_pairs = Set((r.product.id, r.id, k.id) for r in odpairs for k in r.paths)
model = Model(Gurobi.Optimizer)
alpha_h = 0.1
beta_h = 0.1
alpha_f = 0.1
beta_f = 0.1

# --- decision variables ---
# @variable(model, f[[y for y in 1:Y], [p.id for p in products], [k.id for k in paths], v_t_pairs, [g for g in 1:G]] >= 0)
@variable(model, f[[y for y in y_init:Y_end], p_r_k_pairs, v_t_pairs, [g for g in g_init:Y_end]] >= 0)
@variable(model, h[[y for y in y_init:Y_end], [r.id for r in odpairs], v_t_pairs, [g for g in g_init:Y_end]] >= 0)
@variable(model, h_exist[[y for y in y_init:Y_end], [r.id for r in odpairs], v_t_pairs, [g for g in g_init:Y_end]] >= 0)
@variable(model, h_plus[[y for y in y_init:Y_end], [r.id for r in odpairs], v_t_pairs, [g for g in g_init:Y_end]] >= 0)
@variable(model, h_minus[[y for y in y_init:Y_end], [r.id for r in odpairs], v_t_pairs, [g for g in g_init:Y_end]] >= 0)
println("Variables created successfully")

# --- constraints ---
# @constraint(model, [y in 1:Y, r in odpairs], sum(f[y, r.product.id, k.id, (v.vehicle_type.id, v.technology.id), g] for k in r.paths for v in techvehicles for g in 1:G) == r.F[y]) 

@constraint(model, [y in y_init:Y_end, r in odpairs], sum(f[y, (r.product.id, r.id, k.id), (v.vehicle_type.id, v.technology.id), g] for k in r.paths for v in techvehicles for g in g_init:Y_end) == r.F[y-y_init+1]) 
@constraint(model, [y in y_init:Y_end, r in odpairs, v in techvehicles, g in g_init:Y_end], h[y, r.id, (v.vehicle_type.id, v.technology.id), g] >= sum((k.length/(v.W[g-g_init+1]* v.AnnualRange[g-g_init+1])) * f[y, (r.product.id, r.id, k.id), (v.vehicle_type.id, v.technology.id), g] for k in r.paths))

for r in odpairs
    for v in techvehicles
        for y in y_init:Y_end
            for g in g_init:Y_end
                if y >= g                   
                    @constraint(model, h[y, r.id, (v.vehicle_type.id, v.technology.id), g] == h_exist[y, r.id, (v.vehicle_type.id, v.technology.id), g] + h_plus[y, r.id, (v.vehicle_type.id, v.technology.id), g] - h_minus[y, r.id, (v.vehicle_type.id, v.technology.id), g])
                    if y == y_init
                        if y > g
                            @constraint(model, h_exist[y, r.id, (v.vehicle_type.id, v.technology.id), g] == r.vehicle_stock_init[findfirst(ivs -> ivs.year_of_purchase == g && ivs.techvehicle.id == techvehicles[findfirst(tv -> tv.technology.id == v.technology.id && tv.vehicle_type.id == v.vehicle_type.id, techvehicles)].id, r.vehicle_stock_init)].stock)
                        else # y == g
                            @constraint(model, h_exist[y, r.id, (v.vehicle_type.id, v.technology.id), g] == 0)
                        end    
                    else # y > y_init  
                        @constraint(model, h_exist[y, r.id, (v.vehicle_type.id, v.technology.id), g] == h[y-1, r.id, (v.vehicle_type.id, v.technology.id), g])
                    end 
                    if y != g
                        @constraint(model, h_plus[y, r.id, (v.vehicle_type.id, v.technology.id), g] == 0)
                    end
                    if y - g == v.Lifetime[g-g_init+1]    # vehicles are replaced after their lifetime
                        # TODO: cutoff at y - g < v.Lifetime[g-g_init+1] 
                        @constraint(model, h_minus[y, r.id, (v.vehicle_type.id, v.technology.id), g] == h_exist[y, r.id, (v.vehicle_type.id, v.technology.id), g])
                        
                    else
                        @constraint(model, h_minus[y, r.id, (v.vehicle_type.id, v.technology.id), g] == 0)
                    end
                else # y < g    
                    # hier gibts nix; weil: es kann keine Fahrzeuge zu Jahr y geben, die von einer späteren Generation sind (können ja noch nicht produziert worden sein)
                    @constraint(model, h[y, r.id, (v.vehicle_type.id, v.technology.id), g] == 0)
                    @constraint(model, h_exist[y, r.id, (v.vehicle_type.id, v.technology.id), g] == 0)
                    @constraint(model, h_plus[y, r.id, (v.vehicle_type.id, v.technology.id), g] == 0)
                    @constraint(model, h_minus[y, r.id, (v.vehicle_type.id, v.technology.id), g] == 0)
                end 
                
                # if y >= g
                #     @constraint(model, h[y, r.id, (v.vehicle_type.id, v.technology.id), g] == h_exist[y, r.id, (v.vehicle_type.id, v.technology.id), g] + h_plus[y, r.id, (v.vehicle_type.id, v.technology.id), g] - h_minus[y, r.id, (v.vehicle_type.id, v.technology.id), g])
                #     if y-y_init+1 == 1 && g-g_init+1 == 1
                #         @constraint(model, h_exist[y, r.id, (v.vehicle_type.id, v.technology.id), g] == r.vehicle_stock_init[findfirst(ivs -> ivs.year_of_purchase == y && ivs.techvehicle.id == techvehicles[findfirst(tv -> tv.technology.id == v.technology.id && tv.vehicle_type.id == v.vehicle_type.id, techvehicles)].id, r.vehicle_stock_init)].stock)
                #         # println(r.vehicle_stock_init[findfirst(ivs -> ivs.year_of_purchase == y && ivs.techvehicle.id == techvehicles[findfirst(tv -> tv.technology.id == v.technology.id && tv.vehicle_type.id == v.vehicle_type.id, techvehicles)].id, r.vehicle_stock_init)].stock)
                #     else
                #         @constraint(model, h_exist[y, r.id, (v.vehicle_type.id, v.technology.id), g] == h[y-1, r.id, (v.vehicle_type.id, v.technology.id), g])
                #     end
                #     if y != g
                #         @constraint(model, h_plus[y, r.id, (v.vehicle_type.id, v.technology.id), g] == 0)
                #     end

                #     if y - g == v.Lifetime[g-g_init]    # vehicles are replaced after their lifetime
                #         println(v.Lifetime[g-g_init], y, g)
                        
                #         @constraint(model, h_minus[y, r.id, (v.vehicle_type.id, v.technology.id), g] == h_plus[y-v.Lifetime[g-g_init], r.id, (v.vehicle_type.id, v.technology.id), g] + h_exist[y-v.Lifetime[g-g_init], r.id, (v.vehicle_type.id, v.technology.id), g])
                #     else
                #         @constraint(model, h_minus[y, r.id, (v.vehicle_type.id, v.technology.id), g] == 0)
                #     end
                # elseif y < g    # there can be no vehicles at year y that are of generation g = y - 1
                #     @constraint(model, h[y, r.id, (v.vehicle_type.id, v.technology.id), g] == 0)
                #     @constraint(model, h_exist[y, r.id, (v.vehicle_type.id, v.technology.id), g] == 0)
                #     @constraint(model, h_plus[y, r.id, (v.vehicle_type.id, v.technology.id), g] == 0)
                #     @constraint(model, h_minus[y, r.id, (v.vehicle_type.id, v.technology.id), g] == 0)
                # end 
            end 
        end
    end
end

# constraint for speed of technological shift
@constraint(model, [y in (y_init+1):Y_end, r in odpairs, vt in v_t_pairs], (sum(h[y, r.id, vt, g] for g in g_init:Y_end) - sum(h[y-1, r.id, vt, g] for g in g_init:Y_end)) <= alpha_h*sum(h[y, r.id, vt0, g] for vt0 in v_t_pairs for g in g_init:Y_end) + beta_h * sum(h[y-1, r.id, vt, g] for g in g_init:Y_end))
@constraint(model, [y in (y_init+1):Y_end, r in odpairs, vt in v_t_pairs], - (sum(h[y, r.id, vt, g] for g in g_init:Y_end) - sum(h[y-1, r.id, vt, g] for g in g_init:Y_end)) <= alpha_h*sum(h[y, r.id, vt0, g] for vt0 in v_t_pairs for g in g_init:Y_end) + beta_h * sum(h[y-1, r.id, vt, g] for g in g_init:Y_end))

@constraint(model, [y in (y_init+1):Y_end, r in odpairs], (sum(f[y, (r.product.id, r.id, k.id), (v.vehicle_type.id, v.technology.id), g] for k in r.paths for v in techvehicles for g in g_init:Y_end) - sum(f[y-1, (r.product.id, r.id, k.id), (v.vehicle_type.id, v.technology.id), g] for v in techvehicles for k in r.paths for g in g_init:Y_end)) <= alpha_f*sum(f[y, (r.product.id, r.id, k.id), (v.vehicle_type.id, v.technology.id), g] for v in techvehicles for k in r.paths for g in g_init:Y_end) + beta_f * sum(f[y-1, (r.product.id, r.id, k.id), (v.vehicle_type.id, v.technology.id), g] for v in techvehicles for k in r.paths for g in g_init:Y_end))
@constraint(model, [y in (y_init+1):Y_end, r in odpairs], - (sum(f[y, (r.product.id, r.id, k.id), (v.vehicle_type.id, v.technology.id), g] for k in r.paths for v in techvehicles for g in g_init:Y_end) - sum(f[y-1, (r.product.id, r.id, k.id), (v.vehicle_type.id, v.technology.id), g] for v in techvehicles for k in r.paths for g in g_init:Y_end)) <= alpha_f*sum(f[y, (r.product.id, r.id, k.id), (v.vehicle_type.id, v.technology.id), g] for v in techvehicles for k in r.paths for g in g_init:Y_end) + beta_f * sum(f[y-1, (r.product.id, r.id, k.id), (v.vehicle_type.id, v.technology.id), g] for v in techvehicles for k in r.paths for g in g_init:Y_end))
# f[y, (r.product.id, r.id, k.id), (v.vehicle_type.id, v.technology.id), g]

println("Constraints created successfully")
# @objective(model, Min, sum(h_plus[y, r.id, (v.vehicle_type.id, v.technology.id), g]* v.capital_cost[g] for y in 1:Y for r in odpairs for v in techvehicles for g in 1:G)  + sum(f[y, p.id, k.id, (v.vehicle_type.id, v.technology.id), g] * k.length * v.technology.fuel.cost_per_kWh[g] for y in 1:Y for p in products for k in paths for v in techvehicles for g in 1:G))
# @objective(model, Min, sum(h_plus[y, r.id, (v.vehicle_type.id, v.technology.id), g]* v.capital_cost[g] for y in 1:Y for r in odpairs for v in techvehicles for g in 1:G))

# @objective(model, Min, sum(sum(sum(h_plus[y, r.id, (v.vehicle_type.id, v.technology.id), g]) * v.capital_cost[g-g_init+1] + sum(f[y, (r.product.id, r.id, k.id), (v.vehicle_type.id, v.technology.id), g] for k in r.paths) for v in techvehicles for r in odpairs for y in y_init:Y_end for g in g_init:Y_end)))
# @objective(model, Min, sum(sum((h_plus[y, r.id, (v.vehicle_type.id, v.technology.id), g]* v.capital_cost[g-g_init+1] + h[y, r.id, (v.vehicle_type.id, v.technology.id), g] * 100)  for v in techvehicles for r in odpairs for y in y_init:Y_end for g in g_init:Y_end)))
# Precompute the capital cost values
capital_cost_map = Dict((v.vehicle_type.id, v.technology.id, g) => v.capital_cost[g - g_init + 1] for v in techvehicles for g in g_init:Y_end)

# Initialize the total cost expression
#total_cost_expr = @expression(model, 0)
total_cost_expr = AffExpr(0)

# Build the objective function more efficiently
for v in techvehicles
    for r in odpairs
        for y in y_init:Y_end
            for g in g_init:Y_end
                # Fetch precomputed capital cost
                capital_cost = capital_cost_map[(v.vehicle_type.id, v.technology.id, g)]
                
                # Add terms to the objective using add_to_expression!
                add_to_expression!(total_cost_expr, h_plus[y, r.id, (v.vehicle_type.id, v.technology.id), g] * capital_cost)
                add_to_expression!(total_cost_expr, h[y, r.id, (v.vehicle_type.id, v.technology.id), g] * 100)
                add_to_expression!(total_cost_expr, sum(f[y, (r.product.id, r.id, k.id), (v.vehicle_type.id, v.technology.id), g] * k.length * v.technology.fuel.cost_per_kWh[y - y_init + 1] for k in r.paths))
            end
        end
    end
end

# # Set the objective to minimize
@objective(model, Min, total_cost_expr)

println("Solution .... ")
optimize!(model)
solution_summary(model)

# if case in ["B"]
solved_h = value.(h)
solved_h_plus = value.(h_plus)
solved_h_minus = value.(h_minus)
solved_h_exist = value.(h_exist)
solved_f = value.(f)

for v in techvehicles 
    for y in y_init:Y_end
        # println("h in year ",r.id , " ", sum(solved_h[:, r.id, :, :]), " h_plus in year ",r.id , " ", sum(solved_h_plus[:, r.id, :, :]), " h_minus in year ",r.id , " ", sum(solved_h_minus[:, r.id, :, :]), " h_exist in year ",y , " ", sum(solved_h_exist[y, r.id, :, :])," f in year ",y , " ", sum(solved_f[:, r.id, :, :]))
        println("Tech ", v.id , "; h in year ",y , " ", sum(solved_h[y, :, (v.vehicle_type.id, v.technology.id), :]), " h_plus in year ",y , " ", sum(solved_h_plus[y, :, (v.vehicle_type.id, v.technology.id), :]), " h_minus in year ",y , " ", sum(solved_h_minus[y, :, (v.vehicle_type.id, v.technology.id), :]), " h_exist in year ",y , " ", sum(solved_h_exist[y, :, (v.vehicle_type.id, v.technology.id), :])," f in year ",y , " ", sum(solved_f[y, :,(v.vehicle_type.id, v.technology.id), :]))

    end
end


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
for y in y_init:Y_end, (p, r, k) in p_r_k_pairs, (v, t) in v_t_pairs, g in g_init:Y_end
    f_dict[(y, (p, r, k), (v, t), g)] = value(f[y, (p, r, k), (v, t), g])
end

# Dictionary for 'h' variable
h_dict = Dict()
for y in y_init:Y_end, r in odpairs, (v, t) in v_t_pairs, g in g_init:Y_end
    h_dict[(y, r.id, (v, t), g)] = value(h[y, r.id, (v, t), g])
end

# Dictionary for 'h_exist' variable
h_exist_dict = Dict()
for y in y_init:Y_end, r in odpairs, (v, t) in v_t_pairs, g in g_init:Y_end
    h_exist_dict[(y, r.id, (v, t), g)] = value(h_exist[y, r.id, (v, t), g])
end

# Dictionary for 'h_plus' variable
h_plus_dict = Dict()
for y in y_init:Y_end, r in odpairs, (v, t) in v_t_pairs, g in g_init:Y_end
    h_plus_dict[(y, r.id, (v, t), g)] = value(h_plus[y, r.id, (v, t), g])
end

# Dictionary for 'h_minus' variable
h_minus_dict = Dict()
for y in y_init:Y_end, r in odpairs, (v, t) in v_t_pairs, g in g_init:Y_end
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
