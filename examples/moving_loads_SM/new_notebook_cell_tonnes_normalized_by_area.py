# ==============================================================================
# TONNES BY LATITUDE NORMALIZED BY NUTS2 REGION AREA
# ==============================================================================
from scipy.ndimage import gaussian_filter1d
import geopandas as gpd
from shapely.geometry import shape

def calculate_tonnes_normalized_by_area(case_study_name, nuts2_shapefile_path, target_years=[2030, 2040, 2050]):
    """
    Calculate freight tonnes normalized by NUTS2 region geographic area (km²).

    This metric shows "freight density per square kilometer" - regions with high values
    have concentrated freight traffic relative to their geographic size.

    Parameters:
        case_study_name: Name of the case study
        nuts2_shapefile_path: Path to NUTS2 regions shapefile
        target_years: Years to analyze

    Returns:
        dict: {year: {nuts2_id: {'road_tonnes': X, 'rail_tonnes': Y, 'area_km2': Z, ...}}}
    """
    input_data = loaded_runs[case_study_name]["input_data"]
    output_data = loaded_runs[case_study_name]["output_data"]
    f_data = output_data["f"]

    # Load NUTS2 shapefile and calculate areas
    print("Loading NUTS2 shapefile and calculating areas...")
    nuts2_gdf = gpd.read_file(nuts2_shapefile_path)

    # Calculate area in km² (convert from m² if needed)
    if nuts2_gdf.crs.is_geographic:
        # If CRS is geographic (lat/lon), reproject to appropriate projected CRS
        nuts2_gdf = nuts2_gdf.to_crs('EPSG:3035')  # ETRS89-extended / LAEA Europe

    nuts2_gdf['area_km2'] = nuts2_gdf.geometry.area / 1e6  # Convert m² to km²

    # Create lookup: NUTS2 code -> area in km²
    nuts2_area_lookup = {}
    for idx, row in nuts2_gdf.iterrows():
        nuts2_code = row['NUTS_ID']  # Adjust field name if different in your shapefile
        nuts2_area_lookup[nuts2_code] = row['area_km2']

    print(f"Loaded area data for {len(nuts2_area_lookup)} NUTS2 regions")

    # Load geographic elements
    geo_elements = input_data['GeographicElement']
    nuts2_lookup = {}
    for geo in geo_elements:
        if geo['type'] == 'node' and 'nuts2_region' in geo and geo['nuts2_region']:
            nuts2_code = geo['nuts2_region']
            nuts2_lookup[geo['id']] = {
                'nuts2': nuts2_code,
                'lat': geo['coordinate_lat'],
                'lon': geo['coordinate_long'],
                'country': geo.get('country', 'UNKNOWN'),
                'area_km2': nuts2_area_lookup.get(nuts2_code, None)
            }

    # Check for missing areas
    missing_areas = [n['nuts2'] for n in nuts2_lookup.values() if n['area_km2'] is None]
    if missing_areas:
        print(f"⚠️  Warning: {len(set(missing_areas))} NUTS2 regions missing area data: {set(missing_areas)}")

    # Load paths and odpairs
    paths = input_data['Path']
    odpairs = input_data['Odpair']

    path_lookup = {}
    for path in paths:
        path_lookup[path['id']] = {
            'sequence': path['sequence'],
            'distance_from_previous': path['distance_from_previous']
        }

    od_lookup = {}
    for od in odpairs:
        od_lookup[od['id']] = {
            'origin': od['from'],
            'destination': od['to']
        }

    # Calculate tonnes by region
    print("Calculating tonnes by region...")
    data_by_year_nuts2 = {year: {} for year in target_years}

    SCALING_FACTOR = 1000  # f is in kilotonnes

    for key_str, flow_value_kt in f_data.items():
        key = eval(key_str) if isinstance(key_str, str) else key_str
        year, (product_id, odpair_id, path_id), (mode_id, techvehicle_id), generation = key

        if year not in target_years or flow_value_kt <= 0:
            continue

        if path_id not in path_lookup or odpair_id not in od_lookup:
            continue

        flow_value_tonnes = flow_value_kt * SCALING_FACTOR
        path_info = path_lookup[path_id]
        mode_name = 'rail' if mode_id == 2 else 'road'

        # Add tonnes to each NUTS2 region in the path
        for node_id in path_info['sequence']:
            if node_id in nuts2_lookup:
                nuts2_id = nuts2_lookup[node_id]['nuts2']
                area_km2 = nuts2_lookup[node_id]['area_km2']

                # Skip regions without area data
                if area_km2 is None or area_km2 <= 0:
                    continue

                if nuts2_id not in data_by_year_nuts2[year]:
                    data_by_year_nuts2[year][nuts2_id] = {
                        'road_tonnes': 0.0,
                        'rail_tonnes': 0.0,
                        'lat': nuts2_lookup[node_id]['lat'],
                        'country': nuts2_lookup[node_id]['country'],
                        'area_km2': area_km2
                    }

                data_by_year_nuts2[year][nuts2_id][f'{mode_name}_tonnes'] += flow_value_tonnes

    # Normalize by area
    print("Normalizing by geographic area...")
    for year in target_years:
        for nuts2_id, data in data_by_year_nuts2[year].items():
            area = data['area_km2']

            # Calculate normalized values (tonnes per km²)
            data['road_tonnes_per_km2'] = data['road_tonnes'] / area
            data['rail_tonnes_per_km2'] = data['rail_tonnes'] / area
            data['total_tonnes'] = data['road_tonnes'] + data['rail_tonnes']
            data['total_tonnes_per_km2'] = data['total_tonnes'] / area

    return data_by_year_nuts2, nuts2_gdf

