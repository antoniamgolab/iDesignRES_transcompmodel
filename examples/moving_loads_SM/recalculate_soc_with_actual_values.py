"""
Recalculate SOC step-by-step using actual s and f values from optimization results.
Apply the exact formulas from constraint_soc_track to verify what the constraint produces.
"""

import yaml
import os

# Configuration
case_name = "case_20251110_160646_reverse"
result_timestamp = "case_20251110_160646_reverse_cs_2025-11-16_16-48-22"
base_path = "C:/Users/simuser/Documents/AntoniaGolab/Scand_Med_analysis/SM_baby_2/iDesignRES_transcompmodel/examples/moving_loads_SM"
input_dir = f"{base_path}/input_data/{case_name}"
results_dir = f"{base_path}/results/{case_name}"

print(f"\n{'='*80}")
print(f"RECALCULATING SOC WITH ACTUAL DECISION VARIABLE VALUES")
print(f"Case: {result_timestamp}")
print(f"{'='*80}\n")

# Load input data
print("Loading input data...")
with open(f"{input_dir}/TechVehicle.yaml", 'r') as f:
    techvehicles = yaml.safe_load(f)
with open(f"{input_dir}/Path.yaml", 'r') as f:
    paths = yaml.safe_load(f)

# Load results
print("Loading results...")
with open(f"{results_dir}/{result_timestamp}_soc_dict.yaml", 'r') as f:
    soc_dict = yaml.safe_load(f)
with open(f"{results_dir}/{result_timestamp}_s_dict.yaml", 'r') as f:
    s_dict = yaml.safe_load(f)
with open(f"{results_dir}/{result_timestamp}_f_dict.yaml", 'r') as f:
    f_dict = yaml.safe_load(f)

# Target analysis
year = 2056
path_id = 1129
product_id = 1
region_id = 0
tv_id = 1  # BEV
generation = 2056

print(f"\n{'='*80}")
print(f"ANALYSIS: Path {path_id}, Year {year}, BEV (id={tv_id}), Generation {generation}")
print(f"{'='*80}\n")

# Get path info
path_info = next(p for p in paths if p['id'] == path_id)
sequence = path_info['sequence']
path_length = path_info['length']
distances_from_prev = path_info['distance_from_previous']

print(f"Path Information:")
print(f"  Total length: {path_length:.2f} km")
print(f"  Number of nodes: {len(sequence)}")
print(f"  Sequence: {sequence}")
print(f"  Distance increments: {[f'{d:.2f}' for d in distances_from_prev]}")

# Get TechVehicle info
tv_info = next(tv for tv in techvehicles if tv['id'] == tv_id)
g_init = 2020
g_index = generation - g_init

W = tv_info['W'][g_index]
spec_cons = tv_info['spec_cons'][g_index]
tank_capacity = tv_info['tank_capacity'][g_index]
annual_range = tv_info['AnnualRange'][g_index]

print(f"\nBEV Parameters (Generation {generation}):")
print(f"  W (load factor): {W} tonnes/vehicle")
print(f"  Specific consumption: {spec_cons} kWh/km")
print(f"  Tank capacity: {tank_capacity} kWh")
print(f"  Annual range: {annual_range} km/year")

# Get flow (f variable)
flow_key = f"[{year}, ({product_id}, {region_id}, {path_id}), (1, {tv_id}), {generation}]"
flow_tonnes = f_dict.get(flow_key, 0)
print(f"\nFlow (f): {flow_tonnes:,.2f} tonnes/year")

# Calculate num_vehicles (as per constraint formula)
num_vehicles = (path_length / (W * annual_range)) * 1000 * flow_tonnes

print(f"\nnum_vehicles (annual fleet size):")
print(f"  = (path_length / (W × AnnualRange)) × 1000 × flow")
print(f"  = ({path_length:.2f} / ({W} × {annual_range})) × 1000 × {flow_tonnes:.2f}")
print(f"  = {num_vehicles:,.2f} vehicles")

# Initial SOC at origin (as per constraint_soc_track origin constraint)
initial_soc = tank_capacity * num_vehicles
print(f"\nInitial SOC at origin (constraint formula):")
print(f"  SOC_origin = tank_capacity × num_vehicles")
print(f"  = {tank_capacity} × {num_vehicles:,.2f}")
print(f"  = {initial_soc:,.2f} kWh = {initial_soc/1e6:.2f} GWh")

