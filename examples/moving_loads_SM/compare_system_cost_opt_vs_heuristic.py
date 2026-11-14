"""
Compare TOTAL system cost (electricity + infrastructure) between:
  1. System-optimal (from LP results)
  2. SOC-aware heuristic (with infrastructure sized to meet its charging pattern)

The infrastructure constraint says:
  cumulative_infra_kW >= gamma * sum(s[...]) * 1000 / (gamma_value * 8760)

where gamma=0.3 means capacity must cover 30% of annual energy throughput.
Actually, looking at the constraint more carefully:
  installed_kW + sum(q_fuel_infr_plus) >= factor_gamma * 1000 * sum(s[...])
  factor_gamma = 1 / (gamma * 8760)

So: required_kW = sum(s_MWh) * 1000 / (0.3 * 8760) = sum(s_MWh) * 1000 / 2628

Infrastructure annual costs per kW:
  - O&M: ~16.17 EUR/kW/yr (slow charging, 2020) declining to ~8.94
  - Network: 14.688 EUR/kW/yr (constant)
  Total: ~30.85 EUR/kW/yr in 2020, ~23.63 in 2060

Capital cost: 0 EUR/kW (cost_per_kW = 0 for electric charging)

We compare:
  System cost = electricity_cost + infrastructure_cost
  where infrastructure_cost = required_kW * annual_cost_per_kW * years
"""
import yaml, pathlib, re
import numpy as np
from collections import defaultdict

BASE = pathlib.Path(__file__).resolve().parent
INPUT_BASE = BASE / 'input_data/uncertainty_scenarios'

# ── Constants ────────────────────────────────────────────────────────
BATTERY_CAP = 400  # kWh
SPEC_CONS = 1.1    # kWh/km
Y_INIT = 2020
MODELED_YEARS = list(range(2020, 2064, 4))
TIMESTEP = 4
GAMMA = 0.3
HOURS_PER_YEAR = 8760
DISCOUNT_RATE = 0.04

y_idx_to_year = {i+1: y for i, y in enumerate(MODELED_YEARS)}

# ── Load input data ──────────────────────────────────────────────────
scenario_id = 'scenario_000'
inp = INPUT_BASE / scenario_id

print("Loading input data...")
with open(inp / 'Path.yaml') as f:
    paths = yaml.load(f, Loader=yaml.UnsafeLoader)
with open(inp / 'Odpair.yaml') as f:
    odpairs_raw = yaml.load(f, Loader=yaml.UnsafeLoader)
with open(inp / 'MandatoryBreaks.yaml') as f:
    breaks_data = yaml.safe_load(f)
with open(BASE / 'input_data/fixed_nuts_2/GeographicElement.yaml') as f:
    geo_data = yaml.safe_load(f)
with open(inp / 'FuelCost.yaml') as f:
    fc_data = yaml.safe_load(f)
with open(inp / 'FuelingInfrTypes.yaml') as f:
    fit_data = yaml.safe_load(f)

geo_country = {g['id']: g.get('country', '??') for g in geo_data}

# Infrastructure cost parameters
# Slow charging (id=1)
slow_fit = next(f for f in fit_data if f['id'] == 1)
om_costs = slow_fit['om_costs']  # EUR/kW/year, indexed by year offset
network_cost_per_kW = 14.688  # EUR/kW/year, constant

def annual_infra_cost_per_kW(year):
    """Annual infrastructure cost per kW for a given year."""
    idx = year - Y_INIT
    if idx < 0: idx = 0
    if idx >= len(om_costs): idx = len(om_costs) - 1
    return om_costs[idx] + network_cost_per_kW

def discount_factor(year):
    return 1.0 / (1 + DISCOUNT_RATE) ** (year - Y_INIT)

# Electricity prices: {(geo_id, fl_id): [price_per_kWh for each year offset]}
elec_price_by_geo_year = {}
for e in fc_data:
    if e['fuel'] == 'electricity':
        geo_id = e['location']
        fl_id = e['fueling_infr_type_id']
        elec_price_by_geo_year[(geo_id, fl_id)] = e['cost_per_kWh']  # array indexed by year offset

# Path data
path_by_id = {int(p['id']): [int(x) for x in p['sequence']] for p in paths}
path_dist_by_id = {}
path_length = {}
for p in paths:
    pid = int(p['id'])
    dist = [float(d) for d in p.get('distance_from_previous', [])]
    path_dist_by_id[pid] = dist
    path_length[pid] = sum(dist)

od_to_path = {}
for od in odpairs_raw:
    od_to_path[int(od['id'])] = int(od['path_id'])

breaks_by_path = defaultdict(list)
for brk in breaks_data:
    breaks_by_path[int(brk['path_id'])].append(int(brk['latest_geo_id']))

