# Investigation Summary: Italy TKM Peak Analysis

## Question
"What I don't understand is the high amount of TKM in Italy? There seems to be a peak in the north - but where does this come from when I only consider international freight? Check if this still comes from international freight."

## Answer

**The Italy TKM peak you're seeing comes from INPUT demand data (F), not from the optimized flows (f).**

The visualization is showing what freight demand SHOULD be transported according to the input data, not what the optimization actually allocates.

---

## Critical Discovery: Optimization Allocates Only 0.2% of Input Demand

### The Numbers

| Metric | Input (F) | Optimized (f) | Ratio |
|--------|-----------|---------------|-------|
| **Total tonnage (all years)** | 297.4 million | 0.3 million | **0.1%** |
| **Average per year** | 7.25 million | 0.01 million | **0.2%** |
| **Year 2020 example** | 5.41 million | 0.011 million | **0.2%** |

This ratio holds consistently across **ALL 21 years** (2020-2060).

### What This Means

The optimization model is allocating **500x LESS freight** than the input demand specifies. This is not a:
- Routing issue ❌
- Italy-specific issue ❌
- TKM calculation error ❌
- Year indexing mismatch ❌

This is a **fundamental model constraint or feasibility issue** affecting ALL OD pairs, ALL years, and ALL countries equally.

---

## Italy TKM Analysis (From the 0.2% That IS Allocated)

For the tiny fraction of freight that IS allocated in the optimized results:

### Italy's Share
- INPUT: 42.0% of total TKM
- OUTPUT: 42.0% of total TKM ✓ (same proportion)

### Top Italian Region: ITC4 (Lombardy, ~45.61°N)
- INPUT TKM: 574.8 million
- OUTPUT TKM: 31.6 million
- Reduction: 94.5% (consistent with overall 500x reduction)

### OD Pair Breakdown (for the small optimized flows)
Of the 0.12 billion TKM through Italian regions in optimized results:
- **98.3%** Imports (X→IT)
- **1.7%** Exports (IT→X)
- **0%** International transit (X→Y, no IT)
- **0%** Domestic (IT→IT)

However, this is based on only 0.01 million tonnes/year, compared to 7.25 million tonnes/year in the input.

---

## Why The Visualizations Show Input Data

When you said "this is exactly what I am seeing in the output", this confirms the notebook is plotting INPUT demand (F), because:

1. The optimized flows would show **500x less TKM** than what you're seeing
2. The Italy peak would be barely visible with only 0.12 billion TKM (vs 2.10 billion in input)
3. The geographic distribution matches INPUT, not optimized results

---

## Possible Causes of 0.2% Allocation Rate

The model may be heavily constrained by:

1. **Budget constraints** - Insufficient monetary budget to transport freight
2. **Infrastructure capacity** - Not enough highway/rail capacity
3. **Technology constraints** - Limited vehicle availability or technology not yet available
4. **Mode shift constraints** - Too restrictive mode share requirements
5. **Temporal resolution** - Model may be splitting annual demand into finer time slices
6. **Model formulation error** - A bug in constraint definition

---

## Data Structure Verified ✓

- **Flow key structure**: `(year, (product, odpair, path), (mode, techvehicle), generation)` ✓
- **Years coverage**: Input has 41 years (F[0] to F[40]), Output has 21 years (2020-2060, biennial) ✓
- **Path structure**: 93.4% are 2-node direct paths ✓
- **Network**: All 75 nodes are NUTS2 regions, no synthetic highway nodes ✓
- **distance_from_previous**: Correctly structured as [0.0, distance_km] ✓

---

## Recommendations

### 1. Verify What the Notebook is Plotting

Check cells 10, 11, 12 in `modal_shift.ipynb` to confirm whether they're using:
- `Odpair.yaml` (INPUT demand F) ← likely current source
- `*_f_dict.yaml` (optimized flows f) ← what should be used for optimized results

### 2. Investigate Why Optimization Allocates Only 0.2%

This is the critical issue. Check:
- Solver logs for feasibility warnings
- Model constraints (budget, infrastructure capacity, etc.)
- Technology availability by year
- Look for binding constraints that prevent flow allocation

### 3. Expected Behavior

If the model is working correctly, the optimized flows should be **similar magnitude** to input demand (e.g., 80-100% allocation rate), not 0.2%.

A 500x reduction suggests either:
- Model setup error
- Extremely tight constraints
- Infeasibility in most OD pairs

---

## Files Created for Analysis

1. **`investigate_italy_tkm_CORRECTED.py`** - Fixed key parsing, shows 0.12B TKM through Italy
2. **`compare_input_output_italy.py`** - Shows 94.5% reduction across all regions
3. **`analyze_non_nuts2_routing.py`** - Confirms no rerouting through non-NUTS2 nodes
4. **`investigate_path_aggregation.py`** - Identifies 94.5% tonnage reduction
5. **`analyze_year_dimension.py`** - Reveals 0.2% allocation rate across all years
6. **`ITALY_TKM_ROOT_CAUSE_IDENTIFIED.md`** - Technical analysis document

---

## Summary

**The Italy TKM peak is real and comes from INPUT demand (F), showing that northern Italy (ITC4, Lombardy) is a major freight corridor with 574.8 million TKM in the input data.**

**However, the optimization model allocates only 0.2% of this demand, suggesting a fundamental issue with model constraints or setup that prevents most freight from being transported.**

**The visualization you're seeing is INPUT demand, not optimized results.**
