# TransComp.jl Performance Optimization Plan

**Date:** 2025-10-15
**Target Files:** `src/support_functions.jl`, `src/model_functions.jl`
**Expected Overall Speedup:** 5-10x faster model creation and constraint generation

---

## Executive Summary

This document provides a detailed analysis of performance bottlenecks in the TransComp.jl optimization model and concrete recommendations for improvement. The model processes large-scale transportation problems with nested loops over years (y), OD-pairs (r), vehicles (tv), generations (g), paths (k), and geographic elements (geo). Even small inefficiencies compound dramatically when dealing with millions of variables and constraints.

**Key Finding:** The primary bottleneck is repeated linear searches using `findfirst()` in tight loops, which can be replaced with O(1) dictionary lookups. Secondary issues include filtering inside constraint loops instead of pre-filtering, and recalculating invariant expressions.

---

## Critical Optimization Patterns

### Pattern 1: Replace findfirst() with Dictionary Lookups
**Current Cost:** O(n) linear search per call
**Optimized Cost:** O(1) dictionary lookup
**Impact:** Orders of magnitude faster in tight loops

### Pattern 2: Pre-filter Sets Before Loops
**Current Cost:** Filter with `if` condition on every iteration
**Optimized Cost:** Pre-filter once, iterate only relevant items
**Impact:** Dramatically reduces iteration count

### Pattern 3: Hoist Invariant Calculations
**Current Cost:** Recalculate same value every iteration
**Optimized Cost:** Calculate once, reuse
**Impact:** Eliminates redundant arithmetic operations

### Pattern 4: Build Index Structures
**Current Cost:** Iterate entire lists to find matches
**Optimized Cost:** Pre-build lookups by key
**Impact:** O(n) → O(1) for lookups

---

## Function-by-Function Analysis

## 1. get_input_data() - YAML File Reading
**Location:** `support_functions.jl:23-230`
**Current Performance:** Good
**Priority:** None
**Recommendation:** No changes needed - already well optimized

---

## 2. parse_data() - Data Structure Parsing
**Location:** `support_functions.jl:243-992`
**Current Performance:** Moderate
**Priority:** HIGH

### Problem
Extensive use of `findfirst()` in loops for lookups:
```julia
# Line 287 - Called for EVERY element in EVERY path sequence:
geographic_element_list[findfirst(geo -> geo.id == el, geographic_element_list)]

# Lines 310-315 - Called for every mode in odpair:
modes[findfirst(m -> m.id == mode_id, modes)]
```

### Optimization 2.1: Pre-build All Lookup Dictionaries
**Impact:** HIGH (20-40% speedup)
**Difficulty:** Medium
**Risk:** Low
**Lines to Modify:** 244-495

**Implementation:**
```julia
# After building all lists (around line 260), add:

# Create lookup dictionaries for O(1) access
geo_element_dict = Dict(geo.id => geo for geo in geographic_element_list)
financial_status_dict = Dict(fs.id => fs for fs in financial_status_list)
mode_dict = Dict(m.id => m for m in mode_list)
product_dict = Dict(p.name => p for p in product_list)
fuel_dict = Dict(f.name => f for f in fuel_list)
technology_dict = Dict(t.id => t for t in technology_list)
vehicle_type_dict = Dict(vt.name => vt for vt in vehicle_type_list)
techvehicle_dict = Dict(tv.id => tv for tv in techvehicle_list)
path_dict = Dict(p.id => p for p in path_list)
fueling_infr_type_dict = Dict(fit.id => fit for fit in fueling_infr_types_list)
```

**Then replace all findfirst() calls:**
```julia
# BEFORE (line 287):
geographic_element_list[findfirst(geo -> geo.id == el, geographic_element_list)]

# AFTER:
geo_element_dict[el]

# BEFORE (line 311):
modes[findfirst(m -> m.id == mode_id, modes)]

# AFTER:
mode_dict[mode_id]

# Apply pattern throughout parse_data()
```

**Testing:** Verify odpair_list, path_list have identical structure after change.

---

## 3. create_model() & base_define_variables()
**Location:** `model_functions.jl:18-313`
**Current Performance:** Excellent
**Priority:** None
**Recommendation:** Already well-optimized with selective variable creation

---

## 4. constraint_demand_coverage()
**Location:** `model_functions.jl:324-349`
**Current Performance:** Moderate
**Priority:** HIGH

### Problem
Triple nested loop with conditional filtering inside:
```julia
# Line 333 - Filter mv[1] == 1 checked on EVERY iteration:
sum(
    model[:f][y, (r.product.id, r.id, k.id), mv, g]
    for k ∈ r.paths
    for mv ∈ data_structures["m_tv_pairs"]
    for g ∈ data_structures["g_init"]:y
    if mv[1] == 1  # ← Filtering inside sum
)
```

