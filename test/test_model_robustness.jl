function generate_data_case_tech_shift(W = 1)
    Y = 20
    pre_y = 5
    y_init = 2020
    g_init = y_init - pre_y
    Y_end = Y + y_init - 1

    geographic_element_list =
        [GeographicElement(1, "node", "Main area", fill(60.0, Y + 1), 1, 1, 4.0)]

    financial_status_list = [FinancialStatus(1, "Middle class", 15, 12000, 10000, 13000, 6)]

    mode_list = [
        Mode(
            1,
            "Road",
            true,
            fill(0.12, Y + 1),
            fill(263, Y + 1),
            fill(0.1, Y + 1),
            fill(0.2, Y + 1),
            fill(5, Y + 1),
        ),
        Mode(
            2,
            "Rail",
            false,
            fill(0.1, Y + 1),
            fill(0, Y + 1),
            fill(0.1, Y + 1),
            fill(0.2, Y + 1),
            fill(5, Y + 1),
        ),
    ]

    product_list = [Product(1, "passenger")]

    path_list = [Path(1, "1", 8, [geographic_element_list[1]])]

    fuel_list = [
        Fuel(
            1,
            "petrol",
            fill(5, Y + 1),
            fill(10, Y + 1),
            fill(0, Y + 1),
            fill(0.1, Y + 1),
        ),
        Fuel(
            2,
            "electricity",
            fill(4, Y + 1),
            fill(350, Y + 1),
            fill(0, Y + 1),
            fill(0.1, Y + 1),
        ),
    ]

    technology_list = [
        Technology(1, "electric", fuel_list[1]),
        Technology(2, "cmobustion engine", fuel_list[1]),
    ]

    vehicle_type_list = [
        Vehicletype(1, "Car", mode_list[1], [product_list[1]]),
        Vehicletype(2, "Rail", mode_list[2], [product_list[1]]),
    ]

    regiontype_list = [Regiontype(1, "Urban", fill(0, Y), fill(0, Y))]
    println(Y + 1 + pre_y)
    println(Y + 1)
    techvehicle_list = [
        TechVehicle(
            1,
            "ICEV passenger car",
            vehicle_type_list[1],
            technology_list[1],
            fill(80000, Y + pre_y + 1),
            fill(fill(10, Y + 1), Y + 1 + pre_y),
            fill(fill(10, Y + 1), Y + 1 + pre_y),
            fill(W, Y + 1 + pre_y),
            fill(5, Y + 1 + pre_y),
            fill(2, Y + 1 + pre_y),
            fill(10000, Y + pre_y + 1),
            [product_list[1]],
            fill(100, Y + 1 + pre_y),
            fill(30, Y + 1 + pre_y),
            fill(5 / 60, Y + 1 + pre_y),
        ),
        TechVehicle(
            2,
            "BEV passenger car",
            vehicle_type_list[1],
            technology_list[2],
            fill(60000, Y + pre_y + 1),
            fill(fill(10, Y + 1), Y + 1 + pre_y),
            fill(fill(10, Y + 1), Y + 1 + pre_y),
            fill(W, Y + 1 + pre_y),
            fill(5, Y + 1 + pre_y),
            fill(2, Y + 1 + pre_y),
            fill(10000, Y + pre_y + 1),
            [product_list[1]],
            fill(100, Y + 1 + pre_y),
            fill(30, Y + 1 + pre_y),
            fill(5 / 60, Y + 1 + pre_y),
        ),
    ]
    total_vehs = 0.08 / W
    initvehiclestock_list = [
        InitialVehicleStock(1, techvehicle_list[1], 2014, total_vehs / pre_y),
        InitialVehicleStock(2, techvehicle_list[1], 2015, total_vehs / pre_y),
        InitialVehicleStock(3, techvehicle_list[1], 2016, total_vehs / pre_y),
        InitialVehicleStock(4, techvehicle_list[1], 2017, total_vehs / pre_y),
        InitialVehicleStock(5, techvehicle_list[1], 2018, total_vehs / pre_y),
        InitialVehicleStock(6, techvehicle_list[1], 2019, total_vehs / pre_y),
        InitialVehicleStock(7, techvehicle_list[2], 2014, 0),
        InitialVehicleStock(8, techvehicle_list[2], 2015, 0),
        InitialVehicleStock(9, techvehicle_list[2], 2016, 0),
        InitialVehicleStock(10, techvehicle_list[2], 2017, 0),
        InitialVehicleStock(11, techvehicle_list[2], 2018, 0),
        InitialVehicleStock(12, techvehicle_list[2], 2019, 0),
    ]
    initialmodeinfr_list =
        [InitialModeInfr(1, mode_list[1], 1, 0), InitialModeInfr(2, mode_list[2], 1, 0)]

    initialfuelinginfr_list = [
        InitialFuelingInfr(1, fuel_list[1], 1, 0),
        InitialFuelingInfr(2, fuel_list[2], 1, 0),
    ]

    odpair_list = [
        Odpair(
            1,
            geographic_element_list[1],
            geographic_element_list[1],
            [path_list[1]],
            fill(100, Y + 1),
            product_list[1],
            initvehiclestock_list,
            financial_status_list[1],
            regiontype_list[1],
            120,
        ),
    ]
    speed_list = [
        Speed(1, regiontype_list[1], vehicle_type_list[1], 60),
        # Speed(2, regiontype_list[1], vehicle_type_list[2], 80),
    ]
    return data_structures = Dict(
        "Y" => Y,
        "y_init" => y_init,
        "pre_y" => pre_y,
        "Y_end" => Y + y_init - 1,
        "g_init" => y_init - pre_y,
        "gamma" => 0.0001,
        "budget_penalty_plus" => 100,
        "budget_penalty_minus" => 100,
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
        "market_share_list" => [],
        "emission_constraints_by_mode_list" => [],
        "mode_shares_list" => [],
        "max_mode_shares_list" => [],
        "min_mode_shares_list" => [],
        "initialfuelinginfr_list" => initialfuelinginfr_list,
        "initialmodeinfr_list" => initialmodeinfr_list,
        "vehicle_subsidy_list" => [],
        "geographic_element_list" => geographic_element_list,
        "init_detour_times_list" => [],
        "detour_time_reduction_list" => [],
        "alpha_f" => 1,
        "alpha_h" => 0.5,
        "beta_h" => 0.5,
        "beta_f" => 1,
        "discount_rate" => 0,
        "supplytype_list" => [],
        "initialsupplyinfr_list" => [],
    )
