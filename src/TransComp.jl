"""
    Main module for the TransComp package.

This module contains the main functions and structures for the TransComp package.
"""

module TransComp

using YAML, JuMP, Printf

# Include all source files
include("structs.jl")
include("model_functions.jl")
include("support_functions.jl")
include("checks.jl")

# Export types (from structs.jl)
export Node, Edge, GeographicElement, Mode, Product, Path, Fuel, Technology, Vehicletype, TechVehicle, InitialVehicleStock, InitialFuelingInfr, InitialModeInfr, FinancialStatus, Regiontype, Odpair, Speed, MarketShares, ModeShares, ModeSharemaxbyyear, ModeShareminbyyear, EmissionLimitbymode, EmissionLimitbyyear, VehicleSubsidy, SupplyType, InitialSupplyInfr

# Export model functions (from model_functions.jl)
export base_define_variables, constraint_demand_coverage, constraint_vehicle_sizing, constraint_vehicle_aging, constraint_monetary_budget, constraint_fueling_infrastructure, constraint_mode_infrastructure, constraint_fueling_demand, constraint_vehicle_stock_shift, constraint_mode_shift, constraint_mode_share, constraint_max_mode_share, constraint_min_mode_share, constraint_market_share, constraint_emissions_by_mode, constraint_supply_infrastructure, objective

# Export supporting functions (from support_functions.jl)
export get_input_data, parse_data, create_m_tv_pairs, create_tv_id_set, create_v_t_set, create_p_r_k_set, create_p_r_k_e_set, create_p_r_k_g_set, create_p_r_k_n_set, create_r_k_set, create_model, depreciation_factor, create_emission_price_along_path, disagreggate, save_results

# Export checks (from checks.jl)
export check_input_file, check_required_keys, check_model_parametrization, check_required_sub_keys, check_folder_writable, check_dimensions_of_input_parameters, check_validity_of_model_parametrization, check_uniquness_of_ids
# Add more exports from checks.jl as needed

end
