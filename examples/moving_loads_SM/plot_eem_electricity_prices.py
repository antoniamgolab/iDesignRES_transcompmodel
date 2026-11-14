"""
Plot electricity prices by country/zone for EEM zone-split scenarios.
Similar layout to electricity_prices_by_country_4scenarios but with
4 EEM scenarios: Baseline, Low (5%), Mid (10%), High (20%).
Germany is shown as DE-North and DE-South instead of a single DE line.
"""

import yaml
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from matplotlib.lines import Line2D

SCRIPT_DIR = Path(__file__).parent
EEM_DIR = SCRIPT_DIR / "input_data" / "eem_scenarios"

# Zone mapping (same as create_eem_scenarios.py)
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

SCENARIOS = [
    ("DE_unified",    "Baseline (unified DE)"),
    ("DE_split_low",  "Zone split: 5% spread"),
    ("DE_split_mid",  "Zone split: 10% spread"),
    ("DE_split_high", "Zone split: 20% spread"),
]

# Country prefixes for non-DE nodes
COUNTRY_PREFIXES = {
    'NO': 'NO', 'FI': 'FI', 'SE': 'SE', 'DK': 'DK', 'AT': 'AT', 'IT': 'IT',
}


def load_scenario_prices(scenario_dir):
    """Load electricity prices grouped by country/zone."""
    geo_file = scenario_dir / "GeographicElement.yaml"
    fc_file = scenario_dir / "FuelCost.yaml"

    geos = yaml.safe_load(open(geo_file, encoding='utf-8'))
    fuels = yaml.safe_load(open(fc_file, encoding='utf-8'))

    # Map geo_id -> nuts2
    geo_id_to_nuts2 = {}
    for g in geos:
        geo_id_to_nuts2[g['id']] = g.get('nuts2_region', '')

    # Collect fast-charging electricity prices by group
    group_prices = {}  # group_name -> list of price arrays
    for fc in fuels:
        if fc['fuel'] != 'electricity':
            continue
        infr = fc.get('fueling_infr_type_id', 2)
        if infr != 2:  # fast charging only
            continue

        loc = fc['location']
        nuts2 = geo_id_to_nuts2.get(loc, '')
        prices = fc['cost_per_kWh']

        # Classify
        if nuts2 in DE_NORTH_NUTS2:
            group = 'DE-North'
        elif nuts2 in DE_SOUTH_NUTS2:
            group = 'DE-South'
        else:
            # Find country
            group = None
            for prefix, name in COUNTRY_PREFIXES.items():
                if nuts2.startswith(prefix):
                    group = name
                    break
            if group is None:
                continue

        if group not in group_prices:
            group_prices[group] = []
        group_prices[group].append(prices)

    # Average within each group
    avg_prices = {}
    for group, price_lists in group_prices.items():
        avg_prices[group] = np.mean(price_lists, axis=0)

    return avg_prices


def load_diesel_prices(scenario_dir):
    """Load diesel base price and carbon-inclusive price."""
    fc_file = scenario_dir / "FuelCost.yaml"
    fuels = yaml.safe_load(open(fc_file, encoding='utf-8'))

    # Get diesel price (same everywhere)
    for fc in fuels:
        if fc['fuel'] == 'diesel':
            return np.array(fc['cost_per_kWh'])
    return None


def load_carbon_prices(scenario_dir):
    """Load carbon prices from GeographicElement to compute diesel+CO2."""
    geo_file = scenario_dir / "GeographicElement.yaml"
    geos = yaml.safe_load(open(geo_file, encoding='utf-8'))

    # Get carbon prices from a German node (they're the same for all)
    for g in geos:
        if g.get('nuts2_region', '').startswith('DE'):
            cp = g.get('carbon_price', None)
            if cp is not None:
                return np.array(cp)
    return None


# Diesel CO2 emission factor (kg CO2 per kWh diesel)
# Diesel: ~0.266 kg CO2/kWh (= 73.6 g CO2/MJ * 3.6 MJ/kWh / 1000)
DIESEL_CO2_PER_KWH = 0.266


