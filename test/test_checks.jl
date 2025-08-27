using Test
using ..TransComp

@testset "check_input_file" begin
    @test_throws ErrorException check_input_file("nonexistent.yaml")
    @test_throws ErrorException check_input_file("file.txt")
end

@testset "check_required_keys" begin
    d = Dict("a" => 1)
    
    # This must match the exception type thrown in your function
    @test_throws ErrorException check_required_keys(d, ["a", "b"])
end

using Test

@testset "check_required_sub_keys" begin
    # Case 1: valid input, should not throw
    data_valid = Dict(
        "Layers" => [
            Dict("id" => 1, "type" => "conv"),
            Dict("id" => 2, "type" => "dense")
        ]
    )
    required_keys = ["id", "type"]

    @test check_required_sub_keys(data_valid, required_keys, "Layers") === nothing

    # Case 2: missing a key in one dict, should throw AssertionError
    data_invalid = Dict(
        "Layers" => [
            Dict("id" => 1),              # missing "type"
            Dict("id" => 2, "type" => "dense")
        ]
    )

    @test_throws AssertionError check_required_sub_keys(data_invalid, required_keys, "Layers")
end


@testset "check_folder_writable" begin
    @test_throws ErrorException check_folder_writable("nonexistent_folder")
end

@testset "check_validity_of_model_parametrization" begin
    d = Dict("Model" => Dict("y_init" => "notint", "Y" => 1, "pre_y" => 1, "discount_rate" => 0.05))
    @test_throws AssertionError check_validity_of_model_parametrization(d)
end


@testset "check_model_parametrization" begin
    d = Dict("Model" => Dict())
    @test_throws ErrorException check_model_parametrization(d, ["missing_key"])
end

@testset "check_dimensions_of_input_parameters" begin
    @test check_dimensions_of_input_parameters(Dict())
end

@testset "check_uniquness_of_ids" begin
    d = Dict("A" => [Dict("id" => 1), Dict("id" => 1)])
    @test_throws ErrorException check_uniquness_of_ids(d, ["A"])
end

using Test

