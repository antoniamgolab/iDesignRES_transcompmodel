# ==============================================================================
# SPATIAL FREIGHT DISTRIBUTION: LONGITUDE × LATITUDE HEATMAP
# ==============================================================================
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import matplotlib.patches as mpatches
import geopandas as gpd
from matplotlib.widgets import RectangleSelector, Button
import matplotlib
matplotlib.use('TkAgg')  # Use interactive backend

def calculate_spatial_freight_distribution(case_study_name, target_years=[2030, 2040, 2050]):
    """
    Calculate freight tonnes by geographic coordinates (longitude, latitude).

    Returns:
        dict: {year: {nuts2_id: {'lon': X, 'lat': Y, 'road_tonnes': Z, 'rail_tonnes': W, ...}}}
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

    print(f"Found {len(nuts2_lookup)} NUTS2 regions")

    # Load paths
    paths = input_data['Path']
    path_lookup = {}
    for path in paths:
        path_lookup[path['id']] = {
            'sequence': path['sequence']
        }

    # Calculate tonnes by NUTS2 region
    data_by_year_nuts2 = {year: {} for year in target_years}

    SCALING_FACTOR = 1000  # f is in kilotonnes

    for key_str, flow_value_kt in f_data.items():
        key = eval(key_str) if isinstance(key_str, str) else key_str
        year, (product_id, odpair_id, path_id), (mode_id, techvehicle_id), generation = key

        if year not in target_years or flow_value_kt <= 0:
            continue

        if path_id not in path_lookup:
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
                        'lon': nuts2_lookup[node_id]['lon'],
                        'country': nuts2_lookup[node_id]['country']
                    }

                data_by_year_nuts2[year][nuts2_id][f'{mode_name}_tonnes'] += flow_value_tonnes

    # Calculate totals
    for year in target_years:
        for nuts2_id, data in data_by_year_nuts2[year].items():
            data['total_tonnes'] = data['road_tonnes'] + data['rail_tonnes']

    return data_by_year_nuts2

# Calculate data
print("="*80)
print("CALCULATING SPATIAL FREIGHT DISTRIBUTION")
print("="*80)
spatial_data = calculate_spatial_freight_distribution(case_name, target_years=[2030, 2040, 2050])

# Display summary
print("\n" + "="*80)
print("SUMMARY: SPATIAL FREIGHT DISTRIBUTION")
print("="*80)

for year in [2030, 2040, 2050]:
    data = spatial_data[year]
    total_tonnes = sum(d['total_tonnes'] for d in data.values())
    print(f"\nYear {year}: {total_tonnes/1e9:.2f} Mt across {len(data)} NUTS2 regions")

# ==============================================================================
# LOAD COUNTRY BOUNDARIES
# ==============================================================================

# Load NUTS0 (country level) shapefile for borders
try:
    nuts0_shapefile = 'data/NUTS_RG_20M_2021_4326.shp'
    countries_gdf = gpd.read_file(nuts0_shapefile)

    # Filter to NUTS0 level (country borders) and corridor countries
    corridor_countries = ['IT', 'AT', 'DE', 'DK', 'NO', 'SE']
    countries_gdf = countries_gdf[countries_gdf['LEVL_CODE'] == 0]  # NUTS0 = country level
    countries_gdf = countries_gdf[countries_gdf['CNTR_CODE'].isin(corridor_countries)]

    print(f"Loaded country borders for: {', '.join(countries_gdf['CNTR_CODE'].unique())}")
    has_country_borders = True
except Exception as e:
    print(f"⚠️  Could not load country borders: {e}")
    print("Continuing without country borders...")
    has_country_borders = False

# ==============================================================================
# BEAUTIFUL SPATIAL HEATMAP PLOT
# ==============================================================================

years_to_plot = [2030, 2040, 2050]

# Set style
plt.style.use('seaborn-v0_8-white')

# Create figure: 3 rows × 2 columns (left=total, right=mode split)
fig = plt.figure(figsize=(18, 18))
gs = fig.add_gridspec(3, 2, hspace=0.25, wspace=0.20,
                      top=0.95, bottom=0.06, left=0.08, right=0.92)

for year_idx, year in enumerate(years_to_plot):
    data = spatial_data[year]

    if not data:
        continue

    # Prepare plotting data
    plotting_data = []
    for nuts2_id, metrics in data.items():
        plotting_data.append({
            'nuts2': nuts2_id,
            'lat': metrics['lat'],
            'lon': metrics['lon'],
            'country': metrics['country'],
            'road_tonnes': metrics['road_tonnes'],
            'rail_tonnes': metrics['rail_tonnes'],
            'total_tonnes': metrics['total_tonnes']
        })

    # Extract arrays
    lons = np.array([d['lon'] for d in plotting_data])
    lats = np.array([d['lat'] for d in plotting_data])
    road_tonnes = np.array([d['road_tonnes'] for d in plotting_data])
    rail_tonnes = np.array([d['rail_tonnes'] for d in plotting_data])
    total_tonnes = np.array([d['total_tonnes'] for d in plotting_data])

    # ==============================================================================
    # LEFT COLUMN: TOTAL FREIGHT (COLOR INTENSITY)
    # ==============================================================================

    ax_total = fig.add_subplot(gs[year_idx, 0])

    # Plot country borders in background
    if has_country_borders:
        countries_gdf.boundary.plot(ax=ax_total, color='gray', linewidth=1.5, alpha=0.5, zorder=1)
        countries_gdf.plot(ax=ax_total, color='white', alpha=0.1, zorder=0)

    # Convert to million tonnes
    total_mt = total_tonnes / 1e6

    # Scatter plot with color representing freight volume
    scatter = ax_total.scatter(lons, lats,
                              c=total_mt,
                              s=200,  # Marker size
                              cmap='YlOrRd',  # Yellow-Orange-Red colormap
                              alpha=0.8,
                              edgecolor='black',
                              linewidth=0.8,
                              vmin=0,
                              vmax=np.percentile(total_mt, 95),  # Cap at 95th percentile for better contrast
                              zorder=5)  # Plot on top of borders

    # Colorbar
    cbar = plt.colorbar(scatter, ax=ax_total, pad=0.02)
    cbar.set_label('Freight Volume (Mt)', fontsize=11, fontweight='bold', rotation=270, labelpad=20)
    cbar.ax.tick_params(labelsize=9)

    # Styling
    ax_total.set_xlabel('Longitude (°E)', fontsize=12, fontweight='bold', labelpad=8)
    ax_total.set_ylabel('Latitude (°N)', fontsize=12, fontweight='bold', labelpad=8)
    ax_total.set_title(f'{year} - Total Freight', fontsize=14, fontweight='bold', pad=12,
                      bbox=dict(boxstyle='round,pad=0.5', facecolor='lightyellow', alpha=0.5))

    ax_total.grid(True, alpha=0.3, linestyle='--', linewidth=0.8)
    ax_total.set_aspect('equal', adjustable='box')
    ax_total.tick_params(axis='both', which='major', labelsize=10)

    # ==============================================================================
    # RIGHT COLUMN: MODE SPLIT (PIE CHARTS)
    # ==============================================================================

    ax_mode = fig.add_subplot(gs[year_idx, 1])

    # Plot country borders in background
    if has_country_borders:
        countries_gdf.boundary.plot(ax=ax_mode, color='gray', linewidth=1.5, alpha=0.5, zorder=1)
        countries_gdf.plot(ax=ax_mode, color='white', alpha=0.1, zorder=0)

    # Calculate modal split for sizing
    modal_split = road_tonnes / (total_tonnes + 1e-9)  # Road percentage (avoid div by zero)

    # Create scatter plot where:
    # - Color represents modal split (blue=rail, red=road)
    # - Size represents total volume

    # Normalize sizes (larger circles = more freight)
    sizes = 100 + (total_tonnes / np.max(total_tonnes)) * 400  # Range: 100-500

    # Create custom colormap: Blue (100% rail) to Red (100% road)
    scatter_mode = ax_mode.scatter(lons, lats,
                                   c=modal_split * 100,  # % Road
                                   s=sizes,
                                   cmap='RdBu_r',  # Red (road) to Blue (rail), reversed
                                   alpha=0.8,
                                   edgecolor='black',
                                   linewidth=0.8,
                                   vmin=0,
                                   vmax=100,
                                   zorder=5)  # Plot on top of borders

    # Colorbar
    cbar_mode = plt.colorbar(scatter_mode, ax=ax_mode, pad=0.02)
    cbar_mode.set_label('Road Share (%)', fontsize=11, fontweight='bold', rotation=270, labelpad=20)
    cbar_mode.ax.tick_params(labelsize=9)

    # Styling
    ax_mode.set_xlabel('Longitude (°E)', fontsize=12, fontweight='bold', labelpad=8)
    ax_mode.set_title(f'{year} - Modal Split\n(size = volume)', fontsize=14, fontweight='bold', pad=12,
                     bbox=dict(boxstyle='round,pad=0.5', facecolor='lightblue', alpha=0.5))

    ax_mode.grid(True, alpha=0.3, linestyle='--', linewidth=0.8)
    ax_mode.set_aspect('equal', adjustable='box')
    ax_mode.tick_params(axis='both', which='major', labelsize=10)
    ax_mode.tick_params(axis='y', labelleft=False)

    # Add legend for size
    for size_val, label in [(100, 'Low'), (300, 'Medium'), (500, 'High')]:
        ax_mode.scatter([], [], s=size_val, c='gray', alpha=0.6,
                       edgecolor='black', linewidth=0.8, label=label)

    legend = ax_mode.legend(loc='lower right', fontsize=9, framealpha=0.95,
                           title='Volume', title_fontsize=10,
                           edgecolor='black', fancybox=True)

# Overall title
fig.suptitle('Spatial Freight Distribution: Geographic Heatmap\n' +
            'Scandinavian-Mediterranean Corridor',
            fontsize=18, fontweight='bold', y=0.98,
            bbox=dict(boxstyle='round,pad=0.8', facecolor='lightgreen', alpha=0.2))

# ==============================================================================
# ENABLE INTERACTIVE ZOOM
# ==============================================================================

print("\n" + "="*80)
print("INTERACTIVE ZOOM CONTROLS")
print("="*80)
print("""
🖱️  ZOOM & PAN CONTROLS:

  BUILT-IN MATPLOTLIB TOOLBAR:
  • Zoom button (magnifier icon): Click, then drag rectangle to zoom into area
  • Pan button (cross arrows): Click, then drag to pan around
  • Home button: Reset to original view
  • Back/Forward buttons: Navigate zoom history
  • Save button: Save current view as image

  KEYBOARD SHORTCUTS:
  • Mouse wheel: Zoom in/out at cursor position
  • Right-click drag: Pan the view
  • 'h' or Home: Reset to original view
  • 'c': Toggle zoom rectangle mode

  TIPS:
  • Use zoom to focus on specific countries (e.g., just Italy or Germany)
  • Pan to explore border regions in detail
  • Multiple zoom levels help identify local hotspots
  • Save zoomed views for presentations

