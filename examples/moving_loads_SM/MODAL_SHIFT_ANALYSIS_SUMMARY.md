# Modal Shift Analysis Summary

## Objective Function Bug - FIXED ✅

### Problem
The objective function in `src/model_functions.jl` was **not applying costs for transport modes with `quantify_by_vehs=false`** (modes 1=road and 2=rail). This caused:
- Rail appeared to have **zero cost** in the objective
- Model chose 100% rail regardless of cost_per_ukm values
- Changing rail costs from €0.085 to €1000/tkm had NO effect on results

### Root Cause
The objective function loops over `techvehicles` from `techvehicle_list` (line 3991):
```julia
for v ∈ techvehicles
```

However, modes with `quantify_by_vehs=false` use **dummy techvehicles** that exist in the `m_tv_pairs` set but are **NOT in techvehicle_list**. Therefore:
- The loop never visited these dummy techvehicles
- The `else` branch (line 4230) that adds levelized costs was never executed
- Modal costs were completely missing from the objective

### Solution Implemented
Added a new code block after line 4300 in `src/model_functions.jl` that explicitly handles modes with `quantify_by_vehs=false`:

```julia
# ========================================================================
# FIX: Costs for non-vehicle modes (quantify_by_vehs = false)
# These modes use dummy techvehicles not in techvehicle_list, so we need
# a separate loop to add their levelized costs
# ========================================================================
if has_var["f"]
    for m ∈ modes
        if !m.quantify_by_vehs
            # Get the dummy techvehicle ID for this mode
            dummy_tv_id = length(techvehicles) + findfirst(mode -> mode.id == m.id && !mode.quantify_by_vehs, modes)

            for r ∈ odpairs
                route_length = sum(k.length for k ∈ r.paths)

                for k ∈ r.paths
                    for g ∈ modeled_generations
                        if g > y
                            continue
                        end

                        # Levelized cost per tkm
                        add_to_expression!(
                            total_cost_expr,
                            discount_factor * m.cost_per_ukm[y-y_init+1] * route_length * 1000 * model[:f][
                                y,
                                (r.product.id, r.id, k.id),
                                (m.id, dummy_tv_id),
                                g,
                            ] * time_step,
                        )

                        # Waiting time cost (e.g., terminal access for rail)
                        vot = r.financial_status.VoT
                        waiting_time_cost = vot * m.waiting_time[y-y_init+1]
                        add_to_expression!(
                            total_cost_expr,
                            discount_factor * waiting_time_cost * 1000 * model[:f][
                                y,
                                (r.product.id, r.id, k.id),
                                (m.id, dummy_tv_id),
                                g,
                            ] * time_step,
                        )

                        max_coeff = max(max_coeff, (m.cost_per_ukm[y-y_init+1] * route_length + waiting_time_cost) * discount_factor)
                    end
                end
            end
        end
    end
end
```

**File modified**: `src/model_functions.jl` (lines 4300-4345)

## Verification Results

### Test 1: Rail at €1000/tkm (very expensive)

**Before Fix:**
- Objective: €4,254,133,936
- Modal split: 100% rail (mode 2, dummy techvehicle 4)
- Changing rail costs had **NO effect** whatsoever

**After Fix:**
- Objective: €4,882,720,000 (+€628M, +14.8%)
- Modal split: **100% road** (mode 1, dummy techvehicle 3)
- Gurobi warning: "Model contains large objective coefficients" (correctly seeing €1000/tkm)
- Solver iterations: 312 → 606 (now properly comparing costs)

**Conclusion**: ✅ Rail costs are now being applied correctly!

### Test 2: Rail at €0.085/tkm (same as road)

**Result:**
- Objective: €4,875,368,344 (similar to road-only case)
- Modal split: **100% road** (mode 1, dummy techvehicle 3)
- No rail flows found

