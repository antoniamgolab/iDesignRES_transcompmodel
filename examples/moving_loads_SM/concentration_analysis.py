"""Compare spatial concentration of charging demand: baseline vs rail modal shift."""
import yaml, re, pathlib
from collections import defaultdict
import numpy as np

BASE = pathlib.Path(__file__).resolve().parent
INPUT_BASE = BASE / 'input_data/uncertainty_scenarios'
INPUT_RAIL = BASE / 'input_data/uncertainty_scenarios_rail'
RESULTS_BASE = BASE / 'results/uncertainty_scenarios_v2'
RESULTS_RAIL = BASE / 'results/rail'

BASELINE = {
    'scenario_000': {'s_file': 'scenario_000_cs_2026-02-14_18-25-42_s_dict.yaml', 'input': 'scenario_000'},
    'scenario_001': {'s_file': 'scenario_001_cs_2026-02-14_20-00-45_s_dict.yaml', 'input': 'scenario_001'},
    'scenario_002': {'s_file': 'scenario_002_cs_2026-02-14_22-18-02_s_dict.yaml', 'input': 'scenario_002'},
    'scenario_003': {'s_file': 'scenario_003_cs_2026-02-15_00-33-53_s_dict.yaml', 'input': 'scenario_003'},
}
RAIL = {
    'scenario_004': {'s_file': 'scenario_004_cs_2026-02-14_20-52-20_s_dict.yaml', 'input': 'scenario_004'},
    'scenario_010': {'s_file': 'scenario_010_cs_2026-02-14_21-34-41_s_dict.yaml', 'input': 'scenario_010'},
    'scenario_016': {'s_file': 'scenario_016_cs_2026-02-14_22-16-25_s_dict.yaml', 'input': 'scenario_016'},
    'scenario_022': {'s_file': 'scenario_022_cs_2026-02-14_22-49-14_s_dict.yaml', 'input': 'scenario_022'},
}
PAIRS = [
    ('scenario_000', 'scenario_004', 'Go RES'),
    ('scenario_001', 'scenario_010', 'NECPEssentials'),
    ('scenario_002', 'scenario_016', 'REPowerEU++'),
    ('scenario_003', 'scenario_022', 'Trinity'),
]

YEAR_MAPPING = {i: 2020 + (i - 1) * 4 for i in range(1, 15)}
YEAR_TO_INDEX = {v: k for k, v in YEAR_MAPPING.items()}
BEV_FL_IDXS = {1, 2}

with open(BASE / 'input_data/fixed_nuts_2/GeographicElement.yaml') as f:
    geo_data = yaml.safe_load(f)
geo_id_to_nuts2 = {g['id']: g.get('nuts2_region', '') for g in geo_data if g.get('type') == 'node'}

ci_re = re.compile(r'CartesianIndex\((\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\):\s*(.+)')


def build_prkg(input_dir, scenario_id):
    inp = input_dir / scenario_id
    with open(inp / 'Path.yaml') as f:
        paths = yaml.load(f, Loader=yaml.UnsafeLoader)
    with open(inp / 'Odpair.yaml') as f:
        odpairs = yaml.load(f, Loader=yaml.UnsafeLoader)
    path_by_id = {int(p['id']): [int(x) for x in p['sequence']] for p in paths}
    s = set()
    for od in odpairs:
        for geo_id in path_by_id[int(od['path_id'])]:
            s.add((0, int(od['id']), int(od['path_id']), geo_id))
    return {i + 1: t[3] for i, t in enumerate(sorted(s))}


def load_nuts2_energy(results_dir, scenario_id, s_file, input_dir, input_scen):
    prkg = build_prkg(input_dir, input_scen)
    energy = defaultdict(float)
    with open(results_dir / scenario_id / s_file) as f:
        for line in f:
            m = ci_re.match(line.strip())
            if not m:
                continue
            yr_pos = int(m.group(1))
            prkg_pos = int(m.group(2))
            fl_pos = int(m.group(4))
            val = float(m.group(6))
            if fl_pos not in BEV_FL_IDXS:
                continue
            geo_id = prkg.get(prkg_pos)
            if geo_id is None:
                continue
            n2 = geo_id_to_nuts2.get(geo_id, '')
            if n2:
                energy[(yr_pos, n2)] += val / 1e3  # GWh
    return dict(energy)


def gini(x):
    x = np.sort(x)
    n = len(x)
    if x.sum() == 0:
        return 0
    idx = np.arange(1, n + 1)
    return (2 * np.sum(idx * x) - (n + 1) * np.sum(x)) / (n * np.sum(x))


# Load all
print("Loading baseline scenarios...")
base_nuts2 = {}
for sid, cfg in BASELINE.items():
    base_nuts2[sid] = load_nuts2_energy(RESULTS_BASE, sid, cfg['s_file'], INPUT_BASE, cfg['input'])

print("Loading rail scenarios...")
rail_nuts2 = {}
for sid, cfg in RAIL.items():
    rail_nuts2[sid] = load_nuts2_energy(RESULTS_RAIL, sid, cfg['s_file'], INPUT_RAIL, cfg['input'])

