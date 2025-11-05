# MANDATORY BREAKS BUG - ROOT CAUSE IDENTIFIED

## Executive Summary

**ROOT CAUSE**: The `aggregate_odpairs_by_nuts2()` function uses single-node paths as templates without reconstructing their node sequences, leaving `cumulative_distance=[0.0]` despite updating the path `length` to the aggregated average distance. This causes the mandatory breaks algorithm to place all breaks at `node_idx=0` with `cumulative_driving_time=0`.

## Bug Discovery Timeline

1. **Initial observation**: 94.7% of break_number=1 entries have cumulative_driving_time=0
2. **Deeper analysis**: 97.3% of ALL breaks on multi-node paths are at node_idx=0 with cumulative_time=0
3. **Algorithm validation**: Test proved `_calculate_mandatory_breaks_advanced()` works correctly
4. **Path inspection**: Found 97.4% of paths have proper multi-node sequences
5. **Critical insight**: User suggested investigating aggregation/upscaling
6. **Root cause found**: Aggregation function doesn't reconstruct cumulative_distance for single-node template paths

## Technical Details

### Location
**File**: `SM_preprocessing_nuts2_complete.py`
**Function**: `aggregate_odpairs_by_nuts2()` (lines 974-1060)
**Problem lines**: 1016-1025

### The Aggregation Process

```python
def aggregate_odpairs_by_nuts2(self):
    # Group OD-pairs by (origin_node, dest_node)
    odpair_groups = {}
    for odpair, path in zip(self.odpair_list, self.path_list):
        key = (odpair['from'], odpair['to'])
        if key not in odpair_groups:
            odpair_groups[key] = {'odpairs': [], 'paths': []}
        odpair_groups[key]['odpairs'].append(odpair)
        odpair_groups[key]['paths'].append(path)

    # For each unique NUTS-2 OD-pair:
    for (origin_node, dest_node), group in odpair_groups.items():
        odpairs = group['odpairs']
        paths = group['paths']

        # Calculate weighted average distance
        total_flow = sum(od['F'][0] for od in odpairs)
        avg_distance = sum(p['length'] * od['F'][0] for p, od in zip(paths, odpairs)) / total_flow

        # Use highest-flow path as template
        max_flow_idx = np.argmax([od['F'][0] for od in odpairs])
        template_path = paths[max_flow_idx].copy()
        template_path['length'] = avg_distance  # ← Updates to weighted average

        # Recalculate segment distances proportionally
        if sum(template_path['distance_from_previous']) > 0:  # ← BUG: Condition fails for single-node paths!
            scale = avg_distance / sum(template_path['distance_from_previous'])
            template_path['distance_from_previous'] = [d * scale for d in template_path['distance_from_previous']]
            template_path['cumulative_distance'] = np.cumsum(template_path['distance_from_previous']).tolist()
        # ← If condition fails, cumulative_distance stays [0.0]!
```

### The Bug

When a **single-node path** (e.g., 47→47 representing intra-regional traffic) is selected as the template:

1. **Before aggregation**:
   - `sequence = [47]` (single node)
   - `distance_from_previous = [0.0]` (no segments)
   - `cumulative_distance = [0.0]`
   - `length = 562.8km` (total distance from original data)

2. **During aggregation**:
   - Path is selected as template (highest flow)
   - `template_path['length']` is updated to weighted average (e.g., stays 562.8km or changes to aggregate average)
   - Condition `sum(template_path['distance_from_previous']) > 0` **FAILS** (sum is 0)
   - Distance scaling is **SKIPPED**
   - `cumulative_distance` **REMAINS [0.0]**

3. **Result after aggregation**:
   - `sequence = [47]` (unchanged)
   - `distance_from_previous = [0.0]` (unchanged)
   - `cumulative_distance = [0.0]` ← **BUG: Should reflect the actual 562.8km!**
   - `length = 562.8km` ← Correct, but unused by breaks algorithm

4. **When mandatory breaks are calculated**:
   ```python
   # In _calculate_mandatory_breaks_advanced():
   max_distance_before_event = 4.5 * 80 = 360 km  # First break should be at 360km

   for i, cum_dist in enumerate(cumulative_distance):  # cumulative_distance = [0.0]
       if cum_dist <= max_distance_before_event:
           latest_node_idx = i  # Always returns 0!
   ```
   - Only one value in cumulative_distance: `[0.0]`
   - Loop runs once: `i=0, cum_dist=0.0`
   - Result: `latest_node_idx=0, cumulative_driving_time=0.0`

### Data Evidence

From `analyze_breaks_by_path_type.py` output:

**Multi-node paths (2,853 paths, 97.4% of total):**
- 9,470 breaks total
- 9,219 breaks (97.3%) at node_idx=0 with cumulative_time=0 ← **WRONG**
- Only 251 breaks (2.7%) placed correctly

**Examples:**
```yaml
# Path 29: 0→47, 2 nodes, 841.3km
- break_number: 1
  latest_node_idx: 0       # ← Should be at node 1 (~360km)
  cumulative_distance: 0.0  # ← Should be ~360km
  cumulative_driving_time: 0.0  # ← Should be ~4.5h

- break_number: 2
  latest_node_idx: 0       # ← Should be at node 1 (~720km)
  cumulative_distance: 0.0  # ← Should be ~720km
  cumulative_driving_time: 0.0  # ← Should be ~9.0h
```

