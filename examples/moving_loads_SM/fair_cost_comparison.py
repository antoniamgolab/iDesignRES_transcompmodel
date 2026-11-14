"""
Fair comparison of electricity + infrastructure cost between system-optimal and
SOC-aware heuristic. Scales heuristic energy to match optimizer total per year.
"""
import re, yaml, pathlib
import numpy as np
from collections import defaultdict

BASE = pathlib.Path(__file__).resolve().parent
inp = BASE / 'input_data/uncertainty_scenarios/scenario_000'

MODELED_YEARS = list(range(2020, 2064, 4))
y_idx_map = {i+1: y for i, y in enumerate(MODELED_YEARS)}
Y_INIT = 2020; GAMMA = 0.3; HRS = 8760; DR = 0.04; TIMESTEP = 4
BATTERY_CAP = 400; SPEC_CONS = 1.1
FACTOR = 1000.0 / (GAMMA * HRS)  # MWh -> required kW

# Load inputs
print("Loading data...")
with open(inp / 'FuelingInfrTypes.yaml') as f:
    fit = yaml.safe_load(f)
om = next(x for x in fit if x['id'] == 1)['om_costs']
NET = 14.688

with open(BASE / 'input_data/fixed_nuts_2/GeographicElement.yaml') as f:
    geo_country = {g['id']: g.get('country', '??') for g in yaml.safe_load(f)}

with open(inp / 'FuelCost.yaml') as f:
    fc = yaml.safe_load(f)
elec_p = {}
for e in fc:
    if e['fuel'] == 'electricity':
        elec_p[(e['location'], e['fueling_infr_type_id'])] = e['cost_per_kWh']

with open(inp / 'Path.yaml') as f:
    paths = yaml.load(f, Loader=yaml.UnsafeLoader)
with open(inp / 'Odpair.yaml') as f:
    odpairs = yaml.load(f, Loader=yaml.UnsafeLoader)
with open(inp / 'MandatoryBreaks.yaml') as f:
    brk_data = yaml.safe_load(f)

path_by_id = {int(p['id']): [int(x) for x in p['sequence']] for p in paths}
path_dist = {int(p['id']): [float(d) for d in p.get('distance_from_previous', [])] for p in paths}
od_path = {int(o['id']): int(o['path_id']) for o in odpairs}
breaks_by = defaultdict(set)
for b in brk_data:
    breaks_by[int(b['path_id'])].add(int(b['latest_geo_id']))

prkg_map = {}
with open(BASE / 'prkg_ordering_elsevier.txt') as f:
    for line in f:
        line = line.strip()
        if not line: continue
        parts = line.split('\t')
        prkg_map[int(parts[0])] = tuple(int(x.strip()) for x in parts[1].strip('()').split(','))

# Parse s_dict
print("Parsing s_dict...")
ci5 = re.compile(r'CartesianIndex\((\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\):\s*([\d.eE+-]+)')
s_file = BASE / 'results/uncertainty_scenarios_v2/scenario_000/scenario_000_cs_2026-02-14_18-25-42_s_dict.yaml'

opt_geo_year = defaultdict(lambda: defaultdict(float))
route_year = defaultdict(lambda: defaultdict(float))
with open(s_file) as f:
    for line in f:
        m = ci5.match(line.strip())
        if not m: continue
        yi, pi, fi = int(m.group(1)), int(m.group(2)), int(m.group(4))
        val = float(m.group(6))
        if val < 1e-6 or fi not in {1, 2}: continue
        p = prkg_map.get(pi)
        if p is None: continue
        yr = y_idx_map.get(yi)
        if yr is None: continue
        opt_geo_year[p[3]][yr] += val
        route_year[(p[1], p[2])][yr] += val

# Heuristic charging distribution
print("Computing heuristic...")

