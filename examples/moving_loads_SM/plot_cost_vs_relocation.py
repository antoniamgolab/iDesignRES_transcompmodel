"""
Scatter plot: infrastructure cost advantage vs energy shift per node.
Shows WHY the optimizer concentrates demand at certain locations.
"""
import re, yaml, glob
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from collections import defaultdict
from heuristic_charging import compute_heuristic_charging

matplotlib.rcParams['font.family'] = 'sans-serif'
matplotlib.rcParams['font.sans-serif'] = ['Segoe UI', 'sans-serif']
matplotlib.rcParams['font.size'] = 14

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

# Rest fraction per node
rest_count = defaultdict(int)
break_count = defaultdict(int)
for mb in breaks_data:
    gid = int(mb['latest_geo_id'])
    if mb['break_duration'] >= 8.0:
        rest_count[gid] += 1
    else:
        break_count[gid] += 1

gamma_ccs = 0.75
gamma_mcs = 0.23

# Full cost per MWh served at 2040:
# 1. CAPEX: from FuelingInfrTypes cost_per_kW at index 20 (2040), annualized over 20yr lifetime
with open('input_data/uncertainty_scenarios_v2/scenario_000/FuelingInfrTypes.yaml') as f:
    fit_list = yaml.safe_load(f)

charger_data = {}
for fit in fit_list:
    fid = fit['id']
    capex_2040 = fit['cost_per_kW'][20]  # EUR/kW at 2040
    om_2040 = fit['om_costs'][20]  # EUR/kW/yr at 2040
    gamma = fit['gamma'][20]
    charger_data[fid] = {
        'capex': capex_2040, 'om': om_2040, 'gamma': gamma,
        'name': fit['fueling_type'],
    }

lifetime = 20
for fid in [1, 2]:  # CCS, MCS
    cd = charger_data[fid]
    annual_capex = cd['capex'] / lifetime
    # Cost per MWh = (annual_capex + om) / (gamma * 8760) * 1000
    infra_cost_per_mwh = (annual_capex + cd['om']) * 1000 / (cd['gamma'] * 8760)
    charger_data[fid]['infra_eur_per_mwh'] = infra_cost_per_mwh
    print(f"{cd['name']} (id={fid}): CAPEX={cd['capex']:.0f} EUR/kW, OM={cd['om']:.1f} EUR/kW/yr, "
          f"gamma={cd['gamma']:.2f} -> infra cost={infra_cost_per_mwh:.1f} EUR/MWh")

ccs_infra_cost = charger_data[1]['infra_eur_per_mwh']
mcs_infra_cost = charger_data[2]['infra_eur_per_mwh']

# Load electricity costs per node per charger type at 2040
with open('input_data/uncertainty_scenarios_v2/scenario_000/FuelCost.yaml') as f:
    fuel_costs = yaml.safe_load(f)

elec_cost_node = {}  # (geo_id, infr_type): EUR/MWh
for fc in fuel_costs:
    if fc['fuel'] != 'electricity': continue
    gid = fc['location']
    infr = fc['fueling_infr_type_id']
    cost_2040 = fc['cost_per_kWh'][20] * 1000  # EUR/kWh -> EUR/MWh
    elec_cost_node[(gid, infr)] = cost_2040

tuple_pat = re.compile(
    r'\((\d+),\s*\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\),\s*(\d+),\s*\((\d+),\s*(\d+)\),\s*(\d+)\):\s*([\d.eE+-]+)')

# Load optimal energy by node and charger type at 2040
sf_s = sorted(glob.glob('results/uncertainty_scenarios_v2/scenario_000/*_s_dict.yaml'))
opt_ccs = defaultdict(float)
opt_mcs = defaultdict(float)
route_energy = defaultdict(float)

with open(sf_s[-1]) as f:
    for line in f:
        m = tuple_pat.match(line.strip())
        if not m: continue
        yr = int(m.group(1))
        if yr != 2040: continue
        oid, pid, gid = int(m.group(3)), int(m.group(4)), int(m.group(5))
        fu, inf = int(m.group(7)), int(m.group(8))
        val = float(m.group(10))
        if val < 1e-6 or fu != 0: continue
        if inf == 1:
            opt_ccs[gid] += val
        elif inf == 2:
            opt_mcs[gid] += val
        if inf in {1, 2}:
            route_energy[(oid, pid)] += val

# Heuristic energy split by rest/break
heur_ccs = defaultdict(float)
heur_mcs = defaultdict(float)
for (oid, pid), te in route_energy.items():
    if te < 1e-6: continue
    actual_pid = od_path.get(oid, pid)
    heur_alloc = compute_heuristic_charging(oid, pid, te, od_path, path_seq, path_dist, breaks_by_path)
    for g, mwh in heur_alloc.items():
        if is_rest.get((actual_pid, g), False):
            heur_ccs[g] += mwh
        else:
            heur_mcs[g] += mwh

# Per-node data
COUNTRIES = ['NO', 'FI', 'SE', 'DK', 'DE', 'AT', 'IT']
country_colors = {
    'NO': '#4878a8', 'FI': '#e8a838', 'SE': '#58a058', 'DK': '#c85858',
    'DE': '#8868a8', 'AT': '#987868', 'IT': '#d888b8',
}

