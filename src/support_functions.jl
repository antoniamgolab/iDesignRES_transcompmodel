"""
This file contains the functions that are used in the model but are not directly related to the optimization problem but are supporting functions for this.

"""

include("structs.jl")
using YAML, JuMP, Printf

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
    # checking completion of model parametrization 
    check_model_parametrization(
        data_dict,
        ["Y", "y_init", "pre_y", "gamma", "budget_penalty_plus", "budget_penalty_minus"],
    )
    # check each of the required keys 
    check_required_sub_keys(
        data_dict,
        ["id", "type", "name", "carbon_price", "from", "to", "length"],
        "GeographicElement",
    )
    check_required_sub_keys(
        data_dict,
        [
            "id",
            "name",
            "VoT",
            "monetary_budget_purchase",
            "monetary_budget_purchase_lb",
            "monetary_budget_purchase_ub",
        ],
        "FinancialStatus",
    )
    check_required_sub_keys(
        data_dict,
        [
            "id",
            "name",
            "quantify_by_vehs",
            "costs_per_ukm",
            "emission_factor",
            "infrastructure_expansion_costs",
            "infrastructure_om_costs",
            "waiting_time",
        ],
        "Mode",
    )
    check_required_sub_keys(data_dict, ["id", "name"], "Product")
    check_required_sub_keys(data_dict, ["id", "name", "sequence", "length"], "Path")
    check_required_sub_keys(
        data_dict,
        [
            "id",
            "name",
            "cost_per_kWh",
            "cost_per_kW",
            "emission_factor",
            "fueling_infrastructure_om_costs",
        ],
        "Fuel",
    )
    check_required_sub_keys(data_dict, ["id", "name", "fuel"], "Technology")
    check_required_sub_keys(data_dict, ["id", "name", "mode"], "Vehicletype")
    check_required_sub_keys(
        data_dict,
        ["id", "name", "costs_var", "costs_fix"],
        "Regiontype",
    )
    check_required_sub_keys(
        data_dict,
        [
            "id",
            "name",
            "vehicle_type",
            "technology",
            "capital_cost",
            "maintnanace_cost_annual",
            "maintnance_cost_distance",
            "W",
            "spec_cons",
            "Lifetime",
            "AnnualRange",
            "products",
            "tank_capacity",
            "peak_fueling",
            "fueling_time",
        ],
        "TechVehicle",
    )
    check_required_sub_keys(
        data_dict,
        ["id", "techvehicle", "year_of_purchase", "stock"],
        "InitialVehicleStock",
    )
    check_required_sub_keys(
        data_dict,
        ["id", "fuel", "allocation", "installed_kW"],
        "InitialFuelingInfr",
    )
    check_required_sub_keys(
        data_dict,
        ["id", "mode", "allocation", "installed_ukm"],
        "InitialModeInfr",
    )
    check_required_sub_keys(
        data_dict,
        [
            "id",
            "from",
            "to",
            "path_id",
            "F",
            "product",
            "vehicle_stock_init",
            "financial_status",
            "region_type",
        ],
        "Odpair",
    )
    check_required_sub_keys(
        data_dict,
        ["id", "region_type", "vehicle_type", "travel_speed"],
        "Speed",
    )

    check_validity_of_model_parametrization(data_dict)
    check_uniquness_of_ids(data_dict, struct_names_base)

    res = data_dict["Model"]["Y"] + data_dict["Model"]["y_init"]
    @info "The optimization horizon is $(data_dict["Model"]["y_init"]) - $res."
    first_gen = data_dict["Model"]["y_init"] - data_dict["Model"]["pre_y"]
    @info "Vehicle generations since $first_gen are considered."

    # checking formats
    check_correct_formats_GeographicElement(data_dict, data_dict["Model"]["Y"])
    check_correct_formats_FinancialStatus(data_dict)
    check_correct_format_Mode(data_dict, data_dict["Model"]["Y"])
    check_correct_format_Product(data_dict)
    check_correct_format_Path(data_dict)
    check_correct_format_Fuel(data_dict, data_dict["Model"]["Y"])
    check_correct_format_Technology(data_dict)
    check_correct_format_Vehicletype(data_dict)
    check_correct_format_Regiontype(data_dict, data_dict["Model"]["Y"])
    check_correct_format_TechVehicle(
        data_dict,
        data_dict["Model"]["Y"],
        data_dict["Model"]["Y"] + data_dict["Model"]["pre_y"],
    )
    check_correct_format_InitialVehicleStock(
        data_dict,
        data_dict["Model"]["y_init"],
        first_gen,
    )
    check_correct_format_InitialFuelingInfr(data_dict)
    check_correct_format_InitialModeInfr(data_dict)
    check_correct_format_Odpair(data_dict, data_dict["Model"]["Y"])
    check_correct_format_Speed(data_dict)

    # printing key information for the user 

    @info "Input data checks successfully completed."

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
    geographic_element_list = [
        GeographicElement(
            geographic_element["id"],
            geographic_element["type"],
            geographic_element["name"],
            geographic_element["carbon_price"],
            geographic_element["from"],
            geographic_element["to"],
            geographic_element["length"],
        ) for geographic_element ∈ data_dict["GeographicElement"]
    ]
    financial_status_list = [
        FinancialStatus(
            financial_stat["id"],
            financial_stat["name"],
            financial_stat["VoT"],
            financial_stat["monetary_budget_purchase"],
            financial_stat["monetary_budget_purchase_lb"],
            financial_stat["monetary_budget_purchase_ub"],
            financial_stat["monetary_budget_purchase_time_horizon"],
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
            mode["waiting_time"],
        ) for mode ∈ data_dict["Mode"]
    ]

    product_list =
        [Product(product["id"], product["name"]) for product ∈ data_dict["Product"]]
    path_list = [
        Path(
            path["id"],
            path["name"],
            path["length"],
            [
                geographic_element_list[findfirst(
                    geo -> geo.id == el,
                    geographic_element_list,
                )] for el ∈ path["sequence"]
            ],
        ) for path ∈ data_dict["Path"]
    ]
    fuel_list = [
        Fuel(
            fuel["id"],
            fuel["name"],
            fuel["cost_per_kWh"],
            fuel["cost_per_kW"],
            fuel["emission_factor"],
            fuel["fueling_infrastructure_om_costs"],
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
            techvehicle["tank_capacity"],
            techvehicle["peak_fueling"],
            techvehicle["fueling_time"],
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
            fuel_list[findfirst(f -> f.name == initalfuelinginfr["fuel"], fuel_list)],
            initalfuelinginfr["allocation"],
            initalfuelinginfr["installed_kW"],
        ) for initalfuelinginfr ∈ data_dict["InitialFuelingInfr"]
    ]
    initialmodeinfr_list = [
        InitialModeInfr(
            initialmodeinfr["id"],
            mode_list[findfirst(m -> m.id == initialmodeinfr["mode"], mode_list)],
            initialmodeinfr["allocation"],
            initialmodeinfr["installed_ukm"],
        ) for initialmodeinfr ∈ data_dict["InitialModeInfr"]
    ]

    odpair_list = [
        Odpair(
            odpair["id"],
            geographic_element_list[findfirst(
                nodes -> nodes.id == odpair["from"],
                geographic_element_list,
            )],
            geographic_element_list[findfirst(
                nodes -> nodes.id == odpair["to"],
                geographic_element_list,
            )],
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
            odpair["travel_time_budget"]
        ) for odpair ∈ data_dict["Odpair"]
    ]

    # odpair_list = odpair_list[1:20]
    @info "The number of OD pairs is $(length(odpair_list))."
    speed_list = [
        Speed(
            speed["id"],
            regiontype_list[findfirst(
                rt -> rt.name == speed["region_type"],
                regiontype_list,
            )],
            vehicle_type_list[findfirst(
                vt -> vt.name == speed["vehicle_type"],
                vehicle_type_list,
            )],
            speed["travel_speed"],
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
                [
                    regiontype_list[findfirst(rt -> rt.id == rt_id, regiontype_list)]
                    for rt_id ∈ mode_share["regiontype_list"]
                ],
            ) for mode_share ∈ data_dict["Mode_shares"]
        ]
        @info "Mode shares are defined by year"

    else
        mode_shares_list = []
    end

    if haskey(data_dict, "Mode_share_max_by_year")
        max_mode_shares_list = [
            ModeShare(
                mode_share["id"],
                mode_list[findfirst(m -> m.id == mode_share["mode"], mode_list)],
                mode_share["share"],
                mode_share["year"],
                [
                    regiontype_list[findfirst(rt -> rt.id == rt_id, regiontype_list)]
                    for rt_id ∈ mode_share["regiontype_list"]
                ],
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
                [
                    regiontype_list[findfirst(rt -> rt.id == rt_id, regiontype_list)]
                    for rt_id ∈ mode_share["regiontype_list"]
                ],
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
                techvehicle_list[findfirst(
                    tv -> tv.id == vehicle_subsidy["techvehicle"],
                    techvehicle_list,
                )],
                vehicle_subsidy["subsidy"],
            ) for vehicle_subsidy ∈ data_dict["VehicleSubsidy"]
        ]
    else
        vehicle_subsidy_list = []
    end

    if haskey(data_dict, "InitDetourTime")
        init_detour_times_list = [
            InitDetourTime(
                init_detour_time["id"],
                fuel_list[findfirst(f -> f.name == init_detour_time["fuel"], fuel_list)],
                geographic_element_list[findfirst(
                    ge -> ge.name == init_detour_time["location"],
                    geographic_element_list,
                )],
                init_detour_time["detour_time"],
            ) for init_detour_time ∈ data_dict["InitDetourTime"]
        ]
    else
        init_detour_times_list = []
    end

    if haskey(data_dict, "DetourTimeReduction")
        @info "has detour reduction specified"
        detour_time_reduction_list = [
            DetourTimeReduction(
                detour_time_reduction["id"],
                fuel_list[findfirst(
                    f -> f.name == detour_time_reduction["fuel"],
                    fuel_list,
                )],
                geographic_element_list[findfirst(
                    ge -> ge.name == detour_time_reduction["location"],
                    geographic_element_list,
                )],
                detour_time_reduction["reduction_id"],
                detour_time_reduction["detour_time_reduction"],
                detour_time_reduction["fueling_cap_lb"],
                detour_time_reduction["fueling_cap_ub"],
            ) for detour_time_reduction ∈ data_dict["DetourTimeReduction"]
        ]
    else
        detour_time_reduction_list = []
    end



    if haskey(data_dict, "SupplyType")
        supplytype_list = [
            SupplyType(
                item["id"],
                fuel_list[findfirst(
                    f -> f.name == item["fuel"],
                    fuel_list,
                )],
                geographic_element_list[findfirst(
                    ge -> ge.name == item["location"],
                    geographic_element_list,
                )],
                item["install_costs"],
                item["om_costs"],
            ) for item ∈ data_dict["SupplyType"]
        ]
    else
        supplytype_list = []
    end

    if haskey(data_dict, "InitialSupplyInfr")
        initialsupplyinfr_list = [
            EmissionConstraintByYear(
                item["id"],
                fuel_list[findfirst(
                    f -> f.name == item["fuel"],
                    fuel_list,
                )],
                supplytype_list[findfirst(
                    st -> st.id == item["supplytype"],
                    supplytype_list,
                )],
                geographic_element_list[findfirst(
                    ge -> ge.name == item["location"],
                    geographic_element_list,
                )],
                item["installed_kW"],
            ) for item ∈ data_dict["InitialSupplyInfr"]
        ]
    else
        initialsupplyinfr_list = []
    end

    # TODO: extend here the list of possible data_dict structures
    data_structures = Dict(
        "Y" => data_dict["Model"]["Y"],
        "y_init" => data_dict["Model"]["y_init"],
        "pre_y" => data_dict["Model"]["pre_y"],
        "gamma" => data_dict["Model"]["gamma"],
        "discount_rate" => data_dict["Model"]["discount_rate"],
        "budget_penalty_plus" => data_dict["Model"]["budget_penalty_plus"],
        "budget_penalty_minus" => data_dict["Model"]["budget_penalty_minus"],
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
        "emission_constraints_by_mode_list" => emission_constraint_by_mode_list,
        "mode_shares_list" => mode_shares_list,
        "max_mode_shares_list" => max_mode_shares_list,
        "min_mode_shares_list" => min_mode_shares_list,
        "initialfuelinginfr_list" => initalfuelinginfr_list,
        "initialmodeinfr_list" => initialmodeinfr_list,
        "initialsupplyinfr_list" => initialsupplyinfr_list,
        "vehicle_subsidy_list" => vehicle_subsidy_list,
        "geographic_element_list" => geographic_element_list,
        "init_detour_times_list" => init_detour_times_list,
        "detour_time_reduction_list" => detour_time_reduction_list,
        "supplytype_list" => supplytype_list,
    )

    for key ∈ keys(default_data)
        if haskey(data_dict["Model"], key)
            data_structures[key] = data_dict["Model"][key]
        else
            data_structures[key] = default_data[key]
        end
    end

    data_structures["G"] = data_dict["Model"]["pre_y"] + data_dict["Model"]["Y"]
    data_structures["g_init"] = data_dict["Model"]["y_init"] - data_dict["Model"]["pre_y"]
    data_structures["Y_end"] = data_dict["Model"]["y_init"] + data_dict["Model"]["Y"] - 1

    return data_structures