end


function apply_modeling(data_structures::Dict, case_name::String = "test_case")
    model, data_structures_v2 = create_model(data_structures, case_name, HiGHS.Optimizer)
    constraint_demand_coverage(model, data_structures)
    constraint_vehicle_sizing(model, data_structures)
    constraint_vehicle_aging(model, data_structures)
    constraint_vehicle_stock_shift(model, data_structures)
    constraint_mode_shift(model, data_structures)
    constraint_fueling_demand(model, data_structures)
    constraint_fueling_infrastructure(model, data_structures)
    objective(model, data_structures)
    optimize!(model)
    return model, data_structures_v2
end

"""
Using the `minimum viable case` that is defined and tested in the `test_minimum_viable_case.jl` file, parameters are changed and adapted to test the robustness and validity of the model.
The minimum viable case was tested for the core functionalities of the model. 
A set of key parameters that budget_penalty_minus_dict_str that are driving the model results is defined and altered, which are:
    - [costs] modal and technology shift are mainly driven by cost components
    - [socio-economic parameters] modal and technology shift are also effected by demand elasticity
    - [technological parameters] the amount of vehicles in the system and transition to other technology/mode is highly affected by the lifetime of vehicles
    - [tech/socio-economic parameter] the efficiency of a vehicle is affected by the assumed load factor of it
"""

