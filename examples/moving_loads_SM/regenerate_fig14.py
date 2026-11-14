"""
Regenerate Figure 14: Rail share of freight volume (%) heatmap — Go RES, 2048.
Single panel (left panel of original 2-panel figure).
Font: mathpazo (Palatino), matching Figure 13.
"""

import ast
import re
import yaml
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from pathlib import Path

# ── Font settings ─────────────────────────────────────────────────────
plt.rcParams.update(plt.rcParamsDefault)
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "serif",
    "font.serif": "mathpazo",
    "font.size": 16,
})

# ── Paths ─────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = BASE_DIR / 'results'
INPUT_DIR = BASE_DIR / 'input_data'
FIG_DIR = BASE_DIR / 'figures'
MANUSCRIPT_IMG = BASE_DIR.parent.parent / 'manuscript' / 'images'

TARGET_YEAR = 2048
COUNTRIES = ['NO', 'FI', 'SE', 'DK', 'DE', 'AT', 'IT']

# ── Go RES rail scenario config ──────────────────────────────────────
RAIL_DIR = RESULTS_DIR / 'rail' / 'scenario_004'
RAIL_PREFIX = 'scenario_004_cs_2026-02-14_20-52-20'
INPUT_RAIL = INPUT_DIR / 'uncertainty_scenarios_rail' / 'scenario_000'


# ── Loading functions ────────────────────────────────────────────────
def load_yaml(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def load_f_dict(results_dir, prefix):
    fpath = results_dir / f'{prefix}_f_dict.yaml'
    raw = load_yaml(fpath)
    parsed = {}
    for k, v in raw.items():
        try:
            key = ast.literal_eval(k)
        except (ValueError, SyntaxError):
            continue
        parsed[key] = float(v)
    return parsed


def load_input_data(input_dir):
    geo_data = load_yaml(input_dir / 'GeographicElement.yaml')
    odpair_data = load_yaml(input_dir / 'Odpair.yaml')
    path_data = load_yaml(input_dir / 'Path.yaml')

    geo_by_id = {}
    for g in geo_data:
        gid = g['id']
        geo_by_id[gid] = {
            'coordinate_lat': g.get('coordinate_lat', 0),
            'coordinate_lon': g.get('coordinate_lon', 0),
            'country': g.get('nuts2_region', '??')[:2] if g.get('nuts2_region') else '??',
        }

    odpair_by_id = {}
    for o in odpair_data:
        odpair_by_id[o['id']] = {'from': o['from'], 'to': o['to']}

    path_by_id = {}
    for p in path_data:
        path_by_id[p['id']] = {'length': p.get('length', 0)}

    return {'geo_by_id': geo_by_id, 'odpair_by_id': odpair_by_id, 'path_by_id': path_by_id}


# ── Load data ────────────────────────────────────────────────────────
print('Loading input data...')
input_data = load_input_data(INPUT_RAIL)
print(f'  {len(input_data["geo_by_id"])} geo elements, '
      f'{len(input_data["odpair_by_id"])} OD pairs, '
      f'{len(input_data["path_by_id"])} paths')

print('Loading f_dict...')
f_dict = load_f_dict(RAIL_DIR, RAIL_PREFIX)
print(f'  {len(f_dict):,} flow entries')

# ── Build country-pair rail share matrix ─────────────────────────────
print(f'Computing rail share matrix for {TARGET_YEAR}...')

geo_by_id = input_data['geo_by_id']
odpair_by_id = input_data['odpair_by_id']
path_by_id = input_data['path_by_id']

# Accumulate tkm by (origin_country, dest_country, mode)
from collections import defaultdict
pair_mode_tkm = defaultdict(float)

for key, tonnes in f_dict.items():
    year = key[0]
    if year != TARGET_YEAR:
        continue

    odpair_id = key[1][1]
    path_id = key[1][2]
    mode_id = key[2][0]

    odpair = odpair_by_id.get(odpair_id)
    if odpair is None:
        continue

    origin_geo = geo_by_id.get(odpair['from'])
    dest_geo = geo_by_id.get(odpair['to'])
    if origin_geo is None or dest_geo is None:
        continue

    path_info = path_by_id.get(path_id)
    if path_info is None:
        continue

    tkm = tonnes * path_info['length']
    origin_country = origin_geo['country']
    dest_country = dest_geo['country']

    mode = 'rail' if mode_id == 2 else 'road'
    pair_mode_tkm[(origin_country, dest_country, mode)] += tkm

# Build matrix
matrix = pd.DataFrame(index=COUNTRIES, columns=COUNTRIES, dtype=float)
matrix[:] = np.nan

for oc in COUNTRIES:
    for dc in COUNTRIES:
        if oc == dc:
            continue
        rail = pair_mode_tkm.get((oc, dc, 'rail'), 0)
        road = pair_mode_tkm.get((oc, dc, 'road'), 0)
        total = rail + road
        if total > 0:
            matrix.loc[oc, dc] = rail / total * 100
        # else stays NaN (no flow)

print(matrix)

# ── Plot heatmap ─────────────────────────────────────────────────────
print('\nGenerating figure...')

fig, ax = plt.subplots(figsize=(6.5, 5.5))

# Prepare data for imshow
data_arr = matrix.values.astype(float)
mask = np.isnan(data_arr)

# Use YlOrRd colormap
cmap = plt.cm.YlOrRd.copy()
cmap.set_bad(color='white')

im = ax.imshow(data_arr, cmap=cmap, vmin=0, vmax=100, aspect='equal')

# Tick labels
ax.set_xticks(range(len(COUNTRIES)))
ax.set_xticklabels(COUNTRIES, fontsize=16)
ax.set_yticks(range(len(COUNTRIES)))
ax.set_yticklabels(COUNTRIES, fontsize=16)
ax.set_xlabel('Destination', fontsize=15)
ax.set_ylabel('Origin', fontsize=15)
ax.xaxis.set_label_position('bottom')
ax.xaxis.tick_bottom()

# Annotate cells
for i in range(len(COUNTRIES)):
    for j in range(len(COUNTRIES)):
        if i == j:
            continue
        val = data_arr[i, j]
        if np.isnan(val):
            ax.text(j, i, '--', ha='center', va='center', fontsize=12, color='grey')
        else:
            color = 'white' if val > 60 else 'black'
            ax.text(j, i, f'{val:.0f}\\%', ha='center', va='center',
                    fontsize=12, color=color)

ax.set_title(r'Rail share of freight volume (\%)', fontsize=16)

# Colorbar
cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
cbar.set_label(r'Rail share (\%)', fontsize=13)
cbar.ax.tick_params(labelsize=10)

plt.tight_layout()

# Save
fname = 'rail_shift_by_country_pair_2048'
for dst in [FIG_DIR, MANUSCRIPT_IMG]:
    fig.savefig(dst / f'{fname}.pdf', bbox_inches='tight')
fig.savefig(FIG_DIR / f'{fname}.png', dpi=300, bbox_inches='tight')
plt.close()

print(f'\nSaved: figures/{fname}.pdf')
print('Done.')
