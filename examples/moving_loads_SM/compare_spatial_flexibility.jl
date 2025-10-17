"""
Comparison script to demonstrate the difference between:
1. Model WITH spatial_flexibility constraint
2. Model WITHOUT spatial_flexibility constraint

This script will show how spatial_flexibility affects the geographic distribution
of charging infrastructure usage.
"""

using YAML, JuMP, Gurobi, Printf, Dates

include(joinpath(@__DIR__, "../../src/TransComp.jl"))
using .TransComp

println("="^80)
println("SPATIAL FLEXIBILITY CONSTRAINT COMPARISON")
println("="^80)
println()

# Setup
script_dir = @__DIR__
folder = "case_1_20251010_143600"
input_path = joinpath(@__DIR__, "input_data\\", folder)
relevant_vars = ["f", "h", "h_plus", "h_exist", "h_minus", "s", "q_fuel_infr_plus", "soc", "travel_time", "extra_break_time"]

println("Input path: $input_path")
println()

# Read and parse data (shared for both runs)
@info "Loading input data..."
data_dict = get_input_data(input_path)
data_structures = parse_data(data_dict)

# Extract key data for analysis
y_init = data_structures["y_init"]
Y_end = data_structures["Y_end"]
g_init = data_structures["g_init"]
odpairs = data_structures["odpair_list"]
techvehicle_list = data_structures["techvehicle_list"]
path_list = data_structures["path_list"]
product_list = data_structures["product_list"]
f_l_pairs = data_structures["f_l_not_by_route"]
spatial_flex_edges = data_structures["spatial_flexibility_edges_list"]

println("Model dimensions:")
println("  Years: $y_init to $Y_end")
println("  Paths: $(length(path_list))")
println("  OD pairs: $(length(odpairs))")
println("  Tech vehicles: $(length(techvehicle_list))")
println("  Spatial flexibility regions: $(length(spatial_flex_edges))")
println()

# ============================================================================
# RUN 1: WITHOUT spatial_flexibility constraint
# ============================================================================

println("="^80)
println("RUN 1: WITHOUT spatial_flexibility constraint")
println("="^80)
println()

timestamp1 = Dates.format(now(), "yyyy-mm-dd_HH-MM-SS")
case1 = "$(folder)_NO_spatial_flex_$timestamp1"

@info "Creating model WITHOUT spatial_flexibility..."
model1, data_structures1 = create_model(data_structures, case1, include_vars=relevant_vars)

# Add all constraints EXCEPT spatial_flexibility
@info "Adding constraints..."
constraint_demand_coverage(model1, data_structures1)
constraint_vehicle_sizing(model1, data_structures1)
constraint_vehicle_aging(model1, data_structures1)
constraint_fueling_demand(model1, data_structures1)
constraint_fueling_infrastructure(model1, data_structures1)
constraint_vehicle_stock_shift(model1, data_structures1)
constraint_fueling_infrastructure_expansion_shift(model1, data_structures1)
constraint_travel_time_track(model1, data_structures1)
constraint_mandatory_breaks(model1, data_structures1)
constraint_soc_track(model1, data_structures1)
constraint_soc_max(model1, data_structures1)
# NOTE: spatial_flexibility is NOT added here

@info "Adding objective..."
objective(model1, data_structures1, false)

@info "Solving model 1..."
set_optimizer_attribute(model1, "TimeLimit", 3600)  # 1 hour limit
set_optimizer_attribute(model1, "MIPGap", 0.01)  # 1% gap for faster solve
optimize!(model1)

status1 = termination_status(model1)
@info "Model 1 status: $status1"

if status1 in [MOI.OPTIMAL, MOI.LOCALLY_SOLVED, MOI.TIME_LIMIT]
    obj1 = objective_value(model1)
    println("  Objective value: $(round(obj1, digits=2))")
    println()
end

# ============================================================================
# RUN 2: WITH spatial_flexibility constraint
# ============================================================================

