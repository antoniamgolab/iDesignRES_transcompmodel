"""
Analyze infrastructure deployment vs charging demand by country.
Shows whether the optimizer spreads infrastructure across nodes (even expensive ones)
rather than concentrating at the cheapest nodes.
"""
import yaml, pathlib, re
import numpy as np
from collections import defaultdict

BASE = pathlib.Path(__file__).resolve().parent
INPUT_BASE = BASE / 'input_data/uncertainty_scenarios'

# ── Load geographic data ──────────────────────────────────────────────
with open(BASE / 'input_data/fixed_nuts_2/GeographicElement.yaml') as f:
    geo_data = yaml.safe_load(f)

geo_country = {g['id']: g.get('country', '??') for g in geo_data}
geo_name = {g['id']: g.get('name', f"geo_{g['id']}") for g in geo_data}
geo_lat = {g['id']: g.get('coordinate_lat', 0) for g in geo_data}

# ── Load electricity prices ──────────────────────────────────────────
scenario_id = 'scenario_000'
inp = INPUT_BASE / scenario_id
Y_INIT = 2020
TARGET_YEAR = 2032
fc_idx = TARGET_YEAR - Y_INIT

with open(inp / 'FuelCost.yaml') as f:
    fc = yaml.safe_load(f)

elec_prices = {}
for e in fc:
    if e['fuel'] == 'electricity':
        geo_id = e['location']
        fl_id = e['fueling_infr_type_id']
        elec_prices[(geo_id, fl_id)] = e['cost_per_kWh'][fc_idx]

# Average elec price per country
country_prices = defaultdict(list)
for (geo_id, fl_id), price in elec_prices.items():
    if fl_id == 1:  # slow charging
        c = geo_country.get(geo_id, '??')
        country_prices[c].append(price)

print("="*80)
print("ELECTRICITY PRICES BY COUNTRY (slow charging, 2032)")
print("="*80)
for c in sorted(country_prices.keys()):
    prices = country_prices[c]
    print(f"  {c}: {np.mean(prices)*100:.2f} ct/kWh (n={len(prices)} nodes)")

# ── Modeled years mapping ────────────────────────────────────────────
MODELED_YEARS = list(range(2020, 2064, 4))
y_idx_to_year = {i+1: y for i, y in enumerate(MODELED_YEARS)}

# ── Load infrastructure deployment ───────────────────────────────────
print("\n" + "="*80)
print("INFRASTRUCTURE DEPLOYMENT BY COUNTRY AND YEAR (kW)")
print("="*80)

results_base = BASE / 'results/uncertainty_scenarios_v2/scenario_000'
infra_file = results_base / 'scenario_000_cs_2026-02-14_18-25-42_q_fuel_infr_plus_dict.yaml'

ci_pat = re.compile(r'CartesianIndex\((\d+),\s*(\d+),\s*(\d+)\):\s*([\d.eE+-]+)')

infra_by_country_year = defaultdict(lambda: defaultdict(float))
infra_by_geo_year = defaultdict(lambda: defaultdict(float))

with open(infra_file) as f:
    for line in f:
        m = ci_pat.match(line.strip())
        if not m: continue
        y_idx = int(m.group(1))
        fl_idx = int(m.group(2))
        geo_id = int(m.group(3))
        val = float(m.group(4))

        year = y_idx_to_year.get(y_idx)
        if year is None: continue

        country = geo_country.get(geo_id, '??')
        infra_by_country_year[country][year] += val
        infra_by_geo_year[geo_id][year] += val

# Print by country and year
countries = sorted(infra_by_country_year.keys())
print(f"  {'Country':>8s}", end="")
for y in MODELED_YEARS:
    print(f"  {y:>10d}", end="")
print(f"  {'TOTAL':>12s}")
print("  " + "-"*(8 + 12*len(MODELED_YEARS) + 14))

for c in countries:
    print(f"  {c:>8s}", end="")
    total = 0
    for y in MODELED_YEARS:
        v = infra_by_country_year[c][y]
        total += v
        print(f"  {v:>10.0f}", end="")
    print(f"  {total:>12.0f}")

# Grand total
print(f"  {'TOTAL':>8s}", end="")
grand = 0
for y in MODELED_YEARS:
    ysum = sum(infra_by_country_year[c][y] for c in countries)
    grand += ysum
    print(f"  {ysum:>10.0f}", end="")
print(f"  {grand:>12.0f}")

