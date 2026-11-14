# Long Edge Routes Investigation - Summary

## Your Question
*"May it be that these breaks that are displayed to have so much extra_break_time are due to routes with super long edge length where multiple mandatory breaks are defined for the same node along the edge?"*

## Answer: **NO** - But you were right about the mechanism!

---

## Key Findings

### 1. Long Edges with Multiple Breaks DO Exist ✓

**Confirmed:** Routes with very long edges DO have multiple mandatory breaks at the same node.

**Example - Path 5289:**
- Length: 899.6 km (single edge)
- Nodes: [72, 68] (only 2 nodes)
- **Both breaks assigned to node 68:**
  - Break #1: 360 km cumulative, 5.25h
  - Break #2: 720 km cumulative, 9.75h

**Statistics:**
- Total paths: 1261
- Paths with long edges (>500km avg segment): **15 (1.2%)**
- Paths with multiple breaks at same node: **3**

**Top problematic paths:**
1. Path 5409: 1812 km, **4 breaks at node 72**
2. Path 5289: 899 km, **2 breaks at node 68**
3. Path 5129: 1924 km, **3 breaks at node 69**

### 2. BUT: These Routes Are NOT Causing High extra_break_time ✗

**Surprising Result:** The routes with multiple breaks at same node have **ZERO correlation** with high `extra_break_time`.

**Correlation Analysis:**
- Top 50 routes with highest break time: **0 are problematic long-edge routes**
- Impact: **0.0%** of extra break time comes from long-edge routes

### 3. What's ACTUALLY Causing High extra_break_time?

**Routes with highest extra_break_time:**

| Path | Extra Break Time | Length | Avg Segment | Breaks | Pattern |
|------|-----------------|--------|-------------|--------|---------|
| 2088 | 3234.63h | 1131.8 km | 125.8 km | 3 | NORMAL segments |
| 1993 | 2782.71h | 1095.6 km | 109.6 km | 3 | NORMAL segments |
| 3875 | 2206.01h | 1099.4 km | 109.9 km | 3 | NORMAL segments |

**Common characteristics:**
- Length: ~1000-1200 km (long but not extreme)
- Average segment: **100-140 km** (NORMAL, not long!)
- Mandatory breaks: 3
- All routes ≥360 km with proper break requirements

**Statistical Summary (Top 50 high break time routes):**
- Avg path length: 1159.5 km
- Median path length: 1152.2 km
- **Avg segment length: 127.4 km** ← NORMAL!
- Median num breaks: 3
- Routes < 360km: 0
- Routes > 1000km: 46 (92%)

---

## Technical Analysis

### How Multiple Breaks at Same Node Work

For path 5289 with 2 breaks at node 68:

**Two constraints are created:**
```julia
travel_time[..., geo_id=68, ...] >= 5.25h * num_vehicles  // Break #1
travel_time[..., geo_id=68, ...] >= 9.75h * num_vehicles  // Break #2
```

**Effect:** The second constraint (9.75h) dominates → first becomes redundant.

**Penalty:** Only penalized **once** per node (not double-penalized), because objective function loops through `path.sequence` nodes.

### Why This Isn't a Problem

1. **Constraints are correct**: Having multiple constraints at same node is redundant but not wrong
2. **Not double-penalized**: Penalty applied once per node regardless of break count
3. **Not causing high break times**: These routes don't show up in high break time analysis

---

## Tools Created for You

### 1. `identify_long_edge_routes.py`
Main analysis module with functions:

```python
from identify_long_edge_routes import (
    analyze_problematic_routes,
    create_route_filter,
    print_problematic_routes_summary,
    filter_dataframe_by_routes
)

# Analyze routes
problematic = analyze_problematic_routes(
    input_data,
    avg_segment_threshold=500.0,  # km
    multi_break_threshold=2       # breaks per node
)

# Create filter
filter_func = create_route_filter(problematic, mode='exclude')

# Apply to DataFrame
df_filtered = filter_dataframe_by_routes(df, problematic, 'path_id', 'exclude')
```

