"""Relocation analysis: energy + infrastructure, across scenarios."""
import re, glob, yaml, numpy as np
from collections import defaultdict
from heuristic_charging import compute_heuristic_charging

tuple_pat = re.compile(
    r'\((\d+),\s*\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\),\s*(\d+),\s*\((\d+),\s*(\d+)\),\s*(\d+)\):\s*([\d.eE+-]+)')
ci3_pat = re.compile(r'CartesianIndex\((\d+),\s*(\d+),\s*(\d+)\):\s*([\d.eE+-]+)')

with open('input_data/fixed_nuts_2/GeographicElement.yaml') as f:
    geo_data = yaml.safe_load(f)
geo_country = {g['id']: g.get('country', '??') for g in geo_data}
all_geo_ids = [g['id'] for g in geo_data if g.get('type') == 'node']

with open('input_data/uncertainty_scenarios_v2/scenario_000/Path.yaml') as f:
    paths = yaml.load(f, Loader=yaml.UnsafeLoader)
with open('input_data/uncertainty_scenarios_v2/scenario_000/Odpair.yaml') as f:
    odpairs_raw = yaml.load(f, Loader=yaml.UnsafeLoader)
with open('input_data/uncertainty_scenarios_v2/scenario_000/MandatoryBreaks.yaml') as f:
    breaks_data = yaml.load(f, Loader=yaml.UnsafeLoader)
with open('input_data/uncertainty_scenarios_v2/scenario_000/TechVehicle.yaml') as f:
    tv_data = yaml.safe_load(f)

path_seq = {int(p['id']): [int(x) for x in p['sequence']] for p in paths}
path_dist = {int(p['id']): [float(d) for d in p.get('distance_from_previous', [])] for p in paths}
od_path = {int(od['id']): int(od['path_id']) for od in odpairs_raw}
breaks_by_path = defaultdict(list)
for brk in breaks_data:
    breaks_by_path[int(brk['path_id'])].append(int(brk['latest_geo_id']))

bev_tv = next(t for t in tv_data if t['technology'] == 1)
GEN_YEARS = list(range(2008, 2008 + len(bev_tv['tank_capacity'])))
BATTERY_BY_GEN = dict(zip(GEN_YEARS, bev_tv['tank_capacity']))
SPEC_CONS_BY_GEN = dict(zip(GEN_YEARS, bev_tv['spec_cons']))
MODELED_YEARS = list(range(2020, 2064, 4))
y_idx_to_year = {i+1: y for i, y in enumerate(MODELED_YEARS)}

def bat_cap(year):
    return BATTERY_BY_GEN.get(year, BATTERY_BY_GEN[max(y for y in BATTERY_BY_GEN if y <= year)])
def spec_cons(year):
    return SPEC_CONS_BY_GEN.get(year, SPEC_CONS_BY_GEN[max(y for y in SPEC_CONS_BY_GEN if y <= year)])

def compute_soc(od_id, path_id, total_e, year):
    pid = od_path.get(od_id, path_id)
    seq = path_seq.get(pid, [])
    dist = path_dist.get(pid, [])
    break_set = set(breaks_by_path.get(pid, []))
    if not seq or not dist or len(seq) != len(dist): return {}
    bi = [i for i, g in enumerate(seq) if g in break_set]
    if not bi:
        n = len(seq)
        return {seq[i]: total_e / n for i in range(n)} if n else {}
    cd = np.cumsum(dist)
    td = cd[-1] if len(cd) else 0
    if td < 1e-3: return {}
    bc = bat_cap(year); sc = spec_cons(year)
    soc = bc * 0.5; charges = {}
    for i, b in enumerate(bi):
        pd = cd[bi[i-1]] if i > 0 else 0
        soc -= sc * (cd[b] - pd)
        dn = (cd[bi[i+1]] if i < len(bi)-1 else td) - cd[b]
        en = sc * dn
        if soc < en + bc * 0.1:
            ch = max(0, min(bc - soc, en - soc + bc * 0.1))
            if ch > 0: charges[seq[b]] = charges.get(seq[b], 0) + ch; soc += ch
    if not charges:
        for b in bi: charges[seq[b]] = 1.0
    tr = sum(charges.values())
    if tr < 1e-9: return {}
    s = total_e / tr
    return {g: v * s for g, v in charges.items()}

SCENARIOS = ['scenario_000', 'scenario_001', 'scenario_002', 'scenario_003']
LABELS = {'scenario_000': 'Go RES', 'scenario_001': 'NECP', 'scenario_002': 'REPower', 'scenario_003': 'Trinity'}
COUNTRIES = ['IT', 'AT', 'DE', 'SE', 'DK', 'NO', 'FI']

# ═══════════════════════════
# PART 1: ENERGY RELOCATION
# ═══════════════════════════
print("=" * 90)
print("PART 1: CHARGING ENERGY RELOCATION (optimal vs heuristic)")
print("=" * 90)
print(f"\n{'Year':>6s}", end="")
for sc in SCENARIOS:
    print(f"  {LABELS[sc]:>10s}%  GWh", end="")
print()
print("-" * 80)

