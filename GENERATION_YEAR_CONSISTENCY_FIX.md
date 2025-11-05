# Generation-Year Consistency Fix: `g < y` → `g <= y`

**Date**: 2025-10-30
**Severity**: CRITICAL
**Status**: ✓ COMPLETED

---

## Summary

Fixed critical inconsistency in constraint conditions where some constraints used `g < y` (generation strictly less than year) while variable definitions and most constraints used `g <= y` (generation less than or equal to year).

**Design Intent**: Vehicles purchased in generation-year g **can operate in year g** (not delayed to g+1).

---

## The Inconsistency

### Variable Definitions (Correct)
All variables use `g <= y`:
```julia
@variable(model, f[y in modeled_years, ..., g in modeled_generations; g <= y] >= 0)
@variable(model, soc[y in modeled_years, ..., g in modeled_generations; g <= y] >= 0)
@variable(model, travel_time[y in modeled_years, ..., g in modeled_generations; g <= y] >= 0)
```

### Constraints (Were Inconsistent)

**Before Fix:**
- SOC constraints used `g < y` ❌
- Travel time constraints used `g < y` ❌
- All other constraints used `g <= y` ✓

**After Fix:**
- All constraints now use `g <= y` ✓ ✓ ✓

---

## Changes Made

### File: `src/model_functions.jl`

#### 1. Line 3399 - `constraint_soc_max`
```julia
# BEFORE
@constraint(model, [y in modeled_years, prkg in p_r_k_g_pairs, tv in techvehicle_list; g < y],
    model[:soc][y, prkg, tv.id, g] <= ...
)

# AFTER
@constraint(model, [y in modeled_years, prkg in p_r_k_g_pairs, tv in techvehicle_list; g <= y],  # FIXED
    model[:soc][y, prkg, tv.id, g] <= ...
)
```

#### 2. Line 3438 - `constraint_soc_track` (origin)
```julia
# BEFORE
if g < y  # g < y (vehicles operate year after purchase)

# AFTER
if g <= y  # FIXED: Should be g <= y (vehicles purchased in year y can operate in year y)
```

#### 3. Line 3478 - `constraint_soc_track` (tracking)
```julia
# BEFORE
if g < y  # g < y (vehicles operate year after purchase)

# AFTER
if g <= y  # FIXED: Should be g <= y (vehicles purchased in year y can operate in year y)
```

#### 4. Line 3541 - `constraint_travel_time_track` (origin)
```julia
# BEFORE
if g < y  # g < y

# AFTER
if g <= y  # FIXED: Should be <= to include g==y case
```

#### 5. Line 3575 - `constraint_travel_time_track` (tracking)
```julia
# BEFORE
if g < y  # g < y

# AFTER
if g <= y  # FIXED: Should be <= to include g==y case
```

---

## Impact

### Before Fix (Incorrect)

**For flows with generation==year (e.g., year=2020, gen=2020):**
- ❌ Flow variable exists: `f[2020, ..., 2020]` can be non-zero
- ❌ SOC constraint **NOT APPLIED** (vehicles could have impossible battery states)
- ❌ Travel time constraint **NOT APPLIED** (vehicles could teleport)
- ❌ Model accepted **physically impossible** solutions
- ✓ Model appeared "feasible" but was **silently broken**

**Example violation found:**
- Path: 841.33 km
- Expected driving time: 275.94 hours
- Actual travel_time: 255.83 hours
- **Violation: -20.11 hours** (impossible!)

### After Fix (Correct)

**For flows with generation==year:**
- ✓ Flow variable exists: `f[2020, ..., 2020]` can be non-zero
- ✓ SOC constraint **IS APPLIED** (battery physics enforced)
- ✓ Travel time constraint **IS APPLIED** (speed limits enforced)
- ✓ Model correctly identifies **infeasible** solutions
- ⚠️ Model may now be infeasible (reveals real problems that were hidden)

---

## Why Model Became Infeasible

The fix **revealed** underlying issues that were previously hidden:

1. **Mandatory break requirements** may be too strict for some routes
2. **Vehicle range/charging** may be insufficient for long routes
3. **Infrastructure capacity** may be inadequate
4. **Route parameters** (distance, speed) may have issues

**The fix is correct** - infeasibility means the model setup has conflicting requirements that need to be resolved.

---

## Design Clarification

### When Do Vehicles Start Operating?

