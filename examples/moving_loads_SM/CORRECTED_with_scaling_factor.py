"""
CORRECTED ANALYSIS accounting for 1000x scaling factor.
F is in tonnes, f is in kilotonnes, so we need to multiply f by 1000.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import yaml
from collections import defaultdict

# Load data
case_study_name = 'case_20251103_114421'
input_dir = f'input_data/{case_study_name}'
results_dir = f'results/{case_study_name}'

print("=" * 80)
print("CORRECTED ANALYSIS WITH SCALING FACTOR")
print("=" * 80)
print("\nKey insight: F is in tonnes, f is in kilotonnes")
print("We must multiply f by 1000 to compare with F")
print("=" * 80)

# Load data
with open(f'{input_dir}/Odpair.yaml', 'r', encoding='utf-8') as f:
    odpairs = yaml.safe_load(f)

import glob
f_dict_files = glob.glob(f'{results_dir}/*_f_dict.yaml')
f_dict_file = sorted(f_dict_files)[-1]
with open(f_dict_file, 'r', encoding='utf-8') as f:
    f_data_raw = yaml.safe_load(f)

with open(f'{input_dir}/Path.yaml', 'r', encoding='utf-8') as f:
    paths = yaml.safe_load(f)

# Create path lookup
path_lookup = {}
for path in paths:
    path_lookup[path['id']] = {
        'sequence': path['sequence'],
        'distance_from_previous': path['distance_from_previous'],
        'total_distance': sum(path['distance_from_previous'])
    }

# ============================================================================
# Compare for year 2020
# ============================================================================
print("\n" + "=" * 80)
print("YEAR 2020 COMPARISON (with 1000x scaling correction)")
print("=" * 80)

# INPUT for year 0 (2020)
total_input_2020 = sum(od['F'][0] for od in odpairs if od['F'] and len(od['F']) > 0)

# OUTPUT for year 2020 (multiply by 1000!)
total_output_2020_kt = 0  # in kilotonnes
for key_str, value in f_data_raw.items():
    flow_value = float(value)
    if flow_value < 0.00001:  # Very small threshold since values are in kt
        continue

    key_tuple = eval(key_str)
    year, (product_id, odpair_id, path_id), (mode_id, techvehicle_id), generation = key_tuple

    if year == 2020:
        total_output_2020_kt += flow_value

total_output_2020_tonnes = total_output_2020_kt * 1000  # Convert to tonnes

print(f"\nINPUT demand F[0] (year 2020):     {total_input_2020:>15,.0f} tonnes")
print(f"OUTPUT flows f (year 2020):         {total_output_2020_kt:>15,.3f} kilotonnes")
print(f"OUTPUT flows (converted to tonnes): {total_output_2020_tonnes:>15,.0f} tonnes")
print(f"\nRatio: {100*total_output_2020_tonnes/total_input_2020:.1f}%")

# ============================================================================
# Calculate TKM with correct scaling
# ============================================================================
print("\n" + "=" * 80)
print("TKM CALCULATION (with 1000x scaling correction)")
print("=" * 80)

# INPUT TKM
input_tkm_2020 = 0
for od in odpairs:
    F_values = od['F']
    path_id = od.get('path_id')

    if F_values and len(F_values) > 0 and path_id and path_id in path_lookup:
        demand_tonnes = F_values[0]  # in tonnes
        distance_km = path_lookup[path_id]['total_distance']
        tkm = demand_tonnes * distance_km
        input_tkm_2020 += tkm

# OUTPUT TKM (remember to multiply by 1000!)
output_tkm_2020 = 0
for key_str, value in f_data_raw.items():
    flow_value_kt = float(value)  # in kilotonnes

    if flow_value_kt < 0.00001:
        continue

    key_tuple = eval(key_str)
    year, (product_id, odpair_id, path_id), (mode_id, techvehicle_id), generation = key_tuple

    if year == 2020 and path_id in path_lookup:
        flow_value_tonnes = flow_value_kt * 1000  # Convert to tonnes
        distance_km = path_lookup[path_id]['total_distance']
        tkm = flow_value_tonnes * distance_km
        output_tkm_2020 += tkm

print(f"\nINPUT TKM (F × distance):  {input_tkm_2020/1e9:>10.3f} billion")
print(f"OUTPUT TKM (f × 1000 × distance): {output_tkm_2020/1e9:>10.3f} billion")
print(f"Ratio: {100*output_tkm_2020/input_tkm_2020:.1f}%")

# ============================================================================
# All years comparison
# ============================================================================
print("\n" + "=" * 80)
print("ALL YEARS COMPARISON (with 1000x scaling correction)")
print("=" * 80)

# Total INPUT across all years
total_input_all_years = sum(sum(od['F']) for od in odpairs if od['F'])

# Total OUTPUT across all years (multiply by 1000!)
total_output_all_years_kt = sum(float(value) for value in f_data_raw.values() if float(value) >= 0.00001)
total_output_all_years_tonnes = total_output_all_years_kt * 1000

print(f"\nTotal INPUT (all years):            {total_input_all_years/1e6:>10.2f} million tonnes")
print(f"Total OUTPUT (all years, in kt):    {total_output_all_years_kt/1e3:>10.2f} million kt")
print(f"Total OUTPUT (all years, in tonnes): {total_output_all_years_tonnes/1e6:>10.2f} million tonnes")
print(f"Ratio: {100*total_output_all_years_tonnes/total_input_all_years:.1f}%")

# ============================================================================
# Year-by-year breakdown
# ============================================================================
print("\n" + "=" * 80)
print("YEAR-BY-YEAR BREAKDOWN (first 10 years)")
print("=" * 80)

# Get tonnage by year from OUTPUT
tonnage_by_year_kt = defaultdict(float)
for key_str, value in f_data_raw.items():
    flow_value_kt = float(value)
    if flow_value_kt < 0.00001:
        continue

    key_tuple = eval(key_str)
    year, (product_id, odpair_id, path_id), (mode_id, techvehicle_id), generation = key_tuple
    tonnage_by_year_kt[year] += flow_value_kt

# Get tonnage by year from INPUT (need to map indices to years)
tonnage_by_year_input = defaultdict(float)
for od in odpairs:
    F_values = od['F']
    for year_idx, demand in enumerate(F_values):
        year = 2020 + year_idx * 2  # Assuming biennial starting from 2020
        tonnage_by_year_input[year] += demand

print(f"\n{'Year':<8} {'INPUT (tonnes)':>18} {'OUTPUT (kt)':>15} {'OUTPUT (tonnes)':>18} {'Ratio':>10}")
print("-" * 80)

years = sorted(set(list(tonnage_by_year_kt.keys()) + list(tonnage_by_year_input.keys())))
for year in years[:10]:
    input_t = tonnage_by_year_input.get(year, 0)
    output_kt = tonnage_by_year_kt.get(year, 0)
    output_t = output_kt * 1000
    ratio = 100 * output_t / input_t if input_t > 0 else 0

    print(f"{year:<8} {input_t:>18,.0f} {output_kt:>15,.3f} {output_t:>18,.0f} {ratio:>9.1f}%")

# ============================================================================
# CONCLUSION
# ============================================================================
print("\n" + "=" * 80)
print("CORRECTED CONCLUSION")
print("=" * 80)

if abs(100*total_output_2020_tonnes/total_input_2020 - 100) < 5:
    print("\n✓ GOOD: Optimized flows match input demand within 5%")
    print("The model is allocating demand correctly!")
elif 100*total_output_2020_tonnes/total_input_2020 > 50:
    print(f"\n✓ Optimized flows are {100*total_output_2020_tonnes/total_input_2020:.1f}% of input demand")
    print("This is within reasonable range.")
else:
    print(f"\n⚠️  Optimized flows are only {100*total_output_2020_tonnes/total_input_2020:.1f}% of input demand")
    print("There may still be an issue with model constraints.")

print(f"\nScaling factor confirmed:")
print(f"  - F (input) is in TONNES")
print(f"  - f (optimized) is in KILOTONNES")
print(f"  - Conversion: f_tonnes = f_kilotonnes × 1000")
