"""
Compare break times between BASELINE and CONSTRAINED cases
for OD pairs that are electrified (>=50% BEV) in BOTH cases.

This helps understand how the charging-at-breaks constraint affects
break patterns for routes that remain electrified.
"""

import yaml
import os
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict

# ============================================================================
# CONFIGURATION
# ============================================================================
BASE_DIR = r'C:\Users\simuser\Documents\AntoniaGolab\Scand_Med_analysis\SM_baby_2\iDesignRES_transcompmodel\examples\moving_loads_SM'
BASELINE_DIR = os.path.join(BASE_DIR, 'results', 'uncertainty_analysis')
CONSTRAINED_DIR = os.path.join(BASE_DIR, 'results', 'uncertainty_analysis_charging_at_breaks')
INPUT_DIR = os.path.join(BASE_DIR, 'input_data', 'uncertainty_scenarios', 'scenario_000')

TARGET_YEAR = 2032
ELECTRIFICATION_THRESHOLD = 50  # percent

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
def parse_key(key_str):
    """Parse key string to extract components using regex"""
    numbers = re.findall(r'-?\d+', key_str)
    return [int(n) for n in numbers]

def load_yaml(filepath):
    """Load a YAML file"""
    with open(filepath, 'r') as f:
        return yaml.safe_load(f)

# ============================================================================
# LOAD INPUT DATA
# ============================================================================
print("=" * 80)
print("LOADING INPUT DATA")
print("=" * 80)

# Load path data
path_data = load_yaml(os.path.join(INPUT_DIR, 'Path.yaml'))
path_lengths = {p['id']: p['length'] for p in path_data}
print(f"Loaded {len(path_lengths)} paths")

# Load OD pair data
odpair_data = load_yaml(os.path.join(INPUT_DIR, 'Odpair.yaml'))
odpair_to_path = {od['id']: od['path_id'] for od in odpair_data}
print(f"Loaded {len(odpair_to_path)} OD pairs")

# Load mandatory breaks
mandatory_breaks = load_yaml(os.path.join(INPUT_DIR, 'MandatoryBreaks.yaml'))
print(f"Loaded {len(mandatory_breaks)} mandatory breaks")

# Create path_id -> mandatory breaks mapping
path_to_breaks = defaultdict(list)
for mb in mandatory_breaks:
    path_to_breaks[mb['path_id']].append(mb)

# Load TechVehicle for charging power
techvehicles = load_yaml(os.path.join(INPUT_DIR, 'TechVehicle.yaml'))
tv_dict = {tv['id']: tv for tv in techvehicles}

# Load Model params
model_params = load_yaml(os.path.join(INPUT_DIR, 'Model.yaml'))
g_init = model_params['y_init'] - model_params['pre_y']

# Load geographic elements
geo_data = load_yaml(os.path.join(INPUT_DIR, 'GeographicElement.yaml'))
geo_to_country = {g['id']: g.get('country', 'Unknown') for g in geo_data}

# ============================================================================
# LOAD RESULTS DATA
# ============================================================================
print("\n" + "=" * 80)
print("LOADING RESULTS DATA")
print("=" * 80)

# Find result files
baseline_scenario_dir = os.path.join(BASELINE_DIR, 'scenario_000')
constrained_scenario_dir = os.path.join(CONSTRAINED_DIR, 'scenario_000')

baseline_files = os.listdir(baseline_scenario_dir)
constrained_files = os.listdir(constrained_scenario_dir)

# Load f_dict (flows) to identify electrified OD pairs
baseline_f_file = [f for f in baseline_files if 'f_dict.yaml' in f][0]
constrained_f_file = [f for f in constrained_files if 'f_dict.yaml' in f][0]

print(f"Loading baseline flows: {baseline_f_file}")
baseline_f = load_yaml(os.path.join(baseline_scenario_dir, baseline_f_file))
print(f"Loading constrained flows: {constrained_f_file}")
constrained_f = load_yaml(os.path.join(constrained_scenario_dir, constrained_f_file))

# Load travel_time and extra_break_time
baseline_tt_file = [f for f in baseline_files if 'travel_time_dict.yaml' in f][0]
constrained_tt_file = [f for f in constrained_files if 'travel_time_dict.yaml' in f][0]
baseline_eb_file = [f for f in baseline_files if 'extra_break_time_dict.yaml' in f][0]
constrained_eb_file = [f for f in constrained_files if 'extra_break_time_dict.yaml' in f][0]

print(f"Loading baseline travel_time: {baseline_tt_file}")
baseline_tt = load_yaml(os.path.join(baseline_scenario_dir, baseline_tt_file))
print(f"Loading constrained travel_time: {constrained_tt_file}")
constrained_tt = load_yaml(os.path.join(constrained_scenario_dir, constrained_tt_file))

