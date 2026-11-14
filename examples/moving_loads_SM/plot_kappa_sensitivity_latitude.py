"""
Kappa sensitivity: side-by-side latitude profiles of charging demand.
"""
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter1d
import yaml, re, glob, pathlib
from collections import defaultdict

BASE = pathlib.Path(__file__).resolve().parent
RESULTS = BASE / 'results' / 'kappa_sensitivity'

# Load geographic data
with open(BASE / 'input_data/fixed_nuts_2/GeographicElement.yaml') as f:
    geo_data = yaml.safe_load(f)
geo_lat = {g['id']: g.get('coordinate_lat', 0) for g in geo_data}
geo_country = {g['id']: g.get('country', '??') for g in geo_data}
geo_nuts2 = {g['id']: g.get('nuts2_region', g.get('name', '')) for g in geo_data}

# Kappa runs
RUNS = [
    ('no_cap', 'No cap (baseline)', '#2C3E50'),
    ('kappa_3.0', r'$\kappa$ = 3.0 (loose)', '#3498DB'),
    ('kappa_1.5', r'$\kappa$ = 1.5 (medium)', '#E67E22'),
    ('kappa_0.5', r'$\kappa$ = 0.5 (tight)', '#E74C3C'),
]

# Parse s_dict for each run
tuple_pat = re.compile(
    r'\((\d+),\s*\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\),\s*(\d+),\s*\((\d+),\s*(\d+)\),\s*(\d+)\):\s*([\d.eE+-]+)')

def parse_charging_by_geo(run_dir, target_year):
    """Parse s_dict, return {geo_id: MWh} for electric charging at target_year."""
    s_files = sorted(glob.glob(str(run_dir / '*_s_dict.yaml')))
    if not s_files:
        return {}
    charging = defaultdict(float)
    with open(s_files[-1]) as f:
        for line in f:
            m = tuple_pat.match(line.strip())
            if not m: continue
            year = int(m.group(1))
            if year != target_year: continue
            geo_id = int(m.group(5))
            fuel, infr = int(m.group(7)), int(m.group(8))
            val = float(m.group(10))
            if val < 1e-6 or fuel != 0 or infr not in {1, 2}: continue
            charging[geo_id] += val
    return dict(charging)

# Country latitude bands for annotation
COUNTRY_BANDS = [
    (39, 44, 'IT South'),
    (44, 47, 'IT North / AT'),
    (47, 49, 'AT / DE South'),
    (49, 52, 'DE'),
    (52, 56, 'DK'),
    (56, 62, 'SE'),
    (62, 72, 'NO / FI'),
]

# Border latitudes for reference lines
BORDERS = {
    'IT-AT': 46.5,
    'AT-DE': 47.5,
    'DE-DK': 54.5,
    'DK-SE': 55.5,
}

