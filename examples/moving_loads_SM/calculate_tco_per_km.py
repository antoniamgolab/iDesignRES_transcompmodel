"""
Calculate TCO per km directly from vehicle parameters
This is the proper way to compare with ICCT 2023 study
"""

# Vehicle parameters from TechVehicle.yaml (scenario_001, baseline 1.0x)
vehicles = {
    'ICEV': {
        'capital_cost': 145571,      # EUR
        'annual_maintenance': 20703, # EUR/year
        'spec_cons': 3.639,          # kWh/km (diesel equivalent)
        'fuel_price': 0.1845,        # EUR/kWh (diesel)
        'lifetime': 12,              # years
        'annual_range': 136750,      # km/year
    },
    'BEV': {
        'capital_cost': 557714,      # EUR (at 1.0x tech_cost)
        'annual_maintenance': 14364, # EUR/year
        'spec_cons': 2.056,          # kWh/km
        'fuel_price': 0.17,          # EUR/kWh (electricity avg)
        'lifetime': 12,              # years
        'annual_range': 136750,      # km/year
    }
}

print("=" * 70)
print("TCO PER KILOMETER - Direct Calculation from Parameters")
print("=" * 70)

for name, v in vehicles.items():
    total_km = v['lifetime'] * v['annual_range']

    # Cost components per km
    capital_per_km = v['capital_cost'] / total_km
    maint_per_km = v['annual_maintenance'] / v['annual_range']
    fuel_per_km = v['spec_cons'] * v['fuel_price']

    total_per_km = capital_per_km + maint_per_km + fuel_per_km

    print(f"\n{name}:")
    print(f"  Lifetime distance: {total_km:,} km")
    print(f"\n  Cost per km:")
    print(f"    Capital:     {capital_per_km:.4f} EUR/km  ({capital_per_km/total_per_km*100:5.1f}%)")
    print(f"    Maintenance: {maint_per_km:.4f} EUR/km  ({maint_per_km/total_per_km*100:5.1f}%)")
    print(f"    Fuel/Energy: {fuel_per_km:.4f} EUR/km  ({fuel_per_km/total_per_km*100:5.1f}%)")
    print(f"    ----------------------------------------")
    print(f"    TOTAL:       {total_per_km:.4f} EUR/km  (100.0%)")

# ICCT comparison
print("\n" + "=" * 70)
print("COMPARISON WITH ICCT 2023 (EU long-haul truck)")
print("=" * 70)

print("""
ICCT 2023 approximate breakdown for diesel truck:
  - Purchase/Capital: ~25%
  - Maintenance:      ~15%
  - Fuel:             ~50%
  - Other (tolls etc): ~10%

MODEL (ICEV):
  - Capital:     {:.1f}%
  - Maintenance: {:.1f}%
  - Fuel:        {:.1f}%
""".format(
    vehicles['ICEV']['capital_cost'] / (vehicles['ICEV']['lifetime'] * vehicles['ICEV']['annual_range']) /
    (vehicles['ICEV']['capital_cost'] / (vehicles['ICEV']['lifetime'] * vehicles['ICEV']['annual_range']) +
     vehicles['ICEV']['annual_maintenance'] / vehicles['ICEV']['annual_range'] +
     vehicles['ICEV']['spec_cons'] * vehicles['ICEV']['fuel_price']) * 100,

    vehicles['ICEV']['annual_maintenance'] / vehicles['ICEV']['annual_range'] /
    (vehicles['ICEV']['capital_cost'] / (vehicles['ICEV']['lifetime'] * vehicles['ICEV']['annual_range']) +
     vehicles['ICEV']['annual_maintenance'] / vehicles['ICEV']['annual_range'] +
     vehicles['ICEV']['spec_cons'] * vehicles['ICEV']['fuel_price']) * 100,

    vehicles['ICEV']['spec_cons'] * vehicles['ICEV']['fuel_price'] /
    (vehicles['ICEV']['capital_cost'] / (vehicles['ICEV']['lifetime'] * vehicles['ICEV']['annual_range']) +
     vehicles['ICEV']['annual_maintenance'] / vehicles['ICEV']['annual_range'] +
     vehicles['ICEV']['spec_cons'] * vehicles['ICEV']['fuel_price']) * 100
))

print("KEY OBSERVATIONS:")
print("-" * 70)
print("""
1. FUEL COST DISCREPANCY:
   - Model fuel: {:.4f} EUR/km (spec_cons={:.3f} kWh/km × {:.4f} EUR/kWh)
   - ICCT fuel: ~0.30-0.35 EUR/km (35 L/100km × 1.0 EUR/L)

   The model's spec_cons of {:.3f} kWh/km = {:.1f} kWh/100km
   Converting to diesel: {:.1f} kWh/100km ÷ 10 kWh/L = {:.1f} L/100km

   This is correct for a long-haul truck (~35 L/100km).

2. FUEL PRICE:
   - Model uses {:.4f} EUR/kWh for diesel
   - 1 L diesel ≈ 10 kWh → {:.2f} EUR/L
   - This is LOWER than current EU prices (~1.50 EUR/L)

3. CAPITAL COST:
   - Model: {:.0f} EUR for ICEV
   - ICCT: ~120,000-150,000 EUR for tractor + trailer
   - This matches well.

4. MAINTENANCE:
   - Model: {:.0f} EUR/year = {:.4f} EUR/km
   - ICCT: ~0.10-0.15 EUR/km
   - Model is HIGHER than ICCT estimates.
""".format(
    vehicles['ICEV']['spec_cons'] * vehicles['ICEV']['fuel_price'],
    vehicles['ICEV']['spec_cons'],
    vehicles['ICEV']['fuel_price'],
    vehicles['ICEV']['spec_cons'],
    vehicles['ICEV']['spec_cons'] * 100,
    vehicles['ICEV']['spec_cons'] * 100,
    vehicles['ICEV']['spec_cons'] * 100 / 10,
    vehicles['ICEV']['fuel_price'],
    vehicles['ICEV']['fuel_price'] * 10,
    vehicles['ICEV']['capital_cost'],
    vehicles['ICEV']['annual_maintenance'],
    vehicles['ICEV']['annual_maintenance'] / vehicles['ICEV']['annual_range']
))

print("\nTO MATCH ICCT BREAKDOWN, fuel price should be higher:")
print("  Current:  {:.4f} EUR/kWh = {:.2f} EUR/L diesel".format(
    vehicles['ICEV']['fuel_price'], vehicles['ICEV']['fuel_price'] * 10))
print("  Expected: ~0.15 EUR/kWh = ~1.50 EUR/L diesel (current EU avg)")