end
"""
    generate_exact_length_subsets(start_year::Int, end_year::Int, delta_y::Int)

Generates a list of subsets of years with a fixed length.

# Arguments
- `start_year::Int`: The first year.
- `end_year::Int`: The last year.
- `delta_y::Int`: The length of the subsets.
"""
function generate_exact_length_subsets(start_year::Int, end_year::Int, delta_y::Int)
    all_years = start_year:end_year
    subsets = []

    for i ∈ 1:(length(all_years)-delta_y+1)
        push!(subsets, collect(all_years[i:(i+delta_y-1)]))
    end

    return subsets
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
        (r.product.id, r.id, k.id, el.id) for r ∈ odpairs for k ∈ r.paths for
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
function create_model(data_structures, case_name::String, optimizer)
    model = Model(optimizer)
    base_define_variables(model, data_structures)
    return model, data_structures
end

function create_geo_i_pairs(
    geographic_element_list::Vector{GeographicElement},
    detour_time_reduction_list::Vector{DetourTimeReduction},
)
    geo_i_pairs = Set(
        (geo.id, i.reduction_id) for geo ∈ geographic_element_list for
        i ∈ detour_time_reduction_list[findall(
            item -> item.location == geo.id,
            detour_time_reduction_list,
        )]
    )
    return geo_i_pairs