### Optimization 4.1: Pre-filter m_tv_pairs by Mode
**Impact:** HIGH (30-50% speedup)
**Difficulty:** Easy
**Risk:** Low
**Lines to Modify:** In create_model() and 333-335

**Implementation:**
```julia
# In create_model() after m_tv_pairs is created (around line 130):
m_tv_by_mode = Dict{Int, Vector{Tuple{Int,Int}}}()
for mv in m_tv_pairs
    mode_id = mv[1]
    if !haskey(m_tv_by_mode, mode_id)
        m_tv_by_mode[mode_id] = Tuple{Int,Int}[]
    end
    push!(m_tv_by_mode[mode_id], mv)
end
data_structures["m_tv_by_mode"] = m_tv_by_mode

# In constraint_demand_coverage (line 333):
# BEFORE:
for mv ∈ data_structures["m_tv_pairs"] for g ∈ ... if mv[1] == 1

# AFTER:
for mv ∈ data_structures["m_tv_by_mode"][1] for g ∈ ...
```

**Testing:** Verify constraint count is identical.

---

## 5. constraint_vehicle_sizing()
**Location:** `model_functions.jl:360-476`
**Current Performance:** Poor
**Priority:** VERY HIGH

### Problem
Repeated `findfirst()` calls inside constraint loop:
```julia
# Lines 397-403 - Called for EVERY constraint iteration:
modes[findfirst(m -> m.id == mv[1], modes)].quantify_by_vehs
techvehicle_list[findfirst(v0 -> v0.id == mv[2], techvehicle_list)].W[g-g_init+1]
techvehicle_list[findfirst(v0 -> v0.id == mv[2], techvehicle_list)].AnnualRange[g-g_init+1]
# ^^^ Same findfirst() called twice in same expression!
```

### Optimization 5.1: Pre-compute Tech Vehicle Properties
**Impact:** VERY HIGH (50-70% speedup)
**Difficulty:** Medium
**Risk:** Low
**Lines to Modify:** In create_model() and 385-476

**Implementation:**
```julia
# In create_model() before constraint functions (around line 200):
tv_properties = Dict{Int, Dict{String, Any}}()
for tv in techvehicle_list
    tv_properties[tv.id] = Dict(
        "mode_id" => tv.vehicle_type.mode.id,
        "mode_quantify_by_vehs" => tv.vehicle_type.mode.quantify_by_vehs,
        "W" => tv.W,
        "AnnualRange" => tv.AnnualRange,
        "spec_cons" => tv.spec_cons,
        "tank_capacity" => tv.tank_capacity
    )
end
data_structures["tv_properties"] = tv_properties

# In constraint_vehicle_sizing (lines 385-407):
# BEFORE:
@constraint(
    model,
    [y in y_init:Y_end, r in odpairs, mv in m_tv_pairs, g in g_init:Y_end;
        modes[findfirst(m -> m.id == mv[1], modes)].quantify_by_vehs && g <= y],
    model[:h][y, r.id, mv[2], g] >= sum(
        (k.length / (
            techvehicle_list[findfirst(v0 -> v0.id == mv[2], techvehicle_list)].W[g-g_init+1] *
            techvehicle_list[findfirst(v0 -> v0.id == mv[2], techvehicle_list)].AnnualRange[g-g_init+1]
        )) * 1000 * model[:f][y, (r.product.id, r.id, k.id), mv, g]
        for k ∈ r.paths
    )
)

# AFTER:
@constraint(
    model,
    [y in y_init:Y_end, r in odpairs, mv in m_tv_pairs, g in g_init:Y_end;
        tv_properties[mv[2]]["mode_quantify_by_vehs"] && g <= y],
    begin
        g_idx = g - g_init + 1
        model[:h][y, r.id, mv[2], g] >= sum(
            (k.length / (
                tv_properties[mv[2]]["W"][g_idx] *
                tv_properties[mv[2]]["AnnualRange"][g_idx]
            )) * 1000 * model[:f][y, (r.product.id, r.id, k.id), mv, g]
            for k ∈ r.paths
        )
    end
)
```

**Testing:** Verify constraint coefficients match exactly.

---

## 6. constraint_vehicle_aging()
**Location:** `model_functions.jl:490-690`
**Current Performance:** Good
**Priority:** LOW

### Optimization 6.1: Pre-allocate Index Sets
**Impact:** LOW-MEDIUM (5-10% speedup)
**Difficulty:** Easy
**Risk:** None

