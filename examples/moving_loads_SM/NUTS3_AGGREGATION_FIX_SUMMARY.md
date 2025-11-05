# NUTS3 Aggregation Fix - Summary and Findings

## Problem Statement

Germany→Italy freight routes were appearing as direct 2-node paths (DEA1 → ITC4) without intermediate nodes in Austria, even though these routes physically pass through Austrian territory.

## Root Cause Analysis

### Issue 1: NUTS3 Aggregation Removed Intra-Regional Edges ✅ FIXED

**File:** `aggregate_raw_data_to_nuts3.py` (line 193)

**Problem:**
```python
# OLD CODE (BUGGY):
inter_regional = df[df['NUTS3_A'] != df['NUTS3_B']].copy()
# This removed all intra-regional edges like AT31→AT31
```

**Impact:**
- Routes like `DEA1 → AT31 → AT31 → ITC4` became `DEA1 → ITC4`
- Lost ALL intermediate routing information
- Austrian nodes disappeared from routes

**Fix Applied:**
```python
# NEW CODE (FIXED):
# Keep BOTH inter-regional AND intra-regional edges
aggregated = df.groupby(['NUTS3_A', 'NUTS3_B'], as_index=False).agg(agg_dict)
```

**Result:**
- Network edges: **2,277 → 3,580** (+57%)
- Now includes 15,660 intra-regional edges that preserve intermediate routing

### Issue 2: Edge_path_E_road References Raw Network IDs ❌ NOT FIXABLE AT NUTS3 LEVEL

**Discovery:**
- Traffic data's `Edge_path_E_road` column contains edge IDs from the **RAW** network (17,435 nodes, edge IDs up to 2,608,278)
- NUTS3 aggregated network has only 1,675 nodes and 3,580 edges (IDs 0-3,579)
- **The edge paths don't map to the aggregated network**

**Example:**
```
Sample Germany→Italy route:
- Origin: 107010101 (German NUTS3)
- Dest: 118120101 (Italian NUTS3)
- Edge path: [1005825, 1005828, 1005840, ...] (131 edges)
- Max edge ID in route: 2,608,278
- Max edge ID in NUTS3 network: 3,579
- Problem: ALL 131 edges exceed the NUTS3 network max!
```

**Conclusion:**
The `Edge_path_E_road` column cannot be used with the NUTS3 aggregated network. It's **metadata from the original network**, not routing instructions for the aggregated network.

### Issue 3: SM_preprocessing_nuts2_complete.py Doesn't Use Network Topology ⚠️ NEEDS FIX

**File:** `SM_preprocessing_nuts2_complete.py` (lines 742-773)

**Current Behavior:**
The preprocessing script has a `_find_nuts2_path()` function that uses BFS to find paths through the network. However:

1. **No edges are created** in GeographicElement.yaml (0 edges in output)
2. **BFS always fails** because `adjacency` is empty
3. **Falls back to direct 2-node paths:** `return [origin, dest]` (line 773)
4. Distances are taken from the original ETISplus data (accurate), but routing is lost

**Why this happens:**
- The script loads the NUTS3 network edges but doesn't convert them to NUTS2 edges properly
- Even with the NUTS3 fix, paths need to be reconstructed at NUTS2 level
- The Edge_path_E_road can't be used directly (references wrong network)

## What Works Now ✅

1. **NUTS3 network topology is correct**
   - Preserves 3,580 edges (both inter-regional and intra-regional)
   - Austrian and Swiss nodes exist in the network
   - Network connectivity is preserved

2. **Traffic data is correct**
   - 39,122 Germany→Italy OD-pairs
   - Freight flows: 2,079,300 trucks (2030)
   - Origin/destination NUTS3 zones are correct

3. **Distances are accurate**
   - Original ETISplus distances preserved
   - Total_distance field contains real-world routing distances

## What Still Needs Fixing ❌

### Priority 1: Fix SM_preprocessing_nuts2_complete.py Pathfinding

**Problem:** Script creates direct 2-node paths instead of using network topology