end

function create_geo_i_f_pairs(
    geographic_element_list::Vector{GeographicElement},
    detour_time_reduction_list::Vector{DetourTimeReduction},
)
    geo_i_f_pairs = Set()
    for item ∈ detour_time_reduction_list
        push!(geo_i_f_pairs, (item.location.id, item.reduction_id, item.fuel.id))
    end
    return geo_i_f_pairs
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
    create_emission_price_along_path(k::Path, y::Int64, data_structures::Dict)

Calculating the carbon price along a given route based on the regions that the path lies in.
(currently simple calculation by averaging over all geometric items among the path).

# Arguments
- k::Path: path
- data_structures::Dict: dictionary with the input data 
"""
function create_emission_price_along_path(k::Path, y::Int64, data_structures::Dict)
    n = length(k.sequence)
    geographic_element_list = data_structures["geographic_element_list"]
    global total_carbon_price = 0.0
    for el ∈ k.sequence
        current_carbon_price =
            geographic_element_list[findfirst(
                e -> e.id == el.id,
                geographic_element_list,
            )].carbon_price
        # println(current_carbon_price, total_carbon_price)
        global total_carbon_price = total_carbon_price + current_carbon_price[y]
    end
    average_carbon_price = total_carbon_price / n
    # println(average_carbon_price)
    return average_carbon_price
end

"""
	save_results(model::Model, case_name::String)

