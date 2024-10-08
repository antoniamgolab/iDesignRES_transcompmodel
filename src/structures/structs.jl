struct Node
    id::Int
    name::String
end

struct Edge
    id::Int
    name::String
    length::Float64
    from::String 
    to::String
end

""" struct for `Mode` defining the modes of transport """

struct Mode
    id::Int 
    name:: String 
end

struct Product
    id::Int
    name::String
end

struct Path
    id::Int
    name::String
    length::Float64
    sequence
end

struct Fuel
    id::Int
    name::String
    cost_per_kWh   # € per kWh 
    cost_per_kW 
end

struct Technology
    id::Int
    name::String
    fuel::Fuel
end 

struct Vehicletype
    id::Int
    name::String
    mode::Mode
end

struct TechVehicle
    id::Int
    name::String
    vehicle_type::Vehicletype
    technology::Technology 
    capital_cost:: Array{Float64, 1}  # capital cost in €
    W::Array{Float64, 1}  # load capacity in t
    spec_cons::Array{Float64, 1}  # specific consumption in kWh/km  
    Lifetime:: Array{Int, 1} # Array if multiple generations are considered 
    AnnualRange::Array{Float64, 1} # annual range in km
    products::Array{Product, 1} # number of vehicles of this type
end

struct InitialVehicleStock
    id::Int
    techvehicle::TechVehicle 
    year_of_purchase::Int
    stock::Int
end

struct Odpair
    id::Int
    origin::Node
    destination::Node
    paths::Array{Path, 1} # this needs to be adaoted later as for each odpair different paths exist depending also on the mode
    F
    product::Product
    vehicle_stock_init::Array{InitialVehicleStock, 1}# initial vehicle stock
end

struct Generation
    id::Int
    year::Int
    y:: Int
end

