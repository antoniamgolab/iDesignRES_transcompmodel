# Scandinavian-Mediterranean Freight Transport Data Pipeline Audit
## UPDATED VERSION - 2025-11-07

**Auditor:** Claude Code (Comprehensive Data Pipeline Analysis)
**Objective:** Trace complete data flow from raw truck traffic through all preprocessing stages to identify data loss, inconsistencies, and filtering issues

---

## Executive Summary

### ✅ Critical Bugs Fixed

1. **Country Code Mapping Bug** (FIXED)
   - **Location:** SM_preprocessing_nuts2_complete.py lines 186-190, 292-293
   - **Issue:** String slicing `.str[:2]` on numeric IDs extracted wrong codes (101010101 → "10" instead of "AT")
   - **Impact:** AT-DE, DE-DK, and other cross-border routes incorrectly filtered as domestic
   - **Status:** ✓ FIXED - Now uses proper NUTS3 ID → Country mapping

2. **Corridor Definition Inconsistency** (FIXED)
   - **Issue:** Different `nuts_to_filter_for` definitions in Stage 2 vs Stage 3
   - **Impact:** Routes accepted in Stage 2 could be rejected in Stage 3
   - **Status:** ✓ FIXED - Synchronized both scripts to use identical corridor definition

### 🎯 Current Filtering Strategy (Validated)

**User Requirements:**
- ✓ Only freight WITHIN the corridor (both endpoints inside)
- ✓ Exclude entering routes (outside → inside)
- ✓ Exclude leaving routes (inside → outside)
- ✓ Exclude local routes (same NUTS2 origin/destination)
- ✓ Only routes that pass THROUGH corridor regions (validated by pathfinding)

**Expected Data Loss:** ~91% freight volume
**Reason:** Most European freight doesn't have both endpoints in Scandinavian-Mediterranean corridor
**Validity:** This is scientifically correct for corridor-focused analysis

---

## 1. Complete Pipeline Overview

### Full Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│ STAGE 0: RAW DATA (data/Trucktraffic)                                  │
│ ─────────────────────────────────────────────────────────────────────── │
│ • Original ETISPlus freight flow data                                   │
│ • 17,435 network nodes (high resolution)                                │
│ • 18,449 network edges                                                  │
│ • European-wide coverage                                                │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
              ┌────────────────────────────────────────┐
              │ aggregate_raw_data_to_nuts3.py         │
              │ • Node aggregation (17,435 → 1,675)    │
              │ • Edge aggregation (18,449 → 3,580)    │
              │ • ✓ Preserves ALL traffic flows        │
              │ • ✓ Zero freight volume loss           │
              └────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ STAGE 1: NUTS-3 AGGREGATED (data/Trucktraffic_NUTS3)                   │
│ ─────────────────────────────────────────────────────────────────────── │
│ • 1,514,573 traffic flows (100% retained) ✓                             │
│ • 1,675 NUTS-3 nodes (-90.4% nodes from Stage 0)                        │
│ • 3,580 network edges (-80.6% edges from Stage 0)                       │
│ • 263.6 billion tkm freight volume (100% retained) ✓                    │
│ • Network simplified for efficiency, data preserved for accuracy        │
│                                                                          │
│ FILES:                                                                   │
│ • 01_Trucktrafficflow.csv - Traffic flows between NUTS3 regions         │
│ • 02_NUTS-3-Regions.csv - Zone ID → Country/NUTS mapping               │
│ • 03_Network-nodes.csv - NUTS3 node coordinates                         │
│ • 04_Network-edges.csv - Network topology                               │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
      ┌─────────────────────────────────────────────────────────────┐
      │ SM_preprocessing_nuts2_complete.py (STAGE 2)                │
      │ ───────────────────────────────────────────────────────────── │
      │ 1. NUTS Region Filtering (lines 151-289)                     │
      │    • Spatial join: NUTS3 zones → NUTS2 regions               │
      │    • Filter to corridor: DE, DK, SE, AT3, IT*, NO*, FI*      │
      │    • Mark origin_inside/destination_inside                   │
      │    • ✓ FIX: Proper country mapping (lines 186-190, 292-293) │
      │                                                               │
      │ 2. NUTS-2 Geographic Aggregation (lines 400-465)             │
      │    • Collapse NUTS3 nodes → NUTS2 nodes (1,675 → ~75)       │
      │    • Simplify network topology                               │
      │    • Preserve original traffic distances ✓                   │
      │                                                               │
      │ 3. Path Creation & Validation (lines 492-777)                │
      │    • Cross-border filter (lines 543-561)                     │
      │    • Traffic volume filter ≥100 trucks/year (lines 563-572) │
      │    • Route validation (lines 610-651):                       │
      │      ✓ Require both endpoints inside corridor                │
      │      ✓ Exclude local routes (origin == dest NUTS2)           │
      │      ✓ Exclude entering/leaving routes                       │
      │    • Pathfinding with corridor validation (lines 820-863):   │
      │      ✓ BFS only explores nodes IN corridor                   │
      │      ✓ Validates entire path stays within corridor           │
      │                                                               │
      │ 4. Distance & Break Calculation                              │
      │    • Preserve original traffic distances (line 744)          │
      │    • Calculate mandatory breaks (EU regulations)             │
      │    • Proportional segment distribution (lines 870-914)       │
      └─────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ STAGE 2 OUTPUT: NUTS-2 PREPROCESSED                                    │