def main():
    plt.rcParams.update({
        'font.size': 10,
        'axes.labelsize': 11,
        'axes.titlesize': 12,
        'legend.fontsize': 8.5,
        'figure.dpi': 150,
    })

    fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharex=True, sharey=True)
    axes = axes.flatten()

    # Colors matching the original figure style
    colors = {
        'NO': '#1f77b4',       # blue
        'FI': '#ff7f0e',       # orange
        'SE': '#2ca02c',       # green
        'DK': '#d62728',       # red
        'DE-North': '#7B2D8E', # purple (darker)
        'DE-South': '#C77CFF', # purple (lighter)
        'AT': '#8c564b',       # brown
        'IT': '#e377c2',       # pink
    }

    markers = {
        'NO': 'o', 'FI': 'o', 'SE': 'o', 'DK': 'o',
        'DE-North': 's', 'DE-South': '^',
        'AT': 'o', 'IT': 'o',
    }

    # Plot order for legend consistency
    plot_order = ['NO', 'FI', 'SE', 'DK', 'DE-North', 'DE-South', 'AT', 'IT']

    # Years: 41 time steps from 2020 to 2060
    years = np.arange(2020, 2061)

    for ax_idx, (scenario_name, scenario_label) in enumerate(SCENARIOS):
        ax = axes[ax_idx]
        scenario_dir = EEM_DIR / scenario_name

        if not scenario_dir.exists():
            ax.set_title(f"{scenario_label}\n(not found)")
            continue

        avg_prices = load_scenario_prices(scenario_dir)
        diesel_base = load_diesel_prices(scenario_dir)
        carbon_prices = load_carbon_prices(scenario_dir)

        # Adjust years to match data length
        n_years = len(next(iter(avg_prices.values())))
        yrs = years[:n_years]

        # Plot diesel background
        if diesel_base is not None:
            diesel_base_plot = diesel_base[:n_years]
            ax.fill_between(yrs, 0, diesel_base_plot,
                          alpha=0.15, color='gray', label='_nolegend_')

            if carbon_prices is not None:
                # diesel + CO2: carbon_price is EUR/tCO2, convert to EUR/kWh
                carbon_add = carbon_prices[:n_years] / 1000.0 * DIESEL_CO2_PER_KWH
                diesel_co2 = diesel_base_plot + carbon_add
                ax.fill_between(yrs, diesel_base_plot, diesel_co2,
                              alpha=0.25, color='gray', label='_nolegend_')
                ax.plot(yrs, diesel_co2, '--', color='gray', linewidth=1, alpha=0.7)

        # Plot electricity prices
        for group in plot_order:
            if group in avg_prices:
                p = avg_prices[group][:n_years]
                lw = 2.0 if group.startswith('DE') else 1.2
                ms = 5 if group.startswith('DE') else 3.5
                ax.plot(yrs, p, '-', color=colors[group], marker=markers[group],
                       markersize=ms, linewidth=lw, markevery=5)

        ax.set_title(scenario_label)
        ax.set_ylim(0, 0.60)
        ax.set_xlim(2020, 2060)
        ax.grid(True, alpha=0.3)

        if ax_idx >= 2:
            ax.set_xlabel('Year')
        if ax_idx % 2 == 0:
            ax.set_ylabel('Fuel cost (EUR/kWh)')

    # Legend
    legend_elements = []
    # Diesel
    legend_elements.append(plt.Rectangle((0,0), 1, 1, fc='gray', alpha=0.15,
                                         label='Diesel (base)'))
    legend_elements.append(plt.Rectangle((0,0), 1, 1, fc='gray', alpha=0.35,
                                         label='Diesel (+ CO$_2$ price)'))
    # Countries/zones
    for group in plot_order:
        legend_elements.append(
            Line2D([0], [0], color=colors[group], marker=markers[group],
                   markersize=5, linewidth=1.5, label=group)
        )

    fig.legend(handles=legend_elements, loc='lower center', ncol=5,
              bbox_to_anchor=(0.5, -0.02), frameon=True)

    fig.suptitle('Electricity charging prices by country/zone -- EEM scenarios\n'
                 '(fast charging, Go RES baseline)', fontsize=13, y=0.98)
    plt.tight_layout(rect=[0, 0.04, 1, 0.95])

    # Save
    out_dir = SCRIPT_DIR / "figures"
    out_dir.mkdir(exist_ok=True)
    for ext in ['pdf', 'png']:
        fig.savefig(out_dir / f"eem_electricity_prices_by_zone.{ext}",
                   bbox_inches='tight', dpi=200)
    print(f"Saved to figures/eem_electricity_prices_by_zone.pdf/.png")
    plt.close()


if __name__ == "__main__":
    main()
