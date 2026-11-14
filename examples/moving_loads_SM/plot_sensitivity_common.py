"""
Unified sensitivity table generator.

Produces the SOC-style 5-metric LaTeX table (Obj / BEV% / Total GWh /
Relocation% / IT-AT-DE country shares at 2032, 2040, 2048) for any of the
three remaining sensitivities, using the exact same metric definitions as
plot_soc_sensitivity.py so the appendix sections are directly comparable.

Usage:
    python plot_sensitivity_common.py battery
    python plot_sensitivity_common.py kappa
    python plot_sensitivity_common.py kspace
    python plot_sensitivity_common.py all
"""
import sys
import yaml, re, glob, pathlib, subprocess
from collections import defaultdict
from heuristic_charging import compute_heuristic_charging

BASE = pathlib.Path(__file__).resolve().parent

TARGET_YEARS = [2032, 2040, 2048]
COUNTRIES = ['IT', 'AT', 'DE', 'SE', 'NO', 'DK', 'FI']

# ── Sensitivity configurations ───────────────────────────────────────
# Each: results subdir, list of (run_dir, latex_label), table caption noun
SENSITIVITIES = {
    'battery': {
        'results_dir': 'battery_sensitivity',
        'runs': [
            ('bat_low_70pct',   r'$-30\,\%$ (392/784/980)'),
            ('bat_baseline',    'Baseline (560/1120/1400)'),
            ('bat_high_130pct', r'$+30\,\%$ (728/1456/1820)'),
        ],
        'col_header': 'Battery capacity (kWh)',
        'tex_name': 'battery_sensitivity_table',
    },
    'kappa': {
        'results_dir': 'kappa_sensitivity',
        'runs': [
            ('no_cap',    r'$\infty$ (no cap)'),
            ('kappa_0.5', r'$\kappa = 0.5$'),
            ('kappa_0.3', r'$\kappa = 0.3$'),
            ('kappa_0.2', r'$\kappa = 0.2$'),
            ('kappa_0.1', r'$\kappa = 0.1$'),
        ],
        'col_header': r'$\kappa$ (power cap)',
        'tex_name': 'kappa_sensitivity_table',
    },
    'kspace': {
        'results_dir': 'kspace_sensitivity',
        'runs': [
            ('no_space_cap',  r'$\infty$ (no cap)'),
            ('kspace_0.001',  r'$\kappa_{\mathrm{s}} = 0.001$'),
            ('kspace_0.0005', r'$\kappa_{\mathrm{s}} = 0.0005$'),
            ('kspace_0.0002', r'$\kappa_{\mathrm{s}} = 0.0002$'),
            ('kspace_0.0001', r'$\kappa_{\mathrm{s}} = 0.0001$'),
        ],
        'col_header': r'$\kappa_{\mathrm{s}}$ (space cap)',
        'tex_name': 'kspace_sensitivity_table',
    },
}

# ── Shared input data (geo, paths, breaks) ───────────────────────────
with open(BASE / 'input_data/fixed_nuts_2/GeographicElement.yaml') as f:
    geo_data = yaml.safe_load(f)
geo_country = {g['id']: g.get('country', '??') for g in geo_data}
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

tuple_pat = re.compile(
    r'\((\d+),\s*\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\),\s*(\d+),\s*\((\d+),\s*(\d+)\),\s*(\d+)\):\s*([\d.eE+-]+)')


def load_run(run_dir):
    """Return (charging[geo][year], route_charging[(od,path)][year], summary) or None."""
    s_files = sorted(glob.glob(str(run_dir / '*_s_dict.yaml')))
    summary_file = run_dir / 'summary_stats.yaml'
    if not s_files or not summary_file.exists():
        return None
    charging = defaultdict(lambda: defaultdict(float))
    route_charging = defaultdict(lambda: defaultdict(float))
    with open(s_files[-1]) as f:
        for line in f:
            m = tuple_pat.match(line.strip())
            if not m:
                continue
            year = int(m.group(1))
            od_id, path_id, geo_id = int(m.group(3)), int(m.group(4)), int(m.group(5))
            fuel, infr = int(m.group(7)), int(m.group(8))
            val = float(m.group(10))
            if val < 1e-6 or fuel != 0 or infr not in {1, 2}:
                continue
            charging[geo_id][year] += val
            route_charging[(od_id, path_id)][year] += val
    with open(summary_file) as f:
        summary = yaml.safe_load(f)
    return charging, route_charging, summary


