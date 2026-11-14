"""
Levelized cost impact of electricity vs network fee surcharges.
Shows MCS and CCS side by side to highlight the utilization-driven asymmetry.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

plt.rcParams.update(plt.rcParamsDefault)
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Segoe UI", "sans-serif"],
    "font.size": 15,
})

BASE = Path(__file__).resolve().parent
FIG_DIR = BASE / 'figures'
MANUSCRIPT_IMG = BASE.parent.parent / 'Moving-electricity-loads-in-long-term-decarbonizations' / 'images'

# === Parameters ===
CHARGERS = {
    'MCS': {'gamma': 0.23, 'power': 1000},
    'CCS': {'gamma': 0.75, 'power': 100},
}
capex_per_kw = 283.33
lifetime = 15
discount_rate = 0.05
annuity_factor = discount_rate / (1 - (1 + discount_rate)**(-lifetime))
ann_capex = capex_per_kw * annuity_factor

NODES = {
    'AT33': {'elec_mcs': 15.9, 'elec_ccs': 17.7, 'network': 14.69},
    'ITH1': {'elec_mcs': 15.5, 'elec_ccs': 17.2, 'network': 8.96},
}

ELEC_SURCHARGES = [0, 1, 2, 4, 6, 8, 10, 15]
NET_SURCHARGES = [0, 2, 5, 10, 20, 50]

# Colors
ELEC_BASE_COL = '#e8a08d'   # muted coral
ELEC_SURCH_COL = '#c93c3c'  # red
INFRA_COL = '#7ba4c4'       # steel blue
NET_BASE_COL = '#a5c98f'    # sage
NET_SURCH_COL = '#4a7a3a'   # dark green

# === Figure: 2 rows (AT33, ITH1) x 2 columns (electricity, network) ===
# Each panel has grouped bars: MCS | CCS
fig, axes = plt.subplots(2, 2, figsize=(17, 10))

for row, (node, params) in enumerate(NODES.items()):
    # --- Left: Electricity surcharges ---
    ax = axes[row, 0]
    n = len(ELEC_SURCHARGES)
    x = np.arange(n)
    bar_w = 0.35

    for ci, (ctype, cparams) in enumerate(CHARGERS.items()):
        gamma = cparams['gamma']
        elec_base = params[f'elec_{ctype.lower()}']
        infra_ct = ann_capex / (gamma * 8760) * 1000 / 10
        net_ct = params['network'] / (gamma * 8760) * 1000 / 10

        offset = -bar_w / 2 if ci == 0 else bar_w / 2

        for i, surcharge in enumerate(ELEC_SURCHARGES):
            # Stack: electricity base | surcharge | infra | network
            bottom = 0
            ax.bar(x[i] + offset, elec_base, bar_w, bottom=bottom,
                   color=ELEC_BASE_COL, edgecolor='black', linewidth=0.4)
            bottom += elec_base
            if surcharge > 0:
                ax.bar(x[i] + offset, surcharge, bar_w, bottom=bottom,
                       color=ELEC_SURCH_COL, edgecolor='black', linewidth=0.4)
            bottom += surcharge
            ax.bar(x[i] + offset, infra_ct, bar_w, bottom=bottom,
                   color=INFRA_COL, edgecolor='black', linewidth=0.4)
            bottom += infra_ct
            ax.bar(x[i] + offset, net_ct, bar_w, bottom=bottom,
                   color=NET_BASE_COL, edgecolor='black', linewidth=0.4)
            total = bottom + net_ct

            # Total annotation (only on top)
            ax.text(x[i] + offset, total + 0.2, f'{total:.1f}',
                    ha='center', va='bottom', fontsize=8, color='#333')

    # Charger type labels
    ax.text(0 - bar_w / 2, -2.5, 'MCS', ha='center', fontsize=10, fontweight='bold', color='#555')
    ax.text(0 + bar_w / 2, -2.5, 'CCS', ha='center', fontsize=10, fontweight='bold', color='#555')

    ax.set_xticks(x)
    ax.set_xticklabels([f'+{s}' if s > 0 else 'Ref' for s in ELEC_SURCHARGES], fontsize=11)
    ax.set_xlabel('Electricity surcharge (ct/kWh)', fontsize=13)
    ax.set_title(f'{node} — Electricity price surcharges', fontsize=14)
    ax.set_ylim(0, 36)
    ax.grid(axis='y', alpha=0.2)

    # --- Right: Network fee surcharges ---
    ax = axes[row, 1]
    n = len(NET_SURCHARGES)
    x = np.arange(n)

    for ci, (ctype, cparams) in enumerate(CHARGERS.items()):
        gamma = cparams['gamma']
        elec_base = params[f'elec_{ctype.lower()}']
        infra_ct = ann_capex / (gamma * 8760) * 1000 / 10
        net_base_ct = params['network'] / (gamma * 8760) * 1000 / 10

        offset = -bar_w / 2 if ci == 0 else bar_w / 2

        for i, surcharge in enumerate(NET_SURCHARGES):
            net_surch_ct = surcharge / (gamma * 8760) * 1000 / 10
            bottom = 0
            ax.bar(x[i] + offset, elec_base, bar_w, bottom=bottom,
                   color=ELEC_BASE_COL, edgecolor='black', linewidth=0.4)
            bottom += elec_base
            ax.bar(x[i] + offset, infra_ct, bar_w, bottom=bottom,
                   color=INFRA_COL, edgecolor='black', linewidth=0.4)
            bottom += infra_ct
            ax.bar(x[i] + offset, net_base_ct, bar_w, bottom=bottom,
                   color=NET_BASE_COL, edgecolor='black', linewidth=0.4)
            bottom += net_base_ct
            if net_surch_ct > 0.01:
                ax.bar(x[i] + offset, net_surch_ct, bar_w, bottom=bottom,
                       color=NET_SURCH_COL, edgecolor='black', linewidth=0.4)
            total = bottom + net_surch_ct

            ax.text(x[i] + offset, total + 0.2, f'{total:.1f}',
                    ha='center', va='bottom', fontsize=8, color='#333')

    ax.text(0 - bar_w / 2, -2.5, 'MCS', ha='center', fontsize=10, fontweight='bold', color='#555')
    ax.text(0 + bar_w / 2, -2.5, 'CCS', ha='center', fontsize=10, fontweight='bold', color='#555')

    ax.set_xticks(x)
    ax.set_xticklabels([f'+{s}' if s > 0 else 'Ref' for s in NET_SURCHARGES], fontsize=11)
    ax.set_xlabel('Network fee surcharge (EUR/kW/yr)', fontsize=13)
    ax.set_title(f'{node} — Network fee surcharges', fontsize=14)
    ax.set_ylim(0, 36)  # same scale
    ax.grid(axis='y', alpha=0.2)

axes[0, 0].set_ylabel('Levelized charging cost\n(ct/kWh)', fontsize=13)
axes[1, 0].set_ylabel('Levelized charging cost\n(ct/kWh)', fontsize=13)

# Shared legend
from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor=ELEC_BASE_COL, edgecolor='black', linewidth=0.5, label='Electricity (base)'),
    Patch(facecolor=ELEC_SURCH_COL, edgecolor='black', linewidth=0.5, label='Electricity surcharge'),
    Patch(facecolor=INFRA_COL, edgecolor='black', linewidth=0.5, label='Charger CAPEX'),
    Patch(facecolor=NET_BASE_COL, edgecolor='black', linewidth=0.5, label='Network fees (base)'),
    Patch(facecolor=NET_SURCH_COL, edgecolor='black', linewidth=0.5, label='Network fee surcharge'),
]
fig.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, 1.03),
           ncol=5, fontsize=11, framealpha=0.9)

fig.suptitle('Levelized charging cost decomposition — MCS vs CCS (2040)',
             fontsize=16, y=1.06)

plt.tight_layout()
plt.savefig(str(FIG_DIR / 'surcharge_levelized_cost_comparison.pdf'), bbox_inches='tight', dpi=300)
plt.savefig(str(FIG_DIR / 'surcharge_levelized_cost_comparison.png'), bbox_inches='tight', dpi=300)
if MANUSCRIPT_IMG.exists():
    plt.savefig(str(MANUSCRIPT_IMG / 'surcharge_levelized_cost_comparison.pdf'), bbox_inches='tight', dpi=300)
print('Saved: surcharge_levelized_cost_comparison.pdf/.png')
plt.close()
