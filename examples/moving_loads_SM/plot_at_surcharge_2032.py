"""
Standalone script: BEV charging reallocation in DE-AT-IT border regions (2032 only).

Produces a 2-row stacked bar chart:
  Row 1: Road-only scenarios
  Row 2: Road+Rail scenarios

Each row has 8 bars:
  Reference | Breaks-only | +0.01 EUR/kWh | +0.02 EUR/kWh | +0.04 EUR/kWh |
  +2 EUR/kW/yr | +5 EUR/kW/yr | +10 EUR/kW/yr

Output:
  figures/at_surcharge_border_charging_reallocation_2032.pdf
  figures/at_surcharge_border_charging_reallocation_2032.svg
"""

import sys
import re
import ast
import time
import yaml
import numpy as np
import matplotlib
matplotlib.use('Agg')   # non-interactive backend for faster saving
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from pathlib import Path
from collections import defaultdict

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)

t0 = time.time()

# ============================================================================
# CONFIGURATION
# ============================================================================
BASE_PATH = Path(__file__).resolve().parent
INPUT_PATH = BASE_PATH / 'input_data' / 'fixed_nuts_2'
FIGURES_PATH = BASE_PATH / 'figures'
FIGURES_PATH.mkdir(exist_ok=True)

MODELED_YEARS = list(range(2020, 2064, 4))
TARGET_YEAR = 2032

# Border NUTS-2 regions (DE-AT-IT intersection)
SOUTHERN_BORDER_REGIONS = {
    'AT33', 'AT34',                      # Austria: Tyrol, Vorarlberg
    'ITC4', 'ITH1', 'ITH2', 'ITH3',     # Italy: Lombardy, Bolzano, Trento, Veneto
    'DE14', 'DE21', 'DE27',              # Germany: Tuebingen, Oberbayern, Schwaben
}

# Country colors
COUNTRY_COLORS = {'AT': '#E63946', 'DE': '#2A9D8F', 'IT': '#457B9D'}
COUNTRY_LABELS = {'AT': 'Austria', 'DE': 'Germany', 'IT': 'Italy'}
COUNTRY_ORDER = ['AT', 'DE', 'IT']

# Index mappings shared across CartesianIndex files
CI_RE = re.compile(r'CartesianIndex\((\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\)')
YEAR_IDX_MAP = {i + 1: y for i, y in enumerate(MODELED_YEARS)}
# Reverse: which y_idx corresponds to TARGET_YEAR?
TARGET_Y_IDX = None
for k, v in YEAR_IDX_MAP.items():
    if v == TARGET_YEAR:
        TARGET_Y_IDX = k
        break

