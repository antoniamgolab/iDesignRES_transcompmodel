"""
Kappa sensitivity analysis figures for the paper.

Uses only s_dict and summary_stats (available from kappa batch).
  (A) BEV adoption trajectory across kappa values
  (B) Spatial charging demand distribution (by latitude)
  (C) Optimal vs heuristic charging comparison

Target years: 2032, 2040, 2048
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter1d
import yaml, re, glob, pathlib
from collections import defaultdict
from heuristic_charging import compute_heuristic_charging

BASE = pathlib.Path(__file__).resolve().parent
RESULTS_BASE = BASE / 'results' / 'kappa_sensitivity'

KAPPA_RUNS = [
    ('no_cap',    'No cap',          '#2C3E50', '-',  2.5),
    ('kappa_0.5', r'$\kappa$=0.5',   '#3498DB', '--', 1.8),
    ('kappa_0.3', r'$\kappa$=0.3',   '#2ECC71', '-',  1.8),
    ('kappa_0.2', r'$\kappa$=0.2',   '#E67E22', '--', 1.8),
    ('kappa_0.1', r'$\kappa$=0.1',   '#E74C3C', '-',  2.5),
]

TARGET_YEARS = [2032, 2040, 2048]

# Load geographic data
with open(BASE / 'input_data/fixed_nuts_2/GeographicElement.yaml') as f:
    geo_data = yaml.safe_load(f)
geo_lat = {g['id']: g.get('coordinate_lat', 0) for g in geo_data}
geo_country = {g['id']: g.get('country', '??') for g in geo_data}

# Load paths, OD pairs, breaks, battery data
with open(BASE / 'input_data/uncertainty_scenarios_v2/scenario_000/Path.yaml') as f:
    paths = yaml.load(f, Loader=yaml.UnsafeLoader)
with open(BASE / 'input_data/uncertainty_scenarios_v2/scenario_000/Odpair.yaml') as f:
    odpairs_raw = yaml.load(f, Loader=yaml.UnsafeLoader)
with open(BASE / 'input_data/uncertainty_scenarios_v2/scenario_000/MandatoryBreaks.yaml') as f:
    breaks_data = yaml.load(f, Loader=yaml.UnsafeLoader)
with open(BASE / 'input_data/uncertainty_scenarios_v2/scenario_000/TechVehicle.yaml') as f:
    tv_data = yaml.safe_load(f)

path_seq = {int(p['id']): [int(x) for x in p['sequence']] for p in paths}
path_dist = {int(p['id']): [float(d) for d in p.get('distance_from_previous', [])] for p in paths}
od_path = {int(od['id']): int(od['path_id']) for od in odpairs_raw}

breaks_by_path = defaultdict(list)
for brk in breaks_data:
    breaks_by_path[int(brk['path_id'])].append(int(brk['latest_geo_id']))

bev_tv = next(t for t in tv_data if t['technology'] == 1)
GEN_YEARS = list(range(2008, 2008 + len(bev_tv['tank_capacity'])))
BATTERY_BY_GEN = dict(zip(GEN_YEARS, bev_tv['tank_capacity']))
SPEC_CONS_BY_GEN = dict(zip(GEN_YEARS, bev_tv['spec_cons']))

tuple_pat = re.compile(
    r'\((\d+),\s*\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\),\s*(\d+),\s*\((\d+),\s*(\d+)\),\s*(\d+)\):\s*([\d.eE+-]+)')

BORDERS = {'IT-AT': 46.5, 'AT-DE': 47.5, 'DE-DK': 54.5, 'DK-SE': 55.5}


def battery_cap_for_year(year):
    return BATTERY_BY_GEN.get(year, BATTERY_BY_GEN[max(y for y in BATTERY_BY_GEN if y <= year)])

def spec_cons_for_year(year):
    return SPEC_CONS_BY_GEN.get(year, SPEC_CONS_BY_GEN[max(y for y in SPEC_CONS_BY_GEN if y <= year)])

def compute_soc_charging(od_id, path_id, total_energy_mwh, year):
    pid = od_path.get(od_id, path_id)
    seq = path_seq.get(pid, [])
    dist = path_dist.get(pid, [])
    break_set = set(breaks_by_path.get(pid, []))
    if not seq or not dist or len(seq) != len(dist): return {}
    break_indices = [i for i, g in enumerate(seq) if g in break_set]
    if not break_indices:
        n = len(seq)
        return {seq[i]: total_energy_mwh / n for i in range(n)} if n > 0 else {}
    cum_dist = np.cumsum(dist)
    total_dist = cum_dist[-1] if len(cum_dist) > 0 else 0
    if total_dist < 1e-3: return {}
    bat_cap = battery_cap_for_year(year)
    sc = spec_cons_for_year(year)
    soc = bat_cap * 0.5
    charges = {}
    for i, bi in enumerate(break_indices):
        prev_dist = cum_dist[break_indices[i-1]] if i > 0 else 0
        soc -= sc * (cum_dist[bi] - prev_dist)
        dist_to_next = (cum_dist[break_indices[i+1]] if i < len(break_indices)-1 else total_dist) - cum_dist[bi]
        energy_to_next = sc * dist_to_next
        if soc < energy_to_next + bat_cap * 0.1:
            charge = max(0, min(bat_cap - soc, energy_to_next - soc + bat_cap * 0.1))
            if charge > 0:
                charges[seq[bi]] = charges.get(seq[bi], 0) + charge
                soc += charge
    if not charges:
        for bi in break_indices:
            charges[seq[bi]] = 1.0
    total_raw = sum(charges.values())
    if total_raw < 1e-9: return {}
    scale = total_energy_mwh / total_raw
    return {g: v * scale for g, v in charges.items()}


# ============================================================================
# Load data
# ============================================================================
print("Loading kappa sensitivity data...")
kappa_data = {}
available = []

for run_name, label, color, ls, lw in KAPPA_RUNS:
    run_dir = RESULTS_BASE / run_name
    s_files = sorted(glob.glob(str(run_dir / '*_s_dict.yaml')))
    summary_file = run_dir / 'summary_stats.yaml'

    if not s_files or not summary_file.exists():
        print(f"  {run_name}: MISSING")
        continue

    print(f"  {run_name}...", end="", flush=True)

    # Parse s
    charging = defaultdict(lambda: defaultdict(float))
    route_charging = defaultdict(lambda: defaultdict(float))
    with open(s_files[-1]) as f:
        for line in f:
            m = tuple_pat.match(line.strip())
            if not m: continue
            year = int(m.group(1))
            od_id, path_id, geo_id = int(m.group(3)), int(m.group(4)), int(m.group(5))
            fuel, infr = int(m.group(7)), int(m.group(8))
            val = float(m.group(10))
            if val < 1e-6 or fuel != 0 or infr not in {1, 2}: continue
            charging[geo_id][year] += val
            route_charging[(od_id, path_id)][year] += val

    # Load summary
    with open(summary_file) as f:
        summary = yaml.safe_load(f)

    kappa_data[run_name] = {
        'charging': charging,
        'route_charging': route_charging,
        'summary': summary,
    }
    available.append(run_name)
    print(" OK")

if not available:
    print("No data found! Run SM_batch_kappa_sensitivity.jl first.")
    exit(1)

print(f"\nAvailable: {len(available)}/{len(KAPPA_RUNS)}")


# ============================================================================
# (A) BEV ADOPTION TRAJECTORY
# ============================================================================
print("\n" + "="*80)
print("(A) BEV ADOPTION TRAJECTORY")
print("="*80)

fig, ax = plt.subplots(figsize=(10, 5))
MODELED_YEARS = list(range(2020, 2064, 4))

for run_name in available:
    _, label, color, ls, lw = next(r for r in KAPPA_RUNS if r[0] == run_name)
    stats = kappa_data[run_name]['summary']
    years_plot = []
    bev_pcts = []
    for year in MODELED_YEARS:
        bev = float(stats['tonnes_by_year'].get(year, {}).get('BEV', 0))
        icev = float(stats['tonnes_by_year'].get(year, {}).get('ICEV', 0))
        total = bev + icev
        if total > 0:
            years_plot.append(year)
            bev_pcts.append(bev / total * 100)

    ax.plot(years_plot, bev_pcts, color=color, linestyle=ls, linewidth=lw, label=label, marker='o', markersize=4)

ax.set_xlabel('Year', fontsize=11)
ax.set_ylabel('BEV Share of Freight (%)', fontsize=11)
ax.set_title('BEV Adoption Trajectory\nKappa sensitivity', fontsize=13, fontweight='bold')
ax.legend(fontsize=9)
ax.set_ylim(0, 105)
ax.grid(alpha=0.3)
ax.axhline(y=50, color='gray', linestyle=':', alpha=0.3)

# Mark target years
for ty in TARGET_YEARS:
    ax.axvline(x=ty, color='lightgray', linestyle=':', alpha=0.5)

plt.tight_layout()
outfile = BASE / 'kappa_bev_trajectory.png'
plt.savefig(outfile, dpi=200, bbox_inches='tight')
plt.savefig(outfile.with_suffix('.pdf'), bbox_inches='tight')
print(f"  Saved: {outfile.name}")
plt.close()

# Country-level charging share bar chart
for target_year in TARGET_YEARS:
    fig, ax = plt.subplots(figsize=(10, 5))
    countries = ['IT', 'DE', 'AT', 'SE', 'NO', 'DK', 'FI']
    x = np.arange(len(countries))
    n_runs = len(available)
    width = 0.8 / n_runs

    for i, run_name in enumerate(available):
        _, label, color, _, _ = next(r for r in KAPPA_RUNS if r[0] == run_name)
        country_gwh = defaultdict(float)
        total_gwh = 0
        for geo_id, year_dict in kappa_data[run_name]['charging'].items():
            mwh = year_dict.get(target_year, 0)
            if mwh > 0:
                c = geo_country.get(geo_id, '??')
                country_gwh[c] += mwh / 1000
                total_gwh += mwh / 1000

        shares = [country_gwh.get(c, 0) / total_gwh * 100 if total_gwh > 0 else 0 for c in countries]
        ax.bar(x + i * width, shares, width, label=label, color=color, alpha=0.8)

    ax.set_xlabel('Country', fontsize=11)
    ax.set_ylabel('Share of charging demand (%)', fontsize=11)
    ax.set_title(f'Charging demand share by country - {target_year}\nKappa sensitivity', fontsize=13, fontweight='bold')
    ax.set_xticks(x + width * (n_runs - 1) / 2)
    ax.set_xticklabels(countries, fontsize=10)
    ax.legend(fontsize=9, ncol=3)
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    outfile = BASE / f'kappa_country_share_{target_year}.png'
    plt.savefig(outfile, dpi=200, bbox_inches='tight')
    plt.savefig(outfile.with_suffix('.pdf'), bbox_inches='tight')
    print(f"  Saved: {outfile.name}")
    plt.close()


# ============================================================================
# (B) SPATIAL CHARGING BY LATITUDE — panels
# ============================================================================
print("\n" + "="*80)
print("(B) SPATIAL CHARGING DEMAND BY LATITUDE")
print("="*80)

for target_year in TARGET_YEARS:
    fig, axes = plt.subplots(1, len(available), figsize=(3.2 * len(available), 8), sharey=True, sharex=True)
    if len(available) == 1: axes = [axes]
    fig.suptitle(f'Charging demand by latitude - {target_year}', fontsize=13, fontweight='bold', y=0.98)

    global_max = 0
    all_lat = {}
    for run_name in available:
        lat_gwh = sorted([(geo_lat.get(g, 0), kappa_data[run_name]['charging'][g].get(target_year, 0)/1000)
                          for g in kappa_data[run_name]['charging']
                          if geo_lat.get(g, 0) > 0 and kappa_data[run_name]['charging'][g].get(target_year, 0) > 0])
        all_lat[run_name] = lat_gwh
        if lat_gwh: global_max = max(global_max, max(g for _, g in lat_gwh))

    for idx, run_name in enumerate(available):
        ax = axes[idx]
        _, label, color, _, _ = next(r for r in KAPPA_RUNS if r[0] == run_name)
        data = all_lat[run_name]
        if not data: continue
        lats = np.array([x[0] for x in data])
        gwhs = np.array([x[1] for x in data])
        si = np.argsort(lats)
        gwh_s = gaussian_filter1d(gwhs[si], sigma=1.2) if len(lats) > 3 else gwhs[si]
        ax.fill_betweenx(lats[si], 0, gwh_s, alpha=0.3, color=color)
        ax.plot(gwh_s, lats[si], color=color, linewidth=1.5)
        ax.scatter(gwhs[si], lats[si], color=color, s=12, zorder=5, alpha=0.6)
        for blat in BORDERS.values():
            ax.axhline(y=blat, color='gray', linestyle='--', alpha=0.3, linewidth=0.7)
        ax.set_title(f'{label}\n({sum(gwhs):.0f} GWh)', fontsize=9)
        ax.set_xlim(0, global_max * 1.15)
        ax.set_ylim(38, 72)
        ax.set_xlabel('GWh/yr', fontsize=9)
        if idx == 0: ax.set_ylabel('Latitude (N)', fontsize=10)
        ax.grid(axis='y', alpha=0.2)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    outfile = BASE / f'kappa_charging_panels_{target_year}.png'
    plt.savefig(outfile, dpi=200, bbox_inches='tight')
    plt.savefig(outfile.with_suffix('.pdf'), bbox_inches='tight')
    print(f"  Saved: {outfile.name}")
    plt.close()


# ============================================================================
# (C) OPTIMAL vs HEURISTIC
# ============================================================================
print("\n" + "="*80)
print("(C) OPTIMAL vs HEURISTIC COMPARISON")
print("="*80)

for target_year in TARGET_YEARS:
    print(f"\n--- Year {target_year} ---")
    fig, axes = plt.subplots(1, len(available), figsize=(3.5 * len(available), 8), sharey=True, sharex=True)
    if len(available) == 1: axes = [axes]
    fig.suptitle(f'Optimal vs Heuristic charging - {target_year}', fontsize=13, fontweight='bold', y=0.98)

    global_max = 0

    for idx, run_name in enumerate(available):
        ax = axes[idx]
        _, label, color, _, _ = next(r for r in KAPPA_RUNS if r[0] == run_name)

        opt_geo = {g: kappa_data[run_name]['charging'][g].get(target_year, 0)
                   for g in kappa_data[run_name]['charging']}

        heur_geo = defaultdict(float)
        for (od_id, path_id), year_dict in kappa_data[run_name]['route_charging'].items():
            total_e = year_dict.get(target_year, 0)
            if total_e < 1e-6: continue
            for g, mwh in compute_heuristic_charging(od_id, path_id, total_e, od_path, path_seq, path_dist, breaks_by_path).items():
                heur_geo[g] += mwh

        all_geos = set(list(opt_geo.keys()) + list(heur_geo.keys()))
        total_energy = sum(v for v in opt_geo.values() if v > 0)
        relocated = sum(abs(opt_geo.get(g, 0) - heur_geo.get(g, 0)) for g in all_geos) / 2
        reloc_pct = relocated / total_energy * 100 if total_energy > 0 else 0

        opt_lat = sorted([(geo_lat.get(g, 0), opt_geo.get(g, 0)/1000) for g in all_geos
                          if geo_lat.get(g, 0) > 0 and opt_geo.get(g, 0) > 0])
        heur_lat = sorted([(geo_lat.get(g, 0), heur_geo.get(g, 0)/1000) for g in all_geos
                           if geo_lat.get(g, 0) > 0 and heur_geo.get(g, 0) > 0])

        if opt_lat:
            lats = np.array([x[0] for x in opt_lat])
            gwhs = np.array([x[1] for x in opt_lat])
            si = np.argsort(lats)
            gs = gaussian_filter1d(gwhs[si], sigma=1.2) if len(lats) > 3 else gwhs[si]
            ax.fill_betweenx(lats[si], 0, gs, alpha=0.2, color=color)
            ax.plot(gs, lats[si], color=color, linewidth=2, label='Optimal')
            global_max = max(global_max, max(gwhs))

        if heur_lat:
            lats = np.array([x[0] for x in heur_lat])
            gwhs = np.array([x[1] for x in heur_lat])
            si = np.argsort(lats)
            gs = gaussian_filter1d(gwhs[si], sigma=1.2) if len(lats) > 3 else gwhs[si]
            ax.plot(gs, lats[si], color='gray', linewidth=1.5, linestyle='--', label='Heuristic')

        for blat in BORDERS.values():
            ax.axhline(y=blat, color='gray', linestyle=':', alpha=0.3, linewidth=0.7)

        ax.set_title(f'{label}\nRelocation: {reloc_pct:.1f}%', fontsize=10)
        ax.set_ylim(38, 72)
        ax.set_xlabel('GWh/yr', fontsize=9)
        if idx == 0:
            ax.set_ylabel('Latitude (N)', fontsize=10)
            ax.legend(fontsize=8)
        ax.grid(axis='y', alpha=0.2)
        print(f"  {label}: relocation = {reloc_pct:.1f}%")

    for ax in axes:
        ax.set_xlim(0, global_max * 1.15)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    outfile = BASE / f'kappa_opt_vs_heuristic_{target_year}.png'
    plt.savefig(outfile, dpi=200, bbox_inches='tight')
    plt.savefig(outfile.with_suffix('.pdf'), bbox_inches='tight')
    print(f"  Saved: {outfile.name}")
    plt.close()

print("\nAll figures generated!")