print(f"Loading baseline extra_break_time: {baseline_eb_file}")
baseline_eb = load_yaml(os.path.join(baseline_scenario_dir, baseline_eb_file))
print(f"Loading constrained extra_break_time: {constrained_eb_file}")
constrained_eb = load_yaml(os.path.join(constrained_scenario_dir, constrained_eb_file))

# Load s_dict (charging)
baseline_s_file = [f for f in baseline_files if 's_dict.yaml' in f][0]
constrained_s_file = [f for f in constrained_files if 's_dict.yaml' in f][0]

print(f"Loading baseline charging (s): {baseline_s_file}")
baseline_s = load_yaml(os.path.join(baseline_scenario_dir, baseline_s_file))
print(f"Loading constrained charging (s): {constrained_s_file}")
constrained_s = load_yaml(os.path.join(constrained_scenario_dir, constrained_s_file))

# ============================================================================
# IDENTIFY ELECTRIFIED OD PAIRS IN BOTH CASES
# ============================================================================
print("\n" + "=" * 80)
print(f"IDENTIFYING ELECTRIFIED OD PAIRS (>={ELECTRIFICATION_THRESHOLD}% BEV) IN YEAR {TARGET_YEAR}")
print("=" * 80)

def calculate_bev_shares(f_dict, year):
    """Calculate BEV share by OD pair for a given year"""
    od_flows = defaultdict(lambda: {'bev': 0, 'other': 0})

    for key, value in f_dict.items():
        val = float(value) if isinstance(value, str) else value
        if val < 1e-6:
            continue

        nums = parse_key(key)
        if len(nums) < 7:
            continue

        key_year = nums[0]
        odpair_id = nums[2]
        techvehicle_id = nums[5]

        if key_year != year:
            continue

        # BEV techvehicle_id = 1
        if techvehicle_id == 1:
            od_flows[odpair_id]['bev'] += val
        else:
            od_flows[odpair_id]['other'] += val

    # Calculate shares
    shares = {}
    for odpair_id, flows in od_flows.items():
        total = flows['bev'] + flows['other']
        shares[odpair_id] = 100 * flows['bev'] / total if total > 0 else 0

    return shares

baseline_shares = calculate_bev_shares(baseline_f, TARGET_YEAR)
constrained_shares = calculate_bev_shares(constrained_f, TARGET_YEAR)

# Find OD pairs electrified in BOTH cases
baseline_electrified = set(od for od, share in baseline_shares.items() if share >= ELECTRIFICATION_THRESHOLD)
constrained_electrified = set(od for od, share in constrained_shares.items() if share >= ELECTRIFICATION_THRESHOLD)
both_electrified = baseline_electrified & constrained_electrified

print(f"Baseline electrified OD pairs: {len(baseline_electrified)}")
print(f"Constrained electrified OD pairs: {len(constrained_electrified)}")
print(f"BOTH electrified: {len(both_electrified)}")

# ============================================================================
# EXTRACT BREAK TIMES FOR BOTH-ELECTRIFIED OD PAIRS
# ============================================================================
print("\n" + "=" * 80)
print("EXTRACTING BREAK TIMES FOR BOTH-ELECTRIFIED OD PAIRS")
print("=" * 80)

