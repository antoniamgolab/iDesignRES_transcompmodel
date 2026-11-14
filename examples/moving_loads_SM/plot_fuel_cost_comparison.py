"""
Fleet Verification: WITH vs WITHOUT Fuel Costs Comparison
Generates:
1. Electrification rate (BEV share) by scenario - comparing WITH vs WITHOUT fuel costs
2. Levelized costs per scenario
3. Combined summary figure
"""

import yaml
import matplotlib.pyplot as plt
import numpy as np
import os

# Set up paths
script_dir = os.path.dirname(__file__)
results_dir = os.path.join(script_dir, 'results', 'fleet_verification_compare')
figures_dir = os.path.join(script_dir, 'figures')
os.makedirs(figures_dir, exist_ok=True)

# Load comparison summary
with open(os.path.join(results_dir, 'comparison_summary.yaml'), 'r') as f:
    comparison = yaml.safe_load(f)

# Scenario metadata
scenarios = ['scenario_000', 'scenario_001', 'scenario_002']
tech_costs = {'scenario_000': 0.7, 'scenario_001': 1.0, 'scenario_002': 1.3}
scenario_labels = {
    'scenario_000': 'Low Cost\n(0.7x)',
    'scenario_001': 'Baseline\n(1.0x)',
    'scenario_002': 'High Cost\n(1.3x)'
}
scenario_colors = {
    'scenario_000': '#2ecc71',  # Green
    'scenario_001': '#3498db',  # Blue
    'scenario_002': '#e74c3c'   # Red
}

# Years
years = [2020, 2024, 2028, 2032, 2036, 2040, 2044, 2048, 2052, 2056, 2060]

# =============================================================================
# FIGURE 1: BEV Share Over Time - WITH vs WITHOUT Fuel Costs
# =============================================================================
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Panel 1: WITHOUT Fuel Costs
ax = axes[0]
for scenario in scenarios:
    fleet_data = comparison[scenario]['no_fuel']['fleet_by_tv_year']
    bev_shares = []
    for y in years:
        icev = float(fleet_data.get('0', fleet_data.get(0, {})).get(str(y), fleet_data.get('0', fleet_data.get(0, {})).get(y, 0)))
        bev = float(fleet_data.get('1', fleet_data.get(1, {})).get(str(y), fleet_data.get('1', fleet_data.get(1, {})).get(y, 0)))
        total = icev + bev
        share = (bev / total * 100) if total > 0 else 0
        bev_shares.append(share)

    ax.plot(years, bev_shares, 'o-',
            color=scenario_colors[scenario],
            linewidth=2.5, markersize=8,
            label=f'Tech Cost = {tech_costs[scenario]}x')

ax.set_xlabel('Year', fontsize=12)
ax.set_ylabel('BEV Share of Fleet (%)', fontsize=12)
ax.set_title('(a) WITHOUT Fuel Costs in Objective', fontsize=13, fontweight='bold')
ax.set_xlim(2018, 2062)
ax.set_ylim(0, 100)
ax.legend(loc='upper left', fontsize=10)
ax.grid(True, alpha=0.3)
ax.axhline(50, color='gray', linestyle='--', alpha=0.5)

# Panel 2: WITH Fuel Costs
ax = axes[1]
for scenario in scenarios:
    fleet_data = comparison[scenario]['with_fuel']['fleet_by_tv_year']
    bev_shares = []
    for y in years:
        icev = float(fleet_data.get('0', fleet_data.get(0, {})).get(str(y), fleet_data.get('0', fleet_data.get(0, {})).get(y, 0)))
        bev = float(fleet_data.get('1', fleet_data.get(1, {})).get(str(y), fleet_data.get('1', fleet_data.get(1, {})).get(y, 0)))
        total = icev + bev
        share = (bev / total * 100) if total > 0 else 0
        bev_shares.append(share)

    ax.plot(years, bev_shares, 'o-',
            color=scenario_colors[scenario],
            linewidth=2.5, markersize=8,
            label=f'Tech Cost = {tech_costs[scenario]}x')

ax.set_xlabel('Year', fontsize=12)
ax.set_ylabel('BEV Share of Fleet (%)', fontsize=12)
ax.set_title('(b) WITH Fuel Costs in Objective', fontsize=13, fontweight='bold')
ax.set_xlim(2018, 2062)
ax.set_ylim(0, 100)
ax.legend(loc='upper left', fontsize=10)
ax.grid(True, alpha=0.3)
ax.axhline(50, color='gray', linestyle='--', alpha=0.5)