def heur_distribute(od_id, path_id, total_e):
    pid = od_path.get(od_id, path_id)
    seq = path_by_id.get(pid, [])
    dist = path_dist.get(pid, [])
    bs = breaks_by.get(pid, set())
    if not seq or not dist or len(seq) != len(dist):
        return {}
    bi = [i for i, g in enumerate(seq) if g in bs]
    if not bi:
        return {}
    cum = []
    d = 0
    for dd in dist:
        d += dd
        cum.append(d)
    td = cum[-1]
    if td < 1:
        return {}
    ept = SPEC_CONS * td / 1000
    if ept < 1e-9:
        return {}
    nt = total_e / ept
    soc = BATTERY_CAP * 0.5
    charges = {}
    for i, b in enumerate(bi):
        prev = cum[bi[i-1]] if i > 0 else 0
        soc -= SPEC_CONS * (cum[b] - prev)
        nxt = cum[bi[i+1]] - cum[b] if i < len(bi) - 1 else td - cum[b]
        en = SPEC_CONS * nxt
        if soc < en:
            ch = min(BATTERY_CAP - soc, en - soc + BATTERY_CAP * 0.1, BATTERY_CAP - soc)
            if ch > 0:
                charges[seq[b]] = charges.get(seq[b], 0) + ch
                soc += ch
    return {g: kwh * nt / 1000 for g, kwh in charges.items()}

heur_geo_year_raw = defaultdict(lambda: defaultdict(float))
heur_raw_total = defaultdict(float)
for (od, pid), yd in route_year.items():
    for yr, te in yd.items():
        dist = heur_distribute(od, pid, te)
        for g, mwh in dist.items():
            heur_geo_year_raw[g][yr] += mwh
            heur_raw_total[yr] += mwh

# Scale heuristic to match opt total per year
opt_total_yr = defaultdict(float)
for g in opt_geo_year:
    for yr in MODELED_YEARS:
        opt_total_yr[yr] += opt_geo_year[g][yr]

heur_geo_year = defaultdict(lambda: defaultdict(float))
for g in heur_geo_year_raw:
    for yr in MODELED_YEARS:
        raw = heur_raw_total[yr]
        opt_t = opt_total_yr[yr]
        scale = opt_t / raw if raw > 0 else 1
        heur_geo_year[g][yr] = heur_geo_year_raw[g][yr] * scale

# Verify scaling
for yr in [2032, 2040, 2048]:
    h = sum(heur_geo_year[g][yr] for g in heur_geo_year)
    o = opt_total_yr[yr]
    print(f"  {yr}: opt={o:.0f} MWh, heur_scaled={h:.0f} MWh, ratio={h/o:.4f}")

# Compute costs
print("\nComputing costs...")
all_geos = set(list(opt_geo_year.keys()) + list(heur_geo_year.keys()))

opt_cum_req = defaultdict(float)
heur_cum_req = defaultdict(float)

header = "Year  |  Opt Elec  Opt Infra  Opt Total |  Heur Elec Heur Infra Heur Total |  Delta    ct/kWh(opt) ct/kWh(heur)"
print("\n" + "=" * len(header))
print("FAIR COMPARISON: Same total energy, different spatial distribution (all MEUR, discounted)")
print("=" * len(header))
print(header)
print("-" * len(header))

