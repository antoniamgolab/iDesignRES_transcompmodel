"""
Read the 3 diagnostic runs and report objective + ITH1 cumulative units side by side.
"""
import re, glob, yaml, pathlib
from collections import defaultdict

BASE = pathlib.Path(__file__).resolve().parent
ci3_pat = re.compile(r'CartesianIndex\((\d+),\s*(\d+),\s*(\d+)\):\s*([\d.eE+-]+)')

with open(BASE / 'input_data/fixed_nuts_2/GeographicElement.yaml') as f:
    geo_data = yaml.safe_load(f)
geo_name = {g['id']: g.get('name', '?').replace('nuts2_', '') for g in geo_data}
ITH1_ID = next((gid for gid, n in geo_name.items() if n == 'ITH1'), None)

MODELED_YEARS = list(range(2020, 2064, 4))
y_idx_to_year = {i + 1: y for i, y in enumerate(MODELED_YEARS)}
CHARGER_KW = {1: 100, 2: 1000}

def analyze(run_dir):
    summary_file = run_dir / 'summary_stats.yaml'
    if not summary_file.exists():
        return None
    with open(summary_file) as f:
        summary = yaml.safe_load(f)
    q_files = sorted(glob.glob(str(run_dir / '*_q_fuel_infr_plus_dict.yaml')))
    per_year = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    if q_files:
        with open(q_files[-1]) as f:
            for line in f:
                m = ci3_pat.match(line.strip())
                if not m:
                    continue
                yi, fi, pos = int(m.group(1)), int(m.group(2)), int(m.group(3))
                val_kw = float(m.group(4))
                if val_kw < 1e-3 or fi == 3:
                    continue
                yr = y_idx_to_year.get(yi)
                if yr is None:
                    continue
                per_year[pos - 1][yr][fi] += val_kw
    return summary, per_year

def ith1_cum(per_year, year):
    cum_mcs_units = 0
    cum_ccs_units = 0
    if ITH1_ID is None or ITH1_ID not in per_year:
        return 0, 0, 0
    for y, fis in per_year[ITH1_ID].items():
        if y > year:
            continue
        cum_ccs_units += fis.get(1, 0) / 100
        cum_mcs_units += fis.get(2, 0) / 1000
    return cum_mcs_units, cum_ccs_units, cum_mcs_units + cum_ccs_units

RUNS = ['run_a_clean', 'run_b_clean', 'run_c_reordered']
results = {}
for r in RUNS:
    ar = analyze(BASE / 'results' / 'baseline_canonical' / r)
    if ar is None:
        print(f"{r}: MISSING")
        continue
    results[r] = ar

print(f"\n{'='*92}")
print(f"BASELINE DIAGNOSTIC: 3 runs, all with κᵖʷʳ=0.5, κˢᵖᵃᶜᵉ=0.0005")
print(f"{'='*92}")
print(f"{'Run':<22s} {'Obj (bn EUR)':>15s} {'ITH1 MCS @2048':>16s} {'ITH1 CCS @2048':>16s} {'ITH1 total':>12s}")
print("-" * 92)
for r in RUNS:
    if r not in results:
        continue
    summary, py = results[r]
    obj = float(summary['objective_value']) / 1e9
    mcs, ccs, tot = ith1_cum(py, 2048)
    print(f"{r:<22s} {obj:>15.6f} {mcs:>16.1f} {ccs:>16.1f} {tot:>12.1f}")

# Compare A vs B (solver non-determinism) and A vs C (constraint order)
print()
if 'run_a_clean' in results and 'run_b_clean' in results:
    obj_a = float(results['run_a_clean'][0]['objective_value'])
    obj_b = float(results['run_b_clean'][0]['objective_value'])
    _, _, tot_a = ith1_cum(results['run_a_clean'][1], 2048)
    _, _, tot_b = ith1_cum(results['run_b_clean'][1], 2048)
    print(f"A vs B (solver non-determinism): Δ obj = {abs(obj_a-obj_b)/1e6:.2f} M EUR, "
          f"Δ ITH1 2048 total = {abs(tot_a-tot_b):.0f} units")
if 'run_a_clean' in results and 'run_c_reordered' in results:
    obj_a = float(results['run_a_clean'][0]['objective_value'])
    obj_c = float(results['run_c_reordered'][0]['objective_value'])
    _, _, tot_a = ith1_cum(results['run_a_clean'][1], 2048)
    _, _, tot_c = ith1_cum(results['run_c_reordered'][1], 2048)
    print(f"A vs C (constraint order):      Δ obj = {abs(obj_a-obj_c)/1e6:.2f} M EUR, "
          f"Δ ITH1 2048 total = {abs(tot_a-tot_c):.0f} units")

# Reference: existing baselines
print()
print("Reference: existing baseline runs from previous sensitivity batches")
print("-" * 92)
for label, path in [
    ('kappa_sensitivity/kappa_0.5',     'results/kappa_sensitivity/kappa_0.5'),
    ('kspace_sensitivity/kspace_0.0005','results/kspace_sensitivity/kspace_0.0005'),
]:
    ar = analyze(BASE / path)
    if ar is None:
        print(f"{label}: MISSING")
        continue
    summary, py = ar
    obj = float(summary['objective_value']) / 1e9
    mcs, ccs, tot = ith1_cum(py, 2048)
    print(f"{label:<40s} obj={obj:.6f} bn, ITH1 2048 total = {tot:.0f} units")
