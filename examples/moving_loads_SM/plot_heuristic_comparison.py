"""
System-optimal vs Heuristic vs Rail comparison figure (Go RES, 2048).
(a) Normalized charging distribution by latitude: optimal, heuristic, rail
(b) Infrastructure by country: optimal vs heuristic vs rail (CCS+MCS stacked)
(c) Relocated/shifted energy by country (optimal-heuristic) + rail reduction
"""
import re, yaml, glob
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from pathlib import Path
from collections import defaultdict
from scipy.ndimage import gaussian_filter1d
from heuristic_charging import compute_heuristic_charging

matplotlib.rcParams['font.family'] = 'sans-serif'
matplotlib.rcParams['font.sans-serif'] = ['Segoe UI', 'sans-serif']
matplotlib.rcParams['font.size'] = 13

BASE = Path(__file__).resolve().parent
RESULTS_PATH = BASE / 'results' / 'uncertainty_scenarios_v2'
RESULTS_RAIL = BASE / 'results' / 'uncertainty_scenarios_v2_rail'
FIG_DIR = BASE / 'figures'
FIG_DIR.mkdir(exist_ok=True)

COUNTRY_ORDER = ['NO', 'FI', 'SE', 'DK', 'DE', 'AT', 'IT']
TARGET_YEAR = 2048
MODELED_YEARS = list(range(2020, 2064, 4))
y_idx_to_year = {i+1: y for i, y in enumerate(MODELED_YEARS)}
gamma_ccs = 0.75
gamma_mcs = 0.23

COL_OPT = '#4a6274'
COL_HEUR = '#c4956a'
COL_RAIL = '#7a9e5a'

# ── Load input data ──
print("Loading input data...")
with open(BASE / 'input_data/fixed_nuts_2/GeographicElement.yaml') as f:
    geo_data = yaml.safe_load(f)
geo_country = {g['id']: g.get('country', '??') for g in geo_data}
geo_lat = {g['id']: g.get('coordinate_lat', 0) for g in geo_data}
all_geo_ids = [g['id'] for g in geo_data if g.get('type') == 'node']

with open(BASE / 'input_data/uncertainty_scenarios_v2/scenario_000/Path.yaml') as f:
    paths = yaml.load(f, Loader=yaml.UnsafeLoader)
with open(BASE / 'input_data/uncertainty_scenarios_v2/scenario_000/Odpair.yaml') as f:
    odpairs_raw = yaml.load(f, Loader=yaml.UnsafeLoader)
with open(BASE / 'input_data/uncertainty_scenarios_v2/scenario_000/MandatoryBreaks.yaml') as f:
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

tuple_pat = re.compile(
    r'\((\d+),\s*\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\),\s*(\d+),\s*\((\d+),\s*(\d+)\),\s*(\d+)\):\s*([\d.eE+-]+)')
ci3_pat = re.compile(r'CartesianIndex\((\d+),\s*(\d+),\s*(\d+)\):\s*([\d.eE+-]+)')

# ── Load energy: optimal, heuristic, rail ──
print("Loading energy data...")

def load_energy_by_geo(s_file, year):
    energy = defaultdict(float)
    route_energy = defaultdict(float)
    with open(s_file) as f:
        for line in f:
            m = tuple_pat.match(line.strip())
            if not m: continue
            yr = int(m.group(1))
            if yr != year: continue
            oid, pid, gid = int(m.group(3)), int(m.group(4)), int(m.group(5))
            fu, inf = int(m.group(7)), int(m.group(8))
            val = float(m.group(10))
            if val < 1e-6 or fu != 0 or inf not in {1, 2}: continue
            energy[gid] += val
            route_energy[(oid, pid)] += val
    return dict(energy), dict(route_energy)

# Road-only optimal
sf_s = sorted(glob.glob(str(RESULTS_PATH / 'scenario_000' / '*_s_dict.yaml')))
opt_energy, route_energy = load_energy_by_geo(sf_s[-1], TARGET_YEAR)

# Heuristic
heur_energy = defaultdict(float)
for (oid, pid), te in route_energy.items():
    if te < 1e-6: continue
    for g, mwh in compute_heuristic_charging(oid, pid, te, od_path, path_seq, path_dist, breaks_by_path).items():
        heur_energy[g] += mwh
heur_energy = dict(heur_energy)

# Rail
sf_rail = sorted(glob.glob(str(RESULTS_RAIL / 'scenario_000' / '*_s_dict.yaml')))
rail_energy, _ = load_energy_by_geo(sf_rail[-1], TARGET_YEAR)

# ── Load infrastructure: optimal, heuristic, rail ──
print("Loading infrastructure data...")

