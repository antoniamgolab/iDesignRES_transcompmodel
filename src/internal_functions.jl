function generate_exact_length_subsets(start_year::Int, end_year::Int, delta_y::Int)
    """
    	generate_exact_length_subsets(start_year::Int, end_year::Int, delta_y::Int)
    
    Generates a list of subsets of years with a fixed length.
    
    # Arguments
    - start_year::Int: The first year.
    - end_year::Int: The last year.
    - delta_y::Int: The length of the subsets.
    # Returns
    - Vector{Vector{Int}}: List of year subsets.
    """
    all_years = start_year:end_year
    subsets = []
    for i ∈ 1:(length(all_years)-delta_y+1)
        push!(subsets, collect(all_years[i:(i+delta_y-1)]))
    end
    return subsets
end

function create_m_tv_pairs(techvehicle_list::Vector{TechVehicle}, mode_list::Vector{Mode})
    """
    	create_m_tv_pairs(techvehicle_list::Vector{TechVehicle}, mode_list::Vector{Mode})
    
    Creates a set of pairs of mode and techvehicle IDs.
    
    # Arguments
    - techvehicle_list::Vector{TechVehicle}: List of techvehicles.
    - mode_list::Vector{Mode}: List of modes.
    # Returns
    - Set{Tuple{Int,Int}}: Set of (mode_id, techvehicle_id) pairs.
    """
    m_tv_pairs = Set((tv.vehicle_type.mode.id, tv.id) for tv ∈ techvehicle_list)
    techvehicle_ids = [tv.id for tv ∈ techvehicle_list]
    global counter_additional_vehs = length(techvehicle_list)
    for m ∈ mode_list
        for v ∈ techvehicle_list
            if v.vehicle_type.mode.id == m.id
                push!(m_tv_pairs, (m.id, v.id))
            end
        end
        if !m.quantify_by_vehs
            push!(m_tv_pairs, (m.id, counter_additional_vehs + 1))
            push!(techvehicle_ids, counter_additional_vehs + 1)
            global counter_additional_vehs += 1
        end
    end
    return m_tv_pairs
end

function create_tv_id_set(techvehicle_list_2::Vector{TechVehicle}, mode_list::Vector{Mode})
    """
    	create_tv_id_set(techvehicle_list_2::Vector{TechVehicle}, mode_list::Vector{Mode})
    
    Creates a set of techvehicle IDs, including additional ones for non-vehicle modes.
    
    # Arguments
    - techvehicle_list_2::Vector{TechVehicle}: List of techvehicles.
    - mode_list::Vector{Mode}: List of modes.
    # Returns
    - Set{Int}: Set of techvehicle IDs.
    """
    m_tv_pairs = Set((tv.vehicle_type.mode.id, tv.id) for tv ∈ techvehicle_list_2)
    techvehicle_ids_2 = Set([tv.id for tv ∈ techvehicle_list_2])
    global counter_additional_vehs_2 = length(techvehicle_list_2)
    for m ∈ mode_list
        if !m.quantify_by_vehs
            push!(techvehicle_ids_2, counter_additional_vehs_2 + 1)
            global counter_additional_vehs_2 += 1
        end
    end
    return techvehicle_ids_2
end

function create_v_t_set(techvehicle_list::Vector{TechVehicle})
    """
    	create_v_t_set(techvehicle_list::Vector{TechVehicle})
    
    Creates a set of pairs of techvehicle IDs.
    
    # Arguments
    - techvehicle_list::Vector{TechVehicle}: List of techvehicles.
    # Returns
    - Set{Tuple{Int,Int}}: Set of (techvehicle_id, techvehicle_id) pairs.
    """
    t_v_pairs = Set((tv.id, tv.id) for tv ∈ techvehicle_list)
    return t_v_pairs
end


"""
	create_p_r_k_set(odpairs::Vector{Odpair})

Creates a set of (product_id, odpair_id, path_id) tuples.

# Arguments
- odpairs::Vector{Odpair}: List of odpairs.
# Returns
- Set{Tuple{Int,Int,Int}}: Set of (product_id, odpair_id, path_id) tuples.
"""
function create_p_r_k_set(odpairs::Vector{Odpair})
    p_r_k_pairs = Set((r.product.id, r.id, k.id) for r ∈ odpairs for k ∈ r.paths)
    return p_r_k_pairs
