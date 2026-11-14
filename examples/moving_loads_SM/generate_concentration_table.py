"""Generate LaTeX table: Go RES baseline vs rail, country-level charging shares."""
import yaml, re, pathlib
from collections import defaultdict

BASE = pathlib.Path(__file__).resolve().parent
INPUT_BASE = BASE / 'input_data/uncertainty_scenarios'
INPUT_RAIL = BASE / 'input_data/uncertainty_scenarios_rail'
RESULTS_BASE = BASE / 'results/uncertainty_scenarios_v2'
RESULTS_RAIL = BASE / 'results/rail'

YEAR_MAPPING = {i: 2020 + (i - 1) * 4 for i in range(1, 15)}
YEAR_TO_INDEX = {v: k for k, v in YEAR_MAPPING.items()}
BEV_FL_IDXS = {1, 2}

with open(BASE / 'input_data/fixed_nuts_2/GeographicElement.yaml') as f:
    geo_data = yaml.safe_load(f)
geo_id_to_country = {g['id']: g.get('country', '') for g in geo_data if g.get('type') == 'node'}

ci_re = re.compile(r'CartesianIndex\((\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\):\s*(.+)')


def build_prkg(input_dir, scenario_id):
    inp = input_dir / scenario_id
    with open(inp / 'Path.yaml') as f:
        paths = yaml.load(f, Loader=yaml.UnsafeLoader)
    with open(inp / 'Odpair.yaml') as f:
        odpairs = yaml.load(f, Loader=yaml.UnsafeLoader)
    path_by_id = {int(p['id']): [int(x) for x in p['sequence']] for p in paths}
    s = set()
    for od in odpairs:
        for geo_id in path_by_id[int(od['path_id'])]:
            s.add((0, int(od['id']), int(od['path_id']), geo_id))
    return {i + 1: t[3] for i, t in enumerate(sorted(s))}


def load_country_energy(results_dir, scenario_id, s_file, input_dir, input_scen):
    prkg = build_prkg(input_dir, input_scen)
    energy = defaultdict(float)
    with open(results_dir / scenario_id / s_file) as f:
        for line in f:
            m = ci_re.match(line.strip())
            if not m:
                continue
            yr_pos = int(m.group(1))
            prkg_pos = int(m.group(2))
            fl_pos = int(m.group(4))
            val = float(m.group(6))
            if fl_pos not in BEV_FL_IDXS:
                continue
            geo_id = prkg.get(prkg_pos)
            if geo_id is None:
                continue
            c = geo_id_to_country.get(geo_id, '')
            if c:
                energy[(yr_pos, c)] += val / 1e3  # GWh
    return dict(energy)


print("Loading Go RES baseline...")
base = load_country_energy(
    RESULTS_BASE, 'scenario_000',
    'scenario_000_cs_2026-02-14_18-25-42_s_dict.yaml',
    INPUT_BASE, 'scenario_000')

print("Loading Go RES + Rail...")
rail = load_country_energy(
    RESULTS_RAIL, 'scenario_004',
    'scenario_004_cs_2026-02-14_20-52-20_s_dict.yaml',
    INPUT_RAIL, 'scenario_004')

countries = ['NO', 'FI', 'SE', 'DK', 'DE', 'AT', 'IT']
years = [2032, 2040, 2048]

# Build table data
print("\n% LaTeX table:\n")

print(r"\begin{table}[H]")
print(r"\centering")
print(r"\caption{Country-level BEV charging demand (GWh) and corridor share (\%) for the Go~RES scenario: road-only baseline vs.\ with modal shift to rail.}")
print(r"\label{tab:rail_concentration}")
print(r"\begin{tabular}{@{}l" + "rrrrrr" + r"@{}}")
print(r"\toprule")

# Header
print(r" & \multicolumn{2}{c}{\textbf{2032}}", end="")
print(r" & \multicolumn{2}{c}{\textbf{2040}}", end="")
print(r" & \multicolumn{2}{c}{\textbf{2048}} \\")
print(r"\cmidrule(lr){2-3} \cmidrule(lr){4-5} \cmidrule(lr){6-7}")
print(r"\textbf{Country} & \textbf{Road} & \textbf{+Rail} & \textbf{Road} & \textbf{+Rail} & \textbf{Road} & \textbf{+Rail} \\")
print(r"\midrule")

for year in years:
    yi = YEAR_TO_INDEX[year]
    b_total = sum(base.get((yi, c), 0) for c in countries)
    r_total = sum(rail.get((yi, c), 0) for c in countries)

