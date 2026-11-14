"""
Add carbon price visualization and carbon-adjusted levelized cost analysis to the notebook.
"""

import json
import uuid
from pathlib import Path

notebook_path = Path("uncertainty_analysis_results.ipynb")

# Load notebook
with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

def make_cell(cell_type, source, cell_id=None):
    """Create a notebook cell."""
    if cell_id is None:
        cell_id = str(uuid.uuid4())[:8]

    cell = {
        "cell_type": cell_type,
        "id": cell_id,
        "metadata": {},
        "source": source if isinstance(source, list) else source.split('\n')
    }

    if cell_type == "code":
        cell["execution_count"] = None
        cell["outputs"] = []

    return cell

# Carbon price visualization cells
carbon_price_md = """## Carbon Price Impact on Levelized Costs

The GENeSYS scenarios have different carbon price trajectories that significantly impact the true cost of diesel (ICEV) operations:

| Scenario | 2020 | 2030 | 2040 | 2050 |
|----------|------|------|------|------|
| Go RES | 30 | 200 | 500 | 1000 |
| REPowerEU++ | 30 | 150 | 350 | 700 |
| NECPEssentials | 30 | 100 | 250 | 500 |
| Trinity | 30 | 80 | 180 | 350 |

Carbon pricing adds: `carbon_price (EUR/tCO2) × 0.000266 (tCO2/kWh)` to diesel costs."""

carbon_price_code = '''# Carbon price trajectories from GENeSYS scenarios
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

CARBON_PRICE_TRAJECTORIES = {
    'Go RES': {2020: 30, 2030: 200, 2040: 500, 2050: 1000, 2060: 1000},
    'REPowerEU++': {2020: 30, 2030: 150, 2040: 350, 2050: 700, 2060: 700},
    'NECPEssentials': {2020: 30, 2030: 100, 2040: 250, 2050: 500, 2060: 500},
    'Trinity': {2020: 30, 2030: 80, 2040: 180, 2050: 350, 2060: 350}
}

# Base diesel cost
BASE_DIESEL_COST = 0.1845  # EUR/kWh
DIESEL_EMISSION_FACTOR = 0.000266  # tCO2/kWh (266 gCO2/kWh)

def interpolate_trajectory(traj, years):
    """Interpolate carbon prices for all years."""
    key_years = sorted(traj.keys())
    key_values = [traj[y] for y in key_years]
    return np.interp(years, key_years, key_values)

years = np.arange(2020, 2061, 2)  # Match model timesteps

# Create figure with two subplots
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Color scheme consistent with existing plots
colors = {
    'Go RES': '#2ecc71',
    'REPowerEU++': '#3498db',
    'NECPEssentials': '#f39c12',
    'Trinity': '#e74c3c'
}

# Plot 1: Carbon Price Trajectories
ax1 = axes[0]
for scenario, traj in CARBON_PRICE_TRAJECTORIES.items():
    prices = interpolate_trajectory(traj, years)
    ax1.plot(years, prices, label=scenario, linewidth=2.5, color=colors[scenario])

ax1.set_xlabel('Year', fontsize=12)
ax1.set_ylabel('Carbon Price (EUR/tCO2)', fontsize=12)
ax1.set_title('Carbon Price Trajectories by GENeSYS Scenario', fontsize=14)
ax1.legend(loc='upper left', fontsize=10)
ax1.grid(True, alpha=0.3)
ax1.set_xlim(2020, 2060)

# Plot 2: Diesel Cost with Carbon Price
ax2 = axes[1]
for scenario, traj in CARBON_PRICE_TRAJECTORIES.items():
    carbon_prices = interpolate_trajectory(traj, years)
    carbon_cost_component = carbon_prices * DIESEL_EMISSION_FACTOR
    total_diesel_cost = BASE_DIESEL_COST + carbon_cost_component
    ax2.plot(years, total_diesel_cost, label=scenario, linewidth=2.5, color=colors[scenario])

# Add base diesel cost line
ax2.axhline(y=BASE_DIESEL_COST, color='gray', linestyle='--', linewidth=1.5, label='Base Diesel (no carbon)')

ax2.set_xlabel('Year', fontsize=12)
ax2.set_ylabel('Diesel Cost (EUR/kWh)', fontsize=12)
ax2.set_title('Diesel Cost Including Carbon Price', fontsize=14)
ax2.legend(loc='upper left', fontsize=10)
ax2.grid(True, alpha=0.3)
ax2.set_xlim(2020, 2060)

plt.tight_layout()
plt.savefig('figures/carbon_price_driving_electrification.pdf', bbox_inches='tight', dpi=300)
plt.savefig('figures/carbon_price_driving_electrification.png', bbox_inches='tight', dpi=150)
plt.show()

# Print some key values
print("Carbon cost component added to diesel (EUR/kWh):")
for scenario, traj in CARBON_PRICE_TRAJECTORIES.items():
    cp_2040 = interpolate_trajectory(traj, [2040])[0]
    cc_2040 = cp_2040 * DIESEL_EMISSION_FACTOR
    total_2040 = BASE_DIESEL_COST + cc_2040
    print(f"  {scenario} in 2040: +{cc_2040:.4f} EUR/kWh (total: {total_2040:.4f} EUR/kWh, +{cc_2040/BASE_DIESEL_COST*100:.1f}%)")'''