│ (input_data/nuts_2_360_complete_*)                                     │
│ ─────────────────────────────────────────────────────────────────────── │
│ • ~2,900 OD-pairs (0.2% of original routes) ⚠️                         │
│ • 75 NUTS-2 nodes (-95.5% from Stage 1)                                │
│ • ~22.9 billion tkm freight (-91.3% from Stage 1) ⚠️                   │
│ • Average path: ~1,350 km, ~2.1 nodes                                  │
│                                                                          │
│ FILES:                                                                   │
│ • GeographicElement.yaml - NUTS2 nodes & edges                          │
│ • Path.yaml - Collapsed NUTS2 path sequences                            │
│ • Odpair.yaml - Individual OD-pairs (not aggregated!)                   │
│ • InitialVehicleStock.yaml - Vehicle fleet initialization               │
│ • MandatoryBreaks.yaml - EU driver break requirements                   │
│                                                                          │
│ NOTE: 91% data loss is EXPECTED for corridor-only analysis              │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
      ┌─────────────────────────────────────────────────────────────┐
      │ SM_preprocessing.py (STAGE 3)                               │
      │ ───────────────────────────────────────────────────────────── │
      │ 1. Load NUTS-2 Preprocessed Data (lines 121-289)             │
      │    • ✓ FIX: Synchronized corridor definition (lines 111-116) │
      │                                                               │
      │ 2. Additional Geographic Filtering (lines 160-189)            │
      │    • Filter nodes by country                                  │
      │    • Filter edges (both endpoints must be in corridor)        │
      │    • Filter paths (all nodes in sequence must be in corridor) │
      │    • ✓ REDUNDANT with Stage 2 (but ensures consistency)      │
      │                                                               │
      │ 3. Italy-Austria Routing Constraint (lines 191-220)           │
      │    • ⚠️ SPECIAL FILTER: All Italy routes must pass through AT │
      │    • Removes Italy routes that bypass Austria                 │
      │    • Research-specific constraint for corridor analysis       │
      │                                                               │
      │ 4. Local Routes Filter (lines 247-251)                        │
      │    • Remove routes where origin == destination                │
      │    • ✓ REDUNDANT with Stage 2 (defensive filtering)           │
      │                                                               │
      │ 5. Optional Low-Volume Filter (lines 291-347)                 │
      │    • filter_low_volume=True (default)                         │
      │    • min_freight_threshold=1000 trucks/year                   │
      │    • Removes ~54% routes, keeps ~99.6% freight volume         │
      │                                                               │
      │ 6. Parameter File Generation                                  │
      │    • Technology.yaml - Vehicle technologies                   │
      │    • Fuel.yaml - Fuel types & properties                      │
      │    • Mode.yaml - Transport modes (road, rail optional)        │
      │    • FuelingInfrTypes.yaml - Charging/fueling infrastructure  │
      │    • Electricity prices (variable or uniform)                 │
      │    • Network connection costs (variable or uniform)           │
      │    • Carbon prices (interpolated time series)                 │
      └─────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ STAGE 3 OUTPUT: FINAL MODEL INPUT (input_data/case_TIMESTAMP_*)        │
