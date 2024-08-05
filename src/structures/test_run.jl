println("Running the test program ...")
using JuMP, Gurobi

# case = "A.1"
# case = "A.2"
case = "B"

""" definition of all structs definining the dimensions of the model """


""" struct for `Node` defining the subregions of the considered region """

if case in ["A.1", "A.2"]
    Y = 2   # number of years
elseif case in ["B"]
    Y = 10
    G = 10 
end

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
    paths::Array{Path, 1} # this needs to be adaoted later as for each odpair different paths exist depending also on the mode
    F
    product::Product
end


struct Fuel
    id::Int
    name::String
    cost_per_kWh::Float64   # € per kWh 
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
    W::Float64  # load capacity in t
    spec_cons::Float64  # specific consumption in kWh/km
    capital_cost::Int  
    Lifetime:: Array{Int, 1} # Array if multiple generations are considered
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

if case=="A.1"
    odpairs = [Odpair(1, nodes[1], nodes[1], [paths[1]], 100.0, product[1]), Odpair(2, nodes[1], nodes[1], [paths[1]], 100.0, product[2]), OdpairA1(3, nodes[2], nodes[2], [paths[2]], 100.0, product[1]), OdpairA1(4, nodes[2], nodes[2], [paths[2]], 100.0, product[2])]
elseif case=="A.2"
    odpairs = [Odpair(1, nodes[1], nodes[1], [paths[1]], [100.0, 100.0], product[1]), Odpair(2, nodes[1], nodes[1], [paths[1]], [100.0, 100.0], product[2]), Odpair(3, nodes[2], nodes[2], [paths[2]], [100.0, 100.0], product[1]), Odpair(4, nodes[2], nodes[2], [paths[2]], [100.0, 100.0], product[2])]
    println("F: ",odpairs[1].F[2])
elseif case=="B"
    odpairs = [Odpair(1, nodes[1], nodes[1], [paths[1]], fill(100, G), product[1]), Odpair(2, nodes[1], nodes[1], [paths[1]], fill(100, G), product[2]), Odpair(3, nodes[2], nodes[2], [paths[2]], fill(100, G), product[1]), Odpair(4, nodes[2], nodes[2], [paths[2]], fill(100, G), product[2])]
end

modes = [Mode(1, "mode1"), Mode(2, "mode2")]
technologies = [Technology(1, "tech1", Fuel(1, "fuel1", 20/100)), Technology(2, "tech2", Fuel(2, "fuel2", 30/100))]

if case=="A.1" # in this case - as we only consider the time horizon of 2 years - we assume a vehicle age of 1 year, so that we can observe a replacement in this time span for this simple(!) case
    vehicles = [Vehicle(1, "vehicle1", 1, modes[1], technologies, 10.0, 1, 10000, [1]), Vehicle(2, "vehicle2", 1, modes[2], technologies, 10.0, 1, 15000, [1])]   
elseif case=="A.2"
    vehicles = [Vehicle(1, "vehicle1", 1, modes[1], technologies, 10.0, 1, 10000, [1,1]), Vehicle(2, "vehicle2", 1, modes[2], technologies, 10.0, 1, 15000, [1, 1])]   
elseif case=="B"
    vehicles = [Vehicle(1, "vehicle1", 1, modes[1], technologies, 10.0, 1, 10000, fill(2, G)), Vehicle(2, "vehicle2", 1, modes[2], technologies, 10.0, 1, 15000, fill(2, G))]   
end

print("thats the lifetime of the vehs", vehicles[1].Lifetime)
# now defining the constraints

model = Model(Gurobi.Optimizer)

# creating variables 
# flow variable pkvt

if in("a", ["A.1", "A.2"])
    println("a is in A")
end 
if case=="A.1"
    @variable(model, f[[p.id for p in product], [k.id for k in paths], [v.id for v in vehicles], [t.id for t in technologies]] >= 0)
    @variable(model, h[[r.id for r in odpairs], [v.id for v in vehicles], [t.id for t in technologies]] >= 0)
elseif case=="A.2"
    @variable(model, f[[y for y in 1:Y], [p.id for p in product], [k.id for k in paths], [v.id for v in vehicles], [t.id for t in technologies]] >= 0)
    @variable(model, h[[y for y in 1:Y], [r.id for r in odpairs], [v.id for v in vehicles], [t.id for t in technologies]] >= 0)
