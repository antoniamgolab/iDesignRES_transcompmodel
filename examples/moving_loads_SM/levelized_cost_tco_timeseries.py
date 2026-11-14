"""
Levelized Cost Time Series - TCO-based calculation for BEV vs ICEV

Components:
- Capital costs (annualized)
- Maintenance costs (annual)
- Fuel costs (EUR/kWh × kWh/km × km)
- Carbon costs for ICEV (EUR/tCO2 × kgCO2/kWh × kWh/km)

Creates time series comparing BEV and ICEV levelized costs across all 4 GENeSYS scenarios.
"""

import yaml
import os
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

# ============================================================================
# CARBON PRICE TRAJECTORIES (EUR/tCO2)
# ============================================================================
CARBON_PRICES = {
    'Go RES v1.2': {2020: 30, 2030: 200, 2040: 500, 2050: 1000, 2060: 1000},
    'REPowerEU++ v1.2': {2020: 30, 2030: 150, 2040: 350, 2050: 700, 2060: 700},
    'NECPEssentials v1.2': {2020: 30, 2030: 100, 2040: 250, 2050: 500, 2060: 500},
    'Trinity v1.2': {2020: 30, 2030: 80, 2040: 180, 2050: 350, 2060: 350}
}

SHORT_NAMES = {
    'Go RES v1.2': 'Go RES',
    'REPowerEU++ v1.2': 'REPowerEU++',
    'NECPEssentials v1.2': 'NECPEssentials',
    'Trinity v1.2': 'Trinity'
}

COLORS = {
    'Go RES v1.2': '#1f77b4',
    'REPowerEU++ v1.2': '#ff7f0e',
    'NECPEssentials v1.2': '#2ca02c',
    'Trinity v1.2': '#d62728'
}

# ============================================================================
# VEHICLE PARAMETERS (from TechVehicle.yaml)
# ============================================================================
YEARS = list(range(2020, 2061))  # Index 0-40
MODEL_YEARS = [2020, 2024, 2028, 2032, 2036, 2040, 2044, 2048, 2052, 2056, 2060]

# ICEV parameters (from scenario_000 TechVehicle.yaml)
ICEV_CAPITAL_COST = {
    2020: 105484, 2024: 107689, 2028: 111596, 2032: 114033,
    2036: 115252, 2040: 115252, 2044: 115252, 2048: 115252,
    2052: 115252, 2056: 115252, 2060: 115252
}
ICEV_MAINTENANCE_ANNUAL = 20703  # EUR/year (constant)
ICEV_SPEC_CONS = {  # kWh/km
    2020: 3.64, 2024: 3.45, 2028: 3.27, 2032: 3.08,
    2036: 2.90, 2040: 2.71, 2044: 2.53, 2048: 2.40,
    2052: 2.28, 2056: 2.28, 2060: 2.28
}
ICEV_LIFETIME = 12  # years
ANNUAL_RANGE = 136750  # km/year

# BEV parameters (from scenario_000 TechVehicle.yaml)
BEV_CAPITAL_COST = {
    2020: 220000, 2024: 185725, 2028: 149705, 2032: 129500,
    2036: 116350, 2040: 106881, 2044: 97750, 2048: 91713,
    2052: 89125, 2056: 83950, 2060: 80500
}
BEV_MAINTENANCE_ANNUAL = 14364  # EUR/year (constant)
BEV_SPEC_CONS = {  # kWh/km
    2020: 2.06, 2024: 1.94, 2028: 1.79, 2032: 1.68,
    2036: 1.52, 2040: 1.41, 2044: 1.29, 2048: 1.21,
    2052: 1.21, 2056: 1.21, 2060: 1.21
}
BEV_LIFETIME = 12  # years

# Fuel costs (EUR/kWh) - from FuelCost.yaml, averaged across locations
DIESEL_COST = {  # EUR/kWh (excluding carbon)
    2020: 0.051, 2024: 0.054, 2028: 0.047, 2032: 0.034,
    2036: 0.029, 2040: 0.024, 2044: 0.022, 2048: 0.020,
    2052: 0.020, 2056: 0.020, 2060: 0.020
}

