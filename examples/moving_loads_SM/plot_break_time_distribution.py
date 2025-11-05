"""
Create focused visualization of mandatory break timing distribution.
"""

import yaml
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

print("="*80)
print("BREAK TIMING DISTRIBUTION VISUALIZATION")
print("="*80)

# Load data from corrected case
case_dir = Path("input_data/case_20251029_105650")
print(f"\nLoading data from: {case_dir}")

with open(case_dir / "MandatoryBreaks.yaml") as f:
    breaks = yaml.safe_load(f)

df_breaks = pd.DataFrame(breaks)
print(f"Loaded {len(df_breaks)} breaks")

# Get break numbers
break_numbers = sorted(df_breaks['break_number'].unique())
print(f"Break numbers: {break_numbers}")

# Create figure with multiple visualizations
fig = plt.figure(figsize=(18, 10))

# Define colors for each break number
colors = ['#4472C4', '#ED7D31', '#A5A5A5', '#FFC000', '#5B9BD5',
          '#70AD47', '#9E480E', '#997300', '#43682B']

# =============================================================================
# Plot 1: Overall distribution with expected times marked
# =============================================================================
ax1 = plt.subplot(2, 3, 1)

all_times = df_breaks['cumulative_driving_time'].values
ax1.hist(all_times, bins=50, edgecolor='black', alpha=0.7, color='steelblue')

# Mark expected break times
for bn in break_numbers:
    expected = bn * 4.5
    ax1.axvline(x=expected, color='red', linestyle='--', linewidth=2, alpha=0.6)

ax1.set_xlabel('Cumulative Driving Time (hours)', fontsize=12, fontweight='bold')
ax1.set_ylabel('Count', fontsize=12, fontweight='bold')
ax1.set_title('Overall Break Time Distribution\n(All breaks combined)',
              fontsize=13, fontweight='bold')
ax1.grid(True, alpha=0.3, axis='y')

# =============================================================================
# Plot 2: Distribution by break number (overlaid histograms)
# =============================================================================
ax2 = plt.subplot(2, 3, 2)

for i, bn in enumerate(break_numbers):
    df_bn = df_breaks[df_breaks['break_number'] == bn]
    ax2.hist(df_bn['cumulative_driving_time'], bins=30, alpha=0.6,
             label=f'Break #{bn}', color=colors[i % len(colors)],
             edgecolor='black', linewidth=0.5)

ax2.set_xlabel('Cumulative Driving Time (hours)', fontsize=12, fontweight='bold')
ax2.set_ylabel('Count', fontsize=12, fontweight='bold')
ax2.set_title('Break Time Distribution by Break Number\n(Overlaid)',
              fontsize=13, fontweight='bold')
ax2.legend(fontsize=9, loc='upper right')
ax2.grid(True, alpha=0.3, axis='y')

# =============================================================================
# Plot 3: Box plot by break number
# =============================================================================
ax3 = plt.subplot(2, 3, 3)

data_by_break = [df_breaks[df_breaks['break_number'] == bn]['cumulative_driving_time'].values
                 for bn in break_numbers]

bp = ax3.boxplot(data_by_break, positions=break_numbers, widths=0.6,
                 patch_artist=True, showmeans=True, meanline=True,
                 medianprops=dict(color='red', linewidth=2),
                 meanprops=dict(color='blue', linewidth=2, linestyle='--'))

# Color the boxes
for patch, color in zip(bp['boxes'], colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)

# Add expected times as red stars
for bn in break_numbers:
    expected = bn * 4.5
    ax3.plot(bn, expected, 'r*', markersize=15, zorder=10)

ax3.set_xlabel('Break Number', fontsize=12, fontweight='bold')
ax3.set_ylabel('Cumulative Driving Time (hours)', fontsize=12, fontweight='bold')
ax3.set_title('Break Timing Distribution\n(Red stars = expected times)',
              fontsize=13, fontweight='bold')
ax3.set_xticks(break_numbers)
ax3.grid(True, alpha=0.3, axis='y')

# =============================================================================
# Plot 4: Violin plot by break number
# =============================================================================
ax4 = plt.subplot(2, 3, 4)

parts = ax4.violinplot(data_by_break, positions=break_numbers, widths=0.7,
                       showmeans=True, showmedians=True)

# Color the violins
for i, pc in enumerate(parts['bodies']):
    pc.set_facecolor(colors[i % len(colors)])
    pc.set_alpha(0.7)

# Add expected times
for bn in break_numbers:
    expected = bn * 4.5
    ax4.plot(bn, expected, 'r*', markersize=15, zorder=10)

ax4.set_xlabel('Break Number', fontsize=12, fontweight='bold')
ax4.set_ylabel('Cumulative Driving Time (hours)', fontsize=12, fontweight='bold')
ax4.set_title('Break Timing Density Distribution\n(Violin plot)',
              fontsize=13, fontweight='bold')
ax4.set_xticks(break_numbers)
ax4.grid(True, alpha=0.3, axis='y')

# =============================================================================
# Plot 5: Deviation from expected time
# =============================================================================
ax5 = plt.subplot(2, 3, 5)

deviations = []
for bn in break_numbers:
    df_bn = df_breaks[df_breaks['break_number'] == bn]
    expected = bn * 4.5
    deviation = df_bn['cumulative_driving_time'] - expected
    deviations.append(deviation.values)

bp_dev = ax5.boxplot(deviations, positions=break_numbers, widths=0.6,
                     patch_artist=True, showmeans=True)

# Color the boxes
for patch, color in zip(bp_dev['boxes'], colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)

