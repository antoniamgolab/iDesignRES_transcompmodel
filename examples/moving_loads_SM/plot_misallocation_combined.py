"""
Combined misallocation figure:
(a) Stacked bars: consistent infra (bottom, solid) + differently allocated (top, hatched)
(b) Latitude comparison: system-optimal vs heuristic spatial distribution
"""
import re, yaml, glob
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from collections import defaultdict
from scipy.ndimage import gaussian_filter1d
from heuristic_charging import compute_heuristic_charging

matplotlib.rcParams['font.family'] = 'sans-serif'
matplotlib.rcParams['font.sans-serif'] = ['Segoe UI', 'sans-serif']
matplotlib.rcParams['font.size'] = 15

with open('input_data/fixed_nuts_2/GeographicElement.yaml') as f:
    geo_data = yaml.safe_load(f)
geo_country = {g['id']: g.get('country', '??') for g in geo_data}
geo_lat = {g['id']: g.get('coordinate_lat', 0) for g in geo_data}
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

TARGET_YEAR = 2040

# ── Load energy (for latitude plot) ──
sf_s = sorted(glob.glob('results/uncertainty_scenarios_v2/scenario_000/*_s_dict.yaml'))
opt_energy = defaultdict(float)
route_energy = defaultdict(float)
with open(sf_s[-1]) as f:
    for line in f:
        m = tuple_pat.match(line.strip())
        if not m: continue
        if int(m.group(1)) != TARGET_YEAR: continue
        oid, pid, gid = int(m.group(3)), int(m.group(4)), int(m.group(5))
        fu, inf = int(m.group(7)), int(m.group(8))
        val = float(m.group(10))
        if val < 1e-6 or fu != 0 or inf not in {1, 2}: continue
        opt_energy[gid] += val
        route_energy[(oid, pid)] += val

heur_energy = defaultdict(float)
heur_ccs_geo = defaultdict(float)
heur_mcs_geo = defaultdict(float)
for (oid, pid), te in route_energy.items():
    if te < 1e-6: continue
    actual_pid = od_path.get(oid, pid)
    for g, mwh in compute_heuristic_charging(oid, pid, te, od_path, path_seq, path_dist, breaks_by_path).items():
        heur_energy[g] += mwh
        if is_rest.get((actual_pid, g), False):
            heur_ccs_geo[g] += mwh * 1000 / (gamma_ccs * 8760) / 1000
        else:
            heur_mcs_geo[g] += mwh * 1000 / (gamma_mcs * 8760) / 1000

# Rail energy
sf_s_rail = sorted(glob.glob('results/uncertainty_scenarios_v2_rail/scenario_000/*_s_dict.yaml'))
rail_energy = defaultdict(float)
with open(sf_s_rail[-1]) as f:
    for line in f:
        m = tuple_pat.match(line.strip())
        if not m: continue
        if int(m.group(1)) != TARGET_YEAR: continue
        gid = int(m.group(5))
        fu, inf = int(m.group(7)), int(m.group(8))
        val = float(m.group(10))
        if val < 1e-6 or fu != 0 or inf not in {1, 2}: continue
        rail_energy[gid] += val

# ── Load infra ──
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
        if yr and yr <= TARGET_YEAR:
            # fi=2 -> CCS (100 kW), fi=1 -> MCS (1000 kW); see memory: q-fuel-infr-plus-yaml-parsing
            if fi == 2: opt_ccs[pos - 1] += val / 1000
            elif fi == 1: opt_mcs[pos - 1] += val / 1000

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
        if yr and yr <= TARGET_YEAR:
            if fi == 2: rail_ccs[pos - 1] += val / 1000
            elif fi == 1: rail_mcs[pos - 1] += val / 1000

# ── Totals ──
h_ccs = sum(heur_ccs_geo.values())
h_mcs = sum(heur_mcs_geo.values())
o_ccs = sum(opt_ccs.values())
o_mcs = sum(opt_mcs.values())
r_ccs = sum(rail_ccs.values())
r_mcs = sum(rail_mcs.values())