plt.suptitle('Impact of Fuel Costs on BEV Adoption\n(Electricity cheaper than Diesel drives electrification)',
             fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(os.path.join(figures_dir, 'bev_share_fuel_cost_comparison.pdf'), bbox_inches='tight', dpi=150)
plt.savefig(os.path.join(figures_dir, 'bev_share_fuel_cost_comparison.png'), bbox_inches='tight', dpi=150)
print("Saved: bev_share_fuel_cost_comparison.pdf/png")

# =============================================================================
# FIGURE 2: Bar Chart - BEV Share in 2060 by Scenario
# =============================================================================
fig, ax = plt.subplots(figsize=(10, 6))

x = np.arange(len(scenarios))
width = 0.35

# Extract 2060 BEV shares
no_fuel_shares = []
with_fuel_shares = []

for scenario in scenarios:
    # No fuel
    fleet_data = comparison[scenario]['no_fuel']['fleet_by_tv_year']
    icev = float(fleet_data.get('0', fleet_data.get(0, {})).get('2060', fleet_data.get('0', fleet_data.get(0, {})).get(2060, 0)))
    bev = float(fleet_data.get('1', fleet_data.get(1, {})).get('2060', fleet_data.get('1', fleet_data.get(1, {})).get(2060, 0)))
    total = icev + bev
    no_fuel_shares.append((bev / total * 100) if total > 0 else 0)

    # With fuel
    fleet_data = comparison[scenario]['with_fuel']['fleet_by_tv_year']
    icev = float(fleet_data.get('0', fleet_data.get(0, {})).get('2060', fleet_data.get('0', fleet_data.get(0, {})).get(2060, 0)))
    bev = float(fleet_data.get('1', fleet_data.get(1, {})).get('2060', fleet_data.get('1', fleet_data.get(1, {})).get(2060, 0)))
    total = icev + bev
    with_fuel_shares.append((bev / total * 100) if total > 0 else 0)

bars1 = ax.bar(x - width/2, no_fuel_shares, width, label='WITHOUT Fuel Costs', color='#bdc3c7', edgecolor='black')
bars2 = ax.bar(x + width/2, with_fuel_shares, width, label='WITH Fuel Costs', color='#27ae60', edgecolor='black')

# Add value labels
for bar, val in zip(bars1, no_fuel_shares):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
           f'{val:.0f}%', ha='center', fontsize=11, fontweight='bold')
for bar, val in zip(bars2, with_fuel_shares):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
           f'{val:.0f}%', ha='center', fontsize=11, fontweight='bold', color='darkgreen')

ax.set_xticks(x)
ax.set_xticklabels([f'Tech Cost = {tech_costs[s]}x' for s in scenarios], fontsize=11)
ax.set_ylabel('BEV Share in 2060 (%)', fontsize=12)
ax.set_title('BEV Adoption in 2060: Effect of Including Fuel Costs', fontsize=14, fontweight='bold')
ax.legend(loc='upper right', fontsize=11)
ax.set_ylim(0, 110)
ax.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig(os.path.join(figures_dir, 'bev_share_2060_comparison.pdf'), bbox_inches='tight', dpi=150)
plt.savefig(os.path.join(figures_dir, 'bev_share_2060_comparison.png'), bbox_inches='tight', dpi=150)
print("Saved: bev_share_2060_comparison.pdf/png")

# =============================================================================
# FIGURE 3: Objective Value (Total System Cost) Comparison
# =============================================================================
fig, ax = plt.subplots(figsize=(10, 6))

x = np.arange(len(scenarios))
width = 0.35

no_fuel_obj = []
with_fuel_obj = []

for scenario in scenarios:
    no_fuel_obj.append(float(comparison[scenario]['no_fuel']['objective_value']) / 1e9)
    with_fuel_obj.append(float(comparison[scenario]['with_fuel']['objective_value']) / 1e9)

bars1 = ax.bar(x - width/2, no_fuel_obj, width, label='WITHOUT Fuel Costs', color='#bdc3c7', edgecolor='black')
bars2 = ax.bar(x + width/2, with_fuel_obj, width, label='WITH Fuel Costs', color='#3498db', edgecolor='black')

# Add value labels
for bar, val in zip(bars1, no_fuel_obj):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,
           f'{val:.0f}B', ha='center', fontsize=10, fontweight='bold')
for bar, val in zip(bars2, with_fuel_obj):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,
           f'{val:.0f}B', ha='center', fontsize=10, fontweight='bold', color='darkblue')

ax.set_xticks(x)
ax.set_xticklabels([f'Tech Cost = {tech_costs[s]}x' for s in scenarios], fontsize=11)
ax.set_ylabel('Total System Cost (Billion EUR)', fontsize=12)
ax.set_title('Total System Cost by Scenario', fontsize=14, fontweight='bold')
ax.legend(loc='upper left', fontsize=11)
ax.set_ylim(0, max(with_fuel_obj) * 1.15)
ax.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig(os.path.join(figures_dir, 'total_system_cost_comparison.pdf'), bbox_inches='tight', dpi=150)
plt.savefig(os.path.join(figures_dir, 'total_system_cost_comparison.png'), bbox_inches='tight', dpi=150)
print("Saved: total_system_cost_comparison.pdf/png")

