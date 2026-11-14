"""
Full fuel cost comparison (electricity + diesel with carbon price)
for 2032 and 2040, between optimized and breaks-only strategies.
Standalone script — does not insert into manuscript.
"""
import yaml, pathlib, re, csv
from collections import defaultdict

BASE = pathlib.Path('C:/Users/simuser/Documents/AntoniaGolab/Scand_Med_analysis/'
                    'SM_baby_2/iDesignRES_transcompmodel/examples/moving_loads_SM')
INPUT_BASE = BASE / 'input_data/uncertainty_scenarios'
RESULTS_UNC = BASE / 'results/uncertainty_scenarios'
RESULTS_BRK = BASE / 'results/uncertainty_scenarios_breaks_only'
FIG_DIR = BASE / 'figures'

SCENARIOS = {
    'scenario_000': {'name': 'Go RES'},
    'scenario_001': {'name': 'NECPEssentials'},
    'scenario_002': {'name': 'REPowerEU++'},
    'scenario_003': {'name': 'Trinity'},
}
scenario_order = ['scenario_000', 'scenario_001', 'scenario_002', 'scenario_003']

S_FILES_UNC = {
    'scenario_000': 'scenario_000_cs_2026-02-11_11-52-48_s_dict.yaml',
    'scenario_001': 'scenario_001_cs_2026-02-11_12-14-54_s_dict.yaml',
    'scenario_002': 'scenario_002_cs_2026-02-11_12-48-36_s_dict.yaml',
    'scenario_003': 'scenario_003_cs_2026-02-11_13-15-34_s_dict.yaml',
}
S_FILES_BRK = {
    'scenario_000': 'scenario_000_cs_2026-02-11_12-48-22_s_dict.yaml',
    'scenario_001': 'scenario_001_cs_2026-02-11_13-14-27_s_dict.yaml',
    'scenario_002': 'scenario_002_cs_2026-02-11_13-38-11_s_dict.yaml',
    'scenario_003': 'scenario_003_cs_2026-02-11_14-02-22_s_dict.yaml',
}

YEAR_CONFIG = {
    2032: {'y_idx': 4, 'fc_idx': 12},
    2040: {'y_idx': 6, 'fc_idx': 20},
}

BEV_FL_IDXS = {1, 2}
DIESEL_FL_IDX = 3
EMISSION_FACTOR = 266.0 / 1e6  # tCO2/kWh


# ── Load structural data ─────────────────────────────────────────────
def load_structural(scenario_id):
    """Load paths, odpairs, and build prkg_idx_map."""
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
    prkg_idx_map = {i+1: t for i, t in enumerate(p_r_k_g_sorted)}
    return prkg_idx_map


# ── Parse s_dict for MULTIPLE year indices at once ────────────────────
def load_s_dict_multi_year(filepath, prkg_idx_map, year_indices):
    """Parse s_dict for multiple year indices simultaneously.
    Returns dict: {y_idx: {bev_by_node_fl, diesel_by_node}} where
    bev_by_node_fl = {(geo_id, fl_idx): kWh}, diesel_by_node = {geo_id: kWh}.
    """
    ci_pat = re.compile(
        r'CartesianIndex\((\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\):\s*([\d.eE+-]+)')

    year_set = set(year_indices)
    result = {}
    for yi in year_indices:
        result[yi] = {
            'bev_fl': defaultdict(float),
            'diesel': defaultdict(float),
        }

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
            prkg = prkg_idx_map.get(prkg_idx)
            if prkg is None:
                continue
            _, od_id, path_id, geo_id = prkg

            if fl_idx in BEV_FL_IDXS:
                result[y_idx]['bev_fl'][(geo_id, fl_idx)] += val
            elif fl_idx == DIESEL_FL_IDX:
                result[y_idx]['diesel'][geo_id] += val

    return result


# ── Load fuel prices for a specific year ──────────────────────────────
def load_fuel_prices(scenario_id, fc_idx):
    """Load electricity and diesel+carbon prices for a given FuelCost array index."""
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

    carbon_price = {}
    for g in geo:
        carbon_price[g['id']] = g['carbon_price'][fc_idx]

    diesel_effective = {}
    for loc in diesel_base:
        cp = carbon_price.get(loc, 0)
        diesel_effective[loc] = diesel_base[loc] + cp * EMISSION_FACTOR

    return elec_price, diesel_effective, diesel_base, carbon_price


