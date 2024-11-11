using YAML, JuMP, Gurobi, Printf
include("structs.jl")

# Reading the data 
# data = YAML.load_file("temp_data/transport_data_years_v5.yaml")
data = YAML.load_file("C:/Users/Antonia/Documents/external sources/transport_data_years_v5/transport_data_years_v45.yaml")
case = "restricted_EVs_with_mode_restriction"

# println(keys(data))

# "Mode", "Product", "Vehicletype", "Technology", "Path", "Fuel", "Odpair", "Node", "TechVehicle"
node_list = [Node(node["id"], node["name"]) for node in data["Node"]]
edge_list = [Edge(edge["id"], edge["name"], edge["length"], node_list[findfirst(n -> n.name == edge["from"], node_list)], node_list[findfirst(n -> n.name == edge["to"], node_list)]) for edge in data["Edge"]]
financial_stati =[FinancialStatus(financial_stat["id"], financial_stat["name"], financial_stat["weight"], financial_stat["VoT"], financial_stat["monetary_budget_operational"], financial_stat["monetary_budget_operational_lb"], financial_stat["monetary_budget_operational_ub"], financial_stat["monetary_budget_purchase"], financial_stat["monetary_budget_purchase_lb"], financial_stat["monetary_budget_purchase_ub"]) for financial_stat in data["FinancialStatus"]]
modes = [Mode(mode["id"], mode["name"], mode["quantify_by_vehs"], mode["cost_per_ukm"]) for mode in data["Mode"]]
products = [Product(product["id"], product["name"]) for product in data["Product"]]
nodes = [Node(node["id"], node["name"]) for node in data["Node"]]
paths = [Path(path["id"], path["name"], path["length"],[el for el in path["sequence"]]) for path in data["Path"]]
fuels = [Fuel(fuel["id"], fuel["name"], fuel["cost_per_kWh"], fuel["cost_per_kW"]) for fuel in data["Fuel"]]
technologies = [Technology(technology["id"], technology["name"], fuels[findfirst(f -> f.name == technology["fuel"], fuels)]) for technology in data["Technology"]]
vehicletypes = [Vehicletype(vehicletype["id"], vehicletype["name"], modes[findfirst(m -> m.id == vehicletype["mode"], modes)],vehicletype["size_order"], products[findfirst(p -> p.name == vehicletype["product"], products)]) for vehicletype in data["Vehicletype"]]
regiontypes = [Regiontype(regiontype["id"], regiontype["name"], regiontype["weight"], regiontype["speed"]) for regiontype in data["Regiontypes"]]

techvehicles = [TechVehicle(techvehicle["id"], techvehicle["name"], vehicletypes[findfirst(v -> v.name == techvehicle["vehicle_type"], vehicletypes)], technologies[findfirst(t -> t.id == techvehicle["technology"], technologies)], techvehicle["capital_cost"], techvehicle["maintnanace_cost_annual"], techvehicle["maintnance_cost_distance"], techvehicle["W"], techvehicle["spec_cons"], techvehicle["Lifetime"], techvehicle["AnnualRange"], [products[findfirst(p -> p.name == prod, products)] for prod in techvehicle["products"]], techvehicle["battery_capacity"], techvehicle["peak_charging"]) for techvehicle in data["TechVehicle"]]
initvehiclestocks = [InitialVehicleStock(initvehiclestock["id"], techvehicles[findfirst(tv -> tv.id == initvehiclestock["techvehicle"], techvehicles)], initvehiclestock["year_of_purchase"], initvehiclestock["stock"]) for initvehiclestock in data["InitialVehicleStock"]]

odpairs = [Odpair(odpair["id"], nodes[findfirst(nodes -> nodes.name == odpair["from"], nodes)], nodes[findfirst(nodes -> nodes.name == odpair["to"], nodes)], [paths[findfirst(p -> p.id == odpair["path_id"], paths)]], odpair["F"], products[findfirst(p -> p.name == odpair["product"], products)], [initvehiclestocks[findfirst(ivs -> ivs.id == vsi, initvehiclestocks)] for vsi in odpair["vehicle_stock_init"]], financial_stati[findfirst(fs -> fs.name == odpair["financial_status"], financial_stati)], odpair["urban"]) for odpair in data["Odpair"]]

