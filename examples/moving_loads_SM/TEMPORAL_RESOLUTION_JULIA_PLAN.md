# Variable Temporal Resolution - Julia Model Implementation Plan

## Overview

This document details the Julia code changes needed to support variable temporal resolution in the TransComp model. The implementation allows the model to operate at different temporal resolutions (annual, biennial, quinquennial, etc.) while maintaining annual cost and demand data arrays.

**Key Principle:** Replace all hardcoded year ranges (`y_init:Y_end`) with dynamic sets (`modeled_years`) that respect the `time_step` parameter.

---

## Files Requiring Changes

| File | Purpose | Complexity | Lines to Change |
|------|---------|------------|-----------------|
| `src/support_functions.jl` | Create modeled year/generation sets | Low | ~10 lines |
| `src/model_functions.jl` | Update variable definitions | Medium | ~40 locations |
| `src/model_functions.jl` | Update constraint functions | High | ~100+ locations |
| `src/checks.jl` | Update validation logic | Low | ~5 locations |
| Example files (e.g., `SM.jl`) | Update calls if needed | Low | 0-5 lines |

---

## Implementation Steps

### Step 1: Create Modeled Year/Generation Sets

**File:** `src/support_functions.jl`
**Function:** `parse_data()`
**Current location:** Line ~1010-1015

#### Current Code
```julia
data_structures["G"] = data_dict["Model"]["pre_y"] + data_dict["Model"]["Y"]
data_structures["g_init"] = data_dict["Model"]["y_init"] - data_dict["Model"]["pre_y"]
data_structures["Y_end"] = data_dict["Model"]["y_init"] + data_dict["Model"]["Y"] - 1
```

#### New Code to Add
```julia
# Existing calculations
data_structures["G"] = data_dict["Model"]["pre_y"] + data_dict["Model"]["Y"]
data_structures["g_init"] = data_dict["Model"]["y_init"] - data_dict["Model"]["pre_y"]
data_structures["Y_end"] = data_dict["Model"]["y_init"] + data_dict["Model"]["Y"] - 1

# NEW: Get temporal resolution parameter (default to 1 for backward compatibility)
time_step = get(data_dict["Model"], "time_step", 1)
data_structures["time_step"] = time_step

# NEW: Create set of modeled years (years actually optimized)
y_init = data_dict["Model"]["y_init"]
Y_end = data_structures["Y_end"]
modeled_years = collect(y_init:time_step:Y_end)
data_structures["modeled_years"] = modeled_years

# NEW: Create set of modeled generations (vehicle purchase years including pre-period)
g_init = data_structures["g_init"]
modeled_generations = collect(g_init:time_step:Y_end)
data_structures["modeled_generations"] = modeled_generations

# NEW: Update investment years to align with modeled years
investment_period = data_dict["Model"]["investment_period"]
investment_years = [y for y in modeled_years if (y - y_init) % investment_period == 0]
data_structures["investment_years"] = investment_years

@info "Temporal resolution settings:"
@info "  time_step: $(time_step) year(s)"
@info "  Modeled years: $(length(modeled_years)) years from $(minimum(modeled_years)) to $(maximum(modeled_years))"
@info "  Modeled generations: $(length(modeled_generations)) generations from $(minimum(modeled_generations)) to $(maximum(modeled_generations))"
@info "  Investment years: $(length(investment_years)) years"
```

**Impact:**
- Adds 4 new keys to `data_structures` dictionary
- Provides sets that respect `time_step` parameter
- Backward compatible: `time_step=1` gives same results as before

---

### Step 2: Update Variable Definitions

**File:** `src/model_functions.jl`
**Function:** `base_define_variables()`
**Starting location:** Line ~58

#### Changes Needed

All variable definitions that iterate over years need to be updated. The pattern is:

**OLD:** `y in y_init:Y_end`
**NEW:** `y in modeled_years`

**OLD:** `g in g_init:Y_end`
**NEW:** `g in modeled_generations`

#### Example Changes

##### Change 1: Vehicle Stock Variables (h, h_exist, h_plus, h_minus)