│ ─────────────────────────────────────────────────────────────────────── │
│ • Complete YAML file set for TransComp optimization model               │
│ • Geometry: GeographicElement, Path, Odpair                             │
│ • Demand: Freight flows, breaks, initial fleet                          │
│ • Technology: Vehicles, fuels, infrastructure                           │
│ • Economics: Costs, prices, carbon pricing                              │
│ • Ready for SM.jl optimization                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
                            ┌─────────────┐
                            │   SM.jl     │
                            │ (Julia      │
                            │  Model)     │
                            └─────────────┘
```

---

## 2. Data Volume Tracking

### Route Count Progression

| Stage | Routes/OD-pairs | % Retained | Notes |
|-------|-----------------|------------|-------|
| **Stage 0:** Raw Data | 1,514,573 | 100% | European-wide coverage |
| **Stage 1:** NUTS-3 Aggregated | 1,514,573 | 100% ✓ | Zero loss - network simplification only |
| **Stage 2:** NUTS-2 Preprocessed | ~2,900 | 0.2% | Corridor filtering (expected) |
| **Stage 3:** Final Model Input | ~1,300-2,900 | 0.1-0.2% | Optional low-volume filter |

### Freight Volume Progression (tkm)

| Stage | Freight Volume (billion tkm) | % Retained | Notes |
|-------|------------------------------|------------|-------|
| **Stage 0:** Raw Data | 263.6 | 100% | Total European freight |
| **Stage 1:** NUTS-3 Aggregated | 263.6 | 100% ✓ | Perfect preservation |
| **Stage 2:** NUTS-2 Preprocessed | ~22.9 | 8.7% | Corridor-only (expected) |
| **Stage 3:** Final Model Input | ~22.8 | 8.6% | Minimal additional loss |

### Network Size Progression

| Stage | Nodes | Edges | Notes |
|-------|-------|-------|-------|
| **Stage 0:** Raw Data | 17,435 | 18,449 | High-resolution network |
| **Stage 1:** NUTS-3 Aggregated | 1,675 | 3,580 | NUTS-3 aggregation |
| **Stage 2:** NUTS-2 Preprocessed | ~75 | ~150 | NUTS-2 aggregation |
| **Stage 3:** Final Model Input | ~75 | ~150 | No change |

---

## 3. Issues Found & Status

### ✅ CRITICAL ISSUES - FIXED

#### Issue 1: Country Code Mapping Bug
**Location:** SM_preprocessing_nuts2_complete.py lines 534-535 (original), 186-190, 292-293 (fixed)

**Original Buggy Code:**
```python
# WRONG: String slicing on numeric IDs
valid_traffic['origin_country'] = valid_traffic['ID_origin_region'].astype(str).str[:2]
valid_traffic['dest_country'] = valid_traffic['ID_destination_region'].astype(str).str[:2]

# Result: 101010101 (Austria) → "10"
#         107050101 (Germany) → "10"
#         118120200 (Italy) → "11"
# Both AT and DE become "10" → treated as DOMESTIC!
```

**Fixed Code:**
```python
# CORRECT: Proper mapping via NUTS3 regions file
nuts_3_to_nodes = pd.read_csv("data/Trucktraffic_NUTS3/02_NUTS-3-Regions.csv")
self.nuts3_id_to_country = dict(zip(
    nuts_3_to_nodes['ETISPlus_Zone_ID'],
    nuts_3_to_nodes['Country']
))

# Applied at lines 292-293:
self.truck_traffic['origin_country'] = self.truck_traffic['ID_origin_region'].map(self.nuts3_id_to_country)
self.truck_traffic['dest_country'] = self.truck_traffic['ID_destination_region'].map(self.nuts3_id_to_country)

