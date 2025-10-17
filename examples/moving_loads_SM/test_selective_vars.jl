using YAML, JuMP, Gurobi

include(joinpath(@__DIR__, "../../src/TransComp.jl"))
using .TransComp

# Get input data
input_path = joinpath(@__DIR__, "input_data", "case_1_20251002_135149")
println("Loading data from: $input_path")

# Read and parse data
data_dict = get_input_data(input_path)
data_structures = parse_data(data_dict)

# Test 1: Create model with ALL variables (default)
println("\n" * "="^80)
println("TEST 1: Creating model with ALL variables (default)")
println("="^80)
model_all, ds_all = create_model(data_structures, "test_all")
println("\nVariables in model:")
for (name, var) in model_all.obj_dict
    if var isa VariableRef || var isa Array{<:VariableRef}
        println("  - $name")
    end
end

# Test 2: Create model with ONLY f, h, s variables
println("\n" * "="^80)
println("TEST 2: Creating model with SELECTIVE variables (f, h, s)")
println("="^80)
model_selective, ds_selective = create_model(data_structures, "test_selective", include_vars=["f", "h", "s"])
println("\nVariables in model:")
for (name, var) in model_selective.obj_dict
    if var isa VariableRef || var isa Array{<:VariableRef}
        println("  - $name")
    end
end

println("\n" * "="^80)
println("COMPARISON:")
println("="^80)
all_vars = [String(name) for (name, var) in model_all.obj_dict if var isa VariableRef || var isa Array{<:VariableRef}]
selective_vars = [String(name) for (name, var) in model_selective.obj_dict if var isa VariableRef || var isa Array{<:VariableRef}]

println("Total variables in ALL mode: $(length(all_vars))")
println("Total variables in SELECTIVE mode: $(length(selective_vars))")
println("\nVariables SKIPPED in selective mode:")
for v in setdiff(all_vars, selective_vars)
    println("  - $v")
end
