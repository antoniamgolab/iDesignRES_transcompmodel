"""Figure 3 (final inputs): MCS charging price by country and diesel cost (base and incl. CO2 price) for the four
GENeSYS-MOD scenarios, from input_data/v4_gridconn150/scenario_00{0..3} (time-of-day prices, 30 % markup)."""
import yaml
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

HERE = Path(__file__).parent
INP = HERE / 'input_data' / 'v4_gridconn150'
SCEN = [('scenario_000', 'Go RES'), ('scenario_001', 'NECPEssentials'), ('scenario_002', 'REPowerEU++'), ('scenario_003', 'Trinity')]
YEARS = np.arange(2020, 2061)
MODEL_YEARS = list(range(2020, 2061, 4))
DIESEL_CO2 = 266e-6  # tCO2 per kWh diesel (Fuel.yaml: 266 g/kWh)
COUNTRIES = ['NO', 'FI', 'SE', 'DK', 'DE', 'AT', 'IT']
COL = {'NO': '#1f77b4', 'FI': '#17becf', 'SE': '#2ca02c', 'DK': '#ff7f0e', 'DE': '#9467bd', 'AT': '#d4a017', 'IT': '#d62728'}
L = lambda p: yaml.load(open(p), Loader=yaml.CSafeLoader)


def load(d):
    geo = {g['id']: g for g in L(d / 'GeographicElement.yaml') if g['type'] == 'node'}
    fc = L(d / 'FuelCost.yaml')
    el = {}
    for c in fc:
        if c['fuel'] == 'electricity' and c['fueling_infr_type_id'] == 2 and c['location'] in geo:
            el.setdefault(geo[c['location']]['country'], []).append(c['cost_per_kWh'])
    el = {k: np.mean(v, axis=0) for k, v in el.items()}
    diesel = np.array([c for c in fc if c['fuel'] == 'diesel'][0]['cost_per_kWh'])
    co2 = np.array(next(iter(geo.values()))['carbon_price'])
    return el, diesel, diesel + co2 * DIESEL_CO2


plt.rcParams.update({'font.size': 10, 'axes.labelsize': 10, 'axes.titlesize': 11, 'legend.fontsize': 9})
fig, axes = plt.subplots(2, 2, figsize=(11, 6.2), sharex=True, sharey=True)
idx = [YEARS.tolist().index(y) for y in MODEL_YEARS]
for ax, (folder, title) in zip(axes.flat, SCEN):
    el, dbase, dco2 = load(INP / folder)
    ax.fill_between(MODEL_YEARS, 0, dco2[idx], color='#bdbdbd', alpha=0.8, lw=0)
    ax.fill_between(MODEL_YEARS, 0, dbase[idx], color='#e6e6e6', alpha=1.0, lw=0)
    ax.plot(MODEL_YEARS, dco2[idx], color='#333333', ls='--', lw=1)
    for c in COUNTRIES:
        ax.plot(MODEL_YEARS, el[c][idx], marker='o', ms=3.5, lw=1.4, color=COL[c])
    ax.set_title(title)
    ax.set_xlim(2019, 2061); ax.set_ylim(0, 0.6)
    ax.grid(alpha=0.3)
for ax in axes[1]:
    ax.set_xlabel('Year')
for ax in axes[:, 0]:
    ax.set_ylabel('Cost (EUR/kWh)')
handles = [Patch(color='#e6e6e6', label='Diesel (base)'), Patch(color='#bdbdbd', label='Diesel (+ CO$_2$ price)')] + \
          [Line2D([], [], color=COL[c], marker='o', ms=3.5, label=c) for c in COUNTRIES]
fig.legend(handles=handles, loc='lower center', ncol=9, frameon=True, bbox_to_anchor=(0.5, -0.02))
fig.tight_layout(rect=(0, 0.05, 1, 1))
out = HERE / 'figures'
for ext in ('pdf', 'png'):
    fig.savefig(out / f'electricity_prices_by_country_4scenarios_final.{ext}', bbox_inches='tight', dpi=200)
print('saved')
for folder, title in SCEN:
    el, dbase, dco2 = load(INP / folder)
    cross = {c: next((y for y, e, d in zip(YEARS, el[c], dco2) if d >= e), None) for c in COUNTRIES}
    print(title, 'diesel+CO2 >= MCS price from:', cross)
