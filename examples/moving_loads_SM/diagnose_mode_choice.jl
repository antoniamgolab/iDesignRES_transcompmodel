# Diagnostic script to understand why model chooses rail over road
# despite road having lower cost_per_ukm

using YAML

# Load input data
input_path = joinpath(@__DIR__, "input_data", "case_20251102_093733")

println("="^80)
println("DIAGNOSTIC: Why is model choosing rail over road?")
println("="^80)

# Load Mode.yaml
modes_data = YAML.load_file(joinpath(input_path, "Mode.yaml"))
println("\nMODE COSTS:")
for mode in modes_data
    println("  Mode $(mode["id"]) ($(mode["name"])):")
    println("    quantify_by_vehs: $(mode["quantify_by_vehs"])")
    println("    cost_per_ukm (first year): $(mode["costs_per_ukm"][1])")
    println("    waiting_time (first year): $(mode["waiting_time"][1])")
end

# Load Vehicletype.yaml
veh_data = YAML.load_file(joinpath(input_path, "Vehicletype.yaml"))
println("\nVEHICLE TYPES:")
for veh in veh_data
    veh_id = veh["id"]
    veh_name = veh["name"]
    veh_mode = veh["mode"]
    veh_product = veh["product"]
    println("  Vehicle $veh_id ($veh_name):")
    println("    mode: $veh_mode")
    println("    product: $veh_product")
end

# Load TechVehicle.yaml
tech_data = YAML.load_file(joinpath(input_path, "TechVehicle.yaml"))
println("\nTECH VEHICLES:")
for tv in tech_data
    tv_id = tv["id"]
    tv_name = tv["name"]
    tv_veh_type = tv["vehicle_type"]
    println("  TechVehicle $tv_id ($tv_name):")
    println("    vehicle_type: $tv_veh_type")
end

# Load Path.yaml (sample first few paths)
paths_data = YAML.load_file(joinpath(input_path, "Path.yaml"))
println("\nPATH SAMPLE (first 3 paths):")
for (i, path) in enumerate(paths_data[1:min(3, length(paths_data))])
    p_id = path["id"]
    p_odpair = path["odpair"]
    p_mode = path["mode"]
    p_length = path["route_length"]
    println("  Path $p_id:")
    println("    odpair: $p_odpair")
    println("    mode: $p_mode")
    println("    route_length: $p_length km")
end

# Check if paths are mode-specific
println("\nPATH MODE DISTRIBUTION:")
mode_counts = Dict{Int, Int}()
for path in paths_data
    mode_id = path["mode"]
    mode_counts[mode_id] = get(mode_counts, mode_id, 0) + 1
end
for (mode_id, count) in sort(collect(mode_counts))
    println("  Mode $mode_id: $count paths")
end

println("\n" * "="^80)
println("ANALYSIS:")
println("="^80)

# Calculate expected costs for a 1000 km trip with 1000 tkm
road_cost_per_ukm = modes_data[1]["costs_per_ukm"][1]
rail_cost_per_ukm = modes_data[2]["costs_per_ukm"][1]
road_waiting = modes_data[1]["waiting_time"][1]
rail_waiting = modes_data[2]["waiting_time"][1]
vot = 30.0  # EUR/hour (from FinancialStatus)

distance_km = 1000
demand_tkm = 1000

road_levelized = road_cost_per_ukm * demand_tkm
road_waiting_cost = road_waiting * vot
road_total = road_levelized + road_waiting_cost

rail_levelized = rail_cost_per_ukm * demand_tkm
rail_waiting_cost = rail_waiting * vot
rail_total = rail_levelized + rail_waiting_cost

println("For $distance_km km trip with $demand_tkm tkm:")
println("\nROAD MODE:")
println("  Levelized cost: $road_cost_per_ukm EUR/tkm × $demand_tkm tkm = €$(road_levelized)")
println("  Waiting time cost: $road_waiting h × €$vot/h = €$(road_waiting_cost)")
println("  TOTAL: €$(road_total)")

println("\nRAIL MODE:")
println("  Levelized cost: $rail_cost_per_ukm EUR/tkm × $demand_tkm tkm = €$(rail_levelized)")
println("  Waiting time cost: $rail_waiting h × €$vot/h = €$(rail_waiting_cost)")
println("  TOTAL: €$(rail_total)")

println("\nCOST DIFFERENCE:")
if road_total < rail_total
    println("  Road is cheaper by €$(rail_total - road_total) (road should be chosen)")
else
    println("  Rail is cheaper by €$(road_total - rail_total) (rail should be chosen)")
end

println("\n" * "="^80)
println("POSSIBLE REASONS FOR RAIL BEING CHOSEN:")
println("="^80)
println("1. Check if paths are mode-specific (each OD-pair might have separate road/rail paths)")
println("2. Check if rail paths have shorter route_length than road paths")
println("3. Check if there are constraints forcing rail (e.g., max_mode_share)")
println("4. Check if objective function is actually using cost_per_ukm for both modes")
println("="^80)