**Current (lines ~74-109):**
```julia
@variable(model, h[y in y_init:Y_end, r_id in [r.id for r ∈ odpairs], tv_id in techvehicle_ids, g in g_init:Y_end] >= 0)

@variable(model, h_exist[y in y_init:Y_end, r_id in [r.id for r ∈ odpairs], tv_id in techvehicle_ids, g in g_init:Y_end] >= 0)

@variable(model, h_plus[y in y_init:Y_end, r_id in [r.id for r ∈ odpairs], tv_id in techvehicle_ids, g in g_init:Y_end] >= 0)

@variable(model, h_minus[y in y_init:Y_end, r_id in [r.id for r ∈ odpairs], tv_id in techvehicle_ids, g in g_init:Y_end] >= 0)
```

**New:**
```julia
modeled_years = data_structures["modeled_years"]
modeled_generations = data_structures["modeled_generations"]

@variable(model, h[y in modeled_years, r_id in [r.id for r ∈ odpairs], tv_id in techvehicle_ids, g in modeled_generations; g <= y] >= 0)

@variable(model, h_exist[y in modeled_years, r_id in [r.id for r ∈ odpairs], tv_id in techvehicle_ids, g in modeled_generations; g <= y] >= 0)

@variable(model, h_plus[y in modeled_years, r_id in [r.id for r ∈ odpairs], tv_id in techvehicle_ids, g in modeled_generations; g <= y] >= 0)

@variable(model, h_minus[y in modeled_years, r_id in [r.id for r ∈ odpairs], tv_id in techvehicle_ids, g in modeled_generations; g <= y] >= 0)
```

**Note:** Added `g <= y` condition to ensure vehicles can only be used in years after purchase.

##### Change 2: Energy Consumption Variables (s)

**Current (line ~119):**
```julia
@variable(model, s[y in y_init:Y_end, p_r_k_g_pairs, tv_id in techvehicle_ids, g in g_init:Y_end] >= 0)
```

**New:**
```julia
@variable(model, s[y in modeled_years, p_r_k_g_pairs, tv_id in techvehicle_ids, g in modeled_generations; g <= y] >= 0)
```

##### Change 3: Infrastructure Variables (q_fuel_infr_plus)

**Current (line ~127):**
```julia
@variable(model, q_fuel_infr_plus[y in collect(y_init:investment_period:Y_end), f_id in [f.id for f ∈ fuel_list], geo_id in [geo.id for geo ∈ geographic_element_list]] >= 0)
```

**New:**
```julia
investment_years = data_structures["investment_years"]

@variable(model, q_fuel_infr_plus[y in investment_years, f_id in [f.id for f ∈ fuel_list], geo_id in [geo.id for geo ∈ geographic_element_list]] >= 0)
```

##### Change 4: Flow Variables (f)

**Current (line ~270):**
```julia
@variable(model, f[y in y_init:Y_end, p_r_k_pairs, m_tv_pairs, g in g_init:Y_end; g <= y] >= 0)
```

**New:**
```julia
@variable(model, f[y in modeled_years, p_r_k_pairs, m_tv_pairs, g in modeled_generations; g <= y] >= 0)
```

##### Change 5: Budget Penalty Variables

**Current (lines ~279-291):**
```julia
@variable(model, budget_penalty_plus[y in y_init:Y_end, r_id in [r.id for r ∈ odpairs]] >= 0)
@variable(model, budget_penalty_minus[y in y_init:Y_end, r_id in [r.id for r ∈ odpairs]] >= 0)
@variable(model, budget_penalty_yearly_plus[y in y_init:Y_end, r_id in [r.id for r ∈ odpairs]] >= 0)
@variable(model, budget_penalty_yearly_minus[y in y_init:Y_end, r_id in [r.id for r ∈ odpairs]] >= 0)
```

**New:**
```julia
@variable(model, budget_penalty_plus[y in modeled_years, r_id in [r.id for r ∈ odpairs]] >= 0)
@variable(model, budget_penalty_minus[y in modeled_years, r_id in [r.id for r ∈ odpairs]] >= 0)
@variable(model, budget_penalty_yearly_plus[y in modeled_years, r_id in [r.id for r ∈ odpairs]] >= 0)
@variable(model, budget_penalty_yearly_minus[y in modeled_years, r_id in [r.id for r ∈ odpairs]] >= 0)
```

