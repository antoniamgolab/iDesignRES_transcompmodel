"""
Regenerate Figure 6: BET fleet by OD country pair (2040).
Symmetric matrix: DE-AT and AT-DE are summed into one connection.
Country ordering: north to south along the corridor.

Top row: absolute BEV vehicles per scenario.
Bottom row: differences relative to Go RES.
"""

import yaml, re
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path

# -- Font settings -------------------------------------------------------------
plt.rcParams.update(plt.rcParamsDefault)
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "serif",
    "font.serif": "mathpazo",
    "font.size": 18,
})

# -- Paths ---------------------------------------------------------------------
BASE = Path(__file__).resolve().parent
INPUT_BASE = BASE / 'input_data' / 'uncertainty_scenarios_v2'
RESULTS_PATH = BASE / 'results' / 'uncertainty_scenarios_v2'
FIG_DIR = BASE / 'figures'
FIG_DIR.mkdir(exist_ok=True)
MANUSCRIPT_IMG = BASE.parent.parent / 'Moving-electricity-loads-in-long-term-decarbonizations' / 'images'

# North to south ordering along the Scandinavian-Mediterranean corridor
COUNTRY_ORDER = ['NO', 'FI', 'SE', 'DK', 'DE', 'AT', 'IT']

# Auto-detect latest result prefixes
import glob as _glob
SCENARIOS = {}
for sc_name, sc_label in [('scenario_000', 'Go RES'), ('scenario_001', 'NECPEssentials'),
                           ('scenario_002', 'REPowerEU++'), ('scenario_003', 'Trinity')]:
    h_files = sorted(_glob.glob(str(RESULTS_PATH / sc_name / '*_h_dict.yaml')))
    if h_files:
        prefix = Path(h_files[-1]).stem.replace('_h_dict', '')
        SCENARIOS[sc_name] = {'name': sc_label, 'prefix': prefix}
    else:
        print(f"WARNING: No h_dict found for {sc_name}")

YEAR_MAPPING = {i: 2020 + (i - 1) * 4 for i in range(1, 15)}
TARGET_YEAR = 2040
BEV_TECH_ID = 1

CI_RE = re.compile(r'CartesianIndex\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\)')


# -- Load geographic data ------------------------------------------------------
print('Loading geographic data...')
with open(BASE / 'input_data' / 'fixed_nuts_2' / 'GeographicElement.yaml') as f:
    geo_data = yaml.safe_load(f)
geoid2country = {g['id']: g.get('country', '??') for g in geo_data if g.get('type') == 'node'}

# -- Load OD pair mapping ------------------------------------------------------
print('Loading OD pair mapping...')
with open(INPUT_BASE / 'scenario_000' / 'Odpair.yaml') as f:
    odpairs = yaml.load(f, Loader=yaml.UnsafeLoader)
odpair_map = {}
for od in odpairs:
    odpair_map[od['id']] = (od['from'], od['to'])


# -- Load h_dict ---------------------------------------------------------------
def load_h_dict(scenario_id):
    cfg = SCENARIOS[scenario_id]
    fpath = RESULTS_PATH / scenario_id / f"{cfg['prefix']}_h_dict.yaml"
    print(f'  Loading {fpath.name}...')
    with open(fpath) as f:
        return yaml.safe_load(f)


# -- Extract BEV by OD pair (symmetric: sum both directions) -------------------
def extract_bev_symmetric(h_dict, target_year):
    od_vehicles = {}

    for key, value in h_dict.items():
        if isinstance(value, str):
            value = float(value)
        if value < 0.01:
            continue

        m = CI_RE.match(str(key))
        if m:
            year_idx = int(m.group(1))
            odpair_id = int(m.group(2))
            tech_id = int(m.group(3))
            year = YEAR_MAPPING.get(year_idx, year_idx)
            if year != target_year or tech_id != BEV_TECH_ID:
                continue
        else:
            try:
                parts = str(key).strip('()').split(',')
                if len(parts) < 4:
                    continue
                year = int(parts[0].strip())
                odpair_id = int(parts[1].strip())
                tech_id = int(parts[2].strip())
                if year != target_year or tech_id != BEV_TECH_ID:
                    continue
            except (ValueError, IndexError):
                continue

        if odpair_id not in odpair_map:
            continue

        origin_geo, dest_geo = odpair_map[odpair_id]
        oc = geoid2country.get(origin_geo)
        dc = geoid2country.get(dest_geo)
        if oc is None or dc is None:
            continue

        # Symmetric key: always put the northernmost country first
        pair = tuple(sorted([oc, dc], key=lambda c: COUNTRY_ORDER.index(c)))
        od_vehicles[pair] = od_vehicles.get(pair, 0.0) + value

    return od_vehicles


def build_symmetric_matrix(od_vehicles):
    """Build symmetric OD matrix with north-to-south ordering (upper triangle only)."""
    present = set()
    for (c1, c2) in od_vehicles:
        present.add(c1)
        present.add(c2)
    countries = [c for c in COUNTRY_ORDER if c in present]

    matrix = pd.DataFrame(np.nan, index=countries, columns=countries)
    for (c1, c2), val in od_vehicles.items():
        # Only fill upper triangle: row index < col index
        ri = countries.index(c1)
        ci = countries.index(c2)
        if ri < ci:
            matrix.iloc[ri, ci] = val
        elif ci < ri:
            matrix.iloc[ci, ri] = val
        # diagonal (same country) stays NaN
    return matrix


# -- Load all scenarios --------------------------------------------------------
print('Loading scenario results...')
matrices = {}
for sid, cfg in SCENARIOS.items():
    h_dict = load_h_dict(sid)
    od_veh = extract_bev_symmetric(h_dict, TARGET_YEAR)
    matrices[sid] = build_symmetric_matrix(od_veh)
    total = sum(od_veh.values())  # use non-mirrored sum
    print(f'  {cfg["name"]}: {total:.0f} BEV vehicles')