**Implementation:**
```julia
# BEFORE (lines 498-503):
all_indices = [
    (y, g, r, tv) for y ∈ y_init:Y_end, g ∈ g_init:Y_end, r ∈ odpairs, tv ∈ techvehicles
]
selected_indices = filter(t -> t[2] <= t[1], all_indices)

# AFTER - Filter during comprehension:
selected_indices = [
    (y, g, r, tv)
    for y ∈ y_init:Y_end
    for g ∈ g_init:min(y, Y_end)
    for r ∈ odpairs
    for tv ∈ techvehicles
]
```

---

## 7. constraint_fueling_demand()
**Location:** `model_functions.jl:1257-1303`
**Current Performance:** Poor
**Priority:** CRITICAL

### Problem
Repeated `findfirst()` for path lookups - called 3+ times per constraint:
```julia
# Lines 1276-1282 - Same findfirst() called 3 times:
for el ∈ paths[findfirst(k0 -> k0.id == r_k[2], paths)].sequence
    if el == paths[findfirst(...)].sequence[1] || el == paths[findfirst(...)].sequence[end]
    # ^^^ THREE separate findfirst() calls for the SAME path!

# Line 1284:
paths[findfirst(p0 -> p0.id == r_k[2], paths)].length
# ^^^ FOURTH call to same findfirst()
```

### Optimization 7.1: Pre-build Path Dictionary
**Impact:** VERY HIGH (60-80% speedup)
**Difficulty:** Easy
**Risk:** None
**Lines to Modify:** In parse_data() (add dict) and 1274-1303

**Implementation:**
```julia
# Already implemented in parse_data() from Optimization 2.1:
# path_dict = Dict(path.id => path for path in path_list)
# Just add to data_structures if not already there

# In constraint_fueling_demand (lines 1274-1303):
# BEFORE:
for y ∈ y_init:Y_end
    for r_k ∈ r_k_pairs
        @constraint(
            model,
            sum(
                model[:s][y, (p.id, r_k[1], r_k[2], el.id), v.id] for
                el ∈ paths[findfirst(k0 -> k0.id == r_k[2], paths)].sequence
                if el == paths[findfirst(...)].sequence[1] || el == paths[findfirst(...)].sequence[end]
            ) == sum(
                ((v.spec_cons[g-g_init+1]) / v.W[g-g_init+1] *
                paths[findfirst(p0 -> p0.id == r_k[2], paths)].length) * ...
            )
        )
    end
end

# AFTER:
for y ∈ y_init:Y_end
    for r_k ∈ r_k_pairs
        path = path_dict[r_k[2]]  # Single lookup!
        path_origin = path.sequence[1]
        path_destination = path.sequence[end]

        @constraint(
            model,
            sum(
                model[:s][y, (p.id, r_k[1], r_k[2], el.id), v.id]
                for el ∈ path.sequence
                if el == path_origin || el == path_destination
            ) == sum(
                ((v.spec_cons[g-g_init+1]) / v.W[g-g_init+1] * path.length) * ...
            )
        )
    end
end
```

**Expected Benefit:** Eliminates 4+ findfirst() calls per constraint iteration.

---

## 8. constraint_fueling_infrastructure()
**Location:** `model_functions.jl:896-1115`
**Current Performance:** Poor
**Priority:** VERY HIGH

### Problem 1: Repeated findfirst() in Infrastructure Lookup
```julia
# Lines 923-925 - In tight loop:
initialfuelinginfr_list[findfirst(
    i -> i.fuel.name == f.name && i.allocation == geo.id,
    initialfuelinginfr_list,
)].installed_kW
```

### Problem 2: Filtering p_r_k_g_pairs by geo_id on Every Iteration
```julia
# Lines 929-931:
for p_r_k_g ∈ p_r_k_g_pairs
for tv ∈ techvehicles
if p_r_k_g[4] == geo.id  # ← Filter checked millions of times
```

### Optimization 8.1: Pre-build Fueling Infrastructure Index
**Impact:** HIGH (40-60% speedup)
**Difficulty:** Medium
**Risk:** Low

**Implementation:**
```julia
# In create_model() or parse_data():
infr_by_fuel_geo = Dict{Tuple{String, Int}, Float64}()
for infr in initialfuelinginfr_list
    key = (infr.fuel.name, infr.allocation)
    infr_by_fuel_geo[key] = get(infr_by_fuel_geo, key, 0.0) + infr.installed_kW
end
data_structures["infr_by_fuel_geo"] = infr_by_fuel_geo

# In constraint (line 923):
# BEFORE:
initial_kW = initialfuelinginfr_list[findfirst(...)].installed_kW

# AFTER:
initial_kW = get(infr_by_fuel_geo, (f.name, geo.id), 0.0)
```

### Optimization 8.2: Pre-filter p_r_k_g_pairs by geo_id
**Impact:** VERY HIGH (50-70% speedup)
**Difficulty:** Medium
**Risk:** Low

