"""
Regenerate Figure 6: Electricity prices by country for 4 GENeSYS-MOD scenarios.
Shows electricity price incl. 30% charging markup and diesel price (base + CO2).
Font: LaTeX mathpazo matching other manuscript figures.
Distinct, non-default country colours.
"""

import yaml
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path

# ── Font settings (matching results figures) ─────────────────────────
plt.rcParams.update(plt.rcParamsDefault)
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Segoe UI", "sans-serif"],
    'font.size': 13,
})

# ── Paths ────────────────────────────────────────────────────────────
BASE_PATH = Path(__file__).resolve().parent
INPUT_DIR = BASE_PATH / 'input_data'
FIG_DIR = BASE_PATH / 'figures'
MANUSCRIPT_IMG = BASE_PATH.parent.parent / 'Moving-electricity-loads-in-long-term-decarbonizations' / 'images'

CORRIDOR_COUNTRIES = ['NO', 'FI', 'SE', 'DK', 'DE', 'AT', 'IT']
MODEL_YEARS = list(range(2020, 2061))
PLOT_YEARS = list(range(2020, 2061, 4))  # 4-year steps

CHARGING_MARKUP = 0.30

# Distinct country colours — matching manuscript palette
COUNTRY_COLORS = {
    'NO': '#2c6e99',   # medium navy
    'FI': '#45a0cc',   # light blue
    'SE': '#7bc4a0',   # sage green
    'DK': '#d97a3e',   # warm orange
    'DE': '#5b4fa8',   # purple
    'AT': '#d4a017',   # golden yellow
    'IT': '#e05050',   # red
}

SCENARIOS = {
    0: 'Go RES',
    1: 'NECPEssentials',
    2: 'REPowerEU++',
    3: 'Trinity',
}

# ── Load geographic mapping ──────────────────────────────────────────
print('Loading geographic data...')
with open(INPUT_DIR / 'fixed_nuts_2' / 'GeographicElement.yaml', 'r', encoding='utf-8') as f:
    geo_data = yaml.safe_load(f)

loc_to_country = {}
for g in geo_data:
    if g.get('type') == 'node':
        loc_to_country[g['id']] = g.get('country', '')

# ── Load carbon price data ───────────────────────────────────────────
print('Loading carbon prices...')
carbon_prices_by_scenario = {}
for scen_idx in SCENARIOS:
    scen_dir = INPUT_DIR / 'uncertainty_scenarios' / f'scenario_{scen_idx:03d}'
    with open(scen_dir / 'GeographicElement.yaml', 'r', encoding='utf-8') as f:
        scen_geo = yaml.safe_load(f)
    # Carbon price is per geographic element — take the first node's carbon_price
    for g in scen_geo:
        if g.get('type') == 'node':
            cp = g.get('carbon_price', [0]*len(MODEL_YEARS))
            carbon_prices_by_scenario[scen_idx] = [float(c) for c in cp]
            break

# ── Load fuel costs ──────────────────────────────────────────────────
print('Loading fuel cost data...')

# Per scenario: electricity by country, diesel base
elec_by_country = {}  # {scen_idx: {country: [prices]}}
diesel_base = {}      # {scen_idx: [prices]}

for scen_idx in SCENARIOS:
    scen_dir = INPUT_DIR / 'uncertainty_scenarios' / f'scenario_{scen_idx:03d}'
    with open(scen_dir / 'FuelCost.yaml', 'r', encoding='utf-8') as f:
        fc = yaml.safe_load(f)

    country_elec = {c: [] for c in CORRIDOR_COUNTRIES}
    diesel_prices_all = []

    for entry in fc:
        loc = entry['location']
        fuel = entry['fuel']
        prices = entry['cost_per_kWh']
        country = loc_to_country.get(loc, '')

        if fuel == 'electricity' and entry.get('fueling_infr_type_id') == 1:
            # Slow charging — representative price
            if country in CORRIDOR_COUNTRIES:
                country_elec[country].append(prices)
        elif fuel == 'diesel':
            if country in CORRIDOR_COUNTRIES:
                diesel_prices_all.append(prices)

    # Average electricity per country (there may be multiple nodes per country)
    avg_elec = {}
    for c in CORRIDOR_COUNTRIES:
        if country_elec[c]:
            arr = np.array(country_elec[c])
            avg_elec[c] = arr.mean(axis=0).tolist()
    elec_by_country[scen_idx] = avg_elec

    # Average diesel (base, without carbon)
    if diesel_prices_all:
        diesel_base[scen_idx] = np.array(diesel_prices_all).mean(axis=0).tolist()
    else:
        diesel_base[scen_idx] = [0] * len(MODEL_YEARS)