end

function create_p_r_k_e_set(odpairs::Vector{Odpair})
    """
    	create_p_r_k_e_set(odpairs::Vector{Odpair})
    
    Creates a set of (product_id, odpair_id, path_id, element_id) tuples for edges.
    
    # Arguments
    - odpairs::Vector{Odpair}: List of odpairs.
    # Returns
    - Set{Tuple{Int,Int,Int,Any}}: Set of tuples for edges.
    """
    p_r_k_e_pairs = Set(
        (r.product.id, r.id, k.id, el) for r ∈ odpairs for k ∈ r.paths for
        el ∈ k.sequence if el.type == "edge"
    )
    return p_r_k_e_pairs
end

function create_p_r_k_g_set(odpairs::Vector{Odpair})
    """
    	create_p_r_k_g_set(odpairs::Vector{Odpair})
    
    Creates a set of (product_id, odpair_id, path_id, element_id) tuples for all elements.
    
    # Arguments
    - odpairs::Vector{Odpair}: List of odpairs.
    # Returns
    - Set{Tuple{Int,Int,Int,Int}}: Set of tuples for all elements.
    """
    p_r_k_g_pairs = Set(
        (r.product.id, r.id, k.id, el.id) for r ∈ odpairs for k ∈ r.paths for
        el ∈ k.sequence
    )
    return p_r_k_g_pairs
end

function create_p_r_k_n_set(odpairs::Vector{Odpair})
    """
    	create_p_r_k_n_set(odpairs::Vector{Odpair})
    
    Creates a set of (product_id, odpair_id, path_id, element_id) tuples for nodes.
    
    # Arguments
    - odpairs::Vector{Odpair}: List of odpairs.
    # Returns
    - Set{Tuple{Int,Int,Int,Any}}: Set of tuples for nodes.
    """
    p_r_k_n_pairs = Set(
        (r.product.id, r.id, k.id, el) for r ∈ odpairs for k ∈ r.paths for
        el ∈ k.sequence if el.type == "node"
    )
    return p_r_k_n_pairs
end

function create_r_k_set(odpairs::Vector{Odpair})
    """
    	create_r_k_set(odpairs::Vector{Odpair})
    
    Creates a set of (odpair_id, path_id) tuples.
    
    # Arguments
    - odpairs::Vector{Odpair}: List of odpairs.
    # Returns
    - Set{Tuple{Int,Int}}: Set of (odpair_id, path_id) tuples.
    """
    r_k_pairs = Set((r.id, k.id) for r ∈ odpairs for k ∈ r.paths)
    return r_k_pairs
end

function create_emission_price_along_path(k::Path, y::Int64, data_structures::Dict)
    """
    	create_emission_price_along_path(k::Path, y::Int64, data_structures::Dict)
    
    Calculates the average carbon price along a path for a given year.
    
    # Arguments
    - k::Path: Path object.
    - y::Int64: Year index.
    - data_structures::Dict: Model data.
    # Returns
    - Float64: Average carbon price for the path in year y.
    """
    n = length(k.sequence)
    geographic_element_list = data_structures["geographic_element_list"]
    global total_carbon_price = 0.0
    for el ∈ k.sequence
        current_carbon_price =
            geographic_element_list[findfirst(
                e -> e.id == el.id,
                geographic_element_list,
            )].carbon_price
        global total_carbon_price = total_carbon_price + current_carbon_price[y]
    end
    average_carbon_price = total_carbon_price / n
    return average_carbon_price
end

function stringify_keys(dict::Dict)
    """
    	stringify_keys(dict::Dict)
    
    Convert all keys in a dictionary to strings.
    
    # Arguments
    - `dict::Dict`: The dictionary whose keys will be stringified.
    # Returns
    - Dict{String,Any}: Dictionary with string keys and formatted values.
    """
    new_dict = Dict{String,Any}()
    for (k, v) ∈ dict
        new_dict[string(k)] = v
    end
    return new_dict
end
"""
This file contains internal helper functions for the transport model. These are not used directly in tests or in the main example workflow (basque_cs.jl).
"""

# Functions will be moved here from support_functions.jl
