# Decision Variable Indexing Change Analysis

**Objective**: Remove `f_l` (fuel-infrastructure pair) dimension from `soc` and `travel_time` variables

**Current indexing:**
- `model[:soc][y, (p, r, k, g_element), tv, f_l, g]`
- `model[:travel_time][y, (p, r, k, g_element), tv, f_l, g]`

**Desired indexing:**
- `model[:soc][y, (p, r, k, g_element), tv, g]`
- `model[:travel_time][y, (p, r, k, g_element), tv, g]`

---

## Changes Required

### 1. Variable Definitions (src/model_functions.jl)

#### Line 253: `soc` variable definition
**Current:**
```julia
@variable(model, soc[y in modeled_years, p_r_k_g_pairs, tv in techvehicle_ids, f_l in f_l_not_by_route, g in modeled_generations; g <= y] >= 0)
```

**Change to:**
```julia
@variable(model, soc[y in modeled_years, p_r_k_g_pairs, tv in techvehicle_ids, g in modeled_generations; g <= y] >= 0)
```

#### Line 260: `travel_time` variable definition
**Current:**
```julia
@variable(model, travel_time[y in modeled_years, p_r_k_g_pairs, tv in techvehicle_ids, f_l in f_l_not_by_route, g in modeled_generations; g <= y] >= 0)
```

**Change to:**
```julia
@variable(model, travel_time[y in modeled_years, p_r_k_g_pairs, tv in techvehicle_ids, g in modeled_generations; g <= y] >= 0)
```

---

### 2. Constraint Functions - All References

#### `constraint_tank_capacity` (around line 3398)
**Current:**
```julia
model[:soc][y, prkg, tv.id, f_l, g] <= tv.tank_capacity[g-g_init+1] * (...)
```

**Change to:**
```julia
model[:soc][y, prkg, tv.id, g] <= tv.tank_capacity[g-g_init+1] * (...)
```

**Note**: Need to check if f_l loop is still needed or can be removed

---

#### `constraint_soc_origin` (around line 3450)
**Current:**
```julia
model[:soc][y, prkg, tv.id, f_l, g] == (...)
```

**Change to:**
```julia
model[:soc][y, prkg, tv.id, g] == (...)
```

---

#### `constraint_soc_track` (around lines 3494-3495)
**Current:**
```julia
model[:soc][y, (p.id, r.id, path.id, geo_curr.id), tv.id, f_l, g] ==
model[:soc][y, (p.id, r.id, path.id, geo_prev.id), tv.id, f_l, g] - (...)
```

**Change to:**
```julia
model[:soc][y, (p.id, r.id, path.id, geo_curr.id), tv.id, g] ==
model[:soc][y, (p.id, r.id, path.id, geo_prev.id), tv.id, g] - (...)
```

**Also in this constraint:** Check the charging term `model[:s][y, (...), tv.id, f_l, g]`
- If `s` keeps `f_l`, you need logic to map from no-f_l soc to f_l-indexed charging
- If `s` also loses `f_l`, update accordingly

---

#### `constraint_travel_time_track` (around lines 3549, 3594-3595, 3603-3604)

**Line 3549 - Origin constraint:**
**Current:**
```julia
model[:travel_time][y, prkg, tv.id, f_l, g] == 0
```

**Change to:**
```julia
model[:travel_time][y, prkg, tv.id, g] == 0
```

**Lines 3594-3595 - SOC tracking with extra_break_time:**
**Current:**
```julia
model[:travel_time][y, (p.id, r.id, path.id, geo_curr.id), tv.id, f_l, g] ==
model[:travel_time][y, (p.id, r.id, path.id, geo_prev.id), tv.id, f_l, g] + (...)
```

**Change to:**
```julia
model[:travel_time][y, (p.id, r.id, path.id, geo_curr.id), tv.id, g] ==
model[:travel_time][y, (p.id, r.id, path.id, geo_prev.id), tv.id, g] + (...)
```

**Lines 3603-3604 - SOC tracking without extra_break_time:**
**Current:**
```julia
model[:travel_time][y, (p.id, r.id, path.id, geo_curr.id), tv.id, f_l, g] ==
model[:travel_time][y, (p.id, r.id, path.id, geo_prev.id), tv.id, f_l, g] + (...)
```

