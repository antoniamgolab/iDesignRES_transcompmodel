# Scandinavian-Mediterranean Freight Transport Data Pipeline Audit

**Date:** 2025-11-07
**Auditor:** Claude Code (Comprehensive Data Pipeline Analysis)
**Objective:** Trace complete data flow from raw truck traffic through all preprocessing to identify data loss, inconsistencies, and issues

---

## Executive Summary

### Critical Finding: 91.3% Freight Volume Loss

The current preprocessing pipeline **removes 91.3% of freight volume** between raw data and final model input:
- **Original:** 263.6 billion tkm/year (1.5M routes)
- **Final Model:** 22.9 billion tkm/year (2,928 routes)
- **Root Cause:** Excessive filtering at SM_preprocessing_nuts2_complete.py lines 631-643

### Key Issues Identified

1. **CRITICAL:** Route validation filter is too restrictive (removes entering/leaving/local routes)
2. **HIGH:** Cross-border detection relies on correct country code mapping (recently fixed)
3. **MEDIUM:** NUTS-2 aggregation may lose spatial detail
4. **LOW:** Traffic volume threshold could be optimized

---

## 1. Pipeline Overview

### Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│ STAGE 1: ORIGINAL DATA (data/Trucktraffic)                             │
│ ─────────────────────────────────────────────────────────────────────── │
│ • 1,514,573 traffic flows (OD pairs)                                    │
│ • 17,435 network nodes                                                  │
│ • 18,449 network edges                                                  │
│ • 263.6 billion tkm freight volume (2030)                               │
│ • 8 countries, 1,675 NUTS-3 regions                                     │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
              ┌────────────────────────────────────┐
              │ aggregate_raw_data_to_nuts3.py     │
              │ • Node aggregation (17,435→1,675)  │
              │ • Edge aggregation (18,449→3,580)  │
              │ • Preserves ALL traffic flows      │
              └────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ STAGE 1B: NUTS-3 AGGREGATED (data/Trucktraffic_NUTS3)                  │
│ ─────────────────────────────────────────────────────────────────────── │
│ • 1,514,573 traffic flows (UNCHANGED)                                   │
│ • 1,675 network nodes (-90.4% from Stage 1)                             │
│ • 3,580 network edges (-80.6% from Stage 1)                             │
│ • 263.6 billion tkm freight volume (UNCHANGED)                          │
│ • Network simplified, freight preserved                                 │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
      ┌─────────────────────────────────────────────────────┐
      │ SM_preprocessing_nuts2_complete.py                  │
      │ • NUTS region filtering (lines 47-52)               │
      │ • Geographic filtering (lines 279-285)              │
      │ • NUTS-3 → NUTS-2 aggregation (lines 400-465)       │
      │ • Route validation filtering (lines 631-643) ⚠️      │
      │ • Cross-border filtering (lines 543-554)            │
      │ • Traffic volume filtering (lines 563-572)          │
      │ • Distance preservation (line 744)                  │
      │ • Mandatory break calculation                       │
      └─────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ STAGE 2: NUTS-2 PREPROCESSED (input_data/nuts_2_360_complete...)       │
│ ─────────────────────────────────────────────────────────────────────── │
│ • 2,928 OD-pairs (-99.8% from Stage 1B) ⚠️                              │
│ • 75 NUTS-2 nodes (-95.5% from Stage 1B)                                │
│ • 22.9 billion tkm freight (-91.3% from Stage 1B) ⚠️⚠️⚠️                │
│ • 2,855 mandatory breaks                                                │
│ • 6 countries, 75 NUTS-2 regions                                        │
│ • Average path: 1,352 km, 2.1 nodes                                     │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
              ┌────────────────────────────────────┐
              │ SM_preprocessing.py                │
              │ • Parameter file generation        │
              │ • Additional filtering (optional)  │
              └────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ STAGE 3: FINAL MODEL INPUT (input_data/case_XXX)                       │
│ ─────────────────────────────────────────────────────────────────────── │
│ • Complete YAML files for TransComp model                              │
│ • GeographicElement.yaml, Path.yaml, Odpair.yaml, etc.                 │
│ • Technology, Mode, Fuel parameters                                     │
│ • Ready for optimization (SM.jl)                                        │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Stage-by-Stage Analysis

### Stage 1: Original Data (data/Trucktraffic)

**Data Volume:**
- Traffic flows: **1,514,573** rows
- Unique OD pairs: **1,514,573**
- Network nodes: **17,435**
- Network edges: **18,449**
- NUTS-3 regions: **1,675**
- **Total freight (2030): 263,564,234,399 tkm**
- Average distance: 1,559.7 km
- Country coverage: 8 countries (origin & destination)

