# MANDATORY BREAKS - CRITICAL BUG REPORT

## Summary

**All mandatory breaks are being placed at the route origin (node_idx=0) with cumulative_driving_time=0**, regardless of break_number. This is a critical bug in the preprocessing code.

## Data Evidence

### Actual Data from `MandatoryBreaks.yaml`:

**Path 0 (562.7 km, 7.0h total driving time):**
```yaml
- path_id: 0
  break_number: 1
  latest_node_idx: 0      # ← Should be at origin
  cumulative_distance: 0.0  # ← Correct for first break
  cumulative_driving_time: 0.0  # ← Correct for first break
```

**Path 10 (838.6 km, 10.5h total driving time):**
```yaml
- path_id: 10
  break_number: 1
  latest_node_idx: 0
  cumulative_distance: 0.0
  cumulative_driving_time: 0.0  # Correct

- path_id: 10
  break_number: 2  # SECOND break
  latest_node_idx: 0      # ❌ WRONG! Should be ~360-720 km into route
  cumulative_distance: 0.0  # ❌ WRONG! Should be ~360-720 km
  cumulative_driving_time: 0.0  # ❌ WRONG! Should be ~4.5-9.0 hours
```

## Histogram Evidence

From our histogram analysis of break_number=1:
- **2,773 routes (94.7%)**: cumulative_driving_time = 0.0
- **155 routes (5.3%)**: cumulative_driving_time > 0 (up to 4.48h)

This confirms that:
1. Most break_number=1 entries are at route origin (correct)
2. But some have driving time >0 (should be investigated)

From break_number=2 analysis:
- **Average driving time**: 0.07h (WAY too low!)
- **Max driving time**: 8.95h (exceeds 4.5h limit, but most are near 0)

## Code Analysis

### File: `SM_preprocessing_nuts2_complete.py` (lines 800-849)

**Current Implementation:**
```python
def create_mandatory_breaks(self, driver_limit_hours=4.5, avg_speed_kmh=80.0):
    max_distance = driver_limit_hours * avg_speed_kmh  # 360 km

    for path in self.path_list:
        distance_since_break = 0
        break_number = 0

        for i in range(1, len(sequence)):  # Starts at node 1
            distance_since_break += distances[i]

            if distance_since_break >= max_distance:
                break_number += 1
                total_driving_time = cumulative[i] / avg_speed_kmh

                self.mandatory_breaks.append({
                    'break_number': break_number,
                    'latest_node_idx': i,  # ← Should be the CURRENT node
                    'cumulative_distance': cumulative[i],
                    'cumulative_driving_time': total_driving_time,
                    ...
                })
                distance_since_break = 0
```

**Issues:**
1. ✅ **Loop logic looks correct**: Iterates through nodes, accumulates distance
2. ✅ **Break placement logic looks correct**: Places break when distance >= 360 km
3. ✅ **Uses correct cumulative values**: `cumulative[i]` and `cumulative[i] / avg_speed_kmh`
4. ❌ **BUT: Data shows all breaks at node_idx=0!**

**Hypothesis:** The code looks correct, but something happens AFTER this function that overwrites the data or there's a different version being used.

### File: `mandatory_breaks_calculation.py`

This is a **reference implementation** showing the CORRECT logic:

```python
def calculate_mandatory_breaks(path, speed=80):
    total_driving_time = total_length / speed
    num_breaks_required = int(np.floor(total_driving_time / MAX_DRIVING_TIME))

    for break_num in range(1, num_breaks_required + 1):
        max_time_before_break = break_num * MAX_DRIVING_TIME  # 4.5h, 9.0h, 13.5h, ...
        max_distance_before_break = max_time_before_break * speed  # 360km, 720km, 1080km, ...

        # Find the latest node where cumulative_distance <= max_distance
        for i, cum_dist in enumerate(cumulative_distance):
            if cum_dist <= max_distance_before_break:
                latest_node_idx = i
                actual_cum_distance = cum_dist
            else:
                break

        cumulative_driving_time = actual_cum_distance / speed

        break_list.append({
            'break_number': break_num,
            'latest_node_idx': latest_node_idx,  # ← Varies by break
            'cumulative_distance': actual_cum_distance,  # ← Varies by break
            'cumulative_driving_time': cumulative_driving_time,  # ← Varies by break
            ...
        })
```

## Expected Behavior

For a route of 800 km at 80 km/h (10 hours driving):

| Break # | Should occur by | Expected node_idx | Expected cumulative_distance | Expected cumulative_driving_time |
|---------|----------------|-------------------|------------------------------|----------------------------------|
| 1       | 360 km (4.5h)  | Node near 360 km  | ~360 km                      | ~4.5 h                           |
| 2       | 720 km (9.0h)  | Node near 720 km  | ~720 km                      | ~9.0 h                           |

