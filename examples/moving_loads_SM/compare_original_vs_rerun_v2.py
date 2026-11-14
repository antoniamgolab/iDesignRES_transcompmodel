"""
Deeper comparison: understand key count differences and whether they matter.
Focus on:
1. Are the "extra" keys in the original near-zero?
2. For common keys, what is the actual magnitude of difference?
3. Separate the s_dict indexing issue from actual value differences.
"""

import os
import re
import ast
import numpy as np
from collections import defaultdict

BASE = r"C:\Users\simuser\Documents\AntoniaGolab\Scand_Med_analysis\SM_baby_2\iDesignRES_transcompmodel\examples\moving_loads_SM\results"


def parse_cartesian_index(s):
    m = re.match(r'CartesianIndex\((.+)\)', s.strip())
    if m:
        inner = m.group(1)
        parts = [x.strip() for x in inner.split(',')]
        return tuple(ast.literal_eval(p) for p in parts)
    return None


def load_result_dict(filepath):
    data = {}
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            idx = line.rfind(': ')
            if idx == -1:
                continue
            key_str = line[:idx].strip()
            val_str = line[idx+2:].strip()
            try:
                value = float(val_str)
            except ValueError:
                continue
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


def analyze_key_differences(d_orig, d_rerun, name):
    """Analyze keys that exist only in original."""
    keys_only_orig = set(d_orig.keys()) - set(d_rerun.keys())
    keys_only_rerun = set(d_rerun.keys()) - set(d_orig.keys())
    common = set(d_orig.keys()) & set(d_rerun.keys())

    print(f"\n{'='*80}")
    print(f"  {name}")
    print(f"{'='*80}")
    print(f"  Keys only in original: {len(keys_only_orig)}")
    print(f"  Keys only in re-run:   {len(keys_only_rerun)}")
    print(f"  Common keys:           {len(common)}")

    if keys_only_orig:
        vals_only_orig = [d_orig[k] for k in keys_only_orig]
        print(f"\n  Values of keys ONLY in original:")
        print(f"    Sum:    {sum(vals_only_orig):.6f}")
        print(f"    Mean:   {np.mean(vals_only_orig):.8f}")
        print(f"    Median: {np.median(vals_only_orig):.8f}")
        print(f"    Max:    {max(vals_only_orig):.8f}")
        print(f"    Min:    {min(vals_only_orig):.8f}")
        print(f"    Std:    {np.std(vals_only_orig):.8f}")
        # How many are near-zero?
        near_zero = sum(1 for v in vals_only_orig if abs(v) < 1e-6)
        small = sum(1 for v in vals_only_orig if abs(v) < 0.01)
        print(f"    |v| < 1e-6: {near_zero} ({near_zero/len(vals_only_orig)*100:.1f}%)")
        print(f"    |v| < 0.01: {small} ({small/len(vals_only_orig)*100:.1f}%)")
        # Total sum of original vs re-run
        total_orig = sum(d_orig.values())
        total_rerun = sum(d_rerun.values())
        sum_only_orig = sum(vals_only_orig)
        print(f"\n    Total sum original:  {total_orig:.4f}")
        print(f"    Total sum re-run:    {total_rerun:.4f}")
        print(f"    Sum of extra keys:   {sum_only_orig:.4f} ({sum_only_orig/total_orig*100:.4f}% of original total)")

    if keys_only_rerun:
        vals_only_rerun = [d_rerun[k] for k in keys_only_rerun]
        print(f"\n  Values of keys ONLY in re-run:")
        print(f"    Sum:    {sum(vals_only_rerun):.6f}")
        print(f"    Mean:   {np.mean(vals_only_rerun):.8f}")
        print(f"    Max:    {max(vals_only_rerun):.8f}")

    # For common keys, analyze differences
    if common:
        diffs = []
        rel_diffs = []
        for k in common:
            v1 = d_orig[k]
            v2 = d_rerun[k]
            diffs.append(v2 - v1)
            if abs(v1) > 1e-10:
                rel_diffs.append((v2 - v1) / abs(v1) * 100)

        diffs = np.array(diffs)
        print(f"\n  Differences on COMMON keys:")
        print(f"    Mean diff:       {np.mean(diffs):.8f}")
        print(f"    Std diff:        {np.std(diffs):.8f}")
        print(f"    Max abs diff:    {np.max(np.abs(diffs)):.8f}")
        print(f"    Mean abs diff:   {np.mean(np.abs(diffs)):.8f}")
        print(f"    Median abs diff: {np.median(np.abs(diffs)):.8f}")

        if rel_diffs:
            rel_diffs = np.array(rel_diffs)
            print(f"    Mean abs rel diff:   {np.mean(np.abs(rel_diffs)):.6f}%")
            print(f"    Median abs rel diff: {np.median(np.abs(rel_diffs)):.6f}%")

        # Count exact matches
        exact = sum(1 for d in diffs if d == 0.0)
        tiny = sum(1 for d in diffs if abs(d) < 1e-6)
        small = sum(1 for d in diffs if abs(d) < 0.01)
        print(f"    Exact matches:   {exact} ({exact/len(common)*100:.1f}%)")
        print(f"    |diff| < 1e-6:   {tiny} ({tiny/len(common)*100:.1f}%)")
        print(f"    |diff| < 0.01:   {small} ({small/len(common)*100:.1f}%)")


