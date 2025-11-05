# Variable Temporal Resolution Implementation - Overview

## Purpose

This document provides an overview of the variable temporal resolution feature for the TransComp model. This feature allows the model to operate at different temporal resolutions (annual, biennial, quinquennial, etc.) to balance computational efficiency with accuracy.

## Motivation

**Current limitation:** The model runs at annual resolution (41 years = 41 time periods), which creates many decision variables and long solve times for large-scale problems.

**Solution:** Introduce a `time_step` parameter that allows the model to optimize at coarser temporal resolutions (e.g., every 2 years, every 5 years) while maintaining annual cost and demand data.

**Benefits:**
- 🚀 **Faster solve times:** 50-95% reduction depending on time_step
- 🔍 **Exploratory analysis:** Quick scenario testing with coarse resolution
- 📊 **Scalable:** Enables larger geographic scope (more NUTS regions)
- ⚙️ **Flexible:** Choose resolution based on analysis needs

## How It Works

### Core Concept

**Before (Annual Resolution):**
- Optimize every year: 2020, 2021, 2022, ..., 2060 (41 years)
- 41 time periods → More variables → Longer solve time

**After (Biennial Resolution, time_step=2):**
- Optimize every 2nd year: 2020, 2022, 2024, ..., 2060 (21 years)
- 21 time periods → Fewer variables → Faster solve time

**After (Quinquennial Resolution, time_step=5):**
- Optimize every 5th year: 2020, 2025, 2030, ..., 2060 (9 years)
- 9 time periods → Much fewer variables → Much faster solve time

### Key Design Principle

**Cost and demand data remain annual** (41 data points), but the model only optimizes at selected years and samples the data arrays.

**Example with time_step=2:**
```python
# Preprocessing: Cost array has 41 annual values
capital_cost = [100, 98, 96, 94, 92, ...]  # 41 values

# Julia model: Only optimize years 2020, 2022, 2024, ...
# Sample cost array at positions 1, 3, 5, ...
for y in [2020, 2022, 2024, ...]:
    cost = capital_cost[y - 2020 + 1]  # Gets values at indices 1, 3, 5, ...
```

**Result:** Fewer decision variables, same data granularity.

---

## Implementation Components

### 1. Preprocessing Changes (Python)

**Files:** `SM_preprocessing.py`, `SM_preprocessing_nuts2_complete.py`

**Changes:**
- Add `time_step` parameter to Model dictionary (default: 1)
- Update initial vehicle stock generation to only create stocks for modeled years
- Cost arrays stay annual (no changes)
- Demand arrays (F) stay annual (no changes)

**See:** `TEMPORAL_RESOLUTION_PREPROCESSING_PLAN.md` for detailed instructions.

---

### 2. Julia Model Changes

**Files:** `src/support_functions.jl`, `src/model_functions.jl`, `src/checks.jl`

**Changes:**
- Create `modeled_years` and `modeled_generations` sets based on time_step
- Replace all `y in y_init:Y_end` with `y in modeled_years`
- Replace all `g in g_init:Y_end` with `g in modeled_generations`
- Update objective function to scale costs by time_step
- Update result saving loops

**See:** `TEMPORAL_RESOLUTION_JULIA_PLAN.md` for detailed instructions.

---

## Quick Start Guide

### For Users: Running with Different Resolutions

**Step 1:** Generate input data with desired time_step

```bash
# Edit SM_preprocessing.py, set time_step in generate_model_params():
# 'time_step': 1  # Annual (default)
# 'time_step': 2  # Biennial
# 'time_step': 5  # Quinquennial

python SM_preprocessing_nuts2_complete.py
```

**Step 2:** Run Julia model as usual

```julia
include("SM.jl")
# Model automatically respects time_step from input YAML
```

**Step 3:** Analyze results

Results will only be available for modeled years (e.g., 2020, 2022, 2024, ... for time_step=2).

---

### For Developers: Implementation Steps

**Phase 1: Preprocessing (Python)**
1. Modify `generate_model_params()` - add time_step parameter
2. Modify `generate_initial_vehicle_stock()` - filter by modeled years
3. Test with time_step=1 (should be identical to current)
4. Test with time_step=2

