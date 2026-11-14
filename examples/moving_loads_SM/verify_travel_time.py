"""
Verify travel time calculation for path 1323 to check consistency with charging and mandatory breaks.
"""

import yaml
import os

# Parameters
PATH_ID = 1323
YEAR = 2040
GEN = 2040
TV_ID = 1  # BEV
SPEED = 80  # km/h
G_INIT = 2020
TIMESTEP = 4

results_dir = "results/uncertainty_analysis/scenario_000"
input_dir = "input_data/uncertainty_scenarios/scenario_000"

# Find the most recent results
prefix = "scenario_000_2025-12-16_10-22-42"

# Load data
print("Loading data...")

# Load path data
with open(f"{input_dir}/Path.yaml", 'r') as f:
    paths = yaml.safe_load(f)
path_data = next(p for p in paths if p['id'] == PATH_ID)

print(f"\n{'='*80}")
print(f"PATH {PATH_ID} DATA:")
print(f"{'='*80}")
print(f"Length: {path_data['length']:.2f} km")
print(f"Sequence: {path_data['sequence']}")
print(f"Distance from previous: {[f'{d:.1f}' for d in path_data['distance_from_previous']]}")

# Load TechVehicle data for BEV
with open(f"{input_dir}/TechVehicle.yaml", 'r') as f:
    techvehicles = yaml.safe_load(f)
bev_data = next(tv for tv in techvehicles if tv['id'] == TV_ID)

# Index calculations
gen_index_yearly = GEN - G_INIT  # 20 for year 2040
gen_index_4yr = (GEN - G_INIT) // TIMESTEP  # 5 for year 2040

print(f"\n{'='*80}")
print(f"BEV PARAMETERS:")
print(f"{'='*80}")
print(f"W array length: {len(bev_data['W'])}")
print(f"peak_fueling array length: {len(bev_data['peak_fueling'])}")
print(f"AnnualRange: {bev_data['AnnualRange'][0]} km")

# Get values
W = bev_data['W'][gen_index_4yr]
AnnualRange = bev_data['AnnualRange'][gen_index_4yr]
peak_fueling_4yr = bev_data['peak_fueling'][gen_index_4yr]
peak_fueling_yearly = bev_data['peak_fueling'][gen_index_yearly] if gen_index_yearly < len(bev_data['peak_fueling']) else bev_data['peak_fueling'][-1]

print(f"\nFor generation {GEN}:")
print(f"  4yr index: {gen_index_4yr}, yearly index: {gen_index_yearly}")
print(f"  W: {W:.4f} tonnes")
print(f"  AnnualRange: {AnnualRange} km")
print(f"  peak_fueling[4yr]: {peak_fueling_4yr:.2f} kW")
print(f"  peak_fueling[yearly]: {peak_fueling_yearly:.2f} kW")

# Load f values
with open(f"{results_dir}/{prefix}_f_dict.yaml", 'r') as f:
    f_dict = yaml.safe_load(f)

f_value = 0.503564
for key, val in f_dict.items():
    key_str = str(key)
    if "(2040, (0, 1323, 1323), (1, 1), 2040)" in key_str:
        f_value = float(val)
        print(f"\nFound f value: {f_value}")
        break

# Calculate number of vehicles
num_vehicles = (path_data['length'] / (W * AnnualRange)) * 1000 * f_value
print(f"\nNum vehicles = ({path_data['length']:.2f} / ({W:.4f} * {AnnualRange})) * 1000 * {f_value:.6f}")
print(f"            = {num_vehicles:.6f}")

# Load travel_time, s, extra_break_time
with open(f"{results_dir}/{prefix}_travel_time_dict.yaml", 'r') as f:
    travel_time_dict = yaml.safe_load(f)
with open(f"{results_dir}/{prefix}_s_dict.yaml", 'r') as f:
    s_dict = yaml.safe_load(f)
with open(f"{results_dir}/{prefix}_extra_break_time_dict.yaml", 'r') as f:
    extra_break_dict = yaml.safe_load(f)

# Extract values for path 1323, year 2040, gen 2040, BEV
sequence = path_data['sequence']
distances = path_data['distance_from_previous']

print(f"\n{'='*80}")
print(f"STEP-BY-STEP TRAVEL TIME TRACE:")
print(f"{'='*80}")

