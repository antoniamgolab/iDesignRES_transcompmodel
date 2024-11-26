println("Running the test program ...")
using JuMP, Gurobi

# case = "A.1"
# case = "A.2"
# case = "B"
# case = "C.1"
# case = "C.2"
# case = "C.3"
case = "C.4"
# case = "C.5"

""" definition of all structs definining the dimensions of the model """

""" struct for `Node` defining the subregions of the considered region """

if case in ["A.1", "A.2"]
    Y = 2   # number of years
elseif case in ["B", "C.3", "C.4", "C.5"]
    Y = 10
    G = 10
elseif case in ["C.1", "C.2"]
    Y = 9
    G = 9
end

struct Node
    id::Int
    name::String
end

""" struct for `Mode` defining the modes of transport """

struct Mode
    id::Int
    name::String
end

struct Product
    id::Int
    name::String
end

struct Path
    id::Int
    name::String
    length::Float64
    nodes::Array{Node,1}
end

struct Odpair
    id::Int
    origin::Node
    destination::Node
    paths::Array{Path,1} # this needs to be adaoted later as for each odpair different paths exist depending also on the mode
    F::Any
    product::Product
end

struct Fuel
    id::Int
    name::String
    cost_per_kWh::Any   # € per kWh 
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
    capital_cost::Array{Float64,1}  # capital cost in €
    W::Array{Float64,1}  # load capacity in t
    spec_cons::Array{Float64,1}  # specific consumption in kWh/km  
    Lifetime::Array{Int,1} # Array if multiple generations are considered 
    AnnualRange::Array{Float64,1} # annual range in km
    products::Array{Product,1} # number of vehicles of this type
end

# now setting up some data
# ()
# case study A.1 
# these are the basic sets/dimensions that are included in the model 
nodes = [Node(1, "area1"), Node(2, "area2")]
product = [Product(1, "product1"), Product(2, "product2")]
paths = [Path(1, "path1", 100, [nodes[1]]), Path(2, "path2", 100, [nodes[2]])]
F = 10000

if case == "A.1"
    odpairs = [
        Odpair(1, nodes[1], nodes[1], [paths[1]], F, product[1]),
        Odpair(2, nodes[1], nodes[1], [paths[1]], F, product[2]),
        Odpair(3, nodes[2], nodes[2], [paths[2]], F, product[1]),
        Odpair(4, nodes[2], nodes[2], [paths[2]], F, product[2]),
    ]
elseif case == "A.2"
    odpairs = [
        Odpair(1, nodes[1], nodes[1], [paths[1]], [F, F], product[1]),
        Odpair(2, nodes[1], nodes[1], [paths[1]], [F, F], product[2]),
        Odpair(3, nodes[2], nodes[2], [paths[2]], [F, F], product[1]),
        Odpair(4, nodes[2], nodes[2], [paths[2]], [F, F], product[2]),
    ]
    println("F: ", odpairs[1].F[2])
elseif case in ["B", "C.1", "C.2", "C.3", "C.4", "C.5"]
    odpairs = [
        Odpair(1, nodes[1], nodes[1], [paths[1]], fill(F, Y), product[1]),
        Odpair(2, nodes[1], nodes[1], [paths[1]], fill(F, Y), product[2]),
        Odpair(3, nodes[2], nodes[2], [paths[2]], fill(F, Y), product[1]),
        Odpair(4, nodes[2], nodes[2], [paths[2]], fill(F, Y), product[2]),
    ]
end

modes = [Mode(1, "mode1"), Mode(2, "mode2")]
vehicletypes = [
    Vehicletype(1, "vehicletype1", modes[1]),
    Vehicletype(2, "vehicletype2", modes[2]),
    Vehicletype(3, "vehicletype3", modes[1]),
    Vehicletype(4, "vehicletype4", modes[2]),
]

if case in ["A.1", "A.2", "B"]
    technologies = [
        Technology(1, "tech1", Fuel(1, "fuel1", fill(20 / 100, Y))),
        Technology(2, "tech2", Fuel(2, "fuel2", fill(30 / 100, Y))),
    ]
elseif case in ["C.1", "C.3", "C.4", "C.5"]
    technologies = [
        Technology(1, "tech1", Fuel(1, "fuel1", fill(20 / 100, Y))),
        Technology(2, "tech2", Fuel(2, "fuel2", fill(20 / 100, Y))),
    ]
elseif case in ["C.2"]
    technologies = [
        Technology(
            1,
            "tech1",
            Fuel(1, "fuel1", vcat(fill(50 / 100, 3), fill(10 / 100, 3), fill(50 / 100, 3))),
        ),
        Technology(
            2,
            "tech2",
            Fuel(2, "fuel2", vcat(fill(10 / 100, 3), fill(50 / 100, 3), fill(10 / 100, 3))),
        ),
    ]
end

if case == "A.1" # in this case - as we only consider the time horizon of 2 years - we assume a vehicle age of 1 year, so that we can observe a replacement in this time span for this simple(!) case
    vehicles = [
        TechVehicle(
            1,
            "vehicle1",
            vehicletypes[1],
            technologies[1],
            [10000],
            [10.0],
            [1],
            [1],
            [10000],
            product,
        ),
        TechVehicle(
            2,
            "vehicle2",
            vehicletypes[2],
            technologies[2],
            [15000],
            [10.0],
            [1],
            [1],
            [10000],
            product,
        ),
    ]
