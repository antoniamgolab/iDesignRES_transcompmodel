# Variable Temporal Resolution - Preprocessing Implementation Plan

## Overview

This document details the preprocessing changes needed to support variable temporal resolution in the TransComp model. The `time_step` parameter allows the model to operate at different temporal resolutions (annual, biennial, quinquennial, etc.) without changing the underlying cost and demand data structure.

**Key Principle:** Cost and demand arrays remain **annual** (41 elements for Y=41), but initial vehicle stock is only generated for **modeled years** that align with the `time_step`.

---

## Files Requiring Changes

### 1. `SM_preprocessing_nuts2_complete.py` ⚠️ PRIMARY FILE
**Location:** `C:\Github\SM\iDesignRES_transcompmodel\examples\moving_loads_SM\SM_preprocessing_nuts2_complete.py`

**Functions to modify:**
- `_create_vehicle_stock()` (line ~705) - **CRITICAL:** Update loop to use time_step
- No other changes needed (F arrays, cost arrays remain annual)

**Note:** This is where initial vehicle stock is actually generated!

---

### 2. `SM_preprocessing_nuts3_complete.py` (if used)
**Location:** `C:\Github\SM\iDesignRES_transcompmodel\examples\moving_loads_SM\SM_preprocessing_nuts3_complete.py`

**Functions to modify:**
- `_create_vehicle_stock()` (similar to NUTS2) - Update loop to use time_step

---

### 3. Model Parameters (all files)
**Locations:**
- Any file that generates `Model.yaml` component
- Need to add `time_step` parameter to Model dictionary

**Note:** Currently, Model params appear to be generated elsewhere or loaded from config.

---

## Detailed Implementation Steps

### Step 1: Add `time_step` Parameter to Model Dictionary

**Where:** Wherever Model parameters are defined (needs to be identified in your codebase)

**Options:**
1. Add to a config file that gets loaded
2. Add as a parameter when calling preprocessing
3. Add directly in the preprocessing script

**What to add:**
```yaml
Model:
  Y: 41
  y_init: 2020
  pre_y: 10
  time_step: 1  # NEW: Temporal resolution (1=annual, 2=biennial, 5=quinquennial)
  gamma: 0.0001
  discount_rate: 0.05
  # ... other parameters
```

**Implementation notes:**
- Default value: `time_step = 1` (annual, backward compatible)
- For biennial: Set to `2`
- For quinquennial: Set to `5`
- Must be a positive integer
- Should be a divisor of `Y` for cleaner results (not required, but recommended)

**TODO:** Locate where Model.yaml is generated in the preprocessing pipeline and add this parameter.

---

### Step 2: Update Initial Vehicle Stock Generation

**File:** `SM_preprocessing_nuts2_complete.py`
**Function:** `_create_vehicle_stock()`
**Current location:** Line ~705

**Current approach:**
Generates initial vehicle stock for ALL years from `g_init` (2010) to `y_init-1` (2019).

**New approach:**
Only generate initial vehicle stock for years that align with `time_step`.

#### Current Code (Line ~705 in SM_preprocessing_nuts2_complete.py)

```python
def _create_vehicle_stock(
    self,
    traffic_flow: float,
    distance: float,
    start_id: int,
    y_init: int = 2020,
    prey_y: int = 10,
    occ: float = 0.5
) -> List[int]:
    """Create initial vehicle stock for an OD-pair."""
    # Calculate number of vehicles
    nb_vehicles = traffic_flow * (distance / (13.6 * 136750))
    factor = 1 / prey_y

    vehicle_ids = []

    # CURRENT: Creates stock for EVERY year from y_init-prey_y to y_init-1
    for g in range(y_init-prey_y, y_init):  # e.g., range(2010, 2020) = [2010, 2011, ..., 2019]
        stock = nb_vehicles * factor

        # Diesel truck (ICEV) - only create entries with stock
        self.initial_vehicle_stock.append({
            "id": start_id,
            "techvehicle": 0,
            "year_of_purchase": g,
            "stock": float(round(stock, 5))
        })
        vehicle_ids.append(start_id)
        start_id += 1

        # Electric truck (BEV) - DON'T create zero-stock entries
        # start_id still increments to maintain ID spacing
        start_id += 1

    return vehicle_ids
```

