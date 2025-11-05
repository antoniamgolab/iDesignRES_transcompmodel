# ==============================================================================
# TONNES vs TKM BY LATITUDE - TWO-PANEL COMPARISON
# ==============================================================================
from scipy.ndimage import gaussian_filter1d

def calculate_tonnes_and_tkm_by_latitude(case_study_name, target_years=[2030, 2040, 2050]):
    """
    Calculate both TONNES (freight volume) and TKM (transport work) by NUTS2 region.

    This separates:
    - TONNES: How much freight passes through each region
    - TKM: How much transport work (distance × weight) occurs in each region

    Returns:
        dict: {year: {nuts2_id: {'road_tonnes': X, 'rail_tonnes': X, 'road_tkm': X, 'rail_tkm': X, 'lat': X}}}
    """
    input_data = loaded_runs[case_study_name]["input_data"]
    output_data = loaded_runs[case_study_name]["output_data"]
    f_data = output_data["f"]

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

    # Load paths
    paths = {p['id']: p for p in input_data['Path']}

    # Initialize: {year: {geo_id: {metrics}}}
    data_by_year_geo = {year: {} for year in target_years}

    # SCALING FACTOR: f is in kilotonnes, multiply by 1000 to get tonnes
    SCALING_FACTOR = 1000

    # Process each flow
    for key, flow_value_kt in f_data.items():
        year, (prod_id, od_id, path_id), (mode_id, tv_id), gen = key

        if year not in target_years or flow_value_kt <= 0:
            continue

        # Convert to tonnes
        flow_value_tonnes = flow_value_kt * SCALING_FACTOR

        # Get path data
        path = paths[path_id]
        sequence = path['sequence']
        distance_from_previous = path['distance_from_previous']

        mode_name = 'rail' if mode_id == 2 else 'road'

        # Assign TONNES and TKM to each node based on distance_from_previous
        for i, node_id in enumerate(sequence):
            # Only process NUTS2 nodes
            if node_id not in nuts2_lookup:
                continue

            # TKM = flow × distance traveled TO this node
            segment_distance = distance_from_previous[i]
            tkm_segment = flow_value_tonnes * segment_distance

            # Initialize if needed
            if node_id not in data_by_year_geo[year]:
                data_by_year_geo[year][node_id] = {
                    'road_tonnes': 0.0,
                    'rail_tonnes': 0.0,
                    'road_tkm': 0.0,
                    'rail_tkm': 0.0,
                    'lat': nuts2_lookup[node_id]['lat'],
                    'nuts2': nuts2_lookup[node_id]['nuts2']
                }

            # Add tonnes (full flow passes through this node)
            data_by_year_geo[year][node_id][f'{mode_name}_tonnes'] += flow_value_tonnes

            # Add TKM (flow × segment distance)
            data_by_year_geo[year][node_id][f'{mode_name}_tkm'] += tkm_segment

    return data_by_year_geo

# Calculate data
print("Calculating TONNES and TKM by latitude...")
tonnes_tkm_data = calculate_tonnes_and_tkm_by_latitude(case_name, target_years=[2030, 2040, 2050])

# Display summary
print("\n" + "="*80)
print("SUMMARY: TONNES vs TKM")
print("="*80)
for year in [2030, 2040, 2050]:
    data = tonnes_tkm_data[year]

    total_road_tonnes = sum(d['road_tonnes'] for d in data.values())
    total_rail_tonnes = sum(d['rail_tonnes'] for d in data.values())
    total_road_tkm = sum(d['road_tkm'] for d in data.values())
    total_rail_tkm = sum(d['rail_tkm'] for d in data.values())

    print(f"\nYear {year}:")
    print(f"  TONNES - Road: {total_road_tonnes/1e6:.1f}M, Rail: {total_rail_tonnes/1e6:.1f}M, Total: {(total_road_tonnes+total_rail_tonnes)/1e6:.1f}M")
    print(f"  TKM    - Road: {total_road_tkm/1e9:.2f}B, Rail: {total_rail_tkm/1e9:.2f}B, Total: {(total_road_tkm+total_rail_tkm)/1e9:.2f}B")

    avg_distance = (total_road_tkm + total_rail_tkm) / (total_road_tonnes + total_rail_tonnes)
    print(f"  Average distance per tonne: {avg_distance:.1f} km")

