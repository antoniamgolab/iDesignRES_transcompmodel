"""
Reproduce manuscript Figure 7: BET energy charged by latitude for 4 scenarios × 3 years.
Three panels (2032, 2040, 2048), all 4 scenarios overlaid.
"""

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter1d
import yaml, re, glob, pathlib
from collections import defaultdict

BASE = pathlib.Path(__file__).resolve().parent
RESULTS_BASE = BASE / 'results' / 'uncertainty_scenarios_v2'

# Font
matplotlib.rcParams['font.family'] = 'serif'
matplotlib.rcParams['font.serif'] = ['Palatino Linotype', 'Palatino', 'Georgia', 'serif']
matplotlib.rcParams['mathtext.fontset'] = 'cm'
matplotlib.rcParams['font.size'] = 28
matplotlib.rcParams['axes.titlesize'] = 36
matplotlib.rcParams['axes.labelsize'] = 32
matplotlib.rcParams['xtick.labelsize'] = 26
matplotlib.rcParams['ytick.labelsize'] = 26
matplotlib.rcParams['legend.fontsize'] = 24
matplotlib.rcParams['figure.titlesize'] = 40

SCENARIOS = [
    ('scenario_000', 'Go RES',          '#E74C3C', '-',  3.0),
    ('scenario_003', 'Trinity',         '#F39C12', '-',  2.5),
    ('scenario_002', 'REPowerEU++',     '#3498DB', '-',  2.5),
    ('scenario_001', 'NECPEssentials',  '#2ECC71', '--', 2.5),
]

TARGET_YEARS = [2032, 2040, 2048]

# Load geo data
with open(BASE / 'input_data/fixed_nuts_2/GeographicElement.yaml') as f:
    geo_data = yaml.safe_load(f)
geo_lat = {g['id']: g.get('coordinate_lat', 0) for g in geo_data}
geo_country = {g['id']: g.get('country', '??') for g in geo_data}

tuple_pat = re.compile(
    r'\((\d+),\s*\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\),\s*(\d+),\s*\((\d+),\s*(\d+)\),\s*(\d+)\):\s*([\d.eE+-]+)')

# Country latitude labels (right side annotation)
COUNTRY_LATS = [
    (41.5, 'IT'),
    (47.0, 'AT'),
    (50.5, 'DE'),
    (54.5, 'DK'),
    (61.0, 'SE'),
    (68.0, 'NO'),
]

BORDERS = {'IT-AT': 46.5, 'AT-DE': 47.5, 'DE-DK': 54.5, 'DK-SE': 55.5}

# Load charging data
print("Loading scenario data...")
scenario_data = {}
for sc_name, label, color, ls, lw in SCENARIOS:
    s_files = sorted(glob.glob(str(RESULTS_BASE / sc_name / '*_s_dict.yaml')))
    if not s_files:
        print(f"  {sc_name}: MISSING")
        continue
    print(f"  {sc_name} ({label})...", end="", flush=True)
    charging = defaultdict(lambda: defaultdict(float))
    with open(s_files[-1]) as f:
        for line in f:
            m = tuple_pat.match(line.strip())
            if not m: continue
            year = int(m.group(1))
            geo_id = int(m.group(5))
            fuel, infr = int(m.group(7)), int(m.group(8))
            val = float(m.group(10))
            if val < 1e-6 or fuel != 0 or infr not in {1, 2}: continue
            charging[geo_id][year] += val
    scenario_data[sc_name] = charging
    print(" OK")

# Create figure
fig, axes = plt.subplots(1, 3, figsize=(28, 12), sharey=True)

for yi, target_year in enumerate(TARGET_YEARS):
    ax = axes[yi]

    global_max = 0
    for sc_name, label, color, ls, lw in SCENARIOS:
        if sc_name not in scenario_data: continue
        lat_gwh = sorted([(geo_lat.get(g, 0), scenario_data[sc_name][g].get(target_year, 0)/1000)
                          for g in scenario_data[sc_name]
                          if geo_lat.get(g, 0) > 0 and scenario_data[sc_name][g].get(target_year, 0) > 0])
        if not lat_gwh: continue
        lats = np.array([x[0] for x in lat_gwh])
        gwhs = np.array([x[1] for x in lat_gwh])
        si = np.argsort(lats)
        gs = gaussian_filter1d(gwhs[si], sigma=1.2) if len(lats) > 3 else gwhs[si]
        ax.plot(gs, lats[si], color=color, linestyle=ls, linewidth=lw, label=label)
        global_max = max(global_max, max(gwhs))

    # Border lines
    for bname, blat in BORDERS.items():
        ax.axhline(y=blat, color='lightgray', linestyle='-', alpha=0.5, linewidth=1.0)

    ax.set_title(str(target_year))
    ax.set_xlabel('Energy charged (GWh)')
    ax.set_ylim(38, 72)
    ax.set_xlim(0, None)
    ax.grid(axis='x', alpha=0.15)

    if yi == 0:
        ax.set_ylabel('Latitude (°N)')

    # Country labels on right side of last panel
    if yi == 2:
        ax.legend(loc='lower left', framealpha=0.9)
        for lat, cname in COUNTRY_LATS:
            ax.annotate(cname, xy=(1.02, lat), xycoords=('axes fraction', 'data'),
                       fontsize=26, ha='left', va='center',
                       bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='lightgray', alpha=0.8))

plt.tight_layout()
outfile = BASE / 'figure7_latitude_4scenarios.png'
plt.savefig(outfile, dpi=200, bbox_inches='tight')
plt.savefig(outfile.with_suffix('.pdf'), bbox_inches='tight')
print(f"\nSaved: {outfile.name}")
plt.close()

# Print summary
print("\nCharging demand totals (GWh):")
for target_year in TARGET_YEARS:
    print(f"  {target_year}:", end="")
    for sc_name, label, _, _, _ in SCENARIOS:
        if sc_name not in scenario_data: continue
        total = sum(scenario_data[sc_name][g].get(target_year, 0) for g in scenario_data[sc_name]) / 1000
        print(f"  {label}={total:.0f}", end="")
    print()

print("\nDone!")
