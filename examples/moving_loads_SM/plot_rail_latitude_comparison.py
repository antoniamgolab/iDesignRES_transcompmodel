"""
Separate figure: System-optimal vs with shift to rail — spatial distribution by latitude.
"""
import re, yaml, glob
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from collections import defaultdict
from scipy.ndimage import gaussian_filter1d

matplotlib.rcParams['font.family'] = 'sans-serif'
matplotlib.rcParams['font.sans-serif'] = ['Segoe UI', 'sans-serif']
matplotlib.rcParams['font.size'] = 15

with open('input_data/fixed_nuts_2/GeographicElement.yaml') as f:
    geo_data = yaml.safe_load(f)
geo_lat = {g['id']: g.get('coordinate_lat', 0) for g in geo_data}

tuple_pat = re.compile(
    r'\((\d+),\s*\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\),\s*(\d+),\s*\((\d+),\s*(\d+)\),\s*(\d+)\):\s*"?([\d.eE+-]+)"?')

TARGET_YEAR = 2040
COL_OPT = '#1a5276'
COL_RAIL = '#2e7d32'

def load_energy(s_file, year):
    e = defaultdict(float)
    with open(s_file) as f:
        for line in f:
            m = tuple_pat.match(line.strip())
            if not m: continue
            if int(m.group(1)) != year: continue
            gid = int(m.group(5))
            fu, inf = int(m.group(7)), int(m.group(8))
            val = float(m.group(10))
            if val < 1e-6 or fu != 0 or inf not in {1, 2}: continue
            e[gid] += val
    return dict(e)

sf_s = sorted(glob.glob('results/uncertainty_scenarios_v2/scenario_000/*_s_dict.yaml'))
sf_s_rail = sorted(glob.glob('results/uncertainty_scenarios_v2_rail/scenario_000/*_s_dict.yaml'))

opt_energy = load_energy(sf_s[-1], TARGET_YEAR)
rail_energy = load_energy(sf_s_rail[-1], TARGET_YEAR)

fig, ax = plt.subplots(figsize=(6, 6))
sigma = 1.2
country_lats = {'IT': 42.5, 'AT': 47.5, 'DE': 51.0, 'DK': 56.0, 'SE': 62.0, 'NO': 64.0}

for label, geo_dict, color, ls, lw in [
    ('System-optimal', opt_energy, COL_OPT, '-', 2.0),
    ('With shift to rail', rail_energy, COL_RAIL, '--', 1.8),
]:
    e_by_lat = defaultdict(float)
    for gid, mwh in geo_dict.items():
        lat = geo_lat.get(gid)
        if lat is not None:
            e_by_lat[lat] += mwh
    lats = np.array(sorted(e_by_lat.keys()))
    vals = np.array([e_by_lat[l] for l in lats])
    total = vals.sum()
    vals_norm = vals / total * 100 if total > 0 else vals
    vals_smooth = gaussian_filter1d(vals_norm, sigma)
    ax.fill_betweenx(lats, 0, vals_smooth, alpha=0.15, color=color)
    ax.plot(vals_smooth, lats, color=color, linewidth=lw, linestyle=ls, label=label)

ax.set_ylabel('Latitude')
ax.set_xlabel('Share of total charging demand (%)')
ax.set_title(f'Charging demand: road-only vs with shift to rail\n(Go RES, {TARGET_YEAR})', fontsize=14)
ax.legend(fontsize=12, loc='upper center')
ax.grid(True, alpha=0.2)

for c, lat in country_lats.items():
    ax.axhline(y=lat, color='gray', linestyle=':', alpha=0.3, linewidth=0.5)
    ax.text(ax.get_xlim()[1] * 0.95, lat, c, fontsize=10, ha='right', va='center', color='gray')

plt.tight_layout()
plt.savefig('figures/rail_latitude_comparison.pdf', bbox_inches='tight', dpi=300)
plt.savefig('figures/rail_latitude_comparison.png', bbox_inches='tight', dpi=300)
print('Saved: figures/rail_latitude_comparison.pdf/.png')
plt.close()
