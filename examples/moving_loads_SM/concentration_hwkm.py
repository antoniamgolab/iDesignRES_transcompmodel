"""Compare GWh/highway-km concentration: baseline vs rail, Go RES."""
import yaml, re, pathlib, csv
from collections import defaultdict
import numpy as np

BASE = pathlib.Path(__file__).resolve().parent
INPUT_BASE = BASE / 'input_data/uncertainty_scenarios'
INPUT_RAIL = BASE / 'input_data/uncertainty_scenarios_rail'
RESULTS_BASE = BASE / 'results/uncertainty_scenarios_v2'
RESULTS_RAIL = BASE / 'results/rail'

YEAR_MAPPING = {i: 2020 + (i - 1) * 4 for i in range(1, 15)}
YEAR_TO_INDEX = {v: k for k, v in YEAR_MAPPING.items()}
BEV_FL_IDXS = {1, 2}

with open(BASE / 'input_data/fixed_nuts_2/GeographicElement.yaml') as f:
    geo_data = yaml.safe_load(f)
geo_id_to_nuts2 = {g['id']: g.get('nuts2_region', '') for g in geo_data if g.get('type') == 'node'}
geo_id_to_country = {g['id']: g.get('country', '') for g in geo_data if g.get('type') == 'node'}

# Load highway km
hw_km = {}
with open(BASE / 'highway_km_per_nuts2.csv') as f:
    for row in csv.DictReader(f):
        hw_km[row['NUTS2_CODE']] = float(row['highway_km'])

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


print("Loading Go RES baseline...")
base = load_nuts2_energy(
    RESULTS_BASE, 'scenario_000',
    'scenario_000_cs_2026-02-14_18-25-42_s_dict.yaml',
    INPUT_BASE, 'scenario_000')

print("Loading Go RES + Rail...")
rail = load_nuts2_energy(
    RESULTS_RAIL, 'scenario_004',
    'scenario_004_cs_2026-02-14_20-52-20_s_dict.yaml',
    INPUT_RAIL, 'scenario_004')

countries_order = ['NO', 'FI', 'SE', 'DK', 'DE', 'AT', 'IT']
years = [2032, 2040, 2048]

for year in years:
    yi = YEAR_TO_INDEX[year]
    print(f"\n===== {year} =====")

    # Get all NUTS-2 with any demand
    all_n2 = set()
    for (y, n2) in list(base.keys()) + list(rail.keys()):
        if y == yi:
            all_n2.add(n2)

    # Filter to regions with highway data
    n2_with_hw = [n2 for n2 in sorted(all_n2) if hw_km.get(n2, 0) > 0]

    # Compute GWh/highway-km
    b_intensity = {}
    r_intensity = {}
    for n2 in n2_with_hw:
        km = hw_km[n2]
        b_intensity[n2] = base.get((yi, n2), 0) / km * 1e3  # MWh/hw-km
        r_intensity[n2] = rail.get((yi, n2), 0) / km * 1e3

    # Aggregate by country: total GWh / total hw-km
    for c in countries_order:
        c_n2 = [n2 for n2 in n2_with_hw if n2.startswith(c)]
        if not c_n2:
            continue
        c_gwh_b = sum(base.get((yi, n2), 0) for n2 in c_n2)
        c_gwh_r = sum(rail.get((yi, n2), 0) for n2 in c_n2)
        c_km = sum(hw_km[n2] for n2 in c_n2)
        int_b = c_gwh_b / c_km * 1e3 if c_km > 0 else 0  # MWh/hw-km
        int_r = c_gwh_r / c_km * 1e3 if c_km > 0 else 0
        delta = int_r - int_b
        pct = delta / int_b * 100 if int_b > 0.01 else 0
        print(f"  {c}: {int_b:>7.1f} -> {int_r:>7.1f} MWh/hw-km  ({delta:+.1f}, {pct:+.0f}%)  "
              f"[{c_gwh_b:.0f}->{c_gwh_r:.0f} GWh, {c_km:.0f} km]")

    # Concentration metrics on intensity values
    b_vals = np.array([b_intensity.get(n2, 0) for n2 in n2_with_hw])
    r_vals = np.array([r_intensity.get(n2, 0) for n2 in n2_with_hw])

    # HHI on intensity shares
    b_s = b_vals / b_vals.sum() if b_vals.sum() > 0 else b_vals
    r_s = r_vals / r_vals.sum() if r_vals.sum() > 0 else r_vals
    hhi_b = (b_s ** 2).sum() * 10000
    hhi_r = (r_s ** 2).sum() * 10000

    gini_b = gini(b_vals)
    gini_r = gini(r_vals)

    # Max intensity region
    b_max_n2 = n2_with_hw[np.argmax(b_vals)]
    r_max_n2 = n2_with_hw[np.argmax(r_vals)]

    # Top-3
    b_top3_idx = np.argsort(b_vals)[-3:][::-1]
    r_top3_idx = np.argsort(r_vals)[-3:][::-1]

    print(f"\n  Concentration metrics (GWh/hw-km based):")
    print(f"    HHI:  {hhi_b:.0f} -> {hhi_r:.0f}  ({hhi_r - hhi_b:+.0f})")
    print(f"    Gini: {gini_b:.3f} -> {gini_r:.3f}  ({gini_r - gini_b:+.3f})")
    print(f"    Max:  {b_max_n2} ({b_vals.max():.1f}) -> {r_max_n2} ({r_vals.max():.1f}) MWh/hw-km")

    print(f"\n  Top-5 NUTS-2 by intensity:")
    b_ranked = sorted(zip(b_vals, [n2_with_hw[i] for i in range(len(n2_with_hw))]), reverse=True)
    r_ranked = sorted(zip(r_vals, [n2_with_hw[i] for i in range(len(n2_with_hw))]), reverse=True)
    print(f"    {'Baseline':>30}  {'Rail':>30}")
    for i in range(5):
        bv, bn = b_ranked[i]
        rv, rn = r_ranked[i]
        print(f"    {bn} {bv:>7.1f} MWh/hw-km     {rn} {rv:>7.1f} MWh/hw-km")

    # Biggest intensity increases/decreases
    intensity_deltas = [(r_intensity.get(n2, 0) - b_intensity.get(n2, 0), n2, n2[:2],
                         b_intensity.get(n2, 0), r_intensity.get(n2, 0))
                        for n2 in n2_with_hw]
    intensity_deltas.sort()

    print(f"\n  Biggest intensity DECREASES (MWh/hw-km):")
    for d, n2, ctry, bv, rv in intensity_deltas[:5]:
        print(f"    {n2} ({ctry}): {bv:.1f} -> {rv:.1f}  ({d:+.1f})")
    print(f"  Biggest intensity INCREASES (MWh/hw-km):")
    for d, n2, ctry, bv, rv in reversed(intensity_deltas[-5:]):
        print(f"    {n2} ({ctry}): {bv:.1f} -> {rv:.1f}  ({d:+.1f})")
