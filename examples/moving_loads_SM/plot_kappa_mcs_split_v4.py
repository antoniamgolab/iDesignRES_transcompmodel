"""
Two-panel figure illustrating the opposing pressures of kappa^pwr and kappa^space
on the MCS share of corridor-wide installed charging power.

Left panel  : MCS share vs kappa^pwr   (tightening kappa^pwr LOWERS MCS share)
Right panel: MCS share vs kappa^space (tightening kappa^space RAISES MCS share)

Also overlays BEV% and total MW to give context. Output:
  figures/kappa_mcs_split.pdf, .png
"""
import yaml, glob, re
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from collections import defaultdict

matplotlib.rcParams['font.family'] = 'sans-serif'
matplotlib.rcParams['font.sans-serif'] = ['Segoe UI', 'sans-serif']
matplotlib.rcParams['font.size'] = 12

BASE = Path(__file__).resolve().parent
FIG_DIR = BASE / 'figures'
FIG_DIR.mkdir(exist_ok=True)

ci3 = re.compile(r'CartesianIndex\((\d+),\s*(\d+),\s*(\d+)\):\s*([\d.eE+-]+)')
MODELED = list(range(2020, 2064, 4))
y_idx = {i + 1: y for i, y in enumerate(MODELED)}

TARGET_YEAR = 2048


def analyze(run_dir):
    qf = sorted(glob.glob(str(run_dir / '*_q_fuel_infr_plus_dict.yaml')))
    sf = run_dir / 'summary_stats.yaml'
    if not qf or not sf.exists():
        return None
    mcs_kw = 0
    ccs_kw = 0
    with open(qf[-1]) as f:
        for line in f:
            m = ci3.match(line.strip())
            if not m:
                continue
            yi, fi, pos = int(m.group(1)), int(m.group(2)), int(m.group(3))
            kw = float(m.group(4))
            if kw < 1e-3 or fi == 3:
                continue
            yr = y_idx.get(yi)
            if yr is None or yr > TARGET_YEAR:
                continue
            if fi == 1:    # MCS
                mcs_kw += kw
            elif fi == 2:  # CCS
                ccs_kw += kw
    total_kw = mcs_kw + ccs_kw
    mcs_share = mcs_kw / total_kw * 100 if total_kw > 0 else 0

    with open(sf) as f:
        s = yaml.safe_load(f)
    bev_pct = 0
    for k, v in s.get('tonnes_by_year', {}).items():
        try:
            yr = int(k)
        except Exception:
            continue
        if yr == TARGET_YEAR:
            b = float(v.get('BEV', 0))
            i = float(v.get('ICEV', 0))
            bev_pct = b / (b + i) * 100 if b + i > 0 else 0
            break
    return {
        'mcs_mw': mcs_kw / 1000,
        'ccs_mw': ccs_kw / 1000,
        'total_mw': total_kw / 1000,
        'mcs_share': mcs_share,
        'bev_pct': bev_pct,
    }


# ── Load both sweeps ──
KAPPA_RUNS = [
    (1e9,  'kpwr=Inf',       'results/v4/kappa_sensitivity/no_cap'),
    (0.5,  'kpwr=0.5 base',  'results/v4/uncertainty_scenarios/scenario_000'),
    (0.3,  'kpwr=0.3',       'results/v4/kappa_sensitivity/kappa_0.3'),
    (0.2,  'kpwr=0.2',       'results/v4/kappa_sensitivity/kappa_0.2'),
    (0.1,  'kpwr=0.1',       'results/v4/kappa_sensitivity/kappa_0.1'),
]
KSPACE_RUNS = [
    (1e-1,  'kspace=Inf',      'results/v4/kappa_sensitivity/no_space_cap'),
    (1e-3,  'kspace=0.001',    'results/v4/kappa_sensitivity/kspace_0.001'),
    (5e-4,  'kspace=0.0005 base', 'results/v4/uncertainty_scenarios/scenario_000'),
    (2e-4,  'kspace=0.0002',   'results/v4/kappa_sensitivity/kspace_0.0002'),
    (1e-4,  'kspace=0.0001',   'results/v4/kappa_sensitivity/kspace_0.0001'),
]

kappa_data = []
for val, lab, path in KAPPA_RUNS:
    r = analyze(BASE / path)
    if r is None:
        continue
    kappa_data.append((val, lab, r))

kspace_data = []
for val, lab, path in KSPACE_RUNS:
    r = analyze(BASE / path)
    if r is None:
        continue
    kspace_data.append((val, lab, r))

# ── Figure ──
fig, axes = plt.subplots(1, 2, figsize=(13, 5.2))

COL_MCS = '#5b4fa8'    # purple — MCS (as in Figure 5)
COL_CCS = '#d4a017'    # gold — CCS (as in Figure 5)
COL_BEV = '#2c6e99'    # navy — BEV %
BASE_HIGHLIGHT = '#e05050'

# ─ Panel (a): kappa^pwr sweep ─
ax = axes[0]
ax2 = ax.twinx()

x_kpwr = np.arange(len(kappa_data))
mcs_shares = [d[2]['mcs_share'] for d in kappa_data]
bev_pcts = [d[2]['bev_pct'] for d in kappa_data]
mcs_mw = [d[2]['mcs_mw'] for d in kappa_data]
ccs_mw = [d[2]['ccs_mw'] for d in kappa_data]
labels = [d[1].replace('kpwr=', '').replace(' base', '') for d in kappa_data]