println("Data read successfully")
println("Number of odpairs: ", length(odpairs))
# 

odpairs = odpairs[1:20]


# print(odpairs)
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
r_k_pairs = Set((r.id, k.id) for r in odpairs for k in r.paths)
model = Model(Gurobi.Optimizer)
alpha_h = 0.1
beta_h = 0.1
alpha_f = 0.1
beta_f = 0.1
E = data["Model"]["E"] # number of edges
N = data["Model"]["N"] # number of nodes
p_r_k_e_pairs = Set((r.product.id, r.id, k.id, el) for r in odpairs for k in r.paths for el in k.sequence if typeof(el) == Int)
p_r_k_n_pairs = Set((r.product.id, r.id, k.id, el) for r in odpairs for k in r.paths for el in k.sequence if typeof(el) == String)


# creating here "empty" vehicle types for the modes that are not assigned to have 
m_v_pairs = Set()
counter_additional_vehs = length(techvehicles)
for m in modes
    global vehs_in_this_mode = False
    for v in techvehicles
        if v.vehicle_type.mode.id == m.id
            push!(m_v_pairs, (m.id, v.id))
            vehs_in_this_mode = True
        end
    end
    if mode.
        push!(m_v_pairs, (m.id, counter_additional_vehs + 1))
        counter_additional_vehs += 1
    end
end

m_v_pairs = Set((v.vehicle_type.mode.id, v.id) for v in techvehicles)
println(m_v_pairs)
# print(p_r_k_e_pairs)
# print(p_r_k_n_pairs)
gamma = data["Model"]["gamma"] 
# goal_tot_BEV = data["Model"]["goal_tot_BEV"]
# goal_no_new_ICEV = data["Model"]["goal_no_new_ICEV"]
# prinln(goal_no_new_ICEV)

# --- decision variables ---


@variable(model, h[y in y_init:Y_end, r_id in [r.id for r in odpairs], tv_id in [tv.id for tv in techvehicles], g in g_init:Y_end; g <= y] >= 0)
@variable(model, h_exist[y in y_init:Y_end, r_id in [r.id for r in odpairs], tv_id in [tv.id for tv in techvehicles], g in g_init:Y_end; g <= y] >= 0)
@variable(model, h_plus[y in y_init:Y_end, r_id in [r.id for r in odpairs], tv_id in [tv.id for tv in techvehicles], g in g_init:Y_end; g <= y] >= 0)
@variable(model, h_minus[y in y_init:Y_end, r_id in [r.id for r in odpairs], tv_id in [tv.id for tv in techvehicles], g in g_init:Y_end; g <= y] >= 0)
@variable(model, s_e[y in y_init:Y_end, p_r_k_e_pairs, tv_id in [tv.id for tv in techvehicles]] >= 0)
@variable(model, s_n[y in y_init:Y_end, p_r_k_n_pairs, tv_id in [tv.id for tv in techvehicles]] >= 0)
@variable(model, q_fuel_infr_plus_e[y in y_init:Y_end, t_id in [t.id for t in technologies], [e.id for e in edge_list]] >= 0)
@variable(model, q_fuel_infr_plus_n[y in y_init:Y_end, t_id in [t.id for t in technologies], [n.id for n in node_list]] >= 0)
@variable(model, f[y in y_init:Y_end, p_r_k_pairs, m_v_pairs, g in g_init:Y_end; g <= y] >= 0)
@variable(model, budget_penalty[y in y_init:Y_end, r_id in [r.id for r in odpairs]] >= 0) # variable for penalty of crossing the budget



println("Variables created successfully")

