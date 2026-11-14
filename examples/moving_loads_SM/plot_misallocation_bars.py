"""
Misallocation summary: stacked CCS+MCS bars showing correctly placed vs misallocated.
Bar 1: Heuristic (reference, fully solid)
Bar 2: System-optimal (solid = correctly placed, hatched = at different location)
Bar 3: System-optimal + Rail (same treatment)
"""
import re, yaml, glob
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from collections import defaultdict
from heuristic_charging import compute_heuristic_charging

matplotlib.rcParams['font.family'] = 'sans-serif'
matplotlib.rcParams['font.sans-serif'] = ['Segoe UI', 'sans-serif']
matplotlib.rcParams['font.size'] = 15

with open('input_data/fixed_nuts_2/GeographicElement.yaml') as f:
    geo_data = yaml.safe_load(f)
geo_country = {g['id']: g.get('country', '??') for g in geo_data}
all_geo_ids = [g['id'] for g in geo_data if g.get('type') == 'node']

with open('input_data/uncertainty_scenarios_v2/scenario_000/Path.yaml') as f:
    paths = yaml.load(f, Loader=yaml.UnsafeLoader)
with open('input_data/uncertainty_scenarios_v2/scenario_000/Odpair.yaml') as f:
    odpairs_raw = yaml.load(f, Loader=yaml.UnsafeLoader)
with open('input_data/uncertainty_scenarios_v2/scenario_000/MandatoryBreaks.yaml') as f:
    breaks_data = yaml.load(f, Loader=yaml.UnsafeLoader)

path_seq = {int(p['id']): [int(x) for x in p['sequence']] for p in paths}
path_dist = {int(p['id']): [float(d) for d in p.get('distance_from_previous', [])] for p in paths}
od_path = {int(od['id']): int(od['path_id']) for od in odpairs_raw}
breaks_by_path = defaultdict(list)
for brk in breaks_data:
    breaks_by_path[int(brk['path_id'])].append(int(brk['latest_geo_id']))
is_rest = {}
for mb in breaks_data:
    is_rest[(int(mb['path_id']), int(mb['latest_geo_id']))] = mb['break_duration'] >= 8.0

gamma_ccs = 0.75
gamma_mcs = 0.23
MODELED_YEARS = list(range(2020, 2064, 4))
y_idx_to_year = {i + 1: y for i, y in enumerate(MODELED_YEARS)}
tuple_pat = re.compile(
    r'\((\d+),\s*\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\),\s*(\d+),\s*\((\d+),\s*(\d+)\),\s*(\d+)\):\s*([\d.eE+-]+)')
ci3_pat = re.compile(r'CartesianIndex\((\d+),\s*(\d+),\s*(\d+)\):\s*([\d.eE+-]+)')

# ── Load heuristic infra ──
sf_s = sorted(glob.glob('results/uncertainty_scenarios_v2/scenario_000/*_s_dict.yaml'))
route_energy = defaultdict(float)
with open(sf_s[-1]) as f:
    for line in f:
        m = tuple_pat.match(line.strip())
        if not m: continue
        if int(m.group(1)) != 2040: continue
        oid, pid = int(m.group(3)), int(m.group(4))
        fu, inf = int(m.group(7)), int(m.group(8))
        val = float(m.group(10))
        if val < 1e-6 or fu != 0 or inf not in {1, 2}: continue
        route_energy[(oid, pid)] += val

heur_ccs = defaultdict(float)
heur_mcs = defaultdict(float)
for (oid, pid), te in route_energy.items():
    if te < 1e-6: continue
    actual_pid = od_path.get(oid, pid)
    for g, mwh in compute_heuristic_charging(oid, pid, te, od_path, path_seq, path_dist, breaks_by_path).items():
        if is_rest.get((actual_pid, g), False):
            heur_ccs[g] += mwh * 1000 / (gamma_ccs * 8760) / 1000
        else:
            heur_mcs[g] += mwh * 1000 / (gamma_mcs * 8760) / 1000