#### Complete List of Variables to Update

In `base_define_variables()`, update ALL of the following:

1. ✅ `h`, `h_exist`, `h_plus`, `h_minus` (lines 74-109)
2. ✅ `s` (line 119 or 184)
3. ✅ `q_fuel_infr_plus` (lines 127, 175, 234, 239, 240)
4. ✅ `n_fueling` (lines 138, 191)
5. ✅ `detour_time` (lines 151, 204)
6. ✅ `x_c`, `a` (lines 158, 211, 212)
7. ✅ `z` (lines 162, 217)
8. ✅ `vot_dt` (lines 164, 219)
9. ✅ `q_fuel_abs` (line 241)
10. ✅ `soc` (line 247)
11. ✅ `travel_time` (line 254)
12. ✅ `extra_break_time` (line 260)
13. ✅ `f` (line 270)
14. ✅ `budget_penalty_*` (lines 279-291)
15. ✅ `q_mode_infr_plus` (line 301)
16. ✅ `q_supply_infr` (line 314)

**Estimated:** ~30-40 variable declarations need updating

---

### Step 3: Update Constraint Functions

**File:** `src/model_functions.jl`
**Functions:** All `constraint_*()` functions

#### Pattern to Follow

All constraint functions that loop over years need updating:

**OLD:**
```julia
for y in y_init:Y_end
    # constraint logic
end
```

**NEW:**
```julia
modeled_years = data_structures["modeled_years"]
for y in modeled_years
    # constraint logic
end
```

#### Constraint Functions Requiring Updates

Based on the codebase, these constraint functions need updates (estimated):

1. `constraint_vehicle_stock_balance()` - Update year loops
2. `constraint_vehicle_stock_shift()` - Update year loops
3. `constraint_fueling_infrastructure_capacity()` - Update year and investment year loops
4. `constraint_energy_consumption()` - Update year loops
5. `constraint_mode_shift()` - Update year loops
6. `constraint_emission_reduction()` - Update year loops
7. `constraint_monetary_budget()` - Update year loops
8. `constraint_detour_time()` - Update year loops
9. `objective()` - Update year loops in cost summations

**Estimated:** ~100-150 `for y in y_init:Y_end` replacements across all constraint functions

#### Important: Array Indexing

When accessing cost/demand arrays, the indexing must account for the year position:

**Current approach (annual, works as-is):**
```julia
for y in y_init:Y_end
    cost = tv.capital_cost[y - y_init + 1]  # Index: 1, 2, 3, ..., 41
end
```

**New approach (variable time_step, NO CHANGE NEEDED):**
```julia
for y in modeled_years  # e.g., [2020, 2022, 2024, ...]
    cost = tv.capital_cost[y - y_init + 1]  # Index: 1, 3, 5, ... (samples array)
end
```

**Key insight:** Because cost arrays remain annual with all 41 elements, we can sample them at modeled years without changing the indexing formula. The formula `y - y_init + 1` automatically gives us the correct position in the annual array.

**Example:**
- `time_step = 2`, modeled years: [2020, 2022, 2024]
- For y=2020: `capital_cost[2020 - 2020 + 1] = capital_cost[1]` ✅
- For y=2022: `capital_cost[2022 - 2020 + 1] = capital_cost[3]` ✅
- For y=2024: `capital_cost[2024 - 2020 + 1] = capital_cost[5]` ✅

**No changes needed to array access patterns!**

---

### Step 4: Update Objective Function

**File:** `src/model_functions.jl`
**Function:** `objective()`

#### Current Pattern
```julia
for y in y_init:Y_end
    # Sum costs for this year
    # Apply discount factor
end
```

#### New Pattern
```julia
modeled_years = data_structures["modeled_years"]
time_step = data_structures["time_step"]

for y in modeled_years
    # Sum costs for this year

    # Apply discount factor (same as before)
    discount_factor = (1 + discount_rate)^(y - y_init)

    # IMPORTANT: Multiply by time_step to account for period length
    # Each modeled year represents time_step years of costs
    total_cost += annual_cost * time_step / discount_factor
end
```

**Critical change:** When `time_step > 1`, each modeled year represents multiple years. The costs must be scaled by `time_step` to account for the full period.