elseif case == "A.2"
    vehicles = [
        TechVehicle(
            1,
            "vehicle1",
            vehicletypes[1],
            technologies[1],
            [10000, 10000],
            [10.0, 10.0],
            [1, 1],
            [1, 1],
            [10000, 10000],
            product,
        ),
        TechVehicle(
            2,
            "vehicle2",
            vehicletypes[2],
            technologies[2],
            [15000, 15000],
            [10.0, 10.0],
            [1, 1],
            [1, 1],
            [10000, 10000],
            product,
        ),
    ]
elseif case == "B"
    vehicles = [
        TechVehicle(
            1,
            "vehicle1",
            vehicletypes[1],
            technologies[1],
            fill(10000, G),
            fill(10, G),
            fill(1, G),
            fill(5, G),
            fill(10000, G),
            product,
        ),
        TechVehicle(
            2,
            "vehicle2",
            vehicletypes[2],
            technologies[2],
            fill(15000, G),
            fill(10, G),
            fill(1, G),
            fill(5, G),
            fill(10000, G),
            product,
        ),
    ]
elseif case in ["C.1", "C.2"]
    vehicles = [
        TechVehicle(
            1,
            "vehicle1",
            vehicletypes[1],
            technologies[1],
            [10000, 10000, 10000, 5000, 5000, 5000, 10000, 10000, 10000],
            fill(10, G),
            fill(1, G),
            fill(3, G),
            fill(10000, G),
            product,
        ),
        TechVehicle(
            1,
            "vehicle1",
            vehicletypes[1],
            technologies[2],
            [5000, 5000, 5000, 10000, 10000, 10000, 5000, 5000, 5000],
            fill(10, G),
            fill(1, G),
            fill(3, G),
            fill(10000, G),
            product,
        ),
    ]
elseif case in ["C.3", "C.5"]
    vehicles = [
        TechVehicle(
            1,
            "vehicle1",
            vehicletypes[1],
            technologies[1],
            [10000, 10000, 10000, 10000, 10000, 5000, 5000, 5000, 5000, 5000],
            fill(10, G),
            fill(1, G),
            fill(2, G),
            fill(10000, G),
            product,
        ),
        TechVehicle(
            2,
            "vehicle2",
            vehicletypes[2],
            technologies[2],
            [5000, 5000, 5000, 5000, 5000, 10000, 10000, 10000, 10000, 10000],
            fill(10, G),
            fill(1, G),
            fill(2, G),
            fill(10000, G),
            product,
        ),
    ]
elseif case in ["C.4"]
    vehicles = [
        TechVehicle(
            1,
            "vehicle1",
            vehicletypes[1],
            technologies[1],
            [10000, 10000, 10000, 10000, 10000, 5000, 5000, 5000, 5000, 5000],
            fill(10, G),
            fill(1, G),
            fill(2, G),
            fill(10000, G),
            product,
        ),
        TechVehicle(
            2,
            "vehicle2",
            vehicletypes[3],
            technologies[2],
            [5000, 5000, 5000, 5000, 5000, 10000, 10000, 10000, 10000, 10000],
            fill(10, G),
            fill(1, G),
            fill(2, G),
            fill(10000, G),
            product,
        ),
    ]
end

# print("thats the lifetime of the vehs", vehicles[1].Lifetime)
# now defining the constraints

model = Model(Gurobi.Optimizer)

# creating variables 
# flow variable pkvt

v_t_pairs = Set((tv.vehicle_type.id, tv.technology.id) for tv in vehicles)
m_t_v_pairs = Set(
    (mtv.vehicle_type.mode.id, mtv.vehicle_type.id, mtv.technology.id) for mtv in vehicles
)
p_m_t_v_pairs = Set(
    (p.id, pmtv.vehicle_type.mode.id, pmtv.vehicle_type.id, pmtv.technology.id) for
    pmtv in vehicles for p in pmtv.products
)
alpha_h = 0.25
beta_h = 0.25
alpha_f = 0.25
beta_f = 0.25
if case == "A.1"
    @variable(model, f[[p.id for p in product], [k.id for k in paths], v_t_pairs] >= 0)
    @variable(model, h[[r.id for r in odpairs], v_t_pairs] >= 0)
elseif case == "A.2"
    @variable(
        model,
        f[[y for y in 1:Y], [p.id for p in product], [k.id for k in paths], v_t_pairs] >= 0
    )
    @variable(model, h[[y for y in 1:Y], [r.id for r in odpairs], v_t_pairs] >= 0)
elseif case in ["B", "C.1", "C.2"]
    @variable(
        model,
        f[
            [y for y in 1:Y],
            [p.id for p in product],
            [k.id for k in paths],
            v_t_pairs,
            [g for g in 1:G],
        ] >= 0
    )
    @variable(
        model, h[[y for y in 1:Y], [r.id for r in odpairs], v_t_pairs, [g for g in 1:G]] >= 0
    )
    @variable(
        model,
        h_exist[[y for y in 1:Y], [r.id for r in odpairs], v_t_pairs, [g for g in 1:G]] >= 0
    )
    @variable(
        model,
        h_plus[[y for y in 1:Y], [r.id for r in odpairs], v_t_pairs, [g for g in 1:G]] >= 0
    )
    @variable(
        model,
        h_minus[[y for y in 1:Y], [r.id for r in odpairs], v_t_pairs, [g for g in 1:G]] >= 0
    )
