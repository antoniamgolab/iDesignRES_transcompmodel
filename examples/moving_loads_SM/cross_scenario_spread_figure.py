"""Cross-scenario spread in BEV charging demand by NUTS-2 region.

Two-row bar chart, ordered north-to-south by latitude.
Bar height = max cross-scenario spread (GWh), color = year of max spread.
"""
import yaml, re, pathlib
from collections import defaultdict
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ['Times New Roman', 'serif'],
    "font.size": 12,
})
try:
    plt.rcParams["text.usetex"] = True
    plt.rcParams["font.serif"] = "mathpazo"
except Exception:
    pass

BASE = pathlib.Path(__file__).resolve().parent
INPUT_BASE = BASE / 'input_data/uncertainty_scenarios_v2'
RESULTS_BASE = BASE / 'results/uncertainty_scenarios_v2'

MODELED_YEARS = list(range(2020, 2064, 4))

# Load geo
with open(BASE / 'input_data/fixed_nuts_2/GeographicElement.yaml') as f:
    geo_data = yaml.safe_load(f)

geo_id_to_nuts2 = {}
geo_id_to_country = {}
node_lat = {}
for g in geo_data:
    if g.get('type') == 'node':
        geo_id_to_nuts2[g['id']] = g.get('nuts2_region', '')
        geo_id_to_country[g['id']] = g.get('country', '')
        node_lat[g['id']] = g.get('coordinate_lat', 0)

# NUTS-2 average latitude
nuts2_lats = defaultdict(list)
for gid, n2 in geo_id_to_nuts2.items():
    if n2:
        nuts2_lats[n2].append(node_lat.get(gid, 0))
nuts2_avg_lat = {n2: np.mean(lats) for n2, lats in nuts2_lats.items()}

# NUTS-2 country
nuts2_country = {}
for n2 in nuts2_avg_lat:
    nuts2_country[n2] = n2[:2]

# Tuple format parser
tuple_re = re.compile(
    r'\((\d+),\s*\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\),\s*(\d+),\s*\((\d+),\s*(\d+)\),\s*(\d+)\):\s*([\d.eE+-]+)')

import glob as _glob

def load_nuts2_energy(results_dir, scenario_id):
    """Load BEV charging energy by (year, nuts2) from tuple-format s_dict."""
    s_files = sorted(_glob.glob(str(results_dir / scenario_id / '*_s_dict.yaml')))
    if not s_files:
        print(f"  WARNING: no s_dict for {scenario_id}")
        return {}
    energy = defaultdict(float)
    with open(s_files[-1]) as f:
        for line in f:
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
            n2 = geo_id_to_nuts2.get(geo_id, '')
            if n2:
                energy[(year, n2)] += val / 1e3  # GWh
    return dict(energy)


# Load all 4 road-only scenarios
scenarios = ['scenario_000', 'scenario_001', 'scenario_002', 'scenario_003']

all_data = {}
for scen_id in scenarios:
    print(f"Loading {scen_id}...")
    all_data[scen_id] = load_nuts2_energy(RESULTS_BASE, scen_id)

# Collect all NUTS-2 regions
all_nuts2 = set()
for data in all_data.values():
    for (year, n2) in data:
        all_nuts2.add(n2)

# For each NUTS-2, find max spread across scenarios and the year it occurs
# Only consider years up to 2048 (exclude post-2050)
years_all = [y for y in MODELED_YEARS if y <= 2048]
spread_info = {}  # n2 -> (max_spread_gwh, year_of_max)

for n2 in all_nuts2:
    max_spread = 0
    max_year = 2032
    for year in years_all:
        vals = [data.get((year, n2), 0) for data in all_data.values()]
        spread = max(vals) - min(vals)
        if spread > max_spread:
            max_spread = spread
            max_year = year
    spread_info[n2] = (max_spread, max_year)

# Sort by latitude: north to south (descending latitude)
sorted_nuts2 = sorted(all_nuts2, key=lambda n2: -nuts2_avg_lat.get(n2, 0))