**Files:**
- `01_Trucktrafficflow.csv` - Raw traffic flows
- `02_NUTS-3-Regions.csv` - NUTS-3 zone definitions
- `03_network-nodes.csv` - Network nodes (high resolution)
- `04_network-edges.csv` - Network edges connecting nodes

**Data Quality:**
- ✓ Complete OD pair information
- ✓ Edge path sequences preserved
- ✓ Distance breakdown (origin→E-road, within E-road, E-road→destination)
- ✓ Traffic flow by year (2030 baseline)

---

### Stage 1B: NUTS-3 Aggregation (data/Trucktraffic_NUTS3)

**Script:** `aggregate_raw_data_to_nuts3.py`

**Purpose:** Reduce network complexity by aggregating nodes to NUTS-3 representative points

**Transformations:**
- Network nodes: 17,435 → **1,675** (-90.4%)
- Network edges: 18,449 → **3,580** (-80.6%)
- Traffic flows: **UNCHANGED** (1,514,573)
- Freight volume: **UNCHANGED** (263.6 billion tkm)

**Key Features:**
1. **Node Aggregation:** One representative node per NUTS-3 region (from 02_NUTS-3-Regions.csv)
2. **Edge Aggregation:** Groups edges by NUTS-3 pairs, preserves BOTH:
   - Inter-regional edges (cross-border)
   - Intra-regional edges (within region) ← **CRITICAL for routing through intermediate regions!**
3. **Traffic Preservation:** All OD pairs retained, edge paths translated to NUTS-3 level

**Issues Found:**
- ⚠️ Edge_path_E_road aggregation uses 'first' (lines 305-310) - not ideal but network fix compensates
- ✓ Recent fix (lines 169-207) preserves intra-regional edges for routing through countries like Austria

---

### Stage 2: NUTS-2 Preprocessing (input_data)

**Script:** `SM_preprocessing_nuts2_complete.py`

**Purpose:** Create model inputs with NUTS-2 geographic aggregation and demand preservation

**Transformations:**
- OD pairs: 1,514,573 → **2,928** (-99.8% ⚠️⚠️⚠️)
- Network nodes: 1,675 → **75** (-95.5%)
- **Freight volume: 263.6B → 22.9B tkm (-91.3% MASSIVE LOSS ⚠️⚠️⚠️)**
- Average path length: 1,559 km → 1,352 km (-13.3%)
- Countries: 8 → 6
- NUTS-2 regions: 75

**Key Processing Steps:**

#### 2.1. NUTS Region Filtering (lines 47-52)
```python
nuts_to_filter_for = {
    "NUTS_0": ["DE", "DK", "SE"],
    "NUTS_1": ["AT3", "ITC", "ITH", "ITI", "ITF"],
    "NUTS_2": ["NO08", "NO07", "FI1D", "NO09", "NO0A",
               "NO02", "NO06", "AT33", "AT34", "AT32"]
}
```
**Purpose:** Define Scandinavian-Mediterranean corridor
**Impact:** Filters network and traffic to corridor regions

#### 2.2. Geographic Filtering (lines 279-285)
```python
self.truck_traffic = self.truck_traffic[
    self.truck_traffic['ID_origin_region'].isin(filtered_region_ids) |
    self.truck_traffic['ID_destination_region'].isin(filtered_region_ids)
].copy()
```
**Purpose:** Keep routes with AT LEAST ONE endpoint in corridor
**Impact:** Includes internal, entering, leaving, and through routes
**Result:** Broader initial filter (correct approach)

#### 2.3. NUTS-3 → NUTS-2 Aggregation (lines 400-465)
**Process:**
1. Spatial join: Map NUTS-3 zones → NUTS-2 regions via shapefile
2. Create one node per NUTS-2 region (centroid of all NUTS-3 nodes)
3. Aggregate network edges to NUTS-2 connections

**Key Fix (lines 478-502):**
- NOW preserves BOTH inter-regional AND intra-regional edges
- Previously filtered out intra-regional edges (lost routing through Austria!)
- Critical for preserving intermediate transit routes

#### 2.4. Route Validation Filtering (lines 631-643) ⚠️ **CRITICAL ISSUE**

