"""
Analyze per-route cost differential between system-optimal and SOC-aware heuristic.
Shows that while the aggregate gap is small (~0.2 ct/kWh), individual routes can differ much more.
"""
import yaml, pathlib, re
import numpy as np
from collections import defaultdict

BASE = pathlib.Path(__file__).resolve().parent
INPUT_BASE = BASE / 'input_data/uncertainty_scenarios'

# ── Constants ────────────────────────────────────────────────────────
BATTERY_CAP = 400  # kWh
SPEC_CONS_2032 = 1.1  # kWh/km for 2032
Y_INIT = 2020
MODELED_YEARS = list(range(2020, 2064, 4))
TARGET_YEAR = 2032
TARGET_Y_IDX = (TARGET_YEAR - Y_INIT) // 4 + 1  # period 4

# ── Load structural data ─────────────────────────────────────────────
print("Loading structural data...")
scenario_id = 'scenario_000'
inp = INPUT_BASE / scenario_id

with open(inp / 'Path.yaml') as f:
    paths = yaml.load(f, Loader=yaml.UnsafeLoader)
with open(inp / 'Odpair.yaml') as f:
    odpairs_raw = yaml.load(f, Loader=yaml.UnsafeLoader)
with open(inp / 'MandatoryBreaks.yaml') as f:
    breaks_data = yaml.safe_load(f)
with open(BASE / 'input_data/fixed_nuts_2/GeographicElement.yaml') as f:
    geo_data = yaml.safe_load(f)

geo_country = {g['id']: g.get('country', '??') for g in geo_data}
geo_lat = {g['id']: g.get('coordinate_lat', 0) for g in geo_data}

path_by_id = {int(p['id']): [int(x) for x in p['sequence']] for p in paths}
path_dist_by_id = {}
path_length = {}
for p in paths:
    pid = int(p['id'])
    dist = [float(d) for d in p.get('distance_from_previous', [])]
    path_dist_by_id[pid] = dist
    path_length[pid] = sum(dist)

od_to_path = {}
od_from_to = {}
for od in odpairs_raw:
    oid = int(od['id'])
    od_to_path[oid] = int(od['path_id'])
    od_from_to[oid] = (int(od['from']), int(od['to']))

breaks_by_path = defaultdict(list)
for brk in breaks_data:
    breaks_by_path[int(brk['path_id'])].append(int(brk['latest_geo_id']))

# ── Load prkg ordering ───────────────────────────────────────────────
ordering_file = BASE / 'prkg_ordering_elsevier.txt'
prkg_map = {}
if ordering_file.exists():
    with open(ordering_file) as f:
        for line in f:
            line = line.strip()
            if not line: continue
            parts = line.split('\t')
            idx = int(parts[0])
            t = parts[1].strip('()')
            vals = [int(x.strip()) for x in t.split(',')]
            prkg_map[idx] = tuple(vals)

# ── Load electricity prices ──────────────────────────────────────────
fc_idx = TARGET_YEAR - Y_INIT  # index into cost arrays
with open(inp / 'FuelCost.yaml') as f:
    fc = yaml.safe_load(f)
elec_prices = {}
for e in fc:
    if e['fuel'] == 'electricity':
        geo_id = e['location']
        fl_id = e['fueling_infr_type_id']
        elec_prices[(geo_id, fl_id)] = e['cost_per_kWh'][fc_idx]

# ── Parse s_dict ─────────────────────────────────────────────────────
print("Parsing s_dict (system-optimal)...")
s_path = BASE / 'results/uncertainty_scenarios_v2/scenario_000/scenario_000_cs_2026-02-14_18-25-42_s_dict.yaml'

ci_pat = re.compile(
    r'CartesianIndex\((\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\):\s*([\d.eE+-]+)')

# Per OD-path: {(od,path): {(geo,fl): MWh}}
opt_by_route = defaultdict(lambda: defaultdict(float))
opt_route_total = defaultdict(float)

with open(s_path) as f:
    for line in f:
        m = ci_pat.match(line.strip())
        if not m: continue
        y_idx = int(m.group(1))
        if y_idx != TARGET_Y_IDX: continue
        prkg_idx = int(m.group(2))
        fl_idx = int(m.group(4))
        val = float(m.group(6))
        if val < 1e-6 or fl_idx not in {1, 2}: continue
        prkg = prkg_map.get(prkg_idx)
        if prkg is None: continue
        _, od_id, path_id, geo_id = prkg
        opt_by_route[(od_id, path_id)][(geo_id, fl_idx)] += val
        opt_route_total[(od_id, path_id)] += val

print(f"  {len(opt_route_total)} routes with BEV energy in {TARGET_YEAR}")

# ── Compute SOC-aware distribution per route ─────────────────────────
print("Computing SOC-aware heuristic per route...")

