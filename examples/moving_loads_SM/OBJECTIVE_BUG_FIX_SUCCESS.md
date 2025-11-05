# Objective Function Bug Fix - SUCCESS

## Problem Summary

The objective function in `model_functions.jl` was not applying costs for transport modes with `quantify_by_vehs=false` (modes 1 and 2: road and rail). This caused rail to appear free, resulting in unrealistic 100% rail modal split.

## Root Cause

The objective function loops over `techvehicles` from `techvehicle_list` (line 3991):
```julia
for v ∈ techvehicles
```

However, modes with `quantify_by_vehs=false` use **dummy techvehicles** that exist in the `m_tv_pairs` set but are **NOT** in `techvehicle_list`. Therefore, the loop never visited these techvehicles, and the `else` branch (line 4230) that adds levelized costs was never executed.

## Solution Implemented

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

## Verification Results

### Test 1: Rail at €1000/tkm (very expensive)

**Before Fix:**
- Objective: €4,254,133,936
- Modal split: 100% rail (mode 2)
- Changing rail costs had NO effect

**After Fix:**
- Objective: €4,882,720,000 (+€628M)
- Modal split: 100% road (mode 1 with dummy techvehicle 3)
- Gurobi warning: "Model contains large objective coefficients" (correctly seeing €1000/tkm)
- Solver iterations: 312 → 606 (now comparing real costs)

**Flow Results:**
```yaml
(2022, (0, 1, 1), (1, 3), 2010): "1.071229"    # Mode 1, techvehicle 3
(2022, (0, 9, 9), (1, 3), 2010): "11.863699"
(2022, (0, 12, 12), (1, 3), 2018): "12.380384"
```

All flows show `(1, 3)` = mode 1 (road) with dummy techvehicle 3.
No mode 2 (rail) flows exist.

## Key Technical Details

- **Dummy Techvehicle ID Calculation**: `length(techvehicles) + findfirst(mode -> mode.id == m.id && !mode.quantify_by_vehs, modes)`
  - Mode 1 (road): dummy techvehicle ID = 3
  - Mode 2 (rail): dummy techvehicle ID = 4

- **Costs Applied**:
  - Levelized cost: `cost_per_ukm * route_length * flow * time_step`
  - Waiting time cost: `VoT * waiting_time * flow * time_step`

## Next Steps

1. Test with realistic rail costs (€0.085-€0.15/tkm) to see actual modal competition
2. Verify mode 3 "road2" workaround is no longer needed
3. Consider removing mode 3 from input data to clean up

## Status

✅ **BUG FIX SUCCESSFUL** - Modal costs now properly applied, model responds to cost changes