# ── Load s_dict (charging energy) for comparison ──────────────────────
print("\n" + "="*80)
print("CHARGING ENERGY BY COUNTRY AND YEAR (from s_dict)")
print("="*80)

s_file = results_base / 'scenario_000_cs_2026-02-14_18-25-42_s_dict.yaml'

# s_dict: CartesianIndex(y_idx, prkg_idx, tv_id, fl_idx, gen_idx): value
# Need prkg_ordering to map prkg_idx to geo_id
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
            prkg_map[idx] = tuple(vals)  # (p, r, k, g)

ci5_pat = re.compile(
    r'CartesianIndex\((\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\):\s*([\d.eE+-]+)')

charging_by_country_year = defaultdict(lambda: defaultdict(float))

print("  Loading s_dict (this may take a moment)...")
with open(s_file) as f:
    for line in f:
        m = ci5_pat.match(line.strip())
        if not m: continue
        y_idx = int(m.group(1))
        prkg_idx = int(m.group(2))
        fl_idx = int(m.group(4))
        val = float(m.group(6))

        if val < 1e-6: continue
        if fl_idx not in {1, 2}: continue  # only electricity

        prkg = prkg_map.get(prkg_idx)
        if prkg is None: continue
        _, _, _, geo_id = prkg

        year = y_idx_to_year.get(y_idx)
        if year is None: continue

        country = geo_country.get(geo_id, '??')
        charging_by_country_year[country][year] += val  # MWh

# Print charging by country
print(f"\n  {'Country':>8s}", end="")
for y in MODELED_YEARS:
    print(f"  {y:>10d}", end="")
print(f"  {'TOTAL':>12s}")
print("  " + "-"*(8 + 12*len(MODELED_YEARS) + 14))

for c in countries:
    print(f"  {c:>8s}", end="")
    total = 0
    for y in MODELED_YEARS:
        v = charging_by_country_year[c][y]
        total += v
        print(f"  {v:>10.1f}", end="")
    print(f"  {total:>12.1f}")

# ── Compare: Infrastructure share vs Charging share ──────────────────
print("\n" + "="*80)
print("INFRASTRUCTURE SHARE vs CHARGING SHARE vs PRICE (by country)")
print("="*80)
print("  If optimizer minimizes electricity cost alone, cheap countries get all charging.")
print("  If infrastructure cost matters, charging spreads to reduce peak infra at any node.")
print()

for target_y in [2032, 2040, 2048]:
    print(f"\n  --- Year {target_y} ---")
    total_infra = sum(infra_by_country_year[c][target_y] for c in countries)
    total_charge = sum(charging_by_country_year[c][target_y] for c in countries)

    # Cumulative infra up to target_y
    cum_infra = defaultdict(float)
    for c in countries:
        for y in MODELED_YEARS:
            if y <= target_y:
                cum_infra[c] += infra_by_country_year[c][y]
    total_cum_infra = sum(cum_infra.values())

    print(f"  {'Country':>8s}  {'Price(ct)':>10s}  {'Infra(kW)':>12s}  {'Infra%':>8s}  {'CumInfra%':>10s}  {'Charge(MWh)':>12s}  {'Charge%':>9s}  {'Charge/Infra':>13s}")
    print("  " + "-"*100)

    for c in sorted(countries, key=lambda x: np.mean(country_prices.get(x, [0]))):
        infra_y = infra_by_country_year[c][target_y]
        charge_y = charging_by_country_year[c][target_y]
        price = np.mean(country_prices.get(c, [0])) * 100

        infra_pct = infra_y / total_infra * 100 if total_infra > 0 else 0
        cum_pct = cum_infra[c] / total_cum_infra * 100 if total_cum_infra > 0 else 0
        charge_pct = charge_y / total_charge * 100 if total_charge > 0 else 0
        ratio = charge_y / cum_infra[c] if cum_infra[c] > 0 else 0

        print(f"  {c:>8s}  {price:>9.2f}  {infra_y:>12.0f}  {infra_pct:>7.1f}%  {cum_pct:>9.1f}%  {charge_y:>12.1f}  {charge_pct:>8.1f}%  {ratio:>12.2f}")

# ── Top nodes by infrastructure investment ────────────────────────────
print("\n" + "="*80)
print("TOP 15 NODES BY CUMULATIVE INFRASTRUCTURE (up to 2048)")
print("="*80)