def analyze_s_dict_properly(s_orig, s_rerun, name):
    """
    s_dict uses CartesianIndex(year_idx, route_idx, mode_idx, tv_idx, geo_idx).
    The original has 2.2M entries because it includes ALL geo_elements (most with ~0 charging).
    The re-run only saves non-negligible entries.

    We need to compare properly: for keys in the re-run, compare values.
    For keys only in original, check they are small.
    """
    common = set(s_orig.keys()) & set(s_rerun.keys())
    only_orig = set(s_orig.keys()) - set(s_rerun.keys())
    only_rerun = set(s_rerun.keys()) - set(s_orig.keys())

    print(f"\n{'='*80}")
    print(f"  {name}")
    print(f"{'='*80}")
    print(f"  Original keys:  {len(s_orig)}")
    print(f"  Re-run keys:    {len(s_rerun)}")
    print(f"  Only original:  {len(only_orig)}")
    print(f"  Only re-run:    {len(only_rerun)}")
    print(f"  Common keys:    {len(common)}")

    # The s_dict structure: values are total charging at a geo_element for a route/year.
    # The original likely saves all (year, route, mode, tv, geo_element) combos.
    # The re-run only saves where charging > 0 (or above some threshold).

    # Check: sum of values in keys only in original
    if only_orig:
        vals_only = [s_orig[k] for k in only_orig]
        total_only = sum(vals_only)
        total_orig = sum(s_orig.values())
        total_rerun = sum(s_rerun.values())
        print(f"\n  Total sum original:     {total_orig:.2f}")
        print(f"  Total sum re-run:       {total_rerun:.2f}")
        print(f"  Sum only-in-original:   {total_only:.2f} ({total_only/total_orig*100:.4f}% of original)")
        print(f"  Grand total diff:       {total_rerun - total_orig:.2f} ({(total_rerun - total_orig)/total_orig*100:.6f}%)")

        # Distribution of "only in original" values
        vals_arr = np.array(vals_only)
        print(f"\n  Distribution of only-in-original values:")
        print(f"    Mean:   {np.mean(vals_arr):.6f}")
        print(f"    Median: {np.median(vals_arr):.6f}")
        print(f"    Max:    {np.max(vals_arr):.6f}")
        print(f"    Min:    {np.min(vals_arr):.6f}")
        near_zero = sum(1 for v in vals_arr if abs(v) < 1e-6)
        small = sum(1 for v in vals_arr if abs(v) < 1.0)
        print(f"    |v| < 1e-6: {near_zero} ({near_zero/len(vals_arr)*100:.1f}%)")
        print(f"    |v| < 1.0:  {small} ({small/len(vals_arr)*100:.1f}%)")

    # For common keys: the "raw" comparison was misleading because it compared
    # individual (route, geo_element) pairs. Due to solver degeneracy, the model
    # can spread charging differently across nodes for the same total.
    # Let's aggregate by (year_idx, route_idx) to see if totals per route match.

    print(f"\n  Aggregating common keys by (year_idx, route_idx)...")
    agg_orig = defaultdict(float)
    agg_rerun = defaultdict(float)

    for k in s_rerun.keys():  # Use all re-run keys as reference
        yr, route = k[0], k[1]
        agg_rerun[(yr, route)] += s_rerun[k]

    for k in s_orig.keys():
        yr, route = k[0], k[1]
        agg_orig[(yr, route)] += s_orig[k]

    # Compare on common (year, route) pairs
    common_yr_route = set(agg_orig.keys()) & set(agg_rerun.keys())
    print(f"  Common (year, route) pairs: {len(common_yr_route)}")

    if common_yr_route:
        diffs_yr_route = []
        rel_diffs_yr_route = []
        for k in common_yr_route:
            v1 = agg_orig[k]
            v2 = agg_rerun[k]
            diffs_yr_route.append(v2 - v1)
            if abs(v1) > 1e-6:
                rel_diffs_yr_route.append(abs(v2 - v1) / abs(v1) * 100)

        diffs_arr = np.array(diffs_yr_route)
        print(f"  Per-(year,route) total charging differences:")
        print(f"    Mean diff:       {np.mean(diffs_arr):.6f}")
        print(f"    Mean abs diff:   {np.mean(np.abs(diffs_arr)):.6f}")
        print(f"    Median abs diff: {np.median(np.abs(diffs_arr)):.6f}")
        print(f"    Max abs diff:    {np.max(np.abs(diffs_arr)):.6f}")
        if rel_diffs_yr_route:
            rda = np.array(rel_diffs_yr_route)
            print(f"    Mean abs rel diff:   {np.mean(rda):.6f}%")
            print(f"    Median abs rel diff: {np.median(rda):.6f}%")
            print(f"    90th pctl rel diff:  {np.percentile(rda, 90):.6f}%")
            print(f"    99th pctl rel diff:  {np.percentile(rda, 99):.6f}%")

    # Also aggregate by year_idx only
    agg_orig_y = defaultdict(float)
    agg_rerun_y = defaultdict(float)
    for k, v in s_orig.items():
        agg_orig_y[k[0]] += v
    for k, v in s_rerun.items():
        agg_rerun_y[k[0]] += v

    print(f"\n  Per-year total charging comparison:")
    print(f"  {'YearIdx':>10} {'Original':>18} {'Re-run':>18} {'AbsDiff':>15} {'RelDiff%':>12}")
    for yr in sorted(set(agg_orig_y.keys()) | set(agg_rerun_y.keys())):
        v1 = agg_orig_y.get(yr, 0)
        v2 = agg_rerun_y.get(yr, 0)
        ad = v2 - v1
        rd = ad / abs(v1) * 100 if abs(v1) > 0 else 0
        print(f"  {yr:>10} {v1:>18.2f} {v2:>18.2f} {ad:>15.4f} {rd:>11.6f}%")


