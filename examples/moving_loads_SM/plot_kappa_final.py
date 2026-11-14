"""
Final kappa sensitivity figures:
  1. Single figure with 3 subplots (2032, 2040, 2048) — all kappa overlaid
  2. LaTeX table with relocation % for each kappa × year
"""

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter1d
import yaml, re, glob, pathlib, subprocess
from collections import defaultdict
from heuristic_charging import compute_heuristic_charging

# Set font — Times New Roman (Elsevier style)
matplotlib.rcParams['font.family'] = 'serif'
matplotlib.rcParams['font.serif'] = ['Times New Roman', 'serif']
matplotlib.rcParams['mathtext.fontset'] = 'cm'  # Computer Modern math — pairs well with Palatino

# Font sizes — A4 vertical print readable
matplotlib.rcParams['font.size'] = 28
matplotlib.rcParams['axes.titlesize'] = 38
matplotlib.rcParams['axes.labelsize'] = 34
matplotlib.rcParams['xtick.labelsize'] = 28
matplotlib.rcParams['ytick.labelsize'] = 28
matplotlib.rcParams['legend.fontsize'] = 26
matplotlib.rcParams['figure.titlesize'] = 42

BASE = pathlib.Path(__file__).resolve().parent
RESULTS_BASE = BASE / 'results' / 'kappa_sensitivity'

KAPPA_RUNS = [
    ('no_cap',    'No cap',          '#2C3E50', '-',  3.5),
    ('kappa_0.5', r'$\kappa=0.5$',   '#3498DB', '--', 2.5),
    ('kappa_0.3', r'$\kappa=0.3$',   '#2ECC71', '-',  2.5),
    ('kappa_0.2', r'$\kappa=0.2$',   '#E67E22', '--', 2.5),
    ('kappa_0.1', r'$\kappa=0.1$',   '#E74C3C', '-',  3.5),
]

TARGET_YEARS = [2032, 2040, 2048]

# Load geo data
with open(BASE / 'input_data/fixed_nuts_2/GeographicElement.yaml') as f:
    geo_data = yaml.safe_load(f)
geo_lat = {g['id']: g.get('coordinate_lat', 0) for g in geo_data}
geo_country = {g['id']: g.get('country', '??') for g in geo_data}

# Load paths, OD pairs, breaks, battery
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

BORDERS = {'IT--AT': 46.5, 'AT--DE': 47.5, 'DE--DK': 54.5, 'DK--SE': 55.5}


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
print("Loading data...")
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

    with open(summary_file) as f:
        summary = yaml.safe_load(f)

    kappa_data[run_name] = {'charging': charging, 'route_charging': route_charging, 'summary': summary}
    available.append(run_name)
    print(" OK")

print(f"Available: {len(available)}")


# ============================================================================
# FIGURE 1: Three-panel overlay (2032, 2040, 2048)
# ============================================================================
print("\nGenerating latitude overlay figure...")

fig, axes = plt.subplots(1, 3, figsize=(30, 14), sharey=True)
fig.suptitle('Charging demand by latitude across deployment pace scenarios',
             fontweight='bold', y=0.99)

for yi, target_year in enumerate(TARGET_YEARS):
    ax = axes[yi]

    for run_name in available:
        _, label, color, ls, lw = next(r for r in KAPPA_RUNS if r[0] == run_name)
        lat_gwh = sorted([(geo_lat.get(g, 0), kappa_data[run_name]['charging'][g].get(target_year, 0)/1000)
                          for g in kappa_data[run_name]['charging']
                          if geo_lat.get(g, 0) > 0 and kappa_data[run_name]['charging'][g].get(target_year, 0) > 0])
        if not lat_gwh: continue
        lats = np.array([x[0] for x in lat_gwh])
        gwhs = np.array([x[1] for x in lat_gwh])
        si = np.argsort(lats)
        gs = gaussian_filter1d(gwhs[si], sigma=1.2) if len(lats) > 3 else gwhs[si]
        ax.plot(gs, lats[si], color=color, linestyle=ls, linewidth=lw, label=label)

    for bname, blat in BORDERS.items():
        ax.axhline(y=blat, color='gray', linestyle=':', alpha=0.4, linewidth=0.7)
        if yi == 0:
            ax.annotate(bname, xy=(0.97, blat + 0.3), xycoords=('axes fraction', 'data'),
                       fontsize=24, color='gray', ha='right')

    total_nocap = sum(kappa_data['no_cap']['charging'][g].get(target_year, 0)
                      for g in kappa_data['no_cap']['charging']) / 1000 if 'no_cap' in kappa_data else 0
    ax.set_title(f'{target_year}\n(Total: {total_nocap:.0f} GWh)')
    ax.set_xlabel('GWh/year')
    ax.set_ylim(38, 72)
    ax.grid(axis='y', alpha=0.2)
    ax.grid(axis='x', alpha=0.15)

    if yi == 0:
        ax.set_ylabel('Latitude (°N)')
    if yi == 2:
        ax.legend(loc='upper right')

plt.tight_layout(rect=[0, 0, 1, 0.95])
outfile = BASE / 'kappa_latitude_3panel.png'
plt.savefig(outfile, dpi=200, bbox_inches='tight')
plt.savefig(outfile.with_suffix('.pdf'), bbox_inches='tight')
print(f"  Saved: {outfile.name}")
plt.close()


# ============================================================================
# Compute relocation metrics for table
# ============================================================================
print("\nComputing relocation metrics...")

