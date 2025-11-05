"""
Analyze the year dimension in both INPUT (F) and OPTIMIZED (f) to understand
if the 94.5% tonnage reduction is due to year indexing mismatch.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import yaml
from collections import defaultdict
import numpy as np

# Load data
case_study_name = 'case_20251103_114421'
input_dir = f'input_data/{case_study_name}'
results_dir = f'results/{case_study_name}'

print("=" * 80)
print("YEAR DIMENSION ANALYSIS")
print("=" * 80)

# Load data
print("\nLoading data files...")
with open(f'{input_dir}/Odpair.yaml', 'r', encoding='utf-8') as f:
    odpairs = yaml.safe_load(f)

import glob
f_dict_files = glob.glob(f'{results_dir}/*_f_dict.yaml')
f_dict_file = sorted(f_dict_files)[-1]
with open(f_dict_file, 'r', encoding='utf-8') as f:
    f_data_raw = yaml.safe_load(f)

print("Data loaded successfully")

# ============================================================================
# Analyze INPUT demand F structure
# ============================================================================
print("\n" + "=" * 80)
print("INPUT DEMAND (F) STRUCTURE")
print("=" * 80)

# Check how many years of data in F
F_lengths = []
for od in odpairs:
    F_values = od['F']
    if F_values:
        F_lengths.append(len(F_values))

print(f"\nNumber of OD pairs: {len(odpairs)}")
print(f"\nF (demand) array lengths:")
print(f"  Min:     {min(F_lengths) if F_lengths else 0}")
print(f"  Max:     {max(F_lengths) if F_lengths else 0}")
print(f"  Mean:    {np.mean(F_lengths) if F_lengths else 0:.1f}")
print(f"  Median:  {np.median(F_lengths) if F_lengths else 0:.0f}")

# Most common length
from collections import Counter
length_counts = Counter(F_lengths)
print(f"\nMost common F array length: {length_counts.most_common(1)[0][0]} (appears in {length_counts.most_common(1)[0][1]} OD pairs)")

# Sum tonnage by year index
tonnage_by_year_index = defaultdict(float)
max_years = max(F_lengths) if F_lengths else 0

for year_idx in range(max_years):
    for od in odpairs:
        F_values = od['F']
        if F_values and year_idx < len(F_values):
            tonnage_by_year_index[year_idx] += F_values[year_idx]

print(f"\n INPUT tonnage by year index (first 10 years):")
print("-" * 60)
print(f"{'Year Index':<12} {'Tonnage (tonnes)':>20} {'TKM (approx)':>20}")
print("-" * 60)

# For TKM, we need to multiply by average distance
# Let's estimate average distance first
from yaml import safe_load
with open(f'{input_dir}/Path.yaml', 'r', encoding='utf-8') as f:
    paths = yaml.safe_load(f)

path_distances = {}
for path in paths:
    path_distances[path['id']] = sum(path['distance_from_previous'])

avg_distance = np.mean(list(path_distances.values()))
print(f"\nAverage path distance: {avg_distance:.1f} km")
print()

for year_idx in range(min(10, max_years)):
    tonnage = tonnage_by_year_index[year_idx]
    tkm_approx = tonnage * avg_distance
    print(f"{year_idx:<12} {tonnage:>20,.0f} {tkm_approx/1e9:>19.3f}B")

total_input_all_years = sum(tonnage_by_year_index.values())
print("-" * 60)
print(f"{'TOTAL (all years)':<12} {total_input_all_years:>20,.0f}")

# ============================================================================
# Analyze OPTIMIZED flows f structure
# ============================================================================
print("\n" + "=" * 80)
print("OPTIMIZED FLOWS (f) STRUCTURE")
print("=" * 80)

# Extract year values from keys
years_in_f = set()
tonnage_by_year_f = defaultdict(float)
mode_by_year = defaultdict(lambda: {'road': 0, 'rail': 0})

for key_str, value in f_data_raw.items():
    flow_value = float(value)

    if flow_value < 0.01:
        continue

    key_tuple = eval(key_str)
    year, (product_id, odpair_id, path_id), (mode_id, techvehicle_id), generation = key_tuple

    years_in_f.add(year)
    tonnage_by_year_f[year] += flow_value

    mode_name = 'rail' if mode_id == 2 else 'road'
    mode_by_year[year][mode_name] += flow_value

print(f"\nYears present in optimized flows:")
print(f"  Years: {sorted(years_in_f)}")
print(f"  Number of years: {len(years_in_f)}")
print(f"  Year range: {min(years_in_f)} - {max(years_in_f)}")

print(f"\nOptimized tonnage by year (first 10 years):")
print("-" * 80)
print(f"{'Year':<12} {'Road (tonnes)':>20} {'Rail (tonnes)':>20} {'Total (tonnes)':>20}")
print("-" * 80)

sorted_years = sorted(years_in_f)
for year in sorted_years[:10]:
    road_tonnage = mode_by_year[year]['road']
    rail_tonnage = mode_by_year[year]['rail']
    total_tonnage = road_tonnage + rail_tonnage
    print(f"{year:<12} {road_tonnage:>20,.0f} {rail_tonnage:>20,.0f} {total_tonnage:>20,.0f}")

total_output_all_years = sum(tonnage_by_year_f.values())
print("-" * 80)
print(f"{'TOTAL (all years)':<12} {'':>20} {'':>20} {total_output_all_years:>20,.0f}")

# ============================================================================
# Compare F vs f for matching years
# ============================================================================
print("\n" + "=" * 80)
print("COMPARISON: INPUT F vs OPTIMIZED f BY YEAR")
print("=" * 80)

# We need to map year indices in F to calendar years
# Let's check if there's a base year defined
print("\nAssuming F[0] corresponds to first optimization year...")

# Get the minimum year from optimized flows
min_year_f = min(years_in_f)

print(f"\nOptimized flows start year: {min_year_f}")
print(f"\nMapping assumption: F[0] = year {min_year_f}")

print(f"\n{'Year':<8} {'F Index':<10} {'INPUT F (tonnes)':>20} {'OUTPUT f (tonnes)':>20} {'Ratio':>10}")
print("-" * 80)

for year in sorted(years_in_f)[:20]:  # First 20 years
    year_idx = year - min_year_f

    if year_idx < len(tonnage_by_year_index):
        input_tonnage = tonnage_by_year_index[year_idx]
        output_tonnage = tonnage_by_year_f[year]
        ratio = output_tonnage / input_tonnage if input_tonnage > 0 else 0

        print(f"{year:<8} {year_idx:<10} {input_tonnage:>20,.0f} {output_tonnage:>20,.0f} {100*ratio:>9.1f}%")

# ============================================================================
# CONCLUSION
# ============================================================================
print("\n" + "=" * 80)
print("DIAGNOSIS")
print("=" * 80)

print(f"\nINPUT (F):")
print(f"  - Contains {max_years} year indices (0 to {max_years-1})")
print(f"  - Total tonnage across all years: {total_input_all_years/1e6:.2f} million tonnes")
print(f"  - Average per year: {total_input_all_years/max_years/1e6:.2f} million tonnes")

print(f"\nOUTPUT (f):")
print(f"  - Contains {len(years_in_f)} calendar years ({min(years_in_f)} to {max(years_in_f)})")
print(f"  - Total tonnage across all years: {total_output_all_years/1e6:.2f} million tonnes")
print(f"  - Average per year: {total_output_all_years/len(years_in_f)/1e6:.2f} million tonnes")

print(f"\nRATIO:")
print(f"  - Total OUTPUT / Total INPUT: {100*total_output_all_years/total_input_all_years:.1f}%")

# Check if any single year in f matches any year in F
print("\nLooking for year-to-year matches:")
min_ratio = 100.0
max_ratio = 0.0
for year in sorted(years_in_f):
    year_idx = year - min_year_f
    if year_idx < len(tonnage_by_year_index):
        input_tonnage = tonnage_by_year_index[year_idx]
        output_tonnage = tonnage_by_year_f[year]
        if input_tonnage > 0:
            ratio = 100 * output_tonnage / input_tonnage
            if ratio < min_ratio:
                min_ratio = ratio
            if ratio > max_ratio:
                max_ratio = ratio

print(f"  Year-to-year ratio range: {min_ratio:.1f}% - {max_ratio:.1f}%")

if max_ratio < 10:
    print("\n⚠️  CRITICAL: Even for individual years, optimized flow is < 10% of input!")
    print("    This suggests the model is heavily constrained or has an issue.")
elif min_ratio > 90 and max_ratio < 110:
    print("\n✓ Year-to-year ratios are close to 100% - data is consistent")
else:
    print(f"\n⚠️  Year-to-year ratios vary widely ({min_ratio:.1f}% - {max_ratio:.1f}%)")
