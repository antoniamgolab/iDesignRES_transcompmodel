# ==============================================================================
# TONNES BY LATITUDE NORMALIZED BY AVERAGE SEGMENT DISTANCE
# ==============================================================================
from scipy.ndimage import gaussian_filter1d

def calculate_tonnes_normalized_by_distance(case_study_name, target_years=[2030, 2040, 2050]):
    """
    Calculate freight tonnes normalized by average segment distance for each NUTS2 region.

    This metric shows "freight density per kilometer" - regions with high values have
    concentrated freight traffic relative to their network spacing.

    Returns:
        dict: {year: {nuts2_id: {'road_tonnes': X, 'rail_tonnes': Y, 'avg_distance_km': Z, ...}}}
    """
    input_data = loaded_runs[case_study_name]["input_data"]
    output_data = loaded_runs[case_study_name]["output_data"]
    f_data = output_data["f"]

    # Load geographic elements
    geo_elements = input_data['GeographicElement']
    nuts2_lookup = {}
    for geo in geo_elements:
        if geo['type'] == 'node' and 'nuts2_region' in geo and geo['nuts2_region']:
            nuts2_lookup[geo['id']] = {
                'nuts2': geo['nuts2_region'],
                'lat': geo['coordinate_lat'],
                'lon': geo['coordinate_long'],
                'country': geo.get('country', 'UNKNOWN')
            }

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

    # First pass: Calculate average distance for each NUTS2 region
    print("Calculating average segment distances...")
    nuts2_distances = {}

    for path in paths:
        sequence = path['sequence']
        distance_from_previous = path['distance_from_previous']

        for i, node_id in enumerate(sequence):
            if node_id in nuts2_lookup:
                nuts2_id = nuts2_lookup[node_id]['nuts2']
                distance_km = distance_from_previous[i]

                if nuts2_id not in nuts2_distances:
                    nuts2_distances[nuts2_id] = []

                if distance_km > 0:
                    nuts2_distances[nuts2_id].append(distance_km)

    # Calculate average for each region
    nuts2_avg_distance = {}
    for nuts2_id, distances in nuts2_distances.items():
        if distances:
            nuts2_avg_distance[nuts2_id] = sum(distances) / len(distances)
        else:
            nuts2_avg_distance[nuts2_id] = 1.0  # Avoid division by zero

    print(f"Calculated average distances for {len(nuts2_avg_distance)} NUTS2 regions")

    # Second pass: Calculate tonnes by region
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

                if nuts2_id not in data_by_year_nuts2[year]:
                    data_by_year_nuts2[year][nuts2_id] = {
                        'road_tonnes': 0.0,
                        'rail_tonnes': 0.0,
                        'lat': nuts2_lookup[node_id]['lat'],
                        'country': nuts2_lookup[node_id]['country'],
                        'avg_distance_km': nuts2_avg_distance.get(nuts2_id, 1.0)
                    }

                data_by_year_nuts2[year][nuts2_id][f'{mode_name}_tonnes'] += flow_value_tonnes

    # Third pass: Normalize by average distance
    print("Normalizing by average segment distance...")
    for year in target_years:
        for nuts2_id, data in data_by_year_nuts2[year].items():
            avg_dist = data['avg_distance_km']

            # Calculate normalized values (tonnes per km)
            data['road_tonnes_per_km'] = data['road_tonnes'] / avg_dist
            data['rail_tonnes_per_km'] = data['rail_tonnes'] / avg_dist
            data['total_tonnes'] = data['road_tonnes'] + data['rail_tonnes']
            data['total_tonnes_per_km'] = data['total_tonnes'] / avg_dist

    return data_by_year_nuts2

# Calculate data
print("="*80)
print("CALCULATING NORMALIZED FREIGHT DENSITY")
print("="*80)
normalized_data = calculate_tonnes_normalized_by_distance(case_name, target_years=[2030, 2040, 2050])

# Display summary
print("\n" + "="*80)
print("SUMMARY: NORMALIZED FREIGHT DENSITY BY YEAR")
print("="*80)

for year in [2030, 2040, 2050]:
    data = normalized_data[year]

    total_road_tonnes = sum(d['road_tonnes'] for d in data.values())
    total_rail_tonnes = sum(d['rail_tonnes'] for d in data.values())
    total_tonnes = total_road_tonnes + total_rail_tonnes

    # Also calculate normalized totals
    total_road_normalized = sum(d['road_tonnes_per_km'] for d in data.values())
    total_rail_normalized = sum(d['rail_tonnes_per_km'] for d in data.values())
    total_normalized = total_road_normalized + total_rail_normalized

    print(f"\nYear {year}:")
    print(f"  Raw Tonnes:")
    print(f"    Road: {total_road_tonnes/1e9:.2f} Mt  |  Rail: {total_rail_tonnes/1e9:.2f} Mt  |  Total: {total_tonnes/1e9:.2f} Mt")
    print(f"  Normalized (tonnes/km of network):")
    print(f"    Road: {total_road_normalized/1e6:.2f} Mt/km  |  Rail: {total_rail_normalized/1e6:.2f} Mt/km  |  Total: {total_normalized/1e6:.2f} Mt/km")

