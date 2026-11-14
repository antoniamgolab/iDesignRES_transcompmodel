"""
Analyze SOC tracking consistency for a selected BEV route.
"""
import yaml
import ast
import os
from collections import defaultdict

# Load scenario 000 results - use a specific timestamp
scenario_dir = 'results/uncertainty_analysis/scenario_000'
prefix = 'scenario_000_2025-12-12_18-51-06'

print('Loading results...')
with open(f'{scenario_dir}/{prefix}_f_dict.yaml', 'r') as f:
    f_dict = yaml.safe_load(f)
with open(f'{scenario_dir}/{prefix}_s_dict.yaml', 'r') as f:
    s_dict = yaml.safe_load(f)
with open(f'{scenario_dir}/{prefix}_soc_dict.yaml', 'r') as f:
    soc_dict = yaml.safe_load(f)

# Load input data
input_path = 'input_data/uncertainty_scenarios/scenario_000'
with open(f'{input_path}/TechVehicle.yaml', 'r') as f:
    tech_vehicles = yaml.safe_load(f)
with open(f'{input_path}/Path.yaml', 'r') as f:
    paths = yaml.safe_load(f)
with open(f'{input_path}/Model.yaml', 'r') as f:
    model_params = yaml.safe_load(f)

# Get model parameters
y_init = model_params['y_init']
pre_y = model_params.get('pre_y', 12)
g_init = y_init - pre_y

# Get BEV tech vehicle params
bev_tv = next(tv for tv in tech_vehicles if tv['id'] == 1)

# Find routes with BEV flow in year 2040, gen 2032
year = 2040
gen = 2032
tv_bev = 1

print(f'\nSearching for routes with BEV flow in year {year}, gen {gen}...')

# Get all paths with BEV flow
bev_routes = []
for key_str, val_str in f_dict.items():
    key = ast.literal_eval(key_str)
    if key[0] == year and key[2][1] == tv_bev and key[3] == gen:
        f_val = float(val_str)
        if f_val > 0.1:  # Significant flow
            path_id = key[1][2]
            odpair = key[1][0]
            mode = key[1][1]
            bev_routes.append({
                'path_id': path_id,
                'f': f_val,
                'odpair': odpair,
                'mode': mode,
                'key': key
            })

bev_routes.sort(key=lambda x: -x['f'])
print(f'Found {len(bev_routes)} routes with BEV flow > 0.1 tkm')

