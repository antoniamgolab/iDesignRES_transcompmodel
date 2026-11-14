"""
Build all revision (v3) input folders on top of the time-of-day price inputs (2026-10-13).

  uncertainty_scenarios_v2_rail_night/scenario_00X  rail inputs with night/day prices (make_night_inputs.py)
  soc_v3/<label>                                     Go RES night + soc_init/soc_final in Model.yaml
  battery_v3/<label>                                 Go RES night + TechVehicle.yaml of the battery case
(Surcharge cases: make_surcharge_v3.py -> surcharge_v3/<case>.)
"""
import os, shutil, subprocess, sys
import yaml

os.chdir(os.path.dirname(os.path.abspath(__file__)))
BASE = 'input_data/uncertainty_scenarios_v2_night/scenario_000/'


def copy_base(dst):
    os.makedirs(dst, exist_ok=True)
    for f in os.listdir(BASE):
        shutil.copy(BASE + f, os.path.join(dst, f))


# 1) rail inputs
for s in ['000', '001', '002', '003']:
    subprocess.run([sys.executable, 'make_night_inputs.py', f'uncertainty_scenarios_v2_rail/scenario_{s}',
                    f'uncertainty_scenarios_v2_rail_night/scenario_{s}'], check=True)

# 2) SOC sensitivity (labels as in SM_batch_soc_sensitivity.jl; base_50_50 = Go RES night itself)
SOC_RUNS = [(0.3, 0.5, 'low_start_30_50'), (0.7, 0.5, 'high_start_70_50'), (0.5, 0.3, 'low_end_50_30'),
            (0.5, 0.7, 'high_end_50_70'), (0.3, 0.7, 'tight_30_70'), (0.7, 0.3, 'loose_70_30')]
for si, sf, label in SOC_RUNS:
    dst = f'input_data/soc_v3/{label}/'
    copy_base(dst)
    m = yaml.safe_load(open(dst + 'Model.yaml'))
    m['soc_init'], m['soc_final'] = si, sf
    yaml.safe_dump(m, open(dst + 'Model.yaml', 'w'), sort_keys=False)
    print('soc', label, si, sf)

# 3) battery sensitivity (bat_baseline = Go RES night itself)
for label in ['bat_low_70pct', 'bat_high_130pct']:
    dst = f'input_data/battery_v3/{label}/'
    copy_base(dst)
    shutil.copy(f'input_data/battery_sensitivity/{label}/TechVehicle.yaml', dst + 'TechVehicle.yaml')
    print('battery', label)