# Stacked bars: MCS + CCS (left axis)
ax.bar(x_kpwr, mcs_mw, color=COL_MCS, alpha=0.75, edgecolor='white', linewidth=0.5,
       label='MCS MW', width=0.6)
ax.bar(x_kpwr, ccs_mw, bottom=mcs_mw, color=COL_CCS, alpha=0.75, edgecolor='white',
       linewidth=0.5, label='CCS MW', width=0.6)
# Highlight baseline
ax.axvspan(0.6, 1.4, color=BASE_HIGHLIGHT, alpha=0.08, zorder=0)
ax.text(1.0, ax.get_ylim()[1] if False else 880, 'baseline', ha='center', va='top',
        fontsize=10, color=BASE_HIGHLIGHT, fontweight='bold')

# MCS share on right axis
ax2.plot(x_kpwr, mcs_shares, '-o', color='#333333', linewidth=2.0, markersize=7,
         label='MCS share (%)', zorder=4)
# BEV% as a dashed grey line on right axis
ax2.plot(x_kpwr, bev_pcts, '--^', color=COL_BEV, linewidth=1.5, markersize=6,
         alpha=0.7, label='BEV share (%)', zorder=3)

ax.set_xticks(x_kpwr)
ax.set_xticklabels(labels, fontsize=11)
ax.set_ylabel('Corridor-wide installed power 2048 (MW)', fontsize=12)
ax2.set_ylabel('MCS / BEV share (%)', fontsize=12)
ax.set_xlabel(r'$\kappa^{\mathrm{pwr}}$ (per-period kW budget)', fontsize=12)
ax.set_title('(a) $\\kappa^{\\mathrm{pwr}}$ sweep — tightening LOWERS MCS share\n(MCS$\\to$CCS substitution)',
             fontsize=13)
ax.set_ylim(0, 1450)
ax2.set_ylim(0, 105)
ax.grid(True, alpha=0.2, axis='y')

# Combined legend
h1, l1 = ax.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax.legend(h1 + h2, l1 + l2, fontsize=10, loc='upper center', bbox_to_anchor=(0.5, -0.18), ncol=3, framealpha=0.92)

# ─ Panel (b): kappa^space sweep ─
ax = axes[1]
ax2 = ax.twinx()

x_ks = np.arange(len(kspace_data))
mcs_shares_s = [d[2]['mcs_share'] for d in kspace_data]
bev_pcts_s = [d[2]['bev_pct'] for d in kspace_data]
mcs_mw_s = [d[2]['mcs_mw'] for d in kspace_data]
ccs_mw_s = [d[2]['ccs_mw'] for d in kspace_data]
labels_s = [d[1].replace('kspace=', '').replace(' base', '') for d in kspace_data]

ax.bar(x_ks, mcs_mw_s, color=COL_MCS, alpha=0.75, edgecolor='white', linewidth=0.5,
       label='MCS MW', width=0.6)
ax.bar(x_ks, ccs_mw_s, bottom=mcs_mw_s, color=COL_CCS, alpha=0.75, edgecolor='white',
       linewidth=0.5, label='CCS MW', width=0.6)
ax.axvspan(1.6, 2.4, color=BASE_HIGHLIGHT, alpha=0.08, zorder=0)
ax.text(2.0, 880, 'baseline', ha='center', va='top',
        fontsize=10, color=BASE_HIGHLIGHT, fontweight='bold')

ax2.plot(x_ks, mcs_shares_s, '-o', color='#333333', linewidth=2.0, markersize=7,
         label='MCS share (%)', zorder=4)
ax2.plot(x_ks, bev_pcts_s, '--^', color=COL_BEV, linewidth=1.5, markersize=6,
         alpha=0.7, label='BEV share (%)', zorder=3)

ax.set_xticks(x_ks)
ax.set_xticklabels(labels_s, fontsize=11, rotation=10, ha='right')
ax.set_ylabel('Corridor-wide installed power 2048 (MW)', fontsize=12)
ax2.set_ylabel('MCS / BEV share (%)', fontsize=12)
ax.set_xlabel(r'$\kappa^{\mathrm{space}}$ (per-period charger-count budget)', fontsize=12)
ax.set_title('(b) $\\kappa^{\\mathrm{space}}$ sweep — tightening RAISES MCS share\n(no substitution; CCS suppressed)',
             fontsize=13)
ax.set_ylim(0, 1450)
ax2.set_ylim(0, 105)
ax.grid(True, alpha=0.2, axis='y')

h1, l1 = ax.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax.legend(h1 + h2, l1 + l2, fontsize=10, loc='upper center', bbox_to_anchor=(0.5, -0.18), ncol=3, framealpha=0.92)

plt.tight_layout()
out_pdf = FIG_DIR / 'kappa_mcs_split_v4.pdf'
out_png = FIG_DIR / 'kappa_mcs_split_v4.png'
plt.savefig(out_pdf, bbox_inches='tight', dpi=300)
plt.savefig(out_png, bbox_inches='tight', dpi=200)
print(f"Saved: {out_pdf.name}, {out_png.name}")
plt.close()
