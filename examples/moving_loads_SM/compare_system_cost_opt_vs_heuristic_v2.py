"""
Compare TOTAL system cost (electricity + infrastructure) between:
  1. System-optimal (from LP results)
  2. SOC-aware heuristic (with infrastructure sized to meet its charging pattern)

Only counting public charging infrastructure (slow_el=1, fast_el=2), NOT home charging (3) or diesel (0).

Infrastructure constraint: infra_kW >= s_MWh * 1000 / (gamma * 8760)
  gamma = 0.3, so factor = 1000 / (0.3 * 8760) = 0.3805 kW per MWh

Infrastructure annual costs per kW (electric):
  - O&M: ~16 EUR/kW/yr declining to ~9
  - Network: 14.688 EUR/kW/yr constant
  - Capital (cost_per_kW): 0 EUR
  Total: ~31 EUR/kW/yr
"""
import yaml, pathlib, re
import numpy as np
from collections import defaultdict

BASE = pathlib.Path(__file__).resolve().parent
INPUT_BASE = BASE / 'input_data/uncertainty_scenarios'

BATTERY_CAP = 400
SPEC_CONS = 1.1
Y_INIT = 2020
MODELED_YEARS = list(range(2020, 2064, 4))
TIMESTEP = 4
GAMMA = 0.3
HOURS_PER_YEAR = 8760
DISCOUNT_RATE = 0.04
ELEC_FL_IDS = {1, 2}  # Only public electric charging

y_idx_to_year = {i+1: y for i, y in enumerate(MODELED_YEARS)}

scenario_id = 'scenario_000'
inp = INPUT_BASE / scenario_id

print("Loading data...")
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

slow_fit = next(f for f in fit_data if f['id'] == 1)
om_costs = slow_fit['om_costs']
NETWORK_COST = 14.688

def annual_infra_cost_per_kW(year):
    idx = min(max(year - Y_INIT, 0), len(om_costs) - 1)
    return om_costs[idx] + NETWORK_COST

def discount_factor(year):
    return 1.0 / (1 + DISCOUNT_RATE) ** (year - Y_INIT)

elec_price_by_geo = {}
for e in fc_data:
    if e['fuel'] == 'electricity':
        elec_price_by_geo[(e['location'], e['fueling_infr_type_id'])] = e['cost_per_kWh']

path_by_id = {int(p['id']): [int(x) for x in p['sequence']] for p in paths}
path_dist_by_id = {}
for p in paths:
    pid = int(p['id'])
    path_dist_by_id[pid] = [float(d) for d in p.get('distance_from_previous', [])]

od_to_path = {int(od['id']): int(od['path_id']) for od in odpairs_raw}

breaks_by_path = defaultdict(list)
for brk in breaks_data:
    breaks_by_path[int(brk['path_id'])].append(int(brk['latest_geo_id']))

prkg_map = {}
with open(BASE / 'prkg_ordering_elsevier.txt') as f:
    for line in f:
        line = line.strip()
        if not line: continue
        parts = line.split('\t')
        idx = int(parts[0])
        t = parts[1].strip('()')
        vals = [int(x.strip()) for x in t.split(',')]
        prkg_map[idx] = tuple(vals)

# ── Parse s_dict ──────────────────────────────────────────────────────
print("Parsing s_dict...")
s_file = BASE / 'results/uncertainty_scenarios_v2/scenario_000/scenario_000_cs_2026-02-14_18-25-42_s_dict.yaml'
ci5_pat = re.compile(r'CartesianIndex\((\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\):\s*([\d.eE+-]+)')

opt_s = defaultdict(lambda: defaultdict(float))
opt_route_year = defaultdict(lambda: defaultdict(float))

with open(s_file) as f:
    for line in f:
        m = ci5_pat.match(line.strip())
        if not m: continue
        y_idx = int(m.group(1))
        prkg_idx = int(m.group(2))
        fl_idx = int(m.group(4))
        val = float(m.group(6))
        if val < 1e-6 or fl_idx not in ELEC_FL_IDS: continue
        prkg = prkg_map.get(prkg_idx)
        if prkg is None: continue
        _, od_id, path_id, geo_id = prkg
        year = y_idx_to_year.get(y_idx)
        if year is None: continue
        opt_s[geo_id][year] += val
        opt_route_year[(od_id, path_id)][year] += val

# ── Parse infrastructure (only electric, fl_idx in {1,2}) ────────────
print("Parsing infrastructure...")
ci3_pat = re.compile(r'CartesianIndex\((\d+),\s*(\d+),\s*(\d+)\):\s*([\d.eE+-]+)')
infra_file = BASE / 'results/uncertainty_scenarios_v2/scenario_000/scenario_000_cs_2026-02-14_18-25-42_q_fuel_infr_plus_dict.yaml'

