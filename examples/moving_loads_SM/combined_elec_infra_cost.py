"""
Combined electricity + infrastructure cost per kWh over time.
Breaks-only vs Unconstrained for scenario_000 (Go RES).
s is in MWh → multiply by 1000 for kWh.
"""
import yaml, pathlib, re
from collections import defaultdict

BASE = pathlib.Path('C:/Users/simuser/Documents/AntoniaGolab/Scand_Med_analysis/'
                    'SM_baby_2/iDesignRES_transcompmodel/examples/moving_loads_SM')
INPUT_BASE = BASE / 'input_data/uncertainty_scenarios'

Y_INIT = 2020; TIME_STEP = 4; Y_END = 2060
MODELED_YEARS = list(range(Y_INIT, Y_END + 1, TIME_STEP))
DISCOUNT_RATE = 0.04
EMISSION_FACTOR = 266.0 / 1e6

# ── Load params ──────────────────────────────────────────────────────
with open(INPUT_BASE / 'scenario_000/FuelingInfrTypes.yaml') as f:
    fit_data = yaml.safe_load(f)
fit_om = {fit['id']: fit['om_costs'] for fit in fit_data}

with open(INPUT_BASE / 'scenario_000/NetworkConnectionCosts.yaml') as f:
    ncc_data = yaml.safe_load(f)
ncc_by_loc = {e['location']: e['network_cost_per_kW'] for e in ncc_data}

with open(INPUT_BASE / 'scenario_000/InitialFuelInfr.yaml') as f:
    init_infr = yaml.safe_load(f)
init_kw = {}
for e in init_infr:
    init_kw[(e['allocation'], e['fuel'])] = e['installed_kW']

with open(BASE / 'input_data/fixed_nuts_2/GeographicElement.yaml') as f:
    geo_data = yaml.safe_load(f)
geo_country = {g['id']: g['country'] for g in geo_data}

FL_TO_FIT = {1: 1, 2: 2}


def load_structural(scenario_id):
    inp = INPUT_BASE / scenario_id
    with open(inp / 'Path.yaml') as f:
        paths = yaml.load(f, Loader=yaml.UnsafeLoader)
    with open(inp / 'Odpair.yaml') as f:
        odpairs = yaml.load(f, Loader=yaml.UnsafeLoader)
    path_by_id = {int(p['id']): [int(x) for x in p['sequence']] for p in paths}
    s = set()
    for od in odpairs:
        for geo_id in path_by_id[int(od['path_id'])]:
            s.add((0, int(od['id']), int(od['path_id']), geo_id))
    return {i+1: t for i, t in enumerate(sorted(s))}


def parse_s_by_year(filepath, prkg_map):
    """Returns {y_idx: {'bev_fl': {(geo,fl): MWh}, 'bev_total': MWh}}"""
    ci_pat = re.compile(
        r'CartesianIndex\((\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\):\s*([\d.eE+-]+)')
    result = defaultdict(lambda: {'bev_fl': defaultdict(float), 'bev_total': 0.0})
    with open(filepath) as f:
        for line in f:
            m = ci_pat.match(line.strip())
            if not m: continue
            y_idx, prkg_idx, fl_idx = int(m.group(1)), int(m.group(2)), int(m.group(4))
            val = float(m.group(6))
            if val < 1e-6 or prkg_map.get(prkg_idx) is None: continue
            _, _, _, geo_id = prkg_map[prkg_idx]
            if fl_idx in {1, 2}:
                result[y_idx]['bev_fl'][(geo_id, fl_idx)] += val
                result[y_idx]['bev_total'] += val
    return dict(result)


def parse_q_infr(filepath):
    ci_pat = re.compile(r'CartesianIndex\((\d+),\s*(\d+),\s*(\d+)\):\s*([\d.eE+-]+)')
    result = {}
    with open(filepath) as f:
        for line in f:
            m = ci_pat.match(line.strip())
            if not m: continue
            y_idx, fl_idx, geo_id = int(m.group(1)), int(m.group(2)), int(m.group(3))
            val = float(m.group(4))
            if val > 1e-6:
                result[(y_idx, fl_idx, geo_id)] = val
    return result


def load_fuel_prices(scenario_id, fc_idx):
    inp = INPUT_BASE / scenario_id
    with open(inp / 'FuelCost.yaml') as f:
        fc = yaml.safe_load(f)
    elec_price = {}
    for entry in fc:
        if entry['fuel'] == 'electricity':
            elec_price[(entry['location'], entry['fueling_infr_type_id'])] = \
                entry['cost_per_kWh'][fc_idx]
    return elec_price


def weighted_elec_price(bev_fl, elec_price):
    """Weighted avg electricity price from {(geo_id, fl_idx): MWh}."""
    cost = mwh = 0.0
    for (geo_id, fl_idx), val in bev_fl.items():
        if val > 0:
            cost += val * 1000 * elec_price.get((geo_id, fl_idx), 0)  # MWh→kWh × EUR/kWh
            mwh += val
    kwh = mwh * 1000
    return cost, kwh, (cost / kwh if kwh > 0 else 0)


