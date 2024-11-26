using YAML, JuMP, Gurobi
include("checks.jl")
include("structs.jl")


"""
	get_input_data(path_to_source_file::String)

This function reads the input data and checks requirements for the content of the file.

# Arguments
- path_to_source_file::String: path to the source file

# Returns
- data_dict::Dict: dictionary with the input data
"""
function get_input_data(path_to_source_file::String)
    check_input_file(path_to_source_file)
    data_dict = YAML.load_file(path_to_source_file)
    check_required_keys(data_dict, struct_names_base)

    return data_dict
end

"""
	parse_data(data_dict::Dict)

Parses the input data into the corresponding parameters in struct format from structs.jl.

# Arguments
- data_dict::Dict: dictionary with the input data

# Returns
- data_structures::Dict: dictionary with the parsed data
"""
function parse_data(data_dict::Dict)
    node_list = [Node(node["id"], node["name"]) for node ∈ data_dict["Node"]]
    edge_list = [
        Edge(
            edge["id"],
            edge["name"],
            edge["length"],
            node_list[findfirst(n -> n.name == edge["from"], node_list)],
            node_list[findfirst(n -> n.name == edge["to"], node_list)],
        ) for edge ∈ data_dict["Edge"]
    ]
    financial_status_list = [
        FinancialStatus(
            financial_stat["id"],
            financial_stat["name"],
            financial_stat["VoT"],
            financial_stat["monetary_budget_operational"],
            financial_stat["monetary_budget_operational_lb"],
            financial_stat["monetary_budget_operational_ub"],
            financial_stat["monetary_budget_purchase"],
            financial_stat["monetary_budget_purchase_lb"],
            financial_stat["monetary_budget_purchase_ub"],
        ) for financial_stat ∈ data_dict["FinancialStatus"]
    ]
    mode_list = [
        Mode(
            mode["id"],
            mode["name"],
            mode["quantify_by_vehs"],
            mode["costs_per_ukm"],
            mode["emission_factor"],
        ) for mode ∈ data_dict["Mode"]
    ]

    path_list = [
        Path(path["id"], path["name"], path["length"], [el for el ∈ path["sequence"]])
        for path ∈ data_dict["Path"]
    ]
    product_list =
        [Product(product["id"], product["name"]) for product ∈ data_dict["Product"]]
    path_list = [
        Path(path["id"], path["name"], path["length"], [el for el ∈ path["sequence"]])
        for path ∈ data_dict["Path"]
    ]
    fuel_list = [
        Fuel(
            fuel["id"],
            fuel["name"],
            fuel["cost_per_kWh"],
            fuel["cost_per_kW"],
            fuel["emission_factor"],
        ) for fuel ∈ data_dict["Fuel"]
    ]
    technology_list = [
        Technology(
            technology["id"],
            technology["name"],
            fuel_list[findfirst(f -> f.name == technology["fuel"], fuel_list)],
        ) for technology ∈ data_dict["Technology"]
    ]
    vehicle_type_list = [
        Vehicletype(
            vehicletype["id"],
            vehicletype["name"],
            mode_list[findfirst(m -> m.id == vehicletype["mode"], mode_list)],
            [product_list[findfirst(p -> p.name == vehicletype["product"], product_list)]],
        ) for vehicletype ∈ data_dict["Vehicletype"]
    ]
    regiontype_list = [
        Regiontype(
            regiontype["id"],
            regiontype["name"],
            regiontype["costs_var"],
            regiontype["costs_fix"],
        ) for regiontype ∈ data_dict["Regiontype"]
    ]
    techvehicle_list = [
        TechVehicle(
            techvehicle["id"],
            techvehicle["name"],
            vehicle_type_list[findfirst(
                v -> v.name == techvehicle["vehicle_type"],
                vehicle_type_list,
            )],
            technology_list[findfirst(
                t -> t.id == techvehicle["technology"],
                technology_list,
            )],
            techvehicle["capital_cost"],
            techvehicle["maintnanace_cost_annual"],
            techvehicle["maintnance_cost_distance"],
            techvehicle["W"],
            techvehicle["spec_cons"],
            techvehicle["Lifetime"],
            techvehicle["AnnualRange"],
            [
                product_list[findfirst(p -> p.name == prod, product_list)] for
                prod ∈ techvehicle["products"]
            ],
            techvehicle["battery_capacity"],
            techvehicle["peak_charging"],
        ) for techvehicle ∈ data_dict["TechVehicle"]
    ]
    initvehiclestock_list = [
        InitialVehicleStock(
            initvehiclestock["id"],
            techvehicle_list[findfirst(
                tv -> tv.id == initvehiclestock["techvehicle"],
                techvehicle_list,
            )],
            initvehiclestock["year_of_purchase"],
            initvehiclestock["stock"],
        ) for initvehiclestock ∈ data_dict["InitialVehicleStock"]
    ]
    odpair_list = [
        Odpair(
            odpair["id"],
            node_list[findfirst(nodes -> nodes.name == odpair["from"], node_list)],
            node_list[findfirst(nodes -> nodes.name == odpair["to"], node_list)],
            [path_list[findfirst(p -> p.id == odpair["path_id"], path_list)]],
            odpair["F"],
            product_list[findfirst(p -> p.name == odpair["product"], product_list)],
            [
                initvehiclestock_list[findfirst(
                    ivs -> ivs.id == vsi,
                    initvehiclestock_list,
                )] for vsi ∈ odpair["vehicle_stock_init"]
            ],
            financial_status_list[findfirst(
                fs -> fs.name == odpair["financial_status"],
                financial_status_list,
            )],
            regiontype_list[findfirst(
                rt -> rt.name == odpair["region_type"],
                regiontype_list,
            )],
        ) for odpair ∈ data_dict["Odpair"]
    ]

    odpair_list = odpair_list[1:20]

    if haskey(data_dict, "Market_shares")
        market_share_list = [
            MarketShare(
                market_share["id"],
                techvehicle_list[findfirst(tv -> tv.id, techvehicle_list)],
                market_share["share"],
                market_share["financial_status"],
            ) for market_share ∈ data_dict["Market_shares"]
        ]
    else
        market_share_list = []
    end

    # TODO: extend here the list of possible data_dict structures

    data_structures = Dict(
        "Y" => data_dict["Model"]["Y"],
        "y_init" => data_dict["Model"]["y_init"],
        "prey_y" => data_dict["Model"]["pre_y"],
        "gamma" => data_dict["Model"]["gamma"],
        "node_list" => node_list,
        "edge_list" => edge_list,
        "financial_status_list" => financial_status_list,
        "mode_list" => mode_list,
        "product_list" => product_list,
        "path_list" => path_list,
        "fuel_list" => fuel_list,
        "technology_list" => technology_list,
        "vehicletype_list" => vehicle_type_list,
        "regiontype_list" => regiontype_list,
        "techvehicle_list" => techvehicle_list,
        "initvehiclestock_list" => initvehiclestock_list,
        "odpair_list" => odpair_list,
        "market_share_list" => market_share_list,
    )

    for key ∈ keys(default_data)
        if haskey(data_dict["Model"], key)
            data_structures[key] = data_dict["Model"][key]
        else
            data_structures[key] = default_data[key]
        end
    end

    data_structures["G"] = data_dict["Model"]["pre_y"] * data_dict["Model"]["Y"]
    data_structures["g_init"] = data_dict["Model"]["y_init"] - data_dict["Model"]["pre_y"]
    data_structures["Y_end"] = data_dict["Model"]["y_init"] + data_dict["Model"]["Y"] - 1

    return data_structures
