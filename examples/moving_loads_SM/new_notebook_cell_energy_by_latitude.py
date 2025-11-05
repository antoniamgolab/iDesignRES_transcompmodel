# ==============================================================================
# ENERGY CONSUMPTION BY LATITUDE
# ==============================================================================
from scipy.ndimage import gaussian_filter1d

def calculate_energy_by_latitude(case_study_name, target_years=[2030, 2040, 2050]):
    """
    Calculate energy consumption (kWh) by NUTS2 region from the s variable.

    The s variable represents energy consumption and is scaled by 1000 in the model.
    s variable structure: (year, (product_id, odpair_id, path_id, geo_id), tech_id, (fuel_id, fueling_infra_id), generation)

    Returns:
        dict: {year: {nuts2_id: {'road_kwh': X, 'rail_kwh': X, 'lat': X}}}
    """
    input_data = loaded_runs[case_study_name]["input_data"]
    output_data = loaded_runs[case_study_name]["output_data"]
    s_data = output_data["s"]

    # Load geographic elements and filter to NUTS2 nodes
    geo_elements = input_data['GeographicElement']
    nuts2_lookup = {}
    for geo in geo_elements:
        if geo['type'] == 'node' and 'nuts2_region' in geo and geo['nuts2_region']:
            nuts2_lookup[geo['id']] = {
                'nuts2': geo['nuts2_region'],
                'lat': geo['coordinate_lat'],
                'lon': geo['coordinate_long']
            }

    print(f"Found {len(nuts2_lookup)} NUTS2 regions")

    # Load TechVehicle and Vehicletype data to map tech_id to mode
    techvehicles = input_data['TechVehicle']
    vehicletypes = input_data['Vehicletype']

    # Create vehicle_type_name -> mode_id mapping
    vtype_to_mode = {}
    for vt in vehicletypes:
        vtype_to_mode[vt['name']] = vt['mode']

    # Create tech_id -> mode_id mapping through vehicle_type
    tech_to_mode = {}
    for tv in techvehicles:
        vehicle_type_name = tv['vehicle_type']
        tech_to_mode[tv['id']] = vtype_to_mode.get(vehicle_type_name, 1)  # Default to road (1)

    # Initialize: {year: {geo_id: {metrics}}}
    data_by_year_geo = {year: {} for year in target_years}

    # SCALING FACTOR: s is scaled by 1000 in the model (multiply by 1000 to get kWh)
    SCALING_FACTOR = 1000

    # Process each energy consumption entry
    for key_str, energy_value_scaled in s_data.items():
        # Parse key structure: (year, (product_id, odpair_id, path_id, geo_id), tech_id, (fuel_id, fueling_infra_id), generation)
        key = eval(key_str) if isinstance(key_str, str) else key_str
        year, (product_id, odpair_id, path_id, geo_id), tech_id, (fuel_id, fueling_infra_id), generation = key

        if year not in target_years or energy_value_scaled <= 0:
            continue

        # Convert to kWh
        energy_kwh = energy_value_scaled * SCALING_FACTOR

        # Only process NUTS2 nodes
        if geo_id not in nuts2_lookup:
            continue

        # Get mode from tech_id
        mode_id = tech_to_mode.get(tech_id, 1)  # Default to road (1) if not found
        mode_name = 'rail' if mode_id == 2 else 'road'

        # Initialize if needed
        if geo_id not in data_by_year_geo[year]:
            data_by_year_geo[year][geo_id] = {
                'road_kwh': 0.0,
                'rail_kwh': 0.0,
                'lat': nuts2_lookup[geo_id]['lat'],
                'nuts2': nuts2_lookup[geo_id]['nuts2']
            }

        # Add energy consumption
        data_by_year_geo[year][geo_id][f'{mode_name}_kwh'] += energy_kwh

    return data_by_year_geo

# Calculate data
print("Calculating energy consumption by latitude...")
energy_data = calculate_energy_by_latitude(case_name, target_years=[2030, 2040, 2050])

