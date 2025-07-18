"""
This module contains functions to check for potential issues in the input data.
"""

"""
    check_input_file(path_to_source_file::String)

Check if the input file exists and is a YAML file.

# Arguments
- `path_to_source_file::String`: The path to the input file.
"""
function check_input_file(path_to_source_file::String)
    if !isfile(path_to_source_file)
        error("The input file does not exist.")
    end

    if !endswith(path_to_source_file, ".yaml") && !endswith(path_to_source_file, ".yml")
        error("The input file must be a YAML file.")
    end
end

"""
    check_required_keys(data_dict::Dict, required_keys::Vector{String})

Check if the required keys are present in the input data.

# Arguments
- `data_dict::Dict`: The input data.
"""
function check_required_keys(data_dict::Dict, required_keys::Vector{String})
    for key ∈ required_keys
        @assert haskey(data_dict, key) "The key $key is missing in the input file."
    end
end

"""
    check_model_parametrization(data_dict::Dict, required_keys::Vector{String})

Check if the required keys are present in the model data.

# Arguments
- `data_dict::Dict`: The input data.

# Returns
- `Bool`: True if the required keys are present, false otherwise.
"""
function check_model_parametrization(data_dict::Dict, required_keys::Vector{String})
    return check_required_keys(data_dict["Model"], required_keys)
end

"""
    check_required_sub_keys(data_dict::Dict, required_keys::Vector{String}, parent_key::String)

Check if the keys are defined for a parent key in the input data.
"""
function check_required_sub_keys(
    data_dict::Dict,
    required_keys::Vector{String},
    parent_key::String,
)
    for key ∈ required_keys
        for d ∈ data_dict[parent_key]
            @assert haskey(d, key) "The key $key is missing in the definition of $parent_key."
        end
    end
end

"""
    check_folder_writable(folder_path::String)

Check if the folder exists and can be written in.

# Arguments
- `folder_path::String`: The path to the folder.
"""
function check_folder_writable(folder_path::String)
    if !isdir(folder_path)
        error("The folder does not exist.")
    end

    test_file = joinpath(folder_path, "test_write_permission.tmp")
    try
        open(test_file, "w") do f
            write(f, "test")
        end
        rm(test_file)
    catch e
        error("The folder is not writable: $e")
    end
end

# TODO: check for detour_time_reduction_list -> is lb and ub do not overlap but are adjacent + check if reduction ids are ascending and are not repeating

function check_dimensions_of_input_parameters(data_structures::Dict)
    return true
end

"""
    check_validity_of_model_parametrization(data_structures::Dict)

Checks if model parametrization has correct format.

# Arguments
- `data_structures::Dict`: The input data.

"""

function check_validity_of_model_parametrization(data_structures::Dict)
    @assert isa(data_structures["Model"]["y_init"], Int) "The key 'y_init' in 'Model' must be an integer value."
    @assert isa(data_structures["Model"]["Y"], Int) "The key 'Y' in 'Model' must be an integer value."
    @assert isa(data_structures["Model"]["pre_y"], Int) "The key 'pre_y' in 'Model' must be an integer value."
    @assert isa(data_structures["Model"]["discount_rate"], Float64) "The key 'discount_rate' in 'Model' must be an integer value."
end

"""
    check_uniquness_of_ids(data_structures::Dict, required_keys::Vector{String})

Checks if all "id" entries in a list of dictionaries are unique.

# Arguments
- `data_structures::Dict`: The input data.
- `required_keys::Vector{String}`: The keys to check for uniqueness.
"""
function check_uniquness_of_ids(data_structures::Dict, required_keys)
    for key ∈ required_keys
        if key != "Model"
            ids = [d["id"] for d ∈ data_structures[key]]
            if length(ids) != length(unique(ids))
                error("The ids of $key entries in input data must be unique.")
            end
        end
    end
end

