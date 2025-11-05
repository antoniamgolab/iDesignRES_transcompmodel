# ==============================================================================
# SPATIAL FREIGHT DISTRIBUTION: SIMPLIFIED VERSION WITH REGIONAL VIEWS
# ==============================================================================
import matplotlib.pyplot as plt
import geopandas as gpd
import numpy as np

def calculate_spatial_freight_distribution(case_study_name, target_years=[2030, 2040, 2050]):
    """
    Calculate freight tonnes by geographic coordinates (longitude, latitude).
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

    # Load paths
    paths = input_data['Path']
    path_lookup = {}
    for path in paths:
        path_lookup[path['id']] = {'sequence': path['sequence']}

    # Calculate tonnes by NUTS2 region
    data_by_year_nuts2 = {year: {} for year in target_years}
    SCALING_FACTOR = 1000

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

# Load country borders
try:
    nuts0_shapefile = 'data/NUTS_RG_20M_2021_4326.shp'
    countries_gdf = gpd.read_file(nuts0_shapefile)
    corridor_countries = ['IT', 'AT', 'DE', 'DK', 'NO', 'SE']
    countries_gdf = countries_gdf[countries_gdf['LEVL_CODE'] == 0]
    countries_gdf = countries_gdf[countries_gdf['CNTR_CODE'].isin(corridor_countries)]
    has_borders = True
except:
    has_borders = False
    print("⚠️  Could not load country borders")

# ==============================================================================
# PLOT: SINGLE YEAR, SIMPLIFIED LAYOUT
# ==============================================================================

# Choose year to plot (can change to 2040 or 2050)
year_to_plot = 2030

data = spatial_data[year_to_plot]

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

lons = np.array([d['lon'] for d in plotting_data])
lats = np.array([d['lat'] for d in plotting_data])
total_tonnes = np.array([d['total_tonnes'] for d in plotting_data])
road_tonnes = np.array([d['road_tonnes'] for d in plotting_data])

# Convert to million tonnes
total_mt = total_tonnes / 1e6

# ==============================================================================
# MAIN PLOT: FULL CORRIDOR
# ==============================================================================

fig, ax = plt.subplots(1, 1, figsize=(10, 14))

# Plot country borders
if has_borders:
    countries_gdf.boundary.plot(ax=ax, color='gray', linewidth=2, alpha=0.6, zorder=1)
    countries_gdf.plot(ax=ax, color='lightgray', alpha=0.2, zorder=0)

# Scatter plot
scatter = ax.scatter(lons, lats,
                    c=total_mt,
                    s=150,
                    cmap='YlOrRd',
                    alpha=0.8,
                    edgecolor='black',
                    linewidth=0.8,
                    vmin=0,
                    vmax=np.percentile(total_mt, 95),
                    zorder=5)

# Colorbar
cbar = plt.colorbar(scatter, ax=ax, fraction=0.046, pad=0.04)
cbar.set_label('Freight Volume (Mt)', fontsize=12, fontweight='bold', rotation=270, labelpad=20)

# Styling
ax.set_xlabel('Longitude (°E)', fontsize=12, fontweight='bold')
ax.set_ylabel('Latitude (°N)', fontsize=12, fontweight='bold')
ax.set_title(f'Freight Distribution - {year_to_plot}\nScandinavian-Mediterranean Corridor',
            fontsize=14, fontweight='bold', pad=15)
ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.8)
ax.set_aspect('equal', adjustable='box')

plt.tight_layout()
plt.savefig(f'spatial_freight_{year_to_plot}_full.png', dpi=300, bbox_inches='tight')
print(f"✓ Saved: spatial_freight_{year_to_plot}_full.png")
plt.show()

# ==============================================================================
# REGIONAL ZOOM PLOTS
# ==============================================================================

# Define regions to zoom into
zoom_regions = {
    'Italy': {'lon_range': (6, 19), 'lat_range': (36, 48), 'title': 'Italy & Alps'},
    'Central Europe': {'lon_range': (6, 16), 'lat_range': (45, 54), 'title': 'Central Europe (DE, AT)'},
    'Northern Europe': {'lon_range': (5, 18), 'lat_range': (54, 70), 'title': 'Scandinavia (DK, SE, NO)'},
}

for region_name, bounds in zoom_regions.items():
    # Filter data to region
    mask = ((lons >= bounds['lon_range'][0]) & (lons <= bounds['lon_range'][1]) &
            (lats >= bounds['lat_range'][0]) & (lats <= bounds['lat_range'][1]))

    if not np.any(mask):
        continue

    lons_region = lons[mask]
    lats_region = lats[mask]
    total_mt_region = total_mt[mask]

    # Create zoomed plot
    fig, ax = plt.subplots(1, 1, figsize=(10, 10))

    # Plot country borders
    if has_borders:
        countries_gdf.boundary.plot(ax=ax, color='gray', linewidth=2, alpha=0.6, zorder=1)
        countries_gdf.plot(ax=ax, color='lightgray', alpha=0.2, zorder=0)

    # Scatter plot
    scatter = ax.scatter(lons_region, lats_region,
                        c=total_mt_region,
                        s=200,
                        cmap='YlOrRd',
                        alpha=0.8,
                        edgecolor='black',
                        linewidth=1,
                        vmin=0,
                        vmax=np.percentile(total_mt, 95),
                        zorder=5)

    # Colorbar
    cbar = plt.colorbar(scatter, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label('Freight Volume (Mt)', fontsize=11, fontweight='bold', rotation=270, labelpad=20)

    # Set zoom bounds
    ax.set_xlim(bounds['lon_range'])
    ax.set_ylim(bounds['lat_range'])

    # Styling
    ax.set_xlabel('Longitude (°E)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Latitude (°N)', fontsize=12, fontweight='bold')
    ax.set_title(f'{bounds["title"]} - {year_to_plot}',
                fontsize=14, fontweight='bold', pad=15)
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.8)
    ax.set_aspect('equal', adjustable='box')

    plt.tight_layout()

    # Save
    filename = f'spatial_freight_{year_to_plot}_{region_name.replace(" ", "_").lower()}.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {filename}")
    plt.show()

# ==============================================================================
# SUMMARY
# ==============================================================================

print("\n" + "="*80)
print("SPATIAL PLOTS CREATED")
print("="*80)
print(f"""
Created {1 + len(zoom_regions)} maps for year {year_to_plot}:

1. Full corridor view: spatial_freight_{year_to_plot}_full.png
2. Italy & Alps zoom: spatial_freight_{year_to_plot}_italy.png
3. Central Europe zoom: spatial_freight_{year_to_plot}_central_europe.png
4. Scandinavia zoom: spatial_freight_{year_to_plot}_northern_europe.png

💡 TO CHANGE YEAR:
   Modify the 'year_to_plot' variable at the top of this cell
   Options: 2030, 2040, 2050

📊 ADVANTAGES:
   • Faster rendering (no interactive overhead)
   • Multiple zoom levels automatically generated
   • High-quality static images for papers
   • Each region saved separately for presentations
""")
