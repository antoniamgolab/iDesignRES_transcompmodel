"""
Quick test to check debug logging in constraint_soc_track function.
This will load the model and add constraints without running optimization.
"""

using Pkg
Pkg.activate("../..")

using TransComp
using Gurobi
using JuMP

# Use var_var case
case_name = "case_20251110_160304_var_var"
input_dir = "input_data/$(case_name)"

println("\n" * "="^100)
println("DEBUG TEST: Checking if initial SOC constraint condition is working")
println("="^100)

println("\nLoading input data from directory: $input_dir")
yaml_data = get_input_data(input_dir)

println("Parsing data structures...")
data_structures = parse_data(yaml_data)

println("Creating base model with SOC variable...")
model, data_structures = create_model(data_structures, "test_debug", include_vars=["soc", "f"])

println("\nAdding SOC tracking constraint (this will trigger debug logging)...")
constraint_soc_track(model, yaml_data, data_structures)

println("\n" * "="^100)
println("TEST COMPLETE")
println("="^100)
println("\nCheck the output above for:")
println("  1. 'Initial SOC Constraint Debug' line showing origin_checks and origin_matches")
println("  2. 'Sample comparisons' showing (path_id, geo_id, origin_id, match?)")
println("\nIf origin_matches = 0, the condition is NEVER true and constraint is not applied!")
println("="^100)
