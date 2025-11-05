# Travel Time Multi-Node Path Infeasibility Fix

**Date**: 2025-10-30
**Status**: 🔍 DIAGNOSED - FIX PROPOSED

---

## Problem

The `constraint_travel_time_track()` function creates **strict equality constraints** for every node in a path sequence:

```julia
travel_time[node_i] == travel_time[node_i-1] + driving_time + charging + breaks
```

For paths with multiple nodes (especially short boundary-crossing paths), this creates:
1. **Long chains of linked equality constraints**
2. **Over-constrained system** where any single conflict makes the entire path infeasible
3. **Accumulation of small numerical errors** across many segments

---

## Root Cause

### Example: 5 km Boundary Path with 5 Nodes

```
Path: [DE1, AT1, AT2, IT1, IT2]
Total length: 5 km
Nodes: 5
distance_from_previous: [0, 1.5, 1.0, 1.5, 1.0] km
```

This creates **4 chained equality constraints**:
```
travel_time[AT1] == travel_time[DE1] + 1.5/speed * num_vehicles + ...
travel_time[AT2] == travel_time[AT1] + 1.0/speed * num_vehicles + ...
travel_time[IT1] == travel_time[AT2] + 1.5/speed * num_vehicles + ...
travel_time[IT2] == travel_time[IT1] + 1.0/speed * num_vehicles + ...
```

If **any** of these conflicts with another constraint (mandatory breaks, charging capacity, etc.), the **entire path** becomes infeasible.

### Why This is Problematic

1. **Boundary paths** often have multiple intermediate nodes for routing purposes but small total distance
2. **Each segment adds a constraint** even if distance is tiny or zero
3. **Accumulated travel_time** at intermediate nodes can conflict with mandatory break requirements
4. **No flexibility** - strict equality means no wiggle room for numerical issues

---

## Diagnosis

Run the diagnostic script to identify problematic paths:

```julia
include("diagnose_travel_time_infeasibility.jl")
```

This will show:
- Paths with 3+ nodes and small total length (< 50 km)
- Paths with distance mismatches
- Zero-distance segments
- Constraint count analysis

---

## Proposed Solutions

### Option 1: Skip Constraints for Very Short Paths ⭐ RECOMMENDED

**Logic**: For very short paths (< 10 km), travel time is negligible and doesn't need to be tracked.

```julia
function constraint_travel_time_track(model::JuMP.Model, data_structures::Dict)
    # ... existing setup code ...

    MIN_PATH_LENGTH_FOR_TRACKING = 10.0  # km

    for r in odpairs
        p = r.product
        for path in r.paths
            # SKIP: Don't track travel time for very short paths
            if path.length < MIN_PATH_LENGTH_FOR_TRACKING
                continue
            end

            # ... rest of constraint logic ...
        end
    end
end
```

**Pros**:
- Simple to implement
- Eliminates infeasibility for short boundary paths
- Short paths don't meaningfully contribute to travel time anyway

**Cons**:
- Arbitrary threshold
- May miss some genuine short-distance flows

---

### Option 2: Use Inequality for Intermediate Nodes

**Logic**: Only enforce strict equality at the final destination. Use >= for intermediate nodes to allow flexibility.

```julia
# For intermediate nodes (not last node in sequence)
if i < nb_in_sequ  # Not the last node
    @constraint(
        model,
        model[:travel_time][y, (p.id, r.id, path.id, geo_curr.id), tv.id, g] >=
        model[:travel_time][y, (p.id, r.id, path.id, geo_prev.id), tv.id, g]
        + (distance_increment / speed) * numbers_vehicles
        + charging_time_sum
        + extra_break_var
    )
else  # Last node - enforce strict equality
    @constraint(
        model,
        model[:travel_time][y, (p.id, r.id, path.id, geo_curr.id), tv.id, g] ==
        model[:travel_time][y, (p.id, r.id, path.id, geo_prev.id), tv.id, g]
        + (distance_increment / speed) * numbers_vehicles
        + charging_time_sum
        + extra_break_var
    )
end
```

**Pros**:
- Maintains accurate tracking for final destination
- Allows flexibility for intermediate nodes
- More robust to numerical issues

**Cons**:
- Intermediate travel_time values may be less accurate
- Slightly more complex logic

---

### Option 3: Simplify Path Sequences in Preprocessing

**Logic**: For short paths, remove intermediate nodes that don't have infrastructure.

**In preprocessing**:
```python
if path['length'] < 50:  # km
    # Keep only first and last node
    simplified_sequence = [path['sequence'][0], path['sequence'][-1]]
    path['sequence'] = simplified_sequence
    path['distance_from_previous'] = [0, path['length']]
```

**Pros**:
- Cleaner data structure
- Fewer constraints overall
- Fixes the root cause

