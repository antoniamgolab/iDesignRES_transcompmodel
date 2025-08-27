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


@testset "Checks functions" begin
    years = 3
    generations = 2

    # -------------------------
    # check_required_keys
    # -------------------------
    @testset "check_required_keys" begin
        d = Dict("a" => 1)
        @test check_required_keys(d, ["a"]) === nothing
        @test_throws ErrorException check_required_keys(d, ["a", "b"])
    end

    # -------------------------
    # check_required_sub_keys
    # -------------------------
    @testset "check_required_sub_keys" begin
        d_valid = Dict("Layers" => [Dict("id" => 1, "type" => "x")])
        @test check_required_sub_keys(d_valid, ["id","type"], "Layers") === nothing

        d_invalid = Dict("Layers" => [Dict("id" => 1)]) # missing "type"
        @test_throws AssertionError check_required_sub_keys(d_invalid, ["id","type"], "Layers")
    end

    # -------------------------
    # check_uniquness_of_ids
    # -------------------------
    @testset "check_uniquness_of_ids" begin
        good = Dict("Vehicle" => [Dict("id"=>1), Dict("id"=>2)])
        @test check_uniquness_of_ids(good, "Vehicle") === nothing

        bad = Dict("Vehicle" => [Dict("id"=>1), Dict("id"=>1)]) # duplicate id
        @test_throws AssertionError check_uniquness_of_ids(bad, "Vehicle")
    end

    # -------------------------
    # check_dimensions_of_input_parameters
    # -------------------------
    @testset "check_dimensions_of_input_parameters" begin
        good = Dict(
            "ParameterA" => [1,2,3],
            "ParameterB" => [10,20,30]
        )
        @test check_dimensions_of_input_parameters(good, ["ParameterA","ParameterB"], years) === nothing

        bad = Dict(
            "ParameterA" => [1,2],
            "ParameterB" => [10,20,30]
        )
        @test_throws AssertionError check_dimensions_of_input_parameters(bad, ["ParameterA","ParameterB"], years)
    end

    # -------------------------
    # GeographicElement
    # -------------------------
    @testset "check_correct_formats_GeographicElement" begin
        good = Dict("GeographicElement" => [
            Dict("id"=>1,"type"=>"region","name"=>"North",
                 "carbon_price"=>[1,2,3],"length"=>100.0)
        ])
        @test check_correct_formats_GeographicElement(good, years) === nothing

        bad = Dict("GeographicElement" => [
            Dict("id"=>1,"type"=>"region","name"=>"North",
                 "carbon_price"=>[1,2], "length"=>100.0) # wrong length
        ])
        @test_throws AssertionError check_correct_formats_GeographicElement(bad, years)
    end

    # -------------------------
    # FinancialStatus
    # -------------------------
    @testset "check_correct_formats_FinancialStatus" begin
        good = Dict("FinancialStatus" => [
            Dict("id"=>1,"name"=>"HH","VoT"=>5.0,
                 "monetary_budget_purchase"=>100.0,
                 "monetary_budget_purchase_lb"=>50.0,
                 "monetary_budget_purchase_ub"=>150.0)
        ])
        @test check_correct_formats_FinancialStatus(good) === nothing

        bad = Dict("FinancialStatus" => [
            Dict("id"=>1,"name"=>"HH","VoT"=>"oops",
                 "monetary_budget_purchase"=>100.0,
                 "monetary_budget_purchase_lb"=>50.0,
                 "monetary_budget_purchase_ub"=>150.0)
        ])
        @test_throws AssertionError check_correct_formats_FinancialStatus(bad)
    end

    # -------------------------
    # Mode
    # -------------------------
    @testset "check_correct_format_Mode" begin
        good = Dict("Mode" => [
            Dict("id"=>1,"name"=>"Car","quantify_by_vehs"=>true,
                 "costs_per_ukm"=>[1,2,3],
                 "emission_factor"=>[0.1,0.2,0.3],
                 "infrastructure_expansion_costs"=>[10,20,30],
                 "infrastructure_om_costs"=>[5,5,5],
                 "waiting_time"=>[1,1,1])
        ])
        @test check_correct_format_Mode(good, years) === nothing

        bad = deepcopy(good)
        bad["Mode"][1]["costs_per_ukm"] = [1] # wrong length
        @test_throws AssertionError check_correct_format_Mode(bad, years)
    end

    # -------------------------
    # Product
    # -------------------------
    @testset "check_correct_format_Product" begin
        good = Dict("Product" => [
            Dict("id"=>1,"name"=>"p1","category"=>"c1")
        ])
        @test check_correct_format_Product(good) === nothing

        bad = Dict("Product" => [
            Dict("id"=>1,"category"=>"c1") # missing name
        ])
        @test_throws ErrorException check_correct_format_Product(bad)
    end

    # -------------------------
    # Path
    # -------------------------
    @testset "check_correct_format_Path" begin
        good = Dict("Path" => [Dict("id"=>1,"name"=>"p1")])
        @test check_correct_format_Path(good) === nothing

        bad = Dict("Path" => [Dict("name"=>"p1")]) # missing id
        @test_throws ErrorException check_correct_format_Path(bad)
    end

    # -------------------------
    # Fuel
    # -------------------------
    @testset "check_correct_format_Fuel" begin
        good = Dict("Fuel" => [
            Dict("id"=>1,"name"=>"f1","co2_content"=>[1,2,3])
        ])
        @test check_correct_format_Fuel(good, years) === nothing

        bad = Dict("Fuel" => [
            Dict("id"=>1,"name"=>"f1","co2_content"=>[1]) # wrong length
        ])
        @test_throws AssertionError check_correct_format_Fuel(bad, years)
    end

    # -------------------------
    # Technology
    # -------------------------
    @testset "check_correct_format_Technology" begin
        good = Dict("Technology" => [
            Dict("id"=>1,"name"=>"t1","energy_efficiency"=>[1,2,3])
        ])
        @test check_correct_format_Technology(good, years) === nothing

        bad = Dict("Technology" => [
            Dict("id"=>1,"name"=>"t1","energy_efficiency"=>[1]) # wrong length
        ])
        @test_throws AssertionError check_correct_format_Technology(bad, years)
    end

    # -------------------------
    # Vehicletype
    # -------------------------
    @testset "check_correct_format_Vehicletype" begin
        good = Dict("Vehicletype" => [
            Dict("id"=>1,"name"=>"vt1")
        ])
        @test check_correct_format_Vehicletype(good) === nothing

        bad = Dict("Vehicletype" => [
            Dict("name"=>"vt1") # missing id
        ])
        @test_throws ErrorException check_correct_format_Vehicletype(bad)
    end

    # -------------------------
    # Regiontype
    # -------------------------
    @testset "check_correct_format_Regiontype" begin
        good = Dict("Regiontype" => [Dict("id"=>1,"name"=>"r1")])
        @test check_correct_format_Regiontype(good) === nothing

        bad = Dict("Regiontype" => [Dict("name"=>"r1")]) # missing id
        @test_throws ErrorException check_correct_format_Regiontype(bad)
    end

    # -------------------------
    # TechVehicle
    # -------------------------
    @testset "check_correct_format_TechVehicle" begin
        good = Dict("TechVehicle" => [Dict("id"=>1,"tech_id"=>1,"veh_id"=>1)])
        @test check_correct_format_TechVehicle(good) === nothing

        bad = Dict("TechVehicle" => [Dict("id"=>1,"tech_id"=>1)]) # missing veh_id
        @test_throws ErrorException check_correct_format_TechVehicle(bad)
    end

    # -------------------------
    # InitialVehicleStock
    # -------------------------
    @testset "check_correct_format_InitialVehicleStock" begin
        good = Dict("InitialVehicleStock" => [
            Dict("veh_id"=>1,"region_id"=>1,"stock"=>[1,2])
        ])
        @test check_correct_format_InitialVehicleStock(good, generations) === nothing

        bad = Dict("InitialVehicleStock" => [
            Dict("veh_id"=>1,"region_id"=>1,"stock"=>[1]) # wrong length
        ])
        @test_throws AssertionError check_correct_format_InitialVehicleStock(bad, generations)
    end

    # -------------------------
    # InitialFuelingInfr
    # -------------------------
    @testset "check_correct_format_InitialFuelingInfr" begin
        good = Dict("InitialFuelingInfr" => [
            Dict("fuel_id"=>1,"region_id"=>1,"infra"=>[1,2])
        ])
        @test check_correct_format_InitialFuelingInfr(good, generations) === nothing

        bad = Dict("InitialFuelingInfr" => [
            Dict("fuel_id"=>1,"region_id"=>1,"infra"=>[1]) # wrong length
        ])
        @test_throws AssertionError check_correct_format_InitialFuelingInfr(bad, generations)
    end

    # -------------------------
    # InitialModeInfr
    # -------------------------
    @testset "check_correct_format_InitialModeInfr" begin
        good = Dict("InitialModeInfr" => [
            Dict("mode_id"=>1,"region_id"=>1,"infra"=>[1,2])
        ])
        @test check_correct_format_InitialModeInfr(good, generations) === nothing

        bad = Dict("InitialModeInfr" => [
            Dict("mode_id"=>1,"region_id"=>1,"infra"=>[1]) # wrong length
        ])
        @test_throws AssertionError check_correct_format_InitialModeInfr(bad, generations)
    end

    # -------------------------
    # Odpair
    # -------------------------
    @testset "check_correct_format_Odpair" begin
        good = Dict("Odpair" => [
            Dict("id"=>1,"origin"=>1,"destination"=>2,"distance"=>[10,20,30])
        ])
        @test check_correct_format_Odpair(good, years) === nothing

        bad = Dict("Odpair" => [
            Dict("id"=>1,"origin"=>1,"destination"=>2,"distance"=>[10]) # wrong length
        ])
        @test_throws AssertionError check_correct_format_Odpair(bad, years)
    end

    # -------------------------
    # Speed
    # -------------------------
    @testset "check_correct_format_Speed" begin
        good = Dict("Speed" => [
            Dict("origin"=>1,"destination"=>2,"mode"=>1,"speeds"=>[50,60,70])
        ])
        @test check_correct_format_Speed(good, years) === nothing

        bad = Dict("Speed" => [
            Dict("origin"=>1,"destination"=>2,"mode"=>1,"speeds"=>[50]) # wrong length
        ])
        @test_throws AssertionError check_correct_format_Speed(bad, years)
    end
end
