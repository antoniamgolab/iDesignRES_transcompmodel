"""
Regenerate Figure 3: Truck-break counts per NUTS-2 region along the
Scandinavian-Mediterranean corridor (2040).

Single continuous map covering NO-FI-SE-DK-DE-AT-IT with discrete color bins
for mandatory break counts. Border region highlighted.
"""

import yaml
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm
from matplotlib import cm
from matplotlib.lines import Line2D
import matplotlib.patches as mpatches
from pathlib import Path
from collections import defaultdict
import re

plt.rcParams.update(plt.rcParamsDefault)
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Segoe UI", "sans-serif"],
    "font.size": 18,
})

BASE_PATH = Path(__file__).resolve().parent
INPUT_DIR = BASE_PATH / 'input_data'
FIG_DIR = BASE_PATH / 'figures'
MANUSCRIPT_IMG = BASE_PATH.parent.parent / 'Moving-electricity-loads-in-long-term-decarbonizations' / 'images'

CORRIDOR_COUNTRIES = ['AT', 'DE', 'IT', 'DK', 'SE', 'NO', 'FI']
SOUTHERN_BORDER_REGIONS = {
    'AT33', 'AT34',
    'ITC4', 'ITH1', 'ITH2', 'ITH3',
    'DE14', 'DE21', 'DE27',
}

WEIGHT_YEAR = 2040
TENT_SHP = Path('D:/AntoniaMariaG/ten-t/roads_GL2017_CNC_E.shp')