# Verify with actual SOC from results
origin_geo = sequence[0]
soc_key_origin = f"[{year}, ({product_id}, {region_id}, {path_id}, {origin_geo}), {tv_id}, {generation}]"
actual_soc_origin = soc_dict.get(soc_key_origin, 0)
print(f"\nActual SOC at origin (from results): {actual_soc_origin:,.2f} kWh = {actual_soc_origin/1e6:.2f} GWh")
if initial_soc > 0:
    print(f"Difference: {abs(initial_soc - actual_soc_origin):,.2f} kWh ({abs(initial_soc - actual_soc_origin)/initial_soc*100:.4f}%)")
else:
    print(f"Difference: {abs(initial_soc - actual_soc_origin):,.2f} kWh")

print(f"\n{'='*80}")
print(f"NODE-BY-NODE SOC CALCULATION (Using Constraint Formula)")
print(f"{'='*80}\n")

# Track SOC node by node using the exact constraint formula
soc_calculated = initial_soc
total_consumption = 0
total_charging = 0

for i, geo_id in enumerate(sequence):
    # Get actual SOC from results
    soc_key = f"[{year}, ({product_id}, {region_id}, {path_id}, {geo_id}), {tv_id}, {generation}]"
    actual_soc = soc_dict.get(soc_key, 0)

    # Get charging at this node (s variable, stored in MWh)
    charging_at_node = 0
    for fuel_id in range(1, 10):  # Check all possible fuel types
        for infr_id in range(1, 10):  # Check all possible infrastructure types
            s_key = f"[{year}, ({product_id}, {region_id}, {path_id}, {geo_id}), {tv_id}, ({fuel_id}, {infr_id}), {generation}]"
            if s_key in s_dict:
                # s is stored in MWh, multiply by 1000 to get kWh (as in constraint)
                charging_at_node += s_dict[s_key] * 1000

    if i == 0:
        # ORIGIN NODE
        print(f"\nNode {i+1}/{len(sequence)} - Geo {geo_id} (ORIGIN)")
        print(f"  {'-'*70}")
        print(f"  SOC (calculated) = {soc_calculated:,.2f} kWh = {soc_calculated/1e6:.2f} GWh")
        print(f"  SOC (actual)     = {actual_soc:,.2f} kWh = {actual_soc/1e6:.2f} GWh")
        print(f"  Charging at node = {charging_at_node:,.2f} kWh = {charging_at_node/1e6:.4f} GWh")
        if charging_at_node > 0:
            # At origin, charging would increase SOC
            soc_calculated += charging_at_node
            total_charging += charging_at_node
    else:
        # TRACKING CONSTRAINT
        # Calculate consumption on segment from previous to current node
        geo_prev = sequence[i-1]
        distance_increment = distances_from_prev[i]

        # Energy consumed per vehicle on this segment
        energy_per_vehicle = distance_increment * spec_cons

        # Total consumption for the fleet (as per constraint formula)
        segment_consumption = energy_per_vehicle * num_vehicles

        # Previous SOC (what we calculated for previous node)
        soc_prev = soc_calculated

        # Apply tracking constraint formula:
        # soc[current] = soc[previous] - energy_consumed_per_vehicle × num_vehicles + charging_sum
        soc_calculated = soc_prev - segment_consumption + charging_at_node

        total_consumption += segment_consumption
        total_charging += charging_at_node

        print(f"\nNode {i+1}/{len(sequence)} - Geo {geo_id}")
        print(f"  {'-'*70}")
        print(f"  Distance from node {i}: {distance_increment:.2f} km")
        print(f"  Energy per vehicle: {energy_per_vehicle:.4f} kWh")
        print(f"  Segment consumption: {segment_consumption:,.2f} kWh = {segment_consumption/1e6:.2f} GWh")
        print(f"  Charging at node: {charging_at_node:,.2f} kWh = {charging_at_node/1e6:.4f} GWh")
        print(f"  ")
        print(f"  Constraint formula:")
        print(f"    SOC[{i+1}] = SOC[{i}] - consumption + charging")
        print(f"    = {soc_prev/1e6:.2f} - {segment_consumption/1e6:.2f} + {charging_at_node/1e6:.4f}")
        print(f"    = {soc_calculated/1e6:.2f} GWh")
        print(f"  ")
        print(f"  SOC (calculated) = {soc_calculated:,.2f} kWh = {soc_calculated/1e6:.2f} GWh")
        print(f"  SOC (actual)     = {actual_soc:,.2f} kWh = {actual_soc/1e6:.2f} GWh")
        print(f"  Difference       = {abs(soc_calculated - actual_soc):,.2f} kWh = {abs(soc_calculated - actual_soc)/1e6:.4f} GWh")

        if abs(soc_calculated - actual_soc) > 1e-6:
            print(f"  ⚠ WARNING: Calculated and actual SOC differ!")