elseif case in ["C.3"]
    @variable(
        model,
        f[
            [y for y in 1:Y],
            [p.id for p in product],
            [k.id for k in paths],
            m_t_v_pairs,
            [g for g in 1:G],
        ] >= 0
    )
    @variable(
        model,
        h[[y for y in 1:Y], [r.id for r in odpairs], m_t_v_pairs, [g for g in 1:G]] >= 0
    )
    @variable(
        model,
        h_exist[[y for y in 1:Y], [r.id for r in odpairs], m_t_v_pairs, [g for g in 1:G]] >= 0
    )
    @variable(
        model,
        h_plus[[y for y in 1:Y], [r.id for r in odpairs], m_t_v_pairs, [g for g in 1:G]] >= 0
    )
    @variable(
        model,
        h_minus[[y for y in 1:Y], [r.id for r in odpairs], m_t_v_pairs, [g for g in 1:G]] >= 0
    )
elseif case in ["C.4", "C.5"]
    @variable(
        model,
        f[
            [y for y in 1:Y],
            [r.id for r in odpairs],
            p_m_t_v_pairs,
            [k.id for k in paths],
            [g for g in 1:G],
        ] >= 0
    )
    @variable(
        model,
        h[[y for y in 1:Y], [r.id for r in odpairs], m_t_v_pairs, [g for g in 1:G]] >= 0
    )
    @variable(
        model,
        h_exist[[y for y in 1:Y], [r.id for r in odpairs], m_t_v_pairs, [g for g in 1:G]] >= 0
    )
    @variable(
        model,
        h_plus[[y for y in 1:Y], [r.id for r in odpairs], m_t_v_pairs, [g for g in 1:G]] >= 0
    )
    @variable(
        model,
        h_minus[[y for y in 1:Y], [r.id for r in odpairs], m_t_v_pairs, [g for g in 1:G]] >= 0
    )
end
print()

if case == "A.1"
    println(paths[1].length / (vehicles[1].W[1] * vehicles[1].AnnualRange[1]))
    println(paths[1].length, vehicles[1].W[1], vehicles[1].AnnualRange[1])
    @constraint(
        model,
        [r in odpairs],
        sum(f[r.product.id, k.id, v_t] for k in r.paths for v_t in v_t_pairs) == r.F
    )
    @constraint(
        model,
        [r in odpairs, v in vehicles],
        h[r.id, (v.vehicle_type.id, v.technology.id)] >= sum(
            (k.length / (v.W[1] * v.AnnualRange[1])) *
            f[r.product.id, k.id, (v.vehicle_type.id, v.technology.id)] for k in r.paths
        )
    )

elseif case == "A.2"
    @constraint(
        model,
        [y in 1:Y, r in odpairs],
        sum(f[y, r.product.id, k.id, v_t] for k in r.paths for v_t in v_t_pairs) == r.F[y]
    )
    @constraint(
        model,
        [y in 1:Y, r in odpairs, v in vehicles],
        h[y, r.id, (v.vehicle_type.id, v.technology.id)] >= sum(
            (k.length / (v.W[y] * v.AnnualRange[y])) *
            f[y, r.product.id, k.id, (v.vehicle_type.id, v.technology.id)] for k in r.paths
        )
    )
elseif case in ["B", "C.1", "C.2"]
    @constraint(
        model,
        [y in 1:Y, r in odpairs],
        sum(
            f[y, r.product.id, k.id, (v.vehicle_type.id, v.technology.id), g] for
            k in r.paths for v in vehicles for g in 1:G
        ) == r.F[y]
    )
    @constraint(
        model,
        [y in 1:Y, r in odpairs, v in vehicles, g in 1:G],
        h[y, r.id, (v.vehicle_type.id, v.technology.id), g] >= sum(
            (k.length / (v.W[y] * v.AnnualRange[y])) *
            f[y, r.product.id, k.id, (v.vehicle_type.id, v.technology.id), g] for
            k in r.paths
        )
    )
    # vehicle stock aging
    for r in odpairs
        for v in vehicles
            for y in 1:Y
                for g in 1:G
                    if y >= g
                        @constraint(
                            model,
                            h[y, r.id, (v.vehicle_type.id, v.technology.id), g] ==
                                h_exist[y, r.id, (v.vehicle_type.id, v.technology.id), g] +
                            h_plus[y, r.id, (v.vehicle_type.id, v.technology.id), g] -
                            h_minus[y, r.id, (v.vehicle_type.id, v.technology.id), g]
                        )
                        if y == 1
                            @constraint(
                                model,
                                h_exist[y, r.id, (v.vehicle_type.id, v.technology.id), g] ==
                                    0
                            )
                        else
                            @constraint(
                                model,
                                h_exist[y, r.id, (v.vehicle_type.id, v.technology.id), g] ==
                                    h[y - 1, r.id, (v.vehicle_type.id, v.technology.id), g]
                            )
                        end
                        if y != g
                            @constraint(
                                model,
                                h_plus[y, r.id, (v.vehicle_type.id, v.technology.id), g] ==
                                    0
                            )
                        end

                        if y - g == v.Lifetime[g]    # vehicles are replaced after their lifetime
                            # println("")
                            @constraint(
                                model,
                                h_minus[y, r.id, (v.vehicle_type.id, v.technology.id), g] ==
                                    h_plus[
                                    y - v.Lifetime[g],
                                    r.id,
                                    (v.vehicle_type.id, v.technology.id),
                                    g,
                                ]
                            )
                        else
                            @constraint(
                                model,
                                h_minus[y, r.id, (v.vehicle_type.id, v.technology.id), g] ==
                                    0
                            )
                        end
                    elseif y < g    # there can be no vehicles at year y that are of generation g = y - 1
                        @constraint(
                            model, h[y, r.id, (v.vehicle_type.id, v.technology.id), g] == 0
                        )
                        @constraint(
                            model,
                            h_exist[y, r.id, (v.vehicle_type.id, v.technology.id), g] == 0
                        )
                        @constraint(
                            model,
                            h_plus[y, r.id, (v.vehicle_type.id, v.technology.id), g] == 0
                        )
                        @constraint(
                            model,
                            h_minus[y, r.id, (v.vehicle_type.id, v.technology.id), g] == 0
                        )
                    end
                end
            end
        end
    end