### 2. `problematic_routes.yaml` / `problematic_routes_detailed.yaml`
Pre-identified problematic route IDs for quick filtering.

### 3. Usage in `break_times.ipynb`

**Quick filter:**
```python
import yaml

with open('problematic_routes.yaml', 'r') as f:
    problematic_info = yaml.safe_load(f)

problematic_path_ids = set(problematic_info['problematic_paths'])

# Filter function
def is_not_problematic(path_id):
    return path_id not in problematic_path_ids

# Apply when aggregating data
for key, value in extra_break_time_data.items():
    if value > 0:
        year, (prod_id, od_id, path_id, geo_id), tv_id, gen = key

        if is_not_problematic(path_id):
            # ... process data
```

**Full analysis in notebook:**
```python
from identify_long_edge_routes import analyze_problematic_routes, filter_dataframe_by_routes

# Analyze
problematic = analyze_problematic_routes(input_data)

# Filter DataFrame
df_filtered = filter_dataframe_by_routes(df, problematic, 'path_id', 'exclude')
```

### 4. Other Analysis Scripts
- `investigate_long_edges.py`: Edge and break analysis
- `check_specific_path.py`: Detailed path investigation
- `test_filter_impact.py`: Correlation analysis
- `investigate_high_break_routes.py`: High break time analysis

---

## Conclusions

### 1. Your Hypothesis Was Partially Correct ✓
- YES: Long edges DO create multiple breaks at same node
- NO: This is NOT causing high extra_break_time values

### 2. Long-Edge Routes Are Fine ✓
- Only 1.2% of routes affected
- Constraints handle them correctly
- No negative impact on model performance

### 3. High extra_break_time Has Different Cause
The extremely high values (1500-3200h) suggest:
- BEV charging needs (intended use of extra_break_time)
- **OR** model optimization dynamics that need investigation
- **NOT** related to edge length or break distribution

### 4. Filtering May Not Be Necessary
Since long-edge routes aren't causing the issue, filtering them won't reduce high break times.

**However**, the filtering tools are still useful for:
- Exploring model behavior
- Comparing different route types
- Debugging other issues

---

## Recommendations

### For Analysis
1. **Don't filter long-edge routes** - they're not the problem
2. **Investigate why break times are so high** (1500-3200h is unrealistic)
3. **Check if it's BEV-specific** by filtering by technology type
4. **Verify penalty is working** - may need higher multiplier

### For Model Tuning
1. Current penalty: 3.0 × VoT = 90 €/h
2. Consider testing: 5.0-10.0 multiplier
3. Check if high values are from specific:
   - Years (early vs late)
   - Technologies (BEV vs ICEV)
   - Regions (specific OD pairs)

### For Visualization
Use the filtering tools to **compare** different subsets:
- Long-edge vs normal routes
- BEV vs ICEV
- Different time periods
- Different route lengths

---

## Files Generated

| File | Purpose |
|------|---------|
| `identify_long_edge_routes.py` | Main analysis module |
| `problematic_routes.yaml` | Route IDs for quick filtering |
| `problematic_routes_detailed.yaml` | Detailed route information |
| `investigate_long_edges.py` | Edge length analysis |
| `check_specific_path.py` | Path-specific investigation |
| `test_filter_impact.py` | Correlation testing |
| `investigate_high_break_routes.py` | High break time analysis |
| `FILTER_ROUTES_EXAMPLE.md` | Usage examples for notebooks |
| `long_edges_analysis.txt` | Full analysis output |

---

## Next Steps

1. ✓ Confirmed long edges exist but aren't the problem
2. ✓ Created filtering tools for analysis
3. → **Investigate what's causing 1500-3200h break times**
4. → Check if it's technology-specific (BEV charging)
5. → Consider adjusting penalty multiplier if needed
