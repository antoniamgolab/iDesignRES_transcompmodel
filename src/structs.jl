"""
    Node

A 'Node' represents geographic region. 

# Fields
- `id::Int`: unique identifier of the node
- `name::String`: name the region
- `carbon_price::Array{Float64,1}`: carbon price in €/tCO2 for each year
"""
struct Node
    id::Int
    name::String
    carbon_price::Array{Float64,1}
end

"""
    Edge

An 'Edge' represents a connection between two nodes and is a representation of connecting transport infrastructure.

# Fields
- `id::Int`: unique identifier of the edge
- `name::String`: name of the connection
- `length::Float64`: length of the connection in km
- `from::Node`: the node from which the edge starts
- `to::Node`: the node to which the edge ends
- `carbon_price::Array{Float64,1}`: carbon price in €/tCO2 for each year
"""
struct Edge
    id::Int
    name::String
    length::Float64
    from::Node
    to::Node
    carbon_price::Array{Float64,1}
end

"""
    GeographicElement

A 'Graph_item' represents a graph item that is either a node or an edge.

# Fields
- `id::Int`: unique identifier of the graph item
- `type::String`: type of the graph item (either 'node' or 'edge')
- `name::String`: name of the graph item
- `carbon_price::Array{Float64,1}`: carbon price in €/tCO2 for each year
- `from::Node`: the node from which the edge starts
- `to::Node`: the node to which the edge ends
- `length::Float64`: length of the connection in km
"""
struct GeographicElement
    id::Int
    type::String
    name::String
    carbon_price::Array{Float64,1}
    from::Any
    to::Any
    length::Float64
end

"""
    Mode

A 'Mode' represents a transport mode. Transport modes may differ either by the infrastructure used (for example, road vs. rail) or by the used vehicle type (for example, private passenger car vs. bus) that directly influences the travel time but excludes a differentiation based on technology.

# Fields
- `id::Int`: unique identifier of the mode
- `name::String`: name of the mode
- `quantify_by_vehs::Bool`: if for this mode vehicles stock is sized or not. If this mode is considered with levelized costs, including the costs for vehicles and related costs.
- `cost_per_ukm::Array{Float64, 1}`: cost per km in €/km (only relevant when quantify_by_vehs is false) 
- `emission_factor::Array{Float64,1}`: emission factor of the mode in gCO2/ukm (only relevant when quantify_by_vehs is false)
- `infrastructure_expansion_costs::Array{Float64,1}`: infrastructure expansion costs in € (only relevant when quantify_by_vehs is false)
- `infrastructure_om_costs::Array{Float64,1}`: infrastructure operation and maintenance costs in €/year (only relevant when quantify_by_vehs is false)
- `waiting_time::Array{Float64,1}`: waiting time in h
"""
struct Mode
    id::Int
    name::String
    quantify_by_vehs::Bool
    cost_per_ukm::Array{Float64,1}
    emission_factor::Array{Float64,1} # gCO2/ukm
    infrastructure_expansion_costs::Array{Float64,1}
    infrastructure_om_costs::Array{Float64,1}
    waiting_time::Array{Float64,1} # waiting time in h
end

"""
    Product

A 'Product' represents either a good or a service that is being transported. This may include passengers, or different types of products in the freight transport.
The differentiation of transported products related to the different needs for transportation and, therefore, different possible sets of transport modes, vehicle types and drivetrain technologies are available for transport.

# Fields
- `id::Int`: unique identifier of the product
- `name::String`: name of the product
"""
struct Product
    id::Int
    name::String
end

"""
    Path

A 'Path' represents a possible route between two nodes. This sequence includes the nodes that are passed through and the length of the path.

# Fields
- `id::Int`: unique identifier of the path
- `name::String`: name of the path
- `length::Float64`: length of the path in km
- `sequence`: sequence of nodes and edges that are passed through

"""
struct Path
    id::Int
    name::String
    length::Float64
    sequence::Array{GeographicElement,1}
end

