"""
Verify SOC tracking constraint satisfaction across all 5 November 16 runs.

For each run, this script:
1. Identifies paths with significant BEV flow
2. Recalculates SOC node-by-node using actual s and f values
3. Compares calculated vs actual SOC to verify constraint satisfaction
4. Checks if charging exceeds what's needed (overcharging)
5. Reports violations and summary statistics
"""

import yaml
import re
from collections import defaultdict

# Configuration
base_path = "C:/Users/simuser/Documents/AntoniaGolab/Scand_Med_analysis/SM_baby_2/iDesignRES_transcompmodel/examples/moving_loads_SM"

runs = [
    {
        'name': 'var_var',
        'case': 'case_20251110_160304_var_var',
        'timestamp': 'case_20251110_160304_var_var_cs_2025-11-16_17-02-00'
    },
    {
        'name': 'var_uni',
        'case': 'case_20251110_160335_var_uni',
        'timestamp': 'case_20251110_160335_var_uni_cs_2025-11-16_17-15-38'
    },
    {
        'name': 'uni_var',
        'case': 'case_20251110_160526_uni_var',
        'timestamp': 'case_20251110_160526_uni_var_cs_2025-11-16_17-28-55'
    },
    {
        'name': 'uni_uni',
        'case': 'case_20251110_160604_uni_uni',
        'timestamp': 'case_20251110_160604_uni_uni_cs_2025-11-16_17-43-19'
    },
    {
        'name': 'reverse',
        'case': 'case_20251110_160646_reverse',
        'timestamp': 'case_20251110_160646_reverse_cs_2025-11-16_16-48-22'
    }
]

# Parameters
g_init = 2020
target_year = 2056  # Check year 2056 as representative year
tv_id = 1  # BEV
min_flow_threshold = 10.0  # Only check paths with significant flow (tonnes/year)

def parse_f_key(key_str):
    """Parse f_dict key string to extract components."""
    # November 16 format uses parentheses: "(year, (product, odpair, path), (mode, techvehicle), generation)"
    pattern = r'\((\d+),\s*\((\d+),\s*(\d+),\s*(\d+)\),\s*\((\d+),\s*(\d+)\),\s*(\d+)\)'
    match = re.match(pattern, key_str)
    if match:
        return {
            'year': int(match.group(1)),
            'product': int(match.group(2)),
            'odpair': int(match.group(3)),
            'path': int(match.group(4)),
            'mode': int(match.group(5)),
            'techvehicle': int(match.group(6)),
            'generation': int(match.group(7))
        }
    return None

