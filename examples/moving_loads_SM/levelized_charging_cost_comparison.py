"""
Final comparison table: levelized charging cost (electricity + infrastructure)
across 4 strategies for scenario_000 (Go RES).

Strategies:
  (1) Unconstrained (free fleet)    — model run, free charging + free fleet
  (2) SOC-aware analytical          — analytical benchmark, lazy charging at breaks
  (3) Unconstrained (brk fleet)     — model run, free charging + fixed brk fleet
  (4) Breaks-only (free fleet)      — model run, breaks-only charging + free fleet

s is in MWh. Infrastructure = O&M + NCC on installed electric charging capacity.
SOC-aware infra assumed = breaks-only infra (charges at break locations).
"""
import yaml, pathlib, re, csv
from collections import defaultdict

BASE = pathlib.Path(__file__).resolve().parent
INPUT_BASE = BASE / 'input_data/uncertainty_scenarios'
FIG_DIR = BASE / 'figures'

Y_INIT = 2020; TIME_STEP = 4; Y_END = 2060
MODELED_YEARS = list(range(Y_INIT, Y_END + 1, TIME_STEP))
DISCOUNT_RATE = 0.04
BATTERY_CAP = 1187.0
SPEC_CONS_2032 = 1.6

# ── Load all infrastructure parameters ───────────────────────────────
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


# ── Structural data ──────────────────────────────────────────────────
def load_structural(scenario_id):
    inp = INPUT_BASE / scenario_id
    with open(inp / 'Path.yaml') as f:
        paths = yaml.load(f, Loader=yaml.UnsafeLoader)
    with open(inp / 'Odpair.yaml') as f:
        odpairs = yaml.load(f, Loader=yaml.UnsafeLoader)
    with open(inp / 'MandatoryBreaks.yaml') as f:
        breaks_data = yaml.safe_load(f)

    path_by_id = {int(p['id']): [int(x) for x in p['sequence']] for p in paths}
    path_dist_by_id = {}
    for p in paths:
        pid = int(p['id'])
        path_dist_by_id[pid] = [float(d) for d in p.get('distance_from_previous', [])]

    s = set()
    od_to_path = {}
    for od in odpairs:
        od_id, pid = int(od['id']), int(od['path_id'])
        od_to_path[od_id] = pid
        for geo_id in path_by_id[pid]:
            s.add((0, od_id, pid, geo_id))
    prkg_map = {i+1: t for i, t in enumerate(sorted(s))}

    breaks_by_path = defaultdict(list)
    for brk in breaks_data:
        breaks_by_path[int(brk['path_id'])].append(int(brk['latest_geo_id']))

    return prkg_map, path_by_id, path_dist_by_id, od_to_path, breaks_by_path


# ── Parse s_dict ─────────────────────────────────────────────────────
def parse_s_by_year(filepath, prkg_map):
    """Returns {y_idx: {'bev_fl': {(geo,fl): MWh}, 'by_od_path': {(od,path): MWh}, 'total': MWh}}"""
    ci_pat = re.compile(
        r'CartesianIndex\((\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\):\s*([\d.eE+-]+)')
    result = defaultdict(lambda: {'bev_fl': defaultdict(float),
                                   'by_od_path': defaultdict(float),
                                   'total': 0.0})
    with open(filepath) as f:
        for line in f:
            m = ci_pat.match(line.strip())
            if not m: continue
            y_idx, prkg_idx, fl_idx = int(m.group(1)), int(m.group(2)), int(m.group(4))
            val = float(m.group(6))
            if val < 1e-6: continue
            prkg = prkg_map.get(prkg_idx)
            if prkg is None: continue
            _, od_id, path_id, geo_id = prkg
            if fl_idx in {1, 2}:
                result[y_idx]['bev_fl'][(geo_id, fl_idx)] += val
                result[y_idx]['by_od_path'][(od_id, path_id)] += val
                result[y_idx]['total'] += val
    return dict(result)


