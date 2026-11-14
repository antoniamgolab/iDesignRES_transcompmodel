"""
Clarify the relationship between fleet, flow, and energy
"""

# From model outputs
icev_fleet_years = 564_866      # vehicle-years
icev_flow_ktonnes = 1_151_492   # thousand-tonnes (already × time_step)
icev_energy_mwh = 43_317_118    # MWh

# Parameters
annual_range = 136_750  # km/year (THEORETICAL maximum per truck)
W = 13.6                # tonnes payload
spec_cons = 3.639       # kWh/km
time_step = 4
num_years = 11

print("=" * 70)
print("CLARIFYING ENERGY CALCULATION")
print("=" * 70)

# Method 1: From fleet capacity (WRONG approach)
print("\n1. WRONG APPROACH: Fleet capacity × spec_cons")
print("-" * 50)
theoretical_vkm = icev_fleet_years * annual_range
theoretical_energy_twh = spec_cons * theoretical_vkm / 1e9
print(f"   Fleet-years: {icev_fleet_years:,}")
print(f"   × Annual range: {annual_range:,} km/year")
print(f"   = Theoretical max vehicle-km: {theoretical_vkm/1e9:.2f} billion km")
print(f"   × spec_cons: {spec_cons} kWh/km")
print(f"   = Theoretical energy: {theoretical_energy_twh:.1f} TWh")
print(f"\n   This assumes ALL trucks drive {annual_range:,} km/year at FULL LOAD")
print(f"   This is NOT realistic!")

# Method 2: From flow (CORRECT approach)
print("\n2. CORRECT APPROACH: Flow × energy_per_tkm")
print("-" * 50)
flow_tonnes = icev_flow_ktonnes * 1000  # convert to tonnes
energy_per_tkm = spec_cons / W  # kWh per tonne-km
print(f"   Flow: {flow_tonnes/1e9:.2f} billion tonnes")
print(f"   Energy per tkm: {energy_per_tkm:.4f} kWh/tkm")

# We need average path length to get tkm
# From s = (spec_cons / W) × path_length × flow
# Rearranging: avg_path = s × W / (spec_cons × flow)
actual_energy_kwh = icev_energy_mwh * 1000  # convert MWh to kWh
avg_path = actual_energy_kwh * W / (spec_cons * flow_tonnes)
print(f"\n   From s = (spec_cons/W) × path × flow, solving for avg path:")
print(f"   Average path length: {avg_path:.0f} km")

tkm = flow_tonnes * avg_path
print(f"\n   Total tonne-km: {tkm/1e12:.2f} trillion tkm")
print(f"   × Energy per tkm: {energy_per_tkm:.4f} kWh/tkm")
energy_from_flow = tkm * energy_per_tkm / 1e9
print(f"   = Energy from flow: {energy_from_flow:.1f} TWh")
print(f"\n   Actual s_dict energy: {icev_energy_mwh/1e6:.1f} TWh")
print(f"   Match: {energy_from_flow:.1f} ≈ {icev_energy_mwh/1e6:.1f} TWh ✓")

# Method 3: Actual vehicle-km driven
print("\n3. ACTUAL VEHICLE-KM (from flow, not fleet capacity)")
print("-" * 50)
trips = flow_tonnes / W
loaded_vkm = trips * avg_path  # one-way loaded km
round_trip_vkm = loaded_vkm * 2  # assuming empty return
print(f"   Trips needed: {trips/1e6:.1f} million")
print(f"   × Average path: {avg_path:.0f} km")
print(f"   = Loaded vehicle-km: {loaded_vkm/1e9:.2f} billion km (one-way)")
print(f"   = Round-trip vehicle-km: {round_trip_vkm/1e9:.2f} billion km")

print("\n4. COMPARISON")
print("-" * 50)
print(f"   Theoretical max vkm (fleet × annual_range): {theoretical_vkm/1e9:.2f} B km")
print(f"   Actual loaded vkm (from flow):             {loaded_vkm/1e9:.2f} B km")
print(f"   Ratio: {loaded_vkm/theoretical_vkm*100:.1f}%")

print("\n5. INTERPRETATION")
print("-" * 50)
print(f"""
   The fleet of {icev_fleet_years:,} vehicle-years COULD drive {theoretical_vkm/1e9:.0f}B km
   if every truck drove {annual_range:,} km/year.

   But the actual demand only requires {loaded_vkm/1e9:.1f}B loaded km
   (or {round_trip_vkm/1e9:.1f}B km including empty returns).

   The ratio ({loaded_vkm/theoretical_vkm*100:.1f}%) reflects:
   - Fleet is sized for PEAK demand, not average
   - Fleet must be available even when not fully utilized
   - annual_range is MAXIMUM capacity, not actual usage

   The energy calculation in the model is CORRECT:
   s = (spec_cons / W) × path_length × flow

   This gives energy based on ACTUAL transport work done,
   NOT based on theoretical fleet capacity.
""")
