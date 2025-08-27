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

@testset "check_correct_formats_GeographicElement" begin
    d = Dict("GeographicElement" => [Dict("id" => "notint", "type" => "t", "name" => "n", "carbon_price" => [1.0, 1.0], "length" => 1.0)])
    @test_throws ErrorException check_correct_formats_GeographicElement(d, 1)
end

@testset "check_correct_formats_FinancialStatus" begin
    d = Dict("FinancialStatus" => [Dict("id" => "notint", "name" => "n", "VoT" => 1.0, "monetary_budget_purchase" => 1.0, "monetary_budget_purchase_lb" => 2.0, "monetary_budget_purchase_ub" => 3.0)])
    @test_throws ErrorException check_correct_formats_FinancialStatus(d)
end

@testset "check_correct_format_Mode" begin
    d = Dict("Mode" => [Dict("id" => "notint", "name" => "n", "quantify_by_vehs" => true, "costs_per_ukm" => [1.0, 1.0], "emission_factor" => [1.0, 1.0], "infrastructure_expansion_costs" => [1.0, 1.0], "infrastructure_om_costs" => [1.0, 1.0], "waiting_time" => [1.0, 1.0])])
    @test_throws ErrorException check_correct_format_Mode(d, 1)
end

@testset "check_correct_format_Product" begin
    d = Dict("Product" => [Dict("id" => "notint", "name" => "n")])
    @test_throws ErrorException check_correct_format_Product(d)
end

@testset "check_correct_format_Path" begin
    d = Dict("Path" => [Dict("id" => "notint", "name" => "n", "length" => 1.0, "sequence" => [1])])
    @test_throws ErrorException check_correct_format_Path(d)
end

@testset "check_correct_format_Fuel" begin
    d = Dict("Fuel" => [Dict("id" => "notint", "name" => "n", "cost_per_kWh" => [1.0, 1.0], "cost_per_kW" => [1.0, 1.0], "emission_factor" => [1.0, 1.0], "fueling_infrastructure_om_costs" => [1.0, 1.0])])
    @test_throws ErrorException check_correct_format_Fuel(d, 1)
end

@testset "check_correct_format_Technology" begin
    d = Dict("Technology" => [Dict("id" => "notint", "name" => "n", "fuel" => "f")])
    @test_throws ErrorException check_correct_format_Technology(d)
end

@testset "check_correct_format_Vehicletype" begin
    d = Dict("Vehicletype" => [Dict("id" => "notint", "name" => "n", "mode" => 1, "product" => "p")])
    @test_throws ErrorException check_correct_format_Vehicletype(d)
end

@testset "check_correct_format_Regiontype" begin
    d = Dict("Regiontype" => [Dict("id" => "notint", "name" => "n", "costs_var" => [1.0, 1.0], "costs_fix" => [1.0, 1.0])])
    @test_throws ErrorException check_correct_format_Regiontype(d, 1)
end

@testset "check_correct_format_TechVehicle" begin
    d = Dict("TechVehicle" => [Dict("id" => "notint", "name" => "n", "vehicle_type" => "vt", "technology" => 1, "capital_cost" => [1.0], "maintenance_cost_annual" => [[1.0]], "maintenance_cost_distance" => [[1.0]], "W" => [1.0], "spec_cons" => [1.0], "Lifetime" => [1.0], "AnnualRange" => [1.0], "products" => ["p"], "tank_capacity" => [1.0], "peak_fueling" => [1.0])])
    @test_throws ErrorException check_correct_format_TechVehicle(d, 1, 1)
end

@testset "check_correct_format_InitialVehicleStock" begin
    d = Dict("InitialVehicleStock" => [Dict("id" => "notint", "techvehicle" => 1, "year_of_purchase" => 0, "stock" => 1.0)])
    @test_throws ErrorException check_correct_format_InitialVehicleStock(d, 1, 1)
end

@testset "check_correct_format_InitialFuelingInfr" begin
    d = Dict("InitialFuelingInfr" => [Dict("id" => "notint", "fuel" => "f", "allocation" => 1, "installed_kW" => 1.0)])
    @test_throws ErrorException check_correct_format_InitialFuelingInfr(d)
end

@testset "check_correct_format_InitialModeInfr" begin
    d = Dict("InitialModeInfr" => [Dict("id" => "notint", "mode" => 1, "allocation" => 1, "installed_ukm" => 1.0)])
    @test_throws ErrorException check_correct_format_InitialModeInfr(d)
end

@testset "check_correct_format_Odpair" begin
    d = Dict("Odpair" => [Dict("id" => "notint", "from" => 1, "to" => 1, "path_id" => 1, "F" => [1.0], "product" => "p", "vehicle_stock_init" => [1.0], "financial_status" => "fs", "region_type" => "rt")])
    @test_throws ErrorException check_correct_format_Odpair(d, 1)
end

@testset "check_correct_format_Speed" begin
    # Provide all required keys, but make 'id' the wrong type to trigger the assertion
    d = Dict("Speed" => [Dict("id" => "notint", "region_type" => "rt", "vehicle_type" => "vt", "travel_speed" => 1.0)])
    @test_throws ErrorException check_correct_format_Speed(d)
end