end

"""
	create_m_tv_pairs(techvehicle_list::Vector{TechVehicle}, mode_list::Vector{Mode})

Creates a set of pairs of mode and techvehicle IDs.

# Arguments
- techvehicle_list::Vector{TechVehicle}: list of techvehicles
- mode_list::Vector{Mode}: list of modes

# Returns
- m_tv_pairs::Set: set of pairs of mode and techvehicle IDs

"""
function create_m_tv_pairs(techvehicle_list::Vector{TechVehicle}, mode_list::Vector{Mode})
    m_tv_pairs = Set((tv.vehicle_type.mode.id, tv.id) for tv ∈ techvehicle_list)
    techvehicle_ids = [tv.id for tv ∈ techvehicle_list]
    global counter_additional_vehs = length(techvehicle_list)
    for m ∈ mode_list
        for v ∈ techvehicle_list
            if v.vehicle_type.mode.id == m.id
                push!(m_tv_pairs, (m.id, v.id))
            end
        end
        if !m.quantify_by_vehs
            push!(m_tv_pairs, (m.id, counter_additional_vehs + 1))
            push!(techvehicle_ids, counter_additional_vehs + 1)
            global counter_additional_vehs += 1
        end
    end
    return m_tv_pairs
end

"""
	create_tv_id_set(techvehicle_list::Vector{TechVehicle}, mode_list::Vector{Mode})

Creates a list of techvehicle IDs.

# Arguments
- techvehicle_list::Vector{TechVehicle}: list of techvehicles
- mode_list::Vector{Mode}: list of modes

# Returns
- techvehicle_ids_2::Set: set of techvehicle IDs
"""
function create_tv_id_set(techvehicle_list_2::Vector{TechVehicle}, mode_list::Vector{Mode})
    m_tv_pairs = Set((tv.vehicle_type.mode.id, tv.id) for tv ∈ techvehicle_list_2)
    techvehicle_ids_2 = Set([tv.id for tv ∈ techvehicle_list_2])
    global counter_additional_vehs_2 = length(techvehicle_list_2)

    for m ∈ mode_list
        if !m.quantify_by_vehs
            print(counter_additional_vehs + 1)
            push!(techvehicle_ids_2, counter_additional_vehs_2 + 1)
            global counter_additional_vehs_2 += 1
        end
    end
    return techvehicle_ids_2
end

"""
	create_v_t_set(techvehicle_list::Vector{TechVehicle})

Creates a set of pairs of techvehicle IDs.

# Arguments
- techvehicle_list::Vector{TechVehicle}: list of techvehicles

# Returns
- t_v_pairs::Set: set of pairs of techvehicle IDs
"""
function create_v_t_set(techvehicle_list::Vector{TechVehicle})
    t_v_pairs = Set((tv.id, tv.id) for tv ∈ techvehicle_list)
    return t_v_pairs
end

"""
	create_p_r_k_set(odpairs::Vector{Odpair})

Creates a set of pairs of product, odpair, and path IDs.

# Arguments
- odpairs::Vector{Odpair}: list of odpairs

# Returns
- p_r_k_pairs::Set: set of pairs of product, odpair, and path IDs
"""
function create_p_r_k_set(odpairs::Vector{Odpair})
    p_r_k_pairs = Set((r.product.id, r.id, k.id) for r ∈ odpairs for k ∈ r.paths)
    return p_r_k_pairs
end

"""
	create_p_r_k_e_set(odpairs::Vector{Odpair})

Creates a set of pairs of product, odpair, path, and element IDs.

# Arguments
- odpairs::Vector{Odpair}: list of odpairs

# Returns
- p_r_k_e_pairs::Set: set of pairs of product, odpair, path, and element IDs
"""
function create_p_r_k_e_set(odpairs::Vector{Odpair})
    p_r_k_e_pairs = Set(
        (r.product.id, r.id, k.id, el) for r ∈ odpairs for k ∈ r.paths for
        el ∈ k.sequence if typeof(el) == Int
    )
    return p_r_k_e_pairs
end

"""
	create_p_r_k_n_set(odpairs::Vector{Odpair})

Creates a set of pairs of product, odpair, path, and element IDs.

# Arguments
- odpairs::Vector{Odpair}: list of odpairs

# Returns
- p_r_k_n_pairs::Set: set of pairs of product, odpair, path, and element IDs
"""
function create_p_r_k_n_set(odpairs::Vector{Odpair})
    p_r_k_n_pairs = Set(
        (r.product.id, r.id, k.id, el) for r ∈ odpairs for k ∈ r.paths for
        el ∈ k.sequence if typeof(el) == String
    )
    return p_r_k_n_pairs
end

"""
	create_r_k_set(odpairs::Vector{Odpair})

Creates a set of pairs of odpair and path IDs.

# Arguments
- odpairs::Vector{Odpair}: list of odpairs

# Returns
- r_k_pairs::Set: set of pairs of odpair and path IDs
"""
function create_r_k_set(odpairs::Vector{Odpair})
    r_k_pairs = Set((r.id, k.id) for r ∈ odpairs for k ∈ r.paths)
    return r_k_pairs
end