println("="^80)
println("RUN 2: WITH spatial_flexibility constraint")
println("="^80)
println()

timestamp2 = Dates.format(now(), "yyyy-mm-dd_HH-MM-SS")
case2 = "$(folder)_WITH_spatial_flex_$timestamp2"

@info "Creating model WITH spatial_flexibility..."
model2, data_structures2 = create_model(data_structures, case2, include_vars=relevant_vars)

# Add all constraints INCLUDING spatial_flexibility
@info "Adding constraints..."
constraint_demand_coverage(model2, data_structures2)
constraint_vehicle_sizing(model2, data_structures2)
constraint_vehicle_aging(model2, data_structures2)
constraint_fueling_demand(model2, data_structures2)
constraint_fueling_infrastructure(model2, data_structures2)
constraint_vehicle_stock_shift(model2, data_structures2)
constraint_fueling_infrastructure_expansion_shift(model2, data_structures2)
constraint_travel_time_track(model2, data_structures2)
constraint_mandatory_breaks(model2, data_structures2)
constraint_soc_track(model2, data_structures2)
constraint_soc_max(model2, data_structures2)
constraint_spatial_flexibility(model2, data_structures2)  # ← ADDED HERE

@info "Adding objective..."
objective(model2, data_structures2, false)

@info "Solving model 2..."
set_optimizer_attribute(model2, "TimeLimit", 3600)  # 1 hour limit
set_optimizer_attribute(model2, "MIPGap", 0.01)  # 1% gap for faster solve
optimize!(model2)

status2 = termination_status(model2)
@info "Model 2 status: $status2"

if status2 in [MOI.OPTIMAL, MOI.LOCALLY_SOLVED, MOI.TIME_LIMIT]
    obj2 = objective_value(model2)
    println("  Objective value: $(round(obj2, digits=2))")
    println()
end

# ============================================================================
# COMPARISON ANALYSIS
# ============================================================================

println("="^80)
println("COMPARATIVE ANALYSIS")
println("="^80)
println()

# Check if both models solved
if !(status1 in [MOI.OPTIMAL, MOI.LOCALLY_SOLVED, MOI.TIME_LIMIT]) ||
   !(status2 in [MOI.OPTIMAL, MOI.LOCALLY_SOLVED, MOI.TIME_LIMIT])
    @warn "One or both models did not solve successfully. Skipping comparison."
    exit(0)
end

# Focus on a single test year for comparison
test_year = 2030

println("Analyzing year $test_year:")
println()

# Function to analyze charging distribution for a model
function analyze_charging_distribution(model, data_structures, model_name)
    println("─"^80)
    println("$model_name: Charging Distribution")
    println("─"^80)

    charging_by_path = Dict()
    charging_by_node = Dict()

    # Collect all charging values
    for path in path_list
        path_id = path.id
        charging_by_path[path_id] = Dict()

        for geo in path.sequence
            geo_id = geo.id
            node_key = (path_id, geo_id)
            charging_by_node[node_key] = 0.0

            for odpair in odpairs
                if path in odpair.paths
                    p = odpair.product
                    for tv in techvehicle_list
                        for f_l in f_l_pairs
                            if tv.technology.fuel.id == f_l[1]
                                for g in g_init:test_year
                                    key = (test_year, (p.id, odpair.id, path_id, geo_id), tv.id, f_l, g)
                                    try
                                        charging_val = value(model[:s][key...])
                                        if charging_val > 1e-6
                                            charging_by_node[node_key] += charging_val
                                        end
                                    catch
                                        # Key doesn't exist, skip
                                    end
                                end
                            end
                        end
                    end
                end
            end
        end
    end

    # Sort and display results
    sorted_nodes = sort(collect(charging_by_node), by=x->x[2], rev=true)

    println("\nTop 20 charging locations (kWh):")
    println("  Rank | Path ID | Geo ID  | Charging (kWh)")
    println("  -----|---------|---------|---------------")

    total_charging = sum(values(charging_by_node))

    for (rank, ((path_id, geo_id), charging)) in enumerate(sorted_nodes[1:min(20, length(sorted_nodes))])
        if charging > 1e-6
            pct = 100 * charging / total_charging
            println("  $(lpad(rank, 4)) | $(lpad(path_id, 7)) | $(lpad(geo_id, 7)) | $(lpad(round(charging, digits=1), 13)) ($(round(pct, digits=1))%)")
        end
    end

    println("\nSummary:")
    println("  Total charging: $(round(total_charging, digits=1)) kWh")
    println("  Number of active nodes: $(count(x -> x > 1e-6, values(charging_by_node)))")

    # Calculate concentration metrics
    top5_charging = sum([x[2] for x in sorted_nodes[1:min(5, length(sorted_nodes))]])
    top10_charging = sum([x[2] for x in sorted_nodes[1:min(10, length(sorted_nodes))]])

    if total_charging > 0
        println("  Top 5 nodes concentration: $(round(100*top5_charging/total_charging, digits=1))%")
        println("  Top 10 nodes concentration: $(round(100*top10_charging/total_charging, digits=1))%")
    end

    println()

    return charging_by_node, total_charging