# Per-node: what's consistent (min of planned and heuristic) vs different
def consistent_split(plan_ccs, plan_mcs, ref_ccs, ref_mcs):
    cons_ccs = sum(min(plan_ccs.get(g, 0), ref_ccs.get(g, 0)) for g in all_geo_ids)
    cons_mcs = sum(min(plan_mcs.get(g, 0), ref_mcs.get(g, 0)) for g in all_geo_ids)
    diff_ccs = sum(plan_ccs.values()) - cons_ccs
    diff_mcs = sum(plan_mcs.values()) - cons_mcs
    return cons_ccs, cons_mcs, diff_ccs, diff_mcs

cons_ccs_o, cons_mcs_o, diff_ccs_o, diff_mcs_o = consistent_split(opt_ccs, opt_mcs, heur_ccs_geo, heur_mcs_geo)
cons_ccs_r, cons_mcs_r, diff_ccs_r, diff_mcs_r = consistent_split(rail_ccs, rail_mcs, heur_ccs_geo, heur_mcs_geo)

print(f"Heuristic: CCS={h_ccs:.0f}, MCS={h_mcs:.0f}, Total={h_ccs+h_mcs:.0f}")
print(f"Optimal:   consistent CCS={cons_ccs_o:.0f} + diff={diff_ccs_o:.0f}, consistent MCS={cons_mcs_o:.0f} + diff={diff_mcs_o:.0f}")
print(f"Rail:      consistent CCS={cons_ccs_r:.0f} + diff={diff_ccs_r:.0f}, consistent MCS={cons_mcs_r:.0f} + diff={diff_mcs_r:.0f}")

# ══════════════════════════════════════════════════════════════════════
# FIGURE
# ══════════════════════════════════════════════════════════════════════
fig, axes = plt.subplots(1, 2, figsize=(11, 6.5), gridspec_kw={'width_ratios': [1, 1]})

CCS_COL = '#d4a017'
MCS_COL = '#5b4fa8'
COL_OPT = '#1a5276'
COL_HEUR = '#c4956a'

# ── Panel (a): Stacked bars (heuristic vs system-optimal) ──
ax = axes[0]
x = np.array([0, 1.2])
bar_w = 0.7

# Bar 1: Heuristic (solid)
ax.bar(x[0], h_ccs, bar_w, color=CCS_COL, alpha=0.85, edgecolor='white', linewidth=0.5)
ax.bar(x[0], h_mcs, bar_w, bottom=h_ccs, color=MCS_COL, alpha=0.85, edgecolor='white', linewidth=0.5)

# Bar 2: System-optimal — consistent at bottom, different on top
ax.bar(x[1], cons_ccs_o, bar_w, color=CCS_COL, alpha=0.85, edgecolor='white', linewidth=0.5)
ax.bar(x[1], cons_mcs_o, bar_w, bottom=cons_ccs_o, color=MCS_COL, alpha=0.85, edgecolor='white', linewidth=0.5)
base_diff = cons_ccs_o + cons_mcs_o
ax.bar(x[1], diff_ccs_o, bar_w, bottom=base_diff, color=CCS_COL, alpha=0.3,
       edgecolor=CCS_COL, linewidth=1.0, hatch='///')
ax.bar(x[1], diff_mcs_o, bar_w, bottom=base_diff + diff_ccs_o, color=MCS_COL, alpha=0.3,
       edgecolor=MCS_COL, linewidth=1.0, hatch='///')

# Labels
labels_a = ['Heuristic\n(reference)', 'System-\noptimal']
totals = [h_ccs + h_mcs, o_ccs + o_mcs]
diffs = [0, diff_ccs_o + diff_mcs_o]

for i in range(2):
    ax.text(x[i], totals[i] + 3, f'{totals[i]:.0f} MW', ha='center', va='bottom',
           fontsize=14, fontweight='bold')
    if diffs[i] > 0:
        pct = diffs[i] / totals[i] * 100
        mid = totals[i] - diffs[i] / 2
        ax.text(x[i], mid, f'{diffs[i]:.0f} MW\n({pct:.0f}%)',
               ha='center', va='center', fontsize=12, color='#333', fontweight='bold')