**Implementation:**
```julia
# In create_model() after p_r_k_g_pairs is built:
p_r_k_g_by_geo = Dict{Int, Vector}()
for prkg in p_r_k_g_pairs
    geo_id = prkg[4]
    if !haskey(p_r_k_g_by_geo, geo_id)
        p_r_k_g_by_geo[geo_id] = []
    end
    push!(p_r_k_g_by_geo[geo_id], prkg)
end
data_structures["p_r_k_g_by_geo"] = p_r_k_g_by_geo

# In constraint (lines 929-931):
# BEFORE:
sum(
    gamma * 1000 * model[:s][y, p_r_k_g, tv.id, g]
    for g in g_init:y
    for p_r_k_g ∈ p_r_k_g_pairs
    for tv ∈ techvehicles
    if p_r_k_g[4] == geo.id && tv.technology.fuel.name == f.name
)

# AFTER:
sum(
    gamma * 1000 * model[:s][y, p_r_k_g, tv.id, g]
    for g in g_init:y
    for p_r_k_g ∈ p_r_k_g_by_geo[geo.id]  # Pre-filtered!
    for tv ∈ techvehicles
    if tv.technology.fuel.name == f.name
)
```

**Expected Benefit:** If you have 100 geo elements and 10,000 p_r_k_g_pairs, this reduces iterations from 1,000,000 to 100,000.

---

## 9. constraint_fueling_infrastructure_expansion_shift()
**Location:** `model_functions.jl:3062-3219`
**Current Performance:** Moderate
**Priority:** MEDIUM

### Optimization 9.1: Pre-filter Fuel Infrastructure Types
**Impact:** MEDIUM (20-30% speedup)
**Difficulty:** Easy
**Risk:** None

**Implementation:**
```julia
# In create_model():
f_l_non_fossil = [f_l for f_l in f_l_pairs if f_l[1] != 1]
f_l_non_type1 = [f_l for f_l in f_l_pairs if f_l[2] != 1]
f_l_non_fossil_non_type1 = [f_l for f_l in f_l_pairs if f_l[1] != 1 && f_l[2] != 1]
data_structures["f_l_non_fossil"] = f_l_non_fossil
data_structures["f_l_non_type1"] = f_l_non_type1
data_structures["f_l_non_fossil_non_type1"] = f_l_non_fossil_non_type1

# Also pre-compute initial infrastructure by geo:
init_infr_by_geo_fuel = Dict{Tuple{Int,Int}, Float64}()
for item in initialfuelinfr_list
    key = (item.allocation, item.fuel.id)
    init_infr_by_geo_fuel[key] = get(init_infr_by_geo_fuel, key, 0.0) + item.installed_kW
end
data_structures["init_infr_by_geo_fuel"] = init_infr_by_geo_fuel

# In constraint (line 3106):
# BEFORE:
sum(model[:q_fuel_infr_plus][y_init, f_l, geo.id] for f_l in f_l_pairs if f_l[1] != 1 && f_l[2] != 1)

# AFTER:
sum(model[:q_fuel_infr_plus][y_init, f_l, geo.id] for f_l in f_l_non_fossil_non_type1)

# In constraint (line 3118):
# BEFORE:
sum(item.installed_kW for item in initialfuelinfr_list if item.allocation == geo.id && item.fuel.id == 2)

# AFTER:
get(init_infr_by_geo_fuel, (geo.id, 2), 0.0)
```

---

## 10. constraint_soc_max()
**Location:** `model_functions.jl:3272-3292`
**Current Performance:** Good (already has path_dict on line 3283)
**Priority:** MEDIUM

### Optimization 10.1: Hoist Repeated Calculations
**Impact:** MEDIUM (15-25% speedup)
**Difficulty:** Easy
**Risk:** None

**Implementation:**
```julia
# BEFORE (lines 3285-3290):
for g in g_init:Y_end
    @constraint(
        model,
        [y in y_init:Y_end, prkg in p_r_k_g_pairs, f_l in f_l_pairs, tv in techvehicle_list;
         g <= y && tv.technology.fuel.id == f_l[1]],
        model[:soc][y, prkg, tv.id, f_l, g] <=
            tv.tank_capacity[g-g_init+1] * (
                path_dict[prkg[3]].length /
                (tv.W[g-g_init+1] * tv.AnnualRange[g-g_init+1])
            ) * 1000 * model[:f][y, (prkg[1], prkg[2], prkg[3]), (tv.vehicle_type.mode.id, tv.id), g]
    )
end

# AFTER - hoist calculations outside:
for g in g_init:Y_end
    g_idx = g - g_init + 1
    for y in y_init:Y_end
        if g > y
            continue
        end
        for prkg in p_r_k_g_pairs
            path_length = path_dict[prkg[3]].length  # Calculate once
            for f_l in f_l_pairs
                for tv in techvehicle_list
                    if tv.technology.fuel.id == f_l[1]
                        # Pre-compute capacity factor
                        capacity_factor = tv.tank_capacity[g_idx] /
                                        (tv.W[g_idx] * tv.AnnualRange[g_idx])

                        @constraint(
                            model,
                            model[:soc][y, prkg, tv.id, f_l, g] <=
                                capacity_factor * path_length * 1000 *
                                model[:f][y, (prkg[1], prkg[2], prkg[3]),
                                         (tv.vehicle_type.mode.id, tv.id), g]
                        )
                    end
                end
            end
        end
    end
end
```

