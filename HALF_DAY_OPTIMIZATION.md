# Half-Day Performance Optimization Plan
**Estimated Time: 4 hours | Expected Speedup: 3-4x overall**

This is a condensed optimization plan focusing on the highest-impact changes that can be implemented in approximately half a day.

---

## Priority 1: Fix Critical Bug (15 minutes)
**File:** `src/model_functions.jl`
**Lines:** 3404-3413
**Impact:** Bug fix + 10-20% speedup
**Difficulty:** Trivial

### The Problem
Lines 3404-3413 are EXACT DUPLICATES of lines 3392-3401 (copy-paste error).

### The Fix
**DELETE lines 3404-3413 entirely.**

```julia
# LINES TO DELETE (3404-3413):
        for p_r_k ∈ p_r_k_set
            path = paths[findfirst(k0 -> k0.id == p_r_k[2], paths)]
            for el ∈ path.sequence
                if el == path.sequence[1] || el == path.sequence[end]
                    continue
                end
                JuMP.@constraint(model, travel_time[p_r_k[1], p_r_k[2], p_r_k[3], el] >= 0)
            end
        end
```

These lines are duplicates and should be removed.

---

## Priority 2: Add Dictionary Lookups to parse_data() (45 minutes)
**File:** `src/support_functions.jl`
**Function:** `parse_data()` (lines 243-992)
**Impact:** 20-40% speedup
**Difficulty:** Easy

### The Problem
The function repeatedly uses `findfirst()` to look up elements by ID:
```julia
# Called hundreds/thousands of times in nested loops:
geographic_element_list[findfirst(geo -> geo.id == el, geographic_element_list)]
paths[findfirst(k0 -> k0.id == p_id, paths)]
mode_list[findfirst(k0 -> k0.id == mode_id, mode_list)]
```
Each call is O(n) - scanning the entire list every time.

### The Fix

**Step 1:** Add these dictionary builders RIGHT AFTER line 287 (after all lists are populated):

```julia
    # ===== NEW: Build lookup dictionaries for O(1) access =====
    geo_element_dict = Dict(geo.id => geo for geo in geographic_element_list)
    path_dict = Dict(p.id => p for p in paths)
    mode_dict = Dict(m.id => m for m in mode_list)
    tech_dict = Dict(t.id => t for t in technology_list)
    fuel_dict = Dict(f.id => f for f in fuel_list)
    vehicle_dict = Dict(v.id => v for v in vehicletype_list)
    @info "✓ Lookup dictionaries created for fast access"
    # ==========================================================
```

**Step 2:** Replace the most critical `findfirst()` calls:

**Location 1: Line ~288-300 (path sequence parsing)**
```julia
# BEFORE:
for el ∈ path_temp.sequence
    push!(sequence_temp, geographic_element_list[findfirst(geo -> geo.id == el, geographic_element_list)])
end

# AFTER:
for el ∈ path_temp.sequence
    push!(sequence_temp, geo_element_dict[el])
end
```

**Location 2: Line ~400-450 (odpair path lookup)**
```julia
# BEFORE:
path_id = paths[findfirst(k0 -> k0.id == odpair_temp.path_id, paths)]

# AFTER:
path_id = path_dict[odpair_temp.path_id]
```

**Location 3: Line ~500-600 (mode/vehicle lookups)**
```julia
# BEFORE:
mode = mode_list[findfirst(k0 -> k0.id == mode_id, mode_list)]
vehicle = vehicletype_list[findfirst(k0 -> k0.id == veh_id, vehicletype_list)]

# AFTER:
mode = mode_dict[mode_id]
vehicle = vehicle_dict[veh_id]
```

**Step 3:** Pass dictionaries in DataStructure (optional but recommended):
At line ~980, add dictionaries to the returned DataStructure:
```julia
return DataStructure(
    # ... existing fields ...
    geo_element_dict,
    path_dict,
    mode_dict,
    tech_dict,
    fuel_dict,
    vehicle_dict
)
```

**Note:** If you add to DataStructure, you must also update the struct definition in `src/structs.jl`.

---

## Priority 3: Optimize constraint_fueling_demand() (60 minutes)
**File:** `src/model_functions.jl`
**Lines:** 1257-1303
**Impact:** 60-80% speedup for this constraint
**Difficulty:** Easy

### The Problem
Current code calls `findfirst()` **4+ times per constraint**:

```julia
# Line 1270-1280 (CURRENT - SLOW):
for el ∈ paths[findfirst(k0 -> k0.id == r_k[2], paths)].sequence
    if el == paths[findfirst(k0 -> k0.id == r_k[2], paths)].sequence[1] ||
       el == paths[findfirst(k0 -> k0.id == r_k[2], paths)].sequence[end]
        continue
    end

    for odpair ∈ odpairs
        if odpair.path_id == paths[findfirst(k0 -> k0.id == r_k[2], paths)]
            # ... constraint code ...
        end
    end
end
```

Each `findfirst(k0 -> k0.id == r_k[2], paths)` scans the entire paths list!

### The Fix

**Replace the entire loop structure (lines ~1270-1295) with:**