# ── Load optimal infra ──
sf_q = sorted(glob.glob('results/uncertainty_scenarios_v2/scenario_000/*_q_fuel_infr_plus_dict.yaml'))
opt_ccs = defaultdict(float)
opt_mcs = defaultdict(float)
with open(sf_q[-1]) as f:
    for line in f:
        m = ci3_pat.match(line.strip())
        if not m: continue
        yi, fi, pos = int(m.group(1)), int(m.group(2)), int(m.group(3))
        val = float(m.group(4))
        if val < 1e-3 or fi == 3: continue
        yr = y_idx_to_year.get(yi)
        if yr and yr <= 2040:
            if fi == 2: opt_ccs[pos - 1] += val / 1000
            elif fi == 1: opt_mcs[pos - 1] += val / 1000

# ── Load rail infra ──
sf_q_r = sorted(glob.glob('results/uncertainty_scenarios_v2_rail/scenario_000/*_q_fuel_infr_plus_dict.yaml'))
rail_ccs = defaultdict(float)
rail_mcs = defaultdict(float)
with open(sf_q_r[-1]) as f:
    for line in f:
        m = ci3_pat.match(line.strip())
        if not m: continue
        yi, fi, pos = int(m.group(1)), int(m.group(2)), int(m.group(3))
        val = float(m.group(4))
        if val < 1e-3 or fi == 3: continue
        yr = y_idx_to_year.get(yi)
        if yr and yr <= 2040:
            if fi == 2: rail_ccs[pos - 1] += val / 1000
            elif fi == 1: rail_mcs[pos - 1] += val / 1000

# ── Compute totals and misallocation ──
h_ccs = sum(heur_ccs.values())
h_mcs = sum(heur_mcs.values())

o_ccs = sum(opt_ccs.values())
o_mcs = sum(opt_mcs.values())
mis_ccs_o = sum(abs(opt_ccs.get(g, 0) - heur_ccs.get(g, 0)) for g in all_geo_ids) / 2
mis_mcs_o = sum(abs(opt_mcs.get(g, 0) - heur_mcs.get(g, 0)) for g in all_geo_ids) / 2

r_ccs = sum(rail_ccs.values())
r_mcs = sum(rail_mcs.values())
mis_ccs_r = sum(abs(rail_ccs.get(g, 0) - heur_ccs.get(g, 0)) for g in all_geo_ids) / 2
mis_mcs_r = sum(abs(rail_mcs.get(g, 0) - heur_mcs.get(g, 0)) for g in all_geo_ids) / 2

print(f"Heuristic:     CCS={h_ccs:.0f}, MCS={h_mcs:.0f}, Total={h_ccs+h_mcs:.0f} MW")
print(f"Sys-optimal:   CCS={o_ccs:.0f}, MCS={o_mcs:.0f}, Total={o_ccs+o_mcs:.0f} MW")
print(f"  misalloc:    CCS={mis_ccs_o:.0f}, MCS={mis_mcs_o:.0f}, Total={mis_ccs_o+mis_mcs_o:.0f} MW")
print(f"Road+Rail:     CCS={r_ccs:.0f}, MCS={r_mcs:.0f}, Total={r_ccs+r_mcs:.0f} MW")
print(f"  misalloc:    CCS={mis_ccs_r:.0f}, MCS={mis_mcs_r:.0f}, Total={mis_ccs_r+mis_mcs_r:.0f} MW")

# ══════════════════════════════════════════════════════════════════════
# FIGURE
# ══════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(10, 6))

CCS_COL = '#d4a017'   # golden for CCS
MCS_COL = '#5b4fa8'   # purple for MCS

x = np.array([0, 1.2, 2.4])
bar_w = 0.7
labels = ['Heuristic\n(reference)', 'System-\noptimal', 'System-optimal\n+ rail']

# Bar 1: Heuristic - fully solid
ax.bar(x[0], h_ccs, bar_w, color=CCS_COL, alpha=0.85, edgecolor='white', linewidth=0.5)
ax.bar(x[0], h_mcs, bar_w, bottom=h_ccs, color=MCS_COL, alpha=0.85, edgecolor='white', linewidth=0.5)

