"""
SIMPLEST REPLACEMENT: Just change Y-axis from percentage to TKM
Keep everything else the same as your current plot
"""

import matplotlib.pyplot as plt
import numpy as np

# Calculate
# modal_split_data, bin_labels = analyze_modal_split_by_distance(case_name, selected_years=[2028, 2036, 2044])

# Plot - RAIL TKM VALUES (same structure as your current plot)
fig, ax = plt.subplots(figsize=(14, 8))

x = np.arange(len(bin_labels))
width = 0.2
years = [2028, 2036, 2044]
colors = ['#3498DB', '#2ECC71', '#F39C12']

for i, year in enumerate(years):
    # Get rail TKM for each bin (in billions)
    rail_tkm_values = [modal_split_data[year][label]['rail'] / 1e9 for label in bin_labels]

    # Plot bars
    bars = ax.bar(x + i*width, rail_tkm_values, width, label=f'{year}',
                  alpha=0.85, color=colors[i], edgecolor='black', linewidth=1.2)

    # Add rail percentage labels on top of bars
    for j, (bar, label) in enumerate(zip(bars, bin_labels)):
        height = bar.get_height()
        if height > 0.01:  # Only label if significant
            rail_pct = modal_split_data[year][label]['rail_pct']
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                   f'{rail_pct:.0f}%',
                   ha='center', va='bottom', fontsize=9,
                   rotation=0, color=colors[i], fontweight='bold')

ax.set_xlabel('Route Length Category', fontsize=14, fontweight='bold')
ax.set_ylabel('Rail Freight Volume (Billion TKM)', fontsize=14, fontweight='bold')
ax.set_title('Rail Freight Volume by Route Length Category\n(Percentages show rail modal share)',
             fontsize=16, fontweight='bold', pad=20)
ax.set_xticks(x + width)
ax.set_xticklabels(bin_labels, rotation=0, fontsize=12)
ax.legend(title='Year', fontsize=12, title_fontsize=13, loc='upper left')
ax.grid(True, alpha=0.3, axis='y', linestyle='--')

plt.tight_layout()
plt.savefig('rail_freight_volume_by_distance.png', dpi=300, bbox_inches='tight')
print("✓ Rail TKM plot saved as 'rail_freight_volume_by_distance.png'")
plt.show()

print("\nNow you can see:")
print("  - If bars grow taller: Rail TKM is INCREASING")
print("  - If bars shrink: Rail TKM is DECREASING")
print("  - If bars grow but % labels decrease: Road is growing faster than rail")