FL_IDX_MAP = {1: (0, 1), 2: (0, 2), 3: (1, 0)}
GEN_LIST = list(range(2008, 2064, 4))
GEN_IDX_MAP = {i + 1: g for i, g in enumerate(GEN_LIST)}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
def load_yaml(filepath):
    """Load YAML with UnsafeLoader (handles numpy scalars in Path.yaml)."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return yaml.load(f, Loader=yaml.UnsafeLoader)


def find_latest_result_file(folder, variable):
    """Find the latest result file for a given variable in a folder."""
    folder = Path(folder)
    pattern = f'*_{variable}_dict.yaml'
    files = list(folder.glob(pattern))
    if not files:
        return None
    return max(files, key=lambda x: x.stat().st_mtime)


def load_tuple_s_dict_fast(folder, target_year, border_node_ids):
    """
    Load s_dict in tuple format, filtering for BEV charging (tv_id=1, fuel_id=0)
    at target_year and border nodes only. Returns {country: total_kWh}.

    This avoids loading the entire 100MB+ file into memory via yaml.safe_load.
    Lines look like: (2032, (0, 1655, 1655, 21), 1, (0, 1), 2044): "0.002234"
    """
    s_file = find_latest_result_file(folder, 's')
    if s_file is None:
        raise FileNotFoundError(f'No s_dict found in {folder}')

    # Fast prefix filter: only parse lines starting with target year
    year_prefix = f'({target_year},'

    by_country = defaultdict(float)
    count = 0
    matched = 0

    with open(s_file, 'r') as f:
        for line in f:
            count += 1
            if not line.startswith(year_prefix):
                continue
            # Parse the line
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
            if geo_elem in border_node_ids:
                country = border_node_ids[geo_elem]
                by_country[country] += val
                matched += 1

    print(f'  Scanned {count:,} lines, {matched} border BEV entries -> {s_file.name}')
    return dict(by_country)


def build_prkg_set(odpair_data, path_by_id):
    """Build sorted list of (prod, odpair, path, geo_elem) tuples."""
    prkg = set()
    for o in odpair_data:
        odpair_id = o['id']
        path_id = o.get('path_id', odpair_id)
        p = path_by_id.get(path_id)
        if p:
            for geo_id in p.get('sequence', []):
                prkg.add((0, int(odpair_id), int(path_id), int(geo_id)))
    return sorted(prkg)


def decode_cartesian_border_only(filepath, prkg_idx_map, tv_idx_map,
                                  target_y_idx, bev_tv_idx_list,
                                  border_node_ids):
    """
    Decode CartesianIndex s_dict, filtering for target year + BEV + border nodes.
    Returns: {country: total_kWh}

    bev_tv_idx_list: list of tv_idx values that map to BEV (tv_id=1).
    For road: [2], for rail with 3 TVs: [2].
    """
    # BEV electric fuel: fl_idx in {1, 2} -> (0, 1) or (0, 2)
    bev_fl_idxs = {1, 2}  # both are electric (fuel_id=0)

    by_country = defaultdict(float)
    count = 0
    matched = 0

    # Pre-filter string for fast skip
    target_prefix = f'CartesianIndex({target_y_idx},'

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

            # Filter: must be BEV tech vehicle AND electric fuel
            if tv_idx not in bev_tv_idx_list:
                continue
            if fl_idx not in bev_fl_idxs:
                continue

            val = float(val_str)
            if val <= 0:
                continue

            # Look up the geo_elem from the prkg index
            prkg = prkg_idx_map.get(prkg_idx)
            if prkg is None:
                continue
            geo_elem = prkg[3]  # (prod, odpair, path, geo_elem)

            if geo_elem in border_node_ids:
                by_country[border_node_ids[geo_elem]] += val
                matched += 1

    print(f'  Scanned {count:,} lines, {matched} border BEV entries -> {Path(filepath).name}')
    return dict(by_country)


# ============================================================================
# LOAD GEOGRAPHIC DATA -> node_to_border mapping
# ============================================================================
print('Loading geographic data...')
geo_data = load_yaml(INPUT_PATH / 'GeographicElement.yaml')
geoid_to_nuts2 = {}
for g in geo_data:
    if g.get('type') == 'node':
        gid = int(g['id'])
        nuts2 = g.get('nuts2_region', '')
        if nuts2:
            geoid_to_nuts2[gid] = nuts2

node_to_border = {
    nid: nuts2 for nid, nuts2 in geoid_to_nuts2.items()
    if nuts2 in SOUTHERN_BORDER_REGIONS
}
# Map node_id -> country code (for fast lookup)
border_node_to_country = {
    nid: nuts2[:2] for nid, nuts2 in node_to_border.items()
}
print(f'  Border nodes: {len(node_to_border)}')
print(f'  Time: {time.time()-t0:.1f}s')


# ============================================================================
# LOAD ROAD-ONLY SCENARIOS
# ============================================================================

# --- Load Julia's prkg ordering for road scenarios ---
print('\n=== Loading prkg ordering ===')
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
    road_prkg_idx_map = _prkg_from_file
    print(f'  Loaded prkg ordering from Julia: {len(road_prkg_idx_map)} entries')
else:
    print('  WARNING: prkg_ordering_elsevier.txt not found, falling back to Python sorted')
    road_002_input = BASE_PATH / 'input_data' / 'uncertainty_scenarios' / 'scenario_002'
    odpair_002 = load_yaml(road_002_input / 'Odpair.yaml')
    path_002 = load_yaml(road_002_input / 'Path.yaml')
    path_002_by_id = {p['id']: p for p in path_002}
    road_prkg_sorted = build_prkg_set(odpair_002, path_002_by_id)
    road_prkg_idx_map = {i + 1: t for i, t in enumerate(road_prkg_sorted)}

# --- Road baseline (CartesianIndex, v2 re-run with sorted prkg) ---
print('\n=== Loading road baseline (scenario_002, v2) ===')
road_baseline_border = decode_cartesian_border_only(
    BASE_PATH / 'results' / 'uncertainty_scenarios_v2' / 'scenario_002'
    / 'scenario_002_cs_2026-02-14_22-18-02_s_dict.yaml',
    road_prkg_idx_map,
    {1: 0, 2: 1},  # tv_idx_map (not used directly here)
    TARGET_Y_IDX,
    [2],  # BEV is tv_idx=2 for road
    border_node_to_country,
)
print(f'  Time: {time.time()-t0:.1f}s')

# --- Road breaks (CartesianIndex, Feb 14) ---
print('\n=== Loading road breaks (scenario_002_breaks, CartesianIndex) ===')
road_breaks_border = decode_cartesian_border_only(
    BASE_PATH / 'results' / 'uncertainty_scenarios_breaks_only' / 'scenario_002'
    / 'scenario_002_cs_2026-02-14_23-47-28_s_dict.yaml',
    road_prkg_idx_map,
    {1: 0, 2: 1},
    TARGET_Y_IDX,
    [2],
    border_node_to_country,
)
print(f'  Time: {time.time()-t0:.1f}s')

# --- Road surcharges (tuple format, fast line-by-line) ---
print('\n=== Loading road surcharge scenarios (tuple format, fast) ===')
ROAD_SURCHARGE_PATH = BASE_PATH / 'results' / 'at_surcharge'
road_surcharge_ids = [
    'at_elec_low', 'at_elec_med', 'at_elec_high',
    'at_network_low', 'at_network_med', 'at_network_high',
]
road_surcharge_border = {}
for sid in road_surcharge_ids:
    print(f'  Loading {sid}...')
    road_surcharge_border[sid] = load_tuple_s_dict_fast(
        ROAD_SURCHARGE_PATH / sid, TARGET_YEAR, border_node_to_country
    )
    print(f'  Time: {time.time()-t0:.1f}s')


# ============================================================================
# LOAD ROAD+RAIL SCENARIOS
# ============================================================================

# --- Rail baseline (CartesianIndex, Feb 14 — sorted prkg) ---
print('\n=== Loading rail baseline (scenario_016, CartesianIndex, Feb 14) ===')
rail_016_input = BASE_PATH / 'input_data' / 'uncertainty_scenarios_rail' / 'scenario_016'
rail_odpair = load_yaml(rail_016_input / 'Odpair.yaml')
rail_path = load_yaml(rail_016_input / 'Path.yaml')
rail_path_by_id = {p['id']: p for p in rail_path}
rail_prkg_sorted = build_prkg_set(rail_odpair, rail_path_by_id)
rail_prkg_idx_map = {i + 1: t for i, t in enumerate(rail_prkg_sorted)}
print(f'  p_r_k_g entries: {len(rail_prkg_sorted)}')

rail_baseline_border = decode_cartesian_border_only(
    BASE_PATH / 'results' / 'rail' / 'scenario_016'
    / 'scenario_016_cs_2026-02-14_22-16-25_s_dict.yaml',
    rail_prkg_idx_map,
    {1: 0, 2: 1},
    TARGET_Y_IDX,
    [2],  # BEV is tv_idx=2 for Feb 14 runs
    border_node_to_country,
)
print(f'  Time: {time.time()-t0:.1f}s')

# --- Rail breaks (CartesianIndex) ---
print('\n=== Loading rail breaks (scenario_016 breaks, CartesianIndex) ===')
# Check for Feb 14 breaks file first
_rail_brk_path_v2 = (BASE_PATH / 'results' / 'uncertainty_scenarios_breaks_only' / 'scenario_016'
                     / 'scenario_016_cs_2026-02-14_23-47-28_s_dict.yaml')
_rail_brk_path_old = (BASE_PATH / 'results' / 'uncertainty_scenarios_breaks_only' / 'scenario_016'
                      / 'scenario_016_cs_2026-01-06_16-17-00_s_dict.yaml')
_rail_brk_path = _rail_brk_path_v2 if _rail_brk_path_v2.exists() else _rail_brk_path_old
print(f'  Using: {_rail_brk_path.name}')
rail_breaks_border = decode_cartesian_border_only(
    _rail_brk_path,
    rail_prkg_idx_map,
    {1: 0, 2: 1},
    TARGET_Y_IDX,
    [2],  # BEV is tv_idx=2
    border_node_to_country,
)
print(f'  Time: {time.time()-t0:.1f}s')

# --- Rail surcharges (tuple format, fast line-by-line) ---
print('\n=== Loading rail surcharge scenarios (tuple format, fast) ===')
RAIL_SURCHARGE_PATH = BASE_PATH / 'results' / 'at_surcharge_rail'
rail_surcharge_ids = [
    'at_elec_low', 'at_elec_med', 'at_elec_high',
    'at_network_low', 'at_network_med', 'at_network_high',
]
rail_surcharge_border = {}
for sid in rail_surcharge_ids:
    print(f'  Loading rail {sid}...')
    rail_surcharge_border[sid] = load_tuple_s_dict_fast(
        RAIL_SURCHARGE_PATH / sid, TARGET_YEAR, border_node_to_country
    )
    print(f'  Time: {time.time()-t0:.1f}s')


# ============================================================================
# COLLECT BORDER DATA INTO UNIFIED DICTS
# ============================================================================
road_border = {}
road_border['baseline'] = road_baseline_border
road_border['breaks'] = road_breaks_border
for sid in road_surcharge_ids:
    road_border[sid] = road_surcharge_border[sid]

rail_border = {}
rail_border['rail_baseline'] = rail_baseline_border
rail_border['rail_breaks'] = rail_breaks_border
for sid in rail_surcharge_ids:
    rail_border['rail_' + sid] = rail_surcharge_border[sid]


# ============================================================================
# PRINT SUMMARY
# ============================================================================
print(f"\n{'Scenario':>28s}  {'AT':>8s}  {'DE':>8s}  {'IT':>8s}  {'Total':>8s}")
print('--- Road-only ---')
for sid in ['baseline', 'breaks'] + road_surcharge_ids:
    d = road_border[sid]
    at = d.get('AT', 0) / 1000
    de = d.get('DE', 0) / 1000
    it = d.get('IT', 0) / 1000
    print(f'{sid:>28s}:  {at:>8.0f}  {de:>8.0f}  {it:>8.0f}  {at+de+it:>8.0f}')
print('--- Road+Rail ---')
for sid in ['rail_baseline', 'rail_breaks'] + ['rail_' + s for s in rail_surcharge_ids]:
    d = rail_border[sid]
    at = d.get('AT', 0) / 1000
    de = d.get('DE', 0) / 1000
    it = d.get('IT', 0) / 1000
    print(f'{sid:>28s}:  {at:>8.0f}  {de:>8.0f}  {it:>8.0f}  {at+de+it:>8.0f}')


# ============================================================================
# PLOT: 2-row stacked bar chart
# ============================================================================
print('\n=== Generating figure ===')

plt.rcParams.update(plt.rcParamsDefault)
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "serif",
    "font.serif": "mathpazo",
    'font.size': 14,
    'axes.labelsize': 14,
})

MANUSCRIPT_IMG = Path(BASE_PATH).parent.parent / 'manuscript' / 'images'

fig, ax = plt.subplots(1, 1, figsize=(11, 4.5))

width = 0.55

scen_ids = ['baseline',
            'at_elec_low', 'at_elec_med', 'at_elec_high',
            'at_network_low', 'at_network_med', 'at_network_high']
xlabels = ['Reference',
           '+0.01\nEUR/kWh', '+0.02\nEUR/kWh', '+0.04\nEUR/kWh',
           '+2\nEUR/kW/yr', '+5\nEUR/kW/yr', '+10\nEUR/kW/yr']

available = [s for s in scen_ids if s in road_border]
x = np.arange(len(available))
bottom = np.zeros(len(available))

for c in COUNTRY_ORDER:
    vals = np.array([road_border[s].get(c, 0) / 1000
                     for s in available])
    ax.bar(x, vals, width, bottom=bottom, label=COUNTRY_LABELS[c],
           color=COUNTRY_COLORS[c], edgecolor='black', linewidth=0.5)
    for i, v in enumerate(vals):
        if v > 20:
            ax.text(x[i], bottom[i] + v / 2, f'{v:,.0f}',
                    ha='center', va='center', fontsize=12,
                    color='white')
    bottom += vals

# Total labels on top
for i in range(len(available)):
    ax.text(x[i], bottom[i] + 5, f'{bottom[i]:,.0f}',
            ha='center', va='bottom', fontsize=12, color='#555')

# Vertical separators
ax.axvline(x=0.5, color='gray', ls='--', alpha=0.5, lw=1)
ax.axvline(x=3.5, color='gray', ls=':', alpha=0.4, lw=1)

# Group labels
y_top = max(bottom) * 1.08 if max(bottom) > 0 else 10
ax.text(0, y_top, 'Reference', ha='center', fontsize=12,
        fontstyle='italic', color='#888')
ax.text(2, y_top, 'Electricity surcharges', ha='center', fontsize=12,
        fontstyle='italic', color='#888')
ax.text(5, y_top, 'Network fee surcharges', ha='center', fontsize=12,
        fontstyle='italic', color='#888')

ax.set_xticks(x)
ax.set_xticklabels(xlabels[:len(available)], fontsize=13)
ax.set_ylabel('BEV charging in\nborder regions (GWh)')
ax.set_ylim(0, max(max(bottom) * 1.18, 1))
ax.grid(axis='y', alpha=0.3)

# Legend (upper right)
handles = [Patch(facecolor=COUNTRY_COLORS[c], edgecolor='black',
                 label=COUNTRY_LABELS[c]) for c in COUNTRY_ORDER]
ax.legend(handles=handles, loc='upper center', fontsize=13,
          frameon=True, edgecolor='#ccc', ncol=3,
          bbox_to_anchor=(0.5, 1.18))

fig.suptitle(
    f'BEV charging reallocation in DE--AT--IT border regions --- {TARGET_YEAR}',
    fontsize=16, y=1.08
)
plt.tight_layout()

# Save
fname = 'at_surcharge_border_charging_reallocation_2032'
for dst in [FIGURES_PATH, MANUSCRIPT_IMG]:
    fig.savefig(dst / f'{fname}.pdf', bbox_inches='tight')
fig.savefig(FIGURES_PATH / f'{fname}.svg', bbox_inches='tight')
print(f'\nSaved: figures/{fname}.pdf')
print(f'Saved: figures/{fname}.svg')
plt.close()
print(f'Done. Total time: {time.time()-t0:.1f}s')
