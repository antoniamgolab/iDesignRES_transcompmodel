"""
Infrastructure misallocation figure:
(a) Total misallocation bars (absolute + avg/node + %)
(b) Boxplot of per-node deviation with outliers labeled
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
matplotlib.rcParams['font.size'] = 13

# Load data
with open('input_data/fixed_nuts_2/GeographicElement.yaml') as f:
    geo_data = yaml.safe_load(f)
geo_country = {g['id']: g.get('country', '??') for g in geo_data}
geo_names = {g['id']: g.get('name', '??').replace('nuts2_', '') for g in geo_data}
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

# ── Optimal infra ──
sf_q = sorted(glob.glob('results/uncertainty_scenarios_v2/scenario_000/*_q_fuel_infr_plus_dict.yaml'))
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

# ── Heuristic infra ──
sf_s = sorted(glob.glob('results/uncertainty_scenarios_v2/scenario_000/*_s_dict.yaml'))
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

# ── Rail infra ──
sf_q_rail = sorted(glob.glob('results/uncertainty_scenarios_v2_rail/scenario_000/*_q_fuel_infr_plus_dict.yaml'))
rail_infra = defaultdict(float)
with open(sf_q_rail[-1]) as f:
    for line in f:
        m = ci3_pat.match(line.strip())
        if not m: continue
        yi, fi, pos = int(m.group(1)), int(m.group(2)), int(m.group(3))
        val = float(m.group(4))
        if val < 1e-3 or fi == 3: continue
        yr = y_idx_to_year.get(yi)
        if yr and yr <= 2040:
            rail_infra[pos - 1] += val / 1000

# ── Per-node deltas ──
delta_heur = [heur_infra.get(g, 0) - opt_infra.get(g, 0) for g in all_geo_ids]
delta_rail = [opt_infra.get(g, 0) - rail_infra.get(g, 0) for g in all_geo_ids]
delta_worst = [heur_infra.get(g, 0) - rail_infra.get(g, 0) for g in all_geo_ids]

opt_total = sum(opt_infra[g] for g in all_geo_ids)
misalloc_heur = sum(abs(d) for d in delta_heur) / 2
misalloc_rail = sum(abs(d) for d in delta_rail) / 2
misalloc_worst = sum(abs(d) for d in delta_worst) / 2

# ── Find consistent outliers across all three comparisons ──
outlier_threshold = 12
outlier_nodes = set()
for data in [delta_heur, delta_rail, delta_worst]:
    for j, d in enumerate(data):
        if abs(d) > outlier_threshold:
            outlier_nodes.add(all_geo_ids[j])

print("Consistent outliers:")
print(f"{'Node':>8s} {'Heur-Opt':>10s} {'Road-Rail':>10s} {'Heur-Rail':>10s}")
for g in sorted(outlier_nodes, key=lambda g: -max(abs(delta_heur[all_geo_ids.index(g)]),
                                                    abs(delta_worst[all_geo_ids.index(g)]))):
    j = all_geo_ids.index(g)
    dh = delta_heur[j]; dr = delta_rail[j]; dw = delta_worst[j]
    appear = sum(1 for d in [dh, dr, dw] if abs(d) > outlier_threshold)
    print(f"{geo_names[g]:>8s} {dh:>+10.0f} {dr:>+10.0f} {dw:>+10.0f}  (in {appear}/3)")

# ══════════════════════════════════════════════════════════════════════
# FIGURE
# ══════════════════════════════════════════════════════════════════════
fig, axes = plt.subplots(1, 2, figsize=(16, 7.5), gridspec_kw={'width_ratios': [1, 1.6]})

# Two comparisons: Heuristic vs optimal, Heuristic vs road+rail
colors = ['#c4956a', '#b07050']

# ── Panel (a): Summary bars ──
ax = axes[0]
labels_a = ['Heuristic\nvs system-optimal', 'Heuristic\nvs road+rail']
vals_a = [misalloc_heur, misalloc_worst]
avgs_a = [sum(abs(d) for d in delta_heur) / 81,
          sum(abs(d) for d in delta_worst) / 81]
pcts_a = [v / opt_total * 100 for v in vals_a]

x = np.arange(len(labels_a))
ax.bar(x, vals_a, 0.5, color=colors, alpha=0.85, edgecolor='white')

for j in range(len(labels_a)):
    ax.text(x[j], vals_a[j] + 5,
            f'{vals_a[j]:.0f} MW ({pcts_a[j]:.0f}%)\n{avgs_a[j]:.1f} MW/node',
            ha='center', va='bottom', fontsize=14, fontweight='bold', color=colors[j])

ax.set_xticks(x)
ax.set_xticklabels(labels_a, fontsize=14)
ax.set_ylabel('Misallocated capacity (MW)', fontsize=15)
ax.set_title('(a) Total misallocation\n(Go RES, 2040)', fontsize=16)
ax.set_ylim(0, 200)
ax.grid(True, alpha=0.15, axis='y')

# ── Panel (b): Boxplots with outliers labeled ──
ax = axes[1]

bp_data = [delta_heur, delta_worst]
bp_labels = ['Heuristic vs\nsystem-optimal', 'Heuristic vs\nroad+rail']

np.random.seed(42)
bp = ax.boxplot(bp_data, vert=True, patch_artist=True, showfliers=False,
                widths=0.5, medianprops=dict(color='black', linewidth=2))

for patch, color in zip(bp['boxes'], colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.4)

# Identify nodes that are outliers in 2+ comparisons
consistent_outlier_indices = set()
for j in range(len(all_geo_ids)):
    appear = sum(1 for data in bp_data if abs(data[j]) > outlier_threshold)
    if appear >= 2:
        consistent_outlier_indices.add(j)

# Scatter all points and store jitter positions for arrow targeting
jitter_positions = {}  # (box_idx, data_idx) -> actual x position
for i, (data, color) in enumerate(zip(bp_data, colors)):
    jitter = np.random.uniform(-0.15, 0.15, len(data))
    x_positions = np.full(len(data), i + 1) + jitter

    # Regular points
    regular_mask = [j not in consistent_outlier_indices for j in range(len(data))]
    consistent_mask = [j in consistent_outlier_indices for j in range(len(data))]

    ax.scatter(x_positions[regular_mask], np.array(data)[regular_mask],
              color=color, alpha=0.3, s=18, zorder=3, marker='o')
    # Consistent outliers: larger, diamond shape, dark red edge
    ax.scatter(x_positions[consistent_mask], np.array(data)[consistent_mask],
              color=color, alpha=0.9, s=60, zorder=4, marker='D',
              edgecolors='#8B0000', linewidths=1.2)

    for j in range(len(data)):
        jitter_positions[(i, j)] = x_positions[j]

# Collect outliers per boxplot, then place labels carefully
# For each boxplot, gather outliers and sort by value for stacking
outlier_labels = {0: [], 1: [], 2: []}  # i -> [(j, d, name, appear)]
for i, data in enumerate(bp_data):
    for j, d in enumerate(data):
        g = all_geo_ids[j]
        if abs(d) > outlier_threshold:
            name = geo_names[g]
            appear = sum(1 for dd in [delta_heur[j], delta_rail[j], delta_worst[j]] if abs(dd) > outlier_threshold)
            marker = '*' if appear >= 2 else ''
            outlier_labels[i].append((j, d, f'{name}{marker}', d))

# Sort outliers by value (top to bottom) for clean stacking
for i in outlier_labels:
    outlier_labels[i].sort(key=lambda x: -x[1])

# Place labels: left side for box 0, between for box 1, right side for box 2
# Use fixed x positions and stack y with minimum spacing
ax.axhline(y=0, color='black', linewidth=0.5)

label_fontsize = 12
min_y_gap = 7  # minimum MW gap between labels

def place_labels(ax, outliers, box_idx, text_x, ha, color, min_gap=6):
    if not outliers:
        return
    pos = [(j, d, name, val) for j, d, name, val in outliers if d > 0]
    neg = [(j, d, name, val) for j, d, name, val in outliers if d <= 0]

    for group in [pos, neg]:
        if not group:
            continue
        group.sort(key=lambda x: -x[1] if x[1] > 0 else x[1])
        placed_y = []
        for j, d, name, val in group:
            target_y = d
            for py in placed_y:
                if abs(target_y - py) < min_gap:
                    if d > 0:
                        target_y = py + min_gap
                    else:
                        target_y = py - min_gap
            placed_y.append(target_y)

            # Use actual dot position for arrow target
            dot_x = jitter_positions.get((box_idx, j), box_idx + 1)
            label = f'{name} ({d:+.0f})'
            ax.annotate(label, xy=(dot_x, d), xytext=(text_x, target_y),
                       fontsize=label_fontsize, ha=ha, va='center', color=color, fontweight='bold',
                       arrowprops=dict(arrowstyle='->', color=color, alpha=0.35, lw=0.7,
                                      connectionstyle='arc3,rad=0.05'))

# Box 0: labels to the left
place_labels(ax, outlier_labels[0], 0, 0.65, 'right', colors[0], min_gap=6)
# Box 1: labels to the right
place_labels(ax, outlier_labels[1], 1, 2.3, 'left', colors[1], min_gap=6)

ax.set_xticklabels(bp_labels, fontsize=14)
ax.set_ylabel('Deviation per NUTS-2 node (MW)', fontsize=15)
ax.set_title('(b) Distribution of per-region deviation\n(Go RES, 2040)', fontsize=16)
ax.grid(True, alpha=0.15, axis='y')
ax.set_xlim(0.3, 2.8)

ax.text(0.5, 0.98, 'overbuilt', transform=ax.transAxes, fontsize=13,
       va='top', ha='center', color='#d4816b', style='italic')
ax.text(0.5, 0.02, 'underbuilt', transform=ax.transAxes, fontsize=13,
       va='bottom', ha='center', color='#6b9dc4', style='italic')

from matplotlib.lines import Line2D
ax.legend(handles=[
    Line2D([0], [0], marker='D', color='w', markerfacecolor='gray', markeredgecolor='#8B0000',
           markersize=8, markeredgewidth=1.2, label='Outlier in 2+ comparisons (*)'),
    Line2D([0], [0], marker='o', color='w', markerfacecolor='gray', alpha=0.4,
           markersize=6, label='Single comparison only'),
], fontsize=10, loc='center left', framealpha=0.9)

plt.tight_layout()
plt.savefig('figures/misallocation_summary.pdf', bbox_inches='tight', dpi=300)
plt.savefig('figures/misallocation_summary.png', bbox_inches='tight', dpi=300)
print("Saved: figures/misallocation_summary.pdf/.png")
plt.close()