# ── SOC-aware distribution ───────────────────────────────────────────
def compute_soc_aware(by_od_path, breaks_by_path, path_by_id, path_dist_by_id,
                      battery_cap=BATTERY_CAP, spec_cons=SPEC_CONS_2032,
                      initial_soc_frac=0.5):
    """Lazy charging: only charge when SOC < energy_to_next_break."""
    soc_fl = defaultdict(float)  # (geo_id, fl_idx=1) → MWh

    for (od_id, path_id), total_energy in by_od_path.items():
        if total_energy < 1e-6:
            continue
        seq = path_by_id.get(path_id, [])
        dist = path_dist_by_id.get(path_id, [])
        break_set = set(breaks_by_path.get(path_id, []))
        if not seq or not dist or len(seq) != len(dist):
            continue

        # Build cumulative distances and identify break indices
        break_indices = [i for i, g in enumerate(seq) if g in break_set]
        cum_dist = []
        d = 0
        for dd in dist:
            d += dd
            cum_dist.append(d)

        # Simulate SOC
        initial_soc = battery_cap * initial_soc_frac
        soc = initial_soc
        raw_charges = {}
        for bi in break_indices:
            dist_here = cum_dist[bi]
            # Energy consumed since start (or last charge)
            energy_consumed = spec_cons * dist_here if bi == break_indices[0] else \
                spec_cons * (cum_dist[bi] - cum_dist[last_charged]) if 'last_charged' in dir() else spec_cons * dist_here

            # Simpler: track SOC along route
            pass

        # Restart with clean simulation
        soc = initial_soc
        charges = []
        last_pos = 0  # cumulative distance of last charge/start

        for bi in break_indices:
            dist_traveled = cum_dist[bi] - last_pos if last_pos > 0 else cum_dist[bi]
            energy_used = spec_cons * dist_traveled
            soc -= energy_used

            # Look ahead to next break or end
            if bi < break_indices[-1]:
                next_bi = break_indices[break_indices.index(bi) + 1]
                dist_to_next = cum_dist[next_bi] - cum_dist[bi]
            else:
                dist_to_next = cum_dist[-1] - cum_dist[bi]
            energy_to_next = spec_cons * dist_to_next

            if soc < energy_to_next:
                charge_amount = battery_cap - soc
                charges.append((seq[bi], charge_amount))
                soc = battery_cap
                last_pos = cum_dist[bi]
            else:
                last_pos = cum_dist[bi] if last_pos == 0 else last_pos
                # Don't update last_pos if we didn't charge — keep tracking from last charge
                pass

        # Scale proportions to match model total
        total_raw = sum(c for _, c in charges)
        if total_raw > 0:
            scale = total_energy / total_raw
            for geo_id, amount in charges:
                soc_fl[(geo_id, 1)] += amount * scale
        elif break_set:
            # Fallback: even distribution at breaks
            per_break = total_energy / len(break_set)
            for geo_id in break_set:
                soc_fl[(geo_id, 1)] += per_break

    return dict(soc_fl)


# ── Infrastructure cost ──────────────────────────────────────────────
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


def infra_cost_per_year(q_infr):
    q_by = defaultdict(float)
    for (y_idx, fl_idx, geo_id), kw in q_infr.items():
        if fl_idx in FL_TO_FIT:
            q_by[(fl_idx, geo_id, y_idx)] = kw
    result = {}
    for y_enum, y in enumerate(MODELED_YEARS):
        y_idx = y_enum + 1
        y_arr = y - Y_INIT
        discount = 1.0 / (1 + DISCOUNT_RATE) ** (y - Y_INIT)
        cost = 0.0
        for fl_idx in [1, 2]:
            fit_id = FL_TO_FIT[fl_idx]
            for geo_id in ncc_by_loc:
                om = fit_om[fit_id][y_arr]
                ncc = ncc_by_loc.get(geo_id, [0]*41)[y_arr]
                for y0_enum in range(y_enum + 1):
                    latest = max(ci for ci in range(1, len(MODELED_YEARS)+1) if ci <= y0_enum+1)
                    cum_kw = q_by.get((fl_idx, geo_id, latest), 0)
                    init = init_kw.get((geo_id, 'electricity'), 0)
                    total_kw = init + cum_kw
                    if total_kw > 0:
                        cost += total_kw * (om + ncc) * discount * TIME_STEP
        result[y_idx] = cost
    return result


