"""
Reconcile the two different path length estimates
"""

# From model outputs (scenario_001, with_fuel, ICEV only)
fleet_years = 564_866          # vehicle-years over horizon
flow_ktonnes = 1_151_492       # ktonnes over horizon (with time_step)
energy_mwh = 43_317_118        # MWh over horizon

# Parameters
W = 13.6           # tonnes payload
annual_range = 136_750  # km/year
spec_cons = 3.639  # kWh/km
time_step = 4
num_years = 11

print("=" * 70)
print("RECONCILING PATH LENGTH ESTIMATES")
print("=" * 70)

# Method 1: From FLEET constraint
# h >= (path × flow × 1000) / (W × AnnualRange)
# So: path = h × W × AnnualRange / (flow × 1000)
print("\n1. PATH FROM FLEET CONSTRAINT:")
print("-" * 50)
flow_tonnes = flow_ktonnes * 1000
path_from_fleet = fleet_years * W * annual_range / flow_tonnes
print(f"   fleet_years × W × AnnualRange / flow_tonnes")
print(f"   = {fleet_years:,} × {W} × {annual_range:,} / {flow_tonnes/1e9:.2f}B")
print(f"   = {path_from_fleet:,.0f} km")

# Method 2: From ENERGY constraint
# s = (spec_cons / W) × path × flow
# So: path = s × W / (spec_cons × flow)
print("\n2. PATH FROM ENERGY CONSTRAINT:")
print("-" * 50)
energy_kwh = energy_mwh * 1000
path_from_energy = energy_kwh * W / (spec_cons * flow_tonnes)
print(f"   energy_kwh × W / (spec_cons × flow_tonnes)")
print(f"   = {energy_kwh/1e9:.1f}B × {W} / ({spec_cons} × {flow_tonnes/1e9:.2f}B)")
print(f"   = {path_from_energy:,.0f} km")

print("\n3. RATIO:")
print("-" * 50)
ratio = path_from_fleet / path_from_energy
print(f"   Fleet path / Energy path = {path_from_fleet:.0f} / {path_from_energy:.0f} = {ratio:.1f}x")

print("\n4. WHAT DOES THIS RATIO MEAN?")
print("-" * 50)
print(f"""
   The fleet is sized for {path_from_fleet:.0f} km paths.
   The energy is calculated for {path_from_energy:.0f} km paths.

   Ratio = {ratio:.1f}x

   This could mean:
   a) Fleet drives {ratio:.1f}x more km than just the loaded transport
      (includes empty returns, repositioning, etc.)

   b) OR there's an error in my aggregation of flow/energy data
""")

# Check: what should the relationship be?
print("\n5. EXPECTED RELATIONSHIP:")
print("-" * 50)
print(f"""
   From constraints:
   - Fleet constraint: h = (path × flow) / (W × AnnualRange)
   - Energy constraint: s = (spec_cons / W) × path × flow

   Combining:
   - h × W × AnnualRange = path × flow (from fleet)
   - s × W / spec_cons = path × flow (from energy)

   So: h × W × AnnualRange = s × W / spec_cons
   => h × AnnualRange = s / spec_cons
   => h = s / (spec_cons × AnnualRange)
""")

# Check if this holds
expected_fleet = energy_kwh / (spec_cons * annual_range)
print(f"   Expected fleet from energy: {expected_fleet:,.0f}")
print(f"   Actual fleet: {fleet_years:,.0f}")
print(f"   Ratio: {fleet_years / expected_fleet:.1f}x")

print("\n6. CONCLUSION:")
print("-" * 50)
print(f"""
   The fleet is {fleet_years / expected_fleet:.1f}x larger than what the energy
   consumption would require.

   This means either:
   - Vehicles drive km that don't consume energy (impossible)
   - The energy (s) is underreported/parsed incorrectly
   - The fleet (h) includes vehicles that aren't being used
   - There's a constraint forcing excess fleet (aging, stock shift)

   Most likely: The model's h variable represents CAPACITY needed,
   while s represents ENERGY for actual transport. The gap is the
   "slack" or unutilized capacity in the fleet.
""")