ref_id = 'scenario_000'
ref_matrix = matrices[ref_id]
ref_name = SCENARIOS[ref_id]['name']
other_ids = [s for s in SCENARIOS if s != ref_id]

# -- Plot ----------------------------------------------------------------------
print('Generating figure...')

abs_vmax = max(np.nanmax(m.values) for m in matrices.values())
delta_vmax = 0
for sid in other_ids:
    delta = matrices[sid] - ref_matrix
    delta_vmax = max(delta_vmax, np.nanmax(np.abs(delta.values)))

fig, axes = plt.subplots(2, len(other_ids) + 1, figsize=(18, 10))
fig.subplots_adjust(right=0.88, wspace=0.3, hspace=0.35)

cmap_abs = plt.cm.YlOrRd.copy()
cmap_abs.set_bad('white')
cmap_delta = plt.cm.RdBu_r.copy()
cmap_delta.set_bad('white')


def annotate_cells(ax, data, fmt='.0f', threshold_frac=0.5):
    """Add value annotations to heatmap cells (skip NaN / masked cells)."""
    vmax = np.nanmax(np.abs(data.values))
    for i in range(len(data.index)):
        for j in range(len(data.columns)):
            val = data.iloc[i, j]
            if np.isnan(val) or abs(val) < 0.5:
                continue
            color = 'white' if abs(val) > vmax * threshold_frac else 'black'
            ax.text(j, i, f'{val:{fmt}}', ha='center', va='center',
                    fontsize=9, color=color)


# --- Top row: absolute values ---
ax = axes[0, 0]
im_abs = ax.imshow(np.ma.masked_invalid(ref_matrix.values), cmap=cmap_abs, aspect='auto', vmin=0, vmax=abs_vmax)
ax.set_xticks(range(len(ref_matrix.columns)))
ax.set_xticklabels(ref_matrix.columns, rotation=45, ha='right', fontsize=12)
ax.set_yticks(range(len(ref_matrix.index)))
ax.set_yticklabels(ref_matrix.index, fontsize=12)
total = sum(extract_bev_symmetric(load_h_dict(ref_id), TARGET_YEAR).values())
ax.set_title(f'\\textit{{{ref_name}}} (Reference)\nTotal: {total:.0f}', fontsize=14)
annotate_cells(ax, ref_matrix)

for idx, sid in enumerate(other_ids):
    ax = axes[0, idx + 1]
    matrix = matrices[sid]
    name = SCENARIOS[sid]['name']
    im_abs = ax.imshow(np.ma.masked_invalid(matrix.values), cmap=cmap_abs, aspect='auto', vmin=0, vmax=abs_vmax)
    ax.set_xticks(range(len(matrix.columns)))
    ax.set_xticklabels(matrix.columns, rotation=45, ha='right', fontsize=12)
    ax.set_yticks(range(len(matrix.index)))
    ax.set_yticklabels(matrix.index, fontsize=12)
    total_s = sum(extract_bev_symmetric(load_h_dict(sid), TARGET_YEAR).values())
    ax.set_title(f'\\textit{{{name}}}\nTotal: {total_s:.0f}', fontsize=14)
    annotate_cells(ax, matrix)

# --- Bottom row: deltas ---
ax = axes[1, 0]
ax.text(0.5, 0.5, f'Reference:\n\\textit{{{ref_name}}}',
        ha='center', va='center', fontsize=14, transform=ax.transAxes)
ax.axis('off')

for idx, sid in enumerate(other_ids):
    ax = axes[1, idx + 1]
    name = SCENARIOS[sid]['name']
    delta = matrices[sid] - ref_matrix

    im_delta = ax.imshow(np.ma.masked_invalid(delta.values), cmap=cmap_delta, aspect='auto',
                         vmin=-delta_vmax, vmax=delta_vmax)
    ax.set_xticks(range(len(delta.columns)))
    ax.set_xticklabels(delta.columns, rotation=45, ha='right', fontsize=12)
    ax.set_yticks(range(len(delta.index)))
    ax.set_yticklabels(delta.index, fontsize=12)

    total_delta = np.nansum(matrices[sid].values - ref_matrix.values)  # upper triangle only, no double-count
    sign = '+' if total_delta >= 0 else ''
    ax.set_title(f'\\textit{{{name}}} $-$ \\textit{{{ref_name}}}\nNet: {sign}{total_delta:.0f}', fontsize=14)
    annotate_cells(ax, delta, threshold_frac=0.4)

# Colorbars
cbar_ax_abs = fig.add_axes([0.90, 0.55, 0.02, 0.32])
cbar_abs = fig.colorbar(im_abs, cax=cbar_ax_abs)
cbar_abs.set_label('BEV vehicles', fontsize=11)

cbar_ax_delta = fig.add_axes([0.90, 0.10, 0.02, 0.32])
cbar_delta = fig.colorbar(im_delta, cax=cbar_ax_delta)
cbar_delta.set_label('$\\Delta$ BEV vehicles', fontsize=11)

# -- Save ----------------------------------------------------------------------
for dst in [FIG_DIR, MANUSCRIPT_IMG]:
    dst.mkdir(parents=True, exist_ok=True)
    fig.savefig(dst / 'bev_od_matrices_4scenarios_2040.pdf', bbox_inches='tight')
fig.savefig(FIG_DIR / 'bev_od_matrices_4scenarios_2040.png', bbox_inches='tight', dpi=150)
plt.close()
print('Saved: bev_od_matrices_4scenarios_2040.pdf')
print('Done.')
