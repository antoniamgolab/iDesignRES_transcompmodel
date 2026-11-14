"""Final-setup inputs: copy night-price scenarios and add a one-off grid connection of +250 EUR/kW to CCS (id 1) and MCS (id 2) CAPEX."""
import os, shutil, yaml
ADD = 250.0
JOBS = [(f'uncertainty_scenarios_v2_night/scenario_00{i}', f'v4_gridconn/scenario_00{i}') for i in (1, 2, 3)] + \
       [(f'uncertainty_scenarios_v2_rail_night/scenario_00{i}', f'v4_gridconn_rail/scenario_00{i}') for i in (0, 1, 2, 3)]
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
