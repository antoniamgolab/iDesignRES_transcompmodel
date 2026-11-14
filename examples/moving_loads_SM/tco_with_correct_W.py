"""
TCO calculation with CORRECT W (payload) values from TechVehicle.yaml
"""

# Correct parameters from TechVehicle.yaml
tv_params = {
    'ICEV': {
        'capital': 145571,      # EUR
        'maint': 20703,         # EUR/year
        'spec_cons': 3.639,     # kWh/km
        'fuel_price': 0.1845,   # EUR/kWh
        'W': 13.6,              # tonnes payload
        'lifetime': 12,         # years
        'annual_range': 136750, # km/year
    },
    'BEV': {
        'capital': 557714,      # EUR
        'maint': 14364,         # EUR/year
        'spec_cons': 2.056,     # kWh/km
        'fuel_price': 0.17,     # EUR/kWh
        'W': 10.9,              # tonnes payload (lower due to battery weight)
        'lifetime': 12,         # years
        'annual_range': 136750, # km/year
    }
}

print("=" * 70)
print("TCO CALCULATION WITH CORRECT W VALUES")
print("=" * 70)

for name, v in tv_params.items():
    print(f"\n{name}:")
    print(f"  Payload (W): {v['W']} tonnes")

    # Per vehicle-km
    lifetime_km = v['lifetime'] * v['annual_range']
    cap_per_km = v['capital'] / lifetime_km
    maint_per_km = v['maint'] / v['annual_range']
    fuel_per_km = v['spec_cons'] * v['fuel_price']
    total_per_km = cap_per_km + maint_per_km + fuel_per_km

    print(f"\n  Per VEHICLE-KM:")
    print(f"    Capital:     {cap_per_km:.4f} EUR/km  ({cap_per_km/total_per_km*100:5.1f}%)")
    print(f"    Maintenance: {maint_per_km:.4f} EUR/km  ({maint_per_km/total_per_km*100:5.1f}%)")
    print(f"    Fuel:        {fuel_per_km:.4f} EUR/km  ({fuel_per_km/total_per_km*100:5.1f}%)")
    print(f"    TOTAL:       {total_per_km:.4f} EUR/km")

    # Per tonne-km (divide by W)
    cap_per_tkm = cap_per_km / v['W']
    maint_per_tkm = maint_per_km / v['W']
    fuel_per_tkm = fuel_per_km / v['W']  # = spec_cons * fuel_price / W
    total_per_tkm = cap_per_tkm + maint_per_tkm + fuel_per_tkm

    print(f"\n  Per TONNE-KM (divided by W={v['W']}t):")
    print(f"    Capital:     {cap_per_tkm:.5f} EUR/tkm  ({cap_per_tkm/total_per_tkm*100:5.1f}%)")
    print(f"    Maintenance: {maint_per_tkm:.5f} EUR/tkm  ({maint_per_tkm/total_per_tkm*100:5.1f}%)")
    print(f"    Fuel:        {fuel_per_tkm:.5f} EUR/tkm  ({fuel_per_tkm/total_per_tkm*100:5.1f}%)")
    print(f"    TOTAL:       {total_per_tkm:.5f} EUR/tkm")

    # Energy per tkm (this is what constraint_fueling_demand uses)
    energy_per_tkm = v['spec_cons'] / v['W']
    print(f"\n  Energy per tkm: {energy_per_tkm:.4f} kWh/tkm")

print("\n" + "=" * 70)
print("COMPARISON SUMMARY")
print("=" * 70)

print("\nPer vehicle-km:")
print(f"  ICEV: {tv_params['ICEV']['capital']/(12*136750) + tv_params['ICEV']['maint']/136750 + tv_params['ICEV']['spec_cons']*tv_params['ICEV']['fuel_price']:.4f} EUR/km")
print(f"  BEV:  {tv_params['BEV']['capital']/(12*136750) + tv_params['BEV']['maint']/136750 + tv_params['BEV']['spec_cons']*tv_params['BEV']['fuel_price']:.4f} EUR/km")

icev_tkm = (tv_params['ICEV']['capital']/(12*136750) + tv_params['ICEV']['maint']/136750 + tv_params['ICEV']['spec_cons']*tv_params['ICEV']['fuel_price']) / tv_params['ICEV']['W']
bev_tkm = (tv_params['BEV']['capital']/(12*136750) + tv_params['BEV']['maint']/136750 + tv_params['BEV']['spec_cons']*tv_params['BEV']['fuel_price']) / tv_params['BEV']['W']

print("\nPer tonne-km:")
print(f"  ICEV: {icev_tkm:.5f} EUR/tkm")
print(f"  BEV:  {bev_tkm:.5f} EUR/tkm")
print(f"  BEV advantage: {(1 - bev_tkm/icev_tkm)*100:.1f}% cheaper per tkm")

print("\n" + "=" * 70)
print("NOTE: BEV has LOWER payload (10.9t vs 13.6t) due to battery weight")
print("This means more trips needed to transport same tonnage!")
print("=" * 70)

# Calculate trips needed for 1000 tonnes over 1000 km
tonnes = 1000
distance = 1000

icev_trips = tonnes / tv_params['ICEV']['W']
bev_trips = tonnes / tv_params['BEV']['W']

icev_vkm = icev_trips * distance
bev_vkm = bev_trips * distance

icev_cost = icev_vkm * (tv_params['ICEV']['capital']/(12*136750) + tv_params['ICEV']['maint']/136750 + tv_params['ICEV']['spec_cons']*tv_params['ICEV']['fuel_price'])
bev_cost = bev_vkm * (tv_params['BEV']['capital']/(12*136750) + tv_params['BEV']['maint']/136750 + tv_params['BEV']['spec_cons']*tv_params['BEV']['fuel_price'])

print(f"\nExample: Transport {tonnes} tonnes over {distance} km")
print(f"  ICEV: {icev_trips:.1f} trips x {distance} km = {icev_vkm:,.0f} vehicle-km = {icev_cost:,.0f} EUR")
print(f"  BEV:  {bev_trips:.1f} trips x {distance} km = {bev_vkm:,.0f} vehicle-km = {bev_cost:,.0f} EUR")
print(f"  Difference: BEV is {(bev_cost/icev_cost - 1)*100:+.1f}% vs ICEV")