"""
	base_define_variables(model::Model, data_structures::Dict)

Defines the variables for the model.

# Arguments
- model::Model: JuMP model
- data_structures::Dict: dictionary with the input data
"""
function base_define_variables(model::Model, data_structures::Dict)
    m_tv_pairs =
        create_m_tv_pairs(data_structures["techvehicle_list"], data_structures["mode_list"])
    techvehicle_ids =
        create_tv_id_set(data_structures["techvehicle_list"], data_structures["mode_list"])
    t_v_pairs = create_v_t_set(data_structures["techvehicle_list"])
    p_r_k_pairs = create_p_r_k_set(data_structures["odpair_list"])
    p_r_k_e_pairs = create_p_r_k_e_set(data_structures["odpair_list"])
    p_r_k_n_pairs = create_p_r_k_n_set(data_structures["odpair_list"])

    data_structures["m_tv_pairs"] = m_tv_pairs
    data_structures["techvehicle_ids"] = techvehicle_ids
    data_structures["t_v_pairs"] = t_v_pairs
    data_structures["p_r_k_pairs"] = p_r_k_pairs
    data_structures["p_r_k_e_pairs"] = p_r_k_e_pairs
    data_structures["p_r_k_n_pairs"] = p_r_k_n_pairs
    data_structures["r_k_pairs"] = create_r_k_set(data_structures["odpair_list"])

    odpairs = data_structures["odpair_list"]
    y_init = data_structures["y_init"]
    Y_end = data_structures["Y_end"]
    g_init = data_structures["g_init"]
    technologies = data_structures["technology_list"]
    edge_list = data_structures["edge_list"]
    node_list = data_structures["node_list"]

    @variable(
        model,
        h[
            y in y_init:Y_end,
            r_id in [r.id for r ∈ odpairs],
            tv_id in techvehicle_ids,
            g in g_init:Y_end;
            g <= y,
        ] >= 0
    )
    @variable(
        model,
        h_exist[
            y in y_init:Y_end,
            r_id in [r.id for r ∈ odpairs],
            tv_id in techvehicle_ids,
            g in g_init:Y_end;
            g <= y,
        ] >= 0
    )
    @variable(
        model,
        h_plus[
            y in y_init:Y_end,
            r_id in [r.id for r ∈ odpairs],
            tv_id in techvehicle_ids,
            g in g_init:Y_end;
            g <= y,
        ] >= 0
    )
    @variable(
        model,
        h_minus[
            y in y_init:Y_end,
            r_id in [r.id for r ∈ odpairs],
            tv_id in techvehicle_ids,
            g in g_init:Y_end;
            g <= y,
        ] >= 0
    )
    @variable(model, s_e[y in y_init:Y_end, p_r_k_e_pairs, tv_id in techvehicle_ids] >= 0)
    @variable(model, s_n[y in y_init:Y_end, p_r_k_n_pairs, tv_id in techvehicle_ids] >= 0)
    @variable(
        model,
        q_fuel_infr_plus_e[
            y in y_init:Y_end,
            t_id in [t.id for t ∈ technologies],
            [e.id for e ∈ edge_list],
        ] >= 0
    )
    @variable(
        model,
        q_fuel_infr_plus_n[
            y in y_init:Y_end,
            t_id in [t.id for t ∈ technologies],
            [n.id for n ∈ node_list],
        ] >= 0
    )
    @variable(
        model,
        f[y in y_init:Y_end, p_r_k_pairs, m_tv_pairs, g in g_init:Y_end; g <= y] >= 0
    )
    @variable(
        model,
        budget_penalty_plus[y in y_init:Y_end, r_id in [r.id for r ∈ odpairs]] >= 0
    )
    @variable(
        model,
        budget_penalty_minus[y in y_init:Y_end, r_id in [r.id for r ∈ odpairs]] >= 0
    )
end

"""
	constraint_demand_coverage(model::JuMP.Model, data_structures::Dict)

Creates constraint for demand coverage.

# Arguments
- model::JuMP.Model: JuMP model
- data_structures::Dict: dictionary with the input data
"""
function constraint_demand_coverage(model::JuMP.Model, data_structures)
    @constraint(
        model,
        [
            y in data_structures["y_init"]:data_structures["Y_end"],
            r in data_structures["odpair_list"],
        ],
        sum(
            model[:f][y, (r.product.id, r.id, k.id), mv, g] for k ∈ r.paths for
            mv ∈ data_structures["m_tv_pairs"] for g ∈ data_structures["g_init"]:y
        ) >= r.F[y-data_structures["y_init"]+1]
    )
end

"""
	constraint_vehicle_sizing(model::JuMP.Model, data_structures::Dict)

Creates constraint for vehicle sizing.

# Arguments
- model::JuMP.Model: JuMP model
- data_structures::Dict: dictionary with the input data
"""
function constraint_vehicle_sizing(model::JuMP.Model, data_structures::Dict)

    odpairs = data_structures["odpair_list"]
    techvehicles = data_structures["techvehicle_list"]
    vehicletypes = data_structures["vehicletype_list"]
    technologies = data_structures["technology_list"]
    edge_list = data_structures["edge_list"]
    regiontypes = data_structures["regiontype_list"]
    node_list = data_structures["node_list"]
    modes = data_structures["mode_list"]
    m_tv_pairs = data_structures["m_tv_pairs"]
    g_init = data_structures["g_init"]
    Y_end = data_structures["Y_end"]
    y_init = data_structures["y_init"]
    products = data_structures["product_list"]
    r_k_pairs = Set((r.id, k.id) for r ∈ odpairs for k ∈ r.paths)
    p_r_k_pairs = data_structures["p_r_k_pairs"]
    p_r_k_e_pairs = data_structures["p_r_k_e_pairs"]
    p_r_k_n_pairs = data_structures["p_r_k_n_pairs"]
    paths = data_structures["path_list"]
    gamma = data_structures["gamma"]
    alpha_h = data_structures["alpha_h"]
    beta_h = data_structures["beta_h"]
    alpha_f = data_structures["alpha_f"]
    beta_f = data_structures["beta_f"]
    odpairs = data_structures["odpair_list"]
    @constraint(
        model,
        [
            y in data_structures["y_init"]:data_structures["Y_end"],
            r in odpairs,
            mv in data_structures["m_tv_pairs"],
            g in data_structures["g_init"]:data_structures["Y_end"];
            modes[findfirst(m -> m.id == mv[1], modes)].quantify_by_vehs && g <= y,
        ],
        model[:h][y, r.id, mv[2], g] >= sum(
            (
                k.length / (
                    data_structures["techvehicle_list"][findfirst(
                        v0 -> v0.id == mv[2],
                        data_structures["techvehicle_list"],
                    )].W[g-g_init+1] * data_structures["techvehicle_list"][findfirst(
                        v0 -> v0.id == mv[2],
                        data_structures["techvehicle_list"],
                    )].AnnualRange[g-g_init+1]
                )
            ) * model[:f][y, (r.product.id, r.id, k.id), mv, g] for k ∈ r.paths
        )
    )

    @constraint(
        model,
        [
            y in data_structures["y_init"]:data_structures["Y_end"],
            r in odpairs,
            mv in data_structures["m_tv_pairs"],
            g in data_structures["g_init"]:data_structures["Y_end"];
            !data_structures["mode_list"][findfirst(
                m -> m.id == mv[1],
                data_structures["mode_list"],
            )].quantify_by_vehs && g <= y,
        ],
        model[:h][y, r.id, mv[2], g] == 0
    )
    @constraint(
        model,
        [
            y in data_structures["y_init"]:data_structures["Y_end"],
            r in odpairs,
            mv in data_structures["m_tv_pairs"],
            g in data_structures["g_init"]:data_structures["Y_end"];
            !data_structures["mode_list"][findfirst(
                m -> m.id == mv[1],
                data_structures["mode_list"],
            )].quantify_by_vehs && g <= y,
        ],
        model[:h_minus][y, r.id, mv[2], g] == 0
    )
    @constraint(
        model,
        [
            y in data_structures["y_init"]:data_structures["Y_end"],
            r in odpairs,
            mv in data_structures["m_tv_pairs"],
            g in data_structures["g_init"]:data_structures["Y_end"];
            !data_structures["mode_list"][findfirst(
                m -> m.id == mv[1],
                data_structures["mode_list"],
            )].quantify_by_vehs && g <= y,
        ],
        model[:h_plus][y, r.id, mv[2], g] == 0
    )
    @constraint(
        model,
        [
            y in data_structures["y_init"]:data_structures["Y_end"],
            r in odpairs,
            mv in data_structures["m_tv_pairs"],
            g in data_structures["g_init"]:data_structures["Y_end"];
            !data_structures["mode_list"][findfirst(
                m -> m.id == mv[1],
                data_structures["mode_list"],
            )].quantify_by_vehs && g <= y,
        ],
        model[:h_exist][y, r.id, mv[2], g] == 0
    )
