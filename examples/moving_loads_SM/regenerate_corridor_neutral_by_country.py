"""
Left-panel-only corridor map, neutral styling.

Same geography as the left side of `mandatory_breaks_and_border_region.pdf`
(NUTS-2 regions along the NO-FI-SE-DK-DE-AT-IT corridor, TEN-T road network,
DE-AT-IT border region highlight), but:
  - regions are colored ONLY by country (neutral palette), not by truck-breaks
  - country name labels are removed
  - Germany is split into two bidding zones (DEN / DES) following the optimal
    delineation in Fraunholz et al. (2021), Energy Policy 149, 111833, Fig. 5

Output: figures/corridor_neutral_by_country.png
"""

import yaml
import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import matplotlib.patches as mpatches
from pathlib import Path

plt.rcParams.update(plt.rcParamsDefault)
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Segoe UI", "sans-serif"],
    "font.size": 18,
})

BASE_PATH = Path(__file__).resolve().parent
FIG_DIR = BASE_PATH / 'figures'

CORRIDOR_COUNTRIES = ['AT', 'DE', 'IT', 'DK', 'SE', 'NO', 'FI']
SOUTHERN_BORDER_REGIONS = {
    'AT33', 'AT34',
    'ITC4', 'ITH1', 'ITH2', 'ITH3',
    'DE14', 'DE21', 'DE27',
}
TENT_SHP = Path('D:/AntoniaMariaG/ten-t/roads_GL2017_CNC_E.shp')

# Germany is split into two electricity bidding zones following the optimal
# delineation in Fraunholz et al. (2021), "On the long-term efficiency of
# market splitting in Germany", Energy Policy 149, 111833, Fig. 5.
# Their zones (DEN = North, DES = South) come from fuzzy c-means clustering of
# hourly nodal prices, NOT from federal-state / TSO boundaries. The resulting
# DES (South) zone is the southern band of Germany: Baden-Wuerttemberg +
# Bavaria (+ Saarland); DEN (North) is everything else.
#
# NOTE: this differs from the TSO-boundary split coded in
# create_eem_scenarios.py, which assigns Hesse, NRW, Thuringia, Saxony and
# Rhineland-Palatinate to South. Here we follow the paper's Fig. 5.
DE_SOUTH_NUTS2 = {
    # Baden-Wuerttemberg
    'DE11', 'DE12', 'DE13', 'DE14',
    # Bavaria
    'DE21', 'DE22', 'DE23', 'DE24', 'DE25', 'DE26', 'DE27',
    # Saarland (far southwest, in DES per Fig. 5)
    'DEC0',
}
# DE_NORTH = all remaining German NUTS-2 regions (computed below from the data)

# Neutral, soft country palette (distinct but muted)
COUNTRY_COLORS = {
    'NO': '#cfd8dc',  # blue-grey
    'SE': '#b0bec5',  # grey-blue
    'FI': '#d7ccc8',  # warm grey
    'DK': '#c5cae9',  # pale lavender
    'DE-North (DEN)': '#a1887f',  # darker taupe
    'DE-South (DES)': '#d7c4ba',  # lighter taupe
    'AT': '#b2dfdb',  # muted teal
    'IT': '#cfd0e8',  # soft periwinkle
}

# Order for the legend (DE split into two zones)
LEGEND_ORDER = ['NO', 'SE', 'FI', 'DK', 'DE-North (DEN)', 'DE-South (DES)', 'AT', 'IT']


def zone_for(row):
    """Map a NUTS-2 region to its color group (country, or DE zone).

    Germany follows Fraunholz et al. (2021) Fig. 5: South (DES) is the
    explicit set above; every other German region is North (DEN).
    """
    if row['CNTR_CODE'] == 'DE':
        return 'DE-South (DES)' if row['NUTS_ID'] in DE_SOUTH_NUTS2 else 'DE-North (DEN)'
    return row['CNTR_CODE']

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
tent_gdf = gpd.read_file(TENT_SHP).to_crs('EPSG:4326')

# Remove Svalbard (NO0B)
corridor_nuts2 = corridor_nuts2[~corridor_nuts2['NUTS_ID'].isin(['NO0B'])]

# -- Reproject to ETRS89-LAEA (EPSG:3035) -------------------------------------
TARGET_CRS = 'EPSG:3035'
corridor_nuts2 = corridor_nuts2.to_crs(TARGET_CRS)
corridor_countries_gdf = corridor_countries_gdf.to_crs(TARGET_CRS)
tent_gdf = tent_gdf.to_crs(TARGET_CRS)

corridor_nuts2['zone'] = corridor_nuts2.apply(zone_for, axis=1)
corridor_nuts2['country_color'] = corridor_nuts2['zone'].map(COUNTRY_COLORS).fillna('#eeeeee')

# -- Figure -------------------------------------------------------------------
print('Generating figure...')
fig, ax = plt.subplots(figsize=(9, 16))

# Country backgrounds
corridor_countries_gdf.plot(ax=ax, color='#f5f5f5', edgecolor='#999', linewidth=0.8)

# Regions colored by country
corridor_nuts2.plot(ax=ax, color=corridor_nuts2['country_color'],
                    edgecolor='black', linewidth=0.4)

# Boundary between the two German zones
de_north = corridor_nuts2[corridor_nuts2['zone'] == 'DE-North (DEN)'].dissolve()
de_south = corridor_nuts2[corridor_nuts2['zone'] == 'DE-South (DES)'].dissolve()
if len(de_north) and len(de_south):
    zone_border = de_north.geometry.iloc[0].intersection(de_south.geometry.iloc[0].boundary)
    gpd.GeoSeries([zone_border], crs=TARGET_CRS).plot(
        ax=ax, color='#5d4037', linewidth=1.8, zorder=3.5)

# TEN-T road network
tent_gdf.plot(ax=ax, color='#CC5500', linewidth=2.0, alpha=0.8, zorder=4)

# (No border-region highlight, no country name labels)

# Crop to corridor bounds
b = corridor_nuts2.total_bounds  # xmin, ymin, xmax, ymax
ax.set_xlim(b[0] - 100000, b[2] + 100000)
ax.set_ylim(b[1] - 100000, b[3] + 100000)
ax.set_axis_off()

# Scale bar (500 km)
bar_m = 500_000
x0 = b[0] + 100_000
y0 = b[1] + 100_000
ax.plot([x0, x0 + bar_m], [y0, y0], color='black', linewidth=2.5)
ax.text(x0 + bar_m / 2, y0 + 30_000, '500 km',
        ha='center', va='bottom', fontsize=14,
        bbox=dict(facecolor='white', edgecolor='none', alpha=0.8))

# Legend: country colors + network + border region
legend_elements = [
    mpatches.Patch(facecolor=COUNTRY_COLORS[g], edgecolor='black',
                   linewidth=0.5, label=g)
    for g in LEGEND_ORDER
]
legend_elements.append(Line2D([0], [0], color='#CC5500', linewidth=2.5,
                              label='TEN-T road network'))
ax.legend(handles=legend_elements, loc='upper right', fontsize=13, framealpha=0.9)

plt.tight_layout()
out = FIG_DIR / 'corridor_neutral_by_country.png'
plt.savefig(str(out), bbox_inches='tight', dpi=300)
print(f'Saved: {out}')
plt.close()