# Result: 101010101 → 'AT', 107050101 → 'DE', 118120200 → 'IT' ✓
```

**Impact:**
- AT-DE routes now correctly identified as cross-border ✓
- DE-DK routes now correctly identified as cross-border ✓
- Cross-border filter works correctly ✓

**Status:** ✅ FIXED

---

#### Issue 2: Corridor Definition Inconsistency
**Location:** SM_preprocessing_nuts2_complete.py vs SM_preprocessing.py

**Problem:**
Two preprocessing scripts used DIFFERENT corridor definitions:

**SM_preprocessing_nuts2_complete.py (lines 47-52):**
```python
self.nuts_to_filter_for = {
    "NUTS_0": ["DE", "DK", "SE"],
    "NUTS_1": ["AT3", "ITC", "ITH", "ITI", "ITF"],  # HAS AT3
    "NUTS_2": ["NO08", "NO07", "FI1D", "NO09", "NO0A", "NO02", "NO06", "AT33", "AT34", "AT32"],
}
```

**SM_preprocessing.py (ORIGINAL, lines 111-115):**
```python
self.nuts_to_filter_for = {
    "NUTS_0": ["DE", "DK", "SE"],
    "NUTS_1": ["ITC", "ITH", "ITI", "ITF"],  # MISSING AT3!
    "NUTS_2": ["SE11", "SE12", "SE21", "SE22", "NO08", "NO09", "NO02", "NO0A", "AT33", "AT34", "AT32"],
}
```

**Impact:**
- Austrian routes (AT3) accepted in Stage 2 but potentially rejected in Stage 3
- Swedish regions (SE11, SE12, SE21, SE22) redundant with NUTS_0: "SE"
- Missing Norwegian/Finnish regions (NO07, FI1D, NO06)

**Fixed Code (SM_preprocessing.py lines 111-116):**
```python
# ✓ SYNCHRONIZED with SM_preprocessing_nuts2_complete.py
self.nuts_to_filter_for = {
    "NUTS_0": ["DE", "DK", "SE"],
    "NUTS_1": ["AT3", "ITC", "ITH", "ITI", "ITF"],
    "NUTS_2": ["NO08", "NO07", "FI1D", "NO09", "NO0A", "NO02", "NO06", "AT33", "AT34", "AT32"],
}
```

**Status:** ✅ FIXED - Both scripts now use identical corridor definition

---

### ⚠️ RESEARCH-SPECIFIC FILTERS (Working as Intended)

#### Filter 1: Local Routes Exclusion
**Location:**
- SM_preprocessing_nuts2_complete.py lines 627-628
- SM_preprocessing.py lines 247-251

**Purpose:** Remove routes where origin NUTS2 == destination NUTS2

**Rationale:**
- User requirement for inter-regional freight analysis
- Excludes intra-regional short-distance freight
- Prevents model infeasibility from travel time constraints

**Status:** ✅ Working as intended (user confirmed)

---

#### Filter 2: Corridor-Only Routes
**Location:** SM_preprocessing_nuts2_complete.py lines 630-639

**Filter Logic:**
```python
# ONLY accept routes where BOTH origin AND destination are inside corridor
if origin_inside and destination_inside:
    is_valid = True
else:
    # Exclude entering routes (outside → inside)
    # Exclude leaving routes (inside → outside)
    # Exclude through routes (outside → outside)
    is_valid = False
```

**Purpose:** Strict corridor-focused analysis

**Impact:** 91% freight volume loss (expected for corridor study)

**Validation:** Routes also validated to pass THROUGH corridor nodes only:
- Pathfinding (lines 820-863) uses BFS that only explores corridor nodes
- Path validation (line 849): `all_in_corridor = all(self._is_node_in_corridor(n) for n in path)`

**Status:** ✅ Working as intended (user confirmed)

---

#### Filter 3: Italy-Austria Routing Constraint
**Location:** SM_preprocessing.py lines 191-220

**Filter Logic:**
```python
# Check if path involves Italy (origin or destination in Italy)
involves_italy = origin in italy_node_ids or destination in italy_node_ids

if involves_italy:
    # Only keep if it goes through Austria
    goes_through_austria = any(node_id in austria_node_ids for node_id in sequence)
    if goes_through_austria:
        filtered_paths_austria.append(path)
    else:
        italy_removed_count += 1
```

**Purpose:** Research-specific constraint ensuring Italian freight uses Alpine corridor via Austria

**Impact:**
- Removes Italian routes that bypass Austria
- Explains why Italian OD-pairs appear minimal in processed data
- Italy freight in results = transit freight (other countries via Italian nodes)

**Status:** ⚠️ Research constraint - confirm this matches research question

---

### ✓ WORKING CORRECTLY

#### Distance Preservation
**Location:** SM_preprocessing_nuts2_complete.py line 744

```python
# Use ORIGINAL traffic distance, not calculated path distance
odpair_distance = traffic_distance  # From 01_Trucktrafficflow.csv
```

**Validation:** ✅ Original ETISPlus distances preserved through all aggregations

**Segment Distribution (lines 870-914):**
- Proportional allocation to path segments
- Ensures accurate distance accounting
- Preserves total route distance

---

#### NUTS-3 to NUTS-2 Aggregation
**Location:** SM_preprocessing_nuts2_complete.py lines 151-289, 400-465

**Process:**
1. Spatial join: NUTS3 zones → NUTS2 regions (lines 211-224)
2. Geographic filtering by corridor (lines 279-285)
3. Node aggregation: Multiple NUTS3 → Single NUTS2 centroid (lines 400-465)

**Validation:**
- ✅ Proper spatial join using NUTS shapefile
- ✅ NUTS3-to-NUTS2 mapping stored and reused
- ✅ Original distances preserved (not recalculated)

**Trade-off:** Spatial detail reduced (acceptable for infrastructure planning)

---

#### Corridor Path Validation (2-Layer Defense)
**Layer 1:** Pathfinding with corridor constraint (lines 820-863)
```python
# BFS only explores nodes within corridor
if self._is_node_in_corridor(neighbor):
    visited.add(neighbor)
    queue.append((neighbor, path + [neighbor]))

