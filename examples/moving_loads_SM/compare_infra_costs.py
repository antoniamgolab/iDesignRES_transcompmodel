"""
Compare infrastructure costs (q_fuel_infr_plus) + fuel costs across 3 strategies
for scenario_000 (Go RES).

Infrastructure cost components per kW installed:
  - FIT om_costs (from FuelingInfrTypes.yaml)
  - Network connection costs (from NetworkConnectionCosts.yaml, location-dependent)
  - FIT cost_per_kW = 0 for electric, so no capital cost

Objective structure: for each year y, cost = cumulative_kW × (fit_om + ncc) × discount × time_step
"""
import yaml, pathlib, re
from collections import defaultdict

BASE = pathlib.Path('C:/Users/simuser/Documents/AntoniaGolab/Scand_Med_analysis/'
                    'SM_baby_2/iDesignRES_transcompmodel/examples/moving_loads_SM')
INPUT_BASE = BASE / 'input_data/uncertainty_scenarios'

# ── Load infrastructure parameters ───────────────────────────────────
print("Loading infrastructure cost parameters...")

with open(INPUT_BASE / 'scenario_000/FuelingInfrTypes.yaml') as f:
    fit_data = yaml.safe_load(f)

# FIT om_costs by id (41-element array, index 0 = year 2020)
fit_om = {}
fit_cost_per_kw = {}
for fit in fit_data:
    fit_om[fit['id']] = fit['om_costs']
    fit_cost_per_kw[fit['id']] = fit.get('cost_per_kW', [0.0]*41)

with open(INPUT_BASE / 'scenario_000/NetworkConnectionCosts.yaml') as f:
    ncc_data = yaml.safe_load(f)

# NCC by location (41-element array)
ncc_by_loc = {}
for entry in ncc_data:
    ncc_by_loc[entry['location']] = entry['network_cost_per_kW']

with open(INPUT_BASE / 'scenario_000/InitialFuelInfr.yaml') as f:
    init_infr = yaml.safe_load(f)

# Initial installed kW by (location, fuel)
init_kw = {}
for entry in init_infr:
    init_kw[(entry['allocation'], entry['fuel'])] = entry['installed_kW']

with open(BASE / 'input_data/fixed_nuts_2/GeographicElement.yaml') as f:
    geo_data = yaml.safe_load(f)
geo_country = {g['id']: g['country'] for g in geo_data}

# Model parameters
Y_INIT = 2020
TIME_STEP = 4
Y_END = 2060
MODELED_YEARS = list(range(Y_INIT, Y_END + 1, TIME_STEP))
INVESTMENT_YEARS = MODELED_YEARS  # same
DISCOUNT_RATE = 0.04

# f_l mapping: in the CartesianIndex, the second element maps to f_l_not_by_route
# Based on the model: f_l_not_by_route pairs are indexed 1,2,3
# 1 = (electricity, 1) = slow charging (FIT1)
# 2 = (electricity, 2) = fast charging (FIT2)
# 3 = (diesel, 0) = diesel (FIT0)
FL_TO_FIT = {1: 1, 2: 2, 3: 0}  # f_l_idx → FIT id
FL_TO_FUEL = {1: 'electricity', 2: 'electricity', 3: 'diesel'}

# ── Parse q_fuel_infr_plus ───────────────────────────────────────────
def parse_q_infr(filepath):
    """Parse q_fuel_infr_plus dict. Returns {(y_idx, f_l_idx, geo_id): kW}."""
    ci_pat = re.compile(r'CartesianIndex\((\d+),\s*(\d+),\s*(\d+)\):\s*([\d.eE+-]+)')
    result = {}
    with open(filepath) as f:
        for line in f:
            m = ci_pat.match(line.strip())
            if not m:
                continue
            y_idx = int(m.group(1))
            fl_idx = int(m.group(2))
            geo_id = int(m.group(3))
            val = float(m.group(4))
            if val > 1e-6:
                result[(y_idx, fl_idx, geo_id)] = val
    return result