"""
    Fuel

A 'Fuel' represents the energy source used for the vehicle propulsion. 

# Fields
- `id::Int`: unique identifier of the fuel
- `name::String`: name of the fuel
- `emission_factor::Float64`: emission factor of the fuel in gCO2/kWh
- `cost_per_kWh`: cost per kWh of the fuel in €
- `cost_per_kW`: cost per kW of the fuel in €
- `fueling_infrastructure_om_costs::Array{Float64,1}`: fueling infrastructure operation and maintenance costs in €/year
"""
struct Fuel
    id::Int
    name::String
    emission_factor::Array{Float64,1}  # gCO2/kWh
    cost_per_kWh::Array{Float64,1}   # € per kWh 
    cost_per_kW::Array{Float64,1}
    fueling_infrastructure_om_costs::Array{Float64,1}
end

"""
    Technology

A 'Technology' represents the drivetrain technology used in the vehicle.

# Fields
- `id::Int`: unique identifier of the technology
- `name::String`: name of the technology
- `fuel::Fuel`: fuel used by the technology
"""
struct Technology
    id::Int
    name::String
    fuel::Fuel
end

"""
    Vehicletype

A 'Vehicletype' represents a type of vehicle that is used for transportation. This may be for example, small passenger cars, buses, or light-duty trucks.

# Fields
- `id::Int`: unique identifier of the vehicle type
- `name::String`: name of the vehicle type
- `mode::Mode`: mode of transport that the vehicle type is used for
- `product::Product`: product that the vehicle type is used for
"""
struct Vehicletype
    id::Int
    name::String
    mode::Mode
    products::Array{Product,1}
end

"""
    TechVehicle

A 'TechVehicle' represents a vehicle that is used for transportation. This includes the vehicle type, the technology used in the vehicle, the capital and maintenance costs, the load capacity, the specific consumption, the lifetime, the annual range, the number of vehicles of this type, the battery capacity, and the peak charging power.
"""
struct TechVehicle
    id::Int
    name::String
    vehicle_type::Vehicletype
    technology::Technology
    capital_cost::Array{Float64}  # capital cost in €
    maintenance_cost_annual::Array{Array{Float64, 1}, 1}
    maintenance_cost_distance::Array{Array{Float64, 1}, 1}
    W::Array{Float64}  # load capacity in t
    spec_cons::Array{Float64}  # specific consumption in kWh/km  
    Lifetime::Array{Int} # Array if multiple generations are considered 
    AnnualRange::Array{Float64} # annual range in km
    products::Array{Product} # number of vehicles of this type
    battery_capacity::Array{Float64} # battery capacity in kWh
    peak_charging::Array{Float64} # peak charging power in kW
end

"""
    InitialVehicleStock

An 'InitialVehicleStock' represents a vehicle fleet that exisits at the initial year of the optimization horizon.

# Fields
- `id::Int`: unique identifier of the initial vehicle stock
- `techvehicle::TechVehicle`: vehicle type and technology of the vehicle
- `year_of_purchase::Int`: year in which the vehicle was purchased
- `stock::Float64`: number of vehicles of this type in the initial vehicle stock

"""
struct InitialVehicleStock
    id::Int
    techvehicle::TechVehicle
    year_of_purchase::Int
    stock::Float64
end

"""
    InitialFuelingInfr

An 'InitialFuelingInfr' represents the fueling infrastructure that exists at the initial year of the optimization horizon.

# Fields
- `id::Int`: unique identifier of the initial fueling infrastructure
- `technology::Technology`: technology of the fueling infrastructure
- `allocation`: allocation of the fueling infrastructure
- `installed_kW::Float64`: installed capacity of the fueling infrastructure in kW
"""
struct InitialFuelingInfr
    id::Int
    fuel::Fuel
    allocation::Any
    installed_kW::Float64
end

"""
    InitialModeInfr

An 'InitialModeInfr' represents the mode infrastructure that exists at the initial year of the optimization horizon.

# Fields
- `id::Int`: unique identifier of the initial mode infrastructure
- `mode::Mode`: mode of transport
- `allocation`: allocation of the mode infrastructure
- `installed_ukm::Float64`: installed transport capacity of the mode infrastructure in Ukm

"""
struct InitialModeInfr
    id::Int
    mode::Mode
    allocation::Any
    installed_ukm::Float64
