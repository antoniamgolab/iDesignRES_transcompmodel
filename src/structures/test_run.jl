println("Running the test program ...")
using JuMP, Gurobi

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
struct Path
    id::Int
    name::String
    length::Float64
    nodes::Array{Node, 1}
end

struct Odpair
    id::Int
    origin::Node
    destination::Node
    paths:: Array{Path, 1} # this needs to be adaoted later as for each odpair different paths exist depending also on the mode
    F::Float64
    product::Product
end

struct Fuel
    id::Int
    name::String
end
struct Technology
    id::Int
    name::String
    fuel::Fuel
end 

struct Vehicle
    id::Int
    name::String
    generation::Int
    mode::Mode
    technology:: Array{Technology, 1} 
    W::Float64
    capital_cost::Float64
end


ind(x) = x.id

technology(v::Vehicle) = v.technology
get_paths(o::Odpair) = o.paths

function id(x:: Array)
    return [el.id for el in x]
end

function get_paths(odpairs::Array{Odpair, 1})
    return [o.paths for o in odpairs] 
end
# now setting up some data
# ()
# case study A.1 
# these are the basic sets/dimensions that are included in the model 
nodes = [Node(1, "area1"), Node(2, "area2")]
product = [Product(1, "product1"), Product(2, "product2")]
paths = [Path(1, "path1",100, [nodes[1]]), Path(2, "path2",100, [nodes[2]])]  
odpairs = [Odpair(1, nodes[1], nodes[1], [paths[1]], 100.0, product[1]), Odpair(2, nodes[1], nodes[1], [paths[1]], 100.0, product[2]), Odpair(3, nodes[2], nodes[2], [paths[2]], 100.0, product[1]), Odpair(4, nodes[2], nodes[2], [paths[2]], 100.0, product[2])]
modes = [Mode(1, "mode1"), Mode(2, "mode2")]
technologies = [Technology(1, "tech1", Fuel(1, "fuel1")), Technology(2, "tech2", Fuel(2, "fuel2"))]
vehicles = [Vehicle(1, "vehicle1", 1, modes[1], technologies, 10.0, 10000), Vehicle(2, "vehicle2", 1, modes[2], technologies, 10.0, 15000)]   

# now defining the constraints

model = Model(Gurobi.Optimizer)

# creating variables 
# flow variable pkvt
@variable(model, f[[p.id for p in product], [k.id for k in paths], [v.id for v in vehicles], [t.id for t in technologies]] >= 0)
@variable(model, h[[r.id for r in odpairs], [v.id for v in vehicles], [t.id for t in technologies]] >= 0)
println(f)
@constraint(model, [r in odpairs], sum(f[r.product.id, k.id, v.id, t.id] for k in r.paths for v in vehicles for t in v.technology) == r.F) 
@constraint(model, [r in odpairs, v in vehicles, t in v.technology], h[r.id, v.id, t.id] >= sum((k.length/v.W) * f[r.product.id, k.id, v.id, t.id] for k in r.paths))
@objective(model, Min, sum(h[r.id, v.id, t.id] * v.capital_cost for r in odpairs for v in vehicles for t in v.technology))
println(f)
optimize!(model)
solution_summary(model)
println(value.(f))
println(value.(h))

