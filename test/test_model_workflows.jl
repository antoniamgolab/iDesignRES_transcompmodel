using Test, JuMP, HiGHS, TransComp

using Dates

# Years
y_init = 2020
Y_end = 2022
nyears = Y_end - y_init + 1
pre_y = 0
g_init = y_init - pre_y

# Minimal GeographicElement
ge_elem = GeographicElement(1, "node", "Node1", fill(60.0, nyears), 1, 1, 10.0)

# Minimal FinancialStatus
fin_status = FinancialStatus(1, "default", 15.0, 10000.0, 9000.0, 11000.0, 5)

# Minimal Regiontype
region = Regiontype(1, "urban", fill(0.0, nyears), fill(0.0, nyears))

# Minimal Mode
mode = Mode(1, "road", true, zeros(nyears), zeros(nyears), zeros(nyears), zeros(nyears), zeros(nyears))

# Minimal Product
product = Product(1, "default")

# Minimal Fuel
fuel = Fuel(1, "electricity", fill(0.0, nyears), fill(0.0, nyears), fill(0.0, nyears), fill(0.0, nyears))

# Minimal Technology
technology = Technology(1, "BEV", fuel)

# Minimal Vehicletype
vehicletype = Vehicletype(1, "car", mode, [product])

# Minimal TechVehicle
techvehicle = TechVehicle(
    1,
    "EV",
    vehicletype,
    technology,
    fill(0.0, nyears),                      # capital_cost
    [fill(0.0, nyears) for _ in 1:nyears],  # maintenance_cost_annual
    [fill(0.0, nyears) for _ in 1:nyears],  # maintenance_cost_distance
    fill(1.0, nyears),                      # W
    fill(0.0, nyears),                      # spec_cons
    fill(5, nyears),                        # Lifetime
    fill(10000.0, nyears),                  # AnnualRange
    [product],                               # products
    fill(50.0, nyears),                     # tank_capacity
    fill(10.0, nyears),                     # peak_fueling
    fill(0.5, nyears)                       # fueling_time
)

# Minimal InitialVehicleStock
init_stock = InitialVehicleStock(1, techvehicle, y_init, 1.0)

# Minimal Path
path = Path(1, "path1", 10.0, [ge_elem])

# Minimal Odpair
odpair = Odpair(
    1,
    ge_elem,
    ge_elem,
    [path],
    fill(100.0, nyears),
    product,
    [init_stock],
    fin_status,
    region,
    120.0
)

# Minimal Initial Mode & Fueling Infrastructure
initial_mode_infr = InitialModeInfr(1, mode, 1, 0.0)
initial_fueling_infr = InitialFuelingInfr(1, fuel, 1, 0.0)

# Create data_structures dict
data_structures = Dict(
    "y_init" => y_init,
    "Y_end" => Y_end,
    "pre_y" => pre_y,
    "Y" => nyears,
    "g_init" => g_init,
    "gamma" => 1.0,
    "budget_penalty_plus" => 100,
    "budget_penalty_minus" => 100,
    "alpha_f" => 1.0,
    "beta_f" => 1.0,
    "alpha_h" => 0.5,
    "beta_h" => 0.5,
    "discount_rate" => 0.05,
    "techvehicle_list" => [techvehicle],
    "mode_list" => [mode],
    "product_list" => [product],
    "fuel_list" => [fuel],
    "technology_list" => [technology],
    "vehicletype_list" => [vehicletype],
    "odpair_list" => [odpair],
    "initvehiclestock_list" => [init_stock],
    "initialmodeinfr_list" => [initial_mode_infr],
    "initialfuelinginfr_list" => [initial_fueling_infr],
    "initialsupplyinfr_list" => [],  # missing from first dict
    "financial_status_list" => [fin_status],
    "regiontype_list" => [region],
    "path_list" => [path],
    "geographic_element_list" => [ge_elem],
    "speed_list" => [],  # added
    "market_share_list" => [],  # added
    "emission_constraints_by_mode_list" => [],  # added
    "mode_shares_list" => [],  # added
    "max_mode_shares_list" => [],  # added
    "min_mode_shares_list" => [],  # added
    "vehicle_subsidy_list" => [],  # added
    "init_detour_times_list" => [],  # added
    "detour_time_reduction_list" => [],  # added
    "supplytype_list" => [],  # already in first
    
)


speed = Speed(1, region, vehicletype, 60.0)  # travel speed 60 km/h
speed_list = [speed]

# Then in your data_structures dictionary:
data_structures["speed_list"] = speed_list
# Optimizer
optimizer = HiGHS.Optimizer

@testset "Model workflow functions include expected constraints" begin
    model, _ = run_minimum_viable_case(data_structures, optimizer)
    @test haskey(model, :f)
    @test length(all_constraints(model; include_variable_in_set_constraints=true)) > 0

    model, _ = run_vehicle_stock_sizing(data_structures, optimizer)
        @test haskey(model, :h)
        @test length(all_constraints(model; include_variable_in_set_constraints=true)) > 0

    model, _ = run_vehicle_stock_aging(data_structures, optimizer)
    @test haskey(model, :h_exist)
    @test length(all_constraints(model; include_variable_in_set_constraints=true)) > 0

    model, _ = run_constrained_technology_shift(data_structures, optimizer)
    @test haskey(model, :h_exist)
        @test length(all_constraints(model; include_variable_in_set_constraints=true)) > 0

    model, _ = run_fueling_infrastructure_sizing(data_structures, optimizer)
    @test haskey(model, :q_fuel_infr_plus)
        @test length(all_constraints(model; include_variable_in_set_constraints=true)) > 0

    model, _ = run_constrained_mode_shift(data_structures, optimizer)
    @test haskey(model, :h)
        @test length(all_constraints(model; include_variable_in_set_constraints=true)) > 0

    model, _ = run_mode_infrastructure_sizing(data_structures, optimizer)
    @test haskey(model, :q_mode_infr_plus)
        @test length(all_constraints(model; include_variable_in_set_constraints=true)) > 0
end
