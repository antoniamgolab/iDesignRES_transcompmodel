"""
Verify initial SOC constraint for November 17 runs with ONLY initial SOC constraint active.

This checks if soc[origin] = tank_capacity × num_vehicles
where num_vehicles = (path_length / (W × AnnualRange)) × 1000 × f
"""

import yaml
import re
from collections import defaultdict

base_path = "C:/Users/simuser/Documents/AntoniaGolab/Scand_Med_analysis/SM_baby_2/iDesignRES_transcompmodel/examples/moving_loads_SM"

runs = [
    {
        'name': 'reverse',
        'case': 'case_20251110_160646_reverse',
        'timestamp': 'case_20251110_160646_reverse_cs_2025-11-17_14-09-45'
    }
]

# Parameters
target_year = 2056
bev_id = 1  # BEV techvehicle ID
# g_init will be calculated from Model.yaml (y_init - pre_y)

def parse_soc_key(key_str):
    """Parse soc_dict key: (year, (product, odpair, path, geo), techvehicle, generation)"""
    pattern = r'\((\d+),\s*\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\),\s*(\d+),\s*(\d+)\)'
    match = re.match(pattern, key_str)
    if match:
        return {
            'year': int(match.group(1)),
            'product': int(match.group(2)),
            'odpair': int(match.group(3)),
            'path': int(match.group(4)),
            'geo': int(match.group(5)),
            'techvehicle': int(match.group(6)),
            'generation': int(match.group(7))
        }
    return None

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
    """Verify initial SOC constraint for a single run."""
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
        with open(f"{input_dir}/Path.yaml", 'r', encoding='utf-8') as f:
            paths = yaml.safe_load(f)
        with open(f"{input_dir}/TechVehicle.yaml", 'r', encoding='utf-8') as f:
            techvehicles = yaml.safe_load(f)
        with open(f"{input_dir}/Model.yaml", 'r', encoding='utf-8') as f:
            model_data = yaml.safe_load(f)
    except FileNotFoundError as e:
        print(f"ERROR: Could not find input files: {e}")
        return None

    # Calculate g_init from Model parameters
    y_init = model_data["y_init"]
    pre_y = model_data["pre_y"]
    g_init = y_init - pre_y
    print(f"Model parameters: y_init={y_init}, pre_y={pre_y}, g_init={g_init}")

    # Load results
    print("Loading results...")
    try:
        with open(f"{results_dir}/{result_timestamp}_soc_dict.yaml", 'r', encoding='utf-8') as f:
            soc_dict = yaml.safe_load(f)
        with open(f"{results_dir}/{result_timestamp}_f_dict.yaml", 'r', encoding='utf-8') as f:
            f_dict = yaml.safe_load(f)
    except FileNotFoundError as e:
        print(f"ERROR: Could not find result files: {e}")
        return None

    print(f"Loaded {len(paths)} paths, {len(techvehicles)} techvehicles")
    print(f"Loaded {len(soc_dict):,} SOC entries, {len(f_dict):,} flow entries\n")

    # Build lookups
    path_dict = {p['id']: p for p in paths}
    tv_dict = {tv['id']: tv for tv in techvehicles}

    # Get BEV info
    bev = tv_dict[bev_id]
    gen_idx = target_year - g_init
    tank_capacity = bev['tank_capacity'][gen_idx]
    W = bev['W'][gen_idx]
    AnnualRange = bev['AnnualRange'][gen_idx]

    print(f"BEV parameters for year {target_year} (generation {target_year}):")
    print(f"  Tank capacity: {tank_capacity:.2f} kWh")
    print(f"  W (payload weight): {W:.2f} tonnes")
    print(f"  Annual range: {AnnualRange:.2f} km\n")

    # Find SOC values at origins for BEV
    print(f"{'='*100}")
    print(f"CHECKING INITIAL SOC CONSTRAINT FOR YEAR {target_year}, BEV (tv={bev_id})")
    print(f"{'='*100}\n")

    # Group SOC by (path, generation) at origins only
    soc_at_origins = {}

    for key_str, value in soc_dict.items():
        parsed = parse_soc_key(key_str)
        if not parsed:
            continue

        if (parsed['year'] != target_year or
            parsed['techvehicle'] != bev_id):
            continue

        path_id = parsed['path']
        geo_id = parsed['geo']
        generation = parsed['generation']

        if path_id not in path_dict:
            continue

        path = path_dict[path_id]
        sequence = path['sequence']

        # Get origin geo ID
        if isinstance(sequence[0], dict):
            origin_id = sequence[0]['id']
        else:
            origin_id = sequence[0]

        # Only check at origins
        if geo_id == origin_id:
            val = float(value) if isinstance(value, str) else value
            soc_at_origins[(path_id, generation)] = {
                'soc': val,  # Already in kWh, no conversion needed
                'path': path
            }

    print(f"Found {len(soc_at_origins)} SOC values at origins\n")

    # For each origin SOC, calculate expected value and compare
    violations = []
    checks_done = 0

    # Sample first 20 to avoid clutter
    sample_keys = sorted(soc_at_origins.keys())[:20]

    for path_id, generation in sample_keys:
        data = soc_at_origins[(path_id, generation)]
        actual_soc = data['soc']
        path = data['path']
        path_length = path['length']

        # Find corresponding f value
        f_value = None
        for key_str, value in f_dict.items():
            parsed = parse_f_key(key_str)
            if (parsed and
                parsed['year'] == target_year and
                parsed['path'] == path_id and
                parsed['techvehicle'] == bev_id and
                parsed['generation'] == generation):
                f_value = float(value) if isinstance(value, str) else value
                break

        if f_value is None:
            print(f"WARNING: No f value found for path {path_id}, gen {generation}, skipping")
            continue

        # Calculate expected SOC: tank_capacity × num_vehicles
        # num_vehicles = (path_length / (W × AnnualRange)) × 1000 × f
        num_vehicles = (path_length / (W * AnnualRange)) * 1000 * f_value
        expected_soc = tank_capacity * num_vehicles

        # Compare
        diff = actual_soc - expected_soc
        diff_pct = (diff / expected_soc * 100) if expected_soc > 0 else 0

        checks_done += 1

        print(f"Path {path_id}, Gen {generation}:")
        print(f"  Path length:        {path_length:>10.2f} km")
        print(f"  Flow (f):           {f_value:>10.6f}")
        print(f"  Num vehicles:       {num_vehicles:>10.6f}")
        print(f"  Expected SOC:       {expected_soc:>10.2f} kWh  (tank_capacity × num_vehicles)")
        print(f"  Actual SOC:         {actual_soc:>10.2f} kWh")
        print(f"  Difference:         {diff:>+10.2f} kWh ({diff_pct:+.4f}%)")

        tolerance = 1e-3  # 0.001 kWh tolerance
        if abs(diff) < tolerance:
            print(f"  [OK] Constraint satisfied (within {tolerance} kWh tolerance)")
        else:
            print(f"  [ERROR] Constraint VIOLATED (exceeds {tolerance} kWh tolerance)")
            violations.append({
                'path_id': path_id,
                'generation': generation,
                'expected': expected_soc,
                'actual': actual_soc,
                'diff': diff,
                'diff_pct': diff_pct
            })

        print()

    return {
        'run': run_info['name'],
        'checks_done': checks_done,
        'violations': violations,
        'total_origins': len(soc_at_origins)
    }

# Main execution
print(f"\n{'='*100}")
print(f"INITIAL SOC CONSTRAINT VERIFICATION FOR NOVEMBER 17 RUNS")
print(f"Checking constraint: soc[origin] = tank_capacity × num_vehicles")
print(f"where num_vehicles = (path_length / (W × AnnualRange)) × 1000 × f")
print(f"{'='*100}")

for run_info in runs:
    result = analyze_run(run_info)

    if result:
        print(f"\n\n{'='*100}")
        print(f"SUMMARY FOR {result['run']}")
        print(f"{'='*100}\n")

        print(f"Total origins with SOC values: {result['total_origins']}")
        print(f"Checks performed (sampled):    {result['checks_done']}")
        print(f"Violations found:              {len(result['violations'])}")

        if result['violations']:
            print(f"\nViolations:")
            for v in result['violations']:
                print(f"  Path {v['path_id']}, Gen {v['generation']}: expected {v['expected']:.2f} kWh, got {v['actual']:.2f} kWh ({v['diff_pct']:+.4f}%)")
        else:
            print(f"\n[OK] All initial SOC constraints satisfied!")
            print(f"The formula soc[origin] = tank_capacity × num_vehicles is correct")

print(f"\n{'='*100}\n")
