"""
Check how energy consumption is calculated in the model
s is linked to flow (f) via constraint_fueling_demand
"""

# From model outputs:
icev_energy_mwh = 43_317_118
bev_energy_mwh = 17_280_714

icev_vehicle_km = 77.25e9
bev_vehicle_km = 62.22e9

icev_flow_ktonnes = 1_151_492  # thousand-tonnes over horizon
bev_flow_ktonnes = 900_303

# Spec cons from TechVehicle.yaml
icev_spec_cons = 3.639  # kWh/km
bev_spec_cons = 2.056   # kWh/km

# Vehicle capacity
capacity_tonnes = 25  # typical truck payload

print("=" * 70)
print("ENERGY CALCULATION CHECK")
print("=" * 70)

# Method 1: Energy per vehicle-km
print("\nMethod 1: Energy per vehicle-km")
icev_kwh_per_vkm = icev_energy_mwh * 1000 / icev_vehicle_km
bev_kwh_per_vkm = bev_energy_mwh * 1000 / bev_vehicle_km
print(f"  ICEV: {icev_kwh_per_vkm:.3f} kWh/km (expected: {icev_spec_cons:.3f})")
print(f"  BEV:  {bev_kwh_per_vkm:.3f} kWh/km (expected: {bev_spec_cons:.3f})")

# Method 2: Energy per tonne-km
print("\nMethod 2: Energy per tonne-km")
# Flow is in thousand-tonnes, so multiply by 1000 to get tonnes
icev_tkm = icev_flow_ktonnes * 1000  # We need path lengths too, but let's approximate
bev_tkm = bev_flow_ktonnes * 1000

# Average path length - let's estimate from vehicle-km / (flow / capacity)
# vehicle-km = trips × path_length
# trips = flow_tonnes / capacity
icev_trips = icev_flow_ktonnes * 1000 / capacity_tonnes
bev_trips = bev_flow_ktonnes * 1000 / capacity_tonnes

icev_avg_path = icev_vehicle_km / icev_trips
bev_avg_path = bev_vehicle_km / bev_trips

print(f"\nEstimated average path length:")
print(f"  ICEV: {icev_avg_path:.0f} km")
print(f"  BEV:  {bev_avg_path:.0f} km")

# tonne-km
icev_tkm_total = icev_flow_ktonnes * 1000 * icev_avg_path / 1e9  # billion tkm
bev_tkm_total = bev_flow_ktonnes * 1000 * bev_avg_path / 1e9

print(f"\nTotal tonne-km:")
print(f"  ICEV: {icev_tkm_total:.2f} billion tkm")
print(f"  BEV:  {bev_tkm_total:.2f} billion tkm")

# Energy per tkm
icev_kwh_per_tkm = icev_energy_mwh * 1000 / (icev_tkm_total * 1e9)
bev_kwh_per_tkm = bev_energy_mwh * 1000 / (bev_tkm_total * 1e9)

print(f"\nEnergy per tonne-km:")
print(f"  ICEV: {icev_kwh_per_tkm:.4f} kWh/tkm")
print(f"  BEV:  {bev_kwh_per_tkm:.4f} kWh/tkm")

# Expected: spec_cons / capacity
print(f"\nExpected (spec_cons / capacity of {capacity_tonnes}t):")
print(f"  ICEV: {icev_spec_cons/capacity_tonnes:.4f} kWh/tkm")
print(f"  BEV:  {bev_spec_cons/capacity_tonnes:.4f} kWh/tkm")

print("\n" + "=" * 70)
print("RECONCILIATION")
print("=" * 70)

# The discrepancy suggests the model energy is consistent
# Let's verify: energy = spec_cons × vehicle-km should equal s_dict total
expected_icev_energy = icev_spec_cons * icev_vehicle_km / 1e6  # MWh
expected_bev_energy = bev_spec_cons * bev_vehicle_km / 1e6

print(f"\nExpected energy (spec_cons x vehicle-km):")
print(f"  ICEV: {expected_icev_energy:,.0f} MWh")
print(f"  BEV:  {expected_bev_energy:,.0f} MWh")

print(f"\nActual energy from s_dict:")
print(f"  ICEV: {icev_energy_mwh:,.0f} MWh")
print(f"  BEV:  {bev_energy_mwh:,.0f} MWh")

print(f"\nRatio (expected/actual):")
print(f"  ICEV: {expected_icev_energy/icev_energy_mwh:.1f}x")
print(f"  BEV:  {expected_bev_energy/bev_energy_mwh:.1f}x")

print("\n" + "=" * 70)
print("CONCLUSION")
print("=" * 70)
print("""
The energy from s_dict is ~6-7x LOWER than spec_cons x vehicle-km.

This could mean:
1. The s variable represents something different (per-trip energy?)
2. There's a unit conversion issue in s_dict
3. Not all vehicle-km require fueling (e.g., return trips empty?)

Let's check what constraint_fueling_demand actually does...
""")
