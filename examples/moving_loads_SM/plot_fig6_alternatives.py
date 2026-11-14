"""
Figure 6 alternatives: BEV adoption by OD country pair.
  Option A: BEV share (%) matrix
  Option B: Grouped bar chart
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

# Font
matplotlib.rcParams['font.family'] = 'serif'
matplotlib.rcParams['font.serif'] = ['Times New Roman', 'serif']
matplotlib.rcParams['font.size'] = 14

BASE = Path(__file__).resolve().parent
RESULTS_PATH = BASE / 'results' / 'uncertainty_scenarios_v2'
FIG_DIR = BASE / 'figures'
FIG_DIR.mkdir(exist_ok=True)

COUNTRY_ORDER = ['NO', 'FI', 'SE', 'DK', 'DE', 'AT', 'IT']

SCENARIOS = {
    'scenario_000': {'name': 'Go RES',         'color': '#1B5E20'},
    'scenario_001': {'name': 'NECPEssentials',  'color': '#E65100'},
    'scenario_002': {'name': 'REPowerEU++',     'color': '#0D47A1'},
    'scenario_003': {'name': 'Trinity',         'color': '#6A1B9A'},
}

TARGET_YEAR = 2040
CI_RE = re.compile(r'CartesianIndex\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\)')
YEAR_MAPPING = {i: 2020 + (i - 1) * 4 for i in range(1, 15)}

# Load geo and OD pairs
with open(BASE / 'input_data/fixed_nuts_2/GeographicElement.yaml') as f:
    geo_data = yaml.safe_load(f)
geoid2country = {g['id']: g.get('country', '??') for g in geo_data if g.get('type') == 'node'}

with open(BASE / 'input_data/uncertainty_scenarios_v2/scenario_000/Odpair.yaml') as f:
    odpairs = yaml.load(f, Loader=yaml.UnsafeLoader)
odpair_map = {od['id']: (od['from'], od['to']) for od in odpairs}


def load_h_dict(scenario_id):
    h_files = sorted(glob.glob(str(RESULTS_PATH / scenario_id / '*_h_dict.yaml')))
    with open(h_files[-1]) as f:
        return yaml.safe_load(f)


def extract_bev_by_od(h_dict, target_year, tech_id):
    """Extract vehicles by OD country pair for a given technology."""
    od_vehicles = defaultdict(float)
    for key, value in h_dict.items():
        if isinstance(value, str):
            value = float(value)
        if value < 0.01:
            continue
        m = CI_RE.match(str(key))
        if m:
            year_idx = int(m.group(1))
            odpair_id = int(m.group(2))
            tid = int(m.group(3))
            year = YEAR_MAPPING.get(year_idx, year_idx)
            if year != target_year or tid != tech_id:
                continue
        else:
            try:
                parts = str(key).strip('()').split(',')
                year = int(parts[0].strip())
                odpair_id = int(parts[1].strip())
                tid = int(parts[2].strip())
                if year != target_year or tid != tech_id:
                    continue
            except:
                continue
        if odpair_id not in odpair_map:
            continue
        origin_geo, dest_geo = odpair_map[odpair_id]
        oc = geoid2country.get(origin_geo)
        dc = geoid2country.get(dest_geo)
        if oc and dc:
            pair = tuple(sorted([oc, dc], key=lambda c: COUNTRY_ORDER.index(c)))
            od_vehicles[pair] += value
    return od_vehicles


# Load data
print("Loading data...")
scenario_data = {}
for sc_id in SCENARIOS:
    print(f"  {sc_id}...")
    h_dict = load_h_dict(sc_id)
    bev = extract_bev_by_od(h_dict, TARGET_YEAR, 1)
    icev = extract_bev_by_od(h_dict, TARGET_YEAR, 0)
    scenario_data[sc_id] = {'bev': bev, 'icev': icev}


# ================================================================
# OPTION A: BEV Share (%) Matrix
# ================================================================
print("\nGenerating Option A: BEV share matrix...")

scenario_order = ['scenario_000', 'scenario_001', 'scenario_002', 'scenario_003']

fig, axes = plt.subplots(2, 4, figsize=(18, 9),
                          gridspec_kw={'height_ratios': [1, 1], 'hspace': 0.35, 'wspace': 0.15})

# Top row: absolute BEV share
for idx, sc_id in enumerate(scenario_order):
    ax = axes[0, idx]
    bev = scenario_data[sc_id]['bev']
    icev = scenario_data[sc_id]['icev']

    present = set()
    for pair in list(bev.keys()) + list(icev.keys()):
        present.update(pair)
    countries = [c for c in COUNTRY_ORDER if c in present]

    matrix = pd.DataFrame(np.nan, index=countries, columns=countries)
    for c1 in countries:
        for c2 in countries:
            if COUNTRY_ORDER.index(c1) >= COUNTRY_ORDER.index(c2):
                continue
            pair = (c1, c2)
            b = bev.get(pair, 0)
            i = icev.get(pair, 0)
            total = b + i
            if total > 10:  # minimum threshold
                matrix.loc[c1, c2] = b / total * 100

    cfg = SCENARIOS[sc_id]
    total_bev = sum(bev.values())

    # Plot heatmap
    mask = matrix.isna()
    im = ax.imshow(matrix.values, cmap='YlOrRd', vmin=0, vmax=100, aspect='auto')

    ax.set_xticks(range(len(countries)))
    ax.set_xticklabels(countries, rotation=45, ha='right', fontsize=10)
    ax.set_yticks(range(len(countries)))
    ax.set_yticklabels(countries, fontsize=10)

    # Add text
    for i in range(len(countries)):
        for j in range(len(countries)):
            val = matrix.iloc[i, j]
            if not np.isnan(val):
                color = 'white' if val > 60 else 'black'
                ax.text(j, i, f'{val:.0f}', ha='center', va='center', fontsize=8, color=color)

    # Mask lower triangle + diagonal
    for i in range(len(countries)):
        for j in range(len(countries)):
            if j <= i or np.isnan(matrix.iloc[i, j]):
                ax.add_patch(plt.Rectangle((j-0.5, i-0.5), 1, 1, fill=True,
                            facecolor='white', edgecolor='lightgray', linewidth=0.5))

    ax.set_title(f'{cfg["name"]}\nTotal: {total_bev:.0f} BEV', fontsize=11, fontweight='bold')

# Colorbar for top row
cbar = fig.colorbar(im, ax=axes[0, :], shrink=0.6, pad=0.02)
cbar.set_label('BEV share (%)', fontsize=11)

# Bottom row: delta in percentage points vs Go RES
ref_bev = scenario_data['scenario_000']['bev']
ref_icev = scenario_data['scenario_000']['icev']

for idx, sc_id in enumerate(scenario_order[1:]):
    ax = axes[1, idx + 1]
    bev = scenario_data[sc_id]['bev']
    icev = scenario_data[sc_id]['icev']

    countries = [c for c in COUNTRY_ORDER]
    matrix = pd.DataFrame(np.nan, index=countries, columns=countries)

    for c1 in countries:
        for c2 in countries:
            if COUNTRY_ORDER.index(c1) >= COUNTRY_ORDER.index(c2):
                continue
            pair = (c1, c2)
            b_new = bev.get(pair, 0)
            i_new = icev.get(pair, 0)
            b_ref = ref_bev.get(pair, 0)
            i_ref = ref_icev.get(pair, 0)
            total_new = b_new + i_new
            total_ref = b_ref + i_ref
            if total_ref > 10 or total_new > 10:
                pct_new = b_new / total_new * 100 if total_new > 10 else 0
                pct_ref = b_ref / total_ref * 100 if total_ref > 10 else 0
                matrix.loc[c1, c2] = pct_new - pct_ref

    cfg = SCENARIOS[sc_id]
    norm = TwoSlopeNorm(vmin=-50, vcenter=0, vmax=50)
    im2 = ax.imshow(matrix.values, cmap='RdBu_r', norm=norm, aspect='auto')

    ax.set_xticks(range(len(countries)))
    ax.set_xticklabels(countries, rotation=45, ha='right', fontsize=10)
    ax.set_yticks(range(len(countries)))
    ax.set_yticklabels(countries, fontsize=10)

    for i in range(len(countries)):
        for j in range(len(countries)):
            val = matrix.iloc[i, j]
            if not np.isnan(val):
                color = 'white' if abs(val) > 30 else 'black'
                ax.text(j, i, f'{val:+.0f}', ha='center', va='center', fontsize=8, color=color)

    for i in range(len(countries)):
        for j in range(len(countries)):
            if j <= i or np.isnan(matrix.iloc[i, j]):
                ax.add_patch(plt.Rectangle((j-0.5, i-0.5), 1, 1, fill=True,
                            facecolor='white', edgecolor='lightgray', linewidth=0.5))

    ax.set_title(f'{cfg["name"]} - Go RES\n(pp difference)', fontsize=10)

# Reference label
axes[1, 0].text(0.5, 0.5, 'Reference:\nGo RES', ha='center', va='center',
                fontsize=14, fontweight='bold', transform=axes[1, 0].transAxes)
axes[1, 0].axis('off')

cbar2 = fig.colorbar(im2, ax=axes[1, :], shrink=0.6, pad=0.02)
cbar2.set_label('$\\Delta$ BEV share (pp)', fontsize=11)

plt.suptitle(f'BEV adoption share by OD country pair ({TARGET_YEAR})', fontsize=14, fontweight='bold', y=1.01)
plt.savefig(FIG_DIR / 'fig6_option_a_bev_share_matrix.pdf', bbox_inches='tight', dpi=300)
plt.savefig(FIG_DIR / 'fig6_option_a_bev_share_matrix.png', bbox_inches='tight', dpi=200)
print("  Saved: fig6_option_a_bev_share_matrix.pdf")
plt.close()


# ================================================================
# OPTION B: Grouped Bar Chart
# ================================================================
print("\nGenerating Option B: Grouped bar chart...")

# Get all OD pairs and sort by total traffic
all_pairs = set()
for sc_id in scenario_order:
    all_pairs.update(scenario_data[sc_id]['bev'].keys())
    all_pairs.update(scenario_data[sc_id]['icev'].keys())

pair_traffic = {}
for pair in all_pairs:
    total = sum(
        scenario_data[sc_id]['bev'].get(pair, 0) + scenario_data[sc_id]['icev'].get(pair, 0)
        for sc_id in scenario_order
    )
    pair_traffic[pair] = total

top_pairs = sorted(pair_traffic.keys(), key=lambda p: pair_traffic[p], reverse=True)[:10]

fig, ax = plt.subplots(figsize=(14, 7))

x = np.arange(len(top_pairs))
n_sc = len(scenario_order)
width = 0.8 / n_sc
colors = ['#1B5E20', '#E65100', '#0D47A1', '#6A1B9A']

for i, sc_id in enumerate(scenario_order):
    bev_pcts = []
    for pair in top_pairs:
        b = scenario_data[sc_id]['bev'].get(pair, 0)
        ic = scenario_data[sc_id]['icev'].get(pair, 0)
        total = b + ic
        pct = b / total * 100 if total > 10 else 0
        bev_pcts.append(pct)

    ax.bar(x + i * width, bev_pcts, width,
           label=SCENARIOS[sc_id]['name'], color=colors[i], alpha=0.85,
           edgecolor='white', linewidth=0.5)

ax.set_xlabel('Origin-Destination Country Pair', fontsize=13)
ax.set_ylabel('BEV Share (%)', fontsize=13)
ax.set_title(f'BEV adoption by OD country pair — {TARGET_YEAR}', fontsize=15, fontweight='bold')
ax.set_xticks(x + width * (n_sc - 1) / 2)
pair_labels = [f'{p[0]}–{p[1]}' for p in top_pairs]
ax.set_xticklabels(pair_labels, rotation=0, ha='center', fontsize=11)
ax.legend(fontsize=11, ncol=2, loc='upper right')
ax.set_ylim(0, 105)
ax.grid(axis='y', alpha=0.3)
ax.axhline(y=50, color='gray', linestyle=':', alpha=0.3)

# Add total traffic annotation
for j, pair in enumerate(top_pairs):
    total = pair_traffic[pair]
    ax.annotate(f'{total:.0f}', xy=(j + width * (n_sc-1) / 2, -5),
               ha='center', fontsize=7, color='gray', annotation_clip=False)
ax.annotate('Total fleet', xy=(-0.5, -5), ha='right', fontsize=7, color='gray',
           annotation_clip=False)

plt.tight_layout()
plt.savefig(FIG_DIR / 'fig6_option_b_grouped_bar.pdf', bbox_inches='tight', dpi=300)
plt.savefig(FIG_DIR / 'fig6_option_b_grouped_bar.png', bbox_inches='tight', dpi=200)
print("  Saved: fig6_option_b_grouped_bar.pdf")
plt.close()

print("\nDone!")