**Confirmed interpretation**: Vehicles purchased in year g **begin operating in year g**, not year g+1.

**Evidence**:
1. Variable definitions allow `g <= y`
2. Flow variable can have non-zero values for `g == y`
3. User confirmed: "vehicles are purchased at the beginning of the year y"

**Old comments were wrong**:
```julia
if g < y  # g < y (vehicles operate year after purchase)  # ← INCORRECT COMMENT
```

Should be:
```julia
if g <= y  # Vehicles purchased in year y can operate in year y  # ← CORRECT
```

---

## Verification Checklist

✓ All variable definitions use `g <= y`
✓ All SOC constraints now use `g <= y`
✓ All travel time constraints now use `g <= y`
✓ Mandatory breaks constraint already used `g <= y`
✓ Infrastructure constraints already use `g <= y`
✓ Fuel demand constraints already use `g <= y`
✓ Budget constraints already use `g <= y`
✓ Objective function already uses `g <= y`

**Result**: Model is now **fully consistent** across all components.

---

## What This Means for Results

### Previous Results (Before Fix)
- **Invalid**: Ignored constraints for generation==year vehicles
- **Optimistic**: Allowed impossible vehicle behavior
- **Unreliable**: Cannot be trusted for decision-making

### New Results (After Fix)
- **Valid**: All constraints properly enforced
- **Realistic**: Only physically possible solutions accepted
- **Trustworthy**: Can be used for decision-making

---

## Resolving Infeasibility

If the model becomes infeasible after this fix, investigate:

### 1. Check Mandatory Breaks
```julia
# Temporarily comment out to test
# constraint_mandatory_breaks(model, data_structures)
```

### 2. Relax Constraints
- Increase vehicle range
- Add more charging infrastructure
- Adjust break requirements for short routes
- Review route distance data

### 3. Debug with Gurobi IIS
```julia
# Add before optimize!()
set_optimizer_attribute(model, "ResultFile", "model_infeas.ilp")
```

This creates a file showing which constraints conflict.

---

## Consistency Check Results

Searched all constraint functions for `g < y` vs `g <= y`:

| Component | Before | After | Status |
|-----------|--------|-------|--------|
| Variable definitions | `g <= y` | `g <= y` | ✓ Consistent |
| Flow variable `f` | `g <= y` | `g <= y` | ✓ Consistent |
| SOC max | `g < y` | `g <= y` | ✓ **Fixed** |
| SOC track (origin) | `g < y` | `g <= y` | ✓ **Fixed** |
| SOC track (tracking) | `g < y` | `g <= y` | ✓ **Fixed** |
| Travel time (origin) | `g < y` | `g <= y` | ✓ **Fixed** |
| Travel time (tracking) | `g < y` | `g <= y` | ✓ **Fixed** |
| Mandatory breaks | `g <= y` | `g <= y` | ✓ Consistent |
| Infrastructure | `g <= y` | `g <= y` | ✓ Consistent |
| Fuel demand | `g <= y` | `g <= y` | ✓ Consistent |
| Vehicle stock | `g <= y` | `g <= y` | ✓ Consistent |
| Budget | `g <= y` | `g <= y` | ✓ Consistent |
| Objective | `g <= y` | `g <= y` | ✓ Consistent |

**Result**: ✓ **All 5 inconsistencies fixed** - model is now fully consistent.

---

## Commit Message

```
Fix critical inconsistency: Change g < y to g <= y in SOC and travel time constraints

Changed 5 constraint conditions from `g < y` to `g <= y` to match variable definitions
and design intent that vehicles purchased in year y can operate in year y.

Affected constraints:
- constraint_soc_max (line 3399)
- constraint_soc_track origin (line 3438)
- constraint_soc_track tracking (line 3478)
- constraint_travel_time_track origin (line 3541)
- constraint_travel_time_track tracking (line 3575)

Impact: Previously, constraints were not applied for generation==year vehicles,
allowing physically impossible solutions. Model may now be infeasible but this
reveals real problems that need to be addressed.

Files: src/model_functions.jl
```

---

## Related Issues

- See `TRAVEL_TIME_CONSTRAINT_BUG_FIX.md` for initial discovery of travel time issue
- See `INDEXING_CHANGES_COMPLETED.md` for removal of f_l dimension from soc/travel_time

---

**Status**: ✓ All fixes completed and documented
**Next Step**: Investigate and resolve model infeasibility
