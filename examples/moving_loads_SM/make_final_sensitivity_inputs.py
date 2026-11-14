"""
Build the input folders for the robustness / sensitivity batch with the final base case (2026-10-15).

Base case input: v4_gridconn150/scenario_000 (time-of-day prices, 30 % markup, CAPEX 400 + 150 EUR/kW grid connection).
All variants below add the same +150 EUR/kW so that only the varied parameter differs from the base case.

  surcharge_final/<case>        surcharge_v3/<case>        + 150 EUR/kW
  soc_final/<label>             soc_v3/<label>             + 150 EUR/kW
  battery_final/<label>         battery_v3/<label>         + 150 EUR/kW
  uniform_prices_final          uncertainty_scenarios_v2/scenario_000 with price = 1.3 * (tax + wholesale) (no time-of-day factor) + 150 EUR/kW
  gamma_final/{m25,p25}         base case, utilisation factors gamma (CCS, MCS) x 0.75 / x 1.25            (R6-3)
  freight_final/{low,high}      base case, freight growth relative to the 2030 ETISplus base x 0.5 / x 1.5   (R6-11)
"""
import os, shutil
import yaml

os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'input_data'))
BASE = 'v4_gridconn150/scenario_000'
ADD = 150.0
MARKUP_OLD, MARKUP_NEW = 1.5, 1.3
TYPE_FACTOR_OLD = {1: 1.075, 2: 0.97}  # see make_night_inputs.py
TAX = (0.0277 + 0.1005 + 0.1249 + 0.007 + 0.0787 + 0.01 + 0.0039) / 7
Y0, Y_BASE = 2020, 2030


def load(p):
    return yaml.load(open(p), Loader=yaml.UnsafeLoader)


def dump(obj, p):
    yaml.dump(obj, open(p, 'w'), sort_keys=False)


def copy(src, dst):
    if os.path.exists(dst):
        print('exists, skipped:', dst)
        return False
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns('*.bak*'))
    return True


def add_gridconn(dst):
    p = os.path.join(dst, 'FuelingInfrTypes.yaml')
    fit = load(p)
    for f in fit:
        if f['id'] in (1, 2):
            f['cost_per_kW'] = [round(c + ADD, 2) for c in f['cost_per_kW']]
    dump(fit, p)


# 1) surcharge, SOC, battery: v3 inputs + grid connection
for group_src, group_dst in [('surcharge_v3', 'surcharge_final'), ('soc_v3', 'soc_final'), ('battery_v3', 'battery_final')]:
    for case in sorted(os.listdir(group_src)):
        dst = os.path.join(group_dst, case)
        if copy(os.path.join(group_src, case), dst):
            add_gridconn(dst)
            print(dst)

# 2) uniform prices (no time-of-day factor), same 30 % markup
dst = 'uniform_prices_final/scenario_000'
if copy('uncertainty_scenarios_v2/scenario_000', dst):
    add_gridconn(dst)
    p = os.path.join(dst, 'FuelCost.yaml')
    fc = yaml.safe_load(open(p))
    for c in fc:
        t = c.get('fueling_infr_type_id')
        if c.get('fuel') != 'electricity' or t not in TYPE_FACTOR_OLD:
            continue
        c['cost_per_kWh'] = [float(MARKUP_NEW * (TAX + (pr / MARKUP_OLD / TYPE_FACTOR_OLD[t] - TAX))) for pr in c['cost_per_kWh']]
    yaml.safe_dump(fc, open(p, 'w'), sort_keys=False)
    print(dst)

# 3) utilisation factors
for label, fac in [('m25', 0.75), ('p25', 1.25)]:
    dst = f'gamma_final/{label}'
    if copy(BASE, dst):
        p = os.path.join(dst, 'FuelingInfrTypes.yaml')
        fit = load(p)
        for f in fit:
            if f['id'] in (1, 2):
                g = f['gamma']
                f['gamma'] = [min(1.0, x * fac) for x in g] if isinstance(g, list) else min(1.0, g * fac)
        dump(fit, p)
        print(dst, {f['id']: (f['gamma'][0] if isinstance(f['gamma'], list) else f['gamma']) for f in fit})

# 4) freight growth trajectory relative to the 2030 base year: F'(y) = F(2030) * (1 + k * (F(y)/F(2030) - 1))
for label, k in [('low', 0.5), ('high', 1.5)]:
    dst = f'freight_final/{label}'
    if copy(BASE, dst):
        p = os.path.join(dst, 'Odpair.yaml')
        ods = load(p)
        i0 = Y_BASE - Y0
        for o in ods:
            F = o['F']
            o['F'] = [F[i0] * (1 + k * (f / F[i0] - 1)) for f in F]
        dump(ods, p)
        F0 = load(os.path.join(BASE, 'Odpair.yaml'))[0]['F']
        print(dst, 'OD 0: 2020', round(F0[0]), '->', round(ods[0]['F'][0]), '| 2060', round(F0[-1]), '->', round(ods[0]['F'][-1]))
