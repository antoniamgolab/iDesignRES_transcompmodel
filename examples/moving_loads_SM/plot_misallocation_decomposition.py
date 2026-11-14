"""
DRAFT revised Figure 5(a) for reviewer comment R6-4 (does NOT replace misallocation_combined).

Separates the two effects in the Heuristic vs System-optimal comparison (Go RES):
  - One charger type (MCS-only run, BEV flows fixed to the canonical run -> same route energy):
    totals are equal -> difference is purely spatial
  - Two charger types (canonical run): total drops -> charger-type (overnight CCS) effect
"Same node" is evaluated per node regardless of charger type.
"""
import re, sys, yaml, glob
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from collections import defaultdict
from heuristic_charging import compute_heuristic_charging

matplotlib.rcParams['font.family'] = 'sans-serif'
matplotlib.rcParams['font.sans-serif'] = ['Segoe UI', 'sans-serif']
matplotlib.rcParams['font.size'] = 13

TARGET_YEAR = int(sys.argv[1]) if len(sys.argv) > 1 else 2040
RUNS = {'mcs_only': 'uncertainty_scenarios_v2_mcs_only_fixed_flows', 'canonical': 'uncertainty_scenarios_v2'}

base = 'input_data/uncertainty_scenarios_v2/scenario_000/'
paths = yaml.load(open(base + 'Path.yaml'), Loader=yaml.UnsafeLoader)
odpairs_raw = yaml.load(open(base + 'Odpair.yaml'), Loader=yaml.UnsafeLoader)
breaks_data = yaml.load(open(base + 'MandatoryBreaks.yaml'), Loader=yaml.UnsafeLoader)
path_seq = {int(p['id']): [int(x) for x in p['sequence']] for p in paths}
path_dist = {int(p['id']): [float(d) for d in p.get('distance_from_previous', [])] for p in paths}
od_path = {int(od['id']): int(od['path_id']) for od in odpairs_raw}
breaks_by_path = defaultdict(list)
is_rest = {}
for b in breaks_data:
    breaks_by_path[int(b['path_id'])].append(int(b['latest_geo_id']))
    is_rest[(int(b['path_id']), int(b['latest_geo_id']))] = b['break_duration'] >= 8.0


def heuristic(oid, pid, te):
    return compute_heuristic_charging(oid, pid, te, od_path, path_seq, path_dist, breaks_by_path)


gamma_ccs, gamma_mcs, H = 0.75, 0.23, 8760
MODELED_YEARS = list(range(2020, 2064, 4))
y_idx_to_year = {i + 1: y for i, y in enumerate(MODELED_YEARS)}
tuple_pat = re.compile(
    r'\((\d+),\s*\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\),\s*(\d+),\s*\((\d+),\s*(\d+)\),\s*(\d+)\):\s*([\d.eE+-]+)')
ci3_pat = re.compile(r'CartesianIndex\((\d+),\s*(\d+),\s*(\d+)\):\s*([\d.eE+-]+)')


def load(results_dir, all_mcs):
    route_energy = defaultdict(float)
    sf = sorted(glob.glob(f'results/{results_dir}/scenario_000/*_s_dict.yaml'))[-1]
    with open(sf) as f:
        for line in f:
            m = tuple_pat.match(line.strip())
            if not m or int(m.group(1)) != TARGET_YEAR: continue
            fu, inf, val = int(m.group(7)), int(m.group(8)), float(m.group(10))
            if val < 1e-6 or fu != 0 or inf not in {1, 2}: continue
            route_energy[(int(m.group(3)), int(m.group(4)))] += val
    h_ccs, h_mcs = defaultdict(float), defaultdict(float)
    for (oid, pid), te in route_energy.items():
        ap = od_path.get(oid, pid)
        for g, mwh in heuristic(oid, pid, te).items():
            if not all_mcs and is_rest.get((ap, g), False):
                h_ccs[g] += mwh / (gamma_ccs * H)
            else:
                h_mcs[g] += mwh / (gamma_mcs * H)
    # fi=1 -> MCS, fi=2 -> CCS (see memory: q-fuel-infr-plus-yaml-parsing)
    o_ccs, o_mcs = defaultdict(float), defaultdict(float)
    qf = sorted(glob.glob(f'results/{results_dir}/scenario_000/*_q_fuel_infr_plus_dict.yaml'))[-1]
    with open(qf) as f:
        for line in f:
            m = ci3_pat.match(line.strip())
            if not m: continue
            yi, fi, pos, val = int(m.group(1)), int(m.group(2)), int(m.group(3)), float(m.group(4))
            if val < 1e-3 or fi == 3 or y_idx_to_year[yi] > TARGET_YEAR: continue
            (o_ccs if fi == 2 else o_mcs)[pos - 1] += val / 1000
    # Same node regardless of charger type; overlap split by the optimum's type mix at that node
    same_ccs = same_mcs = 0.0
    for g in set(o_ccs) | set(o_mcs) | set(h_ccs) | set(h_mcs):
        o_tot = o_ccs[g] + o_mcs[g]
        if o_tot <= 0: continue
        ov = min(o_tot, h_ccs[g] + h_mcs[g])
        same_ccs += ov * o_ccs[g] / o_tot
        same_mcs += ov * o_mcs[g] / o_tot
    oC, oM = sum(o_ccs.values()), sum(o_mcs.values())
    return dict(energy=sum(route_energy.values()) / 1000,
                h_ccs=sum(h_ccs.values()), h_mcs=sum(h_mcs.values()),
                same_ccs=same_ccs, same_mcs=same_mcs, diff_ccs=oC - same_ccs, diff_mcs=oM - same_mcs)


