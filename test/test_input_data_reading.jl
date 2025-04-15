Y = 20
y_init = 2020
pre_y = 5

geographic_element_list = [Dict("id" => 1, "type" => "node", "name" => "Main area", "carbon_price" => fill(60.0, Y + 1), "from" => 1, "to" => 1, "length" => 4.0)]
println(length(geographic_element_list[1]["carbon_price"]), " ", Y + 1)
financial_status_list = [Dict("id" => 1, "name" => "Middle class", "VoT" => 15, "monetary_budget_purchase" => 12000, "monetary_budget_purchase_lb" => 10000, "monetary_budget_purchase_ub" => 13000, "monetary_budget_purchase_time_horizon" => 6)]

mode_list = [
Dict("id" => 1, "name" => "Road", "quantify_by_vehs" => true, "costs_per_ukm" => fill(0.12, Y + 1), "emission_factor" => fill(263, Y + 1), "infrastructure_expansion_costs" => fill(0.1, Y + 1), "infrastructure_om_costs" => fill(0.2, Y + 1), "waiting_time" => fill(5, Y + 1)),
Dict("id" => 2, "name" => "Rail", "quantify_by_vehs" => false, "costs_per_ukm" => fill(0.1, Y + 1), "emission_factor" => fill(0, Y + 1), "infrastructure_expansion_costs" => fill(0.1, Y + 1), "infrastructure_om_costs" => fill(0.2, Y + 1), "waiting_time" => fill(5, Y + 1)),
]
product_list = [Dict("id" => 1, "name" => "passenger")]
path_list = [Dict("id" => 1, "name" => "1", "length" => 8, "sequence" => [geographic_element_list[1]["id"]])]

fuel_list = [
Dict("id" => 1, "name" => "petrol", "emission_factor" => fill(5, Y + 1), "cost_per_kWh" => fill(10, Y + 1), "cost_per_kW" => fill(0, Y + 1), "fueling_infrastructure_om_costs" => fill(0.1, Y + 1)),
Dict("id" => 2, "name" => "electricity", "emission_factor" => fill(4, Y + 1), "cost_per_kWh" => fill(350, Y + 1), "cost_per_kW" => fill(0, Y + 1), "fueling_infrastructure_om_costs" => fill(0.1, Y + 1)),
]


technology_list = [
Dict("id" => 1, "name" => "ICEV", "fuel" => fuel_list[1]["name"]),
Dict("id" => 2, "name" => "BEV", "fuel" => fuel_list[2]["name"]),
]


vehicle_type_list = [
Dict("id" => 1, "name" => "Car", "mode" => mode_list[1]["id"], "product" => product_list[1]["name"]),
Dict("id" => 2, "name" => "Rail", "mode" => mode_list[2]["id"], "product" => product_list[1]["name"]),
]

regiontype_list =  [Dict("id" => 1, "name" => "Rural", "costs_fix" => fill(0, Y), "costs_var" => fill(0, Y))]

techvehicle_list = [
Dict("id" => 1, "name" => "ICEV passenger car", "vehicle_type" => vehicle_type_list[1]["name"], "technology" => technology_list[1]["id"], "capital_cost" => fill(80000, Y + pre_y + 1), "maintenance_cost_annual" => fill(fill(10, Y + 1), Y + 1 + pre_y), "maintenance_cost_distance" => fill(fill(10, Y + 1), Y + 1 + pre_y), "W" => fill(1, Y + 1 + pre_y), "spec_cons" => fill(5, Y + 1 + pre_y), "Lifetime" => fill(2, Y + 1 + pre_y), "AnnualRange" => fill(10000, Y + pre_y + 1), "products" => [product_list[1]["name"]], "tank_capacity" => fill(100, Y + 1 + pre_y), "peak_fueling" => fill(30, Y + 1 + pre_y), "fueling_time" => fill(5 / 60, Y + 1 + pre_y)),
Dict("id" => 2, "name" => "BEV passenger car", "vehicle_type" => vehicle_type_list[1]["name"], "technology" => technology_list[2]["id"], "capital_cost" => fill(60000, Y + pre_y + 1), "maintenance_cost_annual" => fill(fill(10, Y + 1), Y + 1 + pre_y), "maintenance_cost_distance" => fill(fill(10, Y + 1), Y + 1 + pre_y), "W" => fill(1, Y + 1 + pre_y), "spec_cons" => fill(5, Y + 1 + pre_y), "Lifetime" => fill(2, Y + 1 + pre_y), "AnnualRange" => fill(10000, Y + pre_y + 1), "products" => [product_list[1]["name"]], "tank_capacity" => fill(100, Y + 1 + pre_y), "peak_fueling" => fill(30, Y + 1 + pre_y), "fueling_time" => fill(5 / 60, Y + 1 + pre_y)),
]
total_vehs = 0.08

