"""
Fix the electrification analysis cell in results_SM.ipynb
The issue: tv_id is a tuple like (0, 2006, 2006) but we need just the first element
"""

import json

# Load the notebook
notebook_path = "results_SM.ipynb"
with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# The corrected cell code
corrected_code = '''# Electrification by Country Analysis
# Calculate percentage of electricity consumption vs total fuel consumption by country

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Get timestep from Model parameters
time_step = input_data["Model"].get("time_step", 1)
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
entries_skipped = 0
countries_found = set()

for key, flow_value in output_data["f"].items():
    odpair_id, tv_id, g, y = key

    # Handle the case where tv_id might be a tuple
    # Extract the first element if it's a tuple
    if isinstance(tv_id, tuple):
        tv_id_lookup = tv_id[0]
    else:
        tv_id_lookup = tv_id

    # Handle the case where y might need conversion
    # If y is very large (like 2040), it might actually be the odpair ID repeated
    # In that case, we need to extract the year index from generation or elsewhere
    if y > 100:  # Year indices should be 0-40 for 2020-2060
        # This might be the odpair ID repeated, not the year index
        # The year might be encoded in the generation tuple g
        if isinstance(g, tuple) and len(g) >= 2:
            y = g[1]  # Try second element of generation tuple
        else:
            entries_skipped += 1
            continue

    # Only process years we're interested in
    if y not in year_indices:
        continue

    entries_processed += 1

    # Get odpair information
    odpair = next((od for od in input_data["Odpair"] if od["id"] == odpair_id), None)
    if odpair is None:
        continue

    # Get origin node to determine country
    origin_node_id = odpair["from"]
    origin_node = geographic_element_list.get(origin_node_id)
    if origin_node is None or origin_node["type"] != "node":
        continue

    country = origin_node.get("country", "Unknown")
    if country == "Unknown":
        continue

    countries_found.add(country)

    # Get techvehicle and fuel information using the extracted ID
    techvehicle = techvehicle_list.get(tv_id_lookup)
    if techvehicle is None:
        continue

    tech_id = techvehicle["technology"]
    technology = technology_list.get(tech_id)
    if technology is None:
        continue

    fuel_id = technology["fuel"]
    fuel = fuel_list.get(fuel_id)
    if fuel is None:
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

print(f"\\nProcessed {entries_processed} entries for target years")
print(f"Skipped {entries_skipped} entries (could not parse year)")
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
    print("\\n[WARNING] No electrification data found!")
    print("Please check the data structure and year indices.")
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
'''

# Find the cell with the electrification analysis (search for specific marker)
target_cell_idx = None
for idx, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if 'Electrification by Country Analysis' in source and 'years_to_plot' in source:
            target_cell_idx = idx
            break

if target_cell_idx is None:
    print("ERROR: Could not find the electrification analysis cell!")
else:
    print(f"Found electrification cell at index {target_cell_idx}")

    # Replace the cell source
    nb['cells'][target_cell_idx]['source'] = corrected_code.split('\n')

    # Clear outputs
    nb['cells'][target_cell_idx]['outputs'] = []
    nb['cells'][target_cell_idx]['execution_count'] = None

    # Save the notebook
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1)

    print(f"Successfully updated cell {target_cell_idx}")
    print("\nKey fixes:")
    print("  1. Extract first element of tv_id tuple: tv_id_lookup = tv_id[0]")
    print("  2. Handle year encoding: if y > 100, extract from generation tuple")
    print("  3. Added debug output to show sample keys and techvehicles")
    print("\nPlease reload the notebook and run the cell again!")
