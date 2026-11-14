"""
Analyze the range of F (demand) values in Odpair.yaml
to understand numerical scaling issues
"""

import yaml
import numpy as np
from pathlib import Path

# Find the most recent case directory
input_dir = Path("input_data")
case_dirs = [d for d in input_dir.iterdir() if d.is_dir() and d.name.startswith("case_")]
case_dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)

if not case_dirs:
    print("[ERROR] No case directories found!")
    exit(1)

newest_case = case_dirs[0]
print("="*80)
print(f"ANALYZING DEMAND (F) VALUES IN: {newest_case.name}")
print("="*80)

# Load Odpair.yaml
odpair_file = newest_case / "Odpair.yaml"
if not odpair_file.exists():
    print(f"[ERROR] Odpair.yaml not found in {newest_case.name}")
    exit(1)

with open(odpair_file, 'r', encoding='utf-8') as f:
    odpairs = yaml.safe_load(f)

print(f"\nTotal odpairs: {len(odpairs)}")

# Extract F values (demand)
# F is stored as a list where each element corresponds to a year
f_values = []
num_years = 0

for odpair in odpairs:
    if 'F' in odpair:
        f_list = odpair['F']
        if isinstance(f_list, list):
            f_values.extend(f_list)
            if num_years == 0:
                num_years = len(f_list)
        else:
            f_values.append(f_list)

if not f_values:
    print("[ERROR] No F values found in Odpair data!")
    exit(1)

f_array = np.array(f_values)

print("\n" + "="*80)
print("DEMAND (F) VALUE STATISTICS")
print("="*80)

print(f"\nTotal F entries: {len(f_values)}")
print(f"Number of years: {num_years}")
print(f"Number of odpairs: {len(odpairs)}")

print(f"\nBasic Statistics:")
print(f"  Minimum:    {f_array.min():.6e}")
print(f"  Maximum:    {f_array.max():.6e}")
print(f"  Mean:       {f_array.mean():.6e}")
print(f"  Median:     {np.median(f_array):.6e}")
print(f"  Std Dev:    {f_array.std():.6e}")

print(f"\nRange:")
print(f"  Min/Max ratio: {f_array.min() / f_array.max():.6e}")
print(f"  Orders of magnitude: {np.log10(f_array.max()) - np.log10(f_array.min()):.1f}")

print(f"\nPercentiles:")
percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]
for p in percentiles:
    value = np.percentile(f_array, p)
    print(f"  {p:2d}th: {value:.6e}")

# Count very small values
print("\n" + "="*80)
print("SMALL VALUE ANALYSIS")
print("="*80)

thresholds = [1e-6, 1e-5, 1e-4, 1e-3, 1e-2, 1e-1, 1.0]
for threshold in thresholds:
    count = np.sum(f_array < threshold)
    pct = count / len(f_array) * 100
    print(f"  F < {threshold:.0e}: {count:,} entries ({pct:.1f}%)")

# Count zero or near-zero values
near_zero = np.sum(f_array < 1e-10)
zero = np.sum(f_array == 0)
print(f"\n  F ~= 0 (< 1e-10): {near_zero:,} entries")
print(f"  F == 0:          {zero:,} entries")

# Count very large values
print("\n" + "="*80)
print("LARGE VALUE ANALYSIS")
print("="*80)

thresholds_large = [1.0, 10.0, 100.0, 1000.0, 10000.0, 100000.0]
for threshold in thresholds_large:
    count = np.sum(f_array > threshold)
    pct = count / len(f_array) * 100
    print(f"  F > {threshold:.0e}: {count:,} entries ({pct:.1f}%)")

# Histogram-like distribution
print("\n" + "="*80)
print("DISTRIBUTION (Log scale)")
print("="*80)

# Create log bins
log_min = int(np.floor(np.log10(f_array[f_array > 0].min())))
log_max = int(np.ceil(np.log10(f_array.max())))

print(f"\nValue ranges:")
for log_val in range(log_min, log_max + 1):
    lower = 10**log_val
    upper = 10**(log_val + 1)
    count = np.sum((f_array >= lower) & (f_array < upper))
    pct = count / len(f_array) * 100
    bar = '#' * int(pct / 2)  # Scale bar
    print(f"  [{10**log_val:.0e}, {10**(log_val+1):.0e}): {count:6,} ({pct:5.1f}%) {bar}")

# Numerical stability assessment
print("\n" + "="*80)
print("NUMERICAL STABILITY ASSESSMENT")
print("="*80)

orders_of_magnitude = np.log10(f_array.max()) - np.log10(f_array[f_array > 0].min())

print(f"\nOrders of magnitude in F: {orders_of_magnitude:.1f}")

if orders_of_magnitude > 6:
    print("  [WARNING] >6 orders of magnitude - POOR numerical scaling")
    print("     Recommendation: Scale F values or filter small entries")
elif orders_of_magnitude > 4:
    print("  [CAUTION] 4-6 orders of magnitude - Moderate scaling issues")
    print("     Recommendation: Consider scaling F values")
elif orders_of_magnitude > 3:
    print("  [INFO] 3-4 orders of magnitude - Acceptable scaling")
else:
    print("  [GOOD] <3 orders of magnitude - Good numerical scaling")

# Check if there are values that would cause Gurobi warnings
matrix_range_lower = f_array[f_array > 0].min()
matrix_range_upper = f_array.max()

print(f"\nExpected matrix coefficient range from F:")
print(f"  Lower bound: {matrix_range_lower:.6e}")
print(f"  Upper bound: {matrix_range_upper:.6e}")

if matrix_range_lower < 1e-4:
    print(f"\n  [WARNING] Values < 1e-4 detected - will appear in Gurobi 'Matrix range' warning")
if matrix_range_upper > 1e6:
    print(f"  [WARNING] Values > 1e6 detected - will appear in Gurobi 'Matrix range' warning")

# Recommendations
print("\n" + "="*80)
print("RECOMMENDATIONS")
print("="*80)

if orders_of_magnitude > 4:
    print("\n1. SCALE F VALUES:")
    print("   In SM.jl, scale demand when creating constraints:")
    print("   @constraint(model, f[...] >= F[odpair_id, year] / 1000)")
    print("   This reduces F by 1000x, improving scaling")

    print("\n2. OR FILTER MORE AGGRESSIVELY:")
    small_pct = np.sum(f_array < 0.01) / len(f_array) * 100
    if small_pct > 50:
        print(f"   {small_pct:.1f}% of F values < 0.01")
        print(f"   Consider increasing min_traffic_threshold in preprocessing")

print("\n" + "="*80)

# Show some examples
print("\nSample of smallest F values:")
smallest_idx = np.argsort(f_array)[:10]
for i, idx in enumerate(smallest_idx):
    print(f"  {i+1}. F = {f_array[idx]:.6e}")

print("\nSample of largest F values:")
largest_idx = np.argsort(f_array)[-10:][::-1]
for i, idx in enumerate(largest_idx):
    print(f"  {i+1}. F = {f_array[idx]:.6e}")

print("\n" + "="*80)
