function generate_data_supply_infr()
    Y = 5
    y_init = 2020
    pre_y = 6
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
            fill(0, Y + 1),
            fill(0, Y + 1),
            fill(0.1, Y + 1),
            fill(0.2, Y + 1),
            fill(20, Y + 1),
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
            fill(263, Y + 1),
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

    technology_list =
        [Technology(1, "ICEV", fuel_list[1]), Technology(2, "BEV", fuel_list[2])]

    vehicle_type_list = [Vehicletype(1, "Car", mode_list[1], [product_list[1]])]

    regiontype_list = [Regiontype(1, "Rural", fill(0, Y), fill(0, Y))]
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
            fill(1, Y + 1 + pre_y),
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
            fill(1, Y + 1 + pre_y),
            fill(5, Y + 1 + pre_y),
            fill(2, Y + 1 + pre_y),
            fill(10000, Y + pre_y + 1),
            [product_list[1]],
            fill(100, Y + 1 + pre_y),
            fill(30, Y + 1 + pre_y),
            fill(5 / 60, Y + 1 + pre_y),
        ),
    ]

    total_vehs = 0.08

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
    initialmodeinfr_list = [InitialModeInfr(1, mode_list[1], 1, 0)]

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
    speed_list = [Speed(1, regiontype_list[1], vehicle_type_list[1], 60)]

    # adding supply infrastructure 

    supplytype_list = [
        SupplyType(1, "Fueling station", fuel_list[1], fill(10, Y + 1), fill(10, Y + 1))
        SupplyType(2, "Charging station", fuel_list[2], fill(20, Y + 1), fill(20, Y + 1))
    ]

    initialsupplyinfr_list = [
        InitialSupplyInfr(1, "1", fuel_list[1], supplytype_list[1], geographic_element_list[1], 0),
        InitialSupplyInfr(2, "2", fuel_list[2], supplytype_list[2], geographic_element_list[1], 0),
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
        "alpha_f" => 0.2,
        "alpha_h" => 0.5,
        "beta_h" => 0.5,
        "beta_f" => 0.2,
        "discount_rate" => 0,
        "supplytype_list" => supplytype_list,
        "initialsupplyinfr_list" => initialsupplyinfr_list,
    )
end

@testset "Test supply infrastructure" begin


    case_name = "test_supply_infrastructure"
    data_structures = generate_data_supply_infr()
    model, data_structures = create_model(data_structures, case_name, HiGHS.Optimizer)
    constraint_demand_coverage(model, data_structures)
    constraint_fueling_demand(model, data_structures)
    constraint_vehicle_sizing(model, data_structures)
    constraint_vehicle_aging(model, data_structures)
    constraint_vehicle_stock_shift(model, data_structures)
    constraint_mode_shift(model, data_structures)
    constraint_supply_infrastructure(model, data_structures)
    objective(model, data_structures)
    optimize!(model)
    solution_summary(model)

    results_file_path = normpath(joinpath(@__DIR__, "results/"))
    f_dict,
    h_dict,
    h_exist_dict,
    h_plus_dict,
    h_minus_dict,
    s_dict,
    q_fuel_infr_plus_dict,
    q_mode_infr_plus_dict,
    budget_penalty_plus_dict,
    budget_penalty_minus_dict,
    q_supply_infr_plus_dict = 
        save_results(model, case_name, data_structures, false, results_file_path)


    p_r_k_pairs = create_p_r_k_set(data_structures["odpair_list"])
    m_tv_pairs =
        create_m_tv_pairs(data_structures["techvehicle_list"], data_structures["mode_list"])
    techvehicle_list = data_structures["techvehicle_list"]
    g_init = data_structures["g_init"]
    Y_end = data_structures["Y_end"]
    techvehicle_list = data_structures["techvehicle_list"]
    odpair_list = data_structures["odpair_list"]
    supplytype_list = data_structures["supplytype_list"]

    @test sum(q_supply_infr_plus_dict[y, st.id, geo.id] for st in supplytype_list for geo in data_structures["geographic_element_list"] for v in
    techvehicle_list for y in data_structures["y_init"]:Y_end if st.id == 2) == 0.8
    
    @test (round(sum(q_supply_infr_plus_dict[y, st.id, geo.id] for st in supplytype_list for geo in data_structures["geographic_element_list"] for v in
    techvehicle_list for y in data_structures["y_init"]:Y_end if st.id == 1), digits=2) == 0.09)


end