if bev_routes:
    # Pick the top route with BEV flow
    route = bev_routes[0]
    path_id = route['path_id']
    f_val = route['f']
    odpair = route['odpair']
    mode = route['mode']

    print(f'\nAnalyzing top BEV route:')
    print(f'  Path ID: {path_id}')
    print(f'  OD pair: {odpair}')
    print(f'  Mode: {mode}')
    print(f'  Flow (f): {f_val:.4f} tkm')

    # Get path details
    path = next((p for p in paths if p['id'] == path_id), None)
    if path:
        sequence = path['sequence']
        distance_from_prev = path['distance_from_previous']
        path_length = path['length']

        print(f'  Path length: {path_length:.2f} km')
        print(f'  Sequence length: {len(sequence)} nodes')

        # Get BEV params for gen 2032
        gen_idx = gen - g_init
        spec_cons = bev_tv['spec_cons'][gen_idx]
        W = bev_tv['W'][gen_idx]
        AR = bev_tv['AnnualRange'][gen_idx]
        tank_capacity = bev_tv['tank_capacity'][gen_idx]

        print(f'\nBEV Gen {gen} parameters:')
        print(f'  spec_cons = {spec_cons:.4f} kWh/km')
        print(f'  W (payload) = {W:.2f} tonnes')
        print(f'  AnnualRange = {AR:.0f} km')
        print(f'  tank_capacity (battery) = {tank_capacity:.0f} kWh')

        # Calculate num_vehicles
        num_vehicles = (path_length / (W * AR)) * 1000 * f_val
        print(f'  num_vehicles = {num_vehicles:.6f}')

        # Initial SOC = tank_capacity * num_vehicles
        initial_soc = tank_capacity * num_vehicles
        final_soc_constraint = 0.5 * tank_capacity * num_vehicles

        print(f'\nSOC constraints:')
        print(f'  Initial SOC (full tank): {initial_soc:.4f} kWh')
        print(f'  Final SOC minimum (50%): {final_soc_constraint:.4f} kWh')
        print(f'  Available battery depletion: {initial_soc - final_soc_constraint:.4f} kWh')

        # Total energy needed for the route
        total_energy_needed = path_length * spec_cons * num_vehicles
        print(f'\nEnergy calculation:')
        print(f'  Total energy needed: {total_energy_needed:.4f} kWh')
        print(f'  = {path_length:.2f} km * {spec_cons:.4f} kWh/km * {num_vehicles:.6f} vehicles')

        # Required charging
        required_charging = total_energy_needed - (initial_soc - final_soc_constraint)
        print(f'  Required charging: {required_charging:.4f} kWh')
        print(f'  = {total_energy_needed:.4f} - ({initial_soc:.4f} - {final_soc_constraint:.4f})')

        # Find SOC values for this route
        print(f'\n=== SOC VALUES FROM MODEL ===')

        # Collect all SOC values for this path
        soc_by_node = {}
        for key_str, val_str in soc_dict.items():
            key = ast.literal_eval(key_str)
            # key format: (year, (odpair, mode, path_id, geo_id), tv_id, gen)
            if key[0] == year and key[3] == gen and key[2] == tv_bev:
                if len(key[1]) >= 4 and key[1][2] == path_id:
                    geo_id = key[1][3]
                    soc_by_node[geo_id] = float(val_str)

        print(f'Found SOC values at {len(soc_by_node)} nodes')
        if sequence[0] in soc_by_node:
            print(f'  First node (geo {sequence[0]}): SOC = {soc_by_node[sequence[0]]:.4f} kWh')
        if sequence[-1] in soc_by_node:
            print(f'  Last node (geo {sequence[-1]}): SOC = {soc_by_node[sequence[-1]]:.4f} kWh')

        # Find total charging (s) for this route
        print(f'\n=== CHARGING VALUES FROM MODEL ===')
        total_charged = 0
        charging_by_node = {}

        for key_str, val_str in s_dict.items():
            key = ast.literal_eval(key_str)
            if key[0] == year and key[2] == tv_bev and key[3] == gen:
                # key[1] could be (odpair, mode, path_id, geo_id)
                if len(key[1]) >= 4 and key[1][2] == path_id:
                    geo_id = key[1][3]
                    s_val = float(val_str) * 1000  # MWh to kWh
                    total_charged += s_val
                    if s_val > 0.001:
                        charging_by_node[geo_id] = s_val

        print(f'  Total energy charged (s): {total_charged:.4f} kWh = {total_charged/1000:.6f} MWh')

        if charging_by_node:
            print(f'  Charging at nodes:')
            for geo, s_val in sorted(charging_by_node.items()):
                print(f'    geo {geo}: {s_val:.4f} kWh')
        else:
            print(f'  No charging found!')

        # Node-by-node tracking
        print(f'\n=== NODE-BY-NODE SOC TRACKING ===')
        print(f'{"Node":<8} {"Dist":<10} {"SOC_model":<12} {"SOC_calc":<12} {"Energy_cons":<12} {"s_charged":<12}')
        print('=' * 80)

        cumulative_distance = 0
        calculated_soc = initial_soc
        total_consumed = 0
        s_total = 0

        for i, geo_id in enumerate(sequence[:15]):  # Show first 15 nodes
            # Distance
            if i == 0:
                dist = 0
            else:
                dist = distance_from_prev[i]
                cumulative_distance += dist

            # Energy consumed
            energy_consumed = dist * spec_cons * num_vehicles
            total_consumed += energy_consumed

            # Charging at this node
            s_val = charging_by_node.get(geo_id, 0)
            s_total += s_val

            # Update calculated SOC (after arriving at node, before charging)
            if i > 0:
                calculated_soc = calculated_soc - energy_consumed

            # Model SOC
            model_soc = soc_by_node.get(geo_id, None)

            # Then add charging
            calculated_soc_after_charging = calculated_soc + s_val

            model_str = f'{model_soc:.2f}' if model_soc is not None else 'N/A'
            print(f'{geo_id:<8} {cumulative_distance:<10.1f} {model_str:<12} {calculated_soc_after_charging:<12.2f} {energy_consumed:<12.2f} {s_val:<12.2f}')

            calculated_soc = calculated_soc_after_charging

        if len(sequence) > 15:
            print(f'... ({len(sequence) - 15} more nodes)')

        print('=' * 80)

        # Verification
        print(f'\n=== VERIFICATION ===')
        print(f'  Total energy needed for route: {total_energy_needed:.4f} kWh')
        print(f'  Available from battery (50% use): {initial_soc - final_soc_constraint:.4f} kWh')
        print(f'  Required charging: {required_charging:.4f} kWh')
        print(f'  Actual charging (s): {total_charged:.4f} kWh')

        if required_charging > 0:
            ratio = total_charged / required_charging
            print(f'  Ratio (actual/required): {ratio:.4f}')
            if abs(ratio - 1.0) < 0.01:
                print(f'  RESULT: SOC tracking is CONSISTENT!')
            else:
                print(f'  RESULT: Discrepancy found - ratio is {ratio:.4f}')
        elif required_charging <= 0:
            print(f'  Battery capacity sufficient - no charging required')
            if total_charged < 0.001:
                print(f'  RESULT: SOC tracking is CONSISTENT (no charging needed or used)')
            else:
                print(f'  RESULT: Model charged {total_charged:.4f} kWh despite sufficient battery capacity')
else:
    print('No BEV routes found!')
