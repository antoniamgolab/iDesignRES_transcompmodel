"""
SOC sensitivity analysis figures + LaTeX table.
  1. Three-panel latitude overlay (2032, 2040, 2048)
  2. LaTeX table with relocation %, country shares, costs
"""

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter1d
import yaml, re, glob, pathlib, subprocess
from collections import defaultdict
from heuristic_charging import compute_heuristic_charging

BASE = pathlib.Path(__file__).resolve().parent
RESULTS_BASE = BASE / 'results' / 'soc_sensitivity'
FIG_DIR = BASE / 'figures'
FIG_DIR.mkdir(exist_ok=True)

# Font
matplotlib.rcParams['font.family'] = 'serif'
matplotlib.rcParams['font.serif'] = ['Times New Roman', 'serif']
matplotlib.rcParams['font.size'] = 28
matplotlib.rcParams['axes.titlesize'] = 38
matplotlib.rcParams['axes.labelsize'] = 34
matplotlib.rcParams['xtick.labelsize'] = 28
matplotlib.rcParams['ytick.labelsize'] = 28
matplotlib.rcParams['legend.fontsize'] = 22
matplotlib.rcParams['figure.titlesize'] = 42

# Geo data
with open(BASE / 'input_data/fixed_nuts_2/GeographicElement.yaml') as f:
    geo_data = yaml.safe_load(f)
geo_lat = {g['id']: g.get('coordinate_lat', 0) for g in geo_data}
geo_country = {g['id']: g.get('country', '??') for g in geo_data}
all_geo_ids = [g['id'] for g in geo_data if g.get('type') == 'node']

# Paths, breaks, battery
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

SOC_RUNS = [
    ('base_50_50',      '50/50 (base)',   '#2C3E50', '-',  3.0),
    ('low_start_30_50', '30/50',          '#E74C3C', '--', 2.0),
    ('high_start_70_50','70/50',          '#3498DB', '--', 2.0),
    ('low_end_50_30',   '50/30',          '#2ECC71', '--', 2.0),
    ('high_end_50_70',  '50/70',          '#F39C12', '--', 2.0),
    ('tight_30_70',     '30/70 (tight)',  '#9B59B6', '-',  2.5),
    ('loose_70_30',     '70/30 (loose)',  '#1ABC9C', '-',  2.5),
]

TARGET_YEARS = [2032, 2040, 2048]
BORDERS = {'IT--AT': 46.5, 'AT--DE': 47.5, 'DE--DK': 54.5, 'DK--SE': 55.5}
COUNTRIES = ['IT', 'AT', 'DE', 'SE', 'NO', 'DK', 'FI']

def battery_cap_for_year(year):
    return BATTERY_BY_GEN.get(year, BATTERY_BY_GEN[max(y for y in BATTERY_BY_GEN if y <= year)])
def spec_cons_for_year(year):
    return SPEC_CONS_BY_GEN.get(year, SPEC_CONS_BY_GEN[max(y for y in SPEC_CONS_BY_GEN if y <= year)])

def compute_soc_charging(od_id, path_id, total_energy_mwh, year, soc_init_frac=0.5):
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
    soc = bat_cap * soc_init_frac
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

# ── Load data ──
print("Loading SOC sensitivity data...")
soc_data = {}
available = []

for run_name, label, color, ls, lw in SOC_RUNS:
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

    soc_data[run_name] = {'charging': charging, 'route_charging': route_charging, 'summary': summary}
    available.append(run_name)
    print(" OK")

print(f"Available: {len(available)}")

# ── FIGURE 1: Three-panel latitude overlay ──
print("\nGenerating latitude overlay...")
fig, axes = plt.subplots(1, 3, figsize=(30, 14), sharey=True)
fig.suptitle('Charging demand by latitude -- SOC sensitivity',
             fontweight='bold', y=0.99)

