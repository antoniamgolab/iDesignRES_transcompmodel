"""
Regenerate Figure 3: Truck-break counts per NUTS-2 region along the
Scandinavian-Mediterranean corridor (2040).

Each mandatory break is weighted by the number of annual truck-trips on its
path, derived from freight volumes (kt/year) and an average payload of
13.6 tonnes per truck.

Layout: TWO HORIZONTAL subplots side by side.
  - LEFT:  Scandinavia (Norway, Sweden, Finland, Denmark) — lat 54-71, lon 4-30
  - RIGHT: Central/Southern Europe (Germany, Austria, Italy) — lat 37-55, lon 4-18
Shared colorbar at the bottom.  One legend in the lower-left of the left subplot.
"""

import yaml
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib import cm
from matplotlib.lines import Line2D
from matplotlib.gridspec import GridSpec
from pathlib import Path
from collections import defaultdict

# -- Font settings (matching results figures) ---------------------------------
plt.rcParams.update(plt.rcParamsDefault)
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "serif",
    'font.serif': 'mathpazo',
    'font.size': 18,
})

# -- Paths --------------------------------------------------------------------
BASE_PATH = Path(__file__).resolve().parent
INPUT_DIR = BASE_PATH / 'input_data'
FIG_DIR = BASE_PATH / 'figures'
MANUSCRIPT_IMG = BASE_PATH.parent.parent / 'manuscript' / 'images'

CORRIDOR_COUNTRIES = ['AT', 'DE', 'IT', 'DK', 'SE', 'NO', 'FI']
SOUTHERN_BORDER_REGIONS = {
    'AT33', 'AT34',
    'ITC4', 'ITH1', 'ITH2', 'ITH3',
    'DE14', 'DE21', 'DE27',
}

WEIGHT_YEAR = 2040

# TEN-T road network shapefile (Scandinavian-Mediterranean corridor)
TENT_SHP = Path('D:/AntoniaMariaG/ten-t/roads_GL2017_CNC_E.shp')

# -- Subplot extents ----------------------------------------------------------
# LEFT: Scandinavia
SCAND_LON = (4, 30)
SCAND_LAT = (54, 71)

# RIGHT: Central / Southern Europe
SOUTH_LON = (4, 18)
SOUTH_LAT = (37, 55)


