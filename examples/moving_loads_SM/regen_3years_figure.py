"""
Standalone script to regenerate at_surcharge_border_charging_reallocation_3years.pdf
with increased font sizes. Extracted from visualize_at_surcharge.ipynb.
"""
import matplotlib
matplotlib.use('Agg')

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yaml
import ast
import re
import os
import glob
from pathlib import Path
from collections import defaultdict

# === Configure matplotlib ===
plt.rcParams.update(plt.rcParamsDefault)
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "serif",
    'font.serif': ['Palatino Linotype', 'Palatino', 'Times New Roman'],
    'font.size': 20,
    'axes.labelsize': 20,
})

# === Configuration ===
BASE_PATH = Path.cwd()
INPUT_PATH = BASE_PATH / 'input_data' / 'fixed_nuts_2'
FIGURES_PATH = BASE_PATH / 'figures'
FIGURES_PATH.mkdir(exist_ok=True)

ROAD_BASELINE_PATH = BASE_PATH / 'results' / 'uncertainty_scenarios_v2' / 'scenario_002'
RAIL_BASELINE_PATH = BASE_PATH / 'results' / 'rail' / 'scenario_016'
ROAD_SURCHARGE_PATH = BASE_PATH / 'results' / 'at_surcharge'
FIXED_FLEET_PATH = BASE_PATH / 'results' / 'at_surcharge_fixed_fleet' / 'at_elec_extreme'
RAIL_SURCHARGE_PATH = BASE_PATH / 'results' / 'at_surcharge_rail'

MODELED_YEARS = list(range(2020, 2064, 4))

print(f"Base path: {BASE_PATH}")

# === Utility functions ===
def find_latest_result_file(folder, variable):
    folder = Path(folder)
    pattern = f'*_{variable}_dict.yaml'
    files = list(folder.glob(pattern))
    if not files:
        return None
    return max(files, key=lambda x: x.stat().st_mtime)