elseif case in ["C.3"]
    @constraint(
        model,
        [y in 1:Y, r in odpairs],
        sum(
            f[
                y,
                r.product.id,
                k.id,
                (v.vehicle_type.mode.id, v.vehicle_type.id, v.technology.id),
                g,
            ] for k in r.paths for v in vehicles for g in 1:G
        ) == r.F[y]
    )
    @constraint(
        model,
        [y in 1:Y, r in odpairs, v in vehicles, g in 1:G],
        h[y, r.id, (v.vehicle_type.mode.id, v.vehicle_type.id, v.technology.id), g] >= sum(
            (k.length / (v.W[y] * v.AnnualRange[y])) * f[
                y,
                r.product.id,
                k.id,
                (v.vehicle_type.mode.id, v.vehicle_type.id, v.technology.id),
                g,
            ] for k in r.paths
        )
    )
    # vehicle stock aging
    for r in odpairs
        for v in vehicles
            for y in 1:Y
                for g in 1:G
                    if y >= g
                        @constraint(
                            model,
                            h[
                                y,
                                r.id,
                                (
                                    v.vehicle_type.mode.id,
                                    v.vehicle_type.id,
                                    v.technology.id,
                                ),
                                g,
                            ] ==
                                h_exist[
                                y,
                                r.id,
                                (
                                    v.vehicle_type.mode.id,
                                    v.vehicle_type.id,
                                    v.technology.id,
                                ),
                                g,
                            ] + h_plus[
                                y,
                                r.id,
                                (
                                    v.vehicle_type.mode.id,
                                    v.vehicle_type.id,
                                    v.technology.id,
                                ),
                                g,
                            ] - h_minus[
                                y,
                                r.id,
                                (
                                    v.vehicle_type.mode.id,
                                    v.vehicle_type.id,
                                    v.technology.id,
                                ),
                                g,
                            ]
                        )
                        if y == 1
                            @constraint(
                                model,
                                h_exist[
                                    y,
                                    r.id,
                                    (
                                        v.vehicle_type.mode.id,
                                        v.vehicle_type.id,
                                        v.technology.id,
                                    ),
                                    g,
                                ] == 0
                            )
                        else
                            @constraint(
                                model,
                                h_exist[
                                    y,
                                    r.id,
                                    (
                                        v.vehicle_type.mode.id,
                                        v.vehicle_type.id,
                                        v.technology.id,
                                    ),
                                    g,
                                ] == h[
                                    y - 1,
                                    r.id,
                                    (
                                        v.vehicle_type.mode.id,
                                        v.vehicle_type.id,
                                        v.technology.id,
                                    ),
                                    g,
                                ]
                            )
                        end
                        if y != g
                            @constraint(
                                model,
                                h_plus[
                                    y,
                                    r.id,
                                    (
                                        v.vehicle_type.mode.id,
                                        v.vehicle_type.id,
                                        v.technology.id,
                                    ),
                                    g,
                                ] == 0
                            )
                        end

                        if y - g == v.Lifetime[g]    # vehicles are replaced after their lifetime
                            # println("")
                            @constraint(
                                model,
                                h_minus[
                                    y,
                                    r.id,
                                    (
                                        v.vehicle_type.mode.id,
                                        v.vehicle_type.id,
                                        v.technology.id,
                                    ),
                                    g,
                                ] == h_plus[
                                    y - v.Lifetime[g],
                                    r.id,
                                    (
                                        v.vehicle_type.mode.id,
                                        v.vehicle_type.id,
                                        v.technology.id,
                                    ),
                                    g,
                                ]
                            )
                        else
                            @constraint(
                                model,
                                h_minus[
                                    y,
                                    r.id,
                                    (
                                        v.vehicle_type.mode.id,
                                        v.vehicle_type.id,
                                        v.technology.id,
                                    ),
                                    g,
                                ] == 0
                            )
                        end
                    elseif y < g    # there can be no vehicles at year y that are of generation g = y - 1
                        @constraint(
                            model,
                            h[
                                y,
                                r.id,
                                (
                                    v.vehicle_type.mode.id,
                                    v.vehicle_type.id,
                                    v.technology.id,
                                ),
                                g,
                            ] == 0
                        )
                        @constraint(
                            model,
                            h_exist[
                                y,
                                r.id,
                                (
                                    v.vehicle_type.mode.id,
                                    v.vehicle_type.id,
                                    v.technology.id,
                                ),
                                g,
                            ] == 0
                        )
                        @constraint(
                            model,
                            h_plus[
                                y,
                                r.id,
                                (
                                    v.vehicle_type.mode.id,
                                    v.vehicle_type.id,
                                    v.technology.id,
                                ),
                                g,
                            ] == 0
                        )
                        @constraint(
                            model,
                            h_minus[
                                y,
                                r.id,
                                (
                                    v.vehicle_type.mode.id,
                                    v.vehicle_type.id,
                                    v.technology.id,
                                ),
                                g,
                            ] == 0
                        )
                    end
                end
            end
        end
    end
