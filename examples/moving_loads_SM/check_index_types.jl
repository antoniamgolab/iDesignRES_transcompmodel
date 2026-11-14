# Quick check of index types for h, f, and s variables

using Pkg
Pkg.activate(joinpath(@__DIR__, "../.."))

using YAML, JuMP, Gurobi

include(joinpath(@__DIR__, "../../src/TransComp.jl"))
using .TransComp

# Load data
folder = "case_20251107_214315_uni_uni"
input_path = joinpath(@__DIR__, "input_data", folder)
data_dict = get_input_data(input_path)
data_structures = parse_data(data_dict)

# Create model
relevant_vars = ["f", "h", "s"]
model, data_structures = create_model(data_structures, "test_idx", include_vars=relevant_vars)

println("\n" * "=" ^ 80)
println("INDEX TYPE ANALYSIS")
println("=" ^ 80)

# Check h variable
h_dict = model[:h]
h_first_idx = first(eachindex(h_dict))
println("\nh variable:")
println("  First index type: $(typeof(h_first_idx))")
println("  First index value: $h_first_idx")
println("  h_first_idx[1]: $(h_first_idx[1]) (type: $(typeof(h_first_idx[1])))")

# Check f variable
f_dict = model[:f]
f_first_idx = first(eachindex(f_dict))
println("\nf variable:")
println("  First index type: $(typeof(f_first_idx))")
println("  First index value: $f_first_idx")
println("  f_first_idx[1]: $(f_first_idx[1]) (type: $(typeof(f_first_idx[1])))")

# Check s variable
s_dict = model[:s]
s_first_idx = first(eachindex(s_dict))
println("\ns variable:")
println("  First index type: $(typeof(s_first_idx))")
println("  First index value: $s_first_idx")
println("  s_first_idx[1]: $(s_first_idx[1]) (type: $(typeof(s_first_idx[1])))")

# Show modeled_years for reference
modeled_years = data_structures["modeled_years"]
println("\nmodeled_years: $modeled_years")

println("\n" * "=" ^ 80)