"""
    check_correct_formats_GeographicElement(data_structures::Dict, years)

Check if the format of the GeographicElement entries is correct.

# Arguments
- `data_structures::Dict`: The input data.
- `years::Int`: The number of years in the optimization horizon.
"""
function check_correct_formats_GeographicElement(data_structures::Dict, years)
    for ij ∈ 1:length(data_structures["GeographicElement"])
        d = data_structures["GeographicElement"][ij]

        # checking for the variable types
        @assert isa(d["id"], Int) "The key 'id' in 'GeographicElement' must be an integer value. Error at $(d["id"])."
        @assert isa(d["type"], String) "The key 'type' in 'GeographicElement' must be a string value. Error at $(d["id"])."
        @assert isa(d["name"], String) "The key 'name' in 'GeographicElement' must be a string value. Error at $(d["id"])."
        @assert (
            isa(d["carbon_price"], Array{Float64,1}) ||
            isa(d["carbon_price"], Array{Int,1})
        ) "The key 'carbon_price' in 'GeographicElement' must be an array with int or float values. Error at $(d["id"])."
        @assert (isa(d["length"], Float64) || isa(d["length"], Int)) "The key 'length' in 'GeographicElement' must be a float value. Error at $(d["id"])."

        # checking for the correct length of arrays
        @assert length(d["carbon_price"]) >= years "The key 'carbon_price' in 'GeographicElement' must have the same length as the years of the optimization horizon. Error at $(d["id"])."
    end
end

"""
    check_correct_formats_FinancialStatus(data_structures::Dict, years)

Check if the format of the FinancialStatus entries is correct.

# Arguments
- `data_structures::Dict`: The input data.

"""
function check_correct_formats_FinancialStatus(data_structures::Dict)
    for ij ∈ 1:length(data_structures["FinancialStatus"])
        fs = data_structures["FinancialStatus"][ij]

        # checking for the variable types
        @assert isa(fs["id"], Int) "The key 'id' in 'FinancialStatus' must be an integer value. Error at $(fs["id"])."
        @assert isa(fs["name"], String) "The key 'name' in 'FinancialStatus' must be a string value. Error at $(fs["id"])."
        @assert (isa(fs["VoT"], Float64) || isa(fs["VoT"], Int)) "The key 'VoT' in 'FinancialStatus' must be a float or int value. Error at $(fs["id"])."
        @assert (
            isa(fs["monetary_budget_purchase"], Float64) ||
            isa(fs["monetary_budget_purchase"], Int)
        ) "The key 'monetary_budget_purchase' in 'FinancialStatus' must be a float or int value. Error at $(fs["id"])."
        @assert (
            isa(fs["monetary_budget_purchase_lb"], Float64) ||
            isa(fs["monetary_budget_purchase_lb"], Int)
        ) "The key 'monetary_budget_purchase_lb' in 'FinancialStatus' must be a float or int value. Error at $(fs["id"])."
        @assert (
            isa(fs["monetary_budget_purchase_ub"], Float64) ||
            isa(fs["monetary_budget_purchase_ub"], Int)
        ) "The key 'monetary_budget_purchase_ub' in 'FinancialStatus' must be a float or int value. Error at $(fs["id"])."

        # checking for appropriate values of the monetary budgets and their limits

        if fs["monetary_budget_purchase"] < fs["monetary_budget_purchase_lb"]
            error(
                "The lower bound of the purchase monetary budget must be smaller than the purchase monetary budget.",
            )
        end

        if fs["monetary_budget_purchase"] > fs["monetary_budget_purchase_ub"]
            error(
                "The upper bound of the purchase monetary budget must be larger than the purchase monetary budget.",
            )
        end

        if fs["monetary_budget_purchase_lb"] > fs["monetary_budget_purchase_ub"]
            error(
                "The upper bound of the purchase monetary budget must be larger than the lower bound of the purchase monetary budget.",
            )
        end

        if fs["monetary_budget_purchase_lb"] == fs["monetary_budget_purchase_ub"]
            @warn "The lower and upper bounds of the purchase monetary budget are equal."
        end

    end
end