# --- constraints ---
@constraint(model, [y in y_init:Y_end, m_id in [2]], sum(f[y, (r.product.id, r.id, k.id), (m_id, tv.id), g] * k.length for r in odpairs for k in r.paths for m in modes for tv in techvehicles for g in g_init:y if tv.vehicle_type.mode.id == m_id && r.urban) <= 0.1 * sum(r.F[y-y_init+1] * k.length for r in odpairs for k in r.paths))
@constraint(model, [y in y_init:Y_end, m_id in [2]], sum(f[y, (r.product.id, r.id, k.id), (m_id, tv.id), g] * k.length for r in odpairs for k in r.paths for m in modes for tv in techvehicles for g in g_init:y if tv.vehicle_type.mode.id == m_id && r.urban == false) <= 0.03 * sum(r.F[y-y_init+1] * k.length for r in odpairs for k in r.paths))

@constraint(model, [y in 2035:2050, r in odpairs, v in techvehicles; v.id==1 || v.id ==2 || v.id ==0], sum(h_plus[y, r.id, v.id, g] for g in g_init:y) == 0)

# demand coverage
# @constraint(model, [y in y_init:Y_end, r in odpairs], sum(f[y, (r.product.id, r.id, k.id), v.id, g] for k in r.paths for v in techvehicles for g in g_init:y) == r.F[y-y_init+1]) 
@constraint(model, [y in y_init:Y_end, r in odpairs], sum(f[y, (r.product.id, r.id, k.id), mv, g] for k in r.paths for mv in m_v_pairs for g in g_init:y) == r.F[y-y_init+1]) 

# vehicle stock sizing
@constraint(model, [y in y_init:Y_end, r in odpairs, mv in m_v_pairs, g in g_init:Y_end; g <= y], h[y, r.id, mv[2], g] >= sum((k.length/(techvehicles[findfirst(v0 -> v0.id == mv[2], techvehicles)].W[g-g_init+1]* techvehicles[findfirst(v0 -> v0.id == mv[2], techvehicles)].AnnualRange[g-g_init+1])) * f[y, (r.product.id, r.id, k.id), mv, g] for k in r.paths))

# fueling demand
@constraint(model, [y in y_init:Y_end, p in products, r_k in r_k_pairs, v in techvehicles], sum(s_e[y, (p.id, r_k[1], r_k[2], el), v.id] for el in paths[findfirst(k0 -> k0.id == r_k[2], paths)].sequence if typeof(el) == Int) + sum(s_n[y, (p.id, r_k[1], r_k[2], el), v.id] for el in paths[findfirst(k0 -> k0.id == r_k[2], paths)].sequence if typeof(el) == String) >= sum(((gamma * v.spec_cons[g-g_init+1])/(v.W[g-g_init+1] * paths[findfirst(p0 -> p0.id == r_k[2], paths)].length)) * f[y, (p.id, r_k[1], r_k[2]), (tv.vehicle_type.mode.id, tv.id), g] for g in g_init:y for tv in techvehicles if tv.vehicle_type.id == v.id))


