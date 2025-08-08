using YAML, JuMP, Gurobi, Printf, ProgressMeter

include(joinpath(@__DIR__, "../../src/TransComp.jl"))

# reading input data
# Get the path to the YAML file

using .TransComp

script_dir = @__DIR__   # Directory of the current script
yaml_file_path = normpath(joinpath(@__DIR__, "data/transport_data_v1_ONENODE_concentrated_cut_demand.yaml"))
println("Constructed file path: $yaml_file_path")

using Dates

timestamp = Dates.format(now(), "yyyy-mm-dd_HH-MM-SS")
case = "cs_$timestamp"

file = yaml_file_path
@info file

# reading input data and initializing the model
@info "Initialization ..."
data_dict = get_input_data(file)
data_structures = parse_data(data_dict)
model, data_structures = create_model(data_structures, case)
@info "Model created successfully"

# -------- constraints --------
# constraint_q_fuel_fossil(model, data_structures) # this makes the model infeasible
# @info "Constraint for fossil fuel created successfully"
# constraint_to_fast_charging(model, data_structures)
constraint_fueling_infrastructure_expansion_shift(model, data_structures)
@info "Constraint for fueling infrastructure expansion and shift created successfully"
constraint_q_fuel_abs(model, data_structures)

constraint_slow_fast_expansion(model, data_structures)
# @info "Constraint for slow and fast expansion created successfully"

constraint_trip_ratio(model, data_structures)
@info "Constraint for trip ratio created successfully"

constraint_policy_goal(model, data_structures)
@info "Constraint for policy goal created successfully"

# constraint_mode_infrastructure(model, data_structures)
# @info "Constraint for mode infrastructure created successfully"
# constraint_maximum_fueling_infrastructure_by_year(model, data_structures)
# @info "Constraint for maximum fueling infrastructure by year created successfully"
constraint_maximum_fueling_infrastructure(model, data_structures)

@info "Constraint for maximum fueling infrastructure created successfully"

constraint_monetary_budget(model, data_structures)
@info "Policy related constraints created successfully"

constraint_fueling_infrastructure(model, data_structures)
@info "Constraint for fueling infrastructure created successfully"

constraint_demand_coverage(model, data_structures)
@info "Constraint for demand coverage created successfully"

constraint_vehicle_sizing(model, data_structures)
@info "Constraint for vehicle stock sizing created successfully"

constraint_vehicle_aging(model, data_structures)
@info "Constraint for vehicle aging created successfully"

constraint_fueling_demand(model, data_structures)
@info "Constraint for fueling demand created successfully"

constraint_vehicle_stock_shift(model, data_structures)

@info "Constraint for vehicle stock shift created successfully"

constraint_vehicle_stock_shift_vehicle_type(model, data_structures)

@info "Constraint for vehicle stock shift by vehicle type created successfully"

# # constraint_mode_shift(model, data_structures)
# # @info "Constraint for mode shift created successfully"

constraint_market_share(model, data_structures)
@info "Constraint for market share created successfully"

# optimize!(model)

# # -------- constraints (alternative) --------
if data_structures["detour_time_reduction_list"] != []

    constraint_detour_time(model, data_structures)
    # constraint_n_fueling_upper_bound(model, data_structures)
    # constraint_detour_time_capacity_reduction(model, data_structures)

    constraint_def_n_fueling(model, data_structures)

    constraint_sum_x(model, data_structures) 

    constraint_vot_dt(model, data_structures)
    @info "Constraint for VOT and detour time created successfully"

#     # constraint_def_n_fueling(model, data_structures)
#     @info "Detour time reduction constraint is added"
end 
# find_large_rhs(model)
@info "Constraints created successfully"                

# -------- objective --------
objective(model, data_structures)
@info "Objective function added successfully"

# -------- model solution and saving of results --------
# set_optimizer_attribute(model, "ScaleFlag", 2)
set_optimizer_attribute(model, "Presolve", 2)
# set_optimizer_attribute(model, "Crossover", 0)
set_optimizer_attribute(model, "MIPFocus", 1) 
set_optimizer_attribute(model, "Cuts", 3) 
set_optimizer_attribute(model, "MIPGap", 0.024)
set_optimizer_attribute(model, "NumericFocus", 1)
set_optimizer_attribute(model, "NoRelHeurWork", 600)
# set_optimizer_attribute(model, "NoRelHeurTime", 3600 * 1)

set_optimizer_attribute(model, "Heuristics", 1)
set_optimizer_attribute(model, "PreSparsify", 0)
set_optimizer_attribute(model, "FeasibilityTol", 1e-4) # or 1e-4
set_optimizer_attribute(model, "Threads", 11)
set_optimizer_attribute(model, "NodefileStart", 50) # 0.5 GB node file size
set_optimizer_attribute(model, "TimeLimit", 3600 * 30) # 1 hour time limit
set_optimizer_attribute(model, "PreSOS1BigM", 0)
set_optimizer_attribute(model, "ScaleFlag", 2)
#set_optimizer_attribute(model, "ImproveStartGap", 0.1)    # Only after <10% gap

println("Solution .... ")
optimize!(model)
solution_summary(model)

results_file_path = normpath(joinpath(@__DIR__, "results/"))
save_results(model, case, data_structures, true, results_file_path)
# output_ = disagreggate(model, data_structures, 2, 2040)
# println(output_)
@info "Results saved successfully"
@info "Model solved successfully"
