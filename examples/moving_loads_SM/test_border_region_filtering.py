"""
Test script to verify border region filtering works with actual data
"""

import matplotlib.pyplot as plt
import numpy as np
import os
import sys
import pandas as pd
import yaml

# Import the original read_data function
def process_key(key):
    import ast
    return ast.literal_eval(key)

def process_value(value):
    return float(value)

def read_data(case_study_name, input_folder_name, variables_to_read, run_id):
    current_path = os.getcwd()
    file_results = os.path.normpath(current_path + "/results")
    folder_input = os.path.normpath(current_path + "/input_data/" + input_folder_name)

    input_data = {}
    for file_name in os.listdir(folder_input):
        if file_name.endswith(".yaml"):
            key_name = os.path.splitext(file_name)[0]
            if key_name != "SpatialFlexibilityEdges":
                with open(os.path.join(folder_input, file_name)) as file:
                    input_data[key_name] = yaml.safe_load(file)

    output_data = {}
    for variable in variables_to_read:
        file_name = os.path.normpath(
            file_results + "/" + input_folder_name + "/" +
            case_study_name + f"_{variable}_dict.yaml"
        )
        with open(file_name) as file:
            data_dict = yaml.safe_load(file)
        output_data[variable] = {
            process_key(key): process_value(value)
            for key, value in data_dict.items()
        }
        print(f"Loaded {variable}")

    return input_data, output_data


# Import border region analysis
from border_region_electrification_analysis import (
    load_border_region_codes,
    calculate_electrification_by_country_border_only,
    compare_border_vs_all_electrification
)
from electrification_analysis import calculate_electrification_by_country

# Test with one scenario
print("=" * 80)
print("TESTING BORDER REGION FILTERING")
print("=" * 80)

case_study_name = "case_20251022_152235_var_var"
run_id = "case_20251022_152235_var_var_cs_2025-10-23_08-22-09"
variables_to_read = ["f"]

print(f"\nLoading data for: {case_study_name}")
input_data, output_data = read_data(
    run_id,
    case_study_name,
    variables_to_read,
    0
)

# Load border codes
print("\nLoading border region codes...")
border_nuts2_codes = load_border_region_codes("border_nuts2_codes.txt")
print(f"Loaded {len(border_nuts2_codes)} border codes: {sorted(border_nuts2_codes)}")

# Calculate electrification for ALL regions
print("\n" + "-" * 80)
print("Calculating electrification for ALL regions...")
df_all, fuel_all, skip_all = calculate_electrification_by_country(
    input_data,
    output_data,
    years_to_plot=[2030, 2040]
)

print(f"\nALL REGIONS Results:")
print(f"  Countries found: {df_all['country'].unique().tolist()}")
print(f"  Total entries: {len(df_all)}")
print(f"  Skip counters: {skip_all}")
print(f"\nData sample:")
print(df_all)

# Calculate electrification for BORDER regions only
print("\n" + "-" * 80)
print("Calculating electrification for BORDER regions only...")
df_border, fuel_border, skip_border = calculate_electrification_by_country_border_only(
    input_data,
    output_data,
    border_nuts2_codes,
    years_to_plot=[2030, 2040]
)

print(f"\nBORDER REGIONS Results:")
print(f"  Countries found: {df_border['country'].unique().tolist()}")
print(f"  Total entries: {len(df_border)}")
print(f"  Entries filtered (not border): {skip_border['not_border_region']}")
print(f"  Skip counters: {skip_border}")
print(f"\nData sample:")
print(df_border)

# Compare results
print("\n" + "=" * 80)
print("COMPARISON")
print("=" * 80)

for year in [2030, 2040]:
    print(f"\nYear {year}:")
    print("-" * 40)

    all_year = df_all[df_all['year'] == year]
    border_year = df_border[df_border['year'] == year]

    print(f"  All regions:")
    print(f"    Total electricity: {all_year['electricity'].sum():.2f} kWh")
    print(f"    Avg electrification: {all_year['electrification_pct'].mean():.2f}%")

    print(f"  Border regions:")
    print(f"    Total electricity: {border_year['electricity'].sum():.2f} kWh")
    print(f"    Avg electrification: {border_year['electrification_pct'].mean():.2f}%")

    reduction_pct = (1 - border_year['electricity'].sum() / all_year['electricity'].sum()) * 100
    print(f"  Reduction by filtering: {reduction_pct:.1f}%")

# Visualize comparison
print("\n" + "=" * 80)
print("CREATING VISUALIZATION")
print("=" * 80)

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

for idx, year in enumerate([2030, 2040]):
    ax = axes[idx]

    all_year = df_all[df_all['year'] == year]
    border_year = df_border[df_border['year'] == year]

    # Get all countries
    countries = sorted(set(all_year['country'].unique()) | set(border_year['country'].unique()))

    x = np.arange(len(countries))
    width = 0.35

    # Prepare data
    all_vals = []
    border_vals = []

    for country in countries:
        all_val = all_year[all_year['country'] == country]['electricity'].sum()
        border_val = border_year[border_year['country'] == country]['electricity'].sum()
        all_vals.append(all_val)
        border_vals.append(border_val)

    # Plot
    ax.bar(x - width/2, all_vals, width, label='All regions', alpha=0.8, color='steelblue')
    ax.bar(x + width/2, border_vals, width, label='Border regions', alpha=0.8, color='coral')

    ax.set_title(f'Electricity Consumption ({year})', fontsize=12, fontweight='bold')
    ax.set_xlabel('Country')
    ax.set_ylabel('Electricity (kWh)')
    ax.set_xticks(x)
    ax.set_xticklabels(countries, rotation=45, ha='right')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('test_border_filtering_comparison.png', dpi=300, bbox_inches='tight')
print("Saved: test_border_filtering_comparison.png")
plt.show()

print("\n" + "=" * 80)
print("TEST COMPLETED SUCCESSFULLY!")
print("=" * 80)