levelized_cost_carbon_code = '''# Calculate levelized costs WITH carbon pricing
# This shows the true cost comparison between BEV and ICEV

# First, let's load electricity prices from scenario data
from pathlib import Path
import yaml
import pandas as pd

def load_electricity_prices_for_scenario(scenario_dir):
    """Load electricity prices from FuelCost.yaml for a scenario."""
    fuel_cost_path = Path(scenario_dir) / 'FuelCost.yaml'
    if not fuel_cost_path.exists():
        return None

    with open(fuel_cost_path, 'r') as f:
        fuel_costs = yaml.safe_load(f)

    # Find electricity cost (fuel=electricity)
    for fc in fuel_costs:
        if fc.get('fuel') == 'electricity':
            return fc.get('cost_per_kWh', [])
    return None

# Load scenario metadata
scenarios_base = Path('input_data/uncertainty_scenarios')
scenario_dirs = sorted([d for d in scenarios_base.iterdir() if d.is_dir() and d.name.startswith('scenario_')])

# Model parameters
MODEL_YEARS = list(range(2020, 2061, 2))  # 2020, 2022, ..., 2060

# BEV and ICEV efficiency parameters
BEV_EFFICIENCY = 1.2  # kWh/km (for heavy trucks)
ICEV_EFFICIENCY = 3.0  # kWh/km (diesel equivalent for heavy trucks)

# Annual driving distance assumption
ANNUAL_KM = 100000  # km per vehicle per year

# Vehicle capital cost difference (simplified)
# BEV premium over ICEV
BEV_PREMIUM = 50000  # EUR

# Create comparison dataframe
levelized_data = []

for scenario_dir in scenario_dirs[:4]:  # First 4 scenarios (one per GENeSYS)
    scenario_name = scenario_dir.name

    # Load scenario config to get GENeSYS name
    config_path = scenario_dir / 'scenario_config.json'
    if config_path.exists():
        with open(config_path) as f:
            config = json.load(f)
        genesys = config.get('genesys_scenario', '').replace(' v1.2', '')
    else:
        genesys = 'Unknown'

    # Load electricity prices
    elec_prices = load_electricity_prices_for_scenario(scenario_dir)
    if elec_prices is None:
        continue

    # Get carbon price trajectory for this scenario
    if genesys in CARBON_PRICE_TRAJECTORIES:
        carbon_traj = CARBON_PRICE_TRAJECTORIES[genesys]
    else:
        carbon_traj = CARBON_PRICE_TRAJECTORIES['Go RES']  # Default

    for year_idx, year in enumerate(MODEL_YEARS):
        if year_idx >= len(elec_prices):
            break

        elec_price = elec_prices[year_idx]
        carbon_price = interpolate_trajectory(carbon_traj, [year])[0]
        carbon_cost = carbon_price * DIESEL_EMISSION_FACTOR
        diesel_price_with_carbon = BASE_DIESEL_COST + carbon_cost

        # Calculate annual fuel costs
        bev_fuel_cost = elec_price * BEV_EFFICIENCY * ANNUAL_KM
        icev_fuel_cost_base = BASE_DIESEL_COST * ICEV_EFFICIENCY * ANNUAL_KM
        icev_fuel_cost_carbon = diesel_price_with_carbon * ICEV_EFFICIENCY * ANNUAL_KM

        levelized_data.append({
            'scenario': scenario_name,
            'genesys': genesys,
            'year': year,
            'electricity_price': elec_price,
            'carbon_price': carbon_price,
            'diesel_base': BASE_DIESEL_COST,
            'diesel_with_carbon': diesel_price_with_carbon,
            'bev_fuel_cost_annual': bev_fuel_cost,
            'icev_fuel_cost_base': icev_fuel_cost_base,
            'icev_fuel_cost_carbon': icev_fuel_cost_carbon,
            'bev_advantage_base': icev_fuel_cost_base - bev_fuel_cost,
            'bev_advantage_carbon': icev_fuel_cost_carbon - bev_fuel_cost
        })

df_levelized = pd.DataFrame(levelized_data)
print(f"Calculated levelized costs for {len(df_levelized)} scenario-year combinations")
df_levelized.head(10)'''

