"""
Break down electric infrastructure costs to EUR/kWh charged.
Computes: discounted infra cost / discounted kWh for all years.
"""
import yaml, pathlib, re
from collections import defaultdict

BASE = pathlib.Path('C:/Users/simuser/Documents/AntoniaGolab/Scand_Med_analysis/'
                    'SM_baby_2/iDesignRES_transcompmodel/examples/moving_loads_SM')
INPUT_BASE = BASE / 'input_data/uncertainty_scenarios'

Y_INIT = 2020
TIME_STEP = 4
Y_END = 2060
MODELED_YEARS = list(range(Y_INIT, Y_END + 1, TIME_STEP))
DISCOUNT_RATE = 0.04
BEV_FL_IDXS = {1, 2}

# ── Load structural data ─────────────────────────────────────────────
def load_structural(scenario_id):
    inp = INPUT_BASE / scenario_id
    with open(inp / 'Path.yaml') as f:
        paths = yaml.load(f, Loader=yaml.UnsafeLoader)
    with open(inp / 'Odpair.yaml') as f:
        odpairs = yaml.load(f, Loader=yaml.UnsafeLoader)
    path_by_id = {int(p['id']): [int(x) for x in p['sequence']] for p in paths}
    s = set()
    for od in odpairs:
        od_id = int(od['id'])
        pid = int(od['path_id'])
        for geo_id in path_by_id[pid]:
            s.add((0, od_id, pid, geo_id))
    return {i+1: t for i, t in enumerate(sorted(s))}


def parse_s_all_years(filepath, prkg_map):
    """Parse s_dict for ALL year indices. Returns {y_idx: total_bev_kwh}."""
    ci_pat = re.compile(
        r'CartesianIndex\((\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\):\s*([\d.eE+-]+)')
    bev_by_year = defaultdict(float)
    diesel_by_year = defaultdict(float)
    with open(filepath) as f:
        for line in f:
            m = ci_pat.match(line.strip())
            if not m:
                continue
            y_idx = int(m.group(1))
            prkg_idx = int(m.group(2))
            fl_idx = int(m.group(4))
            val = float(m.group(6))
            if val < 1e-6:
                continue
            if prkg_map.get(prkg_idx) is None:
                continue
            if fl_idx in BEV_FL_IDXS:
                bev_by_year[y_idx] += val
            elif fl_idx == 3:
                diesel_by_year[y_idx] += val
    return dict(bev_by_year), dict(diesel_by_year)


# ── Infrastructure cost calculation (electric only) ──────────────────
def parse_q_infr(filepath):
    ci_pat = re.compile(r'CartesianIndex\((\d+),\s*(\d+),\s*(\d+)\):\s*([\d.eE+-]+)')
    result = {}
    with open(filepath) as f:
        for line in f:
            m = ci_pat.match(line.strip())
            if not m:
                continue
            y_idx, fl_idx, geo_id = int(m.group(1)), int(m.group(2)), int(m.group(3))
            val = float(m.group(4))
            if val > 1e-6:
                result[(y_idx, fl_idx, geo_id)] = val
    return result


# Load NCC and FIT om
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

FL_TO_FIT = {1: 1, 2: 2}  # only electric


def compute_elec_infra_cost_by_year(q_infr):
    """Compute electric infrastructure cost per model year (discounted)."""
    q_by = defaultdict(float)
    for (y_idx, fl_idx, geo_id), kw in q_infr.items():
        if fl_idx in FL_TO_FIT:
            q_by[(fl_idx, geo_id, y_idx)] = kw

    cost_by_year_idx = {}
    for y_enum, y in enumerate(MODELED_YEARS):
        y_idx_model = y_enum + 1  # 1-based
        y_arr = y - Y_INIT
        discount = 1.0 / (1 + DISCOUNT_RATE) ** (y - Y_INIT)
        year_cost = 0.0

        for fl_idx in [1, 2]:
            fit_id = FL_TO_FIT[fl_idx]
            for geo_id in ncc_by_loc:
                om = fit_om[fit_id][y_arr]
                ncc = ncc_by_loc.get(geo_id, [0]*41)[y_arr]

                # O&M + NCC on cumulative capacity
                for y0_enum in range(y_enum + 1):  # y0 from y_init to y
                    y0_idx = y0_enum + 1
                    # Latest investment year index <= y0
                    latest_inv_yidx = 0
                    for check_idx in range(1, len(MODELED_YEARS) + 1):
                        if check_idx <= y0_idx:
                            latest_inv_yidx = check_idx
                    cum_kw = q_by.get((fl_idx, geo_id, latest_inv_yidx), 0)
                    init = init_kw.get((geo_id, 'electricity'), 0)
                    total_kw = init + cum_kw
                    if total_kw > 0:
                        year_cost += total_kw * (om + ncc) * discount * TIME_STEP

        cost_by_year_idx[y_idx_model] = year_cost
    return cost_by_year_idx