# -- Helpers ------------------------------------------------------------------
def load_yaml(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def load_yaml_unsafe(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return yaml.load(f, Loader=yaml.UnsafeLoader)


# -- Load geographic elements -------------------------------------------------
print('Loading geographic data...')
geo_yaml = load_yaml(INPUT_DIR / 'fixed_nuts_2' / 'GeographicElement.yaml')
geo_to_nuts2 = {}
for g in geo_yaml:
    if g.get('type') == 'node':
        nuts2 = g.get('nuts2_region', '')
        if nuts2:
            geo_to_nuts2[g['id']] = nuts2
print(f'  Nodes with NUTS-2: {len(geo_to_nuts2)}')

# -- Load f_dict (Go RES, scenario_000) ---------------------------------------
print('Loading f_dict...')
import re

results_dir = BASE_PATH / 'results' / 'uncertainty_scenarios' / 'scenario_000'
f_files = list(results_dir.glob('*_f_dict.yaml'))
f_file = max(f_files, key=lambda x: x.stat().st_mtime)
print(f'  Using: {f_file.name}')

raw_f = load_yaml(f_file)

def parse_tuple_key(key_str):
    nums = re.findall(r'-?\d+', str(key_str))
    return tuple(int(x) for x in nums)

tonnes_per_path = defaultdict(float)
for k, v in raw_f.items():
    nums = parse_tuple_key(k)
    if len(nums) >= 7:
        year = nums[0]
        if year != WEIGHT_YEAR:
            continue
        path_id = nums[3]
        tonnes_per_path[path_id] += float(v)

print(f'  Paths with freight in {WEIGHT_YEAR}: {len(tonnes_per_path)}')
print(f'  Total freight: {sum(tonnes_per_path.values()):.0f} kt')

# -- Load mandatory breaks ----------------------------------------------------
print('Loading mandatory breaks...')
breaks_yaml = load_yaml(INPUT_DIR / 'uncertainty_scenarios' / 'scenario_000' / 'MandatoryBreaks.yaml')
print(f'  Loaded {len(breaks_yaml)} mandatory breaks')

# Weight breaks by number of truck-trips on their path
# Conversion: truck_trips = freight_kt * 1000 / payload_tonnes
PAYLOAD_TONNES = 13.6  # average payload per truck (tonnes)

weighted_breaks_per_nuts2 = defaultdict(float)
for brk in breaks_yaml:
    geo_id = brk['latest_geo_id']
    nuts2 = geo_to_nuts2.get(geo_id, '')
    pid = brk['path_id']
    if nuts2:
        truck_trips = tonnes_per_path.get(pid, 0.0) * 1000 / PAYLOAD_TONNES
        weighted_breaks_per_nuts2[nuts2] += truck_trips

# Convert to thousands for readable colorbar
weighted_break_df = pd.DataFrame([
    {'nuts2': n, 'weighted_breaks': v / 1000}
    for n, v in weighted_breaks_per_nuts2.items()
])
print(f'  Regions with breaks: {len(weighted_break_df)}')

# -- Load shapefile and highway data ------------------------------------------
print('Loading shapefile...')
nuts_shp = BASE_PATH / 'data' / 'NUTS_RG_20M_2021_4326.shp' / 'NUTS_RG_20M_2021_4326.shp'
nuts_gdf = gpd.read_file(nuts_shp)
nuts2_gdf = nuts_gdf[nuts_gdf['LEVL_CODE'] == 2].copy()
nuts0_gdf = nuts_gdf[nuts_gdf['LEVL_CODE'] == 0].copy()

corridor_nuts2 = nuts2_gdf[nuts2_gdf['CNTR_CODE'].isin(CORRIDOR_COUNTRIES)].copy()
corridor_countries_gdf = nuts0_gdf[nuts0_gdf['CNTR_CODE'].isin(CORRIDOR_COUNTRIES)]

highway_df = pd.read_csv(BASE_PATH / 'highway_km_per_nuts2.csv')
corridor_with_hw = corridor_nuts2.merge(
    highway_df.rename(columns={'NUTS2_CODE': 'NUTS_ID'}),
    on='NUTS_ID', how='left'
)

# -- Load TEN-T road network --------------------------------------------------
print('Loading TEN-T road network...')
tent_gdf = gpd.read_file(TENT_SHP)
tent_gdf = tent_gdf.to_crs('EPSG:4326')  # reproject from EPSG:3857 to match map
print(f'  TEN-T road segments: {len(tent_gdf)}')

# -- Merge break data with geodataframe --------------------------------------
plot_gdf = corridor_with_hw.merge(
    weighted_break_df[['nuts2', 'weighted_breaks']],
    left_on='NUTS_ID', right_on='nuts2', how='left'
)
plot_gdf['weighted_breaks'] = plot_gdf['weighted_breaks'].fillna(0)

# Shared colour scale
vmax = plot_gdf['weighted_breaks'].max()
norm = Normalize(vmin=0, vmax=vmax)

# Border regions subset
border_gdf = plot_gdf[plot_gdf['NUTS_ID'].isin(SOUTHERN_BORDER_REGIONS)]

# Country name labels and centroids
country_names = {
    'AT': 'Austria', 'DE': 'Germany', 'IT': 'Italy',
    'DK': 'Denmark', 'SE': 'Sweden', 'NO': 'Norway', 'FI': 'Finland',
}


# -- Helper: draw one map panel -----------------------------------------------
def draw_panel(ax, lon_range, lat_range, show_legend=False):
    """Draw a single choropleth panel on the given axes."""
    # Background: corridor countries
    corridor_countries_gdf.plot(ax=ax, color='#f5f5f5', edgecolor='#999', linewidth=0.8)

    # Choropleth
    plot_gdf.plot(
        ax=ax, column='weighted_breaks', cmap='YlGnBu',
        edgecolor='black', linewidth=0.4,
        vmin=0, vmax=vmax, legend=False,
    )

    # TEN-T road network overlay
    tent_gdf.plot(ax=ax, color='#CC5500', linewidth=3.0, alpha=0.9, zorder=3)

    # Border regions
    border_gdf.plot(ax=ax, facecolor='none', edgecolor='#CC0066',
                    linewidth=3, linestyle='--')

    # Country name labels
    for _, row in corridor_countries_gdf.iterrows():
        cc = row['CNTR_CODE']
        if cc in country_names:
            centroid = row.geometry.centroid
            # Only label if centroid falls within this panel's extent
            if (lon_range[0] <= centroid.x <= lon_range[1] and
                    lat_range[0] <= centroid.y <= lat_range[1]):
                ax.text(centroid.x, centroid.y, country_names[cc],
                        ha='center', va='center', fontsize=14, fontweight='bold',
                        color='#333', fontstyle='italic',
                        bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                                  alpha=0.6, edgecolor='none'))

    # Crop to panel extent
    ax.set_xlim(*lon_range)
    ax.set_ylim(*lat_range)
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.tick_params(labelsize=14)

    # Scale bar (200 km) — compute at the mid-latitude of this panel
    mid_lat = (lat_range[0] + lat_range[1]) / 2
    km_per_deg = 111.32 * np.cos(np.radians(mid_lat))
    bar_km = 200
    bar_deg = bar_km / km_per_deg

    x0 = lon_range[0] + 1.0
    y0 = lat_range[0] + 0.8
    ax.plot([x0, x0 + bar_deg], [y0, y0], color='black', linewidth=2.5,
            transform=ax.transData, clip_on=False)
    ax.text(x0 + bar_deg / 2, y0 + 0.4, f'{bar_km} km',
            ha='center', va='bottom', fontsize=12,
            bbox=dict(facecolor='white', edgecolor='none', alpha=0.8))

    # Legend handles are created but placed outside the panel (see fig.legend below)


# -- Create figure with two horizontal subplots and a shared colorbar ---------
print('Generating figure...')

fig = plt.figure(figsize=(16, 10))
gs = GridSpec(2, 2, height_ratios=[1, 0.03], hspace=0.08, wspace=0.15)

ax_left = fig.add_subplot(gs[0, 0])
ax_right = fig.add_subplot(gs[0, 1])
cax = fig.add_subplot(gs[1, :])

# Draw panels
draw_panel(ax_left,  SCAND_LON, SCAND_LAT, show_legend=True)
draw_panel(ax_right, SOUTH_LON, SOUTH_LAT, show_legend=False)

# Legend placed outside the panels, between map and colorbar
tent_handle = Line2D([0], [0], color='#CC5500', linewidth=3.0, alpha=0.9,
                     label='Scand-Med TEN-T road network')
border_handle = Line2D([0], [0], color='#CC0066', linewidth=3, linestyle='--',
                       label='DE--AT--IT border region')
fig.legend(handles=[tent_handle, border_handle], loc='lower center',
           bbox_to_anchor=(0.5, 0.08), ncol=2, fontsize=13, framealpha=0.9)

# Shared colorbar at the bottom
sm = cm.ScalarMappable(cmap='YlGnBu', norm=norm)
sm.set_array([])
cbar = fig.colorbar(sm, cax=cax, orientation='horizontal')
cbar.set_label(f'Truck-breaks (thousands, {WEIGHT_YEAR})', fontsize=16, labelpad=6)
cbar.ax.tick_params(labelsize=13)

plt.tight_layout()
# Adjust bottom to make room for the legend between panels and colorbar
fig.subplots_adjust(bottom=0.12)

# -- Save ---------------------------------------------------------------------
for dst in [FIG_DIR, MANUSCRIPT_IMG]:
    fig.savefig(dst / 'mandatory_breaks_map_left_only.pdf', bbox_inches='tight')
fig.savefig(FIG_DIR / 'mandatory_breaks_map_left_only.png', bbox_inches='tight', dpi=150)
plt.close()
print(f'Saved: figures/mandatory_breaks_map_left_only.pdf')
print(f'Saved: manuscript/images/mandatory_breaks_map_left_only.pdf')
print('Done.')