levelized_comparison_plot = '''# Plot: BEV cost advantage WITH vs WITHOUT carbon pricing
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Get unique scenarios
scenarios_to_plot = df_levelized['genesys'].unique()

ax1 = axes[0]
for genesys in scenarios_to_plot:
    df_scen = df_levelized[df_levelized['genesys'] == genesys]
    color = colors.get(genesys, 'gray')
    ax1.plot(df_scen['year'], df_scen['bev_advantage_base']/1000,
             label=f'{genesys} (no carbon)', linestyle='--', color=color, alpha=0.5)
    ax1.plot(df_scen['year'], df_scen['bev_advantage_carbon']/1000,
             label=f'{genesys} (with carbon)', linewidth=2, color=color)

ax1.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
ax1.set_xlabel('Year', fontsize=12)
ax1.set_ylabel('BEV Annual Fuel Cost Advantage (k EUR)', fontsize=12)
ax1.set_title('BEV vs ICEV: Annual Fuel Cost Difference', fontsize=14)
ax1.legend(loc='upper left', fontsize=8, ncol=2)
ax1.grid(True, alpha=0.3)

# Plot 2: Fuel cost comparison over time for one scenario
ax2 = axes[1]
genesys_focus = 'Go RES'
df_focus = df_levelized[df_levelized['genesys'] == genesys_focus]

ax2.plot(df_focus['year'], df_focus['bev_fuel_cost_annual']/1000,
         label='BEV electricity cost', linewidth=2.5, color='#2ecc71')
ax2.plot(df_focus['year'], df_focus['icev_fuel_cost_base']/1000,
         label='ICEV diesel (no carbon)', linewidth=2, linestyle='--', color='#95a5a6')
ax2.plot(df_focus['year'], df_focus['icev_fuel_cost_carbon']/1000,
         label='ICEV diesel (with carbon)', linewidth=2.5, color='#e74c3c')

ax2.fill_between(df_focus['year'],
                 df_focus['bev_fuel_cost_annual']/1000,
                 df_focus['icev_fuel_cost_carbon']/1000,
                 alpha=0.2, color='#2ecc71', label='BEV advantage')

ax2.set_xlabel('Year', fontsize=12)
ax2.set_ylabel('Annual Fuel Cost (k EUR/vehicle)', fontsize=12)
ax2.set_title(f'Annual Fuel Costs - {genesys_focus} Scenario', fontsize=14)
ax2.legend(loc='upper right', fontsize=10)
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('figures/levelized_cost_with_carbon_prices.pdf', bbox_inches='tight', dpi=300)
plt.show()

# Print key insights
print("\\nKey insight: Carbon pricing makes BEV more attractive over time")
print(f"\\n{genesys_focus} scenario example:")
for year in [2030, 2040, 2050]:
    row = df_focus[df_focus['year'] == year].iloc[0]
    print(f"  {year}: BEV saves EUR {row['bev_advantage_carbon']:,.0f}/year vs ICEV (with carbon)")
    print(f"         Without carbon: BEV saves EUR {row['bev_advantage_base']:,.0f}/year")'''

levelized_by_scenario_code = '''# Create a comprehensive levelized cost comparison across ALL scenarios
# Including charging markup variations

# Recalculate for all 24 scenarios
all_levelized = []

for scenario_dir in scenario_dirs:
    scenario_name = scenario_dir.name

    # Load scenario config
    config_path = scenario_dir / 'scenario_config.json'
    if not config_path.exists():
        continue

    with open(config_path) as f:
        config = json.load(f)

    genesys = config.get('genesys_scenario', '').replace(' v1.2', '')
    charging_markup = config.get('charging_markup', 0.15)
    tech_cost_mult = config.get('tech_cost_multiplier', 1.0)

    # Load electricity prices
    elec_prices = load_electricity_prices_for_scenario(scenario_dir)
    if elec_prices is None:
        continue

    # Get carbon price trajectory
    carbon_key = genesys if genesys in CARBON_PRICE_TRAJECTORIES else 'Go RES'
    carbon_traj = CARBON_PRICE_TRAJECTORIES[carbon_key]

    for year_idx, year in enumerate(MODEL_YEARS):
        if year_idx >= len(elec_prices):
            break

        elec_price = elec_prices[year_idx]
        elec_price_with_markup = elec_price * (1 + charging_markup)

        carbon_price = interpolate_trajectory(carbon_traj, [year])[0]
        carbon_cost = carbon_price * DIESEL_EMISSION_FACTOR
        diesel_with_carbon = BASE_DIESEL_COST + carbon_cost

        # Annual costs with markup
        bev_fuel_cost = elec_price_with_markup * BEV_EFFICIENCY * ANNUAL_KM
        icev_fuel_cost = diesel_with_carbon * ICEV_EFFICIENCY * ANNUAL_KM

        all_levelized.append({
            'scenario': scenario_name,
            'genesys': genesys,
            'charging_markup': charging_markup,
            'tech_cost_mult': tech_cost_mult,
            'year': year,
            'elec_price_base': elec_price,
            'elec_price_with_markup': elec_price_with_markup,
            'carbon_price': carbon_price,
            'diesel_with_carbon': diesel_with_carbon,
            'bev_fuel_cost': bev_fuel_cost,
            'icev_fuel_cost': icev_fuel_cost,
            'bev_advantage': icev_fuel_cost - bev_fuel_cost
        })

df_all = pd.DataFrame(all_levelized)
print(f"Loaded {len(df_all)} scenario-year combinations across {len(scenario_dirs)} scenarios")'''