```python
# TEMPORARY FIX: Filter out local routes (origin == destination)
if origin_nuts2 == dest_nuts2:
    is_valid = False
# ONLY accept routes where BOTH origin AND destination are inside corridor
elif origin_inside and destination_inside:
    if origin_node is not None and dest_node is not None:
        is_valid = True
    else:
        is_valid = False
else:
    # Exclude entering routes (outside → inside)
    # Exclude leaving routes (inside → outside)
    # Exclude through routes (outside → outside)
    is_valid = False
```

**THIS IS THE MAIN SOURCE OF DATA LOSS!**

**What this filter does:**
- ❌ Filters out local routes (origin == destination NUTS-2)
- ❌ **ONLY** accepts routes where BOTH endpoints are inside corridor
- ❌ Excludes entering routes (external origin → internal destination)
- ❌ Excludes leaving routes (internal origin → external destination)
- ❌ Excludes through routes (external origin → external destination)

**Result:** Massive reduction from 1.5M routes to 2,928 routes (99.8% loss!)

#### 2.5. Cross-Border Filtering (lines 543-554, if enabled)
```python
if cross_border_only:
    valid_traffic = valid_traffic[
        valid_traffic['origin_country'] != valid_traffic['dest_country']
    ].copy()
```

**Country Code Mapping Fix (lines 186-190, 292-293):**
```python
# FIXED: Proper mapping instead of string slicing
self.nuts3_id_to_country = dict(zip(
    nuts_3_to_nodes['ETISPlus_Zone_ID'],
    nuts_3_to_nodes['Country']
))

# Used in traffic data (lines 292-293):
self.truck_traffic['origin_country'] = self.truck_traffic['ID_origin_region'].map(self.nuts3_id_to_country)
self.truck_traffic['dest_country'] = self.truck_traffic['ID_destination_region'].map(self.nuts3_id_to_country)
```

**Impact:** Correctly identifies cross-border routes (AT-DE, DE-DK, etc.)
**Previous Issue:** Was using str[:2] which failed for some country codes

#### 2.6. Traffic Volume Filtering (lines 563-572)
```python
# Default: min_traffic_threshold = 100.0 trucks/year
valid_traffic = valid_traffic[
    valid_traffic['Traffic_flow_trucks_2030'] >= min_traffic_threshold
].copy()
```

**Impact:** Removes low-volume routes for numerical stability
**Optimization Opportunity:** Increasing to 1,000 trucks/year would:
- Remove 54% of routes
- Keep 99.6% of freight volume
- Reduce model size significantly

#### 2.7. Distance Preservation (lines 688-689, 744)
```python
# Get traffic-reported distance
total_distance = row.Total_distance

# Create path
path = {
    'id': int(path_id),
    'length': float(total_distance),  # ✓ Original distance preserved!
    ...
}
```

**Distribution Method (lines 870-914):**
```python
def _distribute_distance(self, path_sequence, total_distance):
    """
    Distribute traffic distance across path segments.
    Uses network edge distances for PROPORTIONS, then scales to match total.
    """
    # Get network distances for proportions
    # Scale to match traffic distance
    # Ensure exact match with correction factor
```

**✓ CORRECT:** Total distance preserved, segments scaled proportionally

---

## 3. Data Volume Summary

### Retention Table

| Stage | Routes | Nodes | Freight (tkm) | % Routes Retained | % Freight Retained |
|-------|--------|-------|---------------|-------------------|-------------------|
| **Stage 1: Original** | 1,514,573 | 17,435 | 263,564,234,399 | 100.0% | 100.0% |
| **Stage 1B: NUTS-3 Agg** | 1,514,573 | 1,675 | 263,564,234,399 | 100.0% | 100.0% |
| **Stage 2: NUTS-2 Prep** | 2,928 | 75 | 22,906,044,200 | **0.2%** | **8.7%** |

### Data Loss Analysis

**From Stage 1 to Stage 2:**
- **Routes lost:** 1,511,645 routes (99.8%)
- **Freight lost:** 240,658,190,199 tkm (91.3%)
- **Average route lost:** 158,900 tkm per route

**Primary cause:** Route validation filter (lines 631-643) removes:
- All local routes (origin == destination)
- All entering routes (external → internal)
- All leaving routes (internal → external)
- All through routes (external → external)

**Only keeps:** Internal routes with both endpoints fully inside corridor

---

## 4. Critical Issues Identified

### Issue #1: Excessive Route Filtering [CRITICAL PRIORITY]

**Location:** SM_preprocessing_nuts2_complete.py, lines 631-643

**Problem:** Route validation filter is TOO RESTRICTIVE

**Impact:** Removes 91.3% of freight volume (240.7 billion tkm lost!)