print(f"\n{'='*80}")
print(f"SUMMARY")
print(f"{'='*80}\n")

dest_geo = sequence[-1]
soc_key_dest = f"[{year}, ({product_id}, {region_id}, {path_id}, {dest_geo}), {tv_id}, {generation}]"
actual_soc_dest = soc_dict.get(soc_key_dest, 0)

print(f"Initial SOC (origin):  {initial_soc:,.2f} kWh = {initial_soc/1e6:.2f} GWh")
print(f"Final SOC (calculated): {soc_calculated:,.2f} kWh = {soc_calculated/1e6:.2f} GWh")
print(f"Final SOC (actual):     {actual_soc_dest:,.2f} kWh = {actual_soc_dest/1e6:.2f} GWh")
print(f"\nTotal consumption: {total_consumption:,.2f} kWh = {total_consumption/1e6:.2f} GWh")
print(f"Total charging:    {total_charging:,.2f} kWh = {total_charging/1e6:.4f} GWh")
print(f"Net SOC change:    {(soc_calculated - initial_soc):,.2f} kWh = {(soc_calculated - initial_soc)/1e6:.2f} GWh")
print(f"\nExpected: SOC_final = SOC_initial - consumption + charging")
print(f"        = {initial_soc/1e6:.2f} - {total_consumption/1e6:.2f} + {total_charging/1e6:.4f}")
print(f"        = {(initial_soc - total_consumption + total_charging)/1e6:.2f} GWh")

print(f"\n{'='*80}")
print(f"VERIFICATION")
print(f"{'='*80}\n")

# Check if our calculation matches the constraint logic
expected_total_consumption = path_length * spec_cons * num_vehicles
print(f"Expected total consumption (path_length × spec_cons × num_vehicles):")
print(f"  = {path_length:.2f} × {spec_cons} × {num_vehicles:,.2f}")
print(f"  = {expected_total_consumption:,.2f} kWh = {expected_total_consumption/1e6:.2f} GWh")
print(f"\nActual total consumption (sum of segments): {total_consumption:,.2f} kWh = {total_consumption/1e6:.2f} GWh")
print(f"Difference: {abs(expected_total_consumption - total_consumption):,.2f} kWh")
print(f"Ratio: {total_consumption / expected_total_consumption:.6f}x")

print(f"\n{'='*80}")
print(f"DIAGNOSIS")
print(f"{'='*80}\n")

if abs(soc_calculated - actual_soc_dest) < 1e-6:
    print("✓ Calculated SOC matches actual SOC from results!")
    print("  This confirms the constraint formulas are working as expected.")
    print()
    if soc_calculated > initial_soc:
        print("⚠ ISSUE CONFIRMED: SOC increases along the route!")
        print(f"  SOC increased from {initial_soc/1e6:.2f} GWh to {soc_calculated/1e6:.2f} GWh")
        print(f"  This is physically impossible for a consumption-based process.")
        print()
        print("  Possible explanations:")
        print("  1. Charging > Consumption (model chose to overcharge)")
        print("  2. Sign error in constraint formula")
        print("  3. Misinterpretation of what SOC represents")
else:
    print("✗ Calculated SOC does NOT match actual SOC from results!")
    print(f"  Difference: {abs(soc_calculated - actual_soc_dest)/1e6:.4f} GWh")
    print("  This suggests either:")
    print("  1. The constraint formula is different than expected")
    print("  2. There's an error in how we're reading the results")
    print("  3. Post-processing is applied to SOC values")

print(f"\n{'='*80}")
print(f"ANALYSIS COMPLETE")
print(f"{'='*80}\n")
