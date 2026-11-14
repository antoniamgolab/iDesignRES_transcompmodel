"""Analyze stranded infrastructure capacity from zone-split timing."""
import yaml, re, os
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
os.chdir(SCRIPT_DIR)
results_dir = SCRIPT_DIR / 'results' / 'eem_scenarios'
geos = yaml.safe_load(open(SCRIPT_DIR / 'input_data' / 'eem_scenarios' / 'DE_unified' / 'GeographicElement.yaml'))
geo_id_to_nuts2 = {g['id']: g.get('nuts2_region', '?') for g in geos}

modeled_years = list(range(2020, 2061, 4))
idx_to_year = {i+1: y for i, y in enumerate(modeled_years)}

DE_NORTH = {'DE30','DE40','DE50','DE60','DE80','DE91','DE92','DE93','DE94',
            'DEF0','DED2','DED4','DED5','DEE0','DEG0'}
DE_SOUTH = {'DE11','DE12','DE13','DE14','DE21','DE22','DE23','DE24','DE25','DE26','DE27',
            'DE71','DE72','DE73','DEA1','DEA2','DEA3','DEA4','DEA5',
            'DEB1','DEB2','DEB3','DEC0'}

def get_zone(nuts2):
    if nuts2 in DE_NORTH: return 'DE-North'
    if nuts2 in DE_SOUTH: return 'DE-South'
    return 'Other'

pat3 = re.compile(r'CartesianIndex\((\d+),\s*(\d+),\s*(\d+)\)')

scenarios = sorted([d.name for d in results_dir.iterdir()
                    if d.is_dir() and list((results_dir/d).glob('*_q_fuel_infr_plus_dict.yaml'))])

print(f"Found {len(scenarios)} completed scenarios: {scenarios}\n")

cumul_south = {}
cumul_north = {}
added_south = {}
added_north = {}

for sc in scenarios:
    q_files = list((results_dir / sc).glob('*_q_fuel_infr_plus_dict.yaml'))
    q_data = yaml.safe_load(open(q_files[0]))

    added = {y: {'DE-North': 0.0, 'DE-South': 0.0} for y in modeled_years}

    for key, val in q_data.items():
        m = pat3.match(key)
        if not m:
            continue
        y_idx = int(m.group(1))
        geo_id = int(m.group(3))
        year = idx_to_year.get(y_idx)
        if year is None:
            continue
        nuts2 = geo_id_to_nuts2.get(geo_id, '?')
        zone = get_zone(nuts2)
        if zone in added[year]:
            added[year][zone] += val

    n_c, s_c = 0.0, 0.0
    cn, cs = {}, {}
    an, as_ = {}, {}
    for year in modeled_years:
        n_c += added[year]['DE-North']
        s_c += added[year]['DE-South']
        cn[year] = n_c
        cs[year] = s_c
        an[year] = added[year]['DE-North']
        as_[year] = added[year]['DE-South']

    cumul_north[sc] = cn
    cumul_south[sc] = cs
    added_north[sc] = an
    added_south[sc] = as_

# ============================================================
show_years = [2028, 2032, 2036, 2040, 2044, 2048, 2060]

print("=" * 110)
print("TABLE 1: CUMULATIVE SOUTH-DE INFRASTRUCTURE (kW)")
print("=" * 110)
header = "Scenario".ljust(35)
for y in show_years:
    header += str(y).rjust(10)
print(header)
print("-" * 110)
for sc in scenarios:
    line = sc.ljust(35)
    for y in show_years:
        line += f"{cumul_south[sc][y]:10,.0f}"
    print(line)

print()
print("=" * 110)
print("TABLE 2: CUMULATIVE NORTH-DE INFRASTRUCTURE (kW)")
print("=" * 110)
header = "Scenario".ljust(35)
for y in show_years:
    header += str(y).rjust(10)
print(header)
print("-" * 110)
for sc in scenarios:
    line = sc.ljust(35)
    for y in show_years:
        line += f"{cumul_north[sc][y]:10,.0f}"
    print(line)

print()
print("=" * 110)
print("TABLE 3: NORTH SHARE OF GERMAN INFRASTRUCTURE (%)")
print("=" * 110)
header = "Scenario".ljust(35)
for y in show_years:
    header += str(y).rjust(10)
print(header)
print("-" * 110)
for sc in scenarios:
    line = sc.ljust(35)
    for y in show_years:
        n = cumul_north[sc][y]
        s = cumul_south[sc][y]
        t = n + s
        pct = n / t * 100 if t > 0 else 0
        line += f"{pct:9.1f}%"
    print(line)

print()
print("=" * 110)
print("TABLE 4: SOUTH-DE EXCESS vs EARLY-SPLIT (stranded capacity indicator)")
print("  Positive = more South capacity than early-split => potentially underutilized")
print("=" * 110)
header = "Scenario".ljust(35)
for y in show_years:
    header += str(y).rjust(10)
print(header)
print("-" * 110)

for sc in scenarios:
    if 'from2020' in sc or sc == 'DE_unified':
        continue
    # Find matching from2020
    if 'low' in sc:
        ref_key = 'DE_split_low_from2020'
    elif 'mid' in sc:
        ref_key = 'DE_split_mid_from2020'
    elif 'high' in sc:
        ref_key = 'DE_split_high_from2020'
    else:
        continue
    if ref_key not in cumul_south:
        continue

    line = sc.ljust(35)
    for y in show_years:
        delta = cumul_south[sc][y] - cumul_south[ref_key][y]
        line += f"{delta:+10,.0f}"
    print(line)

# Also show: yearly additions to see the shift timing
print()
print("=" * 110)
print("TABLE 5: YEARLY ADDITIONS TO SOUTH-DE (kW per period)")
print("=" * 110)
header = "Scenario".ljust(35)
for y in show_years:
    header += str(y).rjust(10)
print(header)
print("-" * 110)
for sc in scenarios:
    line = sc.ljust(35)
    for y in show_years:
        line += f"{added_south[sc].get(y, 0):10,.0f}"
    print(line)

print()
print("=" * 110)
print("TABLE 6: YEARLY ADDITIONS TO NORTH-DE (kW per period)")
print("=" * 110)
header = "Scenario".ljust(35)
for y in show_years:
    header += str(y).rjust(10)
print(header)
print("-" * 110)
for sc in scenarios:
    line = sc.ljust(35)
    for y in show_years:
        line += f"{added_north[sc].get(y, 0):10,.0f}"
    print(line)