# Bracket for consistent part
cons_o = cons_ccs_o + cons_mcs_o
ax.annotate('', xy=(x[1] + bar_w/2 + 0.05, 0), xytext=(x[1] + bar_w/2 + 0.05, cons_o),
           arrowprops=dict(arrowstyle='<->', color='#555', lw=1.5))
ax.text(x[1] + bar_w/2 + 0.12, cons_o / 2, f'same locations\nas Heuristic\n{cons_o:.0f} MW',
       fontsize=13, va='center', ha='left', color='#333', fontweight='bold')

ax.set_xticks(x)
ax.set_xticklabels(labels_a, fontsize=13)
ax.set_ylabel('Cumulative charging infrastructure (MW)', fontsize=14)
ax.set_title(f'(a) Charging infrastructure allocation\n(Go RES, {TARGET_YEAR})', fontsize=16)
ax.set_ylim(0, 300)
ax.grid(True, alpha=0.15, axis='y')

# Legend below
legend_items = [
    Patch(facecolor=CCS_COL, alpha=0.85, label='CCS (overnight)'),
    Patch(facecolor=MCS_COL, alpha=0.85, label='MCS (megawatt)'),
    Patch(facecolor=CCS_COL, alpha=0.3, hatch='///', edgecolor=CCS_COL, label='CCS differently allocated'),
    Patch(facecolor=MCS_COL, alpha=0.3, hatch='///', edgecolor=MCS_COL, label='MCS differently allocated'),
]
ax.legend(handles=legend_items, fontsize=10, loc='upper center',
         bbox_to_anchor=(0.5, -0.1), ncol=2, framealpha=0.9)

# ── Panel (b): Latitude comparison ──
ax = axes[1]
sigma = 1.2
country_lats = {'IT': 42.5, 'AT': 47.5, 'DE': 51.0, 'DK': 56.0, 'SE': 62.0, 'NO': 64.0}

COL_RAIL = '#2e7d32'

# ── Panel (b): Latitude — heuristic vs system-optimal ──
ax = axes[1]
for label, geo_dict, color, ls, lw in [
    ('System-optimal', opt_energy, COL_OPT, '-', 2.0),
    ('Heuristic', heur_energy, COL_HEUR, '--', 1.8),
]:
    e_by_lat = defaultdict(float)
    for gid, mwh in geo_dict.items():
        lat = geo_lat.get(gid)
        if lat is not None:
            e_by_lat[lat] += mwh
    lats = np.array(sorted(e_by_lat.keys()))
    vals = np.array([e_by_lat[l] for l in lats])
    total = vals.sum()
    vals_norm = vals / total * 100 if total > 0 else vals
    vals_smooth = gaussian_filter1d(vals_norm, sigma)
    ax.fill_betweenx(lats, 0, vals_smooth, alpha=0.15, color=color)
    ax.plot(vals_smooth, lats, color=color, linewidth=lw, linestyle=ls, label=label)

ax.set_ylabel('Latitude')
ax.set_xlabel('Share of total charging demand (%)')
ax.set_title(f'(b) Heuristic vs system-optimal\n(Go RES, {TARGET_YEAR})', fontsize=14)
ax.legend(fontsize=11, loc='upper center')
ax.grid(True, alpha=0.2)
for c, lat in country_lats.items():
    ax.axhline(y=lat, color='gray', linestyle=':', alpha=0.3, linewidth=0.5)
    ax.text(ax.get_xlim()[1] * 0.95, lat, c, fontsize=10, ha='right', va='center', color='gray')


plt.tight_layout()
plt.savefig('figures/misallocation_combined.pdf', bbox_inches='tight', dpi=300)
plt.savefig('figures/misallocation_combined.png', bbox_inches='tight', dpi=300)
print("Saved: figures/misallocation_combined.pdf/.png")
plt.close()
