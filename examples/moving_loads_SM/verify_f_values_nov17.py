"""
Verify that the f decision variable matches input demand for November 17 runs.

This checks if f values from results match the expected relationship: f ≈ F / 1000
where F is the input demand from Odpair.yaml.

If f values are incorrect, this would explain why the initial SOC constraint
produces wrong SOC values even though the constraint is being applied.
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
g_init = 2020  # Initial year
target_year = 2056
tv_id = 1  # BEV

def parse_f_key(key_str):
    """Parse f_dict key string: (year, (product, odpair, path), (mode, techvehicle), generation)"""
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
    """Analyze f values vs input demand for a single run."""
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
        with open(f"{input_dir}/Product.yaml", 'r', encoding='utf-8') as f:
            products = yaml.safe_load(f)
    except FileNotFoundError as e:
        print(f"ERROR: Could not find input files: {e}")
        return None

    # Build odpair lookup: {odpair_id: {'F': demand, 'path_id': path}}
    odpair_dict = {}
    for odpair in odpairs:
        odpair_dict[odpair['id']] = {
            'F': odpair['F'],
            'path_id': odpair['path_id'],
            'from': odpair['from'],
            'to': odpair['to']
        }

    # Product mapping (should be 'freight' = 0)
    product_map = {p['name']: p['id'] for p in products}
    freight_id = product_map.get('freight', 0)

    # Load results
    print("Loading results...")
    try:
        with open(f"{results_dir}/{result_timestamp}_f_dict.yaml", 'r', encoding='utf-8') as f:
            f_dict = yaml.safe_load(f)
    except FileNotFoundError as e:
        print(f"ERROR: Could not find result files: {e}")
        return None

    print(f"Loaded {len(odpairs)} odpairs, {len(f_dict):,} flow entries\n")

    # Filter f_dict for target year and BEV
    print(f"Filtering for year {target_year}, techvehicle {tv_id} (BEV)...")
    filtered_flows = []

    for key_str, value in f_dict.items():
        parsed = parse_f_key(key_str)
        if parsed and parsed['year'] == target_year and parsed['techvehicle'] == tv_id:
            val = float(value) if isinstance(value, str) else value
            if val > 0.001:  # Filter out negligible flows
                filtered_flows.append({
                    'odpair_id': parsed['odpair'],
                    'path_id': parsed['path'],
                    'generation': parsed['generation'],
                    'f_value': val
                })

    print(f"Found {len(filtered_flows)} non-zero BEV flows in year {target_year}\n")

    # Compare f values to input demand
    print(f"{'='*100}")
    print(f"COMPARING f VALUES TO INPUT DEMAND (F)")
    print(f"{'='*100}\n")

    discrepancies = []

    for flow in filtered_flows[:20]:  # Check first 20 to avoid clutter
        odpair_id = flow['odpair_id']
        f_value = flow['f_value']
        generation = flow['generation']

        if odpair_id not in odpair_dict:
            print(f"WARNING: Odpair {odpair_id} not found in input data, skipping")
            continue

        odpair_info = odpair_dict[odpair_id]
        F_list = odpair_info['F']  # List indexed by year
        path_id = odpair_info['path_id']

        # Get F value for target year
        year_idx = target_year - g_init
        if year_idx < 0 or year_idx >= len(F_list):
            print(f"WARNING: Year index {year_idx} out of range for odpair {odpair_id}, skipping")
            continue

        F_input = F_list[year_idx]

        # Expected relationship: f ≈ F / 1000
        expected_f = F_input / 1000

        # Calculate discrepancy
        diff = f_value - expected_f
        diff_pct = (diff / expected_f * 100) if expected_f > 0 else 0

        print(f"OD pair {odpair_id}, path {path_id}, gen {generation}:")
        print(f"  Input demand (F):  {F_input:,.2f} tonnes/year")
        print(f"  Expected f value:  {expected_f:,.6f} (F / 1000)")
        print(f"  Actual f value:    {f_value:,.6f}")
        print(f"  Difference:        {diff:+,.6f} ({diff_pct:+.2f}%)")

        if abs(diff_pct) > 1.0:  # More than 1% discrepancy
            print(f"  [WARNING] Significant discrepancy detected!")
            discrepancies.append({
                'odpair_id': odpair_id,
                'path_id': path_id,
                'generation': generation,
                'F_input': F_input,
                'expected_f': expected_f,
                'actual_f': f_value,
                'diff_pct': diff_pct
            })
        else:
            print(f"  [OK] f value matches expected (within 1% tolerance)")

        print()

    return {
        'run': run_info['name'],
        'total_flows': len(filtered_flows),
        'discrepancies': discrepancies
    }

# Main execution
print(f"\n{'='*100}")
print(f"VERIFYING f VALUES FOR NOVEMBER 17 RUNS")
print(f"{'='*100}")
print(f"\nChecking if f (model output) matches F/1000 (input demand)")
print(f"Discrepancies would indicate other constraints are modifying f values\n")

all_results = []

for run_info in runs:
    result = analyze_run(run_info)
    if result:
        all_results.append(result)

# Summary
print(f"\n\n{'='*100}")
print(f"SUMMARY ACROSS ALL RUNS")
print(f"{'='*100}\n")

total_discrepancies = sum(len(r['discrepancies']) for r in all_results)

print(f"Total runs analyzed: {len(all_results)}")
print(f"Total f values with >1% discrepancy: {total_discrepancies}\n")

if total_discrepancies > 0:
    print(f"SIGNIFICANT DISCREPANCIES FOUND:")
    print(f"This indicates that f values don't match input demand F/1000")
    print(f"Other constraints in the model are modifying f values")
    print(f"This would explain why SOC values are incorrect!\n")

    for result in all_results:
        if result['discrepancies']:
            print(f"\n{result['run']}:")
            for d in result['discrepancies'][:5]:  # First 5 per run
                print(f"  OD {d['odpair_id']}: expected {d['expected_f']:.6f}, got {d['actual_f']:.6f} ({d['diff_pct']:+.2f}%)")
else:
    print(f"[OK] All f values match input demand (within 1% tolerance)")
    print(f"This means the problem is NOT in f values")
    print(f"The issue must be elsewhere in the SOC constraint formula")

print(f"\n{'='*100}\n")
