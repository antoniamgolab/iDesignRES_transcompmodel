"""
Compare model results between original and re-run versions.
- Unconstrained: uncertainty_scenarios (original) vs uncertainty_scenarios_v2
- Fixed-fleet: uncertainty_scenarios_fixed_brk_fleet vs uncertainty_scenarios_fixed_brk_fleet_v3
"""

import os
import re
import ast
import yaml
import numpy as np
from collections import defaultdict

BASE = r"C:\Users\simuser\Documents\AntoniaGolab\Scand_Med_analysis\SM_baby_2\iDesignRES_transcompmodel\examples\moving_loads_SM\results"

# -------------------------------------------------------------------
# Helper: parse a YAML dict file into a Python dict
# Keys may be tuples or CartesianIndex(...)
# -------------------------------------------------------------------

def parse_cartesian_index(s):
    """Parse CartesianIndex(a, b, c, d, e) -> tuple"""
    m = re.match(r'CartesianIndex\((.+)\)', s.strip())
    if m:
        inner = m.group(1)
        parts = [x.strip() for x in inner.split(',')]
        return tuple(ast.literal_eval(p) for p in parts)
    return None

def load_result_dict(filepath):
    """Load a result YAML file. Each line is  key: value."""
    data = {}
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            # Split on LAST colon followed by a space and number
            # But keys can contain colons (e.g., timestamps), so we need to be careful
            # The format is: key: float_value
            # Find the last ': ' that precedes a number
            idx = line.rfind(': ')
            if idx == -1:
                continue
            key_str = line[:idx].strip()
            val_str = line[idx+2:].strip()
            try:
                value = float(val_str)
            except ValueError:
                continue

            # Parse the key
            if key_str.startswith('CartesianIndex'):
                key = parse_cartesian_index(key_str)
            else:
                try:
                    key = ast.literal_eval(key_str)
                except:
                    key = key_str

            if key is not None:
                data[key] = value
    return data


def find_latest_timestamp(directory, prefix, suffix):
    """Find the file with the latest timestamp in a directory."""
    pattern = re.compile(rf'{re.escape(prefix)}_(\d{{4}}-\d{{2}}-\d{{2}}_\d{{2}}-\d{{2}}-\d{{2}})_{re.escape(suffix)}')
    latest_ts = None
    latest_file = None
    for f in os.listdir(directory):
        m = pattern.match(f)
        if m:
            ts = m.group(1)
            if latest_ts is None or ts > latest_ts:
                latest_ts = ts
                latest_file = f
    return latest_file, latest_ts


def get_file(directory, dict_name, prefix="scenario_000_cs"):
    """Get the file path for a given dict in a scenario directory.
    If multiple timestamps, pick the latest."""
    files = [f for f in os.listdir(directory) if f.endswith(f'_{dict_name}.yaml')]
    if not files:
        return None
    # Sort by timestamp embedded in filename
    files.sort()
    return os.path.join(directory, files[-1])


# -------------------------------------------------------------------
# Aggregate h_dict by year and technology
# -------------------------------------------------------------------

def aggregate_h_by_year_tech(h_dict):
    """h_dict keys: (year, odpair_id, tv_id, generation) -> value (fleet count)
    Aggregate to {(year, tv_id): total}"""
    agg = defaultdict(float)
    for key, val in h_dict.items():
        year, odpair_id, tv_id, gen = key
        agg[(year, tv_id)] += val
    return dict(agg)


def aggregate_h_by_year(h_dict):
    """Aggregate fleet to {year: total}"""
    agg = defaultdict(float)
    for key, val in h_dict.items():
        year = key[0]
        agg[year] += val
    return dict(agg)


# -------------------------------------------------------------------
# Aggregate s_dict by year
# s_dict keys: CartesianIndex(a, b, c, d, e) -> value (charging kWh)
# The first element maps to year index, but we need to figure out the mapping.
# Actually let's aggregate by the first element directly.
# -------------------------------------------------------------------

def aggregate_s_by_first(s_dict):
    """Aggregate s_dict by first element of key."""
    agg = defaultdict(float)
    for key, val in s_dict.items():
        agg[key[0]] += val
    return dict(agg)


# -------------------------------------------------------------------
# Aggregate f_dict by year and technology
# f_dict keys: (year, (product, odpair, path), (mode, tv), generation)
# -------------------------------------------------------------------

def aggregate_f_by_year_tech(f_dict):
    """Aggregate f_dict to {(year, tv_id): total}"""
    agg = defaultdict(float)
    for key, val in f_dict.items():
        year = key[0]
        mode_tv = key[2]
        if isinstance(mode_tv, tuple) and len(mode_tv) == 2:
            tv_id = mode_tv[1]
        else:
            tv_id = 'unknown'
        agg[(year, tv_id)] += val
    return dict(agg)


def aggregate_f_by_year(f_dict):
    """Aggregate f_dict to {year: total}"""
    agg = defaultdict(float)
    for key, val in f_dict.items():
        year = key[0]
        agg[year] += val
    return dict(agg)