# First pass: compute FULL cost per MWh at each node (infra + electricity)
node_costs = {}
for g in all_geo_ids:
    opt_total = opt_ccs.get(g, 0) + opt_mcs.get(g, 0)
    if opt_total > 0.1:
        ccs_e = opt_ccs.get(g, 0)
        mcs_e = opt_mcs.get(g, 0)
        # Weighted cost: infra + electricity for each charger type
        ccs_full = ccs_infra_cost + elec_cost_node.get((g, 1), 180)  # infr_type 1 = CCS
        mcs_full = mcs_infra_cost + elec_cost_node.get((g, 2), 170)  # infr_type 2 = MCS
        node_costs[g] = (ccs_e * ccs_full + mcs_e * mcs_full) / opt_total

# Network average cost (energy-weighted)
total_energy = sum(opt_ccs.get(g, 0) + opt_mcs.get(g, 0) for g in node_costs)
avg_cost = sum(node_costs[g] * (opt_ccs.get(g, 0) + opt_mcs.get(g, 0)) for g in node_costs) / total_energy
print(f"Network average FULL charging cost: {avg_cost:.1f} EUR/MWh")
print(f"  (infra component: ~{(ccs_infra_cost + mcs_infra_cost)/2:.1f} EUR/MWh, electricity: ~{avg_cost - (ccs_infra_cost + mcs_infra_cost)/2:.1f} EUR/MWh)")

nodes = []
for g in all_geo_ids:
    opt_total = opt_ccs.get(g, 0) + opt_mcs.get(g, 0)
    heur_total = heur_ccs.get(g, 0) + heur_mcs.get(g, 0)
    if opt_total < 0.1 and heur_total < 0.1:
        continue

    # Energy shift as % of total network energy
    total_network = sum(opt_ccs.get(gg, 0) + opt_mcs.get(gg, 0) for gg in all_geo_ids)
    energy_shift = (opt_total - heur_total) / total_network * 100  # percentage points

    # Cost relative to network average (positive = cheaper than average)
    if g in node_costs:
        cost_rel = avg_cost - node_costs[g]
    else:
        cost_rel = 0

    # Rest fraction
    tb = rest_count.get(g, 0) + break_count.get(g, 0)
    rf = rest_count.get(g, 0) / tb if tb > 0 else 0

    nodes.append({
        'g': g, 'name': geo_names[g], 'country': geo_country[g],
        'energy_shift': energy_shift, 'cost_rel': cost_rel,
        'rest_frac': rf, 'opt_total': opt_total / 1000,
    })

# ── FIGURE ──
fig, ax = plt.subplots(figsize=(10, 7))

for n in nodes:
    size = max(20, min(250, abs(n['energy_shift']) * 40))
    ax.scatter(n['cost_rel'], n['energy_shift'],
              c=country_colors.get(n['country'], 'gray'),
              s=size, alpha=0.6, edgecolors='white', linewidth=0.5, zorder=3)

# Label outliers
for n in nodes:
    if abs(n['energy_shift']) > 0.5 or abs(n['cost_rel']) > 12:
        offset_x = 6 if n['energy_shift'] > 0 else -6
        ha = 'left' if n['energy_shift'] > 0 else 'right'
        ax.annotate(n['name'], xy=(n['cost_rel'], n['energy_shift']),
                   xytext=(offset_x, 3), textcoords='offset points',
                   fontsize=10, alpha=0.85, fontweight='bold')

ax.axhline(y=0, color='black', linewidth=0.5, alpha=0.4)
ax.axvline(x=0, color='black', linewidth=0.5, alpha=0.4)

# Trend line
x_vals = [n['cost_rel'] for n in nodes]
y_vals = [n['energy_shift'] for n in nodes]
z = np.polyfit(x_vals, y_vals, 1)
x_line = np.linspace(min(x_vals), max(x_vals), 100)
ax.plot(x_line, np.polyval(z, x_line), '--', color='gray', alpha=0.5, linewidth=1.5)

# Correlation
corr = np.corrcoef(x_vals, y_vals)[0, 1]
ax.text(0.02, 0.98, f'r = {corr:.2f}', transform=ax.transAxes,
       fontsize=12, va='top', ha='left', color='gray',
       bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

ax.set_xlabel('Total charging cost advantage vs network average\n(avg $-$ node cost, EUR/MWh; includes infra CAPEX, O&M, electricity)', fontsize=12)
ax.set_ylabel('Energy shifted to node\n(optimal $-$ heuristic, % of total)', fontsize=14)
ax.set_title('Why does the optimizer relocate charging demand?\n(Go RES, 2040)', fontsize=15)

# Country legend
from matplotlib.lines import Line2D
legend_items = [Line2D([0], [0], marker='o', color='w', markerfacecolor=country_colors[c],
                       markersize=8, label=c) for c in COUNTRIES]
ax.legend(handles=legend_items, fontsize=11, loc='lower right', ncol=2)

# Quadrant annotations
ax.text(0.97, 0.97, 'Cheaper than avg +\nenergy concentrated here',
       transform=ax.transAxes, fontsize=10, va='top', ha='right',
       color='#2a7a2a', alpha=0.5, style='italic')
ax.text(0.03, 0.03, 'More expensive than avg +\nenergy shifted away',
       transform=ax.transAxes, fontsize=10, va='bottom', ha='left',
       color='#a03030', alpha=0.5, style='italic')

ax.grid(True, alpha=0.15)
plt.tight_layout()
plt.savefig('figures/cost_vs_relocation.pdf', bbox_inches='tight', dpi=300)
plt.savefig('figures/cost_vs_relocation.png', bbox_inches='tight', dpi=300)
print("Saved: figures/cost_vs_relocation.pdf/.png")
plt.close()