initvehiclestock_list = [
    Dict("id" => 1, "techvehicle" => techvehicle_list[1]["id"], "year_of_purchase" => 2015, "stock" => total_vehs / pre_y),
    Dict("id" => 2, "techvehicle" => techvehicle_list[1]["id"], "year_of_purchase" => 2016, "stock" => total_vehs / pre_y),
    Dict("id" => 3, "techvehicle" => techvehicle_list[1]["id"], "year_of_purchase" => 2017, "stock" => total_vehs / pre_y),
    Dict("id" => 4, "techvehicle" => techvehicle_list[1]["id"], "year_of_purchase" => 2018, "stock" => total_vehs / pre_y),
    Dict("id" => 5, "techvehicle" => techvehicle_list[1]["id"], "year_of_purchase" => 2019, "stock" => total_vehs / pre_y),
    Dict("id" => 6, "techvehicle" => techvehicle_list[2]["id"], "year_of_purchase" => 2015, "stock" => 0),
    Dict("id" => 7, "techvehicle" => techvehicle_list[2]["id"], "year_of_purchase" => 2016, "stock" => 0),
    Dict("id" => 8, "techvehicle" => techvehicle_list[2]["id"], "year_of_purchase" => 2017, "stock" => 0),
    Dict("id" => 9, "techvehicle" => techvehicle_list[2]["id"], "year_of_purchase" => 2018, "stock" => 0),
    Dict("id" => 10, "techvehicle" => techvehicle_list[2]["id"], "year_of_purchase" => 2019, "stock" => 0),
]

initialmodeinfr_list = [
Dict("id" => 1, "mode" => mode_list[1]["id"], "allocation" => geographic_element_list[1]["id"], "installed_ukm" => 0),
Dict("id" => 2, "mode" => mode_list[2]["id"], "allocation" => geographic_element_list[1]["id"], "installed_ukm" => 0),
]

initialfuelinginfr_list = [
Dict("id" => 1, "fuel" => fuel_list[1]["name"], "allocation" => geographic_element_list[1]["id"], "installed_kW" => 0),
Dict("id" => 2, "fuel" => fuel_list[2]["name"], "allocation" => geographic_element_list[1]["id"], "installed_kW" => 0),
]


