"""
Compare TOTAL system cost (electricity + infrastructure) between:
  1. System-optimal (from LP results with small battery: bat_low_400_800)
  2. SOC-aware heuristic (charge only when needed at mandatory break stops)

Uses the bat_low_400_800 scenario (400 kWh in 2020 -> 800 in 2035 -> 1000 in 2060).
The heuristic uses generation-specific battery capacity for SOC simulation.
"""
import yaml, pathlib, re, glob
import numpy as np
from collections import defaultdict

BASE = pathlib.Path(__file__).resolve().parent
INPUT_BASE = BASE / 'input_data/battery_sensitivity/bat_low_400_800'
RESULTS_BASE = BASE / 'results/battery_sensitivity/bat_low_400_800'

# ── Constants ────────────────────────────────────────────────────────
Y_INIT = 2020
MODELED_YEARS = list(range(2020, 2064, 4))
TIMESTEP = 4
GAMMA = 0.3
HOURS_PER_YEAR = 8760
DISCOUNT_RATE = 0.05

y_idx_to_year = {i+1: y for i, y in enumerate(MODELED_YEARS)}

# Battery capacity by generation year (from bat_low_400_800 TechVehicle)
with open(INPUT_BASE / 'TechVehicle.yaml') as f:
    tv_data = yaml.safe_load(f)
bev_tv = next(tv for tv in tv_data if tv['technology'] == 1)
GEN_YEARS = list(range(2008, 2008 + len(bev_tv['tank_capacity'])))
BATTERY_BY_GEN = dict(zip(GEN_YEARS, bev_tv['tank_capacity']))
SPEC_CONS_BY_GEN = dict(zip(GEN_YEARS, bev_tv['spec_cons']))

# For heuristic: use modeled-year-specific battery (newest gen available)
def battery_cap_for_year(year):
    """Battery capacity of the newest generation available in a given year."""
    return BATTERY_BY_GEN.get(year, BATTERY_BY_GEN[max(y for y in BATTERY_BY_GEN if y <= year)])

def spec_cons_for_year(year):
    """Specific consumption of newest generation in a given year."""
    return SPEC_CONS_BY_GEN.get(year, SPEC_CONS_BY_GEN[max(y for y in SPEC_CONS_BY_GEN if y <= year)])

# ── Load input data ──────────────────────────────────────────────────
print("Loading input data...")
with open(INPUT_BASE / 'Path.yaml') as f:
    paths = yaml.load(f, Loader=yaml.UnsafeLoader)
with open(INPUT_BASE / 'Odpair.yaml') as f:
    odpairs_raw = yaml.load(f, Loader=yaml.UnsafeLoader)
with open(INPUT_BASE / 'MandatoryBreaks.yaml') as f:
    breaks_data = yaml.safe_load(f)
with open(BASE / 'input_data/fixed_nuts_2/GeographicElement.yaml') as f:
    geo_data = yaml.safe_load(f)
with open(INPUT_BASE / 'FuelCost.yaml') as f:
    fc_data = yaml.safe_load(f)
with open(INPUT_BASE / 'FuelingInfrTypes.yaml') as f:
    fit_data = yaml.safe_load(f)

geo_country = {g['id']: g.get('country', '??') for g in geo_data}
geo_name = {g['id']: g.get('name', f"geo_{g['id']}") for g in geo_data}
geo_lat = {g['id']: g.get('coordinate_lat', 0) for g in geo_data}

# Infrastructure cost parameters
slow_fit = next(f for f in fit_data if f['id'] == 1)
om_costs = slow_fit['om_costs']
network_cost_per_kW = 14.688

def annual_infra_cost_per_kW(year):
    idx = year - Y_INIT
    idx = max(0, min(idx, len(om_costs) - 1))
    return om_costs[idx] + network_cost_per_kW

def discount_factor(year):
    return 1.0 / (1 + DISCOUNT_RATE) ** (year - Y_INIT)

# Electricity prices
elec_price_by_geo_year = {}
for e in fc_data:
    if e['fuel'] == 'electricity':
        elec_price_by_geo_year[(e['location'], e['fueling_infr_type_id'])] = e['cost_per_kWh']

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
    print(f"Loaded prkg ordering: {len(prkg_map)} entries")
else:
    print("WARNING: prkg_ordering_elsevier.txt not found!")

# ── Parse s_dict (system-optimal charging) ────────────────────────────
print("Parsing s_dict (system-optimal charging)...")
s_files = glob.glob(str(RESULTS_BASE / '*_s_dict.yaml'))
if not s_files:
    raise FileNotFoundError(f"No s_dict file in {RESULTS_BASE}")
s_file = s_files[0]
print(f"  Using: {pathlib.Path(s_file).name}")

