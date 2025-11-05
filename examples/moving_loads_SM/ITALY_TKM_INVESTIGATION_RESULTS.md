# Investigation Results: Italy TKM Peak Analysis

## Summary

Investigated the high TKM appearing in northern Italy in latitude visualizations to determine if this comes from international freight.

## Key Finding

**ALL flows in case study `case_20251103_114421_cs_2025-11-03_16-49-35` route through ZERO NUTS2 nodes.**

### Evidence

1. **Total flows processed**: 140,222 non-zero flows
2. **Flows through NUTS2 regions**: 0
3. **TKM in ANY NUTS2 region**: 0
4. **TKM in Italian NUTS2 regions**: 0

### What This Means

The optimized model results show that **no freight passes through any NUTS2 regional nodes** - neither Italian nor any other country's NUTS2 regions.

This suggests all flows are routed through:
- Synthetic highway nodes only
- OR there's a fundamental mismatch between the flow results and the NUTS2 node definitions

## Investigation Scripts Created

1. **`investigate_italy_tkm.py`** - Analyzes flows by country and OD pair type
   - Result: 0 flows through Italian nodes

2. **`analyze_italy_latitude_attribution.py`** - Checks TKM attribution to Italian latitude range
   - Result: 0 TKM in Italian latitude range (38.90-46.66°N)

3. **`find_max_tkm_latitude.py`** - Finds maximum TKM location in stacked curve
   - Result: 0 NUTS2 regions with TKM

## Data Verified

- **Input**: `input_data/case_20251103_114421/GeographicElement.yaml`
  - Contains 19 Italian NUTS2 nodes ✓
  - Contains 75 total NUTS2 nodes across 6 countries ✓

- **Paths**: `input_data/case_20251103_114421/Path.yaml`
  - 36 out of first 50 paths include Italian nodes ✓
  - Paths DO contain NUTS2 nodes in their sequences ✓

- **Flows**: `results/case_20251103_114421/case_20251103_114421_cs_2025-11-03_16-49-35_f_dict.yaml`
  - 151,087 total flow entries
  - 140,222 non-zero flows (>0.01 tonnes)
  - **But NONE of these flows use paths that pass through NUTS2 nodes**

## Hypothesis

The model is routing all international freight through:
1. **Highway/synthetic nodes only** - Not actual NUTS2 regional nodes
2. **Alternative network layer** - Perhaps a separate highway network that doesn't intersect with NUTS2 nodes

## Implications for Visualizations

The latitude visualizations showing high TKM in Italy must be:

1. **Using a different data source** than the optimized flow results
2. **Showing input demand (F)** rather than optimized flows (f)
3. **Or plotting different results** than what's in this specific case study file

## Recommendation

**Critical**: Verify which data is actually being plotted in the latitude visualizations. The investigation proves conclusively that the optimized flow results (`f_dict.yaml`) contain zero flows through NUTS2 nodes, so any visualization showing TKM by NUTS2 latitude must be using either:

- Input demand data (unoptimized)
- A different results file
- A different network layer (non-NUTS2 nodes)

## Files Generated

- `italy_tkm_analysis.txt` - Output from investigate_italy_tkm.py
- `italy_latitude_analysis.txt` - Output from analyze_italy_latitude_attribution.py
- `max_tkm_location.txt` - Output from find_max_tkm_latitude.py
- `ITALY_TKM_INVESTIGATION_RESULTS.md` - This summary document