# ── Fuel prices ──────────────────────────────────────────────────────
def load_elec_prices(fc_idx):
    with open(INPUT_BASE / 'scenario_000/FuelCost.yaml') as f:
        fc = yaml.safe_load(f)
    return {(e['location'], e['fueling_infr_type_id']): e['cost_per_kWh'][fc_idx]
            for e in fc if e['fuel'] == 'electricity'}


def weighted_elec(bev_fl, prices):
    """From {(geo, fl): MWh} → total cost (EUR), total kWh, avg EUR/kWh."""
    cost = mwh = 0.0
    for (g, fl), val in bev_fl.items():
        if val > 0:
            cost += val * 1000 * prices.get((g, fl), 0)
            mwh += val
    kwh = mwh * 1000
    return cost, kwh, (cost/kwh if kwh > 0 else 0)


# ══════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════
print("Loading structural data...")
prkg_map, path_by_id, path_dist_by_id, od_to_path, breaks_by_path = \
    load_structural('scenario_000')

# Load s_dict for 3 model runs
S_PATHS = {
    'unc':     BASE / 'results/uncertainty_scenarios_v2/scenario_000/scenario_000_cs_2026-02-14_18-25-42_s_dict.yaml',
    'brk':     BASE / 'results/uncertainty_scenarios_breaks_only/scenario_000/scenario_000_cs_2026-02-11_12-48-22_s_dict.yaml',
    'unc_ff':  BASE / 'results/uncertainty_scenarios_fixed_brk_fleet_v3/scenario_000/scenario_000_ff_2026-02-14_18-57-14_s_dict.yaml',
}
Q_PATHS = {
    'unc':     BASE / 'results/uncertainty_scenarios_v2/scenario_000/scenario_000_cs_2026-02-14_18-25-42_q_fuel_infr_plus_dict.yaml',
    'brk':     BASE / 'results/uncertainty_scenarios_breaks_only/scenario_000/scenario_000_cs_2026-02-11_12-48-22_q_fuel_infr_plus_dict.yaml',
    'unc_ff':  BASE / 'results/uncertainty_scenarios_fixed_brk_fleet_v3/scenario_000/scenario_000_ff_2026-02-14_18-57-14_q_fuel_infr_plus_dict.yaml',
}

s_data = {}
infra_data = {}
for key in ['unc', 'brk', 'unc_ff']:
    print(f"  Parsing {key} s_dict...")
    s_data[key] = parse_s_by_year(S_PATHS[key], prkg_map)
    q = parse_q_infr(Q_PATHS[key])
    infra_data[key] = infra_cost_per_year(q)

# For SOC-aware: compute per year using unconstrained by_od_path
print("  Computing SOC-aware distributions for all years...")
soc_data = {}
for y_enum, y in enumerate(MODELED_YEARS):
    y_idx = y_enum + 1
    unc_year = s_data['unc'].get(y_idx)
    if unc_year is None or unc_year['total'] < 1e-6:
        continue
    soc_fl = compute_soc_aware(unc_year['by_od_path'], breaks_by_path,
                                path_by_id, path_dist_by_id)
    soc_data[y_idx] = soc_fl

# ── Build comparison table ───────────────────────────────────────────
print(f"\n{'='*140}")
print(f"LEVELIZED CHARGING COST COMPARISON — SCENARIO 000 (Go RES)")
print(f"{'='*140}")
print(f"  {'Year':>6s}  |  {'(1) Unc (free fleet)':^24s}  |  {'(2) SOC-aware':^24s}  |  {'(3) Unc (brk fleet)':^24s}  |  {'(4) Breaks-only':^24s}")
print(f"  {'':>6s}  |  {'Elec':>8s} {'Infra':>7s} {'Total':>8s}  |  {'Elec':>8s} {'Infra':>7s} {'Total':>8s}  |  {'Elec':>8s} {'Infra':>7s} {'Total':>8s}  |  {'Elec':>8s} {'Infra':>7s} {'Total':>8s}")
print("  " + "-"*136)

csv_rows = []

