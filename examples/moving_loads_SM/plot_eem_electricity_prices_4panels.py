"""
Plot electricity prices for EEM zone-split scenarios.
Single panel: High (20%) spread only.
Other corridor countries shown as a grey band (min-max range);
Germany shown as DE-North and DE-South lines to highlight the split.
"""

import yaml
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

# -- Font settings (matching manuscript figures) --
plt.rcParams.update(plt.rcParamsDefault)
plt.rcParams.update({
    "text.usetex": False,
    "font.family": "serif",
    'font.serif': ['Times New Roman', 'DejaVu Serif'],
    'font.size': 14,
    'mathtext.fontset': 'stix',
})

BASE_PATH = Path(__file__).resolve().parent
INPUT_DIR = BASE_PATH / 'input_data'
EEM_DIR = INPUT_DIR / 'eem_scenarios'
FIG_DIR = BASE_PATH / 'figures'
MANUSCRIPT_IMG = BASE_PATH.parent.parent / 'manuscript' / 'images'
EEM_PAPER_DIR = BASE_PATH.parent.parent / '-EEM-Impact-of-German-electricity-market-zone-splitting-on-spatial-distribution-of-charging-loads'

CORRIDOR_COUNTRIES = ['NO', 'FI', 'SE', 'DK', 'AT', 'IT']
MODEL_YEARS = list(range(2020, 2061))
PLOT_YEARS = list(range(2020, 2061, 4))

CHARGING_MARKUP = 0.30

DE_SOUTH_NUTS2 = {
    'DE11', 'DE12', 'DE13', 'DE14',
    'DE21', 'DE22', 'DE23', 'DE24', 'DE25', 'DE26', 'DE27',
    'DE71', 'DE72', 'DE73',
    'DEA1', 'DEA2', 'DEA3', 'DEA4', 'DEA5',
    'DEB1', 'DEB2', 'DEB3',
    'DEC0',
}
DE_NORTH_NUTS2 = {
    'DE30', 'DE40', 'DE50', 'DE60', 'DE80',
    'DE91', 'DE92', 'DE93', 'DE94',
    'DEF0', 'DED2', 'DED4', 'DED5', 'DEE0', 'DEG0',
}

SCENARIOS_ALL = [
    ("DE_unified",    "Baseline (unified DE)"),
    ("DE_split_low",  "Zone split: 5% spread"),
    ("DE_split_mid",  "Zone split: 10% spread"),
    ("DE_split_high", "Zone split: 20% spread"),
]

# Only plot scenario H-2032: 20% spread, split applied from 2032 onward
SCENARIOS = [
    ("DE_split_high_from2032", "H-2032 (20% spread, split from 2032)"),
]

DIESEL_EMISSION_FACTOR = 0.2664


def load_scenario(scenario_dir):
    """Load electricity prices grouped by country/zone, diesel, and carbon prices."""
    geo_file = scenario_dir / "GeographicElement.yaml"
    fc_file = scenario_dir / "FuelCost.yaml"

    with open(geo_file, encoding='utf-8') as f:
        geos = yaml.safe_load(f)
    with open(fc_file, encoding='utf-8') as f:
        fuels = yaml.safe_load(f)

    geo_id_to_nuts2 = {}
    geo_id_to_country = {}
    carbon_prices = None
    for g in geos:
        geo_id_to_nuts2[g['id']] = g.get('nuts2_region', '')
        geo_id_to_country[g['id']] = g.get('country', '')
        if carbon_prices is None and g.get('carbon_price') is not None:
            carbon_prices = [float(c) for c in g['carbon_price']]

    # Separate collection: DE zones vs other countries
    de_north_prices = []
    de_south_prices = []
    country_prices = {c: [] for c in CORRIDOR_COUNTRIES}
    diesel_prices_all = []

    for fc in fuels:
        loc = fc['location']
        fuel = fc['fuel']
        prices = fc['cost_per_kWh']
        nuts2 = geo_id_to_nuts2.get(loc, '')
        country = geo_id_to_country.get(loc, '')

        if fuel == 'electricity' and fc.get('fueling_infr_type_id') == 1:
            if nuts2 in DE_NORTH_NUTS2:
                de_north_prices.append(prices)
            elif nuts2 in DE_SOUTH_NUTS2:
                de_south_prices.append(prices)
            else:
                for c in CORRIDOR_COUNTRIES:
                    if country == c or nuts2.startswith(c):
                        country_prices[c].append(prices)
                        break
        elif fuel == 'diesel':
            diesel_prices_all.append(prices)

    # Average DE zones
    avg_de_north = np.mean(de_north_prices, axis=0) if de_north_prices else None
    avg_de_south = np.mean(de_south_prices, axis=0) if de_south_prices else None

    # Per-country averages (for computing the range band)
    avg_by_country = {}
    for c, plist in country_prices.items():
        if plist:
            avg_by_country[c] = np.mean(plist, axis=0)

    diesel_base = np.mean(diesel_prices_all, axis=0) if diesel_prices_all else np.zeros(len(MODEL_YEARS))
    if carbon_prices is None:
        carbon_prices = [0.0] * len(MODEL_YEARS)

    return avg_de_north, avg_de_south, avg_by_country, diesel_base, carbon_prices


# -- Load all scenarios --
print('Loading EEM scenarios...')
all_data = {}
for folder, label in SCENARIOS:
    sdir = EEM_DIR / folder
    if not sdir.exists():
        print(f"  WARNING: {sdir} not found, skipping")
        continue
    all_data[folder] = load_scenario(sdir)
    print(f"  Loaded {folder}")

# -- Plot single panel: High (20%) only --
print('Generating figure...')
fig, ax = plt.subplots(1, 1, figsize=(7, 4.5))

