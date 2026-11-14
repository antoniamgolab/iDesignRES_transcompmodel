"""
Diagnose the 10x discrepancy between the kappa_space cap I computed (~28 charge
points/period at ITH1) and the actual q_plus additions in the model output
(~280 CCS units/period at ITH1).

For each top node, compute:
  1. B_e from input data (same way SM_batch.jl does)
  2. Per-period cap: kappa_space * B_e
  3. Actual per-period sum( q_plus[fl] / power[fl[2]] ) from the YAML output
  4. Ratio: actual / cap

If the ratio is uniformly 10 across all nodes/periods, the unit factor is
constant (likely a multiplier on q_plus values, or B_e). If it varies, the
discrepancy is structural and depends on the node.

Also computes what the constraint LHS would be using different alternative
power factor assumptions, to identify which one Gurobi was actually applying.
"""
import yaml, glob, re
from pathlib import Path
from collections import defaultdict

BASE = Path('.')
ci3 = re.compile(r'CartesianIndex\((\d+),\s*(\d+),\s*(\d+)\):\s*([\d.eE+-]+)')

# Load geo info
with open(BASE / 'input_data/fixed_nuts_2/GeographicElement.yaml') as f:
    geo = yaml.safe_load(f)
gname = {g['id']: g.get('name', '?').replace('nuts2_', '') for g in geo}

# Load input data (same way SM_batch does)
INP = BASE / 'input_data/uncertainty_scenarios_v2/scenario_000'
with open(INP / 'MandatoryBreaks.yaml') as f:
    breaks = yaml.load(f, Loader=yaml.UnsafeLoader)
with open(INP / 'Odpair.yaml') as f:
    odpairs = yaml.load(f, Loader=yaml.UnsafeLoader)
with open(INP / 'TechVehicle.yaml') as f:
    tv = yaml.safe_load(f)
with open(INP / 'FuelingInfrTypes.yaml') as f:
    finfr = yaml.safe_load(f)

# Charger powers (kW per unit)
power = {fi['id']: fi['fueling_power'][0] for fi in finfr}
print(f"Charger powers: {power}")

# Payload
W = tv[0]['W'][0]
print(f"Payload W = {W} tonnes/truck")

# Build B_e (same way as SM_batch.jl: B_e[geo] = sum over od.paths * (od.F[1]/W) for paths with mandatory break at geo)
breaks_by_path = defaultdict(list)
for mb in breaks:
    breaks_by_path[int(mb['path_id'])].append(int(mb['latest_geo_id']))

B_e = defaultdict(float)
for od in odpairs:
    F_base = od['F'][0]
    truck_trips = F_base / W
    path_ids = []
    if 'paths' in od:
        path_ids = [int(p) if not isinstance(p, dict) else int(p['id']) for p in od['paths']]
    elif 'path_id' in od:
        path_ids = [int(od['path_id'])]
    for pid in path_ids:
        for gid in breaks_by_path.get(pid, []):
            B_e[gid] += truck_trips

# Get q_plus from the canonical baseline run
qf = sorted(glob.glob(str(BASE / 'results/kappa_sensitivity/kappa_0.5/*_q_fuel_infr_plus_dict.yaml')))[-1]
MODELED = list(range(2020, 2064, 4))
y_idx = {i+1: y for i, y in enumerate(MODELED)}

# q_plus[geo][year][fi] = kW
q_plus = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
with open(qf) as f:
    for line in f:
        m = ci3.match(line.strip())
        if not m: continue
        yi, fi, pos = int(m.group(1)), int(m.group(2)), int(m.group(3))
        kw = float(m.group(4))
        if kw < 1e-3 or fi == 3: continue
        yr = y_idx.get(yi)
        if yr is None: continue
        q_plus[pos-1][yr][fi] += kw

ks = 0.0005  # kappa_space

# Inspect top 3 nodes
ith1 = next(gid for gid, n in gname.items() if n == 'ITH1')
de21 = next(gid for gid, n in gname.items() if n == 'DE21')
at33 = next(gid for gid, n in gname.items() if n == 'AT33')