end

"""

    InitDetourTimes

An 'InitDetourTimes' represents the detour times that exist at the initial year of the optimization horizon. It is the average detour time to reach a fueling station.

# Fields
- `id::Int`: unique identifier of the initial detour times
- `fuel::Fuel`: fuel type of the fueling station
- `location::GeographicElement`: location of the fueling station
- `detour_time::Float64`: detour time in h
"""
struct InitDetourTime
    id::Int
    fuel::Fuel
    location::GeographicElement
    detour_time::Float64
end

"""

    DetourTimeReductions

A 'DetourTimeReductions' represents the detour time reductions that can be achieved by the expansion of the fueling infrastructure.

# Fields
- `id::Int`: unique identifier of the detour time reductions
- `fuel::Fuel`: fuel type of the fueling station
- `location::GeographicElement`: location of the fueling station
- `reduction_id::Int`: unique identifier of the detour time reduction
- `detour_time_reduction::Float64`: detour time reduction in h

"""

struct DetourTimeReduction
    id::Int
    fuel::Fuel
    location::GeographicElement
    reduction_id::Int    
    detour_time_reduction::Float64
    fueling_cap_lb::Float64
    fueling_cap_ub::Float64
end

"""

    FinancialStatus

A 'FinancialStatus' describes a demographic group based on what there average budget for transportation-related expenses is.

# Fields
- `id::Int`: unique identifier of the financial status
- `name::String`: name of the financial status
- `VoT`: value of time in €/h
- `monetary_budget_operational`: budget for operational costs in €/year
- `monetary_budget_operational_lb`: lower bound of the budget for operational costs in €/year
- `monetary_budget_operational_ub`: upper bound of the budget for operational costs in €/year
- `monetary_budget_purchase`: budget for purchasing costs in €/year
- `monetary_budget_purchase_lb`: lower bound of the budget for purchasing costs in €/year
- `monetary_budget_purchase_ub`: upper bound of the budget for purchasing costs in €/year
"""
struct FinancialStatus
    id::Int
    name::String
    VoT::Any
    monetary_budget_operational::Any
    monetary_budget_operational_lb::Any
    monetary_budget_operational_ub::Any
    monetary_budget_purchase::Any
    monetary_budget_purchase_lb::Any
    monetary_budget_purchase_ub::Any
    monetary_budget_purchase_time_horizon::Int
end

"""
    Regiontype

A 'Regiontype' describes a region based on its characteristics that induces differences in transportation needs (for example, urban vs. rural area).

# Fields
- `id::Int`: unique identifier of the regiontype
- `name::String`: name of the regiontype
- `speed::Float64`: average speed in km/h
- `costs_var::Array{Float64, 1}`: variable costs in €/vehicle-km
- `costs_fix::Array{Float64, 1}`: fixed costs in €/year

"""
struct Regiontype
    id::Int
    name::String
    costs_var::Array{Float64,1}
    costs_fix::Array{Float64,1}
end

"""
    Odpair

An 'Odpair' describes transport demand. It may take place between two regions but origin and destination may al so 

# Fields
- `id::Int`: unique identifier of the odpair
- `origin::Node`: origin of the transport demand
- `destination::Node`: destination of the transport demand
- `paths::Array{Path, 1}`: possible paths between origin and destination
- `F`: number of trips in p/year or t/year
"""
struct Odpair
    id::Int
    origin::GeographicElement
    destination::GeographicElement
    paths::Array{Path,1} # this needs to be adaoted later as for each odpair different paths exist depending also on the mode
    F::Any
    product::Product
    vehicle_stock_init::Array{InitialVehicleStock,1}# initial vehicle stock
    financial_status::FinancialStatus
    region_type::Regiontype
end