# ── Main ─────────────────────────────────────────────────────────────
S_FILES = {
    'Unconstrained (free fleet)': (
        BASE / 'results/uncertainty_scenarios/scenario_000/scenario_000_cs_2026-02-11_11-52-48_s_dict.yaml',
        BASE / 'results/uncertainty_scenarios/scenario_000/scenario_000_cs_2026-02-11_11-52-48_q_fuel_infr_plus_dict.yaml',
    ),
    'Breaks-only (free fleet)': (
        BASE / 'results/uncertainty_scenarios_breaks_only/scenario_000/scenario_000_cs_2026-02-11_12-48-22_s_dict.yaml',
        BASE / 'results/uncertainty_scenarios_breaks_only/scenario_000/scenario_000_cs_2026-02-11_12-48-22_q_fuel_infr_plus_dict.yaml',
    ),
    'Unconstrained (brk fleet)': (
        BASE / 'results/uncertainty_scenarios_fixed_brk_fleet/scenario_000/scenario_000_ff_2026-02-14_16-45-30_s_dict.yaml',
        BASE / 'results/uncertainty_scenarios_fixed_brk_fleet/scenario_000/scenario_000_ff_2026-02-14_16-45-30_q_fuel_infr_plus_dict.yaml',
    ),
}

print("Loading structural data...")
prkg_map = load_structural('scenario_000')

print("\n" + "="*110)
print("ELECTRIC INFRASTRUCTURE COST PER kWh CHARGED — SCENARIO 000 (Go RES)")
print("="*110)

for label, (s_path, q_path) in S_FILES.items():
    print(f"\n--- {label} ---")

    # Parse s_dict for all years
    print("  Parsing s_dict (all years)...")
    bev_by_yidx, diesel_by_yidx = parse_s_all_years(s_path, prkg_map)

    # Parse q_infr
    q_infr = parse_q_infr(q_path)
    infra_by_yidx = compute_elec_infra_cost_by_year(q_infr)

    # Print per-year breakdown
    print(f"  {'Year':>6s}  {'BEV kWh':>14s}  {'Disc BEV kWh':>14s}  "
          f"{'Infra cost':>14s}  {'EUR/kWh (disc)':>14s}  {'EUR/kWh (nom)':>14s}")

    total_disc_kwh = 0.0
    total_disc_cost = 0.0
    total_nom_kwh = 0.0
    total_nom_cost = 0.0

    for y_enum, y in enumerate(MODELED_YEARS):
        y_idx = y_enum + 1
        discount = 1.0 / (1 + DISCOUNT_RATE) ** (y - Y_INIT)

        bev_kwh = bev_by_yidx.get(y_idx, 0)
        # kWh in s_dict is already per period; discount for present value
        disc_kwh = bev_kwh * discount * TIME_STEP  # kWh × discount × time_step
        infra_cost = infra_by_yidx.get(y_idx, 0)

        eur_per_kwh_disc = infra_cost / disc_kwh if disc_kwh > 0 else 0
        eur_per_kwh_nom = infra_cost / (bev_kwh * TIME_STEP) if bev_kwh > 0 else 0

        total_disc_kwh += disc_kwh
        total_disc_cost += infra_cost
        total_nom_kwh += bev_kwh * TIME_STEP
        total_nom_cost += infra_cost

        print(f"  {y:6d}  {bev_kwh:14,.0f}  {disc_kwh:14,.0f}  "
              f"{infra_cost:14,.0f}  {eur_per_kwh_disc:14.4f}  {eur_per_kwh_nom:14.4f}")

    avg_disc = total_disc_cost / total_disc_kwh if total_disc_kwh > 0 else 0
    avg_nom = total_nom_cost / total_nom_kwh if total_nom_kwh > 0 else 0
    print(f"  {'TOTAL':>6s}  {'':>14s}  {total_disc_kwh:14,.0f}  "
          f"{total_disc_cost:14,.0f}  {avg_disc:14.4f}  {avg_nom:14.4f}")

print("\nDone.")