# -- Helpers ------------------------------------------------------------------
def load_yaml(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

# -- Load geographic elements -------------------------------------------------
print('Loading geographic data...')
geo_yaml = load_yaml(INPUT_DIR / 'fixed_nuts_2' / 'GeographicElement.yaml')
geo_to_nuts2 = {}
for g in geo_yaml:
    if g.get('type') == 'node':
        nuts2 = g.get('nuts2_region', '')
        if nuts2:
            geo_to_nuts2[g['id']] = nuts2

# -- Load f_dict (Go RES, scenario_000) ---------------------------------------
print('Loading f_dict...')
results_dir = BASE_PATH / 'results' / 'uncertainty_scenarios_v2' / 'scenario_000'
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

# -- Load mandatory breaks ----------------------------------------------------
print('Loading mandatory breaks...')
breaks_yaml = load_yaml(INPUT_DIR / 'uncertainty_scenarios_v2' / 'scenario_000' / 'MandatoryBreaks.yaml')
print(f'  Loaded {len(breaks_yaml)} mandatory breaks')

PAYLOAD_TONNES = 13.6

weighted_breaks_per_nuts2 = defaultdict(float)
for brk in breaks_yaml:
    geo_id = brk['latest_geo_id']
    nuts2 = geo_to_nuts2.get(geo_id, '')
    pid = brk['path_id']
    if nuts2:
        truck_trips = tonnes_per_path.get(pid, 0.0) * 1000 / PAYLOAD_TONNES
        weighted_breaks_per_nuts2[nuts2] += truck_trips

weighted_break_df = pd.DataFrame([
    {'nuts2': n, 'weighted_breaks': v / 1000}
    for n, v in weighted_breaks_per_nuts2.items()
])

# -- Load shapefile -----------------------------------------------------------
print('Loading shapefile...')
nuts_shp = BASE_PATH / 'data' / 'NUTS_RG_20M_2021_4326.shp' / 'NUTS_RG_20M_2021_4326.shp'
nuts_gdf = gpd.read_file(nuts_shp)
nuts2_gdf = nuts_gdf[nuts_gdf['LEVL_CODE'] == 2].copy()
nuts0_gdf = nuts_gdf[nuts_gdf['LEVL_CODE'] == 0].copy()

corridor_nuts2 = nuts2_gdf[nuts2_gdf['CNTR_CODE'].isin(CORRIDOR_COUNTRIES)].copy()
corridor_countries_gdf = nuts0_gdf[nuts0_gdf['CNTR_CODE'].isin(CORRIDOR_COUNTRIES)]

# -- Load TEN-T ---------------------------------------------------------------
print('Loading TEN-T road network...')
tent_gdf = gpd.read_file(TENT_SHP)
tent_gdf = tent_gdf.to_crs('EPSG:4326')

# Remove Svalbard (NO0B) and other extreme outlier regions
corridor_nuts2 = corridor_nuts2[~corridor_nuts2['NUTS_ID'].isin(['NO0B'])]

# -- Reproject to ETRS89-LAEA (EPSG:3035) — Europe equal-area, compresses Scandinavia
TARGET_CRS = 'EPSG:3035'
corridor_nuts2 = corridor_nuts2.to_crs(TARGET_CRS)
corridor_countries_gdf = corridor_countries_gdf.to_crs(TARGET_CRS)
tent_gdf = tent_gdf.to_crs(TARGET_CRS)

# -- Merge break data ---------------------------------------------------------
plot_gdf = corridor_nuts2.merge(
    weighted_break_df[['nuts2', 'weighted_breaks']],
    left_on='NUTS_ID', right_on='nuts2', how='left'
)
plot_gdf['weighted_breaks'] = plot_gdf['weighted_breaks'].fillna(0)

# -- Discrete bins for break counts -------------------------------------------
bin_edges = [0, 1, 5, 10, 20, 50, 100, 200]
bin_labels = ['0-1', '1-5', '5-10', '10-20', '20-50', '50-100', '100+']
bin_colors = ['#f0f0f0', '#d4d4eb', '#a8a8d8', '#7b7bc4', '#5b4fa8', '#3a2d7c', '#67001f']

def get_bin_idx(val):
    for i in range(len(bin_edges) - 1):
        if val < bin_edges[i + 1]:
            return i
    return len(bin_edges) - 1  # last bin (100+)

plot_gdf['bin_idx'] = plot_gdf['weighted_breaks'].apply(get_bin_idx)
plot_gdf['bin_color'] = plot_gdf['bin_idx'].apply(lambda i: bin_colors[min(i, len(bin_colors)-1)])

border_gdf = plot_gdf[plot_gdf['NUTS_ID'].isin(SOUTHERN_BORDER_REGIONS)]

country_names = {
    'AT': 'Austria', 'DE': 'Germany', 'IT': 'Italy',
    'DK': 'Denmark', 'SE': 'Sweden', 'NO': 'Norway', 'FI': 'Finland',
}

# -- Create single continuous figure ------------------------------------------
print('Generating figure...')

fig = plt.figure(figsize=(16, 16))
gs = fig.add_gridspec(2, 2, width_ratios=[2.5, 1], height_ratios=[1, 2],
                      wspace=-0.32, hspace=0.02)
ax = fig.add_subplot(gs[:, 0])          # left: full height
ax_zoom = fig.add_subplot(gs[1, 1])     # right-bottom: zoom panel

# Let extent auto-fit to the data in projected coords

# Country backgrounds
corridor_countries_gdf.plot(ax=ax, color='#f5f5f5', edgecolor='#999', linewidth=0.8)

# Choropleth with discrete bins
for idx, row in plot_gdf.iterrows():
    color = row['bin_color']
    plot_gdf.loc[[idx]].plot(ax=ax, color=color, edgecolor='black', linewidth=0.4)

# TEN-T road network
tent_gdf.plot(ax=ax, color='#CC5500', linewidth=2.0, alpha=0.8, zorder=3)

# Border regions highlight — single dissolved outline
border_dissolved = border_gdf.dissolve()
border_dissolved.plot(ax=ax, facecolor='none', edgecolor='#666666',
                      linewidth=3.0, linestyle='--', zorder=4)

# Country name labels (with manual offsets for overlap)
label_offsets = {'AT': (120000, 0)}  # shift Austria label right
for _, row in corridor_countries_gdf.iterrows():
    cc = row['CNTR_CODE']
    if cc in country_names:
        centroid = row.geometry.centroid
        dx, dy = label_offsets.get(cc, (0, 0))
        ax.text(centroid.x + dx, centroid.y + dy, country_names[cc],
                ha='center', va='center', fontsize=16, fontweight='bold',
                color='#333', fontstyle='italic',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                          alpha=0.6, edgecolor='none'))

# No NUTS codes on main map — they go in the zoom panel