def load_infra_by_country(q_file, max_year):
    ccs_c = defaultdict(float)
    mcs_c = defaultdict(float)
    with open(q_file) as f:
        for line in f:
            m = ci3_pat.match(line.strip())
            if not m: continue
            yi, fi, pos = int(m.group(1)), int(m.group(2)), int(m.group(3))
            val = float(m.group(4))
            if val < 1e-3 or fi == 3: continue
            geo_id = pos - 1
            yr = y_idx_to_year.get(yi)
            if yr and yr <= max_year:
                c = geo_country.get(geo_id, '??')
                if fi == 2: ccs_c[c] += val / 1000  # CCS
                elif fi == 1: mcs_c[c] += val / 1000  # MCS
    return dict(ccs_c), dict(mcs_c)

sf_q = sorted(glob.glob(str(RESULTS_PATH / 'scenario_000' / '*_q_fuel_infr_plus_dict.yaml')))
opt_ccs_c, opt_mcs_c = load_infra_by_country(sf_q[-1], TARGET_YEAR)

sf_q_rail = sorted(glob.glob(str(RESULTS_RAIL / 'scenario_000' / '*_q_fuel_infr_plus_dict.yaml')))
rail_ccs_c, rail_mcs_c = load_infra_by_country(sf_q_rail[-1], TARGET_YEAR)

# Heuristic infrastructure
heur_ccs_c = defaultdict(float)
heur_mcs_c = defaultdict(float)
for (oid, pid), te in route_energy.items():
    if te < 1e-6: continue
    actual_pid = od_path.get(oid, pid)
    heur_alloc = compute_heuristic_charging(oid, pid, te, od_path, path_seq, path_dist, breaks_by_path)
    for g, mwh in heur_alloc.items():
        c = geo_country.get(g, '??')
        if is_rest.get((actual_pid, g), False):
            heur_ccs_c[c] += mwh * 1000 / (gamma_ccs * 8760) / 1000
        else:
            heur_mcs_c[c] += mwh * 1000 / (gamma_mcs * 8760) / 1000

# ══════════════════════════════════════════════════════════════════════
# BUILD FIGURE
# ══════════════════════════════════════════════════════════════════════
print("Building figure...")
fig, axes = plt.subplots(1, 3, figsize=(16, 5.5))

# ── Panel (a): Normalized distribution by latitude ──
ax = axes[0]
sigma = 1.2

