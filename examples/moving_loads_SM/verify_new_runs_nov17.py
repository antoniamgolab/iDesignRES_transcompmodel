"""
Verify SOC constraint satisfaction for the November 17 runs (after bug fix).

This script checks that the initial SOC constraint is now properly satisfied
after adding the missing × 1000 factor to the upper bound constraint.
"""

import yaml
import re
from collections import defaultdict

base_path = "C:/Users/simuser/Documents/AntoniaGolab/Scand_Med_analysis/SM_baby_2/iDesignRES_transcompmodel/examples/moving_loads_SM"

runs = [
    {
        'name': 'var_var',
        'case': 'case_20251110_160304_var_var',
        'timestamp': 'case_20251110_160304_var_var_cs_2025-11-17_08-22-40'
    },
    {
        'name': 'var_uni',
        'case': 'case_20251110_160335_var_uni',
        'timestamp': 'case_20251110_160335_var_uni_cs_2025-11-17_08-36-06'
    },
    {
        'name': 'uni_var',
        'case': 'case_20251110_160526_uni_var',
        'timestamp': 'case_20251110_160526_uni_var_cs_2025-11-17_08-49-36'
    },
    {
        'name': 'uni_uni',
        'case': 'case_20251110_160604_uni_uni',
        'timestamp': 'case_20251110_160604_uni_uni_cs_2025-11-17_09-03-48'
    },
    {
        'name': 'reverse',
        'case': 'case_20251110_160646_reverse',
        'timestamp': 'case_20251110_160646_reverse_cs_2025-11-17_08-09-25'
    }
]

# Parameters
g_init = 2020
target_year = 2056
tv_id = 1  # BEV
min_flow_threshold = 10.0

def parse_f_key(key_str):
    """Parse f_dict key string."""
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
    """Analyze initial SOC constraint satisfaction for a single run."""
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
    except FileNotFoundError as e:
        print(f"ERROR: Could not find result files: {e}")
        return None

    print(f"Loaded {len(f_dict):,} flow entries, {len(soc_dict):,} SOC entries\n")

    # Find paths with significant BEV flow
    print(f"Identifying paths with significant BEV flow in year {target_year}...")
    bev_flows = defaultdict(list)  # path_id -> list of (generation, flow)

    for key_str, value in f_dict.items():
        parsed = parse_f_key(key_str)
        if parsed and parsed['year'] == target_year and parsed['techvehicle'] == tv_id:
            val = float(value) if isinstance(value, str) else value
            if val >= min_flow_threshold:
                bev_flows[parsed['path']].append((parsed['generation'], val, parsed['product'], parsed['odpair']))

    # Get total flow per path
    path_totals = [(path_id, sum(f[1] for f in flows)) for path_id, flows in bev_flows.items()]
    path_totals.sort(key=lambda x: x[1], reverse=True)

    print(f"Found {len(path_totals)} paths with BEV flow >= {min_flow_threshold} tonnes/year")
    print(f"Top 5 paths by flow: {[(p, f'{f:.1f}') for p, f in path_totals[:5]]}\n")

    # Get BEV parameters
    tv_info = next(tv for tv in techvehicles if tv['id'] == tv_id)

    # Check initial SOC for top paths
    max_paths_to_check = 10
    paths_to_check = path_totals[:max_paths_to_check]

    print(f"{'='*100}")
    print(f"CHECKING INITIAL SOC CONSTRAINT FOR {len(paths_to_check)} PATHS")
    print(f"{'='*100}\n")

    violations = []
    all_discrepancies = []

    for path_id, total_flow in paths_to_check:
        # Get path info
        try:
            path_info = next(p for p in paths if p['id'] == path_id)
        except StopIteration:
            print(f"WARNING: Path {path_id} not found in Path.yaml, skipping")
            continue

        path_length = path_info['length']

        # Get origin geo ID
        sequence = path_info['sequence']
        if isinstance(sequence[0], dict):
            origin_geo = sequence[0]['id']
        else:
            origin_geo = sequence[0]

        print(f"\n{'-'*100}")
        print(f"Path {path_id}: {path_length:.2f} km, {total_flow:.2f} tonnes/year total BEV, origin geo: {origin_geo}")
        print(f"{'-'*100}")

        # Check each generation on this path
        for generation, flow_tonnes, product_id, odpair_id in bev_flows[path_id]:
            g_index = generation - g_init
            W_gen = tv_info['W'][g_index]
            annual_range_gen = tv_info['AnnualRange'][g_index]
            tank_capacity_gen = tv_info['tank_capacity'][g_index]

            # Calculate expected SOC using constraint formula
            num_vehicles = (path_length / (W_gen * annual_range_gen)) * 1000 * flow_tonnes
            expected_soc_kwh = tank_capacity_gen * num_vehicles

            # Get actual SOC from results
            soc_key = f"({target_year}, ({product_id}, {odpair_id}, {path_id}, {origin_geo}), {tv_id}, {generation})"

            if soc_key in soc_dict:
                actual_soc_kwh = soc_dict[soc_key]
                actual_soc_kwh = float(actual_soc_kwh) if isinstance(actual_soc_kwh, str) else actual_soc_kwh
            else:
                print(f"  WARNING: SOC key not found for generation {generation}")
                continue

            # Compare
            diff_kwh = actual_soc_kwh - expected_soc_kwh
            diff_pct = (diff_kwh / expected_soc_kwh * 100) if expected_soc_kwh > 0 else 0

            print(f"\n  Generation {generation} ({flow_tonnes:.2f} t/year):")
            print(f"    W={W_gen} t/veh, tank_capacity={tank_capacity_gen} kWh, AnnualRange={annual_range_gen} km/year")
            print(f"    Expected SOC: {expected_soc_kwh/1e6:.6f} GWh ({expected_soc_kwh:,.2f} kWh)")
            print(f"    Actual SOC:   {actual_soc_kwh/1e6:.6f} GWh ({actual_soc_kwh:,.2f} kWh)")
            print(f"    Difference:   {diff_kwh/1e6:.6f} GWh ({diff_pct:+.4f}%)")

            all_discrepancies.append(abs(diff_pct))

            tolerance_kwh = 0.1  # 0.1 kWh tolerance
            if abs(diff_kwh) < tolerance_kwh:
                print(f"    [OK] CONSTRAINT SATISFIED (within {tolerance_kwh} kWh tolerance)")
            else:
                print(f"    [ERROR] CONSTRAINT VIOLATION (exceeds {tolerance_kwh} kWh tolerance)")
                violations.append({
                    'path_id': path_id,
                    'generation': generation,
                    'flow': flow_tonnes,
                    'diff_kwh': diff_kwh,
                    'diff_pct': diff_pct
                })

    return {
        'run': run_info['name'],
        'paths_checked': len(paths_to_check),
        'violations': violations,
        'all_discrepancies': all_discrepancies
    }