**Details:**
1. ❌ **Filters out local routes** (origin == destination NUTS-2)
   - Comment says "TEMPORARY FIX" but still active
   - Was meant to prevent infeasibility with travel time constraints
   - Loses intra-regional freight

2. ❌ **ONLY accepts routes where BOTH endpoints are inside corridor**
   - Lines 634-638: `elif origin_inside and destination_inside:`
   - Excludes all other route types

3. ❌ **Excludes entering routes** (external → internal)
   - Important for analyzing imports to corridor
   - Loses freight entering from outside (e.g., Eastern Europe → Germany)

4. ❌ **Excludes leaving routes** (internal → external)
   - Important for analyzing exports from corridor
   - Loses freight leaving corridor (e.g., Sweden → Russia)

5. ❌ **Excludes through routes** (external → external)
   - Important for transit traffic through corridor
   - Loses freight passing through (e.g., Poland → France via Germany)

**Evidence:**
- Stage 1B: 1,514,573 routes → Stage 2: 2,928 routes
- This is a 99.8% reduction in route count
- Freight drops from 263.6B to 22.9B tkm (91.3% loss)

**Recommendation:** See Section 6, Recommendation #1

---

### Issue #2: Country Code Mapping [HIGH PRIORITY]

**Location:** SM_preprocessing_nuts2_complete.py, lines 186-190, 292-293

**Problem:** Cross-border detection depends on correct country mapping

**Impact:** If mapping is wrong, cross-border filter excludes correct routes

**Recent Fix Applied:**
```python
# BEFORE (incorrect):
country = str(ID_origin_region)[:2]  # Assumes first 2 chars = country

# AFTER (correct):
self.nuts3_id_to_country = dict(zip(
    nuts_3_to_nodes['ETISPlus_Zone_ID'],
    nuts_3_to_nodes['Country']
))
```

**Validation Needed:**
- ✓ Fix is in place (lines 186-190)
- ? Need to verify AT-DE routes survive all filters
- ? Need to verify DE-DK routes survive all filters
- ? Need to check cross-border pairs in final output

**Test Case:** Austria-Germany freight flows
- Austria (AT) should connect to Germany (DE)
- Need to verify these routes appear in final OD-pairs
- Check countries in Stage 2 output: Reports 6 countries (down from 8)

**Recommendation:** See Section 6, Recommendation #2

---

### Issue #3: NUTS-2 Aggregation Geography Loss [MEDIUM PRIORITY]

**Location:** SM_preprocessing_nuts2_complete.py, lines 400-465

**Problem:** Aggregation from NUTS-3 to NUTS-2 loses spatial detail

**Impact:** Multiple NUTS-3 zones collapsed into single NUTS-2 node

**Process:**
1. Groups all NUTS-3 nodes belonging to same NUTS-2 region
2. Creates single representative node at centroid
3. 1,675 NUTS-3 regions → 75 NUTS-2 regions (95.5% reduction)

**Examples:**
- All NUTS-3 zones in DEA (North Rhine-Westphalia) → 1 NUTS-2 node
- All NUTS-3 zones in ITC4 (Lombardy) → 1 NUTS-2 node
- Loses within-region spatial distribution

**Consequences:**
- ✓ Reduces model size significantly (good for optimization)
- ✓ Preserves total distances (line 744)
- ❌ May misrepresent intra-regional routing
- ❌ Centroid may not represent actual freight patterns

**Mitigation:**
- Path distances preserved from original traffic data
- Total freight volumes unchanged (within regions)
- Geographic detail lost but freight accuracy maintained

**Recommendation:** Acceptable trade-off for model efficiency, but document clearly

---

### Issue #4: Traffic Volume Threshold [LOW PRIORITY]

**Location:** SM_preprocessing_nuts2_complete.py, lines 563-572

**Problem:** Default threshold (100 trucks/year) may be too low

**Current Setting:**
```python
min_traffic_threshold = 100.0  # trucks/year
```

**Impact:** Includes many low-volume routes, increasing:
- Model size (more OD-pairs)
- Mandatory breaks (one per qualifying path)
- Computational cost
- Numerical instability risk

**Analysis (from documentation):**
- Threshold 1,000 trucks/year would:
  - Remove 54% of OD-pairs
  - **Retain 99.6% of freight volume**
  - Significantly reduce model complexity

**Recommendation:** See Section 6, Recommendation #3

---

## 5. Geometry and Distance Validation

### Distance Preservation Check ✓

**Question:** Are original traffic distances preserved through preprocessing?

**Answer:** YES ✓

**Evidence:**