"""
    check_correct_format_Mode(data_structures::Dict, years)

Check if the format of the Mode entries is correct.

# Arguments
- `data_structures::Dict`: The input data.
- `years::Int`: The number of years in the optimization horizon.
"""
function check_correct_format_Mode(data_structures::Dict, years)
    for ij ∈ 1:length(data_structures["Mode"])
        m = data_structures["Mode"][ij]

        @assert isa(m["id"], Int) "The key 'id' in 'Mode' must be an integer value. Error at $(m["id"])."
        @assert isa(m["name"], String) "The key 'name' in 'Mode' must be a string value. Error at $(m["id"])."
        @assert isa(m["quantify_by_vehs"], Bool) "The key 'quantify_by_vehs' in 'Mode' must be a boolean value. Error at $(m["id"])."
        @assert (
            isa(m["costs_per_ukm"], Array{Float64,1}) ||
            isa(m["costs_per_ukm"], Array{Int,1})
        ) "The key 'costs_per_ukm' in 'Mode' must be an array with float or integer values. Error at $(m["id"])."
        @assert (
            isa(m["emission_factor"], Array{Float64,1}) ||
            isa(m["emission_factor"], Array{Int,1})
        ) "The key 'emission_factor' in 'Mode' must be an array with float or integer values. Error at $(m["id"])."
        @assert (
            isa(m["infrastructure_expansion_costs"], Array{Float64,1}) ||
            isa(m["infrastructure_expansion_costs"], Array{Int,1})
        ) "The key 'infrastructure_expansion_costs' in 'Mode' must be an array with float or integer values. Error at $(m["id"])."
        @assert (
            isa(m["infrastructure_om_costs"], Array{Float64,1}) ||
            isa(m["infrastructure_om_costs"], Array{Int,1})
        ) "The key 'infrastructure_om_costs' in 'Mode' must be an array with float or integer values. Error at $(m["id"])."
        @assert (
            isa(m["waiting_time"], Array{Float64,1}) ||
            isa(m["waiting_time"], Array{Int,1})
        ) "The key 'waiting_time' in 'Mode' must be an array with float or integer values. Error at $(m["id"])."

        # checking for correct lengths of the arrays 
        @assert length(m["costs_per_ukm"]) >= years "The key 'costs_per_ukm' in 'Mode' must have the same length as the years of the optimization horizon. Error at $(m["id"])."
        @assert length(m["emission_factor"]) >= years "The key 'emission_factor' in 'Mode' must have the same length as the years of the optimization horizon. Error at $(m["id"])."
        @assert length(m["infrastructure_expansion_costs"]) >= years "The key 'infrastructure_expansion_costs' in 'Mode' must have the same length as the years of the optimization horizon. Error at $(m["id"])."
        @assert length(m["infrastructure_om_costs"]) >= years "The key 'infrastructure_om_costs' in 'Mode' must have the same length as the years of the optimization horizon. Error at $(m["id"])."
        @assert length(m["waiting_time"]) >= years "The key 'waiting_time' in 'Mode' must have the same length as the years of the optimization horizon. Error at $(m["id"])."
    end
end

"""
    check_correct_format_Product(data_structures::Dict, years)

Check if the format of the Product entries is correct.

# Arguments
- `data_structures::Dict`: The input data.
"""
function check_correct_format_Product(data_structures::Dict)
    for ij ∈ 1:length(data_structures["Product"])
        p = data_structures["Product"][ij]

        @assert isa(p["id"], Int) "The key 'id' in 'Product' must be an integer value. Error at $(p["id"])."
        @assert isa(p["name"], String) "The key 'name' in 'Product' must be a string value. Error at $(p["id"])."
    end
end

"""
    check_correct_format_Path(data_structures::Dict)

Check if the format of the Path entries is correct.

# Arguments
- `data_structures::Dict`: The input data.
"""
function check_correct_format_Path(data_structures::Dict)
    for ij ∈ 1:length(data_structures["Path"])
        p = data_structures["Path"][ij]

        @assert isa(p["id"], Int) "The key 'id' in 'Path' must be an integer value. Error at $(p["id"])."
        @assert isa(p["name"], String) "The key 'name' in 'Path' must be a string value. Error at $(p["id"])."
        @assert (isa(p["length"], Float64) || isa(p["length"], Int)) "The key 'length' in 'Path' must be a float or integer value. Error at $(p["id"])."
        @assert isa(p["sequence"], Array{Int,1}) "The key 'sequence' in 'Path' must be an array of integer values. Error at $(p["id"])."
    end
end