# Format: (year, (p, r, k, geo_id), tv_id, (fuel, infr_type), gen): value
# Electric charging: fuel=0, infr_type in {1, 2}
tuple_pat = re.compile(
    r'\((\d+),\s*\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\),\s*(\d+),\s*\((\d+),\s*(\d+)\),\s*(\d+)\):\s*([\d.eE+-]+)')

opt_s = defaultdict(lambda: defaultdict(float))
opt_route_year = defaultdict(lambda: defaultdict(float))
n_parsed = 0

with open(s_file) as f:
    for line in f:
        m = tuple_pat.match(line.strip())
        if not m: continue
        year = int(m.group(1))
        p, od_id, path_id, geo_id = int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5))
        tv_id = int(m.group(6))
        fuel, infr_type = int(m.group(7)), int(m.group(8))
        val = float(m.group(10))
        if val < 1e-6: continue
        # Only electric charging (fuel=0, infr_type=1 slow or 2 fast)
        if fuel != 0 or infr_type not in {1, 2}: continue
        opt_s[geo_id][year] += val
        opt_route_year[(od_id, path_id)][year] += val
        n_parsed += 1

print(f"  Parsed {n_parsed} electric charging entries across {len(opt_s)} nodes")

# ── Parse q_fuel_infr_plus ────────────────────────────────────────────
print("Parsing q_fuel_infr_plus...")
ci3_pat = re.compile(r'CartesianIndex\((\d+),\s*(\d+),\s*(\d+)\):\s*([\d.eE+-]+)')
infra_files = glob.glob(str(RESULTS_BASE / '*_q_fuel_infr_plus_dict.yaml'))
infra_file = infra_files[0]
print(f"  Using: {pathlib.Path(infra_file).name}")

opt_infra = defaultdict(lambda: defaultdict(float))
with open(infra_file) as f:
    for line in f:
        m = ci3_pat.match(line.strip())
        if not m: continue
        y_idx, fl_idx, geo_id = int(m.group(1)), int(m.group(2)), int(m.group(3))
        val = float(m.group(4))
        if val < 1e-6: continue
        # fl=1 slow electric, fl=2 fast electric, fl=3 diesel — only electric
        if fl_idx not in {1, 2}: continue
        year = y_idx_to_year.get(y_idx)
        if year: opt_infra[geo_id][year] += val

# ── SOC-aware heuristic ──────────────────────────────────────────────
print("Computing SOC-aware heuristic charging pattern...")

def compute_soc_charging(od_id, path_id, total_energy_mwh, year):
    """SOC-aware lazy charging at break stops with year-specific battery.

    Energy conservation: distributes exactly total_energy_mwh across break nodes.
    First simulates SOC to determine charging pattern (which breaks need charging),
    then scales so total charged == total_energy_mwh.
    """
    pid = od_to_path.get(od_id, path_id)
    seq = path_by_id.get(pid, [])
    dist = path_dist_by_id.get(pid, [])
    break_set = set(breaks_by_path.get(pid, []))
    if not seq or not dist or len(seq) != len(dist): return {}

    break_indices = [i for i, g in enumerate(seq) if g in break_set]
    if not break_indices:
        # No breaks — distribute evenly across all path nodes
        n = len(seq)
        return {seq[i]: total_energy_mwh / n for i in range(n)} if n > 0 else {}

    cum_dist = np.cumsum(dist)
    total_dist = cum_dist[-1] if len(cum_dist) > 0 else 0
    if total_dist < 1e-3: return {}

    bat_cap = battery_cap_for_year(year)
    sc = spec_cons_for_year(year)

    # Simulate one trip with SOC tracking to determine charging pattern
    soc = bat_cap * 0.5  # 50% initial SOC
    charges = {}  # geo_id -> kWh charged in one trip

    for i, bi in enumerate(break_indices):
        prev_dist = cum_dist[break_indices[i-1]] if i > 0 else 0
        energy_consumed = sc * (cum_dist[bi] - prev_dist)
        soc -= energy_consumed

        # Look ahead: how much energy to next break (or destination)?
        if i < len(break_indices) - 1:
            dist_to_next = cum_dist[break_indices[i+1]] - cum_dist[bi]
        else:
            dist_to_next = total_dist - cum_dist[bi]

        energy_to_next = sc * dist_to_next
        # Charge if SOC won't make it to next stop (with 10% margin)
        if soc < energy_to_next + bat_cap * 0.1:
            charge = min(bat_cap - soc, energy_to_next - soc + bat_cap * 0.1)
            charge = max(0, min(charge, bat_cap - soc))
            if charge > 0:
                charges[seq[bi]] = charges.get(seq[bi], 0) + charge
                soc += charge

    # If heuristic found no charging needed (shouldn't happen), distribute evenly
    if not charges:
        for bi in break_indices:
            charges[seq[bi]] = 1.0  # equal weight

    # Scale to conserve total energy: distribute total_energy_mwh proportionally
    total_raw = sum(charges.values())
    if total_raw < 1e-9:
        return {}
    scale = total_energy_mwh / total_raw
    # Note: scale uses total_energy_mwh directly (already in MWh from route)
    # The raw charges are in kWh for one trip, but we just need proportions
    return {geo_id: kwh * scale for geo_id, kwh in charges.items()}

