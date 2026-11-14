"""
kappa_space sensitivity analysis: 3-panel figure
(a) BEV adoption over time by kappa_space
(b) CCS vs MCS cumulative charge points over time by kappa_space
(c) Max cumulative charge points at single NUTS-2 node by kappa_space
"""
import re, yaml
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from collections import defaultdict

plt.rcParams['font.family'] = 'Times New Roman'
plt.rcParams['font.size'] = 10

basedir = 'D:/AntoniaMariaG/Scand_Med_analysis/SM_baby_2/iDesignRES_transcompmodel/examples/moving_loads_SM/'

# ── Data sources ──
summary_files = {
    r'$\infty$': 'results/kspace_sensitivity/no_space_cap/summary_stats.yaml',
    '0.001': 'results/kspace_sensitivity/kspace_0.001/summary_stats.yaml',
    '0.0005': 'results/kspace_sensitivity/kspace_0.0005/summary_stats.yaml',
    '0.0002': 'results/kspace_sensitivity/kspace_0.0002/summary_stats.yaml',
    '0.0001': 'results/kspace_sensitivity/kspace_0.0001/summary_stats.yaml',
}

q_files = {
    r'$\infty$': 'results/kspace_sensitivity/no_space_cap/no_space_cap_cs_2026-04-29_14-03-57_q_fuel_infr_plus_dict.yaml',
    '0.001': 'results/kspace_sensitivity/kspace_0.001/kspace_0.001_cs_2026-04-29_14-35-46_q_fuel_infr_plus_dict.yaml',
    '0.0005': 'results/kspace_sensitivity/kspace_0.0005/kspace_0.0005_cs_2026-04-29_15-06-31_q_fuel_infr_plus_dict.yaml',
    '0.0002': 'results/kspace_sensitivity/kspace_0.0002/kspace_0.0002_cs_2026-04-29_15-34-39_q_fuel_infr_plus_dict.yaml',
    '0.0001': 'results/kspace_sensitivity/kspace_0.0001/kspace_0.0001_cs_2026-04-29_16-09-13_q_fuel_infr_plus_dict.yaml',
}

ci3_pat = re.compile(r'CartesianIndex\((\d+),\s*(\d+),\s*(\d+)\):\s*([\d.eE+-]+)')
years = [2020, 2024, 2028, 2032, 2036, 2040, 2044, 2048, 2052, 2056, 2060]
labels_order = list(summary_files.keys())

colors = {
    r'$\infty$': '#2c7bb6',
    '0.001': '#abd9e9',
    '0.0005': '#fdae61',
    '0.0002': '#d7191c',
    '0.0001': '#7b3294',
}
linewidths = {
    r'$\infty$': 2.5,
    '0.001': 1.5,
    '0.0005': 2.5,
    '0.0002': 2.0,
    '0.0001': 2.0,
}
linestyles = {
    r'$\infty$': '-',
    '0.001': '--',
    '0.0005': '-',
    '0.0002': '--',
    '0.0001': ':',
}

# ── Panel 1: BEV adoption ──
bev_data = {}
for label, fname in summary_files.items():
    with open(basedir + fname) as f:
        s = yaml.safe_load(f)
    bev_pct = []
    for yr in years:
        fl = s.get('fleet_by_year', {}).get(yr, {})
        i = fl.get('ICEV', 0); b = fl.get('BEV', 0)
        t = i + b
        bev_pct.append(b / t * 100 if t > 0 else 0)
    bev_data[label] = bev_pct

