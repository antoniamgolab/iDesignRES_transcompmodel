"""
Regenerate Figure 13: charging intensity at DE-AT-IT border region (2032 only).
2x2 grid, no annotation numbers, proportional colorbars, larger fonts.
"""

import sys
import re
import ast
import time
import yaml
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.colors import Normalize
from mpl_toolkits.axes_grid1 import make_axes_locatable
from pathlib import Path
from collections import defaultdict

sys.stdout.reconfigure(line_buffering=True)
t0 = time.time()

# ── Font settings ─────────────────────────────────────────────────────
plt.rcParams.update(plt.rcParamsDefault)
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "serif",
    "font.serif": "mathpazo",
    'font.size': 16,
})

# ── Paths ─────────────────────────────────────────────────────────────
BASE_PATH = Path(__file__).resolve().parent
INPUT_PATH = BASE_PATH / 'input_data' / 'fixed_nuts_2'
FIGURES_PATH = BASE_PATH / 'figures'
MANUSCRIPT_IMG = BASE_PATH.parent.parent / 'manuscript' / 'images'

TARGET_YEAR = 2032
MODELED_YEARS = list(range(2020, 2064, 4))
TARGET_Y_IDX = MODELED_YEARS.index(TARGET_YEAR) + 1  # 1-based

# Border NUTS-2 regions
SOUTHERN_BORDER_REGIONS = {
    'AT33', 'AT34',
    'ITC4', 'ITH1', 'ITH2', 'ITH3',
    'DE14', 'DE21', 'DE27',
}

XLIM = (8.5, 16.5)
YLIM = (44.5, 49.5)

CI_RE = re.compile(r'CartesianIndex\((\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\)')


