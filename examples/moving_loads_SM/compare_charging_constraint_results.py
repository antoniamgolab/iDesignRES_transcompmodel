"""
Compare results between baseline (no charging constraint) and with charging-at-breaks-only constraint.

This script analyzes the impact of restricting BEV charging to mandatory break locations only.
"""

import yaml
import os
from collections import defaultdict

# Define paths
BASE_DIR = r"C:\Users\simuser\Documents\AntoniaGolab\Scand_Med_analysis\SM_baby_2\iDesignRES_transcompmodel\examples\moving_loads_SM"
RESULTS_DIR = os.path.join(BASE_DIR, "results")

# Result file paths - Fresh comparison runs from 2025-12-05
BASELINE_PREFIX = os.path.join(RESULTS_DIR, "comparison_charging_constraint", "comparison_WITHOUT_constraint_2025-12-05_15-56-44")
CONSTRAINED_PREFIX = os.path.join(RESULTS_DIR, "comparison_charging_constraint", "comparison_WITH_constraint_2025-12-05_15-57-49")

def load_yaml(filepath):
    """Load a YAML file."""
    print(f"Loading: {os.path.basename(filepath)}")
    with open(filepath, 'r') as f:
        return yaml.safe_load(f)

def compare_s_variable(baseline_s, constrained_s):
    """Compare charging (s variable) patterns between baseline and constrained runs."""
    print("\n" + "="*80)
    print("COMPARISON: Charging Pattern (s variable)")
    print("="*80)

    # Aggregate by year
    baseline_by_year = defaultdict(float)
    constrained_by_year = defaultdict(float)

    # Count non-zero entries
    baseline_nonzero = 0
    constrained_nonzero = 0

    for key, value in baseline_s.items():
        # Convert value to float if string
        val = float(value) if isinstance(value, str) else value
        if val > 1e-6:  # Non-zero threshold
            baseline_nonzero += 1
            # Extract year from key (first element)
            if isinstance(key, str):
                parts = key.strip("()").split(",")
                year = int(parts[0].strip())
            else:
                year = key[0]
            baseline_by_year[year] += val

    for key, value in constrained_s.items():
        val = float(value) if isinstance(value, str) else value
        if val > 1e-6:
            constrained_nonzero += 1
            if isinstance(key, str):
                parts = key.strip("()").split(",")
                year = int(parts[0].strip())
            else:
                year = key[0]
            constrained_by_year[year] += val

    print(f"\nNon-zero charging locations:")
    print(f"  Baseline:    {baseline_nonzero:,}")
    print(f"  Constrained: {constrained_nonzero:,}")
    print(f"  Reduction:   {baseline_nonzero - constrained_nonzero:,} ({100*(baseline_nonzero - constrained_nonzero)/max(baseline_nonzero, 1):.1f}%)")

    print(f"\nTotal charging by year (kWh):")
    years = sorted(set(baseline_by_year.keys()) | set(constrained_by_year.keys()))
    for year in years:
        b_val = baseline_by_year.get(year, 0)
        c_val = constrained_by_year.get(year, 0)
        diff = c_val - b_val
        diff_pct = 100 * diff / max(b_val, 1e-6)
        print(f"  {year}: Baseline={b_val:,.0f}, Constrained={c_val:,.0f}, Diff={diff:+,.0f} ({diff_pct:+.2f}%)")

    total_baseline = sum(baseline_by_year.values())
    total_constrained = sum(constrained_by_year.values())
    print(f"\n  TOTAL: Baseline={total_baseline:,.0f}, Constrained={total_constrained:,.0f}")
    print(f"         Difference: {total_constrained - total_baseline:+,.0f} ({100*(total_constrained - total_baseline)/max(total_baseline, 1):+.2f}%)")

    return baseline_by_year, constrained_by_year

def compare_f_variable(baseline_f, constrained_f):
    """Compare flow (f variable) patterns - this represents vehicle-km by technology."""
    print("\n" + "="*80)
    print("COMPARISON: Vehicle Flows (f variable)")
    print("="*80)

    # Aggregate by year and technology
    baseline_by_year = defaultdict(float)
    constrained_by_year = defaultdict(float)

    for key, value in baseline_f.items():
        val = float(value) if isinstance(value, str) else value
        if val > 1e-6:
            if isinstance(key, str):
                parts = key.strip("()").split(",")
                year = int(parts[0].strip())
            else:
                year = key[0]
            baseline_by_year[year] += val

    for key, value in constrained_f.items():
        val = float(value) if isinstance(value, str) else value
        if val > 1e-6:
            if isinstance(key, str):
                parts = key.strip("()").split(",")
                year = int(parts[0].strip())
            else:
                year = key[0]
            constrained_by_year[year] += val

    print(f"\nTotal vehicle flows by year:")
    years = sorted(set(baseline_by_year.keys()) | set(constrained_by_year.keys()))
    for year in years:
        b_val = baseline_by_year.get(year, 0)
        c_val = constrained_by_year.get(year, 0)
        diff = c_val - b_val
        diff_pct = 100 * diff / max(b_val, 1e-6)
        print(f"  {year}: Baseline={b_val:,.0f}, Constrained={c_val:,.0f}, Diff={diff:+,.0f} ({diff_pct:+.2f}%)")

    return baseline_by_year, constrained_by_year