# Crop to exclude Faroe Islands / Svalbard — set limits based on corridor bounds
corridor_bounds = plot_gdf.total_bounds  # xmin, ymin, xmax, ymax
ax.set_xlim(corridor_bounds[0] - 100000, corridor_bounds[2] + 100000)
ax.set_ylim(corridor_bounds[1] - 100000, corridor_bounds[3] + 100000)
ax.set_axis_off()

# Scale bar (500 km) — in EPSG:3035, 1 unit = 1 meter
bar_m = 500_000  # 500 km
bounds = plot_gdf.total_bounds  # xmin, ymin, xmax, ymax
x0 = bounds[0] + 100_000
y0 = bounds[1] + 100_000
ax.plot([x0, x0 + bar_m], [y0, y0], color='black', linewidth=2.5)
ax.text(x0 + bar_m / 2, y0 + 30_000, '500 km',
        ha='center', va='bottom', fontsize=14,
        bbox=dict(facecolor='white', edgecolor='none', alpha=0.8))

# Legend: discrete bins — placed in center-right area of left panel
legend_elements = []
for i, label in enumerate(bin_labels):
    legend_elements.append(mpatches.Patch(facecolor=bin_colors[i], edgecolor='black',
                                           linewidth=0.5, label=f'{label}k truck-breaks'))
legend_elements.append(Line2D([0], [0], color='#CC5500', linewidth=2.5, label='TEN-T road network'))
legend_elements.append(mpatches.Patch(facecolor='none', edgecolor='#666666',
                                       linewidth=2, linestyle='--', label='DE-AT-IT border region'))

fig.legend(handles=legend_elements, loc='upper center',
           bbox_to_anchor=(0.78, 0.82), fontsize=13, framealpha=0.9)

ax.set_title(f'Mandatory truck-breaks per NUTS-2 region\n(weighted by freight volume, {WEIGHT_YEAR})',
            fontsize=20, fontweight='bold')

# ── Right panel: zoomed border region map — colored by electricity price ──

# Load electricity prices (Go RES, scenario_000, MCS=type 2, year 2028=index 8)
fuel_costs = load_yaml(INPUT_DIR / 'uncertainty_scenarios_v2' / 'scenario_000' / 'FuelCost.yaml')
nuts2_to_geo = {}
for g in geo_yaml:
    if g.get('type') == 'node':
        n2 = g.get('nuts2_region', '')
        if n2:
            nuts2_to_geo[n2] = g['id']

elec_price_nuts2 = {}  # nuts2 -> ct/kWh
for fc in fuel_costs:
    if fc['fuel'] != 'electricity' or fc['fueling_infr_type_id'] != 2:  # MCS
        continue
    gid = fc['location']
    n2 = geo_to_nuts2.get(gid, '')
    if n2 in SOUTHERN_BORDER_REGIONS:
        elec_price_nuts2[n2] = fc['cost_per_kWh'][20] * 100  # EUR/kWh -> ct/kWh (2040)

corridor_nuts2_local = corridor_nuts2.copy()
corridor_nuts2_local['is_border'] = corridor_nuts2_local['NUTS_ID'].isin(SOUTHERN_BORDER_REGIONS)
border_regions_zoom = corridor_nuts2_local[corridor_nuts2_local['is_border']]

# Merge electricity prices
border_zoom_merged = border_regions_zoom.copy()
border_zoom_merged['elec_price'] = border_zoom_merged['NUTS_ID'].map(elec_price_nuts2)

# Three discrete price levels by country — matching colors from other figures
COUNTRY_COLORS_ZOOM = {
    'AT': '#d4a017',   # golden yellow
    'DE': '#5b4fa8',   # purple
    'IT': '#e05050',   # red
}

# Get actual prices per country for legend
country_prices = {}
for n2, price in elec_price_nuts2.items():
    cc = n2[:2]
    country_prices[cc] = price

PRICE_LABELS = {cc: f'{cc}: {country_prices[cc]:.1f} ct/kWh' for cc in ['AT', 'DE', 'IT']}

for idx, row in border_zoom_merged.iterrows():
    cc = row['NUTS_ID'][:2]
    color = COUNTRY_COLORS_ZOOM.get(cc, '#cccccc')
    border_zoom_merged.loc[[idx]].plot(ax=ax_zoom, color=color,
                                        edgecolor='black', linewidth=1.5)

