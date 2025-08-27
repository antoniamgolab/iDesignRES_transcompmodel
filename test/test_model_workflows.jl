using Test
using JuMP
using HiGHS
using TransComp

# Dummy data_structures for testing (should be replaced with a proper fixture or mock)
data_structures = Dict(
    "y_init" => 2020,
    "Y_end" => 2022,
    "g_init" => 2020,
    "odpair_list" => [],
    "techvehicle_list" => [],
    "mode_list" => [],
    "product_list" => [],
    "path_list" => [],
    "regiontype_list" => [],
    "fuel_list" => [],
    "technology_list" => [],
    "vehicletype_list" => [],
    "market_share_list" => [],
    "emission_constraints_by_mode_list" => [],
    "initialfuelinginfr_list" => [],
    "initialmodeinfr_list" => [],
    "initialsupplyinfr_list" => [],
    "vehicle_subsidy_list" => [],
    "geographic_element_list" => [],
    "init_detour_times_list" => [],
    "detour_time_reduction_list" => [],
    "supplytype_list" => [],
    "m_tv_pairs" => [],
    "techvehicle_ids" => [],
    "t_v_pairs" => [],
    "p_r_k_pairs" => [],
    "p_r_k_e_pairs" => [],
    "p_r_k_n_pairs" => [],
    "p_r_k_g_pairs" => [],
    "r_k_pairs" => [],
    "speed_list" => [],
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