"""
    Speed 

Speed indicates the average travel speed that is given by a certain region and vehicle type.

# Fields
- `id::Int`: unique identifier of the speed
- `region_type::Regiontype`: region in which the speed is valid
- `vehicle_type::Vehicletype`: vehicle type for which the speed is valid
- `travel_speed::Float64`: travel speed in km/h
"""

struct Speed
    id::Int
    region_type::Regiontype
    vehicle_type::Vehicletype
    travel_speed::Float64
end

"""
    Market_shares

A 'Market_shares' describes the market share of a vehicle type with a specific drivetrain technology in a specific year.

# Fields
- `id::Int`: unique identifier of the market share
- `type::TechVehicle`: vehicle type and technology
- `share::Float64`: market share of the vehicle type (in %)
- `year::Int`: year of the expected market share
- `region_type::Array{Regiontype,1}`: array of region types that are affected by this TechVehicle share constraint
"""

struct Market_shares
    id::Int
    type::TechVehicle
    share::Float64
    year::Int
    region_type::Array{Regiontype,1}
end

"""
    Mode_shares

A 'Mode_shares' describes the mode share of a transport mode in a specific year.

# Fields
- `id::Int`: unique identifier of the mode share
- `mode::Mode`: mode of transport
- `share::Float64`: share of the mode
- `year::Int`: year of the mode share
- `region_type::Array{Regiontype,1}`: array of region types that are affected by this TechVehicle share constraint
"""

struct Mode_shares
    id::Int
    mode::Mode
    share::Float64
    year::Int
    region_type::Array{Regiontype,1}
end

"""
    Mode_share_max_by_year

Maximum mode shares of a transport mode in a specific year.

# Fields
- `id::Int`: unique identifier of the mode share
- `mode::Mode`: mode of transport
- `share::Float64`: maximum share of the mode
- `year::Int`: year of the maximum mode share
- `region_type::Array{Regiontype,1}`: array of region types that are affected by this TechVehicle share constraint
"""
struct Mode_share_max_by_year
    id::Int
    mode::Mode
    share::Float64
    year::Int
    region_type::Array{Regiontype,1}
end

"""
    Mode_share_min_by_year

Minimum mode shares of a transport mode in a specific year.

# Fields
- `id::Int`: unique identifier of the mode share
- `mode::Mode`: mode of transport
- `share::Float64`: minimum share of the mode
- `year::Int`: year of the minimum mode share
- `region_type::Array{Regiontype,1}`: array of region types that are affected by this TechVehicle share constraint
"""
struct Mode_share_min_by_year
    id::Int
    mode::Mode
    share::Float64
    year::Int
    financial_status::Array{FinancialStatus,1}
    region_type::Array{Regiontype,1}
end

"""
    Mode_share_max

Maximum mode shares of a transport mode independent of year, i.e. over total horizon.

# Fields
- `id::Int`: unique identifier of the mode share
- `mode::Mode`: mode of transport
- `share::Float64`: maximum share of the mode
- `financial_status::Array{FinancialStatus, 1}`: array of financial status that is affected by this mode share constraint
- `region_type::Array{Regiontype,1}`: array of region types that are affected by this TechVehicle share constraint
"""
struct Mode_share_max
    id::Int
    mode::Mode
    share::Float64
    financial_status::Array{FinancialStatus,1}
    region_type::Array{Regiontype,1}
end

"""
    Mode_share_min

Maximum mode shares of a transport mode independent of year, i.e. over total horizon.

# Fields
- `id::Int`: unique identifier of the mode share
- `mode::Mode`: mode of transport
- `share::Float64`: maximum share of the mode
- `financial_status::Array{FinancialStatus, 1}`: array of financial status that is affected by this mode share constraint
- `region_type::Array{Regiontype,1}`: array of region types that are affected by this TechVehicle share constraint
"""
struct Mode_share_min
    id::Int
    mode::Mode
    share::Float64
    financial_status::Array{FinancialStatus,1}
    region_type::Array{Regiontype,1}
end

