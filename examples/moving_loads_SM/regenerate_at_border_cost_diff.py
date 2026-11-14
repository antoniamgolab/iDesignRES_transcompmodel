"""
Regenerate at_border_cost_difference_by_surcharge.pdf:
Electricity price difference (ct/kWh) between Austrian and neighbouring
border regions under locational cost premiums (fast charging, REPowerEU++).

Two panels: AT vs DE (left), AT vs IT (right).
Shaded areas: green below zero (AT cheaper), pink above zero (AT more expensive).
"""

import yaml
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path

# -- Font settings (matching other manuscript figures) -------------------------
plt.rcParams.update(plt.rcParamsDefault)
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "serif",
    "font.serif": "mathpazo",
    "font.size": 18,
})

# -- Paths --------------------------------------------------------------------
BASE_PATH = Path(__file__).resolve().parent
INPUT_DIR = BASE_PATH / 'input_data'
FIG_DIR = BASE_PATH / 'figures'
MANUSCRIPT_IMG = BASE_PATH.parent.parent / 'Moving-electricity-loads-in-long-term-decarbonizations' / 'images'

# -- Node IDs for border regions ----------------------------------------------
AT_NODES = [2, 3]       # AT33 Tyrol, AT34 Vorarlberg
DE_NODES = [7, 8, 14]   # DE14 Tübingen, DE21 Upper Bavaria, DE27 Swabia
IT_NODES = [51, 58, 59, 60]  # ITC4 Lombardy, ITH1-3

YEARS = list(range(2020, 2061))
MODEL_YEARS = list(range(2020, 2061, 4))  # for x-ticks


def load_yaml(fpath):
    with open(fpath, 'r') as f:
        return yaml.safe_load(f)


def avg_elec_price(fc_list, nodes, infr_type=1):
    """Average electricity cost_per_kWh across given nodes for fast charging."""
    prices = []
    for entry in fc_list:
        if (entry['fuel'] == 'electricity'
                and entry['fueling_infr_type_id'] == infr_type
                and entry['location'] in nodes):
            prices.append(entry['cost_per_kWh'])
    if not prices:
        return None
    return np.mean(prices, axis=0)


# -- Load baseline (REPowerEU++ = scenario_002) --------------------------------
print('Loading baseline prices...')
base_fc = load_yaml(INPUT_DIR / 'uncertainty_scenarios' / 'scenario_002' / 'FuelCost.yaml')
at_base = avg_elec_price(base_fc, AT_NODES)
de_base = avg_elec_price(base_fc, DE_NODES)
it_base = avg_elec_price(base_fc, IT_NODES)

# -- Surcharge scenarios (electricity price premiums only) ---------------------
surcharge_scenarios = {
    '+1 ct/kWh': INPUT_DIR / 'at_surcharge_scenarios' / 'at_elec_low' / 'FuelCost.yaml',
    '+2 ct/kWh': INPUT_DIR / 'at_surcharge_scenarios' / 'at_elec_med' / 'FuelCost.yaml',
    '+4 ct/kWh': INPUT_DIR / 'at_surcharge_scenarios' / 'at_elec_high' / 'FuelCost.yaml',
}

surcharge_at_prices = {}
for label, fpath in surcharge_scenarios.items():
    print(f'  Loading {label}...')
    fc = load_yaml(fpath)
    surcharge_at_prices[label] = avg_elec_price(fc, AT_NODES)

# -- Compute price differences (AT - neighbour), in ct/kWh --------------------
# Positive = AT more expensive; Negative = AT cheaper
years_arr = np.array(YEARS)

baseline_diff_de = (at_base - de_base) * 100  # ct/kWh
baseline_diff_it = (at_base - it_base) * 100

surcharge_diffs_de = {}
surcharge_diffs_it = {}
for label, at_prices in surcharge_at_prices.items():
    surcharge_diffs_de[label] = (at_prices - de_base) * 100
    surcharge_diffs_it[label] = (at_prices - it_base) * 100

# -- Plot ----------------------------------------------------------------------
print('Generating figure...')

colors = {
    'Baseline': '#2c3e50',
    '+1 ct/kWh': '#1abc9c',
    '+2 ct/kWh': '#f39c12',
    '+4 ct/kWh': '#e74c3c',
}
linestyles = {
    'Baseline': '-',
    '+1 ct/kWh': '--',
    '+2 ct/kWh': '-.',
    '+4 ct/kWh': ':',
}
linewidths = {
    'Baseline': 2.5,
    '+1 ct/kWh': 2.0,
    '+2 ct/kWh': 2.0,
    '+4 ct/kWh': 2.5,
}

fig, (ax_de, ax_it) = plt.subplots(1, 2, figsize=(14, 5), sharey=True)

for ax, diff_base, surcharge_diffs, title in [
    (ax_de, baseline_diff_de, surcharge_diffs_de, r'\textbf{AT vs DE border regions}'),
    (ax_it, baseline_diff_it, surcharge_diffs_it, r'\textbf{AT vs IT border regions}'),
]:
    # Shaded areas for baseline: green below 0, pink above 0
    ax.fill_between(years_arr, 0, diff_base,
                    where=diff_base <= 0,
                    interpolate=True,
                    color='#2ecc71', alpha=0.15)
    ax.fill_between(years_arr, 0, diff_base,
                    where=diff_base >= 0,
                    interpolate=True,
                    color='#e74c3c', alpha=0.15)

    # Zero line
    ax.axhline(0, color='gray', linewidth=0.8, linestyle='-', alpha=0.5)

    # Baseline line
    ax.plot(years_arr, diff_base, color=colors['Baseline'],
            linewidth=linewidths['Baseline'], linestyle=linestyles['Baseline'],
            label='Baseline', zorder=5)

    # Surcharge lines
    for label in ['+1 ct/kWh', '+2 ct/kWh', '+4 ct/kWh']:
        ax.plot(years_arr, surcharge_diffs[label],
                color=colors[label], linewidth=linewidths[label],
                linestyle=linestyles[label], label=label, zorder=4)

    ax.set_title(title, fontsize=16)
    ax.set_xlabel('Year', fontsize=14)
    ax.set_xlim(2020, 2052)
    ax.legend(fontsize=12, loc='best')
    ax.grid(True, alpha=0.2, linestyle='--')

ax_de.set_ylabel('Electricity price difference\n(ct/kWh)', fontsize=14)

# Annotation below
fig.text(0.5, -0.02,
         r'\textit{Negative: AT cheaper than neighbour $|$ Positive: AT more expensive}',
         ha='center', fontsize=13, color='gray')

plt.tight_layout()

# -- Save ----------------------------------------------------------------------
for dst in [FIG_DIR, MANUSCRIPT_IMG]:
    dst.mkdir(parents=True, exist_ok=True)
    fig.savefig(dst / 'at_border_cost_difference_by_surcharge.pdf', bbox_inches='tight')
fig.savefig(FIG_DIR / 'at_border_cost_difference_by_surcharge.png', bbox_inches='tight', dpi=150)
plt.close()
print('Saved: at_border_cost_difference_by_surcharge.pdf')
print('Done.')
