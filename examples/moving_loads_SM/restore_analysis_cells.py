"""
Restore both the diagnostic cell and the fixed electrification analysis cell
"""

import json

# Load the notebook
notebook_path = "results_SM.ipynb"
with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# ============================================================================
# CELL 1: Comprehensive Diagnostic
# ============================================================================
diagnostic_code = '''# COMPREHENSIVE FLOW DATA STRUCTURE ANALYSIS

import pandas as pd
from collections import Counter

print("=" * 80)
print("FLOW DATA STRUCTURE ANALYSIS")
print("=" * 80)

# Analyze all keys to understand structure
all_keys = list(output_data["f"].keys())
print(f"\\nTotal flow entries: {len(all_keys)}")

# Analyze first 10 keys
print(f"\\nFirst 10 keys:")
for i, key in enumerate(all_keys[:10]):
    print(f"  {i}: {key}")

# Analyze each component
odpair_ids = []
tv_ids = []
g_values = []
fourth_values = []

for key in all_keys:
    if len(key) == 4:
        odpair_ids.append(key[0])
        tv_ids.append(key[1])
        g_values.append(key[2])
        fourth_values.append(key[3])

print(f"\\n--- Component Analysis ---")

# Odpair IDs
unique_odpairs = sorted(set(odpair_ids))
print(f"\\nOdpair IDs (first element):")
print(f"  Count: {len(unique_odpairs)}")
print(f"  Range: {min(unique_odpairs)} to {max(unique_odpairs)}")
print(f"  Sample: {unique_odpairs[:10]}")

# TechVehicle IDs
unique_tvs = sorted(set(tv_ids))
print(f"\\nTechVehicle IDs (second element):")
print(f"  Count: {len(unique_tvs)}")
print(f"  Sample: {unique_tvs[:5]}")

# Generation values
unique_gs = sorted(set(g_values))
print(f"\\nGeneration values (third element):")
print(f"  Count: {len(unique_gs)}")
print(f"  All unique values: {unique_gs[:20]}")

# Fourth values
unique_fourths = sorted(set(fourth_values))
print(f"\\nFourth element:")
print(f"  Count: {len(unique_fourths)}")
print(f"  Range: {min(unique_fourths)} to {max(unique_fourths)}")
print(f"  Sample: {unique_fourths[:10]}")

# Check if fourth element equals first element
matches = sum(1 for k in all_keys if len(k) == 4 and k[0] == k[3])
print(f"  Entries where 4th element == 1st element: {matches}/{len(all_keys)}")

# Check if generation tuple contains year information
print(f"\\n--- Testing if year is in generation tuple ---")
if len(unique_gs) > 0:
    for g in unique_gs[:10]:
        if isinstance(g, tuple):
            print(f"  g = {g}, elements: {list(g)}")
        else:
            print(f"  g = {g} (not a tuple)")

# Try to find entries with different generation values
print(f"\\n--- Looking for patterns in generation values ---")
g_counter = Counter(g_values)
print(f"Most common generation values:")
for g, count in g_counter.most_common(10):
    print(f"  {g}: {count} entries")

# Check if generation elements vary
sample_g = g_values[0]
if isinstance(sample_g, tuple) and len(sample_g) >= 2:
    print(f"\\nGeneration tuple structure (from first entry): {sample_g}")
    print(f"  g[0] = {sample_g[0]}")
    print(f"  g[1] = {sample_g[1]}")

    # Check range of g[0] and g[1]
    g0_values = [g[0] for g in g_values if isinstance(g, tuple) and len(g) >= 2]
    g1_values = [g[1] for g in g_values if isinstance(g, tuple) and len(g) >= 2]

    print(f"\\nRange of g[0]: {min(g0_values)} to {max(g0_values)} (unique: {len(set(g0_values))})")
    print(f"  Unique values: {sorted(set(g0_values))[:20]}")
    print(f"\\nRange of g[1]: {min(g1_values)} to {max(g1_values)} (unique: {len(set(g1_values))})")
    print(f"  Unique values: {sorted(set(g1_values))[:20]}")

    # Determine which might be the year
    if len(set(g0_values)) > 1:
        print(f"\\n*** g[0] has {len(set(g0_values))} unique values - likely the year index! ***")
    if len(set(g1_values)) > 1:
        print(f"\\n*** g[1] has {len(set(g1_values))} unique values - likely the year index! ***")
    if len(set(g0_values)) == 1 and len(set(g1_values)) == 1:
        print(f"\\n*** WARNING: Both g[0] and g[1] are constant - this file may only have data for ONE year! ***")

print("\\n" + "=" * 80)
'''