end

"""
	constraint_vehicle_aging(model::JuMP.Model, data_structures::Dict)

Creates constraints for vehicle aging.

# Arguments
- model::JuMP.Model: JuMP model
- data_structures::Dict: dictionary with the input data

# Returns
- model::JuMP.Model: JuMP model with the constraints added
"""
function constraint_vehicle_aging(model::JuMP.Model, data_structures::Dict)
    # TODO: implement the constraint in a more efficient way compared to the og script 
    y_init = data_structures["y_init"]
    Y_end = data_structures["Y_end"]
    odpairs = data_structures["odpair_list"]
    g_init = data_structures["g_init"]
    techvehicles = data_structures["techvehicle_list"]
    modes = data_structures["mode_list"]
    # Define all combinations of indices as a collection of tuples
    all_indices = [
        (y, g, r, tv) for y ∈ y_init:Y_end, g ∈ g_init:Y_end, r ∈ odpairs, tv ∈ techvehicles
    ]

    # Use filter to apply the condition
    valid_subset = filter(
        t -> t[2] <= t[1] && (t[1] - t[2]) > t[4].Lifetime[t[2]-g_init+1],
        all_indices,
    )

    # println(valid_subset)
    # case y - g > tv.Lifetime[g-g_init + 1]
    # @constraint(model, [y, g, r, tv] in valid_subset, model[:h][y, r.id, v.id, g] == model[:h_exist][y, r.id, v.id, g] - model[:h_minus][y, r.id, v.id, g] + model[:h_plus][y, r.id, v.id, g])
    for (y, g, r, tv) ∈ valid_subset
        @constraint(
            model,
            model[:h][y, r.id, tv.id, g] ==
            model[:h_exist][y, r.id, tv.id, g] - model[:h_minus][y, r.id, tv.id, g] +
            model[:h_plus][y, r.id, tv.id, g]
        )
        @constraint(model, model[:h_plus][y, r.id, tv.id, g] == 0)
        @constraint(model, model[:h][y, r.id, tv.id, g] == 0)
        @constraint(model, model[:h_exist][y, r.id, tv.id, g] == 0)
        @constraint(model, model[:h_minus][y, r.id, tv.id, g] == 0)
    end
    # Convert valid_subset into a set
    valid_subset_set = Set(valid_subset)

    # Define the second subset: y - g == Lifetime, excluding valid_subset
    valid_subset_equal_exclusive = filter(
        t ->
            t[2] <= t[1] &&
                (t[1] - t[2]) == t[4].Lifetime[t[2]-g_init+1] &&
                !(t in valid_subset_set),
        all_indices,
    )

    # Add constraints for valid_subset_equal_exclusive
    for (y, g, r, tv) ∈ valid_subset_equal_exclusive
        @constraint(
            model,
            model[:h][y, r.id, tv.id, g] ==
            model[:h_exist][y, r.id, tv.id, g] - model[:h_minus][y, r.id, tv.id, g]
        )
        @constraint(model, model[:h_plus][y, r.id, tv.id, g] == 0)
    end

    # Define subset for y - g == Lifetime and y == y_init
    valid_subset_equal_exclusive_y_init = filter(
        t ->
            t[2] <= t[1] &&
                (t[1] - t[2]) == t[4].Lifetime[t[2]-g_init+1] &&
                t[1] == y_init &&
                !(t in valid_subset_set),
        all_indices,
    )

    # Add constraints for valid_subset_equal_exclusive_y_init
    for (y, g, r, tv) ∈ valid_subset_equal_exclusive_y_init
        stock_index = findfirst(
            ivs -> ivs.year_of_purchase == g && ivs.techvehicle.id == tv.id,
            r.vehicle_stock_init,
        )
        @constraint(
            model,
            model[:h_exist][y, r.id, tv.id, g] == r.vehicle_stock_init[stock_index].stock
        )
    end
    # Define subset for in-between years (y - g == Lifetime but not y_init)
    valid_subset_equal_exclusive_inbetw = filter(
        t ->
            t[2] <= t[1] &&
                (t[1] - t[2]) == t[4].Lifetime[t[2]-g_init+1] &&
                !(t in valid_subset_set) &&
                !(t in valid_subset_equal_exclusive_y_init),
        all_indices,
    )

    # Add constraints for valid_subset_equal_exclusive_inbetw
    for (y, g, r, tv) ∈ valid_subset_equal_exclusive_inbetw
        @constraint(
            model,
            model[:h_exist][y, r.id, tv.id, g] == model[:h][y-1, r.id, tv.id, g]
        )
    end

    # Define remaining subset: Lifetime satisfied but not y_init or in-between
    valid_subset_equal_exclusive_rest = filter(
        t ->
            t[2] <= t[1] &&
                (t[1] - t[2]) == t[4].Lifetime[t[2]-g_init+1] &&
                !(t in valid_subset_set) &&
                !(t in valid_subset_equal_exclusive_y_init) &&
                !(t in valid_subset_equal_exclusive_inbetw),
        all_indices,
    )

    # Add constraints for valid_subset_equal_exclusive_rest
    for (y, g, r, tv) ∈ valid_subset_equal_exclusive_rest
        @constraint(model, model[:h_exist][y, r.id, tv.id, g] == 0)
    end
    # Update the valid_subset_equal_exclusive set
    valid_subset_equal_exclusive_set = Set(valid_subset_equal_exclusive)

    # Define subset for g == y (same year)
    valid_subset_equal_g_y = filter(
        t ->
            t[1] == t[2] &&
                !(t in valid_subset_equal_exclusive_set) &&
                !(t in valid_subset_set),
        all_indices,
    )

    # Add constraints for valid_subset_equal_g_y
    for (y, g, r, tv) ∈ valid_subset_equal_g_y
        @constraint(
            model,
            model[:h][y, r.id, tv.id, g] == model[:h_plus][y, r.id, tv.id, g]
        )
        @constraint(model, model[:h_exist][y, r.id, tv.id, g] == 0)
        @constraint(model, model[:h_minus][y, r.id, tv.id, g] == 0)
    end

    # Define subset for g < y, excluding earlier subsets
    valid_subset_g_less_y_exclusive = filter(
        t ->
            t[2] < t[1] &&
                !(t in valid_subset_set) &&
                !(t in valid_subset_equal_exclusive_set) &&
                !(t in valid_subset_equal_g_y),
        all_indices,
    )

    # Add constraints for valid_subset_g_less_y_exclusive
    for (y, g, r, tv) ∈ valid_subset_g_less_y_exclusive
        @constraint(
            model,
            model[:h][y, r.id, tv.id, g] ==
            model[:h_exist][y, r.id, tv.id, g] - model[:h_minus][y, r.id, tv.id, g]
        )
        @constraint(model, model[:h_plus][y, r.id, tv.id, g] == 0)
        @constraint(model, model[:h_minus][y, r.id, tv.id, g] == 0)
    end

    # Define subset for g < y and y == y_init
    valid_subset_g_less_y_exclusive_2 = filter(
        t ->
            t[2] < t[1] &&
                t[1] == y_init &&
                !(t in valid_subset_set) &&
                !(t in valid_subset_equal_exclusive_set) &&
                !(t in valid_subset_equal_g_y),
        all_indices,
    )

    # Add constraints for valid_subset_g_less_y_exclusive_2
    for (y, g, r, tv) ∈ valid_subset_g_less_y_exclusive_2
        stock_index = findfirst(
            ivs -> ivs.year_of_purchase == g && ivs.techvehicle.id == tv.id,
            r.vehicle_stock_init,
        )
        @constraint(
            model,
            model[:h_exist][y, r.id, tv.id, g] == r.vehicle_stock_init[stock_index].stock
        )
    end

    valid_subset_g_less_y_exclusive_3 = filter(
        t ->
            t[2] < t[1] &&
                t[1] > y_init &&
                !(t in valid_subset_g_less_y_exclusive_2) &&
                !(t in valid_subset_set) &&
                !(t in valid_subset_equal_exclusive_set) &&
                !(t in valid_subset_equal_g_y),
        all_indices,
    )

    for (y, g, r, tv) ∈ valid_subset_g_less_y_exclusive_3
        @constraint(
            model,
            model[:h_exist][y, r.id, tv.id, g] ==
            model[:h][y-1, r.id, tv.id, g] - model[:h_minus][y, r.id, tv.id, g]
        )
    end
    # Define remaining subset: Lifetime satisfied but excluding all previous subsets
    valid_subset_rest = filter(
        t ->
            (t[1] - t[2]) == t[4].Lifetime[t[2]-g_init+1] &&
                !(t in valid_subset_set) &&
                !(t in valid_subset_equal_exclusive_set) &&
                !(t in valid_subset_equal_g_y) &&
                !(t in valid_subset_g_less_y_exclusive),
        all_indices,
    )

    # Add constraints for valid_subset_rest
    for (y, g, r, tv) ∈ valid_subset_rest
        @constraint(model, model[:h][y, r.id, tv.id, g] == 0)
        @constraint(model, model[:h_exist][y, r.id, tv.id, g] == 0)
        @constraint(model, model[:h_plus][y, r.id, tv.id, g] == 0)
        @constraint(model, model[:h_minus][y, r.id, tv.id, g] == 0)
    end
