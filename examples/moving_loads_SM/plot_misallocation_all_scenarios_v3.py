"""
Boxplot of per-node misallocation (heuristic vs optimal) across all 8 runs.
4 road-only + 4 rail scenarios.
"""
import re, yaml, glob
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from collections import defaultdict
from heuristic_charging import compute_heuristic_charging

matplotlib.rcParams['font.family'] = 'sans-serif'
matplotlib.rcParams['font.sans-serif'] = ['Segoe UI', 'sans-serif']
matplotlib.rcParams['font.size'] = 16

with open('input_data/fixed_nuts_2/GeographicElement.yaml') as f:
    geo_data = yaml.safe_load(f)
geo_country = {g['id']: g.get('country', '??') for g in geo_data}
geo_names = {g['id']: g.get('name', '??').replace('nuts2_', '') for g in geo_data}
all_geo_ids = [g['id'] for g in geo_data if g.get('type') == 'node']

with open('input_data/uncertainty_scenarios_v2_night/scenario_000/Path.yaml') as f:
    paths = yaml.load(f, Loader=yaml.UnsafeLoader)
with open('input_data/uncertainty_scenarios_v2_night/scenario_000/Odpair.yaml') as f:
    odpairs_raw = yaml.load(f, Loader=yaml.UnsafeLoader)
with open('input_data/uncertainty_scenarios_v2_night/scenario_000/MandatoryBreaks.yaml') as f:
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

SC_NAMES = {
    'scenario_000': 'Go RES', 'scenario_001': 'NECP',
    'scenario_002': 'REPowerEU++', 'scenario_003': 'Trinity',
}

RUNS = []
for sc_id in ['scenario_000', 'scenario_001', 'scenario_002', 'scenario_003']:
    RUNS.append(('Road', sc_id, ('results/uncertainty_scenarios_v2_night/scenario_000' if sc_id == 'scenario_000' else f'results/v3/uncertainty_scenarios/{sc_id}')))

# Compute deltas for all runs
outlier_threshold = 5
all_deltas = {}
all_over_count = defaultdict(int)
all_under_count = defaultdict(int)

for mode, sc_id, path in RUNS:
    sf_q = sorted(glob.glob(f'{path}/*_q_fuel_infr_plus_dict.yaml'))
    sf_s = sorted(glob.glob(f'{path}/*_s_dict.yaml'))
    if not sf_q or not sf_s:
        continue

    opt_infra = defaultdict(float)
    with open(sf_q[-1]) as f:
        for line in f:
            m = ci3_pat.match(line.strip())
            if not m: continue
            yi, fi, pos = int(m.group(1)), int(m.group(2)), int(m.group(3))
            val = float(m.group(4))
            if val < 1e-3 or fi == 3: continue
            yr = y_idx_to_year.get(yi)
            if yr and yr <= 2040:
                opt_infra[pos - 1] += val / 1000

    route_energy = defaultdict(float)
    with open(sf_s[-1]) as f:
        for line in f:
            m = tuple_pat.match(line.strip())
            if not m: continue
            yr = int(m.group(1))
            if yr != 2040: continue
            oid, pid = int(m.group(3)), int(m.group(4))
            fu, inf = int(m.group(7)), int(m.group(8))
            val = float(m.group(10))
            if val < 1e-6 or fu != 0 or inf not in {1, 2}: continue
            route_energy[(oid, pid)] += val

    heur_infra = defaultdict(float)
    for (oid, pid), te in route_energy.items():
        if te < 1e-6: continue
        actual_pid = od_path.get(oid, pid)
        heur_alloc = compute_heuristic_charging(oid, pid, te, od_path, path_seq, path_dist, breaks_by_path)
        for g, mwh in heur_alloc.items():
            if is_rest.get((actual_pid, g), False):
                heur_infra[g] += mwh * 1000 / (gamma_ccs * 8760) / 1000
            else:
                heur_infra[g] += mwh * 1000 / (gamma_mcs * 8760) / 1000

    deltas = [heur_infra.get(g, 0) - opt_infra.get(g, 0) for g in all_geo_ids]
    key = f"{mode}_{sc_id}"
    all_deltas[key] = deltas

    for j, d in enumerate(deltas):
        if d > outlier_threshold: all_over_count[all_geo_ids[j]] += 1
        if d < -outlier_threshold: all_under_count[all_geo_ids[j]] += 1