# ============================================================================
# CELL 2: Fixed Electrification Analysis
# ============================================================================
electrification_code = '''# Electrification by Country Analysis
# Calculate percentage of electricity consumption vs total fuel consumption by country

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Get timestep from Model parameters
time_step = input_data["Model"].get("time_step", 1)
y_init = input_data["Model"]["y_init"]
Y = input_data["Model"]["Y"]

print(f"Time step: {time_step} (1=annual, 2=biennial, etc.)")
print(f"Model years: {y_init} to {y_init + (Y-1) * time_step}")

# Years to analyze (actual calendar years)
years_to_plot = [2024, 2034]  # Adjust these to match your timestep!

# Convert actual years to year indices
year_indices = [(year - y_init) // time_step for year in years_to_plot]
print(f"Analyzing years: {years_to_plot} (indices: {year_indices})")

# Initialize data structure to store fuel consumption by country, fuel type, and year
# Structure: {country: {year_index: {fuel: total_consumption}}}
fuel_by_country = {}

# Get fuel types from input data
fuel_list = {d["id"]: d for d in input_data["Fuel"]}
techvehicle_list = {d["id"]: d for d in input_data["TechVehicle"]}
technology_list = {d["id"]: d for d in input_data["Technology"]}

print(f"\\nAvailable techvehicles: {list(techvehicle_list.keys())}")

# Process flow data (f) to calculate fuel consumption
# f[odpair, tv, g, y] = flow of techvehicle tv on odpair in generation g, year y
print(f"\\nProcessing {len(output_data['f'])} flow entries...")

# First, let's understand the key structure
sample_keys = list(output_data["f"].keys())[:3]
print(f"Sample keys: {sample_keys}")

entries_processed = 0
entries_skipped_year = 0
entries_skipped_other = 0
countries_found = set()

for key, flow_value in output_data["f"].items():
    odpair_id, tv_id, g, y_key = key

    # Handle the case where tv_id might be a tuple
    # Extract the first element if it's a tuple
    if isinstance(tv_id, tuple):
        tv_id_lookup = tv_id[0]
    else:
        tv_id_lookup = tv_id

    # Determine the year index from the generation tuple g
    # Based on diagnostic: g = (generation, year_index)
    if isinstance(g, tuple) and len(g) >= 2:
        y = g[1]  # Year index is the second element
    elif isinstance(g, tuple) and len(g) == 1:
        y = g[0]  # Year index might be the only element
    else:
        # Can't determine year, skip
        entries_skipped_other += 1
        continue

    # Only process years we're interested in
    if y not in year_indices:
        entries_skipped_year += 1
        continue

    # Get odpair information
    odpair = next((od for od in input_data["Odpair"] if od["id"] == odpair_id), None)
    if odpair is None:
        entries_skipped_other += 1
        continue

    # Get origin node to determine country
    origin_node_id = odpair["from"]
    origin_node = geographic_element_list.get(origin_node_id)
    if origin_node is None or origin_node["type"] != "node":
        entries_skipped_other += 1
        continue

    country = origin_node.get("country", "Unknown")
    if country == "Unknown":
        entries_skipped_other += 1
        continue

    countries_found.add(country)

    # Get techvehicle and fuel information using the extracted ID
    techvehicle = techvehicle_list.get(tv_id_lookup)
    if techvehicle is None:
        entries_skipped_other += 1
        continue

    tech_id = techvehicle["technology"]
    technology = technology_list.get(tech_id)
    if technology is None:
        entries_skipped_other += 1
        continue

    fuel_id = technology["fuel"]
    fuel = fuel_list.get(fuel_id)
    if fuel is None:
        entries_skipped_other += 1
        continue

    fuel_name = fuel["name"]

    # Calculate fuel consumption
    # Flow is in vehicle-km, multiply by fuel consumption rate
    distance = odpair["d"]  # distance in km
    fuel_consumption_per_km = technology.get("specific_fuel_consumption", 0)  # kWh/km or L/km

    # Total fuel consumed = flow * distance * fuel_consumption_per_km
    total_fuel = flow_value * distance * fuel_consumption_per_km

    # Initialize nested dictionaries if needed
    if country not in fuel_by_country:
        fuel_by_country[country] = {}
    if y not in fuel_by_country[country]:
        fuel_by_country[country][y] = {}
    if fuel_name not in fuel_by_country[country][y]:
        fuel_by_country[country][y][fuel_name] = 0

    # Add to total
    fuel_by_country[country][y][fuel_name] += total_fuel
    entries_processed += 1

print(f"\\nProcessed {entries_processed} entries for target years")
print(f"Skipped {entries_skipped_year} entries (wrong year)")
print(f"Skipped {entries_skipped_other} entries (other reasons)")
print(f"Found {len(countries_found)} countries: {sorted(countries_found)}")

# Calculate electrification percentage by country and year
electrification_data = []

for country, years_data in fuel_by_country.items():
    for y_idx, fuels_data in years_data.items():
        # Calculate total fuel consumption
        total_fuel = sum(fuels_data.values())

        # Calculate electricity consumption
        electricity_consumption = fuels_data.get("electricity", 0)

        # Calculate percentage
        if total_fuel > 0:
            electrification_pct = (electricity_consumption / total_fuel) * 100
        else:
            electrification_pct = 0

        # Convert year index back to actual year
        actual_year = y_init + y_idx * time_step

        electrification_data.append({
            'country': country,
            'year': actual_year,
            'electrification_pct': electrification_pct,
            'total_fuel': total_fuel,
            'electricity': electricity_consumption
        })

# Create DataFrame
df_electrification = pd.DataFrame(electrification_data)
print(f"\\nCollected data for {len(df_electrification['country'].unique() if len(df_electrification) > 0 else [])} countries")
if len(df_electrification) > 0:
    print(f"Countries: {sorted(df_electrification['country'].unique())}")
    print(f"Electrification data rows: {len(df_electrification)}")

if len(df_electrification) == 0:
    print("\\n" + "=" * 80)
    print("[WARNING] No electrification data found!")
    print("=" * 80)
    print("\\nPossible reasons:")
    print("  1. The results file only contains data for certain years")
    print("  2. The year indices don't match the requested years")
    print("  3. Run the diagnostic cell above to see available year indices")
    print("\\nTip: Check the diagnostic output and adjust years_to_plot accordingly")
    print("=" * 80)
else:
    # Create scatter plots
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    for idx, year in enumerate(years_to_plot):
        ax = axes[idx]

        # Filter data for this year
        year_data = df_electrification[df_electrification['year'] == year].sort_values('country')

        if len(year_data) == 0:
            ax.text(0.5, 0.5, f'No data for {year}',
                    ha='center', va='center', transform=ax.transAxes)
            ax.set_title(f'Year {year}')
            continue

        # Create scatter plot
        x_pos = np.arange(len(year_data))
        ax.scatter(x_pos, year_data['electrification_pct'], alpha=0.6, s=100)

        # Set labels
        ax.set_xticks(x_pos)
        ax.set_xticklabels(year_data['country'], rotation=45, ha='right')
        ax.set_ylabel('Electrification %')
        ax.set_title(f'Battery-Electric Fueling by Country ({year})')
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, 100)

    plt.tight_layout()
    plt.show()

    # Print summary statistics
    print("\\n" + "="*80)
    print("ELECTRIFICATION SUMMARY")
    print("="*80)
    for year in years_to_plot:
        year_data = df_electrification[df_electrification['year'] == year]
        if len(year_data) > 0:
            print(f"\\nYear {year}:")
            print(f"  Average electrification: {year_data['electrification_pct'].mean():.2f}%")
            print(f"  Min: {year_data['electrification_pct'].min():.2f}% ({year_data.loc[year_data['electrification_pct'].idxmin(), 'country']})")
            print(f"  Max: {year_data['electrification_pct'].max():.2f}% ({year_data.loc[year_data['electrification_pct'].idxmax(), 'country']})")
    print("="*80)
'''