for ty in [2032, 2036, 2040, 2044, 2048]:
    row = f"{ty:>6d}"
    for sc in SCENARIOS:
        sf = sorted(glob.glob(f"results/uncertainty_scenarios_v2/{sc}/*_s_dict.yaml"))
        og = defaultdict(float); re_dict = defaultdict(float)
        with open(sf[-1]) as f:
            for line in f:
                m = tuple_pat.match(line.strip())
                if not m: continue
                yr = int(m.group(1))
                if yr != ty: continue
                oid, pid, gid = int(m.group(3)), int(m.group(4)), int(m.group(5))
                fu, inf = int(m.group(7)), int(m.group(8))
                val = float(m.group(10))
                if val < 1e-6 or fu != 0 or inf not in {1, 2}: continue
                og[gid] += val; re_dict[(oid, pid)] += val
        hg = defaultdict(float)
        for (oid, pid), te in re_dict.items():
            if te < 1e-6: continue
            for g, mwh in compute_heuristic_charging(oid, pid, te, od_path, path_seq, path_dist, breaks_by_path).items():
                hg[g] += mwh
        ot = sum(og.values())
        rel = sum(abs(og.get(g, 0) - hg.get(g, 0)) for g in all_geo_ids) / 2
        rp = rel / ot * 100 if ot > 0 else 0
        row += f"  {rp:>10.1f}  {ot/1000:>4.0f}"
    print(row)

# ═══════════════════════════════════════
# PART 2: CROSS-SCENARIO INFRA SPREAD
# ═══════════════════════════════════════
print(f"\n{'=' * 90}")
print("PART 2: INFRASTRUCTURE SPREAD ACROSS SCENARIOS (cumulative MW)")
print("=" * 90)

for ty in [2040, 2048]:
    print(f"\n--- {ty} ---")
    print(f"{'Country':>8s}", end="")
    for sc in SCENARIOS:
        print(f"  {LABELS[sc]:>8s}", end="")
    print(f"  {'Spread':>8s}  {'Spread%':>8s}")
    print("-" * 70)

    sc_c = {}
    for sc in SCENARIOS:
        qf = sorted(glob.glob(f"results/uncertainty_scenarios_v2/{sc}/*_q_fuel_infr_plus_dict.yaml"))
        cm = defaultdict(float)
        with open(qf[-1]) as f:
            for line in f:
                m = ci3_pat.match(line.strip())
                if not m: continue
                yi, fl, geo = int(m.group(1)), int(m.group(2)), int(m.group(3))
                val = float(m.group(4))
                if val < 1e-3 or fl == 3: continue
                geo_id = geo - 1  # CartesianIndex is 1-based positional
                yr = y_idx_to_year.get(yi)
                if yr and yr <= ty:
                    cm[geo_country.get(geo_id, '??')] += val / 1000
        sc_c[sc] = cm

    for c in COUNTRIES:
        vals = [sc_c[sc].get(c, 0) for sc in SCENARIOS]
        sp = max(vals) - min(vals)
        spp = sp / max(vals) * 100 if max(vals) > 0.1 else 0
        row = f"{c:>8s}"
        for v in vals:
            row += f"  {v:>8.1f}"
        row += f"  {sp:>8.1f}  {spp:>7.0f}%"
        print(row)

    vt = [sum(sc_c[sc].values()) for sc in SCENARIOS]
    row = f"{'TOTAL':>8s}"
    for v in vt:
        row += f"  {v:>8.1f}"
    row += f"  {max(vt)-min(vt):>8.1f}  {(max(vt)-min(vt))/max(vt)*100:>7.0f}%"
    print(row)

# ═══════════════════════════════════════
# PART 3: ENERGY COUNTRY SHARES (opt)
# ═══════════════════════════════════════
print(f"\n{'=' * 90}")
print("PART 3: CHARGING ENERGY COUNTRY SHARES (%) — Optimal allocation")
print("=" * 90)

for ty in [2040, 2048]:
    print(f"\n--- {ty} ---")
    print(f"{'Country':>8s}", end="")
    for sc in SCENARIOS:
        print(f"  {LABELS[sc]:>8s}", end="")
    print(f"  {'Spread':>8s}")
    print("-" * 60)

    sc_e = {}
    for sc in SCENARIOS:
        sf = sorted(glob.glob(f"results/uncertainty_scenarios_v2/{sc}/*_s_dict.yaml"))
        ce = defaultdict(float)
        with open(sf[-1]) as f:
            for line in f:
                m = tuple_pat.match(line.strip())
                if not m: continue
                yr = int(m.group(1))
                if yr != ty: continue
                gid = int(m.group(5))
                fu = int(m.group(7))
                val = float(m.group(10))
                if val < 1e-6 or fu != 0: continue
                ce[geo_country.get(gid, '??')] += val
        sc_e[sc] = ce

    for c in COUNTRIES:
        vals = []
        for sc in SCENARIOS:
            tot = sum(sc_e[sc].values())
            pct = sc_e[sc].get(c, 0) / tot * 100 if tot > 0 else 0
            vals.append(pct)
        sp = max(vals) - min(vals)
        row = f"{c:>8s}"
        for v in vals:
            row += f"  {v:>7.1f}%"
        row += f"  {sp:>7.1f}pp"
        print(row)

print("\nDone!")
