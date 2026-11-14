"""
Verify the demand constraint from model_functions.jl lines 349-352.

The constraint is:
sum(f[y, (product, odpair, path), (mode, techvehicle), g]
    for all paths, all mode-techvehicle pairs, all generations <= y)
== sum(F[i] for year range) * (1/1000)

This verifies that the TOTAL flow (summed across all technologies and generations)
matches the input demand, NOT individual f values.
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
    }
]

# Parameters
g_init = 2020
target_year = 2056
time_step = 4  # Assuming 4-year timesteps based on generation pattern

def parse_f_key(key_str):
    """Parse f_dict key: (year, (product, odpair, path), (mode, techvehicle), generation)"""
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
    """Verify demand constraint for a single run."""
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
        with open(f"{input_dir}/Odpair.yaml", 'r', encoding='utf-8') as f:
            odpairs = yaml.safe_load(f)
    except FileNotFoundError as e:
        print(f"ERROR: Could not find input files: {e}")
        return None

    # Load results
    print("Loading results...")
    try:
        with open(f"{results_dir}/{result_timestamp}_f_dict.yaml", 'r', encoding='utf-8') as f:
            f_dict = yaml.safe_load(f)
    except FileNotFoundError as e:
        print(f"ERROR: Could not find result files: {e}")
        return None

    print(f"Loaded {len(odpairs)} odpairs, {len(f_dict):,} flow entries\n")

    # Group f values by (year, odpair)
    print(f"Grouping f values by (year, odpair)...")
    f_by_year_odpair = defaultdict(list)

    for key_str, value in f_dict.items():
        parsed = parse_f_key(key_str)
        if parsed:
            val = float(value) if isinstance(value, str) else value
            if val > 1e-6:  # Filter out negligible flows
                f_by_year_odpair[(parsed['year'], parsed['odpair'])].append({
                    'path': parsed['path'],
                    'mode': parsed['mode'],
                    'techvehicle': parsed['techvehicle'],
                    'generation': parsed['generation'],
                    'value': val
                })

    print(f"Found flow data for {len(f_by_year_odpair)} (year, odpair) combinations\n")

    # Check constraint for target year
    print(f"{'='*100}")
    print(f"CHECKING DEMAND CONSTRAINT FOR YEAR {target_year}")
    print(f"{'='*100}\n")

    # Build odpair lookup
    odpair_dict = {od['id']: od for od in odpairs}

    violations = []
    checks_done = 0

    # Sample a few odpairs to check
    sample_odpairs = sorted(set(odpair_id for (year, odpair_id) in f_by_year_odpair.keys() if year == target_year))[:20]

    for odpair_id in sample_odpairs:
        if odpair_id not in odpair_dict:
            continue

        odpair_info = odpair_dict[odpair_id]
        F_list = odpair_info['F']

        # Calculate expected total flow: sum(F[i]) * (1/1000) for year range
        # For target_year, the range is (y-y_init+1):min((y-y_init+time_step), length(F))
        y_init = g_init  # Assuming y_init = g_init
        start_idx = target_year - y_init  # 0-indexed for Python
        end_idx = min(target_year - y_init + time_step - 1, len(F_list) - 1)

        expected_total = sum(F_list[i] for i in range(start_idx, end_idx + 1)) / 1000

        # Sum actual f values for this odpair in target year
        # Constraint: sum over all paths, all mv pairs, all generations <= target_year
        flows = f_by_year_odpair.get((target_year, odpair_id), [])

        # Filter to only generations <= target_year
        flows_filtered = [f for f in flows if f['generation'] <= target_year]

        actual_total = sum(f['value'] for f in flows_filtered)

        # Compare
        diff = actual_total - expected_total
        diff_pct = (diff / expected_total * 100) if expected_total > 0 else 0

        checks_done += 1

        print(f"OD pair {odpair_id}:")
        print(f"  Expected (sum F[{start_idx}:{end_idx+1}] / 1000): {expected_total:,.6f}")
        print(f"  Actual (sum of {len(flows_filtered)} f values):      {actual_total:,.6f}")
        print(f"  Difference:                                {diff:+,.6f} ({diff_pct:+.4f}%)")

        # Show breakdown by techvehicle
        by_tv = defaultdict(float)
        by_gen = defaultdict(float)
        for f in flows_filtered:
            by_tv[f['techvehicle']] += f['value']
            by_gen[f['generation']] += f['value']

        print(f"  Breakdown by techvehicle: {dict(by_tv)}")
        print(f"  Breakdown by generation: {dict(by_gen)}")

        tolerance = 1e-3  # 0.001 tolerance
        if abs(diff) < tolerance:
            print(f"  [OK] Constraint satisfied (within {tolerance} tolerance)")
        else:
            print(f"  [ERROR] Constraint VIOLATED (exceeds {tolerance} tolerance)")
            violations.append({
                'odpair_id': odpair_id,
                'expected': expected_total,
                'actual': actual_total,
                'diff': diff,
                'diff_pct': diff_pct
            })

        print()

    return {
        'run': run_info['name'],
        'checks_done': checks_done,
        'violations': violations
    }

# Main execution
print(f"\n{'='*100}")
print(f"DEMAND CONSTRAINT VERIFICATION FOR NOVEMBER 17 RUNS")
print(f"Checking constraint from model_functions.jl:349-352")
print(f"{'='*100}")

for run_info in runs:
    result = analyze_run(run_info)

    if result:
        print(f"\n\n{'='*100}")
        print(f"SUMMARY FOR {result['run']}")
        print(f"{'='*100}\n")

        print(f"Checks performed: {result['checks_done']}")
        print(f"Violations found: {len(result['violations'])}")

        if result['violations']:
            print(f"\nViolations:")
            for v in result['violations']:
                print(f"  OD {v['odpair_id']}: expected {v['expected']:.6f}, got {v['actual']:.6f} ({v['diff_pct']:+.4f}%)")
        else:
            print(f"\n[OK] All demand constraints satisfied!")
            print(f"The model correctly enforces total flow = input demand")

print(f"\n{'='*100}\n")