end

"""
	constraint_vehicle_purchase(model::JuMP.Model, data_structures::Dict)

Creates constraints for monetary budget for vehicle purchase by route.

# Arguments
- model::JuMP.Model: JuMP model
- data_structures::Dict: dictionary with the input data
"""
function constraint_monetary_budget(model::JuMP.Model, data_structures::Dict)
    odpairs = data_structures["odpair_list"]
    techvehicles = data_structures["techvehicle_list"]
    g_init = data_structures["g_init"]
    @constraint(
        model,
        [r in odpairs],
        sum([
            (model[:h_plus][y, r.id, v.id, g] * v.capital_cost[g-g_init+1]) for
            y ∈ data_structures["y_init"]:data_structures["Y_end"] for v ∈ techvehicles for
            g ∈ data_structures["g_init"]:y
        ]) - sum([
            (
                model[:h_minus][y, r.id, v.id, g] *
                v.capital_cost[g-g_init+1] *
                depreciation_factor(y, g)
            ) for y ∈ data_structures["y_init"]:data_structures["Y_end"] for
            v ∈ techvehicles for g ∈ data_structures["g_init"]:y
        ]) <=
        r.financial_status.monetary_budget_purchase_ub *
        (data_structures["Y_end"] - data_structures["y_init"] + 1) + sum(
            model[:budget_penalty_plus][y, r.id] for
            y ∈ data_structures["y_init"]:data_structures["Y_end"]
        )
    )
    @constraint(
        model,
        [r in odpairs],
        sum([
            (model[:h_plus][y, r.id, v.id, g] * v.capital_cost[g-g_init+1]) for
            y ∈ data_structures["y_init"]:data_structures["Y_end"] for v ∈ techvehicles for
            g ∈ g_init:y
        ]) >=
        r.financial_status.monetary_budget_purchase_lb *
        3 *
        (data_structures["Y_end"] - data_structures["y_init"] + 1) - sum(
            model[:budget_penalty_minus][y, r.id] for
            y ∈ data_structures["y_init"]:data_structures["Y_end"]
        )
    )
end

"""
	constraint_vehicle_purchase(model::JuMP.Model, data_structures::Dict)

Constraints for the sizing of fueling infrastructure at nodes and edges.

# Arguments
- model::JuMP.Model: JuMP model
- data_structures::Dict: dictionary with the input data
"""
function constraint_fueling_infrastructure(model::JuMP.Model, data_structures::Dict)
    technologies = data_structures["technology_list"]
    edge_list = data_structures["edge_list"]
    node_list = data_structures["node_list"]
    p_r_k_n_pairs = data_structures["p_r_k_n_pairs"]
    p_r_k_e_pairs = data_structures["p_r_k_e_pairs"]
    techvehicles = data_structures["techvehicle_list"]

    @constraint(
        model,
        [
            y in data_structures["y_init"]:data_structures["Y_end"],
            t in technologies,
            e in edge_list,
        ],
        sum(
            model[:q_fuel_infr_plus_e][y0, t.id, e.id] for y0 ∈ data_structures["y_init"]:y
        ) >= sum(
            model[:s_e][y, p_r_k_e, tv.id] for p_r_k_e ∈ p_r_k_e_pairs for
            tv ∈ techvehicles if p_r_k_e[4] == e.id && tv.technology.id == t.id
        )
    )

    @constraint(
        model,
        [
            y in data_structures["y_init"]:data_structures["Y_end"],
            t in technologies,
            n in node_list,
        ],
        sum(
            model[:q_fuel_infr_plus_n][y0, t.id, n.id] for y0 ∈ data_structures["y_init"]:y
        ) >= sum(
            model[:s_n][y, p_r_k_n, tv.id] for p_r_k_n ∈ p_r_k_n_pairs for
            tv ∈ techvehicles if p_r_k_n[4] == n.name && tv.technology.id == t.id
        )
    )