#### New Code Implementation

**Option A: Add time_step as parameter**

```python
def _create_vehicle_stock(
    self,
    traffic_flow: float,
    distance: float,
    start_id: int,
    y_init: int = 2020,
    prey_y: int = 10,
    occ: float = 0.5,
    time_step: int = 1  # NEW PARAMETER
) -> List[int]:
    """Create initial vehicle stock for an OD-pair, respecting temporal resolution."""
    # Calculate number of vehicles
    nb_vehicles = traffic_flow * (distance / (13.6 * 136750))

    # Adjust factor: distribute stock evenly across modeled years
    # Number of modeled pre-years
    num_modeled_years = len(range(y_init-prey_y, y_init, time_step))
    factor = 1 / num_modeled_years  # Changed from: 1 / prey_y

    vehicle_ids = []

    # NEW: Create stock only for years aligned with time_step
    for g in range(y_init-prey_y, y_init, time_step):  # e.g., range(2010, 2020, 2) = [2010, 2012, 2014, 2016, 2018]
        stock = nb_vehicles * factor

        # Diesel truck (ICEV)
        self.initial_vehicle_stock.append({
            "id": start_id,
            "techvehicle": 0,
            "year_of_purchase": g,
            "stock": float(round(stock, 5))
        })
        vehicle_ids.append(start_id)
        start_id += 1

        # Electric truck (BEV)
        start_id += 1

    return vehicle_ids
```

**Then update the calls to this method** (lines ~592 and ~880):

**Current:**
```python
vehicle_init_ids = self._create_vehicle_stock(
    traffic_flow, total_distance, init_veh_stock_id
)
```

**New:**
```python
# Get time_step from somewhere (Model params, class attribute, etc.)
time_step = 1  # TODO: Get from Model params

vehicle_init_ids = self._create_vehicle_stock(
    traffic_flow, total_distance, init_veh_stock_id,
    time_step=time_step  # Pass time_step
)
```

**Option B: Get time_step from class/global configuration (RECOMMENDED)**

```python
def _create_vehicle_stock(
    self,
    traffic_flow: float,
    distance: float,
    start_id: int,
    y_init: int = 2020,
    prey_y: int = 10,
    occ: float = 0.5
) -> List[int]:
    """Create initial vehicle stock for an OD-pair, respecting temporal resolution."""
    # Get time_step from configuration
    time_step = getattr(self, 'time_step', 1)  # Read from self.time_step if it exists, default 1

    # Calculate number of vehicles
    nb_vehicles = traffic_flow * (distance / (13.6 * 136750))

    # Get list of modeled years in pre-period
    modeled_years = list(range(y_init-prey_y, y_init, time_step))

    # IMPORTANT: Distribute stock evenly across modeled years (not all years)
    # Example: time_step=1 → 10 years → factor=1/10 (each year gets 10%)
    #          time_step=2 → 5 years → factor=1/5 (each year gets 20%)
    factor = 1 / len(modeled_years)

    vehicle_ids = []

    # Create stock only for modeled years
    for g in modeled_years:
        stock = nb_vehicles * factor

        self.initial_vehicle_stock.append({
            "id": start_id,
            "techvehicle": 0,
            "year_of_purchase": g,
            "stock": float(round(stock, 5))
        })
        vehicle_ids.append(start_id)
        start_id += 1

        start_id += 1  # BEV (skipped, maintains ID spacing)

    return vehicle_ids
```

**Then add time_step as class attribute in __init__:**

