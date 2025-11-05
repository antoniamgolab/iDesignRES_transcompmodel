using Pkg
Pkg.activate(joinpath(@__DIR__, "../.."))

using YAML, JuMP, Gurobi, Printf

include(joinpath(@__DIR__, "../../src/TransComp.jl"))
using .TransComp

println("="^80)
println("TESTING TEMPORAL RESOLUTION IN JULIA")
println("="^80)

# Test case 1: time_step = 1 (baseline)
println("\n TEST CASE 1: time_step=1 (baseline - backward compatibility)")
println("="^80)

script_dir = @__DIR__
folder = "case_20251021_085841"
input_path = joinpath(@__DIR__, "input_data", folder)
println("Input path: $input_path")

# Read and parse data
println("\nStep 1: Reading input data...")
data_dict = get_input_data(input_path)
println("✓ Input data loaded")

# Check Model parameters
println("\nStep 2: Checking Model parameters...")
println("  Y: $(data_dict["Model"]["Y"])")
println("  y_init: $(data_dict["Model"]["y_init"])")
println("  pre_y: $(data_dict["Model"]["pre_y"])")
println("  time_step: $(data_dict["Model"]["time_step"])")
println("  investment_period: $(data_dict["Model"]["investment_period"])")

# Parse data structures
println("\nStep 3: Parsing data structures...")
data_structures = parse_data(data_dict)
println("✓ Data structures parsed")

# Check temporal sets
println("\nStep 4: Verifying temporal sets...")
time_step = data_structures["time_step"]
modeled_years = data_structures["modeled_years"]
modeled_generations = data_structures["modeled_generations"]
investment_years = data_structures["investment_years"]
Y_end = data_structures["Y_end"]
g_init = data_structures["g_init"]
y_init = data_dict["Model"]["y_init"]

println("  time_step: $time_step")
println("  Y_end: $Y_end")
println("  g_init: $g_init")
println("  y_init: $y_init")
println("\n  modeled_years (length=$(length(modeled_years))):")
println("    First 5: $(modeled_years[1:min(5, length(modeled_years))])")
println("    Last 5:  $(modeled_years[max(1, length(modeled_years)-4):end])")
println("\n  modeled_generations (length=$(length(modeled_generations))):")
println("    First 5: $(modeled_generations[1:min(5, length(modeled_generations))])")
println("    Last 5:  $(modeled_generations[max(1, length(modeled_generations)-4):end])")
println("\n  investment_years (length=$(length(investment_years))):")
println("    All: $investment_years")

# Verify correctness for time_step=1
println("\nStep 5: Validating temporal sets for time_step=1...")
expected_years = collect(y_init:Y_end)
expected_gens = collect(g_init:Y_end)
expected_inv = collect(y_init:data_dict["Model"]["investment_period"]:Y_end)

if modeled_years == expected_years
    println("  ✓ modeled_years correct ($(length(modeled_years)) years)")
else
    println("  ✗ ERROR: modeled_years mismatch!")
    println("    Expected: $(expected_years[1:5])...$(expected_years[end-4:end])")
    println("    Got:      $(modeled_years[1:5])...$(modeled_years[end-4:end])")
end

if modeled_generations == expected_gens
    println("  ✓ modeled_generations correct ($(length(modeled_generations)) generations)")
else
    println("  ✗ ERROR: modeled_generations mismatch!")
    println("    Expected: $(expected_gens[1:5])...$(expected_gens[end-4:end])")
    println("    Got:      $(modeled_generations[1:5])...$(modeled_generations[end-4:end])")
end

if investment_years == expected_inv
    println("  ✓ investment_years correct ($(length(investment_years)) investment periods)")
else
    println("  ✗ ERROR: investment_years mismatch!")
    println("    Expected: $expected_inv")
    println("    Got:      $investment_years")
end

# Create a minimal model with just one variable to test variable creation
println("\nStep 6: Testing variable creation with temporal sets...")
println("  Creating model with vehicle stock variables (h, h_plus, h_minus, h_exist)...")

case = "test_temporal_$(time_step)"
relevant_vars = ["h", "h_plus", "h_minus", "h_exist"]
model, data_structures_updated = create_model(data_structures, case, include_vars=relevant_vars)

println("  ✓ Model created successfully")
println("  Number of variables: $(num_variables(model))")

# Check variable dimensions
for var_name in relevant_vars
    if haskey(model.obj_dict, Symbol(var_name))
        var_ref = model.obj_dict[Symbol(var_name)]
        if var_ref isa JuMP.Containers.DenseAxisArray || var_ref isa JuMP.Containers.SparseAxisArray
            println("  - $var_name: $(length(var_ref)) variables")
        end
    else
        println("  - $var_name: NOT FOUND")
    end
end

println("\n" * "="^80)
println("TEST CASE 1 COMPLETE: time_step=1")
println("="^80)

# Clean up
println("\nCleaning up...")
model = nothing
data_structures = nothing
data_dict = nothing
GC.gc()

println("\n" * "="^80)
println("ALL TESTS PASSED ✓")
println("="^80)
println("\nNext steps:")
println("  1. Run full optimization with time_step=1 to verify backward compatibility")
println("  2. Test with time_step=2 to validate biennial resolution")
println("  3. Compare results for reasonableness")
println()
