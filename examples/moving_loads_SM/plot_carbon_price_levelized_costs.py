"""
Plot carbon prices and resulting levelized fuel costs for the 4 GENeSYS scenarios.
This addresses the question about how different carbon prices affect costs beyond Go RES.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os

# ============================================================================
# CARBON PRICE TRAJECTORIES FOR 4 GENeSYS SCENARIOS (EUR/tCO2)
# ============================================================================
carbon_prices = {
    'Go RES v1.2': {2020: 30, 2030: 200, 2040: 500, 2050: 1000, 2060: 1000},
    'REPowerEU++ v1.2': {2020: 30, 2030: 150, 2040: 350, 2050: 700, 2060: 700},
    'NECPEssentials v1.2': {2020: 30, 2030: 100, 2040: 250, 2050: 500, 2060: 500},
    'Trinity v1.2': {2020: 30, 2030: 80, 2040: 180, 2050: 350, 2060: 350}
}

# Short names for plotting
short_names = {
    'Go RES v1.2': 'Go RES',
    'REPowerEU++ v1.2': 'REPowerEU++',
    'NECPEssentials v1.2': 'NECPEssentials',
    'Trinity v1.2': 'Trinity'
}

# Colors for scenarios
colors = {
    'Go RES v1.2': '#1f77b4',
    'REPowerEU++ v1.2': '#ff7f0e',
    'NECPEssentials v1.2': '#2ca02c',
    'Trinity v1.2': '#d62728'
}

# ============================================================================
# FUEL COST PARAMETERS (from the model data)
# ============================================================================
DIESEL_BASE_COST = 0.1845  # EUR/kWh (constant across all years)
DIESEL_EMISSION_FACTOR = 266  # gCO2/kWh = 0.266 kgCO2/kWh

# Representative electricity price (average for 2040, using Go RES scenario)
# From the FuelCost.yaml analysis, electricity prices vary by location
# Using an average value around 0.17 EUR/kWh in 2040 (declining from ~0.37-0.61 in 2020)
electricity_prices = {
    2020: 0.49,  # EUR/kWh (average estimate)
    2024: 0.40,
    2028: 0.30,
    2032: 0.22,
    2036: 0.18,
    2040: 0.17,
    2044: 0.17,
    2048: 0.17,
    2052: 0.17,
    2056: 0.17,
    2060: 0.17
}

# Charging markup (from scenario metadata)
CHARGING_MARKUP = 0.15  # 15% markup on electricity price


def interpolate_carbon_price(year, trajectory):
    """Interpolate carbon price for any year."""
    years = sorted(trajectory.keys())
    if year <= years[0]:
        return trajectory[years[0]]
    if year >= years[-1]:
        return trajectory[years[-1]]

    for i in range(len(years) - 1):
        if years[i] <= year <= years[i+1]:
            t = (year - years[i]) / (years[i+1] - years[i])
            return trajectory[years[i]] * (1 - t) + trajectory[years[i+1]] * t
    return trajectory[years[-1]]


def calc_diesel_levelized_cost(year, scenario):
    """Calculate levelized diesel cost including carbon pricing."""
    carbon_price = interpolate_carbon_price(year, carbon_prices[scenario])
    # Convert carbon price from EUR/tCO2 to EUR/kWh
    # Emission factor is 266 gCO2/kWh = 0.266 kgCO2/kWh = 0.000266 tCO2/kWh
    carbon_cost_per_kwh = carbon_price * DIESEL_EMISSION_FACTOR / 1e6  # EUR/kWh
    return DIESEL_BASE_COST + carbon_cost_per_kwh


def calc_electricity_levelized_cost(year):
    """Calculate levelized electricity cost including charging markup."""
    # Interpolate if year not exact
    if year in electricity_prices:
        base_price = electricity_prices[year]
    else:
        years = sorted(electricity_prices.keys())
        for i in range(len(years) - 1):
            if years[i] <= year <= years[i+1]:
                t = (year - years[i]) / (years[i+1] - years[i])
                base_price = electricity_prices[years[i]] * (1 - t) + electricity_prices[years[i+1]] * t
                break
        else:
            base_price = electricity_prices[years[-1]]

    return base_price * (1 + CHARGING_MARKUP)


# ============================================================================
# CREATE VISUALIZATION
# ============================================================================
years = np.arange(2020, 2061, 4)

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# ============================
# Plot 1: Carbon price trajectories
# ============================
ax1 = axes[0, 0]
for scenario in carbon_prices:
    cp_values = [interpolate_carbon_price(y, carbon_prices[scenario]) for y in years]
    ax1.plot(years, cp_values, 'o-', label=short_names[scenario], color=colors[scenario], linewidth=2, markersize=5)

ax1.set_xlabel('Year', fontsize=11)
ax1.set_ylabel('Carbon Price (EUR/tCO2)', fontsize=11)
ax1.set_title('Carbon Price Trajectories by GENeSYS Scenario', fontsize=12, fontweight='bold')
ax1.legend(loc='upper left', fontsize=9)
ax1.grid(True, alpha=0.3)
ax1.set_xlim(2018, 2062)

# ============================
# Plot 2: Levelized diesel cost (including carbon)
# ============================
ax2 = axes[0, 1]
for scenario in carbon_prices:
    diesel_costs = [calc_diesel_levelized_cost(y, scenario) for y in years]
    ax2.plot(years, diesel_costs, 'o-', label=short_names[scenario], color=colors[scenario], linewidth=2, markersize=5)

# Add base diesel cost line
ax2.axhline(y=DIESEL_BASE_COST, color='gray', linestyle='--', linewidth=1.5, label=f'Diesel base ({DIESEL_BASE_COST:.3f})')

ax2.set_xlabel('Year', fontsize=11)
ax2.set_ylabel('Levelized Diesel Cost (EUR/kWh)', fontsize=11)
ax2.set_title('Diesel Cost with Carbon Pricing', fontsize=12, fontweight='bold')
ax2.legend(loc='upper left', fontsize=9)
ax2.grid(True, alpha=0.3)
ax2.set_xlim(2018, 2062)

# ============================
# Plot 3: Electricity vs Diesel comparison
# ============================
ax3 = axes[1, 0]

# Electricity cost (same for all scenarios)
elec_costs = [calc_electricity_levelized_cost(y) for y in years]
ax3.plot(years, elec_costs, 's-', label='Electricity (with markup)', color='green', linewidth=2.5, markersize=6)

# Diesel costs by scenario
for scenario in carbon_prices:
    diesel_costs = [calc_diesel_levelized_cost(y, scenario) for y in years]
    ax3.plot(years, diesel_costs, 'o-', label=f'Diesel ({short_names[scenario]})', color=colors[scenario], linewidth=1.5, markersize=4, alpha=0.8)

ax3.set_xlabel('Year', fontsize=11)
ax3.set_ylabel('Levelized Fuel Cost (EUR/kWh)', fontsize=11)
ax3.set_title('Electricity vs Diesel Cost Comparison', fontsize=12, fontweight='bold')
ax3.legend(loc='upper left', fontsize=8, ncol=2)
ax3.grid(True, alpha=0.3)
ax3.set_xlim(2018, 2062)

# ============================
# Plot 4: Cost ratio (diesel/electricity)
# ============================
ax4 = axes[1, 1]
for scenario in carbon_prices:
    ratios = []
    for y in years:
        diesel = calc_diesel_levelized_cost(y, scenario)
        elec = calc_electricity_levelized_cost(y)
        ratios.append(diesel / elec)
    ax4.plot(years, ratios, 'o-', label=short_names[scenario], color=colors[scenario], linewidth=2, markersize=5)

ax4.axhline(y=1.0, color='black', linestyle='--', linewidth=1.5, label='Break-even')
ax4.fill_between(years, 0, 1, alpha=0.1, color='green', label='BEV advantage')
ax4.fill_between(years, 1, max([calc_diesel_levelized_cost(2060, s) / calc_electricity_levelized_cost(2060) for s in carbon_prices]) + 0.5, alpha=0.1, color='red', label='ICEV advantage')

ax4.set_xlabel('Year', fontsize=11)
ax4.set_ylabel('Diesel/Electricity Cost Ratio', fontsize=11)
ax4.set_title('Fuel Cost Competitiveness (>1 = BEV cheaper per kWh)', fontsize=12, fontweight='bold')
ax4.legend(loc='upper left', fontsize=8, ncol=2)
ax4.grid(True, alpha=0.3)
ax4.set_xlim(2018, 2062)
ax4.set_ylim(0, 4)

plt.tight_layout()

# Save figure
os.makedirs('figures', exist_ok=True)
plt.savefig('figures/carbon_price_driving_electrification.pdf', dpi=150, bbox_inches='tight')
plt.savefig('figures/carbon_price_driving_electrification.png', dpi=150, bbox_inches='tight')
print('Saved: figures/carbon_price_driving_electrification.pdf')

# ============================================================================
# CREATE DETAILED DATA TABLE
# ============================================================================
print("\n" + "=" * 100)
print("LEVELIZED FUEL COSTS BY SCENARIO AND YEAR (EUR/kWh)")
print("=" * 100)

print(f"\n{'Year':<6}", end="")
print(f"{'Electricity':<14}", end="")
for scenario in carbon_prices:
    print(f"{short_names[scenario]:<16}", end="")
print()
print("-" * 80)

for y in [2020, 2030, 2040, 2050, 2060]:
    elec = calc_electricity_levelized_cost(y)
    print(f"{y:<6}{elec:<14.3f}", end="")
    for scenario in carbon_prices:
        diesel = calc_diesel_levelized_cost(y, scenario)
        print(f"{diesel:<16.3f}", end="")
    print()

print("\n" + "=" * 100)
print("COST RATIO (DIESEL / ELECTRICITY) - Values >1 indicate BEV is cheaper per kWh")
print("=" * 100)

print(f"\n{'Year':<6}", end="")
for scenario in carbon_prices:
    print(f"{short_names[scenario]:<16}", end="")
print()
print("-" * 70)

for y in [2020, 2030, 2040, 2050, 2060]:
    elec = calc_electricity_levelized_cost(y)
    print(f"{y:<6}", end="")
    for scenario in carbon_prices:
        diesel = calc_diesel_levelized_cost(y, scenario)
        ratio = diesel / elec
        print(f"{ratio:<16.2f}", end="")
    print()

# ============================================================================
# KEY INSIGHTS
# ============================================================================
print("\n" + "=" * 100)
print("KEY INSIGHTS")
print("=" * 100)
print("""
1. CARBON PRICE VARIATION:
   - Go RES has the highest carbon prices (500 EUR/t in 2040)
   - Trinity has the lowest carbon prices (180 EUR/t in 2040)
   - This represents a 2.8x difference in 2040 carbon prices

2. IMPACT ON DIESEL COSTS:
   - In 2040, diesel costs range from 0.23 EUR/kWh (Trinity) to 0.32 EUR/kWh (Go RES)
   - Carbon pricing adds 0.048 - 0.133 EUR/kWh to base diesel cost

3. ELECTRICITY COMPETITIVENESS:
   - Electricity (with 15% markup) costs ~0.19 EUR/kWh in 2040
   - In ALL scenarios, diesel becomes more expensive than electricity by 2030-2035
   - The transition point varies: earlier in Go RES, later in Trinity

4. WHY BEV ADOPTION IS LIMITED:
   - Despite fuel cost advantage, BEV adoption remains low due to:
     * High upfront vehicle costs (tech_cost_multiplier effect)
     * Infrastructure constraints
     * Constant diesel base price assumption (unrealistic)

5. REALISTIC DIESEL PRICING:
   - Current model uses constant 0.1845 EUR/kWh diesel base price
   - Real diesel prices would likely increase due to:
     * Carbon pass-through
     * Supply constraints
     * Policy measures
""")

# plt.show()  # Commented for non-interactive execution