# vehicle stock aging and renewale
vehs_total = 0
for r in odpairs
    for v in techvehicles
        for y in y_init:Y_end
            for g in g_init:y
                if y - g > v.Lifetime[g-g_init+1]
                    @constraint(model, h[y, r.id, v.id, g] == h_exist[y, r.id, v.id, g] - h_minus[y, r.id, v.id, g] + h_plus[y, r.id, v.id, g])
                    @constraint(model, h_exist[y, r.id, v.id, g] == 0)
                    @constraint(model, h_plus[y, r.id, v.id, g] == 0)
                    @constraint(model, h[y, r.id, v.id, g] == 0)
                    @constraint(model, h_minus[y, r.id, v.id, g] == 0)
                elseif y - g == v.Lifetime[g-g_init+1]
                    @constraint(model, h[y, r.id, v.id, g] == h_exist[y, r.id, v.id, g] - h_minus[y, r.id, v.id, g])
                    @constraint(model, h_plus[y, r.id,  v.id, g] == 0)
                    if y == y_init
                        @constraint(model, h_exist[y, r.id, v.id, g] == r.vehicle_stock_init[findfirst(ivs -> ivs.year_of_purchase == g && ivs.techvehicle.id == v.id, r.vehicle_stock_init)].stock)
                        stockvalue = r.vehicle_stock_init[findfirst(ivs -> ivs.year_of_purchase == g && ivs.techvehicle.id == v.id, r.vehicle_stock_init)].stock
                        global vehs_total += stockvalue
                    elseif g > g_init && g < y-1 && y <= Y_end
                        @constraint(model, h_exist[y, r.id, v.id, g] == h[y-1, r.id, v.id, g])
                    else 
                        @constraint(model, h_exist[y, r.id,  v.id, g] == 0)
                    end
                elseif g == y 
                    @constraint(model, h[y, r.id, v.id, g] == h_plus[y, r.id, v.id, g])
                    @constraint(model, h_exist[y, r.id, v.id, g] == 0)
                    @constraint(model, h_minus[y, r.id, v.id, g] == 0)
                elseif g < y

                    @constraint(model, h[y, r.id, v.id, g] == h_exist[y, r.id, v.id, g] - h_minus[y, r.id, v.id, g])
                    @constraint(model, h_plus[y, r.id, v.id, g] == 0)
                    @constraint(model, h_minus[y, r.id, v.id, g] == 0)
                    if y == y_init
                        @constraint(model, h_exist[y, r.id, v.id, g] == r.vehicle_stock_init[findfirst(ivs -> ivs.year_of_purchase == g && ivs.techvehicle.id == v.id, r.vehicle_stock_init)].stock)                    else
                        @constraint(model, h_exist[y, r.id, v.id, g] == h[y-1, r.id, v.id, g] - h_minus[y, r.id, v.id, g])
                    end
                else
                    @constraint(model, h[y, r.id, v.id, g] == 0)
                    @constraint(model, h_exist[y, r.id, v.id, g] == 0)
                    @constraint(model, h_plus[y, r.id, v.id, g] == 0)
                    @constraint(model, h_minus[y, r.id, v.id, g] == 0)
                end 
            end 
        end
    end
end
println("vehicle total: ", vehs_total)

# constraint for speed of technological shift
# ... for vehicle stock
@constraint(model, [y in (y_init+1):Y_end, r in odpairs,  t in technologies], (sum(h[y, r.id, tv.id, g] for g in g_init:y for v in vehicletypes for tv in techvehicles if g <= y && tv.technology.id == t.id) - sum(h[y-1, r.id, tv.id,  g] for g in g_init:y for v in vehicletypes for tv in techvehicles if g <= y-1 && tv.technology.id == t.id)) <= alpha_h*sum(h[y, r.id, tv.id, g] for g in g_init:(y-1) for tv in techvehicles) + beta_h * sum(h[y-1, r.id, tv.id, g] for v in vehicletypes for g in g_init:(y-1) for tv in techvehicles if tv.technology.id == t.id))
@constraint(model, [y in (y_init+1):Y_end, r in odpairs,  t in technologies], - (sum(h[y, r.id,tv.id, g] for g in g_init:y for v in vehicletypes for tv in techvehicles if g <= y && tv.technology.id == t.id) - sum(h[y-1, r.id, tv.id,  g] for g in g_init:y for v in vehicletypes for tv in techvehicles if g <= y-1 && tv.technology.id == t.id)) <= alpha_h*sum(h[y, r.id, tv.id, g] for g in g_init:(y-1) for tv in techvehicles) + beta_h * sum(h[y-1, r.id, tv.id, g] for v in vehicletypes for g in g_init:(y-1) for tv in techvehicles if tv.technology.id == t.id))