heur_s = defaultdict(lambda: defaultdict(float))
for (od_id, path_id), year_dict in opt_route_year.items():
    for year, total_e in year_dict.items():
        if total_e < 1e-6: continue
        geo_charges = compute_soc_charging(od_id, path_id, total_e, year)
        for geo_id, mwh in geo_charges.items():
            heur_s[geo_id][year] += mwh

# ── Compute costs ────────────────────────────────────────────────────
print("\nComputing total system costs...")
print("="*130)

factor = 1000.0 / (GAMMA * HOURS_PER_YEAR)
all_geos = set(list(opt_s.keys()) + list(heur_s.keys()))

opt_elec_cost = {}; opt_infra_cost = {}
heur_elec_cost = {}; heur_infra_cost = {}
opt_cum_infra = defaultdict(float)
heur_cum_infra = defaultdict(float)

for year in MODELED_YEARS:
    y_offset = year - Y_INIT
    df = discount_factor(year)
    infra_annual = annual_infra_cost_per_kW(year)

    # System-optimal
    e_cost_opt = 0
    for geo_id in all_geos:
        s_mwh = opt_s[geo_id].get(year, 0)
        if s_mwh > 0:
            price = 0
            if (geo_id, 1) in elec_price_by_geo_year:
                prices = elec_price_by_geo_year[(geo_id, 1)]
                if y_offset < len(prices):
                    price = prices[y_offset]
            e_cost_opt += s_mwh * 1000 * price
    opt_elec_cost[year] = e_cost_opt * df * TIMESTEP

    i_cost_opt = 0
    for geo_id in all_geos:
        opt_cum_infra[geo_id] += opt_infra[geo_id].get(year, 0)
        i_cost_opt += opt_cum_infra[geo_id] * infra_annual
    opt_infra_cost[year] = i_cost_opt * df * TIMESTEP

    # Heuristic
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

    i_cost_heur = 0
    for geo_id in all_geos:
        required_kw = heur_s[geo_id].get(year, 0) * factor
        if required_kw > heur_cum_infra[geo_id]:
            heur_cum_infra[geo_id] = required_kw
        i_cost_heur += heur_cum_infra[geo_id] * infra_annual
    heur_infra_cost[year] = i_cost_heur * df * TIMESTEP

# ── Print comparison ──────────────────────────────────────────────────
print(f"\n{'Year':>6s}  {'Opt Elec':>12s}  {'Opt Infra':>12s}  {'Opt Total':>12s}  {'Heur Elec':>12s}  {'Heur Infra':>12s}  {'Heur Total':>12s}  {'Delta':>10s}  {'%':>7s}")
print("-"*105)

total_opt_e = total_opt_i = total_heur_e = total_heur_i = 0
for year in MODELED_YEARS:
    oe = opt_elec_cost[year] / 1e6
    oi = opt_infra_cost[year] / 1e6
    he = heur_elec_cost[year] / 1e6
    hi = heur_infra_cost[year] / 1e6
    ot = oe + oi; ht = he + hi
    delta = ht - ot
    dpct = delta / ot * 100 if ot > 0 else 0
    total_opt_e += oe; total_opt_i += oi
    total_heur_e += he; total_heur_i += hi
    print(f"{year:>6d}  {oe:>11.2f}  {oi:>11.2f}  {ot:>11.2f}  {he:>11.2f}  {hi:>11.2f}  {ht:>11.2f}  {delta:>+9.2f}  {dpct:>+6.1f}%")

print("-"*105)
total_ot = total_opt_e + total_opt_i
total_ht = total_heur_e + total_heur_i
total_delta = total_ht - total_ot
total_dpct = total_delta / total_ot * 100 if total_ot > 0 else 0
print(f"{'TOTAL':>6s}  {total_opt_e:>11.2f}  {total_opt_i:>11.2f}  {total_ot:>11.2f}  {total_heur_e:>11.2f}  {total_heur_i:>11.2f}  {total_ht:>11.2f}  {total_delta:>+9.2f}  {total_dpct:>+6.1f}%")