"""
    Technology_share_max_by_year

Maximum technology shares of a vehicle technology in a specific year.

# Fields
- `id::Int`: unique identifier of the technology share
- `technology::Technology`: vehicle technology
- `share::Float64`: maximum share of the technology
- `year::Int`: year of the maximum technology share
- `financial_status::Array{FinancialStatus, 1}`: financial status that is affected by this technology share constraint
- `region_type::Array{Regiontype,1}`: array of region types that are affected by this TechVehicle share constraint
"""
struct Technology_share_max_by_year
    id::Int
    technology::Technology
    share::Float64
    year::Int
    financial_status::Array{FinancialStatus,1}
    region_type::Array{Regiontype,1}
end

"""
    Technology_share_min_by_year

Minimum technology shares of a vehicle technology in a specific year.

# Fields
- `id::Int`: unique identifier of the technology share
- `technology::Technology`: vehicle technology
- `share::Float64`: minimum share of the technology
- `year::Int`: year of the minimum technology share
- `financial_status::Array{FinancialStatus, 1}`: financial status that is affected by this technology share constraint
- `region_type::Array{Regiontype,1}`: array of region types that are affected by this TechVehicle share constraint
"""
struct Technology_share_min_by_year
    id::Int
    technology::Technology
    share::Float64
    year::Int
    financial_status::Array{FinancialStatus,1}
    region_type::Array{Regiontype,1}
end

"""
    Technology_share_max

Maximum technology shares of a vehicle technology independent of year, i.e. over total horizon.

# Fields
- `id::Int`: unique identifier of the technology share
- `technology::Technology`: vehicle technology
- `share::Float64`: maximum share of the technology
- `financial_status::Array{FinancialStatus, 1}`: array of financial status that is affected by this technology share constraint
- `region_type::Array{Regiontype,1}`: array of region types that are affected by this TechVehicle share constraint
"""
struct Technology_share_max
    id::Int
    technology::Technology
    share::Float64
    financial_status::Array{FinancialStatus,1}
    region_type::Array{Regiontype,1}
end

"""
    Technology_share_min

Minimum technology shares of a vehicle technology independent of year, i.e. over total horizon.

# Fields
- `id::Int`: unique identifier of the technology share
- `technology::Technology`: vehicle technology
- `share::Float64`: minimum share of the technology
- `financial_status::Array{FinancialStatus, 1}`: array of financial status that is affected by this technology share constraint
- `region_type::Array{Regiontype,1}`: array of region types that are affected by this TechVehicle share constraint
"""
struct Technology_share_min
    id::Int
    technology::Technology
    share::Float64
    financial_status::Array{FinancialStatus,1}
    region_type::Array{Regiontype,1}
end

"""
    VehicleType_share_max_by_year

Maximum vehicle type shares of a vehicle type in a specific year.

# Fields
- `id::Int`: unique identifier of the vehicle type share
- `vehicle_type::Vehicletype`: vehicle type
- `share::Float64`: maximum share of the vehicle type
- `year::Int`: year of the maximum vehicle type share
- `financial_status::Array{FinancialStatus, 1}`: financial status that is affected by this vehicle type share constraint
- `region_type::Array{Regiontype,1}`: array of region types that are affected by this TechVehicle share constraint
"""
struct VehicleType_share_max_by_year
    id::Int
    vehicle_type::Vehicletype
    share::Float64
    year::Int
    financial_status::Array{FinancialStatus,1}
    region_type::Array{Regiontype,1}
end

"""
    VehicleType_share_min_by_year

Minimum vehicle type shares of a vehicle type in a specific year.

# Fields
- `id::Int`: unique identifier of the vehicle type share
- `vehicle_type::Vehicletype`: vehicle type
- `share::Float64`: minimum share of the vehicle type
- `year::Int`: year of the minimum vehicle type share
- `financial_status::Array{FinancialStatus, 1}`: financial status that is affected by this vehicle type share constraint
- `region_type::Array{Regiontype,1}`: array of region types that are affected by this TechVehicle share constraint
"""
struct VehicleType_share_min_by_year
    id::Int
    vehicle_type::Vehicletype
    share::Float64
    year::Int
    financial_status::Array{FinancialStatus,1}
    region_type::Array{Regiontype,1}