# ==============================================================================
# LOAD DATA AND CALCULATE
# ==============================================================================

# Path to NUTS2 shapefile
nuts2_shapefile = 'data/NUTS_RG_20M_2021_4326.shp'

print("="*80)
print("CALCULATING FREIGHT DENSITY NORMALIZED BY GEOGRAPHIC AREA")
print("="*80)

try:
    normalized_data, nuts2_gdf = calculate_tonnes_normalized_by_area(
        case_name,
        nuts2_shapefile,
        target_years=[2030, 2040, 2050]
    )
except FileNotFoundError:
    print(f"\n⚠️  Error: Shapefile not found at '{nuts2_shapefile}'")
    print("Please check the path to the NUTS2 shapefile.")
    print("Expected location: data/NUTS_RG_20M_2021_4326.shp")
    raise

# Display summary
print("\n" + "="*80)
print("SUMMARY: FREIGHT DENSITY BY GEOGRAPHIC AREA")
print("="*80)

for year in [2030, 2040, 2050]:
    data = normalized_data[year]

    total_road_tonnes = sum(d['road_tonnes'] for d in data.values())
    total_rail_tonnes = sum(d['rail_tonnes'] for d in data.values())
    total_tonnes = total_road_tonnes + total_rail_tonnes

    # Calculate weighted average density
    total_area = sum(d['area_km2'] for d in data.values())
    avg_density = total_tonnes / total_area if total_area > 0 else 0

    print(f"\nYear {year}:")
    print(f"  Total freight: {total_tonnes/1e9:.2f} Mt")
    print(f"  Total area: {total_area:,.0f} km²")
    print(f"  Average density: {avg_density:.2f} tonnes/km²")
    print(f"  Road: {total_road_tonnes/1e9:.2f} Mt ({100*total_road_tonnes/total_tonnes:.1f}%)")
    print(f"  Rail: {total_rail_tonnes/1e9:.2f} Mt ({100*total_rail_tonnes/total_tonnes:.1f}%)")

# ==============================================================================
# BEAUTIFUL PLOT: AREA-NORMALIZED FREIGHT DENSITY BY LATITUDE
# ==============================================================================

years_to_plot = [2030, 2040, 2050]

# Set style
plt.style.use('seaborn-v0_8-darkgrid')

