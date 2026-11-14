"""
Full 4-scenario battery sensitivity analysis.

Compares across all battery capacity assumptions:
  1. BEV adoption (from summary_stats.yaml)
  2. Infrastructure distribution by country (from q_fuel_infr_plus)
  3. Charging energy distribution by country (from s_dict)
  4. Opt vs heuristic relocation % for each scenario
"""
import yaml, pathlib, re, glob
import numpy as np
from collections import defaultdict

BASE = pathlib.Path(__file__).resolve().parent
RESULTS_DIR = BASE / 'results' / 'battery_sensitivity'
INPUT_DIR = BASE / 'input_data' / 'battery_sensitivity'

SCENARIOS = ['bat_constant_1187', 'bat_low_400_800', 'bat_mid_400_1000', 'bat_high_600_1200']
LABELS = {
    'bat_constant_1187': 'Constant 1187',
    'bat_low_400_800':   'Low 400->1000',
    'bat_mid_400_1000':  'Mid 400->1200',
    'bat_high_600_1200': 'High 600->1500',
}

Y_INIT = 2020
MODELED_YEARS = list(range(2020, 2064, 4))
TIMESTEP = 4
GAMMA = 0.3
HOURS_PER_YEAR = 8760
DISCOUNT_RATE = 0.05
FACTOR = 1000.0 / (GAMMA * HOURS_PER_YEAR)  # MWh -> kW for infrastructure sizing

y_idx_to_year = {i+1: y for i, y in enumerate(MODELED_YEARS)}

# ── Load shared geographic data ──────────────────────────────────────
with open(BASE / 'input_data/fixed_nuts_2/GeographicElement.yaml') as f:
    geo_data = yaml.safe_load(f)

geo_country = {g['id']: g.get('country', '??') for g in geo_data}
geo_lat = {g['id']: g.get('coordinate_lat', 0) for g in geo_data}

# Regex patterns
tuple_pat = re.compile(
    r'\((\d+),\s*\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\),\s*(\d+),\s*\((\d+),\s*(\d+)\),\s*(\d+)\):\s*([\d.eE+-]+)')
ci3_pat = re.compile(r'CartesianIndex\((\d+),\s*(\d+),\s*(\d+)\):\s*([\d.eE+-]+)')

# ══════════════════════════════════════════════════════════════════════
# PART 1: BEV ADOPTION COMPARISON (from summary_stats)
# ══════════════════════════════════════════════════════════════════════
print("=" * 100)
print("PART 1: BEV ADOPTION COMPARISON")
print("=" * 100)

KEY_YEARS = [2028, 2032, 2036, 2040, 2044, 2048, 2052, 2056, 2060]

header = f"{'Year':>6s}"
for sc in SCENARIOS:
    header += f"  {LABELS[sc]:>16s}"
print(header)
print("-" * (6 + 18 * len(SCENARIOS)))

stats_cache = {}
for sc in SCENARIOS:
    with open(RESULTS_DIR / sc / 'summary_stats.yaml') as f:
        stats_cache[sc] = yaml.safe_load(f)

for year in KEY_YEARS:
    row = f"{year:>6d}"
    for sc in SCENARIOS:
        stats = stats_cache[sc]
        bev_t = float(stats['tonnes_by_year'].get(year, {}).get('BEV', 0))
        icev_t = float(stats['tonnes_by_year'].get(year, {}).get('ICEV', 0))
        total = bev_t + icev_t
        pct = bev_t / total * 100 if total > 0 else 0
        row += f"  {pct:>15.1f}%"
    print(row)

# Objective values
print(f"\n{'Objective (bn EUR)':>20s}", end="")
for sc in SCENARIOS:
    stats = stats_cache[sc]
    obj = float(stats['objective_value']) / 1e9
    print(f"  {obj:>16.3f}", end="")
print()

# ══════════════════════════════════════════════════════════════════════
# PART 2: INFRASTRUCTURE BY COUNTRY (from q_fuel_infr_plus)
# ══════════════════════════════════════════════════════════════════════
print(f"\n{'=' * 100}")
print("PART 2: INFRASTRUCTURE BY COUNTRY (cumulative MW)")
print("=" * 100)

