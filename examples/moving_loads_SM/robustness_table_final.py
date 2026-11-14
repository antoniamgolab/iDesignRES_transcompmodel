"""Robustness table: all final sensitivity runs vs base case, 2040 and 2048. Heuristic uses each run's own fleet/energy and gamma."""
import sys, os, re, glob, yaml, json
from collections import defaultdict
W = r'D:\AntoniaMariaG\Scand_Med_analysis\SM_baby_2\iDesignRES_transcompmodel\examples\moving_loads_SM'
os.chdir(W); sys.path.insert(0, W)
from heuristic_charging import compute_heuristic_charging
F = 'results/final/'; S = F + 'sensitivity/'
RUNS = [('base', F + 'uncertainty_scenarios/scenario_000', 1.0),
        ('base_rail', F + 'uncertainty_scenarios_rail/scenario_000', 1.0)]
for l in ['rail_growth_2pp', 'rail_growth_5pp', 'rail_cap_20', 'rail_cost_0.04', 'rail_cost_0.08', 'kappa_pwr_0.3', 'kappa_pwr_1.0', 'kspace_cum_0.002', 'kspace_cum_0.008',
          'no_space_cap', 'space_per_period', 'overbuild_10pct', 'overbuild_allowed', 'uniform_prices', 'uniform_spatial_costs', 'freight_low', 'freight_high',
          'mcs_only', 'mcs_only_fixed_flows']:
    RUNS.append((l, S + l, 1.0))
RUNS += [('gamma_m25', S + 'gamma_m25', .75), ('gamma_p25', S + 'gamma_p25', 1.25)]
RUNS += [(os.path.basename(d), d, 1.0) for d in sorted(glob.glob(S + 'battery/*')) + sorted(glob.glob(S + 'soc/*'))]
RUNS += [(f'scen_{i}', F + f'uncertainty_scenarios/scenario_00{i}', 1.0) for i in (1, 2, 3)]
RUNS += [('cx400', S + 'capex_400', 1.0)]
RUNS += [('cx650', S + 'capex_650', 1.0)]
RUNS += [('gc_x2.5', S + 'gridcharge_x2.5', 1.0), ('gc_x5', S + 'gridcharge_x5', 1.0)]
inp = 'input_data/uncertainty_scenarios_v2_night/scenario_000/'
L = lambda n: yaml.load(open(inp + n), Loader=yaml.UnsafeLoader)
geo = yaml.safe_load(open(inp + 'GeographicElement.yaml'))
gname = {g['id']: g.get('nuts2_region', '') for g in geo}
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
BR = {gid for gid, n in gname.items() if n in ('AT33', 'ITH1')}
out = []
for lab, d, gf in RUNS:
    if not glob.glob(d + '/summary_stats.yaml'): print('missing', lab, d); continue
    st = yaml.safe_load(open(d + '/summary_stats.yaml')); tb = st['tonnes_by_year']
    sdl = open(last(d, '*_s_dict.yaml')).read().splitlines()
    qdl = open(last(d, '*_q_fuel_infr_plus_dict.yaml')).read().splitlines()
    row = {'run': lab, 'obj': float(st['objective_value'])}
    for YR in (2040, 2048):
        route = defaultdict(float); E = 0; EB = 0
        for line in sdl:
            m = tp.match(line.strip())
            if not m or int(m[1]) != YR or int(m[7]) != 0 or int(m[8]) not in (1, 2): continue
            v = float(m[10])
            if v < 1e-6: continue
            route[(int(m[3]), int(m[4]))] += v; E += v
            if int(m[5]) in BR: EB += v
        opt = defaultdict(lambda: [0., 0.])
        for line in qdl:
            m = cp.match(line.strip())
            if not m: continue
            yi, fi, pos = int(m[1]), int(m[2]), int(m[3]); v = float(m[4])
            if v < 1e-3 or fi == 3 or yi2y.get(yi, 9999) > YR: continue
            opt[pos - 1][0 if fi == 2 else 1] += v / 1000
        heur = defaultdict(lambda: [0., 0.])
        mcs_only = lab.startswith('mcs_only'); HB = 0
        for (o, p), te in route.items():
            ap = od_path.get(o, p)
            for g, mwh in compute_heuristic_charging(o, p, te, od_path, path_seq, path_dist, bbp).items():
                if g in BR: HB += mwh
                if is_rest.get((ap, g), False) and not mcs_only: heur[g][0] += mwh / (min(1, .75 * gf) * 8760)
                else: heur[g][1] += mwh / (min(1, .23 * gf) * 8760)
        oc, om = sum(v[0] for v in opt.values()), sum(v[1] for v in opt.values())
        hc, hm = sum(v[0] for v in heur.values()), sum(v[1] for v in heur.values())
        dpt = sum(max(0, opt[g][0] - heur[g][0]) + max(0, opt[g][1] - heur[g][1]) for g in set(opt) | set(heur))
        bet = float(tb[YR]['BEV']) / (float(tb[YR]['BEV']) + float(tb[YR]['ICEV'])) * 100
        row[YR] = dict(E=E / 1e3, opt=oc + om, ccs=oc / (oc + om) * 100, heur=hc + hm, dcap=((oc + om) / (hc + hm) - 1) * 100,
                       ld=dpt / (oc + om) * 100, bet=bet, brenner=sum(sum(opt[g]) for g in BR) / (oc + om) * 100, brenner_e=EB / E * 100, brenner_h=HB / E * 100)
    out.append(row)
    b = out[0]
    print(f"{lab:24s} dObj {(row['obj']/b['obj']-1)*100:+6.2f}% | " + ' || '.join(
        f"{Y}: BET {row[Y]['bet']:3.0f}% E {row[Y]['E']:5.0f} opt {row[Y]['opt']:4.0f} heur {row[Y]['heur']:4.0f} dCap {row[Y]['dcap']:+4.0f}% LD {row[Y]['ld']:3.0f}% CCS {row[Y]['ccs']:3.0f}% Br {row[Y]['brenner']:3.0f}% BrE {row[Y]['brenner_e']:3.0f}% (heur {row[Y]['brenner_h']:3.0f}%)"
        for Y in (2040, 2048)), flush=True)
json.dump(out, open('results/final/robustness_table.json', 'w'), indent=1)