# ==============================================================================
# BEAUTIFUL PLOT: NORMALIZED FREIGHT DENSITY BY LATITUDE
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
            'road_tonnes_per_km': metrics['road_tonnes_per_km'],
            'rail_tonnes_per_km': metrics['rail_tonnes_per_km'],
            'avg_distance_km': metrics['avg_distance_km']
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

    # NORMALIZED DATA
    road_tonnes_norm = np.array([d['road_tonnes_per_km'] for d in plotting_data])
    rail_tonnes_norm = np.array([d['rail_tonnes_per_km'] for d in plotting_data])

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
    # RIGHT COLUMN: NORMALIZED (TONNES PER KM)
    # ==============================================================================

    ax_norm = fig.add_subplot(gs[year_idx, 1])

    # Convert to kilotonnes per km for readability
    road_kt_per_km = road_norm_smooth / 1e3
    rail_kt_per_km = rail_norm_smooth / 1e3

    # Stacked area plot
    ax_norm.fill_betweenx(lats, 0, road_kt_per_km,
                          color='#E74C3C', alpha=0.7, label='Road',
                          edgecolor='darkred', linewidth=1.2)
    ax_norm.fill_betweenx(lats, road_kt_per_km, road_kt_per_km + rail_kt_per_km,
                          color='#3498DB', alpha=0.7, label='Rail',
                          edgecolor='darkblue', linewidth=1.2)

    # Total outline
    total_kt_per_km = road_kt_per_km + rail_kt_per_km
    ax_norm.plot(total_kt_per_km, lats, 'k-', linewidth=2.5, alpha=0.6, zorder=10)

    # Styling
    ax_norm.set_title(f'{year} - Freight Density (normalized)', fontsize=14, fontweight='bold', pad=12,
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
axes_bottom[1].set_xlabel('Freight Density (kt/km)', fontsize=13, fontweight='bold', labelpad=10)

# Overall title
fig.suptitle('Freight Volume vs Freight Density (Normalized by Network Spacing)\n' +
            'Scandinavian-Mediterranean Corridor',
            fontsize=17, fontweight='bold', y=0.98,
            bbox=dict(boxstyle='round,pad=0.8', facecolor='lightyellow', alpha=0.3))

# Save with high quality
plt.savefig('tonnes_normalized_by_distance.png', dpi=400,
            bbox_inches='tight', facecolor='white', edgecolor='none')
print("\n✓ High-quality plot saved as 'tonnes_normalized_by_distance.png' (400 DPI)")
plt.show()

# ==============================================================================
# TOP REGIONS ANALYSIS
# ==============================================================================

print("\n" + "="*80)
print("TOP 10 REGIONS BY NORMALIZED FREIGHT DENSITY (2030)")
print("="*80)

year_2030_data = []
for nuts2_id, metrics in normalized_data[2030].items():
    year_2030_data.append({
        'nuts2': nuts2_id,
        'country': metrics['country'],
        'lat': metrics['lat'],
        'total_tonnes': metrics['total_tonnes'],
        'total_tonnes_per_km': metrics['total_tonnes_per_km'],
        'avg_distance_km': metrics['avg_distance_km']
    })

# Sort by normalized density
year_2030_data.sort(key=lambda x: x['total_tonnes_per_km'], reverse=True)

print(f"{'Rank':<6} {'NUTS2':<8} {'Country':<8} {'Raw Tonnes':>15} {'Tonnes/km':>15} {'Avg Dist':>12}")
print("-" * 80)

for i, d in enumerate(year_2030_data[:10], 1):
    print(f"{i:<6} {d['nuts2']:<8} {d['country']:<8} "
          f"{d['total_tonnes']/1e6:>14.2f} Mt {d['total_tonnes_per_km']/1e3:>14.2f} kt/km "
          f"{d['avg_distance_km']:>11.1f} km")

# ==============================================================================
# INTERPRETATION GUIDE
# ==============================================================================

print("\n" + "="*80)
print("INTERPRETATION GUIDE: NORMALIZED FREIGHT DENSITY")
print("="*80)
print("""
📊 WHAT THIS SHOWS:
   LEFT PANELS:  Raw freight volume (tonnes) passing through each latitude
   RIGHT PANELS: Freight density normalized by average network segment distance (tonnes/km)

🔍 WHY NORMALIZE BY DISTANCE?

   The normalization accounts for network topology:

   • SPARSE NETWORKS (long average distances):
     - Raw tonnes may appear high simply because paths are long
     - Normalization reveals TRUE concentration of freight activity

   • DENSE NETWORKS (short average distances):
     - Raw tonnes may appear lower despite high activity
     - Normalization amplifies these high-density regions

📈 INTERPRETING THE RESULTS:

   HIGH normalized values = True freight "hotspots"
   - High traffic concentration relative to network structure
   - Important logistics hubs and corridors
   - NOT just artifacts of long-distance paths

   DIFFERENCES between left/right panels reveal:
   - Regions where network topology inflates/deflates raw volumes
   - True concentration of freight activity vs geographic spread

🎯 KEY INSIGHTS:

   • Peaks shift between raw and normalized views
   • Italian peak may change if network is sparse (long distances)
   • German regions may show higher density if network is dense (short distances)
   • Helps identify ACTUAL logistics bottlenecks vs geographic artifacts

⚙️ TECHNICAL DETAILS:
   • Normalization: tonnes / (average segment distance for that region)
   • Average distance calculated from all path segments touching each region
   • Smoothing: Gaussian (σ=2.0) for visual clarity
   • Units: Left (Mt), Right (kt/km)
""")
