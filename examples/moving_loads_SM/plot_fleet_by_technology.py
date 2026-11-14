"""
Plot fleet composition by technology (ICEV vs BEV) - two visualizations:
1. Stacked bar chart showing total fleet
2. Separate BEV-only line plot to highlight the "constant at 1000" pattern
"""

import yaml
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict

# Load the h_dict from scenario_000 results (BASELINE)
h_file = 'results/uncertainty_analysis/scenario_000/scenario_000_2025-12-12_19-26-52_h_dict.yaml'
with open(h_file, 'r') as f:
    h_dict = yaml.safe_load(f)

# Aggregate by year and tech
h_by_year = defaultdict(lambda: defaultdict(float))

for key, value in h_dict.items():
    parts = key.strip('()').split(',')
    year = int(parts[0].strip())
    tech = int(parts[2].strip())  # tech_vehicle_id: 0=ICEV, 1=BEV
    h_by_year[year][tech] += float(value)

# Prepare data for plotting
years = sorted(h_by_year.keys())
icev_values = [h_by_year[year].get(0, 0) for year in years]
bev_values = [h_by_year[year].get(1, 0) for year in years]

# Create figure with two subplots
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

x = np.arange(len(years))
width = 0.6

# ============================================
# TOP PLOT: Stacked bar chart
# ============================================
bars_icev = ax1.bar(x, icev_values, width, label='ICEV', color='#d62728', alpha=0.8)
bars_bev = ax1.bar(x, bev_values, width, bottom=icev_values, label='BEV', color='#2ca02c', alpha=0.8)

ax1.set_xlabel('Year', fontsize=12)
ax1.set_ylabel('Number of Vehicles', fontsize=12)
ax1.set_title('Fleet Composition by Technology (Scenario 000 - Baseline)', fontsize=14)
ax1.set_xticks(x)
ax1.set_xticklabels(years, rotation=45)
ax1.legend(loc='upper left')

# Add value labels on bars
for i, (icev, bev) in enumerate(zip(icev_values, bev_values)):
    total = icev + bev
    bev_pct = 100 * bev / total if total > 0 else 0
    ax1.annotate(f'{bev_pct:.0f}%',
                xy=(i, total),
                ha='center', va='bottom',
                fontsize=9, fontweight='bold')

ax1.set_ylim(0, max([i + b for i, b in zip(icev_values, bev_values)]) * 1.15)

# ============================================
# BOTTOM PLOT: BEV-only bar chart to show "constant at 1000" pattern
# ============================================
# Color bars differently for years where BEV is ~1000
colors = []
for year, bev in zip(years, bev_values):
    if 999 < bev < 1001:  # Check if approximately 1000
        colors.append('#ff7f0e')  # Orange for the "constant" years
    else:
        colors.append('#2ca02c')  # Green for other years

bars = ax2.bar(x, bev_values, width, color=colors, alpha=0.8, edgecolor='black', linewidth=0.5)

# Add horizontal line at 1000 to highlight the constant value
ax2.axhline(y=1000, color='red', linestyle='--', linewidth=2, label='1000 vehicles')

ax2.set_xlabel('Year', fontsize=12)
ax2.set_ylabel('BEV Fleet Size', fontsize=12)
ax2.set_title('BEV Fleet Only - Highlighting "Constant at 1000" Pattern (2028-2040)', fontsize=14)
ax2.set_xticks(x)
ax2.set_xticklabels(years, rotation=45)
ax2.legend(loc='upper left')

# Add value labels on each bar
for i, bev in enumerate(bev_values):
    ax2.annotate(f'{bev:.0f}',
                xy=(i, bev),
                ha='center', va='bottom',
                fontsize=9, fontweight='bold')

ax2.set_ylim(0, max(bev_values) * 1.15)

plt.tight_layout()
plt.savefig('figures/fleet_by_technology_scenario_000.pdf', dpi=150, bbox_inches='tight')
plt.savefig('figures/fleet_by_technology_scenario_000.png', dpi=150, bbox_inches='tight')
print('Saved: figures/fleet_by_technology_scenario_000.pdf')
print('Saved: figures/fleet_by_technology_scenario_000.png')

# Print the exact BEV values
print("\nBEV fleet values by year:")
for year, bev in zip(years, bev_values):
    is_constant = "  <-- ~1000" if 999 < bev < 1001 else ""
    print(f"  {year}: {bev:.4f}{is_constant}")

# plt.show()  # Commented out for non-interactive execution