cum_infra_geo = {}
for geo_id in infra_by_geo_year:
    cum = sum(infra_by_geo_year[geo_id][y] for y in MODELED_YEARS if y <= 2048)
    cum_infra_geo[geo_id] = cum

top_nodes = sorted(cum_infra_geo.items(), key=lambda x: x[1], reverse=True)[:15]
print(f"  {'GeoID':>6s}  {'Country':>8s}  {'Name':>25s}  {'Lat':>6s}  {'CumInfra(kW)':>13s}  {'Price(ct)':>10s}")
print("  " + "-"*80)
for geo_id, cum in top_nodes:
    c = geo_country.get(geo_id, '??')
    name = geo_name.get(geo_id, '??')
    lat = geo_lat.get(geo_id, 0)
    price = elec_prices.get((geo_id, 1), 0) * 100
    print(f"  {geo_id:>6d}  {c:>8s}  {name:>25s}  {lat:>6.1f}  {cum:>13.0f}  {price:>9.2f}")

# ── Charge/Infrastructure ratio by node (reveals where infra is "saturated") ──
print("\n" + "="*80)
print("NODES WITH HIGHEST CHARGING-TO-INFRASTRUCTURE RATIO (potential bottlenecks)")
print("  High ratio = lots of charging relative to installed capacity -> constraint likely binding")
print("="*80)

# Load charging per geo_id
charging_by_geo_2032 = defaultdict(float)
with open(s_file) as f:
    for line in f:
        m = ci5_pat.match(line.strip())
        if not m: continue
        y_idx = int(m.group(1))
        if y_idx != 4: continue  # 2032
        prkg_idx = int(m.group(2))
        fl_idx = int(m.group(4))
        val = float(m.group(6))
        if val < 1e-6 or fl_idx not in {1, 2}: continue
        prkg = prkg_map.get(prkg_idx)
        if prkg is None: continue
        _, _, _, geo_id = prkg
        charging_by_geo_2032[geo_id] += val

# Compute ratio
ratios = []
for geo_id in charging_by_geo_2032:
    cum = sum(infra_by_geo_year[geo_id][y] for y in MODELED_YEARS if y <= 2032)
    charge = charging_by_geo_2032[geo_id]
    if cum > 10:  # only nodes with meaningful infra
        ratios.append((geo_id, charge, cum, charge/cum))

ratios.sort(key=lambda x: x[3], reverse=True)
print(f"\n  Year 2032 — Top 15 nodes by MWh/kW ratio:")
print(f"  {'GeoID':>6s}  {'Country':>8s}  {'Name':>25s}  {'Charge(MWh)':>12s}  {'CumInfra(kW)':>13s}  {'Ratio':>8s}  {'Price(ct)':>10s}")
print("  " + "-"*95)
for geo_id, charge, cum, ratio in ratios[:15]:
    c = geo_country.get(geo_id, '??')
    name = geo_name.get(geo_id, '??')
    price = elec_prices.get((geo_id, 1), 0) * 100
    print(f"  {geo_id:>6d}  {c:>8s}  {name:>25s}  {charge:>12.1f}  {cum:>13.0f}  {ratio:>8.2f}  {price:>9.2f}")

# ── AT border region analysis ─────────────────────────────────────────
print("\n" + "="*80)
print("AUSTRIAN NODES — INFRASTRUCTURE vs CHARGING DETAIL")
print("="*80)

at_geos = [g for g in geo_data if g.get('country') == 'AT']
print(f"  {'GeoID':>6s}  {'Name':>25s}  {'Lat':>6s}  {'CumInfra2032':>13s}  {'CumInfra2040':>13s}  {'Charge2032':>12s}  {'Price(ct)':>10s}")
print("  " + "-"*100)
for g in sorted(at_geos, key=lambda x: x.get('coordinate_lat', 0), reverse=True):
    gid = g['id']
    cum32 = sum(infra_by_geo_year[gid][y] for y in MODELED_YEARS if y <= 2032)
    cum40 = sum(infra_by_geo_year[gid][y] for y in MODELED_YEARS if y <= 2040)
    charge32 = charging_by_geo_2032.get(gid, 0)
    price = elec_prices.get((gid, 1), 0) * 100
    name = g.get('name', '??')
    lat = g.get('coordinate_lat', 0)
    print(f"  {gid:>6d}  {name:>25s}  {lat:>6.1f}  {cum32:>13.0f}  {cum40:>13.0f}  {charge32:>12.1f}  {price:>9.2f}")