**Note:** This trades JuMP's macro indexing for explicit loops, which may or may not be faster depending on JuMP internals. Test both approaches.

---

## 11. constraint_soc_track()
**Location:** `model_functions.jl:3294-3389`
**Current Performance:** Moderate
**Priority:** HIGH

### Problem
7-level nested loops with repeated calculations:
```julia
# Deeply nested: r → path → sequence → y → tv → f_l → g
# Line 3326 & 3370: num_vehicles calculated twice with same formula
# Lines 3314-3342: Filtering by geo_id == path.sequence[1].id for every prkg
```

### Optimization 11.1: Pre-index Paths by Origin/Destination
**Impact:** HIGH (30-50% speedup for origin/destination constraints)
**Difficulty:** Medium
**Risk:** Low

**Implementation:**
```julia
# In create_model() after paths are available:
prkg_by_path_origin = Dict{Tuple{Int,Int}, Vector}()
prkg_by_path_destination = Dict{Tuple{Int,Int}, Vector}()

for prkg in p_r_k_g_pairs
    path = path_dict[prkg[3]]
    origin_id = path.sequence[1].id
    destination_id = path.sequence[end].id

    # Index by (path_id, origin_geo_id)
    if prkg[4] == origin_id
        key = (prkg[3], origin_id)
        if !haskey(prkg_by_path_origin, key)
            prkg_by_path_origin[key] = []
        end
        push!(prkg_by_path_origin[key], prkg)
    end

    # Index by (path_id, destination_geo_id)
    if prkg[4] == destination_id
        key = (prkg[3], destination_id)
        if !haskey(prkg_by_path_destination, key)
            prkg_by_path_destination[key] = []
        end
        push!(prkg_by_path_destination[key], prkg)
    end
end

data_structures["prkg_by_path_origin"] = prkg_by_path_origin
data_structures["prkg_by_path_destination"] = prkg_by_path_destination

# In constraint (lines 3311-3342):
# BEFORE:
for y in y_init:Y_end
    for prkg in p_r_k_g_pairs
        path = path_dict[prkg[3]]
        if geo_id == path.sequence[1].id  # Origin constraint
            # ... constraints

# AFTER:
for y in y_init:Y_end
    for path in path_list
        origin_id = path.sequence[1].id
        origin_prkgs = get(prkg_by_path_origin, (path.id, origin_id), [])
        for prkg in origin_prkgs
            # ... constraints (no conditional check needed!)
```

### Optimization 11.2: Pre-compute Vehicle Factors
**Impact:** MEDIUM (20-30% speedup)
**Difficulty:** Easy
**Risk:** None

**Implementation:**
```julia
# Use tv_properties from Optimization 5.1:
# BEFORE (lines 3326, 3370):
spec_cons = tv.spec_cons[g-g_init+1]
num_vehicles = (path.length / (tv.W[g-g_init+1] * tv.AnnualRange[g-g_init+1])) * 1000 * ...

# AFTER:
g_idx = g - g_init + 1
spec_cons = tv_properties[tv.id]["spec_cons"][g_idx]
W = tv_properties[tv.id]["W"][g_idx]
AnnualRange = tv_properties[tv.id]["AnnualRange"][g_idx]
num_vehicles = (path.length / (W * AnnualRange)) * 1000 * ...
```

---

## 12. constraint_travel_time_track()
**Location:** `model_functions.jl:3391-3502`
**Current Performance:** Poor (contains bug)
**Priority:** CRITICAL (BUG FIX)

### Problem 1: DUPLICATED CODE (BUG!)
```julia
# Lines 3392-3401:
y_init = data_structures["y_init"]
Y_end = data_structures["Y_end"]
odpairs = data_structures["odpair_list"]
# ... etc

# Lines 3404-3413: EXACT DUPLICATE!
y_init = data_structures["y_init"]  # ← DUPLICATE
Y_end = data_structures["Y_end"]    # ← DUPLICATE
odpairs = data_structures["odpair_list"]  # ← DUPLICATE
# ... etc
```

### Optimization 12.1: Fix Duplicated Code
**Impact:** MEDIUM (10-20% speedup + bug fix)
**Difficulty:** Trivial
**Risk:** None
**Lines to Modify:** 3404-3413

