"""
Fleet Verification Visualization
Generates plots for:
1. Technology mix (fleet composition) over time for all 3 scenarios
2. Purchase cost development of ICEV vs BEV across scenarios
"""

import yaml
import matplotlib.pyplot as plt
import numpy as np
import os

# Load the fleet verification summary
results_dir = os.path.join(os.path.dirname(__file__), 'results', 'fleet_verification')
summary_path = os.path.join(results_dir, 'fleet_verification_summary.yaml')

with open(summary_path, 'r') as f:
    results = yaml.safe_load(f)

# Scenario metadata
scenarios = {
    'scenario_000': {'tech_cost': 0.7, 'label': 'Low Cost (0.7x)', 'color': '#2ecc71'},
    'scenario_001': {'tech_cost': 1.0, 'label': 'Baseline (1.0x)', 'color': '#3498db'},
    'scenario_002': {'tech_cost': 1.3, 'label': 'High Cost (1.3x)', 'color': '#e74c3c'}
}

# Years to plot
years = [2020, 2024, 2028, 2032, 2036, 2040, 2044, 2048, 2052, 2056, 2060]

# =============================================================================
# FIGURE 1: Technology Mix (Fleet Composition)
# =============================================================================
fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=True)

for idx, (scenario_id, meta) in enumerate(scenarios.items()):
    ax = axes[idx]

    fleet_data = results[scenario_id]['fleet_by_tv_year']

    icev_fleet = [fleet_data[0].get(y, 0) for y in years]
    bev_fleet = [fleet_data[1].get(y, 0) for y in years]

    # Stacked area chart
    ax.stackplot(years, [icev_fleet, bev_fleet],
                 labels=['ICEV', 'BEV'],
                 colors=['#95a5a6', '#27ae60'],
                 alpha=0.8)

    ax.set_xlabel('Year', fontsize=11)
    if idx == 0:
        ax.set_ylabel('Fleet Size (vehicles)', fontsize=11)
    ax.set_title(f'Tech Cost = {meta["tech_cost"]}x', fontsize=12, fontweight='bold')
    ax.set_xlim(2020, 2060)
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3)

    # Add BEV share annotation at 2056
    total_2056 = icev_fleet[-2] + bev_fleet[-2]
    if total_2056 > 0:
        bev_share = bev_fleet[-2] / total_2056 * 100
        ax.annotate(f'BEV: {bev_share:.0f}%',
                   xy=(2056, bev_fleet[-2]/2 + icev_fleet[-2]),
                   fontsize=10, ha='center', fontweight='bold')