# TEN-T in zoom
tent_gdf.plot(ax=ax_zoom, color='#CC5500', linewidth=2.5, alpha=0.8, zorder=3)

# NUTS-2 code labels only
for idx, row in border_zoom_merged.iterrows():
    centroid = row.geometry.centroid
    nuts_id = row['NUTS_ID']
    ax_zoom.annotate(nuts_id,
                xy=(centroid.x, centroid.y),
                ha='center', va='center',
                fontsize=12, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                          edgecolor='gray', alpha=0.9),
                zorder=5)

# Set zoom extent to border region bounds with padding
border_bounds = border_regions_zoom.total_bounds  # xmin, ymin, xmax, ymax
pad = 80000  # 80 km padding
ax_zoom.set_xlim(border_bounds[0] - pad, border_bounds[2] + pad)
ax_zoom.set_ylim(border_bounds[1] - pad, border_bounds[3] + pad)
ax_zoom.set_axis_off()
ax_zoom.set_title('DE-AT-IT border region', fontsize=18, fontweight='bold', color='#333')

# Discrete price legend below zoom panel
price_legend = [mpatches.Patch(facecolor=COUNTRY_COLORS_ZOOM[cc], edgecolor='black',
                                linewidth=0.5, label=PRICE_LABELS[cc])
                for cc in ['IT', 'AT', 'DE']]  # order by price: cheapest first
ax_zoom.legend(handles=price_legend, loc='upper center',
               bbox_to_anchor=(0.5, -0.02), fontsize=12, framealpha=0.9, ncol=1)

# Caption below legend
ax_zoom.text(0.5, -0.28, 'Go RES scenario, 2040 electricity prices',
             transform=ax_zoom.transAxes, ha='center', fontsize=13,
             fontstyle='italic', color='#555')

# Scale bar (100 km)
bar_m = 100_000
x0 = border_bounds[0] - pad + 20000
y0 = border_bounds[1] - pad + 20000
ax_zoom.plot([x0, x0 + bar_m], [y0, y0], color='black', linewidth=2.5)
ax_zoom.text(x0 + bar_m / 2, y0 + 10000, '100 km',
        ha='center', va='bottom', fontsize=13,
        bbox=dict(facecolor='white', edgecolor='none', alpha=0.8))

# Draw connection box on main map and connecting lines to zoom panel
from matplotlib.patches import ConnectionPatch

# Rectangle on main map
rect = plt.Rectangle((border_bounds[0] - pad, border_bounds[1] - pad),
                      border_bounds[2] - border_bounds[0] + 2*pad,
                      border_bounds[3] - border_bounds[1] + 2*pad,
                      linewidth=2, edgecolor='#666666', facecolor='none',
                      linestyle='--', zorder=6)
ax.add_patch(rect)

# Connecting lines: top-right of rectangle to top-left of zoom panel
con_top = ConnectionPatch(
    xyA=(border_bounds[2] + pad, border_bounds[3] + pad), coordsA=ax.transData,
    xyB=(border_bounds[0] - pad, border_bounds[3] + pad), coordsB=ax_zoom.transData,
    color='#666666', linewidth=1.2, linestyle='--', alpha=0.6)
fig.add_artist(con_top)

# Bottom-right of rectangle to bottom-left of zoom panel
con_bot = ConnectionPatch(
    xyA=(border_bounds[2] + pad, border_bounds[1] - pad), coordsA=ax.transData,
    xyB=(border_bounds[0] - pad, border_bounds[1] - pad), coordsB=ax_zoom.transData,
    color='#666666', linewidth=1.2, linestyle='--', alpha=0.6)
fig.add_artist(con_bot)

plt.tight_layout()

# Save
for path in [FIG_DIR]:
    plt.savefig(str(path / 'mandatory_breaks_and_border_region.pdf'), bbox_inches='tight', dpi=300)
    plt.savefig(str(path / 'mandatory_breaks_and_border_region.png'), bbox_inches='tight', dpi=300)

if MANUSCRIPT_IMG.exists():
    plt.savefig(str(MANUSCRIPT_IMG / 'mandatory_breaks_and_border_region.pdf'), bbox_inches='tight', dpi=300)

print('Saved: mandatory_breaks_and_border_region.pdf/.png')
plt.close()