# Display summary
print("\n" + "="*80)
print("SUMMARY: ENERGY CONSUMPTION BY YEAR")
print("="*80)
for year in [2030, 2040, 2050]:
    data = energy_data[year]

    total_road_kwh = sum(d['road_kwh'] for d in data.values())
    total_rail_kwh = sum(d['rail_kwh'] for d in data.values())
    total_kwh = total_road_kwh + total_rail_kwh

    # Convert to TWh for readability
    print(f"\nYear {year}:")
    print(f"  Road:  {total_road_kwh/1e9:.2f} TWh ({100*total_road_kwh/total_kwh:.1f}%)")
    print(f"  Rail:  {total_rail_kwh/1e9:.2f} TWh ({100*total_rail_kwh/total_kwh:.1f}%)")
    print(f"  Total: {total_kwh/1e9:.2f} TWh")

# ==============================================================================
# PLOT: ENERGY CONSUMPTION BY LATITUDE
# ==============================================================================

years_to_plot = [2030, 2040, 2050]
colors = ['#3498DB', '#2ECC71', '#F39C12']

# Create figure with 3 rows (one per year)
fig, axes = plt.subplots(3, 1, figsize=(12, 16), sharex=True)

for year_idx, (year, color) in enumerate(zip(years_to_plot, colors)):
    data = energy_data[year]

    if not data:
        continue

    # Prepare data for plotting
    plotting_data = []
    for geo_id, metrics in data.items():
        lat = metrics['lat']
        total_kwh = metrics['road_kwh'] + metrics['rail_kwh']

        if total_kwh > 0:
            plotting_data.append({
                'lat': lat,
                'road_kwh': metrics['road_kwh'],
                'rail_kwh': metrics['rail_kwh']
            })

    # Sort by latitude
    plotting_data.sort(key=lambda x: x['lat'])

    if len(plotting_data) < 2:
        continue

    # Extract arrays
    lats = np.array([d['lat'] for d in plotting_data])
    road_kwh = np.array([d['road_kwh'] for d in plotting_data])
    rail_kwh = np.array([d['rail_kwh'] for d in plotting_data])

    # Apply Gaussian smoothing
    sigma = 2.0
    road_kwh_smooth = gaussian_filter1d(road_kwh, sigma=sigma)
    rail_kwh_smooth = gaussian_filter1d(rail_kwh, sigma=sigma)

    ax = axes[year_idx]

    # Convert to GWh for readability (1 GWh = 1,000,000 kWh)
    road_gwh = road_kwh_smooth / 1e6
    rail_gwh = rail_kwh_smooth / 1e6

    # Stacked area plot
    ax.fill_betweenx(lats, 0, road_gwh,
                     color='#E74C3C', alpha=0.6, label='Road', edgecolor='darkred', linewidth=1.5)
    ax.fill_betweenx(lats, road_gwh, road_gwh + rail_gwh,
                     color='#3498DB', alpha=0.6, label='Rail', edgecolor='darkblue', linewidth=1.5)

    # Total outline
    total_gwh = road_gwh + rail_gwh
    ax.plot(total_gwh, lats, 'k-', linewidth=2, alpha=0.5)

    ax.set_ylabel('Latitude (°N)', fontsize=12, fontweight='bold')
    ax.set_title(f'Year {year}', fontsize=13, fontweight='bold', pad=10)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_xlim(left=0)

    if year_idx == 0:
        ax.legend(loc='lower left', fontsize=11, framealpha=0.95)

# Set common x-label
axes[-1].set_xlabel('Energy Consumption (GWh)', fontsize=12, fontweight='bold')

# Overall title
fig.suptitle('Energy Consumption by Latitude\\nScandinavian-Mediterranean Corridor',
             fontsize=17, fontweight='bold', y=0.995)

# ==============================================================================
# ADD COUNTRY LABELS AND BORDERS
# ==============================================================================