```python
def __init__(self, ...):
    # ... existing code ...
    self.time_step = 1  # Default temporal resolution (1=annual, 2=biennial, etc.)
```

**Key changes:**
1. ✅ Loop uses `time_step`: `range(y_init-prey_y, y_init, time_step)`
2. ✅ Factor adjusted: `1 / len(modeled_years)` ensures total stock = 100%
3. ✅ No call-site changes needed (reads from `self.time_step`)

**Recommended:** Option B - cleaner, doesn't require updating all call sites.

---

### Step 3: Update Method Calls

**File:** `SM_preprocessing.py`
**Function:** `main()` or wherever initial stock is generated

**Current usage:**
```python
initial_stock = preprocessor.generate_initial_vehicle_stock(num_generations=51)
```

**New usage (if using Option A):**
```python
model_params = preprocessor.generate_model_params()
time_step = model_params['time_step']
initial_stock = preprocessor.generate_initial_vehicle_stock(
    num_generations=51,
    time_step=time_step
)
```

**New usage (if using Option B):**
```python
# No changes needed - time_step is read internally
initial_stock = preprocessor.generate_initial_vehicle_stock(num_generations=51)
```

---

### Step 4: Verification - What STAYS Annual

The following data structures should **NOT** be changed and remain annual:

#### ✅ Cost Arrays (Remain Annual)
**Location:** `generate_techvehicle_list()`

**No changes needed:**
```python
icev_capital = [105484.0] * 5 + [109159.0] * 5 + [115252.0] * 41
bev_capital = [417255.0 - subsidy] * 5 + [200006.0 - subsidy] * 5 + [145346.0 - subsidy] * 41
icev_spec_cons = [29.86 * L_to_kWh] * 5 + [26.67 * L_to_kWh] * 5 + [23.47 * L_to_kWh] * 41
bev_spec_cons = [1.60] * 5 + [1.41] * 5 + [1.21] * 41
bev_peak_fueling = [350.0] * 15 + [900.0] * 10 + [1000.0] * 26
icev_maint_annual = [[20471.0 + vehicle_tax_ICEV] * 51 for _ in range(51)]
bev_maint_annual = [[14085.0 + vehicle_tax_BEV] * 51 for _ in range(51)]
```

**Rationale:** Julia model will sample these arrays at modeled years only.

#### ✅ Demand Arrays (F) (Remain Annual)
**Location:** `SM_preprocessing_nuts2_complete.py` - OD-pair generation

**No changes needed:**
```python
odpair = {
    'id': int(path_id),
    'path_id': int(path_id),
    'from': int(origin_node),
    'to': int(dest_node),
    'product': 'freight',
    'purpose': 'long-haul',
    'region_type': 'highway',
    'financial_status': 'any',
    'F': [float(traffic_flow)] * 41,  # Stays 41 elements (annual)
    'vehicle_stock_init': vehicle_init_ids,
    'travel_time_budget': 0.0
}
```

**Rationale:** Julia model will access `F[year - y_init + 1]` only for modeled years.

#### ✅ Carbon Price Arrays (Remain Annual)
**Location:** Geographic element generation

**No changes needed:**
```python
geo_element = {
    # ... other fields ...
    'carbon_price': [0.0] * 41  # Stays 41 elements (annual)
}
```

#### ✅ Infrastructure Cost Arrays (Remain Annual)
**Location:** Fueling infrastructure type definitions

**No changes needed:** All infrastructure-related cost arrays stay annual.

---

## Testing Strategy

### Test 1: Annual Resolution (Baseline)
**Configuration:**
```python
'time_step': 1
```

**Expected behavior:**
- Initial stock for years: 2010, 2011, 2012, ..., 2019 (10 entries per technology)
- Total initial stock entries: 20 (10 ICEV + 10 BEV)
- Model runs identically to current implementation