def analyze_run(run_info):
    """Analyze SOC tracking for a single run."""
    print(f"\n{'='*100}")
    print(f"ANALYZING RUN: {run_info['name']} ({run_info['timestamp']})")
    print(f"{'='*100}\n")

    case_name = run_info['case']
    result_timestamp = run_info['timestamp']
    input_dir = f"{base_path}/input_data/{case_name}"
    results_dir = f"{base_path}/results/{case_name}"

    # Load input data
    print("Loading input data...")
    try:
        with open(f"{input_dir}/TechVehicle.yaml", 'r') as f:
            techvehicles = yaml.safe_load(f)
        with open(f"{input_dir}/Path.yaml", 'r') as f:
            paths = yaml.safe_load(f)
    except FileNotFoundError as e:
        print(f"ERROR: Could not find input files: {e}")
        return None

    # Load results
    print("Loading results...")
    try:
        with open(f"{results_dir}/{result_timestamp}_f_dict.yaml", 'r') as f:
            f_dict = yaml.safe_load(f)
        with open(f"{results_dir}/{result_timestamp}_soc_dict.yaml", 'r') as f:
            soc_dict = yaml.safe_load(f)
        with open(f"{results_dir}/{result_timestamp}_s_dict.yaml", 'r') as f:
            s_dict = yaml.safe_load(f)
    except FileNotFoundError as e:
        print(f"ERROR: Could not find result files: {e}")
        return None

    print(f"Loaded {len(f_dict):,} flow entries, {len(soc_dict):,} SOC entries, {len(s_dict):,} charging entries\n")

    # Find paths with significant BEV flow in target year
    print(f"Identifying paths with significant BEV flow in year {target_year}...")
    bev_flows = defaultdict(float)

    for key_str, value in f_dict.items():
        parsed = parse_f_key(key_str)
        if parsed and parsed['year'] == target_year and parsed['techvehicle'] == tv_id:
            path_id = parsed['path']
            bev_flows[path_id] += float(value) if isinstance(value, str) else value

    # Filter paths with significant flow
    significant_paths = [(path_id, flow) for path_id, flow in bev_flows.items() if flow >= min_flow_threshold]
    significant_paths.sort(key=lambda x: x[1], reverse=True)

    print(f"Found {len(significant_paths)} paths with BEV flow >= {min_flow_threshold} tonnes/year")

    if not significant_paths:
        print("No paths with significant BEV flow found!")
        return {
            'run': run_info['name'],
            'paths_checked': 0,
            'violations': [],
            'overcharging_cases': []
        }

    print(f"Top 5 paths by flow: {significant_paths[:5]}\n")

    # Get BEV parameters for target year
    tv_info = next(tv for tv in techvehicles if tv['id'] == tv_id)
    g_index = target_year - g_init
    W = tv_info['W'][g_index]
    spec_cons = tv_info['spec_cons'][g_index]
    tank_capacity = tv_info['tank_capacity'][g_index]
    annual_range = tv_info['AnnualRange'][g_index]

    print(f"BEV Parameters (Year {target_year}):")
    print(f"  W: {W} t/vehicle, spec_cons: {spec_cons} kWh/km")
    print(f"  tank_capacity: {tank_capacity} kWh, annual_range: {annual_range} km/year\n")

    # Check SOC tracking for top paths (limit to 10 to avoid excessive computation)
    max_paths_to_check = 10
    paths_to_check = significant_paths[:max_paths_to_check]

    print(f"{'='*100}")
    print(f"CHECKING SOC TRACKING FOR {len(paths_to_check)} PATHS")
    print(f"{'='*100}\n")

    violations = []
    overcharging_cases = []

    for path_id, total_flow in paths_to_check:
        # Get path info
        try:
            path_info = next(p for p in paths if p['id'] == path_id)
        except StopIteration:
            print(f"WARNING: Path {path_id} not found in Path.yaml, skipping")
            continue

        sequence = path_info['sequence']
        path_length = path_info['length']
        distances_from_prev = path_info['distance_from_previous']

        print(f"\n{'-'*100}")
        print(f"Path {path_id}: {path_length:.2f} km, {len(sequence)} nodes, {total_flow:.2f} tonnes/year BEV")
        print(f"{'-'*100}")

        # Find which OD pair uses this path with BEV flow
        path_flow_found = False
        for key_str, value in f_dict.items():
            parsed = parse_f_key(key_str)
            if (parsed and parsed['year'] == target_year and
                parsed['path'] == path_id and parsed['techvehicle'] == tv_id):

                flow_val = float(value) if isinstance(value, str) else value
                if flow_val >= min_flow_threshold:
                    product_id = parsed['product']
                    region_id = parsed['odpair']
                    generation = parsed['generation']
                    flow_tonnes = flow_val
                    path_flow_found = True
                    break

        if not path_flow_found:
            print(f"  WARNING: Could not find flow entry for path {path_id}")
            continue

        # Calculate num_vehicles
        num_vehicles = (path_length / (W * annual_range)) * 1000 * flow_tonnes

        # Initial SOC at origin
        initial_soc = tank_capacity * num_vehicles

        # Track SOC node by node
        soc_calculated = initial_soc
        total_consumption = 0
        total_charging = 0
        max_soc_violation = 0

        for i, geo_id in enumerate(sequence):
            # Get actual SOC from results
            soc_key = f"[{target_year}, ({product_id}, {region_id}, {path_id}, {geo_id}), {tv_id}, {generation}]"
            actual_soc = soc_dict.get(soc_key, 0)

            # Get charging at this node
            charging_at_node = 0
            for fuel_id in range(1, 10):
                for infr_id in range(1, 10):
                    s_key = f"[{target_year}, ({product_id}, {region_id}, {path_id}, {geo_id}), {tv_id}, ({fuel_id}, {infr_id}), {generation}]"
                    if s_key in s_dict:
                        charging_at_node += s_dict[s_key] * 1000  # MWh to kWh

            if i == 0:
                # Origin node
                if charging_at_node > 0:
                    soc_calculated += charging_at_node
                    total_charging += charging_at_node
            else:
                # Tracking constraint
                distance_increment = distances_from_prev[i]
                energy_per_vehicle = distance_increment * spec_cons
                segment_consumption = energy_per_vehicle * num_vehicles

                soc_prev = soc_calculated
                soc_calculated = soc_prev - segment_consumption + charging_at_node

                total_consumption += segment_consumption
                total_charging += charging_at_node

            # Check violation
            soc_diff = abs(soc_calculated - actual_soc)
            if soc_diff > 1e-3:  # 1 Wh tolerance
                max_soc_violation = max(max_soc_violation, soc_diff)

        # Final SOC
        dest_geo = sequence[-1]
        soc_key_dest = f"[{target_year}, ({product_id}, {region_id}, {path_id}, {dest_geo}), {tv_id}, {generation}]"
        actual_soc_dest = soc_dict.get(soc_key_dest, 0)

        # Check if constraint is satisfied
        final_soc_diff = abs(soc_calculated - actual_soc_dest)

        print(f"  Initial SOC: {initial_soc/1e6:.4f} GWh")
        print(f"  Final SOC (calculated): {soc_calculated/1e6:.4f} GWh")
        print(f"  Final SOC (actual): {actual_soc_dest/1e6:.4f} GWh")
        print(f"  Total consumption: {total_consumption/1e6:.4f} GWh")
        print(f"  Total charging: {total_charging/1e6:.4f} GWh")
        print(f"  Net SOC change: {(soc_calculated - initial_soc)/1e6:.4f} GWh")
        print(f"  Max node violation: {max_soc_violation/1e6:.6f} GWh")
        print(f"  Final violation: {final_soc_diff/1e6:.6f} GWh")

        if final_soc_diff > 1e-3:  # 1 Wh tolerance
            print(f"  *** VIOLATION: Calculated SOC does not match actual!")
            violations.append({
                'path_id': path_id,
                'flow': flow_tonnes,
                'violation': final_soc_diff,
                'initial_soc': initial_soc,
                'final_soc_calc': soc_calculated,
                'final_soc_actual': actual_soc_dest
            })
        else:
            print(f"  OK: SOC tracking constraint satisfied")

        # Check for overcharging
        energy_needed = total_consumption
        if total_charging > energy_needed * 1.01:  # Allow 1% tolerance
            excess_charging = total_charging - energy_needed
            print(f"  *** OVERCHARGING: {excess_charging/1e6:.4f} GWh excess ({(total_charging/energy_needed - 1)*100:.1f}% more than needed)")
            overcharging_cases.append({
                'path_id': path_id,
                'flow': flow_tonnes,
                'consumption': total_consumption,
                'charging': total_charging,
                'excess': excess_charging,
                'excess_pct': (total_charging/energy_needed - 1)*100
            })
        else:
            charging_ratio = total_charging / energy_needed if energy_needed > 0 else 0
            print(f"  OK: Charging {charging_ratio*100:.1f}% of consumption (no overcharging)")

    return {
        'run': run_info['name'],
        'paths_checked': len(paths_to_check),
        'violations': violations,
        'overcharging_cases': overcharging_cases
    }