plt.suptitle('Fleet Technology Mix by Tech Cost Scenario\n(Fleet + Fuel Demand Constraints)',
             fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(os.path.join(results_dir, 'fleet_technology_mix.pdf'), bbox_inches='tight', dpi=150)
plt.savefig(os.path.join(results_dir, 'fleet_technology_mix.png'), bbox_inches='tight', dpi=150)
print("Saved: fleet_technology_mix.pdf/png")

# =============================================================================
# FIGURE 2: BEV Share Comparison Across Scenarios
# =============================================================================
fig, ax = plt.subplots(figsize=(10, 6))

for scenario_id, meta in scenarios.items():
    fleet_data = results[scenario_id]['fleet_by_tv_year']

    bev_shares = []
    for y in years:
        icev = fleet_data[0].get(y, 0)
        bev = fleet_data[1].get(y, 0)
        total = icev + bev
        share = (bev / total * 100) if total > 0 else 0
        bev_shares.append(share)

    ax.plot(years, bev_shares, 'o-',
            color=meta['color'],
            linewidth=2.5,
            markersize=8,
            label=meta['label'])

ax.set_xlabel('Year', fontsize=12)
ax.set_ylabel('BEV Share of Fleet (%)', fontsize=12)
ax.set_title('BEV Adoption Rate by Technology Cost Scenario', fontsize=14, fontweight='bold')
ax.set_xlim(2020, 2060)
ax.set_ylim(0, 75)
ax.legend(loc='upper left', fontsize=11)
ax.grid(True, alpha=0.3)

# Add annotations
ax.axhline(50, color='gray', linestyle='--', alpha=0.5, label='_nolegend_')
ax.text(2022, 52, '50% threshold', fontsize=9, color='gray')

plt.tight_layout()
plt.savefig(os.path.join(results_dir, 'bev_share_comparison.pdf'), bbox_inches='tight', dpi=150)
plt.savefig(os.path.join(results_dir, 'bev_share_comparison.png'), bbox_inches='tight', dpi=150)
print("Saved: bev_share_comparison.pdf/png")

# =============================================================================
# FIGURE 3: Purchase Cost Development (ICEV vs BEV)
# =============================================================================
# Load TechVehicle data to get purchase costs
# We need to read from one of the scenario input files
input_path = os.path.join(os.path.dirname(__file__), 'input_data', 'uncertainty_scenarios')

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Panel 1: Purchase costs by scenario
ax1 = axes[0]

# Load purchase costs from each scenario
for scenario_id, meta in scenarios.items():
    tv_path = os.path.join(input_path, scenario_id, 'TechVehicle.yaml')
    with open(tv_path, 'r') as f:
        tv_data = yaml.safe_load(f)

    # Find ICEV and BEV
    for tv in tv_data:
        if tv['name'] == 'BEV':
            bev_costs = tv['capital_cost']
            # Years align with generations starting from g_init (2008)
            # capital_cost array indexed by generation, we want years 2020-2060
            # g_init = 2008, so 2020 = index 3 (assuming 4-year steps)
            cost_years = list(range(2008, 2008 + len(bev_costs)))  # Generation years

            ax1.plot(cost_years,
                    [c/1000 for c in bev_costs],  # Convert to thousands
                    'o-', color=meta['color'], linewidth=2, markersize=6,
                    label=f'BEV - {meta["label"]}')

        elif tv['name'] == 'ICEV' and scenario_id == 'scenario_001':
            # ICEV costs same across scenarios, plot only once
            icev_costs = tv['capital_cost']
            cost_years = list(range(2008, 2008 + len(icev_costs)))
            ax1.plot(cost_years,
                    [c/1000 for c in icev_costs],
                    's--', color='#2c3e50', linewidth=2.5, markersize=7,
                    label='ICEV (all scenarios)')

ax1.set_xlabel('Year (Vehicle Generation)', fontsize=12)
ax1.set_ylabel('Purchase Cost (thousand EUR)', fontsize=12)
ax1.set_title('Vehicle Purchase Costs by Technology', fontsize=13, fontweight='bold')
ax1.set_xlim(2016, 2064)
ax1.legend(loc='upper right', fontsize=9)
ax1.grid(True, alpha=0.3)

# Panel 2: Cost difference (BEV - ICEV)
ax2 = axes[1]

for scenario_id, meta in scenarios.items():
    tv_path = os.path.join(input_path, scenario_id, 'TechVehicle.yaml')
    with open(tv_path, 'r') as f:
        tv_data = yaml.safe_load(f)

    icev_costs = None
    bev_costs = None
    for tv in tv_data:
        if tv['name'] == 'ICEV':
            icev_costs = tv['capital_cost']
        elif tv['name'] == 'BEV':
            bev_costs = tv['capital_cost']

    if icev_costs and bev_costs:
        cost_diff = [(b - i)/1000 for b, i in zip(bev_costs, icev_costs)]
        cost_years = list(range(2008, 2008 + len(cost_diff)))

        ax2.plot(cost_years[:len(cost_diff)], cost_diff,
                'o-', color=meta['color'], linewidth=2.5, markersize=7,
                label=meta['label'])

ax2.axhline(0, color='black', linewidth=1.5, linestyle='-')
ax2.fill_between([2008, 2064], [0, 0], [-50, -50], alpha=0.1, color='green', label='_nolegend_')
ax2.fill_between([2008, 2064], [0, 0], [100, 100], alpha=0.1, color='red', label='_nolegend_')

ax2.set_xlabel('Year (Vehicle Generation)', fontsize=12)
ax2.set_ylabel('Cost Premium: BEV - ICEV (thousand EUR)', fontsize=12)
ax2.set_title('BEV Cost Premium Over ICEV', fontsize=13, fontweight='bold')
ax2.set_xlim(2016, 2064)
ax2.legend(loc='upper right', fontsize=10)
ax2.grid(True, alpha=0.3)

# Add annotation
ax2.text(2060, -5, 'BEV cheaper', fontsize=9, color='green', ha='right')
ax2.text(2060, 5, 'ICEV cheaper', fontsize=9, color='red', ha='right')

plt.suptitle('Purchase Cost Analysis: Impact of Technology Cost Multiplier',
             fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(os.path.join(results_dir, 'purchase_cost_comparison.pdf'), bbox_inches='tight', dpi=150)
plt.savefig(os.path.join(results_dir, 'purchase_cost_comparison.png'), bbox_inches='tight', dpi=150)
print("Saved: purchase_cost_comparison.pdf/png")

# =============================================================================
# FIGURE 4: Combined Summary - Fleet + Costs
# =============================================================================
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Top-left: BEV share over time
ax = axes[0, 0]
for scenario_id, meta in scenarios.items():
    fleet_data = results[scenario_id]['fleet_by_tv_year']
    bev_shares = []
    for y in years:
        icev = fleet_data[0].get(y, 0)
        bev = fleet_data[1].get(y, 0)
        total = icev + bev
        share = (bev / total * 100) if total > 0 else 0
        bev_shares.append(share)
    ax.plot(years, bev_shares, 'o-', color=meta['color'], linewidth=2.5, markersize=7, label=meta['label'])
ax.set_xlabel('Year')
ax.set_ylabel('BEV Share (%)')
ax.set_title('(a) BEV Fleet Share Over Time', fontweight='bold')
ax.legend(loc='upper left')
ax.grid(True, alpha=0.3)
ax.set_xlim(2020, 2060)

# Top-right: Fleet composition at 2056
ax = axes[0, 1]
x = np.arange(3)
width = 0.35
icev_2056 = []
bev_2056 = []
labels = []
for scenario_id, meta in scenarios.items():
    fleet_data = results[scenario_id]['fleet_by_tv_year']
    icev_2056.append(fleet_data[0].get(2056, 0))
    bev_2056.append(fleet_data[1].get(2056, 0))
    labels.append(f'{meta["tech_cost"]}x')

ax.bar(x - width/2, [i/1000 for i in icev_2056], width, label='ICEV', color='#95a5a6')
ax.bar(x + width/2, [b/1000 for b in bev_2056], width, label='BEV', color='#27ae60')
ax.set_xticks(x)
ax.set_xticklabels(labels)
ax.set_xlabel('Tech Cost Multiplier')
ax.set_ylabel('Fleet Size (thousands)')
ax.set_title('(b) Fleet Composition in 2056', fontweight='bold')
ax.legend()
ax.grid(True, alpha=0.3, axis='y')

# Bottom-left: Purchase costs
ax = axes[1, 0]
for scenario_id, meta in scenarios.items():
    tv_path = os.path.join(input_path, scenario_id, 'TechVehicle.yaml')
    with open(tv_path, 'r') as f:
        tv_data = yaml.safe_load(f)
    for tv in tv_data:
        if tv['name'] == 'BEV':
            bev_costs = tv['capital_cost']
            cost_years = list(range(2008, 2008 + len(bev_costs)))
            ax.plot(cost_years, [c/1000 for c in bev_costs],
                   'o-', color=meta['color'], linewidth=2, markersize=5,
                   label=f'BEV {meta["label"]}')
        elif tv['name'] == 'ICEV' and scenario_id == 'scenario_001':
            icev_costs = tv['capital_cost']
            cost_years = list(range(2008, 2008 + len(icev_costs)))
            ax.plot(cost_years, [c/1000 for c in icev_costs],
                   's--', color='#2c3e50', linewidth=2.5, markersize=6,
                   label='ICEV')
ax.set_xlabel('Year')
ax.set_ylabel('Purchase Cost (thousand EUR)')
ax.set_title('(c) Vehicle Purchase Costs', fontweight='bold')
ax.legend(loc='upper right', fontsize=8)
ax.grid(True, alpha=0.3)
ax.set_xlim(2016, 2064)

# Bottom-right: Objective values (total system cost)
ax = axes[1, 1]
obj_values = []
colors = []
labels = []
for scenario_id, meta in scenarios.items():
    obj_values.append(float(results[scenario_id]['objective_value']) / 1e9)
    colors.append(meta['color'])
    labels.append(f'{meta["tech_cost"]}x')

bars = ax.bar(labels, obj_values, color=colors, edgecolor='black', linewidth=1.5)
ax.set_xlabel('Tech Cost Multiplier')
ax.set_ylabel('Total System Cost (billion EUR)')
ax.set_title('(d) Total System Cost', fontweight='bold')
ax.grid(True, alpha=0.3, axis='y')

# Add value labels on bars
for bar, val in zip(bars, obj_values):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
           f'{val:.1f}B', ha='center', fontsize=10, fontweight='bold')

ax.set_ylim(0, max(obj_values) * 1.1)

plt.suptitle('Fleet Verification Summary: Effect of Technology Cost on Electrification\n(Including Fuel Costs via constraint_fueling_demand)',
             fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(os.path.join(results_dir, 'fleet_verification_summary.pdf'), bbox_inches='tight', dpi=150)
plt.savefig(os.path.join(results_dir, 'fleet_verification_summary.png'), bbox_inches='tight', dpi=150)
print("Saved: fleet_verification_summary.pdf/png")

# plt.show()  # Commented out for batch run
print("\nAll figures generated successfully!")