end

"""
    VehicleType_share_max

Maximum vehicle type shares of a vehicle type independent of year, i.e. over total horizon.

# Fields
- `id::Int`: unique identifier of the vehicle type share
- `vehicle_type::Vehicletype`: vehicle type
- `share::Float64`: maximum share of the vehicle type
- `financial_status::Array{FinancialStatus, 1}`: array of financial status that is affected by this vehicle type share constraint
- `region_type::Array{Regiontype,1}`: array of region types that are affected by this TechVehicle share constraint
"""
struct VehicleType_share_max
    id::Int
    vehicle_type::Vehicletype
    share::Float64
    financial_status::Array{FinancialStatus,1}
    region_type::Array{Regiontype,1}
end

"""
    VehicleType_share_min

Minimum vehicle type shares of a vehicle type independent of year, i.e. over total horizon.

# Fields
- `id::Int`: unique identifier of the vehicle type share
- `vehicle_type::Vehicletype`: vehicle type
- `share::Float64`: minimum share of the vehicle type
- `financial_status::Array{FinancialStatus, 1}`: array of financial status that is affected by this vehicle type share constraint
- `region_type::Array{Regiontype,1}`: array of region types that are affected by this TechVehicle share constraint
"""
struct VehicleType_share_min
    id::Int
    vehicle_type::Vehicletype
    share::Float64
    financial_status::Array{FinancialStatus,1}
    region_type::Array{Regiontype,1}
end
"""
    TechVehicle_share_max_by_year

Maximum vehicle type shares of a TechVehicle in a specific year.

# Fields
- `id::Int`: unique identifier of the TechVehicle share
- `techvehicle::TechVehicle`: TechVehicle
- `share::Float64`: maximum share of the TechVehicle
- `year::Int`: year of the maximum TechVehicle share
- `financial_status::Array{FinancialStatus, 1}`: financial status that is affected by this TechVehicle share constraint
- `region_type::Array{Regiontype,1}`: array of region types that are affected by this TechVehicle share constraint
"""
struct TechVehicle_share_max_by_year
    id::Int
    techvehicle::TechVehicle
    share::Float64
    year::Int
    financial_status::Array{FinancialStatus,1}
    region_type::Array{Regiontype,1}
end

"""
    TechVehicle_share_min_by_year

Minimum vehicle type shares of a TechVehicle in a specific year.

# Fields
- `id::Int`: unique identifier of the TechVehicle share
- `techvehicle::TechVehicle`: TechVehicle
- `share::Float64`: minimum share of the TechVehicle
- `year::Int`: year of the minimum TechVehicle share
- `financial_status::Array{FinancialStatus, 1}`: financial status that is affected by this TechVehicle share constraint
- `region_type::Array{Regiontype,1}`: array of region types that are affected by this TechVehicle share constraint
"""
struct TechVehicle_share_min_by_year
    id::Int
    techvehicle::TechVehicle
    share::Float64
    year::Int
    financial_status::Array{FinancialStatus,1}
    region_type::Array{Regiontype,1}
end

"""
    TechVehicle_share_max

Maximum vehicle type shares of a TechVehicle independent of year, i.e. over total horizon.

# Fields
- `id::Int`: unique identifier of the TechVehicle share
- `techvehicle::TechVehicle`: TechVehicle
- `share::Float64`: maximum share of the TechVehicle
- `financial_status::Array{FinancialStatus, 1}`: array of financial status that is affected by this TechVehicle share constraint
- `region_type::Array{Regiontype,1}`: array of region types that are affected by this TechVehicle share constraint
"""
struct TechVehicle_share_max
    id::Int
    techvehicle::TechVehicle
    share::Float64
    financial_status::Array{FinancialStatus,1}
    region_type::Array{Regiontype,1}
end