def load_yaml(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return yaml.load(f, Loader=yaml.UnsafeLoader)

# === Load geographic data ===
geo_data = load_yaml(INPUT_PATH / 'GeographicElement.yaml')
path_data = load_yaml(INPUT_PATH / 'Path.yaml')

geoid_to_nuts2 = {}
for g in geo_data:
    if g.get('type') == 'node':
        geoid_to_nuts2[int(g['id'])] = g.get('nuts2_region', '')

path_by_id = {p['id']: p for p in path_data}
path_seq = {}
for p in path_data:
    path_seq[p['id']] = [int(x) for x in p.get('sequence', [])]

print(f"Geo nodes with NUTS-2: {len(geoid_to_nuts2)}")
print(f"Paths: {len(path_by_id)}")

# === Border region definitions ===
SOUTHERN_BORDER_REGIONS = {'AT33', 'AT34', 'ITC4', 'ITH1', 'ITH2', 'ITH3', 'DE14', 'DE21', 'DE27'}
node_to_border = {nid: nuts2 for nid, nuts2 in geoid_to_nuts2.items() if nuts2 in SOUTHERN_BORDER_REGIONS}
print(f"Border nodes: {len(node_to_border)}")

# === CartesianIndex decoder ===
CI_RE = re.compile(r'CartesianIndex\((\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\)')
year_idx_map = {i+1: y for i, y in enumerate(MODELED_YEARS)}
fl_idx_map = {1: (0, 1), 2: (0, 2), 3: (1, 0)}
gen_list = list(range(2008, 2064, 4))
gen_idx_map = {i+1: g for i, g in enumerate(gen_list)}

def decode_cartesian_s_dict(filepath, prkg_sorted, tv_map):
    prkg_map = {i+1: t for i, t in enumerate(prkg_sorted)}
    result = {}
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            sep_idx = line.rfind(': ')
            if sep_idx < 0: continue
            m = CI_RE.match(line[:sep_idx])
            if not m: continue
            y_idx, prkg_idx, tv_idx, fl_idx, g_idx = (int(m.group(i)) for i in range(1, 6))
            year = year_idx_map.get(y_idx)
            prkg = prkg_map.get(prkg_idx)
            tv_id = tv_map.get(tv_idx)
            fl_pair = fl_idx_map.get(fl_idx)
            gen = gen_idx_map.get(g_idx)
            if any(x is None for x in [year, prkg, tv_id, fl_pair, gen]):
                continue
            result[(year, prkg, tv_id, fl_pair, gen)] = float(line[sep_idx+2:])
    return result

def load_surcharge_s_dicts(scenarios):
    result = {}
    for scen_id, cfg in scenarios.items():
        if cfg['path'] is None:
            continue
        s_file = find_latest_result_file(cfg['path'], 's')
        if s_file is None:
            print(f'  SKIP {scen_id}: no s_dict')
            continue
        with open(s_file, 'r') as f:
            raw = yaml.safe_load(f)
        parsed = {}
        for k, v in raw.items():
            try:
                key = ast.literal_eval(str(k))
            except (ValueError, SyntaxError):
                continue
            parsed[key] = float(v)
        result[scen_id] = parsed
        print(f'  OK   {scen_id}: {len(parsed)} entries')
    return result

def aggregate_border_by_country(s_dicts_dict):
    result = {}
    for scen_id, sd in s_dicts_dict.items():
        result[scen_id] = {}
        for y in MODELED_YEARS:
            by_c = defaultdict(float)
            for key, val in sd.items():
                year, (prod, odpair, path, geo_elem), tv_id, (fuel_id, fl_type), gen = key
                if year != y or tv_id != 1 or fuel_id != 0 or val <= 0:
                    continue
                nuts2 = node_to_border.get(geo_elem)
                if nuts2:
                    by_c[nuts2[:2]] += val
            result[scen_id][y] = dict(by_c)
    return result

# === Load road-only scenarios ===
all_s_scenarios = {
    'baseline':        {'path': None, 'label': 'Baseline', 'type': 'baseline'},
    'at_elec_low':     {'path': ROAD_SURCHARGE_PATH / 'at_elec_low',     'label': '+0.01 EUR/kWh', 'type': 'elec'},
    'at_elec_med':     {'path': ROAD_SURCHARGE_PATH / 'at_elec_med',     'label': '+0.02 EUR/kWh', 'type': 'elec'},
    'at_elec_high':    {'path': ROAD_SURCHARGE_PATH / 'at_elec_high',    'label': '+0.04 EUR/kWh', 'type': 'elec'},
    'at_network_low':  {'path': ROAD_SURCHARGE_PATH / 'at_network_low',  'label': '+2 EUR/kW/yr',  'type': 'network'},
    'at_network_med':  {'path': ROAD_SURCHARGE_PATH / 'at_network_med',  'label': '+5 EUR/kW/yr',  'type': 'network'},
    'at_network_high': {'path': ROAD_SURCHARGE_PATH / 'at_network_high', 'label': '+10 EUR/kW/yr', 'type': 'network'},
}

print("=== Road-only surcharges ===")
all_s_dicts = load_surcharge_s_dicts(all_s_scenarios)

# Road baseline (CartesianIndex) — use Julia's prkg ordering if available
scenario_002_input = BASE_PATH / 'input_data' / 'uncertainty_scenarios' / 'scenario_002'
odpair_002 = load_yaml(scenario_002_input / 'Odpair.yaml')
path_002 = load_yaml(scenario_002_input / 'Path.yaml')
path_002_by_id = {p['id']: p for p in path_002}

_ordering_file = BASE_PATH / 'prkg_ordering_elsevier.txt'
if _ordering_file.exists():
    _prkg_from_file = {}
    with open(_ordering_file) as _f:
        for _line in _f:
            _line = _line.strip()
            if not _line:
                continue
            _parts = _line.split('\t')
            _idx = int(_parts[0])
            _t = _parts[1].strip('()')
            _vals = [int(x.strip()) for x in _t.split(',')]
            _prkg_from_file[_idx] = tuple(_vals)
    road_prkg_sorted = [_prkg_from_file[i] for i in sorted(_prkg_from_file.keys())]
    print(f'  Loaded prkg ordering from Julia: {len(road_prkg_sorted)} entries')
else:
    print('  WARNING: prkg_ordering_elsevier.txt not found, using Python sorted')
    road_prkg = set()
    for o in odpair_002:
        pid = o.get('path_id', o['id'])
        p = path_002_by_id.get(pid)
        if p:
            for g in p.get('sequence', []):
                road_prkg.add((0, int(o['id']), int(pid), int(g)))
    road_prkg_sorted = sorted(road_prkg)

baseline_path = (BASE_PATH / 'results' / 'uncertainty_scenarios_v2' / 'scenario_002' /
                 'scenario_002_cs_2026-02-14_22-18-02_s_dict.yaml')
all_s_dicts['baseline'] = decode_cartesian_s_dict(
    baseline_path, road_prkg_sorted, {1: 0, 2: 1})
print(f'  OK   baseline: {len(all_s_dicts["baseline"])} entries')

# === Load rail scenarios ===
rail_s_scenarios = {
    'rail_baseline':     {'path': None, 'label': 'Baseline\n(rail)', 'type': 'baseline'},
    'rail_elec_low':     {'path': RAIL_SURCHARGE_PATH / 'at_elec_low',     'label': '+0.01 EUR/kWh', 'type': 'elec'},
    'rail_elec_med':     {'path': RAIL_SURCHARGE_PATH / 'at_elec_med',     'label': '+0.02 EUR/kWh', 'type': 'elec'},
    'rail_elec_high':    {'path': RAIL_SURCHARGE_PATH / 'at_elec_high',    'label': '+0.04 EUR/kWh', 'type': 'elec'},
    'rail_network_low':  {'path': RAIL_SURCHARGE_PATH / 'at_network_low',  'label': '+2 EUR/kW/yr',  'type': 'network'},
    'rail_network_med':  {'path': RAIL_SURCHARGE_PATH / 'at_network_med',  'label': '+5 EUR/kW/yr',  'type': 'network'},
    'rail_network_high': {'path': RAIL_SURCHARGE_PATH / 'at_network_high', 'label': '+10 EUR/kW/yr', 'type': 'network'},
}

print("\n=== Road+Rail surcharges ===")
rail_s_dicts = load_surcharge_s_dicts(rail_s_scenarios)

# Rail baseline (CartesianIndex)
rail_016_input = BASE_PATH / 'input_data' / 'uncertainty_scenarios_rail' / 'scenario_016'
rail_016_odpair = load_yaml(rail_016_input / 'Odpair.yaml')
rail_016_path = load_yaml(rail_016_input / 'Path.yaml')
rail_016_path_by_id = {p['id']: p for p in rail_016_path}

rail_prkg = set()
for o in rail_016_odpair:
    pid = o.get('path_id', o['id'])
    p = rail_016_path_by_id.get(pid)
    if p:
        for g in p.get('sequence', []):
            rail_prkg.add((0, int(o['id']), int(pid), int(g)))
rail_prkg_sorted = sorted(rail_prkg)
rail_prkg_idx_map = {i+1: t for i, t in enumerate(rail_prkg_sorted)}

rail_baseline_path = (BASE_PATH / 'results' / 'rail' / 'scenario_016' /
                      'scenario_016_cs_2026-02-14_22-16-25_s_dict.yaml')
rail_s_dicts['rail_baseline'] = decode_cartesian_s_dict(
    rail_baseline_path, rail_prkg_sorted, {1: 0, 2: 1})
print(f'  OK   rail_baseline: {len(rail_s_dicts["rail_baseline"])} entries')

# === Aggregate road+rail by border country ===
all_border_by_country = aggregate_border_by_country(all_s_dicts)
rail_border_by_country = aggregate_border_by_country(rail_s_dicts)

# === Load breaks scenario (road-only) ===
results_dir = BASE_PATH / 'results'
breaks_dir = results_dir / 'uncertainty_scenarios_breaks_only'

print("\n=== Breaks scenario (road) ===")
breaks_s_file = find_latest_result_file(breaks_dir / 'scenario_002', 's')
if breaks_s_file:
    breaks_s_path = Path(breaks_s_file)
    print(f'  File: {breaks_s_path.name}')

    # Use same prkg ordering as baseline (all road scenarios share identical OD/paths)
    road_prkg_breaks_idx_map = {i+1: t for i, t in enumerate(road_prkg_sorted)}

    breaks_s = {}
    with open(breaks_s_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            sep_idx = line.rfind(': ')
            if sep_idx < 0: continue
            m = CI_RE.match(line[:sep_idx])
            if not m: continue
            y_idx, prkg_idx, tv_idx, fl_idx, g_idx = (int(m.group(i)) for i in range(1, 6))
            year = year_idx_map.get(y_idx)
            prkg = road_prkg_breaks_idx_map.get(prkg_idx)
            tv_id = {1: 0, 2: 1}.get(tv_idx)
            fl_pair = fl_idx_map.get(fl_idx)
            gen = gen_idx_map.get(g_idx)
            if any(x is None for x in [year, prkg, tv_id, fl_pair, gen]):
                continue
            breaks_s[(year, prkg, tv_id, fl_pair, gen)] = float(line[sep_idx+2:])

    print(f'  OK   breaks: {len(breaks_s)} entries')

    breaks_border = {}
    for y in MODELED_YEARS:
        by_c = defaultdict(float)
        for key, val in breaks_s.items():
            year, (prod, odpair, path, geo_elem), tv_id, (fuel_id, fl_type), gen = key
            if year != y or tv_id != 1 or fuel_id != 0 or val <= 0:
                continue
            nuts2 = node_to_border.get(geo_elem)
            if nuts2:
                by_c[nuts2[:2]] += val
        breaks_border[y] = dict(by_c)

    all_border_by_country['breaks'] = breaks_border
    all_s_scenarios['breaks'] = {'label': 'Breaks\nconstraint', 'type': 'breaks'}
    print(f'  Added breaks to all_border_by_country')
else:
    print('  SKIP breaks: no s_dict found')

# === Load breaks+rail scenario ===
print("\n=== Breaks+rail scenario ===")
breaks_rail_dir = results_dir / 'uncertainty_scenarios_breaks_only' / 'scenario_016'
if breaks_rail_dir.exists():
    s_files = list(breaks_rail_dir.glob('*_s_dict.yaml'))
    if s_files:
        breaks_rail_s_path = s_files[0]
        print(f'  File: {breaks_rail_s_path.name}')

        # Decode with {1: 0, 2: 1} mapping (Jan 6 file uses 2-TV standard mapping)
        breaks_rail_s = {}
        with open(breaks_rail_s_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line: continue
                sep_idx = line.rfind(': ')
                if sep_idx < 0: continue
                m = CI_RE.match(line[:sep_idx])
                if not m: continue
                y_idx, prkg_idx, tv_idx, fl_idx, g_idx = (int(m.group(i)) for i in range(1, 6))
                year = year_idx_map.get(y_idx)
                prkg = rail_prkg_idx_map.get(prkg_idx)
                tv_id = {1: 0, 2: 1}.get(tv_idx)
                fl_pair = fl_idx_map.get(fl_idx)
                gen = gen_idx_map.get(g_idx)
                if any(x is None for x in [year, prkg, fl_pair, gen]):
                    continue
                if tv_id is None:
                    continue
                breaks_rail_s[(year, prkg, tv_id, fl_pair, gen)] = float(line[sep_idx+2:])

        print(f'  OK   breaks+rail: {len(breaks_rail_s)} entries')

        breaks_rail_border = {}
        for y in MODELED_YEARS:
            by_c = defaultdict(float)
            for key, val in breaks_rail_s.items():
                year, (prod, odpair, path, geo_elem), tv_id, (fuel_id, fl_type), gen = key
                if year != y or tv_id != 1 or fuel_id != 0 or val <= 0:
                    continue
                nuts2 = node_to_border.get(geo_elem)
                if nuts2:
                    by_c[nuts2[:2]] += val
            breaks_rail_border[y] = dict(by_c)

        rail_border_by_country['rail_breaks'] = breaks_rail_border
        rail_s_scenarios['rail_breaks'] = {'label': 'Breaks\nconstraint', 'type': 'breaks'}
        print(f'  Added rail_breaks to rail_border_by_country')
    else:
        print('  SKIP: no s_dict files')
else:
    print('  SKIP: directory not found')

# === Summary ===
print(f'\n{"":>28s}  {"AT":>6s}  {"DE":>6s}  {"IT":>6s}  {"Total":>6s}')
for label, data, scens in [("Reference", all_border_by_country, all_s_scenarios),
                            ("With shift to rail", rail_border_by_country, rail_s_scenarios)]:
    print(f"--- {label} ---")
    for sid in scens:
        if sid not in data: continue
        d = data[sid].get(2040, {})
        lbl = scens[sid]['label'].replace('\n', ' ')
        print(f"  {lbl:>26s}: {d.get('AT',0)/1000:>6.0f}  {d.get('DE',0)/1000:>6.0f}  {d.get('IT',0)/1000:>6.0f}  {sum(d.values())/1000:>6.0f}")

# === Generate figure with larger fonts ===
print("\n=== Generating 3-year figure ===")

fig, axes = plt.subplots(6, 1, figsize=(14, 28))

COUNTRY_COLORS = {'AT': '#E63946', 'DE': '#2A9D8F', 'IT': '#457B9D'}
COUNTRY_LABELS = {'AT': 'Austria', 'DE': 'Germany', 'IT': 'Italy'}
country_order = ['AT', 'DE', 'IT']
width = 0.55

years = [2032, 2040, 2048]

row_templates = [
    ('Reference',
     ['baseline', 'breaks', 'fixed_fleet', 'at_elec_low', 'at_elec_med', 'at_elec_high',
      'at_network_low', 'at_network_med', 'at_network_high'],
     all_border_by_country,
     ['Baseline', 'Breaks', 'Fixed fleet',
      '+1ct/kWh', '+2ct/kWh', '+4ct/kWh',
      '+2/kW/yr', '+5/kW/yr', '+10/kW/yr']),
    ('With shift to rail',
     ['rail_baseline', 'rail_breaks', 'rail_elec_low', 'rail_elec_med', 'rail_elec_high',
      'rail_network_low', 'rail_network_med', 'rail_network_high'],
     rail_border_by_country,
     ['Baseline', 'Breaks',
      '+1ct/kWh', '+2ct/kWh', '+4ct/kWh',
      '+2/kW/yr', '+5/kW/yr', '+10/kW/yr']),
]

ax_idx = 0
for yr in years:
    for mode_label, scen_ids, border_data, xlabels in row_templates:
        ax = axes[ax_idx]
        available = [s for s in scen_ids if s in border_data]
        x = np.arange(len(available))
        bottom = np.zeros(len(available))

        # Build matching xlabels for available scenarios
        available_labels = []
        for s in scen_ids:
            if s in border_data:
                idx = scen_ids.index(s)
                available_labels.append(xlabels[idx] if idx < len(xlabels) else s)

        for c in country_order:
            vals = np.array([border_data[s].get(yr, {}).get(c, 0) / 1000
                             for s in available])
            ax.bar(x, vals, width, bottom=bottom, label=COUNTRY_LABELS[c],
                   color=COUNTRY_COLORS[c], edgecolor='black', linewidth=0.5)
            bottom += vals

        # Separators between reference, elec, network groups
        ref_ids = {'baseline', 'breaks', 'fixed_fleet', 'rail_baseline', 'rail_breaks'}
        ref_end = sum(1 for s in available if s in ref_ids)
        elec_end = ref_end + sum(1 for s in available if 'elec' in s)
        if ref_end > 0 and ref_end < len(available):
            ax.axvline(x=ref_end - 0.5, color='gray', ls='--', alpha=0.5, lw=1)
        if elec_end > 0 and elec_end < len(available):
            ax.axvline(x=elec_end - 0.5, color='gray', ls=':', alpha=0.4, lw=1)

        ax.set_xticks(x)
        ax.set_xticklabels(available_labels, fontsize=26, rotation=45, ha='right')
        ax.tick_params(axis='y', labelsize=26)
        ax.set_ylim(0, max(bottom) * 1.08)
        ax.grid(axis='y', alpha=0.3)

        ax.set_ylabel('GWh', fontsize=28)
        ax.set_title(f'{yr} --- {mode_label}', fontsize=32, fontweight='bold')

        ax_idx += 1

from matplotlib.patches import Patch
handles = [Patch(facecolor=COUNTRY_COLORS[c], edgecolor='black', label=COUNTRY_LABELS[c])
           for c in country_order]
plt.tight_layout()
# Place legend inside the first (top) subplot's upper-right corner
axes[0].legend(handles=handles, loc='upper right', fontsize=22,
               title='Country', title_fontsize=22,
               frameon=True, edgecolor='#ccc', ncol=1)
MANUSCRIPT_IMG = BASE_PATH.parent.parent / 'manuscript' / 'images'
plt.savefig(str(BASE_PATH / 'figures' / 'at_surcharge_border_charging_reallocation_3years.pdf'), bbox_inches='tight')
plt.savefig(str(BASE_PATH / 'figures' / 'at_surcharge_border_charging_reallocation_3years.svg'), bbox_inches='tight')
if MANUSCRIPT_IMG.exists():
    plt.savefig(str(MANUSCRIPT_IMG / 'at_surcharge_border_charging_reallocation_3years.pdf'), bbox_inches='tight')
print("Saved C.22 (reallocation 3-year figure).")

# ============================================================================
# C.23: Charging intensity choropleth map (3-year version)
# ============================================================================
print("\n=== Generating C.23: charging intensity border map ===")

import geopandas as gpd
import matplotlib.cm as cm
import matplotlib.patheffects
from matplotlib.colors import Normalize
import matplotlib.gridspec as gridspec
from mpl_toolkits.axes_grid1 import make_axes_locatable

# Load NUTS-2 shapefile
nuts_shp_path = BASE_PATH / 'data' / 'NUTS_RG_20M_2021_4326.shp' / 'NUTS_RG_20M_2021_4326.shp'
nuts_gdf = gpd.read_file(nuts_shp_path)
nuts2_gdf = nuts_gdf[nuts_gdf['LEVL_CODE'] == 2].copy()

# Area calculation
nuts2_proj = nuts2_gdf.to_crs('EPSG:3035')
nuts2_proj['area_km2'] = nuts2_proj.geometry.area / 1e6
nuts2_gdf = nuts2_gdf.merge(
    nuts2_proj[['NUTS_ID', 'area_km2']].drop_duplicates('NUTS_ID'),
    on='NUTS_ID', how='left'
)

CORRIDOR_COUNTRIES = {'NO', 'SE', 'DK', 'DE', 'AT', 'IT', 'FI'}
corridor_nuts2 = nuts2_gdf[nuts2_gdf['CNTR_CODE'].isin(CORRIDOR_COUNTRIES)].copy()

# Highway km
highway_df = pd.read_csv(BASE_PATH / 'highway_km_per_nuts2.csv')
highway_by_nuts2 = dict(zip(highway_df['NUTS2_CODE'], highway_df['highway_km']))

# Country boundaries
nuts0 = nuts_gdf[nuts_gdf['LEVL_CODE'] == 0].copy()
corridor_countries_gdf = nuts0[nuts0['CNTR_CODE'].isin(CORRIDOR_COUNTRIES)]

# Merge highway into corridor gdf
corridor_with_hw = corridor_nuts2.merge(
    highway_df.rename(columns={'NUTS2_CODE': 'NUTS_ID'}),
    on='NUTS_ID', how='left'
)

print(f"Corridor NUTS-2 regions: {len(corridor_nuts2)}")
print(f"Highway data available: {len(highway_by_nuts2)} regions")

# Aggregate BEV charging by NUTS-2
def aggregate_s_by_nuts2(s_dict, years_list):
    result = {y: defaultdict(float) for y in years_list}
    for key, val in s_dict.items():
        year, (prod, odpair, path, geo_elem), tv_id, (fuel_id, fl_type), gen = key
        if year not in result or tv_id != 1 or fuel_id != 0 or val <= 0:
            continue
        nuts2 = geoid_to_nuts2.get(geo_elem, '')
        if nuts2:
            result[year][nuts2] += val / 1000  # convert to MWh
    return {y: dict(v) for y, v in result.items()}

# Build road_all_s dict combining all loaded s_dicts
road_all_s = dict(all_s_dicts)
if 'breaks_s' in dir():
    road_all_s['breaks'] = breaks_s

# Scenarios to plot: baseline, breaks, +0.04 EUR/kWh, +10 EUR/kW/yr
map_years = [2032, 2040, 2048]
map_scenarios = {}
if 'baseline' in road_all_s:
    map_scenarios['Baseline'] = road_all_s['baseline']
if 'breaks' in road_all_s:
    map_scenarios['Breaks'] = road_all_s['breaks']
if 'at_elec_high' in road_all_s:
    map_scenarios['+0.04 EUR/kWh'] = road_all_s['at_elec_high']
if 'at_network_high' in road_all_s:
    map_scenarios['+10 EUR/kW/yr'] = road_all_s['at_network_high']

energy_by_nuts2 = {}
for name, sd in map_scenarios.items():
    energy_by_nuts2[name] = aggregate_s_by_nuts2(sd, map_years)
    for y in map_years:
        total = sum(energy_by_nuts2[name][y].values())
        print(f"  {name:>18s} {y}: {total:,.0f} MWh across {len(energy_by_nuts2[name][y])} regions")

scen_names = list(map_scenarios.keys())
XLIM = (8.5, 16.5)
YLIM = (44.5, 49.5)

border_area_gdf = corridor_with_hw[
    (corridor_with_hw.geometry.centroid.y >= YLIM[0] - 1) &
    (corridor_with_hw.geometry.centroid.y <= YLIM[1] + 1) &
    (corridor_with_hw.geometry.centroid.x >= XLIM[0] - 1) &
    (corridor_with_hw.geometry.centroid.x <= XLIM[1] + 1)
].copy()

# === 3-year version with larger fonts ===
fig = plt.figure(figsize=(22, 19))
gs = gridspec.GridSpec(4, 4, height_ratios=[1, 1, 1, 0.05], wspace=0.05, hspace=0.15)

for si, sn in enumerate(scen_names):
    col_vmax = 0
    for yr in map_years:
        for nuts2, mwh in energy_by_nuts2[sn][yr].items():
            hw = highway_by_nuts2.get(nuts2, 0)
            if hw > 0:
                col_vmax = max(col_vmax, mwh / hw)

    for yi, yr in enumerate(map_years):
        ax = fig.add_subplot(gs[yi, si])
        intensity = {}
        for nuts2, mwh in energy_by_nuts2[sn][yr].items():
            hw = highway_by_nuts2.get(nuts2, 0)
            intensity[nuts2] = mwh / hw if hw > 0 else 0
        int_df = pd.DataFrame([{'nuts2': n, 'intensity': v} for n, v in intensity.items()])
        plot_gdf = border_area_gdf.merge(int_df, left_on='NUTS_ID', right_on='nuts2', how='left')
        plot_gdf['intensity'] = plot_gdf['intensity'].fillna(0)
        corridor_countries_gdf.plot(ax=ax, color='#f5f5f5', edgecolor='#999', linewidth=0.8)
        plot_gdf.plot(ax=ax, column='intensity', cmap='YlOrRd', edgecolor='black', linewidth=0.6,
                      vmin=0, vmax=col_vmax, legend=False)
        # Only label countries on the first row
        if yi == 0:
            # Compute average centroid per country from border regions
            country_centroids = defaultdict(lambda: [0, 0, 0])
            for idx_r, row in plot_gdf.iterrows():
                if row['NUTS_ID'] in SOUTHERN_BORDER_REGIONS:
                    c = row['NUTS_ID'][:2]
                    cx, cy = row.geometry.centroid.x, row.geometry.centroid.y
                    country_centroids[c][0] += cx
                    country_centroids[c][1] += cy
                    country_centroids[c][2] += 1
            for c, (sx, sy, n) in country_centroids.items():
                if n > 0:
                    ax.annotate(c, xy=(sx/n, sy/n),
                                ha='center', va='center', fontsize=22, fontweight='bold',
                                color='black', path_effects=[
                                    matplotlib.patheffects.withStroke(linewidth=4, foreground='white')])
        ax.set_xlim(*XLIM); ax.set_ylim(*YLIM); ax.tick_params(labelsize=18)
        if yi == 0: ax.set_title(sn, fontweight='bold', fontsize=28)
        if si == 0: ax.set_ylabel(f'{yr}', fontweight='bold', fontsize=28, labelpad=10)
        else: ax.set_yticklabels([])
        if yi < 2: ax.set_xticklabels([])
    cax = fig.add_subplot(gs[3, si])
    sm = cm.ScalarMappable(cmap='YlOrRd', norm=Normalize(vmin=0, vmax=col_vmax))
    sm.set_array([])
    cbar = fig.colorbar(sm, cax=cax, orientation='horizontal')
    cbar.set_label('GWh / highway-km', fontsize=22); cbar.ax.tick_params(labelsize=18)

fig.suptitle('Charging demand intensity at DE-AT-IT border (2032, 2040, 2048)', fontweight='bold', fontsize=30)
plt.savefig(str(BASE_PATH / 'figures' / 'at_surcharge_charging_intensity_border_3years.pdf'), bbox_inches='tight')
plt.savefig(str(BASE_PATH / 'figures' / 'at_surcharge_charging_intensity_border_3years.svg'), bbox_inches='tight')
if MANUSCRIPT_IMG.exists():
    plt.savefig(str(MANUSCRIPT_IMG / 'at_surcharge_charging_intensity_border_3years.pdf'), bbox_inches='tight')
print("Saved C.23 (intensity 3-year figure).")

# === 2032-only version (main text) with larger fonts ===
yr_single = 2032
fig2, axes2 = plt.subplots(1, 4, figsize=(22, 6))

for si, sn in enumerate(scen_names):
    ax = axes2[si]
    col_vmax = 0
    for nuts2, mwh in energy_by_nuts2[sn][yr_single].items():
        hw = highway_by_nuts2.get(nuts2, 0)
        if hw > 0:
            col_vmax = max(col_vmax, mwh / hw)

    intensity = {}
    for nuts2, mwh in energy_by_nuts2[sn][yr_single].items():
        hw = highway_by_nuts2.get(nuts2, 0)
        intensity[nuts2] = mwh / hw if hw > 0 else 0
    int_df = pd.DataFrame([{'nuts2': n, 'intensity': v} for n, v in intensity.items()])
    plot_gdf = border_area_gdf.merge(int_df, left_on='NUTS_ID', right_on='nuts2', how='left')
    plot_gdf['intensity'] = plot_gdf['intensity'].fillna(0)
    corridor_countries_gdf.plot(ax=ax, color='#f5f5f5', edgecolor='#999', linewidth=0.8)
    plot_gdf.plot(ax=ax, column='intensity', cmap='YlOrRd', edgecolor='black', linewidth=0.6,
                  vmin=0, vmax=col_vmax, legend=False)
    # Country labels only
    country_centroids_mt = defaultdict(lambda: [0, 0, 0])
    for idx_r, row in plot_gdf.iterrows():
        if row['NUTS_ID'] in SOUTHERN_BORDER_REGIONS:
            c = row['NUTS_ID'][:2]
            cx, cy = row.geometry.centroid.x, row.geometry.centroid.y
            country_centroids_mt[c][0] += cx
            country_centroids_mt[c][1] += cy
            country_centroids_mt[c][2] += 1
    for c, (sx, sy, n) in country_centroids_mt.items():
        if n > 0:
            ax.annotate(c, xy=(sx/n, sy/n),
                        ha='center', va='center', fontsize=20, fontweight='bold',
                        color='black', path_effects=[
                            matplotlib.patheffects.withStroke(linewidth=3, foreground='white')])
    ax.set_xlim(*XLIM); ax.set_ylim(*YLIM); ax.tick_params(labelsize=18)
    ax.set_title(sn, fontweight='bold', fontsize=24)
    if si > 0: ax.set_yticklabels([])

    divider = make_axes_locatable(ax)
    cax = divider.append_axes('bottom', size='5%', pad=0.1)
    sm = cm.ScalarMappable(cmap='YlOrRd', norm=Normalize(vmin=0, vmax=col_vmax))
    sm.set_array([])
    cbar = fig2.colorbar(sm, cax=cax, orientation='horizontal')
    cbar.set_label('GWh / highway-km', fontsize=20); cbar.ax.tick_params(labelsize=18)

fig2.suptitle(f'Charging demand intensity at DE-AT-IT border -- {yr_single}', fontweight='bold', fontsize=26)
plt.tight_layout()
plt.savefig(str(BASE_PATH / 'figures' / 'at_surcharge_charging_intensity_border.pdf'), bbox_inches='tight')
plt.savefig(str(BASE_PATH / 'figures' / 'at_surcharge_charging_intensity_border.svg'), bbox_inches='tight')
if MANUSCRIPT_IMG.exists():
    plt.savefig(str(MANUSCRIPT_IMG / 'at_surcharge_charging_intensity_border.pdf'), bbox_inches='tight')
print("Saved main text intensity figure.")