# ── Compute diesel with carbon ───────────────────────────────────────
# Diesel emission factor: ~0.2664 kgCO2/kWh (standard diesel)
DIESEL_EMISSION_FACTOR = 0.2664  # kgCO2/kWh

diesel_with_carbon = {}
for scen_idx in SCENARIOS:
    base = diesel_base[scen_idx]
    cp = carbon_prices_by_scenario.get(scen_idx, [0]*len(MODEL_YEARS))
    # carbon_price in EUR/tCO2, emission factor in kgCO2/kWh -> EUR/kWh = cp * ef * 1e-3
    diesel_with_carbon[scen_idx] = [
        base[y] + cp[y] * DIESEL_EMISSION_FACTOR * 1e-3
        for y in range(len(MODEL_YEARS))
    ]

# ── Plot: 2x2 grid ──────────────────────────────────────────────────
print('Generating figure...')
fig, axes = plt.subplots(2, 2, figsize=(14, 7), sharey=True)
axes_flat = axes.flatten()

for si, (scen_idx, scen_name) in enumerate(SCENARIOS.items()):
    ax = axes_flat[si]

    # Diesel areas
    d_base = [diesel_base[scen_idx][MODEL_YEARS.index(y)] for y in PLOT_YEARS]
    d_carbon = [diesel_with_carbon[scen_idx][MODEL_YEARS.index(y)] for y in PLOT_YEARS]

    ax.fill_between(PLOT_YEARS, 0, d_base, color='#d9d9d9', alpha=0.6, label='Diesel (base)')
    ax.fill_between(PLOT_YEARS, d_base, d_carbon, color='#969696', alpha=0.5, label='Diesel (+ CO2 price)')
    ax.plot(PLOT_YEARS, d_carbon, color='black', linewidth=1.5, linestyle='--', alpha=0.7)

    # Electricity prices by country (with 30% markup)
    for country in CORRIDOR_COUNTRIES:
        if country in elec_by_country[scen_idx]:
            prices = elec_by_country[scen_idx][country]
            prices_at_steps = [prices[MODEL_YEARS.index(y)] * (1 + CHARGING_MARKUP)
                               for y in PLOT_YEARS]
            ax.plot(PLOT_YEARS, prices_at_steps, color=COUNTRY_COLORS[country],
                    marker='o', markersize=4, linewidth=1.8, label=country)

    ax.set_title(scen_name, fontsize=15)
    ax.set_ylim(0, 0.40)
    ax.grid(True, alpha=0.2, linestyle='--')
    ax.tick_params(labelsize=13)

    if si >= 2:
        ax.set_xlabel('Year')
    if si % 2 == 0:
        ax.set_ylabel('Fuel cost (EUR/kWh)')

# Shared legend below
handles, labels = axes_flat[0].get_legend_handles_labels()
fig.legend(handles, labels, loc='lower center', ncol=5, fontsize=13,
           bbox_to_anchor=(0.5, -0.02), frameon=True, fancybox=True)

plt.tight_layout(rect=[0, 0.05, 1, 1])

# Save
fname = 'electricity_prices_by_country_4scenarios'
for dst in [FIG_DIR, MANUSCRIPT_IMG]:
    fig.savefig(dst / f'{fname}.pdf', bbox_inches='tight')
fig.savefig(FIG_DIR / f'{fname}.png', bbox_inches='tight', dpi=150)
plt.close()
print(f'Saved: figures/{fname}.pdf')
print(f'Saved: manuscript/images/{fname}.pdf')
print('Done.')