def compute_soc_for_route(od_id, path_id, total_energy, battery_cap=BATTERY_CAP,
                          spec_cons=SPEC_CONS_2032, initial_soc_frac=0.5):
    """Returns {(geo_id, fl_idx=1): MWh} for SOC-aware lazy charging."""
    seq = path_by_id.get(path_id, [])
    dist = path_dist_by_id.get(path_id, [])
    break_set = set(breaks_by_path.get(path_id, []))
    if not seq or not dist or len(seq) != len(dist):
        return {}

    break_indices = [i for i, g in enumerate(seq) if g in break_set]
    if not break_indices:
        return {}

    cum_dist = []
    d = 0
    for dd in dist:
        d += dd
        cum_dist.append(d)

    total_dist = cum_dist[-1] if cum_dist else 0
    if total_dist < 1e-3:
        return {}

    # Number of trips = total_energy / (spec_cons * total_dist) [in MWh vs kWh]
    energy_per_trip = spec_cons * total_dist / 1000  # MWh
    if energy_per_trip < 1e-9:
        return {}
    num_trips = total_energy / energy_per_trip

    # Simulate one trip with lazy charging
    soc = battery_cap * initial_soc_frac  # kWh
    charges = {}  # geo_id -> kWh charged per trip

    for i, bi in enumerate(break_indices):
        energy_consumed = spec_cons * (cum_dist[bi] - (cum_dist[break_indices[i-1]] if i > 0 else 0))
        soc -= energy_consumed

        # Look ahead: distance to next break or end
        if i < len(break_indices) - 1:
            dist_to_next = cum_dist[break_indices[i+1]] - cum_dist[bi]
        else:
            dist_to_next = total_dist - cum_dist[bi]

        energy_to_next = spec_cons * dist_to_next

        if soc < energy_to_next:
            charge = min(battery_cap - soc, energy_to_next - soc + battery_cap * 0.1)
            charge = min(charge, battery_cap - soc)
            if charge > 0:
                charges[seq[bi]] = charge
                soc += charge

    # Scale by num_trips and convert to MWh
    result = {}
    for geo_id, kwh in charges.items():
        result[(geo_id, 1)] = kwh * num_trips / 1000  # MWh, fl=1 (slow)
    return result


soc_by_route = {}
for (od_id, path_id), total_e in opt_route_total.items():
    soc_by_route[(od_id, path_id)] = compute_soc_for_route(od_id, path_id, total_e)

# ── Compute per-route electricity cost ───────────────────────────────
print("Computing per-route electricity costs...")

def route_elec_cost(geo_fl_dict):
    """From {(geo, fl): MWh} -> (total_cost_EUR, total_kWh, avg_EUR_per_kWh)"""
    cost = kwh = 0.0
    for (g, fl), mwh in geo_fl_dict.items():
        if mwh > 0:
            price = elec_prices.get((g, fl), 0)
            cost += mwh * 1000 * price
            kwh += mwh * 1000
    return cost, kwh, (cost / kwh if kwh > 0 else 0)


results = []
for (od_id, path_id), opt_dist in opt_by_route.items():
    soc_dist = soc_by_route.get((od_id, path_id), {})
    if not opt_dist or not soc_dist:
        continue

    opt_cost, opt_kwh, opt_avg = route_elec_cost(opt_dist)
    soc_cost, soc_kwh, soc_avg = route_elec_cost(soc_dist)

    if opt_kwh < 1 or soc_kwh < 1:
        continue

    origin, dest = od_from_to.get(od_id, (0, 0))
    oc = geo_country.get(origin, '??')
    dc = geo_country.get(dest, '??')
    dist_km = path_length.get(path_id, 0)

    delta_ct = (soc_avg - opt_avg) * 100  # ct/kWh
    delta_pct = (soc_avg - opt_avg) / opt_avg * 100 if opt_avg > 0 else 0

    results.append({
        'od_id': od_id,
        'origin': oc,
        'dest': dc,
        'dist_km': dist_km,
        'opt_ct_kwh': opt_avg * 100,
        'soc_ct_kwh': soc_avg * 100,
        'delta_ct': delta_ct,
        'delta_pct': delta_pct,
        'energy_kwh': opt_kwh,
    })

# ── Sort and display ─────────────────────────────────────────────────
results.sort(key=lambda x: abs(x['delta_ct']), reverse=True)

print(f"\n{'='*120}")
print(f"PER-ROUTE ELECTRICITY COST DIFFERENTIAL: System-optimal vs SOC-aware heuristic ({TARGET_YEAR})")
print(f"{'='*120}")
print(f"  {'OD':>5s}  {'Route':>12s}  {'Dist(km)':>9s}  {'Opt(ct/kWh)':>12s}  {'SOC(ct/kWh)':>12s}  {'Delta(ct)':>10s}  {'Delta(%)':>9s}  {'Energy(kWh)':>12s}")
print("  " + "-"*100)

for r in results[:30]:
    print(f"  {r['od_id']:>5d}  {r['origin']:>5s}->{r['dest']:<5s}  {r['dist_km']:>8.0f}  {r['opt_ct_kwh']:>11.2f}  {r['soc_ct_kwh']:>11.2f}  {r['delta_ct']:>+9.2f}  {r['delta_pct']:>+8.1f}%  {r['energy_kwh']:>11.0f}")

print(f"\n  ... {len(results)} routes total")