@testset "Model robustness" begin
    Y = 20
    y_init = 2020
    pre_y = 5
    g_init = y_init - pre_y
    Y_end = Y + y_init - 1
    results_file_path = normpath(joinpath(@__DIR__, "results/"))

    data_structures_original = generate_data_case_tech_shift()

    # costs are increased for public transport, so that the model share stays at 100% for public transport
    data_structures_v2 = deepcopy(data_structures_original)
    case_name = "high_public_transport_costs"
    mode_list = [
        Mode(
            1,
            "Road",
            true,
            fill(0.12, Y + 1),
            fill(263, Y + 1),
            fill(0.1, Y + 1),
            fill(0.2, Y + 1),
            fill(5, Y + 1),
        ),
        Mode(
            2,
            "Rail",
            false,
            fill(100, Y + 1),
            fill(0.2, Y + 1),
            fill(0.1, Y + 1),
            fill(0.2, Y + 1),
            fill(5, Y + 1),
        ),
    ]
    data_structures_v2["mode_list"] = mode_list

    model, data_structures_v2 = apply_modeling(data_structures_v2, case_name)
    f_dict,
    h_dict,
    h_exist_dict,
    h_plus_dict,
    h_minus_dict,
    s_dict,
    q_fuel_infr_plus_dict,
    q_mode_infr_plus_dict,
    budget_penalty_plus_dict,
    budget_penalty_minus_dict =
        save_results(model, case_name, data_structures_v2, true, results_file_path)

    p_r_k_pairs = create_p_r_k_set(data_structures_v2["odpair_list"])
    m_tv_pairs = create_m_tv_pairs(
        data_structures_v2["techvehicle_list"],
        data_structures_v2["mode_list"],
    )
    g_init = data_structures_v2["g_init"]
    Y_end = data_structures_v2["Y_end"]
    y_init = data_structures_v2["y_init"]
    odpair_list = data_structures_v2["odpair_list"]
    techvehicle_list = data_structures_v2["techvehicle_list"]
    # expected outcome: mode shift of 1 == 100% at Y_end
    @test (
        round(
            sum(
                f_dict[(y_init, (prk), mv, g)] for prk ∈ p_r_k_pairs for mv ∈ m_tv_pairs for
                g ∈ g_init:y_init if mv[1] == 1
            ),
        ) == 100
    )

    # demand elasticity parameters are altered for mode shift, indicating a fast slower transition to public transport 
    case_name3 = "low_demand_elasticity"
    data_structures_v3 = deepcopy(data_structures_original)

    data_structures_v3["alpha_f"] = 0.001
    data_structures_v3["beta_f"] = 0.001

    model3, data_structures_v3 = apply_modeling(data_structures_v3)

    f_dict,
    h_dict,
    h_exist_dict,
    h_plus_dict,
    h_minus_dict,
    s_dict,
    q_fuel_infr_plus_dict,
    q_mode_infr_plus_dict,
    budget_penalty_plus_dict,
    budget_penalty_minus_dict =
        save_results(model3, case_name3, data_structures_v3, true, results_file_path)

    p_r_k_pairs = create_p_r_k_set(data_structures_v2["odpair_list"])
    m_tv_pairs = create_m_tv_pairs(
        data_structures_v2["techvehicle_list"],
        data_structures_v2["mode_list"],
    )
    g_init = data_structures_v2["g_init"]
    Y_end = data_structures_v2["Y_end"]
    y_init = data_structures_v2["y_init"]
    odpair_list = data_structures_v2["odpair_list"]
    techvehicle_list = data_structures_v2["techvehicle_list"]


    # expected outcome: mode shift of 2 == 100% at Y_end
    @test (
        round(
            sum(
                f_dict[(Y_end, (prk), mv, g)] for prk ∈ p_r_k_pairs for mv ∈ m_tv_pairs for
                g ∈ g_init:Y_end if mv[1] == 2
            ),
        ) == 92
    )


    case_name4 = "lifetime_expansion_of_vehicles"
    data_structures_v4 = generate_data_case_tech_shift()

    # adapting mode costs
    mode_list = [
        Mode(
            1,
            "Road",
            true,
            fill(0.12, Y + 1),
            fill(263, Y + 1),
            fill(0.1, Y + 1),
            fill(0.2, Y + 1),
            fill(5, Y + 1),
        ),
        Mode(
            2,
            "Rail",
            false,
            fill(100, Y + 1),
            fill(0.2, Y + 1),
            fill(0.1, Y + 1),
            fill(0.2, Y + 1),
            fill(5, Y + 1),
        ),
    ]
    data_structures_v4["mode_list"] = mode_list

    # adapting Lifetime of vehicles
    techvehicle_list = [
        TechVehicle(
            1,
            "ICEV passenger car",
            data_structures_v4["vehicletype_list"][1],
            data_structures_v4["technology_list"][1],
            fill(80000, Y + pre_y + 1),
            fill(fill(10, Y + 1), Y + 1 + pre_y),
            fill(fill(10, Y + 1), Y + 1 + pre_y),
            fill(1, Y + 1 + pre_y),
            fill(5, Y + 1 + pre_y),
            fill(20, Y + 1 + pre_y), # lifetime 
            fill(10000, Y + pre_y + 1),
            [data_structures_v4["product_list"][1]],
            fill(100, Y + 1 + pre_y),
            fill(30, Y + 1 + pre_y),
            fill(5 / 60, Y + 1 + pre_y),
        ),
        TechVehicle(
            2,
            "BEV passenger car",
            data_structures_v4["vehicletype_list"][1],
            data_structures_v4["technology_list"][1],
            fill(60000, Y + pre_y + 1),
            fill(fill(10, Y + 1), Y + 1 + pre_y),
            fill(fill(10, Y + 1), Y + 1 + pre_y),
            fill(1, Y + 1 + pre_y),
            fill(5, Y + 1 + pre_y),
            fill(20, Y + 1 + pre_y),
            fill(10000, Y + pre_y + 1),
            [data_structures_v4["product_list"][1]],
            fill(100, Y + 1 + pre_y),
            fill(30, Y + 1 + pre_y),
            fill(5 / 60, Y + 1 + pre_y),
        ),
    ]

    data_structures_v4["techvehicle_list"] = techvehicle_list
    model4, data_structures_v4 = apply_modeling(data_structures_v4)

    f_dict,
    h_dict,
    h_exist_dict,
    h_plus_dict,
    h_minus_dict,
    s_dict,
    q_fuel_infr_plus_dict,
    q_mode_infr_plus_dict,
    budget_penalty_plus_dict,
    budget_penalty_minus_dict =
        save_results(model4, case_name4, data_structures_v4, true, results_file_path)

    p_r_k_pairs = create_p_r_k_set(data_structures_v2["odpair_list"])
    m_tv_pairs = create_m_tv_pairs(
        data_structures_v2["techvehicle_list"],
        data_structures_v2["mode_list"],
    )
    g_init = data_structures_v2["g_init"]
    Y_end = data_structures_v2["Y_end"]
    y_init = data_structures_v2["y_init"]
    odpair_list = data_structures_v2["odpair_list"]
    techvehicle_list = data_structures_v2["techvehicle_list"]



    # checking that no vehicle are added to the system outside of y==g
    @test (
        round(
            sum(
                h_plus_dict[(y, r.id, tv.id, g)] for y ∈ y_init:Y_end for r ∈ odpair_list
                for tv ∈ techvehicle_list for g ∈ g_init:y if y != g
            ),
            digits = 2,
        ) == 0
    )

    # testing that the amount of vehicles in the system is equal to the initial amount of vehicles
    @test (
        round(
            sum(
                h_exist_dict[(y_init, r.id, tv.id, g)] for r ∈ odpair_list for
                tv ∈ techvehicle_list for g ∈ g_init:y_init if tv.id == 1
            ),
            digits = 2,
        ) == 0.08
    )

    # testing if end share of battery-electric vehicles is correct 
    @test (
        round(
            sum(
                h_exist_dict[(Y_end, r.id, tv.id, g)] for r ∈ odpair_list for
                tv ∈ techvehicle_list for g ∈ g_init:Y_end if tv.id == 2
            ),
            digits = 2,
        ) == 0.06
    )


    data_structures_v5 = generate_data_case_tech_shift(1.5)
    mode_list = [
        Mode(
            1,
            "Road",
            true,
            fill(0.12, Y + 1),
            fill(263, Y + 1),
            fill(0.1, Y + 1),
            fill(0.2, Y + 1),
            fill(5, Y + 1),
        ),
        Mode(
            2,
            "Rail",
            false,
            fill(100, Y + 1),
            fill(0.2, Y + 1),
            fill(0.1, Y + 1),
            fill(0.2, Y + 1),
            fill(5, Y + 1),
        ),
    ]
    data_structures_v5["mode_list"] = mode_list
    case_name5 = "load_factor_change"
    model5, data_structures_v5 = apply_modeling(data_structures_v5, case_name5)

    f_dict,
    h_dict,
    h_exist_dict,
    h_plus_dict,
    h_minus_dict,
    s_dict,
    q_fuel_infr_plus_dict,
    q_mode_infr_plus_dict,
    budget_penalty_plus_dict,
    budget_penalty_minus_dict =
        save_results(model5, case_name5, data_structures_v5, false, results_file_path)

    p_r_k_pairs = create_p_r_k_set(data_structures_v2["odpair_list"])
    m_tv_pairs = create_m_tv_pairs(
        data_structures_v2["techvehicle_list"],
        data_structures_v2["mode_list"],
    )
    g_init = data_structures_v2["g_init"]
    Y_end = data_structures_v2["Y_end"]
    y_init = data_structures_v2["y_init"]
    odpair_list = data_structures_v2["odpair_list"]
    techvehicle_list = data_structures_v2["techvehicle_list"]

    @test (
        round(
            sum(
                h_dict[(Y_end, r.id, tv.id, g)] for r ∈ odpair_list for
                tv ∈ techvehicle_list for g ∈ g_init:Y_end
            ),
            digits = 2,
        ) == 0.05
    )
end