**Implementation:**
```julia
# DELETE lines 3404-3413 entirely
# They are exact duplicates of lines 3392-3401
```

### Optimization 12.2: Pre-compute Speed Constant
**Impact:** LOW (5-10% speedup)
**Difficulty:** Trivial
**Risk:** None

**Implementation:**
```julia
# BEFORE (line 3449 - inside loop):
speed = data_structures["speed_list"][1].travel_speed

# AFTER (move to function start, line 3414):
speed = data_structures["speed_list"][1].travel_speed  # Moved outside loops
```

### Optimization 12.3: Apply Same Optimizations as constraint_soc_track()
- Use prkg_by_path_origin/destination (Optimization 11.1)
- Use tv_properties (Optimization 11.2)

---

## 13. constraint_mandatory_breaks()
**Location:** `model_functions.jl:3504-3611`
**Current Performance:** Good (has breaks_by_path optimization)
**Priority:** LOW

### Optimization 13.1: Pre-build Geo-in-Path Lookup
**Impact:** MEDIUM (20-30% speedup when breaks are used)
**Difficulty:** Easy
**Risk:** None

**Implementation:**
```julia
# In parse_data() when building paths:
geo_in_path = Dict{Int, Set{Int}}()
for path in path_list
    geo_in_path[path.id] = Set(geo.id for geo in path.sequence)
end
data_structures["geo_in_path"] = geo_in_path

# In constraint (lines 3562-3573):
# BEFORE:
geo_found = false
for geo_element in path.sequence
    if geo_element.id == break_geo_id
        geo_found = true
        break
    end
end
if !geo_found
    @warn "Break location geo_id=$(break_geo_id) not found..."
    continue
end

# AFTER:
if break_geo_id ∉ geo_in_path[path.id]
    @warn "Break location geo_id=$(break_geo_id) not found in path $(path.id)"
    continue
end
```

**Expected Benefit:** O(n) → O(1) lookup for geo validation

---

## 14. objective()
**Location:** `model_functions.jl:3669-4394`
**Current Performance:** Good
**Priority:** LOW

### Optimization 14.1: Use geo_elements_in_paths Consistently
**Impact:** MEDIUM (15-30% speedup for some cost components)
**Difficulty:** Easy
**Risk:** None

**Note:** The code already extracts `geo_elements_in_paths` at line 3712. Review objective function to ensure this is used everywhere instead of iterating over full `geographic_element_list`.

### Optimization 14.2: Pre-compute Discount Factors
**Impact:** LOW (< 5% speedup)
**Difficulty:** Trivial
**Risk:** None

**Implementation:**
```julia
# At function start (around line 3700):
discount_factors = Dict(y => 1/((1 + discount_rate)^(y - y_init)) for y in y_init:Y_end)

# Then replace all instances of:
# 1/((1 + discount_rate)^(y - y_init))
# with:
# discount_factors[y]
```

---

## 15. save_results()
**Location:** `support_functions.jl:1402-1802`
**Current Performance:** Moderate (I/O bound)
**Priority:** None

**Recommendation:** Already well-optimized (saves only non-zero values). YAML serialization is inherently slow. Further optimization would require changing output format (e.g., HDF5, Arrow).

---

## Implementation Roadmap

### Phase 1: Quick Wins (1-2 days)
**Goal:** 2-3x faster

1. **Fix duplicated code bug** (Optimization 12.1)
   - Delete lines 3404-3413 in constraint_travel_time_track()
   - Move speed calculation outside loop (12.2)
   - Test: 15 minutes

2. **Add path_dict to parse_data** (Optimization 2.1 partial)
   - Add path dictionary creation
   - Use in constraint_fueling_demand() (7.1)
   - Test: 30 minutes

3. **Pre-filter m_tv_pairs by mode** (Optimization 4.1)
   - Create m_tv_by_mode in create_model()
   - Update constraint_demand_coverage()
   - Test: 30 minutes

4. **Pre-compute speed constant** (Optimization 12.2)
   - Already included in step 1

**Testing:** Run on small test case, verify identical results.

### Phase 2: Core Optimizations (3-5 days)
**Goal:** 4-6x faster (cumulative)

5. **Complete lookup dictionaries in parse_data** (Optimization 2.1 full)
   - Add all lookup dicts (geo, mode, product, fuel, tech, vehicle, etc.)
   - Replace all findfirst() calls with dict lookups
   - Test: 2-3 hours

6. **Add tv_properties pre-computation** (Optimization 5.1)
   - Create tv_properties dict in create_model()
   - Update constraint_vehicle_sizing()
   - Update constraint_soc_track() (11.2)
   - Update constraint_travel_time_track() (12.3)
   - Test: 1-2 hours

