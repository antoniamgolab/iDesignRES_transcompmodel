"""Compare energy relocation vs infrastructure relocation."""
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
COUNTRIES = ['IT', 'AT', 'DE', 'SE', 'NO', 'DK', 'FI']

def bat_cap(y): return BATTERY_BY_GEN.get(y, BATTERY_BY_GEN[max(k for k in BATTERY_BY_GEN if k <= y)])
def sc_(y): return SPEC_CONS_BY_GEN.get(y, SPEC_CONS_BY_GEN[max(k for k in SPEC_CONS_BY_GEN if k <= y)])

def compute_soc(oid, pid, te, yr):
    p = od_path.get(oid, pid); seq = path_seq.get(p, []); dist = path_dist.get(p, [])
    bs = set(breaks_by_path.get(p, []))
    if not seq or not dist or len(seq) != len(dist): return {}
    bi = [i for i, g in enumerate(seq) if g in bs]
    if not bi: n = len(seq); return {seq[i]: te/n for i in range(n)} if n else {}
    cd = np.cumsum(dist); td = cd[-1] if len(cd) else 0
    if td < 1e-3: return {}
    bc = bat_cap(yr); s = sc_(yr); soc = bc*0.5; ch = {}
    for i, b in enumerate(bi):
        pd = cd[bi[i-1]] if i > 0 else 0; soc -= s*(cd[b]-pd)
        dn = (cd[bi[i+1]] if i<len(bi)-1 else td)-cd[b]; en = s*dn
        if soc < en+bc*0.1:
            c = max(0, min(bc-soc, en-soc+bc*0.1))
            if c > 0: ch[seq[b]] = ch.get(seq[b],0)+c; soc += c
    if not ch:
        for b in bi: ch[seq[b]] = 1.0
    tr = sum(ch.values())
    if tr < 1e-9: return {}
    sc2 = te/tr; return {g: v*sc2 for g, v in ch.items()}

# Parse Go RES data
sf = sorted(glob.glob('results/uncertainty_scenarios_v2/scenario_000/*_s_dict.yaml'))
qf = sorted(glob.glob('results/uncertainty_scenarios_v2/scenario_000/*_q_fuel_infr_plus_dict.yaml'))

all_opt = defaultdict(lambda: defaultdict(float))
all_route = defaultdict(lambda: defaultdict(float))
with open(sf[-1]) as f:
    for line in f:
        m = tuple_pat.match(line.strip())
        if not m: continue
        yr=int(m.group(1)); oid=int(m.group(3)); pid=int(m.group(4)); gid=int(m.group(5))
        fu=int(m.group(7)); inf=int(m.group(8)); val=float(m.group(10))
        if val<1e-6 or fu!=0 or inf not in {1,2}: continue
        all_opt[yr][gid] += val; all_route[yr][(oid,pid)] += val

infra_geo = defaultdict(lambda: defaultdict(float))
with open(qf[-1]) as f:
    for line in f:
        m = ci3_pat.match(line.strip())
        if not m: continue
        yi=int(m.group(1)); fl=int(m.group(2)); geo=int(m.group(3)); val=float(m.group(4))
        if val<1e-3 or fl==3: continue
        yr = y_idx_to_year.get(yi)
        if yr: infra_geo[geo][yr] += val

print("GO RES: ENERGY vs INFRASTRUCTURE RELOCATION")
print("="*95)
print()
print(f"{'Year':>6s}  {'Total':>7s}  {'Reloc':>7s}  {'Reloc':>6s}  |  {'Opt':>7s}  {'Heur':>7s}  {'Delta':>7s}  {'Infra':>6s}")
print(f"{'':>6s}  {'GWh':>7s}  {'GWh':>7s}  {'%':>6s}  |  {'MW':>7s}  {'MW':>7s}  {'MW':>7s}  {'Reloc%':>6s}")
print("-"*70)

for ty in [2032, 2036, 2040, 2044, 2048]:
    og = all_opt[ty]
    hg = defaultdict(float)
    for (oid,pid), te in all_route[ty].items():
        if te<1e-6: continue
        for g, mwh in compute_heuristic_charging(oid, pid, te, od_path, path_seq, path_dist, breaks_by_path).items(): hg[g]+=mwh

    e_total = sum(og.values())/1000
    e_reloc = sum(abs(og.get(g,0)-hg.get(g,0)) for g in all_geo_ids)/2/1000
    e_reloc_pct = e_reloc/e_total*100 if e_total>0 else 0

    # Infra: optimal cumulative MW
    opt_mw = sum(sum(infra_geo[g].get(y,0) for y in MODELED_YEARS if y<=ty) for g in infra_geo)/1000

    # Heur infra: what heuristic needs (capacity = energy / (gamma_blend * 8760))
    # Use node-level: required_kW = energy_MWh * 1000 / (gamma * 8760)
    # Approximate with gamma=0.4 (blended)
    heur_mw = sum(hg.get(g,0)*1000/(0.4*8760)/1000 for g in all_geo_ids if hg.get(g,0)>0)

    infra_delta = sum(abs(
        sum(infra_geo[g].get(y,0) for y in MODELED_YEARS if y<=ty)/1000 -
        hg.get(g,0)*1000/(0.4*8760)/1000
    ) for g in all_geo_ids) / 2
    infra_reloc_pct = infra_delta/opt_mw*100 if opt_mw>0 else 0

    print(f"{ty:>6d}  {e_total:>7.0f}  {e_reloc:>7.0f}  {e_reloc_pct:>5.1f}%  |  {opt_mw:>7.0f}  {heur_mw:>7.0f}  {abs(opt_mw-heur_mw):>7.0f}  {infra_reloc_pct:>5.1f}%")

# Country-level for 2040 and 2048
for ty in [2040, 2048]:
    print(f"\n--- Country-level at {ty} ---")
    print(f"{'Country':>8s}  {'OptE%':>6s}  {'HeurE%':>7s}  {'DE':>5s}  |  {'OptMW':>6s}  {'HeurMW':>7s}  {'DMW':>6s}")
    print("-"*55)

    og = all_opt[ty]
    hg = defaultdict(float)
    for (oid,pid), te in all_route[ty].items():
        if te<1e-6: continue
        for g, mwh in compute_heuristic_charging(oid, pid, te, od_path, path_seq, path_dist, breaks_by_path).items(): hg[g]+=mwh

    oe_t = sum(og.values()); he_t = sum(hg.values())

    for c in COUNTRIES:
        oe = sum(og.get(g,0) for g in all_geo_ids if geo_country.get(g)==c)
        he = sum(hg.get(g,0) for g in all_geo_ids if geo_country.get(g)==c)
        oep = oe/oe_t*100 if oe_t>0 else 0
        hep = he/he_t*100 if he_t>0 else 0

        oi = sum(sum(infra_geo[g].get(y,0) for y in MODELED_YEARS if y<=ty) for g in all_geo_ids if geo_country.get(g)==c)/1000
        hi = sum(hg.get(g,0)*1000/(0.4*8760)/1000 for g in all_geo_ids if geo_country.get(g)==c and hg.get(g,0)>0)

        print(f"{c:>8s}  {oep:>5.1f}%  {hep:>6.1f}%  {oep-hep:>+4.1f}  |  {oi:>6.1f}  {hi:>7.1f}  {oi-hi:>+5.1f}")

print("\nDone!")