# Main execution
print(f"\n{'='*100}")
print(f"INITIAL SOC CONSTRAINT VERIFICATION FOR NOVEMBER 17 RUNS")
print(f"(After fixing missing × 1000 factor in upper bound constraint)")
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
all_disc = [d for r in all_results for d in r['all_discrepancies']]

print(f"Total runs analyzed: {len(all_results)}")
print(f"Total paths checked: {total_paths_checked}")
print(f"Total constraint violations: {total_violations}\n")

if all_disc:
    print(f"Discrepancy statistics:")
    print(f"  Average: {sum(all_disc)/len(all_disc):.6f}%")
    print(f"  Maximum: {max(all_disc):.6f}%")
    print(f"  Minimum: {min(all_disc):.6f}%")

if total_violations > 0:
    print(f"\n{'='*100}")
    print(f"CONSTRAINT VIOLATIONS BY RUN")
    print(f"{'='*100}\n")
    for result in all_results:
        if result['violations']:
            print(f"\n{result['run']}:")
            for v in result['violations']:
                print(f"  Path {v['path_id']}, Gen {v['generation']}: {v['flow']:.2f} t/year")
                print(f"    Difference: {v['diff_kwh']/1e6:.6f} GWh ({v['diff_pct']:+.4f}%)")
else:
    print(f"\n{'='*100}")
    print(f"[OK] ALL CHECKS PASSED!")
    print(f"{'='*100}")
    print(f"\nFindings:")
    print(f"  - Initial SOC constraint satisfied for all checked paths")
    print(f"  - The x 1000 factor bug fix successfully resolved the issue")
    print(f"  - SOC values now match the constraint formula")
    print(f"  - Maximum discrepancy: {max(all_disc):.6f}% (numerical precision)")

print(f"\n{'='*100}\n")