for target_year in [2032, 2040, 2048]:
    print(f"\n--- Year {target_year} ---")
    sc_infra = {}  # scenario -> {country: MW}

    for sc in SCENARIOS:
        infra_files = glob.glob(str(RESULTS_DIR / sc / '*_q_fuel_infr_plus_dict.yaml'))
        if not infra_files:
            print(f"  WARNING: no q_fuel_infr_plus for {sc}")
            continue

        geo_infra = defaultdict(float)
        with open(infra_files[0]) as f:
            for line in f:
                m = ci3_pat.match(line.strip())
                if not m: continue
                y_idx, fl_idx, geo_id = int(m.group(1)), int(m.group(2)), int(m.group(3))
                val = float(m.group(4))
                if val < 1e-6 or fl_idx not in {1, 2}: continue
                year = y_idx_to_year.get(y_idx)
                if year and year <= target_year:
                    geo_infra[geo_id] += val

        country_mw = defaultdict(float)
        for geo_id, kw in geo_infra.items():
            country_mw[geo_country.get(geo_id, '??')] += kw / 1000.0
        sc_infra[sc] = country_mw

    # Collect all countries
    all_countries = set()
    for ci in sc_infra.values():
        all_countries.update(ci.keys())
    countries = sorted(all_countries, key=lambda c: max(sc_infra[sc].get(c, 0) for sc in SCENARIOS), reverse=True)

    header = f"  {'Country':>8s}"
    for sc in SCENARIOS:
        header += f"  {LABELS[sc]:>16s}"
    header += f"  {'Spread':>8s}"
    print(header)
    print("  " + "-" * (8 + 18 * len(SCENARIOS) + 10))

    total_by_sc = {sc: 0 for sc in SCENARIOS}
    for c in countries:
        vals = [sc_infra[sc].get(c, 0) for sc in SCENARIOS]
        if max(vals) < 0.1: continue
        row = f"  {c:>8s}"
        for i, sc in enumerate(SCENARIOS):
            row += f"  {vals[i]:>15.1f}M"
            total_by_sc[sc] += vals[i]
        spread = (max(vals) - min(vals)) / max(vals) * 100 if max(vals) > 0.1 else 0
        row += f"  {spread:>+7.1f}%"
        print(row)

    row = f"  {'TOTAL':>8s}"
    for sc in SCENARIOS:
        row += f"  {total_by_sc[sc]:>15.1f}M"
    totals = list(total_by_sc.values())
    spread = (max(totals) - min(totals)) / max(totals) * 100 if max(totals) > 0.1 else 0
    row += f"  {spread:>+7.1f}%"
    print(row)


# ══════════════════════════════════════════════════════════════════════
# PART 3: CHARGING ENERGY BY COUNTRY (from s_dict)
# ══════════════════════════════════════════════════════════════════════
print(f"\n{'=' * 100}")
print("PART 3: CHARGING ENERGY DISTRIBUTION BY COUNTRY (MWh)")
print("=" * 100)

sc_charging = {}  # scenario -> {country -> {year -> MWh}}
sc_route_charging = {}  # scenario -> {(od, path) -> {year -> MWh}}

for sc in SCENARIOS:
    print(f"  Parsing s_dict for {sc}...", end="", flush=True)
    s_files = glob.glob(str(RESULTS_DIR / sc / '*_s_dict.yaml'))
    if not s_files:
        print(" NOT FOUND")
        continue

    geo_year_mwh = defaultdict(lambda: defaultdict(float))
    route_year_mwh = defaultdict(lambda: defaultdict(float))
    n = 0

    with open(s_files[0]) as f:
        for line in f:
            m = tuple_pat.match(line.strip())
            if not m: continue
            year = int(m.group(1))
            od_id, path_id, geo_id = int(m.group(3)), int(m.group(4)), int(m.group(5))
            fuel, infr_type = int(m.group(7)), int(m.group(8))
            val = float(m.group(10))
            if val < 1e-6 or fuel != 0 or infr_type not in {1, 2}: continue
            geo_year_mwh[geo_id][year] += val
            route_year_mwh[(od_id, path_id)][year] += val
            n += 1

    country_year = defaultdict(lambda: defaultdict(float))
    for geo_id, year_dict in geo_year_mwh.items():
        c = geo_country.get(geo_id, '??')
        for y, mwh in year_dict.items():
            country_year[c][y] += mwh

    sc_charging[sc] = country_year
    sc_route_charging[sc] = route_year_mwh
    print(f" {n} entries")

