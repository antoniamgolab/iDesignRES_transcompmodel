# NUTS-3 Spatial Aggregation for TransComp Model

## Overview

The `aggregate_to_nuts3.py` script reduces the spatial resolution of TransComp model input data from individual nodes to NUTS-3 regional level. This dramatically reduces model size and complexity, enabling processing of larger datasets.

## Key Benefits

- **Model Size Reduction**: ~89% reduction in geographic nodes (4621 → 501 in test case)
- **Path Simplification**: ~79% reduction in path nodes (186 avg → 39 avg nodes per path)
- **Infrastructure Consolidation**: Aggregates fueling and mode infrastructure by region
- **Preserved Structure**: Maintains network topology and demand patterns

## Quick Start

### Basic Usage

```python
from aggregate_to_nuts3 import aggregate_case_to_nuts3

# Aggregate a case to NUTS-3 resolution
aggregate_case_to_nuts3(
    input_case_dir="input_data/case_1_20251014_101827",
    output_case_dir="input_data/case_1_20251014_101827_nuts3"
)
```

### Command Line

```bash
cd examples/moving_loads_SM
python aggregate_to_nuts3.py input_data/case_original input_data/case_nuts3
```

## What Gets Aggregated

### 1. Geographic Elements (Nodes)
- **Original**: Individual network nodes (e.g., highway intersections)
- **Aggregated**: One representative node per NUTS-3 region
- **Method**: Centroid of coordinates, preserves regional attributes
- **Result**: Massive reduction in spatial detail while maintaining regional structure

### 2. Paths (Routes)
- **Challenge**: Most complex aggregation task
- **Method**:
  - Collapse consecutive nodes in same NUTS-3 region
  - Keep only inter-regional transitions
  - Aggregate distances within regions
  - Recalculate cumulative distances
- **Example**:
  - Original: `[A1, A2, A3, B1, B2, C1, C2, C3]` (8 nodes)
  - Aggregated: `[A, B, C]` (3 nodes, where A, B, C are NUTS-3 regions)

### 3. OD-Pairs (Origin-Destination Demand)
- **Method**: Group by (origin_nuts3, dest_nuts3, product, purpose)
- **Aggregation**:
  - Sum demand (F values) across all years
  - Concatenate vehicle stock
  - Maintain trip characteristics
- **Benefit**: Consolidates multiple local trips into regional flows

### 4. Infrastructure
- **Fueling Infrastructure**: Sum capacity (kW) by NUTS-3 and fuel type
- **Mode Infrastructure**: Sum capacity by NUTS-3 and transport mode
- **Result**: Regional infrastructure profiles

### 5. Spatial Flexibility Edges
- **Method**: Keep only inter-regional connections
- **Result**: Regional connectivity network

### 6. Pass-Through Data
These files are copied without modification:
- Technology definitions
- Fuel specifications
- Vehicle types
- Cost parameters
- Policy constraints
- Model configuration

## Aggregation Strategy Details

### Node Aggregation Algorithm

```
For each NUTS-3 region:
  1. Identify all nodes within region
  2. Calculate geographic centroid (lat/lon)
  3. Create single representative node
  4. Map all original nodes → NUTS-3 node
```

### Path Simplification Algorithm

```
For each path:
  1. Map each node → its NUTS-3 region
  2. Identify consecutive same-region segments
  3. For each segment:
     - Sum distances within region
     - Keep only region entry/exit points
  4. Rebuild path with inter-regional structure
  5. Recalculate cumulative distances
```

### Demand Aggregation Algorithm

```
For each unique (origin_nuts3, dest_nuts3, product, purpose):
  1. Find all OD-pairs matching this combination
  2. Sum demand (F) across all years
  3. Aggregate vehicle stock
  4. Create single aggregated OD-pair
```

## Output Structure

The aggregated case directory contains all original files, with spatial data reduced to NUTS-3 resolution:

```
case_1_20251014_101827_nuts3/
├── GeographicElement.yaml      # NUTS-3 nodes (501 regions)
├── Path.yaml                   # Simplified inter-regional paths
├── Odpair.yaml                 # Aggregated regional demand
├── InitialFuelInfr.yaml        # Regional fueling infrastructure
├── InitialModeInfr.yaml        # Regional mode infrastructure
├── Technology.yaml             # (unchanged)
├── Fuel.yaml                   # (unchanged)
└── ... (other config files)    # (unchanged)
```

