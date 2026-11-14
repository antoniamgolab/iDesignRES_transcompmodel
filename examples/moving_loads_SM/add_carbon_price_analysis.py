"""
Add analysis showing carbon prices by GENeSYS scenario and their impact on levelized costs.
"""
import json

with open('uncertainty_analysis_results.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

# New cell for carbon price analysis
new_cell_source = '''# Carbon Price Impact on Levelized Costs by GENeSYS Scenario
import matplotlib.pyplot as plt
import numpy as np
import yaml

# Load carbon prices from a scenario to understand the structure
# Carbon prices vary by GENeSYS scenario
genesys_scenarios = ['Go RES', 'NECPEssentials', 'REPowerEU++', 'Trinity']

# Load carbon prices from each GENeSYS scenario
carbon_prices_by_genesys = {}
for i, scenario_name in enumerate(genesys_scenarios):
    # Find a scenario with this GENeSYS scenario
    for case_id, case in cases.items():
        if scenario_name in case['genesys_scenario']:
            # Load the carbon price data
            scenario_folder = f"scenario_{case_id:03d}"
            try:
                with open(f'input_data/uncertainty_scenarios/{scenario_folder}/Fuel.yaml', 'r') as f:
                    fuels = yaml.safe_load(f)
                # Find diesel to get carbon price (stored in diesel cost)
                diesel = next((fuel for fuel in fuels if 'diesel' in fuel['name'].lower()), None)
                if diesel and 'carbon_price' in diesel:
                    carbon_prices_by_genesys[scenario_name] = diesel['carbon_price']
                elif diesel:
                    # Carbon price might be separate
                    with open(f'input_data/uncertainty_scenarios/{scenario_folder}/Model.yaml', 'r') as f:
                        model = yaml.safe_load(f)
                    if 'carbon_price' in model:
                        carbon_prices_by_genesys[scenario_name] = model['carbon_price']
            except Exception as e:
                print(f"Could not load carbon price for {scenario_name}: {e}")
            break

# If carbon prices aren't found in those locations, check emission_factor and carbon cost
if not carbon_prices_by_genesys:
    print("Attempting to find carbon prices from emission factors...")
    for case_id, case in cases.items():
        if 'Go RES' in case['genesys_scenario']:
            scenario_folder = f"scenario_{case_id:03d}"
            with open(f'input_data/uncertainty_scenarios/{scenario_folder}/Fuel.yaml', 'r') as f:
                fuels = yaml.safe_load(f)
            print(f"Fuel keys for scenario {scenario_folder}:")
            for fuel in fuels:
                print(f"  {fuel['name']}: {list(fuel.keys())}")
            break

# Create the plot with two panels
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Colors for GENeSYS scenarios
genesys_colors = {
    'Go RES': '#e41a1c',        # red
    'NECPEssentials': '#377eb8', # blue
    'REPowerEU++': '#4daf4a',    # green
    'Trinity': '#984ea3'         # purple
}

# Left plot: Levelized cost by GENeSYS scenario for year 2040
ax1 = axes[0]
year_target = 2040

# Group scenarios by GENeSYS
for genesys in genesys_scenarios:
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
        # Sort by tech_cost for consistent ordering
        genesys_lcots.sort(key=lambda x: x['tech_cost'])

        # Plot mean and range
        icev_vals = [x['icev'] for x in genesys_lcots]
        bev_vals = [x['bev'] for x in genesys_lcots]

        x_pos = genesys_scenarios.index(genesys)

        # Plot individual points
        for lcot in genesys_lcots:
            ax1.scatter(x_pos - 0.15, lcot['icev'], color='#666666', s=50, alpha=0.7, zorder=3)
            ax1.scatter(x_pos + 0.15, lcot['bev'], color=genesys_colors[genesys], s=50, alpha=0.7, zorder=3)

        # Add mean markers
        ax1.scatter(x_pos - 0.15, np.mean(icev_vals), color='black', s=100, marker='_', linewidths=3, zorder=4)
        ax1.scatter(x_pos + 0.15, np.mean(bev_vals), color=genesys_colors[genesys], s=100, marker='_', linewidths=3, zorder=4)

ax1.set_xticks(range(len(genesys_scenarios)))
ax1.set_xticklabels(genesys_scenarios, rotation=15, ha='right')
ax1.set_ylabel('Levelized Cost (EUR/tkm)')
ax1.set_title(f'Levelized Cost by GENeSYS Scenario - Year {year_target}')
ax1.grid(axis='y', alpha=0.3)

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
ax1.legend(handles=legend_elements, loc='upper right', fontsize=8)

# Right plot: Time series comparison across GENeSYS scenarios
ax2 = axes[1]

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
        ax2.plot(years, bev_mean, '-', color=genesys_colors[genesys], linewidth=2, label=genesys)
        ax2.fill_between(years, bev_min, bev_max, color=genesys_colors[genesys], alpha=0.2)

# Add ICEV reference (same across all scenarios)
first_df = list(levelized_costs_by_scenario.values())[0]
icev_lcot = first_df['icev_lcot'].values
ax2.plot(first_df['year'].values, icev_lcot, 'k--', linewidth=2, label='ICEV (reference)')

ax2.set_xlabel('Year')
ax2.set_ylabel('Levelized Cost (EUR/tkm)')
ax2.set_title('BEV Levelized Cost Over Time by GENeSYS Scenario')
ax2.legend(loc='upper right', fontsize=9)
ax2.grid(alpha=0.3)
ax2.set_ylim(0, None)

plt.tight_layout()
plt.savefig('figures/levelized_cost_by_genesys_scenario.pdf', bbox_inches='tight', dpi=300)
plt.show()

# Print summary statistics
print("\\nLevelized Cost Summary by GENeSYS Scenario (Year 2040):")
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

print("\\nNote: Different GENeSYS scenarios have different electricity and carbon prices.")
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

# Insert after cell 138 (tech cost curve)
nb['cells'].insert(139, new_cell)

with open('uncertainty_analysis_results.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)

print('Added cell 139 with carbon price / GENeSYS scenario analysis')
