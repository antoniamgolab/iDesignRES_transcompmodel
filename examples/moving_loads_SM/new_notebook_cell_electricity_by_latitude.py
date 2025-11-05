# ==============================================================================
# ELECTRICITY CONSUMPTION BY LATITUDE AND FUELING INFRASTRUCTURE TYPE
# ==============================================================================
from scipy.ndimage import gaussian_filter1d
import matplotlib.patches as mpatches

def calculate_electricity_by_latitude(case_study_name, target_years=[2030, 2040, 2050]):
    """
    Calculate electricity consumption (kWh) by NUTS2 region from the s variable.

    Filters for electric vehicles only and breaks down by fueling infrastructure type.

    s variable structure: (year, (product_id, odpair_id, path_id, geo_id), tech_id, (fuel_id, fueling_infra_id), generation)

    Returns:
        dict: {year: {nuts2_id: {infra_type: kWh, 'lat': X}}}
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

    # Load Fuel data to identify electricity
    fuels = input_data['Fuel']
    electricity_fuel_ids = []
    for fuel in fuels:
        if 'electricity' in fuel['name'].lower() or 'electric' in fuel['name'].lower():
            electricity_fuel_ids.append(fuel['id'])

    print(f"Electricity fuel IDs: {electricity_fuel_ids}")

    # Load FuelingInfrTypes to map infrastructure IDs to types
    fueling_infra_types = input_data.get('FuelingInfrTypes', [])
    infra_id_to_type = {}
    for infra in fueling_infra_types:
        # Only include electricity-based infrastructure
        if infra.get('fuel', '').lower() == 'electricity':
            infra_id_to_type[infra['id']] = infra['fueling_type']

    print(f"Electric fueling infrastructure types: {infra_id_to_type}")

    # Initialize: {year: {geo_id: {infra_name: kWh}}}
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

        # Only process electricity
        if fuel_id not in electricity_fuel_ids:
            continue

        # Convert to kWh
        energy_kwh = energy_value_scaled * SCALING_FACTOR

        # Only process NUTS2 nodes
        if geo_id not in nuts2_lookup:
            continue

        # Get infrastructure type
        infra_type = infra_id_to_type.get(fueling_infra_id, f'infra_{fueling_infra_id}')

        # Initialize if needed
        if geo_id not in data_by_year_geo[year]:
            data_by_year_geo[year][geo_id] = {
                'lat': nuts2_lookup[geo_id]['lat'],
                'nuts2': nuts2_lookup[geo_id]['nuts2']
            }

        # Add energy consumption by infrastructure type
        if infra_type not in data_by_year_geo[year][geo_id]:
            data_by_year_geo[year][geo_id][infra_type] = 0.0

        data_by_year_geo[year][geo_id][infra_type] += energy_kwh

    return data_by_year_geo

# Calculate data
print("Calculating electricity consumption by latitude and infrastructure type...")
electricity_data = calculate_electricity_by_latitude(case_name, target_years=[2030, 2040, 2050])

# Get list of all infrastructure types across all years
all_infra_types = set()
for year_data in electricity_data.values():
    for geo_data in year_data.values():
        for key in geo_data.keys():
            if key not in ['lat', 'nuts2']:
                all_infra_types.add(key)

all_infra_types = sorted(all_infra_types)
print(f"\nInfrastructure types found: {all_infra_types}")

# Display summary
print("\n" + "="*80)
print("SUMMARY: ELECTRICITY CONSUMPTION BY YEAR AND INFRASTRUCTURE TYPE")
print("="*80)
for year in [2030, 2040, 2050]:
    data = electricity_data[year]

    # Aggregate by infrastructure type
    infra_totals = {}
    for geo_data in data.values():
        for infra_type in all_infra_types:
            if infra_type in geo_data:
                infra_totals[infra_type] = infra_totals.get(infra_type, 0) + geo_data[infra_type]

    total_kwh = sum(infra_totals.values())

    print(f"\nYear {year}:")
    if total_kwh > 0:
        for infra_type in all_infra_types:
            kwh = infra_totals.get(infra_type, 0)
            pct = 100 * kwh / total_kwh if total_kwh > 0 else 0
            print(f"  {infra_type:30} {kwh/1e9:>8.2f} TWh ({pct:>5.1f}%)")
        print(f"  {'TOTAL':30} {total_kwh/1e9:>8.2f} TWh")
    else:
        print("  No electricity consumption found")

# ==============================================================================
# BEAUTIFUL PLOT: ELECTRICITY CONSUMPTION BY LATITUDE
# ==============================================================================

if len(all_infra_types) == 0:
    print("\n⚠️  No electricity consumption data found. Skipping visualization.")
else:
    years_to_plot = [2030, 2040, 2050]

    # Enhanced color palette - vibrant, professional colors with good contrast
    infra_colors = {
        'slow_charging_station': '#3498DB',      # Vivid blue
        'fast_charging_station': '#E74C3C',      # Vivid red
        'opportunity_charging': '#2ECC71',       # Emerald green
        'overhead_catenary': '#F39C12',          # Orange
        'battery_swapping': '#9B59B6',           # Purple
        'conventional_fueling_station': '#95A5A6' # Gray (if present)
    }

    # Friendly display names for infrastructure types
    infra_display_names = {
        'slow_charging_station': 'Slow Charging',
        'fast_charging_station': 'Fast Charging',
        'opportunity_charging': 'Opportunity Charging',
        'overhead_catenary': 'Overhead Catenary',
        'battery_swapping': 'Battery Swapping',
        'conventional_fueling_station': 'Conventional Fueling'
    }

    # Set style
    plt.style.use('seaborn-v0_8-darkgrid')

    # Create figure with enhanced proportions
    fig = plt.figure(figsize=(14, 18))
    gs = fig.add_gridspec(3, 1, hspace=0.12, top=0.96, bottom=0.06, left=0.10, right=0.88)
    axes = [fig.add_subplot(gs[i]) for i in range(3)]

    for year_idx, year in enumerate(years_to_plot):
        data = electricity_data[year]

        if not data:
            continue

        # Prepare data for plotting
        plotting_data = []
        for geo_id, metrics in data.items():
            lat = metrics['lat']

            # Get electricity by infrastructure type
            infra_kwh = {}
            for infra_type in all_infra_types:
                infra_kwh[infra_type] = metrics.get(infra_type, 0)

            total_kwh = sum(infra_kwh.values())

            if total_kwh > 0:
                plotting_data.append({
                    'lat': lat,
                    **infra_kwh
                })

        # Sort by latitude
        plotting_data.sort(key=lambda x: x['lat'])

        if len(plotting_data) < 2:
            continue

        # Extract arrays
        lats = np.array([d['lat'] for d in plotting_data])

        # Get data for each infrastructure type
        infra_arrays = {}
        for infra_type in all_infra_types:
            infra_arrays[infra_type] = np.array([d.get(infra_type, 0) for d in plotting_data])

        # Apply Gaussian smoothing with adaptive sigma
        sigma = 2.5  # Slightly increased for smoother curves
        infra_arrays_smooth = {}
        for infra_type, arr in infra_arrays.items():
            infra_arrays_smooth[infra_type] = gaussian_filter1d(arr, sigma=sigma)

        ax = axes[year_idx]

        # Convert to GWh for readability (1 GWh = 1,000,000 kWh)
        # Create stacked area plot with enhanced styling
        cumulative = np.zeros(len(lats))

        for infra_type in all_infra_types:
            arr_gwh = infra_arrays_smooth[infra_type] / 1e6
            color = infra_colors.get(infra_type, '#95A5A6')  # Default gray
            display_name = infra_display_names.get(infra_type, infra_type)

            ax.fill_betweenx(lats, cumulative, cumulative + arr_gwh,
                             color=color, alpha=0.85, label=display_name,
                             edgecolor='white', linewidth=0.8)
            cumulative += arr_gwh

        # Enhanced total outline
        ax.plot(cumulative, lats, 'k-', linewidth=2.5, alpha=0.6, zorder=10)

        # Enhanced styling
        ax.set_ylabel('Latitude (°N)', fontsize=14, fontweight='bold', labelpad=10)
        ax.set_title(f'{year}', fontsize=16, fontweight='bold', pad=15,
                    bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgray', alpha=0.3))

        # Enhanced grid
        ax.grid(True, alpha=0.25, linestyle='--', linewidth=0.8, color='gray')
        ax.set_xlim(left=0)

        # Enhanced axis styling
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_linewidth(1.5)
        ax.spines['bottom'].set_linewidth(1.5)

        # Tick styling
        ax.tick_params(axis='both', which='major', labelsize=11, width=1.5, length=6)

        # Enhanced legend (only for first subplot)
        if year_idx == 0 and len(all_infra_types) > 0:
            legend = ax.legend(loc='lower left', fontsize=11, framealpha=0.95,
                             edgecolor='black', fancybox=True, shadow=True,
                             bbox_to_anchor=(0.02, 0.02))
            legend.get_frame().set_linewidth(1.5)

    # Enhanced common x-label
    axes[-1].set_xlabel('Electricity Consumption (GWh)', fontsize=14,
                       fontweight='bold', labelpad=10)

    # Enhanced overall title with better spacing
    fig.suptitle('Electricity Consumption by Latitude and Fueling Infrastructure Type\n' +
                'Scandinavian-Mediterranean Corridor',
                fontsize=18, fontweight='bold', y=0.985,
                bbox=dict(boxstyle='round,pad=0.8', facecolor='lightblue', alpha=0.2))

    # ==============================================================================
    # ADD COUNTRY LABELS AND BORDERS WITH ENHANCED STYLING
    # ==============================================================================

    # Load country data
    country_centroids = pd.read_csv('country_centroids.csv')
    borders_df = pd.read_csv('country_southern_borders.csv')

    corridor_countries = ['IT', 'AT', 'DE', 'DK', 'NO', 'SE']
    country_data = country_centroids[country_centroids['CNTR_CODE'].isin(corridor_countries)]

    for ax in axes:
        ylim = ax.get_ylim()

        # Enhanced country labels with better styling
        for _, row in country_data.iterrows():
            country_code = row['CNTR_CODE']
            lat = row['centroid_lat']

            if ylim[0] <= lat <= ylim[1]:
                ax.text(1.03, lat, country_code, transform=ax.get_yaxis_transform(),
                       fontsize=11, fontweight='bold', va='center', ha='left',
                       bbox=dict(boxstyle='round,pad=0.4', facecolor='#FFE44D',
                                edgecolor='black', linewidth=1.2, alpha=0.9))

        # Enhanced border lines
        for _, row in borders_df.iterrows():
            country = row['CNTR_CODE']
            border_lat = row['southern_border_lat']

            if country in corridor_countries and ylim[0] <= border_lat <= ylim[1]:
                ax.axhline(y=border_lat, color='#34495E', linestyle='--',
                          linewidth=1.2, alpha=0.6, zorder=1)

    # Save with high quality
    plt.savefig('electricity_consumption_by_latitude.png', dpi=400,
                bbox_inches='tight', facecolor='white', edgecolor='none')
    print("\n✓ High-quality plot saved as 'electricity_consumption_by_latitude.png' (400 DPI)")
    plt.show()

# ==============================================================================
# ENHANCED INTERPRETATION GUIDE
# ==============================================================================

print("\n" + "="*80)
print("INTERPRETATION GUIDE: ELECTRICITY BY INFRASTRUCTURE TYPE")
print("="*80)
print("""
📊 WHAT THIS VISUALIZATION SHOWS:
   • Electricity consumption (GWh) for electric freight vehicles along the corridor
   • Breakdown by charging/fueling infrastructure type (color-coded)
   • Geographic distribution showing WHERE different charging technologies are deployed

