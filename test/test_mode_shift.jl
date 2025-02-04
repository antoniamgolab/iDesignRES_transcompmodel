
function generate_data_case_mode_shift()
    Y = 5
    y_init = 2020
    pre_y = 0
    g_init = y_init - pre_y
    Y_end = Y + y_init - 1

    geographic_element_list =
        [GeographicElement(1, "node", "Main area", fill(60.0, Y + 1), 1, 1, 4.0)]

    financial_status_list = [FinancialStatus(1, "Middle class", 15, 12000, 10000, 13000, 6)]

    mode_list = [
        Mode(
            1,
            "Road",
            false,
            fill(0.12, Y + 1),
            fill(263, Y + 1),
            fill(0.1, Y + 1),
            fill(0.2, Y + 1),
            fill(0, Y + 1),
        ),
        Mode(
            2,
            "Rail",
            false,
            fill(0.12, Y + 1),
            fill(0, Y + 1),
            fill(0.3, Y + 1),
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

    technology_list = [
        Technology(1, "ICEV", fuel_list[1]),
        Technology(2, "Electrified rail", fuel_list[1]),
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
        ),
        TechVehicle(
            2,
            "Electrified rail",
            vehicle_type_list[2],
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
        ),
    ]

    initvehiclestock_list = []
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
        ),
    ]
    speed_list = [
        Speed(1, regiontype_list[1], vehicle_type_list[1], 60),
        Speed(2, regiontype_list[1], vehicle_type_list[2], 80),
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
    )
end

@testset "Tech shift test" begin
    case_name = "test_modeshift"
    data_structures = generate_data_case_mode_shift()
    model, data_structures = create_model(data_structures, case_name)
    constraint_demand_coverage(model, data_structures)

    objective(model, data_structures)

    # -------- model solution and saving of results --------
    # set_optimizer_attribute(model, "ScaleFlag", 2)
    # set_optimizer_attribute(model, "Presolve", 0)
    set_optimizer_attribute(model, "MIPFocus", 2)
    set_optimizer_attribute(model, "MIPGap", 10^(-9))
    set_optimizer_attribute(model, "Crossover", 0)

    println("Solution .... ")
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
    budget_penalty_minus_dict =
        save_results(model, case_name, data_structures, true, results_file_path)

    p_r_k_pairs = create_p_r_k_set(data_structures["odpair_list"])
    m_tv_pairs =
        create_m_tv_pairs(data_structures["techvehicle_list"], data_structures["mode_list"])
    techvehicle_list = data_structures["techvehicle_list"]
    g_init = data_structures["g_init"]
    Y_end = data_structures["Y_end"]

    # @test (round(objective_value(model); digits = 2) == 66600)
    @test (
        sum(
            f_dict[(Y_end, (prk), mv, g)] for prk ∈ p_r_k_pairs for mv ∈ m_tv_pairs for
            g ∈ g_init:Y_end
        ) == 100.0
    )

    # checking mode share 
    @test (
        sum(
            f_dict[(Y_end, (prk), mv, g)] for prk ∈ p_r_k_pairs for mv ∈ m_tv_pairs for
            g ∈ g_init:Y_end if mv[1] == 1
        ) == 100.0
    )
    @test (
        sum(
            f_dict[(Y_end, (prk), mv, g)] for prk ∈ p_r_k_pairs for mv ∈ m_tv_pairs for
            g ∈ g_init:Y_end if mv[1] == 2
        ) == 0
    )
end