for yi, target_year in enumerate(TARGET_YEARS):
    ax = axes[yi]
    for run_name in available:
        _, label, color, ls, lw = next(r for r in SOC_RUNS if r[0] == run_name)
        lat_gwh = {}
        for g in all_geo_ids:
            lat_gwh[geo_lat[g]] = lat_gwh.get(geo_lat[g], 0) + soc_data[run_name]['charging'].get(g, {}).get(target_year, 0) / 1000
        data = sorted(lat_gwh.items())
        if not data: continue
        lats = np.array([x[0] for x in data])
        gwhs = np.array([x[1] for x in data])
        gs = gaussian_filter1d(gwhs, sigma=1.2) if len(lats) > 3 else gwhs
        ax.plot(gs, lats, color=color, linestyle=ls, linewidth=lw, label=label)

    for bname, blat in BORDERS.items():
        ax.axhline(y=blat, color='gray', linestyle=':', alpha=0.4, linewidth=0.7)
        if yi == 0:
            ax.annotate(bname, xy=(0.97, blat + 0.3), xycoords=('axes fraction', 'data'),
                       fontsize=20, color='gray', ha='right')

    total = sum(soc_data['base_50_50']['charging'].get(g, {}).get(target_year, 0) for g in all_geo_ids) / 1000
    ax.set_title(f'{target_year}')
    ax.set_xlabel('GWh/year')
    ax.set_ylim(38, 72)
    ax.grid(axis='y', alpha=0.2)
    if yi == 0:
        ax.set_ylabel('Latitude (°N)')
    if yi == 2:
        ax.legend(loc='upper right', fontsize=18)

plt.tight_layout(rect=[0, 0, 1, 0.95])
outfile = BASE / 'soc_sensitivity_latitude_3panel.png'
plt.savefig(outfile, dpi=200, bbox_inches='tight')
plt.savefig(outfile.with_suffix('.pdf'), bbox_inches='tight')
print(f"  Saved: {outfile.name}")
plt.close()

# ── Compute relocation metrics ──
print("\nComputing relocation metrics...")
results = {}
for run_name in available:
    results[run_name] = {}
    # Get SOC init for heuristic
    soc_init_frac = float(soc_data[run_name]['summary'].get('soc_init', 0.5))

    for target_year in TARGET_YEARS:
        opt_geo = {g: soc_data[run_name]['charging'].get(g, {}).get(target_year, 0) for g in all_geo_ids}
        heur_geo = defaultdict(float)
        for (od_id, path_id), year_dict in soc_data[run_name]['route_charging'].items():
            total_e = year_dict.get(target_year, 0)
            if total_e < 1e-6: continue
            for g, mwh in compute_heuristic_charging(od_id, path_id, total_e, od_path, path_seq, path_dist, breaks_by_path).items():
                heur_geo[g] += mwh

        total_energy = sum(v for v in opt_geo.values() if v > 0)
        relocated = sum(abs(opt_geo.get(g, 0) - heur_geo.get(g, 0)) for g in set(list(opt_geo.keys()) + list(heur_geo.keys()))) / 2
        reloc_pct = relocated / total_energy * 100 if total_energy > 0 else 0

        # BEV share
        stats = soc_data[run_name]['summary']
        bev = float(stats['tonnes_by_year'].get(target_year, {}).get('BEV', 0))
        icev = float(stats['tonnes_by_year'].get(target_year, {}).get('ICEV', 0))
        bev_pct = bev / (bev + icev) * 100 if (bev + icev) > 0 else 0

        # Country shares
        opt_country = defaultdict(float)
        for g in all_geo_ids:
            c = geo_country.get(g, '??')
            opt_country[c] += opt_geo.get(g, 0)

        results[run_name][target_year] = {
            'reloc_pct': reloc_pct,
            'total_gwh': total_energy / 1000,
            'bev_pct': bev_pct,
            'obj': float(stats['objective_value']) / 1e9,
            'country_shares': {c: opt_country[c] / total_energy * 100 if total_energy > 0 else 0 for c in COUNTRIES},
        }