# Consistent outliers (in 4+ of 8 runs)
consistent = set()
for g in all_geo_ids:
    if all_over_count.get(g, 0) >= 3 or all_under_count.get(g, 0) >= 3:
        consistent.add(g)

# ── FIGURE ──
print("Building figure...")
keys = list(all_deltas.keys())
data = [all_deltas[k] for k in keys]
# X-tick labels: just the scenario name (no Road/Rail prefix)
labels = [SC_NAMES[k.split('_', 1)[1]] for k in keys]

road_colors = ['#c4956a', '#9b7fb5', '#7aafc4', '#c4956a']
rail_colors = ['#7a9e5a', '#5a8e4a', '#4a7e3a', '#7a9e5a']
colors = road_colors

fig, ax = plt.subplots(figsize=(10, 7))

np.random.seed(42)
bp = ax.boxplot(data, vert=True, patch_artist=True, showfliers=False,
                widths=0.5, medianprops=dict(color='black', linewidth=2))

for i, (patch, color) in enumerate(zip(bp['boxes'], colors)):
    patch.set_facecolor(color)
    patch.set_alpha(0.4)

# Only show DE+AT and IT, gray out the rest
country_colors = {
    'DE': '#5b4fa8',                      # purple for DE
    'AT': '#d4a017',                      # golden yellow for AT
    'IT': '#e05050',                      # strong red for IT
}
other_color = '#cccccc'

# Scatter colored by country group, diamonds for consistent outliers
for i, d in enumerate(data):
    jitter = np.random.uniform(-0.15, 0.15, len(d))
    x_pos = np.full(len(d), i + 1) + jitter

    for j in range(len(d)):
        g = all_geo_ids[j]
        c = geo_country.get(g, '??')
        if c in ('DE', 'AT'):
            cc = country_colors.get(c, other_color)
        elif c == 'IT':
            cc = country_colors['IT']
        else:
            cc = other_color

        if g in consistent:
            ax.scatter(x_pos[j], d[j], color=cc, alpha=0.95, s=60, zorder=4,
                      marker='D', edgecolors='#333333', linewidths=1.0)
        else:
            if c in ('DE', 'AT', 'IT'):
                ax.scatter(x_pos[j], d[j], color=cc, alpha=0.5, s=22, zorder=3, marker='o')
            else:
                ax.scatter(x_pos[j], d[j], color=cc, alpha=0.2, s=12, zorder=2, marker='o')

ax.axhline(y=0, color='black', linewidth=0.5)


ax.set_xticklabels(labels, fontsize=12)
ax.set_ylabel('Deviation per NUTS-2 node (MW)\n(Heuristic $-$ System-optimal)', fontsize=16)
ax.set_title('Charging infrastructure misallocation across all scenarios (2040)', fontsize=18)
ax.grid(True, alpha=0.15, axis='y')

ax.text(0.5, 0.98, 'overbuilt', transform=ax.transAxes, fontsize=17,
       va='top', ha='center', color='#d4816b', style='italic', fontweight='bold')
ax.text(0.5, 0.02, 'underbuilt', transform=ax.transAxes, fontsize=17,
       va='bottom', ha='center', color='#6b9dc4', style='italic', fontweight='bold')

# Legend
legend_items = [
    Line2D([0], [0], marker='o', color='w', markerfacecolor='#5b4fa8', markersize=8, label='DE'),
    Line2D([0], [0], marker='o', color='w', markerfacecolor='#d4a017', markersize=8, label='AT'),
    Line2D([0], [0], marker='o', color='w', markerfacecolor='#e05050', markersize=8, label='IT'),
    Line2D([0], [0], marker='o', color='w', markerfacecolor='#cccccc', markersize=7, label='Other'),
    Line2D([0], [0], marker='D', color='w', markerfacecolor='gray',
           markeredgecolor='#333333', markersize=9, markeredgewidth=1.0,
           label='Outlier in 3+ runs'),
]
ax.legend(handles=legend_items, fontsize=14, loc='upper center',
         bbox_to_anchor=(0.5, -0.12), ncol=5, framealpha=0.9)

plt.tight_layout()
plt.savefig('figures/misallocation_all_scenarios_v3.pdf', bbox_inches='tight', dpi=300)
plt.savefig('figures/misallocation_all_scenarios_v3.png', bbox_inches='tight', dpi=300)
print("Saved: figures/misallocation_all_scenarios_v3.pdf/.png")
plt.close()