**Phase 2: Julia Model**
1. Update `parse_data()` - create modeled year sets
2. Update `base_define_variables()` - replace year ranges
3. Update all constraint functions - replace year loops
4. Update objective function - add time_step scaling
5. Update result saving - replace year loops
6. Test with time_step=1 (baseline)
7. Test with time_step=2

**Phase 3: Validation**
1. Compare objective values across different time_steps
2. Verify initial stock alignment
3. Check infrastructure investment timing
4. Document any unexpected behaviors

---

## Configuration Examples

### Example 1: Annual (Current Behavior)
```yaml
Model:
  Y: 41
  y_init: 2020
  pre_y: 10
  time_step: 1  # Annual resolution
```

**Result:**
- Modeled years: 2020, 2021, 2022, ..., 2060 (41 years)
- Initial stock years: 2010, 2011, ..., 2019 (10 years)
- Backward compatible with existing models

---

### Example 2: Biennial (Recommended for Large Models)
```yaml
Model:
  Y: 41
  y_init: 2020
  pre_y: 10
  time_step: 2  # Biennial resolution
```

**Result:**
- Modeled years: 2020, 2022, 2024, ..., 2060 (21 years)
- Initial stock years: 2010, 2012, 2014, 2016, 2018 (5 years)
- ~50% fewer variables, ~50-75% faster solve time

---

### Example 3: Quinquennial (Exploratory Analysis)
```yaml
Model:
  Y: 40  # Changed to 40 to align with time_step=5
  y_init: 2020
  pre_y: 10
  time_step: 5  # Quinquennial resolution
```

**Result:**
- Modeled years: 2020, 2025, 2030, 2035, 2040, 2045, 2050, 2055 (8 years)
- Initial stock years: 2010, 2015 (2 years)
- ~80% fewer variables, ~75-95% faster solve time

---

## Use Case Recommendations

| Use Case | Recommended time_step | Rationale |
|----------|----------------------|-----------|
| Final publication results | 1 (annual) | Maximum accuracy |
| Standard analysis | 1-2 | Good balance of accuracy and speed |
| Large geographic scope (>100 regions) | 2-5 | Computational necessity |
| Exploratory scenario testing | 5 | Quick turnaround for many scenarios |
| Sensitivity analysis | 2-5 | Run many variations quickly |
| Long-term strategic planning | 5 | Coarse resolution sufficient |

---

## Performance Comparison

### Expected Solve Time Reductions

Based on typical MIP scaling behavior:

| time_step | Variables | Constraints | Solve Time | Use Case |
|-----------|-----------|-------------|------------|----------|
| 1 | 100% | 100% | Baseline (e.g., 10 hrs) | Final results |
| 2 | ~50% | ~50% | 25-50% of baseline (2.5-5 hrs) | Standard analysis |
| 5 | ~20% | ~20% | 5-25% of baseline (0.5-2.5 hrs) | Exploratory |

*Note: Actual performance depends on model size, solver settings, and hardware.*

---

## Validation Strategy

### Step 1: Baseline Test (time_step=1)
Run with annual resolution and verify results match current implementation.

**Pass criteria:**
- Objective value within 0.01% of original
- Variable counts match
- Constraint counts match
- All results save successfully

---

### Step 2: Biennial Test (time_step=2)
Run with biennial resolution and verify reasonable approximation.

**Pass criteria:**
- Model solves without errors
- Objective value within 5-10% of baseline (expected due to coarser resolution)
- Initial stock only for years: 2010, 2012, 2014, 2016, 2018
- Results saved correctly for modeled years only

---

### Step 3: Edge Case Testing

**Test 3a:** Large time_step (time_step=10)
- Verify model handles very coarse resolution

**Test 3b:** Non-divisible time_step (time_step=7, Y=41)
- Verify model handles cases where Y is not divisible by time_step

**Test 3c:** Investment period alignment (investment_period=5, time_step=2)
- Verify infrastructure investments occur at correct years

---

## Known Limitations

### Limitation 1: Temporal Accuracy
Coarser temporal resolution may miss:
- Short-term dynamics (e.g., rapid technology adoption)
- Year-to-year fluctuations (e.g., demand spikes)
- Precise timing of policy interventions