# ── Panel 2 & 3: Infrastructure ──
# CORRECTED mapping: fi=1=MCS(1000kW), fi=2=CCS(100kW)
infra_data = {}
for label, fname in q_files.items():
    ccs_year = defaultdict(float)
    mcs_year = defaultdict(float)
    cp_geo_year = defaultdict(lambda: defaultdict(float))

    with open(basedir + fname) as f:
        for line in f:
            m = ci3_pat.match(line.strip())
            if not m:
                continue
            yi, fi, pos = int(m.group(1)), int(m.group(2)), int(m.group(3))
            val = float(m.group(4))
            if val < 1e-6:
                continue
            geo_id = pos - 1
            yr = 2020 + (yi - 1) * 4
            if fi == 1:  # MCS
                mcs_year[yr] += val
                cp_geo_year[geo_id][yr] += val / 1000
            elif fi == 2:  # CCS
                ccs_year[yr] += val
                cp_geo_year[geo_id][yr] += val / 100

    cum_ccs_cp = []
    cum_mcs_cp = []
    c_ccs = 0; c_mcs = 0
    for yr in years:
        c_ccs += ccs_year.get(yr, 0)
        c_mcs += mcs_year.get(yr, 0)
        cum_ccs_cp.append(c_ccs / 100)   # charge points
        cum_mcs_cp.append(c_mcs / 1000)  # charge points

    max_node_cp = []
    for yr_idx, yr in enumerate(years):
        max_cp = 0
        for geo_id in cp_geo_year:
            cum_cp = sum(cp_geo_year[geo_id].get(y, 0) for y in years[:yr_idx + 1])
            if cum_cp > max_cp:
                max_cp = cum_cp
        max_node_cp.append(max_cp)

    infra_data[label] = {
        'cum_ccs_cp': cum_ccs_cp,
        'cum_mcs_cp': cum_mcs_cp,
        'max_node_cp': max_node_cp,
    }

# ── Create figure ──
fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))

# Panel (a): BEV adoption
ax = axes[0]
for label in labels_order:
    ax.plot(years, bev_data[label], color=colors[label], linestyle=linestyles[label],
            linewidth=linewidths[label], marker='o', markersize=3,
            label=r'$\kappa_{space}$ = ' + label)
ax.set_xlabel('Year')
ax.set_ylabel('BEV fleet share (%)')
ax.set_title('(a) BEV adoption by deployment pace constraint')
ax.set_xlim(2028, 2060)
ax.set_ylim(0, 105)
ax.yaxis.set_major_formatter(mticker.PercentFormatter(decimals=0))
ax.legend(fontsize=8, loc='upper left')
ax.grid(True, alpha=0.3)

# Panel (b): CCS vs MCS cumulative charge points
ax = axes[1]
for label in labels_order:
    d = infra_data[label]
    ax.plot(years, d['cum_ccs_cp'], color=colors[label], linestyle='-',
            linewidth=linewidths[label], marker='o', markersize=3)
    ax.plot(years, d['cum_mcs_cp'], color=colors[label], linestyle='--',
            linewidth=linewidths[label], marker='s', markersize=3)

# Create legend manually: kappa labels + CCS/MCS distinction
from matplotlib.lines import Line2D
legend_kappa = [Line2D([0], [0], color=colors[l], linewidth=linewidths[l],
                       label=r'$\kappa_{sp}$=' + l) for l in labels_order]
legend_type = [
    Line2D([0], [0], color='gray', linestyle='-', linewidth=1.5, label='CCS (overnight)'),
    Line2D([0], [0], color='gray', linestyle='--', linewidth=1.5, label='MCS (megawatt)'),
]
ax.legend(handles=legend_kappa + legend_type, fontsize=7, loc='upper left', ncol=2)
ax.set_xlabel('Year')
ax.set_ylabel('Cumulative charge points')
ax.set_title('(b) CCS (solid) vs MCS (dashed) charge points')
ax.set_xlim(2028, 2060)
ax.grid(True, alpha=0.3)

# Panel (c): Max charge points at any single NUTS-2 node
ax = axes[2]
for label in labels_order:
    ax.plot(years, infra_data[label]['max_node_cp'], color=colors[label],
            linestyle=linestyles[label], linewidth=linewidths[label],
            marker='s', markersize=3,
            label=r'$\kappa_{space}$ = ' + label)
ax.set_xlabel('Year')
ax.set_ylabel('Max charge points (single NUTS-2 node)')
ax.set_title('(c) Peak regional deployment')
ax.set_xlim(2028, 2060)
ax.legend(fontsize=8, loc='upper left')
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(basedir + 'kspace_sensitivity_3panel.png', dpi=300, bbox_inches='tight')
plt.savefig(basedir + 'kspace_sensitivity_3panel.pdf', bbox_inches='tight')
print('Saved: kspace_sensitivity_3panel.png/.pdf')
plt.close()
