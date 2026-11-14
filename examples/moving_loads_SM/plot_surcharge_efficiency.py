"""
Surcharge efficiency: demand reduction and infrastructure response vs levelized cost increase.
Top: charging energy reallocation. Bottom: MCS vs CCS at target node.
Both rows share the same x-axis: levelized cost increase (ct/kWh).
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

gamma_mcs = 0.23
gamma_ccs = 0.75

ELEC_COL = '#e07b54'   # warm terracotta
NET_COL = '#4a90a4'    # teal blue

# === Model results: (label, surcharge_level, remaining_GWh, mcs_MW, ccs_MW) ===
AT33_BL = {'gwh': 68.6, 'mcs': 3.4, 'ccs': 13.5}
AT33_ELEC = [
    ('+1ct',   1, 55.0, 13.5, 3.1),
    ('+2ct',   2, 38.1, 9.3, 0.5),
    ('+4ct',   4, 27.9, 9.2, 0.0),
    ('+6ct',   6, 23.8, 9.2, 0.0),
    ('+8ct',   8, 23.4, 4.6, 0.0),
    ('+10ct', 10, 15.2, 4.6, 0.0),
    ('+15ct', 15,  3.3, 0.5, 0.0),
]
AT33_NET = [
    ('+2/kW',   2, 66.7, 13.7, 1.3),
    ('+5/kW',   5, 57.8, 10.0, 0.0),
    ('+10/kW', 10, 51.4, 9.6, 0.0),
    ('+20/kW', 20, 49.3, 9.2, 0.0),
    ('+50/kW', 50, 24.0, 4.6, 0.0),
]

ITH1_BL = {'gwh': 95.3, 'mcs': 38.4, 'ccs': 4.6}
ITH1_ELEC = [
    ('+1ct',   1, 33.7, 7.6, 8.3),
    ('+2ct',   2, 20.3, 8.2, 2.9),
    ('+4ct',   4, 16.6, 8.3, 1.8),
    ('+6ct',   6, 11.1, 5.7, 0.0),
    ('+8ct',   8,  9.8, 4.4, 0.0),
    ('+10ct', 10,  9.8, 2.8, 0.0),
    ('+15ct', 15,  1.2, 0.2, 0.0),
]
ITH1_NET = [
    ('+2/kW',   2, 42.3, 7.6, 8.3),
    ('+5/kW',   5, 30.8, 8.2, 2.5),
    ('+10/kW', 10, 25.1, 5.7, 0.0),
    ('+20/kW', 20, 23.9, 5.7, 0.0),
    ('+50/kW', 50, 11.0, 2.8, 0.0),
]

def elec_cost_increase(surcharge_ct):
    """Electricity surcharge: 1:1 impact on levelized cost."""
    return surcharge_ct

def net_cost_increase_mcs(surcharge_eur):
    """Network fee: diluted by MCS utilization."""
    return surcharge_eur / (gamma_mcs * 8760) * 1000 / 10

# === Figure: 3 rows x 2 columns, shared x-axis per column ===
fig, axes = plt.subplots(3, 2, figsize=(15, 10), sharex='col',
                          gridspec_kw={'hspace': 0.25, 'height_ratios': [1.2, 1, 1]})

for col, (node, bl, elec_data, net_data) in enumerate([
    ('AT33', AT33_BL, AT33_ELEC, AT33_NET),
    ('ITH1', ITH1_BL, ITH1_ELEC, ITH1_NET),
]):
    ax_top = axes[0, col]
    ax_mcs = axes[1, col]
    ax_ccs = axes[2, col]

    # --- Row 1: demand reduction ---
    ex = [elec_cost_increase(s) for _, s, *_ in elec_data]
    ey = [(bl['gwh'] - gwh) / bl['gwh'] * 100 for _, _, gwh, *_ in elec_data]
    ax_top.plot(ex, ey, 'o-', color=ELEC_COL, markersize=7, linewidth=2, label='Surcharge to electricity price', zorder=4)
    # Label selected electricity surcharge points (ct/kWh)
    for (label, s, *_), y in zip(elec_data, ey):
        if label in ('+1ct', '+4ct', '+10ct', '+15ct'):
            ax_top.annotate(f'+{s} ct/kWh', (elec_cost_increase(s), y), textcoords='offset points',
                            xytext=(7, -5), fontsize=9, color=ELEC_COL)

    nx = [net_cost_increase_mcs(s) for _, s, *_ in net_data]
    ny = [(bl['gwh'] - gwh) / bl['gwh'] * 100 for _, _, gwh, *_ in net_data]
    ax_top.plot(nx, ny, 's-', color=NET_COL, markersize=7, linewidth=2, label='Surcharge to grid charge', zorder=4)
    # Label selected network fee points (EUR/kW/yr)
    net_offsets = {'+2/kW': (7, 4), '+10/kW': (12, 6), '+50/kW': (7, 4)}
    for (label, s, *_), x, y in zip(net_data, nx, ny):
        if label in net_offsets:
            ax_top.annotate(f'+{s} EUR/kW/yr', (x, y), textcoords='offset points',
                            xytext=net_offsets[label], fontsize=9, color=NET_COL)

    ax_top.set_title(f'Surcharge in {node}', fontsize=16, fontweight='bold')
    ax_top.set_ylim(-3, 103)
    ax_top.grid(alpha=0.3)
    ax_top.legend(fontsize=10, loc='lower right')

    # --- Row 2: MCS infrastructure ---
    # Baseline
    ax_mcs.plot(0, bl['mcs'], 'X', color='#333', markersize=11, zorder=6,
                markeredgewidth=2, label=f'Baseline ({bl["mcs"]:.1f} MW)')

    # Electricity
    emcs_x = [elec_cost_increase(s) for _, s, *_ in elec_data]
    emcs_y = [mcs for _, _, _, mcs, _ in elec_data]
    ax_mcs.plot(emcs_x, emcs_y, 'o-', color=ELEC_COL, markersize=7, linewidth=2,
                label='Surcharge to electricity price', zorder=4)

    # Network
    nmcs_x = [net_cost_increase_mcs(s) for _, s, *_ in net_data]
    nmcs_y = [mcs for _, _, _, mcs, _ in net_data]
    ax_mcs.plot(nmcs_x, nmcs_y, 's-', color=NET_COL, markersize=7, linewidth=2,
                label='Surcharge to grid charge', zorder=4)

    ax_mcs.set_ylim(bottom=-0.5)
    ax_mcs.grid(alpha=0.3)
    ax_mcs.legend(fontsize=9, loc='upper right')

    # --- Row 3: CCS infrastructure ---
    # Baseline
    ax_ccs.plot(0, bl['ccs'], 'X', color='#333', markersize=11, zorder=6,
                markeredgewidth=2, label=f'Baseline ({bl["ccs"]:.1f} MW)')

    # Electricity
    eccs_x = [elec_cost_increase(s) for _, s, *_ in elec_data]
    eccs_y = [ccs for _, _, _, _, ccs in elec_data]
    ax_ccs.plot(eccs_x, eccs_y, 'o-', color=ELEC_COL, markersize=7, linewidth=2,
                label='Surcharge to electricity price', zorder=4)

    # Network
    nccs_x = [net_cost_increase_mcs(s) for _, s, *_ in net_data]
    nccs_y = [ccs for _, _, _, _, ccs in net_data]
    ax_ccs.plot(nccs_x, nccs_y, 's-', color=NET_COL, markersize=7, linewidth=2,
                label='Surcharge to grid charge', zorder=4)

    ax_ccs.set_xlabel('Levelized cost increase (ct/kWh)', fontsize=14)
    ax_ccs.set_xlim(-0.3, 16)
    ax_ccs.set_ylim(bottom=-0.5)
    ax_ccs.grid(alpha=0.3)
    ax_ccs.legend(fontsize=9, loc='upper right')

axes[0, 0].set_ylabel('Charging demand\nreduction (%)', fontsize=14)
axes[1, 0].set_ylabel('MCS capacity at\ntarget node (MW)', fontsize=14)
axes[2, 0].set_ylabel('CCS capacity at\ntarget node (MW)', fontsize=14)

fig.suptitle('Impact of locational electricity-price surcharges and higher grid charges on the\n'
             'charging demand allocation at a target NUTS-2 node (2040)',
             fontsize=16, y=1.02)

plt.tight_layout()
plt.savefig(str(FIG_DIR / 'surcharge_efficiency_comparison.pdf'), bbox_inches='tight', dpi=300)
plt.savefig(str(FIG_DIR / 'surcharge_efficiency_comparison.png'), bbox_inches='tight', dpi=300)
if MANUSCRIPT_IMG.exists():
    plt.savefig(str(MANUSCRIPT_IMG / 'surcharge_efficiency_comparison.pdf'), bbox_inches='tight', dpi=300)
print('Saved: surcharge_efficiency_comparison.pdf/.png')
plt.close()
