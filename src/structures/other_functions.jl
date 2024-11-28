"""
This file contains the functions that are used in the model but are not directly related to the optimization problem but are supporting functions for this.

"""

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
    node_list = [Node(node["id"], node["name"], node["carbon_price"]) for node ∈ data_dict["Node"]]
    edge_list = [
        Edge(
            edge["id"],
            edge["name"],
            edge["length"],
            node_list[findfirst(n -> n.name == edge["from"], node_list)],
            node_list[findfirst(n -> n.name == edge["to"], node_list)],
            edge["carbon_price"], 
        ) for edge ∈ data_dict["Edge"]
    ]
    geographic_element_list = [
        GeographicElement(
            geographic_element["id"],
            geographic_element["name"],
            geographic_element["length"],
            geographic_element["from"],
            geographic_element["to"],
            geographic_element["carbon_price"],
        ) for geographic_element ∈ data_dict["GeographicElement"]
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
            mode["infrastructure_expansion_costs"],
            mode["infrastructure_om_costs"],
            mode["waiting_time"]
        ) for mode ∈ data_dict["Mode"]
    ]

    product_list =
        [Product(product["id"], product["name"]) for product ∈ data_dict["Product"]]
    path_list = [
        Path(path["id"], path["name"], path["length"], [geographic_element_list[findfirst(geo -> geo.id == el, geographic_element_list)] for el ∈ path["sequence"]])
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
    initalfuelinginfr_list = [
        InitialFuelingInfr(
            initalfuelinginfr["id"],
            technology_list[findfirst(
                t -> t.id == initalfuelinginfr["technology"],
                technology_list,
            )],
            initalfuelinginfr["allocation"],
            initalfuelinginfr["installed_kW"],
        ) for initalfuelinginfr ∈ data_dict["InitialFuelingInfr"]
    ]
    initialmodeinfr_list = [
        InitialModeInfr(
            initialmodeinfr["id"],
            mode_list[findfirst(m -> m.id == initialmodeinfr["mode"], mode_list)],
            initialmodeinfr["allocation"],
            initialmodeinfr["installed_kW"],
        ) for initialmodeinfr ∈ data_dict["InitialModeInfr"]
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

    speed_list = [
        Speed(
            speed["id"],
            regiontype_list[findfirst(rt -> rt.name == speed["region_type"], regiontype_list)],
            speed["speed"],
            speed["emission_factor"],
        ) for speed ∈ data_dict["Speed"]
    ]

    if haskey(data_dict, "Market_shares")
        market_share_list = [
            MarketShare(
                market_share["id"],
                techvehicle_list[findfirst(tv -> tv.id, techvehicle_list)],
                market_share["share"],
                market_share["financial_status"],
            ) for market_share ∈ data_dict["Market_shares"]
        ]
        @info "Market shares are defined"
    else
        market_share_list = []
    end

    if haskey(data_dict, "Emission_constraints_by_mode")
        emission_constraint_by_mode_list = [
            EmissionConstraintByYear(
                emission_constraint["id"],
                mode_list[findfirst(m -> m.id == emission_constraint["mode"], mode_list)],
                emission_constraint["year"],
                emission_constraint["emission_constraint"],
            ) for emission_constraint ∈ data_dict["Emission_constraints_by_year"]
        ]
        @info "Emissions are defined by year"

    else
        emission_constraint_by_mode_list = []
    end

    if haskey(data_dict, "Mode_shares")
        mode_shares_list = [
            ModeShare(
                mode_share["id"],
                mode_list[findfirst(m -> m.id == mode_share["mode"], mode_list)],
                mode_share["share"],
                mode_share["year"],
                [regiontype_list[findfirst(
                    rt -> rt.id == rt_id,
                    regiontype_list,
                )] for rt_id ∈ mode_share["regiontype_list"]],
            ) for mode_share ∈ data_dict["Mode_shares"]
        ]
        @info "Mode shares are defined by year"

    else
        default_data = Dict()
    end


    if haskey(data_dict, "Mode_share_max_by_year")
        max_mode_shares_list = [
            ModeShare(
                mode_share["id"],
                mode_list[findfirst(m -> m.id == mode_share["mode"], mode_list)],
                mode_share["share"],
                mode_share["year"],
                [regiontype_list[findfirst(
                    rt -> rt.id == rt_id,
                    regiontype_list,
                )] for rt_id ∈ mode_share["regiontype_list"]],
            ) for mode_share ∈ data_dict["Mode_shares"]
        ]
        @info "Max Mode shares are defined by year"

    else
        max_mode_shares_list = []
    end

    if haskey(data_dict, "Mode_share_min_by_year")
        min_mode_shares_list = [
            ModeShare(
                mode_share["id"],
                mode_list[findfirst(m -> m.id == mode_share["mode"], mode_list)],
                mode_share["share"],
                mode_share["year"],
                [regiontype_list[findfirst(
                    rt -> rt.id == rt_id,
                    regiontype_list,
                )] for rt_id ∈ mode_share["regiontype_list"]],
            ) for mode_share ∈ data_dict["Mode_shares"]
        ]
        @info "Min Mode shares are defined by year"

    else
        min_mode_shares_list = []
    end

    if haskey(data_dict, "VehicleSubsidy")
        vehicle_subsidy_list = [
            VehicleSubsidy(
                vehicle_subsidy["id"],
                vehicle_subsidy["name"],
                vehicle_subsidy["years"],
                techvehicle_list[findfirst(tv -> tv.id == vehicle_subsidy["techvehicle"], techvehicle_list)],
                vehicle_subsidy["subsidy"],
                
            ) for vehicle_subsidy ∈ data_dict["VehicleSubsidy"]
        ]
    else
        vehicle_subsidy_list = []
    end
    # TODO: extend here the list of possible data_dict structures

    data_structures = Dict(
        "Y" => data_dict["Model"]["Y"],
        "y_init" => data_dict["Model"]["y_init"],
        "prey_y" => data_dict["Model"]["pre_y"],
        "gamma" => data_dict["Model"]["gamma"],
        "budget_constraint_penalty_plus" => data_dict["Model"]["budget_constraint_penalty_plus"],
        "budget_constraint_penalty_minus" => data_dict["Model"]["budget_constraint_penalty_minus"],
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
        "speed_list" => speed_list,
        "market_share_list" => market_share_list,
        "emission_constraints_by_mode_list" => emission_constraint_by_year_list,
        "mode_shares_list" => mode_shares_list,
        "max_mode_shares_list" => max_mode_shares_list,
        "min_mode_shares_list" => min_mode_shares_list,
        "initalfuelinginfr_list" => initalfuelinginfr_list,
        "initialmodeinfr_list" => initialmodeinfr_list,
        "vehicle_subsidy_list" => vehicle_subsidy_list,
        "geographic_element_list" => geographic_element_list,
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
        el ∈ k.sequence if el.type == "edge"
    )
    return p_r_k_e_pairs
end

"""
	create_p_r_k_g_set(odpairs::Vector{Odpair})

Creates a set of pairs of product, odpair, path, and element IDs.

# Arguments
- odpairs::Vector{Odpair}: list of odpairs

# Returns
- p_r_k_g_pairs::Set: set of pairs of product, odpair, path, and element IDs
"""
function create_p_r_k_g_set(odpairs::Vector{Odpair})
    p_r_k_g_pairs = Set(
        (r.product.id, r.id, k.id, el) for r ∈ odpairs for k ∈ r.paths for
        el ∈ k.sequence
    )
    return p_r_k_g_pairs
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
        el ∈ k.sequence if el.type == "node"
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
    depreciation_factor(y, g)

Calculate the depreciation factor for a vehicle based on its age.

# Arguments
- `y::Int`: The year of the vehicle.
- `g::Int`: The year the vehicle was purchased.

# Returns
- `Float64`: The depreciation factor.
"""
function depreciation_factor(y, g)
    age = y - g  # Lifetime of the vehicle
    if age == 0
        return 1.0  # No depreciation in the first year
    elseif age == 1
        return 0.75  # 25% depreciation in the second year
    else
        return max(0, 0.75 - 0.05 * (age - 1))  # Decrease by 5% for each subsequent year
    end
end

"""
    create_emission_price_along_path(k::Path, data_structures::Dict)

Calculating the carbon price along a given route based on the regions that the path lies in.
(currently simple calculation by averaging over all geometric items among the path).

# Arguments
- k::Path: path
- data_structures::Dict: dictionary with the input data 
"""
function create_emission_price_along_path(k::Path, data_structures::Dict)

    n = length(k.sequence)
    geographic_element_list = data_structures["geographic_element_list"]
    total_carbon_price = 0.0
    for el ∈ k.sequence
        current_carbon_price = geographic_element_list[findfirst(e -> e.id == el, node_list)].carbon_price
        global total_carbon_price += current_carbon_price        
    end
    average_carbon_price = total_carbon_price / n
    
    return average_carbon_price
end

"""
	save_results(model::Model, case_name::String)

Saves the results of the optimization model to YAML files.

# Arguments
- model::Model: JuMP model
- case_name::String: name of the case
- file_for_results::String: name of the file to save the results
"""
function save_results(model::Model, case_name::String, folder_for_results::String)
    check_folder_writable(folder_for_results)

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

    YAML.write_file(joinpath(folder_for_results, case * "_f_dict.yaml"), f_dict_str)
    @info "f_dict.yaml written successfully"

    YAML.write_file(joinpath(folder_for_results, case * "_h_dict.yaml"), h_dict_str)
    @info "h_dict.yaml written successfully"

    YAML.write_file(
        joinpath(folder_for_results, case * "_h_exist_dict.yaml"),
        h_exist_dict_str,
    )
    @info case * "_h_exist_dict.yaml written successfully"

    YAML.write_file(
        joinpath(folder_for_results, case * "_h_plus_dict.yaml"),
        h_plus_dict_str,
    )
    @info case * "_h_plus_dict.yaml written successfully"

    YAML.write_file(
        joinpath(folder_for_results, case * "_h_minus_dict.yaml"),
        h_minus_dict_str,
    )
    @info "h_minus_dict.yaml written successfully"

    YAML.write_file(joinpath(folder_for_results, case * "_s_e_dict.yaml"), s_e_dict_str)
    @info "s_e_dict.yaml written successfully"

    YAML.write_file(joinpath(folder_for_results, case * "_s_n_dict.yaml"), s_n_dict_str)
    @info "s_n_dict.yaml written successfully"

    YAML.write_file(
        joinpath(folder_for_results, case * "_q_fuel_infr_plus_e_dict.yaml"),
        q_fuel_infr_plus_e_dict_str,
    )
    @info "q_fuel_infr_plus_e_dict.yaml written successfully"

    YAML.write_file(
        joinpath(folder_for_results, case * "_q_fuel_infr_plus_n_dict.yaml"),
        q_fuel_infr_plus_n_dict_str,
    )
    @info "q_fuel_infr_plus_n_dict.yaml written successfully"

    YAML.write_file(
        joinpath(folder_for_results, case * "_budget_penalty_plus_dict.yaml"),
        budget_penalty_plus_dict_str,
    )
    @info "budget_penalty_plus_dict.yaml written successfully"

    YAML.write_file(
        joinpath(folder_for_results, case * "_budget_penalty_minus_dict.yaml"),
        budget_penalty_minus_dict_str,
    )
    @info "budget_penalty_minus_dict.yaml written successfully"
end