"""
    check_correct_format_Fuel(data_structures::Dict, years)

Check if the format of the Fuel entries is correct.

# Arguments
- `data_structures::Dict`: The input data.
- `years::Int`: The number of years in the optimization horizon.

"""
function check_correct_format_Fuel(data_structures::Dict, years::Int)
    for ij ∈ 1:length(data_structures["Fuel"])
        f = data_structures["Fuel"][ij]

        @assert isa(f["id"], Int) "The key 'id' in 'Fuel' must be an integer value. Error at $(f["id"])."
        @assert isa(f["name"], String) "The key 'name' in 'Fuel' must be a string value. Error at $(f["id"])."
        @assert (
            isa(f["cost_per_kWh"], Array{Float64,1}) ||
            isa(f["cost_per_kWh"], Array{Int,1})
        ) "The key 'cost_per_kWh' in 'Fuel' must be an array with float or integer values. Error at $(f["id"])."
        @assert (
            isa(f["cost_per_kW"], Array{Float64,1}) || isa(f["cost_per_kW"], Array{Int,1})
        ) "The key 'cost_per_kW' in 'Fuel' must be an array with float or integer values. Error at $(f["id"])."
        @assert (
            isa(f["emission_factor"], Array{Float64,1}) ||
            isa(f["emission_factor"], Array{Int,1})
        ) "The key 'emission_factor' in 'Fuel' must be an array with float or integer values. Error at $(f["id"])."
        @assert (
            isa(f["fueling_infrastructure_om_costs"], Array{Float64,1}) ||
            isa(f["fueling_infrastructure_om_costs"], Array{Int,1})
        ) "The key 'fueling_infrastructure_om_costs' in 'Fuel' must be an array with float or integer values. Error at $(f["id"])."

        # checking for correct lengths of the arrays
        @assert length(f["cost_per_kWh"]) >= years "The key 'cost_per_kWh' in 'Fuel' must have the same length as the years of the optimization horizon. Error at $(f["id"])."
        @assert length(f["cost_per_kW"]) >= years "The key 'cost_per_kW' in 'Fuel' must have the same length as the years of the optimization horizon. Error at $(f["id"])."
        @assert length(f["emission_factor"]) >= years "The key 'emission_factor' in 'Fuel' must have the same length as the years of the optimization horizon. Error at $(f["id"])."
        @assert length(f["fueling_infrastructure_om_costs"]) >= years "The key 'fueling_infrastructure_om_costs' in 'Fuel' must have the same length as the years of the optimization horizon. Error at $(f["id"])."
    end
end

"""
    check_correct_format_Technology(data_structures::Dict, years)

Check if the format of the Technology entries is correct.

# Arguments
- `data_structures::Dict`: The input data.
"""
function check_correct_format_Technology(data_structures::Dict)
    for ij ∈ 1:length(data_structures["Technology"])
        t = data_structures["Technology"][ij]

        @assert isa(t["id"], Int) "The key 'id' in 'Technology' must be an integer value. Error at $(t["id"])."
        @assert isa(t["name"], String) "The key 'name' in 'Technology' must be a string value. Error at $(t["id"])."
        @assert isa(t["fuel"], String) "The key 'fuel' in 'Technology' must be a string value. Error at $(t["id"])."
    end
end

"""
    check_correct_format_VehicleType(data_structures::Dict)

Check if the format of the VehicleType entries is correct.

# Arguments
- `data_structures::Dict`: The input data.
"""

function check_correct_format_Vehicletype(data_structures::Dict)
    for ij ∈ 1:length(data_structures["Vehicletype"])
        vt = data_structures["Vehicletype"][ij]

        @assert isa(vt["id"], Int) "The key 'id' in 'VehicleType' must be an integer value. Error at $(vt["id"])."
        @assert isa(vt["name"], String) "The key 'name' in 'VehicleType' must be a string value. Error at $(vt["id"])."
        @assert isa(vt["mode"], Int) "The key 'mode' in 'VehicleType' must be an integer value. Error at $(vt["id"])."
        @assert isa(vt["product"], String) "The key 'product' in 'VehicleType' must be a string value. Error at $(vt["id"])."
    end
end
# TODO: check if an entry or reference to another is valid (maybe in other function) or in other 

"""
    check_correct_format_Regiontype(data_structures::Dict, years)

Check if the format of the Regiontype entries is correct.

# Arguments
- `data_structures::Dict`: The input data.
- `years::Int`: The number of years in the optimization horizon.
"""

function check_correct_format_Regiontype(data_structures::Dict, years::Int)
    for ij ∈ 1:length(data_structures["Regiontype"])
        rt = data_structures["Regiontype"][ij]

        @assert isa(rt["id"], Int) "The key 'id' in 'Regiontype' must be an integer value. Error at $(rt["id"])."
        @assert isa(rt["name"], String) "The key 'name' in 'Regiontype' must be a string value. Error at $(rt["id"])."
        @assert (
            isa(rt["costs_var"], Array{Float64,1}) || isa(rt["costs_var"], Array{Int,1})
        ) "The key 'costs_var' in 'Regiontype' must be an array with float or integer values. Error at $(rt["id"])."
        @assert (
            isa(rt["costs_fix"], Array{Float64,1}) || isa(rt["costs_fix"], Array{Int,1})
        ) "The key 'costs_fix' in 'Regiontype' must be an array with float or integer values. Error at $(rt["id"])."

        # check length of arrays
        @assert length(rt["costs_var"]) >= years "The key 'costs_var' in 'Regiontype' must have the same length as the years of the optimization horizon. Error at $(rt["id"])."
        @assert length(rt["costs_fix"]) >= years "The key 'costs_fix' in 'Regiontype' must have the same length as the years of the optimization horizon. Error at $(rt["id"])."
    end
