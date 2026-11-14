"""
Figure 6 revised: Delta matrices only (vs Go RES reference).
Lower triangle filled, upper triangle blank. Zero/missing = "n.a."
"""
import yaml, re, glob
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from pathlib import Path
from collections import defaultdict

matplotlib.rcParams['font.family'] = 'serif'
matplotlib.rcParams['font.serif'] = ['Times New Roman', 'serif']
matplotlib.rcParams['font.size'] = 16

BASE = Path(__file__).resolve().parent
RESULTS_PATH = BASE / 'results' / 'uncertainty_scenarios_v2'
FIG_DIR = BASE / 'figures'

COUNTRY_ORDER = ['NO', 'FI', 'SE', 'DK', 'DE', 'AT', 'IT']
CI_RE = re.compile(r'CartesianIndex\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\)')
YEAR_MAPPING = {i: 2020 + (i-1)*4 for i in range(1, 15)}

with open(BASE / 'input_data/fixed_nuts_2/GeographicElement.yaml') as f:
    geo_data = yaml.safe_load(f)
geoid2country = {g['id']: g.get('country', '??') for g in geo_data if g.get('type') == 'node'}

with open(BASE / 'input_data/uncertainty_scenarios_v2/scenario_000/Odpair.yaml') as f:
    odpairs = yaml.load(f, Loader=yaml.UnsafeLoader)
odpair_map = {od['id']: (od['from'], od['to']) for od in odpairs}

SCENARIOS = {
    'scenario_001': {'name': 'NECPEssentials', 'short': 'NECP'},
    'scenario_002': {'name': 'REPowerEU++', 'short': 'REPower'},
    'scenario_003': {'name': 'Trinity', 'short': 'Trinity'},
}

TARGET_YEAR = 2040

def load_bev_by_od(sc_id, target_year):
    h_files = sorted(glob.glob(str(RESULTS_PATH / sc_id / '*_h_dict.yaml')))
    with open(h_files[-1]) as f:
        h_dict = yaml.safe_load(f)
    bev = defaultdict(float)
    icev = defaultdict(float)
    for key, value in h_dict.items():
        if isinstance(value, str): value = float(value)
        if value < 0.01: continue
        m = CI_RE.match(str(key))
        if m:
            yi, oid, tid = int(m.group(1)), int(m.group(2)), int(m.group(3))
            year = YEAR_MAPPING.get(yi, yi)
            if year != target_year: continue
        else:
            try:
                parts = str(key).strip('()').split(',')
                year = int(parts[0].strip()); oid = int(parts[1].strip()); tid = int(parts[2].strip())
                if year != target_year: continue
            except: continue
        if oid not in odpair_map: continue
        og, dg = odpair_map[oid]
        oc = geoid2country.get(og); dc = geoid2country.get(dg)
        if not oc or not dc: continue
        pair = tuple(sorted([oc, dc], key=lambda c: COUNTRY_ORDER.index(c)))
        if tid == 1: bev[pair] += value
        elif tid == 0: icev[pair] += value
    result = {}
    for pair in set(list(bev.keys()) + list(icev.keys())):
        b = bev[pair]; i = icev[pair]; t = b + i
        if t > 10: result[pair] = b / t * 100
    return result

# Load reference (Go RES)
print("Loading Go RES reference...")
ref = load_bev_by_od('scenario_000', TARGET_YEAR)

# Load comparison scenarios
sc_data = {}
for sc_id, cfg in SCENARIOS.items():
    print(f"Loading {cfg['name']}...")
    sc_data[sc_id] = load_bev_by_od(sc_id, TARGET_YEAR)

# Build figure: 1 row, 3 columns (delta matrices)
fig, axes = plt.subplots(1, 3, figsize=(16, 6))
fig.suptitle(f'BEV adoption difference vs Go RES - {TARGET_YEAR}  (percentage points)',
             fontsize=18, fontweight='bold', y=1.08)

countries = COUNTRY_ORDER
n = len(countries)