for c in countries:
    parts = []
    for year in years:
        yi = YEAR_TO_INDEX[year]
        b_total = sum(base.get((yi, cc), 0) for cc in countries)
        r_total = sum(rail.get((yi, cc), 0) for cc in countries)
        bv = base.get((yi, c), 0)
        rv = rail.get((yi, c), 0)
        bp = bv / b_total * 100 if b_total > 0 else 0
        rp = rv / r_total * 100 if r_total > 0 else 0
        parts.append(f"{bv:.0f} ({bp:.1f}\\%)")
        parts.append(f"{rv:.0f} ({rp:.1f}\\%)")
    print(f"  {c} & " + " & ".join(parts) + r" \\")

print(r"\addlinespace")

# Totals
parts = []
for year in years:
    yi = YEAR_TO_INDEX[year]
    b_total = sum(base.get((yi, c), 0) for c in countries)
    r_total = sum(rail.get((yi, c), 0) for c in countries)
    delta_pct = (r_total - b_total) / b_total * 100
    parts.append(f"{b_total:.0f}")
    parts.append(f"{r_total:.0f} ({delta_pct:+.0f}\\%)")
print(r"  \textit{Total (GWh)} & " + " & ".join(parts) + r" \\")

# DE share
parts = []
for year in years:
    yi = YEAR_TO_INDEX[year]
    b_total = sum(base.get((yi, c), 0) for c in countries)
    r_total = sum(rail.get((yi, c), 0) for c in countries)
    de_b = base.get((yi, 'DE'), 0) / b_total * 100
    de_r = rail.get((yi, 'DE'), 0) / r_total * 100
    parts.append(f"{de_b:.1f}\\%")
    parts.append(f"{de_r:.1f}\\%")
print(r"  \textit{DE share} & " + " & ".join(parts) + r" \\")

print(r"\bottomrule")
print(r"\end{tabular}")
print(r"\end{table}")

# Also print a simpler version focusing on shares only
print("\n\n% Alternative: shares-only table\n")
print(r"\begin{table}[H]")
print(r"\centering")
print(r"\caption{Country-level share of BEV charging demand (\%) for the Go~RES scenario, comparing road-only (R) and road+rail (R+R) configurations. $\Delta$ denotes the change in percentage points.}")
print(r"\label{tab:rail_charging_shift}")
print(r"\begin{tabular}{@{}l" + "rrr" * 3 + r"@{}}")
print(r"\toprule")
print(r" & \multicolumn{3}{c}{\textbf{2032}}", end="")
print(r" & \multicolumn{3}{c}{\textbf{2040}}", end="")
print(r" & \multicolumn{3}{c}{\textbf{2048}} \\")
print(r"\cmidrule(lr){2-4} \cmidrule(lr){5-7} \cmidrule(lr){8-10}")
print(r"\textbf{Country} & \textbf{R} & \textbf{R{+}R} & \textbf{$\Delta$}", end="")
print(r" & \textbf{R} & \textbf{R{+}R} & \textbf{$\Delta$}", end="")
print(r" & \textbf{R} & \textbf{R{+}R} & \textbf{$\Delta$} \\")
print(r"\midrule")

for c in countries:
    parts = [f"  {c}"]
    for year in years:
        yi = YEAR_TO_INDEX[year]
        b_total = sum(base.get((yi, cc), 0) for cc in countries)
        r_total = sum(rail.get((yi, cc), 0) for cc in countries)
        bp = base.get((yi, c), 0) / b_total * 100
        rp = rail.get((yi, c), 0) / r_total * 100
        dp = rp - bp
        sign = "$+$" if dp >= 0 else "$-$"
        parts.append(f"{bp:.1f}")
        parts.append(f"{rp:.1f}")
        parts.append(f"{sign}{abs(dp):.1f}")
    print(" & ".join(parts) + r" \\")

print(r"\addlinespace")
# Total GWh row
parts = [r"  \textit{Total (GWh)}"]
for year in years:
    yi = YEAR_TO_INDEX[year]
    bt = sum(base.get((yi, c), 0) for c in countries)
    rt = sum(rail.get((yi, c), 0) for c in countries)
    dp = (rt - bt) / bt * 100
    parts.append(f"{bt:.0f}")
    parts.append(f"{rt:.0f}")
    sign = "$+$" if dp >= 0 else "$-$"
    parts.append(f"{sign}{abs(dp):.0f}\\%")
print(" & ".join(parts) + r" \\")

print(r"\bottomrule")
print(r"\end{tabular}")
print(r"\end{table}")

print("\nDone.")
