"""
Check whether charging infrastructure expansion at node level follows an S-curve.
Parses q_fuel_infr_plus (incremental capacity added per period) and plots
cumulative installed capacity over time for selected nodes.
"""
import re, pathlib
import numpy as np
import matplotlib.pyplot as plt
import yaml

BASE = pathlib.Path(__file__).resolve().parent

MODELED_YEARS = list(range(2020, 2064, 4))
y_idx_map = {i+1: y for i, y in enumerate(MODELED_YEARS)}

# Load geographic element names + countries
with open(BASE / 'input_data/fixed_nuts_2/GeographicElement.yaml') as f:
    geo_raw = yaml.safe_load(f)
geo_name = {g['id']: g.get('name', f"geo_{g['id']}") for g in geo_raw}
geo_country = {}
for g in geo_raw:
    name = g.get('name', '')
    if len(name) >= 7 and name.startswith('nuts2_'):
        geo_country[g['id']] = name[6:8]
    elif len(name) >= 2:
        geo_country[g['id']] = name[:2]
    else:
        geo_country[g['id']] = '??'

# Parse q_fuel_infr_plus results
results_file = BASE / 'results/uncertainty_scenarios_v2/scenario_000/scenario_000_cs_2026-04-06_22-51-30_q_fuel_infr_plus_dict.yaml'
ci3 = re.compile(r'CartesianIndex\((\d+),\s*(\d+),\s*(\d+)\):\s*([\d.eE+-]+)')

# node_year[geo_id][year] = total kW added (electric only: fl_mapping=1 is electric)
node_year = {}
for line in open(results_file):
    m = ci3.match(line.strip())
    if not m:
        continue
    yi, fl, geo_id = int(m.group(1)), int(m.group(2)), int(m.group(3))
    val = float(m.group(4))
    yr = y_idx_map.get(yi)
    if yr is None or val < 1e-6:
        continue
    # fl=1 is electric charging, fl=3 is diesel refueling — only want electric
    if fl != 1:
        continue
    if geo_id not in node_year:
        node_year[geo_id] = {}
    node_year[geo_id][yr] = node_year[geo_id].get(yr, 0) + val

# Compute cumulative capacity per node
node_cumulative = {}
for geo_id, yd in node_year.items():
    cum = []
    total = 0
    for yr in MODELED_YEARS:
        total += yd.get(yr, 0)
        cum.append(total)
    node_cumulative[geo_id] = cum

# Rank nodes by total final capacity
ranked = sorted(node_cumulative.items(), key=lambda x: x[1][-1], reverse=True)

# Also compute country-level aggregates
country_cumulative = {}
for geo_id, cum in node_cumulative.items():
    c = geo_country.get(geo_id, '??')
    if c not in country_cumulative:
        country_cumulative[c] = [0.0] * len(MODELED_YEARS)
    for i in range(len(MODELED_YEARS)):
        country_cumulative[c][i] += cum[i]

# ---- PLOT 1: Top 12 individual nodes ----
fig, axes = plt.subplots(3, 4, figsize=(16, 10), sharex=True)
axes_flat = axes.flatten()