**Change to:**
```julia
model[:travel_time][y, (p.id, r.id, path.id, geo_curr.id), tv.id, g] ==
model[:travel_time][y, (p.id, r.id, path.id, geo_prev.id), tv.id, g] + (...)
```

**Also in this constraint:** Check the charging time term `model[:s][y, (...), tv.id, f_l, g]`

---

#### `constraint_mandatory_breaks` (around line 3716)
**Current:**
```julia
model[:travel_time][y, (p.id, odpair.id, path.id, break_geo_id), tv.id, f_l, g] >= min_fleet_travel_time
```

**Change to:**
```julia
model[:travel_time][y, (p.id, odpair.id, path.id, break_geo_id), tv.id, g] >= min_fleet_travel_time
```

---

### 3. Loop Structure Changes

**Critical Question:** What happens to the `for f_l in f_l_pairs` loops?

#### Option A: Keep f_l loops, sum over f_l for charging
If charging `s` still has `f_l` dimension, you need to sum over all fuel types:

```julia
for y in modeled_years
    for tv in techvehicle_list
        for g in modeled_generations
            if g <= y
                @constraint(
                    model,
                    model[:soc][y, prkg, tv.id, g] ==
                    ... - energy_consumed * num_vehicles
                    + sum(model[:s][y, prkg, tv.id, f_l, g] for f_l in f_l_pairs if tv.technology.fuel.id == f_l[1])
                )
            end
        end
    end
end
```

#### Option B: Remove f_l entirely
If both `soc`, `travel_time`, AND `s` lose the `f_l` dimension:
- Remove `for f_l in f_l_pairs` loops entirely
- Just use `model[:s][y, prkg, tv.id, g]`

---

### 4. Additional Considerations

#### Fuel type matching:
Currently, f_l matching ensures constraints only apply to compatible fuel-infrastructure pairs:
```julia
if tv.technology.fuel.id == f_l[1]
    # constraint
end
```

**Without f_l indexing:**
- This logic needs to be handled differently
- Possibly aggregate over all infrastructure types for that fuel
- Or track which infrastructure is used separately

#### Charging variable `s`:
Check if `s` also needs the `f_l` dimension removed:
```bash
grep -n "@variable.*\bs\[" src/model_functions.jl
```

If yes, update all `s` references similarly.

---

### 5. Files to Modify

**Primary file:**
- `src/model_functions.jl`

**Functions to check/modify:**
1. `base_define_variables()` - Variable definitions (lines 253, 260)
2. `constraint_tank_capacity()` - Line 3398
3. `constraint_soc_origin()` - Line 3450
4. `constraint_soc_track()` - Lines 3494-3495
5. `constraint_travel_time_track()` - Lines 3549, 3594-3595, 3603-3604
6. `constraint_mandatory_breaks()` - Line 3716

**Other potential files:**
- Check if any result processing/saving functions reference these variables

---

### 6. Testing Strategy

After making changes:
1. Run a small test case to check model builds without errors
2. Verify constraint counts match expectations
3. Check that solution values are reasonable
4. Compare results with/without f_l dimension on same input

---

### 7. Summary of Line Numbers

| Location | Line(s) | Change |
|----------|---------|--------|
| Variable definition: soc | 253 | Remove `f_l in f_l_not_by_route` from indices |
| Variable definition: travel_time | 260 | Remove `f_l in f_l_not_by_route` from indices |
| constraint_tank_capacity | ~3398 | Remove `f_l` from `soc[...]` |
| constraint_soc_origin | ~3450 | Remove `f_l` from `soc[...]` |
| constraint_soc_track | ~3494-3495 | Remove `f_l` from `soc[...]` |
| constraint_travel_time_track (origin) | ~3549 | Remove `f_l` from `travel_time[...]` |
| constraint_travel_time_track (tracking) | ~3594-3595, ~3603-3604 | Remove `f_l` from `travel_time[...]` |
| constraint_mandatory_breaks | ~3716 | Remove `f_l` from `travel_time[...]` |

**Total affected lines:** ~8-10 locations

---

## Next Steps

1. Decide on loop structure (Option A or B above)
2. Check if `s` (charging) variable also needs f_l removed
3. Update variable definitions (lines 253, 260)
4. Update all constraint references (8-10 locations)
5. Update any loop structures (`for f_l in...`)
6. Test with small case
7. Verify results

Would you like me to implement these changes, or would you prefer to review this analysis first?