# Summary statistics
deltas = [r['delta_ct'] for r in results]
abs_deltas = [abs(d) for d in deltas]
print(f"\n{'='*80}")
print(f"SUMMARY STATISTICS")
print(f"{'='*80}")
print(f"  Routes analyzed: {len(results)}")
print(f"  Mean |delta|:    {np.mean(abs_deltas):.3f} ct/kWh")
print(f"  Median |delta|:  {np.median(abs_deltas):.3f} ct/kWh")
print(f"  Std delta:       {np.std(deltas):.3f} ct/kWh")
print(f"  Min delta:       {min(deltas):+.3f} ct/kWh")
print(f"  Max delta:       {max(deltas):+.3f} ct/kWh")
print(f"  P10:             {np.percentile(deltas, 10):+.3f} ct/kWh")
print(f"  P90:             {np.percentile(deltas, 90):+.3f} ct/kWh")

# By country pair
print(f"\n{'='*80}")
print(f"MEAN DELTA BY COUNTRY PAIR")
print(f"{'='*80}")
from collections import defaultdict as dd
pair_deltas = dd(list)
for r in results:
    pair = f"{r['origin']}->{r['dest']}"
    pair_deltas[pair].append(r['delta_ct'])

pair_summary = []
for pair, ds in pair_deltas.items():
    pair_summary.append((pair, np.mean(ds), np.std(ds), len(ds), max(abs(d) for d in ds)))

pair_summary.sort(key=lambda x: abs(x[1]), reverse=True)
print(f"  {'Pair':>12s}  {'Mean(ct)':>9s}  {'Std':>7s}  {'N':>4s}  {'Max|delta|':>11s}")
print("  " + "-"^60 if False else "  " + "-"*55)
for pair, mean_d, std_d, n, max_d in pair_summary[:20]:
    print(f"  {pair:>12s}  {mean_d:>+8.3f}  {std_d:>6.3f}  {n:>4d}  {max_d:>10.3f}")

# Routes where heuristic is CHEAPER than optimal (optimizer misses something?)
cheaper = [r for r in results if r['delta_ct'] < -0.01]
print(f"\n  Routes where SOC-aware is CHEAPER: {len(cheaper)} / {len(results)}")
if cheaper:
    print(f"  (These routes benefit from the heuristic's conservative charging pattern)")

# ── Energy-weighted distribution ─────────────────────────────────────
print(f"\n{'='*80}")
print(f"ENERGY-WEIGHTED ANALYSIS")
print(f"{'='*80}")

total_energy = sum(r['energy_kwh'] for r in results)
weighted_delta = sum(r['delta_ct'] * r['energy_kwh'] for r in results) / total_energy
weighted_abs_delta = sum(abs(r['delta_ct']) * r['energy_kwh'] for r in results) / total_energy

print(f"  Total energy across routes: {total_energy/1e6:.2f} GWh")
print(f"  Energy-weighted mean delta:  {weighted_delta:+.3f} ct/kWh  (this is what Table 6 shows)")
print(f"  Energy-weighted mean |delta|: {weighted_abs_delta:.3f} ct/kWh")

# What fraction of energy sees |delta| > X?
thresholds = [0.5, 1.0, 2.0, 5.0, 10.0]
print(f"\n  Fraction of energy with |delta| exceeding threshold:")
for t in thresholds:
    energy_above = sum(r['energy_kwh'] for r in results if abs(r['delta_ct']) > t)
    pct = energy_above / total_energy * 100
    print(f"    |delta| > {t:>4.1f} ct/kWh:  {pct:>5.1f}% of energy  ({energy_above/1e6:.2f} GWh)")

# Energy-weighted percentiles
# Sort by delta, compute cumulative energy fraction
results_sorted = sorted(results, key=lambda x: x['delta_ct'])
cum_energy = 0
percentiles_target = [0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95]
pct_idx = 0
print(f"\n  Energy-weighted percentiles of delta:")
for r in results_sorted:
    cum_energy += r['energy_kwh']
    frac = cum_energy / total_energy
    while pct_idx < len(percentiles_target) and frac >= percentiles_target[pct_idx]:
        print(f"    P{int(percentiles_target[pct_idx]*100):>2d}: {r['delta_ct']:+.3f} ct/kWh")
        pct_idx += 1

# Cross-border vs domestic
print(f"\n  Cross-border vs domestic routes:")
cross = [r for r in results if r['origin'] != r['dest']]
domestic = [r for r in results if r['origin'] == r['dest']]
if cross:
    e_cross = sum(r['energy_kwh'] for r in cross)
    w_cross = sum(abs(r['delta_ct']) * r['energy_kwh'] for r in cross) / e_cross
    print(f"    Cross-border: {len(cross)} routes, {e_cross/1e6:.2f} GWh, energy-weighted |delta| = {w_cross:.3f} ct/kWh")
if domestic:
    e_dom = sum(r['energy_kwh'] for r in domestic)
    w_dom = sum(abs(r['delta_ct']) * r['energy_kwh'] for r in domestic) / e_dom
    print(f"    Domestic:     {len(domestic)} routes, {e_dom/1e6:.2f} GWh, energy-weighted |delta| = {w_dom:.3f} ct/kWh")