# ... for transport demand
@constraint(model, [y in (y_init+1):Y_end, r in odpairs, m in modes], (sum(f[y, (r.product.id, r.id, k.id), (m.id, tv.id), g] for k in r.paths for tv in techvehicles for g in g_init:y if tv.vehicle_type.mode.id == m.id) - sum(f[y-1, (r.product.id, r.id, k.id), (m.id, tv.id), g] for k in r.paths for g in g_init:(y-1) for tv in techvehicles if tv.vehicle_type.mode.id == m.id)) <= alpha_f*sum(f[y, (r.product.id, r.id, k.id), (m0.id, tv.id), g] for k in r.paths for g in g_init:y for m0 in modes for tv in techvehicles if tv.vehicle_type.mode.id == m0.id) + beta_f * sum(f[y-1, (r.product.id, r.id, k.id), (m0.id, tv.id), g] for m0 in modes for tv in techvehicles for k in r.paths for g in g_init:(y-1) if tv.vehicle_type.mode.id == m0.id))
@constraint(model, [y in (y_init+1):Y_end, r in odpairs, m in modes], - (sum(f[y, (r.product.id, r.id, k.id), (m.id, tv.id), g] for k in r.paths for tv in techvehicles for g in g_init:y if tv.vehicle_type.mode.id == m.id) - sum(f[y-1, (r.product.id, r.id, k.id), (m.id, tv.id), g] for k in r.paths for g in g_init:(y-1) for tv in techvehicles if tv.vehicle_type.mode.id == m.id)) <= alpha_f*sum(f[y, (r.product.id, r.id, k.id), (m0.id, tv.id), g] for k in r.paths for g in g_init:y for m0 in modes for tv in techvehicles if tv.vehicle_type.mode.id == m0.id) + beta_f * sum(f[y-1, (r.product.id, r.id, k.id), (m0.id, tv.id), g] for m0 in modes for tv in techvehicles for k in r.paths for g in g_init:(y-1) if tv.vehicle_type.mode.id == m0.id))

# constraints for fueling infrastucture
@constraint(model, [y in y_init:Y_end, t in technologies, e in edge_list], sum(q_fuel_infr_plus_e[y0, t.id, e.id] for y0 in y_init:y)>= sum(s_e[y, p_r_k_e, tv.id] for p_r_k_e in p_r_k_e_pairs for tv in techvehicles if p_r_k_e[4] == e.id && tv.technology.id == t.id))
@constraint(model, [y in y_init:Y_end, t in technologies, n in node_list], sum(q_fuel_infr_plus_n[y0, t.id, n.id] for y0 in y_init:y)>= sum(s_n[y, p_r_k_n, tv.id] for p_r_k_n in p_r_k_n_pairs for tv in techvehicles if p_r_k_n[4] == n.name && tv.technology.id == t.id))

# constraints for monetary monetary_budget_investment
@constraint(model, [r in odpairs], sum([(h_plus[y, r.id, v.id,  g] * v.capital_cost[g-g_init+1]) for y in y_init:Y_end for v in techvehicles for g in g_init:y]) - sum(budget_penalty[y, r.id] for y in y_init:Y_end) <= r.financial_status.monetary_budget_purchase_ub)   
@constraint(model, [r in odpairs], sum([(h_plus[y, r.id, v.id, g] * v.capital_cost[g-g_init+1]) for y in y_init:Y_end for v in techvehicles for g in g_init:y]) + sum(budget_penalty[y, r.id] for y in y_init:Y_end) >= r.financial_status.monetary_budget_purchase_lb)   

# constraining for vehicle amount
# @constraint(model, sum(h_plus[2020, r.id, (v.vehicle_type.id, v.technology.id), y] for r in odpairs for v in techvehicles if v.technology.name == "ICEV-g") <= 0)
# @constraint(model, sum(h[2030, r.id, (v.vehicle_type.id, v.technology.id), g] for r in odpairs for v in techvehicles for g in g_init:2030 if v.technology.name == "BEV") >= 300000)


# constraint for mode adoption

# for v in vehicletypes
#     @constraint(model, [y in (y_init+1):Y_end, r in odpairs], sum(h[y, r.id, (v0.id, t.id), g] for g in g_init:y for t in technologies for v0 in vehicletypes if v0.size_order >=v.size_order) >= sum(h[y-1, r.id, (v.id, t.id), g] for t in technologies for g in g_init:(y-1)))
# end

println("Constraints created successfully")
# @objective(model, Min, sum(h_plus[y, r.id, (v.vehicle_type.id, v.technology.id), g]* v.capital_cost[g] for y in 1:Y for r in odpairs for v in techvehicles for g in 1:G)  + sum(f[y, p.id, k.id, (v.vehicle_type.id, v.technology.id), g] * k.length * v.technology.fuel.cost_per_kWh[g] for y in 1:Y for p in products for k in paths for v in techvehicles for g in 1:G))
# @objective(model, Min, sum(h_plus[y, r.id, (v.vehicle_type.id, v.technology.id), g]* v.capital_cost[g] for y in 1:Y for r in odpairs for v in techvehicles for g in 1:G))

