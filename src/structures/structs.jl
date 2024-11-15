"""
    Node

A 'Node' represents geographic region. 

# Fields
- `id::Int`: unique identifier of the node
- `name::String`: name the region

"""
struct Node
    id::Int
    name::String
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
"""
struct Edge
    id::Int
    name::String
    length::Float64
    from::Node 
    to::Node
end

"""
    Mode

A 'Mode' represents a transport mode. Transport modes may differ either by the infrastructure used (for example, road vs. rail) or by the used vehicle type (for example, private passenger car vs. bus) that directly influences the travel time but excludes a differentiation based on technology.

# Fields
- `id::Int`: unique identifier of the mode
- `name::String`: name of the mode
- `quantify_by_vehs::Bool`: if for this mode vehicles stock is sized or not. If this mode is considered with levelized costs, including the costs for vehicles and related costs.
- `cost_per_ukm::Array{Float64, 1}`: cost per km in €/km (only relevant when quantify_by_vehs is false) 
- `emission_factor::Float64`: emission factor of the mode in gCO2/ukm (only relevant when quantify_by_vehs is false)
"""
struct Mode
    id::Int 
    name::String
    quantify_by_vehs::Bool
    cost_per_ukm::Array{Float64, 1}
    emission_factor::Float64 # gCO2/ukm
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
    sequence
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
"""
struct Fuel
    id::Int
    name::String
    emission_factor::Float64
    cost_per_kWh   # € per kWh 
    cost_per_kW 

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
- `size_order::Int`: order of the vehicle type in terms of size
- `product::Product`: product that the vehicle type is used for
"""
struct Vehicletype
    id::Int
    name::String
    mode::Mode
    size_order::Int
    product::Product
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
    capital_cost:: Array{Float64, 1}  # capital cost in €
    maintnanace_cost_annual
    maintnance_cost_distance 
    W::Array{Float64, 1}  # load capacity in t
    spec_cons::Array{Float64, 1}  # specific consumption in kWh/km  
    Lifetime:: Array{Int, 1} # Array if multiple generations are considered 
    AnnualRange::Array{Float64, 1} # annual range in km
    products::Array{Product, 1} # number of vehicles of this type
    battery_capacity::Array{Float64, 1} # battery capacity in kWh
    peak_charging::Array{Float64, 1} # peak charging power in kW
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
    FinancialStatus

A 'FinancialStatus' describes a demographic group based on what there average budget for transportation-related expenses is.

# Fields
- `id::Int`: unique identifier of the financial status
- `name::String`: name of the financial status
- `weight::Float64`: weight of the financial status
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
    weight::Float64
    VoT
    monetary_budget_operational
    monetary_budget_operational_lb
    monetary_budget_operational_ub
    monetary_budget_purchase
    monetary_budget_purchase_lb
    monetary_budget_purchase_ub
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
    origin::Node
    destination::Node
    paths::Array{Path, 1} # this needs to be adaoted later as for each odpair different paths exist depending also on the mode
    F
    product::Product
    vehicle_stock_init::Array{InitialVehicleStock, 1}# initial vehicle stock
    financial_status::FinancialStatus
    urban::Bool
end

"""
    Generation

A 'Generation' referes to model year of a vehicle type to include the variation in vehicle performance parameters depending on when a vehicle was produced.

# Fields
- `id::Int`: unique identifier of the generation
- `year::Int`: year of the generation
- `y::Int`: year of the generation relative to the initial year of the optimization horizon
"""
struct Generation
    id::Int
    year::Int
    y:: Int
end

"""
    Regiontype

A 'Regiontype' describes a region based on its characteristics that induces differences in transportation needs (for example, urban vs. rural area).

# Fields
- `id::Int`: unique identifier of the regiontype
- `name::String`: name of the regiontype
- `weight`: weight of the regiontype
- `speed`: average speed in km/h
- `costs_var::Array{Float64, 1}`: variable costs in €/vehicle-km
- `costs_fix::Array{Float64, 1}`: fixed costs in €/year

"""
struct Regiontype
    id::Int
    name::String
    weight
    speed
    costs_var::Array{Float64, 1}
    costs_fix::Array{Float64, 1} 
end

"""
    F_init_mode_share

