"""
Generate standalone LaTeX tables showing the maximum cumulative installed
CCS+MCS charger capacity at any single NUTS-2 node under each kappa^pwr and
kappa^space setting. Used in the appendix to justify the baseline values.

Charger capacities are computed from the q_fuel_infr_plus_dict.yaml files
produced by the kappa / kspace sensitivity runs. CCS chargers are rated at
100 kW and MCS at 1000 kW per unit (per FuelingInfrTypes.yaml).
"""
import re, glob, yaml, pathlib, subprocess
from collections import defaultdict

BASE = pathlib.Path(__file__).resolve().parent
ci3_pat = re.compile(r'CartesianIndex\((\d+),\s*(\d+),\s*(\d+)\):\s*([\d.eE+-]+)')

with open(BASE / 'input_data/fixed_nuts_2/GeographicElement.yaml') as f:
    geo_data = yaml.safe_load(f)
geo_name = {g['id']: g.get('name', '?').replace('nuts2_', '') for g in geo_data}
geo_country = {g['id']: g.get('country', '??') for g in geo_data}

MODELED_YEARS = list(range(2020, 2064, 4))
y_idx_to_year = {i+1: y for i, y in enumerate(MODELED_YEARS)}

# Charger powers (kW per unit) from FuelingInfrTypes.yaml
# fi index in q_fuel_infr_plus YAML is a POSITION into f_l_pairs, not FuelingInfrTypes id.
# In current runs: fi=1 -> MCS (1000 kW), fi=2 -> CCS (100 kW).
# See memory: q-fuel-infr-plus-yaml-parsing.
CHARGER_KW = {1: 1000, 2: 100}   # 1 = MCS, 2 = CCS
TARGET_YEARS = [2032, 2040, 2048]


def analyze(run_dir):
    """Return {year: (top_node_label, max_mw, max_charge_points)} or None."""
    q_files = sorted(glob.glob(str(run_dir / '*_q_fuel_infr_plus_dict.yaml')))
    if not q_files:
        return None
    per_year_kw = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    with open(q_files[-1]) as f:
        for line in f:
            m = ci3_pat.match(line.strip())
            if not m:
                continue
            yi, fi, pos = int(m.group(1)), int(m.group(2)), int(m.group(3))
            val_kw = float(m.group(4))
            if val_kw < 1e-3 or fi == 3:
                continue
            yr = y_idx_to_year.get(yi)
            if yr is None:
                continue
            per_year_kw[pos - 1][yr][fi] += val_kw

    out = {}
    for target_year in TARGET_YEARS:
        node_kw = defaultdict(float)
        node_mcs_units = defaultdict(float)  # fi=1
        node_ccs_units = defaultdict(float)  # fi=2
        for gid, years in per_year_kw.items():
            for y, fis in years.items():
                if y > target_year:
                    continue
                for fi, kw in fis.items():
                    node_kw[gid] += kw
                    if fi == 1:    # MCS: 1000 kW per unit
                        node_mcs_units[gid] += kw / CHARGER_KW[1]
                    elif fi == 2:  # CCS: 100 kW per unit
                        node_ccs_units[gid] += kw / CHARGER_KW[2]
        if not node_kw:
            out[target_year] = None
            continue
        top_gid = max(node_kw, key=node_kw.get)
        total_cp = node_mcs_units[top_gid] + node_ccs_units[top_gid]
        out[target_year] = (
            f"{geo_name.get(top_gid, '?')} ({geo_country.get(top_gid, '?')})",
            node_kw[top_gid] / 1000.0,
            node_mcs_units[top_gid],
            node_ccs_units[top_gid],
            total_cp,
        )
    return out


