"""
    Main module for the TransComp package.

This module contains the main functions and structures for the TransComp package.
"""

module TransComp
using YAML, JuMP, Printf
# export data types

include("structs.jl")
include("model_functions.jl")
include("support_functions.jl")
export Node
export Edge
export GeographicElement
export Mode
export Product
export Path
export Fuel
export Technology
export Vehicletype
export TechVehicle
export InitialVehicleStock
export InitialFuelingInfr
export InitialModeInfr
export FinancialStatus
export Regiontype
export Odpair
export Speed
export MarketShares
export ModeShares
export ModeSharemaxbyyear
export ModeShareminbyyear
export EmissionLimitbymode
export EmissionLimitbyyear
export VehicleSubsidy
export SupplyType
export InitialSupplyInfr

# exporting model functions
export base_define_variables
export constraint_demand_coverage
export constraint_vehicle_sizing
export constraint_vehicle_aging
export constraint_monetary_budget
export constraint_fueling_infrastructure
export constraint_mode_infrastructure
export constraint_fueling_demand
export constraint_vehicle_stock_shift
export constraint_mode_shift
export constraint_mode_share
export constraint_max_mode_share
export constraint_min_mode_share
export constraint_market_share
export constraint_emissions_by_mode
export constraint_supply_infrastructure
export objective

# exporting supporting functions
export get_input_data
export parse_data
export create_m_tv_pairs
export create_tv_id_set
export create_v_t_set
export create_p_r_k_set
export create_p_r_k_e_set
export create_p_r_k_g_set
export create_p_r_k_n_set
export create_r_k_set
export create_model
export depreciation_factor
export create_emission_price_along_path
export disagreggate
export save_results

end