📊 The figure window is interactive - try it out!
""")

# Enable interactive mode
plt.ion()

# Save with high quality
plt.savefig('spatial_freight_heatmap.png', dpi=400,
            bbox_inches='tight', facecolor='white', edgecolor='none')
print("\n✓ High-quality plot saved as 'spatial_freight_heatmap.png' (400 DPI)")
print("✓ Interactive window opened - use toolbar to zoom and pan")
print("  (Close the window to continue)")

plt.show()

# ==============================================================================
# TOP REGIONS BY GEOGRAPHIC LOCATION
# ==============================================================================

print("\n" + "="*80)
print("TOP 10 REGIONS BY FREIGHT VOLUME (2030)")
print("="*80)

year_2030_data = []
for nuts2_id, metrics in spatial_data[2030].items():
    year_2030_data.append({
        'nuts2': nuts2_id,
        'country': metrics['country'],
        'lat': metrics['lat'],
        'lon': metrics['lon'],
        'total_tonnes': metrics['total_tonnes'],
        'road_tonnes': metrics['road_tonnes'],
        'rail_tonnes': metrics['rail_tonnes']
    })

# Sort by total freight
year_2030_data.sort(key=lambda x: x['total_tonnes'], reverse=True)

print(f"{'Rank':<6} {'NUTS2':<8} {'Country':<8} {'Latitude':>10} {'Longitude':>11} {'Total (Mt)':>12} {'Road %':>8} {'Rail %':>8}")
print("-" * 90)

for i, d in enumerate(year_2030_data[:10], 1):
    road_pct = 100 * d['road_tonnes'] / d['total_tonnes'] if d['total_tonnes'] > 0 else 0
    rail_pct = 100 * d['rail_tonnes'] / d['total_tonnes'] if d['total_tonnes'] > 0 else 0
    print(f"{i:<6} {d['nuts2']:<8} {d['country']:<8} {d['lat']:>10.2f} {d['lon']:>11.2f} "
          f"{d['total_tonnes']/1e6:>12.2f} {road_pct:>7.1f}% {rail_pct:>7.1f}%")

# ==============================================================================
# INTERPRETATION GUIDE
# ==============================================================================

print("\n" + "="*80)
print("INTERPRETATION GUIDE: SPATIAL FREIGHT HEATMAP")
print("="*80)
print("""
🗺️ WHAT THIS SHOWS:

   LEFT PANELS:  Total freight volume by geographic location
   - X-axis: Longitude (East-West position)
   - Y-axis: Latitude (North-South position)
   - Color intensity: Freight volume (Yellow → Orange → Red for increasing volume)
   - Each dot = one NUTS2 region

   RIGHT PANELS: Modal split and volume
   - X-axis: Longitude (East-West position)
   - Y-axis: Latitude (North-South position)
   - Color: Modal split (Red = 100% road, Blue = 100% rail)
   - Size: Total freight volume (larger = more freight)