for label, geo_dict, color, ls, lw in [
    ('System-optimal', opt_energy, COL_OPT, '-', 2.0),
    ('Reference', heur_energy, COL_HEUR, '--', 1.5),
    ('With shift to rail', rail_energy, COL_RAIL, '-.', 1.5),
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
    ax.fill_betweenx(lats, 0, vals_smooth, alpha=0.12, color=color)
    ax.plot(vals_smooth, lats, color=color, linewidth=lw, linestyle=ls, label=label)

ax.set_ylabel('Latitude')
ax.set_xlabel('Share of total energy (%)')
ax.set_title(f'(a) Spatial distribution\nat {TARGET_YEAR} (Go RES)', fontsize=13)
ax.legend(fontsize=9, loc='upper center')
ax.grid(True, alpha=0.2)

country_lats = {'IT': 42.5, 'AT': 47.5, 'DE': 51.0, 'DK': 56.0, 'SE': 62.0, 'NO': 64.0}
for c, lat in country_lats.items():
    ax.axhline(y=lat, color='gray', linestyle=':', alpha=0.3, linewidth=0.5)
    ax.text(ax.get_xlim()[1] * 0.95, lat, c, fontsize=9, ha='right', va='center', color='gray')

# ── Panel (b): Infrastructure by country ──
ax = axes[1]
x = np.arange(len(COUNTRY_ORDER))
bar_width = 0.25

for i, (label, ccs_dict, mcs_dict, color) in enumerate([
    ('Optimal', opt_ccs_c, opt_mcs_c, COL_OPT),
    ('Heuristic', heur_ccs_c, heur_mcs_c, COL_HEUR),
    ('Road+Rail', rail_ccs_c, rail_mcs_c, COL_RAIL),
]):
    ccs_vals = [ccs_dict.get(c, 0) for c in COUNTRY_ORDER]
    mcs_vals = [mcs_dict.get(c, 0) for c in COUNTRY_ORDER]
    totals = [c + m for c, m in zip(ccs_vals, mcs_vals)]
    offset = (i - 1) * bar_width
    ax.bar(x + offset, ccs_vals, bar_width, color=color, alpha=0.4, edgecolor=color, linewidth=0.5)
    ax.bar(x + offset, mcs_vals, bar_width, bottom=ccs_vals, color=color, alpha=0.9, edgecolor=color, linewidth=0.5)
    for j, total in enumerate(totals):
        if total > 5:
            ax.text(x[j] + offset, total + 3, f'{total:.0f}', ha='center', va='bottom', fontsize=6, color=color)

legend_items = [
    Patch(facecolor=COL_OPT, alpha=0.9, label='Optimal'),
    Patch(facecolor=COL_HEUR, alpha=0.9, label='Reference'),
    Patch(facecolor=COL_RAIL, alpha=0.9, label='With shift to rail'),
    Patch(facecolor='gray', alpha=0.4, label='CCS'),
    Patch(facecolor='gray', alpha=0.9, label='MCS'),
]
ax.legend(handles=legend_items, fontsize=7, loc='upper left', ncol=2)
ax.set_xticks(x)
ax.set_xticklabels(COUNTRY_ORDER, fontsize=11)
ax.set_ylabel('Capacity (MW)')
ax.set_title(f'(b) Infrastructure requirements\nat {TARGET_YEAR} (Go RES)', fontsize=13)
ax.grid(True, alpha=0.2, axis='y')

# ── Panel (c): Energy shifts by country ──
ax = axes[2]

# Three comparisons as grouped bars
x = np.arange(len(COUNTRY_ORDER))
bar_width = 0.35

# 1: Energy shift (optimal - heuristic)
delta_opt_heur = []
for c in COUNTRY_ORDER:
    oc = sum(opt_energy.get(g, 0) for g in all_geo_ids if geo_country.get(g) == c) / 1000
    hc = sum(heur_energy.get(g, 0) for g in all_geo_ids if geo_country.get(g) == c) / 1000
    delta_opt_heur.append(oc - hc)

# 2: Energy shift (rail - optimal)
delta_rail = []
for c in COUNTRY_ORDER:
    oc = sum(opt_energy.get(g, 0) for g in all_geo_ids if geo_country.get(g) == c) / 1000
    rc = sum(rail_energy.get(g, 0) for g in all_geo_ids if geo_country.get(g) == c) / 1000
    delta_rail.append(rc - oc)

ax.bar(x - bar_width/2, delta_opt_heur, bar_width, color=COL_OPT, alpha=0.8,
       edgecolor=COL_OPT, linewidth=0.5, label='Optimal $-$ Heuristic')
ax.bar(x + bar_width/2, delta_rail, bar_width, color=COL_RAIL, alpha=0.8,
       edgecolor=COL_RAIL, linewidth=0.5, label='Rail $-$ Road-only')

# Value labels
for j in range(len(COUNTRY_ORDER)):
    for vals, offset in [(delta_opt_heur, -bar_width/2), (delta_rail, bar_width/2)]:
        d = vals[j]
        if abs(d) > 5:
            va = 'bottom' if d > 0 else 'top'
            ax.text(x[j] + offset, d + (5 if d > 0 else -5), f'{d:+.0f}',
                   ha='center', va=va, fontsize=7)

ax.axhline(y=0, color='black', linewidth=0.5)
ax.set_xticks(x)
ax.set_xticklabels(COUNTRY_ORDER, fontsize=11)
ax.set_ylabel('Energy shift (GWh)')
ax.set_title(f'(c) Energy relocation\nat {TARGET_YEAR} (Go RES)', fontsize=13)
ax.legend(fontsize=9, loc='lower left')
ax.grid(True, alpha=0.2, axis='y')

# Add totals annotation
opt_total = sum(opt_energy.values()) / 1000
heur_total = sum(heur_energy.values()) / 1000
rail_total = sum(rail_energy.values()) / 1000
e_reloc = sum(abs(opt_energy.get(g, 0) - heur_energy.get(g, 0)) for g in all_geo_ids) / 2 / 1000

ax.text(0.98, 0.98,
        f'Relocated: {e_reloc:.0f} GWh ({e_reloc/opt_total*100:.0f}%)\n'
        f'Rail reduces: {opt_total-rail_total:.0f} GWh ({(opt_total-rail_total)/opt_total*100:.0f}%)',
        transform=ax.transAxes, fontsize=8, va='top', ha='right',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

plt.tight_layout()
plt.savefig(str(FIG_DIR / 'heuristic_comparison.pdf'), bbox_inches='tight', dpi=300)
plt.savefig(str(FIG_DIR / 'heuristic_comparison.png'), bbox_inches='tight', dpi=300)
print("Saved: figures/heuristic_comparison.pdf/.png")
plt.close()
