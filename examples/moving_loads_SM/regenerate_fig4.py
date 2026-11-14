"""
Regenerate Figure 4: DE-AT-IT border region zoomed map with NUTS-2 boundaries.
Fixes: font consistent with results figures (LaTeX mathpazo), includes scale bar.
"""

import numpy as np
import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

# ── Font settings (matching results figures) ─────────────────────────
plt.rcParams.update(plt.rcParamsDefault)
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "serif",
    'font.serif': 'mathpazo',
    'font.size': 18,
})

# ── Paths ────────────────────────────────────────────────────────────
BASE_PATH = Path(__file__).resolve().parent
FIG_DIR = BASE_PATH / 'figures'
MANUSCRIPT_IMG = BASE_PATH.parent.parent / 'manuscript' / 'images'

CORRIDOR_COUNTRIES = ['AT', 'DE', 'IT', 'DK', 'SE', 'NO']

SOUTHERN_BORDER_REGIONS = {
    'AT33', 'AT34',
    'ITC4', 'ITH1', 'ITH2', 'ITH3',
    'DE14', 'DE21', 'DE27',
}

REGION_NAMES = {
    'AT33': 'Tyrol', 'AT34': 'Vorarlberg',
    'ITC4': 'Lombardy', 'ITH1': 'Trentino-Alto Adige',
    'ITH2': 'Friuli-Venezia Giulia', 'ITH3': 'Veneto',
    'DE14': 'T\\"{u}bingen', 'DE21': 'Upper Bavaria', 'DE27': 'Swabia',
}

colors_by_country = {'AT': '#E74C3C', 'IT': '#27AE60', 'DE': '#3498DB'}

XLIM = (8.5, 14.5)
YLIM = (45.5, 49.5)

# ── Load shapefile ───────────────────────────────────────────────────
print('Loading shapefile...')
nuts_shp = BASE_PATH / 'data' / 'NUTS_RG_20M_2021_4326.shp' / 'NUTS_RG_20M_2021_4326.shp'
nuts_gdf = gpd.read_file(nuts_shp)

nuts2 = nuts_gdf[nuts_gdf['LEVL_CODE'] == 2].copy()
corridor_nuts2 = nuts2[nuts2['CNTR_CODE'].isin(CORRIDOR_COUNTRIES)].copy()
corridor_nuts2['is_border'] = corridor_nuts2['NUTS_ID'].isin(SOUTHERN_BORDER_REGIONS)

nuts0 = nuts_gdf[nuts_gdf['LEVL_CODE'] == 0].copy()
corridor_countries_gdf = nuts0[nuts0['CNTR_CODE'].isin(CORRIDOR_COUNTRIES)]

non_border = corridor_nuts2[~corridor_nuts2['is_border']]
border_regions = corridor_nuts2[corridor_nuts2['is_border']]

print(f'  Border regions: {len(border_regions)}')

# ── Plot ─────────────────────────────────────────────────────────────
print('Generating figure...')
fig, ax = plt.subplots(figsize=(10, 7))

# Non-border regions
non_border.plot(ax=ax, color='#E8E8E8', edgecolor='#CCCCCC', linewidth=0.5)

# Border regions by country
for country, color in colors_by_country.items():
    country_border = border_regions[border_regions['CNTR_CODE'] == country]
    if len(country_border) > 0:
        country_border.plot(ax=ax, color=color, edgecolor='black', linewidth=2, alpha=0.7)

# Country borders
corridor_countries_gdf.boundary.plot(ax=ax, color='black', linewidth=2, linestyle='-')

# Region labels
for idx, row in border_regions.iterrows():
    centroid = row.geometry.centroid
    region_name = REGION_NAMES.get(row['NUTS_ID'], row['NUTS_ID'])
    ax.annotate(f"{row['NUTS_ID']}\n{region_name}",
                xy=(centroid.x, centroid.y),
                ha='center', va='center',
                fontsize=10, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                          edgecolor='gray', alpha=0.9))

# Legend
legend_elements = [
    mpatches.Patch(facecolor='#E74C3C', edgecolor='black', label='Austria (2 regions)', alpha=0.7),
    mpatches.Patch(facecolor='#27AE60', edgecolor='black', label='Italy (4 regions)', alpha=0.7),
    mpatches.Patch(facecolor='#3498DB', edgecolor='black', label='Germany (3 regions)', alpha=0.7),
]
ax.legend(handles=legend_elements, loc='upper right', fontsize=13)

ax.set_xlim(*XLIM)
ax.set_ylim(*YLIM)
ax.set_xlabel('Longitude')
ax.set_ylabel('Latitude')
ax.tick_params(labelsize=14)
ax.grid(True, alpha=0.3, linestyle='--')

# ── Scale bar ────────────────────────────────────────────────────────
mid_lat = (YLIM[0] + YLIM[1]) / 2  # ~47.5°
km_per_deg = 111.32 * np.cos(np.radians(mid_lat))
bar_km = 50
bar_deg = bar_km / km_per_deg

x0 = XLIM[0] + 0.3
y0 = YLIM[0] + 0.2
ax.plot([x0, x0 + bar_deg], [y0, y0], color='black', linewidth=2.5,
        transform=ax.transData, clip_on=False)
ax.text(x0 + bar_deg / 2, y0 + 0.12, f'{bar_km} km',
        ha='center', va='bottom', fontsize=12,
        bbox=dict(facecolor='white', edgecolor='none', alpha=0.8))

plt.tight_layout()

# Save
for dst in [FIG_DIR, MANUSCRIPT_IMG]:
    fig.savefig(dst / 'border_regions_map_zoomed.pdf', bbox_inches='tight')
fig.savefig(FIG_DIR / 'border_regions_map_zoomed.png', bbox_inches='tight', dpi=150)
plt.close()
print('Saved: figures/border_regions_map_zoomed.pdf')
print('Saved: manuscript/images/border_regions_map_zoomed.pdf')
print('Done.')