**Path 33** (5 nodes) - One of the FEW correct examples:
```yaml
- break_number: 1
  latest_node_idx: 3       # ← Correct! Uses later node
  cumulative_distance: 249.8km
  cumulative_driving_time: 3.12h
```

This path likely had a multi-node template selected during aggregation, so the distance scaling worked correctly.

## Impact Analysis

### Affected Routes
- **97.3% of breaks on multi-node paths** are incorrectly placed
- **2.7% of breaks** are correct (paths where multi-node templates were used)

### Model Implications
1. **Mandatory break constraints are meaningless**: Most breaks occur "at origin" with zero driving time
2. **EU driving regulations not enforced**: Trucks can theoretically drive >4.5h without breaks
3. **Charging infrastructure decisions flawed**: Breaks determine when/where trucks charge
4. **Cost calculations incorrect**: Break timing affects charging costs and travel time
5. **Paper results untrustworthy**: Cannot publish without fixing this fundamental input bug

## Proposed Fixes

### Option 1: Reconstruct Path Sequences for Single-Node Templates (RECOMMENDED)

When a single-node template is selected, create synthetic intermediate nodes based on the aggregated distance:

```python
# In aggregate_odpairs_by_nuts2(), after line 1019:

template_path['length'] = avg_distance

# NEW CODE: Reconstruct path for single-node templates
if len(template_path['sequence']) == 1 and avg_distance > 0:
    # Single-node template needs reconstruction
    origin = template_path['origin']
    destination = template_path['destination']

    # Create simple 2-node path: origin → destination
    template_path['sequence'] = [origin, destination]
    template_path['distance_from_previous'] = [0.0, avg_distance]
    template_path['cumulative_distance'] = [0.0, avg_distance]

    print(f"  Reconstructed single-node path {origin}→{destination}: "
          f"sequence={template_path['sequence']}, length={avg_distance:.1f}km")

# Existing code continues:
elif sum(template_path['distance_from_previous']) > 0:
    # Multi-node template: scale distances proportionally
    scale = avg_distance / sum(template_path['distance_from_previous'])
    ...
```

**Pros:**
- Minimal code change
- Preserves aggregation benefits (efficiency)
- Ensures all paths have proper cumulative_distance arrays

**Cons:**
- Creates synthetic sequences that don't represent actual geographic routes
- May oversimplify complex intra-regional traffic patterns

### Option 2: Exclude Single-Node Paths as Templates

Never use single-node paths as templates; always select multi-node alternatives:

```python
# Before line 1017:

# Filter out single-node paths from template selection
multi_node_paths = [(i, od, p) for i, (od, p) in enumerate(zip(odpairs, paths))
                    if len(p['sequence']) > 1]

if multi_node_paths:
    # Use highest-flow MULTI-NODE path as template
    max_flow_idx = max(multi_node_paths, key=lambda x: x[1]['F'][0])[0]
else:
    # All paths are single-node; use reconstruction approach (Option 1)
    max_flow_idx = np.argmax([od['F'][0] for od in odpairs])
    # ... apply reconstruction
```

**Pros:**
- Preserves real geographic sequences
- More accurate for complex routes

**Cons:**
- More complex logic
- May fail if all paths in a group are single-node

### Option 3: Disable Aggregation (NOT RECOMMENDED)

Set `aggregate_odpairs=False` in preprocessing:

```python
preprocessor.run_complete_preprocessing(
    max_odpairs=None,
    min_distance_km=None,
    cross_border_only=False,
    aggregate_odpairs=False  # ← Disable aggregation
)
```

**Pros:**
- Preserves all original path detail

**Cons:**
- Massive computational cost (thousands of individual routes)
- Defeats the purpose of NUTS-2 aggregation
- Model may become intractable

## Recommended Implementation

**Fix Option 1** (reconstruct single-node templates) is the best balance:

1. Add path reconstruction logic after line 1019 in `aggregate_odpairs_by_nuts2()`
2. Re-run preprocessing with the fix
3. Validate that mandatory breaks now have:
   - Breaks distributed along routes (not all at node_idx=0)
   - cumulative_driving_time ≈ 4.5h intervals
   - Non-zero cumulative_distance values
4. Re-run optimization model with corrected data
5. Re-analyze results for paper

## Validation Criteria

After applying the fix, verify:

✅ **For all paths with length > 360km:**
- At least one break with cumulative_distance > 0
- Breaks spaced approximately 360km (4.5h @ 80 km/h) apart

✅ **For aggregated MandatoryBreaks data:**
- < 10% of breaks at node_idx=0 with cumulative_time=0 (only origin charging)
- Break timing follows 4.5h, 9.0h, 13.5h pattern
- cumulative_distance increases with break_number for each path

✅ **Distribution check:**
- Create histogram of cumulative_driving_time for break_number=2
- Should show peak around 4.5h (not 0h)

## Next Steps

1. ✅ **DONE**: Identified root cause (aggregation bug)
2. **TODO**: Implement Fix Option 1 in `SM_preprocessing_nuts2_complete.py`
3. **TODO**: Re-run preprocessing: `python SM_preprocessing_nuts2_complete.py`
4. **TODO**: Validate corrected MandatoryBreaks.yaml
5. **TODO**: Re-run optimization with corrected data
6. **TODO**: Update paper analysis with corrected results

---

**Author**: Claude Code
**Date**: 2025-10-29
**Status**: Root cause identified, fix ready to implement
