"""
Diagnostic Script: Check Modal Shift Constraint Feasibility
============================================================

This script checks if constraint_mode_shift is causing infeasibility by:
1. Examining initial mode distribution
2. Calculating maximum allowed shift per time period
3. Identifying potential conflicts
"""

using YAML

# Load input data
script_dir = @__DIR__
folder = "case_20251030_142356"
input_path = joinpath(script_dir, "input_data", folder)

println("="^80)
println("MODAL SHIFT DIAGNOSTIC")
println("="^80)
println("Input: $folder")
println()

# Load Model parameters
model_params = YAML.load_file(joinpath(input_path, "Model.yaml"))
alpha_f = model_params["alpha_f"]
beta_f = model_params["beta_f"]
y_init = model_params["y_init"]
time_step = model_params["time_step"]

println("Model Parameters:")
println("  y_init: $y_init")
println("  time_step: $time_step")
println("  alpha_f: $alpha_f (max shift as % of total flow)")
println("  beta_f: $beta_f (max shift as % of previous mode flow)")
println()

# Load modes
modes = YAML.load_file(joinpath(input_path, "Mode.yaml"))
println("Modes Defined:")
for m in modes
    println("  - ID $(m["id"]): $(m["name"]) (quantify_by_vehs=$(m["quantify_by_vehs"]))")
end
println()

# Load OD-pairs to check demand
odpairs = YAML.load_file(joinpath(input_path, "Odpair.yaml"))
total_demand_y_init = sum(od["F"][1] for od in odpairs)  # F[1] is year y_init
println("Total Demand at y_init ($y_init): $(round(total_demand_y_init, digits=2))")
println()

# Check initial vehicle stock distribution by mode
if isfile(joinpath(input_path, "InitialVehicleStock.yaml"))
    init_stock = YAML.load_file(joinpath(input_path, "InitialVehicleStock.yaml"))

    # Count by techvehicle (0=ICEV road, 1=BEV road, others=rail/non-vehicle modes)
    stock_by_tech = Dict{Int, Float64}()
    for entry in init_stock
        tech_id = entry["techvehicle"]
        stock = get(entry, "stock", 0.0)
        stock_by_tech[tech_id] = get(stock_by_tech, tech_id, 0.0) + stock
    end

    println("Initial Vehicle Stock Distribution:")
    for (tech_id, stock) in sort(collect(stock_by_tech))
        println("  TechVehicle $tech_id: $(round(stock, digits=2)) vehicles")
    end
    println()
end

# Calculate maximum shift allowed in first period
first_modeled_year = y_init + time_step
max_shift_first_period = alpha_f * total_demand_y_init + beta_f * 0  # Assuming rail starts at 0
max_shift_pct = max_shift_first_period / total_demand_y_init * 100

println("="^80)
println("CONSTRAINT ANALYSIS")
println("="^80)
println("In year $first_modeled_year (first period after y_init):")
println()
println("Maximum flow shift to rail mode:")
println("  Δf_rail ≤ α_f × total_flow + β_f × f_rail[$y_init]")
println("  Δf_rail ≤ $alpha_f × $(round(total_demand_y_init, digits=2)) + $beta_f × 0")
println("  Δf_rail ≤ $(round(max_shift_first_period, digits=2))")
println("  Δf_rail ≤ $(round(max_shift_pct, digits=2))% of total demand")
println()

if max_shift_pct < 30  # Assuming MaxModeShare caps rail at 30%
    println("⚠️  POTENTIAL ISSUE DETECTED:")
    println("   - Rail mode can only capture $(round(max_shift_pct, digits=1))% of demand in first period")
    println("   - This may conflict with other constraints if rail becomes attractive")
    println("   - Consider: Increasing alpha_f/beta_f OR disabling constraint_mode_shift")
else
    println("✓  Modal shift constraint appears reasonable")
    println("   - Rail can capture up to $(round(max_shift_pct, digits=1))% in first period")
end
println()

println("="^80)
println("RECOMMENDATIONS")
println("="^80)
println("1. If infeasibility occurs, try commenting out constraint_mode_shift in SM.jl")
println("2. Or increase alpha_f and beta_f to 0.5 in Model.yaml")
println("3. Or remove rail mode if not needed for your analysis")
println("="^80)