7. **Add p_r_k_g_by_geo indexing** (Optimization 8.2)
   - Create index in create_model()
   - Update constraint_fueling_infrastructure()
   - Test: 1 hour

8. **Add infr_by_fuel_geo lookup** (Optimization 8.1)
   - Create lookup in create_model() or parse_data()
   - Update constraint_fueling_infrastructure()
   - Test: 1 hour

**Testing:** Run on medium test case, verify constraint counts and values.

### Phase 3: Advanced Optimizations (2-3 days)
**Goal:** 5-10x faster (cumulative)

9. **Path origin/destination indexing** (Optimization 11.1)
   - Create prkg_by_path_origin/destination
   - Update constraint_soc_track()
   - Update constraint_travel_time_track()
   - Test: 2 hours

10. **Fueling infrastructure type pre-filtering** (Optimization 9.1)
    - Create filtered sets in create_model()
    - Update constraint_fueling_infrastructure_expansion_shift()
    - Test: 1 hour

11. **Geo-in-path lookup** (Optimization 13.1)
    - Create set during path creation
    - Update constraint_mandatory_breaks()
    - Test: 30 minutes

12. **Hoist SOC calculations** (Optimization 10.1)
    - Restructure constraint_soc_max() loops
    - Test and benchmark both approaches
    - Test: 1-2 hours

**Testing:** Run full-scale test case, compare timing and results.

### Phase 4: Validation & Documentation (2-3 days)

13. **Comprehensive Testing**
    - Run all test cases
    - Compare results with baseline (should be identical)
    - Benchmark all constraint functions individually
    - Profile memory usage

14. **Performance Benchmarking**
    - Document speedup for each optimization
    - Create before/after timing charts
    - Identify any remaining bottlenecks

15. **Code Review & Documentation**
    - Add comments explaining optimizations
    - Update function docstrings
    - Document any API changes
    - Create migration guide if needed

---

## Testing Strategy

### Unit Tests
For each optimization, create test that verifies:
1. **Correctness:** Results identical to baseline
2. **Constraint count:** Number of constraints unchanged
3. **Variable values:** Solution values match
4. **Performance:** Measure actual speedup

### Test Cases
1. **Tiny:** 2 years, 5 OD-pairs, 2 vehicles (fast iteration)
2. **Small:** 5 years, 20 OD-pairs, 3 vehicles (quick testing)
3. **Medium:** 10 years, 50 OD-pairs, 3 vehicles (realistic)
4. **Full:** 21 years, 100+ OD-pairs, 3 vehicles (production)

### Validation Checks
```julia
# After each optimization, verify:
function validate_optimization(baseline_results, optimized_results)
    # Check constraint counts
    @assert num_constraints(baseline_model) == num_constraints(optimized_model)

    # Check variable values (within tolerance)
    for (var_name, var_dict) in baseline_results
        for (key, baseline_value) in var_dict
            optimized_value = optimized_results[var_name][key]
            @assert isapprox(baseline_value, optimized_value, rtol=1e-6)
        end
    end

    # Check objective value
    @assert isapprox(objective_value(baseline_model),
                     objective_value(optimized_model),
                     rtol=1e-6)
end
```

---

## Risk Mitigation

### Type Stability
**Risk:** Dictionary lookups may introduce type instabilities
**Mitigation:**
```julia
# Use typed dictionaries:
geo_element_dict = Dict{Int, GeographicElement}()  # Not Dict()
tv_properties = Dict{Int, Dict{String, Any}}()     # Explicit types
```

### Memory Usage
**Risk:** Pre-computing all lookups increases memory
**Mitigation:**
- Profile memory usage with `@time` and `@allocated`
- Dictionaries are usually small compared to JuMP model
- Modern systems have plenty of RAM for these structures

### Correctness
**Risk:** Optimization errors could change model behavior
**Mitigation:**
- Implement comprehensive unit tests
- Start with small test cases
- Validate constraint counts and values
- Use `isapprox()` for floating-point comparisons
- Keep baseline version for reference

### Maintenance
**Risk:** More complex code harder to maintain
**Mitigation:**
- Document all optimizations with comments
- Keep code style consistent
- Use descriptive variable names
- Add function docstrings explaining pre-computation

### Debugging
**Risk:** Harder to debug optimized code
**Mitigation:**
- Add `@debug` statements for key lookups
- Create validation functions that can be toggled
- Keep baseline version for comparison

---

## Performance Measurement

