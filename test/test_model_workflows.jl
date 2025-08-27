using Test
using JuMP
using HiGHS
using TransComp

using TransComp


# Minimal mock Mode and TechVehicle according to structs.jl
mode = Mode(
    1,
    "road",
    true,
    [0.0, 0.0],
    [0.0, 0.0],
    [0.0, 0.0],
    [0.0, 0.0],
    [0.0, 0.0]
)
product = Product(1, "default")
fuel = Fuel(
    1,
    "electricity",
    [0.0, 0.0],
    [0.0, 0.0],
    [0.0, 0.0],
    [0.0, 0.0]
)
technology = Technology(1, "BEV", fuel)
vehicletype = Vehicletype(1, "car", mode, [product])
techvehicle = TechVehicle(
    1,
    "EV",
    vehicletype,
    technology,
    [0.0, 0.0],
    [[0.0, 0.0], [0.0, 0.0]],
    [[0.0, 0.0], [0.0, 0.0]],
    [0.0, 0.0],
    [0.0, 0.0],
    [1, 2],
    [0.0, 0.0],
    [product, product],
    [0.0, 0.0],
    [0.0, 0.0],
    [0.0, 0.0]
)

data_structures = Dict(
    "y_init" => 2020,
    "Y_end" => 2022,
    "g_init" => 2020,
    "odpair_list" => [Odpair(1, GeographicElement(1, "node", "A", [0.0, 0.0], nothing, nothing, 0.0), GeographicElement(2, "node", "B", [0.0, 0.0], nothing, nothing, 0.0), [Path(1, "A-B", 1.0, [])], 1.0, product, [InitialVehicleStock(1, techvehicle, 2020, 10.0)], FinancialStatus(1, "default", 10.0, 1000.0, 900.0, 1100.0, 5), Regiontype(1, "urban", [0.1, 0.1], [0.2, 0.2]), 100.0)],
    "techvehicle_list" => [techvehicle],
    "mode_list" => [mode],
    "product_list" => [product],
    "path_list" => [],
    "regiontype_list" => [Regiontype(1, "urban", [0.1, 0.1], [0.2, 0.2])],
    "fuel_list" => [fuel],
    "technology_list" => [technology],
    "vehicletype_list" => [vehicletype],
    "market_share_list" => [MarketShares(1, techvehicle, 100.0, 2020, [Regiontype(1, "urban", [0.1, 0.1], [0.2, 0.2])])],
    "emission_constraints_by_mode_list" => [EmissionLimitbymode(1, mode, 0.0, 2020)],
    "initialfuelinginfr_list" => [InitialFuelingInfr(1, fuel, nothing, 100.0)],
    "initialmodeinfr_list" => [InitialModeInfr(1, mode, nothing, 100.0)],
    "initialsupplyinfr_list" => [InitialSupplyInfr(1, "default", fuel, SupplyType(1, "default", fuel, [0.0], [0.0]), nothing, 100.0)],
    "vehicle_subsidy_list" => [VehicleSubsidy(1, "subsidy", [2020], techvehicle, 1000.0)],
    "geographic_element_list" => [GeographicElement(1, "node", "A", [0.0, 0.0], nothing, nothing, 0.0)],
    "init_detour_times_list" => [InitDetourTime(1, fuel, GeographicElement(1, "node", "A", [0.0], nothing, nothing, 0.0), 0.5)],
    "detour_time_reduction_list" => [DetourTimeReduction(1, fuel, GeographicElement(1, "node", "A", [0.0], nothing, nothing, 0.0), 1, 0.1, 0.0, 1.0)],
    "supplytype_list" => [SupplyType(1, "default", fuel, [0.0, 0.0], [0.0, 0.0])],
    "m_tv_pairs" => [],
    "techvehicle_ids" => [],
    "t_v_pairs" => [],
    "p_r_k_pairs" => [],
    "p_r_k_e_pairs" => [],
    "p_r_k_n_pairs" => [],
    "p_r_k_g_pairs" => [],
    "r_k_pairs" => [],
    "speed_list" => [Speed(1, Regiontype(1, "urban", [0.1], [0.2]), vehicletype, 50.0)],
    "default_data" => Dict(),
    "Model" => Dict("Y"=>1,"y_init"=>2020,"pre_y"=>0,"gamma"=>1,"discount_rate"=>0.05,"budget_penalty_plus"=>1,"budget_penalty_minus"=>1)
)
optimizer = HiGHS.Optimizer

@testset "Model workflow functions include expected constraints" begin
    model, _ = run_minimum_viable_case(data_structures, optimizer)
    @test haskey(model, :f)
    @test length(all_constraints(model)) > 0

    model, _ = run_vehicle_stock_sizing(data_structures, optimizer)
    @test haskey(model, :h)
    @test length(all_constraints(model)) > 0

    model, _ = run_vehicle_stock_aging(data_structures, optimizer)
    @test haskey(model, :h_exist)
    @test length(all_constraints(model)) > 0

    model, _ = run_constrained_technology_shift(data_structures, optimizer)
    @test haskey(model, :h_exist)
    @test length(all_constraints(model)) > 0

    model, _ = run_fueling_infrastructure_sizing(data_structures, optimizer)
    @test haskey(model, :q_fuel_infr_plus)
    @test length(all_constraints(model)) > 0

    model, _ = run_constrained_mode_shift(data_structures, optimizer)
    @test haskey(model, :h)
    @test length(all_constraints(model)) > 0

    model, _ = run_mode_infrastructure_sizing(data_structures, optimizer)
    @test haskey(model, :q_mode_infr_plus)
    @test length(all_constraints(model)) > 0
end