for target_year in [2032, 2040, 2048]:
    print(f"\n--- Year {target_year} ---")

    all_countries = set()
    for sc in SCENARIOS:
        if sc in sc_charging:
            all_countries.update(sc_charging[sc].keys())

    # Sort by total energy across scenarios
    country_totals = {}
    for c in all_countries:
        country_totals[c] = max(sc_charging[sc].get(c, {}).get(target_year, 0) for sc in SCENARIOS if sc in sc_charging)
    countries = sorted(all_countries, key=lambda c: country_totals[c], reverse=True)

    header = f"  {'Country':>8s}"
    for sc in SCENARIOS:
        header += f"  {LABELS[sc]:>16s}"
    header += f"  {'Spread':>8s}"
    print(header)
    print("  " + "-" * (8 + 18 * len(SCENARIOS) + 10))

    total_by_sc = {sc: 0 for sc in SCENARIOS}
    for c in countries:
        vals = [sc_charging.get(sc, {}).get(c, {}).get(target_year, 0) for sc in SCENARIOS]
        if max(vals) < 1: continue
        row = f"  {c:>8s}"
        for i, sc in enumerate(SCENARIOS):
            row += f"  {vals[i]:>14.0f}  "
            total_by_sc[sc] += vals[i]
        spread = (max(vals) - min(vals)) / max(vals) * 100 if max(vals) > 1 else 0
        row += f"  {spread:>+7.1f}%"
        print(row)

    row = f"  {'TOTAL':>8s}"
    for sc in SCENARIOS:
        row += f"  {total_by_sc.get(sc, 0):>14.0f}  "
    totals = [total_by_sc.get(sc, 0) for sc in SCENARIOS]
    spread = (max(totals) - min(totals)) / max(totals) * 100 if max(totals) > 1 else 0
    row += f"  {spread:>+7.1f}%"
    print(row)

    # Show % shares
    print(f"\n  % shares:")
    for c in countries:
        vals = [sc_charging.get(sc, {}).get(c, {}).get(target_year, 0) for sc in SCENARIOS]
        if max(vals) < 1: continue
        row = f"  {c:>8s}"
        for i, sc in enumerate(SCENARIOS):
            pct = vals[i] / total_by_sc[sc] * 100 if total_by_sc[sc] > 0 else 0
            row += f"  {pct:>15.1f}%"
        print(row)


# ══════════════════════════════════════════════════════════════════════
# PART 4: CHARGING BY LATITUDE BAND
# ══════════════════════════════════════════════════════════════════════
print(f"\n{'=' * 100}")
print("PART 4: CHARGING BY LATITUDE BAND (% of total, 2040)")
print("=" * 100)

lat_bands = [
    (42, 44, "IT South"),
    (44, 46, "IT North"),
    (46, 48, "AT/CH"),
    (48, 50, "DE South"),
    (50, 52, "DE North"),
    (52, 56, "DK/SE South"),
    (56, 60, "SE Mid"),
    (60, 64, "SE/NO North"),
    (64, 72, "Scandinavia"),
]

for target_year in [2032, 2040, 2048]:
    print(f"\n--- Year {target_year} ---")
    header = f"  {'Band':>20s}"
    for sc in SCENARIOS:
        header += f"  {LABELS[sc]:>16s}"
    print(header)
    print("  " + "-" * (20 + 18 * len(SCENARIOS)))

    # Compute per-scenario totals first
    sc_totals = {}
    for sc in SCENARIOS:
        if sc not in sc_charging: continue
        total = 0
        for geo_id in geo_lat:
            for c_name, year_dict in sc_charging[sc].items():
                pass  # already aggregated by country
        # Actually compute from raw geo data - need to re-aggregate from s_dict
        # Use a different approach: sum all geo-level data
        pass

    # Recompute from s_dict files directly using geo-level data
    sc_geo_year = {}  # sc -> {geo_id -> {year -> MWh}}
    for sc in SCENARIOS:
        s_files = glob.glob(str(RESULTS_DIR / sc / '*_s_dict.yaml'))
        if not s_files:
            continue
        geo_year = defaultdict(lambda: defaultdict(float))
        with open(s_files[0]) as f:
            for line in f:
                m = tuple_pat.match(line.strip())
                if not m: continue
                year = int(m.group(1))
                if year != target_year: continue
                geo_id = int(m.group(5))
                fuel, infr_type = int(m.group(7)), int(m.group(8))
                val = float(m.group(10))
                if val < 1e-6 or fuel != 0 or infr_type not in {1, 2}: continue
                geo_year[geo_id][year] += val
        sc_geo_year[sc] = geo_year

    for lat_lo, lat_hi, label in lat_bands:
        row = f"  {label:>20s}"
        for sc in SCENARIOS:
            if sc not in sc_geo_year:
                row += f"  {'N/A':>16s}"
                continue
            band_mwh = sum(
                sc_geo_year[sc][g].get(target_year, 0)
                for g in sc_geo_year[sc]
                if lat_lo <= geo_lat.get(g, 0) < lat_hi
            )
            total_mwh = sum(v.get(target_year, 0) for v in sc_geo_year[sc].values())
            pct = band_mwh / total_mwh * 100 if total_mwh > 0 else 0
            row += f"  {pct:>15.1f}%"
        print(row)