for target_year in [2040, 2048]:
    print(f"\n=== Year {target_year} ===")

    fig, axes = plt.subplots(1, 4, figsize=(16, 8), sharey=True, sharex=True)
    fig.suptitle(f'Charging demand by latitude — Year {target_year}\n'
                 r'Kappa sensitivity ($q^+_{ye} \leq \kappa \cdot B_e$)',
                 fontsize=13, fontweight='bold')

    global_max = 0
    all_data = {}

    for run_name, label, color in RUNS:
        run_dir = RESULTS / run_name
        charging = parse_charging_by_geo(run_dir, target_year)

        # Convert to (lat, GWh) pairs
        lat_gwh = []
        for geo_id, mwh in charging.items():
            lat = geo_lat.get(geo_id, 0)
            if lat > 0 and mwh > 0:
                lat_gwh.append((lat, mwh / 1000))  # MWh -> GWh

        lat_gwh.sort(key=lambda x: x[0])
        all_data[run_name] = lat_gwh

        if lat_gwh:
            global_max = max(global_max, max(g for _, g in lat_gwh))

        total = sum(g for _, g in lat_gwh)
        print(f"  {run_name}: {len(lat_gwh)} nodes, total={total:.1f} GWh")

    for idx, (run_name, label, color) in enumerate(RUNS):
        ax = axes[idx]
        data = all_data[run_name]

        if not data:
            ax.text(0.5, 0.5, 'No data', ha='center', va='center', transform=ax.transAxes)
            continue

        lats = np.array([x[0] for x in data])
        gwhs = np.array([x[1] for x in data])

        # Sort and smooth
        sort_idx = np.argsort(lats)
        lat_s = lats[sort_idx]
        gwh_s = gwhs[sort_idx]

        if len(lat_s) > 3:
            gwh_smooth = gaussian_filter1d(gwh_s, sigma=1.2)
        else:
            gwh_smooth = gwh_s

        # Area plot
        ax.fill_betweenx(lat_s, 0, gwh_smooth, alpha=0.3, color=color)
        ax.plot(gwh_smooth, lat_s, color=color, linewidth=1.5)

        # Scatter for actual values
        ax.scatter(gwh_s, lat_s, color=color, s=15, zorder=5, alpha=0.7)

        # Border lines
        for border_name, border_lat in BORDERS.items():
            ax.axhline(y=border_lat, color='gray', linestyle='--', alpha=0.3, linewidth=0.8)

        # Labels
        total_gwh = sum(gwhs)
        ax.set_title(f'{label}\n({total_gwh:.0f} GWh total)', fontsize=10)
        ax.set_xlim(0, global_max * 1.15)
        ax.set_ylim(38, 72)

        if idx == 0:
            ax.set_ylabel('Latitude (°N)', fontsize=11)
            # Country labels on y-axis
            for lat_lo, lat_hi, name in COUNTRY_BANDS:
                mid = (lat_lo + lat_hi) / 2
                ax.annotate(name, xy=(-0.02, mid), xycoords=('axes fraction', 'data'),
                           fontsize=7, ha='right', va='center', color='gray')

        ax.set_xlabel('GWh/year', fontsize=10)
        ax.grid(axis='y', alpha=0.2)

    plt.tight_layout()
    outfile = BASE / f'kappa_sensitivity_latitude_{target_year}.png'
    plt.savefig(outfile, dpi=200, bbox_inches='tight')
    plt.savefig(outfile.with_suffix('.pdf'), bbox_inches='tight')
    print(f"  Saved: {outfile.name}")
    plt.close()

# ── Also create overlay comparison plot ──
for target_year in [2040, 2048]:
    fig, ax = plt.subplots(figsize=(6, 8))

    for run_name, label, color in RUNS:
        data = all_data.get(run_name)
        if not data:
            # Re-parse if needed (for 2048 after loop)
            run_dir = RESULTS / run_name
            charging = parse_charging_by_geo(run_dir, target_year)
            data = sorted([(geo_lat.get(g, 0), mwh/1000) for g, mwh in charging.items() if geo_lat.get(g, 0) > 0 and mwh > 0])

        if not data: continue

        lats = np.array([x[0] for x in data])
        gwhs = np.array([x[1] for x in data])
        sort_idx = np.argsort(lats)
        lat_s = lats[sort_idx]
        gwh_s = gwhs[sort_idx]

        if len(lat_s) > 3:
            gwh_smooth = gaussian_filter1d(gwh_s, sigma=1.2)
        else:
            gwh_smooth = gwh_s

        lw = 2.5 if run_name == 'kappa_0.5' else (1.5 if run_name == 'no_cap' else 1.0)
        ls = '-' if run_name in ('no_cap', 'kappa_0.5') else '--'
        ax.plot(gwh_smooth, lat_s, color=color, linewidth=lw, linestyle=ls, label=label)

    for border_name, border_lat in BORDERS.items():
        ax.axhline(y=border_lat, color='gray', linestyle=':', alpha=0.4, linewidth=0.8)
        ax.annotate(border_name, xy=(ax.get_xlim()[1]*0.95, border_lat+0.3),
                   fontsize=7, ha='right', color='gray')

    ax.set_ylabel('Latitude (°N)', fontsize=11)
    ax.set_xlabel('Charging demand (GWh/year)', fontsize=11)
    ax.set_title(f'Charging demand by latitude — {target_year}\nKappa sensitivity overlay', fontsize=12)
    ax.set_ylim(38, 72)
    ax.legend(loc='upper right', fontsize=9)
    ax.grid(axis='y', alpha=0.2)

    plt.tight_layout()
    outfile = BASE / f'kappa_sensitivity_overlay_{target_year}.png'
    plt.savefig(outfile, dpi=200, bbox_inches='tight')
    plt.savefig(outfile.with_suffix('.pdf'), bbox_inches='tight')
    print(f"  Saved: {outfile.name}")
    plt.close()

print("\nDone!")