# Filter to regions with non-trivial spread
sorted_nuts2 = [n2 for n2 in sorted_nuts2 if spread_info[n2][0] > 0.1]

# Split into three rows
n = len(sorted_nuts2)
third1 = n // 3
third2 = 2 * n // 3
row1 = sorted_nuts2[:third1]       # northern third
row2 = sorted_nuts2[third1:third2] # central third
row3 = sorted_nuts2[third2:]       # southern third

# Color map by year
unique_years = sorted(set(y for _, y in spread_info.values()))
year_colors = {
    2024: '#4daf4a', 2028: '#4daf4a',
    2032: '#66c2a5', 2036: '#1b9e77',
    2040: '#e6ab02', 2044: '#d95f02',
    2048: '#e7298a', 2052: '#7570b3',
    2056: '#6a3d9a', 2060: '#1f78b4',
    2020: '#a6cee3', 2064: '#b2df8a', 2068: '#fb9a99', 2072: '#fdbf6f',
}

# Country boundaries for vertical lines
countries_order = ['NO', 'FI', 'SE', 'DK', 'DE', 'AT', 'IT']


def plot_row(ax, regions, label_threshold=15):
    spreads = [spread_info[n2][0] for n2 in regions]
    years_bar = [spread_info[n2][1] for n2 in regions]
    colors = [year_colors.get(y, '#999999') for y in years_bar]

    x = np.arange(len(regions))
    ax.bar(x, spreads, color=colors, edgecolor='none', width=0.8)

    # Labels for high-spread regions — place inside bars to avoid clipping
    for i, (n2, s) in enumerate(zip(regions, spreads)):
        if s > label_threshold:
            ax.text(i, s + 0.3, n2, ha='center', va='bottom', fontsize=10)

    # X-axis labels
    ax.set_xticks(x)
    ax.set_xticklabels(regions, rotation=90, fontsize=9)
    ax.set_ylabel('Max spread (GWh)', fontsize=12)

    # Country separators removed for cleaner appearance

    # Add top margin so labels don't clip
    ymax = max(spreads) if spreads else 1
    ax.set_ylim(0, ymax * 1.18)


# Create figure — three rows
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 10), constrained_layout=True)

fig.suptitle('Cross-scenario spread in BEV charging demand by NUTS-2 region (north $\\rightarrow$ south)',
             fontsize=16, fontweight='bold')

plot_row(ax1, row1, label_threshold=12)
ax1.set_title('Scandinavia \\& northern Germany', fontsize=13, fontstyle='italic')

plot_row(ax2, row2, label_threshold=12)
ax2.set_title('Central Germany', fontsize=13, fontstyle='italic')

plot_row(ax3, row3, label_threshold=12)
ax3.set_title('Southern Germany, Austria \\& Italy', fontsize=13, fontstyle='italic')

# Legend for years — placed below the bottom subplot
from matplotlib.patches import Patch
legend_years = sorted(set(spread_info[n2][1] for n2 in sorted_nuts2))
legend_elements = [Patch(facecolor=year_colors.get(y, '#999'), label=str(y)) for y in legend_years]
fig.legend(handles=legend_elements, title='Year of max spread', fontsize=11,
           title_fontsize=12, loc='lower center', ncol=len(legend_years),
           bbox_to_anchor=(0.5, -0.06), frameon=True)

# Save
fig.savefig(BASE / 'figures/cross_scenario_spread_by_nuts2.pdf', bbox_inches='tight')
fig.savefig(BASE / 'figures/cross_scenario_spread_by_nuts2.png', dpi=200, bbox_inches='tight')
manuscript_img = BASE.parent.parent / 'manuscript' / 'images'
if manuscript_img.exists():
    fig.savefig(manuscript_img / 'cross_scenario_spread_by_nuts2.pdf', bbox_inches='tight')
    print(f"Saved to manuscript/images/cross_scenario_spread_by_nuts2.pdf")
print("Saved.")
