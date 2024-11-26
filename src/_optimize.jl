println("Running the program ...")

using JuMP, Gurobi
include("_functions.jl")

# preliminary parametrization
Y = 2 # year 
R = 1 # origin-destination pair
K = 1 # connection between an origin-destination pair
T = 1 # technology
G = 1 # vehicle generation
N = 3 # node 
E = 2 # edge

y_vec = collect(1:Y)
r_vec = collect(1:R)
k_vec = collect(1:K)
t_vec = collect(1:T)
n_vec = collect(1:N)
g_vec = collect(1:G)

# subsets 
K_r = Dict(1 => [1])

# geometries
nodes = Set([1, 2, 3])
edges = Set([4, 5])

# routes
route = Dict(1 => [1, 4, 5, 3])

# parameters
F = Dict((1, 1) => 2000, (2, 1) => 2000) # y, r 
L_node_edges =
    Dict((1, 1) => 200, (2, 1) => 200, (3, 1) => 200, (4, 1) => 5000, (5, 1) => 5000) # (e/n)k; route length within a note 
W = Dict((1, 1) => 10.63) # t, g 
L_a = Dict((1, 1) => 1200000) # t, g
alpha = 0.5
beta = 0.5
h_init = Dict((1, 1, 1) => 1) # rtg

# cost parameters
c_transport = Dict((1, 1, 1, 1) => 10, (2, 1, 1, 1) => 10) # yktg
c_h = Dict((1, 1, 1) => 2, (2, 1, 1) => 2) # ytg 

# model initialization
model = Model(Gurobi.Optimizer)

# add the dimensions
# initializing sets 
yktg_set = generate_yktg(y_vec, k_vec, t_vec, g_vec)
yrtg_set = generate_yrtg(y_vec, r_vec, t_vec, g_vec)
yr_set = generate_yr(y_vec, r_vec)
rtg_set = generate_rtg(r_vec, t_vec, g_vec)
later_yrtg_set = generate_later_yrtg(y_vec, r_vec, t_vec, g_vec)

# setting decision variables 
@variable(model, f[yktg_set] >= 0)
@variable(model, h[yrtg_set] >= 0)
@variable(model, h_plus[yrtg_set] >= 0)
@variable(model, h_minus[yrtg_set] >= 0)

# setting constraints
# constraint for demand coverage 
@constraint(
    model,
    [subset in yr_set],
    sum(f[(subset[1], k, t, g)] for k ∈ K_r[subset[2]] for g ∈ g_vec for t ∈ t_vec) ==
    F[(subset[1], subset[2])]
)

# ----
# vehicle fleet constraints
# ---
@constraint(
    model,
    [subset in yrtg_set],
    h[subset] >= sum(
        (
            sum(L_node_edges[(route_element, k)] for route_element ∈ route[k]) /
            (W[(subset[3], subset[4])] * L_a[(subset[3], subset[4])])
        ) * f[(subset[1], k, subset[3], subset[4])] for k ∈ K_r[subset[2]]
    )
)
# t = 1
@constraint(
    model,
    [subset in rtg_set],
    h[(1, subset[1], subset[2], subset[3])] ==
    h_init[subset] + h_plus[(1, subset[1], subset[2], subset[3])] -
    h_minus[(1, subset[1], subset[2], subset[3])]
)
# t > 1
@constraint(
    model,
    [subset in later_yrtg_set],
    h[subset] ==
    h[(subset[1] - 1, subset[2], subset[3], subset[4])] + h_plus[subset] - h_minus[subset]
)

# ---
# objective
# ---
@objective(
    model,
    Min,
    sum(c_transport[subset] * f[subset] for subset ∈ yktg_set) +
    sum(h_plus[subset] * c_h[(subset[1], subset[3], subset[4])] for subset ∈ yrtg_set)
)

# ---
# solution
# ---
optimize!(model)
solution_summary(model)