## Validation & Quality Checks

The aggregation preserves:
- ✓ Total demand (sum of F values)
- ✓ Total infrastructure capacity
- ✓ Network connectivity (inter-regional)
- ✓ Path distances (within tolerance)
- ✓ Regional attributes (NUTS-3 IDs, countries)

## Performance Comparison

| Metric | Original | NUTS-3 | Reduction |
|--------|----------|--------|-----------|
| Nodes | 4,621 | 501 | 89.2% |
| Path nodes (avg) | 186 | 39 | 79.0% |
| Fuel infr entries | 9,242 | 1,002 | 89.2% |
| Mode infr entries | 4,621 | 501 | 89.2% |
| OD-pairs | 10 | 9 | 10.0% |

**Expected Model Performance**:
- Variable count: ~80-90% reduction
- Constraint count: ~70-80% reduction
- Solution time: Significant improvement (depends on case)

## Use Cases

### When to Use NUTS-3 Aggregation

✓ **Good for**:
- Large-scale scenarios (many regions/years)
- Policy analysis at regional level
- Long-term infrastructure planning
- Initial model exploration
- Cases where memory is constrained

✗ **Not recommended for**:
- Local infrastructure siting decisions
- Detailed route optimization
- City-level analysis
- Cases requiring precise node locations

## Integration with SM.jl

To use aggregated data in your optimization runs:

```julia
# In SM.jl, change the folder variable
folder = "case_1_20251014_101827_nuts3"  # Use NUTS-3 aggregated case
input_path = joinpath(@__DIR__, "input_data\\", folder)
```

## Technical Notes

### NUTS-3 Region Handling
- Nodes without NUTS-3 assignment are excluded
- Integer NUTS-3 codes are preserved
- Regional attributes (country, carbon price) maintained

### Distance Calculations
- Intra-regional distances are aggregated
- Inter-regional distances based on region centroids
- Cumulative distances recalculated for path consistency

### Infrastructure Mapping
- Multiple charging stations → aggregated regional capacity
- Preserves fuel type and charging type distinctions
- Income class segmentation maintained if present

## Troubleshooting

### Issue: "0 inter-regional edges" in output
- **Cause**: SpatialFlexibilityEdges contains only intra-regional connections
- **Impact**: None if spatial flexibility constraint not used in model
- **Solution**: Ensure input paths cross regional boundaries

### Issue: Path collapsed to < 2 nodes
- **Cause**: Path entirely within one NUTS-3 region
- **Solution**: These paths are automatically skipped (intra-regional trips)

### Issue: Different results between original and aggregated
- **Expected**: Some differences due to spatial simplification
- **Check**: Validate total demand and infrastructure capacity match

## Example Workflow

```python
# Step 1: Generate high-resolution case data
# (using your existing preprocessing pipeline)

# Step 2: Aggregate to NUTS-3
from aggregate_to_nuts3 import aggregate_case_to_nuts3

aggregator = aggregate_case_to_nuts3(
    "input_data/case_1_20251014_101827",
    "input_data/case_1_20251014_101827_nuts3"
)

# Step 3: Run optimization with aggregated case
# In SM.jl:
# folder = "case_1_20251014_101827_nuts3"

# Step 4: Compare results
# - Check solution quality
# - Verify regional trends
# - Validate infrastructure deployment patterns
```

## Future Enhancements

Potential improvements:
- [ ] NUTS-2 or NUTS-1 aggregation options
- [ ] Distance matrix preservation for accurate routing
- [ ] Demand disaggregation for results analysis
- [ ] Automated validation report generation
- [ ] Support for custom regional definitions

## References

- NUTS Classification: https://ec.europa.eu/eurostat/web/nuts
- TransComp Documentation: https://antoniamgolab.github.io/iDesignRES_transcompmodel/
- Geographic aggregation methods: See `aggregate_to_nuts3.py` for implementation details

## Contact

For questions or issues with NUTS-3 aggregation, please check:
1. This README
2. Code documentation in `aggregate_to_nuts3.py`
3. GitHub issues for the TransComp project