A 'F_init_mode_share' describes the initial mode share of a transport mode and is an attribute of a travel connection.

# Fields
- `id::Int`: unique identifier of the initial mode share
- `mode::Mode`: mode of transport
- `share::Float64`: share of the mode in the initial mode share
- `f_init::Float64`: initial number of trips in p/year or t/year
"""
struct F_init_mode_share
    id::Int
    mode::Mode
    share::Float64
    f_init::Float64
end

"""
    Market_shares

A 'Market_shares' describes the market share of a vehicle type with a specific drivetrain technology in a specific year.

# Fields
- `id::Int`: unique identifier of the market share
- `type::TechVehicle`: vehicle type and technology
- `share::Float64`: market share of the vehicle type
- `year::Int`: year of the expected market share
"""

struct Market_shares
    id::Int
    type::TechVehicle
    share::Float64
    year::Int
end

"""
    Mode_shares

A 'Mode_shares' describes the mode share of a transport mode in a specific year.

# Fields
- `id::Int`: unique identifier of the mode share
- `mode::Mode`: mode of transport
- `share::Float64`: share of the mode
- `year::Int`: year of the mode share

"""

struct Mode_shares
    id::Int
    mode::Mode
    share::Float64
    year::Int
    financial_status::Array{FinancialStatus, 1}
end

"""
    Mode_share_max_by_year

Maximum mode shares of a transport mode in a specific year.

# Fields
- `id::Int`: unique identifier of the mode share
- `mode::Mode`: mode of transport
- `share::Float64`: maximum share of the mode
- `year::Int`: year of the maximum mode share
- `financial_status::Array{FinancialStatus, 1}`: financial status that is affected by this mode share constraint

"""
struct Mode_share_max_by_year
    id::Int
    mode::Mode
    share::Float64
    year::Int
    financial_status::Array{FinancialStatus, 1}
end

"""
    Mode_share_min_by_year

Minimum mode shares of a transport mode in a specific year.

# Fields
- `id::Int`: unique identifier of the mode share
- `mode::Mode`: mode of transport
- `share::Float64`: minimum share of the mode
- `year::Int`: year of the minimum mode share
- `financial_status::Array{FinancialStatus, 1}`: financial status that is affected by this mode share constraint
"""
struct Mode_share_min_by_year
    id::Int
    mode::Mode
    share::Float64
    year::Int
    financial_status::Array{FinancialStatus, 1}
end

"""
    Mode_share_max

Maximum mode shares of a transport mode independent of year, i.e. over total horizon.

# Fields
- `id::Int`: unique identifier of the mode share
- `mode::Mode`: mode of transport
- `share::Float64`: maximum share of the mode
- `financial_status::Array{FinancialStatus, 1}`: array of financial status that is affected by this mode share constraint
"""
struct Mode_share_max
    id::Int
    mode::Mode
    share::Float64
    financial_status::Array{FinancialStatus, 1}
end

"""
    Mode_share_min

Maximum mode shares of a transport mode independent of year, i.e. over total horizon.

# Fields
- `id::Int`: unique identifier of the mode share
- `mode::Mode`: mode of transport
- `share::Float64`: maximum share of the mode
- `financial_status::Array{FinancialStatus, 1}`: array of financial status that is affected by this mode share constraint
"""
struct Mode_share_min
    id::Int
    mode::Mode
    share::Float64
    financial_status::Array{FinancialStatus, 1}
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
"""
struct Technology_share_max_by_year
    id::Int
    technology::Technology
    share::Float64
    year::Int
    financial_status::Array{FinancialStatus, 1}
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
"""
struct Technology_share_min_by_year
    id::Int
    technology::Technology
    share::Float64
    year::Int
    financial_status::Array{FinancialStatus, 1}
end

"""
    Technology_share_max

Maximum technology shares of a vehicle technology independent of year, i.e. over total horizon.

