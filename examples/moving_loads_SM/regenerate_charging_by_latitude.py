"""
Standalone script to regenerate charging_by_latitude_multi_year.pdf
showing BEV CHARGED ENERGY (from s_dict), NOT infrastructure capacity.
"""
import yaml, pathlib, re
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
from scipy.ndimage import gaussian_filter1d

BASE = pathlib.Path(__file__).resolve().parent
INPUT_BASE = BASE / 'input_data/uncertainty_scenarios_v2'
RESULTS_PATH = BASE / 'results/uncertainty_scenarios_v2'
FIG_DIR = BASE / 'figures'
FIG_DIR.mkdir(exist_ok=True)

# Font settings (match manuscript)
plt.rcParams.update({
    "font.family": "serif",
    'font.serif': ['Times New Roman', 'serif'],
    'font.size': 20,
    'axes.labelsize': 20,
})
# Try LaTeX if available
try:
    plt.rcParams["text.usetex"] = True
    plt.rcParams['font.serif'] = 'Times New Roman'
except Exception:
    pass

SCENARIOS = {
    'scenario_000': {'name': 'Go RES', 'color': '#2C3E50', 'ls': '-', 'lw': 1.8},           # dark navy, solid
    'scenario_001': {'name': 'NECPEssentials', 'color': '#8E44AD', 'ls': '--', 'lw': 1.5},  # purple, dashed
    'scenario_002': {'name': 'REPowerEU++', 'color': '#3498DB', 'ls': '-', 'lw': 1.5},      # blue, solid
    'scenario_003': {'name': 'Trinity', 'color': '#E67E22', 'ls': ':', 'lw': 1.8},          # orange, dotted
}

# Auto-detect latest s_dict files
import glob as _glob
S_FILES = {}
for sc in SCENARIOS:
    s_files = sorted(_glob.glob(str(RESULTS_PATH / sc / '*_s_dict.yaml')))
    if s_files:
        S_FILES[sc] = pathlib.Path(s_files[-1]).name
    else:
        print(f"WARNING: No s_dict found for {sc}")

# New tuple format: (year, (p, r, k, geo), tv, (fuel, infr), gen): value
USE_TUPLE_FORMAT = True

# ── Load geographic elements ───────────────────────────────────────
print("Loading geographic data...")
with open(BASE / 'input_data/fixed_nuts_2/GeographicElement.yaml') as f:
    geo_data = yaml.safe_load(f)
geo_id_to_lat = {g['id']: g['coordinate_lat'] for g in geo_data}

# No prkg mapping needed — new tuple format includes geo_id directly

# ── Load s_dict and aggregate BEV energy by (year, geo_id) ────
# Tuple format: (year, (p, r, k, geo), tv, (fuel, infr), gen): value
tuple_re = re.compile(
    r'\((\d+),\s*\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\),\s*(\d+),\s*\((\d+),\s*(\d+)\),\s*(\d+)\):\s*([\d.eE+-]+)')

s_energy_results = {}
for scenario_id, config in SCENARIOS.items():
    if scenario_id not in S_FILES:
        continue
    print(f"Processing {scenario_id} ({config['name']})...")

    s_file = RESULTS_PATH / scenario_id / S_FILES[scenario_id]
    if not s_file.exists():
        print(f"  Warning: {s_file} not found")
        continue

    energy_by_year_geo = defaultdict(float)
    total_lines = 0
    bev_lines = 0

    with open(s_file) as f:
        for line in f:
            total_lines += 1
            m = tuple_re.match(line.strip())
            if not m:
                continue
            year = int(m.group(1))
            geo_id = int(m.group(5))
            fuel = int(m.group(7))
            infr = int(m.group(8))
            val = float(m.group(10))

            if val < 1e-6 or fuel != 0 or infr not in {1, 2}:
                continue

            bev_lines += 1
            energy_by_year_geo[(year, geo_id)] += val

    s_energy_results[scenario_id] = {
        's_energy': dict(energy_by_year_geo),
        'config': config,
    }
    print(f"  {total_lines} total, {bev_lines} BEV, {len(energy_by_year_geo)} (year,geo) pairs")

print(f"\nLoaded s energy for {len(s_energy_results)} scenarios")

