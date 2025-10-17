# How to Use the Mandatory Breaks Constraint

## What was added

✅ **Added `constraint_mandatory_breaks()` function** to `model_functions.jl` (lines 3468-3575)

## What it does

The constraint ensures that `travel_time` at mandatory break locations accounts for break duration:

```
travel_time[break_location] >= (driving_time + break_duration) × num_vehicles
```

For example:
- If a break is required at 360 km (4.5 hours driving)
- And the break adds 0.75 hours (45 minutes)
- Then travel_time at that location must be ≥ 5.25 hours per vehicle

## How to use it in SM.jl

### Step 1: Make sure you have MandatoryBreaks.yaml

In SM-preprocessing.ipynb, generate the mandatory breaks data:
```python
mandatory_breaks_list = create_mandatory_breaks_list(path_list, speed=80)

# Export to YAML
output_path = os.path.join(output_dir, 'MandatoryBreaks.yaml')
with open(output_path, 'w') as f:
    yaml.dump(mandatory_breaks_list, f, default_flow_style=False)
```

### Step 2: Add the constraint in SM.jl

Add this after `constraint_travel_time_track`:

```julia
# Timing: Add mandatory breaks constraint
@info "Step 4.12/5: Adding mandatory breaks constraint..."
t_start = time()
constraint_mandatory_breaks(model, data_structures)
t_mandatory_breaks = time() - t_start
@info "✓ Mandatory breaks constraint added in $(round(t_mandatory_breaks, digits=2)) seconds"
```

### Complete placement in SM.jl:

```julia
# ... existing constraints ...

# Timing: Add travel time tracking constraint
@info "Step 4.8/5: Adding travel time tracking constraint..."
constraint_travel_time_track(model, data_structures)
t_travel_time_track = time() - t_start
@info "✓ Travel time tracking constraint added in $(round(t_travel_time_track, digits=2)) seconds"

# Timing: Add mandatory breaks constraint
@info "Step 4.12/5: Adding mandatory breaks constraint..."
t_start = time()
constraint_mandatory_breaks(model, data_structures)
t_mandatory_breaks = time() - t_start
@info "✓ Mandatory breaks constraint added in $(round(t_mandatory_breaks, digits=2)) seconds"

# Timing: Add spatial flexibility constraint
@info "Step 4.8/5: Adding spatial flexibility constraint..."
t_start = time()
constraint_spatial_flexibility(model, data_structures)
# ... rest of code ...
```

## What happens when you run it

The constraint will:

1. ✓ Check if `mandatory_break_list` exists in data_structures
2. ✓ Check if `travel_time` variable exists in the model
3. ✓ Create a lookup dictionary: `path_id -> list of breaks`
4. ✓ For each break on each path:
   - Verify the break location exists in the path sequence
   - Add constraint: `travel_time[break_location] >= min_time_with_breaks`
5. ✓ Print summary: "✓ Mandatory breaks constraint added: X constraints created"

## Example output

```
[ Info: Step 4.12/5: Adding mandatory breaks constraint...
[ Info: Adding mandatory breaks constraints for 8 breaks on 5 paths...
[ Info: ✓ Mandatory breaks constraint added: 1920 constraints created
[ Info: ✓ Mandatory breaks constraint added in 2.34 seconds
```

## If no breaks are needed

The constraint gracefully handles cases with no breaks:

```julia
if !haskey(data_structures, "mandatory_break_list")
    @info "No mandatory breaks data found. Skipping constraint_mandatory_breaks."
    return
end
```

## Validation after optimization

You can verify the constraint is working by checking:

```julia
# After optimize!(model)
for mb in data_structures["mandatory_break_list"]
    path = path_dict[mb.path_id]
    key = (2030, (0, odpair_id, path.id, mb.latest_geo_id), tv_id, f_l, gen)

    if haskey(model[:travel_time].data, key)
        tt_val = value(model[:travel_time][key...])
        println("Break $(mb.break_number) at $(mb.cumulative_distance) km:")
        println("  Required: $(mb.time_with_breaks)h, Actual: $(tt_val)h")
    end
end
```

## Technical Details

**Constraint structure:**
```julia
@constraint(model,
    model[:travel_time][y, (p.id, odpair.id, path.id, break_geo_id), tv.id, f_l, g]
    >= mb.time_with_breaks * num_vehicles
)
```

**Variables:**
- `y`: year
- `p.id`: product ID
- `odpair.id`: OD pair ID
- `path.id`: path ID
- `break_geo_id`: geographic element ID where break must occur
- `tv.id`: tech vehicle ID
- `f_l`: (fuel_id, infrastructure_id) tuple
- `g`: generation (year of purchase)

**Fleet-level calculation:**
- `num_vehicles = (path.length / (W × AnnualRange)) × 1000 × f[...]`
- `min_fleet_travel_time = time_with_breaks × num_vehicles`

This ensures that the TOTAL FLEET travel time accounts for breaks, consistent with other fleet-level variables in the model.