**Example:**
- `time_step = 2`: Each modeled year represents 2 years of costs
- Year 2022 cost should count for both 2022 AND 2023
- Multiply cost by 2

**Alternative approach (more accurate discounting):**
```julia
for y in modeled_years
    # Sum annual costs for this modeled year
    annual_cost = # ... calculate ...

    # Apply costs for all years in this time step period
    for offset in 0:(time_step-1)
        actual_year = y + offset
        if actual_year <= Y_end
            discount_factor = (1 + discount_rate)^(actual_year - y_init)
            total_cost += annual_cost / discount_factor
        end
    end
end
```

This approach applies discounting separately for each actual year in the period.

---

### Step 5: Update Result Saving

**File:** `src/support_functions.jl`
**Function:** `save_results()`
**Current location:** Line ~1458+

#### Current Pattern
```julia
for y ∈ y_init:Y_end, r ∈ odpairs, tv ∈ techvehicles, g ∈ g_init:y
    val = value(model[:h][y, r.id, tv.id, g])
    # Save result
end
```

#### New Pattern
```julia
modeled_years = data_structures["modeled_years"]
modeled_generations = data_structures["modeled_generations"]

for y ∈ modeled_years, r ∈ odpairs, tv ∈ techvehicles, g ∈ modeled_generations
    if g <= y  # Only access valid combinations
        val = value(model[:h][y, r.id, tv.id, g])
        # Save result
    end
end
```

**Locations to update (estimated):**
- Line ~1484: `for y ∈ y_init:Y_end` → `for y ∈ modeled_years`
- Line ~1497: `for y ∈ y_init:Y_end, ..., gen ∈ g_init:y` → `for y ∈ modeled_years, ..., gen ∈ modeled_generations`
- Line ~1516: Vehicle stock (h)
- Line ~1527: Existing stock (h_exist)
- Line ~1538: New stock (h_plus)
- Line ~1549: Retired stock (h_minus)
- Line ~1566, 1578, 1589: Infrastructure variables
- Line ~1604: Mode infrastructure
- All other result saving loops

**Estimated:** ~20-30 loop headers to update

---

### Step 6: Update Validation Functions

**File:** `src/checks.jl`
**Functions:** Various validation functions

#### Update Needed

**Function:** `check_correct_format_InitialVehicleStock()`
**Location:** Line ~526

**Current logic:**
```julia
if ivs["year_of_purchase"] >= y_init
    error("The year of purchase must not be later than the year of the first considered year of the optimization horizon. Error at $(ivs["id"]).")
end
```

**New logic (add validation for time_step alignment):**
```julia
# Existing check
if ivs["year_of_purchase"] >= y_init
    error("The year of purchase must not be later than the year of the first considered year of the optimization horizon. Error at $(ivs["id"]).")
end

# NEW: Check if year aligns with time_step
time_step = data_structures["time_step"]
modeled_generations = data_structures["modeled_generations"]

if !(ivs["year_of_purchase"] in modeled_generations)
    error("Initial vehicle stock year $(ivs["year_of_purchase"]) does not align with time_step=$(time_step). Valid years: $(modeled_generations). Error at $(ivs["id"]).")
end
```

**Purpose:** Ensures initial vehicle stock years match the modeled generations set.

---

## Example: Complete Function Update

### Before: constraint_vehicle_stock_balance() (hypothetical)

```julia
function constraint_vehicle_stock_balance(model, data_structures)
    y_init = data_structures["y_init"]
    Y_end = data_structures["Y_end"]
    g_init = data_structures["g_init"]
    odpairs = data_structures["odpair_list"]
    techvehicles = data_structures["techvehicle_list"]

    for y in y_init:Y_end
        for r in odpairs
            for tv in techvehicles
                # Balance constraint: h[y] = h_exist[y] + h_plus[y] - h_minus[y]
                @constraint(model,
                    sum(model[:h][y, r.id, tv.id, g] for g in g_init:y) ==
                    sum(model[:h_exist][y, r.id, tv.id, g] for g in g_init:y) +
                    sum(model[:h_plus][y, r.id, tv.id, g] for g in g_init:y) -
                    sum(model[:h_minus][y, r.id, tv.id, g] for g in g_init:y)
                )
            end
        end
    end
end
```