# ── LaTeX table ──
print("\nGenerating LaTeX table...")
soc_labels_tex = {
    'base_50_50': '50/50 (base)',
    'low_start_30_50': '30/50',
    'high_start_70_50': '70/50',
    'low_end_50_30': '50/30',
    'high_end_50_70': '50/70',
    'tight_30_70': '30/70 (tight)',
    'loose_70_30': '70/30 (loose)',
}

tex = r"""\documentclass[border=5pt]{standalone}
\usepackage{booktabs}
\usepackage{siunitx}

\begin{document}

\begin{tabular}{l S[table-format=3.2] S[table-format=2.1] S[table-format=3.0] S[table-format=2.1] S[table-format=2.1] S[table-format=2.1] S[table-format=2.1]}
\toprule
{SOC (init/final)} & {Obj} & {BEV} & {Total} & {Reloc.} & \multicolumn{3}{c}{Country share (\%)} \\
{} & {(bn~\euro)} & {(\%)} & {(GWh)} & {(\%)} & {IT} & {AT} & {DE} \\
\midrule
"""

for target_year in TARGET_YEARS:
    tex += r"\multicolumn{8}{l}{\textbf{" + str(target_year) + r"}}" + " \\\\\n"
    for run_name in available:
        r = results[run_name][target_year]
        label = soc_labels_tex.get(run_name, run_name)
        cs = r['country_shares']
        tex += f"  {label} & {r['obj']:.2f} & {r['bev_pct']:.1f} & {r['total_gwh']:.0f} & {r['reloc_pct']:.1f} & {cs.get('IT',0):.1f} & {cs.get('AT',0):.1f} & {cs.get('DE',0):.1f} \\\\\n"
    if target_year != TARGET_YEARS[-1]:
        tex += r"\addlinespace" + "\n"

tex += r"""\bottomrule
\end{tabular}

\end{document}
"""

tex_file = BASE / 'soc_sensitivity_table.tex'
with open(tex_file, 'w') as f:
    f.write(tex)
print(f"  Saved: {tex_file.name}")

try:
    subprocess.run(['pdflatex', '-interaction=nonstopmode', str(tex_file)],
                   capture_output=True, cwd=str(BASE), timeout=30)
    print(f"  Compiled: soc_sensitivity_table.pdf")
except Exception:
    print(f"  Compile manually: pdflatex {tex_file.name}")

# ── Print table ──
print("\n" + "="*100)
print("SOC SENSITIVITY TABLE")
print("="*100)
print(f"{'SOC':>18s}  {'Obj(bn)':>8s}  {'BEV%':>6s}  {'GWh':>6s}  {'Reloc%':>7s}  {'IT%':>5s}  {'AT%':>5s}  {'DE%':>5s}")
for target_year in TARGET_YEARS:
    print(f"--- {target_year} ---")
    for run_name in available:
        r = results[run_name][target_year]
        cs = r['country_shares']
        label = soc_labels_tex.get(run_name, run_name)
        print(f"{label:>18s}  {r['obj']:>8.2f}  {r['bev_pct']:>5.1f}%  {r['total_gwh']:>5.0f}G  {r['reloc_pct']:>6.1f}%  {cs.get('IT',0):>4.1f}%  {cs.get('AT',0):>4.1f}%  {cs.get('DE',0):>4.1f}%")

print("\nDone!")

# ── FIGURE 2: BEV adoption trajectory ──
print("\nGenerating adoption trajectory...")
fig, ax = plt.subplots(figsize=(12, 7))
MODELED_YEARS = list(range(2020, 2064, 4))

