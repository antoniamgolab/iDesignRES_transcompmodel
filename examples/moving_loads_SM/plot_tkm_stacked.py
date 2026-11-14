"""
Updated plotting code for modal_shift.ipynb
Shows absolute TKM values (stacked bars) instead of percentages
"""

# Add this to your modal_shift.ipynb after the analyze_modal_split_by_distance() call

import matplotlib.pyplot as plt
import numpy as np

# Calculate
# modal_split_data, bin_labels = analyze_modal_split_by_distance(case_name, selected_years=[2028, 2036, 2044])

# Plot STACKED BARS showing absolute TKM
fig, ax = plt.subplots(figsize=(14, 8))

x = np.arange(len(bin_labels))
width = 0.2
years = [2028, 2036, 2044]
colors_rail = ['#2ECC71', '#27AE60', '#229954']  # Green shades for rail
colors_road = ['#E74C3C', '#C0392B', '#A93226']  # Red shades for road

for i, year in enumerate(years):
    # Get rail and road TKM for each bin
    rail_tkm = [modal_split_data[year][label]['rail'] / 1e9 for label in bin_labels]  # Convert to billions
    road_tkm = [modal_split_data[year][label]['road'] / 1e9 for label in bin_labels]

    # Plot stacked bars
    bars_road = ax.bar(x + i*width, road_tkm, width,
                       label=f'{year} Road',
                       alpha=0.85, color=colors_road[i],
                       edgecolor='black', linewidth=1.2)

    bars_rail = ax.bar(x + i*width, rail_tkm, width,
                       bottom=road_tkm,
                       label=f'{year} Rail',
                       alpha=0.85, color=colors_rail[i],
                       edgecolor='black', linewidth=1.2)

    # Add rail percentage on top of each stacked bar
    for j, (bar_rail, label) in enumerate(zip(bars_rail, bin_labels)):
        total = rail_tkm[j] + road_tkm[j]
        if total > 0.01:  # Only label if significant
            rail_pct = modal_split_data[year][label]['rail_pct']
            height = bar_rail.get_y() + bar_rail.get_height()
            ax.text(bar_rail.get_x() + bar_rail.get_width()/2., height + 0.05,
                   f'{rail_pct:.0f}%',
                   ha='center', va='bottom', fontsize=9,
                   fontweight='bold', color=colors_rail[i])

ax.set_xlabel('Route Length Category', fontsize=14, fontweight='bold')
ax.set_ylabel('Freight Volume (Billion TKM)', fontsize=14, fontweight='bold')
ax.set_title('Freight Volume by Mode and Route Length\n(Numbers show rail modal share %)',
             fontsize=16, fontweight='bold', pad=20)
ax.set_xticks(x + width * 1)
ax.set_xticklabels(bin_labels, rotation=0, fontsize=12)
ax.legend(fontsize=10, loc='upper left', ncol=2)
ax.grid(True, alpha=0.3, axis='y', linestyle='--')

plt.tight_layout()
plt.savefig('freight_volume_by_mode_stacked.png', dpi=300, bbox_inches='tight')
print("✓ Stacked TKM plot saved as 'freight_volume_by_mode_stacked.png'")
plt.show()