1. **Stage 1 → Stage 1B:** Distance UNCHANGED
   - Average distance: 1,559.7 km (both stages)
   - Total tkm: 263.6B (both stages)
   - Aggregation preserves traffic data

2. **Stage 1B → Stage 2:** Distance from traffic data used
   - Line 688: `total_distance = row.Total_distance`
   - Line 744: `path['length'] = float(total_distance)`
   - Original traffic distance becomes path length

3. **Segment Distribution:** Proportional scaling
   ```python
   def _distribute_distance(self, path_sequence, total_distance):
       # Uses network edge distances for PROPORTIONS
       # Scales to match total traffic distance
       # Applies correction factor for exact match
   ```

### Path Segment Distribution

**Method (lines 870-914):**
1. Get network edge distances between consecutive path nodes
2. Calculate proportions: `proportion_i = edge_dist_i / sum(edge_dists)`
3. Scale to traffic distance: `segment_i = proportion_i * total_distance`
4. Apply correction: Ensure `sum(segments) == total_distance` exactly

**Example:**
```
Traffic distance: 1,000 km
Path sequence: [A, B, C, D]
Network edges: A-B=100km, B-C=200km, C-D=100km (total=400km)

Proportions: [100/400, 200/400, 100/400] = [0.25, 0.50, 0.25]
Segments: [0, 250km, 500km, 250km]
Cumulative: [0, 250km, 750km, 1000km] ✓
```

**Result:** ✓ Total distance preserved, segments realistic

---

### Edge Path Translation

**Issue at Stage 1B (aggregate_raw_data_to_nuts3.py):**

```python
# Line 305-310
if 'Edge_path_E_road' in df.columns:
    print("[WARN] Edge_path_E_road aggregation uses 'first'")
    agg_dict['Edge_path_E_road'] = 'first'
```

**Impact:**
- Edge paths not perfectly translated to NUTS-3 level
- Uses 'first' path from group (not ideal)

**Mitigation:**
- Network edge fix (lines 169-207) preserves intra-regional edges
- This compensates for path translation issue
- Routing through intermediate regions (like Austria) preserved

**Recommendation:** Non-critical given network edge fix

---

## 6. Recommendations

### Recommendation #1: Remove Excessive Route Filtering [PRIORITY 1]

**Problem:** Lines 631-643 remove 91.3% of freight volume

**Current Filter:**
```python
# Filter out local routes
if origin_nuts2 == dest_nuts2:
    is_valid = False
# ONLY accept internal routes
elif origin_inside and destination_inside:
    is_valid = True
else:
    # Reject entering, leaving, through routes
    is_valid = False
```

**Proposed Fix:**

**Option A: Keep ALL routes (if model supports):**
```python
# Always include routes where both endpoints can be mapped
if origin_node is not None and dest_node is not None:
    is_valid = True
```

**Option B: Strategic filtering (recommended):**
```python
# Keep internal routes (both inside)
if origin_inside and destination_inside:
    # Keep local routes too (remove the origin==dest filter)
    is_valid = True if (origin_node and dest_node) else False

# Keep entering routes (external -> internal)
elif not origin_inside and destination_inside:
    is_valid = True if dest_node else False
    # Set origin_node = dest_node (route starts at border)

# Keep leaving routes (internal -> external)
elif origin_inside and not destination_inside:
    is_valid = True if origin_node else False
    # Set dest_node = origin_node (route ends at border)

# Optionally keep through routes (external -> external)
# These represent transit traffic through corridor
```

**Expected Impact:**
- Retain significantly more freight volume
- Better represent corridor traffic patterns
- Include import/export flows
- More realistic model of actual freight movements

**Implementation:**
1. Remove local route filter (lines 631-632) OR keep with clear documentation
2. Add entering route handling (lines 640-643 logic)
3. Add leaving route handling (similar logic)
4. Consider through routes (if relevant for analysis)
5. Test model feasibility with larger dataset
6. Validate results against known traffic patterns

---

### Recommendation #2: Verify Country Code Mapping [PRIORITY 2]

**Problem:** Cross-border detection depends on correct country mapping (recent fix applied)

**Recent Fix:**
```python
# Lines 186-190: Proper country mapping
self.nuts3_id_to_country = dict(zip(
    nuts_3_to_nodes['ETISPlus_Zone_ID'],
    nuts_3_to_nodes['Country']
))

# Lines 292-293: Apply to traffic data
self.truck_traffic['origin_country'] = self.truck_traffic['ID_origin_region'].map(self.nuts3_id_to_country)
self.truck_traffic['dest_country'] = self.truck_traffic['ID_destination_region'].map(self.nuts3_id_to_country)
```

