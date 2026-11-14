"""
Brief analysis of SOC tracking constraint issue
Focuses on understanding the fundamental problem with how SOC changes along routes
"""

import yaml

# Configuration
result_timestamp = "case_20251110_160646_reverse_cs_2025-11-16_16-48-22"

print(f"\n{'='*80}")
print(f"SOC TRACKING ISSUE DIAGNOSIS - {result_timestamp}")
print(f"{'='*80}\n")

print("Reading constraint code from model_functions.jl...")
print("\nFrom lines 3556-3580 (constraint_soc_max):")
print("""
  @constraint(model, [y in modeled_years, prkg in p_r_k_g_pairs, tv in techvehicle_list; g <= y],
      model[:soc][y, prkg, tv.id, g] <= tv.tank_capacity[g-g_init+1] * (
          path_dict[prkg[3]].length / (tv.W[g-g_init+1] * tv.AnnualRange[g-g_init+1])
      ) * 1000 * model[:f][y, (prkg[1], prkg[2], prkg[3]), (tv.vehicle_type.mode.id, tv.id), g]
  )

This sets: SOC <= tank_capacity × num_vehicles
where num_vehicles = (path_length / (W × AnnualRange)) × 1000 × flow
""")

print("\nFrom lines 3601-3633 (constraint_soc_track - ORIGIN):")
print("""
  # At origin (first node in path)
  num_vehicles = (
      path.length / (tv.W[g-g_init+1] * tv.AnnualRange[g-g_init+1])
  ) * 1000 * model[:f][y, (prkg[1], prkg[2], prkg[3]), (tv.vehicle_type.mode.id, tv.id), g]

  @constraint(
      model,
      model[:soc][y, prkg, tv.id, g] ==
      tv.tank_capacity[g-g_init+1] * num_vehicles
  )

This initializes SOC at origin = tank_capacity × num_vehicles
""")

print("\nFrom lines 3635-3682 (constraint_soc_track - TRACKING):")
print("""
  # For each subsequent node along path
  spec_cons = tv.spec_cons[g-g_init+1]
  energy_consumed_per_vehicle = distance_increment * spec_cons

  num_vehicles = (
      path.length / (tv.W[g-g_init+1] * tv.AnnualRange[g-g_init+1])
  ) * 1000 * model[:f][y, (p.id, r.id, path.id), (tv.vehicle_type.mode.id, tv.id), g]

  charging_sum = sum(
      model[:s][y, (p.id, r.id, path.id, geo_curr.id), tv.id, f_l, g] * 1000
      for f_l in f_l_pairs if tv.technology.fuel.id == f_l[1]
  )

  @constraint(
      model,
      model[:soc][y, (p.id, r.id, path.id, geo_curr.id), tv.id, g] ==
      model[:soc][y, (p.id, r.id, path.id, geo_prev.id), tv.id, g]
      - energy_consumed_per_vehicle * num_vehicles
      + charging_sum
  )

This tracks SOC: soc[i] = soc[i-1] - consumption + charging
""")

print("\n" + "="*80)
print("THE FUNDAMENTAL PROBLEM")
print("="*80 + "\n")

print("""
The constraint uses the SAME 'num_vehicles' value at every node:
  num_vehicles = (path_length / (W × AnnualRange)) × 1000 × flow

This represents the TOTAL ANNUAL FLEET SIZE for the entire route.

But then the tracking constraint applies this to EACH SEGMENT:
  consumption_at_segment = energy_per_vehicle × num_vehicles

ISSUE: If there are N segments in the path, and we consume
  'energy_per_vehicle × num_vehicles' at each segment,

  total_consumption = sum over all N segments of (energy_per_vehicle × num_vehicles)

This effectively multiplies the fleet size by the number of segments!

EXAMPLE with actual numbers from path 1129:
- Path has 9 nodes (8 segments)
- Total length: ~1029 km
- Each segment: ~128 km average
- num_vehicles: ~43,300 vehicles (annual fleet)
- Energy per vehicle per segment: ~219 kWh

At EACH of the 8 segments:
  consumption = 219 kWh × 43,300 vehicles = 9,483,000 kWh

Total consumption over all 8 segments:
  = 8 × 9,483,000 = 75,864,000 kWh

But if we calculate it correctly (total distance × fleet):
  = 1029 km × 1.714 kWh/km × 43,300 vehicles
  = ~76,352,700 kWh

The ratio should be 1.0, but due to rounding in segment divisions,
it's close.

HOWEVER - The constraint does NOT track this correctly!

The SOC starts at: tank_capacity × num_vehicles = 664 kWh × 43,300 = 28,755,200 kWh

Then at EACH node it subtracts: energy_per_vehicle × num_vehicles

But because charging is MINIMAL (only 4 GWh total), and consumption
per segment is ~9.5 GWh × 8 segments = ~76 GWh, the SOC should DROP.

Instead, we observe SOC INCREASES from 28.8 GWh to 3,829.9 GWh!

This suggests the CONSTRAINT FORMULA ITSELF has an error, OR the
interpretation of what num_vehicles represents in the tracking
vs origin constraint is inconsistent.
""")

print("\n" + "="*80)
print("HYPOTHESIS")
print("="*80 + "\n")

print("""
HYPOTHESIS 1: The num_vehicles formula is WRONG for segment tracking.

For the ORIGIN constraint:
  num_vehicles should represent the simultaneous fleet at the origin

For the TRACKING constraint:
  num_vehicles might need to represent vehicles passing through each segment

These could be DIFFERENT values if vehicles don't all travel together!

HYPOTHESIS 2: There's a SIGN ERROR in the consumption term.

The constraint has:
  soc[i] = soc[i-1] - consumption + charging

But maybe it should be:
  soc[i] = soc[i-1] + consumption - charging
  (though this seems backwards)

OR:
  The consumption calculation itself is inverted somehow

HYPOTHESIS 3: The data interpretation is wrong.

Maybe the results we're reading don't match what the constraint calculates,
due to some post-processing or unit conversion issue.

NEXT STEPS:
1. Manually calculate what SOC SHOULD be at each node using the constraint formula
2. Compare with actual SOC values from results
3. Identify where the discrepancy occurs
4. Check if this happens in ALL cases or just some
""")

print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80 + "\n")

print("Next: Run detailed node-by-node trace to verify calculations")
