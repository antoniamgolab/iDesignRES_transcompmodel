# MandatoryBreak Struct - Summary

## What was added to structs.jl

I've added a new `MandatoryBreak` struct to `src/structs.jl` (after the `Path` struct, lines 125-153).

### Struct Definition

```julia
struct MandatoryBreak
    id::Int
    path_id::Int
    path_length::Float64
    total_driving_time::Float64
    break_number::Int
    latest_node_idx::Int
    latest_geo_id::Int
    cumulative_distance::Float64
    cumulative_driving_time::Float64
    time_with_breaks::Float64
end
```

### Fields Explanation

- `id`: Unique identifier for this break entry
- `path_id`: Which path this break belongs to
- `path_length`: Total length of the path (km)
- `total_driving_time`: Total driving time for entire path (hours, excluding breaks)
- `break_number`: Sequential number (1st break, 2nd break, etc.)
- `latest_node_idx`: Index in path.sequence where break must occur
- `latest_geo_id`: Geographic element ID of that node
- `cumulative_distance`: Distance traveled up to this break point (km)
- `cumulative_driving_time`: Driving time up to this break (hours, no breaks)
- `time_with_breaks`: Total elapsed time AFTER taking this break (hours, includes break time)

### Registration

Added "MandatoryBreak" to `struct_names_base` list (line 1098) so it will be:
- Automatically loaded from YAML files
- Parsed by `parse_data()` function
- Available in `data_structures` dictionary

## How to use in your model

### 1. In SM-preprocessing.ipynb

Generate the MandatoryBreaks.yaml file using the functions from `mandatory_breaks_calculation.py`.

### 2. Julia will automatically load it

When you call:
```julia
data_dict = get_input_data(file)
data_structures = parse_data(data_dict)
```

The MandatoryBreak data will be loaded and available as:
```julia
mandatory_breaks_list = data_structures["mandatory_break_list"]
```

Each entry will be a `MandatoryBreak` struct instance.

### 3. Example usage in constraints

```julia
# Access mandatory breaks
mandatory_breaks = data_structures["mandatory_break_list"]

# Iterate over breaks for a specific path
for break_entry in mandatory_breaks
    if break_entry.path_id == current_path_id
        # Create constraint that travel time at break_entry.latest_geo_id
        # must be >= break_entry.time_with_breaks

        # Or ensure charging occurs at or before this node

        # Or enforce that vehicles must stop here
    end
end
```

### 4. Example constraint

```julia
# Ensure travel time accounts for mandatory breaks
for mb in mandatory_breaks
    path = path_dict[mb.path_id]
    geo_id = mb.latest_geo_id

    # Travel time at this node must be at least the time including break
    for y in years, tv in techvehicles, g in generations
        @constraint(model,
            model[:travel_time][y, path.id, geo_id, tv.id, g] >=
            mb.time_with_breaks * model[:f][y, path.id, tv.id, g]
        )
    end
end
```

## Data Flow

1. **SM-preprocessing.ipynb** → Creates `MandatoryBreaks.yaml` with flat list structure
2. **Julia load** → `get_input_data()` reads YAML
3. **Julia parse** → `parse_data()` creates `MandatoryBreak` struct instances
4. **Julia model** → Use in constraints via `data_structures["mandatory_break_list"]`

## Notes

- The struct matches exactly the flat structure from the Python code
- All fields are basic types (Int, Float64) for easy YAML serialization
- Located logically after `Path` struct since they're related
- Follows the same pattern as other data structures in the model