for idx, (geo_id, cum) in enumerate(ranked[:12]):
    ax = axes_flat[idx]
    c = geo_country.get(geo_id, '??')
    name = geo_name.get(geo_id, f'geo_{geo_id}')
    ax.plot(MODELED_YEARS, [x/1000 for x in cum], 'o-', color='steelblue', linewidth=2, markersize=4)
    ax.set_title(f'{name} ({c})', fontsize=9)
    ax.set_ylabel('MW', fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.tick_params(labelsize=7)
    # Mark where growth is fastest (inflection point proxy)
    increments = np.diff(cum)
    if len(increments) > 0:
        peak_idx = np.argmax(increments)
        ax.axvline(MODELED_YEARS[peak_idx+1], color='red', linestyle='--', alpha=0.5, linewidth=1)

fig.suptitle('Cumulative charging infrastructure at top 12 nodes (Go RES)\nRed dashed = period of fastest growth', fontsize=12)
plt.tight_layout()
plt.savefig(BASE / 'figures/infra_scurve_top_nodes.pdf', bbox_inches='tight')
plt.savefig(BASE / 'figures/infra_scurve_top_nodes.png', bbox_inches='tight', dpi=150)
print("Saved infra_scurve_top_nodes.pdf/png")

# ---- PLOT 2: Country-level cumulative ----
fig2, ax2 = plt.subplots(figsize=(10, 6))
colors = {'IT': '#2ca02c', 'AT': '#d62728', 'DE': '#1f77b4', 'SE': '#ff7f0e',
          'DK': '#9467bd', 'NO': '#8c564b', 'CH': '#e377c2'}
for c in sorted(country_cumulative.keys(), key=lambda x: country_cumulative[x][-1], reverse=True):
    cum = country_cumulative[c]
    ax2.plot(MODELED_YEARS, [x/1000 for x in cum], 'o-', label=c,
             color=colors.get(c, 'gray'), linewidth=2, markersize=5)
ax2.set_xlabel('Year')
ax2.set_ylabel('Cumulative installed capacity (MW)')
ax2.set_title('Charging infrastructure deployment by country (Go RES)')
ax2.legend()
ax2.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(BASE / 'figures/infra_scurve_by_country.pdf', bbox_inches='tight')
plt.savefig(BASE / 'figures/infra_scurve_by_country.png', bbox_inches='tight', dpi=150)
print("Saved infra_scurve_by_country.pdf/png")

# ---- PLOT 3: Normalized S-curve check ----
# Normalize each node's cumulative trajectory to [0, 1] and overlay
fig3, ax3 = plt.subplots(figsize=(10, 6))
norm_trajectories = []
for geo_id, cum in ranked[:30]:  # top 30 nodes
    final = cum[-1]
    if final > 100:  # only nodes with meaningful capacity
        normed = [x / final for x in cum]
        norm_trajectories.append(normed)
        c = geo_country.get(geo_id, '??')
        ax3.plot(MODELED_YEARS, normed, '-', alpha=0.3, color='steelblue', linewidth=1)

# Compute and plot mean
if norm_trajectories:
    mean_traj = np.mean(norm_trajectories, axis=0)
    ax3.plot(MODELED_YEARS, mean_traj, 'o-', color='darkred', linewidth=3, markersize=6, label='Mean (top 30 nodes)')

    # Compare with logistic S-curve
    t = np.array(MODELED_YEARS)
    t_mid = 2040
    k = 0.2  # steepness
    logistic = 1 / (1 + np.exp(-k * (t - t_mid)))
    logistic = (logistic - logistic[0]) / (logistic[-1] - logistic[0])  # normalize to [0,1]
    ax3.plot(MODELED_YEARS, logistic, '--', color='gray', linewidth=2, label='Reference logistic (midpoint 2040)')

ax3.set_xlabel('Year')
ax3.set_ylabel('Fraction of final capacity installed')
ax3.set_title('Normalized infrastructure trajectories: S-curve check\n(Top 30 nodes, Go RES scenario)')
ax3.legend()
ax3.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(BASE / 'figures/infra_scurve_normalized.pdf', bbox_inches='tight')
plt.savefig(BASE / 'figures/infra_scurve_normalized.png', bbox_inches='tight', dpi=150)
print("Saved infra_scurve_normalized.pdf/png")

# ---- Print growth rates ----
print("\n" + "="*80)
print("GROWTH RATE ANALYSIS (period-over-period % increase)")
print("="*80)
print(f"\n{'Node':<25s} {'Country':>7s} | ", end="")
for i in range(1, len(MODELED_YEARS)):
    print(f" {MODELED_YEARS[i-1]}-{MODELED_YEARS[i]}", end="")
print(f" | Final MW")
print("-"*120)

for geo_id, cum in ranked[:20]:
    c = geo_country.get(geo_id, '??')
    name = geo_name.get(geo_id, f'geo_{geo_id}')[:22]
    print(f"{name:<25s} {c:>7s} | ", end="")
    for i in range(1, len(MODELED_YEARS)):
        prev = cum[i-1]
        curr = cum[i]
        if prev > 10:
            pct = (curr - prev) / prev * 100
            print(f" {pct:>7.0f}%", end="")
        elif curr > 0:
            print(f"    new ", end="")
        else:
            print(f"      - ", end="")
    print(f" | {cum[-1]/1000:>8.1f}")

plt.show()