# -------------------------------------------------------------------
# Comparison functions
# -------------------------------------------------------------------

def compare_dicts(d1, d2, name=""):
    """Compare two aggregated dicts. Return summary stats."""
    all_keys = sorted(set(d1.keys()) | set(d2.keys()))

    if not all_keys:
        print(f"  {name}: Both empty")
        return

    print(f"\n  === {name} ===")
    print(f"  {'Key':<30} {'Original':>15} {'Re-run':>15} {'Abs Diff':>15} {'Rel Diff %':>12}")
    print(f"  {'-'*90}")

    abs_diffs = []
    rel_diffs = []

    for k in all_keys:
        v1 = d1.get(k, 0.0)
        v2 = d2.get(k, 0.0)
        abs_diff = v2 - v1
        if abs(v1) > 1e-10:
            rel_diff = (v2 - v1) / abs(v1) * 100
        elif abs(v2) > 1e-10:
            rel_diff = float('inf')
        else:
            rel_diff = 0.0

        abs_diffs.append(abs(abs_diff))
        if rel_diff != float('inf'):
            rel_diffs.append(abs(rel_diff))

        print(f"  {str(k):<30} {v1:>15.4f} {v2:>15.4f} {abs_diff:>15.4f} {rel_diff:>11.4f}%")

    print(f"\n  Summary:")
    print(f"    Max absolute difference: {max(abs_diffs):.6f}")
    if rel_diffs:
        print(f"    Max relative difference: {max(rel_diffs):.6f}%")
        print(f"    Mean relative difference: {np.mean(rel_diffs):.6f}%")

    # Correlation
    if len(all_keys) > 1:
        vals1 = [d1.get(k, 0.0) for k in all_keys]
        vals2 = [d2.get(k, 0.0) for k in all_keys]
        if np.std(vals1) > 0 and np.std(vals2) > 0:
            corr = np.corrcoef(vals1, vals2)[0, 1]
            print(f"    Pearson correlation: {corr:.10f}")


def compare_raw_dicts(d1, d2, name=""):
    """Compare at the individual key level for raw (non-aggregated) dicts."""
    all_keys = set(d1.keys()) | set(d2.keys())
    keys_only_in_1 = set(d1.keys()) - set(d2.keys())
    keys_only_in_2 = set(d2.keys()) - set(d1.keys())
    common_keys = set(d1.keys()) & set(d2.keys())

    print(f"\n  === {name} (key-level comparison) ===")
    print(f"    Total keys in original: {len(d1)}")
    print(f"    Total keys in re-run:   {len(d2)}")
    print(f"    Keys only in original:  {len(keys_only_in_1)}")
    print(f"    Keys only in re-run:    {len(keys_only_in_2)}")
    print(f"    Common keys:            {len(common_keys)}")

    if not common_keys:
        print(f"    No common keys to compare!")
        return

    abs_diffs = []
    rel_diffs = []
    max_abs_key = None
    max_abs_val = 0
    max_rel_key = None
    max_rel_val = 0

    zero_in_both = 0
    exact_match = 0

    for k in common_keys:
        v1 = d1[k]
        v2 = d2[k]
        ad = abs(v2 - v1)
        abs_diffs.append(ad)

        if v1 == v2:
            exact_match += 1

        if abs(v1) < 1e-12 and abs(v2) < 1e-12:
            zero_in_both += 1
            continue

        if ad > max_abs_val:
            max_abs_val = ad
            max_abs_key = k

        if abs(v1) > 1e-10:
            rd = abs(v2 - v1) / abs(v1) * 100
            rel_diffs.append(rd)
            if rd > max_rel_val:
                max_rel_val = rd
                max_rel_key = k

    print(f"    Exact matches:          {exact_match} ({exact_match/len(common_keys)*100:.1f}%)")
    print(f"    Both near-zero:         {zero_in_both}")
    print(f"    Max abs diff:           {max_abs_val:.8f} at key {max_abs_key}")
    if rel_diffs:
        print(f"    Max rel diff:           {max_rel_val:.4f}% at key {max_rel_key}")
        print(f"    Mean rel diff:          {np.mean(rel_diffs):.6f}%")
        print(f"    Median rel diff:        {np.median(rel_diffs):.6f}%")
        print(f"    90th pctl rel diff:     {np.percentile(rel_diffs, 90):.6f}%")
        print(f"    99th pctl rel diff:     {np.percentile(rel_diffs, 99):.6f}%")

    # Correlation on common keys
    vals1 = [d1[k] for k in common_keys]
    vals2 = [d2[k] for k in common_keys]
    if np.std(vals1) > 0 and np.std(vals2) > 0:
        corr = np.corrcoef(vals1, vals2)[0, 1]
        print(f"    Pearson correlation:     {corr:.10f}")

    # Sum comparison
    sum1 = sum(d1[k] for k in common_keys)
    sum2 = sum(d2[k] for k in common_keys)
    print(f"    Sum (original, common):  {sum1:.4f}")
    print(f"    Sum (re-run, common):    {sum2:.4f}")
    if abs(sum1) > 1e-10:
        print(f"    Sum rel diff:            {(sum2-sum1)/abs(sum1)*100:.6f}%")


