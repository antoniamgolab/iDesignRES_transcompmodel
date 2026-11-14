# Broken Paths Analysis

## Summary

Analysis of `fixed_international_nuts_2` dataset revealed that some paths have only 2 regions (origin + destination) when they should have multiple intermediate NUTS2 regions.

## Classification of 2-Region Paths

| Category | Paths | Demand (2040) | % of Total Demand | Status |
|----------|-------|---------------|-------------------|--------|
| Valid - Land neighbors | 6 | 16,084 t | 0.25% | OK |
| Valid - Sea crossings | 6 | 22,442 t | 0.34% | OK |
| **Truly broken** | **412** | **45,186 t** | **0.69%** | Exclude |

### Valid 2-Region Paths (No Intermediate Regions Expected)

**Land Neighbors:**
- SE33 <-> FI1D: Sweden-Finland border
- NO07 <-> FI1D: Norway-Finland border
- AT33 <-> ITH1: Brenner corridor (Austria-Italy)

**Sea/Ferry Crossings:**
- DK05 <-> SE23: Kattegat strait
- DE80 <-> SE22: Baltic ferry (Rostock-Trelleborg)
- DK05 <-> NO09: Skagerrak ferry
- DK01 <-> SE22: Oresund Bridge
- DE80 <-> DK02: Baltic ferry

### Truly Broken Paths (Missing Intermediate Regions)

These are long-distance routes (1,500-4,300 km) that should have 8-20 intermediate NUTS2 regions but only have origin + destination recorded. They failed E-road matching during preprocessing.

**Examples:**
| Route | Length | Expected Regions | Actual |
|-------|--------|------------------|--------|
| SE33 -> ITF6 | 4,310 km | ~21 | 2 |
| ITF4 -> NO07 | 4,167 km | ~20 | 2 |
| ITC1 -> DK04 | 1,613 km | ~8 | 2 |

**Affected Country Pairs:**
- IT <-> SE: 177 paths
- IT <-> NO: 75 paths
- IT <-> DK: 102 paths
- IT <-> DE: 58 paths

## Impact

- **0.69% of total freight demand** is affected
- These are low-volume, ultra-long-distance routes
- High-volume routes (AT<->IT, DE<->IT core corridors) are properly routed

## Resolution

Broken paths are excluded in preprocessing via the `_filter_broken_paths()` method in `SM_preprocessing.py` (class `SMParameterGenerator`). This filter is **always active** and runs after the cross-border filter in the `load_nuts3_data()` method.

**Exclusion criteria:**
1. Path has exactly 2 regions
2. Regions are NOT a known valid land neighbor (hardcoded list)
3. Regions are NOT a known valid sea/ferry crossing (hardcoded list)

**Implementation location:** `SM_preprocessing.py`, lines ~631-782

## Valid Land Neighbor Pairs (Hardcoded)

```python
VALID_LAND_NEIGHBORS = {
    ('SE33', 'FI1D'), ('FI1D', 'SE33'),  # Sweden-Finland border
    ('NO07', 'FI1D'), ('FI1D', 'NO07'),  # Norway-Finland border
    ('AT33', 'ITH1'), ('ITH1', 'AT33'),  # Brenner corridor (Austria-Italy)
}
```

## Valid Sea Crossing Pairs (Hardcoded)

```python
VALID_SEA_CROSSINGS = {
    ('DE80', 'SE22'), ('SE22', 'DE80'),  # Baltic ferry (Rostock-Trelleborg)
    ('DK05', 'SE23'), ('SE23', 'DK05'),  # Kattegat strait
    ('DK05', 'NO09'), ('NO09', 'DK05'),  # Skagerrak ferry
    ('DK01', 'SE22'), ('SE22', 'DK01'),  # Oresund Bridge
    ('DE80', 'DK02'), ('DK02', 'DE80'),  # Baltic ferry
    ('DK02', 'DK03'), ('DK03', 'DK02'),  # Danish internal
    ('NO08', 'SE23'), ('SE23', 'NO08'),  # Norway-Sweden sea
}
```

---
*Generated: 2025-01*
