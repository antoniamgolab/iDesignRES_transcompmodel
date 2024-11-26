function check_input_file(path_to_source_file::String)
    if !isfile(path_to_source_file)
        error("The input file does not exist.")
    end

    if !endswith(path_to_source_file, ".yaml") && !endswith(path_to_source_file, ".yml")
        error("The input file must be a YAML file.")
    end
end

function check_required_keys(data_dict::Dict, required_keys::Vector{String})
    for key in required_keys
        @assert haskey(data_dict, key) "The key $key is missing in the input file."
    end
end

function check_model_parametrization(data_dict::Dict, required_keys::Vector{String})
    return check_required_keys(data_dict["Model"], required_keys)
end
