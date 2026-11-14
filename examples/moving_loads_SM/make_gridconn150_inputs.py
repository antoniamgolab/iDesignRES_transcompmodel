"""Final base case inputs: night-price scenarios + one-off grid connection of +150 EUR/kW on CCS (id 1) and MCS (id 2) CAPEX
(Bundesnetzagentur guidance as used in the Fraunhofer megawatt-charging study, World Electr. Veh. J. 17(8):386)."""
import os, shutil, yaml
ADD = 150.0
JOBS = [(f'uncertainty_scenarios_v2_night/scenario_00{i}', f'v4_gridconn150/scenario_00{i}') for i in range(4)] + \
       [(f'uncertainty_scenarios_v2_rail_night/scenario_00{i}', f'v4_gridconn150_rail/scenario_00{i}') for i in range(4)]
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'input_data'))
for src, dst in JOBS:
    if os.path.exists(dst):
        print('exists, skipped:', dst); continue
    shutil.copytree(src, dst)
    p = os.path.join(dst, 'FuelingInfrTypes.yaml')
    fit = yaml.load(open(p), Loader=yaml.UnsafeLoader)
    for f in fit:
        if f['id'] in (1, 2):
            f['cost_per_kW'] = [round(c + ADD, 2) for c in f['cost_per_kW']]
    yaml.dump(fit, open(p, 'w'), sort_keys=False)
    print(dst, {f['id']: f['cost_per_kW'][:2] for f in fit})