end

"""
    check_correct_format_TechVehicle(data_structures::Dict, years)

Check if the format of the TechVehicle entries is correct.

# Arguments
- `data_structures::Dict`: The input data.
- `years::Int`: The number of years in the optimization horizon.
- `generations::Int`: The number of generations.

"""

function check_correct_format_TechVehicle(
    data_structures::Dict,
    years::Int,
    generations::Int,
)
    for ij ∈ 1:length(data_structures["TechVehicle"])
        tv = data_structures["TechVehicle"][ij]

        @assert isa(tv["id"], Int) "The key 'id' in 'TechVehicle' must be an integer value. Error at $(tv["id"])."
        @assert isa(tv["name"], String) "The key 'name' in 'TechVehicle' must be a string value. Error at $(tv["id"])."
        @assert isa(tv["vehicle_type"], String) "The key 'vehicle_type' in 'TechVehicle' must be a string value. Error at $(tv["id"])."
        @assert isa(tv["technology"], Int) "The key 'technology' in 'TechVehicle' must be a integer value. Error at $(tv["id"])."
        @assert isa(tv["capital_cost"], Array{Float64,1}) ||
                isa(tv["capital_cost"], Array{Int,1}) "The key 'capital_cost' in 'TechVehicle' must be an array with float or integer values. Error at $(tv["id"])."
        @assert (
            isa(tv["maintenance_cost_annual"], Array{Array{Float64,1},1}) ||
            isa(tv["maintenance_cost_annual"], Array{Array{Int,1},1})
        ) "The key 'maintenance_cost_annual' in 'TechVehicle' must be a two-dimensional array with float or integer values. Error at $(tv["id"])."
        @assert (
            isa(tv["maintenance_cost_distance"], Array{Array{Float64,1},1}) ||
            isa(tv["maintenance_cost_distance"], Array{Array{Int,1},1})
        ) "The key 'maintenance_cost_distance' in 'TechVehicle' must be a two-dimensional array with float or integer values. Error at $(tv["id"])."
        @assert (isa(tv["W"], Array{Float64,1}) || isa(tv["W"], Array{Int,1})) "The key 'W' in 'TechVehicle' must be an array with float or integer values. Error at $(tv["id"])."
        @assert (
            isa(tv["spec_cons"], Array{Float64,1}) || isa(tv["spec_cons"], Array{Int,1})
        ) "The key 'spec_cons' in 'TechVehicle' must be an array with float or integer values. Error at $(tv["id"])."
        @assert (isa(tv["Lifetime"], Array{Float64,1}) || isa(tv["Lifetime"], Array{Int,1})) "The key 'Lifetime' in 'TechVehicle' must be an array with float or integer values. Error at $(tv["id"])."
        @assert (
            isa(tv["AnnualRange"], Array{Float64,1}) ||
            isa(tv["AnnualRange"], Array{Int,1})
        ) "The key 'AnnualRange' in 'TechVehicle' must be an array with float or integer values. Error at $(tv["id"])."
        @assert isa(tv["products"], Array{String,1}) "The key 'products' in 'TechVehicle' must be an array of string values. Error at $(tv["id"])."
        @assert isa(tv["tank_capacity"], Array{Float64,1}) ||
                isa(tv["tank_capacity"], Array{Int,1}) "The key 'tank_capacity' in 'TechVehicle' must be an array with float or integer values. Error at $(tv["id"])."
        @assert isa(tv["peak_fueling"], Array{Float64,1}) ||
                isa(tv["peak_fueling"], Array{Int,1}) "The key 'peak_charging' in 'TechVehicle' must be an array with float or integer values. Error at $(tv["id"])."

        # check length of arrays
        @assert length(tv["capital_cost"]) >= generations "The key 'capital_cost' in 'TechVehicle' must have the same length as the years of the optimization horizon. Error at $(tv["id"])."
        @assert length(tv["maintenance_cost_annual"]) >= generations "The key 'maintenance_cost_annual' in 'TechVehicle' must have the same length as the years of the optimization horizon. Error at $(tv["id"])."
        @assert length(tv["maintenance_cost_distance"]) >= generations "The key 'maintenance_cost_distance' in 'TechVehicle' must have the same length as the years of the optimization horizon. Error at $(tv["id"])."
        for i ∈ 1:length(tv["maintenance_cost_distance"])
            @assert length(tv["maintenance_cost_distance"][i]) >= years "The key 'maintenance_cost_distance' in 'TechVehicle' must have the same length as the years of the optimization horizon. Error at $(tv["id"])."
        end
        for i ∈ 1:length(tv["maintenance_cost_annual"])
            @assert length(tv["maintenance_cost_annual"][i]) >= years "The key 'maintenance_cost_annual' in 'TechVehicle' must have the same length as the years of the optimization horizon. Error at $(tv["id"])."
        end

        @assert length(tv["W"]) >= generations "The key 'W' in 'TechVehicle' must have the same length as the years of the optimization horizon. Error at $(tv["id"])."
        @assert length(tv["spec_cons"]) >= generations "The key 'spec_cons' in 'TechVehicle' must have the same length as the years of the optimization horizon. Error at $(tv["id"])."
        @assert length(tv["Lifetime"]) >= generations "The key 'Lifetime' in 'TechVehicle' must have the same length as the years of the optimization horizon. Error at $(tv["id"])."
        @assert length(tv["AnnualRange"]) >= generations "The key 'AnnualRange' in 'TechVehicle' must have the same length as the years of the optimization horizon. Error at $(tv["id"])."
        @assert length(tv["tank_capacity"]) >= generations "The key 'battery_capacity' in 'TechVehicle' must have the same length as the years of the optimization horizon. Error at $(tv["id"])."
        @assert length(tv["peak_fueling"]) >= generations "The key 'peak_charging' in 'TechVehicle' must have the same length as the years of the optimization horizon. Error at $(tv["id"])."
    end