# prkg ordering
ordering_file = BASE / 'prkg_ordering_elsevier.txt'
prkg_map = {}
with open(ordering_file) as f:
    for line in f:
        line = line.strip()
        if not line: continue
        parts = line.split('\t')
        idx = int(parts[0])
        t = parts[1].strip('()')
        vals = [int(x.strip()) for x in t.split(',')]
        prkg_map[idx] = tuple(vals)

# ── Parse s_dict (system-optimal charging) ────────────────────────────
print("Parsing s_dict (system-optimal charging by node/year)...")
s_file = BASE / 'results/uncertainty_scenarios_v2/scenario_000/scenario_000_cs_2026-02-14_18-25-42_s_dict.yaml'

ci5_pat = re.compile(
    r'CartesianIndex\((\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\):\s*([\d.eE+-]+)')

# opt_s[geo_id][year] = total MWh charged (electricity only)
opt_s = defaultdict(lambda: defaultdict(float))

with open(s_file) as f:
    for line in f:
        m = ci5_pat.match(line.strip())
        if not m: continue
        y_idx = int(m.group(1))
        prkg_idx = int(m.group(2))
        fl_idx = int(m.group(4))
        val = float(m.group(6))
        if val < 1e-6 or fl_idx not in {1, 2}: continue
        prkg = prkg_map.get(prkg_idx)
        if prkg is None: continue
        _, od_id, path_id, geo_id = prkg
        year = y_idx_to_year.get(y_idx)
        if year is None: continue
        opt_s[geo_id][year] += val

# ── Parse q_fuel_infr_plus (system-optimal infrastructure) ────────────
print("Parsing q_fuel_infr_plus (system-optimal infrastructure)...")
ci3_pat = re.compile(r'CartesianIndex\((\d+),\s*(\d+),\s*(\d+)\):\s*([\d.eE+-]+)')
infra_file = BASE / 'results/uncertainty_scenarios_v2/scenario_000/scenario_000_cs_2026-02-14_18-25-42_q_fuel_infr_plus_dict.yaml'

# opt_infra[geo_id][year] = kW added that year
opt_infra = defaultdict(lambda: defaultdict(float))
with open(infra_file) as f:
    for line in f:
        m = ci3_pat.match(line.strip())
        if not m: continue
        y_idx, fl_idx, geo_id = int(m.group(1)), int(m.group(2)), int(m.group(3))
        val = float(m.group(4))
        year = y_idx_to_year.get(y_idx)
        if year: opt_infra[geo_id][year] += val

# ── Compute SOC-aware heuristic charging per node per year ────────────
print("Computing SOC-aware heuristic charging pattern...")

# First get total energy per (od, path, year) from opt_s grouped by route
opt_route_year = defaultdict(lambda: defaultdict(float))
with open(s_file) as f:
    for line in f:
        m = ci5_pat.match(line.strip())
        if not m: continue
        y_idx = int(m.group(1))
        prkg_idx = int(m.group(2))
        fl_idx = int(m.group(4))
        val = float(m.group(6))
        if val < 1e-6 or fl_idx not in {1, 2}: continue
        prkg = prkg_map.get(prkg_idx)
        if prkg is None: continue
        _, od_id, path_id, geo_id = prkg
        year = y_idx_to_year.get(y_idx)
        if year: opt_route_year[(od_id, path_id)][year] += val

def compute_soc_charging(od_id, path_id, total_energy_mwh):
    """SOC-aware lazy charging: returns {geo_id: MWh}."""
    pid = od_to_path.get(od_id)
    if pid is None: pid = path_id
    seq = path_by_id.get(pid, [])
    dist = path_dist_by_id.get(pid, [])
    break_set = set(breaks_by_path.get(pid, []))
    if not seq or not dist or len(seq) != len(dist): return {}

    break_indices = [i for i, g in enumerate(seq) if g in break_set]
    if not break_indices: return {}

    cum_dist = []
    d = 0
    for dd in dist:
        d += dd
        cum_dist.append(d)

    total_dist = cum_dist[-1] if cum_dist else 0
    if total_dist < 1e-3: return {}

    energy_per_trip = SPEC_CONS * total_dist / 1000  # MWh
    if energy_per_trip < 1e-9: return {}
    num_trips = total_energy_mwh / energy_per_trip

    # Simulate one trip
    soc = BATTERY_CAP * 0.5  # 50% initial
    charges = {}

    for i, bi in enumerate(break_indices):
        prev_dist = cum_dist[break_indices[i-1]] if i > 0 else 0
        energy_consumed = SPEC_CONS * (cum_dist[bi] - prev_dist)
        soc -= energy_consumed

        if i < len(break_indices) - 1:
            dist_to_next = cum_dist[break_indices[i+1]] - cum_dist[bi]
        else:
            dist_to_next = total_dist - cum_dist[bi]

        energy_to_next = SPEC_CONS * dist_to_next
        if soc < energy_to_next:
            charge = min(BATTERY_CAP - soc, energy_to_next - soc + BATTERY_CAP * 0.1)
            charge = min(charge, BATTERY_CAP - soc)
            if charge > 0:
                charges[seq[bi]] = charges.get(seq[bi], 0) + charge
                soc += charge

    result = {}
    for geo_id, kwh in charges.items():
        result[geo_id] = kwh * num_trips / 1000  # MWh
    return result