# @objective(model, Min, sum(sum(sum(h_plus[y, r.id, (v.vehicle_type.id, v.technology.id), g]) * v.capital_cost[g-g_init+1] + sum(f[y, (r.product.id, r.id, k.id), (v.vehicle_type.id, v.technology.id), g] for k in r.paths) for v in techvehicles for r in odpairs for y in y_init:Y_end for g in g_init:Y_end)))
# @objective(model, Min, sum(sum((h_plus[y, r.id, (v.vehicle_type.id, v.technology.id), g]* v.capital_cost[g-g_init+1] + h[y, r.id, (v.vehicle_type.id, v.technology.id), g] * 100)  for v in techvehicles for r in odpairs for y in y_init:Y_end for g in g_init:Y_end)))
# Precompute the capital cost values
capital_cost_map = Dict((v.id, g) => v.capital_cost[g - g_init + 1] for v in techvehicles for g in g_init:Y_end)
fuel_cost_map = Dict((v.id, y) => v.technology.fuel.cost_per_kWh[y - y_init + 1] for v in techvehicles for y in y_init:Y_end)
spec_cons_map = Dict((v.id, g) => v.spec_cons[g - g_init + 1] for v in techvehicles for g in g_init:Y_end)
# Initialize the total cost expression
#total_cost_expr = @expression(model, 0)
total_cost_expr = AffExpr(0)
weight_map = Dict(fs.name => fs.weight for fs in financial_stati)

# Build the objective function more efficiently
for y in y_init:Y_end
    for r in odpairs
    add_to_expression!(total_cost_expr, budget_penalty[y, r.id]*1000000)
    end
    for v in techvehicles
        for r in odpairs
            
            # path length
            route_length = sum(k.length for k in r.paths)
            if r.urban
                speed = regiontypes[findfirst(rt -> rt.name == "urban", regiontypes)].speed
            else
                speed = regiontypes[findfirst(rt -> rt.name == "rural", regiontypes)].speed
            end
   
            # if v.technology.name == "BEV" && r.financial_status.name == "upper_10"
            w = weight_map[r.financial_status.name]
            # if v.technology.name == "BEV" && r.financial_status.name == "bottom_50"
            #     w = w
            # end
            # if r.urban 
            #     w_region_type = regiontypes[findfirst(rt -> rt.name == "urban", regiontypes)].weight[v.vehicle_type.size_order]
            # else 
            #     w_region_type = regiontypes[findfirst(rt -> rt.name == "rural", regiontypes)].weight[v.vehicle_type.size_order] 
            # end
            # else 
            #     w = 1
            # end
            # fuel_cost = fuel_cost_map[(v.id, y)] * (1/spec_cons_map[(v.id, y)]) 
            fuel_cost = 1
            for k in r.paths
                for el in k.sequence
                    if typeof(el) == Int
                        add_to_expression!(total_cost_expr, s_e[y, (r.product.id, r.id, k.id, el), v.id] * fuel_cost)
                    elseif typeof(el) == String
                        add_to_expression!(total_cost_expr, s_n[y, (r.product.id, r.id, k.id, el), v.id] * fuel_cost)
                    end
                end
            end    

            for g in g_init:y

                capital_cost = capital_cost_map[(v.id, g)]

                add_to_expression!(total_cost_expr, h_plus[y, r.id, v.id, g] * capital_cost * w)
                # add_to_expression!(total_cost_expr, (-1) * h_minus[y, r.id, (v.vehicle_type.id, v.technology.id), g] * (capital_cost-(capital_cost*0.05))^(y-g+1) * w)
                # add_to_expression!(total_cost_expr, (-1) * h_minus[y, r.id, v.id,  g] * 0.2)

                if y - g <= v.Lifetime[g-g_init+1]
                    add_to_expression!(total_cost_expr, h[y, r.id, v.id, g] * v.maintnanace_cost_annual[g-g_init+1][y-g+1])
                    add_to_expression!(total_cost_expr, h[y, r.id, v.id, g] * v.maintnance_cost_distance[g-g_init+1][y-g+1] * route_length)
                end 
                driving_range = 0.8 * v.battery_capacity[g-g_init+1] * (1/v.spec_cons[g-g_init+1])
                if driving_range * 1000 < route_length
                    charging_time = 0
                else
                    charging_time = v.battery_capacity[g-g_init+1] / v.peak_charging[g-g_init+1]
                end
                # value of time
                vot = r.financial_status.VoT
                los = route_length / speed + charging_time
                
                intangible_costs = vot * los
                # add_to_expression!(total_cost_expr, intangible_costs * sum(f[y, (r.product.id, r.id, k.id), (v.vehicle_type.id, v.technology.id), g] * k.length * v.W[g-g_init+1] for k in r.paths))
                
                
            end

        end
        
    end
    for t in technologies
        for e in edge_list
            add_to_expression!(total_cost_expr, q_fuel_infr_plus_e[y, t.id, e.id] * t.fuel.cost_per_kW[y-y_init+1])
        end
        for n in node_list
            add_to_expression!(total_cost_expr, q_fuel_infr_plus_n[y, t.id, n.id] * t.fuel.cost_per_kW[y-y_init+1])
        end
    end