def extract_break_times(travel_time_dict, extra_break_dict, s_dict, odpairs, year):
    """
    Extract break time data for specified OD pairs.

    travel_time key: (year, (prod_id, odpair_id, path_id, geo_id), tv_id, gen)
    extra_break_time key: (year, (prod_id, odpair_id, path_id, geo_id), tv_id, gen)
    s key: (year, (prod_id, odpair_id, path_id, geo_id), tv_id, (fuel_id, infra_id), gen)
    """
    results = []

    # Get path_ids for the OD pairs we care about
    odpair_paths = {od: odpair_to_path[od] for od in odpairs if od in odpair_to_path}

    # Process travel_time entries
    for key, tt_value in travel_time_dict.items():
        nums = parse_key(key)
        if len(nums) < 6:
            continue

        key_year = nums[0]
        odpair_id = nums[2]
        path_id = nums[3]
        geo_id = nums[4]
        tv_id = nums[5]
        gen = nums[6] if len(nums) > 6 else nums[5]

        if key_year != year:
            continue

        if odpair_id not in odpairs:
            continue

        # Only BEV (tv_id = 1)
        if tv_id != 1:
            continue

        tt_val = float(tt_value) if isinstance(tt_value, str) else tt_value

        # Get extra_break_time for this entry
        extra_val = 0
        for eb_key, eb_value in extra_break_dict.items():
            eb_nums = parse_key(eb_key)
            if len(eb_nums) >= 6:
                if (eb_nums[0] == year and eb_nums[2] == odpair_id and
                    eb_nums[3] == path_id and eb_nums[4] == geo_id and eb_nums[5] == 1):
                    extra_val = float(eb_value) if isinstance(eb_value, str) else eb_value
                    break

        # Get charging at this location
        charging_kwh = 0
        for s_key, s_value in s_dict.items():
            s_nums = parse_key(s_key)
            if len(s_nums) >= 7:
                # s key structure may vary, look for matching location
                if s_nums[0] == year and s_nums[4] == geo_id:
                    s_val = float(s_value) if isinstance(s_value, str) else s_value
                    charging_kwh += s_val

        # Get mandatory break info for this path/location
        mandatory_duration = 0.75  # Default 45 min
        for mb in path_to_breaks.get(path_id, []):
            if mb['latest_geo_id'] == geo_id:
                mandatory_duration = mb['time_with_breaks'] - mb['cumulative_driving_time']
                break

        # Calculate charging time (assume 350 kW for BEV)
        charging_power = 350  # kW
        if tv_id in tv_dict:
            tv = tv_dict[tv_id]
            gen_idx = gen - g_init if gen >= g_init else 0
            if gen_idx < len(tv.get('peak_fueling', [])):
                charging_power = tv['peak_fueling'][gen_idx]

        charging_time = (charging_kwh * 1000) / charging_power if charging_power > 0 else 0

        results.append({
            'odpair_id': odpair_id,
            'path_id': path_id,
            'geo_id': geo_id,
            'year': year,
            'generation': gen,
            'travel_time': tt_val,
            'extra_break_time': extra_val,
            'mandatory_duration': mandatory_duration,
            'actual_break_duration': mandatory_duration + extra_val,
            'charging_kwh': charging_kwh,
            'charging_time': charging_time,
            'total_stop_time': mandatory_duration + extra_val + charging_time
        })

    return pd.DataFrame(results)

print("Extracting baseline break times...")
baseline_breaks_df = extract_break_times(baseline_tt, baseline_eb, baseline_s, both_electrified, TARGET_YEAR)
print(f"  Found {len(baseline_breaks_df)} break entries")

print("Extracting constrained break times...")
constrained_breaks_df = extract_break_times(constrained_tt, constrained_eb, constrained_s, both_electrified, TARGET_YEAR)
print(f"  Found {len(constrained_breaks_df)} break entries")

# ============================================================================
# COMPARE BREAK TIMES
# ============================================================================
print("\n" + "=" * 80)
print("BREAK TIME COMPARISON: BASELINE vs CONSTRAINED")
print("=" * 80)