opt_infra = defaultdict(lambda: defaultdict(float))
with open(infra_file) as f:
    for line in f:
        m = ci3_pat.match(line.strip())
        if not m: continue
        y_idx, fl_idx, geo_id = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if fl_idx not in {1}: continue  # Only slow electric public charging
        val = float(m.group(4))
        year = y_idx_to_year.get(y_idx)
        if year: opt_infra[geo_id][year] += val

# ── Heuristic charging ────────────────────────────────────────────────
print("Computing heuristic charging...")

def compute_soc_charging(od_id, path_id, total_energy_mwh):
    pid = od_to_path.get(od_id, path_id)
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
    energy_per_trip = SPEC_CONS * total_dist / 1000
    if energy_per_trip < 1e-9: return {}
    num_trips = total_energy_mwh / energy_per_trip
    soc = BATTERY_CAP * 0.5
    charges = {}
    for i, bi in enumerate(break_indices):
        prev_dist = cum_dist[break_indices[i-1]] if i > 0 else 0
        soc -= SPEC_CONS * (cum_dist[bi] - prev_dist)
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
    return {g: kwh * num_trips / 1000 for g, kwh in charges.items()}

heur_s = defaultdict(lambda: defaultdict(float))
for (od_id, path_id), year_dict in opt_route_year.items():
    for year, total_e in year_dict.items():
        if total_e < 1e-6: continue
        for geo_id, mwh in compute_soc_charging(od_id, path_id, total_e).items():
            heur_s[geo_id][year] += mwh

# ── Compute costs ─────────────────────────────────────────────────────
print("Computing costs...")

FACTOR = 1000.0 / (GAMMA * HOURS_PER_YEAR)

all_geos = set(list(opt_s.keys()) + list(heur_s.keys()))

results = []
opt_cum = defaultdict(float)
heur_cum = defaultdict(float)

for year in MODELED_YEARS:
    y_off = year - Y_INIT
    df = discount_factor(year)
    infra_cost_kw = annual_infra_cost_per_kW(year)

    # Electricity costs
    opt_e = heur_e = 0
    for geo_id in all_geos:
        for label, s_dict, e_acc in [('opt', opt_s, None), ('heur', heur_s, None)]:
            s_mwh = s_dict[geo_id].get(year, 0)
            if s_mwh > 0:
                price = 0
                if (geo_id, 1) in elec_price_by_geo:
                    prices = elec_price_by_geo[(geo_id, 1)]
                    if y_off < len(prices):
                        price = prices[y_off]
                cost = s_mwh * 1000 * price
                if label == 'opt':
                    opt_e += cost
                else:
                    heur_e += cost

    # Infrastructure costs (annual O&M+network on cumulative capacity)
    opt_i = heur_i = 0
    for geo_id in all_geos:
        # Optimizer: use actual deployed infra
        opt_cum[geo_id] += opt_infra[geo_id].get(year, 0)
        opt_i += opt_cum[geo_id] * infra_cost_kw

        # Heuristic: size infra to meet charging demand
        req = heur_s[geo_id].get(year, 0) * FACTOR
        if req > heur_cum[geo_id]:
            heur_cum[geo_id] = req
        heur_i += heur_cum[geo_id] * infra_cost_kw

    # Discount and scale by timestep
    results.append({
        'year': year,
        'opt_e': opt_e * df * TIMESTEP,
        'opt_i': opt_i * df * TIMESTEP,
        'heur_e': heur_e * df * TIMESTEP,
        'heur_i': heur_i * df * TIMESTEP,
    })

# ── Print ─────────────────────────────────────────────────────────────
print(f"\n{'='*140}")
print(f"SYSTEM COST COMPARISON: System-Optimal vs SOC-Aware Heuristic (electricity + public charging infrastructure)")
print(f"{'='*140}")
print(f"{'Year':>6s}  {'Opt Elec':>12s}  {'Opt Infra':>12s}  {'Opt Total':>12s}  {'Heur Elec':>12s}  {'Heur Infra':>12s}  {'Heur Total':>12s}  {'Delta':>12s}  {'%':>7s}")
print("-"*105)

tot = defaultdict(float)
for r in results:
    ot = r['opt_e'] + r['opt_i']
    ht = r['heur_e'] + r['heur_i']
    d = ht - ot
    dp = d/ot*100 if ot > 0 else 0
    print(f"{r['year']:>6d}  {r['opt_e']/1e6:>12.2f}  {r['opt_i']/1e6:>12.2f}  {ot/1e6:>12.2f}  {r['heur_e']/1e6:>12.2f}  {r['heur_i']/1e6:>12.2f}  {ht/1e6:>12.2f}  {d/1e6:>+12.2f}  {dp:>+6.1f}%")
    for k in ['opt_e', 'opt_i', 'heur_e', 'heur_i']:
        tot[k] += r[k]

