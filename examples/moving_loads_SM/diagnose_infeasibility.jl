using YAML

# Load the input data
println("Loading input data...")
input_path = joinpath(@__DIR__, "input_data", "case_20251015_171650")

# Load Odpair to check demand
odpair_file = joinpath(input_path, "Odpair.yaml")
odpairs = YAML.load_file(odpair_file)

println("\n" * "="^80)
println("DEMAND ANALYSIS")
println("="^80)

# Check for zero or negative demand
println("\nTotal OD-pairs: ", length(odpairs))

zero_demand_count = 0
negative_demand_count = 0
positive_demand_count = 0
no_paths_count = 0

for odpair in odpairs
    F = odpair["F"]
    paths = get(odpair, "paths", [])

    has_zero = any(f -> f <= 0, F)
    has_negative = any(f -> f < 0, F)

    if length(paths) == 0
        global no_paths_count += 1
    end

    if has_zero
        global zero_demand_count += 1
    end
    if has_negative
        global negative_demand_count += 1
    end
    if all(f -> f > 0, F)
        global positive_demand_count += 1
    end
end

println("OD-pairs with all positive demand: $positive_demand_count")
println("OD-pairs with zero demand in at least one year: $zero_demand_count")
println("OD-pairs with negative demand: $negative_demand_count")
println("OD-pairs with no paths: $no_paths_count")

# Sample a few OD-pairs
println("\n" * "="^80)
println("SAMPLE OD-PAIRS (first 3)")
println("="^80)

for (i, odpair) in enumerate(odpairs[1:min(3, length(odpairs))])
    println("\nOD-pair $i:")
    println("  Origin: ", odpair["origin_node"])
    println("  Destination: ", odpair["destination_node"])
    println("  Product: ", odpair["product"])
    println("  Financial status: ", odpair["financial_status"])
    println("  Number of paths: ", length(get(odpair, "paths", [])))
    println("  Demand (F) - first 3 years: ", odpair["F"][1:min(3, length(odpair["F"]))])
    println("  Demand (F) - total years: ", length(odpair["F"]))
end

# Check Model parameters
println("\n" * "="^80)
println("MODEL PARAMETERS")
println("="^80)

model_file = joinpath(input_path, "Model.yaml")
model_params = YAML.load_file(model_file)

println("Y (years in horizon): ", model_params["Y"])
println("y_init (initial year): ", model_params["y_init"])
println("pre_y (years before): ", model_params["pre_y"])
println("Y_end would be: ", model_params["y_init"] + model_params["Y"])

# Check if F array length matches Y
println("\n" * "="^80)
println("DEMAND ARRAY LENGTH CHECK")
println("="^80)

for (i, odpair) in enumerate(odpairs[1:min(5, length(odpairs))])
    F_length = length(odpair["F"])
    Y = model_params["Y"]
    match = F_length == Y ? "✓" : "✗"
    println("OD-pair $i: F length = $F_length, Y = $Y $match")
end

# Check vehicle types
println("\n" * "="^80)
println("VEHICLE TYPES")
println("="^80)

vehicletype_file = joinpath(input_path, "Vehicletype.yaml")
vehicletypes = YAML.load_file(vehicletype_file)

println("Number of vehicle types: ", length(vehicletypes))
for vtype in vehicletypes
    println("  ID: ", vtype["id"], ", Name: ", vtype["name"], ", Mode: ", vtype["mode"], ", Product: ", vtype["product"])
end

# Check tech vehicles
println("\n" * "="^80)
println("TECH VEHICLES")
println("="^80)

techvehicle_file = joinpath(input_path, "TechVehicle.yaml")
techvehicles = YAML.load_file(techvehicle_file)

println("Number of tech vehicles: ", length(techvehicles))
for tv in techvehicles
    println("  ID: ", tv["id"], ", Name: ", tv["name"], ", Technology: ", tv["technology"], ", VehicleType: ", tv["vehicle_type"])
    println("    Products: ", tv["products"])
end

println("\n" * "="^80)
println("DIAGNOSIS COMPLETE")
println("="^80)
