""" definition of all structs definining the dimensions of the model """


""" struct for `Node` defining the subregions of the considered region """

struct Node
    id::Int
    name::String
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


struct Odpair
    id::Int
    origin::Node
    destination::Node
    paths:: Array{Path, 1} # this needs to be adaoted later as for each odpair different paths exist depending also on the mode
    F::Float64
    F_init::Float64
end

struct Vehicle
    id::Int
    name::String
    generation::Int
    mode::Mode
    technology:: Technology 
    W::Float64
end

struct Technology
    id::Int
    name::String
    fuel::Fuel
end 

struct Fuel
    id::Int
    name::String
end

struct Path
    id::Int
    name::String
    length::Float64
    nodes::Array{Node, 1}
    edges::Array{Edge, 1}
end
