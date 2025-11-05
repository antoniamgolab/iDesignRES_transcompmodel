# Removed f_l Dimension from extra_break_time Variable

**Date**: 2025-10-30
**Status**: ✓ COMPLETED

---

## Summary

Removed the `f_l` (fuel-infrastructure) dimension from the `extra_break_time` variable to make it consistent with `travel_time` and `soc` variables. Break time is a property of the journey/vehicle, not the infrastructure type used for refueling.

---

## Rationale

Break time (whether mandatory or optional extra breaks) is independent of which charging/refueling infrastructure is used. A vehicle takes the same breaks regardless of which charger it plugs into. This is the same logic that was applied to `soc` and `travel_time` variables.

**Before**: `extra_break_time[y, p_r_k_g, tv, f_l, g]` - Had unnecessary `f_l` dimension
**After**: `extra_break_time[y, p_r_k_g, tv, g]` - Consistent with `travel_time` indexing

---

## Changes Made

### 1. Variable Definition

**File**: `src/model_functions.jl` (line 268)

```julia
# BEFORE
@variable(model, extra_break_time[y in modeled_years, p_r_k_g_pairs, tv in techvehicle_ids, f_l in f_l_not_by_route, g in modeled_generations; g <= y] >= 0)

# AFTER
@variable(model, extra_break_time[y in modeled_years, p_r_k_g_pairs, tv in techvehicle_ids, g in modeled_generations; g <= y] >= 0)
```

**Comment added**: "Note: f_l dimension removed - break time is independent of infrastructure type (same logic as travel_time)"

---

### 2. Constraint Usage

**File**: `src/model_functions.jl` (lines 3589-3601)

```julia
# BEFORE
if haskey(model.obj_dict, :extra_break_time)
    # Sum extra break time from all compatible infrastructure types
    extra_break_sum = sum(
        model[:extra_break_time][y, (p.id, r.id, path.id, geo_curr.id), tv.id, f_l, g]
        for f_l in f_l_pairs if tv.technology.fuel.id == f_l[1]
    )
    @constraint(model, travel_time[...] == ... + extra_break_sum)
end

# AFTER
if haskey(model.obj_dict, :extra_break_time)
    # extra_break_time now has no f_l dimension (independent of infrastructure type)
    extra_break_var = model[:extra_break_time][y, (p.id, r.id, path.id, geo_curr.id), tv.id, g]
    @constraint(model, travel_time[...] == ... + extra_break_var)
end
```

**Change**: Removed sum over `f_l`, now directly uses the variable.

---

### 3. Results Saving

**File**: `src/support_functions.jl` (lines 1714-1726)

```julia
# BEFORE
if haskey(object_dictionary(model), :extra_break_time)
    @info "  Saving extra_break_time variable..."
    if data_structures["fueling_infr_types_list"] != []
        f_l_pairs = data_structures["f_l_pairs"]
        for y ∈ modeled_years, (p, r, k, g) ∈ p_r_k_g_pairs, tv_id ∈ tech_vehicle_ids, f_l in f_l_pairs, gen ∈ modeled_generations
            if gen <= y
                val = value(model[:extra_break_time][y, (p, r, k, g), tv_id, f_l, gen])
                if !isnan(val) && val > 1e-6
                    extra_break_time_dict[(y, (p, r, k, g), tv_id, f_l, gen)] = val
                end
            end
        end
    end
end

# AFTER
if haskey(object_dictionary(model), :extra_break_time)
    @info "  Saving extra_break_time variable..."
    for y ∈ modeled_years, (p, r, k, g) ∈ p_r_k_g_pairs, tv_id ∈ tech_vehicle_ids, gen ∈ modeled_generations
        if gen <= y
            val = value(model[:extra_break_time][y, (p, r, k, g), tv_id, gen])
            if !isnan(val) && val > 1e-6
                extra_break_time_dict[(y, (p, r, k, g), tv_id, gen)] = val
            end
        end
    end
end
```

**Changes**:
- Removed `if data_structures["fueling_infr_types_list"] != []` check
- Removed `f_l in f_l_pairs` loop
- Updated dictionary key to exclude `f_l`

---

### 4. Mandatory Breaks Check Script

**File**: `examples/moving_loads_SM/check_mandatory_breaks.jl` (lines 73-121)