if __name__ == "__main__":
    print("PART 1: h_dict key analysis (UNCONSTRAINED)")
    h_orig_path = os.path.join(BASE, "uncertainty_scenarios", "scenario_000",
                                "scenario_000_cs_2026-02-11_11-52-48_h_dict.yaml")
    h_rerun_path = os.path.join(BASE, "uncertainty_scenarios_v2", "scenario_000",
                                 "scenario_000_cs_2026-02-14_18-25-42_h_dict.yaml")

    print("  Loading h_dict original...")
    h_orig = load_result_dict(h_orig_path)
    print("  Loading h_dict re-run...")
    h_rerun = load_result_dict(h_rerun_path)
    analyze_key_differences(h_orig, h_rerun, "h_dict (UNCONSTRAINED): original vs v2")

    print("\n\nPART 2: s_dict deep analysis (UNCONSTRAINED)")
    s_orig_path = os.path.join(BASE, "uncertainty_scenarios", "scenario_000",
                                "scenario_000_cs_2026-02-11_11-52-48_s_dict.yaml")
    s_rerun_path = os.path.join(BASE, "uncertainty_scenarios_v2", "scenario_000",
                                 "scenario_000_cs_2026-02-14_18-25-42_s_dict.yaml")

    print("  Loading s_dict original (2.2M lines, this may take a minute)...")
    s_orig = load_result_dict(s_orig_path)
    print("  Loading s_dict re-run...")
    s_rerun = load_result_dict(s_rerun_path)
    analyze_s_dict_properly(s_orig, s_rerun, "s_dict (UNCONSTRAINED): original vs v2")

    print("\n\nPART 3: FIXED-FLEET s_dict deep analysis")
    s_ff_orig_path = os.path.join(BASE, "uncertainty_scenarios_fixed_brk_fleet", "scenario_000",
                                   "scenario_000_ff_2026-02-14_16-45-30_s_dict.yaml")
    s_ff_rerun_path = os.path.join(BASE, "uncertainty_scenarios_fixed_brk_fleet_v3", "scenario_000",
                                    "scenario_000_ff_2026-02-14_18-57-14_s_dict.yaml")

    print("  Loading fixed-fleet s_dict original (2.2M lines)...")
    s_ff_orig = load_result_dict(s_ff_orig_path)
    print("  Loading fixed-fleet s_dict re-run...")
    s_ff_rerun = load_result_dict(s_ff_rerun_path)
    analyze_s_dict_properly(s_ff_orig, s_ff_rerun, "s_dict (FIXED-FLEET): original vs v3")

    print("\n\n" + "="*80)
    print("  OVERALL VERDICT")
    print("="*80)