**Validation:**
```python
# After generating initial stock
assert len(initial_stock) == 20, "Should have 20 initial stock entries"
years = [s['year_of_purchase'] for s in initial_stock]
assert years == [2010, 2010, 2011, 2011, ..., 2019, 2019], "All years from 2010-2019"
```

---

### Test 2: Biennial Resolution
**Configuration:**
```python
'time_step': 2
```

**Expected behavior:**
- Initial stock for years: 2010, 2012, 2014, 2016, 2018 (5 entries per technology)
- Total initial stock entries: 10 (5 ICEV + 5 BEV)
- Model optimization runs for years: 2020, 2022, 2024, ..., 2060

**Validation:**
```python
# After generating initial stock
assert len(initial_stock) == 10, "Should have 10 initial stock entries"
years = sorted(set([s['year_of_purchase'] for s in initial_stock]))
assert years == [2010, 2012, 2014, 2016, 2018], "Biennial years only"
```

---

### Test 3: Quinquennial Resolution
**Configuration:**
```python
'time_step': 5
```

**Expected behavior:**
- Initial stock for years: 2010, 2015 (2 entries per technology)
- Total initial stock entries: 4 (2 ICEV + 2 BEV)
- Model optimization runs for years: 2020, 2025, 2030, ..., 2060

**Validation:**
```python
# After generating initial stock
assert len(initial_stock) == 4, "Should have 4 initial stock entries"
years = sorted(set([s['year_of_purchase'] for s in initial_stock]))
assert years == [2010, 2015], "Quinquennial years only"
```

---

## Implementation Checklist

### Phase 1: Core Changes (`SM_preprocessing_nuts2_complete.py`)
- [ ] Add `self.time_step` attribute in `__init__()` method
- [ ] Modify `_create_vehicle_stock()` to use `time_step` in loop (line ~721)
- [ ] Update factor calculation to account for fewer modeled years (line ~717)
- [ ] Add Model parameter `time_step` to output YAML
- [ ] Verify demand arrays (F) remain unchanged

### Phase 2: YAML Output Validation
- [ ] Run preprocessing with `time_step=1`
- [ ] Verify YAML output contains `time_step: 1` in Model section
- [ ] Count initial stock entries (should be 20 for time_step=1, pre_y=10)
- [ ] Verify all cost arrays are length 41 (or 51 for generation-indexed)

### Phase 3: Alternative Resolution Testing
- [ ] Run preprocessing with `time_step=2`
- [ ] Verify YAML output contains `time_step: 2` in Model section
- [ ] Count initial stock entries (should be 10 for time_step=2, pre_y=10)
- [ ] Verify initial stock years: [2010, 2012, 2014, 2016, 2018]

### Phase 4: Integration Testing
- [ ] Load generated YAML in Julia model
- [ ] Verify `time_step` is accessible in `data_structures["Model"]`
- [ ] Verify initial vehicle stock IDs match expectations
- [ ] Confirm no crashes when accessing cost arrays at modeled years

---

## Edge Cases and Considerations

### Edge Case 1: time_step Larger Than pre_y
**Scenario:** `time_step=15`, `pre_y=10`

**Result:** Only one initial stock year (2010) gets generated.
```python
modeled_pre_years = range(2010, 2020, 15)  # Only 2010
```

**Handling:** Valid configuration, but user should be warned. Consider adding a warning:
```python
if time_step >= pre_y:
    print(f"WARNING: time_step ({time_step}) >= pre_y ({pre_y}). "
          f"Only {len(modeled_pre_years)} initial stock year(s) will be generated.")
```

---

### Edge Case 2: time_step Doesn't Divide Y Evenly
**Scenario:** `time_step=7`, `Y=41`, `y_init=2020`

**Result:** Modeled years: 2020, 2027, 2034, 2041, 2048, 2055 (stops at 2055, not 2060)

**Handling:** Valid, but may be unexpected. Last modeled year is `y_init + (Y // time_step) * time_step - time_step`.