# Load country data
country_centroids = pd.read_csv('country_centroids.csv')
borders_df = pd.read_csv('country_southern_borders.csv')

corridor_countries = ['IT', 'AT', 'DE', 'DK', 'NO', 'SE']
country_data = country_centroids[country_centroids['CNTR_CODE'].isin(corridor_countries)]

for ax in axes:
    ylim = ax.get_ylim()

    # Add country labels
    for _, row in country_data.iterrows():
        country_code = row['CNTR_CODE']
        lat = row['centroid_lat']

        if ylim[0] <= lat <= ylim[1]:
            ax.text(1.02, lat, country_code, transform=ax.get_yaxis_transform(),
                   fontsize=10, fontweight='bold', va='center', ha='left',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))

    # Add border lines
    for _, row in borders_df.iterrows():
        country = row['CNTR_CODE']
        border_lat = row['southern_border_lat']

        if country in corridor_countries and ylim[0] <= border_lat <= ylim[1]:
            ax.axhline(y=border_lat, color='gray', linestyle='--',
                      linewidth=0.8, alpha=0.5, zorder=1)

plt.tight_layout()
plt.savefig('energy_consumption_by_latitude.png', dpi=300, bbox_inches='tight')
print("\n✓ Plot saved as 'energy_consumption_by_latitude.png'")
plt.show()

# ==============================================================================
# INTERPRETATION GUIDE
# ==============================================================================

print("\n" + "="*80)
print("INTERPRETATION GUIDE: ENERGY CONSUMPTION BY LATITUDE")
print("="*80)
print("""
WHAT THIS SHOWS:
- Energy consumption (in GWh) for freight transport at each latitude
- Split by mode: Road (red) vs Rail (blue)
- Represents direct energy use (kWh) from the optimization model

KEY INSIGHTS:
- Peaks show regions with highest energy consumption for freight transport
- Different from TKM (which shows transport work)
- Energy depends on: distance traveled, efficiency of vehicles, and freight volume
- Rail typically more energy-efficient per TKM than road

COMPARISON WITH TKM:
- TKM measures transport work (tonnes × kilometers)
- Energy measures actual fuel/electricity consumption
- Energy can be lower for rail even with similar TKM due to higher efficiency

SCALING:
- s variable is scaled by 1000 in the model
- Results shown in GWh (1 GWh = 1,000,000 kWh)
- Total annual energy for corridor shown in TWh (1 TWh = 1,000 GWh)
""")

# ==============================================================================
# ENERGY INTENSITY ANALYSIS
# ==============================================================================

print("\n" + "="*80)
print("ENERGY INTENSITY (kWh per TKM)")
print("="*80)

# Load TKM data from previous analysis (if available)
# This requires the tonnes_tkm_data to be available
try:
    tonnes_tkm_data = calculate_tonnes_and_tkm_by_latitude(case_name, target_years=[2030, 2040, 2050])

    for year in [2030, 2040, 2050]:
        energy = energy_data[year]
        tkm = tonnes_tkm_data[year]

        total_road_energy = sum(d['road_kwh'] for d in energy.values())
        total_rail_energy = sum(d['rail_kwh'] for d in energy.values())
        total_road_tkm = sum(d['road_tkm'] for d in tkm.values())
        total_rail_tkm = sum(d['rail_tkm'] for d in tkm.values())

        # Calculate energy intensity (kWh per TKM)
        road_intensity = total_road_energy / total_road_tkm if total_road_tkm > 0 else 0
        rail_intensity = total_rail_energy / total_rail_tkm if total_rail_tkm > 0 else 0

        print(f"\nYear {year}:")
        print(f"  Road: {road_intensity:.3f} kWh/TKM")
        print(f"  Rail: {rail_intensity:.3f} kWh/TKM")
        if rail_intensity > 0:
            print(f"  Road/Rail ratio: {road_intensity/rail_intensity:.2f}x")
except:
    print("\nNote: Run the TKM calculation first to compute energy intensity")
