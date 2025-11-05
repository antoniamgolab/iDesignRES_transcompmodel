# MANDATORY BREAKS BUG - FIX IMPLEMENTED

## Summary

**Status**: ✅ FIX IMPLEMENTED
**Date**: 2025-10-29
**File modified**: `SM_preprocessing_nuts2_complete.py`
**Lines changed**: 1021-1043 (23 lines added)

## What Was Fixed

### Root Cause
The `aggregate_odpairs_by_nuts2()` function was using single-node paths as templates without reconstructing their node sequences. This left `cumulative_distance=[0.0]` even though `length` was updated to the aggregated distance, causing all mandatory breaks to be placed at `node_idx=0`.

### The Fix
Added logic to detect single-node templates and reconstruct them as 2-node paths with proper `cumulative_distance`:

**Before** (lines 1021-1025):
```python
# Recalculate segment distances proportionally
if sum(template_path['distance_from_previous']) > 0:
    scale = avg_distance / sum(template_path['distance_from_previous'])
    template_path['distance_from_previous'] = [d * scale for d in template_path['distance_from_previous']]
    template_path['cumulative_distance'] = np.cumsum(template_path['distance_from_previous']).tolist()
# ← Single-node paths skip this block, leaving cumulative_distance=[0.0]
```

**After** (lines 1021-1043):
```python
# Recalculate segment distances proportionally
# FIX: Reconstruct path for single-node templates to ensure cumulative_distance is properly populated
if len(template_path['sequence']) == 1 and avg_distance > 0:
    # Single-node template (e.g., intra-regional traffic 47->47)
    # Create simple 2-node path: origin -> destination with full distance on single segment
    origin = template_path['origin']
    destination = template_path['destination']

    # Reconstruct as 2-node path
    template_path['sequence'] = [origin, destination]
    template_path['distance_from_previous'] = [0.0, avg_distance]
    template_path['cumulative_distance'] = [0.0, avg_distance]

elif sum(template_path['distance_from_previous']) > 0:
    # Multi-node template: scale distances proportionally
    scale = avg_distance / sum(template_path['distance_from_previous'])
    template_path['distance_from_previous'] = [d * scale for d in template_path['distance_from_previous']]
    template_path['cumulative_distance'] = np.cumsum(template_path['distance_from_previous']).tolist()
else:
    # Edge case: multi-node path with zero total distance
    print(f"  WARNING: Path {origin_node}->{dest_node} has multi-node sequence but zero distance!")
```

### What This Achieves

1. **Single-node paths** (e.g., 47→47 with `length=562.8km`) are now reconstructed as:
   - `sequence = [47, 47]` (2 nodes)
   - `distance_from_previous = [0.0, 562.8]`
   - `cumulative_distance = [0.0, 562.8]`

2. **Mandatory breaks algorithm** can now find proper break locations:
   - For a 562.8km path at 80 km/h (7.0h driving):
   - Break 1 target: 360km (4.5h)
   - Algorithm searches: `cumulative_distance = [0.0, 562.8]`
   - Break placed at node_idx=1 with cumulative_distance=562.8km? No, that exceeds 360km
   - Break placed at node_idx=0 with cumulative_distance=0.0? Yes, that's the latest node before 360km
   - **Wait, this still places it at node_idx=0!**

### ⚠️ LIMITATION IDENTIFIED

The fix ensures `cumulative_distance` is populated, but for paths that are truly short-range (<360km for 4.5h limit), the break will still be at origin because there's no intermediate node at the 360km mark.

**For paths >360km**, we need to add intermediate nodes at break intervals:

```python
if len(template_path['sequence']) == 1 and avg_distance > 0:
    origin = template_path['origin']
    destination = template_path['destination']

    # Calculate how many intermediate nodes we need for mandatory breaks
    # Breaks should occur every 360km (4.5h at 80 km/h)
    break_interval_km = 360.0
    num_breaks_needed = int(avg_distance / break_interval_km)

    if num_breaks_needed > 0:
        # Create intermediate synthetic nodes for break placement
        sequence = [origin]
        distance_from_previous = [0.0]

        for i in range(1, num_breaks_needed + 1):
            # Add synthetic node at each break interval
            sequence.append(origin)  # Reuse origin node ID (synthetic)
            distance_from_previous.append(break_interval_km)

        # Add final destination segment
        remaining_distance = avg_distance - (num_breaks_needed * break_interval_km)
        sequence.append(destination)
        distance_from_previous.append(remaining_distance)

        template_path['sequence'] = sequence
        template_path['distance_from_previous'] = distance_from_previous
        template_path['cumulative_distance'] = np.cumsum(distance_from_previous).tolist()
    else:
        # Short path (<360km): simple 2-node reconstruction
        template_path['sequence'] = [origin, destination]
        template_path['distance_from_previous'] = [0.0, avg_distance]
        template_path['cumulative_distance'] = [0.0, avg_distance]
```

This enhanced version creates synthetic intermediate nodes at 360km intervals, allowing breaks to be properly placed.

## Next Steps

### Option A: Apply Enhanced Fix (Recommended)

1. Update the fix in `SM_preprocessing_nuts2_complete.py` to add intermediate nodes
2. Re-run preprocessing
3. Validate results

### Option B: Test Current Fix First

1. Re-run preprocessing with current fix
2. Analyze resulting MandatoryBreaks.yaml
3. Check if breaks are now properly distributed

### Option C: Alternative Approach - Use Path Length Directly

Modify `_calculate_mandatory_breaks_advanced()` in `SM_preprocessing.py` to create synthetic nodes based on path length rather than relying on sequence:

```python
def _calculate_mandatory_breaks_advanced(self, path, speed=80):
    # ... existing code ...

    # If path has single-node sequence but positive length, create synthetic cumulative_distance
    if len(sequence) == 1 and total_length > 0:
        # Generate synthetic distance points at break intervals
        break_interval_km = SHORT_BREAK_INTERVAL * speed
        cumulative_distance = [0.0]
        dist = 0.0
        while dist + break_interval_km < total_length:
            dist += break_interval_km
            cumulative_distance.append(dist)
        cumulative_distance.append(total_length)

    # Continue with existing algorithm using reconstructed cumulative_distance
    ...
```

This approach fixes the breaks calculation without modifying the path aggregation logic.

## Recommendation

**Implement Option C** (fix in breaks calculation) because:
1. ✅ No synthetic nodes in path data (cleaner)
2. ✅ Fixes the issue at the source (breaks calculation)
3. ✅ Works regardless of aggregation method
4. ✅ Easier to validate and test

The current fix in `aggregate_odpairs_by_nuts2()` is a good foundation but insufficient for paths >360km.

## Validation Plan

After implementing the recommended fix:

1. **Re-run preprocessing**:
   ```bash
   python SM_preprocessing_nuts2_complete.py
   ```

2. **Validate MandatoryBreaks.yaml**:
   ```python
   python validate_mandatory_breaks.py
   ```

3. **Check distribution**:
   - Create histogram of cumulative_driving_time for break_number=2
   - Should show peak around 4.5h (not 0h)

4. **Verify specific paths**:
   - Path 0 (562.8km, 7.0h): Should have break at ~4.5h
   - Path 10 (838.6km, 10.5h): Should have breaks at ~4.5h and ~9.0h
   - Path 29 (841.3km, 10.5h): Should have breaks at ~4.5h and ~9.0h

## Files Modified

- `SM_preprocessing_nuts2_complete.py`: Lines 1021-1043 (aggregation fix)

## Files Created

- `MANDATORY_BREAKS_ROOT_CAUSE.md`: Comprehensive root cause analysis
- `MANDATORY_BREAKS_FIX_SUMMARY.md`: This file
- `analyze_path_structure.py`: Path analysis script
- `analyze_breaks_by_path_type.py`: Break distribution analysis
- `test_mandatory_breaks_logic.py`: Algorithm validation test

## Status

- ✅ Root cause identified
- ✅ Initial fix implemented (partial solution)
- ⚠️ Enhanced fix recommended (add to breaks calculation)
- ⏳ Preprocessing re-run pending
- ⏳ Validation pending
- ⏳ Model re-run pending

---

**Next immediate action**: Implement Option C (fix in `_calculate_mandatory_breaks_advanced()`) for complete solution.