# ==============================================================================
# PLOT: TWO-PANEL COMPARISON - TONNES vs TKM BY LATITUDE
# ==============================================================================

years_to_plot = [2030, 2040, 2050]
colors = ['#3498DB', '#2ECC71', '#F39C12']

# Create figure with 2 columns × 3 rows (one row per year)
fig, axes = plt.subplots(3, 2, figsize=(16, 18), sharey='row')

for year_idx, (year, color) in enumerate(zip(years_to_plot, colors)):
    data = tonnes_tkm_data[year]

    if not data:
        continue

    # Prepare data for plotting
    plotting_data = []
    for geo_id, metrics in data.items():
        lat = metrics['lat']
        total_tonnes = metrics['road_tonnes'] + metrics['rail_tonnes']
        total_tkm = metrics['road_tkm'] + metrics['rail_tkm']

        if total_tonnes > 0 or total_tkm > 0:
            plotting_data.append({
                'lat': lat,
                'road_tonnes': metrics['road_tonnes'],
                'rail_tonnes': metrics['rail_tonnes'],
                'road_tkm': metrics['road_tkm'],
                'rail_tkm': metrics['rail_tkm']
            })

    # Sort by latitude
    plotting_data.sort(key=lambda x: x['lat'])

    if len(plotting_data) < 2:
        continue

    # Extract arrays
    lats = np.array([d['lat'] for d in plotting_data])
    road_tonnes = np.array([d['road_tonnes'] for d in plotting_data])
    rail_tonnes = np.array([d['rail_tonnes'] for d in plotting_data])
    road_tkm = np.array([d['road_tkm'] for d in plotting_data])
    rail_tkm = np.array([d['rail_tkm'] for d in plotting_data])

    # Apply Gaussian smoothing
    sigma = 2.0
    road_tonnes_smooth = gaussian_filter1d(road_tonnes, sigma=sigma)
    rail_tonnes_smooth = gaussian_filter1d(rail_tonnes, sigma=sigma)
    road_tkm_smooth = gaussian_filter1d(road_tkm, sigma=sigma)
    rail_tkm_smooth = gaussian_filter1d(rail_tkm, sigma=sigma)

    # ========== LEFT PANEL: TONNES ==========
    ax_tonnes = axes[year_idx, 0]

    # Convert to millions
    road_tonnes_M = road_tonnes_smooth / 1e6
    rail_tonnes_M = rail_tonnes_smooth / 1e6

    # Stacked area plot
    ax_tonnes.fill_betweenx(lats, 0, road_tonnes_M,
                             color='#E74C3C', alpha=0.6, label='Road', edgecolor='darkred', linewidth=1.5)
    ax_tonnes.fill_betweenx(lats, road_tonnes_M, road_tonnes_M + rail_tonnes_M,
                             color='#3498DB', alpha=0.6, label='Rail', edgecolor='darkblue', linewidth=1.5)

    # Total outline
    total_tonnes_M = road_tonnes_M + rail_tonnes_M
    ax_tonnes.plot(total_tonnes_M, lats, 'k-', linewidth=2, alpha=0.5)

    ax_tonnes.set_xlabel('Freight Volume (Million tonnes)', fontsize=12, fontweight='bold')
    ax_tonnes.set_ylabel('Latitude (°N)', fontsize=12, fontweight='bold')
    ax_tonnes.set_title(f'Year {year}', fontsize=13, fontweight='bold', pad=10)
    ax_tonnes.grid(True, alpha=0.3, linestyle='--')
    ax_tonnes.set_xlim(left=0)

    if year_idx == 0:
        ax_tonnes.legend(loc='lower left', fontsize=11, framealpha=0.95)

    # ========== RIGHT PANEL: TKM ==========
    ax_tkm = axes[year_idx, 1]

    # Convert to billions
    road_tkm_B = road_tkm_smooth / 1e9
    rail_tkm_B = rail_tkm_smooth / 1e9

    # Stacked area plot
    ax_tkm.fill_betweenx(lats, 0, road_tkm_B,
                          color='#E74C3C', alpha=0.6, label='Road', edgecolor='darkred', linewidth=1.5)
    ax_tkm.fill_betweenx(lats, road_tkm_B, road_tkm_B + rail_tkm_B,
                          color='#3498DB', alpha=0.6, label='Rail', edgecolor='darkblue', linewidth=1.5)

    # Total outline
    total_tkm_B = road_tkm_B + rail_tkm_B
    ax_tkm.plot(total_tkm_B, lats, 'k-', linewidth=2, alpha=0.5)

    ax_tkm.set_xlabel('Transport Work (Billion TKM)', fontsize=12, fontweight='bold')
    ax_tkm.set_title(f'Year {year}', fontsize=13, fontweight='bold', pad=10)
    ax_tkm.grid(True, alpha=0.3, linestyle='--')
    ax_tkm.set_xlim(left=0)

    if year_idx == 0:
        ax_tkm.legend(loc='lower left', fontsize=11, framealpha=0.95)