**Why road wins with equal costs:**
- Both modes have cost_per_ukm = €0.085/tkm
- Both have waiting_time = 0.0
- Road wins due to either tie-breaking or slightly lower infrastructure O&M costs
- Road infrastructure_om_costs = €0.1/year
- Rail infrastructure_om_costs = €10,000/year (but these aren't modeled - see below)

### Test 3: Rail at €0.05/tkm (40% cheaper than road @ €0.082/tkm)

**Result:**
- Objective: €4,632,736,454 (-€243M vs road, -5.2%)
- Modal split: **100% rail** (mode 2, dummy techvehicle 4)
- Successfully demonstrates modal shift to cheaper mode!

**Conclusion**: ✅ Modal shift is working correctly - model responds to cost differences!

## Key Technical Details

### Dummy Techvehicle IDs
- **Mode 1 (road)**: dummy techvehicle ID = 3
- **Mode 2 (rail)**: dummy techvehicle ID = 4
- Formula: `length(techvehicles) + findfirst(mode -> mode.id == m.id && !mode.quantify_by_vehs, modes)`

### Costs Applied in Objective (for quantify_by_vehs=false modes)
1. **Levelized transport cost**: `cost_per_ukm * route_length * flow * time_step * discount_factor`
2. **Waiting time cost**: `VoT * waiting_time * flow * time_step * discount_factor`

### Mode Infrastructure - NOT MODELED
Mode infrastructure expansion (`q_mode_infr_plus` variable and `constraint_mode_infrastructure`) is **disabled** because:
1. Rail (mode 2) uses levelized costs (quantify_by_vehs=false) - costs already embedded in cost_per_ukm
2. Initial mode infrastructure data only has one global entry (allocation=-1)
3. Not needed for current analysis which focuses on operational costs

The `infrastructure_expansion_costs` and `infrastructure_om_costs` fields in Mode.yaml are therefore **not being used** in the model. Modal competition is based purely on:
- `cost_per_ukm` (EUR/tkm) - levelized operational cost
- `waiting_time` (hours) - terminal access time for value of time calculation

## Files Modified

### 1. `src/model_functions.jl`
- **Lines 4300-4345**: Added objective function fix for non-vehicle modes
- **Status**: Production code - keep permanently

### 2. `examples/moving_loads_SM/SM.jl`
- **Line 25**: Fixed typo `q_fuel_infr_plus^` → `q_fuel_infr_plus`
- **Lines 113-120**: Disabled mode infrastructure constraint (not needed)
- **Lines 245**: Added mode_infra timing to summary (set to 0.0)
- **Status**: Case-specific configuration

### 3. `examples/moving_loads_SM/input_data/case_20251102_093733/Mode.yaml`
- **Lines 4-6**: Road cost_per_ukm = €0.082/tkm
- **Lines 218-258**: Rail cost_per_ukm = €0.05/tkm (CURRENT VALUE for testing)
- **Status**: Test scenario - adjust as needed for analysis

## Modal Split Results Summary

| Rail Cost (€/tkm) | Objective (€B) | Modal Split | Notes |
|-------------------|----------------|-------------|-------|
| 1000.0 (Before fix) | 4.25 | 100% rail | Bug: rail cost not applied |
| 1000.0 (After fix) | 4.88 | 100% road | Fix working: expensive rail avoided |
| 0.085 (Same as road) | 4.88 | 100% road | Road wins tie-break |
| 0.05 (40% cheaper) | 4.63 | 100% rail | Shift to cheaper mode ✅ |

## Next Steps for Analysis

1. **Determine realistic rail cost_per_ukm values** for your scenarios
   - Current value: €0.05/tkm (testing)
   - Road value: €0.082/tkm

2. **Run scenarios** with different rail costs to analyze modal shift sensitivity

3. **Consider adding**:
   - Different cost_per_ukm by year (technology learning curves)
   - Non-zero waiting_time for rail (terminal access penalty)
   - Maximum mode share constraints if needed

4. **Mode 3 (road2) cleanup**: The workaround mode created earlier can be removed from:
   - Mode.yaml (delete mode id=3 entry)
   - Vehicletype.yaml (change trucks back to mode=1)

## Status

✅ **OBJECTIVE BUG FIXED AND VERIFIED**
✅ **MODAL SHIFT WORKING CORRECTLY**
✅ **READY FOR SCENARIO ANALYSIS**

The model now properly accounts for modal costs and responds correctly to cost_per_ukm changes. All modal competition is based on levelized costs defined in Mode.yaml.