ax5.axhline(y=0, color='red', linestyle='--', linewidth=2, alpha=0.6)
ax5.set_xlabel('Break Number', fontsize=12, fontweight='bold')
ax5.set_ylabel('Deviation from Expected (hours)', fontsize=12, fontweight='bold')
ax5.set_title('Deviation from Expected Break Time\n(0 = perfect timing)',
              fontsize=13, fontweight='bold')
ax5.set_xticks(break_numbers)
ax5.grid(True, alpha=0.3, axis='y')

# =============================================================================
# Plot 6: Statistics table
# =============================================================================
ax6 = plt.subplot(2, 3, 6)
ax6.axis('off')

# Create statistics table
stats_data = []
for bn in break_numbers:
    df_bn = df_breaks[df_breaks['break_number'] == bn]
    expected = bn * 4.5

    stats_data.append([
        f'Break #{bn}',
        f'{len(df_bn)}',
        f'{df_bn["cumulative_driving_time"].mean():.2f}h',
        f'{df_bn["cumulative_driving_time"].median():.2f}h',
        f'{df_bn["cumulative_driving_time"].std():.2f}h',
        f'{expected:.1f}h',
        f'{(df_bn["cumulative_driving_time"].mean() - expected):.2f}h'
    ])

# Create table
table = ax6.table(cellText=stats_data,
                  colLabels=['Break', 'Count', 'Mean', 'Median', 'Std', 'Expected', 'Δ Mean'],
                  cellLoc='center',
                  loc='center',
                  bbox=[0, 0.2, 1, 0.7])

table.auto_set_font_size(False)
table.set_fontsize(9)
table.scale(1, 2)

# Color header row
for i in range(7):
    table[(0, i)].set_facecolor('#4472C4')
    table[(0, i)].set_text_props(weight='bold', color='white')

# Alternate row colors
for i in range(1, len(stats_data) + 1):
    color = '#E7E6E6' if i % 2 == 0 else 'white'
    for j in range(7):
        table[(i, j)].set_facecolor(color)

ax6.set_title('Break Timing Statistics\n(Δ = deviation from expected)',
              fontsize=13, fontweight='bold', pad=20)

plt.tight_layout()

# Save figure
output_file = 'figures/break_timing_distribution_complete.png'
plt.savefig(output_file, dpi=300, bbox_inches='tight')
print(f"\nFigure saved: {output_file}")

# =============================================================================
# Additional focused plot for first 3 breaks
# =============================================================================
fig2, axes = plt.subplots(1, 3, figsize=(18, 6))

for i, bn in enumerate(break_numbers[:3]):
    df_bn = df_breaks[df_breaks['break_number'] == bn]
    expected = bn * 4.5

    ax = axes[i]

    # Histogram
    ax.hist(df_bn['cumulative_driving_time'], bins=30,
            edgecolor='black', alpha=0.7, color=colors[i])

    # Expected time line
    ax.axvline(x=expected, color='red', linestyle='--', linewidth=3,
               label=f'Expected: {expected}h', alpha=0.8)

    # Mean and median lines
    mean_time = df_bn['cumulative_driving_time'].mean()
    median_time = df_bn['cumulative_driving_time'].median()

    ax.axvline(x=mean_time, color='blue', linestyle='-', linewidth=2,
               label=f'Mean: {mean_time:.2f}h', alpha=0.6)
    ax.axvline(x=median_time, color='green', linestyle=':', linewidth=2,
               label=f'Median: {median_time:.2f}h', alpha=0.6)

    ax.set_xlabel('Cumulative Driving Time (hours)', fontsize=11, fontweight='bold')
    ax.set_ylabel('Count', fontsize=11, fontweight='bold')
    ax.set_title(f'Break #{bn} Distribution (n={len(df_bn)})\nStd={df_bn["cumulative_driving_time"].std():.3f}h',
                 fontsize=12, fontweight='bold')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3, axis='y')

plt.tight_layout()

output_file2 = 'figures/break_timing_first_three_detailed.png'
plt.savefig(output_file2, dpi=300, bbox_inches='tight')
print(f"Figure saved: {output_file2}")

print("\n" + "="*80)
print("SUMMARY STATISTICS")
print("="*80)

# Overall summary
breaks_at_origin = (df_breaks['cumulative_driving_time'] == 0).sum()
print(f"\nTotal breaks: {len(df_breaks)}")
print(f"Breaks at origin (0h): {breaks_at_origin} ({100*breaks_at_origin/len(df_breaks):.1f}%)")

print(f"\nOverall timing:")
print(f"  Mean: {df_breaks['cumulative_driving_time'].mean():.2f}h")
print(f"  Median: {df_breaks['cumulative_driving_time'].median():.2f}h")
print(f"  Std: {df_breaks['cumulative_driving_time'].std():.2f}h")
print(f"  Min: {df_breaks['cumulative_driving_time'].min():.2f}h")
print(f"  Max: {df_breaks['cumulative_driving_time'].max():.2f}h")

print("\n" + "="*80)
print("VALIDATION: EU Regulation Compliance")
print("="*80)

# Check if break #1 is close to 4.5h
break1 = df_breaks[df_breaks['break_number'] == 1]['cumulative_driving_time']
compliance = ((break1 >= 1.8) & (break1 <= 5.25)).sum() / len(break1) * 100

print(f"\nBreak #1 compliance (1.8h - 5.25h window):")
print(f"  {compliance:.1f}% of breaks within acceptable range")
print(f"  Mean deviation from 4.5h: {abs(break1.mean() - 4.5):.3f}h")

if compliance > 95:
    print("  Status: EXCELLENT - Regulation properly enforced!")
elif compliance > 90:
    print("  Status: GOOD - Minor deviations acceptable")
else:
    print("  Status: NEEDS REVIEW - Check break placement logic")

print("\nDone!")