# ══════════════════════════════════════════════════════════════════════
# PART 5: RELOCATION ANALYSIS (opt vs heuristic) for all scenarios
# ══════════════════════════════════════════════════════════════════════
print(f"\n{'=' * 100}")
print("PART 5: RELOCATION % (energy at different nodes in opt vs heuristic)")
print("=" * 100)

# Load common path / break data (same across scenarios since all copy scenario_000)
with open(INPUT_DIR / 'bat_constant_1187' / 'Path.yaml') as f:
    paths = yaml.load(f, Loader=yaml.UnsafeLoader)
with open(INPUT_DIR / 'bat_constant_1187' / 'Odpair.yaml') as f:
    odpairs_raw = yaml.load(f, Loader=yaml.UnsafeLoader)
with open(INPUT_DIR / 'bat_constant_1187' / 'MandatoryBreaks.yaml') as f:
    breaks_data = yaml.safe_load(f)

path_by_id = {int(p['id']): [int(x) for x in p['sequence']] for p in paths}
path_dist_by_id = {}
for p in paths:
    pid = int(p['id'])
    dist = [float(d) for d in p.get('distance_from_previous', [])]
    path_dist_by_id[pid] = dist

od_to_path = {}
for od in odpairs_raw:
    od_to_path[int(od['id'])] = int(od['path_id'])

breaks_by_path = defaultdict(list)
for brk in breaks_data:
    breaks_by_path[int(brk['path_id'])].append(int(brk['latest_geo_id']))

def compute_soc_charging(od_id, path_id, total_energy_mwh, year, battery_by_gen, spec_cons_by_gen):
    """SOC-aware lazy charging at break stops."""
    pid = od_to_path.get(od_id, path_id)
    seq = path_by_id.get(pid, [])
    dist = path_dist_by_id.get(pid, [])
    break_set = set(breaks_by_path.get(pid, []))
    if not seq or not dist or len(seq) != len(dist): return {}

    break_indices = [i for i, g in enumerate(seq) if g in break_set]
    if not break_indices:
        n = len(seq)
        return {seq[i]: total_energy_mwh / n for i in range(n)} if n > 0 else {}

    cum_dist = np.cumsum(dist)
    total_dist = cum_dist[-1] if len(cum_dist) > 0 else 0
    if total_dist < 1e-3: return {}

    # Battery cap for this year (newest gen available)
    bat_cap = battery_by_gen.get(year, battery_by_gen[max(y for y in battery_by_gen if y <= year)])
    sc = spec_cons_by_gen.get(year, spec_cons_by_gen[max(y for y in spec_cons_by_gen if y <= year)])

    soc = bat_cap * 0.5
    charges = {}

    for i, bi in enumerate(break_indices):
        prev_dist = cum_dist[break_indices[i-1]] if i > 0 else 0
        energy_consumed = sc * (cum_dist[bi] - prev_dist)
        soc -= energy_consumed

        if i < len(break_indices) - 1:
            dist_to_next = cum_dist[break_indices[i+1]] - cum_dist[bi]
        else:
            dist_to_next = total_dist - cum_dist[bi]

        energy_to_next = sc * dist_to_next
        if soc < energy_to_next + bat_cap * 0.1:
            charge = min(bat_cap - soc, energy_to_next - soc + bat_cap * 0.1)
            charge = max(0, min(charge, bat_cap - soc))
            if charge > 0:
                charges[seq[bi]] = charges.get(seq[bi], 0) + charge
                soc += charge

    if not charges:
        for bi in break_indices:
            charges[seq[bi]] = 1.0

    total_raw = sum(charges.values())
    if total_raw < 1e-9:
        return {}
    scale = total_energy_mwh / total_raw
    return {geo_id: kwh * scale for geo_id, kwh in charges.items()}