SENSITIVITIES = {
    'kappa': {
        'results_dir': 'kappa_sensitivity',
        'runs': [
            ('no_cap',    r'$\infty$ (no cap)'),
            ('kappa_0.5', r'$\kappa^{\mathrm{pwr}} = 0.5$ (baseline)'),
            ('kappa_0.3', r'$\kappa^{\mathrm{pwr}} = 0.3$'),
            ('kappa_0.2', r'$\kappa^{\mathrm{pwr}} = 0.2$'),
            ('kappa_0.1', r'$\kappa^{\mathrm{pwr}} = 0.1$'),
        ],
        'col_header': r'$\kappa^{\mathrm{pwr}}$',
        'tex_name': 'kappa_maxnode_table',
        'caption': (r'Maximum cumulative installed CCS\,+\,MCS capacity at any single '
                    r'NUTS-2 node, by year and $\kappa^{\mathrm{pwr}}$ setting. The last '
                    r'column reports the equivalent number of charger units '
                    r'(CCS rated at 100\,kW, MCS at 1\,MW).'),
        'label': 'tab:kappa_maxnode',
    },
    'kspace': {
        'results_dir': 'kspace_sensitivity',
        'runs': [
            ('no_space_cap',  r'$\infty$ (no cap)'),
            ('kspace_0.001',  r'$\kappa^{\mathrm{space}} = 0.001$'),
            ('kspace_0.0005', r'$\kappa^{\mathrm{space}} = 0.0005$ (baseline)'),
            ('kspace_0.0002', r'$\kappa^{\mathrm{space}} = 0.0002$'),
            ('kspace_0.0001', r'$\kappa^{\mathrm{space}} = 0.0001$'),
        ],
        'col_header': r'$\kappa^{\mathrm{space}}$',
        'tex_name': 'kspace_maxnode_table',
        'caption': (r'Maximum cumulative installed CCS\,+\,MCS capacity at any single '
                    r'NUTS-2 node, by year and $\kappa^{\mathrm{space}}$ setting. The last '
                    r'column reports the equivalent number of charger units '
                    r'(CCS rated at 100\,kW, MCS at 1\,MW).'),
        'label': 'tab:kspace_maxnode',
    },
}


def build_table(sens_key):
    cfg = SENSITIVITIES[sens_key]
    results_base = BASE / 'results' / cfg['results_dir']
    print(f"\n=== {sens_key.upper()} max-node table ===")

    rows = []
    for run_name, label in cfg['runs']:
        r = analyze(results_base / run_name)
        if r is None:
            print(f"  {run_name}: MISSING - skipped")
            continue
        rows.append((label, r))
        print(f"  {run_name}: OK")

    if not rows:
        print(f"  No runs available for {sens_key}")
        return

    tex = r"""\documentclass[border=5pt]{standalone}
\usepackage{booktabs}
\usepackage{siunitx}

\begin{document}

\begin{tabular}{l l l S[table-format=3.0] S[table-format=3.0] S[table-format=3.0] S[table-format=4.0]}
\toprule
{""" + cfg['col_header'] + r"""} & {Year} & {Top node} & {Cum.\ MW} & {MCS units} & {CCS units} & {Total units} \\
\midrule
"""
    for i, (label, r) in enumerate(rows):
        first = True
        for y in TARGET_YEARS:
            if r[y] is None:
                continue
            node_label, mw, mcs, ccs, total_cp = r[y]
            label_cell = label if first else ''
            tex += f"  {label_cell} & {y} & {node_label} & {mw:.0f} & {mcs:.0f} & {ccs:.0f} & {total_cp:.0f} \\\\\n"
            first = False
        if i != len(rows) - 1:
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

    # Console view
    print(f"\n  {'Setting':<26s} {'Year':<6s} {'Top node':<22s} {'MW':>8s} {'MCS':>6s} {'CCS':>6s} {'Total':>7s}")
    print("  " + "-" * 86)
    for label, r in rows:
        plain = re.sub(r'[\$\\{}]|mathrm|infty|kappa|pwr|space|,', '', label).strip()
        for y in TARGET_YEARS:
            if r[y] is None:
                continue
            node_label, mw, mcs, ccs, tot = r[y]
            print(f"  {plain:<26s} {y:<6d} {node_label:<22s} {mw:>8.1f} {mcs:>6.0f} {ccs:>6.0f} {tot:>7.0f}")
        print()


if __name__ == '__main__':
    for k in SENSITIVITIES:
        build_table(k)
    print("Done.")