# Main execution
print(f"\n{'='*100}")
print(f"SOC TRACKING VERIFICATION FOR ALL NOVEMBER 16 RUNS")
print(f"{'='*100}")

all_results = []

for run_info in runs:
    result = analyze_run(run_info)
    if result:
        all_results.append(result)

# Summary across all runs
print(f"\n\n{'='*100}")
print(f"SUMMARY ACROSS ALL RUNS")
print(f"{'='*100}\n")

total_paths_checked = sum(r['paths_checked'] for r in all_results)
total_violations = sum(len(r['violations']) for r in all_results)
total_overcharging = sum(len(r['overcharging_cases']) for r in all_results)

print(f"Total runs analyzed: {len(all_results)}")
print(f"Total paths checked: {total_paths_checked}")
print(f"Total SOC tracking violations: {total_violations}")
print(f"Total overcharging cases: {total_overcharging}\n")

if total_violations > 0:
    print(f"\n{'='*100}")
    print(f"SOC TRACKING VIOLATIONS BY RUN")
    print(f"{'='*100}\n")
    for result in all_results:
        if result['violations']:
            print(f"\n{result['run']}:")
            for v in result['violations']:
                print(f"  Path {v['path_id']}: {v['flow']:.2f} t/year, violation {v['violation']/1e6:.6f} GWh")

if total_overcharging > 0:
    print(f"\n{'='*100}")
    print(f"OVERCHARGING CASES BY RUN")
    print(f"{'='*100}\n")
    for result in all_results:
        if result['overcharging_cases']:
            print(f"\n{result['run']}:")
            for oc in result['overcharging_cases']:
                print(f"  Path {oc['path_id']}: {oc['flow']:.2f} t/year")
                print(f"    Consumption: {oc['consumption']/1e6:.4f} GWh")
                print(f"    Charging: {oc['charging']/1e6:.4f} GWh")
                print(f"    Excess: {oc['excess']/1e6:.4f} GWh ({oc['excess_pct']:.1f}% more than needed)")

if total_violations == 0 and total_overcharging == 0:
    print("\n" + "="*100)
    print("ALL CHECKS PASSED!")
    print("="*100)
    print("\nFindings:")
    print("  - SOC tracking constraint satisfied for all checked paths")
    print("  - No overcharging detected (charging <= consumption + 1%)")
    print("  - Constraint implementation appears correct")

print(f"\n{'='*100}\n")