```julia
    for r_k ∈ r_k_set
        # Get path ONCE using dictionary lookup
        path = path_dict[r_k[2]]

        for el ∈ path.sequence
            # Check if first or last element
            if el == path.sequence[1] || el == path.sequence[end]
                continue
            end

            # Iterate over odpairs
            for odpair ∈ odpairs
                if odpair.path_id == path.id
                    if haskey(s, (tau, odpair.id, r_k[1], r_k[3], f_l, el.id))
                        push!(
                            s_tau_o_r_k_f_l_el_temp,
                            s[tau, odpair.id, r_k[1], r_k[3], f_l, el.id],
                        )
                    end
                end
            end
        end

        if !isempty(s_tau_o_r_k_f_l_el_temp)
            JuMP.@constraint(
                model,
                sum(s_tau_o_r_k_f_l_el_temp) <= q_fuel_infr[tau, f_l, r_k[1]]
            )
        end
        empty!(s_tau_o_r_k_f_l_el_temp)
    end
```

**Key change:**
- Single lookup: `path = path_dict[r_k[2]]`
- Reuse `path` throughout instead of 4+ `findfirst()` calls

---

## Priority 4: Pre-filter p_r_k_g_pairs in constraint_fueling_infrastructure() (90 minutes)
**File:** `src/model_functions.jl`
**Lines:** 896-1115
**Impact:** 50-70% speedup for this constraint
**Difficulty:** Medium

### The Problem
The constraint loops over ALL geographic elements, then FILTERS `p_r_k_g_pairs` inside the loop:

```julia
# Lines ~930-960 (CURRENT - SLOW):
for geo ∈ geographic_elements
    for p_r_k_g ∈ p_r_k_g_pairs  # Checking ALL pairs every time!
        if p_r_k_g[4] == geo.id  # Filter checked millions of times
            # ... constraint code ...
        end
    end
end
```

If you have 100 geographic elements and 10,000 p_r_k_g pairs, this does 1,000,000 comparisons.

### The Fix

**Step 1:** Add pre-filtering RIGHT BEFORE the constraint loop (around line ~925):

```julia
    # ===== NEW: Pre-filter p_r_k_g_pairs by geo_id for O(1) access =====
    @info "Pre-filtering p_r_k_g_pairs by geographic element..."
    p_r_k_g_by_geo = Dict{Int, Vector{Tuple}}()

    for p_r_k_g ∈ p_r_k_g_pairs
        geo_id = p_r_k_g[4]
        if !haskey(p_r_k_g_by_geo, geo_id)
            p_r_k_g_by_geo[geo_id] = []
        end
        push!(p_r_k_g_by_geo[geo_id], p_r_k_g)
    end

    @info "✓ Pre-filtering complete: $(length(p_r_k_g_by_geo)) geographic elements with traffic"
    # ====================================================================
```

**Step 2:** Replace the inner loop (lines ~930-1050):

```julia
# BEFORE:
for geo ∈ geographic_elements
    for p_r_k_g ∈ p_r_k_g_pairs
        if p_r_k_g[4] == geo.id
            # ... constraint code ...
        end
    end
end

# AFTER:
for geo ∈ geographic_elements
    # Get only the relevant pairs for this geo (O(1) lookup)
    if !haskey(p_r_k_g_by_geo, geo.id)
        continue  # No traffic through this element
    end

    relevant_pairs = p_r_k_g_by_geo[geo.id]

    for p_r_k_g ∈ relevant_pairs
        # No filtering needed - all pairs are already relevant!
        # ... constraint code ...
    end
end
```

**Key improvement:**
- Pre-filtering reduces inner loop from checking ALL pairs to checking only RELEVANT pairs
- For sparse networks, this can reduce iterations by 90%+

---

## Implementation Order

1. **Start with Priority 1** (bug fix) - safest, quickest win
2. **Then Priority 2** (dictionaries) - enables the other optimizations
3. **Then Priority 3** (constraint_fueling_demand) - uses dictionaries from step 2
4. **Finally Priority 4** (pre-filtering) - most complex but highest impact

---

## Testing Strategy

After each priority, run a quick validation:

```bash
cd examples/moving_loads_SM
julia SM.jl
```

**Check:**
1. Model runs without errors
2. Optimization completes successfully
3. Objective value matches baseline (within tolerance)
4. Timing shows improvement

**Baseline timing (before optimization):**
Record the "TOTAL TIME" from SM.jl output before starting.

**Expected timing (after all 4 priorities):**
Should be 3-4x faster than baseline.

---

## Rollback Plan

If something breaks:
- Git commit before each priority
- Can revert individual changes with:
  ```bash
  git checkout HEAD~1 -- src/support_functions.jl
  git checkout HEAD~1 -- src/model_functions.jl
  ```

---

## Notes

- All optimizations preserve exact mathematical behavior
- No approximations or algorithmic changes
- Results should match baseline within numerical tolerance
- Focus is on reducing redundant computations

---

## If Time Runs Short

**Minimum viable optimization (2 hours):**
- Priority 1: Bug fix (15 min)
- Priority 2: Just add dictionaries, don't replace all findfirst() calls (30 min)
- Priority 3: constraint_fueling_demand optimization (60 min)
- Quick test (15 min)

This minimal set should still give **2-3x speedup**.