years = [2032, 2040, 2048]

for year in years:
    yi = YEAR_TO_INDEX[year]
    print(f"\n===== {year} =====")

    for bsid, rsid, name in PAIRS:
        all_n2 = set()
        for (y, n2) in list(base_nuts2[bsid].keys()) + list(rail_nuts2[rsid].keys()):
            if y == yi:
                all_n2.add(n2)

        b_vals = np.array([base_nuts2[bsid].get((yi, n2), 0) for n2 in sorted(all_n2)])
        r_vals = np.array([rail_nuts2[rsid].get((yi, n2), 0) for n2 in sorted(all_n2)])

        b_total = b_vals.sum()
        r_total = r_vals.sum()

        # Shares
        b_s = b_vals / b_total if b_total > 0 else b_vals
        r_s = r_vals / r_total if r_total > 0 else r_vals

        # HHI
        hhi_base = (b_s ** 2).sum() * 10000
        hhi_rail = (r_s ** 2).sum() * 10000

        # Gini
        gini_base = gini(b_vals)
        gini_rail = gini(r_vals)

        # Top-1, Top-3
        b_sorted = sorted(b_vals, reverse=True)
        r_sorted = sorted(r_vals, reverse=True)
        top1_base = b_sorted[0] / b_total * 100 if b_total > 0 else 0
        top1_rail = r_sorted[0] / r_total * 100 if r_total > 0 else 0
        top3_base = sum(b_sorted[:3]) / b_total * 100 if b_total > 0 else 0
        top3_rail = sum(r_sorted[:3]) / r_total * 100 if r_total > 0 else 0

        # DE share
        de_base = sum(base_nuts2[bsid].get((yi, n2), 0) for n2 in all_n2 if n2.startswith('DE')) / b_total * 100 if b_total > 0 else 0
        de_rail = sum(rail_nuts2[rsid].get((yi, n2), 0) for n2 in all_n2 if n2.startswith('DE')) / r_total * 100 if r_total > 0 else 0

        print(f"\n  {name}:")
        print(f"    Total:         {b_total:.0f} -> {r_total:.0f} GWh ({r_total-b_total:+.0f}, {(r_total-b_total)/b_total*100:+.1f}%)")
        print(f"    HHI:           {hhi_base:.0f} -> {hhi_rail:.0f}  ({hhi_rail - hhi_base:+.0f})")
        print(f"    Gini:          {gini_base:.3f} -> {gini_rail:.3f}  ({gini_rail - gini_base:+.3f})")
        print(f"    Top-1 share:   {top1_base:.1f}% -> {top1_rail:.1f}%  ({top1_rail - top1_base:+.1f} pp)")
        print(f"    Top-3 share:   {top3_base:.1f}% -> {top3_rail:.1f}%  ({top3_rail - top3_base:+.1f} pp)")
        print(f"    DE share:      {de_base:.1f}% -> {de_rail:.1f}%  ({de_rail - de_base:+.1f} pp)")


# Detail: Go RES 2040, top movers
print("\n\n===== TOP NUTS-2 SHARE CHANGES (2040, Go RES) =====")
bsid, rsid = 'scenario_000', 'scenario_004'
yi = YEAR_TO_INDEX[2040]
all_n2 = set()
for (y, n2) in list(base_nuts2[bsid].keys()) + list(rail_nuts2[rsid].keys()):
    if y == yi:
        all_n2.add(n2)
b_total = sum(base_nuts2[bsid].get((yi, n2), 0) for n2 in all_n2)
r_total = sum(rail_nuts2[rsid].get((yi, n2), 0) for n2 in all_n2)

deltas = []
for n2 in all_n2:
    bs = base_nuts2[bsid].get((yi, n2), 0) / b_total * 100
    rs = rail_nuts2[rsid].get((yi, n2), 0) / r_total * 100
    bg = base_nuts2[bsid].get((yi, n2), 0)
    rg = rail_nuts2[rsid].get((yi, n2), 0)
    deltas.append((rs - bs, n2, n2[:2], bs, rs, bg, rg))

deltas.sort()
print(f"\nLargest DECREASES in share:")
print(f"{'NUTS-2':>7} {'Ctry':>4} {'Base %':>7} {'Rail %':>7} {'D pp':>7} {'Base GWh':>9} {'Rail GWh':>9}")
for d, n2, ctry, bs, rs, bg, rg in deltas[:10]:
    print(f"{n2:>7} {ctry:>4} {bs:>7.1f} {rs:>7.1f} {d:>+7.1f} {bg:>9.1f} {rg:>9.1f}")

print(f"\nLargest INCREASES in share:")
for d, n2, ctry, bs, rs, bg, rg in reversed(deltas[-10:]):
    print(f"{n2:>7} {ctry:>4} {bs:>7.1f} {rs:>7.1f} {d:>+7.1f} {bg:>9.1f} {rg:>9.1f}")
