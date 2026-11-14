"""
Detailed node-by-node trace of SOC calculation for path 1129
to identify the exact error in constraint_soc_track logic
"""

import yaml
import os

# Configuration
case_name = "case_20251110_160646_reverse"
result_timestamp = "case_20251110_160646_reverse_cs_2025-11-16_16-48-22"
base_path = f"C:/Users/simuser/Documents/AntoniaGolab/Scand_Med_analysis/SM_baby_2/iDesignRES_transcompmodel/examples/moving_loads_SM"
input_dir = f"{base_path}/input_data/{case_name}"
results_dir = f"{base_path}/results/{case_name}"
# Results are stored directly in results_dir, not in a subdirectory
result_path = results_dir

print(f"Analyzing: {result_timestamp}\n")

# Load input data
print("Loading input data...")
with open(f"{input_dir}/TechVehicle.yaml", 'r') as f:
    techvehicles = yaml.safe_load(f)
with open(f"{input_dir}/Path.yaml", 'r') as f:
    paths = yaml.safe_load(f)

# Load results
print("Loading results...")
with open(f"{result_path}/{result_timestamp}_soc_dict.yaml", 'r') as f:
    soc_dict = yaml.safe_load(f)
with open(f"{result_path}/{result_timestamp}_s_dict.yaml", 'r') as f:
    s_dict = yaml.safe_load(f)
with open(f"{result_path}/{result_timestamp}_f_dict.yaml", 'r') as f:
    f_dict = yaml.safe_load(f)

# Target analysis
year = 2056
path_id = 1129
product_id = 1
region_id = 0
tv_id = 1  # BEV
generation = 2056

print("\n" + "="*80)
print("DETAILED SOC TRACKING ANALYSIS - Path 1129")
print("="*80)

# Get path info
path_info = next(p for p in paths if p['id'] == path_id)
sequence = path_info['sequence']
path_length = path_info['length']

print(f"\nPath {path_id}:")
print(f"  Total length: {path_length} km")
print(f"  Number of nodes: {len(sequence)}")
print(f"  Sequence: {sequence}")

# Get TechVehicle info
tv_info = next(tv for tv in techvehicles if tv['id'] == tv_id)
g_init = 2020
g_index = generation - g_init  # 2056 - 2020 = 36

W = tv_info['W'][g_index]
spec_cons = tv_info['spec_cons'][g_index]
tank_capacity = tv_info['tank_capacity'][g_index]
annual_range = tv_info['AnnualRange'][g_index]

print(f"\nBEV (id={tv_id}), Generation {generation}:")
print(f"  W (load factor): {W} tonnes/vehicle")
print(f"  Specific consumption: {spec_cons} kWh/km")
print(f"  Tank capacity: {tank_capacity} kWh")
print(f"  Annual range: {annual_range} km/year")

# Get flow
flow_key = f"[{year}, ({product_id}, {region_id}, {path_id}), (1, {tv_id}), {generation}]"
flow_tonnes = f_dict.get(flow_key, 0)

print(f"\nFlow: {flow_tonnes:,.2f} tonnes/year")

# Calculate num_vehicles (as per constraint)
num_vehicles = (path_length / (W * annual_range)) * 1000 * flow_tonnes

print(f"\nnum_vehicles calculation:")
print(f"  = (path_length / (W × AnnualRange)) × 1000 × flow")
print(f"  = ({path_length} / ({W} × {annual_range})) × 1000 × {flow_tonnes}")
print(f"  = {num_vehicles:,.2f} vehicles")

print(f"\nInitial SOC (at origin):")
print(f"  SOC_origin = tank_capacity × num_vehicles")
print(f"  = {tank_capacity} × {num_vehicles:,.2f}")
initial_soc = tank_capacity * num_vehicles
print(f"  = {initial_soc:,.2f} kWh")

# Verify with actual value
origin_geo = sequence[0]
soc_key_origin = f"[{year}, ({product_id}, {region_id}, {path_id}, {origin_geo}), {tv_id}, {generation}]"
actual_soc_origin = soc_dict.get(soc_key_origin, 0)
print(f"\n  Actual SOC from results: {actual_soc_origin:,.2f} kWh")
print(f"  Difference: {abs(initial_soc - actual_soc_origin):,.2f} kWh")

print("\n" + "="*80)
print("NODE-BY-NODE SOC TRACKING")
print("="*80)

# Calculate distance increments
distances = [0]  # Start at 0
cumulative_dist = 0
for i in range(1, len(sequence)):
    # In the constraint, distance_increment is calculated from edge lengths
    # For now, approximate as uniform distribution
    segment_length = path_length / (len(sequence) - 1)
    cumulative_dist += segment_length
    distances.append(cumulative_dist)

print(f"\nNote: Using uniform distance distribution ({path_length/(len(sequence)-1):.2f} km per segment)")
print(f"(Actual implementation uses edge.length from network)\n")

# Track SOC node by node
soc_calculated = initial_soc
total_consumption_calculated = 0
total_charging_calculated = 0

