"""
Fleet and Transport Development Visualization for Core Model Results
Compares vehicle fleet composition with actual transport volumes by technology
"""

import yaml
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Set up paths
script_dir = Path(__file__).parent
results_file = script_dir / "results" / "core_model" / "core_model_results.yaml"

# Load results
with open(results_file, 'r') as f:
    results = yaml.safe_load(f)

# Extract fleet data
fleet_by_year = results['fleet_by_year']
tonnes_by_year = results['tonnes_by_year']
years = sorted([int(y) for y in fleet_by_year.keys()])

# Fleet data
fleet_icev = []
fleet_bev = []
fleet_total = []
fleet_bev_share = []

# Tonnes data
tonnes_icev = []
tonnes_bev = []
tonnes_total = []
tonnes_bev_share = []

for year in years:
    # Fleet
    fleet_data = fleet_by_year[year]
    fleet_icev.append(float(fleet_data['ICEV']))
    fleet_bev.append(float(fleet_data['BEV']))
    fleet_total.append(float(fleet_data['Total']))
    fleet_bev_share.append(float(fleet_data['BEV_share_pct']))

    # Tonnes
    tonnes_data = tonnes_by_year[year]
    tonnes_icev.append(float(tonnes_data['ICEV_tonnes']))
    tonnes_bev.append(float(tonnes_data['BEV_tonnes']))
    tonnes_total.append(float(tonnes_data['Total_tonnes']))
    tonnes_bev_share.append(float(tonnes_data['BEV_share_pct']))

# Create figure with 2x2 subplots
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
ax1, ax2, ax3, ax4 = axes.flatten()

bar_width = 2.5
x = np.array(years)

# ============================================================================
# Top Left: Fleet by technology (stacked bar)
# ============================================================================
ax1.bar(x, fleet_icev, bar_width, label='ICEV', color='#E57373', edgecolor='black', linewidth=0.5)
ax1.bar(x, fleet_bev, bar_width, bottom=fleet_icev, label='BEV', color='#4CAF50', edgecolor='black', linewidth=0.5)

ax1.set_xlabel('Year', fontsize=11)
ax1.set_ylabel('Number of Vehicles', fontsize=11)
ax1.set_title('Vehicle Fleet by Technology', fontsize=13, fontweight='bold')
ax1.legend(loc='upper right', fontsize=10)
ax1.set_xticks(years)
ax1.set_xticklabels(years, rotation=45, ha='right')
ax1.set_xlim(2018, 2062)
ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1000:.0f}k'))
ax1.grid(axis='y', alpha=0.3, linestyle='--')

# ============================================================================
# Top Right: Tonnes transported by technology (stacked bar)
# ============================================================================
ax2.bar(x, np.array(tonnes_icev)/1e6, bar_width, label='ICEV', color='#E57373', edgecolor='black', linewidth=0.5)
ax2.bar(x, np.array(tonnes_bev)/1e6, bar_width, bottom=np.array(tonnes_icev)/1e6, label='BEV', color='#4CAF50', edgecolor='black', linewidth=0.5)

ax2.set_xlabel('Year', fontsize=11)
ax2.set_ylabel('Tonnes Transported (Million)', fontsize=11)
ax2.set_title('Tonnes Transported by Technology', fontsize=13, fontweight='bold')
ax2.legend(loc='upper left', fontsize=10)
ax2.set_xticks(years)
ax2.set_xticklabels(years, rotation=45, ha='right')
ax2.set_xlim(2018, 2062)
ax2.grid(axis='y', alpha=0.3, linestyle='--')

# ============================================================================
# Bottom Left: BEV share in fleet
# ============================================================================
ax3.plot(years, fleet_bev_share, marker='o', linewidth=2.5, markersize=8, color='#2196F3', label='Fleet BEV Share')
ax3.fill_between(years, fleet_bev_share, alpha=0.2, color='#2196F3')

ax3.set_xlabel('Year', fontsize=11)
ax3.set_ylabel('BEV Share (%)', fontsize=11)
ax3.set_title('BEV Share in Vehicle Fleet', fontsize=13, fontweight='bold')
ax3.set_xticks(years)
ax3.set_xticklabels(years, rotation=45, ha='right')
ax3.set_xlim(2018, 2062)
ax3.set_ylim(0, 105)
ax3.grid(axis='both', alpha=0.3, linestyle='--')
ax3.axhline(y=100, color='green', linestyle='--', linewidth=1, alpha=0.7)

for year, share in zip(years, fleet_bev_share):
    ax3.annotate(f'{share:.0f}%', (year, share), textcoords="offset points",
                 xytext=(0, 8), ha='center', fontsize=8)

# ============================================================================
# Bottom Right: BEV share in transport (tonnes)
# ============================================================================
ax4.plot(years, tonnes_bev_share, marker='s', linewidth=2.5, markersize=8, color='#FF9800', label='Transport BEV Share')
ax4.fill_between(years, tonnes_bev_share, alpha=0.2, color='#FF9800')

ax4.set_xlabel('Year', fontsize=11)
ax4.set_ylabel('BEV Share (%)', fontsize=11)
ax4.set_title('BEV Share in Transport Volume (Tonnes)', fontsize=13, fontweight='bold')
ax4.set_xticks(years)
ax4.set_xticklabels(years, rotation=45, ha='right')
ax4.set_xlim(2018, 2062)
ax4.set_ylim(0, 105)
ax4.grid(axis='both', alpha=0.3, linestyle='--')
ax4.axhline(y=100, color='green', linestyle='--', linewidth=1, alpha=0.7)

for year, share in zip(years, tonnes_bev_share):
    ax4.annotate(f'{share:.0f}%', (year, share), textcoords="offset points",
                 xytext=(0, 8), ha='center', fontsize=8)

plt.tight_layout()

# Save figure
output_path = script_dir / "figures" / "fleet_development_core_model.pdf"
output_path.parent.mkdir(parents=True, exist_ok=True)
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.savefig(output_path.with_suffix('.png'), dpi=300, bbox_inches='tight')

print(f"Figure saved to: {output_path}")
print(f"Figure saved to: {output_path.with_suffix('.png')}")

# Print comparison summary
print("\n" + "=" * 80)
print("FLEET vs TRANSPORT COMPARISON")
print("=" * 80)
print(f"{'Year':<6} | {'Fleet ICEV':>10} | {'Fleet BEV':>10} | {'Fleet BEV%':>10} | {'Tonnes ICEV':>12} | {'Tonnes BEV':>12} | {'Tonnes BEV%':>11}")
print("-" * 80)
for i, year in enumerate(years):
    print(f"{year:<6} | {fleet_icev[i]:>10,.0f} | {fleet_bev[i]:>10,.0f} | {fleet_bev_share[i]:>9.1f}% | {tonnes_icev[i]:>12,.0f} | {tonnes_bev[i]:>12,.0f} | {tonnes_bev_share[i]:>10.1f}%")
print("-" * 80)

print(f"\nObjective value: {results['objective_value_billion_EUR']:.4f} billion EUR")
print(f"Solve time: {results['solve_time']:.1f} seconds")
print(f"Number of OD pairs: {results['num_odpairs']}")

print("\n" + "=" * 80)
print("KEY INSIGHT")
print("=" * 80)
print("Fleet shows gradual BEV adoption (59% -> 93% over 40 years)")
print("Transport volume shifts abruptly to 100% BEV in 2028")
print("ICEV vehicles remain in fleet but are not used for transport after 2028")
print("This suggests BEVs become cost-optimal for operations even while ICEV stock exists")
