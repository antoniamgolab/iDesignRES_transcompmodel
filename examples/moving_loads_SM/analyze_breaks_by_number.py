"""
Analyze and visualize mandatory breaks distribution by break_number.
"""

import yaml
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

print("="*80)
print("MANDATORY BREAKS ANALYSIS BY BREAK_NUMBER")
print("="*80)

# Load data - use most recent case (corrected, no synthetic nodes in path)
case_dir = Path("input_data/case_20251029_154754")
print(f"\nLoading data from: {case_dir}")

with open(case_dir / "MandatoryBreaks.yaml") as f:
    breaks = yaml.safe_load(f)

with open(case_dir / "Path.yaml") as f:
    paths = yaml.safe_load(f)

df_breaks = pd.DataFrame(breaks)
df_paths = pd.DataFrame(paths)

print(f"Loaded {len(df_breaks)} breaks")
print(f"Loaded {len(df_paths)} paths")

# Merge with path data to get path lengths
df_merged = df_breaks.merge(df_paths[['id', 'length', 'origin', 'destination']],
                             left_on='path_id',
                             right_on='id',
                             how='left')

print("\n" + "="*80)
print("OVERALL STATISTICS")
print("="*80)

print(f"\nTotal breaks: {len(df_breaks)}")
print(f"Total paths: {len(df_paths)}")
print(f"Paths with breaks: {df_breaks['path_id'].nunique()}")
print(f"Average breaks per path: {len(df_breaks)/df_breaks['path_id'].nunique():.2f}")

# Break numbers present
break_numbers = sorted(df_breaks['break_number'].unique())
print(f"\nBreak numbers present: {break_numbers}")

# Breaks at origin check
breaks_at_origin = (df_breaks['cumulative_driving_time'] == 0).sum()
print(f"\nBreaks at origin (0h): {breaks_at_origin} ({100*breaks_at_origin/len(df_breaks):.1f}%)")

if breaks_at_origin < len(df_breaks) * 0.1:
    print("OK: Less than 10% of breaks at origin!")
else:
    print("WARNING: High percentage of breaks at origin")

print("\n" + "="*80)
print("STATISTICS BY BREAK_NUMBER")
print("="*80)

for bn in break_numbers:
    df_bn = df_merged[df_merged['break_number'] == bn]

    print(f"\n{'='*40}")
    print(f"BREAK NUMBER {bn}")
    print(f"{'='*40}")
    print(f"Count: {len(df_bn)}")
    print(f"Cumulative driving time (h):")
    print(f"  Mean:   {df_bn['cumulative_driving_time'].mean():.2f}h")
    print(f"  Median: {df_bn['cumulative_driving_time'].median():.2f}h")
    print(f"  Min:    {df_bn['cumulative_driving_time'].min():.2f}h")
    print(f"  Max:    {df_bn['cumulative_driving_time'].max():.2f}h")
    print(f"  Std:    {df_bn['cumulative_driving_time'].std():.2f}h")

    # Check how many are at origin for this break number
    at_origin = (df_bn['cumulative_driving_time'] == 0).sum()
    print(f"At origin (0h): {at_origin} ({100*at_origin/len(df_bn):.1f}%)")

    # Check node indices
    print(f"\nNode indices:")
    print(f"  Mean:   {df_bn['latest_node_idx'].mean():.1f}")
    print(f"  Median: {df_bn['latest_node_idx'].median():.1f}")
    print(f"  Min:    {df_bn['latest_node_idx'].min()}")
    print(f"  Max:    {df_bn['latest_node_idx'].max()}")

# VISUALIZATION
print("\n" + "="*80)
print("CREATING VISUALIZATIONS")
print("="*80)

n_break_numbers = len(break_numbers)

# Create figure with subplots
fig = plt.figure(figsize=(16, 4*n_break_numbers))

for i, bn in enumerate(break_numbers):
    df_bn = df_merged[df_merged['break_number'] == bn]

    # Row for this break_number
    row = i

    # Subplot 1: Histogram of break timing
    ax1 = plt.subplot(n_break_numbers, 3, row*3 + 1)
    ax1.hist(df_bn['cumulative_driving_time'], bins=20,
             edgecolor='black', alpha=0.7, color='steelblue')

    # Add vertical lines for expected break times
    expected_time = bn * 4.5
    ax1.axvline(x=expected_time, color='red', linestyle='--', linewidth=2,
                label=f'Expected: {expected_time}h', alpha=0.7)
    ax1.axvline(x=4.5, color='orange', linestyle=':', linewidth=1.5,
                label='4.5h limit', alpha=0.5)

    ax1.set_xlabel('Cumulative Driving Time (hours)', fontsize=10, fontweight='bold')
    ax1.set_ylabel('Count', fontsize=10, fontweight='bold')
    ax1.set_title(f'Break #{bn} Timing Distribution (n={len(df_bn)})',
                  fontsize=11, fontweight='bold')
    ax1.legend(fontsize=8)
    ax1.grid(True, alpha=0.3, axis='y')

    # Subplot 2: Scatter - break timing vs path length
    ax2 = plt.subplot(n_break_numbers, 3, row*3 + 2)
    ax2.scatter(df_bn['length'], df_bn['cumulative_driving_time'],
                s=50, alpha=0.6, color='coral', edgecolors='black')
    ax2.axhline(y=expected_time, color='red', linestyle='--', linewidth=2, alpha=0.6)
    ax2.set_xlabel('Path Length (km)', fontsize=10, fontweight='bold')
    ax2.set_ylabel('Cumulative Time to Break (h)', fontsize=10, fontweight='bold')
    ax2.set_title(f'Break #{bn} Timing vs Route Length', fontsize=11, fontweight='bold')
    ax2.grid(True, alpha=0.3)

    # Subplot 3: Histogram of node indices
    ax3 = plt.subplot(n_break_numbers, 3, row*3 + 3)
    ax3.hist(df_bn['latest_node_idx'], bins=range(0, df_bn['latest_node_idx'].max()+2),
             edgecolor='black', alpha=0.7, color='seagreen')
    ax3.set_xlabel('Node Index', fontsize=10, fontweight='bold')
    ax3.set_ylabel('Count', fontsize=10, fontweight='bold')
    ax3.set_title(f'Break #{bn} Node Index Distribution', fontsize=11, fontweight='bold')
    ax3.grid(True, alpha=0.3, axis='y')

