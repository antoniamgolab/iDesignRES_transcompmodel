"""
This module contains functions to check for potential issues in the input data.
"""

"""
    check_input_file(path_to_source_file::String)

Check if the input file exists and is a YAML file.

# Arguments
- `path_to_source_file::String`: The path to the input file.
"""
function check_input_file(path_to_source_file::String)
    if !isfile(path_to_source_file)
        error("The input file does not exist.")
    end

    if !endswith(path_to_source_file, ".yaml") && !endswith(path_to_source_file, ".yml")
        error("The input file must be a YAML file.")
    end
end

"""
    check_required_keys(data_dict::Dict, required_keys::Vector{String})

Check if the required keys are present in the input data.

# Arguments
- `data_dict::Dict`: The input data.
"""
function check_required_keys(data_dict::Dict, required_keys::Vector{String})
    for key ∈ required_keys
        @assert haskey(data_dict, key) "The key $key is missing in the input file."
    end
end

"""
    check_model_parametrization(data_dict::Dict, required_keys::Vector{String})

Check if the required keys are present in the model data.

# Arguments
- `data_dict::Dict`: The input data.

# Returns
- `Bool`: True if the required keys are present, false otherwise.
"""
function check_model_parametrization(data_dict::Dict, required_keys::Vector{String})
    return check_required_keys(data_dict["Model"], required_keys)
end
