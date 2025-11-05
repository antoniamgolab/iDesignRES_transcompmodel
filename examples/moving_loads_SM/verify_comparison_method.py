"""
Verify the comparison method - properly compare INPUT vs OUTPUT for matching years.
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
print("VERIFICATION: PROPER COMPARISON OF INPUT vs OUTPUT")
print("=" * 80)

# Load data
with open(f'{input_dir}/Odpair.yaml', 'r', encoding='utf-8') as f:
    odpairs = yaml.safe_load(f)

import glob
f_dict_files = glob.glob(f'{results_dir}/*_f_dict.yaml')
f_dict_file = sorted(f_dict_files)[-1]
with open(f_dict_file, 'r', encoding='utf-8') as f:
    f_data_raw = yaml.safe_load(f)

print("\n" + "=" * 80)
print("METHOD 1: Compare single year (2020)")
print("=" * 80)

# INPUT for year 0 (assuming this is 2020)
input_year_0 = 0
total_input_year_0 = sum(od['F'][input_year_0] for od in odpairs if od['F'] and len(od['F']) > input_year_0)

print(f"\nINPUT demand F[0] (year 2020): {total_input_year_0:,.0f} tonnes")

# OUTPUT for year 2020
output_year_2020 = 0
for key_str, value in f_data_raw.items():
    flow_value = float(value)
    if flow_value < 0.01:
        continue

    key_tuple = eval(key_str)
    year, (product_id, odpair_id, path_id), (mode_id, techvehicle_id), generation = key_tuple

    if year == 2020:
        output_year_2020 += flow_value

print(f"OUTPUT flows f (year 2020):     {output_year_2020:,.0f} tonnes")
print(f"Ratio: {100*output_year_2020/total_input_year_0:.2f}%")

print("\n" + "=" * 80)
print("METHOD 2: Compare by OD pair (year 2020)")
print("=" * 80)

# For each OD pair, compare INPUT F[0] vs sum of OUTPUT flows for year 2020
odpair_comparison = {}

for od in odpairs:
    odpair_id = od['id']
    F_values = od['F']

    if F_values and len(F_values) > 0:
        input_demand = F_values[0]  # Year 0
    else:
        input_demand = 0

    # Sum output flows for this OD pair in year 2020
    output_flow = 0
    for key_str, value in f_data_raw.items():
        flow_value = float(value)
        if flow_value < 0.01:
            continue

        key_tuple = eval(key_str)
        year, (product_id, od_id, path_id), (mode_id, techvehicle_id), generation = key_tuple

        if year == 2020 and od_id == odpair_id:
            output_flow += flow_value

    odpair_comparison[odpair_id] = {
        'input': input_demand,
        'output': output_flow,
        'ratio': output_flow / input_demand if input_demand > 0 else 0
    }

# Calculate statistics
total_input = sum(c['input'] for c in odpair_comparison.values())
total_output = sum(c['output'] for c in odpair_comparison.values())

print(f"\nTotal INPUT (F[0]):  {total_input:,.0f} tonnes")
print(f"Total OUTPUT (2020): {total_output:,.0f} tonnes")
print(f"Overall ratio: {100*total_output/total_input:.2f}%")

# How many OD pairs have non-zero output?
od_with_output = sum(1 for c in odpair_comparison.values() if c['output'] > 0.01)
od_with_input = sum(1 for c in odpair_comparison.values() if c['input'] > 0.01)

print(f"\nOD pairs with INPUT demand: {od_with_input}")
print(f"OD pairs with OUTPUT flows: {od_with_output}")
print(f"Coverage: {100*od_with_output/od_with_input:.1f}%")

# Show sample OD pairs with highest input
print("\nTop 10 OD pairs by INPUT demand (year 0):")
print("-" * 80)
print(f"{'OD ID':<10} {'INPUT':>15} {'OUTPUT':>15} {'Ratio':>10}")
print("-" * 80)

sorted_by_input = sorted(odpair_comparison.items(), key=lambda x: x[1]['input'], reverse=True)
for odpair_id, data in sorted_by_input[:10]:
    print(f"{odpair_id:<10} {data['input']:>15,.0f} {data['output']:>15,.0f} {100*data['ratio']:>9.1f}%")

print("\n" + "=" * 80)
print("METHOD 3: Check if flows are distributed across modes/techvehicles")
print("=" * 80)

# For a single OD pair with high input, check all flows
sample_od_id = sorted_by_input[0][0]  # OD pair with highest input
sample_input = sorted_by_input[0][1]['input']

print(f"\nSample OD pair: {sample_od_id}")
print(f"INPUT demand F[0]: {sample_input:,.0f} tonnes")

print(f"\nAll OUTPUT flows for this OD pair (year 2020):")
print("-" * 80)
print(f"{'Mode':<10} {'TechVehicle':<15} {'Generation':<12} {'Flow':>15}")
print("-" * 80)

total_sample = 0
for key_str, value in f_data_raw.items():
    flow_value = float(value)
    if flow_value < 0.01:
        continue

    key_tuple = eval(key_str)
    year, (product_id, od_id, path_id), (mode_id, techvehicle_id), generation = key_tuple

    if year == 2020 and od_id == sample_od_id:
        mode_name = 'rail' if mode_id == 2 else 'road'
        print(f"{mode_name:<10} {techvehicle_id:<15} {generation:<12} {flow_value:>15,.2f}")
        total_sample += flow_value

print("-" * 80)
print(f"{'TOTAL':<10} {'':>15} {'':>12} {total_sample:>15,.2f}")
print(f"\nRatio for this OD pair: {100*total_sample/sample_input:.2f}%")

print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)

print(f"\nFor year 2020 specifically:")
print(f"  - INPUT demand (F[0]): {total_input:,.0f} tonnes")
print(f"  - OUTPUT flows (f):    {total_output:,.0f} tonnes")
print(f"  - Ratio: {100*total_output/total_input:.2f}%")

if 100*total_output/total_input < 1:
    print(f"\n⚠️  Confirmed: Optimized flows are < 1% of input demand")
else:
    print(f"\n✓ Optimized flows are within expected range")