# ── Infrastructure by country at 2040 ────────────────────────────────
print(f"\n{'='*80}")
print("INFRASTRUCTURE BY COUNTRY (cumulative kW at 2040)")
print(f"{'='*80}")

opt_country_2040 = defaultdict(float)
heur_country_2040 = defaultdict(float)
for geo_id in all_geos:
    c = geo_country.get(geo_id, '??')
    opt_country_2040[c] += sum(opt_infra[geo_id].get(y, 0) for y in MODELED_YEARS if y <= 2040)
    max_kw = 0
    for y in MODELED_YEARS:
        if y > 2040: break
        req = heur_s[geo_id].get(y, 0) * factor
        if req > max_kw: max_kw = req
    heur_country_2040[c] += max_kw

countries = sorted(set(list(opt_country_2040.keys()) + list(heur_country_2040.keys())),
                   key=lambda c: opt_country_2040[c], reverse=True)
print(f"  {'Country':>8s}  {'Opt (MW)':>10s}  {'Heur (MW)':>10s}  {'Delta(MW)':>10s}  {'Delta%':>8s}")
print("  " + "-"*55)
for c in countries:
    o = opt_country_2040[c] / 1000
    h = heur_country_2040[c] / 1000
    d = h - o
    dp = d / o * 100 if o > 0.01 else 0
    print(f"  {c:>8s}  {o:>10.1f}  {h:>10.1f}  {d:>+10.1f}  {dp:>+7.1f}%")

# ── Charging distribution by latitude ────────────────────────────────
print(f"\n{'='*80}")
print("CHARGING DISTRIBUTION BY LATITUDE BAND (2040, MWh)")
print(f"{'='*80}")

lat_bands = [(42, 44, "IT South"), (44, 46, "IT North"), (46, 48, "AT/CH"),
             (48, 50, "DE South"), (50, 52, "DE North"), (52, 56, "DK/SE South"),
             (56, 60, "SE Mid"), (60, 64, "SE/NO North"), (64, 72, "Scandinavia")]

print(f"  {'Band':>20s}  {'Opt (MWh)':>12s}  {'Heur (MWh)':>12s}  {'Delta':>10s}  {'Opt%':>7s}  {'Heur%':>7s}")
print("  " + "-"*75)

opt_total_2040 = sum(opt_s[g].get(2040, 0) for g in all_geos)
heur_total_2040 = sum(heur_s[g].get(2040, 0) for g in all_geos)

for lat_lo, lat_hi, label in lat_bands:
    opt_band = sum(opt_s[g].get(2040, 0) for g in all_geos if lat_lo <= geo_lat.get(g, 0) < lat_hi)
    heur_band = sum(heur_s[g].get(2040, 0) for g in all_geos if lat_lo <= geo_lat.get(g, 0) < lat_hi)
    delta = heur_band - opt_band
    opt_pct = opt_band / opt_total_2040 * 100 if opt_total_2040 > 0 else 0
    heur_pct = heur_band / heur_total_2040 * 100 if heur_total_2040 > 0 else 0
    print(f"  {label:>20s}  {opt_band:>12.0f}  {heur_band:>12.0f}  {delta:>+10.0f}  {opt_pct:>6.1f}%  {heur_pct:>6.1f}%")

# ── Summary ───────────────────────────────────────────────────────────
print(f"\n{'='*80}")
print("SUMMARY (small battery: 400 -> 800 -> 1000 kWh)")
print(f"{'='*80}")
print(f"  System-optimal total cost (discounted): {total_ot:.2f} MEUR")
print(f"    - Electricity: {total_opt_e:.2f} MEUR ({total_opt_e/total_ot*100:.1f}%)")
print(f"    - Infrastructure: {total_opt_i:.2f} MEUR ({total_opt_i/total_ot*100:.1f}%)")
print()
print(f"  Heuristic total cost (discounted): {total_ht:.2f} MEUR")
print(f"    - Electricity: {total_heur_e:.2f} MEUR ({total_heur_e/total_ht*100:.1f}%)")
print(f"    - Infrastructure: {total_heur_i:.2f} MEUR ({total_heur_i/total_ht*100:.1f}%)")
print()
print(f"  Heuristic premium: {total_delta:+.2f} MEUR ({total_dpct:+.1f}%)")
print(f"  Electricity saving (opt vs heur): {total_opt_e - total_heur_e:+.2f} MEUR")
print(f"  Infrastructure penalty (heur vs opt): {total_heur_i - total_opt_i:+.2f} MEUR")
print()
print(f"  Battery capacity at key years:")
for y in [2020, 2028, 2032, 2040, 2048, 2060]:
    print(f"    {y}: {battery_cap_for_year(y):.0f} kWh, spec_cons={spec_cons_for_year(y):.3f} kWh/km")
