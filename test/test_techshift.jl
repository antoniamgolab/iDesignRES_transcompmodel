function generate_data_case_tech_shift()
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
        "initialfuelinginfr_list" => [],
        "initialmodeinfr_list" => [],
        "vehicle_subsidy_list" => [],
        "geographic_element_list" => [],
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

@testset "Tech shift test" begin
    case_name = "test_tech_shift"
    data_structures = generate_data_case_tech_shift()
    model, data_structures = create_model(data_structures, case_name, HiGHS.Optimizer)
    constraint_demand_coverage(model, data_structures)
    constraint_vehicle_sizing(model, data_structures)
    constraint_vehicle_aging(model, data_structures)
    constraint_vehicle_stock_shift(model, data_structures)
    constraint_mode_shift(model, data_structures)
    objective(model, data_structures)
    optimize!(model)
    solution_summary(model)

    p_r_k_pairs = create_p_r_k_set(data_structures["odpair_list"])
    m_tv_pairs =
        create_m_tv_pairs(data_structures["techvehicle_list"], data_structures["mode_list"])
    g_init = data_structures["g_init"]
    Y_end = data_structures["Y_end"]
    y_init = data_structures["y_init"]
    odpair_list = data_structures["odpair_list"]
    techvehicle_list = data_structures["techvehicle_list"]

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
    budget_penalty_minus_dict =
        save_results(model, case_name, data_structures, false, results_file_path)

    # checking objective value 
    # @test round(objective_value(model); digits = 2) == 160628.8

    # checking demand coverage 
    @test (
        sum(
            f_dict[(Y_end, (prk), mv, g)] for prk ∈ p_r_k_pairs for mv ∈ m_tv_pairs for
            g ∈ g_init:Y_end
        ) == 100.0
    )

    # checking vehicle sizing
    @test (
        sum(
            h_dict[(Y_end, r.id, tv.id, g)] for r ∈ odpair_list for tv ∈ techvehicle_list
            for g ∈ g_init:Y_end
        ) == 0.08
    )

    # initial and final tech mix 
    @test (
        round(
            sum(
                h_dict[(y_init, r.id, tv.id, g)] for r ∈ odpair_list for
                tv ∈ techvehicle_list for g ∈ g_init:y_init if tv.technology.id == 1
            );
            digits = 2,
        ) == 0.01
    )
    @test (
        round(
            sum(
                h_dict[(y_init, r.id, tv.id, g)] for r ∈ odpair_list for
                tv ∈ techvehicle_list for g ∈ g_init:y_init if tv.technology.id == 2
            );
            digits = 2,
        ) == 0.07
    )

    @test (
        round(
            sum(
                h_dict[(Y_end, r.id, tv.id, g)] for r ∈ odpair_list for
                tv ∈ techvehicle_list for g ∈ g_init:Y_end if tv.technology.id == 1
            );
            digits = 2,
        ) == 0.0
    )
    @test (
        round(
            sum(
                h_dict[(Y_end, r.id, tv.id, g)] for r ∈ odpair_list for
                tv ∈ techvehicle_list for g ∈ g_init:Y_end if tv.technology.id == 2
            );
            digits = 2,
        ) == 0.08
    )
end
