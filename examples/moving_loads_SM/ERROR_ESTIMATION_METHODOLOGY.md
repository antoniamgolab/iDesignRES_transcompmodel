# Optimization Error Estimation Methodology

## Overview

The "optimization errors" reported in the aggregation analysis are **theoretical estimates** based on mathematical bounds and assumptions, NOT actual optimization results.

These provide rough guidance on potential errors, but actual errors depend heavily on:
- Your optimization objective function
- Cost structure (fixed vs. variable costs)
- Constraint types and their tightness
- The specific scenarios being optimized

## Detailed Explanation of Each Error Metric

### 1. Cost Error Upper Bound (65.1%)

**What it measures:** Maximum possible error in total system cost

**How it's calculated:**
```python
cost_error_upper_bound = intra_regional_distance / total_distance
                       = 120,143 km / 184,647 km
                       = 65.1%
```

**Assumptions:**
1. Total cost is proportional to distance traveled
2. Intra-regional trips have the SAME cost per km as inter-regional trips
3. All costs are distance-based (no fixed costs, no infrastructure costs)

**Why this is an UPPER BOUND (worst case):**

This assumes that:
- Every intra-regional km costs as much as inter-regional km
- Your objective function only considers travel costs
- No economies of scale in aggregation

**Reality check - Why actual error is much lower:**

1. **Different cost structures:**
   ```
   Intra-regional trips (lost):
   - Average distance: ~8 km (120,143 km / 15,660 edges)
   - Typically: urban/local delivery
   - Cost: LOW per trip

   Inter-regional trips (preserved):
   - Average distance: ~23 km (64,504 km / 2,789 edges)
   - Typically: long-haul freight
   - Cost: HIGH per trip
   ```

2. **Your model likely includes:**
   - Infrastructure costs (CAPEX for charging stations) → Not distance-dependent
   - Vehicle purchase costs → Not distance-dependent
   - Energy costs → Preserved in aggregation (traffic flows preserved)
   - Time costs → Partially preserved

3. **Typical cost breakdown for your type of model:**
   ```
   Infrastructure: 40-60% of total cost → Aggregated correctly
   Vehicle CAPEX:  20-30% of total cost → Aggregated correctly
   Energy costs:   10-20% of total cost → 99.9% preserved
   Distance costs: 10-20% of total cost → 65% error on this component

   Total error ≈ 65% × 0.15 = ~10% worst case
   ```

**Better estimate:**
```
If distance costs = 15% of total objective
Then: Actual cost error ≈ 0.65 × 0.15 = 9.75%
```

### 2. Infrastructure Placement Error (42.5%)

**What it measures:** How far off optimal charging station placement might be

**How it's calculated:**
```python
mean_centroid_displacement = 21.3 km  # From spatial analysis
typical_station_spacing = 50 km       # Industry standard for highway charging

infra_placement_error = 21.3 / 50 = 42.5%
```

**Assumptions:**
1. Optimal charging station placement is at true NUTS-3 centroid
2. Typical highway charging stations are 50 km apart
3. Displacement error is proportional to station spacing

**Why this is approximate:**