print(f"\n{'='*100}")
print(f"KSPACE CONSTRAINT DIAGNOSTIC")
print(f"  Constraint: sum( q_plus[fl] / power[fl[2]] ) <= kappa_space * B_e   per (year, geo)")
print(f"  kappa_space = {ks}")
print(f"{'='*100}")

for gid in [ith1, de21, at33]:
    be = B_e[gid]
    cap_cp = ks * be
    print(f"\n--- {gname[gid]} (geo_id={gid}) ---")
    print(f"  B_e = {be:.1f} truck-breaks/yr")
    print(f"  Cap = kappa_space * B_e = {cap_cp:.2f} charge points/period")
    print(f"  {'Year':<6s} {'+MCS kW':>10s} {'+CCS kW':>10s} {'LHS (CCS/100 + MCS/1000)':>26s} {'Cap':>8s} {'Ratio':>8s}")
    for yr in sorted(q_plus[gid]):
        mcs_kw = q_plus[gid][yr].get(2, 0)
        ccs_kw = q_plus[gid][yr].get(1, 0)
        lhs = ccs_kw / power.get(1, 100) + mcs_kw / power.get(2, 1000)
        ratio = lhs / cap_cp if cap_cp > 0 else 0
        print(f"  {yr:<6d} {mcs_kw:>10.0f} {ccs_kw:>10.0f} {lhs:>26.2f} {cap_cp:>8.2f} {ratio:>7.2f}x")

print(f"\n{'='*100}")
print("ALTERNATIVE INTERPRETATIONS — test what makes the arithmetic work")
print(f"{'='*100}")

# Hypothesis A: q_plus is in W not kW (factor 1000 off — would give 0.01x, ruled out)
# Hypothesis B: q_plus represents kW/yr summed over 4 years => divide by 4 to get per-period
# Hypothesis C: B_e is summed over modeled years (e.g. * pre_y + Y = 53 years?) — would give huge cap
# Hypothesis D: power factor in constraint is different from FuelingInfrTypes.yaml

print("\nB) If q_plus values are kW summed over the 4-year period (divide by 4 for per-period rate):")
for gid in [ith1]:
    be = B_e[gid]
    cap_cp = ks * be
    print(f"  {gname[gid]}:")
    for yr in [2040, 2048]:
        if yr not in q_plus[gid]: continue
        ccs_kw = q_plus[gid][yr].get(1, 0)
        lhs_div4 = (ccs_kw / power.get(1, 100)) / 4
        print(f"    {yr}: LHS/4 = {lhs_div4:.2f}, Cap = {cap_cp:.2f}, ratio = {lhs_div4/cap_cp:.2f}x")

print("\nC) If B_e is multiplied by time_step (4 years) when forming cap:")
for gid in [ith1]:
    be = B_e[gid]
    cap_cp_x4 = ks * be * 4
    print(f"  {gname[gid]}: cap*4 = {cap_cp_x4:.2f}")
    for yr in [2040, 2048]:
        if yr not in q_plus[gid]: continue
        ccs_kw = q_plus[gid][yr].get(1, 0)
        lhs = ccs_kw / power.get(1, 100)
        print(f"    {yr}: LHS = {lhs:.2f}, Cap*4 = {cap_cp_x4:.2f}, ratio = {lhs/cap_cp_x4:.2f}x")

print("\nD) If CCS power factor in constraint is actually 1000 kW (= MCS power, i.e. constraint uses uniform 1000):")
for gid in [ith1]:
    be = B_e[gid]
    cap_cp = ks * be
    print(f"  {gname[gid]}:")
    for yr in [2040, 2048]:
        if yr not in q_plus[gid]: continue
        ccs_kw = q_plus[gid][yr].get(1, 0)
        mcs_kw = q_plus[gid][yr].get(2, 0)
        lhs_uniform = (ccs_kw + mcs_kw) / 1000
        print(f"    {yr}: LHS (using power=1000 for both) = {lhs_uniform:.2f}, Cap = {cap_cp:.2f}, ratio = {lhs_uniform/cap_cp:.2f}x")