# Electricity costs depend on GENeSYS scenario - these are for Go RES with 15% markup
ELECTRICITY_COST_BASE = {  # EUR/kWh (base, without markup)
    2020: 0.32, 2024: 0.35, 2028: 0.29, 2032: 0.20,
    2036: 0.16, 2040: 0.14, 2044: 0.14, 2048: 0.14,
    2052: 0.14, 2056: 0.14, 2060: 0.14
}

# Diesel emission factor
DIESEL_CO2_EMISSION = 266  # gCO2/kWh = 0.266 kgCO2/kWh


def interpolate(data_dict, year):
    """Interpolate value for any year from a dict with known years."""
    years = sorted(data_dict.keys())
    if year <= years[0]:
        return data_dict[years[0]]
    if year >= years[-1]:
        return data_dict[years[-1]]
    for i in range(len(years) - 1):
        if years[i] <= year <= years[i+1]:
            t = (year - years[i]) / (years[i+1] - years[i])
            return data_dict[years[i]] * (1-t) + data_dict[years[i+1]] * t
    return data_dict[years[-1]]


def calc_carbon_cost_per_km(year, scenario):
    """Calculate carbon cost per km for ICEV (EUR/km)."""
    carbon_price = interpolate(CARBON_PRICES[scenario], year)  # EUR/tCO2
    spec_cons = interpolate(ICEV_SPEC_CONS, year)  # kWh/km
    # CO2 per km = spec_cons (kWh/km) × emission factor (gCO2/kWh) / 1e6 (g→t)
    co2_per_km = spec_cons * DIESEL_CO2_EMISSION / 1e6  # tCO2/km
    return carbon_price * co2_per_km  # EUR/km


def calc_icev_levelized_cost(year, scenario, charging_markup=0.15):
    """Calculate ICEV levelized cost (EUR/km)."""
    capital = interpolate(ICEV_CAPITAL_COST, year)
    maintenance = ICEV_MAINTENANCE_ANNUAL
    spec_cons = interpolate(ICEV_SPEC_CONS, year)
    diesel_cost = interpolate(DIESEL_COST, year)

    # Annualized capital cost per km
    capital_per_km = capital / ICEV_LIFETIME / ANNUAL_RANGE

    # Maintenance per km
    maintenance_per_km = maintenance / ANNUAL_RANGE

    # Fuel cost per km
    fuel_per_km = spec_cons * diesel_cost

    # Carbon cost per km
    carbon_per_km = calc_carbon_cost_per_km(year, scenario)

    return {
        'capital': capital_per_km,
        'maintenance': maintenance_per_km,
        'fuel': fuel_per_km,
        'carbon': carbon_per_km,
        'total': capital_per_km + maintenance_per_km + fuel_per_km + carbon_per_km
    }


def calc_bev_levelized_cost(year, scenario, charging_markup=0.15):
    """Calculate BEV levelized cost (EUR/km)."""
    capital = interpolate(BEV_CAPITAL_COST, year)
    maintenance = BEV_MAINTENANCE_ANNUAL
    spec_cons = interpolate(BEV_SPEC_CONS, year)
    elec_cost_base = interpolate(ELECTRICITY_COST_BASE, year)
    elec_cost = elec_cost_base * (1 + charging_markup)

    # Annualized capital cost per km
    capital_per_km = capital / BEV_LIFETIME / ANNUAL_RANGE

    # Maintenance per km
    maintenance_per_km = maintenance / ANNUAL_RANGE

    # Fuel cost per km
    fuel_per_km = spec_cons * elec_cost

    return {
        'capital': capital_per_km,
        'maintenance': maintenance_per_km,
        'fuel': fuel_per_km,
        'carbon': 0,  # BEV has no direct carbon cost
        'total': capital_per_km + maintenance_per_km + fuel_per_km
    }


# ============================================================================
# MAIN CALCULATION
# ============================================================================