for y_enum, y in enumerate(MODELED_YEARS):
    y_idx = y_enum + 1
    fc_idx = y - Y_INIT
    elec_prices = load_elec_prices(fc_idx)

    row = {'year': y}
    cols = []

    for key, label in [('unc', '1_unc'), ('soc', '2_soc'), ('unc_ff', '3_unc_ff'), ('brk', '4_brk')]:
        if key == 'soc':
            # SOC-aware: use analytical distribution + breaks-only infra
            soc_fl = soc_data.get(y_idx, {})
            if not soc_fl:
                cols.append(('', '', ''))
                row[f'{label}_elec'] = ''
                row[f'{label}_infra'] = ''
                row[f'{label}_total'] = ''
                continue
            e_cost, e_kwh, e_avg = weighted_elec(soc_fl, elec_prices)
            infra_cost = infra_data['brk'].get(y_idx, 0)  # Use brk infra
            mwh = sum(soc_fl.values())
            kwh = mwh * 1000
        else:
            year_data = s_data[key].get(y_idx)
            if year_data is None or year_data['total'] < 1e-6:
                cols.append(('', '', ''))
                row[f'{label}_elec'] = ''
                row[f'{label}_infra'] = ''
                row[f'{label}_total'] = ''
                continue
            e_cost, e_kwh, e_avg = weighted_elec(year_data['bev_fl'], elec_prices)
            infra_cost = infra_data[key].get(y_idx, 0)
            kwh = year_data['total'] * 1000

        infra_per_kwh = infra_cost / kwh if kwh > 0 else 0
        total_per_kwh = e_avg + infra_per_kwh

        cols.append((f"{e_avg:.4f}", f"{infra_per_kwh:.4f}", f"{total_per_kwh:.4f}"))
        row[f'{label}_elec'] = round(e_avg, 5)
        row[f'{label}_infra'] = round(infra_per_kwh, 5)
        row[f'{label}_total'] = round(total_per_kwh, 5)

    if any(c[0] != '' for c in cols):
        parts = []
        for c in cols:
            if c[0] == '':
                parts.append(f"  {'—':>8s} {'—':>7s} {'—':>8s}")
            else:
                parts.append(f"  {c[0]:>8s} {c[1]:>7s} {c[2]:>8s}")
        print(f"  {y:6d}  |{'  |'.join(parts)}")
        csv_rows.append(row)

# ── Deltas ───────────────────────────────────────────────────────────
print(f"\n{'='*140}")
print(f"DELTAS vs UNCONSTRAINED (free fleet) — EUR/kWh")
print(f"{'='*140}")
print(f"  {'Year':>6s}  |  {'(2) SOC - (1)':^24s}  |  {'(3) UncFF - (1)':^24s}  |  {'(4) Brk - (1)':^24s}  |  {'(4) Brk - (3)':^24s}")
print(f"  {'':>6s}  |  {'Elec':>8s} {'Infra':>7s} {'Total':>8s}  |  {'Elec':>8s} {'Infra':>7s} {'Total':>8s}  |  {'Elec':>8s} {'Infra':>7s} {'Total':>8s}  |  {'Elec':>8s} {'Infra':>7s} {'Total':>8s}")
print("  " + "-"*110)

for r in csv_rows:
    y = r['year']
    u_e = r.get('1_unc_elec', '')
    u_i = r.get('1_unc_infra', '')
    u_t = r.get('1_unc_total', '')
    if u_e == '' or u_t == '':
        continue

    parts = []
    for ref, comp in [('2_soc', '1_unc'), ('3_unc_ff', '1_unc'), ('4_brk', '1_unc'), ('4_brk', '3_unc_ff')]:
        c_e = r.get(f'{ref}_elec', '')
        c_i = r.get(f'{ref}_infra', '')
        c_t = r.get(f'{ref}_total', '')
        r_e = r.get(f'{comp}_elec', '')
        r_i = r.get(f'{comp}_infra', '')
        r_t = r.get(f'{comp}_total', '')
        if c_e == '' or r_e == '':
            parts.append(f"  {'—':>8s} {'—':>7s} {'—':>8s}")
        else:
            de = c_e - r_e
            di = c_i - r_i
            dt = c_t - r_t
            parts.append(f"  {de:+8.4f} {di:+7.4f} {dt:+8.4f}")
    print(f"  {y:6d}  |{'  |'.join(parts)}")

# Save CSV
csv_path = FIG_DIR / 'levelized_charging_cost_4strategies.csv'
with open(csv_path, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(csv_rows[0].keys()))
    w.writeheader()
    w.writerows(csv_rows)
print(f"\nCSV saved to {csv_path}")
