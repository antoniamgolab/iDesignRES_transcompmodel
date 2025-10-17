using YAML, JuMP, Gurobi, Printf

include(joinpath(@__DIR__, "../../src/TransComp.jl"))
using .TransComp

# Load and parse data
println("Loading input data...")
input_path = joinpath(@__DIR__, "input_data", "case_20251015_174932")
data_dict = get_input_data(input_path)

println("\n" * "="^80)
println("PARSING DATA")
println("="^80)

data_structures = parse_data(data_dict)

println("\nParsing complete!")
println("Number of odpairs parsed: ", length(data_structures["odpair_list"]))
println("Number of paths parsed: ", length(data_structures["path_list"]))

# Check the first few odpairs
println("\n" * "="^80)
println("SAMPLE ODPAIRS (first 5)")
println("="^80)

for (i, odpair) in enumerate(data_structures["odpair_list"][1:min(5, length(data_structures["odpair_list"]))])
    println("\nOD-pair $i:")
    println("  ID: ", odpair.id)
    println("  Origin: ", odpair.origin.id, " (", odpair.origin.name, ")")
    println("  Destination: ", odpair.destination.id, " (", odpair.destination.name, ")")
    println("  Product: ", odpair.product.name)
    println("  Financial status: ", odpair.financial_status.name)
    println("  Number of paths: ", length(odpair.paths))
    if length(odpair.paths) > 0
        println("  Path IDs: ", [p.id for p in odpair.paths])
        println("  Path lengths: ", [p.length for p in odpair.paths])
    else
        println("  WARNING: NO PATHS!")
    end
    println("  Demand (F) - first 3 years: ", odpair.F[1:min(3, length(odpair.F))])
end

# Check if ALL odpairs have paths
println("\n" * "="^80)
println("PATH AVAILABILITY CHECK")
println("="^80)

odpairs_with_paths = sum(1 for odpair in data_structures["odpair_list"] if length(odpair.paths) > 0)
odpairs_without_paths = sum(1 for odpair in data_structures["odpair_list"] if length(odpair.paths) == 0)

println("OD-pairs WITH paths: $odpairs_with_paths")
println("OD-pairs WITHOUT paths: $odpairs_without_paths")

if odpairs_without_paths > 0
    println("\n✗ PROBLEM FOUND: Some OD-pairs have no paths!")
    println("This will cause infeasibility in the demand coverage constraint")
else
    println("\n✓ All OD-pairs have paths")
end

# Check path list details
println("\n" * "="^80)
println("PATH LIST SAMPLE (first 5)")
println("="^80)

for (i, path) in enumerate(data_structures["path_list"][1:min(5, length(data_structures["path_list"]))])
    println("\nPath $i:")
    println("  ID: ", path.id)
    println("  Name: ", path.name)
    println("  Length: ", path.length)
    println("  Sequence length: ", length(path.sequence))
    println("  Sequence: ", [geo.id for geo in path.sequence])
end

println("\n" * "="^80)
println("DIAGNOSIS COMPLETE")
println("="^80)