# ============================================================================
# Find the right place to insert cells
# ============================================================================

# Look for a markdown cell with "Electrification" in it to find the right section
insert_idx = None
for idx, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'markdown':
        source = ''.join(cell['source'])
        if 'Electrification' in source and 'Country' in source:
            insert_idx = idx + 1
            break

# If not found, look for any existing electrification code cell
if insert_idx is None:
    for idx, cell in enumerate(nb['cells']):
        if cell['cell_type'] == 'code':
            source = ''.join(cell['source'])
            if 'Electrification by Country' in source or 'years_to_plot' in source:
                insert_idx = idx
                break

if insert_idx is None:
    print("ERROR: Could not find insertion point. Adding at end of notebook.")
    insert_idx = len(nb['cells'])

print(f"Found insertion point at cell index {insert_idx}")

# Remove old cells if they exist (cells with these markers)
cells_to_remove = []
for idx, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if ('COMPREHENSIVE FLOW DATA STRUCTURE ANALYSIS' in source or
            'Electrification by Country Analysis' in source or
            'FLOW DATA STRUCTURE ANALYSIS' in source or
            ('years_to_plot' in source and 'electrification' in source.lower())):
            cells_to_remove.append(idx)

print(f"Removing {len(cells_to_remove)} old cells: {cells_to_remove}")
for idx in sorted(cells_to_remove, reverse=True):
    nb['cells'].pop(idx)
    if idx < insert_idx:
        insert_idx -= 1

# Create the two new cells
diagnostic_cell = {
    'cell_type': 'code',
    'execution_count': None,
    'metadata': {},
    'outputs': [],
    'source': diagnostic_code.split('\n')
}

electrification_cell = {
    'cell_type': 'code',
    'execution_count': None,
    'metadata': {},
    'outputs': [],
    'source': electrification_code.split('\n')
}

# Insert cells
nb['cells'].insert(insert_idx, diagnostic_cell)
nb['cells'].insert(insert_idx + 1, electrification_cell)

# Save the notebook
with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)

print(f"\nSuccessfully restored both cells!")
print(f"  - Diagnostic cell at index {insert_idx}")
print(f"  - Electrification analysis cell at index {insert_idx + 1}")
print("\nKey fixes in the electrification cell:")
print("  1. Extracts tv_id[0] from tuple (0, 2006, 2006)")
print("  2. Extracts year index from g[1] (generation tuple)")
print("  3. Converts actual years to indices: [2024, 2034] → [2, 7]")
print("  4. Better error reporting and diagnostics")
print("\nPlease reload the notebook and:")
print("  1. Run the diagnostic cell first to see available years")
print("  2. Then run the electrification cell")