scenario_specific_carbon_plot = '''# Plot levelized costs for each GENeSYS scenario with its carbon price
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

for idx, genesys in enumerate(['Go RES', 'REPowerEU++', 'NECPEssentials', 'Trinity']):
    ax = axes[idx // 2, idx % 2]

    df_g = df_all[(df_all['genesys'] == genesys) & (df_all['charging_markup'] == 0.15) & (df_all['tech_cost_mult'] == 1.0)]

    if len(df_g) > 0:
        # Plot BEV and ICEV costs
        ax.plot(df_g['year'], df_g['bev_fuel_cost']/1000,
                label='BEV (with 15% markup)', linewidth=2.5, color='#2ecc71')
        ax.plot(df_g['year'], df_g['icev_fuel_cost']/1000,
                label='ICEV (with carbon)', linewidth=2.5, color='#e74c3c')

        # Add crossover point
        df_g = df_g.reset_index(drop=True)
        crossover_idx = None
        for i in range(1, len(df_g)):
            if df_g.loc[i-1, 'bev_advantage'] < 0 and df_g.loc[i, 'bev_advantage'] >= 0:
                crossover_idx = i
                break

        if crossover_idx:
            crossover_year = df_g.loc[crossover_idx, 'year']
            ax.axvline(x=crossover_year, color='gray', linestyle=':', alpha=0.7)
            ax.annotate(f'Crossover\\n{crossover_year}', xy=(crossover_year, ax.get_ylim()[1]*0.8),
                       fontsize=9, ha='center')

        # Carbon price on secondary axis
        ax2 = ax.twinx()
        ax2.plot(df_g['year'], df_g['carbon_price'],
                 label='Carbon price', linewidth=1.5, linestyle='--', color='gray', alpha=0.6)
        ax2.set_ylabel('Carbon Price (EUR/tCO2)', fontsize=10, color='gray')
        ax2.tick_params(axis='y', labelcolor='gray')

    ax.set_xlabel('Year', fontsize=11)
    ax.set_ylabel('Annual Fuel Cost (k EUR/vehicle)', fontsize=11)
    ax.set_title(f'{genesys} Scenario', fontsize=12, fontweight='bold')
    ax.legend(loc='upper left', fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(2020, 2060)

plt.suptitle('Levelized Fuel Costs by GENeSYS Scenario (with carbon pricing)', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('figures/levelized_cost_scenario_specific_carbon.pdf', bbox_inches='tight', dpi=300)
plt.show()'''

# Create the cells
new_cells = [
    make_cell("markdown", carbon_price_md, "carbon_md"),
    make_cell("code", carbon_price_code, "carbon_code"),
    make_cell("markdown", "### Levelized Costs with Carbon Pricing\n\nThe optimization model may implicitly consider carbon pricing through various mechanisms. Let's calculate the carbon-adjusted levelized costs:", "level_md"),
    make_cell("code", levelized_cost_carbon_code, "level_code"),
    make_cell("code", levelized_comparison_plot, "level_plot"),
    make_cell("code", levelized_by_scenario_code, "all_level"),
    make_cell("code", scenario_specific_carbon_plot, "scen_plot"),
]

# Find a good insertion point - after cell 100 or at the end
insert_idx = min(100, len(nb['cells']))

# Insert cells
for i, cell in enumerate(new_cells):
    nb['cells'].insert(insert_idx + i, cell)

# Save updated notebook
with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print(f"Added {len(new_cells)} cells to {notebook_path}")
print(f"Cells inserted at index {insert_idx}")
print("New cells cover:")
print("  - Carbon price trajectories by GENeSYS scenario")
print("  - Diesel cost including carbon price over time")
print("  - Levelized cost comparison WITH carbon pricing")
print("  - Per-scenario levelized cost analysis")