# Create figure: 3 rows × 2 columns (left=raw, right=normalized)
fig = plt.figure(figsize=(16, 18))
gs = fig.add_gridspec(3, 2, hspace=0.15, wspace=0.25,
                      top=0.95, bottom=0.06, left=0.08, right=0.90)

for year_idx, year in enumerate(years_to_plot):
    data = normalized_data[year]

    if not data:
        continue

    # Prepare plotting data
    plotting_data = []
    for nuts2_id, metrics in data.items():
        plotting_data.append({
            'nuts2': nuts2_id,
            'lat': metrics['lat'],
            'country': metrics['country'],
            'road_tonnes': metrics['road_tonnes'],
            'rail_tonnes': metrics['rail_tonnes'],
            'road_tonnes_per_km2': metrics['road_tonnes_per_km2'],
            'rail_tonnes_per_km2': metrics['rail_tonnes_per_km2'],
            'area_km2': metrics['area_km2']
        })

    # Sort by latitude
    plotting_data.sort(key=lambda x: x['lat'])

    if len(plotting_data) < 2:
        continue

    # Extract arrays
    lats = np.array([d['lat'] for d in plotting_data])

    # RAW DATA
    road_tonnes = np.array([d['road_tonnes'] for d in plotting_data])
    rail_tonnes = np.array([d['rail_tonnes'] for d in plotting_data])

    # NORMALIZED DATA (tonnes per km²)
    road_tonnes_norm = np.array([d['road_tonnes_per_km2'] for d in plotting_data])
    rail_tonnes_norm = np.array([d['rail_tonnes_per_km2'] for d in plotting_data])

    # Apply Gaussian smoothing
    sigma = 2.0
    road_smooth = gaussian_filter1d(road_tonnes, sigma=sigma)
    rail_smooth = gaussian_filter1d(rail_tonnes, sigma=sigma)
    road_norm_smooth = gaussian_filter1d(road_tonnes_norm, sigma=sigma)
    rail_norm_smooth = gaussian_filter1d(rail_tonnes_norm, sigma=sigma)

    # ==============================================================================
    # LEFT COLUMN: RAW TONNES
    # ==============================================================================

    ax_raw = fig.add_subplot(gs[year_idx, 0])

    # Convert to million tonnes for readability
    road_mt = road_smooth / 1e6
    rail_mt = rail_smooth / 1e6

    # Stacked area plot
    ax_raw.fill_betweenx(lats, 0, road_mt,
                         color='#E74C3C', alpha=0.7, label='Road',
                         edgecolor='darkred', linewidth=1.2)
    ax_raw.fill_betweenx(lats, road_mt, road_mt + rail_mt,
                         color='#3498DB', alpha=0.7, label='Rail',
                         edgecolor='darkblue', linewidth=1.2)

    # Total outline
    total_mt = road_mt + rail_mt
    ax_raw.plot(total_mt, lats, 'k-', linewidth=2.5, alpha=0.6, zorder=10)

    # Styling
    ax_raw.set_ylabel('Latitude (°N)', fontsize=13, fontweight='bold', labelpad=10)
    ax_raw.set_title(f'{year} - Raw Tonnes', fontsize=14, fontweight='bold', pad=12,
                    bbox=dict(boxstyle='round,pad=0.5', facecolor='lightcoral', alpha=0.3))

    ax_raw.grid(True, alpha=0.25, linestyle='--', linewidth=0.8)
    ax_raw.set_xlim(left=0)

    # Enhanced axis styling
    ax_raw.spines['top'].set_visible(False)
    ax_raw.spines['right'].set_visible(False)
    ax_raw.spines['left'].set_linewidth(1.5)
    ax_raw.spines['bottom'].set_linewidth(1.5)
    ax_raw.tick_params(axis='both', which='major', labelsize=10, width=1.5, length=6)

    if year_idx == 0:
        legend = ax_raw.legend(loc='lower left', fontsize=10, framealpha=0.95,
                              edgecolor='black', fancybox=True, shadow=True,
                              bbox_to_anchor=(0.02, 0.02))
        legend.get_frame().set_linewidth(1.5)

    # ==============================================================================
    # RIGHT COLUMN: NORMALIZED (TONNES PER KM²)
    # ==============================================================================

    ax_norm = fig.add_subplot(gs[year_idx, 1])

    # Use raw values for better visibility (tonnes/km² already reasonable scale)
    road_t_per_km2 = road_norm_smooth
    rail_t_per_km2 = rail_norm_smooth

    # Stacked area plot
    ax_norm.fill_betweenx(lats, 0, road_t_per_km2,
                          color='#E74C3C', alpha=0.7, label='Road',
                          edgecolor='darkred', linewidth=1.2)
    ax_norm.fill_betweenx(lats, road_t_per_km2, road_t_per_km2 + rail_t_per_km2,
                          color='#3498DB', alpha=0.7, label='Rail',
                          edgecolor='darkblue', linewidth=1.2)

    # Total outline
    total_t_per_km2 = road_t_per_km2 + rail_t_per_km2
    ax_norm.plot(total_t_per_km2, lats, 'k-', linewidth=2.5, alpha=0.6, zorder=10)

    # Styling
    ax_norm.set_title(f'{year} - Freight Density (t/km²)', fontsize=14, fontweight='bold', pad=12,
                     bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgreen', alpha=0.3))

    ax_norm.grid(True, alpha=0.25, linestyle='--', linewidth=0.8)
    ax_norm.set_xlim(left=0)

    # Enhanced axis styling
    ax_norm.spines['top'].set_visible(False)
    ax_norm.spines['right'].set_visible(False)
    ax_norm.spines['left'].set_visible(False)
    ax_norm.spines['bottom'].set_linewidth(1.5)
    ax_norm.tick_params(axis='both', which='major', labelsize=10, width=1.5, length=6)
    ax_norm.tick_params(axis='y', left=False, labelleft=False)

    # ==============================================================================
    # ADD COUNTRY LABELS AND BORDERS
    # ==============================================================================

    # Load country data
    country_centroids = pd.read_csv('country_centroids.csv')
    borders_df = pd.read_csv('country_southern_borders.csv')

    corridor_countries = ['IT', 'AT', 'DE', 'DK', 'NO', 'SE']
    country_data = country_centroids[country_centroids['CNTR_CODE'].isin(corridor_countries)]

    for ax in [ax_raw, ax_norm]:
        ylim = ax.get_ylim()

        # Add country labels (only on left panel)
        if ax == ax_raw:
            for _, row in country_data.iterrows():
                country_code = row['CNTR_CODE']
                lat = row['centroid_lat']

                if ylim[0] <= lat <= ylim[1]:
                    ax.text(-0.12, lat, country_code, transform=ax.get_yaxis_transform(),
                           fontsize=10, fontweight='bold', va='center', ha='right',
                           bbox=dict(boxstyle='round,pad=0.4', facecolor='#FFE44D',
                                    edgecolor='black', linewidth=1.2, alpha=0.9))

        # Add border lines
        for _, row in borders_df.iterrows():
            country = row['CNTR_CODE']
            border_lat = row['southern_border_lat']

            if country in corridor_countries and ylim[0] <= border_lat <= ylim[1]:
                ax.axhline(y=border_lat, color='#34495E', linestyle='--',
                          linewidth=1.2, alpha=0.5, zorder=1)

# X-axis labels
axes_bottom = [fig.add_subplot(gs[2, 0]), fig.add_subplot(gs[2, 1])]
axes_bottom[0].set_xlabel('Freight Volume (Mt)', fontsize=13, fontweight='bold', labelpad=10)
axes_bottom[1].set_xlabel('Freight Density (t/km²)', fontsize=13, fontweight='bold', labelpad=10)

# Overall title
fig.suptitle('Freight Volume vs Geographic Freight Density (Normalized by NUTS2 Area)\n' +
            'Scandinavian-Mediterranean Corridor',
            fontsize=17, fontweight='bold', y=0.98,
            bbox=dict(boxstyle='round,pad=0.8', facecolor='lightyellow', alpha=0.3))

# Save with high quality
plt.savefig('tonnes_normalized_by_area.png', dpi=400,
            bbox_inches='tight', facecolor='white', edgecolor='none')
print("\n✓ High-quality plot saved as 'tonnes_normalized_by_area.png' (400 DPI)")
plt.show()

# ==============================================================================
# TOP REGIONS ANALYSIS
# ==============================================================================

print("\n" + "="*80)
print("TOP 10 REGIONS BY GEOGRAPHIC FREIGHT DENSITY (2030)")
print("="*80)

year_2030_data = []
for nuts2_id, metrics in normalized_data[2030].items():
    year_2030_data.append({
        'nuts2': nuts2_id,
        'country': metrics['country'],
        'lat': metrics['lat'],
        'total_tonnes': metrics['total_tonnes'],
        'total_tonnes_per_km2': metrics['total_tonnes_per_km2'],
        'area_km2': metrics['area_km2']
    })

# Sort by area-normalized density
year_2030_data.sort(key=lambda x: x['total_tonnes_per_km2'], reverse=True)

print(f"{'Rank':<6} {'NUTS2':<8} {'Country':<8} {'Raw Tonnes':>15} {'t/km²':>12} {'Area (km²)':>15}")
print("-" * 80)

for i, d in enumerate(year_2030_data[:10], 1):
    print(f"{i:<6} {d['nuts2']:<8} {d['country']:<8} "
          f"{d['total_tonnes']/1e6:>14.2f} Mt {d['total_tonnes_per_km2']:>12.1f} "
          f"{d['area_km2']:>15,.0f}")

# ==============================================================================
# INTERPRETATION GUIDE
# ==============================================================================

print("\n" + "="*80)
print("INTERPRETATION GUIDE: GEOGRAPHIC FREIGHT DENSITY")
print("="*80)
print("""
📊 WHAT THIS SHOWS:
   LEFT PANELS:  Raw freight volume (tonnes) passing through each latitude
   RIGHT PANELS: Freight density normalized by NUTS2 region geographic area (tonnes/km²)

🗺️ WHY NORMALIZE BY GEOGRAPHIC AREA?

   Geographic area normalization reveals TRUE freight concentration:

   • LARGE REGIONS (e.g., Scandinavia):
     - May have high raw tonnes simply due to large geographic size
     - Normalization reveals actual freight density (tonnes per unit area)

   • SMALL REGIONS (e.g., city-states, dense urban areas):
     - May appear to have low raw tonnes despite high activity
     - Normalization amplifies these true high-density logistics hubs

📈 INTERPRETING THE RESULTS:

   HIGH t/km² values = Geographic freight "hotspots"
   - High traffic concentration per unit area
   - Intense logistics activity
   - Urban/metropolitan centers with dense freight flows

   LOW t/km² values = Sparse freight distribution
   - Large regions with dispersed activity
   - Rural or low-population areas
   - Transit corridors through low-density regions

🎯 KEY INSIGHTS:

   • Urban regions will show dramatically higher normalized density
   • Large northern regions (NO, SE) will show lower density despite high raw volumes
   • Small industrial regions (parts of DE, IT) may reveal hidden intensity
   • Identifies TRUE logistics bottlenecks and congestion points

📏 AREA CALCULATION:
   • Areas calculated from NUTS2 official shapefile (GISCO)
   • Projected to EPSG:3035 (ETRS89-LAEA Europe) for accurate km² calculation
   • Typical NUTS2 areas: 1,000-20,000 km²

🔍 COMPARISON WITH NETWORK-BASED NORMALIZATION:
   • Geographic area (this plot): Physical freight concentration
   • Network distance (previous plot): Infrastructure utilization intensity
   • Both perspectives reveal different aspects of freight patterns

⚠️ IMPORTANT:
   • Regions with missing area data are excluded
   • Uses NUTS 2021 boundaries
   • Full freight (imports + exports + domestic + transit) counted at each node
""")
