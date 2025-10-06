using Test
using TransComp

# Set constants for tests
years = 3
generations = 2
y_init = 2025
g_init = 2025

@testset "Checks functions" begin
    @testset "check_input_file" begin
        @test_throws ErrorException check_input_file("nonexistent.yaml")
        @test_throws ErrorException check_input_file("file.txt")
        @test_throws ErrorException check_input_file("nonexistent_folder")
        # Create a temp folder with no YAML files and test
        mktempdir() do tmpdir
            @test_throws ErrorException check_input_file(tmpdir)
        end
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
            "Layers" =>
                [Dict("id" => 1, "type" => "conv"), Dict("id" => 2, "type" => "dense")],
        )
        required_keys = ["id", "type"]

        @test check_required_sub_keys(data_valid, required_keys, "Layers") === nothing

        # Case 2: missing a key in one dict, should throw AssertionError
        data_invalid = Dict("Layers" => [
            Dict("id" => 1),              # missing "type"
            Dict("id" => 2, "type" => "dense"),
        ])

        @test_throws AssertionError check_required_sub_keys(
            data_invalid,
            required_keys,
            "Layers",
        )
    end


    @testset "check_folder_writable" begin
        @test_throws ErrorException check_folder_writable("nonexistent_folder")
    end

    @testset "check_validity_of_model_parametrization" begin
        d = Dict(
            "Model" => Dict(
                "y_init" => "notint",
                "Y" => 1,
                "pre_y" => 1,
                "discount_rate" => 0.05,
            ),
        )
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
    # ------------------------------
    # GeographicElement
    # ------------------------------
    @testset "GeographicElement" begin
        good = Dict(
            "GeographicElement" => [
                Dict(
                    "id" => 1,
                    "type" => "region",
                    "name" => "Region A",
                    "carbon_price" => [10.0, 12.0, 14.0],
                    "length" => 100.0,
                ),
            ],
        )
        bad = Dict(
            "GeographicElement" => [
                Dict(
                    "id" => "wrong",
                    "type" => 123,
                    "name" => 456,
                    "carbon_price" => [10, "12", 14],
                    "length" => "long",
                ),
            ],
        )
        @test TransComp.check_correct_formats_GeographicElement(good, years) === nothing
        @test_throws AssertionError TransComp.check_correct_formats_GeographicElement(
            bad,
            years,
        )
    end

    # ------------------------------
    # FinancialStatus
    # ------------------------------
    @testset "FinancialStatus" begin
        good = Dict(
            "FinancialStatus" => [
                Dict(
                    "id" => 1,
                    "name" => "Low Income",
                    "VoT" => 50.0,
                    "monetary_budget_purchase" => 10000.0,
                    "monetary_budget_purchase_lb" => 5000.0,
                    "monetary_budget_purchase_ub" => 15000.0,
                ),
            ],
        )
        bad = Dict(
            "FinancialStatus" => [
                Dict(
                    "id" => "wrong",
                    "name" => 123,
                    "VoT" => "high",
                    "monetary_budget_purchase" => "many",
                    "monetary_budget_purchase_lb" => 20000.0,
                    "monetary_budget_purchase_ub" => 15000.0,
                ),
            ],
        )
        @test TransComp.check_correct_formats_FinancialStatus(good) === nothing
        @test_throws AssertionError TransComp.check_correct_formats_FinancialStatus(bad)
    end

    # ------------------------------
    # Mode
    # ------------------------------
    @testset "Mode" begin
        good = Dict(
            "Mode" => [
                Dict(
                    "id" => 1,
                    "name" => "Car",
                    "quantify_by_vehs" => true,
                    "costs_per_ukm" => [0.1, 0.12, 0.14],
                    "emission_factor" => [100.0, 95.0, 90.0],
                    "infrastructure_expansion_costs" => [1000.0, 1100.0, 1200.0],
                    "infrastructure_om_costs" => [100.0, 110.0, 120.0],
                    "waiting_time" => [5.0, 5.0, 5.0],
                ),
            ],
        )
        bad = Dict(
            "Mode" => [
                Dict(
                    "id" => "one",
                    "name" => 123,
                    "quantify_by_vehs" => "yes",
                    "costs_per_ukm" => [0.1, "0.12", 0.14],
                    "emission_factor" => ["high", 95.0, 90.0],
                    "infrastructure_expansion_costs" => [1000, "1100", 1200],
                    "infrastructure_om_costs" => [100, 110, "120"],
                    "waiting_time" => ["fast", 5.0, 5.0],
                ),
            ],
        )
        @test TransComp.check_correct_format_Mode(good, years) === nothing
        @test_throws AssertionError TransComp.check_correct_format_Mode(bad, years)
    end

    # ------------------------------
    # Product
    # ------------------------------
    @testset "Product" begin
        good = Dict("Product" => [Dict("id" => 1, "name" => "Battery")])
        bad = Dict("Product" => [Dict("id" => "wrong", "name" => 123)])
        @test TransComp.check_correct_format_Product(good) === nothing
        @test_throws AssertionError TransComp.check_correct_format_Product(bad)
    end

    # ------------------------------
    # Path
    # ------------------------------
    @testset "Path" begin
        good = Dict(
            "Path" => [
                Dict(
                    "id" => 1,
                    "name" => "PathA",
                    "length" => 100.0,
                    "sequence" => [1, 2, 3],
                ),
            ],
        )
        bad = Dict(
            "Path" => [
                Dict(
                    "id" => "x",
                    "name" => 123,
                    "length" => "long",
                    "sequence" => ["a", "b"],
                ),
            ],
        )
        @test TransComp.check_correct_format_Path(good) === nothing
        @test_throws AssertionError TransComp.check_correct_format_Path(bad)
    end

    # ------------------------------
    # Fuel
    # ------------------------------
    @testset "Fuel" begin
        good = Dict(
            "Fuel" => [
                Dict(
                    "id" => 1,
                    "name" => "Electric",
                    "cost_per_kWh" => [0.2, 0.21, 0.22],
                    "cost_per_kW" => [1000, 1050, 1100],
                    "emission_factor" => [0.0, 0.0, 0.0],
                    "fueling_infrastructure_om_costs" => [10, 11, 12],
                ),
            ],
        )
        bad = Dict(
            "Fuel" => [
                Dict(
                    "id" => "one",
                    "name" => 123,
                    "cost_per_kWh" => [0.2, "0.21", 0.22],
                    "cost_per_kW" => ["1000", 1050, 1100],
                    "emission_factor" => ["low", 0.0, 0.0],
                    "fueling_infrastructure_om_costs" => ["ten", 11, 12],
                ),
            ],
        )
        @test TransComp.check_correct_format_Fuel(good, years) === nothing
        @test_throws AssertionError TransComp.check_correct_format_Fuel(bad, years)
    end

    # ------------------------------
    # Technology
    # ------------------------------
    @testset "Technology" begin
        good = Dict(
            "Technology" =>
                [Dict("id" => 1, "name" => "EV Motor", "fuel" => "Electric")],
        )
        bad = Dict("Technology" => [Dict("id" => "one", "name" => 123, "fuel" => 456)])
        @test TransComp.check_correct_format_Technology(good) === nothing
        @test_throws AssertionError TransComp.check_correct_format_Technology(bad)
    end

    # ------------------------------
    # Vehicletype
    # ------------------------------
    @testset "Vehicletype" begin
        good = Dict(
            "Vehicletype" => [
                Dict("id" => 1, "name" => "Sedan", "mode" => 1, "product" => "Battery"),
            ],
        )
        bad = Dict(
            "Vehicletype" =>
                [Dict("id" => "x", "name" => 123, "mode" => "one", "product" => 456)],
        )
        @test TransComp.check_correct_format_Vehicletype(good) === nothing
        @test_throws AssertionError TransComp.check_correct_format_Vehicletype(bad)
    end

    # ------------------------------
    # Regiontype
    # ------------------------------
    @testset "Regiontype" begin
        good = Dict(
            "Regiontype" => [
                Dict(
                    "id" => 1,
                    "name" => "Urban",
                    "costs_var" => [10, 11, 12],
                    "costs_fix" => [100, 110, 120],
                ),
            ],
        )
        bad = Dict(
            "Regiontype" => [
                Dict(
                    "id" => "x",
                    "name" => 123,
                    "costs_var" => ["10", 11, 12],
                    "costs_fix" => [100, "110", 120],
                ),
            ],
        )
        @test TransComp.check_correct_format_Regiontype(good, years) === nothing
        @test_throws AssertionError TransComp.check_correct_format_Regiontype(bad, years)
    end

    # ------------------------------
    # TechVehicle
    # ------------------------------
    @testset "TechVehicle" begin
        good = Dict(
            "TechVehicle" => [
                Dict(
                    "id" => 1,
                    "name" => "EV1",
                    "vehicle_type" => "Sedan",
                    "technology" => 1,
                    "capital_cost" => [30000, 31000],
                    "maintenance_cost_annual" =>
                        [[1000, 1050, 1100], [1100, 1150, 1200]],
                    "maintenance_cost_distance" =>
                        [[0.1, 0.11, 0.12], [0.12, 0.13, 0.14]],
                    "W" => [10, 11],
                    "spec_cons" => [0.15, 0.16],
                    "Lifetime" => [10, 10],
                    "AnnualRange" => [15000, 15000],
                    "products" => ["Battery"],
                    "tank_capacity" => [60, 60],
                    "peak_fueling" => [50, 50],
                ),
            ],
        )
        bad = Dict(
            "TechVehicle" => [
                Dict(
                    "id" => "x",
                    "name" => 123,
                    "vehicle_type" => 456,
                    "technology" => "one",
                    "capital_cost" => [30000, "31000"],
                    "maintenance_cost_annual" => [[1000, 1050, "1100"]],
                    "maintenance_cost_distance" => [[0.1, "0.11", 0.12]],
                    "W" => ["ten"],
                    "spec_cons" => ["0.15"],
                    "Lifetime" => [10, "10"],
                    "AnnualRange" => [15000, "15000"],
                    "products" => [123],
                    "tank_capacity" => [60, "60"],
                    "peak_fueling" => [50, "50"],
                ),
            ],
        )
        @test TransComp.check_correct_format_TechVehicle(good, years, generations) ===
              nothing
        @test_throws AssertionError TransComp.check_correct_format_TechVehicle(
            bad,
            years,
            generations,
        )
    end

    # ------------------------------
    # InitialVehicleStock
    # ------------------------------
    @testset "InitialVehicleStock" begin
        y_init = 2026
        g_init = 2025

        good = Dict(
            "InitialVehicleStock" => [
                Dict(
                    "id" => 1,
                    "techvehicle" => 1,
                    "year_of_purchase" => 2025,
                    "stock" => 10,
                ),
            ],
        )

        bad = Dict(
            "InitialVehicleStock" => [
                # year_of_purchase earlier than first generation
                Dict(
                    "id" => 1,
                    "techvehicle" => 1,
                    "year_of_purchase" => 2024,
                    "stock" => 10,
                ),
                # year_of_purchase later than first considered year
                Dict(
                    "id" => 2,
                    "techvehicle" => 2,
                    "year_of_purchase" => 2026,
                    "stock" => 5,
                ),
                # stock is not int or float
                Dict(
                    "id" => 3,
                    "techvehicle" => 3,
                    "year_of_purchase" => 2025,
                    "stock" => "ten",
                ),
            ],
        )
        @test TransComp.check_correct_format_InitialVehicleStock(good, y_init, g_init) ===
              nothing
        @test_throws AssertionError TransComp.check_correct_format_InitialVehicleStock(
            bad,
            y_init,
            g_init,
        )

    end

    # ------------------------------
    # InitialFuelingInfr
    # ------------------------------
    @testset "InitialFuelingInfr" begin
        good = Dict(
            "InitialFuelingInfr" => [
                Dict(
                    "id" => 1,
                    "fuel" => "Electric",
                    "allocation" => 1,
                    "installed_kW" => 100,
                ),
            ],
        )
        bad = Dict(
            "InitialFuelingInfr" => [
                Dict(
                    "id" => "x",
                    "fuel" => 123,
                    "allocation" => "one",
                    "installed_kW" => "100",
                ),
            ],
        )
        @test TransComp.check_correct_format_InitialFuelingInfr(good) === nothing
        @test_throws AssertionError TransComp.check_correct_format_InitialFuelingInfr(bad)
    end

    # ------------------------------
    # InitialModeInfr
    # ------------------------------
    @testset "InitialModeInfr" begin
        good = Dict(
            "InitialModeInfr" => [
                Dict("id" => 1, "mode" => 1, "allocation" => 1, "installed_ukm" => 100),
            ],
        )
        bad = Dict(
            "InitialModeInfr" => [
                Dict(
                    "id" => "x",
                    "mode" => "one",
                    "allocation" => "one",
                    "installed_ukm" => "100",
                ),
            ],
        )
        @test TransComp.check_correct_format_InitialModeInfr(good) === nothing
        @test_throws AssertionError TransComp.check_correct_format_InitialModeInfr(bad)
    end

    # ------------------------------
    # Odpair
    # ------------------------------
    @testset "Odpair" begin
        good = Dict(
            "Odpair" => [
                Dict(
                    "id" => 1,
                    "from" => 1,
                    "to" => 2,
                    "path_id" => 1,
                    "F" => [100.0, 105.0, 110.0],
                    "product" => "Battery",
                    "vehicle_stock_init" => [10, 12, 14],
                    "financial_status" => "Low Income",
                    "region_type" => "Urban",
                ),
            ],
        )
        bad = Dict(
            "Odpair" => [
                Dict(
                    "id" => "x",
                    "from" => "one",
                    "to" => "two",
                    "path_id" => "p",
                    "F" => ["100", 105, 110],
                    "product" => 123,
                    "vehicle_stock_init" => ["ten", 12, 14],
                    "financial_status" => 1,
                    "region_type" => 2,
                ),
            ],
        )
        @test TransComp.check_correct_format_Odpair(good, years) === nothing
        @test_throws AssertionError TransComp.check_correct_format_Odpair(bad, years)
    end

    # ------------------------------
    # Speed
    # ------------------------------
    @testset "Speed" begin
        good = Dict(
            "Speed" => [
                Dict(
                    "id" => 1,
                    "region_type" => "Urban",
                    "vehicle_type" => "Sedan",
                    "travel_speed" => 50.0,
                ),
            ],
        )
        bad = Dict(
            "Speed" => [
                Dict(
                    "id" => "x",
                    "region_type" => 123,
                    "vehicle_type" => 456,
                    "travel_speed" => "fast",
                ),
            ],
        )
        @test TransComp.check_correct_format_Speed(good) === nothing
        @test_throws AssertionError TransComp.check_correct_format_Speed(bad)
    end

end