def weighted_avg(by_node_fl, prices):
    """Weighted avg price from {(geo_id, fl_idx): kWh}."""
    cost = kwh = 0.0
    for key, val in by_node_fl.items():
        if val <= 0:
            continue
        cost += val * prices.get(key, 0)
        kwh += val
    return cost, kwh, (cost / kwh if kwh else 0)


def weighted_avg_diesel(by_node, prices):
    """Weighted avg diesel price from {geo_id: kWh}."""
    cost = kwh = 0.0
    for geo_id, val in by_node.items():
        if val <= 0:
            continue
        cost += val * prices.get(geo_id, 0)
        kwh += val
    return cost, kwh, (cost / kwh if kwh else 0)


# ══════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════
print("Loading geographic data...")
with open(BASE / 'input_data/fixed_nuts_2/GeographicElement.yaml') as f:
    geo_data = yaml.safe_load(f)
geo_country = {g['id']: g['country'] for g in geo_data}

all_rows = []

for scen_id in scenario_order:
    cfg = SCENARIOS[scen_id]
    print(f"\nProcessing {cfg['name']}...")

    # Load structural data
    prkg_map = load_structural(scen_id)

    # Parse s_dict for both years (unc + brk)
    unc_path = RESULTS_UNC / scen_id / S_FILES_UNC[scen_id]
    brk_path = RESULTS_BRK / scen_id / S_FILES_BRK[scen_id]

    print(f"  Parsing unconstrained s_dict...")
    unc_data = load_s_dict_multi_year(unc_path, prkg_map, [4, 6])
    print(f"  Parsing breaks-only s_dict...")
    brk_data = load_s_dict_multi_year(brk_path, prkg_map, [4, 6])

    for year, ycfg in YEAR_CONFIG.items():
        y_idx = ycfg['y_idx']
        fc_idx = ycfg['fc_idx']

        # Load prices
        elec_price, diesel_eff, diesel_base_prices, carbon_prices = \
            load_fuel_prices(scen_id, fc_idx)

        # --- Unconstrained ---
        unc_e_cost, unc_e_kwh, unc_e_avg = weighted_avg(
            unc_data[y_idx]['bev_fl'], elec_price)
        unc_d_cost, unc_d_kwh, unc_d_avg = weighted_avg_diesel(
            unc_data[y_idx]['diesel'], diesel_eff)
        unc_d_base_cost, _, unc_d_base_avg = weighted_avg_diesel(
            unc_data[y_idx]['diesel'], diesel_base_prices)
        # Carbon component only
        carbon_eff = {loc: carbon_prices.get(loc, 0) * EMISSION_FACTOR
                      for loc in diesel_base_prices}
        unc_carbon_cost, _, unc_carbon_avg = weighted_avg_diesel(
            unc_data[y_idx]['diesel'], carbon_eff)

        # --- Breaks-only ---
        brk_e_cost, brk_e_kwh, brk_e_avg = weighted_avg(
            brk_data[y_idx]['bev_fl'], elec_price)
        brk_d_cost, brk_d_kwh, brk_d_avg = weighted_avg_diesel(
            brk_data[y_idx]['diesel'], diesel_eff)
        brk_d_base_cost, _, brk_d_base_avg = weighted_avg_diesel(
            brk_data[y_idx]['diesel'], diesel_base_prices)
        brk_carbon_cost, _, brk_carbon_avg = weighted_avg_diesel(
            brk_data[y_idx]['diesel'], carbon_eff)

        # Totals
        unc_total = unc_e_cost + unc_d_cost
        brk_total = brk_e_cost + brk_d_cost
        delta_total = brk_total - unc_total
        delta_pct = delta_total / unc_total * 100 if unc_total else 0

        row = {
            'scenario': cfg['name'], 'year': year,
            'unc_elec_kwh': unc_e_kwh, 'unc_elec_avg': unc_e_avg,
            'unc_elec_cost': unc_e_cost,
            'unc_diesel_kwh': unc_d_kwh, 'unc_diesel_base_avg': unc_d_base_avg,
            'unc_carbon_avg': unc_carbon_avg, 'unc_diesel_eff_avg': unc_d_avg,
            'unc_diesel_cost': unc_d_cost, 'unc_total': unc_total,
            'brk_elec_kwh': brk_e_kwh, 'brk_elec_avg': brk_e_avg,
            'brk_elec_cost': brk_e_cost,
            'brk_diesel_kwh': brk_d_kwh, 'brk_diesel_base_avg': brk_d_base_avg,
            'brk_carbon_avg': brk_carbon_avg, 'brk_diesel_eff_avg': brk_d_avg,
            'brk_diesel_cost': brk_d_cost, 'brk_total': brk_total,
            'delta_total': delta_total, 'delta_pct': delta_pct,
        }
        all_rows.append(row)