def calc_bev_levelized_cost_with_params(year, scenario, charging_markup=0.15, tech_multiplier=1.0):
    """Calculate BEV levelized cost with variable markup and tech cost."""
    # Apply tech multiplier to capital cost
    base_capital = interpolate(BEV_CAPITAL_COST, year)
    capital = base_capital * tech_multiplier

    maintenance = BEV_MAINTENANCE_ANNUAL
    spec_cons = interpolate(BEV_SPEC_CONS, year)
    elec_cost_base = interpolate(ELECTRICITY_COST_BASE, year)
    elec_cost = elec_cost_base * (1 + charging_markup)

    # Annualized capital cost per km
    capital_per_km = capital / BEV_LIFETIME / ANNUAL_RANGE

    # Maintenance per km
    maintenance_per_km = maintenance / ANNUAL_RANGE

    # Fuel cost per km
    fuel_per_km = spec_cons * elec_cost

    return {
        'capital': capital_per_km,
        'maintenance': maintenance_per_km,
        'fuel': fuel_per_km,
        'carbon': 0,
        'total': capital_per_km + maintenance_per_km + fuel_per_km
    }


def main():
    base_dir = os.path.dirname(__file__)
    output_dir = os.path.join(base_dir, 'figures')
    os.makedirs(output_dir, exist_ok=True)

    years = MODEL_YEARS

    # Parameter variations
    MARKUPS = [0.15, 0.30]
    TECH_MULTIPLIERS = [0.7, 1.0, 1.3]

    # Calculate costs for all scenarios and parameter combinations
    results = []
    for scenario in CARBON_PRICES.keys():
        for markup in MARKUPS:
            for tech_mult in TECH_MULTIPLIERS:
                for year in years:
                    icev = calc_icev_levelized_cost(year, scenario)
                    bev = calc_bev_levelized_cost_with_params(year, scenario, markup, tech_mult)

                    results.append({
                        'scenario': scenario,
                        'markup': markup,
                        'tech_mult': tech_mult,
                        'year': year,
                        'tech': 'ICEV',
                        'capital': icev['capital'],
                        'maintenance': icev['maintenance'],
                        'fuel': icev['fuel'],
                        'carbon': icev['carbon'],
                        'total': icev['total']
                    })
                    results.append({
                        'scenario': scenario,
                        'markup': markup,
                        'tech_mult': tech_mult,
                        'year': year,
                        'tech': 'BEV',
                        'capital': bev['capital'],
                        'maintenance': bev['maintenance'],
                        'fuel': bev['fuel'],
                        'carbon': bev['carbon'],
                        'total': bev['total']
                    })

    df = pd.DataFrame(results)

    # Filter for base case (15% markup, 1.0x tech) for original plots
    df_base = df[(df['markup'] == 0.15) & (df['tech_mult'] == 1.0)]

    # ========================================================================
    # FIGURE 1: Total Levelized Cost Time Series (all scenarios) - base case
    # ========================================================================
    fig, ax = plt.subplots(figsize=(12, 7))

    for scenario in CARBON_PRICES.keys():
        scenario_df = df_base[df_base['scenario'] == scenario]
        icev_df = scenario_df[scenario_df['tech'] == 'ICEV']
        bev_df = scenario_df[scenario_df['tech'] == 'BEV']

        ax.plot(icev_df['year'], icev_df['total'], 'o-',
                color=COLORS[scenario], linewidth=2, markersize=6,
                label=f'ICEV - {SHORT_NAMES[scenario]}')
        ax.plot(bev_df['year'], bev_df['total'], 's--',
                color=COLORS[scenario], linewidth=2, markersize=6,
                label=f'BEV - {SHORT_NAMES[scenario]}', alpha=0.7)

    ax.set_xlabel('Year', fontsize=12)
    ax.set_ylabel('Levelized Cost (EUR/km)', fontsize=12)
    ax.set_title('Levelized Transport Cost: BEV vs ICEV by GENeSYS Scenario\n(15% markup, 1.0x tech cost)',
                fontsize=13, fontweight='bold')
    ax.legend(loc='upper right', fontsize=9, ncol=2)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(2018, 2062)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'levelized_cost_timeseries_all_scenarios.pdf'),
                dpi=150, bbox_inches='tight')
    plt.savefig(os.path.join(output_dir, 'levelized_cost_timeseries_all_scenarios.png'),
                dpi=150, bbox_inches='tight')
    print(f"Saved: {output_dir}/levelized_cost_timeseries_all_scenarios.pdf")

    # ========================================================================
    # FIGURE 2: Stacked Cost Components (Go RES scenario)
    # ========================================================================
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    scenario = 'Go RES v1.2'
    scenario_df = df_base[df_base['scenario'] == scenario]

    for idx, tech in enumerate(['ICEV', 'BEV']):
        ax = axes[idx]
        tech_df = scenario_df[scenario_df['tech'] == tech].sort_values('year')

        # Stack: capital, maintenance, fuel, carbon
        ax.fill_between(tech_df['year'], 0, tech_df['capital'],
                       label='Capital', color='#1f77b4', alpha=0.8)
        ax.fill_between(tech_df['year'], tech_df['capital'],
                       tech_df['capital'] + tech_df['maintenance'],
                       label='Maintenance', color='#ff7f0e', alpha=0.8)
        ax.fill_between(tech_df['year'],
                       tech_df['capital'] + tech_df['maintenance'],
                       tech_df['capital'] + tech_df['maintenance'] + tech_df['fuel'],
                       label='Fuel', color='#2ca02c', alpha=0.8)
        if tech == 'ICEV':
            ax.fill_between(tech_df['year'],
                           tech_df['capital'] + tech_df['maintenance'] + tech_df['fuel'],
                           tech_df['total'],
                           label='Carbon', color='#d62728', alpha=0.8)

        ax.set_xlabel('Year', fontsize=11)
        ax.set_ylabel('Levelized Cost (EUR/km)', fontsize=11)
        ax.set_title(f'{tech} Cost Components ({SHORT_NAMES[scenario]})',
                    fontsize=12, fontweight='bold')
        ax.legend(loc='upper right', fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.set_xlim(2018, 2062)
        ax.set_ylim(0, max(tech_df['total']) * 1.1)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'levelized_cost_components_go_res.pdf'),
                dpi=150, bbox_inches='tight')
    plt.savefig(os.path.join(output_dir, 'levelized_cost_components_go_res.png'),
                dpi=150, bbox_inches='tight')
    print(f"Saved: {output_dir}/levelized_cost_components_go_res.pdf")

    # ========================================================================
    # FIGURE 3: Cost Difference (ICEV - BEV) by scenario
    # ========================================================================
    fig, ax = plt.subplots(figsize=(12, 6))

    for scenario in CARBON_PRICES.keys():
        scenario_df = df_base[df_base['scenario'] == scenario]
        icev_df = scenario_df[scenario_df['tech'] == 'ICEV'].set_index('year')
        bev_df = scenario_df[scenario_df['tech'] == 'BEV'].set_index('year')

        diff = icev_df['total'] - bev_df['total']
        ax.plot(diff.index, diff.values, 'o-',
                color=COLORS[scenario], linewidth=2.5, markersize=7,
                label=SHORT_NAMES[scenario])

    ax.axhline(y=0, color='black', linestyle='--', linewidth=1.5, label='Break-even')
    ax.fill_between(years, 0, max(df['total']), alpha=0.1, color='green')
    ax.fill_between(years, min(df['total'].min(), -0.5), 0, alpha=0.1, color='red')

    ax.text(2055, 0.15, 'BEV cheaper', fontsize=11, color='green', fontweight='bold')
    ax.text(2055, -0.08, 'ICEV cheaper', fontsize=11, color='red', fontweight='bold')

    ax.set_xlabel('Year', fontsize=12)
    ax.set_ylabel('Cost Difference: ICEV - BEV (EUR/km)', fontsize=12)
    ax.set_title('When Does BEV Become Cheaper? Cost Difference by GENeSYS Scenario',
                fontsize=13, fontweight='bold')
    ax.legend(loc='upper right', fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(2018, 2062)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'levelized_cost_difference_by_scenario.pdf'),
                dpi=150, bbox_inches='tight')
    plt.savefig(os.path.join(output_dir, 'levelized_cost_difference_by_scenario.png'),
                dpi=150, bbox_inches='tight')
    print(f"Saved: {output_dir}/levelized_cost_difference_by_scenario.pdf")

    # ========================================================================
    # FIGURE 4: Carbon Price Impact
    # ========================================================================
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Panel 1: Carbon price trajectories
    ax = axes[0]
    for scenario in CARBON_PRICES.keys():
        cp_values = [interpolate(CARBON_PRICES[scenario], y) for y in years]
        ax.plot(years, cp_values, 'o-', color=COLORS[scenario],
                label=SHORT_NAMES[scenario], linewidth=2, markersize=5)

    ax.set_xlabel('Year', fontsize=11)
    ax.set_ylabel('Carbon Price (EUR/tCO2)', fontsize=11)
    ax.set_title('Carbon Price Trajectories', fontsize=12, fontweight='bold')
    ax.legend(loc='upper left', fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(2018, 2062)

    # Panel 2: Carbon cost component for ICEV
    ax = axes[1]
    for scenario in CARBON_PRICES.keys():
        carbon_costs = [calc_carbon_cost_per_km(y, scenario) for y in years]
        ax.plot(years, carbon_costs, 'o-', color=COLORS[scenario],
                label=SHORT_NAMES[scenario], linewidth=2, markersize=5)

    ax.set_xlabel('Year', fontsize=11)
    ax.set_ylabel('Carbon Cost (EUR/km)', fontsize=11)
    ax.set_title('ICEV Carbon Cost Component', fontsize=12, fontweight='bold')
    ax.legend(loc='upper left', fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(2018, 2062)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'carbon_price_impact_on_icev.pdf'),
                dpi=150, bbox_inches='tight')
    plt.savefig(os.path.join(output_dir, 'carbon_price_impact_on_icev.png'),
                dpi=150, bbox_inches='tight')
    print(f"Saved: {output_dir}/carbon_price_impact_on_icev.pdf")

    # ========================================================================
    # FIGURE 5: Impact of Tech Cost Multiplier (Go RES scenario)
    # ========================================================================
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    scenario = 'Go RES v1.2'
    markup = 0.15
    tech_colors = {0.7: '#2ca02c', 1.0: '#1f77b4', 1.3: '#d62728'}

    # Panel 1: BEV cost by tech multiplier
    ax = axes[0]
    scenario_df = df[(df['scenario'] == scenario) & (df['markup'] == markup)]

    # ICEV line (same for all tech multipliers)
    icev_df = scenario_df[(scenario_df['tech'] == 'ICEV') & (scenario_df['tech_mult'] == 1.0)]
    ax.plot(icev_df['year'], icev_df['total'], 'k-', linewidth=3, label='ICEV', alpha=0.8)

    for tech_mult in TECH_MULTIPLIERS:
        bev_df = scenario_df[(scenario_df['tech'] == 'BEV') & (scenario_df['tech_mult'] == tech_mult)]
        ax.plot(bev_df['year'], bev_df['total'], 'o--',
                color=tech_colors[tech_mult], linewidth=2, markersize=5,
                label=f'BEV ({tech_mult}x tech cost)')

    ax.set_xlabel('Year', fontsize=11)
    ax.set_ylabel('Levelized Cost (EUR/km)', fontsize=11)
    ax.set_title(f'Impact of Tech Cost Multiplier ({SHORT_NAMES[scenario]})',
                fontsize=12, fontweight='bold')
    ax.legend(loc='upper right', fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(2018, 2062)

    # Panel 2: Cost difference by tech multiplier
    ax = axes[1]
    for tech_mult in TECH_MULTIPLIERS:
        icev_df = scenario_df[(scenario_df['tech'] == 'ICEV') & (scenario_df['tech_mult'] == tech_mult)].set_index('year')
        bev_df = scenario_df[(scenario_df['tech'] == 'BEV') & (scenario_df['tech_mult'] == tech_mult)].set_index('year')
        diff = icev_df['total'] - bev_df['total']
        ax.plot(diff.index, diff.values, 'o-',
                color=tech_colors[tech_mult], linewidth=2.5, markersize=6,
                label=f'{tech_mult}x tech cost')

    ax.axhline(y=0, color='black', linestyle='--', linewidth=1.5)
    ax.fill_between(years, 0, 0.8, alpha=0.1, color='green')
    ax.fill_between(years, -0.8, 0, alpha=0.1, color='red')
    ax.set_xlabel('Year', fontsize=11)
    ax.set_ylabel('Cost Difference: ICEV - BEV (EUR/km)', fontsize=11)
    ax.set_title(f'Break-even by Tech Cost ({SHORT_NAMES[scenario]})',
                fontsize=12, fontweight='bold')
    ax.legend(loc='upper left', fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(2018, 2062)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'levelized_cost_by_tech_multiplier.pdf'),
                dpi=150, bbox_inches='tight')
    plt.savefig(os.path.join(output_dir, 'levelized_cost_by_tech_multiplier.png'),
                dpi=150, bbox_inches='tight')
    print(f"Saved: {output_dir}/levelized_cost_by_tech_multiplier.pdf")

    # ========================================================================
    # FIGURE 6: Impact of Charging Markup (Go RES scenario)
    # ========================================================================
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    scenario = 'Go RES v1.2'
    tech_mult = 1.0
    markup_colors = {0.15: '#1f77b4', 0.30: '#ff7f0e'}

    # Panel 1: BEV cost by markup
    ax = axes[0]
    scenario_df = df[(df['scenario'] == scenario) & (df['tech_mult'] == tech_mult)]

    # ICEV line (same for all markups)
    icev_df = scenario_df[(scenario_df['tech'] == 'ICEV') & (scenario_df['markup'] == 0.15)]
    ax.plot(icev_df['year'], icev_df['total'], 'k-', linewidth=3, label='ICEV', alpha=0.8)

    for markup in MARKUPS:
        bev_df = scenario_df[(scenario_df['tech'] == 'BEV') & (scenario_df['markup'] == markup)]
        ax.plot(bev_df['year'], bev_df['total'], 'o--',
                color=markup_colors[markup], linewidth=2, markersize=5,
                label=f'BEV ({int(markup*100)}% markup)')

    ax.set_xlabel('Year', fontsize=11)
    ax.set_ylabel('Levelized Cost (EUR/km)', fontsize=11)
    ax.set_title(f'Impact of Charging Markup ({SHORT_NAMES[scenario]})',
                fontsize=12, fontweight='bold')
    ax.legend(loc='upper right', fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(2018, 2062)

    # Panel 2: Cost difference by markup
    ax = axes[1]
    for markup in MARKUPS:
        icev_df = scenario_df[(scenario_df['tech'] == 'ICEV') & (scenario_df['markup'] == markup)].set_index('year')
        bev_df = scenario_df[(scenario_df['tech'] == 'BEV') & (scenario_df['markup'] == markup)].set_index('year')
        diff = icev_df['total'] - bev_df['total']
        ax.plot(diff.index, diff.values, 'o-',
                color=markup_colors[markup], linewidth=2.5, markersize=6,
                label=f'{int(markup*100)}% markup')

    ax.axhline(y=0, color='black', linestyle='--', linewidth=1.5)
    ax.fill_between(years, 0, 0.8, alpha=0.1, color='green')
    ax.fill_between(years, -0.8, 0, alpha=0.1, color='red')
    ax.set_xlabel('Year', fontsize=11)
    ax.set_ylabel('Cost Difference: ICEV - BEV (EUR/km)', fontsize=11)
    ax.set_title(f'Break-even by Charging Markup ({SHORT_NAMES[scenario]})',
                fontsize=12, fontweight='bold')
    ax.legend(loc='upper left', fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(2018, 2062)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'levelized_cost_by_charging_markup.pdf'),
                dpi=150, bbox_inches='tight')
    plt.savefig(os.path.join(output_dir, 'levelized_cost_by_charging_markup.png'),
                dpi=150, bbox_inches='tight')
    print(f"Saved: {output_dir}/levelized_cost_by_charging_markup.pdf")

    # ========================================================================
    # FIGURE 7: Full Parameter Space Heatmap (2040)
    # ========================================================================
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    year_select = 2040

    for idx, scenario in enumerate(['Go RES v1.2', 'Trinity v1.2']):
        # Get data for this scenario and year
        scenario_df = df[(df['scenario'] == scenario) & (df['year'] == year_select)]

        # Create pivot table for BEV costs
        bev_pivot = scenario_df[scenario_df['tech'] == 'BEV'].pivot_table(
            values='total', index='tech_mult', columns='markup')

        # Create pivot table for cost difference (ICEV - BEV)
        icev_df = scenario_df[scenario_df['tech'] == 'ICEV'].set_index(['tech_mult', 'markup'])['total']
        bev_df = scenario_df[scenario_df['tech'] == 'BEV'].set_index(['tech_mult', 'markup'])['total']
        diff_df = (icev_df - bev_df).reset_index()
        diff_pivot = diff_df.pivot_table(values='total', index='tech_mult', columns='markup')

        # Panel 1: BEV levelized cost
        ax = axes[idx, 0]
        im = ax.imshow(bev_pivot.values, cmap='YlOrRd', aspect='auto')
        ax.set_xticks(range(len(MARKUPS)))
        ax.set_xticklabels([f'{int(m*100)}%' for m in MARKUPS])
        ax.set_yticks(range(len(TECH_MULTIPLIERS)))
        ax.set_yticklabels([f'{t}x' for t in TECH_MULTIPLIERS])
        ax.set_xlabel('Charging Markup', fontsize=11)
        ax.set_ylabel('Tech Cost Multiplier', fontsize=11)
        ax.set_title(f'BEV Levelized Cost {year_select}\n({SHORT_NAMES[scenario]})',
                    fontsize=11, fontweight='bold')

        # Add values
        for i in range(len(TECH_MULTIPLIERS)):
            for j in range(len(MARKUPS)):
                ax.text(j, i, f'{bev_pivot.values[i, j]:.3f}',
                       ha='center', va='center', fontsize=10, fontweight='bold')
        plt.colorbar(im, ax=ax, label='EUR/km')

        # Panel 2: Cost difference
        ax = axes[idx, 1]
        im = ax.imshow(diff_pivot.values, cmap='RdYlGn', aspect='auto',
                      vmin=-0.3, vmax=0.5)
        ax.set_xticks(range(len(MARKUPS)))
        ax.set_xticklabels([f'{int(m*100)}%' for m in MARKUPS])
        ax.set_yticks(range(len(TECH_MULTIPLIERS)))
        ax.set_yticklabels([f'{t}x' for t in TECH_MULTIPLIERS])
        ax.set_xlabel('Charging Markup', fontsize=11)
        ax.set_ylabel('Tech Cost Multiplier', fontsize=11)
        ax.set_title(f'Cost Diff (ICEV-BEV) {year_select}\n({SHORT_NAMES[scenario]})',
                    fontsize=11, fontweight='bold')

        # Add values
        for i in range(len(TECH_MULTIPLIERS)):
            for j in range(len(MARKUPS)):
                val = diff_pivot.values[i, j]
                color = 'white' if abs(val) > 0.15 else 'black'
                ax.text(j, i, f'{val:+.3f}',
                       ha='center', va='center', fontsize=10, fontweight='bold', color=color)
        plt.colorbar(im, ax=ax, label='EUR/km (+ve = BEV cheaper)')

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'levelized_cost_parameter_heatmap_2040.pdf'),
                dpi=150, bbox_inches='tight')
    plt.savefig(os.path.join(output_dir, 'levelized_cost_parameter_heatmap_2040.png'),
                dpi=150, bbox_inches='tight')
    print(f"Saved: {output_dir}/levelized_cost_parameter_heatmap_2040.pdf")

    # ========================================================================
    # PRINT SUMMARY TABLE
    # ========================================================================
    print("\n" + "=" * 100)
    print("LEVELIZED COST SUMMARY (EUR/km) - Selected Years")
    print("=" * 100)

    for scenario in ['Go RES v1.2', 'Trinity v1.2']:
        print(f"\n--- {SHORT_NAMES[scenario]} ---")
        print(f"{'Year':<8} {'ICEV Total':<12} {'BEV Total':<12} {'Difference':<12} {'ICEV Carbon':<12}")
        print("-" * 60)

        for year in [2020, 2030, 2040, 2050, 2060]:
            icev = calc_icev_levelized_cost(year, scenario)
            bev = calc_bev_levelized_cost(year, scenario)
            diff = icev['total'] - bev['total']
            print(f"{year:<8} {icev['total']:<12.4f} {bev['total']:<12.4f} {diff:<+12.4f} {icev['carbon']:<12.4f}")

    # Save to CSV
    csv_path = os.path.join(output_dir, 'levelized_cost_timeseries.csv')
    df.to_csv(csv_path, index=False)
    print(f"\nSaved: {csv_path}")

    print("\n" + "=" * 100)
    print("ANALYSIS COMPLETE")
    print("=" * 100)


if __name__ == '__main__':
    main()