end


"""
	constraint_vehicle_stock_shift(model::JuMP.Model, data_structures::Dict)

Constraints for vehicle stock turnover.

# Arguments
- model::JuMP.Model: JuMP model
- data_structures::Dict: dictionary with the input data
"""
function constraint_vehicle_stock_shift(model::JuMP.Model, data_structures::Dict)
    y_init = data_structures["y_init"]
    Y_end = data_structures["Y_end"]
    g_init = data_structures["g_init"]
    odpairs = data_structures["odpair_list"]
    techvehicles = data_structures["techvehicle_list"]
    alpha_h = data_structures["alpha_h"]
    beta_h = data_structures["beta_h"]
    technologies = data_structures["technology_list"]
    vehicletypes = data_structures["vehicletype_list"]

    @constraint(
        model,
        [y in (y_init+1):Y_end, r in odpairs, t in technologies],
        (
            sum(
                model[:h][y, r.id, tv.id, g] for g ∈ g_init:y for v ∈ vehicletypes for
                tv ∈ techvehicles if g <= y && tv.technology.id == t.id
            ) - sum(
                model[:h][y-1, r.id, tv.id, g] for g ∈ g_init:y for v ∈ vehicletypes for
                tv ∈ techvehicles if g <= y - 1 && tv.technology.id == t.id
            )
        ) <=
        alpha_h *
        sum(model[:h][y, r.id, tv.id, g] for g ∈ g_init:(y-1) for tv ∈ techvehicles) +
        beta_h * sum(
            model[:h][y-1, r.id, tv.id, g] for v ∈ vehicletypes for g ∈ g_init:(y-1) for
            tv ∈ techvehicles if tv.technology.id == t.id
        )
    )

    @constraint(
        model,
        [y in (y_init+1):Y_end, r in odpairs, t in technologies],
        -(
            sum(
                model[:h][y, r.id, tv.id, g] for g ∈ g_init:y for v ∈ vehicletypes for
                tv ∈ techvehicles if g <= y && tv.technology.id == t.id
            ) - sum(
                model[:h][y-1, r.id, tv.id, g] for g ∈ g_init:y for v ∈ vehicletypes for
                tv ∈ techvehicles if g <= y - 1 && tv.technology.id == t.id
            )
        ) <=
        alpha_h *
        sum(model[:h][y, r.id, tv.id, g] for g ∈ g_init:(y-1) for tv ∈ techvehicles) +
        beta_h * sum(
            model[:h][y-1, r.id, tv.id, g] for v ∈ vehicletypes for g ∈ g_init:(y-1) for
            tv ∈ techvehicles if tv.technology.id == t.id
        )
    )
end

"""
	constraint_mode_shift(model::JuMP.Model, data_structures::Dict)

Constraints for the rate of the mode shfit.

# Arguments
- model::JuMP.Model: JuMP model
- data_structures::Dict: dictionary with the input data
"""
function constraint_mode_shift(model::JuMP.Model, data_structures::Dict)
    y_init = data_structures["y_init"]
    Y_end = data_structures["Y_end"]
    g_init = data_structures["g_init"]
    odpairs = data_structures["odpair_list"]
    techvehicles = data_structures["techvehicle_list"]
    alpha_f = data_structures["alpha_f"]
    beta_f = data_structures["beta_f"]
    modes = data_structures["mode_list"]
    m_tv_pairs = data_structures["m_tv_pairs"]

    @constraint(
        model,
        [y in (y_init+1):Y_end, r in odpairs, m in modes],
        (
            sum(
                model[:f][y, (r.product.id, r.id, k.id), mv, g] for k ∈ r.paths for
                mv ∈ m_tv_pairs for g ∈ g_init:y if mv[1] == m.id
            ) - sum(
                model[:f][y-1, (r.product.id, r.id, k.id), mv, g] for k ∈ r.paths for
                g ∈ g_init:(y-1) for mv ∈ m_tv_pairs if mv[1] == m.id
            )
        ) <=
        alpha_f * sum(
            model[:f][y, (r.product.id, r.id, k.id), mv, g] for k ∈ r.paths for g ∈
                                                                                g_init:y for
            mv ∈ m_tv_pairs
        ) +
        beta_f * sum(
            model[:f][y-1, (r.product.id, r.id, k.id), mv, g] for m0 ∈ modes for
            mv ∈ m_tv_pairs for k ∈ r.paths for g ∈ g_init:(y-1)
        )
    )

    @constraint(
        model,
        [y in (y_init+1):Y_end, r in odpairs, m in modes],
        -(
            sum(
                model[:f][y, (r.product.id, r.id, k.id), mv, g] for k ∈ r.paths for
                mv ∈ m_tv_pairs for g ∈ g_init:y if mv[1] == m.id
            ) - sum(
                model[:f][y-1, (r.product.id, r.id, k.id), mv, g] for k ∈ r.paths for
                g ∈ g_init:(y-1) for mv ∈ m_tv_pairs if mv[1] == m.id
            )
        ) <=
        alpha_f * sum(
            model[:f][y, (r.product.id, r.id, k.id), mv, g] for k ∈ r.paths for g ∈
                                                                                g_init:y for
            mv ∈ m_tv_pairs
        ) +
        beta_f * sum(
            model[:f][y-1, (r.product.id, r.id, k.id), mv, g] for m0 ∈ modes for
            mv ∈ m_tv_pairs for k ∈ r.paths for g ∈ g_init:(y-1)
        )
    )
end

"""
	create_model(model::JuMP.Model, data_structures::Dict)

Definition of JuMP.model and adding of variables.

# Arguments
- model::JuMP.Model: JuMP model
- data_structures::Dict: dictionary with the input data and parsing of the input parameters

# Returns
- model::JuMP.Model: JuMP model with the variables added
- data_structures::Dict: dictionary with the input data
"""
function create_model(data_dict, case_name::String)
    data_structures = parse_data(data_dict)
    model = Model(Gurobi.Optimizer)
    base_define_variables(model, data_structures)
    return model, data_structures
end