def compute_metrics(charging, route_charging, summary):
    """Same metric definitions as plot_soc_sensitivity.py."""
    out = {}
    for target_year in TARGET_YEARS:
        opt_geo = {g: charging.get(g, {}).get(target_year, 0) for g in all_geo_ids}
        heur_geo = defaultdict(float)
        for (od_id, path_id), year_dict in route_charging.items():
            total_e = year_dict.get(target_year, 0)
            if total_e < 1e-6:
                continue
            for g, mwh in compute_heuristic_charging(
                    od_id, path_id, total_e, od_path, path_seq, path_dist, breaks_by_path).items():
                heur_geo[g] += mwh

        total_energy = sum(v for v in opt_geo.values() if v > 0)
        relocated = sum(abs(opt_geo.get(g, 0) - heur_geo.get(g, 0))
                        for g in set(list(opt_geo.keys()) + list(heur_geo.keys()))) / 2
        reloc_pct = relocated / total_energy * 100 if total_energy > 0 else 0

        bev = float(summary['tonnes_by_year'].get(target_year, {}).get('BEV', 0))
        icev = float(summary['tonnes_by_year'].get(target_year, {}).get('ICEV', 0))
        bev_pct = bev / (bev + icev) * 100 if (bev + icev) > 0 else 0

        opt_country = defaultdict(float)
        for g in all_geo_ids:
            opt_country[geo_country.get(g, '??')] += opt_geo.get(g, 0)

        out[target_year] = {
            'reloc_pct': reloc_pct,
            'total_gwh': total_energy / 1000,
            'bev_pct': bev_pct,
            'obj': float(summary['objective_value']) / 1e9,
            'country_shares': {c: opt_country[c] / total_energy * 100 if total_energy > 0 else 0
                               for c in COUNTRIES},
        }
    return out


def build_table(sens_key):
    cfg = SENSITIVITIES[sens_key]
    results_base = BASE / 'results' / cfg['results_dir']
    print(f"\n=== {sens_key.upper()} sensitivity ===")

    results = {}
    available = []
    for run_name, label in cfg['runs']:
        loaded = load_run(results_base / run_name)
        if loaded is None:
            print(f"  {run_name}: MISSING - skipped")
            continue
        results[run_name] = compute_metrics(*loaded)
        available.append((run_name, label))
        print(f"  {run_name}: OK")

    if not available:
        print(f"  No runs available for {sens_key}")
        return

    # ── LaTeX table ──
    tex = r"""\documentclass[border=5pt]{standalone}
\usepackage{booktabs}
\usepackage{siunitx}

\begin{document}

\begin{tabular}{l S[table-format=3.2] S[table-format=3.1] S[table-format=4.0] S[table-format=2.1] S[table-format=2.1] S[table-format=2.1] S[table-format=2.1]}
\toprule
{""" + cfg['col_header'] + r"""} & {Obj} & {BEV} & {Total} & {Reloc.} & \multicolumn{3}{c}{Country share (\%)} \\
{} & {(bn~\euro)} & {(\%)} & {(GWh)} & {(\%)} & {IT} & {AT} & {DE} \\
\midrule
"""
    for target_year in TARGET_YEARS:
        tex += r"\multicolumn{8}{l}{\textbf{" + str(target_year) + r"}}" + " \\\\\n"
        for run_name, label in available:
            r = results[run_name][target_year]
            cs = r['country_shares']
            tex += (f"  {label} & {r['obj']:.2f} & {r['bev_pct']:.1f} & {r['total_gwh']:.0f} "
                    f"& {r['reloc_pct']:.1f} & {cs.get('IT', 0):.1f} & {cs.get('AT', 0):.1f} "
                    f"& {cs.get('DE', 0):.1f} \\\\\n")
        if target_year != TARGET_YEARS[-1]:
            tex += r"\addlinespace" + "\n"
    tex += r"""\bottomrule
\end{tabular}

\end{document}
"""
    tex_file = BASE / f"{cfg['tex_name']}.tex"
    with open(tex_file, 'w') as f:
        f.write(tex)
    print(f"  Saved: {tex_file.name}")

    try:
        subprocess.run(['pdflatex', '-interaction=nonstopmode', str(tex_file)],
                       capture_output=True, cwd=str(BASE), timeout=30)
        print(f"  Compiled: {cfg['tex_name']}.pdf")
    except Exception:
        print(f"  Compile manually: pdflatex {tex_file.name}")

    # ── Console print ──
    print("\n  " + "-" * 86)
    print(f"  {'Run':>26s}  {'Obj(bn)':>8s}  {'BEV%':>6s}  {'GWh':>6s}  "
          f"{'Reloc%':>7s}  {'IT%':>5s}  {'AT%':>5s}  {'DE%':>5s}")
    for target_year in TARGET_YEARS:
        print(f"  --- {target_year} ---")
        for run_name, label in available:
            r = results[run_name][target_year]
            cs = r['country_shares']
            plain = re.sub(r'[\$\\{}]|mathrm|infty|kappa|,', '', label).strip()
            print(f"  {plain:>26s}  {r['obj']:>8.2f}  {r['bev_pct']:>5.1f}%  "
                  f"{r['total_gwh']:>5.0f}G  {r['reloc_pct']:>6.1f}%  "
                  f"{cs.get('IT', 0):>4.1f}%  {cs.get('AT', 0):>4.1f}%  {cs.get('DE', 0):>4.1f}%")


def main():
    arg = sys.argv[1].lower() if len(sys.argv) > 1 else 'all'
    if arg == 'all':
        for key in SENSITIVITIES:
            build_table(key)
    elif arg in SENSITIVITIES:
        build_table(arg)
    else:
        print(f"Unknown sensitivity '{arg}'. Choose from: {', '.join(SENSITIVITIES)}, all")
        sys.exit(1)
    print("\nDone.")


if __name__ == '__main__':
    main()