end


# # Set the objective to minimize
@objective(model, Min, total_cost_expr)
# set_optimizer_attribute(model, "Method", 1)
# set_optimizer_attribute(model, "Threads", 2)
set_optimizer_attribute(model, "ScaleFlag", 2)
set_optimizer_attribute(model, "NumericFocus", 1)
set_optimizer_attribute(model, "PreSparsify", 2)
set_optimizer_attribute(model, "Crossover", 0)
println("Solution .... ")
optimize!(model)
solution_summary(model)

# if case in ["B"]
solved_h = value.(h)
solved_h_plus = value.(h_plus)
solved_h_minus = value.(h_minus)
solved_h_exist = value.(h_exist)
solved_f = value.(f)
solved_s_e = value.(s_e)
solved_s_n = value.(s_n)
solved_q_fuel_infr_plus_e = value.(q_fuel_infr_plus_e)
solved_q_fuel_infr_plus_n = value.(q_fuel_infr_plus_n)

# for y in (y_init):Y_end
#     println("!", sum(solved_h[y, r.id, (v.vehicle_type.id, v.technology.id), v.id, g] for r in odpairs for v in techvehicles for g in g_init:y), " f ", sum(solved_f[y, :,:, :, :]))

# end 

# for g in (g_init:2020)
#     println("g ", g, " ", sum(solved_h[2020, r.id, (v.vehicle_type.id, v.technology.id), g] for r in odpairs for v in techvehicles), " ", sum(solved_h_exist[2020, r.id, (v.vehicle_type.id, v.technology.id), g] for r in odpairs for v in techvehicles), " h_minus: ", sum(solved_h_minus[2020, r.id, (v.vehicle_type.id, v.technology.id), g] for r in odpairs for v in techvehicles), " ", sum(solved_h_plus[2020, r.id, (v.vehicle_type.id, v.technology.id), g] for r in odpairs for v in techvehicles))
# end
println("The total h_plus: ", sum(solved_h_plus[2020, r.id, v.id, g] for r in odpairs for v in techvehicles for g in g_init:2020))
println("The total h_minus: ", sum(solved_h_minus[2020, r.id, v.id, g] for r in odpairs for v in techvehicles for g in g_init:2020))
println("The total h_exist: ", sum(solved_h_exist[2020, r.id, v.id, g] for r in odpairs for v in techvehicles for g in g_init:2020))
# for v in techvehicles 
#     for y in y_init:Y_end
#         # println("h in year ",r.id , " ", sum(solved_h[:, r.id, :, :]), " h_plus in year ",r.id , " ", sum(solved_h_plus[:, r.id, :, :]), " h_minus in year ",r.id , " ", sum(solved_h_minus[:, r.id, :, :]), " h_exist in year ",y , " ", sum(solved_h_exist[y, r.id, :, :])," f in year ",y , " ", sum(solved_f[:, r.id, :, :]))
#         println("TechVeh ", v.technology.name, v.name, v.id , "; h in year ",y , " ", sum(solved_h[y, :, (v.vehicle_type.id, v.technology.id), :]), " h_plus in year ",y , " ", sum(solved_h_plus[y, :, (v.vehicle_type.id, v.technology.id), :]), " h_minus in year ",y , " ", sum(solved_h_minus[y, :, (v.vehicle_type.id, v.technology.id), :]), " h_exist in year ",y , " ", sum(solved_h_exist[y, :, (v.vehicle_type.id, v.technology.id), :])," f in year ",y , " ", sum(solved_f[y, :,(v.vehicle_type.id, v.technology.id), :]), " s ", sum(solved_s_e[y, :, (v.vehicle_type.id, v.technology.id)]) + sum(solved_s_n[y, :, (v.vehicle_type.id, v.technology.id)]), "; q_fuel ", sum(solved_q_fuel_infr_plus_n[y, (v.vehicle_type.id, v.technology.id), :]) + sum(solved_q_fuel_infr_plus_e[y, (v.vehicle_type.id, v.technology.id), :]))
#     end
# end

