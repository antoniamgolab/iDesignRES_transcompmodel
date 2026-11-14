"""
Fix the levelized cost visualization to use distinct colors instead of grey.
"""
import json

with open('uncertainty_analysis_results.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Replace cell 136 with improved version - better colors
new_cell_136_source = '''# Plot levelized costs comparison for year 2040
import matplotlib.pyplot as plt
import numpy as np

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Left plot: Levelized cost by scenario
ax1 = axes[0]
year_target = 2040

# Define distinct colors for each scenario group
genesys_colors = {
    'Go RES': '#e41a1c',        # red
    'NECPEssentials': '#377eb8', # blue
    'REPowerEU++': '#4daf4a',    # green
    'Trinity': '#984ea3'         # purple
}

x_positions = []
labels = []
icev_values = []
bev_values = []
bar_colors = []

for i, (scenario, lcot_df) in enumerate(sorted(levelized_costs_by_scenario.items())):
    case_id = int(scenario.replace('scenario_', ''))
    case = cases[case_id]

    row = lcot_df[lcot_df['year'] == year_target].iloc[0]

    x_positions.append(i)
    labels.append(f'{case_id}')
    icev_values.append(row['icev_lcot'])
    bev_values.append(row['bev_lcot'])

    # Assign color by GENeSYS scenario
    found_color = False
    for gs, color in genesys_colors.items():
        if gs in case['genesys_scenario']:
            bar_colors.append(color)
            found_color = True
            break
    if not found_color:
        bar_colors.append('#999999')  # fallback gray

width = 0.35
x_arr = np.array(x_positions)

# Plot ICEV bars (all same gray)
ax1.bar(x_arr - width/2, icev_values, width, label='ICEV', color='#666666', alpha=0.8)

# Plot BEV bars with GENeSYS colors
ax1.bar(x_arr + width/2, bev_values, width, color=bar_colors, alpha=0.9)

ax1.set_xlabel('Scenario ID')
ax1.set_ylabel('Levelized Cost (EUR/tkm)')
ax1.set_title(f'Levelized Cost of Transport - Year {year_target}')
ax1.set_xticks(x_positions)
ax1.set_xticklabels(labels, rotation=45, ha='right')
ax1.grid(axis='y', alpha=0.3)

# Create legend
from matplotlib.patches import Patch
legend_elements = [Patch(facecolor='#666666', alpha=0.8, label='ICEV (all scenarios)')]
for gs, color in genesys_colors.items():
    legend_elements.append(Patch(facecolor=color, alpha=0.9, label=f'BEV - {gs}'))
ax1.legend(handles=legend_elements, loc='upper right', fontsize=8)

# Right plot: Cost breakdown comparison (stacked bar)
ax2 = axes[1]

# Average across all scenarios
avg_icev_fuel = np.mean([df[df['year']==year_target]['icev_fuel'].values[0] for df in levelized_costs_by_scenario.values()])
avg_icev_maint = np.mean([df[df['year']==year_target]['icev_maint'].values[0] for df in levelized_costs_by_scenario.values()])
avg_icev_capital = np.mean([df[df['year']==year_target]['icev_capital'].values[0] for df in levelized_costs_by_scenario.values()])

avg_bev_fuel = np.mean([df[df['year']==year_target]['bev_fuel'].values[0] for df in levelized_costs_by_scenario.values()])
avg_bev_maint = np.mean([df[df['year']==year_target]['bev_maint'].values[0] for df in levelized_costs_by_scenario.values()])
avg_bev_capital = np.mean([df[df['year']==year_target]['bev_capital'].values[0] for df in levelized_costs_by_scenario.values()])

x = np.array([0, 1])
width = 0.6

# Stacked bars
ax2.bar(x, [avg_icev_fuel, avg_bev_fuel], width, label='Fuel/Energy', color='#ff7f0e')
ax2.bar(x, [avg_icev_maint, avg_bev_maint], width, bottom=[avg_icev_fuel, avg_bev_fuel],
        label='Maintenance', color='#2ca02c')
ax2.bar(x, [avg_icev_capital, avg_bev_capital], width,
        bottom=[avg_icev_fuel+avg_icev_maint, avg_bev_fuel+avg_bev_maint],
        label='Capital', color='#1f77b4')

ax2.set_ylabel('Levelized Cost (EUR/tkm)')
ax2.set_title(f'Cost Component Breakdown - Year {year_target}\\n(Average across all scenarios)')
ax2.set_xticks(x)
ax2.set_xticklabels(['ICEV', 'BEV'])
ax2.legend()
ax2.grid(axis='y', alpha=0.3)

# Add value labels on bars
for i, (f, m, c) in enumerate([(avg_icev_fuel, avg_icev_maint, avg_icev_capital),
                                (avg_bev_fuel, avg_bev_maint, avg_bev_capital)]):
    total = f + m + c
    ax2.text(i, total + 0.002, f'{total:.3f}', ha='center', fontsize=10, fontweight='bold')

plt.tight_layout()
plt.savefig('figures/levelized_cost_comparison_2040.pdf', bbox_inches='tight', dpi=300)
plt.show()

# Print summary
print(f"Average ICEV LCOT ({year_target}): {avg_icev_fuel + avg_icev_maint + avg_icev_capital:.4f} EUR/tkm")
print(f"Average BEV LCOT ({year_target}): {avg_bev_fuel + avg_bev_maint + avg_bev_capital:.4f} EUR/tkm")
print(f"BEV advantage: {(avg_icev_fuel + avg_icev_maint + avg_icev_capital) - (avg_bev_fuel + avg_bev_maint + avg_bev_capital):.4f} EUR/tkm")
'''

new_cell_136 = {
    'cell_type': 'code',
    'execution_count': None,
    'metadata': {},
    'outputs': [],
    'source': new_cell_136_source.strip().split('\n')
}

# Convert source to list of lines with newlines
new_cell_136['source'] = [line + '\n' for line in new_cell_136_source.strip().split('\n')]
new_cell_136['source'][-1] = new_cell_136['source'][-1].rstrip('\n')  # Last line no newline

nb['cells'][136] = new_cell_136

with open('uncertainty_analysis_results.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)

print('Fixed cell 136 with better colors')
