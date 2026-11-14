"""
Debug script to verify BEV share calculation for uncertainty analysis results.
Run this to check what data is actually loaded and what the BEV shares are.
"""

import yaml
import os
import ast
from glob import glob
from collections import defaultdict
import datetime

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
BASELINE_DIR = os.path.join(RESULTS_DIR, "uncertainty_analysis")
CONSTRAINED_DIR = os.path.join(RESULTS_DIR, "uncertainty_analysis_with_breaks")

def get_latest_file(folder, pattern):
    """Get the most recent file matching a pattern in a folder."""
    files = glob(os.path.join(folder, f"*{pattern}"))
    if not files:
        return None
    return max(files, key=os.path.getmtime)

def parse_key_to_year(key):
    """Extract year from a key string like '(2020, ...)' or tuple."""
    if isinstance(key, str):
        parts = key.strip("()").split(",")
        return int(parts[0].strip())
    elif isinstance(key, tuple):
        return key[0]
    return None

def parse_key_to_tech(key):
    """Extract tech_id from h_dict key - format: (year, odpair_id, tech_vehicle_id, generation)."""
    if isinstance(key, str):
        parts = key.strip("()").split(",")
        if len(parts) >= 3:
            return int(parts[2].strip())
    elif isinstance(key, tuple) and len(key) >= 3:
        return key[2]
    return None

def aggregate_h_by_year_and_tech(h_dict):
    """Aggregate vehicle stock by year and technology."""
    if h_dict is None:
        return {}

    result = defaultdict(lambda: defaultdict(float))

    for key, value in h_dict.items():
        val = float(value) if isinstance(value, str) else value
        if val > 1e-6:
            year = parse_key_to_year(key)
            tech = parse_key_to_tech(key)
            if year is not None and tech is not None:
                result[year][tech] += val

    return dict(result)

def calc_bev_share(h_by_year_tech, years):
    """Calculate BEV share as percentage of total fleet."""
    bev_share = {}
    for year in years:
        if year in h_by_year_tech:
            total = sum(h_by_year_tech[year].values())
            bev = sum(v for k, v in h_by_year_tech[year].items() if k == 1 or k == '1')
            bev_share[year] = 100 * bev / total if total > 0 else 0
    return bev_share

def main():
    print("=" * 80)
    print("DEBUG BEV SHARE CALCULATION")
    print("=" * 80)

    years = [2020, 2024, 2028, 2032, 2036, 2040, 2044, 2048, 2052, 2056, 2060]

    # Check scenario_000 from both runs
    for label, base_dir in [("BASELINE (no constraint)", BASELINE_DIR),
                             ("CONSTRAINED (charging at breaks)", CONSTRAINED_DIR)]:
        print(f"\n{label}")
        print("-" * 60)

        scenario_folder = os.path.join(base_dir, "scenario_000")
        if not os.path.exists(scenario_folder):
            print(f"  Folder not found: {scenario_folder}")
            continue

        # Find all h_dict files
        h_files = [f for f in os.listdir(scenario_folder) if 'h_dict' in f]
        print(f"  Found {len(h_files)} h_dict files:")
        for f in sorted(h_files):
            mtime = datetime.datetime.fromtimestamp(os.path.getmtime(os.path.join(scenario_folder, f)))
            print(f"    - {f} (modified: {mtime})")

        # Get the latest file
        h_file = get_latest_file(scenario_folder, "h_dict.yaml")
        if not h_file:
            print("  No h_dict file found!")
            continue

        print(f"\n  Using latest file: {os.path.basename(h_file)}")

        # Load the data
        with open(h_file, 'r') as f:
            h_dict = yaml.safe_load(f)

        print(f"  Total keys in h_dict: {len(h_dict)}")

        # Show first 3 keys
        print("  First 3 keys:")
        for i, (k, v) in enumerate(list(h_dict.items())[:3]):
            print(f"    {k}: {v}")

        # Aggregate and calculate BEV share
        h_agg = aggregate_h_by_year_and_tech(h_dict)
        bev_shares = calc_bev_share(h_agg, years)

        print(f"\n  BEV share by year:")
        for year in sorted(h_agg.keys()):
            tech_data = h_agg[year]
            total = sum(tech_data.values())
            bev = tech_data.get(1, 0) + tech_data.get('1', 0)
            icev = tech_data.get(0, 0) + tech_data.get('0', 0)
            bev_share = 100 * bev / total if total > 0 else 0
            print(f"    {year}: BEV={bev_share:.1f}% (BEV={bev:.1f}, ICEV={icev:.1f}, total={total:.1f})")

if __name__ == "__main__":
    main()
