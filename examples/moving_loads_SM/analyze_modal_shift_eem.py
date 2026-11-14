"""
EEM paper analysis: percent of total annual demand shifted to rail.

For each EEM scenario, computes the rail share of total transport activity
(tkm = flow * path length), per modeled year, across all OD pairs and paths.

The `f` variable has keys:  (year, (product_id, odpair_id, path_id), (mode_id, tv_id), generation): value
  - value is the transport flow (vehicles)
  - tkm contribution = value * path.length
Mode 1 = road, Mode 2 = rail.

"% of total annual demand shifted" = rail_tkm(year) / total_tkm(year) * 100
(total tkm is the same fixed OD demand; rail share = the fraction shifted off road).
"""
import yaml
import re
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

SCRIPT_DIR = Path(__file__).parent
RESULTS_DIR = SCRIPT_DIR / 'results' / 'eem_scenarios'
INPUT_DIR = SCRIPT_DIR / 'input_data' / 'eem_scenarios'
FIGURES_DIR = SCRIPT_DIR / 'figures'
FIGURES_DIR.mkdir(exist_ok=True)

SCENARIOS = {
    'DE_unified':            {'label': 'Baseline',  'color': 'black',   'ls': '-'},
    'DE_split_low_from2032': {'label': 'L-2032',    'color': '#2196F3', 'ls': '-'},
    'DE_split_low_from2040': {'label': 'L-2040',    'color': '#2196F3', 'ls': ':'},
    'DE_split_mid_from2032': {'label': 'M-2032',    'color': '#FF9800', 'ls': '-'},
    'DE_split_mid_from2040': {'label': 'M-2040',    'color': '#FF9800', 'ls': ':'},
    'DE_split_high_from2032':{'label': 'H-2032',    'color': '#F44336', 'ls': '-'},
    'DE_split_high_from2040':{'label': 'H-2040',    'color': '#F44336', 'ls': ':'},
}

# f key: (year, (prod, od, path), (mode, tv), gen): value
PAT_F = re.compile(
    r'\((\d+),\s*\((\d+),\s*(\d+),\s*(\d+)\),\s*\((\d+),\s*(\d+)\),\s*(\d+)\)')


def load_path_lengths():
    paths = yaml.safe_load(open(INPUT_DIR / 'DE_unified' / 'Path.yaml'))
    return {p['id']: p['length'] for p in paths}


def find_latest_f_file(scenario):
    sc_dir = RESULTS_DIR / scenario
    files = sorted(sc_dir.glob('*_f_dict.yaml'))
    return files[-1] if files else None


def compute_rail_share(scenario, path_len):
    """Return dict year -> (rail_tkm, total_tkm, rail_share_pct)."""
    f_file = find_latest_f_file(scenario)
    if f_file is None:
        return None, None
    rail_tkm = {}
    total_tkm = {}
    with open(f_file) as fh:
        for line in fh:
            m = PAT_F.match(line.strip())
            if not m:
                continue
            year = int(m.group(1))
            path_id = int(m.group(4))
            mode_id = int(m.group(5))
            # value after the ': '
            try:
                value = float(line.split(':', 1)[1])
            except (IndexError, ValueError):
                continue
            tkm = value * path_len.get(path_id, 0.0)
            total_tkm[year] = total_tkm.get(year, 0.0) + tkm
            if mode_id == 2:  # rail
                rail_tkm[year] = rail_tkm.get(year, 0.0) + tkm
    result = {}
    for year in sorted(total_tkm):
        r = rail_tkm.get(year, 0.0)
        t = total_tkm[year]
        result[year] = (r, t, 100.0 * r / t if t > 0 else 0.0)
    return result, f_file.name


def main():
    path_len = load_path_lengths()
    print(f"Loaded {len(path_len)} path lengths\n")

    all_results = {}
    for sc in SCENARIOS:
        res, fname = compute_rail_share(sc, path_len)
        if res is None:
            print(f"  [skip] {sc}: no f_dict file")
            continue
        all_results[sc] = res
        print(f"=== {SCENARIOS[sc]['label']} ({sc}) ===  [{fname}]")
        print(f"  {'Year':>6} {'Rail tkm':>16} {'Total tkm':>16} {'Rail %':>8}")
        for year, (r, t, pct) in res.items():
            print(f"  {year:>6} {r:>16,.1f} {t:>16,.1f} {pct:>7.2f}%")
        print()

    # ---- Plot ----
    fig, ax = plt.subplots(figsize=(9, 5.5))
    for sc, res in all_results.items():
        years = sorted(res)
        pct = [res[y][2] for y in years]
        s = SCENARIOS[sc]
        ax.plot(years, pct, label=s['label'], color=s['color'],
                ls=s['ls'], lw=2, marker='o', ms=3)
    ax.axhline(30, color='grey', ls='--', lw=1, alpha=0.7)
    ax.text(ax.get_xlim()[1], 30, ' max rail cap (30%)', va='center',
            ha='left', fontsize=8, color='grey')
    ax.set_xlabel('Year')
    ax.set_ylabel('Share of total annual demand shifted to rail [% of tkm]')
    ax.set_title('Modal shift to rail across EEM scenarios')
    ax.legend(ncol=2, fontsize=9)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    out = FIGURES_DIR / 'eem_modal_shift_rail_share.png'
    fig.savefig(out, dpi=300, bbox_inches='tight')
    print(f"Saved figure: {out}")


if __name__ == '__main__':
    main()
