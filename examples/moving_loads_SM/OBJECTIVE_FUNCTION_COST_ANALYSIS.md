# Objective Function Cost Analysis

## How Electricity Prices and Network Costs Appear in the Objective

### 1. **Electricity/Fuel Costs** (from `FuelCost.yaml`)

**Formula in objective:**
```julia
model[:s][y, (r.product.id, r.id, k.id, geo.id), v.id, f_l, g] * (1000) *
    (current_fuel_infr.cost_per_kWh_network[y-y_init+1] + fuel_cost_per_kWh +
     10^(-6) * v.technology.fuel.emission_factor[y-y_init+1] * geo.carbon_price[y-y_init+1]) *
    discount_factor * time_step
```

**Components:**
- `s`: Energy consumed (kWh, scaled by 1000)
- `fuel_cost_per_kWh`: **Location-specific electricity price** (€/kWh)
  - **Variable prices:** 0.065 - 0.529 €/kWh
  - **Uniform prices:** 0.065 - 0.355 €/kWh
- Carbon cost: ~10^-6 × emission_factor × carbon_price (negligible for electricity)
- Infrastructure network cost: cost_per_kWh_network (if applicable)

**Impact:** Fuel costs are multiplied by:
- Energy consumption `s` (very large)
- Scaling factor 1000
- Discount factor
- Time step

### 2. **Network Connection Costs** (from `NetworkConnectionCosts.yaml`)

**Formula in objective:**
```julia
# Applied to cumulative installed charging capacity
model[:q_fuel_infr_plus][y0, f_l, geo.id] *
    network_cost_item.network_cost_per_kW[y-y_init+1] *
    discount_factor * time_step
```

**Components:**
- `q_fuel_infr_plus`: Installed charging capacity (kW)
- `network_cost_per_kW`: **Annual grid connection cost** (€/kW/year)
  - **Variable network:** 8.58 - 16.77 €/kW
  - **Uniform network:** 12.25 €/kW (constant)
- Discount factor
- Time step

**Impact:** Network costs are:
- Applied ANNUALLY to cumulative capacity
- Summed over all previous installation years (y0 ∈ y_init:y)
- Much smaller than one-time CAPEX

### 3. **Vehicle Capital Costs** (CAPEX)

**Formula in objective:**
```julia
model[:h_plus][y, r.id, v.id, y] * (capital_cost - veh_sub) * discount_factor
```

**Components:**
- `h_plus`: Number of new vehicles purchased
- `capital_cost`: Vehicle purchase price (€/vehicle)
  - **Typical truck CAPEX:** €100,000 - €300,000 per vehicle
  - **BEV premium:** +€50,000 - €100,000 over ICEV
- Vehicle subsidy (if applicable)

**Impact:** This is typically the **dominant cost component** in freight models

### 4. **Vehicle Maintenance Costs** (OPEX)

**Formula in objective:**
```julia
model[:h][y, r.id, v.id, g] * v.opex_var[y-y_init+1] * discount_factor * time_step
```

**Components:**
- `h`: Vehicle stock
- `opex_var`: Annual operating costs (€/vehicle/year)
  - **Typical values:** €10,000 - €30,000 per vehicle per year

---

## Why Results Might Be Identical Despite Different Input Costs

### Hypothesis 1: **CAPEX Dominates the Objective**

If vehicle capital costs (€100k - €300k per truck) dominate the objective, then:
- Electricity cost variations (0.154 vs 0.143 €/kWh) might have **minimal impact**
- Network cost variations (13.47 vs 12.25 €/kW) might be **negligible**

**Example calculation:**
- Single truck driving 100,000 km/year with 1.5 kWh/km consumption = 150,000 kWh
- Electricity cost difference: (0.154 - 0.143) × 150,000 = €1,650/year
- Truck CAPEX: €150,000 one-time
- **Ratio:** 1,650 / 150,000 = **1.1%** (fuel costs are only 1% of CAPEX!)

### Hypothesis 2: **Constraint-Dominated Solution**

The optimal solution might be determined by:
- **Mandatory break constraints** (EU driving time regulations)
- **SOC constraints** (battery capacity limits routes)
- **Demand coverage** (all freight must be transported)
- **Infrastructure availability** (limited charging locations)

If these constraints force a specific solution, then cost variations don't matter.

### Hypothesis 3: **Cost Differences Are Too Small**

With MIPGap = 0.01 (1% optimality tolerance), the solver might consider solutions within 1% of optimal as "equivalent". If your cost variations create differences smaller than 1%, the solver stops at the same solution.

### Hypothesis 4: **Model Not Using Location-Specific Costs**

Check if the model is actually using:
```julia
fuel_cost_list[location_fuel_cost_idx].cost_per_kWh[y-y_init+1]
```

vs falling back to base cost:
```julia
v.technology.fuel.cost_per_kWh[y-y_init+1]  # Fallback to base cost
```

If the location lookup fails, all cases use the same base fuel cost!

---

## Recommended Diagnostics

### 1. Check Objective Function Values

Compare the total objective value across your 4 cases:

```julia
# After optimization
objective_value(model)
```

If values are **identical**, that's a red flag.
If values **differ by <1%**, solver might be stopping early due to MIPGap.

### 2. Check if Location-Specific Costs Are Found

Add logging to see if location lookups succeed:

```julia
location_fuel_cost_idx = findfirst(fc ->
    fc.location.id == geo.id && fc.fuel.id == v.technology.fuel.id,
    fuel_cost_list
)
if location_fuel_cost_idx !== nothing
    println("Found location-specific fuel cost for geo=$(geo.id)")
else
    println("WARNING: Using base fuel cost for geo=$(geo.id)")
end
```

### 3. Calculate Cost Component Breakdown

After solving, calculate:
- Total fuel costs
- Total network costs
- Total vehicle CAPEX
- Total vehicle OPEX

This will show which costs actually matter in the objective.

---

## Expected Outcome

**If costs matter:** You should see different optimal solutions (e.g., different vehicle technologies, routes, or charging infrastructure locations).

**If costs don't matter (current situation):** The solution is constraint-driven, and cost variations are too small relative to:
1. Vehicle CAPEX (€100k-300k per truck)
2. Solver optimality tolerance (1%)
3. Operational constraints (breaks, SOC limits)

**Most likely cause:** Electricity and network costs are **orders of magnitude smaller** than vehicle capital costs, making the variations economically insignificant within the 1% MIPGap tolerance.
