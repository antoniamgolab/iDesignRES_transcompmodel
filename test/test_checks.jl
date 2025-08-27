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

@testset "Format checks (full suite)" begin

    # ------------------------
    # check_required_keys
    # ------------------------
    @testset "check_required_keys" begin
        d_good = Dict("a"=>1, "b"=>2)
        @test check_required_keys(d_good, ["a","b"]) === nothing

        d_bad = Dict("a"=>1)
        @test_throws ErrorException check_required_keys(d_bad, ["a","b"])
    end

    # ------------------------
    # check_model_parametrization
    # ------------------------
    @testset "check_model_parametrization" begin
        md_good = Dict("Model" => Dict("alpha"=>1, "beta"=>2))
        @test check_model_parametrization(md_good, ["alpha","beta"]) === nothing

        md_bad = Dict("Model" => Dict("alpha"=>1))
        @test_throws ErrorException check_model_parametrization(md_bad, ["alpha","beta"])
    end

    # ------------------------
    # check_required_sub_keys
    # ------------------------
    @testset "check_required_sub_keys" begin
        data_ok = Dict("Layers" => [ Dict("id"=>1,"type"=>"conv"), Dict("id"=>2,"type"=>"dense") ])
        @test check_required_sub_keys(data_ok, ["id","type"], "Layers") === nothing

        data_missing = Dict("Layers" => [ Dict("id"=>1,"type"=>"conv"), Dict("id"=>2) ])
        @test_throws AssertionError check_required_sub_keys(data_missing, ["id","type"], "Layers")
    end

    # ------------------------
    # GeographicElement
    # ------------------------
    @testset "check_correct_formats_GeographicElement" begin
        years = 3
        ge_ok = Dict(
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
        @test check_correct_formats_GeographicElement(ge_ok, years) === nothing

        # missing id -> throw(ErrorException(...))
        ge_bad = Dict(
            "GeographicElement" => [
                Dict(
                    "type" => "region",
                    "name" => "North",
                    "carbon_price" => [10.0, 20.0, 30.0],
                    "length" => 100.0
                )
            ]
        )
        @test_throws ErrorException check_correct_formats_GeographicElement(ge_bad, years)
    end

    # ------------------------
    # FinancialStatus
    # ------------------------
    @testset "check_correct_formats_FinancialStatus" begin
        fs_ok = Dict(
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
        @test check_correct_formats_FinancialStatus(fs_ok) === nothing

        # wrong type for VoT -> AssertionError
        fs_bad = Dict(
            "FinancialStatus" => [
                Dict(
                    "id" => 1,
                    "name" => "Household",
                    "VoT" => "five",
                    "monetary_budget_purchase" => 100.0,
                    "monetary_budget_purchase_lb" => 50.0,
                    "monetary_budget_purchase_ub" => 150.0
                )
            ]
        )
        @test_throws AssertionError check_correct_formats_FinancialStatus(fs_bad)
    end

    # ------------------------
    # Mode
    # ------------------------
    @testset "check_correct_format_Mode" begin
        years = 3
        mode_ok = Dict(
            "Mode" => [
                Dict(
                    "id" => 1,
                    "name" => "Car",
                    "quantify_by_vehs" => true,
                    "costs_per_ukm" => [1.0,2.0,3.0],
                    "emission_factor" => [0.1,0.2,0.3],
                    "infrastructure_expansion_costs" => [100.0,200.0,300.0],
                    "infrastructure_om_costs" => [5.0,5.0,5.0],
                    "waiting_time" => [1.0,1.0,1.0]
                )
            ]
        )
        @test check_correct_format_Mode(mode_ok, years) === nothing

        # costs_per_ukm too short -> AssertionError
        mode_bad = Dict(
            "Mode" => [
                Dict(
                    "id" => 1,
                    "name" => "Car",
                    "quantify_by_vehs" => true,
                    "costs_per_ukm" => [1.0], # too short
                    "emission_factor" => [0.1,0.2,0.3],
                    "infrastructure_expansion_costs" => [100.0,200.0,300.0],
                    "infrastructure_om_costs" => [5.0,5.0,5.0],
                    "waiting_time" => [1.0,1.0,1.0]
                )
            ]
        )
        @test_throws AssertionError check_correct_format_Mode(mode_bad, years)
    end

    # ------------------------
    # Product
    # ------------------------
    @testset "check_correct_format_Product" begin
        prod_ok = Dict("Product" => [ Dict("id"=>1, "name"=>"Food") ])
        @test check_correct_format_Product(prod_ok) === nothing

        prod_bad = Dict("Product" => [ Dict("id"=>1) ]) # missing name -> throw(ErrorException)
        @test_throws ErrorException check_correct_format_Product(prod_bad)
    end

    # ------------------------
    # Path
    # ------------------------
    @testset "check_correct_format_Path" begin
        path_ok = Dict("Path" => [ Dict("id"=>1, "name"=>"Route A", "length"=>100.0, "sequence"=>[1,2,3]) ])
        @test check_correct_format_Path(path_ok) === nothing

        path_bad = Dict("Path" => [ Dict("id"=>1, "name"=>"Route B", "length"=>100.0, "sequence"=>["a","b"]) ])
        @test_throws AssertionError check_correct_format_Path(path_bad)
    end

    # ------------------------
    # Fuel
    # ------------------------
    @testset "check_correct_format_Fuel" begin
        years = 3
        fuel_ok = Dict(
            "Fuel" => [
                Dict(
                    "id" => 1,
                    "name" => "Gasoline",
                    "cost_per_kWh" => [1.0,2.0,3.0],
                    "cost_per_kW" => [10.0,20.0,30.0],
                    "emission_factor" => [0.1,0.2,0.3],
                    "fueling_infrastructure_om_costs" => [5.0,5.0,5.0]
                )
            ]
        )
        @test check_correct_format_Fuel(fuel_ok, years) === nothing

        # emission_factor too short -> AssertionError
        fuel_bad = Dict(
            "Fuel" => [
                Dict(
                    "id" => 1,
                    "name" => "Gasoline",
                    "cost_per_kWh" => [1.0,2.0,3.0],
                    "cost_per_kW" => [10.0,20.0,30.0],
                    "emission_factor" => [0.1], # too short
                    "fueling_infrastructure_om_costs" => [5.0,5.0,5.0]
                )
            ]
        )
        @test_throws AssertionError check_correct_format_Fuel(fuel_bad, years)
    end

    # ------------------------
    # Technology
    # ------------------------
    @testset "check_correct_format_Technology" begin
        tech_ok = Dict("Technology" => [ Dict("id"=>1, "name"=>"Battery", "fuel"=>"Electric") ])
        @test check_correct_format_Technology(tech_ok) === nothing

        tech_bad = Dict("Technology" => [ Dict("id"=>1, "name"=>"Battery", "fuel"=>1) ]) # fuel must be String
        @test_throws AssertionError check_correct_format_Technology(tech_bad)
    end

    # ------------------------
    # Vehicletype
    # ------------------------
    @testset "check_correct_format_Vehicletype" begin
        vt_ok = Dict("Vehicletype" => [ Dict("id"=>1, "name"=>"Sedan", "mode"=>1, "product"=>"Passenger") ])
        @test check_correct_format_Vehicletype(vt_ok) === nothing

        vt_bad = Dict("Vehicletype" => [ Dict("id"=>1, "name"=>"Sedan", "mode"=>1) ]) # missing product -> throw(ErrorException)
        @test_throws ErrorException check_correct_format_Vehicletype(vt_bad)
    end

    # ------------------------
    # Regiontype
    # ------------------------
    @testset "check_correct_format_Regiontype" begin
        years = 3
        rt_ok = Dict(
            "Regiontype" => [
                Dict("id"=>1, "name"=>"Urban", "costs_var"=>[10.0,20.0,30.0], "costs_fix"=>[100.0,200.0,300.0])
            ]
        )
        @test check_correct_format_Regiontype(rt_ok, years) === nothing

        rt_bad = Dict("Regiontype" => [ Dict("id"=>1, "name"=>"Urban", "costs_var"=>"expensive", "costs_fix"=>[100.0,200.0,300.0]) ])
        @test_throws AssertionError check_correct_format_Regiontype(rt_bad, years)
    end

    # ------------------------
    # TechVehicle
    # ------------------------
    @testset "check_correct_format_TechVehicle" begin
        years = 3; generations = 2
        tv_ok = Dict(
            "TechVehicle" => [
                Dict(
                    "id"=>1,
                    "name"=>"TV1",
                    "vehicle_type"=>"Sedan",
                    "technology"=>1,
                    "capital_cost"=>[10000.0,9000.0],
                    "maintenance_cost_annual"=>[[100.0,100.0,100.0],[110.0,110.0,110.0]],
                    "maintenance_cost_distance"=>[[0.1,0.1,0.1],[0.12,0.12,0.12]],
                    "W"=>[1.0,1.0],
                    "spec_cons"=>[0.2,0.25],
                    "Lifetime"=>[10,10],
                    "AnnualRange"=>[1000,1000],
                    "products"=>["Passenger"],
                    "tank_capacity"=>[50.0,45.0],
                    "peak_fueling"=>[100.0,90.0]
                )
            ]
        )
        @test check_correct_format_TechVehicle(tv_ok, years, generations) === nothing

        # an inner maintenance_cost_distance array is too short -> AssertionError
        tv_bad = deepcopy(tv_ok)
        tv_bad["TechVehicle"][1]["maintenance_cost_distance"] = [[0.1,0.1], [0.12,0.12,0.12]] # first inner vector too short
        @test_throws AssertionError check_correct_format_TechVehicle(tv_bad, years, generations)
    end

    # ------------------------
    # InitialVehicleStock
    # ------------------------
    @testset "check_correct_format_InitialVehicleStock" begin
        y_init = 2020; g_init = 2015
        ivs_ok = Dict("InitialVehicleStock" => [ Dict("id"=>1, "techvehicle"=>1, "year_of_purchase"=>2018, "stock"=>100) ])
        @test check_correct_format_InitialVehicleStock(ivs_ok, y_init, g_init) === nothing

        ivs_bad = Dict("InitialVehicleStock" => [ Dict("id"=>1, "techvehicle"=>1, "year_of_purchase"=>2010, "stock"=>100) ])
        @test_throws ErrorException check_correct_format_InitialVehicleStock(ivs_bad, y_init, g_init)
    end

    # ------------------------
    # InitialFuelingInfr
    # ------------------------
    @testset "check_correct_format_InitialFuelingInfr" begin
        if_ok = Dict("InitialFuelingInfr" => [ Dict("id"=>1, "fuel"=>"Gasoline", "allocation"=>1, "installed_kW"=>100.0) ])
        @test check_correct_format_InitialFuelingInfr(if_ok) === nothing

        if_bad = Dict("InitialFuelingInfr" => [ Dict("id"=>1, "fuel"=>"Gasoline", "allocation"=>1, "installed_kW"=>"a lot") ])
        @test_throws AssertionError check_correct_format_InitialFuelingInfr(if_bad)
    end

    # ------------------------
    # InitialModeInfr
    # ------------------------
    @testset "check_correct_format_InitialModeInfr" begin
        imi_ok = Dict("InitialModeInfr" => [ Dict("id"=>1, "mode"=>1, "allocation"=>1, "installed_ukm"=>500.0) ])
        @test check_correct_format_InitialModeInfr(imi_ok) === nothing

        imi_bad = Dict("InitialModeInfr" => [ Dict("id"=>1, "mode"=>"one", "allocation"=>1, "installed_ukm"=>500.0) ])
        @test_throws AssertionError check_correct_format_InitialModeInfr(imi_bad)
    end

    # ------------------------
    # Odpair
    # ------------------------
    @testset "check_correct_format_Odpair" begin
        years = 3
        od_ok = Dict(
            "Odpair" => [
                Dict(
                    "id"=>1,
                    "from"=>1,
                    "to"=>2,
                    "path_id"=>1,
                    "F"=>[10.0,20.0,30.0],
                    "product"=>"Food",
                    "vehicle_stock_init"=>[50,60,70],
                    "financial_status"=>"Household",
                    "region_type"=>"Urban"
                )
            ]
        )
        @test check_correct_format_Odpair(od_ok, years) === nothing

        # missing required key "F" -> ErrorException
        od_bad = Dict(
            "Odpair" => [
                Dict(
                    "id"=>1,
                    "from"=>1,
                    "to"=>2,
                    "path_id"=>1,
                    "product"=>"Food",
                    "vehicle_stock_init"=>[50,60,70],
                    "financial_status"=>"Household",
                    "region_type"=>"Urban"
                )
            ]
        )
        @test_throws ErrorException check_correct_format_Odpair(od_bad, years)
    end

    # ------------------------
    # Speed
    # ------------------------
    @testset "check_correct_format_Speed" begin
        speed_ok = Dict("Speed" => [ Dict("id"=>1, "region_type"=>"Urban", "vehicle_type"=>"Sedan", "travel_speed"=>30.0) ])
        @test check_correct_format_Speed(speed_ok) === nothing

        speed_bad = Dict("Speed" => [ Dict("id"=>1, "vehicle_type"=>"Sedan", "travel_speed"=>30.0) ]) # missing region_type -> ErrorException
        @test_throws ErrorException check_correct_format_Speed(speed_bad)
    end
end