elseif case in ["C.4", "C.5"]
    @constraint(
        model,
        [y in 1:Y, r in odpairs],
        sum(
            f[
                y,
                r.id,
                (p.id, v.vehicle_type.mode.id, v.vehicle_type.id, v.technology.id),
                k.id,
                g,
            ] for k in r.paths for v in vehicles for g in 1:G for p in v.products
        ) == r.F[y]
    )
    @constraint(
        model,
        [y in 1:Y, r in odpairs, v in vehicles, g in 1:G],
        h[y, r.id, (v.vehicle_type.mode.id, v.vehicle_type.id, v.technology.id), g] >= sum(
            (k.length / (v.W[y] * v.AnnualRange[y])) * f[
                y,
                r.id,
                (p.id, v.vehicle_type.mode.id, v.vehicle_type.id, v.technology.id),
                k.id,
                g,
            ] for k in r.paths for p in v.products
        )
    )
    for r in odpairs
        for v in vehicles
            for y in 1:Y
                for g in 1:G
                    if y >= g
                        @constraint(
                            model,
                            h[
                                y,
                                r.id,
                                (
                                    v.vehicle_type.mode.id,
                                    v.vehicle_type.id,
                                    v.technology.id,
                                ),
                                g,
                            ] ==
                                h_exist[
                                y,
                                r.id,
                                (
                                    v.vehicle_type.mode.id,
                                    v.vehicle_type.id,
                                    v.technology.id,
                                ),
                                g,
                            ] + h_plus[
                                y,
                                r.id,
                                (
                                    v.vehicle_type.mode.id,
                                    v.vehicle_type.id,
                                    v.technology.id,
                                ),
                                g,
                            ] - h_minus[
                                y,
                                r.id,
                                (
                                    v.vehicle_type.mode.id,
                                    v.vehicle_type.id,
                                    v.technology.id,
                                ),
                                g,
                            ]
                        )
                        if y == 1
                            @constraint(
                                model,
                                h_exist[
                                    y,
                                    r.id,
                                    (
                                        v.vehicle_type.mode.id,
                                        v.vehicle_type.id,
                                        v.technology.id,
                                    ),
                                    g,
                                ] == 0
                            )
                        else
                            @constraint(
                                model,
                                h_exist[
                                    y,
                                    r.id,
                                    (
                                        v.vehicle_type.mode.id,
                                        v.vehicle_type.id,
                                        v.technology.id,
                                    ),
                                    g,
                                ] == h[
                                    y - 1,
                                    r.id,
                                    (
                                        v.vehicle_type.mode.id,
                                        v.vehicle_type.id,
                                        v.technology.id,
                                    ),
                                    g,
                                ]
                            )
                        end
                        if y != g
                            @constraint(
                                model,
                                h_plus[
                                    y,
                                    r.id,
                                    (
                                        v.vehicle_type.mode.id,
                                        v.vehicle_type.id,
                                        v.technology.id,
                                    ),
                                    g,
                                ] == 0
                            )
                        end

                        if y - g == v.Lifetime[g]    # vehicles are replaced after their lifetime
                            # println("")
                            @constraint(
                                model,
                                h_minus[
                                    y,
                                    r.id,
                                    (
                                        v.vehicle_type.mode.id,
                                        v.vehicle_type.id,
                                        v.technology.id,
                                    ),
                                    g,
                                ] == h_plus[
                                    y - v.Lifetime[g],
                                    r.id,
                                    (
                                        v.vehicle_type.mode.id,
                                        v.vehicle_type.id,
                                        v.technology.id,
                                    ),
                                    g,
                                ]
                            )
                        else
                            @constraint(
                                model,
                                h_minus[
                                    y,
                                    r.id,
                                    (
                                        v.vehicle_type.mode.id,
                                        v.vehicle_type.id,
                                        v.technology.id,
                                    ),
                                    g,
                                ] == 0
                            )
                        end
                    elseif y < g    # there can be no vehicles at year y that are of generation g = y - 1
                        @constraint(
                            model,
                            h[
                                y,
                                r.id,
                                (
                                    v.vehicle_type.mode.id,
                                    v.vehicle_type.id,
                                    v.technology.id,
                                ),
                                g,
                            ] == 0
                        )
                        @constraint(
                            model,
                            h_exist[
                                y,
                                r.id,
                                (
                                    v.vehicle_type.mode.id,
                                    v.vehicle_type.id,
                                    v.technology.id,
                                ),
                                g,
                            ] == 0
                        )
                        @constraint(
                            model,
                            h_plus[
                                y,
                                r.id,
                                (
                                    v.vehicle_type.mode.id,
                                    v.vehicle_type.id,
                                    v.technology.id,
                                ),
                                g,
                            ] == 0
                        )
                        @constraint(
                            model,
                            h_minus[
                                y,
                                r.id,
                                (
                                    v.vehicle_type.mode.id,
                                    v.vehicle_type.id,
                                    v.technology.id,
                                ),
                                g,
                            ] == 0
                        )
                    end
                end
            end
        end
    end
    # summiere hier bei über alle die mit dem vehicle type fahren können
    # technology shift 
    @constraint(
        model,
        [y in 2:Y, r in odpairs, mtv in m_t_v_pairs],
        (sum(h[y, r.id, mtv, g] for g in 1:G) - sum(h[y - 1, r.id, mtv, g] for g in 1:G)) <=
            alpha_h * sum(h[y, r.id, mtv0, g] for mtv0 in m_t_v_pairs for g in 1:G) +
        beta_h * sum(h[y - 1, r.id, mtv, g] for g in 1:G)
    )
    @constraint(
        model,
        [y in 2:Y, r in odpairs, p_m_v in p_m_t_v_pairs],
        (
            sum(f[y, r.id, p_m_v, k.id, g] for k in r.paths for g in 1:G) -
            sum(f[y - 1, r.id, p_m_v, k.id, g] for k in r.paths for g in 1:G)
        ) <=
            alpha_f * sum(
            f[y, r.id, pmv0, k.id, g] for pmv0 in p_m_t_v_pairs for k in r.paths for g in 1:G
        ) + beta_f * sum(f[y - 1, r.id, p_m_v, k.id, g] for k in r.paths for g in 1:G)
    )
    @constraint(
        model,
        [y in 2:Y, r in odpairs, mtv in m_t_v_pairs],
        -(sum(h[y, r.id, mtv, g] for g in 1:G) - sum(h[y - 1, r.id, mtv, g] for g in 1:G)) <=
            alpha_h * sum(h[y, r.id, mtv0, g] for mtv0 in m_t_v_pairs for g in 1:G) +
        beta_h * sum(h[y - 1, r.id, mtv, g] for g in 1:G)
    )
    @constraint(
        model,
        [y in 2:Y, r in odpairs, p_m_v in p_m_t_v_pairs],
        -(
            sum(f[y, r.id, p_m_v, k.id, g] for k in r.paths for g in 1:G) -
            sum(f[y - 1, r.id, p_m_v, k.id, g] for k in r.paths for g in 1:G)
        ) <=
            alpha_f * sum(
            f[y, r.id, pmv0, k.id, g] for pmv0 in p_m_t_v_pairs for k in r.paths for g in 1:G
        ) + beta_f * sum(f[y - 1, r.id, p_m_v, k.id, g] for k in r.paths for g in 1:G)
    )
