"""Spatial allocation with two charger types vs MCS only, independent of absolute capacity: compares regional SHARES of capacity and charging energy.
Dissimilarity = 0.5 * sum_g |share_a(g) - share_b(g)|, i.e. the share that would have to move between regions to turn a into b. Output: results/final/mcs_only_allocation.json"""
import sys, os, re, glob, yaml, json
from collections import defaultdict
W = r'D:\AntoniaMariaG\Scand_Med_analysis\SM_baby_2\iDesignRES_transcompmodel\examples\moving_loads_SM'
os.chdir(W); sys.path.insert(0, W)
from heuristic_charging import compute_heuristic_charging
F = 'results/final/'; S = F + 'sensitivity/'
RUNS = {'both': (F + 'uncertainty_scenarios/scenario_000', False), 'mcs': (S + 'mcs_only', True), 'mcs_ff': (S + 'mcs_only_fixed_flows', True)}
inp = 'input_data/uncertainty_scenarios_v2_night/scenario_000/'
L = lambda n: yaml.load(open(inp + n), Loader=yaml.UnsafeLoader)
gname = {g['id']: g.get('nuts2_region', '') for g in yaml.safe_load(open(inp + 'GeographicElement.yaml'))}
paths, ods, brks = L('Path.yaml'), L('Odpair.yaml'), L('MandatoryBreaks.yaml')
path_seq = {int(p['id']): [int(x) for x in p['sequence']] for p in paths}
path_dist = {int(p['id']): [float(d) for d in p.get('distance_from_previous', [])] for p in paths}
od_path = {int(o['id']): int(o['path_id']) for o in ods}
bbp = defaultdict(list); is_rest = {}
for b in brks:
    bbp[int(b['path_id'])].append(int(b['latest_geo_id']))
    is_rest[(int(b['path_id']), int(b['latest_geo_id']))] = b['break_duration'] >= 8.0
YRS = list(range(2020, 2064, 4)); yi2y = {i + 1: y for i, y in enumerate(YRS)}
tp = re.compile(r'\((\d+),\s*\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\),\s*(\d+),\s*\((\d+),\s*(\d+)\),\s*(\d+)\):\s*([\d.eE+-]+)')
cp = re.compile(r'CartesianIndex\((\d+),\s*(\d+),\s*(\d+)\):\s*([\d.eE+-]+)')
last = lambda d, pat: sorted(glob.glob(f'{d}/{pat}'))[-1]
def alloc(d, mcs_only, YR):
    e_opt, route = defaultdict(float), defaultdict(float)
    for line in open(last(d, '*_s_dict.yaml')):
        m = tp.match(line.strip())
        if not m or int(m[1]) != YR or int(m[7]) != 0 or int(m[8]) not in (1, 2): continue
        v = float(m[10])
        if v < 1e-6: continue
        route[(int(m[3]), int(m[4]))] += v; e_opt[int(m[5])] += v
    c_opt = defaultdict(float); c_ccs = defaultdict(float)
    for line in open(last(d, '*_q_fuel_infr_plus_dict.yaml')):
        m = cp.match(line.strip())
        if not m: continue
        yi, fi, pos = int(m[1]), int(m[2]), int(m[3]); v = float(m[4])
        if v < 1e-3 or fi == 3 or yi2y.get(yi, 9999) > YR: continue
        c_opt[pos - 1] += v / 1000
        if fi == 2: c_ccs[pos - 1] += v / 1000
    e_h, c_h = defaultdict(float), defaultdict(float)
    for (o, p), te in route.items():
        ap = od_path.get(o, p)
        for g, mwh in compute_heuristic_charging(o, p, te, od_path, path_seq, path_dist, bbp).items():
            e_h[g] += mwh
            c_h[g] += mwh / ((.75 if is_rest.get((ap, g), False) and not mcs_only else .23) * 8760)
    return dict(e_opt=e_opt, c_opt=c_opt, c_ccs=c_ccs, e_h=e_h, c_h=c_h)
def sh(a):
    t = sum(a.values()); return {g: v / t for g, v in a.items()}
def dis(a, b):
    a, b = sh(a), sh(b); return 50 * sum(abs(a.get(g, 0) - b.get(g, 0)) for g in set(a) | set(b))
def reg(a):
    r = defaultdict(float)
    for g, v in a.items(): r[gname.get(g, str(g))] += v
    return r
out = {}
for YR in (2040, 2048):
    A = {k: alloc(d, f, YR) for k, (d, f) in RUNS.items() if glob.glob(d + '/*_s_dict.yaml')}
    b, m = A['both'], A['mcs']
    r = {'capacity both vs mcs (optimal)': dis(b['c_opt'], m['c_opt']), 'energy both vs mcs (optimal)': dis(b['e_opt'], m['e_opt']),
         'capacity optimal vs heuristic, both': dis(b['c_opt'], b['c_h']), 'capacity optimal vs heuristic, mcs': dis(m['c_opt'], m['c_h']),
         'energy optimal vs heuristic, both': dis(b['e_opt'], b['e_h']), 'energy optimal vs heuristic, mcs': dis(m['e_opt'], m['e_h']),
         'capacity heuristic both vs mcs': dis(b['c_h'], m['c_h']), 'energy heuristic both vs mcs': dis(b['e_h'], m['e_h']),
         'total capacity MW both/mcs': (sum(b['c_opt'].values()), sum(m['c_opt'].values())), 'total energy GWh both/mcs': (sum(b['e_opt'].values()) / 1e3, sum(m['e_opt'].values()) / 1e3)}
    if 'mcs_ff' in A:
        f = A['mcs_ff']
        r.update({'capacity both vs mcs fixed flows': dis(b['c_opt'], f['c_opt']), 'energy both vs mcs fixed flows': dis(b['e_opt'], f['e_opt']), 'capacity optimal vs heuristic, mcs fixed flows': dis(f['c_opt'], f['c_h'])})
    print(YR); [print(f'  {k:50s}', v if isinstance(v, tuple) else round(v, 1)) for k, v in r.items()]
    cb, cm, eb, em, hb = map(lambda x: sh(reg(x)), (b['c_opt'], m['c_opt'], b['e_opt'], m['e_opt'], b['c_h']))
    ccs = reg(b['c_ccs']); cbA = reg(b['c_opt'])
    top = sorted(set(cb) | set(cm), key=lambda g: -abs(cb.get(g, 0) - cm.get(g, 0)))[:10]
    print('  region: capacity share both | mcs | diff pp || energy share both | mcs || CCS share of capacity in both')
    for g in top:
        print(f'  {g:6s} {cb.get(g,0)*100:5.1f} {cm.get(g,0)*100:5.1f} {(cb.get(g,0)-cm.get(g,0))*100:+5.1f} || {eb.get(g,0)*100:5.1f} {em.get(g,0)*100:5.1f} || {(ccs.get(g,0)/cbA[g]*100 if cbA.get(g) else 0):4.0f}')
    out[YR] = {k: v for k, v in r.items()}
    out[YR]['regions'] = {g: dict(cap_both=cb.get(g, 0) * 100, cap_mcs=cm.get(g, 0) * 100, en_both=eb.get(g, 0) * 100, en_mcs=em.get(g, 0) * 100) for g in set(cb) | set(cm)}
json.dump(out, open(F + 'mcs_only_allocation.json', 'w'), indent=1)