# ── Helper functions ──────────────────────────────────────────────────
def load_yaml(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return yaml.load(f, Loader=yaml.UnsafeLoader)


def find_latest_result_file(folder, variable):
    folder = Path(folder)
    files = list(folder.glob(f'*_{variable}_dict.yaml'))
    if not files:
        return None
    return max(files, key=lambda x: x.stat().st_mtime)


def build_prkg_set(odpair_data, path_by_id):
    prkg = set()
    for o in odpair_data:
        odpair_id = o['id']
        path_id = o.get('path_id', odpair_id)
        p = path_by_id.get(path_id)
        if p:
            for geo_id in p.get('sequence', []):
                prkg.add((0, int(odpair_id), int(path_id), int(geo_id)))
    return sorted(prkg)


def load_nuts2_s_dict_cartesian(filepath, prkg_idx_map, target_y_idx,
                                 bev_tv_idx_list, geoid_to_nuts2):
    """Load CartesianIndex s_dict, aggregate BEV charging by NUTS-2."""
    bev_fl_idxs = {1, 2}
    target_prefix = f'CartesianIndex({target_y_idx},'
    by_nuts2 = defaultdict(float)
    count = matched = 0

    with open(filepath, 'r') as f:
        for line in f:
            count += 1
            if not line.startswith(target_prefix):
                continue
            sep_idx = line.rfind(': ')
            if sep_idx < 0:
                continue
            key_str = line[:sep_idx].strip()
            val_str = line[sep_idx + 2:].strip()
            m = CI_RE.match(key_str)
            if not m:
                continue
            y_idx, prkg_idx, tv_idx, fl_idx, g_idx = (
                int(m.group(i)) for i in range(1, 6)
            )
            if tv_idx not in bev_tv_idx_list or fl_idx not in bev_fl_idxs:
                continue
            val = float(val_str)
            if val <= 0:
                continue
            prkg = prkg_idx_map.get(prkg_idx)
            if prkg is None:
                continue
            geo_elem = prkg[3]
            nuts2 = geoid_to_nuts2.get(geo_elem, '')
            if nuts2:
                by_nuts2[nuts2] += val / 1000  # MWh -> GWh
            matched += 1

    print(f'  Scanned {count:,} lines, {matched} BEV entries -> {Path(filepath).name}')
    return dict(by_nuts2)


def load_nuts2_s_dict_tuple(folder, target_year, geoid_to_nuts2):
    """Load tuple-format s_dict, aggregate BEV charging by NUTS-2."""
    s_file = find_latest_result_file(folder, 's')
    if s_file is None:
        raise FileNotFoundError(f'No s_dict found in {folder}')

    year_prefix = f'({target_year},'
    by_nuts2 = defaultdict(float)
    count = matched = 0

    with open(s_file, 'r') as f:
        for line in f:
            count += 1
            if not line.startswith(year_prefix):
                continue
            sep_idx = line.rfind(': ')
            if sep_idx < 0:
                continue
            key_str = line[:sep_idx].strip()
            val_str = line[sep_idx + 2:].strip().strip('"')
            try:
                key = ast.literal_eval(key_str)
            except (ValueError, SyntaxError):
                continue
            year, (prod, odpair, path, geo_elem), tv_id, (fuel_id, fl_type), gen = key
            if tv_id != 1 or fuel_id != 0:
                continue
            val = float(val_str)
            if val <= 0:
                continue
            nuts2 = geoid_to_nuts2.get(geo_elem, '')
            if nuts2:
                by_nuts2[nuts2] += val / 1000  # MWh -> GWh
            matched += 1

    print(f'  Scanned {count:,} lines, {matched} BEV entries -> {s_file.name}')
    return dict(by_nuts2)


# ── Load geographic data ──────────────────────────────────────────────
print('Loading geographic data...')
geo_data = load_yaml(INPUT_PATH / 'GeographicElement.yaml')
geoid_to_nuts2 = {}
for g in geo_data:
    if g.get('type') == 'node':
        gid = int(g['id'])
        nuts2 = g.get('nuts2_region', '')
        if nuts2:
            geoid_to_nuts2[gid] = nuts2
print(f'  Node-to-NUTS2 mapping: {len(geoid_to_nuts2)} nodes')

# ── Load road prkg mapping (prefer Julia ordering file) ───────────────
print('Loading road prkg mapping...')
_ordering_file = BASE_PATH / 'prkg_ordering_elsevier.txt'
if _ordering_file.exists():
    road_prkg_idx_map = {}
    with open(_ordering_file) as _f:
        for _line in _f:
            _line = _line.strip()
            if not _line:
                continue
            _parts = _line.split('\t')
            _idx = int(_parts[0])
            _t = _parts[1].strip('()')
            _vals = [int(x.strip()) for x in _t.split(',')]
            road_prkg_idx_map[_idx] = tuple(_vals)
    print(f'  Loaded prkg ordering from Julia: {len(road_prkg_idx_map)} entries')
else:
    print('  WARNING: prkg_ordering_elsevier.txt not found, falling back to Python sorted')
    road_input = BASE_PATH / 'input_data' / 'uncertainty_scenarios' / 'scenario_002'
    odpair_data = load_yaml(road_input / 'Odpair.yaml')
    path_data = load_yaml(road_input / 'Path.yaml')
    path_by_id = {p['id']: p for p in path_data}
    road_prkg_sorted = build_prkg_set(odpair_data, path_by_id)
    road_prkg_idx_map = {i + 1: t for i, t in enumerate(road_prkg_sorted)}
print(f'  Time: {time.time()-t0:.1f}s')

# ── Load 4 scenarios ──────────────────────────────────────────────────
RESULTS_PATH = BASE_PATH / 'results'

print('\n=== Loading Reference (baseline, v2 CartesianIndex) ===')
nuts2_baseline = load_nuts2_s_dict_cartesian(
    RESULTS_PATH / 'uncertainty_scenarios_v2' / 'scenario_002'
    / 'scenario_002_cs_2026-02-14_22-18-02_s_dict.yaml',
    road_prkg_idx_map, TARGET_Y_IDX, [2], geoid_to_nuts2,
)
print(f'  Time: {time.time()-t0:.1f}s')

print('\n=== Loading +0.04 EUR/kWh (tuple) ===')
nuts2_elec_high = load_nuts2_s_dict_tuple(
    RESULTS_PATH / 'at_surcharge' / 'at_elec_high',
    TARGET_YEAR, geoid_to_nuts2,
)
print(f'  Time: {time.time()-t0:.1f}s')

print('\n=== Loading +10 EUR/kW/yr (tuple) ===')
nuts2_nw_high = load_nuts2_s_dict_tuple(
    RESULTS_PATH / 'at_surcharge' / 'at_network_high',
    TARGET_YEAR, geoid_to_nuts2,
)
print(f'  Time: {time.time()-t0:.1f}s')

energy_by_nuts2 = {
    'Reference': nuts2_baseline,
    '+0.04 EUR/kWh': nuts2_elec_high,
    '+10 EUR/kW/yr': nuts2_nw_high,
}

# ── Load shapefile and highway data ───────────────────────────────────
print('\nLoading shapefile...')
nuts_shp = BASE_PATH / 'data' / 'NUTS_RG_20M_2021_4326.shp' / 'NUTS_RG_20M_2021_4326.shp'
nuts_gdf = gpd.read_file(nuts_shp)
nuts2_gdf = nuts_gdf[nuts_gdf['LEVL_CODE'] == 2].copy()
nuts0_gdf = nuts_gdf[nuts_gdf['LEVL_CODE'] == 0].copy()

CORRIDOR_COUNTRIES = {'NO', 'SE', 'DK', 'DE', 'AT', 'IT', 'FI'}
corridor_nuts2 = nuts2_gdf[nuts2_gdf['CNTR_CODE'].isin(CORRIDOR_COUNTRIES)].copy()
corridor_countries_gdf = nuts0_gdf[nuts0_gdf['CNTR_CODE'].isin(CORRIDOR_COUNTRIES)]

highway_df = pd.read_csv(BASE_PATH / 'highway_km_per_nuts2.csv')
highway_by_nuts2 = dict(zip(highway_df['NUTS2_CODE'], highway_df['highway_km']))

corridor_with_hw = corridor_nuts2.merge(
    highway_df.rename(columns={'NUTS2_CODE': 'NUTS_ID'}),
    on='NUTS_ID', how='left'
)

border_area_gdf = corridor_with_hw[
    (corridor_with_hw.geometry.centroid.y >= YLIM[0] - 1) &
    (corridor_with_hw.geometry.centroid.y <= YLIM[1] + 1) &
    (corridor_with_hw.geometry.centroid.x >= XLIM[0] - 1) &
    (corridor_with_hw.geometry.centroid.x <= XLIM[1] + 1)
].copy()

print(f'  Border area regions: {len(border_area_gdf)}')
print(f'  Time: {time.time()-t0:.1f}s')


# ── Plot: 2x2 grid ───────────────────────────────────────────────────
print('\n=== Generating figure ===')

scen_names = list(energy_by_nuts2.keys())

# Compute global vmax across all scenarios (for one shared colorbar)
global_vmax = 0
for sn in scen_names:
    for nuts2, mwh in energy_by_nuts2[sn].items():
        hw = highway_by_nuts2.get(nuts2, 0)
        if hw > 0 and nuts2[:2] in {'AT', 'DE', 'IT'}:
            global_vmax = max(global_vmax, mwh / hw)

print(f'  Global vmax: {global_vmax:.2f} MWh/hw-km')

fig, axes = plt.subplots(1, 3, figsize=(16, 5),
                         gridspec_kw={'wspace': 0.05})
axes_flat = axes.flatten()

panel_vmax_list = []
for si, sn in enumerate(scen_names):
    ax = axes_flat[si]

    # Compute per-panel vmax (independent colour scale)
    panel_vmax = 0
    intensity = {}
    for nuts2, mwh in energy_by_nuts2[sn].items():
        hw = highway_by_nuts2.get(nuts2, 0)
        if hw > 0:
            intensity[nuts2] = mwh / hw
            if nuts2[:2] in {'AT', 'DE', 'IT'}:
                panel_vmax = max(panel_vmax, mwh / hw)
        else:
            intensity[nuts2] = 0

    panel_vmax_list.append(panel_vmax)

    int_df = pd.DataFrame([{'nuts2': n, 'intensity': v} for n, v in intensity.items()])

    plot_gdf = border_area_gdf.merge(
        int_df, left_on='NUTS_ID', right_on='nuts2', how='left'
    )
    plot_gdf['intensity'] = plot_gdf['intensity'].fillna(0)

    # Background: corridor countries
    corridor_countries_gdf.plot(ax=ax, color='#f5f5f5', edgecolor='#999', linewidth=0.8)

    # Choropleth
    plot_gdf.plot(
        ax=ax, column='intensity', cmap='YlOrRd',
        edgecolor='black', linewidth=0.6,
        vmin=0, vmax=panel_vmax, legend=False,
    )

    # NUTS-2 labels (region code only, no numbers)
    for idx, row in plot_gdf.iterrows():
        if row['NUTS_ID'] in SOUTHERN_BORDER_REGIONS:
            centroid = row.geometry.centroid
            ax.annotate(
                row['NUTS_ID'],
                xy=(centroid.x, centroid.y), ha='center', va='center',
                fontsize=10,
                bbox=dict(boxstyle='round,pad=0.15', facecolor='white', alpha=0.7)
            )

    ax.set_xlim(*XLIM)
    ax.set_ylim(*YLIM)
    ax.tick_params(labelsize=11)
    ax.set_title(sn, fontsize=15)

    if si > 0:
        ax.set_yticklabels([])

# ── Scale bar (bottom-left panel) ────────────────────────────────
# At ~47°N, 1° longitude ≈ 75.1 km
mid_lat = (YLIM[0] + YLIM[1]) / 2  # ~47°
km_per_deg = 111.32 * np.cos(np.radians(mid_lat))
bar_km = 100
bar_deg = bar_km / km_per_deg

ax_sb = axes_flat[0]  # leftmost panel
x0 = XLIM[0] + 0.4
y0 = YLIM[0] + 0.3
ax_sb.plot([x0, x0 + bar_deg], [y0, y0], color='black', linewidth=2.5,
           transform=ax_sb.transData, clip_on=False)
ax_sb.text(x0 + bar_deg / 2, y0 + 0.15, f'{bar_km} km',
           ha='center', va='bottom', fontsize=12,
           bbox=dict(facecolor='white', edgecolor='none', alpha=0.8))

fig.suptitle(
    f'Charging demand intensity at DE--AT--IT border --- {TARGET_YEAR}',
    fontsize=16
)
plt.tight_layout(rect=[0, 0.12, 1, 0.96], w_pad=0.5)

# ── Add colorbars AFTER tight_layout so positions are final ──────
for si, sn in enumerate(scen_names):
    ax = axes_flat[si]
    pos = ax.get_position()
    cbar_width = pos.width * 0.85
    cbar_x0 = pos.x0 + (pos.width - cbar_width) / 2
    cax = fig.add_axes([cbar_x0, pos.y0 - 0.10, cbar_width, 0.025])
    sm = cm.ScalarMappable(cmap='YlOrRd',
                           norm=Normalize(vmin=0, vmax=panel_vmax_list[si]))
    sm.set_array([])
    cbar = fig.colorbar(sm, cax=cax, orientation='horizontal')
    cbar.set_label('GWh/hw-km', fontsize=11)
    cbar.ax.tick_params(labelsize=9)

# Save
fname = 'at_surcharge_charging_intensity_border'
for dst in [FIGURES_PATH, MANUSCRIPT_IMG]:
    fig.savefig(dst / f'{fname}.pdf', bbox_inches='tight')
fig.savefig(FIGURES_PATH / f'{fname}.svg', bbox_inches='tight')
plt.close()
print(f'\nSaved: figures/{fname}.pdf')
print(f'Done. Total time: {time.time()-t0:.1f}s')