for run_name in available:
    _, label, color, ls, lw = next(r for r in SOC_RUNS if r[0] == run_name)
    stats = soc_data[run_name]['summary']
    years_plot = []
    bev_pcts = []
    for year in MODELED_YEARS:
        bev = float(stats['tonnes_by_year'].get(year, {}).get('BEV', 0))
        icev = float(stats['tonnes_by_year'].get(year, {}).get('ICEV', 0))
        total = bev + icev
        if total > 0:
            years_plot.append(year)
            bev_pcts.append(bev / total * 100)
    ax.plot(years_plot, bev_pcts, color=color, linestyle=ls, linewidth=lw,
            label=label, marker='o', markersize=5)

ax.set_xlabel('Year')
ax.set_ylabel('BEV share of freight (%)')
ax.set_title('BEV adoption trajectory -- SOC sensitivity')
ax.legend(fontsize=18, ncol=2)
ax.set_ylim(0, 105)
ax.grid(alpha=0.3)
plt.tight_layout()
outfile = BASE / 'soc_sensitivity_adoption.png'
plt.savefig(outfile, dpi=200, bbox_inches='tight')
plt.savefig(outfile.with_suffix('.pdf'), bbox_inches='tight')
print(f"  Saved: {outfile.name}")
plt.close()

# ── Adoption table ──
print("\nBEV ADOPTION TABLE (% of tonnes)")
print("="*90)
header = f"{'SOC':>18s}"
for y in MODELED_YEARS:
    if y >= 2028 and y <= 2060:
        header += f"  {y:>6d}"
print(header)
print("-"*90)

for run_name in available:
    _, label, _, _, _ = next(r for r in SOC_RUNS if r[0] == run_name)
    stats = soc_data[run_name]['summary']
    row = f"{label:>18s}"
    for year in MODELED_YEARS:
        if year >= 2028 and year <= 2060:
            bev = float(stats['tonnes_by_year'].get(year, {}).get('BEV', 0))
            icev = float(stats['tonnes_by_year'].get(year, {}).get('ICEV', 0))
            total = bev + icev
            pct = bev / total * 100 if total > 0 else 0
            row += f"  {pct:>5.1f}%"
    print(row)

# Adoption LaTeX table
tex_adopt = r"""\documentclass[border=5pt]{standalone}
\usepackage{booktabs}
\usepackage{siunitx}

\begin{document}

\begin{tabular}{l""" + " ".join(["S[table-format=2.1]" for y in MODELED_YEARS if 2028 <= y <= 2060]) + r"""}
\toprule
{SOC (init/final)}"""
for y in MODELED_YEARS:
    if 2028 <= y <= 2060:
        tex_adopt += f" & {{{y}}}"
tex_adopt += r""" \
\midrule
"""

for run_name in available:
    label = soc_labels_tex.get(run_name, run_name)
    stats = soc_data[run_name]['summary']
    tex_adopt += f"  {label}"
    for year in MODELED_YEARS:
        if 2028 <= year <= 2060:
            bev = float(stats['tonnes_by_year'].get(year, {}).get('BEV', 0))
            icev = float(stats['tonnes_by_year'].get(year, {}).get('ICEV', 0))
            total = bev + icev
            pct = bev / total * 100 if total > 0 else 0
            tex_adopt += f" & {pct:.1f}"
    tex_adopt += " \\\n"

tex_adopt += r"""\bottomrule
\end{tabular}

\end{document}
"""

tex_adopt_file = BASE / 'soc_sensitivity_adoption_table.tex'
with open(tex_adopt_file, 'w') as f:
    f.write(tex_adopt)
print(f"\nSaved: {tex_adopt_file.name}")

try:
    subprocess.run(['pdflatex', '-interaction=nonstopmode', str(tex_adopt_file)],
                   capture_output=True, cwd=str(BASE), timeout=30)
    print(f"Compiled: soc_sensitivity_adoption_table.pdf")
except Exception:
    print(f"Compile manually: pdflatex {tex_adopt_file.name}")

print("\nAll SOC sensitivity outputs complete!")