### After: constraint_vehicle_stock_balance() (updated)

```julia
function constraint_vehicle_stock_balance(model, data_structures)
    modeled_years = data_structures["modeled_years"]
    modeled_generations = data_structures["modeled_generations"]
    odpairs = data_structures["odpair_list"]
    techvehicles = data_structures["techvehicle_list"]

    for y in modeled_years
        for r in odpairs
            for tv in techvehicles
                # Filter valid generations (only g <= y)
                valid_gens = [g for g in modeled_generations if g <= y]

                # Balance constraint: h[y] = h_exist[y] + h_plus[y] - h_minus[y]
                @constraint(model,
                    sum(model[:h][y, r.id, tv.id, g] for g in valid_gens) ==
                    sum(model[:h_exist][y, r.id, tv.id, g] for g in valid_gens) +
                    sum(model[:h_plus][y, r.id, tv.id, g] for g in valid_gens) -
                    sum(model[:h_minus][y, r.id, tv.id, g] for g in valid_gens)
                )
            end
        end
    end
end
```

**Changes:**
1. ✅ Replaced `y_init:Y_end` with `modeled_years`
2. ✅ Replaced `g_init` with `modeled_generations`
3. ✅ Added filtering for `g <= y` condition
4. ✅ No changes to constraint logic itself

---

## Testing Strategy

### Test 1: Baseline (time_step=1)
**Configuration:**
```yaml
Model:
  Y: 41
  y_init: 2020
  pre_y: 10
  time_step: 1
```

**Expected:**
- `modeled_years = [2020, 2021, ..., 2060]` (41 years)
- `modeled_generations = [2010, 2011, ..., 2060]` (51 years)
- Results identical to original implementation
- All variables have same dimensionality as before

**Validation:**
```julia
@assert length(data_structures["modeled_years"]) == 41
@assert length(data_structures["modeled_generations"]) == 51
# Run model and compare objective value to baseline run
```

---

### Test 2: Biennial (time_step=2)
**Configuration:**
```yaml
Model:
  Y: 41
  y_init: 2020
  pre_y: 10
  time_step: 2
```

**Expected:**
- `modeled_years = [2020, 2022, 2024, ..., 2060]` (21 years)
- `modeled_generations = [2010, 2012, 2014, ..., 2060]` (26 years)
- Approximately 50% fewer decision variables
- Faster solve time
- Results should be reasonable approximation of annual model

**Validation:**
```julia
@assert length(data_structures["modeled_years"]) == 21
@assert length(data_structures["modeled_generations"]) == 26
@assert data_structures["modeled_years"][1] == 2020
@assert data_structures["modeled_years"][end] == 2060
# Check that all variables are defined correctly (no errors)
# Solve model successfully
```

---

### Test 3: Quinquennial (time_step=5)
**Configuration:**
```yaml
Model:
  Y: 40  # Changed to make it divisible by 5
  y_init: 2020
  pre_y: 10
  time_step: 5
```

**Expected:**
- `modeled_years = [2020, 2025, 2030, ..., 2055]` (8 years)
- `modeled_generations = [2010, 2015, 2020, ..., 2055]` (10 years)
- Approximately 80% fewer decision variables
- Much faster solve time
- Coarser approximation suitable for exploratory analysis

**Validation:**
```julia
@assert length(data_structures["modeled_years"]) == 8
@assert data_structures["modeled_years"] == [2020, 2025, 2030, 2035, 2040, 2045, 2050, 2055]
```

---

## Edge Cases and Error Handling

### Edge Case 1: Empty Investment Years
**Scenario:** `investment_period=10`, `time_step=7`, `Y=20`
- Modeled years: [2020, 2027, 2034, 2041]
- Investment years (should be every 10): [2020, 2030, 2040]
- But 2030 and 2040 not in modeled years!

**Solution:**
```julia
# Find investment years that are in modeled years
investment_years = [y for y in modeled_years if (y - y_init) % investment_period == 0]

# Fallback: if empty, use first modeled year
if isempty(investment_years)
    @warn "No investment years align with modeled years. Using first modeled year only."
    investment_years = [modeled_years[1]]
end

data_structures["investment_years"] = investment_years
```