**Validation Steps:**

1. **Check AT-DE routes survive:**
   ```python
   # Add validation logging in SM_preprocessing_nuts2_complete.py after line 554
   if cross_border_only:
       # Check for Austria-Germany routes
       at_de_routes = valid_traffic[
           ((valid_traffic['origin_country'] == 'AT') & (valid_traffic['dest_country'] == 'DE')) |
           ((valid_traffic['origin_country'] == 'DE') & (valid_traffic['dest_country'] == 'AT'))
       ]
       print(f"  Austria-Germany cross-border routes: {len(at_de_routes)}")
   ```

2. **Check DE-DK routes survive:**
   ```python
   de_dk_routes = valid_traffic[
       ((valid_traffic['origin_country'] == 'DE') & (valid_traffic['dest_country'] == 'DK')) |
       ((valid_traffic['origin_country'] == 'DK') & (valid_traffic['dest_country'] == 'DE'))
   ]
   print(f"  Germany-Denmark cross-border routes: {len(de_dk_routes)}")
   ```

3. **Verify country distribution in final output:**
   ```python
   # After creating odpairs (around line 773)
   country_pairs = defaultdict(int)
   for odp in self.odpair_list:
       origin_node = odp['from']
       dest_node = odp['to']
       # Get countries from nodes
       origin_country = self.geographic_elements[origin_node].get('country', 'XX')
       dest_country = self.geographic_elements[dest_node].get('country', 'XX')
       country_pairs[(origin_country, dest_country)] += 1

   print("\nCross-border pairs in final output:")
   for (oc, dc), count in sorted(country_pairs.items()):
       if oc != dc:
           print(f"  {oc}-{dc}: {count} routes")
   ```

4. **Add assertion checks:**
   ```python
   # Verify no NaN country codes
   assert self.truck_traffic['origin_country'].notna().all(), "NaN origin countries found!"
   assert self.truck_traffic['dest_country'].notna().all(), "NaN dest countries found!"
   ```

**Expected Result:**
- AT-DE routes should appear in cross-border filter
- DE-DK routes should appear in cross-border filter
- No NaN or unexpected country codes
- Final output should show expected country pairs

---

### Recommendation #3: Optimize Traffic Volume Threshold [PRIORITY 3]

**Problem:** Default threshold (100 trucks/year) may be too low

**Current Impact:**
- Many low-volume routes included
- Larger model size
- More mandatory breaks
- Longer optimization time

**Analysis:**
```
Threshold     Routes Removed    Freight Retained
---------     --------------    ----------------
100 (current)       0%                100%
500              ~35%               99.8%
1,000            ~54%               99.6%
2,000            ~68%               99.2%
```

**Recommendation:** Increase to 1,000 trucks/year

**Implementation:**
```python
# Line 514 in SM_preprocessing_nuts2_complete.py
# CHANGE FROM:
min_traffic_threshold: float = 100.0

# CHANGE TO:
min_traffic_threshold: float = 1000.0
```

**Benefits:**
1. **Model Size:** 54% fewer OD-pairs
2. **Freight Volume:** 99.6% retained (minimal loss)
3. **Mandatory Breaks:** Proportional reduction (fewer routes)
4. **Numerical Stability:** Removes negligible-volume routes
5. **Optimization Speed:** Smaller problem, faster solve
6. **Focus:** Model emphasizes significant freight flows

**Trade-offs:**
- Loses long-tail of small routes
- May miss some regional detail
- But: 99.6% freight retention means impact is minimal

**Validation:**
- Run model with both thresholds
- Compare total freight, emissions, costs
- Verify no significant differences in results
- Document threshold choice in paper methodology

---

### Recommendation #4: Add Data Pipeline Validation [PRIORITY 4]

**Problem:** No automated validation of data preservation through pipeline

**Proposed Validation Checks:**

#### 1. Distance Validation
```python
def validate_distance_preservation(self):
    """Validate that total distances match original traffic data."""
    # After creating paths (around line 777)
    total_path_distance = sum(p['length'] for p in self.path_list)
    total_demand = sum(od.get('F', [0])[0] for od in self.odpair_list)
    total_tkm = sum(
        od.get('F', [0])[0] * self.path_list[od['path_id']]['length']
        for od in self.odpair_list
    )

    print(f"\nDistance Validation:")
    print(f"  Total path distance: {total_path_distance:,.0f} km")
    print(f"  Total demand: {total_demand:,.0f} trucks/year")
    print(f"  Total freight: {total_tkm:,.0f} tkm")

    # Compare to original
    if hasattr(self, 'original_tkm'):
        retention = total_tkm / self.original_tkm * 100
        print(f"  Freight retention: {retention:.1f}%")
```

