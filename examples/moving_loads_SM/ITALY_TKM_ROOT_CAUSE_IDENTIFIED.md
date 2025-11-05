# ROOT CAUSE IDENTIFIED: Italy TKM Peak Analysis

## Executive Summary

The Italy TKM peak seen in the latitude visualizations comes from **INPUT demand data (F)**, not optimized flows (f). The optimized model allocates only **5.5% of the input tonnage**.

## Key Findings

### 1. Tonnage Comparison

| Metric | Input (F, year 0) | Optimized (f, all) | Ratio |
|--------|-------------------|---------------------|-------|
| **Total Tonnage** | 5.41 million tonnes | 0.30 million tonnes | **5.5%** |
| **Total TKM** | 4.99 billion | 0.28 billion | **5.5%** |

### 2. Italian Regions Specifically

| Metric | Input (F) | Optimized (f) | Ratio |
|--------|-----------|---------------|-------|
| **Italy TKM** | 2.10 billion | 0.12 billion | **5.5%** |
| **Italy % of total** | 42.0% | 42.0% | ✓ Same |

**Important**: Italy retains the SAME 42% share of total TKM in both input and output, but the absolute values drop by 94.5% due to the overall tonnage reduction.

### 3. Top Italian Region (ITC4 - Northern Italy)

- **Location**: 45.61°N (Lombardy region, includes Milan)
- **INPUT TKM**: 574.8 million
- **OUTPUT TKM**: 31.6 million
- **Reduction**: 94.5%

### 4. Where Italian TKM Comes From (Optimized Results)

In the **optimized flows (f)**, the small amount of TKM through Italy is:
- **98.3%** from imports (X→IT)
- **1.7%** from exports (IT→X)
- **0%** from international transit (X→Y)
- **0%** from domestic (IT→IT)

However, this is based on only 0.3 million tonnes total, compared to 5.4 million tonnes in the input.

## Why the Discrepancy?

### Hypothesis 1: Year Index Mismatch (MOST LIKELY)

The input demand F has **multiple years** of data (likely 2020-2060, ~40 years). When I compared:
- **INPUT**: Used F[0] (first year only) = 5.41 million tonnes
- **OUTPUT**: Summed ALL flows across ALL years = 0.30 million tonnes

The optimized flows are indexed by year: `(year, (product, odpair, path), (mode, techvehicle), generation)`

If the optimization starts in year 2020 and each year index represents a different calendar year, then:
- F[0] might be 2020 demand
- But the optimized flows might only cover a subset of years (e.g., 2020-2030)
- OR the comparison is aggregating improperly

### Hypothesis 2: Model Constraints

The optimization might be intentionally reducing demand due to:
- Budget constraints
- Infrastructure capacity constraints
- Technology availability constraints
- Mode shift constraints

### Hypothesis 3: Temporal Resolution Issue

The model might be:
- Dividing annual demand across multiple time periods
- Using a different temporal resolution between F and f
- Aggregating flows differently than input demand

## What This Means for Visualizations

**The user stated**: "but this is exactly what i am seeing in the output"

This confirms that the latitude visualizations showing the Italy peak are plotting **INPUT demand (F)**, not optimized flows (f).

If the visualization code is using the optimized f_dict.yaml file but showing values similar to INPUT, then there's likely an error in:
1. The year indexing/filtering
2. The flow aggregation method
3. OR the notebook is actually plotting F instead of f

## Recommendations

1. **Verify which data source the notebook is actually plotting**: Check if cells 10, 11, 12 in `modal_shift.ipynb` are using `f_dict.yaml` or `Odpair.yaml`

2. **Check year filtering**: If using f_dict, verify which years are being included in the sum

3. **Verify flow aggregation**: Confirm that all (mode, techvehicle, generation) combinations are being summed for each (year, odpair, path)

4. **Check temporal resolution**: Verify if F represents annual demand but f might be subdivided into shorter time periods

5. **Investigate why optimization only allocates 5.5% of demand**: This seems like a fundamental model issue that should be investigated:
   - Are most OD pairs infeasible?
   - Are budget constraints too tight?
   - Is infrastructure capacity insufficient?
   - Are there errors in the model formulation?

## Data Integrity Verification

✓ **Path structure**: 93.4% of paths are 2-node (direct origin-destination)
✓ **All nodes are NUTS2**: No synthetic highway nodes exist
✓ **distance_from_previous**: Structure is correct [0.0, distance_km]
✓ **TKM calculation**: Sum of segment TKM equals flow × total distance
✓ **Italy share**: Remains 42% in both input and output

## Files Created for Analysis

1. `investigate_italy_tkm_CORRECTED.py` - Correctly parses f_dict keys
2. `compare_input_output_italy.py` - Direct comparison of INPUT vs OUTPUT
3. `analyze_non_nuts2_routing.py` - Confirms no non-NUTS2 routing
4. `investigate_path_aggregation.py` - Identifies 94.5% tonnage reduction

## Next Steps

The critical question is: **Why does the optimization only allocate 5.5% of the input demand?**

This requires investigation of:
- Model constraints (budget, infrastructure, mode share, etc.)
- Feasibility of OD pairs
- Technology availability by year
- Solver status and solution quality