# =============================================================================
# FIGURE 4: Combined 4-Panel Summary
# =============================================================================
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Panel (a): BEV Share WITHOUT Fuel Costs
ax = axes[0, 0]
for scenario in scenarios:
    fleet_data = comparison[scenario]['no_fuel']['fleet_by_tv_year']
    bev_shares = []
    for y in years:
        icev = float(fleet_data.get('0', fleet_data.get(0, {})).get(str(y), fleet_data.get('0', fleet_data.get(0, {})).get(y, 0)))
        bev = float(fleet_data.get('1', fleet_data.get(1, {})).get(str(y), fleet_data.get('1', fleet_data.get(1, {})).get(y, 0)))
        total = icev + bev
        share = (bev / total * 100) if total > 0 else 0
        bev_shares.append(share)
    ax.plot(years, bev_shares, 'o-', color=scenario_colors[scenario], linewidth=2.5, markersize=7,
            label=f'{tech_costs[scenario]}x')

ax.set_xlabel('Year')
ax.set_ylabel('BEV Share (%)')
ax.set_title('(a) BEV Share - WITHOUT Fuel Costs', fontweight='bold')
ax.legend(title='Tech Cost', loc='upper left')
ax.grid(True, alpha=0.3)
ax.set_xlim(2018, 2062)
ax.set_ylim(0, 100)

# Panel (b): BEV Share WITH Fuel Costs
ax = axes[0, 1]
for scenario in scenarios:
    fleet_data = comparison[scenario]['with_fuel']['fleet_by_tv_year']
    bev_shares = []
    for y in years:
        icev = float(fleet_data.get('0', fleet_data.get(0, {})).get(str(y), fleet_data.get('0', fleet_data.get(0, {})).get(y, 0)))
        bev = float(fleet_data.get('1', fleet_data.get(1, {})).get(str(y), fleet_data.get('1', fleet_data.get(1, {})).get(y, 0)))
        total = icev + bev
        share = (bev / total * 100) if total > 0 else 0
        bev_shares.append(share)
    ax.plot(years, bev_shares, 'o-', color=scenario_colors[scenario], linewidth=2.5, markersize=7,
            label=f'{tech_costs[scenario]}x')

ax.set_xlabel('Year')
ax.set_ylabel('BEV Share (%)')
ax.set_title('(b) BEV Share - WITH Fuel Costs', fontweight='bold')
ax.legend(title='Tech Cost', loc='upper left')
ax.grid(True, alpha=0.3)
ax.set_xlim(2018, 2062)
ax.set_ylim(0, 100)

# Panel (c): BEV Share in 2060 Comparison
ax = axes[1, 0]
x = np.arange(len(scenarios))
width = 0.35

bars1 = ax.bar(x - width/2, no_fuel_shares, width, label='Without Fuel', color='#bdc3c7', edgecolor='black')
bars2 = ax.bar(x + width/2, with_fuel_shares, width, label='With Fuel', color='#27ae60', edgecolor='black')

for bar, val in zip(bars1, no_fuel_shares):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2, f'{val:.0f}%', ha='center', fontsize=10, fontweight='bold')
for bar, val in zip(bars2, with_fuel_shares):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2, f'{val:.0f}%', ha='center', fontsize=10, fontweight='bold', color='darkgreen')

ax.set_xticks(x)
ax.set_xticklabels([f'{tech_costs[s]}x' for s in scenarios])
ax.set_xlabel('Tech Cost Multiplier')
ax.set_ylabel('BEV Share in 2060 (%)')
ax.set_title('(c) BEV Adoption in 2060', fontweight='bold')
ax.legend(loc='upper right')
ax.set_ylim(0, 110)
ax.grid(True, alpha=0.3, axis='y')

# Panel (d): Total System Cost
ax = axes[1, 1]
bars1 = ax.bar(x - width/2, no_fuel_obj, width, label='Without Fuel', color='#bdc3c7', edgecolor='black')
bars2 = ax.bar(x + width/2, with_fuel_obj, width, label='With Fuel', color='#3498db', edgecolor='black')

for bar, val in zip(bars1, no_fuel_obj):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 3, f'{val:.0f}B', ha='center', fontsize=9, fontweight='bold')
for bar, val in zip(bars2, with_fuel_obj):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 3, f'{val:.0f}B', ha='center', fontsize=9, fontweight='bold', color='darkblue')

ax.set_xticks(x)
ax.set_xticklabels([f'{tech_costs[s]}x' for s in scenarios])
ax.set_xlabel('Tech Cost Multiplier')
ax.set_ylabel('Total System Cost (Billion EUR)')
ax.set_title('(d) Total System Cost', fontweight='bold')
ax.legend(loc='upper left')
ax.set_ylim(0, max(with_fuel_obj) * 1.15)
ax.grid(True, alpha=0.3, axis='y')

plt.suptitle('Fleet Electrification: Impact of Including Fuel Costs in Optimization\n' +
             '(BEV adoption driven by lower electricity costs vs diesel)',
             fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(os.path.join(figures_dir, 'fuel_cost_impact_summary.pdf'), bbox_inches='tight', dpi=150)
plt.savefig(os.path.join(figures_dir, 'fuel_cost_impact_summary.png'), bbox_inches='tight', dpi=150)
print("Saved: fuel_cost_impact_summary.pdf/png")

print("\n" + "=" * 60)
print("All figures generated successfully!")
print("=" * 60)
print(f"\nFigures saved to: {figures_dir}")