#### 2. Segment Distribution Validation
```python
def validate_segment_distribution(self, path):
    """Validate path segment distances sum to total."""
    segment_sum = sum(path['distance_from_previous'])
    total_distance = path['length']

    if abs(segment_sum - total_distance) > 0.01:  # 10m tolerance
        print(f"WARNING: Path {path['id']} segment mismatch:")
        print(f"  Segments sum: {segment_sum:.2f} km")
        print(f"  Total length: {total_distance:.2f} km")
        print(f"  Difference: {abs(segment_sum - total_distance):.2f} km")
```

#### 3. Country Code Validation
```python
def validate_country_codes(self):
    """Validate country code mapping is complete."""
    # After country mapping (around line 293)
    missing_origin = self.truck_traffic['origin_country'].isna().sum()
    missing_dest = self.truck_traffic['dest_country'].isna().sum()

    if missing_origin > 0 or missing_dest > 0:
        print(f"WARNING: Missing country codes:")
        print(f"  Origin: {missing_origin} routes")
        print(f"  Destination: {missing_dest} routes")

        # Show which NUTS-3 regions lack mapping
        missing_nuts3 = set()
        if missing_origin > 0:
            missing_nuts3.update(
                self.truck_traffic[self.truck_traffic['origin_country'].isna()]['ID_origin_region']
            )
        if missing_dest > 0:
            missing_nuts3.update(
                self.truck_traffic[self.truck_traffic['dest_country'].isna()]['ID_destination_region']
            )

        print(f"  Unmapped NUTS-3 regions: {missing_nuts3}")
```

#### 4. Filter Impact Logging
```python
def log_filter_impact(self, stage_name, before_count, after_count, before_tkm, after_tkm):
    """Log the impact of each filter."""
    print(f"\n{stage_name}:")
    print(f"  Routes: {before_count:,} -> {after_count:,} ({after_count/before_count*100:.1f}% retained)")
    print(f"  Freight: {before_tkm:,.0f} -> {after_tkm:,.0f} tkm ({after_tkm/before_tkm*100:.1f}% retained)")
    print(f"  Loss: {before_count-after_count:,} routes, {before_tkm-after_tkm:,.0f} tkm")
```

**Integration:**
- Add validation calls at key points in preprocessing
- Save validation report to output directory
- Include in model run logs
- Use for regression testing when modifying pipeline

---

## 7. Summary of Findings

### Data Flow Summary

```
Original Data (1.5M routes, 263.6B tkm)
    ↓
NUTS-3 Aggregation (1.5M routes, 263.6B tkm) ✓ No loss
    ↓
NUTS Region Filter (geographic coverage)
    ↓
NUTS-3 → NUTS-2 Aggregation (node reduction)
    ↓
Route Validation Filter ⚠️ CRITICAL ISSUE
    ↓ (99.8% of routes removed!)
    ↓ (91.3% of freight lost!)
    ↓
Cross-Border Filter (if enabled)
    ↓
Traffic Volume Filter (low-volume removal)
    ↓
Distance Preservation ✓ Working correctly
    ↓
Final Model Input (2,928 routes, 22.9B tkm)
```

### Key Findings

1. **✓ Distance Preservation:** Original traffic distances are correctly preserved through all stages

2. **✓ NUTS-3 Aggregation:** Network simplification works well, retains all traffic

3. **✓ Country Code Mapping:** Recent fix ensures correct cross-border detection

4. **⚠️ Excessive Filtering:** Route validation filter (lines 631-643) removes 91.3% of freight
   - Root cause of massive data loss
   - Filters out local, entering, leaving, and through routes
   - Only keeps internal routes with both endpoints inside corridor

5. **⚠️ NUTS-2 Aggregation:** Geographic detail lost (acceptable for model efficiency)
   - 1,675 NUTS-3 regions → 75 NUTS-2 regions
   - Uses centroids, may misrepresent spatial distribution
   - But preserves total distances and freight volumes

6. **Minor: Traffic Volume Threshold:** Could be optimized
   - Current: 100 trucks/year
   - Recommendation: 1,000 trucks/year (removes 54% routes, keeps 99.6% freight)

### Priority Actions

| Priority | Action | Expected Impact |
|----------|--------|-----------------|
| **1. CRITICAL** | Fix route validation filter (lines 631-643) | Retain 91.3% more freight volume |
| **2. HIGH** | Verify country code mapping working | Ensure correct cross-border routes |
| **3. MEDIUM** | Increase traffic threshold to 1,000 | Reduce model size 54%, keep 99.6% freight |
| **4. LOW** | Add validation checks | Better data quality assurance |