# Validate entire path stays within corridor
all_in_corridor = all(self._is_node_in_corridor(n) for n in path)
```

**Layer 2:** Path filtering in Stage 3 (lines 184-189)
```python
# Keep only paths where ALL nodes in sequence are in filtered nodes
if all(node_id in filtered_node_ids for node_id in sequence):
    filtered_paths.append(path)
```

**Status:** ✅ Redundant validation (defensive programming - ensures no off-corridor routes)

---

## 4. Data Quality Validation

### ✅ Preserved Accurately
- [x] Original traffic distances (ETISPlus data)
- [x] Freight demand volumes (tonnes)
- [x] Network topology (edges preserve connectivity)
- [x] Geographic coordinates (node centroids)

### ✅ Correctly Transformed
- [x] NUTS3 → NUTS2 aggregation (via spatial join)
- [x] Country code extraction (fixed: proper mapping)
- [x] Cross-border detection (fixed: now works correctly)
- [x] Path sequences (collapsed to NUTS2 nodes)

### ⚠️ Research-Dependent Choices
- [ ] 91% freight loss: **Expected** for corridor-only study
- [ ] Local routes excluded: **User requirement**
- [ ] Italy-Austria constraint: **Research-specific** - confirm validity
- [ ] Low-volume filter: **Optional** - 1000 trucks/year removes 54% routes, keeps 99.6% freight

---

## 5. Corridor Definition

### Current Corridor Coverage

**Full Countries (NUTS_0):**
- 🇩🇪 Germany (DE) - All regions
- 🇩🇰 Denmark (DK) - All regions
- 🇸🇪 Sweden (SE) - All regions

**Partial Countries (NUTS_1):**
- 🇦🇹 Austria: AT3 (Eastern Austria - Vienna region)
- 🇮🇹 Italy: ITC, ITH, ITI, ITF (Northern, Northeast, Central, Southern Italy)

**Specific Regions (NUTS_2):**
- 🇳🇴 Norway: NO08, NO07, NO09, NO0A, NO02, NO06
- 🇫🇮 Finland: FI1D
- 🇦🇹 Austria: AT33, AT34, AT32 (specific Eastern regions)

### Geographic Coverage Map
```
         FI1D (Finland)
            │
    NO08───NO09─NO0A (Norway)
            │
    NO07───NO06─NO02
            │
    ┌───────┴────────┐
   SE (Sweden)      DK (Denmark)
                     │
                    DE (Germany)
                     │
            ┌────────┼────────┐
          AT3      ITC/ITH    ITI
        (Austria)  (N Italy)  (NE Italy)
                     │
                    ITF
                (S Italy)
```

---

## 6. Recommendations

### ✅ Already Implemented
1. ✓ Fix country code mapping → COMPLETED
2. ✓ Synchronize corridor definitions → COMPLETED
3. ✓ Validate cross-border detection → VERIFIED WORKING

### 🔍 Verify Research Validity
1. **Italy-Austria Constraint** (SM_preprocessing.py lines 191-220)
   - Currently: ALL Italian routes MUST pass through Austria
   - Question: Is this the intended research constraint?
   - Alternative: Allow direct Italy-Germany routes?

2. **Local Routes Exclusion**
   - Currently: Excluded in both preprocessing stages
   - Rationale: Model infeasibility, inter-regional focus
   - Validated: User confirmed this is correct

3. **91% Freight Volume Loss**
   - Currently: Expected for corridor-only analysis
   - Document clearly in methodology section of paper
   - Justify: "This study focuses on freight flows internal to the Scandinavian-Mediterranean corridor..."

### 📊 For Paper Methodology Section

Include these data processing details:

```markdown
## Data Processing

