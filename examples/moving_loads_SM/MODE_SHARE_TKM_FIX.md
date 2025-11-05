# Mode Share Constraint - Fixed to Use Tonne-Kilometers (tkm)

## Problem

The `constraint_max_mode_share` and `constraint_min_mode_share` functions were constraining the **flow variable `f`** directly, rather than the actual **tonne-kilometers (tkm)**.

This meant:
- A 30% share constraint would limit the number of OD pairs or flow volume
- But **NOT** the actual transport work performed (tkm = tonnes × distance)
- Short-distance flows and long-distance flows were weighted equally

## Solution

Modified both functions to multiply flow by path length:

### Before (Incorrect)
```julia
mode_flow = sum(
    model[:f][year, (r.product.id, r.id, k.id), mv, g]
    ...
)
```

### After (Correct)
```julia
mode_tkm = sum(
    model[:f][year, (r.product.id, r.id), k.id), mv, g] * k.length  # <-- multiply by path length
    ...
)
```

## Changes Made

### 1. `constraint_max_mode_share` (Lines 1853-1884)
- **Before**: `mode_flow <= share * total_flow`
- **After**: `mode_tkm <= share * total_tkm`
- Now properly constraints rail to 30% of total tonne-kilometers

### 2. `constraint_min_mode_share` (Lines 1895-1933)
- **Before**: `mode_flow >= share * total_flow` (also had region filtering)
- **After**: `mode_tkm >= share * total_tkm`
- Restructured from `@constraint` macro to explicit loop for clarity
- Added `timestep` parameter that was missing

## Impact

The tkm-based constraint is more meaningful because:

1. **Distance matters**: A 1000 km rail flow counts more than a 100 km rail flow
2. **Aligns with objective**: The objective uses `cost_per_ukm * length * flow`
3. **Industry standard**: Modal share statistics are typically reported in tkm, not just tonnes
4. **Better policy modeling**: Infrastructure capacity is better measured in tkm

### Example

Suppose we have:
- OD pair A→B: 100 km, 100 tonnes → 10,000 tkm
- OD pair C→D: 1000 km, 100 tonnes → 100,000 tkm

**Flow-based** (old):
- Rail carries 1 out of 2 OD pairs = **50% "share"**
- But if rail carries C→D, it's doing **100,000 / 110,000 = 91% of the work**

**Tkm-based** (new):
- Rail carrying C→D = 100,000 tkm / 110,000 total tkm = **91% share** ✅
- Correctly reflects the transport work performed

## Testing

Running model with:
- Rail at €0.05/tkm (cheaper than road)
- 30% rail cap (tkm-based)

Expected result:
- Rail will carry ~30% of **tonne-kilometers**, not just 30% of flow volume
- Modal split may differ from previous run due to distance weighting

## Files Modified

**`src/model_functions.jl`**:
- Lines 1853-1884: `constraint_max_mode_share` - changed to tkm-based
- Lines 1895-1933: `constraint_min_mode_share` - changed to tkm-based

## Status

✅ **Mode share constraints now use tonne-kilometers (tkm)**
✅ **More accurate representation of transport work**
🔄 **Testing with current scenario**