"""
	objective(model::Model, data_structures::Dict)

Definition of the objective function for the optimization model.

# Arguments
- model::Model: JuMP model
- data_structures::Dict: dictionary with the input data
"""
function objective(model::Model, data_structures::Dict)
    y_init = data_structures["y_init"]
    Y_end = data_structures["Y_end"]
    g_init = data_structures["g_init"]
    odpairs = data_structures["odpair_list"]
    techvehicles = data_structures["techvehicle_list"]
    gamma = data_structures["gamma"]
    paths = data_structures["path_list"]
    edge_list = data_structures["edge_list"]
    node_list = data_structures["node_list"]
    technologies = data_structures["technology_list"]
    m_tv_pairs = data_structures["m_tv_pairs"]
    p_r_k_pairs = data_structures["p_r_k_pairs"]
    p_r_k_e_pairs = data_structures["p_r_k_e_pairs"]
    p_r_k_n_pairs = data_structures["p_r_k_n_pairs"]
    regiontypes = data_structures["regiontype_list"]
    modes = data_structures["mode_list"]

    capital_cost_map = Dict(
        (v.id, g) => v.capital_cost[g-g_init+1] for v ∈ techvehicles for g ∈ g_init:Y_end
    )

    # Initialize the total cost expression
    #total_cost_expr = @expression(model, 0)
    total_cost_expr = AffExpr(0)
    fuel_cost = 1

    # Build the objective function more efficiently
    for y ∈ y_init:Y_end
        for r ∈ odpairs
            add_to_expression!(
                total_cost_expr,
                model[:budget_penalty_plus][y, r.id] * 1000000000,
            )
            add_to_expression!(total_cost_expr, model[:budget_penalty_minus][y, r.id])
        end
        for v ∈ techvehicles
            for r ∈ odpairs

                # path length
                route_length = sum(k.length for k ∈ r.paths)
                if r.region_type.name == "urban"
                    speed = 30
                else
                    speed = 60
                end

                for k ∈ r.paths
                    for el ∈ k.sequence
                        if typeof(el) == Int
                            add_to_expression!(
                                total_cost_expr,
                                model[:s_e][y, (r.product.id, r.id, k.id, el), v.id] *
                                fuel_cost,
                            )
                        elseif typeof(el) == String
                            add_to_expression!(
                                total_cost_expr,
                                model[:s_n][y, (r.product.id, r.id, k.id, el), v.id] *
                                fuel_cost,
                            )
                        end
                    end
                end

                for g ∈ g_init:y
                    capital_cost = capital_cost_map[(v.id, g)]

                    add_to_expression!(
                        total_cost_expr,
                        model[:h_plus][y, r.id, v.id, g] * capital_cost,
                    )

                    if y - g <= v.Lifetime[g-g_init+1]
                        add_to_expression!(
                            total_cost_expr,
                            model[:h][y, r.id, v.id, g] *
                            v.maintnanace_cost_annual[g-g_init+1][y-g+1],
                        )
                        add_to_expression!(
                            total_cost_expr,
                            model[:h][y, r.id, v.id, g] *
                            v.maintnance_cost_distance[g-g_init+1][y-g+1] *
                            route_length,
                        )
                    end
                    if y - g == v.Lifetime[g-g_init+1] && r.region_type.name == "urban"
                        add_to_expression!(
                            total_cost_expr,
                            model[:h][y, r.id, v.id, g] * regiontypes[findfirst(
                                rt -> rt.name == "urban",
                                regiontypes,
                            )].costs_fix[y-y+1],
                        )
                    else
                        add_to_expression!(
                            total_cost_expr,
                            model[:h][y, r.id, v.id, g] * regiontypes[findfirst(
                                rt -> rt.name == "rural",
                                regiontypes,
                            )].costs_fix[y-y+1],
                        )
                    end
                    driving_range =
                        0.8 * v.battery_capacity[g-g_init+1] * (1 / v.spec_cons[g-g_init+1])
                    if driving_range < route_length
                        charging_time = 0
                    else
                        charging_time =
                            v.battery_capacity[g-g_init+1] / v.peak_charging[g-g_init+1]
                    end
                    # value of time
                    vot = r.financial_status.VoT
                    los = route_length / speed + charging_time

                    intangible_costs = vot * los
                    add_to_expression!(
                        total_cost_expr,
                        intangible_costs * sum(
                            model[:f][y, (r.product.id, r.id, k.id), mv, g] *
                            k.length *
                            v.W[g-g_init+1] for k ∈ r.paths for
                            mv ∈ m_tv_pairs if mv[2] == v.id
                        ),
                    )
                end
            end
        end
        for m ∈ modes
            if !m.quantify_by_vehs
                for mv ∈ m_tv_pairs
                    if mv[1] == m.id
                        add_to_expression!(
                            total_cost_expr,
                            sum(
                                model[:f][y, (r.product.id, r.id, k.id), mv, g] *
                                sum(k.length for k ∈ r.paths) *
                                m.cost_per_ukm[y-y_init+1] for r ∈ odpairs for k ∈ r.paths
                                for g ∈ g_init:y
                            ),
                        )
                        # adding intangible_costs 
                        for r ∈ odpairs
                            vot = r.financial_status.VoT
                            speed = 30
                            if r.region_type.name == "urban"
                                waiting_time = 20 / 60
                            else
                                waiting_time = 40 / 60
                            end
                            waiting_time = 15
                            los = sum(k.length for k ∈ r.paths) / 30 + waiting_time
                            intangible_costs = vot * los
                            add_to_expression!(
                                total_cost_expr,
                                intangible_costs * sum(
                                    model[:f][y, (r.product.id, r.id, k.id), mv, g] *
                                    k.length for r ∈ odpairs for k ∈ r.paths for
                                    g ∈ g_init:y
                                ),
                            )
                        end
                    end
                end
            end
        end
        for t ∈ technologies
            for e ∈ edge_list
                add_to_expression!(
                    total_cost_expr,
                    model[:q_fuel_infr_plus_e][y, t.id, e.id] *
                    t.fuel.cost_per_kW[y-y_init+1],
                )
            end
            for n ∈ node_list
                add_to_expression!(
                    total_cost_expr,
                    model[:q_fuel_infr_plus_n][y, t.id, n.id] *
                    t.fuel.cost_per_kW[y-y_init+1],
                )
            end
        end
    end

    @objective(model, Min, total_cost_expr)
end