⚡ INFRASTRUCTURE TYPES EXPLAINED:
   • Slow Charging (Blue): Depot/overnight charging (low power, long duration)
   • Fast Charging (Red): En-route quick charging stations (high power, short stops)
   • Opportunity Charging (Green): Brief top-ups during loading/unloading operations
   • Overhead Catenary (Orange): Electric road systems (e-highways with overhead wires)
   • Battery Swapping (Purple): Quick battery exchange stations

🔍 KEY INSIGHTS TO LOOK FOR:
   • Peaks indicate regions with high electric vehicle charging activity
   • Infrastructure mix reveals charging strategy preferences (depot vs en-route)
   • Temporal changes (2030→2040→2050) show infrastructure deployment evolution
   • Geographic patterns reveal corridor-specific electrification strategies

📈 CONTEXTUAL NOTES:
   • Only ELECTRIC vehicles shown (BEV, catenary trucks, etc.)
   • Does NOT include diesel, hydrogen, or other fuel types
   • Compare with total energy plots to assess electrification progress
   • Values include SCALING FACTOR of 1000 (model units × 1000 = kWh)

🎨 VISUAL FEATURES:
   • Gaussian smoothing (σ=2.5) for clearer trends
   • Country labels and borders for geographic reference
   • Stacked areas show cumulative consumption
   • Black outline indicates total electricity consumption envelope
""")