for i, geo_id in enumerate(sequence):
    soc_key = f"[{year}, ({product_id}, {region_id}, {path_id}, {geo_id}), {tv_id}, {generation}]"
    actual_soc = soc_dict.get(soc_key, 0)

    # Get charging at this node
    charging_at_node = 0
    for fuel_id in range(1, 10):  # Check all fuel types
        for infr_id in range(1, 10):  # Check all infrastructure types
            s_key = f"[{year}, ({product_id}, {region_id}, {path_id}, {geo_id}), {tv_id}, ({fuel_id}, {infr_id}), {generation}]"
            if s_key in s_dict:
                charging_at_node += s_dict[s_key] * 1000  # Convert MWh to kWh

    if i == 0:
        # Origin node
        print(f"Node {i+1}/{len(sequence)} - Geo {geo_id} (ORIGIN)")
        print(f"  Distance from start: {distances[i]:.2f} km")
        print(f"  SOC calculated: {soc_calculated:,.2f} kWh")
        print(f"  SOC actual: {actual_soc:,.2f} kWh")
        print(f"  Charging: {charging_at_node:,.2f} kWh")
        print()
    else:
        # Calculate what happened since previous node
        geo_prev = sequence[i-1]
        distance_increment = distances[i] - distances[i-1]

        # Energy consumed per vehicle on this segment
        energy_per_vehicle = distance_increment * spec_cons

        # Total consumption for the fleet
        segment_consumption = energy_per_vehicle * num_vehicles

        # Update calculated SOC
        soc_prev_calculated = soc_calculated
        soc_calculated = soc_prev_calculated - segment_consumption + charging_at_node

        total_consumption_calculated += segment_consumption
        total_charging_calculated += charging_at_node

        print(f"Node {i+1}/{len(sequence)} - Geo {geo_id}")
        print(f"  Distance from start: {distances[i]:.2f} km")
        print(f"  Segment length: {distance_increment:.2f} km")
        print(f"  Energy per vehicle: {energy_per_vehicle:.4f} kWh")
        print(f"  Fleet consumption: {segment_consumption:,.2f} kWh")
        print(f"  Charging at node: {charging_at_node:,.2f} kWh")
        print(f"  SOC before segment: {soc_prev_calculated:,.2f} kWh")
        print(f"  SOC after (calculated): {soc_calculated:,.2f} kWh")
        print(f"  SOC actual: {actual_soc:,.2f} kWh")
        print(f"  Difference: {abs(soc_calculated - actual_soc):,.2f} kWh")
        print()

print("="*80)
print("SUMMARY")
print("="*80)
print(f"Initial SOC: {initial_soc:,.2f} kWh")
print(f"Final SOC (calculated): {soc_calculated:,.2f} kWh")

dest_geo = sequence[-1]
soc_key_dest = f"[{year}, ({product_id}, {region_id}, {path_id}, {dest_geo}), {tv_id}, {generation}]"
actual_soc_dest = soc_dict.get(soc_key_dest, 0)
print(f"Final SOC (actual): {actual_soc_dest:,.2f} kWh")

print(f"\nTotal consumption: {total_consumption_calculated:,.2f} kWh")
print(f"Total charging: {total_charging_calculated:,.2f} kWh")
print(f"Net change: {total_charging_calculated - total_consumption_calculated:,.2f} kWh")
print(f"SOC change: {actual_soc_dest - actual_soc_origin:,.2f} kWh")

print("\n" + "="*80)
print("DIAGNOSTIC: THE FUNDAMENTAL ISSUE")
print("="*80)

print(f"""
The constraint uses:
  num_vehicles = {num_vehicles:,.2f}

This represents the TOTAL ANNUAL FLEET SIZE needed to maintain the annual flow
of {flow_tonnes:,.2f} tonnes on a {path_length} km route.

At each segment, the constraint calculates:
  consumption = distance_increment × spec_cons × num_vehicles

This assumes ALL {num_vehicles:,.2f} vehicles consume energy on EVERY segment.

BUT: If this is the annual fleet size, then:
  - These vehicles don't all travel together
  - Each segment shouldn't see all {num_vehicles:,.2f} vehicles

QUESTION: What should num_vehicles represent for segment-level tracking?

Option 1: Number of vehicles simultaneously on the route at any instant
Option 2: Number of vehicles that pass through each segment annually
Option 3: Something else?

Current formulation appears to multiply the annual fleet size by the number
of segments, causing SOC to grow instead of shrink.
""")

print(f"\nExpected total consumption for route:")
print(f"  If one vehicle travels the full route: {path_length * spec_cons:.2f} kWh")
print(f"  For annual flow: {path_length * spec_cons * num_vehicles:,.2f} kWh")
print(f"\nActual consumption calculated (segment sum): {total_consumption_calculated:,.2f} kWh")
print(f"Ratio: {total_consumption_calculated / (path_length * spec_cons * num_vehicles):.2f}x")
print(f"\nThis ratio should be 1.0 if the logic is correct.")