# heur_s[geo_id][year] = MWh
heur_s = defaultdict(lambda: defaultdict(float))
for (od_id, path_id), year_dict in opt_route_year.items():
    for year, total_e in year_dict.items():
        if total_e < 1e-6: continue
        geo_charges = compute_soc_charging(od_id, path_id, total_e)
        for geo_id, mwh in geo_charges.items():
            heur_s[geo_id][year] += mwh

# ── Compute required infrastructure for heuristic ─────────────────────
print("Computing infrastructure requirements...")

# Required kW at node = peak_MWh * 1000 / (gamma * 8760)
# The constraint: infra_kW >= s_MWh * 1000 / (gamma * 8760)
# This is per year — need cumulative max

factor = 1000.0 / (GAMMA * HOURS_PER_YEAR)  # MWh -> required kW

def required_infra_kw(s_by_year, year):
    """Required cumulative infrastructure at a node for a given year."""
    return s_by_year.get(year, 0) * factor

# ── Compute total costs for both strategies ───────────────────────────
print("\nComputing total system costs...")
print("="*100)

all_geos = set(list(opt_s.keys()) + list(heur_s.keys()))

# For each year, compute:
# 1. Electricity cost = sum over nodes of s_MWh * price_EUR/kWh * 1000
# 2. Infrastructure cost = cumulative_required_kW * annual_cost/kW * timestep

opt_elec_cost = {}
opt_infra_cost = {}
heur_elec_cost = {}
heur_infra_cost = {}

opt_cum_infra = defaultdict(float)  # geo -> cumulative kW
heur_cum_infra = defaultdict(float)

for year in MODELED_YEARS:
    y_offset = year - Y_INIT
    df = discount_factor(year)
    infra_annual = annual_infra_cost_per_kW(year)

    # --- System-optimal ---
    e_cost_opt = 0
    for geo_id in all_geos:
        s_mwh = opt_s[geo_id].get(year, 0)
        if s_mwh > 0:
            # Use fl_id=1 (slow) price as default
            price = 0
            if (geo_id, 1) in elec_price_by_geo_year:
                prices = elec_price_by_geo_year[(geo_id, 1)]
                if y_offset < len(prices):
                    price = prices[y_offset]
            e_cost_opt += s_mwh * 1000 * price  # MWh * 1000 = kWh, * EUR/kWh = EUR
    opt_elec_cost[year] = e_cost_opt * df * TIMESTEP

    # Optimal infrastructure: use actual q_fuel_infr_plus
    i_cost_opt = 0
    for geo_id in all_geos:
        opt_cum_infra[geo_id] += opt_infra[geo_id].get(year, 0)
        i_cost_opt += opt_cum_infra[geo_id] * infra_annual
    opt_infra_cost[year] = i_cost_opt * df * TIMESTEP

    # --- Heuristic ---
    e_cost_heur = 0
    for geo_id in all_geos:
        s_mwh = heur_s[geo_id].get(year, 0)
        if s_mwh > 0:
            price = 0
            if (geo_id, 1) in elec_price_by_geo_year:
                prices = elec_price_by_geo_year[(geo_id, 1)]
                if y_offset < len(prices):
                    price = prices[y_offset]
            e_cost_heur += s_mwh * 1000 * price
    heur_elec_cost[year] = e_cost_heur * df * TIMESTEP

    # Heuristic infrastructure: must be sized to meet heuristic's charging pattern
    # Required: max of required kW across all years up to this year
    i_cost_heur = 0
    for geo_id in all_geos:
        required_kw = required_infra_kw(heur_s[geo_id], year)
        if required_kw > heur_cum_infra[geo_id]:
            heur_cum_infra[geo_id] = required_kw
        i_cost_heur += heur_cum_infra[geo_id] * infra_annual
    heur_infra_cost[year] = i_cost_heur * df * TIMESTEP

# ── Print comparison ──────────────────────────────────────────────────
print(f"\n{'Year':>6s}  {'Opt Elec(MEUR)':>15s}  {'Opt Infra(MEUR)':>16s}  {'Opt Total':>12s}  {'Heur Elec(MEUR)':>16s}  {'Heur Infra(MEUR)':>17s}  {'Heur Total':>12s}  {'Delta(MEUR)':>12s}  {'Delta%':>8s}")
print("-"*130)