# ── Helper: aggregate by latitude ──────────────────────────────────
def calculate_energy_by_latitude_from_s(s_energy, target_year):
    # Start with ALL geo nodes at zero, then fill in nonzero values
    energy_by_lat = {lat: 0.0 for lat in geo_id_to_lat.values()}
    for (year, geo_id), val in s_energy.items():
        if year != target_year:
            continue
        lat = geo_id_to_lat.get(geo_id)
        if lat is None:
            continue
        energy_by_lat[lat] += val
    result = [(lat, mwh / 1e3) for lat, mwh in energy_by_lat.items()]
    result.sort(key=lambda x: x[0])
    return result

# ── Plot: multi-year charged energy by latitude (v2, shared x-axis scale) ──
print("\nPlotting BEV charged energy by latitude...")
years = [2032, 2040, 2048]
fig, axes = plt.subplots(1, 3, figsize=(12, 7), sharey=True, sharex=True)

scenario_order = ['scenario_000', 'scenario_003', 'scenario_002', 'scenario_001']
country_lats = {'IT': 42.5, 'AT': 47.5, 'DE': 51.0, 'DK': 56.0, 'SE': 62.0, 'NO': 64.0}

all_lat_data = {}
for year in years:
    all_lat_data[year] = {}
    for scenario_id in s_energy_results:
        lat_data = calculate_energy_by_latitude_from_s(
            s_energy_results[scenario_id]['s_energy'], year)
        if lat_data:
            all_lat_data[year][scenario_id] = lat_data

# First pass: compute global maximum across all panels
global_max = 0
for i, (year, ax) in enumerate(zip(years, axes)):
    lat_data = all_lat_data[year]
    for scenario_id in scenario_order:
        if scenario_id not in lat_data:
            continue
        config = s_energy_results[scenario_id]['config']
        data = lat_data[scenario_id]
        if len(data) < 3:
            continue
        lats = np.array([x[0] for x in data])
        gwh = np.array([x[1] for x in data])
        sort_idx = np.argsort(lats)
        lat_sorted = lats[sort_idx]
        gwh_sorted = gwh[sort_idx]
        gwh_smoothed = gaussian_filter1d(gwh_sorted, sigma=1.5)
        global_max = max(global_max, gwh_smoothed.max())
        label = config['name'] if i == 0 else None
        ax.fill_betweenx(lat_sorted, 0, gwh_smoothed, color=config['color'], alpha=0.06)
        ax.plot(gwh_smoothed, lat_sorted, color=config['color'],
                linewidth=config.get('lw', 2.0), linestyle=config.get('ls', '-'), label=label)

    for country, lat in country_lats.items():
        ax.axhline(lat, color='gray', linestyle=':', alpha=0.3, linewidth=0.8)

    ax.set_title(f'{year}', fontweight='bold')
    ax.set_xlabel('Energy charged (GWh)')
    ax.set_ylim(40, 68)
    ax.grid(True, alpha=0.3, axis='x')

# Apply shared x-axis limit
for ax in axes:
    ax.set_xlim(0, global_max * 1.15)

axes[0].set_ylabel('Latitude ($^\\circ$N)')

# Country labels on right
for country, lat in country_lats.items():
    axes[-1].text(1.02, lat, country, transform=axes[-1].get_yaxis_transform(),
                  fontsize=14, fontweight='bold', va='center', ha='left',
                  bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                           edgecolor='#888', alpha=0.9))

fig.legend(loc='lower center', bbox_to_anchor=(0.5, -0.04), ncol=4,
           fontsize=14, framealpha=0.9, frameon=True, edgecolor='#ccc')
plt.tight_layout()

save_path = FIG_DIR / 'charging_by_latitude_multi_year.pdf'
manuscript_img = BASE.parent.parent / 'Moving-electricity-loads-in-long-term-decarbonizations' / 'images'
fig.savefig(save_path, dpi=300, bbox_inches='tight')
fig.savefig(str(save_path).replace('.pdf', '.svg'), bbox_inches='tight')
fig.savefig(manuscript_img / 'charging_by_latitude_multi_year.pdf', bbox_inches='tight')
print(f"Saved to {save_path}")
print(f"Saved to manuscript/images/charging_by_latitude_multi_year.pdf")
plt.close()