"""
	save_results(model::Model, case_name::String)

Saves the results of the optimization model to YAML files.

# Arguments
- model::Model: JuMP model
- case_name::String: name of the case

# Returns
- output_file::String: name of the output file
"""
function save_results(model::Model, case_name::String)
    y_init = data_structures["y_init"]
    Y_end = data_structures["Y_end"]
    odpairs = data_structures["odpair_list"]
    techvehicles = data_structures["techvehicle_list"]
    m_tv_pairs = data_structures["m_tv_pairs"]
    p_r_k_pairs = data_structures["p_r_k_pairs"]
    p_r_k_e_pairs = data_structures["p_r_k_e_pairs"]
    p_r_k_n_pairs = data_structures["p_r_k_n_pairs"]
    technologies = data_structures["technology_list"]
    edge_list = data_structures["edge_list"]
    node_list = data_structures["node_list"]
    g_init = data_structures["g_init"]

    # Writing the solved decision variables to YAML
    solved_data = Dict()
    solved_data["h"] = value.(model[:h])
    solved_data["h_plus"] = value.(model[:h_plus])
    solved_data["h_minus"] = value.(model[:h_minus])
    solved_data["h_exist"] = value.(model[:h_exist])
    solved_data["f"] = value.(model[:f])
    solved_data["budget_penalty_plus"] = value.(model[:budget_penalty_plus])
    solved_data["budget_penalty_minus"] = value.(model[:budget_penalty_minus])

    output_file = "solved_data.yaml"
    open("solution.yaml", "w") do file
        YAML.dump(file, solved_data)
    end

    f_dict = Dict()
    for y ∈ y_init:Y_end, (p, r, k) ∈ p_r_k_pairs, mv ∈ m_tv_pairs, g ∈ g_init:y
        f_dict[(y, (p, r, k), mv, g)] = value(model[:f][y, (p, r, k), mv, g])
    end

    # Dictionary for 'h' variable
    h_dict = Dict()
    for y ∈ y_init:Y_end, r ∈ odpairs, tv ∈ techvehicles, g ∈ g_init:y
        h_dict[(y, r.id, tv.id, g)] = value(model[:h][y, r.id, tv.id, g])
    end

    # Dictionary for 'h_exist' variable
    h_exist_dict = Dict()
    for y ∈ y_init:Y_end, r ∈ odpairs, tv ∈ techvehicles, g ∈ g_init:y
        h_exist_dict[(y, r.id, tv.id, g)] = value(model[:h_exist][y, r.id, tv.id, g])
    end

    # Dictionary for 'h_plus' variable
    h_plus_dict = Dict()
    for y ∈ y_init:Y_end, r ∈ odpairs, tv ∈ techvehicles, g ∈ g_init:y
        h_plus_dict[(y, r.id, tv.id, g)] = value(model[:h_plus][y, r.id, tv.id, g])
    end

    # Dictionary for 'h_minus' variable
    h_minus_dict = Dict()
    for y ∈ y_init:Y_end, r ∈ odpairs, tv ∈ techvehicles, g ∈ g_init:y
        h_minus_dict[(y, r.id, tv.id, g)] = value(model[:h_minus][y, r.id, tv.id, g])
    end

    # Dictionary for 's_e' variable
    s_e_dict = Dict()
    for y ∈ y_init:Y_end, (p, r, k, e) ∈ p_r_k_e_pairs, tv ∈ techvehicles
        s_e_dict[(y, (p, r, k, e), tv.id)] = value(model[:s_e][y, (p, r, k, e), tv.id])
    end

    # Dictionary for 's_n' variable
    s_n_dict = Dict()
    for y ∈ y_init:Y_end, (p, r, k, n) ∈ p_r_k_n_pairs, tv ∈ techvehicles
        s_n_dict[(y, (p, r, k, n), tv.id)] = value(model[:s_n][y, (p, r, k, n), tv.id])
    end

    # Dictionary for 'q_fuel_infr_plus_e' variable
    q_fuel_infr_plus_e_dict = Dict()
    for y ∈ y_init:Y_end, t ∈ technologies, e ∈ edge_list
        q_fuel_infr_plus_e_dict[(y, t.id, e.id)] =
            value(model[:q_fuel_infr_plus_e][y, t.id, e.id])
    end

    # Dictionary for 'q_fuel_infr_plus_n' variable
    q_fuel_infr_plus_n_dict = Dict()
    for y ∈ y_init:Y_end, t ∈ technologies, n ∈ node_list
        q_fuel_infr_plus_n_dict[(y, t.id, n.id)] =
            value(model[:q_fuel_infr_plus_n][y, t.id, n.id])
    end

    # Dictionary for 'budget_penalty' variable
    budget_penalty_plus_dict = Dict()
    for y ∈ y_init:Y_end, r ∈ odpairs
        budget_penalty_plus_dict[(y, r.id)] = value(model[:budget_penalty_plus][y, r.id])
    end

    # Dictionary for 'budget_penalty' variable
    budget_penalty_minus_dict = Dict()
    for y ∈ y_init:Y_end, r ∈ odpairs
        budget_penalty_minus_dict[(y, r.id)] = value(model[:budget_penalty_minus][y, r.id])
    end

    function stringify_keys(dict::Dict)
        return Dict(
            string(k) => (v isa Float64 ? @sprintf("%.6f", v) : string(v)) for (k, v) ∈ dict
        )
    end

    @info "Saving results..."
    # Convert the keys of each dictionary to strings
    f_dict_str = stringify_keys(f_dict)
    h_dict_str = stringify_keys(h_dict)
    h_exist_dict_str = stringify_keys(h_exist_dict)
    h_plus_dict_str = stringify_keys(h_plus_dict)
    h_minus_dict_str = stringify_keys(h_minus_dict)
    s_e_dict_str = stringify_keys(s_e_dict)
    s_n_dict_str = stringify_keys(s_n_dict)
    q_fuel_infr_plus_e_dict_str = stringify_keys(q_fuel_infr_plus_e_dict)
    q_fuel_infr_plus_n_dict_str = stringify_keys(q_fuel_infr_plus_n_dict)
    budget_penalty_plus_dict_str = stringify_keys(budget_penalty_plus_dict)
    budget_penalty_minus_dict_str = stringify_keys(budget_penalty_minus_dict)

    YAML.write_file(case * "_f_dict.yaml", f_dict_str)
    @info "f_dict.yaml written successfully"
    YAML.write_file(case * "_h_dict.yaml", h_dict_str)
    @info "h_dict.yaml written successfully"
    YAML.write_file(case * "_h_exist_dict.yaml", h_exist_dict_str)
    @info case * "_h_exist_dict.yaml written successfully"
    YAML.write_file(case * "_h_plus_dict.yaml", h_plus_dict_str)
    @info case * "_h_plus_dict.yaml written successfully"
    YAML.write_file(case * "_h_minus_dict.yaml", h_minus_dict_str)
    @info "h_minus_dict.yaml written successfully"
    YAML.write_file(case * "_s_e_dict.yaml", s_e_dict_str)
    @info "s_e_dict.yaml written successfully"
    YAML.write_file(case * "_s_n_dict.yaml", s_n_dict_str)
    @info "s_n_dict.yaml written successfully"
    YAML.write_file(case * "_q_fuel_infr_plus_e_dict.yaml", q_fuel_infr_plus_e_dict_str)
    @info "q_fuel_infr_plus_e_dict.yaml written successfully"
    YAML.write_file(case * "_q_fuel_infr_plus_n_dict.yaml", q_fuel_infr_plus_n_dict_str)
    @info "q_fuel_infr_plus_n_dict.yaml written successfully"
    YAML.write_file(case * "_budget_penalty_plus_dict.yaml", budget_penalty_plus_dict_str)
    @info "budget_penalty_plus_dict.yaml written successfully"
    YAML.write_file(case * "_budget_penalty_minus_dict.yaml", budget_penalty_minus_dict_str)
    @info "budget_penalty_minus_dict.yaml written successfully"
end