total_opt_e = total_opt_i = total_heur_e = total_heur_i = 0
for year in MODELED_YEARS:
    oe = opt_elec_cost[year] / 1e6
    oi = opt_infra_cost[year] / 1e6
    he = heur_elec_cost[year] / 1e6
    hi = heur_infra_cost[year] / 1e6
    ot = oe + oi
    ht = he + hi
    delta = ht - ot
    dpct = delta / ot * 100 if ot > 0 else 0

    total_opt_e += oe
    total_opt_i += oi
    total_heur_e += he
    total_heur_i += hi

    print(f"{year:>6d}  {oe:>15.2f}  {oi:>16.2f}  {ot:>12.2f}  {he:>16.2f}  {hi:>17.2f}  {ht:>12.2f}  {delta:>+12.2f}  {dpct:>+7.1f}%")

print("-"*130)
total_ot = total_opt_e + total_opt_i
total_ht = total_heur_e + total_heur_i
total_delta = total_ht - total_ot
total_dpct = total_delta / total_ot * 100 if total_ot > 0 else 0
print(f"{'TOTAL':>6s}  {total_opt_e:>15.2f}  {total_opt_i:>16.2f}  {total_ot:>12.2f}  {total_heur_e:>16.2f}  {total_heur_i:>17.2f}  {total_ht:>12.2f}  {total_delta:>+12.2f}  {total_dpct:>+7.1f}%")

# ── Infrastructure comparison by country ──────────────────────────────
print(f"\n{'='*100}")
print("INFRASTRUCTURE REQUIREMENTS BY COUNTRY (cumulative kW at 2040)")
print(f"{'='*100}")

opt_country = defaultdict(float)
heur_country = defaultdict(float)
for geo_id in all_geos:
    c = geo_country.get(geo_id, '??')
    # Opt: actual cumulative
    cum_opt = sum(opt_infra[geo_id][y] for y in MODELED_YEARS if y <= 2040)
    opt_country[c] += cum_opt
    # Heur: required
    heur_country[c] += heur_cum_infra.get(geo_id, 0)  # this is already the max up to final year

# Recompute heuristic at 2040 specifically
heur_country_2040 = defaultdict(float)
for geo_id in all_geos:
    c = geo_country.get(geo_id, '??')
    max_kw = 0
    for y in MODELED_YEARS:
        if y > 2040: break
        req = required_infra_kw(heur_s[geo_id], y)
        if req > max_kw: max_kw = req
    heur_country_2040[c] += max_kw

countries = sorted(set(list(opt_country.keys()) + list(heur_country_2040.keys())))
print(f"  {'Country':>8s}  {'Opt Infra(kW)':>14s}  {'Heur Infra(kW)':>15s}  {'Delta(kW)':>12s}  {'Delta%':>8s}")
print("  " + "-"*65)
for c in countries:
    o = opt_country[c]
    h = heur_country_2040[c]
    d = h - o
    dp = d / o * 100 if o > 0 else float('inf')
    print(f"  {c:>8s}  {o:>14.0f}  {h:>15.0f}  {d:>+12.0f}  {dp:>+7.1f}%")

total_o = sum(opt_country.values())
total_h = sum(heur_country_2040.values())
print(f"  {'TOTAL':>8s}  {total_o:>14.0f}  {total_h:>15.0f}  {total_h-total_o:>+12.0f}  {(total_h-total_o)/total_o*100:>+7.1f}%")

# ── Summary ───────────────────────────────────────────────────────────
print(f"\n{'='*100}")
print("SUMMARY")
print(f"{'='*100}")
print(f"  System-optimal total cost (discounted): {total_ot:.2f} MEUR")
print(f"    - Electricity: {total_opt_e:.2f} MEUR ({total_opt_e/total_ot*100:.1f}%)")
print(f"    - Infrastructure: {total_opt_i:.2f} MEUR ({total_opt_i/total_ot*100:.1f}%)")
print()
print(f"  Heuristic total cost (discounted): {total_ht:.2f} MEUR")
print(f"    - Electricity: {total_heur_e:.2f} MEUR ({total_heur_e/total_ht*100:.1f}%)")
print(f"    - Infrastructure: {total_heur_i:.2f} MEUR ({total_heur_i/total_ht*100:.1f}%)")
print()
print(f"  Heuristic premium: {total_delta:+.2f} MEUR ({total_dpct:+.1f}%)")
print(f"  Electricity saving of heuristic: {total_opt_e - total_heur_e:+.2f} MEUR")
print(f"  Infrastructure penalty of heuristic: {total_heur_i - total_opt_i:+.2f} MEUR")
print()
print(f"  Key insight: The heuristic may save on electricity by concentrating")
print(f"  charging at cheap nodes, but requires MORE infrastructure at those nodes,")
print(f"  which can outweigh the electricity savings.")