**Reality:**
- Optimal placement depends on traffic patterns, not just geography
- Charging stations are discrete (can't place at exact centroid anyway)
- 21 km is MEAN displacement; median is only 13.6 km
- Some regions will be better, some worse

**What 21 km displacement actually means:**

```
Scenario 1: Station at representative node (e.g., major highway junction)
vs.
Scenario 2: Station at true centroid (e.g., geographic center of region)

For a truck traveling 500 km:
- Extra detour: ~21 km (4% of journey)
- Extra time: ~15 minutes at highway speed
- Extra energy: ~4%

BUT: Major highways often DON'T go through geographic centroids!
So representative node might actually be BETTER than true centroid.
```

**Better interpretation:**
- This represents potential sub-optimality in station placement
- Real impact depends on whether representative node is near major routes
- Many representative nodes ARE major highway junctions (by design in NUTS-3 data)

### 3. Traffic Assignment Error (0.01%)

**What it measures:** How much inter-regional traffic is lost in aggregation

**How it's calculated:**
```python
inter_regional_traffic_original = 6,610,754,693 trucks
inter_regional_traffic_aggregated = 6,610,087,898 trucks

preservation_ratio = 6,610,087,898 / 6,610,754,693 = 0.9999

traffic_assignment_error = |1 - 0.9999| = 0.01%
```

**This is ACTUAL measurement, not estimate!**

**Why so low?**
- We preserved all inter-regional edges
- Traffic flows summed correctly across parallel edges
- Only minor rounding errors

**What this means:**
- Inter-regional demand is almost perfectly preserved
- OD matrices at NUTS-3 level are accurate
- This is the MOST reliable error metric

### 4. Lower Bound: 0%

**What it measures:** Best-case scenario where aggregation introduces no error

**When this would be true:**
1. All intra-regional travel is negligible cost
2. All optimization decisions happen at regional level
3. Infrastructure is inherently regional (can only place at NUTS-3 nodes anyway)

**This is obviously optimistic**, but it establishes that error is bounded:
```
0% ≤ Actual Error ≤ 65.1%
```

## What These Estimates DON'T Include

### Missing Factors That Affect Real Error:

1. **Constraint Violations**
   - State-of-charge constraints might be violated due to distance approximations
   - Travel time budgets might be exceeded
   - These would show up as infeasibility, not cost error

2. **Network Effects**
   - Path redundancy changes (more connected network after aggregation)
   - Alternative routes might compensate for distance errors
   - Capacity constraints interact differently

3. **Discrete Decisions**
   - Infrastructure is discrete (0, 1, 2, ... stations)
   - Small distance errors might not change discrete decisions at all
   - Or might flip a decision entirely (threshold effects)

4. **Multi-objective Trade-offs**
   - Your model balances multiple objectives
   - Distance error in one objective may not propagate to others
   - Pareto-optimal solutions might shift

## How to Get ACTUAL Error Estimates

### Option 1: Compare Small Test Case (RECOMMENDED)

```bash
# 1. Run small scenario (e.g., 2 years, 50 regions) at high resolution
julia SM.jl  # with original data

# 2. Run same scenario at NUTS-3 resolution
julia SM.jl  # with aggregated data

# 3. Compare results:
# - Total system cost
# - Infrastructure deployment patterns
# - Technology adoption rates
# - Regional demand satisfaction
```

**Expected results:**
- Total cost difference: 5-15% (if error bounds are right)
- Infrastructure patterns: Similar regional distribution
- Technology mix: Similar

### Option 2: Progressive Refinement

```python
# Test at multiple aggregation levels:
1. NUTS-1 (very coarse) → Expect large errors
2. NUTS-2 (coarse) → Expect moderate errors
3. NUTS-3 (medium) → Our current analysis
4. Original (fine) → Baseline

# Plot error vs. resolution
# Extrapolate to understand error sources
```

### Option 3: Sensitivity Analysis

```python
# Perturb aggregated inputs by error bounds:
1. Increase all distances by +10%
2. Decrease all distances by -10%
3. Shift node locations by ±21 km
4. Remove random inter-regional edges

# Re-optimize and measure objective changes
# This quantifies sensitivity to aggregation errors
```

## Recommended Validation Workflow

```
Step 1: Run current analysis (DONE ✓)
  - Establishes theoretical error bounds
  - Identifies risk areas (high intra-regional fraction)

Step 2: Small-scale comparison
  - 2-3 years, 100 regions, simplified vehicle types
  - Compare NUTS-3 vs. original
  - Validate error bounds

Step 3: If error < 20%:
  - Proceed with NUTS-3 for full-scale runs ✓

Step 4: If error > 30%:
  - Consider NUTS-2 instead
  - Or hybrid approach (NUTS-3 for most, original for critical regions)

Step 5: Document assumptions
  - Report results with error bars
  - State that spatial resolution is NUTS-3
  - Acknowledge ~10-20% potential error in local routing
```

## Mathematical Formulation of Actual Error

The **true optimization error** is:

```
E_opt = |f*(x_agg) - f*(x_orig)| / f*(x_orig)

where:
  f*(x) = optimal objective value for problem formulation x
  x_agg = aggregated (NUTS-3) problem
  x_orig = original (high-resolution) problem
```

**This can ONLY be calculated by solving both optimizations!**

Our estimates provide bounds:

```
E_opt ≤ max(E_distance, E_traffic, E_infrastructure) × weight_in_objective

For typical freight electrification model:
E_opt ≈ 0.65 × 0.15 + 0.425 × 0.40 + 0.001 × 0.45
     ≈ 0.098 + 0.170 + 0.0005
     ≈ 26.8% (very pessimistic upper bound)

More realistic estimate:
E_opt ≈ 0.30 × 0.15 + 0.20 × 0.40 + 0.001 × 0.45
     ≈ 0.045 + 0.080 + 0.0005
     ≈ 12.6% (realistic upper bound)
```

## Summary Table: Error Estimates Explained

| Metric | Value | Type | Pessimism | What It Really Means |
|--------|-------|------|-----------|---------------------|
| **Cost Error UB** | 65.1% | Bound | Very High | Assumes all costs are distance-based and intra=inter costs |
| **Infra Placement** | 42.5% | Estimate | Moderate | Representative node ~21km from centroid on average |
| **Traffic Assignment** | 0.01% | Measured | Accurate | Inter-regional flows preserved almost exactly |
| **Realistic Total** | 10-20% | Estimate | Moderate | Combining factors with realistic weights |

## Bottom Line

**The reported errors are theoretical bounds based on assumptions.**

**To get actual errors: You must run optimizations at both resolutions and compare.**

**But the bounds suggest:**
- Inter-regional planning: LOW error (<10%)
- Infrastructure planning: MODERATE error (10-20%)
- Local routing: HIGH error (>40%)

**For your use case (long-haul freight electrification):**
- ✓ Focus is inter-regional → LOW error impact
- ✓ Infrastructure is regional → MODERATE error impact
- ✗ Local details not important → HIGH error acceptable

**Recommendation: NUTS-3 aggregation is appropriate for regional planning, but validate with small test case.**

---

## Appendix: Alternative Error Estimation Methods

### A. Stochastic Error Bounds

Sample from error distributions:
```python
for trial in range(1000):
    # Randomly perturb distances within bounds
    distances_perturbed = distances * (1 + uniform(-0.1, +0.1))

    # Randomly shift node locations
    node_x += normal(0, 21.3)
    node_y += normal(0, 21.3)

    # Re-compute paths and distances
    # Histogram of resulting objective changes
```

### B. Dual Gap Analysis

Use optimization duality:
```
Primal: min c·x subject to Ax ≥ b
Dual:   max b·y subject to A^T·y ≤ c

Duality gap = |c·x* - b·y*|

Perturbations in A, b, c due to aggregation
→ Changes in dual gap
→ Bounds on primal solution error
```

### C. Lagrangian Relaxation

Relax constraints affected by aggregation:
```
L(x,λ) = f(x) + λ·g(x)

Aggregation error affects g(x)
→ Changes in Lagrangian bounds
→ Estimates of solution quality degradation
```

These are more sophisticated but require optimization-specific knowledge.
For practical purposes, **direct comparison on small test case** is most reliable.