**Mitigation:** Use time_step=1 for final analysis requiring high temporal accuracy.

---

### Limitation 2: Initial Stock Granularity
With large time_step, very few initial stock years are modeled.

**Example:** time_step=10, pre_y=10 → Only 1 initial stock year (2010)

**Mitigation:** Ensure pre_y is large enough to capture reasonable vehicle age distribution.

---

### Limitation 3: Infrastructure Investment Timing
Investment years must align with modeled years. With large time_step, investment flexibility is reduced.

**Example:**
- investment_period=5, time_step=7
- Modeled years: [2020, 2027, 2034, 2041]
- Investment years should be: [2020, 2025, 2030, ...]
- But 2025, 2030 not modeled!

**Mitigation:** Choose time_step that divides investment_period evenly, or vice versa.

---

## Future Enhancements

### Possible Extension 1: Adaptive Resolution
Allow different resolutions for different time periods:
- Fine resolution (time_step=1) for near-term: 2020-2030
- Coarse resolution (time_step=5) for long-term: 2035-2060

**Benefits:** Capture near-term dynamics while reducing long-term variables.

---

### Possible Extension 2: Variable-Length Time Steps
Allow non-uniform time steps:
- Years: [2020, 2021, 2022, 2025, 2030, 2035, 2040, 2050, 2060]
- Finer resolution early, coarser later

**Benefits:** Maximum flexibility for different analysis needs.

---

### Possible Extension 3: Time-Aggregated Demands
Currently, demand arrays (F) stay annual and are sampled.

**Alternative:** Aggregate demands over time_step periods.
- Annual F: [100, 102, 104, 106, ...] tkm/year
- Biennial F: [202, 210, ...] tkm/2-year period

**Benefits:** Better representation of total period demand.
**Challenges:** Requires preprocessing changes to aggregate data correctly.

---

## FAQ

### Q1: Does time_step=2 mean the model assumes constant values for 2 years?
**A:** No. The cost and demand *data* remains annual (41 values). The model *optimizes* at 2-year intervals (samples the data). Think of it as "snapshots" every 2 years rather than continuous video.

---

### Q2: Will results for time_step=2 be exactly half as accurate?
**A:** Not necessarily. Accuracy depends on:
- How much variables change year-to-year
- Whether important dynamics occur in "skipped" years
- Model structure and constraints

For smoothly changing systems, time_step=2 can be surprisingly accurate.

---

### Q3: Can I mix time_step with investment_period?
**A:** Yes, but ensure they align well. Recommended:
- investment_period is a multiple of time_step, OR
- time_step is a multiple of investment_period

Example:
- ✅ time_step=2, investment_period=4 (investments every 2 modeled periods)
- ✅ time_step=5, investment_period=5 (investments every modeled period)
- ⚠️ time_step=3, investment_period=5 (investments may not align with modeled years)

---

### Q4: What happens to cost arrays with time_step=2?
**A:** They stay annual (41 elements). The model samples them:
- Year 2020: Uses capital_cost[1]
- Year 2022: Uses capital_cost[3]
- Year 2024: Uses capital_cost[5]

This is more accurate than creating a coarse 21-element array, because we retain the annual data granularity.

---

### Q5: Should I always use time_step>1 for faster results?
**A:** No. Use time_step based on your needs:
- **Final publication:** time_step=1 (maximum accuracy)
- **Standard analysis:** time_step=1 or 2 (good compromise)
- **Exploratory runs:** time_step=5 (speed priority)
- **Very large models:** time_step=2-5 (computational necessity)

---

## Related Documentation

- **Preprocessing Plan:** `TEMPORAL_RESOLUTION_PREPROCESSING_PLAN.md`
- **Julia Implementation Plan:** `TEMPORAL_RESOLUTION_JULIA_PLAN.md`
- **TransComp Documentation:** https://antoniamgolab.github.io/iDesignRES_transcompmodel/

---

## Contact and Support

For questions or issues related to temporal resolution implementation:
1. Check the detailed plans (preprocessing and Julia)
2. Review edge cases and limitations sections
3. Contact the development team

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-01-XX | Initial design documents created |
| TBD | TBD | Implementation completed |
| TBD | TBD | Validation and testing completed |