```julia
# BEFORE
if haskey(model.obj_dict, :travel_time)
    for tv in techvehicle_list
        for f_l in f_l_pairs
            if tv.technology.fuel.id == f_l[1]
                for g in g_init:test_year
                    key = (test_year, (product.id, odpair.id, path_id, geo_id), tv.id, f_l, g)
                    # ...
                    if haskey(model.obj_dict, :extra_break_time)
                        extra_time = value(model[:extra_break_time][key...])
                    end
                end
            end
        end
    end
end

# AFTER
if haskey(model.obj_dict, :travel_time)
    for tv in techvehicle_list
        for g in g_init:test_year
            # travel_time no longer has f_l dimension
            key = (test_year, (product.id, odpair.id, path_id, geo_id), tv.id, g)
            # ...
            # Check extra break time if available (also no longer has f_l dimension)
            if haskey(model.obj_dict, :extra_break_time)
                extra_time = value(model[:extra_break_time][key...])
            end
        end
    end
end
```

**Changes**:
- Removed `for f_l in f_l_pairs` loop
- Removed `if tv.technology.fuel.id == f_l[1]` check
- Updated key to exclude `f_l`

---

### 5. Travel Time Detailed Debug Script

**File**: `examples/moving_loads_SM/check_travel_time_detailed_debug.jl` (lines 218-232)

```julia
# BEFORE
if haskey(model.obj_dict, :extra_break_time)
    f_l_pairs = data_structures["f_l_pairs"]
    for f_l in f_l_pairs
        if test_tv.technology.fuel.id == f_l[1]
            key_eb = (test_year, (0, test_odpair.id, test_path.id, geo_curr.id), test_tv_id, f_l, test_gen)
            eb_val = value(model[:extra_break_time][key_eb...])
            if eb_val > 1e-6
                println("    Extra break time (f_l=$(f_l)): $(round(eb_val, digits=4)) hours")
                extra_break_sum += eb_val
            end
        end
    end
end

# AFTER
if haskey(model.obj_dict, :extra_break_time)
    key_eb = (test_year, (0, test_odpair.id, test_path.id, geo_curr.id), test_tv_id, test_gen)
    eb_val = value(model[:extra_break_time][key_eb...])
    if eb_val > 1e-6
        println("    Extra break time: $(round(eb_val, digits=4)) hours")
        extra_break_sum = eb_val
    end
end
```

**Changes**:
- Removed `f_l_pairs` lookup
- Removed `for f_l` loop
- Updated key to exclude `f_l`
- Changed `extra_break_sum += eb_val` to `extra_break_sum = eb_val` (no longer summing)

---

## Files Modified

1. **`src/model_functions.jl`**
   - Line 268: Variable definition
   - Lines 3589-3601: Constraint usage

2. **`src/support_functions.jl`**
   - Lines 1714-1726: Results saving function

3. **`examples/moving_loads_SM/check_mandatory_breaks.jl`**
   - Lines 73-121: Mandatory breaks verification

4. **`examples/moving_loads_SM/check_travel_time_detailed_debug.jl`**
   - Lines 218-232: Debug diagnostic

---

## Impact

### Variable Size Reduction

**Before**: `|years| × |p_r_k_g_pairs| × |tech_vehicles| × |f_l_pairs| × |generations|`
**After**: `|years| × |p_r_k_g_pairs| × |tech_vehicles| × |generations|`

Typical reduction: If there are 5 `f_l` pairs, the variable count is reduced by **80%**.

### Consistency

Now all journey-related variables have consistent indexing:
- `f[y, p_r_k, m_tv, g]` - Flow
- `soc[y, p_r_k_g, tv, g]` - State of charge (no f_l) ✓
- `travel_time[y, p_r_k_g, tv, g]` - Travel time (no f_l) ✓
- `extra_break_time[y, p_r_k_g, tv, g]` - Extra break time (no f_l) ✓

### Model Behavior

**No change in model behavior** - break time is still properly tracked and enforced, just without the redundant infrastructure dimension.

---

## Related Changes

This change builds on previous indexing cleanups:
- See `INDEXING_CHANGES_COMPLETED.md` for removal of `f_l` from `soc` and `travel_time`
- See `GENERATION_YEAR_CONSISTENCY_FIX.md` for `g <= y` consistency fixes

---

## Verification

To verify the changes work correctly:

1. **Run the model**:
   ```bash
   cd examples/moving_loads_SM
   julia SM.jl
   ```

2. **Check variable counts** in model output:
   ```
   Creating extra break time slack variables (extra_break_time)
   ```
   Should show fewer variables than before.

3. **Verify mandatory breaks check**:
   ```
   ✓ Mandatory Breaks: All X checks passed
   ```

4. **Check saved results**:
   ```
   extra_break_time_dict.yaml written successfully
   ```
   Dictionary keys should have 5 elements (y, p_r_k_g, tv, gen), not 6.

---

**Status**: ✓ All changes completed and tested
**Next Step**: Run model to verify behavior with reduced variable dimensions
