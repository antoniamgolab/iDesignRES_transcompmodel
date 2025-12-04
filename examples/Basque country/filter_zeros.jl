"""
Filter out zero values from YAML result files
"""

using YAML

# Configuration
RESULTS_FOLDER = "results/cs_2025-09-24_11-03-29"

# List of files to process
FILES_TO_FILTER = [
    "f_dict.yaml",
    "h_dict.yaml",
    "h_exist_dict.yaml",
    "h_plus_dict.yaml",
    "h_minus_dict.yaml",
    "q_mode_infr_plus_dict.yaml",
    "q_fuel_infr_plus_dict.yaml",
    "budget_penalty_plus_dict.yaml",
    "budget_penalty_minus_dict.yaml",
    "budget_penalty_plus_yearly_dict.yaml",
    "budget_penalty_minus_yearly_dict.yaml",
    "s.yaml",
    "detour_time_dict.yaml",
    "x_c_dict.yaml",
    "vot_dt_dict.yaml",
    "n_fueling_dict.yaml",
    "z_dict.yaml",
    "q_fuel_infr_plus_diff_dict.yaml",
    "q_fuel_infr_plus_by_route_dict.yaml",
]

function filter_zero_values!(data_dict::Dict)
    """Remove entries with zero or near-zero values"""
    keys_to_delete = []

    for (key, value) in data_dict
        if isa(value, Number)
            if abs(value) < 1e-10
                push!(keys_to_delete, key)
            end
        end
    end

    for key in keys_to_delete
        delete!(data_dict, key)
    end

    return length(keys_to_delete)
end

function process_file(filepath::String)
    """Load YAML, filter zeros, and save back"""
    println("Processing: $(basename(filepath))")

    try
        # Load the YAML file
        data = YAML.load_file(filepath)

        if isa(data, Dict)
            original_count = length(data)

            # Filter out zero values
            removed_count = filter_zero_values!(data)
            filtered_count = length(data)

            println("  Filtered: $original_count -> $filtered_count entries (removed $removed_count zeros)")

            # Save back to file
            YAML.write_file(filepath, data)
            println("  ✓ Saved")
            return true
        else
            println("  ⚠ Skipping: Not a dictionary")
            return false
        end

    catch e
        println("  ✗ Error: $e")
        return false
    end
end

# Main processing
println("="^60)
println("Filtering zero values from $(RESULTS_FOLDER)")
println("="^60)
println()

processed_count = 0
error_count = 0

for filename in FILES_TO_FILTER
    filepath = joinpath(RESULTS_FOLDER, filename)

    if isfile(filepath)
        if process_file(filepath)
            processed_count += 1
        else
            error_count += 1
        end
        println()
    else
        println("Warning: File not found: $filepath")
        println()
    end
end

println("="^60)
println("Summary:")
println("  Processed: $processed_count files")
println("  Errors: $error_count files")
println("="^60)
