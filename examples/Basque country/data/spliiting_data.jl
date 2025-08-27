using YAML

# Path to your big YAML file
input_path = "examples/Basque country/data/basque_country_input.yaml"

# Load the YAML file
data = YAML.load_file(input_path)

# Output directory for split files
output_dir = "examples/Basque country/data/split/"

# Create output directory if it doesn't exist
isdir(output_dir) || mkdir(output_dir)

# Write each top-level key to its own YAML file
for (key, value) in data
    println(key)
    out_file = joinpath(output_dir, string(key, ".yaml"))
    YAML.write_file(out_file, Dict(key => value))
    println("done")
end

println("Splitting complete!")