tot = defaultdict(float)
for yr in MODELED_YEARS:
    yo = yr - Y_INIT
    df = 1 / (1 + DR) ** (yr - Y_INIT)
    ic = om[min(yo, len(om) - 1)] + NET

    oe = he = 0.0
    oe_kwh = he_kwh = 0.0
    oi = hi = 0.0

    for g in all_geos:
        # Electricity
        s_opt = opt_geo_year[g].get(yr, 0)
        s_heur = heur_geo_year[g].get(yr, 0)
        prices = elec_p.get((g, 1), [])
        price = prices[yo] if yo < len(prices) else 0

        if s_opt > 0:
            oe += s_opt * 1000 * price
            oe_kwh += s_opt * 1000
        if s_heur > 0:
            he += s_heur * 1000 * price
            he_kwh += s_heur * 1000

        # Infrastructure: required kW = s * FACTOR, use cumulative max
        req_opt = opt_geo_year[g].get(yr, 0) * FACTOR
        req_heur = heur_geo_year[g].get(yr, 0) * FACTOR
        opt_cum_req[g] = max(opt_cum_req[g], req_opt)
        heur_cum_req[g] = max(heur_cum_req[g], req_heur)
        oi += opt_cum_req[g] * ic
        hi += heur_cum_req[g] * ic

    oe_d = oe * df * TIMESTEP / 1e6
    he_d = he * df * TIMESTEP / 1e6
    oi_d = oi * df * TIMESTEP / 1e6
    hi_d = hi * df * TIMESTEP / 1e6

    opt_avg = oe / oe_kwh * 100 if oe_kwh > 0 else 0
    heur_avg = he / he_kwh * 100 if he_kwh > 0 else 0

    ot = oe_d + oi_d
    ht = he_d + hi_d
    d = ht - ot

    for k, v in [('oe', oe_d), ('oi', oi_d), ('he', he_d), ('hi', hi_d)]:
        tot[k] += v

    print(f"{yr:>4d}  | {oe_d:>9.1f} {oi_d:>9.1f} {ot:>9.1f} | {he_d:>9.1f} {hi_d:>9.1f} {ht:>9.1f} | {d:>+8.1f}  {opt_avg:>10.2f}    {heur_avg:>10.2f}")

print("-" * len(header))
to = tot['oe'] + tot['oi']
th = tot['he'] + tot['hi']
print(f"{'TOT':>4s}  | {tot['oe']:>9.1f} {tot['oi']:>9.1f} {to:>9.1f} | {tot['he']:>9.1f} {tot['hi']:>9.1f} {th:>9.1f} | {th-to:>+8.1f}")

print(f"\n{'='*80}")
print("SUMMARY")
print(f"{'='*80}")
print(f"  Electricity: opt {tot['oe']:.1f} vs heur {tot['he']:.1f} MEUR -> delta {tot['he']-tot['oe']:+.1f} MEUR")
print(f"  Infrastructure: opt {tot['oi']:.1f} vs heur {tot['hi']:.1f} MEUR -> delta {tot['hi']-tot['oi']:+.1f} MEUR")
print(f"  Total: opt {to:.1f} vs heur {th:.1f} MEUR -> delta {th-to:+.1f} MEUR ({(th-to)/to*100:+.1f}%)")
print()
print(f"  The heuristic saves {tot['oe']-tot['he']:.1f} MEUR on electricity")
print(f"  but costs {tot['hi']-tot['oi']:+.1f} MEUR more/less on infrastructure")
print(f"  Net effect: {th-to:+.1f} MEUR ({(th-to)/to*100:+.1f}%)")

# By country at 2040
print(f"\n{'='*80}")
print("CHARGING DISTRIBUTION BY COUNTRY (2040, scaled to same total)")
print(f"{'='*80}")
opt_c = defaultdict(float)
heur_c = defaultdict(float)
for g in all_geos:
    c = geo_country.get(g, '??')
    opt_c[c] += opt_geo_year[g].get(2040, 0)
    heur_c[c] += heur_geo_year[g].get(2040, 0)

total_opt = sum(opt_c.values())
total_heur = sum(heur_c.values())
print(f"  {'Country':>8s}  {'Opt(MWh)':>12s}  {'Opt%':>7s}  {'Heur(MWh)':>12s}  {'Heur%':>7s}  {'Shift':>8s}")
print("  " + "-" * 65)
for c in sorted(opt_c.keys(), key=lambda x: opt_c.get(x, 0), reverse=True):
    o, h = opt_c[c], heur_c[c]
    op = o / total_opt * 100 if total_opt > 0 else 0
    hp = h / total_heur * 100 if total_heur > 0 else 0
    print(f"  {c:>8s}  {o:>12.0f}  {op:>6.1f}%  {h:>12.0f}  {hp:>6.1f}%  {hp-op:>+7.1f}pp")