def compute_infra_cost(q_infr, year_target=None):
    """Compute total infrastructure cost mirroring the objective function.

    For each year y, for each (f_l, geo):
      cumulative_kW = initial_kW + q_infr[max_inv_year <= y0]
      annual_cost = cumulative_kW × (fit_om[y] + ncc[geo, y]) × discount[y] × time_step

    If year_target is given, only returns cost for that year.
    """
    # Build cumulative capacity by (f_l_idx, geo_id, year)
    # q_infr keys: (y_idx, f_l_idx, geo_id) where y_idx is 1-based into INVESTMENT_YEARS
    q_by_fl_geo_yidx = defaultdict(float)
    for (y_idx, fl_idx, geo_id), kw in q_infr.items():
        q_by_fl_geo_yidx[(fl_idx, geo_id, y_idx)] = kw

    total_cost = 0.0
    cost_by_fl = defaultdict(float)
    cost_by_year = defaultdict(float)
    total_kw_by_fl = defaultdict(float)  # total new capacity by fl

    for y_enum, y in enumerate(MODELED_YEARS):
        y_arr_idx = y - Y_INIT  # 0-based index into 41-element arrays
        discount = 1.0 / (1 + DISCOUNT_RATE) ** (y - Y_INIT)

        if year_target and y != year_target:
            continue

        for fl_idx in [1, 2, 3]:
            fit_id = FL_TO_FIT[fl_idx]
            fuel_name = FL_TO_FUEL[fl_idx]

            for geo_id in ncc_by_loc:
                # Get FIT om cost
                om = fit_om[fit_id][y_arr_idx]
                # Get NCC (only for electricity)
                ncc = ncc_by_loc.get(geo_id, [0]*41)[y_arr_idx] if fuel_name == 'electricity' else 0
                # Get FIT capital cost (per investment year)
                cap = fit_cost_per_kw[fit_id][y_arr_idx]

                # Cumulative installed kW (initial + all investments up to y)
                # Investment years: find which y_idx corresponds to years <= y
                init = init_kw.get((geo_id, fuel_name), 0)

                # Capital cost: only for new investments in this year
                if y in INVESTMENT_YEARS:
                    inv_y_idx = INVESTMENT_YEARS.index(y) + 1  # 1-based
                    new_kw = q_by_fl_geo_yidx.get((fl_idx, geo_id, inv_y_idx), 0)
                    if new_kw > 0:
                        cap_cost = new_kw * cap * discount
                        total_cost += cap_cost
                        cost_by_fl[fl_idx] += cap_cost
                        cost_by_year[y] += cap_cost
                        total_kw_by_fl[fl_idx] += new_kw

                # O&M + NCC: cumulative over y0 from y_init to y (mimicking objective)
                for y0 in range(Y_INIT, y + 1, TIME_STEP):
                    # Get cumulative q at max_inv_year <= y0
                    cum_q = 0.0
                    for inv_y_idx_check in range(1, len(INVESTMENT_YEARS) + 1):
                        inv_year = INVESTMENT_YEARS[inv_y_idx_check - 1]
                        if inv_year <= y0:
                            cum_q = q_by_fl_geo_yidx.get((fl_idx, geo_id, inv_y_idx_check), cum_q)
                            # Actually need max investment year <= y0
                    # Simpler: find the latest investment year <= y0
                    latest_inv_yidx = 0
                    for inv_y_idx_check in range(1, len(INVESTMENT_YEARS) + 1):
                        if INVESTMENT_YEARS[inv_y_idx_check - 1] <= y0:
                            latest_inv_yidx = inv_y_idx_check
                    cum_kw = q_by_fl_geo_yidx.get((fl_idx, geo_id, latest_inv_yidx), 0)

                    total_kw = init + cum_kw
                    if total_kw > 0:
                        annual = total_kw * (om + ncc) * discount * TIME_STEP
                        total_cost += annual
                        cost_by_fl[fl_idx] += annual
                        cost_by_year[y] += annual

    return total_cost, dict(cost_by_fl), dict(cost_by_year), dict(total_kw_by_fl)


# ── Load and compare ─────────────────────────────────────────────────
Q_FILES = {
    'Unconstrained (free fleet)':
        BASE / 'results/uncertainty_scenarios/scenario_000/scenario_000_cs_2026-02-11_11-52-48_q_fuel_infr_plus_dict.yaml',
    'Breaks-only (free fleet)':
        BASE / 'results/uncertainty_scenarios_breaks_only/scenario_000/scenario_000_cs_2026-02-11_12-48-22_q_fuel_infr_plus_dict.yaml',
    'Unconstrained (brk fleet)':
        BASE / 'results/uncertainty_scenarios_fixed_brk_fleet/scenario_000/scenario_000_ff_2026-02-14_16-45-30_q_fuel_infr_plus_dict.yaml',
}

print("\n" + "="*100)
print("INFRASTRUCTURE COST COMPARISON — SCENARIO 000 (Go RES)")
print("="*100)

for label, filepath in Q_FILES.items():
    print(f"\n--- {label} ---")
    q_infr = parse_q_infr(filepath)

    # Aggregate new capacity by fl_idx
    new_kw_by_fl = defaultdict(float)
    new_kw_by_fl_geo = defaultdict(lambda: defaultdict(float))
    for (y_idx, fl_idx, geo_id), kw in q_infr.items():
        new_kw_by_fl[fl_idx] += kw
        new_kw_by_fl_geo[fl_idx][geo_id] += kw

    print(f"  Total new capacity (kW) across all years:")
    for fl_idx in sorted(new_kw_by_fl.keys()):
        fit_id = FL_TO_FIT[fl_idx]
        n_nodes = len(new_kw_by_fl_geo[fl_idx])
        print(f"    fl={fl_idx} (FIT{fit_id}): {new_kw_by_fl[fl_idx]:12.1f} kW at {n_nodes} nodes")

    # Total infra cost
    total, by_fl, by_year, kw_by_fl = compute_infra_cost(q_infr)
    print(f"  Total infrastructure cost (discounted, all years): {total:,.0f} EUR")
    for fl_idx in sorted(by_fl.keys()):
        print(f"    fl={fl_idx}: {by_fl[fl_idx]:,.0f} EUR")

    # Show top nodes by electric capacity
    elec_geo = new_kw_by_fl_geo.get(1, {})
    if elec_geo:
        top = sorted(elec_geo.items(), key=lambda x: -x[1])[:10]
        print(f"  Top 10 nodes by slow-charging capacity:")
        for geo_id, kw in top:
            country = geo_country.get(geo_id, '??')
            ncc_val = ncc_by_loc.get(geo_id, [0]*41)[12]  # 2032 value
            print(f"    Node {geo_id:3d} ({country}): {kw:8.1f} kW  (NCC={ncc_val:.2f} EUR/kW/yr)")

print("\n\nDone.")