Saves the results of the optimization model to YAML files.

# Arguments
- model::Model: JuMP model
- case_name::String: name of the case
- file_for_results::String: name of the file to save the results
- data_structures::Dict: dictionary with the input data
"""
function save_results(
    model::Model,
    case::String,
    data_structures::Dict,
    write_to_file::Bool = true,
    folder_for_results::String = "results",
)
    check_folder_writable(folder_for_results)

    y_init = data_structures["y_init"]
    Y_end = data_structures["Y_end"]
    odpairs = data_structures["odpair_list"]
    techvehicles = data_structures["techvehicle_list"]
    m_tv_pairs = data_structures["m_tv_pairs"]
    p_r_k_pairs = data_structures["p_r_k_pairs"]
    p_r_k_g_pairs = data_structures["p_r_k_g_pairs"]
    technologies = data_structures["technology_list"]
    fuel_list = data_structures["fuel_list"]
    mode_list = data_structures["mode_list"]
    geographic_element_list = data_structures["geographic_element_list"]
    tech_vehicle_ids = data_structures["techvehicle_ids"]
    g_init = data_structures["g_init"]
    if data_structures["detour_time_reduction_list"] != []
        geo_i_pairs = data_structures["geo_i_pairs"]
        geo_i_f = data_structures["geo_i_f_pairs"]
    end

    # Writing the solved decision variables to YAML
    solved_data = Dict()
    solved_data["h"] = value.(model[:h])
    solved_data["h_plus"] = value.(model[:h_plus])
    solved_data["h_minus"] = value.(model[:h_minus])
    solved_data["h_exist"] = value.(model[:h_exist])
    solved_data["f"] = value.(model[:f])
    solved_data["budget_penalty_plus"] = value.(model[:budget_penalty_plus])
    solved_data["budget_penalty_minus"] = value.(model[:budget_penalty_minus])
    solved_data["s"] = value.(model[:s])
    solved_data["q_fuel_infr_plus"] = value.(model[:q_fuel_infr_plus])
    solved_data["q_mode_infr_plus"] = value.(model[:q_fuel_infr_plus])

    f_dict = Dict()
    for y ∈ y_init:Y_end, (p, r, k) ∈ p_r_k_pairs, mv ∈ m_tv_pairs, g ∈ g_init:y
        f_dict[(y, (p, r, k), mv, g)] = value(model[:f][y, (p, r, k), mv, g])
    end

    s_dict = Dict()
    for y ∈ y_init:Y_end, (p, r, k, g) ∈ p_r_k_g_pairs, tv_id ∈ tech_vehicle_ids
        s_dict[(y, (p, r, k, g), tv_id)] = value(model[:s][y, (p, r, k, g), tv_id])
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

    # Dictionary for 'q_fuel_infr_plus_e' variable
    q_mode_infr_plus_dict = Dict()
    for y ∈ y_init:Y_end, m ∈ mode_list, geo ∈ geographic_element_list
        q_mode_infr_plus_dict[(y, m.id, geo.id)] =
            value(model[:q_mode_infr_plus][y, m.id, geo.id])
    end

    # Dictionary for 'q_fuel_infr_plus_n' variable
    q_fuel_infr_plus_dict = Dict()
    for y ∈ y_init:Y_end, f ∈ fuel_list, geo ∈ geographic_element_list
        q_fuel_infr_plus_dict[(y, f.id, geo.id)] =
            value(model[:q_fuel_infr_plus][y, f.id, geo.id])
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
    s_dict_str = stringify_keys(s_dict)
    q_fuel_infr_plus_dict_str = stringify_keys(q_fuel_infr_plus_dict)
    q_mode_infr_plus_dict_str = stringify_keys(q_mode_infr_plus_dict)

    budget_penalty_plus_dict_str = stringify_keys(budget_penalty_plus_dict)
    budget_penalty_minus_dict_str = stringify_keys(budget_penalty_minus_dict)

    if data_structures["detour_time_reduction_list"] != []
        # Dictionary for 'detour_times' variable
        detour_time_dict = Dict()
        for y ∈ y_init:Y_end, p_r_k ∈ p_r_k_g_pairs, f ∈ fuel_list
            detour_time_dict[(y, p_r_k, f.id)] = value(model[:detour_time][y, p_r_k, f.id])
        end

        detour_time_dict_str = stringify_keys(detour_time_dict)
        x_a_dict = Dict()
        for y ∈ y_init:Y_end, g ∈ geo_i_f
            x_a_dict[(y, g)] = value(model[:x_a][y, g])
        end
        x_a_dict_str = stringify_keys(x_a_dict)

        x_b_dict = Dict()
        for y ∈ y_init:Y_end, g ∈ geo_i_f
            x_b_dict[(y, g)] = value(model[:x_b][y, g])
        end
        x_b_dict_str = stringify_keys(x_b_dict)
        x_c_dict = Dict()
        for y ∈ y_init:Y_end, g ∈ geo_i_f
            x_c_dict[(y, g)] = value(model[:x_c][y, g])
        end
        x_c_dict_str = stringify_keys(x_c_dict)
        n_fueling_dict = Dict()
        for y ∈ y_init:Y_end, (p, r, k, g) ∈ p_r_k_g_pairs, f ∈ fuel_list
            n_fueling_dict[(y, (p, r, k, g), f.id)] =
                value(model[:n_fueling][y, (p, r, k, g), f.id])
        end

        z_str = Dict()
        for y ∈ y_init:Y_end, (p, r, k, g) ∈ p_r_k_g_pairs, geo ∈ geo_i_f
            z_str[(y, geo, (p, r, k, g))] = value(model[:z][y, geo, (p, r, k, g)])
        end
        z_str = stringify_keys(z_str)
    end

    if data_structures["supplytype_list"] != []
        supplytype_list = data_structures["supplytype_list"]
        q_supply_infr_dict = Dict()
        for y ∈ y_init:Y_end, st ∈ supplytype_list, geo ∈ geographic_element_list
            q_supply_infr_dict[(y, st.id, geo.id)] = value(model[:q_supply_infr][y, st.id, geo.id])
        end
        q_supply_infr_dict_str = stringify_keys(q_supply_infr_dict)
    end
    if write_to_file
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

        YAML.write_file(
            joinpath(folder_for_results, case * "_q_fuel_infr_plus_dict.yaml"),
            q_fuel_infr_plus_dict_str,
        )
        @info "q_fuel_infr_plus_dict.yaml written successfully"

        YAML.write_file(
            joinpath(folder_for_results, case * "_q_mode_infr_plus_dict.yaml"),
            q_mode_infr_plus_dict_str,
        )
        @info "q_mode_infr_dict.yaml written successfully"

        YAML.write_file(
            joinpath(folder_for_results, case * "_budget_penalty_plus_dict.yaml"),
            budget_penalty_plus_dict_str,
        )
        @info "budget_penalty_plus_dict.yaml written successfully"

        YAML.write_file(
            joinpath(folder_for_results, case * "_budget_penalty_minus_dict.yaml"),
            budget_penalty_minus_dict_str,
        )
        YAML.write_file(joinpath(folder_for_results, case * "_s.yaml"), s_dict_str)
        @info "s.yaml written successfully"
        if data_structures["detour_time_reduction_list"] != []
            YAML.write_file(
                joinpath(folder_for_results, case * "_detour_time_dict.yaml"),
                detour_time_dict_str,
            )
            @info "detour_time_dict.yaml written successfully"

            @info "x_dict.yaml written successfully"
            YAML.write_file(
                joinpath(folder_for_results, case * "_x_a_dict.yaml"),
                x_a_dict_str,
            )
            @info "x_a_dict.yaml written successfully"
            YAML.write_file(
                joinpath(folder_for_results, case * "_x_b_dict.yaml"),
                x_b_dict_str,
            )
            @info "x_b_dict.yaml written successfully"
            YAML.write_file(
                joinpath(folder_for_results, case * "_x_c_dict.yaml"),
                x_c_dict_str,
            )
            YAML.write_file(
                joinpath(folder_for_results, case * "_n_fueling_dict.yaml"),
                n_fueling_dict,
            )
            YAML.write_file(joinpath(folder_for_results, case * "_z_dict.yaml"), z_str)
        end
        if data_structures["supplytype_list"] != []
            YAML.write_file(
                joinpath(folder_for_results, case * "_q_supply_infr_dict.yaml"),
                q_supply_infr_dict_str,
            )
            @info "q_supply_infr_dict.yaml written successfully"
        end
    end

    return f_dict,
    h_dict,
    h_exist_dict,
    h_plus_dict,
    h_minus_dict,
    s_dict,
    q_fuel_infr_plus_dict,
    q_mode_infr_plus_dict,
    budget_penalty_plus_dict,
    budget_penalty_minus_dict
end
