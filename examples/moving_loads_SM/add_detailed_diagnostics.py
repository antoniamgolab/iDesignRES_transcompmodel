"""
Add detailed diagnostics to the electrification cell to see where entries are being skipped
"""

import json

# Load the notebook
notebook_path = "results_SM.ipynb"
with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# The corrected cell code with detailed diagnostics
diagnostic_code = '''# Electrification by Country Analysis - WITH DETAILED DIAGNOSTICS
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
years_to_plot = [2024, 2034]  # These should match actual years in the data!

print(f"Analyzing years: {years_to_plot}")

# Initialize data structure to store fuel consumption by country, fuel type, and year
# Structure: {country: {year: {fuel: total_consumption}}}
fuel_by_country = {}

# Get fuel types from input data
fuel_list = {d["id"]: d for d in input_data["Fuel"]}
techvehicle_list = {d["id"]: d for d in input_data["TechVehicle"]}
technology_list = {d["id"]: d for d in input_data["Technology"]}

print(f"\\nAvailable techvehicles: {list(techvehicle_list.keys())}")
print(f"Available technologies: {list(technology_list.keys())}")
print(f"Available fuels: {list(fuel_list.keys())}")

# Process flow data (f) to calculate fuel consumption
# KEY INSIGHT: key = (year, tv_id_tuple, generation_tuple, odpair_id)
print(f"\\nProcessing {len(output_data['f'])} flow entries...")

# First, let's understand the key structure
sample_keys = list(output_data["f"].keys())[:3]
print(f"Sample keys: {sample_keys}")

# Detailed skip counters
entries_processed = 0
skip_counters = {
    'wrong_year': 0,
    'odpair_not_found': 0,
    'origin_node_not_found': 0,
    'origin_not_node_type': 0,
    'country_unknown': 0,
    'techvehicle_not_found': 0,
    'technology_not_found': 0,
    'fuel_not_found': 0,
}
countries_found = set()

# Sample entries for debugging
debug_sample_size = 5
debug_counter = 0

for key, flow_value in output_data["f"].items():
    # CORRECTED: key = (year, tv_id_tuple, generation_tuple, odpair_id)
    year, tv_id, g, odpair_id = key

    # Debug first few entries that match our year
    if year in years_to_plot and debug_counter < debug_sample_size:
        print(f"\\n--- DEBUG ENTRY {debug_counter + 1} ---")
        print(f"  Year: {year}, TV: {tv_id}, G: {g}, Odpair: {odpair_id}, Flow: {flow_value}")
        debug_counter += 1

    # Only process years we're interested in
    if year not in years_to_plot:
        skip_counters['wrong_year'] += 1
        continue

    # Handle the case where tv_id is a tuple
    # Extract the first element if it's a tuple
    if isinstance(tv_id, tuple):
        tv_id_lookup = tv_id[0]
    else:
        tv_id_lookup = tv_id

    if debug_counter <= debug_sample_size:
        print(f"  TV lookup ID: {tv_id_lookup}")

    # Get odpair information
    odpair = next((od for od in input_data["Odpair"] if od["id"] == odpair_id), None)
    if odpair is None:
        skip_counters['odpair_not_found'] += 1
        if debug_counter <= debug_sample_size:
            print(f"  [SKIP] Odpair {odpair_id} not found")
        continue

    if debug_counter <= debug_sample_size:
        print(f"  Odpair found: from={odpair['from']}, to={odpair['to']}, d={odpair.get('d', 'N/A')}")

    # Get origin node to determine country
    origin_node_id = odpair["from"]
    origin_node = geographic_element_list.get(origin_node_id)
    if origin_node is None:
        skip_counters['origin_node_not_found'] += 1
        if debug_counter <= debug_sample_size:
            print(f"  [SKIP] Origin node {origin_node_id} not found")
        continue

    if origin_node["type"] != "node":
        skip_counters['origin_not_node_type'] += 1
        if debug_counter <= debug_sample_size:
            print(f"  [SKIP] Origin {origin_node_id} type is {origin_node['type']}, not 'node'")
        continue

    country = origin_node.get("country", "Unknown")
    if country == "Unknown":
        skip_counters['country_unknown'] += 1
        if debug_counter <= debug_sample_size:
            print(f"  [SKIP] Country is Unknown")
        continue

    if debug_counter <= debug_sample_size:
        print(f"  Country: {country}")

    countries_found.add(country)

    # Get techvehicle and fuel information using the extracted ID
    techvehicle = techvehicle_list.get(tv_id_lookup)
    if techvehicle is None:
        skip_counters['techvehicle_not_found'] += 1
        if debug_counter <= debug_sample_size:
            print(f"  [SKIP] Techvehicle {tv_id_lookup} not found")
        continue

    if debug_counter <= debug_sample_size:
        print(f"  Techvehicle found: {techvehicle}")

    tech_id = techvehicle["technology"]
    technology = technology_list.get(tech_id)
    if technology is None:
        skip_counters['technology_not_found'] += 1
        if debug_counter <= debug_sample_size:
            print(f"  [SKIP] Technology {tech_id} not found")
        continue

    if debug_counter <= debug_sample_size:
        print(f"  Technology found: {technology}")

    fuel_id = technology["fuel"]
    fuel = fuel_list.get(fuel_id)
    if fuel is None:
        skip_counters['fuel_not_found'] += 1
        if debug_counter <= debug_sample_size:
            print(f"  [SKIP] Fuel {fuel_id} not found")
        continue

    fuel_name = fuel["name"]

    if debug_counter <= debug_sample_size:
        print(f"  Fuel: {fuel_name}")

    # Calculate fuel consumption
    # Flow is in vehicle-km, multiply by fuel consumption rate
    distance = odpair["d"]  # distance in km
    fuel_consumption_per_km = technology.get("specific_fuel_consumption", 0)  # kWh/km or L/km

    # Total fuel consumed = flow * distance * fuel_consumption_per_km
    total_fuel = flow_value * distance * fuel_consumption_per_km

    if debug_counter <= debug_sample_size:
        print(f"  Distance: {distance} km")
        print(f"  Fuel consumption rate: {fuel_consumption_per_km} per km")
        print(f"  Total fuel: {total_fuel}")

    # Initialize nested dictionaries if needed
    if country not in fuel_by_country:
        fuel_by_country[country] = {}
    if year not in fuel_by_country[country]:
        fuel_by_country[country][year] = {}
    if fuel_name not in fuel_by_country[country][year]:
        fuel_by_country[country][year][fuel_name] = 0

    # Add to total
    fuel_by_country[country][year][fuel_name] += total_fuel
    entries_processed += 1

    if debug_counter <= debug_sample_size:
        print(f"  [SUCCESS] Entry processed!")

print(f"\\n{'='*80}")
print(f"PROCESSING SUMMARY")
print(f"{'='*80}")
print(f"Entries processed successfully: {entries_processed}")
print(f"\\nSkip reasons:")
for reason, count in skip_counters.items():
    if count > 0:
        print(f"  {reason}: {count}")
print(f"\\nCountries found: {sorted(countries_found)}")

# Calculate electrification percentage by country and year
electrification_data = []

for country, years_data in fuel_by_country.items():
    for year, fuels_data in years_data.items():
        # Calculate total fuel consumption
        total_fuel = sum(fuels_data.values())

        # Calculate electricity consumption
        electricity_consumption = fuels_data.get("electricity", 0)

        # Calculate percentage
        if total_fuel > 0:
            electrification_pct = (electricity_consumption / total_fuel) * 100
        else:
            electrification_pct = 0

        electrification_data.append({
            'country': country,
            'year': year,
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
    print(f"\\nSample data:")
    print(df_electrification.head(10))

if len(df_electrification) == 0:
    print("\\n" + "=" * 80)
    print("[WARNING] No electrification data found!")
    print("=" * 80)
    print("Check the DEBUG ENTRY output above to see where processing is failing.")
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

# Find the electrification cell
target_cell_idx = None
for idx, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if 'Electrification by Country Analysis' in source:
            target_cell_idx = idx
            break

if target_cell_idx is None:
    print("ERROR: Could not find the electrification analysis cell!")
else:
    print(f"Found electrification cell at index {target_cell_idx}")

    # Replace the cell source
    nb['cells'][target_cell_idx]['source'] = diagnostic_code.split('\n')

    # Clear outputs
    nb['cells'][target_cell_idx]['outputs'] = []
    nb['cells'][target_cell_idx]['execution_count'] = None

    # Save the notebook
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1)

    print(f"Successfully updated cell {target_cell_idx}")
    print("\nAdded detailed diagnostics:")
    print("  - Shows first 5 entries that match target years")
    print("  - Traces each processing step")
    print("  - Shows exactly where entries are being skipped")
    print("  - Detailed skip reason counters")
    print("\nPlease reload the notebook and run the updated cell!")
    print("The debug output will show you exactly what's failing!")
