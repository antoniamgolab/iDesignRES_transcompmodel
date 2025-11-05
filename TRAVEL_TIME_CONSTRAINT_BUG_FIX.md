# CRITICAL BUG FIX: Travel Time Constraint Not Applied When g == y

**Date**: 2025-10-30
**Severity**: CRITICAL
**Status**: ✓ FIXED

---

## Summary

The travel time tracking constraints were not being applied when generation equals year (g == y), causing the model to produce invalid solutions where travel time was less than the minimum driving time.

---

## The Bug

**Location**: `src/model_functions.jl`, function `constraint_travel_time_track()`

**Lines affected**:
- Line 3541 (origin constraint)
- Line 3575 (tracking constraint)

**Original code:**
```julia
if g < y  # g < y
    # Add travel time constraints...
end
```

**Problem**: When `generation == year` (e.g., both are 2020), the condition `g < y` evaluates to **FALSE**, so **no constraint is added**!

---

## Impact

### Before Fix

**Example violation found:**
- Path: 841.33 km
- Flow: 43.50 (1000 tkm)
- Expected minimum driving time: **275.94 hours**
- Actual travel_time value: **255.83 hours**
- **Shortfall: 20.11 hours** ❌

The model allowed travel_time to be LESS than the minimum driving time, violating physical constraints.

### Affected Flows

All flows where `generation == year`:
- Year 2020, Generation 2020
- Year 2025, Generation 2025
- Year 2030, Generation 2030
- etc.

This is a **common case** since vehicles typically start operating in their generation year.

---

## The Fix

**Changed condition from `g < y` to `g <= y`:**

### Location 1: Origin constraint (line 3541)
```julia
# BEFORE
if g < y  # g < y

# AFTER
if g <= y  # FIXED: Should be <= to include g==y case
```

### Location 2: Tracking constraint (line 3575)
```julia
# BEFORE
if g < y  # g < y

# AFTER
if g <= y  # FIXED: Should be <= to include g==y case
```

---

## Why This Matters

### Physical Meaning

The travel time constraint ensures:
```
travel_time[destination] >= driving_time + charging_time + break_time
```

Without this constraint:
- Vehicles can "teleport" with zero travel time
- Flow patterns don't respect speed limits
- Charging and break requirements are ignored
- Results are physically invalid

### Model Integrity

This bug affected:
1. **Travel time calculations** - Invalid travel times
2. **Mandatory breaks** - Breaks may not be enforced if travel time is wrong
3. **Charging patterns** - BEV routing may be incorrect
4. **Value of Time (VoT)** - Cost calculations based on travel time are wrong
5. **Infrastructure planning** - Wrong estimates of required capacity

---

## How the Bug Was Found

### Diagnostic Process

1. **Symptom**: Travel time validation check reported:
   ```
   Destination travel time (255.83) < expected (275.94)
   ```

2. **Investigation**: Created detailed debug script (`check_travel_time_detailed_debug.jl`) showing:
   - Path structure correct ✓
   - Distance calculations correct ✓
   - Flow values correct ✓
   - But actual travel_time LESS than expected ❌

3. **Root cause identified**: Checked constraint code and found:
   ```julia
   Year: 2020
   Generation: 2020
   Condition: if g < y  → 2020 < 2020 → FALSE
   Result: NO CONSTRAINT ADDED!
   ```

---

## Verification

### Before Fix
```
Year: 2020, Generation: 2020
Expected driving time: 275.9442 hours
Actual travel_time: 255.8298 hours
✗ VIOLATION: -20.11 hours
```

### After Fix
Run the model with the fixed constraints. The validation should show:
```
✓ PASS: travel_time >= expected driving time
```

---

## Related Constraints

### Also Check These Functions

The same `g < y` vs `g <= y` issue may exist in other constraint functions. Search for similar patterns in:

- `constraint_soc_track()` - Already uses `g <= y` ✓
- `constraint_soc_max()` - Already uses `g <= y` ✓
- `constraint_mandatory_breaks()` - Check if similar issue exists
- All other constraint functions with generation loops

### Pattern to Look For

```julia
for g in modeled_generations
    if g < y  # ← POTENTIAL BUG
        # Add constraints...
    end
end
```

Should typically be:
```julia
for g in modeled_generations
    if g <= y  # ← CORRECT
        # Add constraints...
    end
end
```

**Rationale**: A generation can operate in its own year (e.g., 2020 generation vehicles can operate in 2020).

---

## Testing

### Quick Test

Run SM.jl with the fixed code and check the diagnostic output:

```bash
cd examples/moving_loads_SM
julia SM.jl
```

Look for the travel time validation:
```
✓ PASS: Travel time >= minimum driving time
```

### Comprehensive Test

1. Compare results before/after fix
2. Check that all travel times are now >= driving times
3. Verify constraint counts increased (more constraints added for g==y cases)
4. Ensure model still solves optimally

---

## Files Modified

1. `src/model_functions.jl`
   - Line 3541: Origin constraint condition
   - Line 3575: Tracking constraint condition

2. `examples/moving_loads_SM/check_travel_time_detailed_debug.jl` (diagnostic tool)
   - Created to identify the bug
   - Can be used for ongoing validation

---

## Commit Message

```
Fix critical bug: Travel time constraints not applied when g==y

Changed condition from `g < y` to `g <= y` in constraint_travel_time_track()
to include the case where generation equals year.

Previously, vehicles of generation G operating in year G had no travel time
constraints, allowing physically impossible travel times less than the
minimum driving time.

Impact: Affects all flows where generation == year (common case).
Files: src/model_functions.jl (lines 3541, 3575)
```

---

## Lessons Learned

1. **Off-by-one errors** with `<` vs `<=` can have major impacts
2. **Domain-specific validation** is critical (travel time >= driving time)
3. **Edge cases matter** (g==y is common, not rare!)
4. **Diagnostic tools** are essential for finding constraint bugs

---

**Status**: ✓ Bug fixed, ready for testing