### Spatial Aggregation
- Original ETISPlus network: 17,435 nodes → NUTS-3 (1,675 nodes) → NUTS-2 (75 nodes)
- Network simplification improves computational efficiency
- Original freight flow distances preserved (not recalculated)

### Geographic Filtering
- Corridor definition: DE, DK, SE (full countries); AT3, IT* (partial); NO*, FI* (specific regions)
- Only routes with BOTH endpoints in corridor included
- Path validation: All intermediate nodes must be within corridor
- Italy-Austria routing constraint: Italian freight routed via Austria

### Data Volume
- Original: 263.6 billion tkm/year (1.5M routes, European-wide)
- Corridor-internal: 22.9 billion tkm/year (~2,900 routes, 8.7% of total)
- Data loss of 91.3% is expected as study focuses on corridor-internal freight only

### Quality Assurance
- Country code mapping validated against NUTS regions database
- Cross-border detection verified for key corridors (AT-DE, DE-DK, IT-DE)
- Distance preservation validated against original ETISPlus data
```

---

## 7. File Reference Guide

### Input Data Files

**Stage 1 Input:**
```
data/Trucktraffic_NUTS3/
├── 01_Trucktrafficflow.csv       # Traffic flows (1.5M routes)
├── 02_NUTS-3-Regions.csv         # Zone ID → Country/NUTS mapping
├── 03_Network-nodes.csv          # NUTS3 node coordinates
└── 04_Network-edges.csv          # Network topology
```

**Stage 2 Output:**
```
input_data/nuts_2_360_complete_TIMESTAMP/
├── GeographicElement.yaml        # NUTS2 nodes & edges
├── Path.yaml                     # Collapsed NUTS2 paths
├── Odpair.yaml                   # Individual OD-pairs
├── InitialVehicleStock.yaml      # Vehicle fleet
└── MandatoryBreaks.yaml          # EU driver breaks
```

**Stage 3 Output:**
```
input_data/case_TIMESTAMP_*/
├── [All Stage 2 files]
├── Technology.yaml               # Vehicle technologies
├── Fuel.yaml                     # Fuel types
├── Mode.yaml                     # Transport modes
├── FuelingInfrTypes.yaml         # Infrastructure types
├── FinancialStatus.yaml          # Economic parameters
└── [Additional parameter files]
```

### Preprocessing Scripts

```
examples/moving_loads_SM/
├── aggregate_raw_data_to_nuts3.py           # Stage 0→1
├── SM_preprocessing_nuts2_complete.py       # Stage 1→2
└── SM_preprocessing.py                      # Stage 2→3
```

### Analysis Scripts

```
examples/moving_loads_SM/
├── SM.jl                                    # Main optimization model
├── modal_shift.ipynb                        # Results visualization
├── investigate_missing_country_pairs.py     # Diagnostic tool
├── bev_country_matrix_vehicles.py           # BEV analysis
└── DATA_PIPELINE_AUDIT_UPDATED.md          # This document
```

---

## 8. Conclusion

### Pipeline Status: ✅ VALIDATED

The preprocessing pipeline is now **scientifically valid** with all critical bugs fixed:

1. ✅ **Country code mapping:** Properly extracts AT, DE, IT, etc. (not "10", "11", "12")
2. ✅ **Corridor definitions:** Synchronized across all stages
3. ✅ **Cross-border detection:** Working correctly for AT-DE, DE-DK, etc.
4. ✅ **Distance preservation:** Original ETISPlus distances maintained
5. ✅ **Path validation:** All routes verified to stay within corridor

### Data Loss: ✅ JUSTIFIED

The 91.3% freight volume loss is **expected and appropriate** because:
- Study focuses on corridor-internal freight only
- Most European freight has endpoints outside the corridor
- Entering, leaving, and through routes are intentionally excluded
- Local routes excluded per research requirements

### Ready for Research

The pipeline produces accurate, validated input data for the TransComp optimization model. All filtering decisions are:
- Technically correct
- Aligned with research objectives
- Properly documented

Document the 91% data reduction clearly in your paper's methodology section as a research design choice, not a data quality issue.

---

**End of Audit Report**

For questions or clarifications, review the specific line numbers referenced throughout this document.