# Results: {run_name: {year: {metric: value}}}
results = {}

for run_name in available:
    results[run_name] = {}
    for target_year in TARGET_YEARS:
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

        # Country shares
        opt_country = defaultdict(float)
        heur_country = defaultdict(float)
        for g in all_geos:
            c = geo_country.get(g, '??')
            opt_country[c] += opt_geo.get(g, 0)
            heur_country[c] += heur_geo.get(g, 0)

        # Max country delta
        max_delta_c = ''
        max_delta_pct = 0
        for c in set(list(opt_country.keys()) + list(heur_country.keys())):
            if total_energy > 0:
                delta = abs(opt_country[c] - heur_country[c]) / total_energy * 100
                if delta > max_delta_pct:
                    max_delta_pct = delta
                    max_delta_c = c

        # BEV share
        stats = kappa_data[run_name]['summary']
        bev = float(stats['tonnes_by_year'].get(target_year, {}).get('BEV', 0))
        icev = float(stats['tonnes_by_year'].get(target_year, {}).get('ICEV', 0))
        bev_pct = bev / (bev + icev) * 100 if (bev + icev) > 0 else 0

        # Concentration: top node share
        if total_energy > 0:
            shares = sorted([v / total_energy for v in opt_geo.values() if v > 0], reverse=True)
            top1 = shares[0] * 100 if shares else 0
            top3 = sum(shares[:3]) * 100
            n_active = sum(1 for s in shares if s > 0.001)
        else:
            top1 = top3 = 0
            n_active = 0

        results[run_name][target_year] = {
            'reloc_pct': reloc_pct,
            'total_gwh': total_energy / 1000,
            'bev_pct': bev_pct,
            'top1_pct': top1,
            'top3_pct': top3,
            'n_active': n_active,
            'max_delta_c': max_delta_c,
            'max_delta_pct': max_delta_pct,
        }
        print(f"  {run_name} @ {target_year}: reloc={reloc_pct:.1f}%, BEV={bev_pct:.1f}%, top1={top1:.1f}%")


# ============================================================================
# Generate LaTeX table
# ============================================================================
print("\nGenerating LaTeX table...")

kappa_labels_tex = {
    'no_cap': r'$\infty$ (no cap)',
    'kappa_0.5': r'0.5',
    'kappa_0.3': r'0.3',
    'kappa_0.2': r'0.2',
    'kappa_0.1': r'0.1',
}

tex = r"""\documentclass[border=5pt]{standalone}
\usepackage{booktabs}
\usepackage{siunitx}
\usepackage{multirow}

\begin{document}

\begin{tabular}{l S[table-format=2.1] S[table-format=3.0] S[table-format=2.1] S[table-format=2.1] S[table-format=2.1] S[table-format=2.0]}
\toprule
{$\kappa$} & {BEV share} & {Total} & {Relocation} & {Top-1 node} & {Top-3 nodes} & {Active} \\
{} & {(\%)} & {(GWh)} & {(\%)} & {share (\%)} & {share (\%)} & {nodes} \\
\midrule
"""

for target_year in TARGET_YEARS:
    tex += r"\multicolumn{7}{l}{\textbf{" + str(target_year) + r"}}" + " \\\\\n"
    for run_name in available:
        r = results[run_name][target_year]
        k_label = kappa_labels_tex.get(run_name, run_name)
        tex += f"  {k_label} & {r['bev_pct']:.1f} & {r['total_gwh']:.0f} & {r['reloc_pct']:.1f} & {r['top1_pct']:.1f} & {r['top3_pct']:.1f} & {r['n_active']:.0f} \\\\\n"
    if target_year != TARGET_YEARS[-1]:
        tex += r"\addlinespace" + "\n"

tex += r"""\bottomrule
\end{tabular}

\end{document}
"""

tex_file = BASE / 'kappa_sensitivity_table.tex'
with open(tex_file, 'w') as f:
    f.write(tex)
print(f"  Saved: {tex_file.name}")

# Try to compile to PDF
try:
    result = subprocess.run(
        ['pdflatex', '-interaction=nonstopmode', str(tex_file)],
        capture_output=True, text=True, cwd=str(BASE), timeout=30
    )
    if result.returncode == 0:
        print(f"  Compiled: kappa_sensitivity_table.pdf")
    else:
        print(f"  LaTeX compilation failed (pdflatex not found or error)")
        print(f"  You can compile manually: pdflatex {tex_file.name}")
except (FileNotFoundError, subprocess.TimeoutExpired):
    print(f"  pdflatex not available — compile manually: pdflatex {tex_file.name}")

# Also print the table as text
print("\n" + "="*90)
print("KAPPA SENSITIVITY TABLE")
print("="*90)
print(f"{'kappa':>10s}  {'BEV%':>6s}  {'GWh':>6s}  {'Reloc%':>7s}  {'Top1%':>6s}  {'Top3%':>6s}  {'Nodes':>6s}")
for target_year in TARGET_YEARS:
    print(f"--- {target_year} ---")
    for run_name in available:
        r = results[run_name][target_year]
        k = kappa_labels_tex.get(run_name, run_name)
        print(f"{k:>10s}  {r['bev_pct']:>5.1f}%  {r['total_gwh']:>5.0f}G  {r['reloc_pct']:>6.1f}%  {r['top1_pct']:>5.1f}%  {r['top3_pct']:>5.1f}%  {r['n_active']:>6d}")

print("\nDone!")