if len(baseline_breaks_df) > 0 and len(constrained_breaks_df) > 0:
    print("\n--- BASELINE (no charging constraint) ---")
    print(f"  Total break entries: {len(baseline_breaks_df)}")
    print(f"  Avg extra_break_time: {baseline_breaks_df['extra_break_time'].mean():.3f}h ({baseline_breaks_df['extra_break_time'].mean()*60:.1f} min)")
    print(f"  Avg actual_break_duration: {baseline_breaks_df['actual_break_duration'].mean():.3f}h ({baseline_breaks_df['actual_break_duration'].mean()*60:.1f} min)")
    print(f"  Avg charging_time: {baseline_breaks_df['charging_time'].mean():.3f}h ({baseline_breaks_df['charging_time'].mean()*60:.1f} min)")
    print(f"  Avg total_stop_time: {baseline_breaks_df['total_stop_time'].mean():.3f}h ({baseline_breaks_df['total_stop_time'].mean()*60:.1f} min)")

    print("\n--- CONSTRAINED (charging at breaks only) ---")
    print(f"  Total break entries: {len(constrained_breaks_df)}")
    print(f"  Avg extra_break_time: {constrained_breaks_df['extra_break_time'].mean():.3f}h ({constrained_breaks_df['extra_break_time'].mean()*60:.1f} min)")
    print(f"  Avg actual_break_duration: {constrained_breaks_df['actual_break_duration'].mean():.3f}h ({constrained_breaks_df['actual_break_duration'].mean()*60:.1f} min)")
    print(f"  Avg charging_time: {constrained_breaks_df['charging_time'].mean():.3f}h ({constrained_breaks_df['charging_time'].mean()*60:.1f} min)")
    print(f"  Avg total_stop_time: {constrained_breaks_df['total_stop_time'].mean():.3f}h ({constrained_breaks_df['total_stop_time'].mean()*60:.1f} min)")

    # Calculate differences
    print("\n--- DIFFERENCES (Constrained - Baseline) ---")
    diff_extra = constrained_breaks_df['extra_break_time'].mean() - baseline_breaks_df['extra_break_time'].mean()
    diff_actual = constrained_breaks_df['actual_break_duration'].mean() - baseline_breaks_df['actual_break_duration'].mean()
    diff_charging = constrained_breaks_df['charging_time'].mean() - baseline_breaks_df['charging_time'].mean()
    diff_total = constrained_breaks_df['total_stop_time'].mean() - baseline_breaks_df['total_stop_time'].mean()

    print(f"  Extra break time: {diff_extra:+.3f}h ({diff_extra*60:+.1f} min)")
    print(f"  Actual break duration: {diff_actual:+.3f}h ({diff_actual*60:+.1f} min)")
    print(f"  Charging time: {diff_charging:+.3f}h ({diff_charging*60:+.1f} min)")
    print(f"  Total stop time: {diff_total:+.3f}h ({diff_total*60:+.1f} min)")

    # Aggregate by OD pair
    print("\n" + "=" * 80)
    print("AGGREGATED BY OD PAIR")
    print("=" * 80)

    baseline_by_od = baseline_breaks_df.groupby('odpair_id').agg({
        'extra_break_time': 'sum',
        'charging_time': 'sum',
        'total_stop_time': 'sum'
    }).reset_index()
    baseline_by_od.columns = ['odpair_id', 'baseline_extra_break', 'baseline_charging', 'baseline_total_stop']

    constrained_by_od = constrained_breaks_df.groupby('odpair_id').agg({
        'extra_break_time': 'sum',
        'charging_time': 'sum',
        'total_stop_time': 'sum'
    }).reset_index()
    constrained_by_od.columns = ['odpair_id', 'constrained_extra_break', 'constrained_charging', 'constrained_total_stop']

    # Merge
    comparison = baseline_by_od.merge(constrained_by_od, on='odpair_id', how='outer').fillna(0)
    comparison['diff_extra_break'] = comparison['constrained_extra_break'] - comparison['baseline_extra_break']
    comparison['diff_charging'] = comparison['constrained_charging'] - comparison['baseline_charging']
    comparison['diff_total_stop'] = comparison['constrained_total_stop'] - comparison['baseline_total_stop']

    # Add path info
    comparison['path_id'] = comparison['odpair_id'].map(odpair_to_path)
    comparison['path_length'] = comparison['path_id'].map(path_lengths)

    print(f"\nOD pairs compared: {len(comparison)}")
    print(f"\nMean differences across OD pairs:")
    print(f"  Extra break: {comparison['diff_extra_break'].mean():+.3f}h")
    print(f"  Charging: {comparison['diff_charging'].mean():+.3f}h")
    print(f"  Total stop: {comparison['diff_total_stop'].mean():+.3f}h")

    # Show top differences
    print("\n" + "=" * 80)
    print("TOP 10 OD PAIRS WITH LARGEST TOTAL STOP TIME INCREASE")
    print("=" * 80)
    top_increase = comparison.nlargest(10, 'diff_total_stop')
    print(f"\n{'OD':>6} {'Path':>6} {'Length':>8} {'Base Stop':>10} {'Constr Stop':>12} {'Diff':>8}")
    print("-" * 60)
    for _, row in top_increase.iterrows():
        print(f"{row['odpair_id']:>6.0f} {row['path_id']:>6.0f} {row['path_length']:>8.0f}km "
              f"{row['baseline_total_stop']:>10.2f}h {row['constrained_total_stop']:>12.2f}h {row['diff_total_stop']:>+8.2f}h")

    print("\n" + "=" * 80)
    print("TOP 10 OD PAIRS WITH LARGEST TOTAL STOP TIME DECREASE")
    print("=" * 80)
    top_decrease = comparison.nsmallest(10, 'diff_total_stop')
    print(f"\n{'OD':>6} {'Path':>6} {'Length':>8} {'Base Stop':>10} {'Constr Stop':>12} {'Diff':>8}")
    print("-" * 60)
    for _, row in top_decrease.iterrows():
        print(f"{row['odpair_id']:>6.0f} {row['path_id']:>6.0f} {row['path_length']:>8.0f}km "
              f"{row['baseline_total_stop']:>10.2f}h {row['constrained_total_stop']:>12.2f}h {row['diff_total_stop']:>+8.2f}h")

    # Save results
    comparison.to_csv(os.path.join(BASE_DIR, 'break_time_comparison_both_electrified.csv'), index=False)
    print(f"\nResults saved to: break_time_comparison_both_electrified.csv")

else:
    print("Not enough data to compare")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