odpair_list = [
    Dict(
        "id" => 1,
        "from" => geographic_element_list[1]["id"],
        "to" => geographic_element_list[1]["id"],
        "path_id" => path_list[1]["id"],
        "F" => fill(100, Y + 1),
        "product" => product_list[1]["name"],
        "vehicle_stock_init" => [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "financial_status" => financial_status_list[1]["name"],
        "region_type" => regiontype_list[1]["name"],
        "travel_time_budget" => 120,
    )
]

speed_list = [
    Dict("id" => 1, "region_type" => regiontype_list[1]["name"], "vehicle_type" => vehicle_type_list[1]["name"], "travel_speed" => 60),
]


input_data_dic = Dict(
    "Model" => Dict("Y" => Y, "y_init" => y_init, "pre_y" => pre_y, "gamma" => 0.0001, "budget_penalty_plus" => 100, "budget_penalty_minus" => 100, "discount_rate" => 0.05),   
    "GeographicElement" => geographic_element_list,
    "FinancialStatus" => financial_status_list,
    "Mode" => mode_list,
    "Product" => product_list,
    "Path" => path_list,
    "Fuel" => fuel_list,
    "Technology" => technology_list,
    "Vehicletype" => vehicle_type_list,
    "TechVehicle" => techvehicle_list,
    "InitialVehicleStock" => initvehiclestock_list,
    "InitialFuelingInfr" => initialfuelinginfr_list,
    "InitialModeInfr" => initialmodeinfr_list,
    "Regiontype" => regiontype_list,
    "Odpair" => odpair_list,
    "Speed" => speed_list,
)

yaml_str = YAML.write(input_data_dic)
open("test/data/test_input_data_reading.yaml", "w") do file
    write(file, yaml_str)
end

file = "test/data/test_input_data_reading.yaml"
data_dict = get_input_data(file)
data_structures = parse_data(data_dict)

keys_list = [
    "Y",
    "y_init",
    "pre_y",
    "gamma",
    "discount_rate",
    "budget_penalty_plus",
    "budget_penalty_minus",
    "financial_status_list",
    "mode_list",
    "product_list",
    "path_list",
    "fuel_list",
    "technology_list",
    "vehicletype_list",
    "regiontype_list",
    "techvehicle_list",
    "initvehiclestock_list",
    "odpair_list",
    "speed_list",
    "market_share_list",
    "emission_constraints_by_mode_list",
    "mode_shares_list",
    "max_mode_shares_list",
    "min_mode_shares_list",
    "initialfuelinginfr_list",
    "initialmodeinfr_list",
    "initialsupplyinfr_list",
    "vehicle_subsidy_list",
    "geographic_element_list",
    "init_detour_times_list",
    "detour_time_reduction_list",
    "supplytype_list",
]

@testset "Input data reading" begin
    # testing if the data_structures dictionary is properly established
    @test all(key -> haskey(data_structures, key), keys_list)

    # testing if values are different, if error is thrown 


    # @test_throws KeyError begin
        # Modify the input data to introduce an error
    odpair_list_wrong = [
        Dict(
            "id" => 1,
            "from" => geographic_element_list[1]["id"],
            "to" => geographic_element_list[1]["id"],
            "path_id" => path_list[1]["id"],
            "travel_demand" => fill(100, Y + 1),  # Incorrect key
            "product" => product_list[1]["name"],
            "vehicle_stock_init" => [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "financial_status" => financial_status_list[1]["name"],
            "region_type" => regiontype_list[1]["name"],
            "travel_time_budget" => 120,
        )
    ]

    input_data_dic_2 = Dict(
        "Model" => Dict("Y" => Y, "y_init" => y_init, "pre_y" => pre_y, "gamma" => 0.0001, "budget_penalty_plus" => 100, "budget_penalty_minus" => 100, "discount_rate" => 0.05),
        "GeographicElement" => geographic_element_list,
        "FinancialStatus" => financial_status_list,
        "Mode" => mode_list,
        "Product" => product_list,
        "Path" => path_list,
        "Fuel" => fuel_list,
        "Technology" => technology_list,
        "Vehicletype" => vehicle_type_list,
        "TechVehicle" => techvehicle_list,
        "InitialVehicleStock" => initvehiclestock_list,
        "InitialFuelingInfr" => initialfuelinginfr_list,
        "InitialModeInfr" => initialmodeinfr_list,
        "Regiontype" => regiontype_list,
        "Odpair" => odpair_list_wrong,
        "Speed" => speed_list,
    )

    yaml_str = YAML.write(input_data_dic_2)
    open("test/data/test_input_data_reading.yaml", "w") do file
        write(file, yaml_str)
    end

    file = "test/data/test_input_data_reading.yaml"
    # data_dict = get_input_data(file)  # This should throw an error
    # end
    @test_throws AssertionError get_input_data(file)

    # testing what if the dimensions are wrong 

    # @test_throws DimensionMismatch begin
    # Modify the input data to introduce an error
    techvehicle_list_wrong = [
        Dict("id" => 1, "name" => "ICEV passenger car", "vehicle_type" => vehicle_type_list[1]["name"], "technology" => technology_list[1]["id"], "capital_cost" => fill(80000, Y + pre_y + 1), "maintenance_cost_annual" => fill(fill(10, Y + 1), Y + 1), "maintenance_cost_distance" => fill(fill(10, Y + 1), Y + 1 + pre_y), "W" => fill(1, Y + 1 + pre_y), "spec_cons" => fill(5, Y + 1 + pre_y), "Lifetime" => fill(2, Y + 1 + pre_y), "AnnualRange" => fill(10000, Y + pre_y + 1), "products" => [product_list[1]["name"]], "tank_capacity" => fill(100, Y + 1 + pre_y), "peak_fueling" => fill(30, Y + 1 + pre_y), "fueling_time" => fill(5 / 60, Y + 1 + pre_y)),
        Dict("id" => 2, "name" => "BEV passenger car", "vehicle_type" => vehicle_type_list[1]["name"], "technology" => technology_list[2]["id"], "capital_cost" => fill(60000, Y + pre_y + 1), "maintenance_cost_annual" => fill(fill(10, Y + 1), Y + 1), "maintenance_cost_distance" => fill(fill(10, Y + 1), Y + 1 + pre_y), "W" => fill(1, Y + 1 + pre_y), "spec_cons" => fill(5, Y + 1 + pre_y), "Lifetime" => fill(2, Y + 1 + pre_y), "AnnualRange" => fill(10000, Y + pre_y + 1), "products" => [product_list[1]["name"]], "tank_capacity" => fill(100, Y + 1 + pre_y), "peak_fueling" => fill(30, Y + 1 + pre_y), "fueling_time" => fill(5 / 60, Y + 1 + pre_y)),
    ]

    input_data_dic_3 = Dict(
        "Model" => Dict("Y" => Y, "y_init" => y_init, "pre_y" => pre_y, "gamma" => 0.0001, "budget_penalty_plus" => 100, "budget_penalty_minus" => 100, "discount_rate" => 0.05),
        "GeographicElement" => geographic_element_list,
        "FinancialStatus" => financial_status_list,
        "Mode" => mode_list,
        "Product" => product_list,
        "Path" => path_list,
        "Fuel" => fuel_list,
        "Technology" => technology_list,
        "Vehicletype" => vehicle_type_list,
        "TechVehicle" => techvehicle_list_wrong,
        "InitialVehicleStock" => initvehiclestock_list,
        "InitialFuelingInfr" => initialfuelinginfr_list,
        "InitialModeInfr" => initialmodeinfr_list,
        "Regiontype" => regiontype_list,
        "Odpair" => odpair_list,
        "Speed" => speed_list,
    )
    yaml_str = YAML.write(input_data_dic_2)
    open("test/data/test_input_data_reading.yaml", "w") do file
        write(file, yaml_str)
    end

    file = "test/data/test_input_data_reading.yaml"
    @test_throws AssertionError get_input_data(file)  # This should throw an error


end