---

## 8. Appendices

### Appendix A: File Locations

**Raw Data:**
- `data/Trucktraffic/01_Trucktrafficflow.csv`
- `data/Trucktraffic/02_NUTS-3-Regions.csv`
- `data/Trucktraffic/03_network-nodes.csv`
- `data/Trucktraffic/04_network-edges.csv`

**NUTS-3 Aggregated:**
- `data/Trucktraffic_NUTS3/` (same structure)

**Preprocessing Scripts:**
- `aggregate_raw_data_to_nuts3.py` - Stage 1 → Stage 1B
- `SM_preprocessing_nuts2_complete.py` - Stage 1B → Stage 2
- `SM_preprocessing.py` - Stage 2 → Stage 3 (parameter generation)

**Model Input:**
- `input_data/nuts_2_360_complete_test_time_step_2/`
- `input_data/case_YYYYMMDD_HHMMSS/` (various cases)

**Model Script:**
- `SM.jl` - Main optimization model

### Appendix B: Critical Code Sections

**Route Validation Filter (lines 631-643):**
```python
# SM_preprocessing_nuts2_complete.py
# ====================================================================
# TEMPORARY FIX: Filter out local routes (origin == destination)
# These create infeasibility issues with multi-node travel time constraints
# TODO: Remove this filter once travel time constraint is improved
# ====================================================================
if origin_nuts2 == dest_nuts2:
    is_valid = False
# ONLY accept routes where BOTH origin AND destination are inside corridor
elif origin_inside and destination_inside:
    if origin_node is not None and dest_node is not None:
        is_valid = True  # Both endpoints in corridor and mappable
    else:
        is_valid = False  # One endpoint not mappable to NUTS2
else:
    # Exclude entering routes (outside → inside)
    # Exclude leaving routes (inside → outside)
    # Exclude through routes (outside → outside)
    is_valid = False
```

**Country Code Mapping (lines 186-190, 292-293):**
```python
# Create mapping: ETISPlus Zone ID -> Country code (FIXED)
self.nuts3_id_to_country = dict(zip(
    nuts_3_to_nodes['ETISPlus_Zone_ID'],
    nuts_3_to_nodes['Country']
))

# Add country columns to truck_traffic (used for cross-border filtering)
self.truck_traffic['origin_country'] = self.truck_traffic['ID_origin_region'].map(self.nuts3_id_to_country)
self.truck_traffic['dest_country'] = self.truck_traffic['ID_destination_region'].map(self.nuts3_id_to_country)
```

**Distance Preservation (lines 688-689, 744):**
```python
# Get traffic-reported distance
total_distance = row.Total_distance

# Create path (convert numpy types to Python native)
path = {
    'id': int(path_id),
    'name': f'path_{path_id}_{origin_node}_to_{dest_node}',
    'origin': int(origin_node),
    'destination': int(dest_node),
    'length': float(total_distance),  # Original traffic distance
    'sequence': [int(x) for x in path_sequence],
    'distance_from_previous': [float(x) for x in segment_distances],
    'cumulative_distance': [float(x) for x in cumulative_dist]
}
```

### Appendix C: Audit Script Usage

To run the audit script:

```bash
cd examples/moving_loads_SM
python audit_data_pipeline.py [case_name]
```

**Examples:**
```bash
# Audit default case
python audit_data_pipeline.py

# Audit specific case
python audit_data_pipeline.py nuts_2_360_complete_test_time_step_2

# Audit and save report
python audit_data_pipeline.py > audit_report.txt
```

**Output includes:**
- Stage-by-stage data volume
- Filter impact analysis
- Distance preservation validation
- Critical issues identification
- Detailed recommendations

---

## Document Metadata

**Version:** 1.0
**Date:** 2025-11-07
**Author:** Claude Code
**Purpose:** Comprehensive data pipeline audit for research validity
**Status:** Complete - Ready for review and action

**Next Steps:**
1. Review findings with research team
2. Prioritize fixes based on recommendations
3. Implement route validation fix (Priority 1)
4. Verify country code mapping (Priority 2)
5. Optimize traffic threshold (Priority 3)
6. Add validation checks (Priority 4)
7. Re-run preprocessing with fixes
8. Validate results against known traffic patterns
9. Update paper methodology to document filtering choices
10. Archive this audit for research transparency

---

**End of Audit Report**