def compute_infra_cost_per_year(q_infr):
    """Returns {y_idx: infra_cost_EUR} for electric infra only."""
    q_by = defaultdict(float)
    for (y_idx, fl_idx, geo_id), kw in q_infr.items():
        if fl_idx in FL_TO_FIT:
            q_by[(fl_idx, geo_id, y_idx)] = kw

    result = {}
    for y_enum, y in enumerate(MODELED_YEARS):
        y_idx = y_enum + 1
        y_arr = y - Y_INIT
        discount = 1.0 / (1 + DISCOUNT_RATE) ** (y - Y_INIT)
        year_cost = 0.0
        for fl_idx in [1, 2]:
            fit_id = FL_TO_FIT[fl_idx]
            for geo_id in ncc_by_loc:
                om = fit_om[fit_id][y_arr]
                ncc = ncc_by_loc.get(geo_id, [0]*41)[y_arr]
                for y0_enum in range(y_enum + 1):
                    latest = 0
                    for ci in range(1, len(MODELED_YEARS) + 1):
                        if ci <= y0_enum + 1:
                            latest = ci
                    cum_kw = q_by.get((fl_idx, geo_id, latest), 0)
                    init = init_kw.get((geo_id, 'electricity'), 0)
                    total_kw = init + cum_kw
                    if total_kw > 0:
                        year_cost += total_kw * (om + ncc) * discount * TIME_STEP
        result[y_idx] = year_cost
    return result


# ── MAIN ─────────────────────────────────────────────────────────────
RUNS = {
    'Unconstrained': (
        BASE / 'results/uncertainty_scenarios/scenario_000/scenario_000_cs_2026-02-11_11-52-48_s_dict.yaml',
        BASE / 'results/uncertainty_scenarios/scenario_000/scenario_000_cs_2026-02-11_11-52-48_q_fuel_infr_plus_dict.yaml',
    ),
    'Breaks-only': (
        BASE / 'results/uncertainty_scenarios_breaks_only/scenario_000/scenario_000_cs_2026-02-11_12-48-22_s_dict.yaml',
        BASE / 'results/uncertainty_scenarios_breaks_only/scenario_000/scenario_000_cs_2026-02-11_12-48-22_q_fuel_infr_plus_dict.yaml',
    ),
}

print("Loading structural data...")
prkg_map = load_structural('scenario_000')

data = {}
for label, (s_path, q_path) in RUNS.items():
    print(f"Parsing {label}...")
    s_data = parse_s_by_year(s_path, prkg_map)
    q_infr = parse_q_infr(q_path)
    infra_by_yidx = compute_infra_cost_per_year(q_infr)
    data[label] = {'s': s_data, 'infra': infra_by_yidx}

# Print combined table
print(f"\n{'='*130}")
print(f"COMBINED ELECTRICITY + INFRASTRUCTURE COST PER kWh — SCENARIO 000 (Go RES)")
print(f"{'='*130}")
print(f"  {'Year':>6s}  |  {'--- Unconstrained ---':^44s}  |  {'--- Breaks-only ---':^44s}  |  {'--- Delta (BRK-UNC) ---':^30s}")
print(f"  {'':>6s}  |  {'MWh':>10s}  {'Elec':>8s}  {'Infra':>8s}  {'Total':>8s}  {'Cost(EUR)':>12s}"
      f"  |  {'MWh':>10s}  {'Elec':>8s}  {'Infra':>8s}  {'Total':>8s}  {'Cost(EUR)':>12s}"
      f"  |  {'Elec':>8s}  {'Infra':>8s}  {'Total':>8s}")
print(f"  {'':>6s}  |  {'':>10s}  {'EUR/kWh':>8s}  {'EUR/kWh':>8s}  {'EUR/kWh':>8s}  {'':>12s}"
      f"  |  {'':>10s}  {'EUR/kWh':>8s}  {'EUR/kWh':>8s}  {'EUR/kWh':>8s}  {'':>12s}"
      f"  |  {'EUR/kWh':>8s}  {'EUR/kWh':>8s}  {'EUR/kWh':>8s}")
print("  " + "-"*126)

for y_enum, y in enumerate(MODELED_YEARS):
    y_idx = y_enum + 1
    fc_idx = y - Y_INIT  # FuelCost array index
    elec_price = load_fuel_prices('scenario_000', fc_idx)

    row = {}
    for label in ['Unconstrained', 'Breaks-only']:
        s_year = data[label]['s'].get(y_idx, {'bev_fl': {}, 'bev_total': 0})
        infra_cost = data[label]['infra'].get(y_idx, 0)
        bev_mwh = s_year['bev_total']
        bev_kwh = bev_mwh * 1000

        if bev_kwh > 0:
            elec_cost, _, elec_avg = weighted_elec_price(s_year['bev_fl'], elec_price)
            infra_per_kwh = infra_cost / bev_kwh
            total_per_kwh = elec_avg + infra_per_kwh
            total_cost = elec_cost + infra_cost
        else:
            elec_avg = infra_per_kwh = total_per_kwh = total_cost = 0

        row[label] = {
            'mwh': bev_mwh, 'elec': elec_avg, 'infra': infra_per_kwh,
            'total': total_per_kwh, 'cost': total_cost,
        }

    u, b = row['Unconstrained'], row['Breaks-only']
    if u['mwh'] > 0 or b['mwh'] > 0:
        d_elec = b['elec'] - u['elec']
        d_infra = b['infra'] - u['infra']
        d_total = b['total'] - u['total']
        print(f"  {y:6d}  |  {u['mwh']:10,.0f}  {u['elec']:8.4f}  {u['infra']:8.4f}  {u['total']:8.4f}  {u['cost']:12,.0f}"
              f"  |  {b['mwh']:10,.0f}  {b['elec']:8.4f}  {b['infra']:8.4f}  {b['total']:8.4f}  {b['cost']:12,.0f}"
              f"  |  {d_elec:+8.4f}  {d_infra:+8.4f}  {d_total:+8.4f}")

print("\nNote: Elec = weighted avg electricity price; Infra = electric infrastructure (O&M + NCC) per kWh charged")
print("      All per-kWh values are nominal (not discounted). Infrastructure cost IS discounted.")
print("Done.")