end
# @constraint(model, [y in v.Lifetime:Y, r in odpairs, v in vehicles, t in v.technology], h[y, r.id, v.id, t.id, y] == h_plus[y, r.id, v.id, t.id] - h_minus[y-v.Lifetime, r.id, v.id, t.id])    

# end of life  
# ! only if y  - A > 0 TODO 

# @constraint(model, [r in odpairs, v in vehicles, y in 2:Y, t in v.technology], h_minus[y, r.id, v.id, t.id, y] == h_plus[y, r.id, v.id, t.id, y-v.Lifetime])
# @constraint(model, [y in 1:Y, r in odpairs, v in vehicles, t in v.technology], h_minus[y, r.id, v.id, t.id, g] == h[y-v.Lifetime, r.id, v.id, t.id, G])
# @constraint(model, [r in odpairs, v in vehicles, y in (1+v.Lifetime):Y, t in v.technology], h_minus[y, r.id, v.id, t.id] == h[y-v.Lifetime, r.id, v.id, t.id, y])

if case == "A.1"
    @objective(
        model,
        Min,
        sum(
            h[r.id, (v.vehicle_type.id, v.technology.id)] * v.capital_cost[1] for
            r in odpairs for v in vehicles
        ) + sum(
            f[p.id, k.id, (v.vehicle_type.id, v.technology.id)] *
            k.length *
            v.technology.fuel.cost_per_kWh[1] for p in product for k in paths for
            v in vehicles
        )
    )
elseif case == "A.2"
    @objective(
        model,
        Min,
        sum(
            h[y, r.id, (v.vehicle_type.id, v.technology.id)] * v.capital_cost[y] for y in
                1:Y for r in odpairs for v in vehicles
        ) + sum(
            f[y, p.id, k.id, (v.vehicle_type.id, v.technology.id)] *
            k.length *
            v.technology.fuel.cost_per_kWh[y] for y in 1:Y for p in product for k in paths
            for v in vehicles
        )
    )
elseif case in ["B"]
    @objective(
        model,
        Min,
        sum(
            h_plus[y, r.id, (v.vehicle_type.id, v.technology.id), g] * v.capital_cost[g] for
            y in 1:Y for r in odpairs for v in vehicles for g in 1:G
        ) + sum(
            f[y, p.id, k.id, (v.vehicle_type.id, v.technology.id), g] *
            k.length *
            v.technology.fuel.cost_per_kWh[g] for y in 1:Y for p in product for k in paths
            for v in vehicles for g in 1:G
        )
    )
elseif case in ["C.1", "C.2"]
    @objective(
        model,
        Min,
        sum(
            h_plus[y, r.id, (v.vehicle_type.id, v.technology.id), g] * v.capital_cost[y] for
            y in 1:Y for r in odpairs for v in vehicles for g in 1:G
        ) + sum(
            f[y, p.id, k.id, (v.vehicle_type.id, v.technology.id), g] *
            k.length *
            v.technology.fuel.cost_per_kWh[y] for y in 1:Y for p in product for k in paths
            for v in vehicles for g in 1:G
        )
    )
elseif case in ["C.3"]
    @objective(
        model,
        Min,
        sum(
            h_plus[
                y, r.id, (v.vehicle_type.mode.id, v.vehicle_type.id, v.technology.id), g
            ] * v.capital_cost[y] for y in 1:Y for r in odpairs for v in vehicles for
            g in 1:G
        ) + sum(
            f[
                y,
                r.product.id,
                k.id,
                (v.vehicle_type.mode.id, v.vehicle_type.id, v.technology.id),
                g,
            ] *
            k.length *
            v.technology.fuel.cost_per_kWh[y] for y in 1:Y for r in odpairs for
            v in vehicles for p in v.products for k in r.paths for g in 1:G
        )
    )