**Cons**:
- Requires reprocessing data
- May lose geographic routing information

---

### Option 4: Conditional Constraint Based on Node Count

**Logic**: For paths with many nodes, skip intermediate constraints.

```julia
MAX_NODES_FOR_ALL_CONSTRAINTS = 3

if nb_in_sequ <= MAX_NODES_FOR_ALL_CONSTRAINTS
    # Create constraints for all nodes (original logic)
    for i in 2:nb_in_sequ
        # ... create constraint ...
    end
else
    # Only create constraint for final destination
    i = nb_in_sequ
    geo_curr = sequence[i]

    # Calculate total distance from origin to destination
    total_distance = sum(path.distance_from_previous[2:end])

    @constraint(
        model,
        model[:travel_time][y, (p.id, r.id, path.id, geo_curr.id), tv.id, g] ==
        model[:travel_time][y, (p.id, r.id, path.id, sequence[1].id), tv.id, g]
        + (total_distance / speed) * numbers_vehicles
        + charging_time_sum_total
        + extra_break_var_total
    )
end
```

**Pros**:
- Preserves accuracy for simple paths
- Simplifies constraints for complex paths
- Flexible threshold

**Cons**:
- May miss charging/break opportunities at intermediate nodes
- Requires aggregating charging/breaks across all segments

---

## Implementation Plan

**Recommended approach**: **Option 1** (Skip short paths) + **Option 2** (Use >= for intermediate nodes)

### Step 1: Modify constraint_travel_time_track

```julia
function constraint_travel_time_track(model::JuMP.Model, data_structures::Dict)
    # ... existing setup ...

    MIN_PATH_LENGTH_FOR_TRACKING = 10.0  # Skip very short paths

    for r in odpairs
        p = r.product
        for path in r.paths
            # SKIP short paths
            if path.length < MIN_PATH_LENGTH_FOR_TRACKING
                continue
            end

            sequence = path.sequence
            nb_in_sequ = length(sequence)

            for i in 2:nb_in_sequ
                geo_curr = sequence[i]
                geo_prev = sequence[i-1]
                distance_increment = path.distance_from_previous[i]

                for y in modeled_years
                    for tv in techvehicle_list
                        for g in modeled_generations
                            if g <= y
                                # ... calculate numbers_vehicles, charging_time_sum, extra_break_var ...

                                # Use >= for intermediate nodes, == for final destination
                                if i == nb_in_sequ  # Final destination
                                    @constraint(
                                        model,
                                        model[:travel_time][y, (p.id, r.id, path.id, geo_curr.id), tv.id, g] ==
                                        model[:travel_time][y, (p.id, r.id, path.id, geo_prev.id), tv.id, g]
                                        + (distance_increment / speed) * numbers_vehicles
                                        + charging_time_sum
                                        + extra_break_var
                                    )
                                else  # Intermediate node
                                    @constraint(
                                        model,
                                        model[:travel_time][y, (p.id, r.id, path.id, geo_curr.id), tv.id, g] >=
                                        model[:travel_time][y, (p.id, r.id, path.id, geo_prev.id), tv.id, g]
                                        + (distance_increment / speed) * numbers_vehicles
                                        + charging_time_sum
                                        + extra_break_var
                                    )
                                end
                            end
                        end
                    end
                end
            end
        end
    end
end
```

### Step 2: Test with diagnostic

Run SM.jl and check:
1. How many paths are skipped
2. Whether infeasibility is resolved
3. Whether results are still reasonable

---

## Expected Impact

### Before Fix
- **Infeasible** due to over-constrained multi-node short paths
- Many equality constraints that conflict

### After Fix
- **Feasible** - short paths skip constraints
- Intermediate nodes use inequalities (more flexible)
- Final destinations still accurately tracked

### Model Size Reduction
- Skip ~N short paths × 4 nodes/path × Y years × TV vehicles × G generations
- Example: 100 short paths × 3 extra nodes × 3 years × 2 vehicles × 3 gens = **5,400 constraints removed**

---

## Testing

1. Run diagnostic: `include("diagnose_travel_time_infeasibility.jl")`
2. Note how many short multi-node paths exist
3. Apply fix to `src/model_functions.jl`
4. Re-run model
5. Check:
   - Model solves to optimality
   - Travel time values are reasonable
   - No violations in mandatory breaks check

---

## Files to Modify

1. **`src/model_functions.jl`** - Function `constraint_travel_time_track()`
   - Add MIN_PATH_LENGTH_FOR_TRACKING threshold
   - Change == to >= for intermediate nodes

2. **`examples/moving_loads_SM/diagnose_travel_time_infeasibility.jl`** (already created)
   - Run to identify problematic paths

---

**Status**: 🔍 Diagnosis complete, fix ready to implement
**Next**: Test diagnostic, then apply Option 1 + Option 2 fix