### Benchmarking Code
```julia
using BenchmarkTools

# Benchmark individual constraint functions
function benchmark_constraint(constraint_fn, model, data_structures)
    @btime $constraint_fn($model, $data_structures)
end

# Compare baseline vs optimized
function compare_performance(baseline_fn, optimized_fn, model, data_structures)
    println("Baseline:")
    @btime $baseline_fn($model, $data_structures)

    println("\nOptimized:")
    @btime $optimized_fn($model, $data_structures)
end

# Full model benchmark
function benchmark_full_model()
    times = Dict()

    times["data_load"] = @elapsed data_dict = get_input_data(file)
    times["data_parse"] = @elapsed data_structures = parse_data(data_dict)
    times["model_create"] = @elapsed model, data_structures = create_model(...)
    times["constraint_demand"] = @elapsed constraint_demand_coverage(...)
    times["constraint_vehicle_sizing"] = @elapsed constraint_vehicle_sizing(...)
    # ... etc

    return times
end
```

### Expected Results
Based on analysis, expected speedups per function:

| Function | Baseline Time | Expected Speedup | Optimized Time |
|----------|---------------|------------------|----------------|
| parse_data | 2.3s | 1.3-1.5x | 1.5-1.8s |
| constraint_demand_coverage | 0.5s | 1.3-1.5x | 0.3-0.4s |
| constraint_vehicle_sizing | 2.9s | 2.0-2.5x | 1.2-1.5s |
| constraint_fueling_demand | 3.9s | 2.5-3.0x | 1.3-1.6s |
| constraint_fueling_infrastructure | 7.2s | 3.0-4.0x | 1.8-2.4s |
| constraint_soc_track | 3.2s | 1.5-2.0x | 1.6-2.1s |
| constraint_soc_max | 4.7s | 1.2-1.5x | 3.1-3.9s |
| constraint_travel_time_track | 6.2s | 1.2-1.5x | 4.1-5.2s |
| **TOTAL CONSTRAINTS** | **~35s** | **2.0-3.0x** | **12-18s** |

---

## Common Pitfalls to Avoid

### 1. Over-optimization
**Don't:** Optimize code that runs once or is already fast
**Do:** Focus on hot loops identified by profiling

### 2. Premature Abstraction
**Don't:** Create complex abstractions before testing
**Do:** Start simple, refactor after validation

### 3. Breaking Correctness
**Don't:** Assume optimization is correct without testing
**Do:** Validate every change with unit tests

### 4. Ignoring Type Stability
**Don't:** Use untyped containers or `Any` unnecessarily
**Do:** Specify types for dictionaries and arrays

### 5. Memory Waste
**Don't:** Create duplicate data structures
**Do:** Reuse and share pre-computed data

### 6. Poor Error Handling
**Don't:** Remove validation checks entirely
**Do:** Keep essential checks, optimize non-critical ones

---

## Maintenance Guidelines

### Adding New Constraints
When adding new constraint functions:

1. **Use existing lookups:**
```julia
# Good:
path = path_dict[path_id]
tv_props = tv_properties[tv_id]

# Bad:
path = paths[findfirst(p -> p.id == path_id, paths)]
```

2. **Pre-filter when possible:**
```julia
# Good:
for mv in m_tv_by_mode[mode_id]

# Bad:
for mv in m_tv_pairs
    if mv[1] == mode_id
```

3. **Hoist invariant calculations:**
```julia
# Good:
g_idx = g - g_init + 1
for ...
    value = array[g_idx]

# Bad:
for ...
    value = array[g - g_init + 1]
```

### Updating Data Structures
When modifying structs:

1. Update lookup dictionaries in parse_data()
2. Update tv_properties if vehicle fields change
3. Update index structures if keys change
4. Run full test suite

### Code Review Checklist
- [ ] Are all `findfirst()` calls necessary?
- [ ] Can any filtering be done outside loops?
- [ ] Are calculations hoisted when possible?
- [ ] Are lookup dictionaries used consistently?
- [ ] Is the code still readable?
- [ ] Are there sufficient comments?
- [ ] Do unit tests pass?
- [ ] Is performance improved?

---

## Conclusion

This optimization plan provides a structured approach to dramatically improve TransComp.jl performance. The key insight is that **repeated linear searches are the primary bottleneck**, easily addressed with dictionary lookups and pre-filtering.

### Key Takeaways

1. **High-Impact, Low-Risk:** Most optimizations are straightforward replacements with minimal risk
2. **Cumulative Effect:** Small improvements in tight loops compound to major speedups
3. **Test-Driven:** Every optimization must be validated against baseline
4. **Maintainable:** Optimized code can be clean and readable with good organization

### Expected Outcomes

- **5-10x faster** overall model creation and constraint generation
- **Reduced memory allocations** through pre-computation
- **Better scalability** for larger problem instances
- **Same correct results** as baseline implementation

### Next Steps

1. Create baseline benchmark with current code
2. Implement Phase 1 quick wins (2-3x speedup)
3. Validate results match baseline
4. Continue with Phase 2 and 3 optimizations
5. Document final performance improvements

**Good luck with the optimization work!**