# Colours for DE zones
COLOR_NORTH = '#2166ac'   # strong blue
COLOR_SOUTH = '#b2182b'   # strong red
COLOR_BAND  = '#bdbdbd'   # grey for other countries range

folder, label = SCENARIOS[0]

if folder not in all_data:
    ax.set_title(f"{label}\n(not found)")
else:
    avg_de_north, avg_de_south, avg_by_country, diesel_base, carbon_prices = all_data[folder]

    # Diesel at plot years
    d_base = [diesel_base[MODEL_YEARS.index(y)] for y in PLOT_YEARS]
    d_carbon = [
        diesel_base[MODEL_YEARS.index(y)]
        + carbon_prices[MODEL_YEARS.index(y)] * DIESEL_EMISSION_FACTOR * 1e-3
        for y in PLOT_YEARS
    ]

    # Diesel background
    ax.fill_between(PLOT_YEARS, 0, d_base, color='#e0e0e0', alpha=0.5)
    ax.fill_between(PLOT_YEARS, d_base, d_carbon, color='#bdbdbd', alpha=0.4)
    ax.plot(PLOT_YEARS, d_carbon, '--', color='#636363', linewidth=1.2, alpha=0.7)

    # Other countries: compute min-max range (with charging markup)
    other_arrays = []
    for c, avg in avg_by_country.items():
        vals = [avg[MODEL_YEARS.index(y)] * (1 + CHARGING_MARKUP) for y in PLOT_YEARS]
        other_arrays.append(vals)

    if other_arrays:
        other_arr = np.array(other_arrays)
        other_min = other_arr.min(axis=0)
        other_max = other_arr.max(axis=0)
        ax.fill_between(PLOT_YEARS, other_min, other_max,
                         color='#a6bddb', alpha=0.35, edgecolor='none')

    # DE-North and DE-South lines: solid pre-2032 (unified), then diverging
    SPLIT_YEAR = 2032
    if avg_de_north is not None and avg_de_south is not None:
        north_vals = np.array([avg_de_north[MODEL_YEARS.index(y)] * (1 + CHARGING_MARKUP)
                                for y in PLOT_YEARS])
        south_vals = np.array([avg_de_south[MODEL_YEARS.index(y)] * (1 + CHARGING_MARKUP)
                                for y in PLOT_YEARS])
        years_arr = np.array(PLOT_YEARS)

        pre_mask = years_arr <= SPLIT_YEAR
        post_mask = years_arr >= SPLIT_YEAR

        # Unified DE (pre-split): average of North and South (they're identical here)
        unified_vals = (north_vals + south_vals) / 2
        ax.plot(years_arr[pre_mask], unified_vals[pre_mask], '-o',
                color='#4d4d4d', markersize=5, linewidth=2.2, label='DE (unified)')

        # Post-split: North and South diverge
        ax.plot(years_arr[post_mask], north_vals[post_mask], '-s', color=COLOR_NORTH,
                markersize=5, linewidth=2.2, label='DE-North (post-split)')
        ax.plot(years_arr[post_mask], south_vals[post_mask], '-^', color=COLOR_SOUTH,
                markersize=5, linewidth=2.2, label='DE-South (post-split)')

    # Shade the post-split region and mark split year
    ax.axvspan(SPLIT_YEAR, 2060, color='#fff5e6', alpha=0.45, zorder=0)
    ax.axvline(x=SPLIT_YEAR, color='#333333', linestyle='--', linewidth=1.3,
               alpha=0.85, zorder=2)
    ax.annotate(f'Zone split ({SPLIT_YEAR})',
                xy=(SPLIT_YEAR, 0.76), xytext=(SPLIT_YEAR + 0.5, 0.76),
                fontsize=11, ha='left', va='top', color='#333333',
                fontstyle='italic')

    ax.set_ylim(0, 0.80)
    ax.set_xlim(2020, 2060)
    ax.grid(True, alpha=0.2, linestyle='--')
    ax.tick_params(labelsize=11)
    ax.set_xlabel('Year', fontsize=12)
    ax.set_ylabel('Fuel cost (EUR/kWh)', fontsize=12)

# Legend
legend_elements = [
    Line2D([0], [0], color='#4d4d4d', marker='o', markersize=6,
           linewidth=2.2, label='DE (unified, pre-2032)'),
    Line2D([0], [0], color=COLOR_NORTH, marker='s', markersize=6,
           linewidth=2.2, label='DE-North (post-2032)'),
    Line2D([0], [0], color=COLOR_SOUTH, marker='^', markersize=6,
           linewidth=2.2, label='DE-South (post-2032)'),
    Patch(facecolor='#a6bddb', alpha=0.35, label='Other corridor countries (range)'),
    Patch(facecolor='#e0e0e0', alpha=0.5, label='Diesel (base)'),
    Patch(facecolor='#bdbdbd', alpha=0.4, label='Diesel (+ CO$_2$ price)'),
]

ax.legend(handles=legend_elements, loc='upper right', fontsize=9,
          frameon=True, fancybox=True)

plt.tight_layout()

# Save
FIG_DIR.mkdir(exist_ok=True)
fname = 'eem_electricity_prices_by_country_4scenarios'
for dst in [FIG_DIR, MANUSCRIPT_IMG, EEM_PAPER_DIR]:
    if dst.exists():
        fig.savefig(dst / f'{fname}.pdf', bbox_inches='tight')
fig.savefig(FIG_DIR / f'{fname}.png', bbox_inches='tight', dpi=150)
plt.close()
print(f'Saved: figures/{fname}.pdf/.png')
print('Done.')