"""
    TechVehicle_share_min

Minimum vehicle type shares of a TechVehicle independent of year, i.e. over total horizon.

# Fields
- `id::Int`: unique identifier of the TechVehicle share
- `techvehicle::TechVehicle`: TechVehicle
- `share::Float64`: minimum share of the TechVehicle
- `financial_status::Array{FinancialStatus, 1}`: array of financial status that is affected by this TechVehicle share constraint
- `region_type::Array{Regiontype,1}`: array of region types that are affected by this TechVehicle share constraint
"""
struct TechVehicle_share_min
    id::Int
    techvehicle::TechVehicle
    share::Float64
    financial_status::Array{FinancialStatus,1}
    region_type::Array{Regiontype,1}
end

"""
    Emission_constraints_by_mode

An 'Emission_constraints_by_mode' describes emissions constrained for a mode.

# Fields
- `id::Int`: unique identifier of the emission constraint
- `mode::Mode`: mode of transport
- `emission::Float64`: emission constraint of the vehicle type (tCO2/year)
- `year::Int`: year of the expected emission constraint
"""
struct Emission_constraints_by_mode
    id::Int
    mode::Mode
    emission::Float64
    year::Int
end

"""
    Emission_constraints_by_year

An 'Emission_constraints_by_year' describes an emission goal for a specific year for the total emissions.

# Fields
- `id::Int`: unique identifier of the emission constraint
- `emission::Float64`: emission constraint
- `year::Int`: year of the expected emission constraint
"""
struct Emission_constraints_by_year
    id::Int
    emission::Float64
    year::Int
end

"""
    Transportation_speeds

A 'Speed' describes the speed of a vehicle type in a specific year.

# Fields


"""
struct Transportation_speeds
    id::Int
    definition_mode_based::Bool
    mode::Mode
    vehicle_type::Vehicletype
    travel_speed::Float64
    year::Int
end

"""
    VehicleSubsidy

A 'VehicleSubsidy' describes the subsidy for a vehicle type in a specific year.

# Fields
- `id::Int`: unique identifier of the subsidy
- `name::String`: name of the subsidy
- `years::Array{Int,1}`: years in which the subsidy is valid
- `techvehicle::TechVehicle`: vehicle type and technology
- `subsidy::Float64`: subsidy in €
"""
struct VehicleSubsidy
    id::Int
    name::String
    years::Array{Int,1}
    techvehicle::TechVehicle
    subsidy::Float64
end

global model_parameters = [
    "Y",
    "y_init",
    "pre_y",
    "budget_constraint_penalty_plus",
    "budget_constraint_penalty_minus",
]

global parameters_extended = ["alpha_f", "beta_f", "alpha_h", "beta_h", "gamma"]

global struct_names_base = [
    "Model",
    "Mode",
    "Product",
    "Path",
    "Fuel",
    "Technology",
    "Vehicletype",
    "TechVehicle",
    "InitialVehicleStock",
    "FinancialStatus",
    "Regiontype",
    "Odpair",
    "Speed",
    "InitialFuelingInfr",
    "InitialModeInfr",
]

global struct_names_extended = [
    "F_init_mode_share",
    "Market_shares",
    "Mode_shares",
    "Mode_share_max_by_year",
    "Mode_share_min_by_year",
    "Mode_share_max",
    "Mode_share_min",
    "Technology_share_max_by_year",
    "Technology_share_min_by_year",
    "Technology_share_max",
    "Technology_share_min",
    "VehicleType_share_max_by_year",
    "VehicleType_share_min_by_year",
    "VehicleType_share_max",
    "VehicleType_share_min",
    "TechVehicle_share_max_by_year",
    "TechVehicle_share_min_by_year",
    "TechVehicle_share_max",
    "TechVehicle_share_min",
    "Emission_constraints_by_mode",
    "Emission_constraints_by_year",
    "Transportation_speeds",
    "VehicleSubsidy",
    "InitDetourTime",
    "DetourReductionFactor",
]

global default_data =
    Dict("alpha_f" => 0.1, "beta_f" => 0.1, "alpha_h" => 0.1, "beta_h" => 0.1)
