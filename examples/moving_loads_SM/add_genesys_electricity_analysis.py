"""
Add analysis showing electricity prices by GENeSYS scenario and their impact on levelized costs.
"""
import json

with open('uncertainty_analysis_results.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

# New cell for electricity price and levelized cost analysis by GENeSYS scenario
new_cell_source = '''# Electricity Prices and Levelized Costs by GENeSYS Scenario
import matplotlib.pyplot as plt
import numpy as np
import yaml

# GENeSYS scenarios and their colors
genesys_scenarios = ['Go RES', 'NECPEssentials', 'REPowerEU++', 'Trinity']
genesys_colors = {
    'Go RES': '#e41a1c',        # red
    'NECPEssentials': '#377eb8', # blue
    'REPowerEU++': '#4daf4a',    # green
    'Trinity': '#984ea3'         # purple
}

# Find one representative scenario for each GENeSYS
genesys_case_ids = {}
for case_id, case in cases.items():
    for gs in genesys_scenarios:
        if gs in case['genesys_scenario'] and gs not in genesys_case_ids:
            genesys_case_ids[gs] = case_id
            break

# Load electricity prices from each GENeSYS scenario
elec_prices_by_genesys = {}
for gs, case_id in genesys_case_ids.items():
    scenario_dir = f'input_data/uncertainty_scenarios/scenario_{case_id:03d}'
    with open(f'{scenario_dir}/FuelCost.yaml', 'r') as f:
        fuel_costs = yaml.safe_load(f)
    elec = next((fc for fc in fuel_costs if fc['fuel'] == 'electricity'), None)
    if elec:
        elec_prices_by_genesys[gs] = elec['cost_per_kWh'][:11]  # First 11 years (2020-2060)

# Years for electricity prices
elec_years = list(range(2020, 2061, 4))[:11]

# Create figure with 3 subplots
fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# Panel 1: Electricity prices over time
ax1 = axes[0]
for gs in genesys_scenarios:
    if gs in elec_prices_by_genesys:
        ax1.plot(elec_years, elec_prices_by_genesys[gs], '-o',
                 color=genesys_colors[gs], linewidth=2, markersize=4, label=gs)
ax1.set_xlabel('Year')
ax1.set_ylabel('Electricity Price (EUR/kWh)')
ax1.set_title('Electricity Prices by GENeSYS Scenario')
ax1.legend(loc='upper right', fontsize=9)
ax1.grid(alpha=0.3)
ax1.set_xlim(2020, 2060)

# Panel 2: Levelized cost by GENeSYS scenario for year 2040
ax2 = axes[1]
year_target = 2040

# Group scenarios by GENeSYS
x_positions = []
for i, genesys in enumerate(genesys_scenarios):
    genesys_lcots = []
    for scenario, lcot_df in levelized_costs_by_scenario.items():
        case_id = int(scenario.replace('scenario_', ''))
        case = cases[case_id]
        if genesys in case['genesys_scenario']:
            row = lcot_df[lcot_df['year'] == year_target].iloc[0]
            genesys_lcots.append({
                'icev': row['icev_lcot'],
                'bev': row['bev_lcot'],
                'tech_cost': case['tech_cost_multiplier']
            })

    if genesys_lcots:
        # Plot individual points
        for lcot in genesys_lcots:
            ax2.scatter(i - 0.15, lcot['icev'], color='#666666', s=50, alpha=0.7, zorder=3)
            ax2.scatter(i + 0.15, lcot['bev'], color=genesys_colors[genesys], s=50, alpha=0.7, zorder=3)

        # Add mean markers
        icev_mean = np.mean([x['icev'] for x in genesys_lcots])
        bev_mean = np.mean([x['bev'] for x in genesys_lcots])
        ax2.scatter(i - 0.15, icev_mean, color='black', s=100, marker='_', linewidths=3, zorder=4)
        ax2.scatter(i + 0.15, bev_mean, color=genesys_colors[genesys], s=100, marker='_', linewidths=3, zorder=4)

ax2.set_xticks(range(len(genesys_scenarios)))
ax2.set_xticklabels(genesys_scenarios, rotation=15, ha='right')
ax2.set_ylabel('Levelized Cost (EUR/tkm)')
ax2.set_title(f'Levelized Cost by GENeSYS Scenario - Year {year_target}')
ax2.grid(axis='y', alpha=0.3)

# Add legend
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
legend_elements = [
    Line2D([0], [0], marker='o', color='w', markerfacecolor='#666666', markersize=8, label='ICEV'),
    Patch(facecolor='#e41a1c', alpha=0.7, label='BEV - Go RES'),
    Patch(facecolor='#377eb8', alpha=0.7, label='BEV - NECPEssentials'),
    Patch(facecolor='#4daf4a', alpha=0.7, label='BEV - REPowerEU++'),
    Patch(facecolor='#984ea3', alpha=0.7, label='BEV - Trinity'),
]
ax2.legend(handles=legend_elements, loc='upper right', fontsize=8)

# Panel 3: Time series comparison across GENeSYS scenarios
ax3 = axes[2]

for genesys in genesys_scenarios:
    # Get all scenarios for this GENeSYS
    genesys_lcot_dfs = []
    for scenario, lcot_df in levelized_costs_by_scenario.items():
        case_id = int(scenario.replace('scenario_', ''))
        case = cases[case_id]
        if genesys in case['genesys_scenario']:
            genesys_lcot_dfs.append(lcot_df)

    if genesys_lcot_dfs:
        # Get years from first scenario
        years = genesys_lcot_dfs[0]['year'].values

        # Calculate mean BEV LCOT across scenarios with same GENeSYS
        bev_lcots = np.array([df['bev_lcot'].values for df in genesys_lcot_dfs])
        bev_mean = bev_lcots.mean(axis=0)
        bev_min = bev_lcots.min(axis=0)
        bev_max = bev_lcots.max(axis=0)

        # Plot mean line with range
        ax3.plot(years, bev_mean, '-', color=genesys_colors[genesys], linewidth=2, label=genesys)
        ax3.fill_between(years, bev_min, bev_max, color=genesys_colors[genesys], alpha=0.2)

# Add ICEV reference (same across all scenarios)
first_df = list(levelized_costs_by_scenario.values())[0]
icev_lcot = first_df['icev_lcot'].values
ax3.plot(first_df['year'].values, icev_lcot, 'k--', linewidth=2, label='ICEV (reference)')

ax3.set_xlabel('Year')
ax3.set_ylabel('Levelized Cost (EUR/tkm)')
ax3.set_title('BEV Levelized Cost Over Time by GENeSYS Scenario')
ax3.legend(loc='upper right', fontsize=9)
ax3.grid(alpha=0.3)
ax3.set_ylim(0, None)

plt.tight_layout()
plt.savefig('figures/levelized_cost_by_genesys_scenario.pdf', bbox_inches='tight', dpi=300)
plt.show()

# Print summary statistics
print("\\n=== Electricity Price Summary by GENeSYS Scenario ===")
print(f"{'Scenario':<20} {'2020':>8} {'2040':>8} {'2056':>8} EUR/kWh")
print("-" * 50)
for gs in genesys_scenarios:
    if gs in elec_prices_by_genesys:
        prices = elec_prices_by_genesys[gs]
        print(f"{gs:<20} {prices[0]:>8.4f} {prices[5]:>8.4f} {prices[9]:>8.4f}")

print("\\n=== Levelized Cost Summary by GENeSYS Scenario (Year 2040) ===")
print("-" * 70)
for genesys in genesys_scenarios:
    genesys_lcots = []
    for scenario, lcot_df in levelized_costs_by_scenario.items():
        case_id = int(scenario.replace('scenario_', ''))
        case = cases[case_id]
        if genesys in case['genesys_scenario']:
            row = lcot_df[lcot_df['year'] == year_target].iloc[0]
            genesys_lcots.append(row['bev_lcot'])

    if genesys_lcots:
        print(f"{genesys:20s}: BEV mean={np.mean(genesys_lcots):.4f} EUR/tkm (range: {min(genesys_lcots):.4f}-{max(genesys_lcots):.4f})")

print("\\nNote: Different GENeSYS scenarios have different electricity prices.")
print("The variation within each GENeSYS scenario comes from tech_cost and charging_markup differences.")
'''

new_cell = {
    'cell_type': 'code',
    'execution_count': None,
    'metadata': {},
    'outputs': [],
    'source': [line + '\n' for line in new_cell_source.strip().split('\n')]
}
new_cell['source'][-1] = new_cell['source'][-1].rstrip('\n')

# Find the position after the carbon price analysis cell (139) or insert at appropriate location
# Let's find the last levelized cost cell and insert after it
insert_position = None
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if 'levelized_cost_by_tech_cost_multiplier' in source or 'levelized_cost_comparison_2040' in source:
            insert_position = i + 1

if insert_position is None:
    insert_position = 140  # Default position

nb['cells'].insert(insert_position, new_cell)

with open('uncertainty_analysis_results.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)

print(f'Added GENeSYS electricity price / levelized cost analysis cell at position {insert_position}')