@testset "Format checks" begin
    years = 3
    generations = 2

    # -------------------------------
    # GeographicElement
    # -------------------------------
    data_valid = Dict(
        "GeographicElement" => [
            Dict(
                "id" => 1,
                "type" => "region",
                "name" => "North",
                "carbon_price" => [10.0, 20.0, 30.0],
                "length" => 100.0
            )
        ]
    )
    @test check_correct_formats_GeographicElement(data_valid, years) === nothing

    data_invalid = Dict(
        "GeographicElement" => [
            Dict(  # missing id
                "type" => "region",
                "name" => "North",
                "carbon_price" => [10.0, 20.0, 30.0],
                "length" => 100.0
            )
        ]
    )
    @test_throws ErrorException check_correct_formats_GeographicElement(data_invalid, years)

    # -------------------------------
    # FinancialStatus
    # -------------------------------
    data_valid = Dict(
        "FinancialStatus" => [
            Dict(
                "id" => 1,
                "name" => "Household",
                "VoT" => 5.0,
                "monetary_budget_purchase" => 100.0,
                "monetary_budget_purchase_lb" => 50.0,
                "monetary_budget_purchase_ub" => 150.0
            )
        ]
    )
    @test check_correct_formats_FinancialStatus(data_valid) === nothing

    data_invalid = Dict(
        "FinancialStatus" => [
            Dict(  # wrong type for VoT
                "id" => 1,
                "name" => "Household",
                "VoT" => "five",
                "monetary_budget_purchase" => 100.0,
                "monetary_budget_purchase_lb" => 50.0,
                "monetary_budget_purchase_ub" => 150.0
            )
        ]
    )
    @test_throws AssertionError check_correct_formats_FinancialStatus(data_invalid)

    # -------------------------------
    # Mode
    # -------------------------------
    data_valid = Dict(
        "Mode" => [
            Dict(
                "id" => 1,
                "name" => "Car",
                "quantify_by_vehs" => true,
                "costs_per_ukm" => [1.0, 2.0, 3.0],
                "emission_factor" => [0.1, 0.2, 0.3],
                "infrastructure_expansion_costs" => [100, 200, 300],
                "infrastructure_om_costs" => [5, 5, 5],
                "waiting_time" => [1, 1, 1]
            )
        ]
    )
    @test check_correct_format_Mode(data_valid, years) === nothing

    data_invalid = Dict(
        "Mode" => [
            Dict(
                "id" => 1,
                "name" => "Car",
                "quantify_by_vehs" => true,
                "costs_per_ukm" => [1.0], # too short
                "emission_factor" => [0.1, 0.2, 0.3],
                "infrastructure_expansion_costs" => [100, 200, 300],
                "infrastructure_om_costs" => [5, 5, 5],
                "waiting_time" => [1, 1, 1]
            )
        ]
    )
    @test_throws AssertionError check_correct_format_Mode(data_invalid, years)

    # -------------------------------
    # Product
    # -------------------------------
    data_valid = Dict(
        "Product" => [
            Dict(
                "id" => 1,
                "name" => "Food",
                "type" => "consumable",
                "base_year_demand" => 100.0
            )
        ]
    )
    @test check_correct_format_Product(data_valid) === nothing

    data_invalid = Dict(
        "Product" => [
            Dict( # wrong type for demand
                "id" => 1,
                "name" => "Food",
                "type" => "consumable",
                "base_year_demand" => "a lot"
            )
        ]
    )
    @test_throws AssertionError check_correct_format_Product(data_invalid)

    # -------------------------------
    # Path
    # -------------------------------
    data_valid = Dict(
        "Path" => [
            Dict(
                "id" => 1,
                "name" => "Route A",
                "od_pair_id" => 1,
                "layer_id_sequence" => [1, 2, 3],
                "time_sequence" => [1.0, 2.0, 3.0],
                "length_sequence" => [10.0, 20.0, 30.0]
            )
        ]
    )
    @test check_correct_format_Path(data_valid) === nothing

    data_invalid = Dict(
        "Path" => [
            Dict( # time_sequence wrong type
                "id" => 1,
                "name" => "Route A",
                "od_pair_id" => 1,
                "layer_id_sequence" => [1, 2, 3],
                "time_sequence" => ["fast", "slow"],
                "length_sequence" => [10.0, 20.0, 30.0]
            )
        ]
    )
    @test_throws AssertionError check_correct_format_Path(data_invalid)

    # -------------------------------
    # Fuel
    # -------------------------------
    data_valid = Dict(
        "Fuel" => [
            Dict(
                "id" => 1,
                "name" => "Gasoline",
                "production_cost" => [1.0, 2.0, 3.0],
                "co2_content" => [0.1, 0.2, 0.3]
            )
        ]
    )
    @test check_correct_format_Fuel(data_valid, years) === nothing

    data_invalid = Dict(
        "Fuel" => [
            Dict( # co2_content too short
                "id" => 1,
                "name" => "Gasoline",
                "production_cost" => [1.0, 2.0, 3.0],
                "co2_content" => [0.1]
            )
        ]
    )
    @test_throws AssertionError check_correct_format_Fuel(data_invalid, years)

    # -------------------------------
    # Technology
    # -------------------------------
    data_valid = Dict(
        "Technology" => [
            Dict(
                "id" => 1,
                "name" => "Battery",
                "fuel_id" => 1,
                "purchase_cost" => [100, 200, 300],
                "om_cost" => [5, 5, 5],
                "max_capacity_addition" => [1, 2, 3],
                "efficiency" => [0.9, 0.95, 0.98]
            )
        ]
    )
    @test check_correct_format_Technology(data_valid, years) === nothing

    data_invalid = Dict(
        "Technology" => [
            Dict( # wrong type for efficiency
                "id" => 1,
                "name" => "Battery",
                "fuel_id" => 1,
                "purchase_cost" => [100, 200, 300],
                "om_cost" => [5, 5, 5],
                "max_capacity_addition" => [1, 2, 3],
                "efficiency" => ["high", "medium", "low"]
            )
        ]
    )
    @test_throws AssertionError check_correct_format_Technology(data_invalid, years)

    # -------------------------------
    # Vehicletype
    # -------------------------------
    data_valid = Dict(
        "Vehicletype" => [
            Dict(
                "id" => 1,
                "name" => "Sedan",
                "mode_id" => 1,
                "capacity" => 4,
                "investment_cost" => [20000, 21000, 22000],
                "om_cost" => [500, 550, 600]
            )
        ]
    )
    @test check_correct_format_Vehicletype(data_valid, years) === nothing

    data_invalid = Dict(
        "Vehicletype" => [
            Dict( # om_cost wrong length
                "id" => 1,
                "name" => "Sedan",
                "mode_id" => 1,
                "capacity" => 4,
                "investment_cost" => [20000, 21000, 22000],
                "om_cost" => [500]
            )
        ]
    )
    @test_throws AssertionError check_correct_format_Vehicletype(data_invalid, years)

    # -------------------------------
    # Regiontype
    # -------------------------------
    data_valid = Dict(
        "Regiontype" => [
            Dict(
                "id" => 1,
                "name" => "Urban",
                "share" => 0.7
            )
        ]
    )
    @test check_correct_format_Regiontype(data_valid) === nothing

    data_invalid = Dict(
        "Regiontype" => [
            Dict( # share wrong type
                "id" => 1,
                "name" => "Urban",
                "share" => "seventy percent"
            )
        ]
    )
    @test_throws AssertionError check_correct_format_Regiontype(data_invalid)

    # -------------------------------
    # TechVehicle
    # -------------------------------
    data_valid = Dict(
        "TechVehicle" => [
            Dict(
                "id" => 1,
                "vehicle_id" => 1,
                "technology_id" => 1,
                "generation" => 1,
                "efficiency" => [0.8, 0.85, 0.9],
                "costs" => [10000, 9500, 9000]
            )
        ]
    )
    @test check_correct_format_TechVehicle(data_valid, years, generations) === nothing

    data_invalid = Dict(
        "TechVehicle" => [
            Dict( # efficiency too short
                "id" => 1,
                "vehicle_id" => 1,
                "technology_id" => 1,
                "generation" => 1,
                "efficiency" => [0.8],
                "costs" => [10000, 9500, 9000]
            )
        ]
    )
    @test_throws AssertionError check_correct_format_TechVehicle(data_invalid, years, generations)

    # -------------------------------
    # InitialVehicleStock
    # -------------------------------
    data_valid = Dict(
        "InitialVehicleStock" => [
            Dict(
                "techvehicle_id" => 1,
                "stock" => 100
            )
        ]
    )
    @test check_correct_format_InitialVehicleStock(data_valid) === nothing

    data_invalid = Dict(
        "InitialVehicleStock" => [
            Dict( # stock wrong type
                "techvehicle_id" => 1,
                "stock" => "many"
            )
        ]
    )
    @test_throws AssertionError check_correct_format_InitialVehicleStock(data_invalid)

    # -------------------------------
    # InitialFuelingInfr
    # -------------------------------
    data_valid = Dict(
        "InitialFuelingInfr" => [
            Dict(
                "fuel_id" => 1,
                "capacity" => 100.0
            )
        ]
    )
    @test check_correct_format_InitialFuelingInfr(data_valid) === nothing

    data_invalid = Dict(
        "InitialFuelingInfr" => [
            Dict( # capacity wrong type
                "fuel_id" => 1,
                "capacity" => "lots"
            )
        ]
    )
    @test_throws AssertionError check_correct_format_InitialFuelingInfr(data_invalid)

    # -------------------------------
    # InitialModeInfr
    # -------------------------------
    data_valid = Dict(
        "InitialModeInfr" => [
            Dict(
                "mode_id" => 1,
                "capacity" => 500.0
            )
        ]
    )
    @test check_correct_format_InitialModeInfr(data_valid) === nothing

    data_invalid = Dict(
        "InitialModeInfr" => [
            Dict( # missing capacity
                "mode_id" => 1
            )
        ]
    )
    @test_throws ErrorException check_correct_format_InitialModeInfr(data_invalid)

    # -------------------------------
    # Odpair
    # -------------------------------
    data_valid = Dict(
        "Odpair" => [
            Dict(
                "id" => 1,
                "origin_id" => 1,
                "destination_id" => 2,
                "product_id" => 1,
                "base_year_demand" => 50.0,
                "base_year_price" => 2.0,
                "price_elast" => -0.5
            )
        ]
    )
    @test check_correct_format_Odpair(data_valid) === nothing

    data_invalid = Dict(
        "Odpair" => [
            Dict( # base_year_demand wrong type
                "id" => 1,
                "origin_id" => 1,
                "destination_id" => 2,
                "product_id" => 1,
                "base_year_demand" => "lots",
                "base_year_price" => 2.0,
                "price_elast" => -0.5
            )
        ]
    )
    @test_throws AssertionError check_correct_format_Odpair(data_invalid)

    # -------------------------------
    # Speed
    # -------------------------------
    data_valid = Dict(
        "Speed" => [
            Dict(
                "layer_id" => 1,
                "mode_id" => 1,
                "speed" => [10.0, 20.0, 30.0]
            )
        ]
    )
    @test check_correct_format_Speed(data_valid, years) === nothing

    data_invalid = Dict(
        "Speed" => [
            Dict( # speed wrong length
                "layer_id" => 1,
                "mode_id" => 1,
                "speed" => [10.0]
            )
        ]
    )
    @test_throws AssertionError check_correct_format_Speed(data_invalid, years)
end
