using JuMP, Gurobi
include("_functions.jl")

# preliminary parametrization
R = 1 # origin-destination pair
K = 1 # connection between an origin-destination pair
T = 1 # technology
N = 1 # node 
G = 1 # vehicle generation

# subsets 
K_r = Dict(1 => [1])

# parameters
F = [2000] # r 
L_node = [20] # nk; route length within a note 
W = [10.63] # t 
L_a = [120000]
alpha = 0.5
beta = 0.5

# cost parameters


model = Model(Gurobi.Optimizer)

# setting decision variables 
@variable(model, f[1:K, 1:T. 1:G] => 0)
@variable(model, h[1:R, 1:T, 1:G] => 0)
@variable(model, h_plus[1:R, 1:T, 1:G] => 0)
@variable(model, h_minus[1:R, 1:T, 1:G] => 0)

# setting constraints
@constraint(model, )



set_attribute(model, "TimeLimit", 100)

# @variable(model, x >= 0)
# @variable(model, 0 <= y <= 3)
# @objective(model, Min, 12x + 20y)
# @constraint(model, c1, 6x + 8y >= 100)
# @constraint(model, c2, 7x + 12y >= 120)
# print(model)