# Fields
- `id::Int`: unique identifier of the technology share
- `technology::Technology`: vehicle technology
- `share::Float64`: maximum share of the technology
- `financial_status::Array{FinancialStatus, 1}`: array of financial status that is affected by this technology share constraint
"""
struct Technology_share_max
    id::Int
    technology::Technology
    share::Float64
    financial_status::Array{FinancialStatus, 1}
end

"""
    Technology_share_min

Minimum technology shares of a vehicle technology independent of year, i.e. over total horizon.

# Fields
- `id::Int`: unique identifier of the technology share
- `technology::Technology`: vehicle technology
- `share::Float64`: minimum share of the technology
- `financial_status::Array{FinancialStatus, 1}`: array of financial status that is affected by this technology share constraint
"""
struct Technology_share_min
    id::Int
    technology::Technology
    share::Float64
    financial_status::Array{FinancialStatus, 1}
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
"""
struct VehicleType_share_max_by_year
    id::Int
    vehicle_type::Vehicletype
    share::Float64
    year::Int
    financial_status::Array{FinancialStatus, 1}
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
"""
struct VehicleType_share_min_by_year
    id::Int
    vehicle_type::Vehicletype
    share::Float64
    year::Int
    financial_status::Array{FinancialStatus, 1}
end

"""
    VehicleType_share_max

Maximum vehicle type shares of a vehicle type independent of year, i.e. over total horizon.

# Fields
- `id::Int`: unique identifier of the vehicle type share
- `vehicle_type::Vehicletype`: vehicle type
- `share::Float64`: maximum share of the vehicle type
- `financial_status::Array{FinancialStatus, 1}`: array of financial status that is affected by this vehicle type share constraint
"""
struct VehicleType_share_max
    id::Int
    vehicle_type::Vehicletype
    share::Float64
    financial_status::Array{FinancialStatus, 1}
end

"""
    VehicleType_share_min

Minimum vehicle type shares of a vehicle type independent of year, i.e. over total horizon.

# Fields
- `id::Int`: unique identifier of the vehicle type share
- `vehicle_type::Vehicletype`: vehicle type
- `share::Float64`: minimum share of the vehicle type
- `financial_status::Array{FinancialStatus, 1}`: array of financial status that is affected by this vehicle type share constraint
"""
struct VehicleType_share_min
    id::Int
    vehicle_type::Vehicletype
    share::Float64
    financial_status::Array{FinancialStatus, 1}
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
"""
struct TechVehicle_share_max_by_year
    id::Int
    techvehicle::TechVehicle
    share::Float64
    year::Int
    financial_status::Array{FinancialStatus, 1}
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
"""
struct TechVehicle_share_min_by_year
    id::Int
    techvehicle::TechVehicle
    share::Float64
    year::Int
    financial_status::Array{FinancialStatus, 1}
end

"""
    TechVehicle_share_max

Maximum vehicle type shares of a TechVehicle independent of year, i.e. over total horizon.

# Fields
- `id::Int`: unique identifier of the TechVehicle share
- `techvehicle::TechVehicle`: TechVehicle
- `share::Float64`: maximum share of the TechVehicle
- `financial_status::Array{FinancialStatus, 1}`: array of financial status that is affected by this TechVehicle share constraint
"""
struct TechVehicle_share_max
    id::Int
    techvehicle::TechVehicle
    share::Float64
    financial_status::Array{FinancialStatus, 1}
end

"""
    TechVehicle_share_min

Minimum vehicle type shares of a TechVehicle independent of year, i.e. over total horizon.

# Fields
- `id::Int`: unique identifier of the TechVehicle share
- `techvehicle::TechVehicle`: TechVehicle
- `share::Float64`: minimum share of the TechVehicle
- `financial_status::Array{FinancialStatus, 1}`: array of financial status that is affected by this TechVehicle share constraint
"""
struct TechVehicle_share_min
    id::Int
    techvehicle::TechVehicle
    share::Float64
    financial_status::Array{FinancialStatus, 1}
end

"""
    Emission_constraints_by_mode

An 'Emission_constraints_by_mode' describes emissions constrained for a mode.

# Fields
- `id::Int`: unique identifier of the emission constraint
- `mode::Mode`: mode of transport
- `emission::Float64`: emission constraint of the vehicle type
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