end

# Analyze both models
charging1, total1 = analyze_charging_distribution(model1, data_structures1, "Model 1 (NO spatial_flexibility)")
charging2, total2 = analyze_charging_distribution(model2, data_structures2, "Model 2 (WITH spatial_flexibility)")

# Compare the two distributions
println("="^80)
println("DIFFERENCE ANALYSIS")
println("="^80)
println()

println("Objective value comparison:")
if status1 in [MOI.OPTIMAL, MOI.LOCALLY_SOLVED, MOI.TIME_LIMIT] &&
   status2 in [MOI.OPTIMAL, MOI.LOCALLY_SOLVED, MOI.TIME_LIMIT]
    obj1 = objective_value(model1)
    obj2 = objective_value(model2)
    diff_pct = 100 * (obj2 - obj1) / obj1
    println("  Without spatial_flexibility: $(round(obj1, digits=2))")
    println("  With spatial_flexibility:    $(round(obj2, digits=2))")
    println("  Difference: $(round(obj2-obj1, digits=2)) ($(round(diff_pct, digits=2))%)")
    println()
end

println("Charging distribution comparison:")
println("  Nodes with charging changed: $(count(k -> abs(get(charging1, k, 0.0) - get(charging2, k, 0.0)) > 1e-3, union(keys(charging1), keys(charging2))))")
println()

# Find nodes with significant changes
println("Nodes with largest changes in charging (kWh):")
println("  Path ID | Geo ID  | Without SF | With SF | Difference")
println("  --------|---------|------------|---------|------------")

all_nodes = union(keys(charging1), keys(charging2))
changes = [(node, get(charging1, node, 0.0), get(charging2, node, 0.0),
            get(charging2, node, 0.0) - get(charging1, node, 0.0)) for node in all_nodes]
sorted_changes = sort(changes, by=x->abs(x[4]), rev=true)

for ((path_id, geo_id), val1, val2, diff) in sorted_changes[1:min(20, length(sorted_changes))]
    if abs(diff) > 1e-3
        println("  $(lpad(path_id, 7)) | $(lpad(geo_id, 7)) | $(lpad(round(val1, digits=1), 10)) | $(lpad(round(val2, digits=1), 7)) | $(lpad(round(diff, digits=1), 10))")
    end
end

println()
println("="^80)
println("CONCLUSIONS:")
println("="^80)
println()
println("If the charging distributions are DIFFERENT:")
println("  → spatial_flexibility constraint IS affecting the solution")
println("  → It redistributes charging geographically as intended")
println()
println("If the charging distributions are IDENTICAL:")
println("  → spatial_flexibility constraint is NOT binding in this case")
println("  → The optimizer already chose a spatially distributed solution")
println("  → Or the spatial flexibility regions are not active/relevant")
println()
println("="^80)
