# Bug Found: quantify_by_vehs=false Costs Not Applied in Objective

**Date**: 2025-11-02
**Status**: ✅ ROOT CAUSE IDENTIFIED

---

## Problem

When both road and rail modes are set to `quantify_by_vehs=false` with different `cost_per_ukm` values:
- Road: 0.010 EUR/tkm
- Rail: 0.085 EUR/tkm

The model achieves **optimal objective = 0.0** and still chooses 100% rail.

---

## Root Cause

### In `src/model_functions.jl` lines 3991-4260:

The objective function loops over `techvehicles` from `techvehicle_list`:

```julia
for v ∈ techvehicles  # Line 3991
    # ...
    if v.vehicle_type.mode.quantify_by_vehs  # Line 4203
        # Add vehicle-based costs (capital, fuel, time, etc.)
    else  # Line 4230
        # Add levelized costs for non-vehicle modes
        m = v.vehicle_type.mode
        add_to_expression!(
            total_cost_expr,
            discount_factor * m.cost_per_ukm[y-y_init+1] * route_length * 1000 * model[:f][...]
        )
    end
end
```

**The Problem**: `techvehicle_list` contains ONLY real techvehicles:
- ID 0: ICEV truck (mode 1, road)
- ID 1: BEV truck (mode 1, road)

**Dummy techvehicles for `quantify_by_vehs=false` modes are created in `support_functions.jl` lines 1179-1183:**
```julia
if !m.quantify_by_vehs
    push!(m_tv_pairs, (m.id, counter_additional_vehs + 1))
    push!(techvehicle_ids, counter_additional_vehs + 1)
    global counter_additional_vehs += 1
end
```

This creates:
- Dummy techvehicle ID 3 for mode 1 (road, now quantify_by_vehs=false)
- Dummy techvehicle ID 4 for mode 2 (rail, quantify_by_vehs=false)

**But these dummy techvehicles are NOT in `techvehicle_list`!** They only exist in the `m_tv_pairs` set.

### Result

The objective function loop **NEVER visits dummy techvehicles 3 and 4**, so:
1. Mode 1 (road) dummy techvehicle 3: ✅ Exists in m_tv_pairs, ❌ Never gets cost added
2. Mode 2 (rail) dummy techvehicle 4: ✅ Exists in m_tv_pairs, ❌ Never gets cost added

Both modes have **zero cost in the objective**!

The model still chooses rail because when costs are equal (zero), Gurobi picks arbitrarily based on variable ordering/internal heuristics.

---

## Evidence

### Test 1: Both modes cost 0.082 EUR/tkm
- **Result**: Objective = 0.0, chose 100% rail

### Test 2: Road 0.010 EUR/tkm, Rail 0.085 EUR/tkm
- **Expected**: Road should be 8.5x cheaper, model should choose 100% road
- **Actual**: Objective = 0.0, still chose 100% rail

Both modes effectively cost zero in the objective!

---

## Solution Options

### Option A: Loop Over Modes Separately (Recommended)

Add a separate loop in the objective function for modes with `quantify_by_vehs=false`:

```julia
# After the techvehicles loop (line ~4260), add:

# Costs for non-vehicle modes (dummy techvehicles)
for m in mode_list
    if !m.quantify_by_vehs
        dummy_tv_id = counter_for_this_mode  # Get the dummy techvehicle ID

        for y in modeled_years
            for r in odpairs
                for k in r.paths
                    for g in modeled_generations
                        if g > y
                            continue
                        end

                        # Levelized cost per tkm
                        add_to_expression!(
                            total_cost_expr,
                            discount_factor * m.cost_per_ukm[y-y_init+1] * k.length * 1000 *
                            model[:f][y, (r.product.id, r.id, k.id), (m.id, dummy_tv_id), g] * time_step
                        )

                        # Waiting time cost
                        vot = r.financial_status.VoT
                        waiting_time_cost = vot * m.waiting_time[y-y_init+1]
                        add_to_expression!(
                            total_cost_expr,
                            discount_factor * waiting_time_cost * 1000 *
                            model[:f][y, (r.product.id, r.id, k.id), (m.id, dummy_tv_id), g] * time_step
                        )
                    end
                end
            end
        end
    end
end
```

### Option B: Create Dummy TechVehicle Objects

Modify `support_functions.jl` to create actual `TechVehicle` objects for dummy techvehicles and add them to `techvehicle_list`. This would allow the existing objective function loop to work without modification.

---

## Recommended Next Steps

1. Implement Option A (cleanest and easiest to understand)
2. Re-test with road=0.010, rail=0.085
3. Verify model chooses 100% road (cheaper option)
4. Re-test with road=0.082, rail=0.085
5. Verify model chooses 100% road (slightly cheaper)

---

## Files Affected

- `src/model_functions.jl` (lines ~4260): Add new loop for non-vehicle mode costs
- OR `src/support_functions.jl` (lines ~1179-1183): Create dummy TechVehicle objects

---

**Status**: Ready to implement fix