end

"""
    check_correct_format_InitialVehicleStock(data_structures::Dict, y_init::Int, g_init::Int)

Check if the format of the InitialVehicleStock entries is correct.

# Arguments
- `data_structures::Dict`: The input data.
- `y_init::Int`: The year of the first year of the optimization horizon.
- `g_init::Int`: The first generation.

"""

function check_correct_format_InitialVehicleStock(
    data_structures::Dict,
    y_init::Int,
    g_init::Int,
)
    for ij ∈ 1:length(data_structures["InitialVehicleStock"])
        ivs = data_structures["InitialVehicleStock"][ij]

        @assert isa(ivs["id"], Int) "The key 'id' in 'InitialVehicleStock' must be an integer value. Error at $(ivs["id"])."
        @assert isa(ivs["techvehicle"], Int) "The key 'techvehicle' in 'InitialVehicleStock' must be a integer value. Error at $(ivs["id"])."
        @assert isa(ivs["year_of_purchase"], Int) "The key 'year_of_purchase' in 'InitialVehicleStock' must be a integer value. Error at $(ivs["id"])."
        @assert isa(ivs["stock"], Int) || isa(ivs["stock"], Float64) "The key 'number' in 'InitialVehicleStock' must be a float or integer value. Error at $(ivs["id"])."
        if ivs["year_of_purchase"] < g_init
            error(
                "The year of purchase must not be earlier than the year of the first considered generation. Error at $(ivs["id"]).",
            )
        end

        if ivs["year_of_purchase"] >= y_init
            error(
                "The year of purchase must not be later than the year of the first considered year of the optimization horizon. Error at $(ivs["id"]).",
            )
        end
    end
end

"""
    check_correct_format_InitialFuelingInfra(data_structures::Dict)

Check if the format of the InitialFuelingInfr entries is correct.

# Arguments
- `data_structures::Dict`: The input data.
"""