def compare_h_plus_variable(baseline_h, constrained_h):
    """Compare vehicle purchases (h_plus variable)."""
    print("\n" + "="*80)
    print("COMPARISON: Vehicle Purchases (h_plus variable)")
    print("="*80)

    # Aggregate by year
    baseline_by_year = defaultdict(float)
    constrained_by_year = defaultdict(float)

    for key, value in baseline_h.items():
        val = float(value) if isinstance(value, str) else value
        if val > 1e-6:
            if isinstance(key, str):
                parts = key.strip("()").split(",")
                year = int(parts[0].strip())
            else:
                year = key[0]
            baseline_by_year[year] += val

    for key, value in constrained_h.items():
        val = float(value) if isinstance(value, str) else value
        if val > 1e-6:
            if isinstance(key, str):
                parts = key.strip("()").split(",")
                year = int(parts[0].strip())
            else:
                year = key[0]
            constrained_by_year[year] += val

    print(f"\nTotal vehicle purchases by year:")
    years = sorted(set(baseline_by_year.keys()) | set(constrained_by_year.keys()))
    for year in years:
        b_val = baseline_by_year.get(year, 0)
        c_val = constrained_by_year.get(year, 0)
        diff = c_val - b_val
        diff_pct = 100 * diff / max(b_val, 1e-6)
        print(f"  {year}: Baseline={b_val:,.0f}, Constrained={c_val:,.0f}, Diff={diff:+,.0f} ({diff_pct:+.2f}%)")

    return baseline_by_year, constrained_by_year

def compare_infrastructure(baseline_infr, constrained_infr):
    """Compare infrastructure deployment (q_fuel_infr_plus variable)."""
    print("\n" + "="*80)
    print("COMPARISON: Infrastructure Deployment (q_fuel_infr_plus)")
    print("="*80)

    # Aggregate by year
    baseline_by_year = defaultdict(float)
    constrained_by_year = defaultdict(float)

    for key, value in baseline_infr.items():
        val = float(value) if isinstance(value, str) else value
        if val > 1e-6:
            if isinstance(key, str):
                parts = key.strip("()").split(",")
                year = int(parts[0].strip())
            else:
                year = key[0]
            baseline_by_year[year] += val

    for key, value in constrained_infr.items():
        val = float(value) if isinstance(value, str) else value
        if val > 1e-6:
            if isinstance(key, str):
                parts = key.strip("()").split(",")
                year = int(parts[0].strip())
            else:
                year = key[0]
            constrained_by_year[year] += val

    print(f"\nTotal infrastructure by year:")
    years = sorted(set(baseline_by_year.keys()) | set(constrained_by_year.keys()))
    for year in years:
        b_val = baseline_by_year.get(year, 0)
        c_val = constrained_by_year.get(year, 0)
        diff = c_val - b_val
        diff_pct = 100 * diff / max(b_val, 1e-6)
        print(f"  {year}: Baseline={b_val:,.0f}, Constrained={c_val:,.0f}, Diff={diff:+,.0f} ({diff_pct:+.2f}%)")

    total_baseline = sum(baseline_by_year.values())
    total_constrained = sum(constrained_by_year.values())
    print(f"\n  TOTAL: Baseline={total_baseline:,.0f}, Constrained={total_constrained:,.0f}")
    print(f"         Difference: {total_constrained - total_baseline:+,.0f} ({100*(total_constrained - total_baseline)/max(total_baseline, 1):+.2f}%)")

    return baseline_by_year, constrained_by_year

def main():
    print("="*80)
    print("RESULTS COMPARISON: Charging at Breaks Only Constraint")
    print("="*80)
    print(f"\nBaseline (no constraint): {os.path.basename(BASELINE_PREFIX)}")
    print(f"Constrained run:          {os.path.basename(CONSTRAINED_PREFIX)}")

    # Check if files exist
    baseline_s_path = f"{BASELINE_PREFIX}_s_dict.yaml"
    constrained_s_path = f"{CONSTRAINED_PREFIX}_s_dict.yaml"

    if not os.path.exists(baseline_s_path):
        print(f"\nERROR: Baseline s_dict not found: {baseline_s_path}")
        return
    if not os.path.exists(constrained_s_path):
        print(f"\nERROR: Constrained s_dict not found: {constrained_s_path}")
        return

    # Load and compare s variable (charging)
    print("\nLoading s_dict files...")
    baseline_s = load_yaml(baseline_s_path)
    constrained_s = load_yaml(constrained_s_path)
    compare_s_variable(baseline_s, constrained_s)

    # Load and compare f variable (flows)
    print("\nLoading f_dict files...")
    baseline_f = load_yaml(f"{BASELINE_PREFIX}_f_dict.yaml")
    constrained_f = load_yaml(f"{CONSTRAINED_PREFIX}_f_dict.yaml")
    compare_f_variable(baseline_f, constrained_f)

    # Load and compare h_plus variable (vehicle purchases)
    print("\nLoading h_plus_dict files...")
    baseline_h = load_yaml(f"{BASELINE_PREFIX}_h_plus_dict.yaml")
    constrained_h = load_yaml(f"{CONSTRAINED_PREFIX}_h_plus_dict.yaml")
    compare_h_plus_variable(baseline_h, constrained_h)

    # Load and compare infrastructure
    print("\nLoading q_fuel_infr_plus_dict files...")
    baseline_infr = load_yaml(f"{BASELINE_PREFIX}_q_fuel_infr_plus_dict.yaml")
    constrained_infr = load_yaml(f"{CONSTRAINED_PREFIX}_q_fuel_infr_plus_dict.yaml")
    compare_infrastructure(baseline_infr, constrained_infr)

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print("""
The charging-at-breaks-only constraint restricts BEV charging to locations
where mandatory driver breaks occur (every ~360 km for 45 minutes).

Key impacts to look for:
1. Reduced number of charging locations (s variable non-zero entries)
2. Changes in total energy charged (should be similar if feasible)
3. Potential changes in vehicle fleet composition (h_plus)
4. Infrastructure deployment patterns (q_fuel_infr_plus)
""")

if __name__ == "__main__":
    main()