res = {k: load(d, all_mcs=(k == 'mcs_only')) for k, d in RUNS.items()}
for k, r in res.items():
    print(k, {kk: round(v, 1) for kk, v in r.items()})

# ══════════════════════════════════════════════════════════════════════
# FIGURE
# ══════════════════════════════════════════════════════════════════════
CCS_COL = '#d4a017'
MCS_COL = '#5b4fa8'
fig, ax = plt.subplots(figsize=(11, 6.5))
bar_w = 0.7
x = {'mcs_only': (0, 0.9), 'canonical': (2.6, 3.5)}


def seg(xpos, bottom, h, col, hatched):
    if h <= 0.05: return bottom
    if hatched:
        ax.bar(xpos, h, bar_w, bottom=bottom, color=col, alpha=0.3, edgecolor=col, linewidth=1.0, hatch='///')
    else:
        ax.bar(xpos, h, bar_w, bottom=bottom, color=col, alpha=0.85, edgecolor='white', linewidth=2)
    return bottom + h


for k, r in res.items():
    xh, xo = x[k]
    top_h = seg(xh, seg(xh, 0, r['h_ccs'], CCS_COL, False), r['h_mcs'], MCS_COL, False)
    b = seg(xo, 0, r['same_ccs'], CCS_COL, False)
    same = seg(xo, b, r['same_mcs'], MCS_COL, False)
    b = seg(xo, same, r['diff_ccs'], CCS_COL, True)
    top_o = seg(xo, b, r['diff_mcs'], MCS_COL, True)
    for xx, t in ((xh, top_h), (xo, top_o)):
        ax.text(xx, t + 4, f'{t:.0f} MW', ha='center', va='bottom', fontsize=13, fontweight='bold')
    diff = top_o - same
    # Brackets right of the System-optimal bar: same nodes / different nodes
    bx = xo + bar_w / 2 + 0.05
    for lo, hi, lab in ((0, same, f'same nodes\n{same:.0f} MW'),
                        (same, top_o, f'different\nnodes\n{diff:.0f} MW ({diff / top_o:.0%})')):
        ax.annotate('', xy=(bx, lo + 1), xytext=(bx, hi - 1), arrowprops=dict(arrowstyle='<->', color='#555', lw=1.2))
        ax.text(bx + 0.06, (lo + hi) / 2, lab, fontsize=10, va='center', ha='left', color='#333')
    title = 'One charger type\n(MCS only, same BET fleet)' if k == 'mcs_only' else 'Two charger types\n(CCS + MCS, as in paper)'
    ax.text((xh + xo) / 2, -0.17, title, ha='center', va='top', fontsize=13, fontweight='bold',
            transform=ax.get_xaxis_transform())
    ax.text((xh + xo) / 2, -0.30, f'BET charging: {r["energy"]:.0f} GWh', ha='center', va='top', fontsize=10,
            color='#555', transform=ax.get_xaxis_transform())
    effect = top_o - top_h
    effect = 0.0 if abs(effect) < 0.5 else effect  # avoid "-0 MW"
    yb = max(top_h, top_o) + 42
    ax.plot([xh, xh, xo, xo], [top_h + 30, yb, yb, top_o + 30], color='#888', lw=1)
    ax.text((xh + xo) / 2, yb + 3, f'total: {effect:+.0f} MW ({effect / top_h:+.0%})', ha='center', va='bottom',
            fontsize=11, color='#333')

ax.set_xticks([v for pair in x.values() for v in pair])
ax.set_xticklabels(['Heuristic', 'System-\noptimal'] * 2, fontsize=12)
ax.axvline(1.95, color='#ccc', lw=1)
ax.set_ylabel('Cumulative charging infrastructure (MW)', fontsize=13)
ax.set_title(f'Spatial relocation vs. charger-type effect (Go RES, {TARGET_YEAR})', fontsize=15)
ax.set_ylim(0, max(r['h_ccs'] + r['h_mcs'] for r in res.values()) * 1.32)
ax.grid(True, alpha=0.15, axis='y')
ax.spines[['top', 'right']].set_visible(False)
ax.legend(handles=[
    Patch(facecolor=CCS_COL, alpha=0.85, label='CCS (overnight)'),
    Patch(facecolor=MCS_COL, alpha=0.85, label='MCS (megawatt)'),
    Patch(facecolor='#999', alpha=0.3, hatch='///', edgecolor='#666', label='capacity beyond Heuristic at that node (different location)'),
], fontsize=10, loc='upper center', bbox_to_anchor=(0.5, -0.36), ncol=2, framealpha=0.9)

plt.tight_layout()
out = f'figures/misallocation_decomposition_DRAFT_{TARGET_YEAR}'
plt.savefig(out + '.pdf', bbox_inches='tight', dpi=300)
plt.savefig(out + '.png', bbox_inches='tight', dpi=300)
print(f'Saved: {out}.pdf/.png')
