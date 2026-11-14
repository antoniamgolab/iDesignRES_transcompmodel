"""
Alternative version: Side-by-side bars for rail and road
Shows absolute TKM values separately for easier comparison
"""

import matplotlib.pyplot as plt
import numpy as np

# Calculate
# modal_split_data, bin_labels = analyze_modal_split_by_distance(case_name, selected_years=[2028, 2036, 2044])

# Plot SIDE-BY-SIDE showing rail and road separately
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))

x = np.arange(len(bin_labels))
width = 0.25
years = [2028, 2036, 2044]
colors = ['#3498DB', '#2ECC71', '#F39C12']

# LEFT PLOT: Rail TKM
for i, year in enumerate(years):
    rail_tkm = [modal_split_data[year][label]['rail'] / 1e9 for label in bin_labels]

    bars = ax1.bar(x + i*width, rail_tkm, width,
                   label=f'{year}',
                   alpha=0.85, color=colors[i],
                   edgecolor='black', linewidth=1.2)

    # Add values on top
    for bar in bars:
        height = bar.get_height()
        if height > 0.01:
            ax1.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                    f'{height:.2f}B',
                    ha='center', va='bottom', fontsize=9,
                    fontweight='bold')

ax1.set_xlabel('Route Length Category', fontsize=13, fontweight='bold')
ax1.set_ylabel('Rail Freight Volume (Billion TKM)', fontsize=13, fontweight='bold')
ax1.set_title('RAIL Freight Volume by Distance Category',
              fontsize=14, fontweight='bold', color='#27AE60')
ax1.set_xticks(x + width)
ax1.set_xticklabels(bin_labels, rotation=0, fontsize=11)
ax1.legend(title='Year', fontsize=11)
ax1.grid(True, alpha=0.3, axis='y', linestyle='--')

# RIGHT PLOT: Road TKM
for i, year in enumerate(years):
    road_tkm = [modal_split_data[year][label]['road'] / 1e9 for label in bin_labels]

    bars = ax2.bar(x + i*width, road_tkm, width,
                   label=f'{year}',
                   alpha=0.85, color=colors[i],
                   edgecolor='black', linewidth=1.2)

    # Add values on top
    for bar in bars:
        height = bar.get_height()
        if height > 0.01:
            ax2.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                    f'{height:.2f}B',
                    ha='center', va='bottom', fontsize=9,
                    fontweight='bold')

ax2.set_xlabel('Route Length Category', fontsize=13, fontweight='bold')
ax2.set_ylabel('Road Freight Volume (Billion TKM)', fontsize=13, fontweight='bold')
ax2.set_title('ROAD Freight Volume by Distance Category',
              fontsize=14, fontweight='bold', color='#E74C3C')
ax2.set_xticks(x + width)
ax2.set_xticklabels(bin_labels, rotation=0, fontsize=11)
ax2.legend(title='Year', fontsize=11)
ax2.grid(True, alpha=0.3, axis='y', linestyle='--')

# Match y-axis scales for fair comparison
y_max = max(ax1.get_ylim()[1], ax2.get_ylim()[1])
ax1.set_ylim(0, y_max)
ax2.set_ylim(0, y_max)

plt.tight_layout()
plt.savefig('freight_volume_rail_vs_road.png', dpi=300, bbox_inches='tight')
print("✓ Side-by-side TKM plot saved as 'freight_volume_rail_vs_road.png'")
plt.show()

print("\nINTERPRETATION:")
print("  - LEFT (Rail): Shows if rail is growing/declining in absolute terms")
print("  - RIGHT (Road): Shows if road is growing/declining")
print("  - If rail grows but road grows faster → rail % decreases")