# for e in edge_list
#     println("q_fuel_infr_plus_e ", e.id, " ", sum(solved_q_fuel_infr_plus_e[:, :, e.id]))
# end

# for n in node_list
#     println("q_fuel_infr_plus_n ", n.id, " ", sum(solved_q_fuel_infr_plus_n[:, :, n.id]))
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

println("done")

f_dict = Dict()
for y in y_init:Y_end, (p, r, k) in p_r_k_pairs, mv in m_v_pairs, g in g_init:y
    f_dict[(y, (p, r, k), mv, g)] = value(f[y, (p, r, k), mv, g])
end

# Dictionary for 'h' variable
h_dict = Dict()
for y in y_init:Y_end, r in odpairs, tv in techvehicles, g in g_init:y
    h_dict[(y, r.id, tv.id, g)] = value(h[y, r.id,  tv.id, g])
end

# Dictionary for 'h_exist' variable
h_exist_dict = Dict()
for y in y_init:Y_end, r in odpairs, tv in techvehicles, g in g_init:y
    h_exist_dict[(y, r.id, tv.id, g)] = value(h_exist[y, r.id, tv.id, g])
end

# Dictionary for 'h_plus' variable
h_plus_dict = Dict()
for y in y_init:Y_end, r in odpairs, tv in techvehicles, g in g_init:y
    h_plus_dict[(y, r.id,  tv.id, g)] = value(h_plus[y, r.id, tv.id, g])
end

# Dictionary for 'h_minus' variable
h_minus_dict = Dict()
for y in y_init:Y_end, r in odpairs, tv in techvehicles, g in g_init:y
    h_minus_dict[(y, r.id, tv.id, g)] = value(h_minus[y, r.id, tv.id, g])
end

function stringify_keys(dict::Dict)
    return Dict(
        string(k) => (v isa Float64 ? @sprintf("%.6f", v) : string(v)) 
        for (k, v) in dict)
end

println("Saving results...")
# Convert the keys of each dictionary to strings
f_dict_str = stringify_keys(f_dict)
h_dict_str = stringify_keys(h_dict)
h_exist_dict_str = stringify_keys(h_exist_dict)
h_plus_dict_str = stringify_keys(h_plus_dict)
h_minus_dict_str = stringify_keys(h_minus_dict)

# Save the dictionaries to YAML files
YAML.write_file(case * "_f_dict.yaml", f_dict_str)
println("f_dict.yaml written successfully")
YAML.write_file(case * "_h_dict.yaml", h_dict_str)
println("h_dict.yaml written successfully")
YAML.write_file(case * "_h_exist_dict.yaml", h_exist_dict_str)
println(case * "_h_exist_dict.yaml written successfully")
YAML.write_file(case * "_h_plus_dict.yaml", h_plus_dict_str)
println(case * "_h_plus_dict.yaml written successfully")
YAML.write_file(case * "_h_minus_dict.yaml", h_minus_dict_str)
println("h_minus_dict.yaml written successfully")