cumul_dist = 0
for i, node_id in enumerate(sequence):
    cumul_dist += distances[i]
    
    # Get travel_time
    tt = None
    for key, val in travel_time_dict.items():
        if f"(2040, (0, 1323, 1323, {node_id}), 1, 2040)" in str(key):
            tt = float(val)
            break
    
    # Get extra_break_time
    eb = 0
    for key, val in extra_break_dict.items():
        if f"(2040, (0, 1323, 1323, {node_id}), 1, 2040)" in str(key):
            eb = float(val)
            break
    
    # Get s (charging) - sum slow and fast
    s_total = 0
    for key, val in s_dict.items():
        key_str = str(key)
        if f"(2040, (0, 1323, 1323, {node_id}), 1, (0," in key_str and ", 2040)" in key_str:
            s_total += float(val)
    
    print(f"\nNode {node_id} (idx {i}):")
    print(f"  Cumulative distance: {cumul_dist:.2f} km")
    print(f"  travel_time: {tt:.6f} hours" if tt is not None else "  travel_time: 0 (origin)")
    print(f"  extra_break_time: {eb:.6f} hours")
    print(f"  s (charging): {s_total*1000:.2f} kWh")
    
    if i > 0:
        edge_dist = distances[i]
        driving_component = (edge_dist / SPEED) * num_vehicles
        charging_time_4yr = (s_total * 1000) / peak_fueling_4yr if peak_fueling_4yr > 0 else 0
        charging_time_yearly = (s_total * 1000) / peak_fueling_yearly if peak_fueling_yearly > 0 else 0
        print(f"  Edge distance: {edge_dist:.2f} km")
        print(f"  Driving component: ({edge_dist}/80)*{num_vehicles:.4f} = {driving_component:.6f} h")
        print(f"  Charging time (4yr): {charging_time_4yr:.6f} h")
        print(f"  Charging time (yearly): {charging_time_yearly:.6f} h")

# Detailed verification for node 58 -> 59
print(f"\n{'='*80}")
print(f"DETAILED VERIFICATION: Node 58 -> Node 59")
print(f"{'='*80}")

tt_58 = tt_59 = eb_59 = s_59 = None
for key, val in travel_time_dict.items():
    if "(2040, (0, 1323, 1323, 58), 1, 2040)" in str(key):
        tt_58 = float(val)
    if "(2040, (0, 1323, 1323, 59), 1, 2040)" in str(key):
        tt_59 = float(val)
for key, val in extra_break_dict.items():
    if "(2040, (0, 1323, 1323, 59), 1, 2040)" in str(key):
        eb_59 = float(val)
s_59 = 0
for key, val in s_dict.items():
    if "(2040, (0, 1323, 1323, 59), 1, (0," in str(key) and ", 2040)" in str(key):
        s_59 += float(val)

dist_58_to_59 = distances[9]  # index 9 is node 59
actual_diff = tt_59 - tt_58

driving = (dist_58_to_59 / SPEED) * num_vehicles
charging_4yr = (s_59 * 1000) / peak_fueling_4yr if peak_fueling_4yr > 0 else 0
charging_yearly = (s_59 * 1000) / peak_fueling_yearly if peak_fueling_yearly > 0 else 0

print(f"travel_time[58] = {tt_58:.6f}")
print(f"travel_time[59] = {tt_59:.6f}")
print(f"Actual difference = {actual_diff:.6f}")
print(f"\nExpected components:")
print(f"  Driving: ({dist_58_to_59:.2f}/80)*{num_vehicles:.4f} = {driving:.6f}")
print(f"  Charging (4yr, {peak_fueling_4yr:.1f}kW): {charging_4yr:.6f}")
print(f"  Charging (yearly, {peak_fueling_yearly:.1f}kW): {charging_yearly:.6f}")
print(f"  extra_break: {eb_59:.6f}")

expected_4yr = driving + charging_4yr + eb_59
expected_yearly = driving + charging_yearly + eb_59

print(f"\nExpected total (4yr): {expected_4yr:.6f}")
print(f"Expected total (yearly): {expected_yearly:.6f}")
print(f"Actual: {actual_diff:.6f}")
print(f"\nDiscrepancy (4yr): {actual_diff - expected_4yr:.6f}")
print(f"Discrepancy (yearly): {actual_diff - expected_yearly:.6f}")

# Load mandatory breaks for context
with open(f"{input_dir}/MandatoryBreaks.yaml", 'r') as f:
    mandatory_breaks = yaml.safe_load(f)
breaks_1323 = [b for b in mandatory_breaks if b.get('path_id') == PATH_ID]

print(f"\n{'='*80}")
print(f"MANDATORY BREAKS (path {PATH_ID}):")
print(f"{'='*80}")
for b in breaks_1323:
    twb = b.get('time_with_breaks', 'N/A')
    print(f"Break {b['break_number']} ({b['event_type']}) at node {b['latest_geo_id']}: "
          f"dist={b['cumulative_distance']:.1f}km, driving={b['cumulative_driving_time']:.2f}h, time_with_breaks={twb}")