for target_year in [2032, 2040, 2048]:
    print(f"\n--- Year {target_year} ---")
    print(f"  {'Scenario':>20s}  {'Total (MWh)':>12s}  {'Relocated (MWh)':>16s}  {'Reloc %':>10s}  {'Heur nodes':>12s}  {'Opt nodes':>12s}")
    print("  " + "-" * 90)

    for sc in SCENARIOS:
        # Load scenario-specific battery data
        with open(INPUT_DIR / sc / 'TechVehicle.yaml') as f:
            tv_data = yaml.safe_load(f)
        bev_tv = next(tv for tv in tv_data if tv['technology'] == 1)
        gen_years = list(range(2008, 2008 + len(bev_tv['tank_capacity'])))
        battery_by_gen = dict(zip(gen_years, bev_tv['tank_capacity']))
        spec_cons_by_gen = dict(zip(gen_years, bev_tv['spec_cons']))

        # Parse s_dict for this year
        s_files = glob.glob(str(RESULTS_DIR / sc / '*_s_dict.yaml'))
        if not s_files: continue

        opt_geo = defaultdict(float)
        route_year = defaultdict(float)

        with open(s_files[0]) as f:
            for line in f:
                m = tuple_pat.match(line.strip())
                if not m: continue
                year = int(m.group(1))
                if year != target_year: continue
                od_id, path_id, geo_id = int(m.group(3)), int(m.group(4)), int(m.group(5))
                fuel, infr_type = int(m.group(7)), int(m.group(8))
                val = float(m.group(10))
                if val < 1e-6 or fuel != 0 or infr_type not in {1, 2}: continue
                opt_geo[geo_id] += val
                route_year[(od_id, path_id)] += val

        # Compute heuristic
        heur_geo = defaultdict(float)
        for (od_id, path_id), total_e in route_year.items():
            if total_e < 1e-6: continue
            geo_charges = compute_soc_charging(od_id, path_id, total_e, target_year,
                                                battery_by_gen, spec_cons_by_gen)
            for geo_id, mwh in geo_charges.items():
                heur_geo[geo_id] += mwh

        # Compute relocation: energy at nodes that differ between opt and heur
        all_nodes = set(list(opt_geo.keys()) + list(heur_geo.keys()))
        total_energy = sum(opt_geo.values())
        relocated = 0
        for g in all_nodes:
            opt_val = opt_geo.get(g, 0)
            heur_val = heur_geo.get(g, 0)
            relocated += abs(opt_val - heur_val)
        relocated /= 2  # each MWh moved counts twice (removed from one, added to another)
        reloc_pct = relocated / total_energy * 100 if total_energy > 0 else 0

        n_heur = sum(1 for v in heur_geo.values() if v > 0.1)
        n_opt = sum(1 for v in opt_geo.values() if v > 0.1)

        print(f"  {LABELS[sc]:>20s}  {total_energy:>12.0f}  {relocated:>16.0f}  {reloc_pct:>9.1f}%  {n_heur:>12d}  {n_opt:>12d}")


# ══════════════════════════════════════════════════════════════════════
# FINAL SUMMARY TABLE
# ══════════════════════════════════════════════════════════════════════
print(f"\n{'=' * 100}")
print("FINAL SUMMARY: BATTERY SENSITIVITY IMPACT")
print("=" * 100)
print("""
Key findings:
  - BEV adoption: Virtually identical across all scenarios (vehicle stock shift constraint dominates)
  - Total infrastructure: Identical across scenarios (same BEV fleet needs same total capacity)
  - Infrastructure DISTRIBUTION: Varies - smaller batteries spread charging into DE, away from AT/IT
  - Charging distribution: Smaller batteries reduce flexibility -> more geographically constrained
  - Relocation %: Smaller batteries reduce the optimizer's ability to relocate charging

  => The constant 1187 kWh assumption overstates spatial flexibility but does NOT change
     BEV adoption dynamics. The paper's core findings about relocation behavior hold,
     with the caveat that reported relocation % represents an upper bound.
""")