elseif case in ["C.4", "C.5"]
    @objective(
        model,
        Min,
        sum(
            h_plus[
                y, r.id, (v.vehicle_type.mode.id, v.vehicle_type.id, v.technology.id), g
            ] * v.capital_cost[y] for y in 1:Y for r in odpairs for v in vehicles for
            g in 1:G
        ) + sum(
            f[
                y,
                r.id,
                (p.id, v.vehicle_type.mode.id, v.vehicle_type.id, v.technology.id),
                k.id,
                g,
            ] *
            k.length *
            v.technology.fuel.cost_per_kWh[y] for y in 1:Y for r in odpairs for
            v in vehicles for p in v.products for k in r.paths for g in 1:G
        )
    )
end

#println(f)
optimize!(model)
solution_summary(model)
# println(value.(f))
# println(value.(h))

# checking solution
if case == "A.1"
    solved_f = value.(f)
    solved_h = value.(h)
    for r in odpairs
        for v_t in v_t_pairs
            println(
                "h for odpair ",
                r.id,
                " vehicle ",
                v_t[1],
                " technology ",
                v_t[2],
                " ",
                solved_h[r.id, v_t],
            )
            println(
                "f for product ",
                r.product.id,
                " vehicle ",
                v_t[1],
                " technology ",
                v_t[2],
                " ",
                sum(solved_f[r.product.id, k.id, v_t] for k in r.paths),
            )
        end
    end
elseif case == "A.2"
    solved_f = value.(f)
    solved_h = value.(h)
    for y in 1:Y
        for r in odpairs
            for v_t in v_t_pairs
                println(
                    "h in year ",
                    y,
                    " for odpair ",
                    r.id,
                    " vehicle ",
                    v_t[1],
                    " technology ",
                    v_t[2],
                    " ",
                    solved_h[y, r.id, v_t],
                )
            end
        end
    end
elseif case in ["B"]
    solved_h = value.(h)
    solved_h_plus = value.(h_plus)
    solved_h_minus = value.(h_minus)
    solved_h_exist = value.(h_exist)
    solved_f = value.(f)

    for y in 1:Y
        println(
            "h in year ",
            y,
            " ",
            sum(solved_h[y, :, :, :]),
            " h_plus in year ",
            y,
            " ",
            sum(solved_h_plus[y, :, :, :]),
            " h_minus in year ",
            y,
            " ",
            sum(solved_h_minus[y, :, :, :]),
            " h_exist in year ",
            y,
            " ",
            sum(solved_h_exist[y, :, :, :]),
            " f in year ",
            y,
            " ",
            sum(solved_f[y, :, :, :, :]),
        )
    end
elseif case in ["C.1", "C.2"]
    solved_h = value.(h)
    solved_h_plus = value.(h_plus)
    solved_h_minus = value.(h_minus)
    solved_h_exist = value.(h_exist)
    solved_f = value.(f)

    for y in 1:Y
        for t in technologies
            println(
                "year ",
                y,
                ": tech ",
                t.name,
                " h ",
                sum(
                    sum(solved_h[y, :, (v.vehicle_type.id, v.technology.id), :]) for
                    v in vehicles if v.technology.id == t.id
                ),
                " h_plus ",
                sum(
                    sum(solved_h_plus[y, :, (v.vehicle_type.id, v.technology.id), :]) for
                    v in vehicles if v.technology.id == t.id
                ),
                " h_minus ",
                sum(
                    sum(solved_h_minus[y, :, (v.vehicle_type.id, v.technology.id), :]) for
                    v in vehicles if v.technology.id == t.id
                ),
                " h_exist ",
                sum(
                    sum(solved_h_exist[y, :, (v.vehicle_type.id, v.technology.id), :]) for
                    v in vehicles if v.technology.id == t.id
                ),
                " f in year ",
                sum(
                    sum(solved_f[y, :, :, (v.vehicle_type.id, v.technology.id), :]) for
                    v in vehicles if v.technology.id == t.id
                ),
            )
        end
        # println("h in year ",y , " ", sum(solved_h[y, :, :, :, :]), " h_plus in year ",y , " ", sum(solved_h_plus[y, :, :, :, :]), " h_minus in year ",y , " ", sum(solved_h_minus[y, :, :, :, :]), " h_exist in year ",y , " ", sum(solved_h_exist[y, :, :, :, :])," f in year ",y , " ", sum(solved_f[y, :, :, :, :, :]))
    end