# -------------------------------------------------------------------
# Main comparison
# -------------------------------------------------------------------

def run_comparison(dir_orig, dir_rerun, label, prefix_orig="scenario_000_cs", prefix_rerun="scenario_000_cs"):
    print(f"\n{'='*100}")
    print(f"  COMPARISON: {label}")
    print(f"{'='*100}")

    scen_orig = os.path.join(dir_orig, "scenario_000")
    scen_rerun = os.path.join(dir_rerun, "scenario_000")

    if not os.path.isdir(scen_orig):
        print(f"  ERROR: {scen_orig} not found")
        return
    if not os.path.isdir(scen_rerun):
        print(f"  ERROR: {scen_rerun} not found")
        return

    # Find files
    h_orig = get_file(scen_orig, "h_dict", prefix_orig)
    h_rerun = get_file(scen_rerun, "h_dict", prefix_rerun)
    s_orig = get_file(scen_orig, "s_dict", prefix_orig)
    s_rerun = get_file(scen_rerun, "s_dict", prefix_rerun)
    f_orig = get_file(scen_orig, "f_dict", prefix_orig)
    f_rerun = get_file(scen_rerun, "f_dict", prefix_rerun)

    print(f"\n  Files being compared:")
    print(f"    h_dict orig:  {os.path.basename(h_orig) if h_orig else 'NOT FOUND'}")
    print(f"    h_dict rerun: {os.path.basename(h_rerun) if h_rerun else 'NOT FOUND'}")
    print(f"    s_dict orig:  {os.path.basename(s_orig) if s_orig else 'NOT FOUND'}")
    print(f"    s_dict rerun: {os.path.basename(s_rerun) if s_rerun else 'NOT FOUND'}")
    print(f"    f_dict orig:  {os.path.basename(f_orig) if f_orig else 'NOT FOUND'}")
    print(f"    f_dict rerun: {os.path.basename(f_rerun) if f_rerun else 'NOT FOUND'}")

    # ---- h_dict comparison ----
    if h_orig and h_rerun:
        print(f"\n  Loading h_dict (fleet composition)...")
        h1 = load_result_dict(h_orig)
        h2 = load_result_dict(h_rerun)

        # Raw comparison
        compare_raw_dicts(h1, h2, "h_dict (fleet) - raw key-level")

        # Aggregated by year and tech
        h1_yt = aggregate_h_by_year_tech(h1)
        h2_yt = aggregate_h_by_year_tech(h2)
        compare_dicts(h1_yt, h2_yt, "h_dict by (year, tech)")

        # Aggregated by year only
        h1_y = aggregate_h_by_year(h1)
        h2_y = aggregate_h_by_year(h2)
        compare_dicts(h1_y, h2_y, "h_dict by year (total fleet)")

    # ---- f_dict comparison ----
    if f_orig and f_rerun:
        print(f"\n  Loading f_dict (flow allocations)...")
        f1 = load_result_dict(f_orig)
        f2 = load_result_dict(f_rerun)

        compare_raw_dicts(f1, f2, "f_dict (flows) - raw key-level")

        f1_yt = aggregate_f_by_year_tech(f1)
        f2_yt = aggregate_f_by_year_tech(f2)
        compare_dicts(f1_yt, f2_yt, "f_dict by (year, tech)")

        f1_y = aggregate_f_by_year(f1)
        f2_y = aggregate_f_by_year(f2)
        compare_dicts(f1_y, f2_y, "f_dict by year (total flow)")

    # ---- s_dict comparison ----
    if s_orig and s_rerun:
        print(f"\n  Loading s_dict (charging)...")
        s1 = load_result_dict(s_orig)
        s2 = load_result_dict(s_rerun)

        compare_raw_dicts(s1, s2, "s_dict (charging) - raw key-level")

        s1_agg = aggregate_s_by_first(s1)
        s2_agg = aggregate_s_by_first(s2)
        compare_dicts(s1_agg, s2_agg, "s_dict by first index (year/period index)")


if __name__ == "__main__":
    # Comparison 1: Unconstrained original vs v2
    run_comparison(
        os.path.join(BASE, "uncertainty_scenarios"),
        os.path.join(BASE, "uncertainty_scenarios_v2"),
        "UNCONSTRAINED: Original (latest) vs V2 Re-run",
        prefix_orig="scenario_000_cs",
        prefix_rerun="scenario_000_cs"
    )

    # Comparison 2: Fixed-fleet original vs v3
    run_comparison(
        os.path.join(BASE, "uncertainty_scenarios_fixed_brk_fleet"),
        os.path.join(BASE, "uncertainty_scenarios_fixed_brk_fleet_v3"),
        "FIXED-FLEET: Original vs V3 Re-run",
        prefix_orig="scenario_000_ff",
        prefix_rerun="scenario_000_ff"
    )
