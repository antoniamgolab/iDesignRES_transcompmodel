"""
Generate OD matrix figure showing international freight demand (Mt/year)
by origin-destination country pair from the input data (Odpair.yaml, year 2020).
For inclusion in the case study section of the manuscript.
"""

import yaml
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
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
INPUT_DIR = BASE_PATH / 'input_data'
FIG_DIR = BASE_PATH / 'figures'
MANUSCRIPT_IMG = BASE_PATH.parent.parent / 'manuscript' / 'images'

CORRIDOR_COUNTRIES = ['NO', 'FI', 'SE', 'DK', 'DE', 'AT', 'IT']

# ── Load data ────────────────────────────────────────────────────────
print('Loading GeographicElement.yaml...')
with open(INPUT_DIR / 'fixed_nuts_2' / 'GeographicElement.yaml', 'r', encoding='utf-8') as f:
    geo_data = yaml.safe_load(f)

node_to_country = {}
for g in geo_data:
    if g.get('type') == 'node':
        node_to_country[g['id']] = g.get('country', '')

print(f'  Nodes: {len(node_to_country)}')

print('Loading Odpair.yaml...')
with open(INPUT_DIR / 'uncertainty_scenarios' / 'scenario_000' / 'Odpair.yaml', 'r', encoding='utf-8') as f:
    odpair_data = yaml.safe_load(f)

print(f'  OD pairs: {len(odpair_data)}')

# ── Aggregate by country pair (first year = index 0 = 2020) ─────────
country_matrix = {}
for od in odpair_data:
    origin_id = od['from']
    dest_id = od['to']
    origin_country = node_to_country.get(origin_id, '??')
    dest_country = node_to_country.get(dest_id, '??')

    # Only international
    if origin_country == dest_country:
        continue

    F_2020 = od['F'][0]  # first year = 2020

    key = (origin_country, dest_country)
    country_matrix[key] = country_matrix.get(key, 0) + F_2020

# ── Build matrix DataFrame ───────────────────────────────────────────
# Filter to corridor countries only
countries = [c for c in CORRIDOR_COUNTRIES
             if any(c in k for k in country_matrix)]

matrix_df = pd.DataFrame(0.0, index=countries, columns=countries)
for (orig, dest), tonnes in country_matrix.items():
    if orig in countries and dest in countries:
        matrix_df.loc[orig, dest] += tonnes

# Convert to Mt (million tonnes)
matrix_mt = matrix_df / 1e3  # input is kt -> Mt

print('\nInternational freight demand (Mt/year, 2020):')
print(matrix_mt.round(2).to_string())
print(f'\nTotal: {matrix_mt.sum().sum():.2f} Mt')

# ── Plot heatmap ─────────────────────────────────────────────────────
print('\nGenerating figure...')
fig, ax = plt.subplots(figsize=(8, 7))

# Mask zeros for cleaner display
data = matrix_mt.values
mask = data == 0

im = ax.imshow(data, cmap='YlOrRd', aspect='equal')

# Annotate cells
for i in range(len(countries)):
    for j in range(len(countries)):
        val = data[i, j]
        if val > 0:
            color = 'white' if val > data.max() * 0.6 else 'black'
            ax.text(j, i, f'{val:.1f}', ha='center', va='center',
                    fontsize=13, color=color, fontweight='bold')
        elif i == j:
            ax.text(j, i, '--', ha='center', va='center',
                    fontsize=11, color='#999')

ax.set_xticks(range(len(countries)))
ax.set_xticklabels(countries, fontsize=14)
ax.set_yticks(range(len(countries)))
ax.set_yticklabels(countries, fontsize=14)
ax.set_xlabel('Destination', fontsize=16)
ax.set_ylabel('Origin', fontsize=16)
ax.xaxis.set_label_position('top')
ax.xaxis.tick_top()

# Colorbar
cbar = fig.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
cbar.set_label('Freight demand (Mt/year)', fontsize=14)
cbar.ax.tick_params(labelsize=12)

plt.tight_layout()

fname = 'od_matrix_input_freight_2020'
for dst in [FIG_DIR, MANUSCRIPT_IMG]:
    fig.savefig(dst / f'{fname}.pdf', bbox_inches='tight')
fig.savefig(FIG_DIR / f'{fname}.png', bbox_inches='tight', dpi=150)
plt.close()
print(f'Saved: figures/{fname}.pdf')
print(f'Saved: manuscript/images/{fname}.pdf')
print('Done.')