function check_correct_format_InitialFuelingInfr(data_structures::Dict)
    for ij ∈ 1:length(data_structures["InitialFuelingInfr"])
        ifi = data_structures["InitialFuelingInfr"][ij]

        @assert isa(ifi["id"], Int) "The key 'id' in 'InitialFuelingInfr' must be an integer value. Error at $(ifi["id"])."
        @assert isa(ifi["fuel"], String) "The key 'fuel' in 'InitialFuelingInfr' must be a string value. Error at $(ifi["id"])."
        @assert isa(ifi["allocation"], Int) "The key 'regiontype' in 'InitialFuelingInfr' must be a integer value. Error at $(ifi["id"])."
        @assert isa(ifi["installed_kW"], Int) || isa(ifi["installed_kW"], Float64) "The key 'installed_kW' in 'InitialFuelingInfr' must be a float or integer value. Error at $(ifi["id"])."
    end
end

"""
    check_correct_format_InitialModeInfr(data_structures::Dict)

Check if the format of the InitialModeInfr entries is correct.

# Arguments
- `data_structures::Dict`: The input data.
"""
function check_correct_format_InitialModeInfr(data_structures::Dict)
    for ij ∈ 1:length(data_structures["InitialModeInfr"])
        imi = data_structures["InitialModeInfr"][ij]

        @assert isa(imi["id"], Int) "The key 'id' in 'InitialModeInfr' must be an integer value. Error at $(imi["id"])."
        @assert isa(imi["mode"], Int) "The key 'mode' in 'InitialModeInfr' must be a integer value. Error at $(imi["id"])."
        @assert isa(imi["allocation"], Int) "The key 'regiontype' in 'InitialModeInfr' must be a integer value. Error at $(imi["id"])."
        @assert isa(imi["installed_ukm"], Int) || isa(imi["installed_ukm"], Float64) "The key 'installed_kW' in 'InitialModeInfr' must be a float or integer value. Error at $(imi["id"])."
    end
end

"""
    check_correct_format_Odpair(data_structures::Dict)

Check if the format of the Odpair entries is correct.

# Arguments
- `data_structures::Dict`: The input data.
- `years::Int`: The number of years in the optimization horizon.
"""
function check_correct_format_Odpair(data_structures::Dict, years::Int)
    for ij ∈ 1:length(data_structures["Odpair"])
        od = data_structures["Odpair"][ij]

        @assert isa(od["id"], Int) "The key 'id' in 'Odpair' must be an integer value. Error at $(od["id"])."
        @assert isa(od["from"], Int) "The key 'origin' in 'Odpair' must be a integer value. Error at $(od["id"])."
        @assert isa(od["to"], Int) "The key 'destination' in 'Odpair' must be a integer value. Error at $(od["id"])."
        @assert isa(od["path_id"], Int) "The key 'path_id' in 'Odpair' must be a integer value. Error at $(od["id"])."
        @assert isa(od["F"], Array{Float64,1}) || isa(od["F"], Array{Int,1}) "The key 'F' in 'Odpair' must be an array with float or integer values. Error at $(od["id"])."
        @assert isa(od["product"], String) "The key 'product' in 'Odpair' must be a string value. Error at $(od["id"])."
        @assert isa(od["vehicle_stock_init"], Array{Float64,1}) ||
                isa(od["vehicle_stock_init"], Array{Int,1}) "The key 'vehicle_stock_init' in 'Odpair' must be an array of integer values. Error at $(od["id"])."
        @assert isa(od["financial_status"], String) "The key 'financial_status' in 'Odpair' must be a string value. Error at $(od["id"])."
        @assert isa(od["region_type"], String) "The key 'region_type' in 'Odpair' must be a integer value. Error at $(od["id"])."

        # check length of arrays
        @assert length(od["F"]) >= years "The key 'F' in 'Odpair' must have the same length as the years of the optimization horizon. Error at $(od["id"])."
    end
end

"""

    check_correct_format_Speed(data_structures::Dict)

Check if the format of the Speed entries is correct.

# Arguments
- `data_structures::Dict`: The input data.
"""
function check_correct_format_Speed(data_structures::Dict)
    for ij ∈ 1:length(data_structures["Speed"])
        s = data_structures["Speed"][ij]

        @assert isa(s["id"], Int) "The key 'id' in 'Speed' must be an integer value. Error at $(s["id"])."
        @assert isa(s["region_type"], String) "The key 'mode' in 'Speed' must be a string value. Error at $(s["id"])."
        @assert isa(s["vehicle_type"], String) "The key 'vehicle_type' in 'Speed' must be a string value. Error at $(s["id"])."
        @assert (isa(s["travel_speed"], Float64) || isa(s["travel_speed"], Int)) "The key 'speed' in 'Speed' must be a integer or float value. Error at $(s["id"])."
    end
end