# Bar 2: System-optimal
# Correctly placed portion (solid)
correct_ccs_o = o_ccs - mis_ccs_o
correct_mcs_o = o_mcs - mis_mcs_o
# CCS solid
ax.bar(x[1], correct_ccs_o, bar_w, color=CCS_COL, alpha=0.85, edgecolor='white', linewidth=0.5)
# CCS misallocated (hatched)
ax.bar(x[1], mis_ccs_o, bar_w, bottom=correct_ccs_o, color=CCS_COL, alpha=0.25,
       edgecolor=CCS_COL, linewidth=1.0, hatch='///')
# MCS solid
ax.bar(x[1], correct_mcs_o, bar_w, bottom=o_ccs, color=MCS_COL, alpha=0.85, edgecolor='white', linewidth=0.5)
# MCS misallocated (hatched)
ax.bar(x[1], mis_mcs_o, bar_w, bottom=o_ccs + correct_mcs_o, color=MCS_COL, alpha=0.25,
       edgecolor=MCS_COL, linewidth=1.0, hatch='///')

# Bar 3: Road+Rail
correct_ccs_r = r_ccs - mis_ccs_r
correct_mcs_r = r_mcs - mis_mcs_r
ax.bar(x[2], correct_ccs_r, bar_w, color=CCS_COL, alpha=0.85, edgecolor='white', linewidth=0.5)
ax.bar(x[2], mis_ccs_r, bar_w, bottom=correct_ccs_r, color=CCS_COL, alpha=0.25,
       edgecolor=CCS_COL, linewidth=1.0, hatch='///')
ax.bar(x[2], correct_mcs_r, bar_w, bottom=r_ccs, color=MCS_COL, alpha=0.85, edgecolor='white', linewidth=0.5)
ax.bar(x[2], mis_mcs_r, bar_w, bottom=r_ccs + correct_mcs_r, color=MCS_COL, alpha=0.25,
       edgecolor=MCS_COL, linewidth=1.0, hatch='///')

# Total labels on top
totals_list = [(h_ccs+h_mcs, 0), (o_ccs+o_mcs, mis_ccs_o+mis_mcs_o), (r_ccs+r_mcs, mis_ccs_r+mis_mcs_r)]
for i, (total, mis) in enumerate(totals_list):
    ax.text(x[i], total + 3, f'{total:.0f} MW', ha='center', va='bottom', fontsize=14, fontweight='bold')
    if mis > 0:
        pct = mis / total * 100
        # Place misalloc text inside the hatched region
        mid_y = total - mis/2
        ax.text(x[i], mid_y, f'{mis:.0f} MW\n({pct:.0f}%)',
               ha='center', va='center', fontsize=12, color='#333', fontweight='bold')

ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=14)
ax.set_ylabel('Cumulative charging infrastructure (MW)', fontsize=15)
ax.set_title('Infrastructure allocation: heuristic vs system-optimal\n(Go RES, 2040)', fontsize=16)
ax.set_ylim(0, 310)
ax.grid(True, alpha=0.15, axis='y')

# Legend
legend_items = [
    Patch(facecolor=CCS_COL, alpha=0.85, label='CCS (overnight)'),
    Patch(facecolor=MCS_COL, alpha=0.85, label='MCS (megawatt)'),
    Patch(facecolor='gray', alpha=0.25, hatch='///', edgecolor='gray', label='Differently allocated\nvs heuristic'),
]
ax.legend(handles=legend_items, fontsize=12, loc='upper center',
         bbox_to_anchor=(0.5, -0.1), ncol=3, framealpha=0.9)

plt.tight_layout()
plt.savefig('figures/misallocation_bars.pdf', bbox_inches='tight', dpi=300)
plt.savefig('figures/misallocation_bars.png', bbox_inches='tight', dpi=300)
print("Saved: figures/misallocation_bars.pdf/.png")
plt.close()