plt.tight_layout()

# Save figure
import os
os.makedirs('figures', exist_ok=True)
output_file = 'figures/breaks_by_number_full_analysis.png'
plt.savefig(output_file, dpi=300, bbox_inches='tight')
print(f"\nFigure saved: {output_file}")

# Additional figure: Combined histogram for all break numbers
fig2, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

# Plot 1: Overlapping histograms
colors = ['steelblue', 'coral', 'seagreen', 'mediumpurple', 'gold']
for i, bn in enumerate(break_numbers):
    df_bn = df_merged[df_merged['break_number'] == bn]
    ax1.hist(df_bn['cumulative_driving_time'], bins=30,
             alpha=0.5, label=f'Break #{bn} (n={len(df_bn)})',
             color=colors[i % len(colors)], edgecolor='black')

# Add expected break times
for bn in break_numbers:
    expected = bn * 4.5
    ax1.axvline(x=expected, color='red', linestyle='--', linewidth=1.5, alpha=0.4)

ax1.set_xlabel('Cumulative Driving Time (hours)', fontsize=12, fontweight='bold')
ax1.set_ylabel('Count', fontsize=12, fontweight='bold')
ax1.set_title('All Breaks - Timing Distribution', fontsize=13, fontweight='bold')
ax1.legend(fontsize=9)
ax1.grid(True, alpha=0.3)

# Plot 2: Box plot by break_number
break_times_by_number = [df_merged[df_merged['break_number'] == bn]['cumulative_driving_time'].values
                          for bn in break_numbers]
positions = list(break_numbers)

bp = ax2.boxplot(break_times_by_number, positions=positions, widths=0.6,
                 patch_artist=True, showmeans=True)

# Color the boxes
for patch, color in zip(bp['boxes'], colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)

# Add expected times
for bn in break_numbers:
    expected = bn * 4.5
    ax2.plot(bn, expected, 'r*', markersize=15, label='Expected' if bn == break_numbers[0] else '')

ax2.set_xlabel('Break Number', fontsize=12, fontweight='bold')
ax2.set_ylabel('Cumulative Driving Time (hours)', fontsize=12, fontweight='bold')
ax2.set_title('Break Timing Distribution by Break Number', fontsize=13, fontweight='bold')
ax2.legend(fontsize=9)
ax2.grid(True, alpha=0.3, axis='y')
ax2.set_xticks(positions)

plt.tight_layout()

output_file2 = 'figures/breaks_combined_overview.png'
plt.savefig(output_file2, dpi=300, bbox_inches='tight')
print(f"Figure saved: {output_file2}")

print("\n" + "="*80)
print("SAMPLE PATHS WITH MULTIPLE BREAKS")
print("="*80)

# Find paths with multiple breaks
paths_with_multiple = df_breaks.groupby('path_id').size()
paths_with_multiple = paths_with_multiple[paths_with_multiple > 1].sort_values(ascending=False)

print(f"\nPaths with multiple breaks: {len(paths_with_multiple)}")
print(f"Maximum breaks on a single path: {paths_with_multiple.max()}")

# Show a few examples
print("\nExamples of paths with multiple breaks:")
for i, (path_id, num_breaks) in enumerate(paths_with_multiple.head(5).items()):
    path = df_paths[df_paths['id'] == path_id].iloc[0]
    path_breaks = df_merged[df_merged['path_id'] == path_id].sort_values('break_number')

    print(f"\n  Path {path_id}: {path['origin']} -> {path['destination']}")
    print(f"    Length: {path['length']:.1f} km")
    print(f"    Breaks: {num_breaks}")

    for _, brk in path_breaks.iterrows():
        print(f"      Break #{brk['break_number']}: {brk['cumulative_driving_time']:.2f}h "
              f"(node_idx={brk['latest_node_idx']}, {brk['cumulative_distance']:.1f}km)")

print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)
print(f"\nGenerated figures:")
print(f"  1. {output_file}")
print(f"  2. {output_file2}")
print("\nDone!")