elseif case=="B"
    @variable(model, f[[y for y in 1:Y], [p.id for p in product], [k.id for k in paths], [v.id for v in vehicles], [t.id for t in technologies], [g for g in 1:G]] >= 0)
    @variable(model, h[[y for y in 1:Y], [r.id for r in odpairs], [v.id for v in vehicles], [t.id for t in technologies], [g for g in 1:G]] >= 0)
    @variable(model, h_exist[[y for y in 1:Y], [r.id for r in odpairs], [v.id for v in vehicles], [t.id for t in technologies], [g for g in 1:G]] >= 0)
    @variable(model, h_plus[[y for y in 1:Y], [r.id for r in odpairs], [v.id for v in vehicles], [t.id for t in technologies]] >= 0)
    @variable(model, h_minus[[y for y in 1:Y], [r.id for r in odpairs], [v.id for v in vehicles], [t.id for t in technologies], [g for g in 1:G]] >= 0)
end
print()

if case=="A.1"
    @constraint(model, [r in odpairs], sum(f[y, r.product.id, k.id, v.id, t.id] for k in r.paths for v in vehicles for t in v.technology) == r.F) 
    @constraint(model, [r in odpairs, v in vehicles, t in v.technology], h[r.id, v.id, t.id] >= sum((k.length/v.W) * f[r.product.id, k.id, v.id, t.id] for k in r.paths))
   
elseif case=="A.2"
    @constraint(model, [y in 1:Y, r in odpairs], sum(f[y, r.product.id, k.id, v.id, t.id] for k in r.paths for v in vehicles for t in v.technology) == r.F[y]) 
    @constraint(model, [y in 1:Y, r in odpairs, v in vehicles, t in v.technology], h[y, r.id, v.id, t.id] >= sum((k.length/v.W) * f[y, r.product.id, k.id, v.id, t.id] for k in r.paths))
elseif case=="B"
    @constraint(model, [y in 1:Y, r in odpairs], sum(f[y, r.product.id, k.id, v.id, t.id, g] for k in r.paths for v in vehicles for t in v.technology for g in 1:G) == r.F[y]) 
    @constraint(model, [y in 1:Y, r in odpairs, v in vehicles, t in v.technology, g in 1:G], h[y, r.id, v.id, t.id, g] >= sum((k.length/v.W) * f[y, r.product.id, k.id, v.id, t.id, g] for k in r.paths))
    # vehicle stock aging
    for r in odpairs
        for v in vehicles
            for t in v.technology
                for y in 1:Y
                    for g in 1:G
                        if y >= g
                            @constraint(model, h[y, r.id, v.id, t.id, g] == h_exist[y, r.id, v.id, t.id, g] + h_plus[y, r.id, v.id, t.id] - h_minus[y, r.id, v.id, t.id, g])
                            if y == 1
                                @constraint(model, h_exist[y, r.id, v.id, t.id, g] == 0)
                            else
                                @constraint(model, h_exist[y, r.id, v.id, t.id, g] == h[y-1, r.id, v.id, t.id, g])
                            end
                            if y > v.Lifetime[g]    # vehicles are replaced after their lifetime
                                # println("vehicle replaced because of old age ", y, " ", y-v.Lifetime[y])
                                @constraint(model, h_minus[y, r.id, v.id, t.id, y-v.Lifetime[y]] == h[y, r.id, v.id, t.id, y-v.Lifetime[y]])
                            end 
                        elseif y < g    # there can be no vehicles at year y that are of generation g = y - 1
                            @constraint(model, h[y, r.id, v.id, t.id, g] == 0)
                            @constraint(model, h_exist[y, r.id, v.id, t.id, g] == 0)
                        end 
                        # if g == y   # vehicles are added to the stock at year y -> are automatially of generation g (==y)
                        #     @constraint(model, h[y, r.id, v.id, t.id, g] == h_plus[y, r.id, v.id, t.id] - h_minus[y, r.id, v.id, t.id])
                        #     if y > v.Lifetime[g]    # vehicles are replaced after their lifetime
                        #         @constraint(model, h_minus[y, r.id, v.id, t.id] == h[y, r.id, v.id, t.id, y-v.Lifetime[y]])
                        #     end 
                        # elseif y > g    # vehicles are aging year by year, but are still same generation
                        #     @constraint(model, h[y, r.id, v.id, t.id, g] == h[y-1, r.id, v.id, t.id, g] - h_minus[y, r.id, v.id, t.id])    # vehicles are aging 
                        #     if y > v.Lifetime[g]    # vehicles are replaced after their lifetime
                        #         @constraint(model, h_minus[y, r.id, v.id, t.id] == h[y, r.id, v.id, t.id, y-v.Lifetime[y]])
                        #     end
                        # elseif y < g    # there can be no vehicles at year y that are of generation g = y - 1
                        # end
                        # if y 
                        #     @constraint(model, h[y, r.id, v.id, t.id, g] == h_plus[y, r.id, v.id, t.id])    # later fleet must be initialized to the exisitng fleet (here we still assume that the fleet must be build from scratch)
                        #     @constraint(model, h_plus[y, r.id, v.id, t.id] == 0)
                        #     @constraint(model, h_minus[y, r.id, v.id, t.id] == 0)
                        # end 
                        #= if y == g
                            if y == 1
                                @constraint(model, h[y, r.id, v.id, t.id, y] == h_plus[y, r.id, v.id, t.id])    # later fleet must be initialized to the exisitng fleet (here we still assume that the fleet must be build from scratch)
                                @constraint(model, h_plus[y, r.id, v.id, t.id] == 0)
                                @constraint(model, h_minus[y, r.id, v.id, t.id] == 0)
                            elseif y <= v.Lifetime[y]
                                @constraint(model, h[y, r.id, v.id, t.id, y] == h_plus[y, r.id, v.id, t.id] - h_minus[y, r.id, v.id, t.id])
                                @constraint(model, h_minus[y, r.id, v.id, t.id] == 0)
                            elseif y > v.Lifetime[y]
                                @constraint(model, h[y, r.id, v.id, t.id, y] == h_plus[y, r.id, v.id, t.id] - h_minus[y, r.id, v.id, t.id])
                                @constraint(model, h_minus[y, r.id, v.id, t.id] == h[y, r.id, v.id, t.id, y-v.Lifetime[y]])
                            end
                        elseif y < g
                            @constraint(model, h[y, r.id, v.id, t.id, g] == 0)     # only new vehicles can be added
                            @constraint(model, h_plus[y, r.id, v.id, t.id] == 0)
                            @constraint(model, h_minus[y, r.id, v.id, t.id] == 0)
                        elseif y > g
                            @constraint(model, h[y, r.id, v.id, t.id, g] == h[y-1, r.id, v.id, t.id, g])    # vehicles are not replaced
                        end =#
                    end 
                    # @constraint(model, h_plus[y, r.id, v.id, t.id] == h[y-1, r.id, v.id, t.id] - h_minus[y-1, r.id, v.id, t.id])
                end
            end
        end
    end
    println("counter: ", counter)
    # @constraint(model, [y in v.Lifetime:Y, r in odpairs, v in vehicles, t in v.technology], h[y, r.id, v.id, t.id, y] == h_plus[y, r.id, v.id, t.id] - h_minus[y-v.Lifetime, r.id, v.id, t.id])    
    
    
    # end of life  
    # ! only if y  - A > 0 TODO 

    # @constraint(model, [r in odpairs, v in vehicles, y in 2:Y, t in v.technology], h_minus[y, r.id, v.id, t.id, y] == h_plus[y, r.id, v.id, t.id, y-v.Lifetime])
    # @constraint(model, [y in 1:Y, r in odpairs, v in vehicles, t in v.technology], h_minus[y, r.id, v.id, t.id, g] == h[y-v.Lifetime, r.id, v.id, t.id, G])
    # @constraint(model, [r in odpairs, v in vehicles, y in (1+v.Lifetime):Y, t in v.technology], h_minus[y, r.id, v.id, t.id] == h[y-v.Lifetime, r.id, v.id, t.id, y])