## Actual Behavior

For the same 800 km route:

| Break # | Actual node_idx | Actual cumulative_distance | Actual cumulative_driving_time |
|---------|----------------|----------------------------|--------------------------------|
| 1       | 0              | 0.0 km                     | 0.0 h                          |
| 2       | 0              | 0.0 km                     | 0.0 h                          |

**❌ Both breaks are placed at the origin with zero driving time!**

## Impact on Model

This bug means:
1. **The optimization model receives INCORRECT break constraints**
2. **Routes are not properly constrained by the 4.5h driving limit**
3. **Break timing in the solution cannot be trusted**
4. **Analysis of break patterns is meaningless with this buggy data**

## Root Cause Investigation

### Hypothesis 1: Wrong preprocessing file is being used
- The code in `SM_preprocessing_nuts2_complete.py` looks correct
- Maybe an older/different version generated the actual input data?
- **Action**: Check which preprocessing script was actually run

### Hypothesis 2: Data corruption after generation
- The preprocessing generates correct data
- Something else overwrites or corrupts it before saving
- **Action**: Add debug prints to verify data before/after saving

### Hypothesis 3: Missing initialization code
- Break_number=1 entries at origin might be added intentionally
- But break_number=2+ should NOT be at origin
- **Action**: Search for code that explicitly adds origin breaks

## Recommended Fix

### Option 1: Use the `mandatory_breaks_calculation.py` module

Replace the broken `create_mandatory_breaks()` in `SM_preprocessing_nuts2_complete.py` with:

```python
from mandatory_breaks_calculation import create_mandatory_breaks_list

def create_mandatory_breaks(self, avg_speed_kmh=80.0):
    """Create mandatory break constraints using the validated calculation module."""
    print("\n" + "="*80)
    print("STEP 4: CREATING MANDATORY BREAKS")
    print("="*80)

    # Use the validated calculation
    self.mandatory_breaks = create_mandatory_breaks_list(self.path_list, speed=avg_speed_kmh)

    # Add additional fields if needed (event_type, charging_type, etc.)
    break_id = 0
    for break_entry in self.mandatory_breaks:
        break_entry['id'] = break_id
        break_entry['event_type'] = 'B'  # Break
        break_entry['event_name'] = 'break'
        break_entry['charging_type'] = 'fast'  # or determine based on logic
        break_entry['num_drivers'] = 1  # or get from route data
        break_id += 1

    print(f"[OK] Created {len(self.mandatory_breaks)} mandatory break points")
    if self.mandatory_breaks:
        avg_breaks = len(self.mandatory_breaks) / len(self.path_list)
        print(f"     Average breaks per path: {avg_breaks:.2f}")
```

### Option 2: Debug the existing code

Add debug output to see what's happening:

```python
if distance_since_break >= max_distance:
    break_number += 1
    total_driving_time = cumulative[i] / avg_speed_kmh

    print(f"  Path {path_id}, Break {break_number}: node_idx={i}, "
          f"cumulative_distance={cumulative[i]:.1f}, "
          f"driving_time={total_driving_time:.2f}h")

    self.mandatory_breaks.append({...})
```

Run the preprocessing and check if the debug output shows correct values.

## Next Steps

1. **Identify which preprocessing script generated the current input data**
2. **Add debug output to verify break placement logic**
3. **Re-run preprocessing with the corrected code**
4. **Validate new MandatoryBreaks data**:
   - Check that break_number=2+ have cumulative_driving_time > 0
   - Check that breaks respect 4.5h intervals
   - Check that latest_node_idx increases with break_number
5. **Re-run the optimization model with corrected input data**
6. **Re-analyze results to get meaningful break patterns**

## Validation Criteria

Correct MandatoryBreaks data should satisfy:

✅ For break_number=1:
- Can be at origin (cumulative_driving_time=0) for initial charging
- Can also be at ~4.5h mark for first mandatory driving break

✅ For break_number=2:
- Must be at cumulative_driving_time ≈ 4.5h or 9.0h (depending on interpretation)
- Must have latest_node_idx > 0
- Must have cumulative_distance > 0

✅ For break_number=n:
- cumulative_driving_time ≈ n * 4.5h (or adjusted for break interpretation)
- latest_node_idx should increase monotonically with break_number for each path
- cumulative_distance should increase monotonically

✅ General:
- Max cumulative_driving_time for any break should not exceed total_driving_time
- Number of breaks should match `floor(total_driving_time / 4.5)`

---

**URGENT**: This bug must be fixed before the results can be trusted for the paper!