elseif case in ["C.3"]
    solved_h = value.(h)
    solved_h_plus = value.(h_plus)
    solved_h_minus = value.(h_minus)
    solved_h_exist = value.(h_exist)
    solved_f = value.(f)

    for y in 1:Y
        for m in modes
            # println("year ", y, ": mode  ", m.id, " h ", sum(sum(solved_h[y, :, (v.vehicle_type.mode.id ,v.vehicle_type.id, v.technology.id), :]) for v in vehicles if v.vehicle_type.mode.id == m.id), " h_plus ", sum(sum(solved_h_plus[y, :, (v.vehicle_type.mode.id ,v.vehicle_type.id, v.technology.id), :]) for v in vehicles if v.vehicle_type.mode.id == m.id))
            println(
                "year ",
                y,
                ": mode ",
                m.name,
                " h ",
                sum(
                    sum(
                        solved_h[
                            y,
                            :,
                            (v.vehicle_type.mode.id, v.vehicle_type.id, v.technology.id),
                            :,
                        ],
                    ) for v in vehicles if v.vehicle_type.mode.id == m.id
                ),
                " h_plus ",
                sum(
                    sum(
                        solved_h_plus[
                            y,
                            :,
                            (v.vehicle_type.mode.id, v.vehicle_type.id, v.technology.id),
                            :,
                        ],
                    ) for v in vehicles if v.vehicle_type.mode.id == m.id
                ),
                " h_minus ",
                sum(
                    sum(
                        solved_h_minus[
                            y,
                            :,
                            (v.vehicle_type.mode.id, v.vehicle_type.id, v.technology.id),
                            :,
                        ],
                    ) for v in vehicles if v.vehicle_type.mode.id == m.id
                ),
                " h_exist ",
                sum(
                    sum(
                        solved_h_exist[
                            y,
                            :,
                            (v.vehicle_type.mode.id, v.vehicle_type.id, v.technology.id),
                            :,
                        ],
                    ) for v in vehicles if v.vehicle_type.mode.id == m.id
                ),
                " f in year ",
                sum(
                    sum(
                        solved_f[
                            y,
                            :,
                            :,
                            (v.vehicle_type.mode.id, v.vehicle_type.id, v.technology.id),
                            :,
                        ],
                    ) for v in vehicles if v.vehicle_type.mode.id == m.id
                ),
            )
        end
    end
elseif case in ["C.4"]
    solved_h = value.(h)
    solved_h_plus = value.(h_plus)
    solved_h_minus = value.(h_minus)
    solved_h_exist = value.(h_exist)
    solved_f = value.(f)
    # checking for each year the transition from one technology to another 
    for y in 1:Y
        for t in technologies
            println(
                "year ",
                y,
                ": tech ",
                t.name,
                " h ",
                sum(
                    sum(
                        solved_h[
                            y,
                            :,
                            (v.vehicle_type.mode.id, v.vehicle_type.id, v.technology.id),
                            :,
                        ],
                    ) for v in vehicles if v.technology.id == t.id
                ),
                " h_plus ",
                sum(
                    sum(
                        solved_h_plus[
                            y,
                            :,
                            (v.vehicle_type.mode.id, v.vehicle_type.id, v.technology.id),
                            :,
                        ],
                    ) for v in vehicles if v.technology.id == t.id
                ),
                " h_minus ",
                sum(
                    sum(
                        solved_h_minus[
                            y,
                            :,
                            (v.vehicle_type.mode.id, v.vehicle_type.id, v.technology.id),
                            :,
                        ],
                    ) for v in vehicles if v.technology.id == t.id
                ),
                " h_exist ",
                sum(
                    sum(
                        solved_h_exist[
                            y,
                            :,
                            (v.vehicle_type.mode.id, v.vehicle_type.id, v.technology.id),
                            :,
                        ],
                    ) for v in vehicles if v.technology.id == t.id
                ),
                " f in year ",
                sum(
                    sum(
                        solved_f[
                            y,
                            :,
                            (
                                p.id,
                                v.vehicle_type.mode.id,
                                v.vehicle_type.id,
                                v.technology.id,
                            ),
                            :,
                            :,
                        ],
                    ) for v in vehicles for p in v.products if v.technology.id == t.id
                ),
            )
        end
    end
elseif case in ["C.5"]
    solved_h = value.(h)
    solved_h_plus = value.(h_plus)
    solved_h_minus = value.(h_minus)
    solved_h_exist = value.(h_exist)
    solved_f = value.(f)
    # checking for each year the transition from one technology to another 
    for y in 1:Y
        for m in modes
            println(
                "year ",
                y,
                ": mode ",
                m.name,
                " h ",
                sum(
                    sum(
                        solved_h[
                            y,
                            :,
                            (v.vehicle_type.mode.id, v.vehicle_type.id, v.technology.id),
                            :,
                        ],
                    ) for v in vehicles if v.vehicle_type.mode.id == m.id
                ),
                " h_plus ",
                sum(
                    sum(
                        solved_h_plus[
                            y,
                            :,
                            (v.vehicle_type.mode.id, v.vehicle_type.id, v.technology.id),
                            :,
                        ],
                    ) for v in vehicles if v.vehicle_type.mode.id == m.id
                ),
                " h_minus ",
                sum(
                    sum(
                        solved_h_minus[
                            y,
                            :,
                            (v.vehicle_type.mode.id, v.vehicle_type.id, v.technology.id),
                            :,
                        ],
                    ) for v in vehicles if v.vehicle_type.mode.id == m.id
                ),
                " h_exist ",
                sum(
                    sum(
                        solved_h_exist[
                            y,
                            :,
                            (v.vehicle_type.mode.id, v.vehicle_type.id, v.technology.id),
                            :,
                        ],
                    ) for v in vehicles if v.vehicle_type.mode.id == m.id
                ),
                " f in year ",
                sum(
                    sum(
                        solved_f[
                            y,
                            :,
                            (
                                p.id,
                                v.vehicle_type.mode.id,
                                v.vehicle_type.id,
                                v.technology.id,
                            ),
                            :,
                            :,
                        ],
                    ) for v in vehicles for
                    p in v.products if v.vehicle_type.mode.id == m.id
                ),
            )
        end
    end
end

mode_ = Dict(
    "id" => Mode.id,
    "name" => vehicle.name,
    "mode" => Dict("name" => vehicle.mode.name, "speed" => vehicle.mode.speed),
)