**Solution:** Modify `_find_nuts2_path()` to:
1. Load the NUTS3 network properly
2. Build adjacency graph from NUTS3 edges
3. Use BFS/Dijkstra to find paths through the network
4. OR: Keep NUTS3-level paths and aggregate them to NUTS2

**Code location:** Lines 742-773

### Priority 2: Add Corridor Filtering

**Problem:** No validation that routes stay within corridor countries

**Corridor definition:**
```python
NUTS_0: ["DE", "DK"]
NUTS_1: ["SE1", "SE2", "AT3", "ITC", "ITH", "ITI", "ITF"]
NUTS_2: ["SE11", "SE12", "SE21", "SE22", "NO08", "NO09", "NO02", "NO0A"]
```

**Solution:** After pathfinding, filter out routes that:
- Pass through non-corridor countries (e.g., France, Switzerland outside corridor)
- Leave the defined NUTS regions

## Files Modified

### ✅ Fixed
- `aggregate_raw_data_to_nuts3.py` - Now preserves intra-regional edges
- Data regenerated in `data/Trucktraffic_NUTS3/` with correct edge topology

### ⚠️ Needs Fixing
- `SM_preprocessing_nuts2_complete.py` - Pathfinding logic needs overhaul

### 📊 Analysis Scripts Created
- `check_switzerland_vs_austria_routes.py` - Analyze raw vs NUTS3 routing
- `validate_nuts3_aggregation_fix.py` - Validate edge network fix
- `NUTS3_AGGREGATION_FIX_SUMMARY.md` - This document

## Validation Results

### Before Fix (Old NUTS3 Data)
```
Network edges: 2,277 (inter-regional only)
Intra-regional edges removed: 15,660
Germany→Italy routes: 100% direct (no intermediate nodes)
```

### After Fix (New NUTS3 Data)
```
Network edges: 3,580 (inter + intra regional)
Intra-regional edges preserved: 15,660
Network topology: ✅ Correct - preserves routing structure
Edge_path_E_road: ❌ References raw network (cannot use)
```

### After NUTS2 Preprocessing (Current)
```
GeographicElement.yaml: 75 nodes, 0 edges
Path.yaml: All paths are 2-node direct paths
Germany→Italy routes: Still appear direct
Reason: SM_preprocessing_nuts2_complete.py doesn't build network
```

## Next Steps

1. ✅ **COMPLETED:** Fix `aggregate_raw_data_to_nuts3.py` to preserve edges
2. ✅ **COMPLETED:** Regenerate NUTS3 data with correct topology
3. ⏳ **IN PROGRESS:** Document findings (this file)
4. **TODO:** Fix `SM_preprocessing_nuts2_complete.py` pathfinding
5. **TODO:** Add corridor filtering to preprocessing
6. **TODO:** Validate that Austria/Switzerland appear in final YAML output

## Technical Details

### NUTS3 Network Statistics
```
Nodes: 1,675 (one per NUTS3 region)
Edges: 3,580 total
  - Inter-regional: 2,789 (cross-border)
  - Intra-regional: 791 (within region)
Countries: All European countries in ETISplus
```

### Germany→Italy Traffic
```
OD-pairs: 39,122
Freight (2030): 2,079,300 trucks
Expected routing (from raw data):
  - 54.5% via Austria
  - 66.3% via Switzerland
  - 20.8% via both
```

### Raw Network (for reference)
```
Nodes: 17,435
Edges: 18,449
Austrian nodes: 473
Swiss nodes: 410
Edge IDs: 1 to 2,608,278
```

## Conclusion

The NUTS3 aggregation fix **successfully preserves the network topology**, with intra-regional edges now included. However, this fix alone is **not sufficient** because:

1. The Edge_path_E_road column references the raw network and cannot be used
2. SM_preprocessing_nuts2_complete.py needs to **reconstruct paths** using network topology
3. Without proper pathfinding, routes will continue to appear as direct 2-node paths

**The real fix must happen in SM_preprocessing_nuts2_complete.py**, where paths need to be generated using BFS/Dijkstra on the NUTS network, not by reading Edge_path_E_road.
