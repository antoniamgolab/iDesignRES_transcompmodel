"""
Quick comparison: fuel costs for scenario_000 (Go RES) across 3 strategies:
  1. Original unconstrained (free fleet + free charging)
  2. Breaks-only (free fleet + breaks-only charging)
  3. Fixed brk fleet + unconstrained charging (brk fleet + free charging)
"""
import yaml, pathlib, re
from collections import defaultdict

BASE = pathlib.Path('C:/Users/simuser/Documents/AntoniaGolab/Scand_Med_analysis/'
                    'SM_baby_2/iDesignRES_transcompmodel/examples/moving_loads_SM')
INPUT_BASE = BASE / 'input_data/uncertainty_scenarios'

EMISSION_FACTOR = 266.0 / 1e6  # tCO2/kWh

# s_dict files for scenario_000
S_FILES = {
    'Unconstrained (free fleet)':
        BASE / 'results/uncertainty_scenarios/scenario_000/scenario_000_cs_2026-02-11_11-52-48_s_dict.yaml',
    'Breaks-only (free fleet)':
        BASE / 'results/uncertainty_scenarios_breaks_only/scenario_000/scenario_000_cs_2026-02-11_12-48-22_s_dict.yaml',
    'Unconstrained (brk fleet)':
        BASE / 'results/uncertainty_scenarios_fixed_brk_fleet/scenario_000/scenario_000_ff_2026-02-14_16-45-30_s_dict.yaml',
}

# Build prkg_idx_map
def load_structural(scenario_id):
    inp = INPUT_BASE / scenario_id
    with open(inp / 'Path.yaml') as f:
        paths = yaml.load(f, Loader=yaml.UnsafeLoader)
    with open(inp / 'Odpair.yaml') as f:
        odpairs = yaml.load(f, Loader=yaml.UnsafeLoader)
    path_by_id = {int(p['id']): [int(x) for x in p['sequence']] for p in paths}
    p_r_k_g_set = set()
    for od in odpairs:
        od_id = int(od['id'])
        pid = int(od['path_id'])
        for geo_id in path_by_id[pid]:
            p_r_k_g_set.add((0, od_id, pid, geo_id))
    p_r_k_g_sorted = sorted(p_r_k_g_set)
    return {i+1: t for i, t in enumerate(p_r_k_g_sorted)}


def parse_s_dict(filepath, prkg_map, year_indices):
    """Parse s_dict for multiple year indices."""
    ci_pat = re.compile(
        r'CartesianIndex\((\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\):\s*([\d.eE+-]+)')
    year_set = set(year_indices)
    result = {yi: {'bev_fl': defaultdict(float), 'diesel': defaultdict(float)}
              for yi in year_indices}
    with open(filepath) as f:
        for line in f:
            m = ci_pat.match(line.strip())
            if not m:
                continue
            y_idx = int(m.group(1))
            if y_idx not in year_set:
                continue
            prkg_idx = int(m.group(2))
            fl_idx = int(m.group(4))
            val = float(m.group(6))
            if val < 1e-6:
                continue
            prkg = prkg_map.get(prkg_idx)
            if prkg is None:
                continue
            _, od_id, path_id, geo_id = prkg
            if fl_idx in {1, 2}:
                result[y_idx]['bev_fl'][(geo_id, fl_idx)] += val
            elif fl_idx == 3:
                result[y_idx]['diesel'][geo_id] += val
    return result


def load_fuel_prices(scenario_id, fc_idx):
    inp = INPUT_BASE / scenario_id
    with open(inp / 'FuelCost.yaml') as f:
        fc = yaml.safe_load(f)
    with open(BASE / 'input_data/fixed_nuts_2/GeographicElement.yaml') as f:
        geo = yaml.safe_load(f)
    elec_price = {}
    for entry in fc:
        if entry['fuel'] == 'electricity':
            elec_price[(entry['location'], entry['fueling_infr_type_id'])] = \
                entry['cost_per_kWh'][fc_idx]
    diesel_base = {}
    for entry in fc:
        if entry['fuel'] == 'diesel':
            diesel_base[entry['location']] = entry['cost_per_kWh'][fc_idx]
    carbon_price = {g['id']: g['carbon_price'][fc_idx] for g in geo}
    diesel_eff = {loc: diesel_base[loc] + carbon_price.get(loc, 0) * EMISSION_FACTOR
                  for loc in diesel_base}
    return elec_price, diesel_eff


def weighted_avg(by_node_fl, prices):
    cost = kwh = 0.0
    for key, val in by_node_fl.items():
        if val > 0:
            cost += val * prices.get(key, 0)
            kwh += val
    return cost, kwh, (cost / kwh if kwh else 0)


def weighted_avg_simple(by_node, prices):
    cost = kwh = 0.0
    for geo_id, val in by_node.items():
        if val > 0:
            cost += val * prices.get(geo_id, 0)
            kwh += val
    return cost, kwh, (cost / kwh if kwh else 0)


# ── MAIN ──────────────────────────────────────────────────────────────
print("Loading structural data...")
prkg_map = load_structural('scenario_000')

for year, y_idx, fc_idx in [(2032, 4, 12), (2040, 6, 20)]:
    print(f"\n{'='*100}")
    print(f"SCENARIO 000 (Go RES) — FUEL COST COMPARISON AT {year}")
    print(f"{'='*100}")

    elec_price, diesel_eff = load_fuel_prices('scenario_000', fc_idx)

    print(f"\n  {'Strategy':<30s}  {'Elec kWh':>10s}  {'Elec avg':>10s}  {'Elec cost':>12s}  "
          f"{'Dies kWh':>10s}  {'Dies avg':>10s}  {'Dies cost':>12s}  {'TOTAL':>12s}")

    for label, filepath in S_FILES.items():
        print(f"\n  Loading {label}...")
        data = parse_s_dict(filepath, prkg_map, [y_idx])

        e_cost, e_kwh, e_avg = weighted_avg(data[y_idx]['bev_fl'], elec_price)
        d_cost, d_kwh, d_avg = weighted_avg_simple(data[y_idx]['diesel'], diesel_eff)
        total = e_cost + d_cost

        print(f"  {label:<30s}  {e_kwh:10.0f}  {e_avg:10.4f}  {e_cost:12.2f}  "
              f"{d_kwh:10.0f}  {d_avg:10.4f}  {d_cost:12.2f}  {total:12.2f}")

print("\nDone.")
