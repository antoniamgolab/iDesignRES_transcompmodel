function generate_data_case_tech_shift()
    Y = 20
    y_init = 2020
    pre_y = 5
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


@testset "Test minimum viable case" begin
    case_name = "minimum_viable_case_tech_shift"
    data_structures = generate_data_case_tech_shift()
    model, data_structures = create_model(data_structures, case_name, HiGHS.Optimizer)
    constraint_demand_coverage(model, data_structures)
    constraint_vehicle_sizing(model, data_structures)
    constraint_vehicle_aging(model, data_structures)
    constraint_vehicle_stock_shift(model, data_structures)
    constraint_mode_shift(model, data_structures)
    constraint_fueling_demand(model, data_structures)
    constraint_fueling_infrastructure(model, data_structures)
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
    fuel_list = data_structures["fuel_list"]
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
        save_results(model, case_name, data_structures, true, results_file_path)

    # check vehicle stock sizing
    println(
        sum(
            f_dict[(y_init, (prk), mv, g)] for prk ∈ p_r_k_pairs for mv ∈ m_tv_pairs for
            g ∈ g_init:y_init if mv[1] == 1
        ),
    )


    println(
        sum(
            h_dict[(y_init, r.id, tv.id, g)] for r ∈ odpair_list for tv ∈ techvehicle_list
            for g ∈ g_init:y_init if tv.technology.id == 1
        ),
    )
    println(
        sum(
            h_dict[((y_init + 1), r.id, tv.id, g)] for r ∈ odpair_list for
            tv ∈ techvehicle_list for g ∈ g_init:(y_init+1) if tv.technology.id == 1
        ),
    )
    @test (
        round(
            sum(
                h_minus_dict[(y_init, r.id, tv.id, g)] for r ∈ odpair_list for
                tv ∈ techvehicle_list for g ∈ g_init:y_init if tv.technology.id == 1
            ),
            digits = 2,
        ) == 0.02
    )

    @test (
        round(
            sum(
                h_minus_dict[(y_init, r.id, tv.id, g)] for r ∈ odpair_list for
                tv ∈ techvehicle_list for g ∈ g_init:y_init if tv.technology.id == 2
            ),
            digits = 2,
        ) == 0.0
    )

    # check modal shift
    @test (
        round(
            sum(
                f_dict[(y_init, (prk), mv, g)] for prk ∈ p_r_k_pairs for mv ∈ m_tv_pairs for
                g ∈ g_init:y_init if mv[1] == 1
            ),
            digits = 2,
        ) == 14.64
    )

    @test (
        round(
            sum(
                f_dict[(Y_end, (prk), mv, g)] for prk ∈ p_r_k_pairs for mv ∈ m_tv_pairs for
                g ∈ g_init:Y_end if mv[1] == 2
            ),
            digits = 2,
        ) == 100.0
    )

    # check tech shift 
    @test (
        sum(
            h_dict[(y_init, r.id, tv.id, g)] for r ∈ odpair_list for tv ∈ techvehicle_list
            for g ∈ g_init:y_init if tv.technology.id == 1
        ) - sum(
            h_exist_dict[(y_init, r.id, tv.id, g)] for r ∈ odpair_list for
            tv ∈ techvehicle_list for g ∈ g_init:y_init if tv.technology.id == 1
        ) <=
        data_structures["alpha_h"] * sum(
            h_dict[(y_init, r.id, tv.id, g)] for r ∈ odpair_list for tv ∈ techvehicle_list
            for g ∈ g_init:y_init
        ) +
        data_structures["beta_h"] * sum(
            h_exist_dict[(y_init, r.id, tv.id, g)] for r ∈ odpair_list for
            tv ∈ techvehicle_list for g ∈ g_init:y_init if tv.technology.id == 1
        )
    )
    @test(
        -(
            sum(
                h_dict[(y_init, r.id, tv.id, g)] for r ∈ odpair_list for
                tv ∈ techvehicle_list for g ∈ g_init:y_init if tv.technology.id == 1
            ) - sum(
                h_exist_dict[(y_init, r.id, tv.id, g)] for r ∈ odpair_list for
                tv ∈ techvehicle_list for g ∈ g_init:y_init if tv.technology.id == 1
            )
        ) <=
        data_structures["alpha_h"] * sum(
            h_dict[(y_init, r.id, tv.id, g)] for r ∈ odpair_list for tv ∈ techvehicle_list
            for g ∈ g_init:y_init
        ) +
        data_structures["beta_h"] * sum(
            h_exist_dict[(y_init, r.id, tv.id, g)] for r ∈ odpair_list for
            tv ∈ techvehicle_list for g ∈ g_init:y_init if tv.technology.id == 1
        )
    )


    # check vehicle aging - testing that the lifetime cannot be exceeded 
    y = 2020
    @test (
        sum(
            h_dict[(y, r.id, tv.id, g)] for r ∈ odpair_list for tv ∈ techvehicle_list for
            g ∈ g_init:(y-2)
        ) == 0
    )

    y = 2025
    @test (
        round(
            sum(
                h_dict[(y, r.id, tv.id, g)] for r ∈ odpair_list for tv ∈ techvehicle_list
                for g ∈ g_init:(y-2)
            ),
            digits = 2,
        ) == 0
    )
    y = 2030
    @test (
        round(
            sum(
                h_dict[(y, r.id, tv.id, g)] for r ∈ odpair_list for tv ∈ techvehicle_list
                for g ∈ g_init:(y-2)
            ),
            digits = 2,
        ) == 0
    )
    y = 2035
    @test (
        round(
            sum(
                h_dict[(y, r.id, tv.id, g)] for r ∈ odpair_list for tv ∈ techvehicle_list
                for g ∈ g_init:(y-2)
            ),
            digits = 2,
        ) == 0
    )
    y = Y_end
    @test (
        round(
            sum(
                h_dict[(y, r.id, tv.id, g)] for r ∈ odpair_list for tv ∈ techvehicle_list
                for g ∈ g_init:(y-2)
            ),
            digits = 2,
        ) == 0
    )

    # check fueling infrastructure sizing 
    print(
        sum(
            q_fuel_infr_plus_dict[(y, 1, 1)] for f ∈ fuel_list for y ∈ y_init:Y_end
        )
    )
    @test (
        round(
            sum(q_fuel_infr_plus_dict[(y, 1, 1)] for f ∈ fuel_list for y ∈ y_init:Y_end),
            digits = 2,
        ) == 0.12
    )
end