print("-"*105)
tot_ot = tot['opt_e'] + tot['opt_i']
tot_ht = tot['heur_e'] + tot['heur_i']
tot_d = tot_ht - tot_ot
print(f"{'TOTAL':>6s}  {tot['opt_e']/1e6:>12.2f}  {tot['opt_i']/1e6:>12.2f}  {tot_ot/1e6:>12.2f}  {tot['heur_e']/1e6:>12.2f}  {tot['heur_i']/1e6:>12.2f}  {tot_ht/1e6:>12.2f}  {tot_d/1e6:>+12.2f}  {tot_d/tot_ot*100:>+6.1f}%")

print(f"\n{'='*100}")
print("SUMMARY (all values in MEUR, discounted)")
print(f"{'='*100}")
print(f"  System-optimal:")
print(f"    Electricity:     {tot['opt_e']/1e6:>10.2f} MEUR ({tot['opt_e']/tot_ot*100:.1f}%)")
print(f"    Infrastructure:  {tot['opt_i']/1e6:>10.2f} MEUR ({tot['opt_i']/tot_ot*100:.1f}%)")
print(f"    Total:           {tot_ot/1e6:>10.2f} MEUR")
print(f"\n  SOC-aware heuristic:")
print(f"    Electricity:     {tot['heur_e']/1e6:>10.2f} MEUR ({tot['heur_e']/tot_ht*100:.1f}%)")
print(f"    Infrastructure:  {tot['heur_i']/1e6:>10.2f} MEUR ({tot['heur_i']/tot_ht*100:.1f}%)")
print(f"    Total:           {tot_ht/1e6:>10.2f} MEUR")
print(f"\n  Delta (heuristic - optimal):")
print(f"    Electricity:     {(tot['heur_e']-tot['opt_e'])/1e6:>+10.2f} MEUR (heuristic saves on electricity)")
print(f"    Infrastructure:  {(tot['heur_i']-tot['opt_i'])/1e6:>+10.2f} MEUR (heuristic needs different infra)")
print(f"    Net:             {tot_d/1e6:>+10.2f} MEUR ({tot_d/tot_ot*100:>+.1f}%)")

# Country breakdown
print(f"\n{'='*100}")
print("INFRASTRUCTURE BY COUNTRY (cumulative kW, 2040)")
print(f"{'='*100}")
opt_c = defaultdict(float)
heur_c = defaultdict(float)
for geo_id in all_geos:
    c = geo_country.get(geo_id, '??')
    opt_c[c] += sum(opt_infra[geo_id][y] for y in MODELED_YEARS if y <= 2040)
    max_kw = 0
    for y in MODELED_YEARS:
        if y > 2040: break
        req = heur_s[geo_id].get(y, 0) * FACTOR
        if req > max_kw: max_kw = req
    heur_c[c] += max_kw

print(f"  {'Country':>8s}  {'Opt(kW)':>12s}  {'Heur(kW)':>12s}  {'Delta(kW)':>12s}  {'Delta%':>8s}")
print("  " + "-"*60)
for c in sorted(opt_c.keys()):
    o, h = opt_c[c], heur_c[c]
    d = h - o
    dp = d/o*100 if o > 0 else 0
    print(f"  {c:>8s}  {o:>12.0f}  {h:>12.0f}  {d:>+12.0f}  {dp:>+7.1f}%")
t_o, t_h = sum(opt_c.values()), sum(heur_c.values())
print(f"  {'TOTAL':>8s}  {t_o:>12.0f}  {t_h:>12.0f}  {t_h-t_o:>+12.0f}  {(t_h-t_o)/t_o*100:>+7.1f}%")

# Charging by country 2040
print(f"\n{'='*100}")
print("CHARGING ENERGY BY COUNTRY (MWh, 2040)")
print(f"{'='*100}")
opt_charge_c = defaultdict(float)
heur_charge_c = defaultdict(float)
for geo_id in all_geos:
    c = geo_country.get(geo_id, '??')
    opt_charge_c[c] += opt_s[geo_id].get(2040, 0)
    heur_charge_c[c] += heur_s[geo_id].get(2040, 0)

print(f"  {'Country':>8s}  {'Opt(MWh)':>12s}  {'Heur(MWh)':>12s}  {'Delta(MWh)':>12s}")
print("  " + "-"*50)
for c in sorted(opt_charge_c.keys()):
    o, h = opt_charge_c[c], heur_charge_c[c]
    print(f"  {c:>8s}  {o:>12.0f}  {h:>12.0f}  {h-o:>+12.0f}")