### Edge Case 2: Single Modeled Year
**Scenario:** `time_step=50`, `Y=41`
- Only one modeled year: [2020]

**Solution:** Valid configuration, but warn user:
```julia
if length(modeled_years) == 1
    @warn "Only 1 modeled year ($(modeled_years[1])) due to large time_step. Model will be trivial."
end
```

### Edge Case 3: Generation Constraints with Large time_step
**Scenario:** `time_step=10`, vehicle lifetime=15 years

Vehicles purchased in 2010 should be available in 2020, 2030, but the constraint `g <= y` may exclude valid combinations.

**Solution:** Already handled by filtering `g <= y` in constraints. This is correct behavior - we only model snapshots at specific years.

---

## Performance Expectations

### Variable Count Reduction

**Formula:**
```
Reduction factor ≈ 1 / time_step
```

For a model with V variables indexed by year:
- `time_step=1`: V variables
- `time_step=2`: V/2 variables (~50% reduction)
- `time_step=5`: V/5 variables (~80% reduction)

**Example:** SM model with ~1 million variables
- Annual: 1,000,000 variables
- Biennial: ~500,000 variables
- Quinquennial: ~200,000 variables

### Solve Time Expectations

MIP solve time scales approximately O(n²) to O(n³) with variable count, so:
- `time_step=2`: 50-75% reduction in solve time
- `time_step=5`: 75-95% reduction in solve time

**Use cases:**
- Exploratory analysis: Use time_step=5 for quick insights
- Final analysis: Use time_step=1 or 2 for accuracy

---

## Implementation Checklist

### Phase 1: Core Infrastructure
- [ ] Update `parse_data()` in `support_functions.jl` to create modeled year sets
- [ ] Add validation for `time_step` parameter in `checks.jl`
- [ ] Test: Load YAML with time_step=1, verify sets are created correctly

### Phase 2: Variable Definitions
- [ ] Update all `@variable` declarations in `base_define_variables()`
- [ ] Extract `modeled_years` and `modeled_generations` at function start
- [ ] Add `g <= y` conditions where needed
- [ ] Test: Model instantiation with time_step=1 (should work identically)
- [ ] Test: Model instantiation with time_step=2 (should create ~50% fewer variables)

### Phase 3: Constraints
- [ ] Update all `constraint_*()` functions year loops
- [ ] Replace `y_init:Y_end` → `modeled_years`
- [ ] Replace `g_init:Y_end` → `modeled_generations`
- [ ] Add `g <= y` filtering where needed
- [ ] Test: Model with time_step=1 solves successfully
- [ ] Test: Model with time_step=2 solves successfully

### Phase 4: Objective Function
- [ ] Update year loops in `objective()`
- [ ] Add time_step scaling for costs (critical!)
- [ ] Test: Verify objective value makes sense with different time_steps

### Phase 5: Result Saving
- [ ] Update all loops in `save_results()`
- [ ] Ensure only valid (y, g) combinations are accessed
- [ ] Test: Results save without errors for time_step=1 and time_step=2

### Phase 6: Integration Testing
- [ ] Run full SM example with time_step=1 (baseline)
- [ ] Run full SM example with time_step=2 (biennial)
- [ ] Compare results for reasonableness
- [ ] Document any unexpected behaviors

---

## Summary

### Files to Modify
1. `src/support_functions.jl` - Add modeled year/generation sets (~10 lines)
2. `src/model_functions.jl` - Update ~150+ locations with year loops
3. `src/checks.jl` - Add validation for initial stock alignment (~5 lines)

### Key Changes
1. Create `modeled_years` and `modeled_generations` sets
2. Replace all `y in y_init:Y_end` with `y in modeled_years`
3. Replace all `g in g_init:Y_end` with `g in modeled_generations`
4. Add `g <= y` filtering in constraints
5. Scale objective function costs by `time_step`
6. Update result saving loops

### Backward Compatibility
- `time_step=1` (default) → Identical behavior to current implementation
- All existing YAML files without `time_step` will default to annual resolution

### Expected Benefits
- **Computational efficiency:** 50-95% reduction in solve time
- **Flexibility:** Quick exploratory runs with coarse resolution
- **Scalability:** Larger geographic scope becomes feasible