For cleaner results, recommend `time_step` values that divide `Y` evenly:
- Y=41: Recommend time_step ∈ {1, 41} (limited options)
- Y=40: Recommend time_step ∈ {1, 2, 4, 5, 8, 10, 20, 40}

---

### Edge Case 3: time_step = 0 or Negative
**Scenario:** Invalid input

**Handling:** Add validation in `generate_model_params()`:
```python
def generate_model_params(self) -> Dict:
    time_step = 1  # Default

    # Validate time_step
    if time_step <= 0:
        raise ValueError(f"time_step must be positive integer, got {time_step}")

    return {
        'Y': 41,
        'y_init': 2020,
        'pre_y': 10,
        'time_step': time_step,
        # ... rest ...
    }
```

---

## Code Snippets for Quick Reference

### Snippet 1: Calculate Modeled Years (Python)
```python
def get_modeled_years(y_init: int, Y: int, time_step: int) -> List[int]:
    """Get list of modeled years based on temporal resolution."""
    Y_end = y_init + Y - 1
    return list(range(y_init, Y_end + 1, time_step))

# Example usage:
modeled_years = get_modeled_years(2020, 41, 2)
# Result: [2020, 2022, 2024, ..., 2060]
```

### Snippet 2: Calculate Modeled Generations (Python)
```python
def get_modeled_generations(y_init: int, pre_y: int, time_step: int) -> List[int]:
    """Get list of modeled generation years for initial stock."""
    g_init = y_init - pre_y
    return list(range(g_init, y_init, time_step))

# Example usage:
modeled_gens = get_modeled_generations(2020, 10, 2)
# Result: [2010, 2012, 2014, 2016, 2018]
```

### Snippet 3: Validate time_step Parameter
```python
def validate_time_step(time_step: int, Y: int, pre_y: int) -> None:
    """Validate time_step parameter and warn about potential issues."""
    if time_step <= 0:
        raise ValueError(f"time_step must be positive, got {time_step}")

    if not isinstance(time_step, int):
        raise TypeError(f"time_step must be integer, got {type(time_step)}")

    if time_step > Y:
        raise ValueError(f"time_step ({time_step}) cannot exceed Y ({Y})")

    # Warning for non-divisible configurations
    if Y % time_step != 0:
        import warnings
        warnings.warn(
            f"time_step ({time_step}) does not divide Y ({Y}) evenly. "
            f"Last modeled year may not be Y_end."
        )

    # Warning for very coarse resolution
    if time_step >= pre_y:
        import warnings
        warnings.warn(
            f"time_step ({time_step}) >= pre_y ({pre_y}). "
            f"Very few initial stock years will be generated."
        )
```

---

## Summary

### What Changes in Preprocessing
1. **Model params:** Add `time_step` parameter (default: 1)
2. **Initial vehicle stock generation:** Only generate for years aligned with `time_step`
3. **Stock distribution factor:** Adjust to distribute evenly across fewer modeled years

### What Stays the Same
1. **Demand arrays (F):** Remain annual (41 elements)
2. **Carbon price arrays:** Remain annual (41 elements)
3. **All other cost/parameter arrays:** Remain annual
4. **OD-pair structure:** No changes
5. **Path structure:** No changes

### Files Modified
- `SM_preprocessing_nuts2_complete.py`: ~10 lines changed (1 method: `_create_vehicle_stock()`)
- `SM_preprocessing_nuts3_complete.py`: ~10 lines changed (same method)
- Model YAML generation: Add `time_step` parameter (location TBD)

### Expected Impact
- **Backward compatible:** `time_step=1` behaves identically to current implementation
- **Reduced model size:** `time_step=2` cuts decision variables roughly in half
- **Faster solve times:** Fewer variables = faster optimization (for large instances)
- **Flexible analysis:** Can run quick coarse analyses (time_step=5) then refine (time_step=1)
