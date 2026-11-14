"""
Add time series curves showing levelized cost over time for tech_cost=1.3 scenarios.
"""
import json

with open('uncertainty_analysis_results.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

# New cell for tech_cost=1.3 time series
new_cell_source = '''# Levelized Cost over Time by Tech Cost Multiplier (0.7x, 1.0x, 1.3x)
import matplotlib.pyplot as plt
import numpy as np

fig, axes = plt.subplots(1, 3, figsize=(16, 5))

tech_cost_values = [0.7, 1.0, 1.3]
tech_cost_colors = {'0.7': '#2ca02c', '1.0': '#1f77b4', '1.3': '#d62728'}  # green, blue, red

for ax_idx, tc_val in enumerate(tech_cost_values):
    ax = axes[ax_idx]

    # Filter scenarios by tech_cost_multiplier
    tc_scenarios = {}
    for scenario, lcot_df in levelized_costs_by_scenario.items():
        case_id = int(scenario.replace('scenario_', ''))
        case = cases[case_id]
        if abs(case['tech_cost_multiplier'] - tc_val) < 0.01:
            tc_scenarios[scenario] = lcot_df

    if not tc_scenarios:
        ax.text(0.5, 0.5, f'No scenarios with\\ntech_cost={tc_val}',
                ha='center', va='center', transform=ax.transAxes)
        ax.set_title(f'Tech Cost = {tc_val}x')
        continue

    # Get years from first scenario
    first_df = list(tc_scenarios.values())[0]
    years = first_df['year'].values

    # Collect ICEV and BEV values
    icev_values = []
    bev_values = []
    for scenario, lcot_df in tc_scenarios.items():
        icev_values.append(lcot_df['icev_lcot'].values)
        bev_values.append(lcot_df['bev_lcot'].values)

    icev_arr = np.array(icev_values)
    bev_arr = np.array(bev_values)

    # Plot range (shaded)
    ax.fill_between(years, icev_arr.min(axis=0), icev_arr.max(axis=0),
                    alpha=0.2, color='#666666', label='ICEV range')
    ax.fill_between(years, bev_arr.min(axis=0), bev_arr.max(axis=0),
                    alpha=0.3, color=tech_cost_colors[str(tc_val)], label='BEV range')

    # Plot mean lines
    ax.plot(years, icev_arr.mean(axis=0), 'k-', linewidth=2, label='ICEV mean')
    ax.plot(years, bev_arr.mean(axis=0), '-', linewidth=2,
            color=tech_cost_colors[str(tc_val)], label='BEV mean')

    ax.set_xlabel('Year')
    ax.set_ylabel('Levelized Cost (EUR/tkm)')
    ax.set_title(f'Tech Cost = {tc_val}x ({len(tc_scenarios)} scenarios)')
    ax.legend(loc='upper right', fontsize=8)
    ax.grid(alpha=0.3)
    ax.set_ylim(0, None)

plt.tight_layout()
plt.savefig('figures/levelized_cost_by_tech_cost_multiplier.pdf', bbox_inches='tight', dpi=300)
plt.show()

# Print summary statistics
print("\\nCost Crossover Years by Tech Cost Multiplier:")
for tc_val in tech_cost_values:
    tc_scenarios = {s: df for s, df in levelized_costs_by_scenario.items()
                    if abs(cases[int(s.replace('scenario_', ''))]['tech_cost_multiplier'] - tc_val) < 0.01}

    crossover_years = []
    for scenario, lcot_df in tc_scenarios.items():
        for i, row in lcot_df.iterrows():
            if row['bev_lcot'] < row['icev_lcot']:
                crossover_years.append(row['year'])
                break

    if crossover_years:
        print(f"  tech_cost={tc_val}x: crossover in {min(crossover_years)}-{max(crossover_years)} (mean: {np.mean(crossover_years):.0f})")
    else:
        print(f"  tech_cost={tc_val}x: BEV never cheaper in any scenario")
'''

new_cell = {
    'cell_type': 'code',
    'execution_count': None,
    'metadata': {},
    'outputs': [],
    'source': [line + '\n' for line in new_cell_source.strip().split('\n')]
}
new_cell['source'][-1] = new_cell['source'][-1].rstrip('\n')

# Insert after cell 137 (time series cell)
nb['cells'].insert(138, new_cell)

with open('uncertainty_analysis_results.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)

print('Added cell 138 with tech_cost time series comparison')