# Add column titles
axes[0, 0].text(0.5, 1.15, 'FREIGHT VOLUME (Tonnes)',
                transform=axes[0, 0].transAxes,
                fontsize=15, fontweight='bold', ha='center')
axes[0, 1].text(0.5, 1.15, 'TRANSPORT WORK (TKM)',
                transform=axes[0, 1].transAxes,
                fontsize=15, fontweight='bold', ha='center')

# Overall title
fig.suptitle('Freight Volume vs Transport Work by Latitude\nScandinavian-Mediterranean Corridor',
             fontsize=17, fontweight='bold', y=0.995)

# ==============================================================================
# ADD COUNTRY LABELS AND BORDERS TO ALL PANELS
# ==============================================================================

# Load country data
country_centroids = pd.read_csv('country_centroids.csv')
borders_df = pd.read_csv('country_southern_borders.csv')

corridor_countries = ['IT', 'AT', 'DE', 'DK', 'NO', 'SE']
country_data = country_centroids[country_centroids['CNTR_CODE'].isin(corridor_countries)]

# Flatten axes for iteration
ax_list = axes.flatten()

for ax_idx, ax in enumerate(ax_list):
    ylim = ax.get_ylim()

    # Add country labels (only on left column to avoid clutter)
    if ax_idx % 2 == 0:  # Left column
        for _, row in country_data.iterrows():
            country_code = row['CNTR_CODE']
            lat = row['centroid_lat']

            if ylim[0] <= lat <= ylim[1]:
                ax.text(1.02, lat, country_code, transform=ax.get_yaxis_transform(),
                       fontsize=10, fontweight='bold', va='center', ha='left',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))

    # Add border lines to all panels
    for _, row in borders_df.iterrows():
        country = row['CNTR_CODE']
        border_lat = row['southern_border_lat']

        if country in corridor_countries and ylim[0] <= border_lat <= ylim[1]:
            ax.axhline(y=border_lat, color='gray', linestyle='--',
                      linewidth=0.8, alpha=0.5, zorder=1)

plt.tight_layout()
plt.savefig('tonnes_vs_tkm_by_latitude.png', dpi=300, bbox_inches='tight')
print("\n✓ Plot saved as 'tonnes_vs_tkm_by_latitude.png'")
plt.show()

# ==============================================================================
# INTERPRETATION GUIDE
# ==============================================================================

print("\n" + "="*80)
print("INTERPRETATION GUIDE: TONNES vs TKM")
print("="*80)
print("""
LEFT PANELS (TONNES):
- Shows freight VOLUME passing through each region
- Independent of distance traveled
- Indicates freight DENSITY and logistics activity
- Peaks show where freight is LOCATED

RIGHT PANELS (TKM):
- Shows transport WORK (volume × distance)
- Captures economic and environmental impact
- Indicates infrastructure stress and energy consumption
- Peaks can be inflated by long routes through regions

COMPARISON:
- If a region has high TONNES but low TKM: Short transit distance
- If a region has low TONNES but high TKM: Long transit distance (corridor)
- If both are high: Major freight hub with long-distance connections
""")