# ── Print results ─────────────────────────────────────────────────────
for year in [2032, 2040]:
    print(f"\n{'='*100}")
    print(f"FUEL COST COMPARISON: OPTIMIZED vs BREAKS-ONLY ({year})")
    print(f"{'='*100}")
    print(f"  {'Scenario':<16s}  {'Strategy':<12s}  "
          f"{'Elec kWh':>10s}  {'Elec avg':>10s}  {'Elec cost':>12s}  "
          f"{'Dies kWh':>10s}  {'Dies base':>10s}  {'Carbon':>8s}  {'Dies eff':>10s}  {'Dies cost':>12s}  "
          f"{'TOTAL':>12s}")

    for scen_id in scenario_order:
        cfg = SCENARIOS[scen_id]
        rows = [r for r in all_rows if r['scenario'] == cfg['name'] and r['year'] == year]
        if not rows:
            continue
        r = rows[0]
        print(f"\n  {cfg['name']:<16s}  {'Optimized':<12s}  "
              f"{r['unc_elec_kwh']:10.0f}  {r['unc_elec_avg']:10.4f}  {r['unc_elec_cost']:12.2f}  "
              f"{r['unc_diesel_kwh']:10.0f}  {r['unc_diesel_base_avg']:10.4f}  "
              f"{r['unc_carbon_avg']:8.4f}  {r['unc_diesel_eff_avg']:10.4f}  "
              f"{r['unc_diesel_cost']:12.2f}  {r['unc_total']:12.2f}")
        print(f"  {'':<16s}  {'Breaks-only':<12s}  "
              f"{r['brk_elec_kwh']:10.0f}  {r['brk_elec_avg']:10.4f}  {r['brk_elec_cost']:12.2f}  "
              f"{r['brk_diesel_kwh']:10.0f}  {r['brk_diesel_base_avg']:10.4f}  "
              f"{r['brk_carbon_avg']:8.4f}  {r['brk_diesel_eff_avg']:10.4f}  "
              f"{r['brk_diesel_cost']:12.2f}  {r['brk_total']:12.2f}")
        print(f"  {'':<16s}  {'Delta':<12s}  "
              f"{'':>10s}  {'':>10s}  "
              f"{r['brk_elec_cost']-r['unc_elec_cost']:+12.2f}  "
              f"{'':>10s}  {'':>10s}  {'':>8s}  {'':>10s}  "
              f"{r['brk_diesel_cost']-r['unc_diesel_cost']:+12.2f}  "
              f"{r['delta_total']:+12.2f} ({r['delta_pct']:+.3f}%)")

    # Summary table
    print(f"\n  --- Summary ({year}) ---")
    print(f"  {'Scenario':<16s}  {'Unc total (EUR)':>16s}  {'Brk total (EUR)':>16s}  "
          f"{'Delta (EUR)':>14s}  {'Delta (%)':>10s}")
    for scen_id in scenario_order:
        cfg = SCENARIOS[scen_id]
        rows = [r for r in all_rows if r['scenario'] == cfg['name'] and r['year'] == year]
        if not rows:
            continue
        r = rows[0]
        print(f"  {cfg['name']:<16s}  {r['unc_total']:16.2f}  {r['brk_total']:16.2f}  "
              f"{r['delta_total']:+14.2f}  {r['delta_pct']:+10.3f}%")

# Save CSV
csv_path = FIG_DIR / 'fuel_cost_comparison_2032_2040.csv'
with open(csv_path, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()))
    w.writeheader()
    w.writerows(all_rows)
print(f"\nCSV saved to {csv_path}")