🎯 KEY INSIGHTS TO LOOK FOR:

   1. GEOGRAPHIC CLUSTERS:
      - Hotspots of intense red/orange = high freight concentration
      - Multiple nearby high-intensity dots = logistics corridor
      - Isolated high-intensity dots = major transshipment points

   2. NORTH-SOUTH PATTERNS:
      - Vertical alignment of hotspots = corridor effect
      - Gaps between hotspots = low-activity regions

   3. MODAL SPLIT GEOGRAPHY:
      - Red regions (right panel) = road-dominated
      - Blue regions = rail-dominated
      - Purple/white regions = balanced modal split
      - Geographic patterns reveal infrastructure availability

   4. VOLUME DISTRIBUTION:
      - Large circles = major freight hubs
      - Small circles = minor nodes
      - Compare size distribution across years for growth patterns

📊 ADVANTAGES OF SPATIAL VIEW:

   • Shows TRUE 2D geographic distribution (not compressed to latitude)
   • Reveals East-West patterns invisible in latitude-only plots
   • Identifies geographic clusters and isolated hubs
   • Modal split visualization shows infrastructure deployment patterns

🔍 WHAT TO COMPARE:

   • 2030 vs 2050: Growth patterns and spatial expansion
   • Left vs Right: Volume concentration vs infrastructure deployment
   • Color intensity: Identifies THE dominant freight regions
   • Circle sizes (right): Shows where freight is consolidating

⚠️ TECHNICAL NOTES:

   • Coordinates from GeographicElement (NUTS2 centroids)
   • Color scale capped at 95th percentile for better contrast
   • Equal aspect ratio preserves true geographic proportions
   • Full freight counted at each node (imports + exports + domestic + transit)
""")