for idx, (sc_id, cfg) in enumerate(SCENARIOS.items()):
    ax = axes[idx]
    comp = sc_data[sc_id]

    # Build lower-triangle matrix
    matrix = np.full((n, n), np.nan)
    text_matrix = [['' for _ in range(n)] for _ in range(n)]

    for i in range(n):
        for j in range(n):
            if i <= j:  # upper triangle + diagonal = blank
                continue
            c1, c2 = countries[j], countries[i]  # lower triangle: row > col
            pair = tuple(sorted([c1, c2], key=lambda c: COUNTRY_ORDER.index(c)))

            ref_val = ref.get(pair)
            comp_val = comp.get(pair)

            if ref_val is None and comp_val is None:
                text_matrix[i][j] = 'n.a.'
            elif ref_val is None or comp_val is None:
                if ref_val is not None:
                    matrix[i, j] = -ref_val
                    text_matrix[i][j] = f'{-ref_val:+.0f}'
                elif comp_val is not None:
                    matrix[i, j] = comp_val
                    text_matrix[i][j] = f'{comp_val:+.0f}'
            else:
                delta = comp_val - ref_val
                if abs(delta) < 0.5:
                    text_matrix[i][j] = '0'
                    matrix[i, j] = 0
                else:
                    matrix[i, j] = delta
                    text_matrix[i][j] = f'{delta:+.0f}'

    # Plot
    norm = TwoSlopeNorm(vmin=-40, vcenter=0, vmax=40)
    im = ax.imshow(matrix, cmap='coolwarm', norm=norm, aspect='auto')

    ax.set_xticks(range(n))
    ax.set_xticklabels(countries, fontsize=12)
    ax.set_yticks(range(n))
    ax.set_yticklabels(countries, fontsize=12)

    # Add text annotations — hide all empty cells completely
    for i in range(n):
        for j in range(n):
            if i <= j:  # upper triangle + diagonal = white, no border
                ax.add_patch(plt.Rectangle((j-0.5, i-0.5), 1, 1,
                            fill=True, facecolor='white', edgecolor='white', linewidth=0))
            elif text_matrix[i][j] == 'n.a.':
                # n.a. cells — show text but no colored background
                ax.add_patch(plt.Rectangle((j-0.5, i-0.5), 1, 1,
                            fill=True, facecolor='white', edgecolor='lightgray', linewidth=0.5))
                ax.text(j, i, 'n.a.', ha='center', va='center', fontsize=9,
                       color='#bbb', style='italic')
            else:
                val = matrix[i, j]
                if not np.isnan(val):
                    color = 'white' if abs(val) > 25 else 'black'
                    ax.text(j, i, text_matrix[i][j], ha='center', va='center',
                           fontsize=11, color=color, fontweight='bold' if abs(val) > 10 else 'normal')

    # Net delta
    all_deltas = [matrix[i, j] for i in range(n) for j in range(n) if not np.isnan(matrix[i, j])]
    net = sum(all_deltas)

    ax.set_title(f'{cfg["name"]} $-$ Go RES\nNet: {net:+.0f} pp', fontsize=13)
    ax.set_xlabel('Origin', fontsize=12)
    if idx == 0:
        ax.set_ylabel('Destination', fontsize=12)

    # Clean up spines
    for spine in ax.spines.values():
        spine.set_visible(False)

# Colorbar — horizontal at bottom
cbar_ax = fig.add_axes([0.25, -0.06, 0.5, 0.025])  # [left, bottom, width, height]
cbar = fig.colorbar(im, cax=cbar_ax, orientation='horizontal')
cbar.set_label('$\\Delta$ BEV share (pp)', fontsize=13)

plt.subplots_adjust(wspace=0.3)
outfile = FIG_DIR / f'fig6_delta_matrix_lower_{TARGET_YEAR}.pdf'
plt.savefig(outfile, bbox_inches='tight', dpi=300)
plt.savefig(str(outfile).replace('.pdf', '.png'), bbox_inches='tight', dpi=200)
print(f"Saved: {outfile.name}")
plt.close()

print("Done!")