end

if case=="A.1"
    @objective(model, Min, sum(h[r.id, v.id, t.id] * v.capital_cost for r in odpairs for v in vehicles for t in v.technology) + sum(f[p.id, k.id, v.id, t.id] * k.length * t.fuel.cost_per_kWh for p in product for k in paths for v in vehicles for t in technologies))
elseif case=="A.2"
    @objective(model, Min, sum(h[y, r.id, v.id, t.id] * v.capital_cost for y in 1:Y for r in odpairs for v in vehicles for t in v.technology) + sum(f[y, p.id, k.id, v.id, t.id] * k.length * t.fuel.cost_per_kWh for y in 1:Y for p in product for k in paths for v in vehicles for t in technologies))
elseif case=="B"
    @objective(model, Min, sum(h_plus[y, r.id, v.id, t.id]* v.capital_cost for y in 1:Y for r in odpairs for v in vehicles for t in v.technology)  + sum(f[y, p.id, k.id, v.id, t.id, g] * k.length * t.fuel.cost_per_kWh for y in 1:Y for p in product for k in paths for v in vehicles for t in v.technology for g in 1:G))
end 

#println(f)
optimize!(model)
solution_summary(model)
# println(value.(f))
# println(value.(h))

# checking solution
solved_h = value.(h)
solved_h_plus = value.(h_plus)
solved_h_minus = value.(h_minus)
solved_h_exist = value.(h_exist)
solved_f = value.(f)

for y in 1:Y
    println("h in year ",y , " ", sum(solved_h[y, :, :, :, :]), " h_plus in year ",y , " ", sum(solved_h_plus[y, :, :, :]), " h_minus in year ",y , " ", sum(solved_h_minus[y, :, :, :]), " h_exist in year ",y , " ", sum(solved_h_exist[y, :, :, :, :])," f in year ",y , " ", sum(solved_f[y, :, :, :, :, :]))
end