"""
Stacked area plot: CCS + MCS installed capacity by latitude.
4 panels: Go RES 2040, Go RES 2048, REPowerEU++ 2040, REPowerEU++ 2048
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter1d
import yaml, re, glob
from collections import defaultdict
from pathlib import Path

matplotlib.rcParams['font.family'] = 'serif'
matplotlib.rcParams['font.serif'] = ['Times New Roman', 'serif']
matplotlib.rcParams['font.size'] = 14

BASE = Path(__file__).resolve().parent
RESULTS = BASE / 'results' / 'uncertainty_scenarios_v2'
FIG_DIR = BASE / 'figures'

with open(BASE / 'input_data/fixed_nuts_2/GeographicElement.yaml') as f:
    geo_data = yaml.safe_load(f)
geo_lat = {g['id']: g.get('coordinate_lat', 0) for g in geo_data}
geo_country = {g['id']: g.get('country', '??') for g in geo_data}
all_geo_ids = sorted([g['id'] for g in geo_data if g.get('type') == 'node'],
                     key=lambda g: geo_lat[g])

ci3_pat = re.compile(r'CartesianIndex\((\d+),\s*(\d+),\s*(\d+)\):\s*([\d.eE+-]+)')
MODELED_YEARS = list(range(2020, 2064, 4))
y_idx_to_year = {i+1: y for i, y in enumerate(MODELED_YEARS)}

BORDERS = {
    'IT-AT': 46.5, 'AT-DE': 47.5, 'DE-DK': 54.5, 'DK-SE': 55.5
}

CCS_COLOR = '#3498DB'   # blue
MCS_COLOR = '#E74C3C'   # red

def get_cumulative_infra_by_geo(sc, target_year):
    """Returns {geo_id: (ccs_mw, mcs_mw)}"""
    q_files = sorted(glob.glob(str(RESULTS / sc / '*_q_fuel_infr_plus_dict.yaml')))
    ccs = defaultdict(float)
    mcs = defaultdict(float)
    with open(q_files[-1]) as f:
        for line in f:
            m = ci3_pat.match(line.strip())
            if not m: continue
            yi, fl, geo = int(m.group(1)), int(m.group(2)), int(m.group(3))
            val = float(m.group(4))
            if val < 1e-3 or fl == 3: continue
            geo_id = geo - 1  # CartesianIndex is 1-based positional
            year = y_idx_to_year.get(yi)
            if year and year <= target_year:
                # CORRECTED mapping: fi=1=MCS(1000kW), fi=2=CCS(100kW)
                if fl == 2:
                    ccs[geo_id] += val / 1000
                elif fl == 1:
                    mcs[geo_id] += val / 1000
    return ccs, mcs

# ── Build figure ──
panels = [
    ('scenario_000', 2040, 'Go RES — 2040'),
    ('scenario_000', 2048, 'Go RES — 2048'),
    ('scenario_002', 2040, 'REPowerEU++ — 2040'),
    ('scenario_002', 2048, 'REPowerEU++ — 2048'),
]

fig, axes = plt.subplots(1, 4, figsize=(18, 8), sharey=True, sharex=True)
fig.suptitle('Installed charging infrastructure by latitude (cumulative MW)',
             fontsize=16, fontweight='bold', y=0.98)

sigma = 1.2  # smoothing
global_max = 0

# First pass: get global max
for sc, ty, title in panels:
    ccs, mcs = get_cumulative_infra_by_geo(sc, ty)
    for g in all_geo_ids:
        total = ccs.get(g, 0) + mcs.get(g, 0)
        global_max = max(global_max, total)

# Second pass: plot
for idx, (sc, ty, title) in enumerate(panels):
    ax = axes[idx]
    ccs, mcs = get_cumulative_infra_by_geo(sc, ty)

    lats = np.array([geo_lat[g] for g in all_geo_ids])
    ccs_vals = np.array([ccs.get(g, 0) for g in all_geo_ids])
    mcs_vals = np.array([mcs.get(g, 0) for g in all_geo_ids])

    # Smooth
    ccs_smooth = gaussian_filter1d(ccs_vals, sigma=sigma)
    mcs_smooth = gaussian_filter1d(mcs_vals, sigma=sigma)

    # Stacked area
    ax.fill_betweenx(lats, 0, ccs_smooth, color=CCS_COLOR, alpha=0.4, label='CCS (100 kW)' if idx == 0 else None)
    ax.fill_betweenx(lats, ccs_smooth, ccs_smooth + mcs_smooth, color=MCS_COLOR, alpha=0.4, label='MCS (1 MW)' if idx == 0 else None)

    # Outline
    ax.plot(ccs_smooth, lats, color=CCS_COLOR, linewidth=1.0, alpha=0.7)
    ax.plot(ccs_smooth + mcs_smooth, lats, color=MCS_COLOR, linewidth=1.0, alpha=0.7)

    # Border lines
    for bname, blat in BORDERS.items():
        ax.axhline(y=blat, color='gray', linestyle=':', alpha=0.4, linewidth=0.7)

    ax.set_title(title, fontsize=13)
    ax.set_xlabel('MW', fontsize=12)
    ax.set_ylim(38, 72)
    ax.grid(axis='x', alpha=0.15)

    # Total annotation
    total_ccs = sum(ccs.values())
    total_mcs = sum(mcs.values())
    ax.text(0.95, 0.02, f'CCS: {total_ccs:.0f} MW\nMCS: {total_mcs:.0f} MW\nTotal: {total_ccs+total_mcs:.0f} MW',
            transform=ax.transAxes, fontsize=9, ha='right', va='bottom',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='lightgray', alpha=0.9))

axes[0].set_ylabel('Latitude (°N)', fontsize=13)

# Shared x-axis
for ax in axes:
    ax.set_xlim(0, global_max * 1.3)

# Country labels on rightmost panel
country_lats = {'IT': 42.5, 'AT': 47.5, 'DE': 51.0, 'DK': 56.0, 'SE': 62.0, 'NO': 64.0}
for c, lat in country_lats.items():
    axes[-1].text(1.02, lat, c, transform=axes[-1].get_yaxis_transform(),
                  fontsize=11, fontweight='bold', va='center', ha='left',
                  bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                           edgecolor='#888', alpha=0.9))

# Legend
fig.legend(loc='lower center', bbox_to_anchor=(0.5, -0.03), ncol=2,
           fontsize=12, framealpha=0.9, frameon=True, edgecolor='#ccc')

plt.tight_layout(rect=[0, 0.03, 1, 0.95])
outfile = FIG_DIR / 'infra_stacked_latitude_gores_repower.pdf'
plt.savefig(outfile, bbox_inches='tight', dpi=300)
plt.savefig(str(outfile).replace('.pdf', '.png'), bbox_inches='tight', dpi=200)
print(f"Saved: {outfile.name}")
plt.close()

print("Done!")
