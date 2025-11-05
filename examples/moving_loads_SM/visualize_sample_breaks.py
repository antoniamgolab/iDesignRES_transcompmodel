"""
Quick visualization of the sample mandatory breaks.
"""

import yaml
import pandas as pd
import matplotlib.pyplot as plt

print("="*80)
print("SAMPLE MANDATORY BREAKS VISUALIZATION")
print("="*80)

# Load data
print("\nLoading data from input_data/...")
with open("input_data/MandatoryBreaks.yaml") as f:
    breaks = yaml.safe_load(f)

with open("input_data/Path.yaml") as f:
    paths = yaml.safe_load(f)

df_breaks = pd.DataFrame(breaks)
df_paths = pd.DataFrame(paths)

print(f"Loaded {len(df_breaks)} breaks")
print(f"Loaded {len(df_paths)} paths")

# Analysis
print("\n" + "="*80)
print("BREAK STATISTICS")
print("="*80)

print(f"\nTotal breaks: {len(df_breaks)}")
print(f"Total paths: {len(df_paths)}")
print(f"Average breaks per path: {len(df_breaks)/len(df_paths):.2f}")

print(f"\nBreak timing:")
print(f"  Mean: {df_breaks['cumulative_driving_time'].mean():.2f}h")
print(f"  Median: {df_breaks['cumulative_driving_time'].median():.2f}h")
print(f"  Min: {df_breaks['cumulative_driving_time'].min():.2f}h")
print(f"  Max: {df_breaks['cumulative_driving_time'].max():.2f}h")
print(f"  Std: {df_breaks['cumulative_driving_time'].std():.2f}h")

# Check origin breaks
breaks_at_origin = (df_breaks['cumulative_driving_time'] == 0).sum()
print(f"\nBreaks at origin (0h): {breaks_at_origin} ({100*breaks_at_origin/len(df_breaks):.1f}%)")

if breaks_at_origin < len(df_breaks) * 0.2:
    print("OK FIX SUCCESSFUL: Most breaks are NOT at origin!")
else:
    print("WARNING: Many breaks still at origin")

# Show all breaks
print("\n" + "="*80)
print("ALL BREAKS DETAIL")
print("="*80)

for _, row in df_breaks.iterrows():
    print(f"\nBreak {row['break_number']} on path {row['path_id']}:")
    print(f"  Node index: {row['latest_node_idx']}")
    print(f"  Cumulative distance: {row['cumulative_distance']:.1f} km")
    print(f"  Cumulative time: {row['cumulative_driving_time']:.2f} h")

# Check which paths have breaks
paths_with_breaks = df_breaks['path_id'].unique()
print(f"\n{len(paths_with_breaks)} paths have breaks (out of {len(df_paths)} total)")

# Show path info for paths with breaks
print("\n" + "="*80)
print("PATHS WITH BREAKS")
print("="*80)

for path_id in paths_with_breaks:
    path = df_paths[df_paths['id'] == path_id].iloc[0]
    path_breaks = df_breaks[df_breaks['path_id'] == path_id]

    print(f"\nPath {path_id}: {path['origin']} -> {path['destination']}")
    print(f"  Length: {path['length']:.1f} km")
    print(f"  Total driving time: {path['length']/80:.2f} h (at 80 km/h)")
    print(f"  Sequence: {path['sequence']}")
    print(f"  Cumulative distances: {path['cumulative_distance']}")
    print(f"  Number of breaks: {len(path_breaks)}")

    for _, brk in path_breaks.iterrows():
        print(f"    Break {brk['break_number']}: at {brk['cumulative_driving_time']:.2f}h "
              f"(node_idx={brk['latest_node_idx']}, {brk['cumulative_distance']:.1f}km)")

# Simple visualization
if len(df_breaks) > 0:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Histogram of break timing
    ax1.hist(df_breaks['cumulative_driving_time'], bins=10,
             edgecolor='black', alpha=0.7, color='steelblue')
    ax1.axvline(x=4.5, color='red', linestyle='--', linewidth=2,
                label='4.5h limit', alpha=0.7)
    ax1.set_xlabel('Cumulative Driving Time (hours)', fontsize=11, fontweight='bold')
    ax1.set_ylabel('Number of Breaks', fontsize=11, fontweight='bold')
    ax1.set_title(f'Break Distribution (n={len(df_breaks)})', fontsize=12, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3, axis='y')

    # Merge with path data
    df_merged = df_breaks.merge(df_paths[['id', 'length']],
                                  left_on='path_id',
                                  right_on='id',
                                  how='left')

    # Scatter: break timing vs path length
    ax2.scatter(df_merged['length'], df_merged['cumulative_driving_time'],
                s=100, alpha=0.6, color='coral', edgecolors='black')
    ax2.axhline(y=4.5, color='red', linestyle='--', linewidth=2, alpha=0.6)
    ax2.set_xlabel('Path Length (km)', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Cumulative Time to Break (h)', fontsize=11, fontweight='bold')
    ax2.set_title('Break Timing vs Route Length', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()

    import os
    os.makedirs('figures', exist_ok=True)
    plt.savefig('figures/sample_breaks_visualization.png', dpi=300, bbox_inches='tight')
    print("\n" + "="*80)
    print("Figure saved: figures/sample_breaks_visualization.png")
    print("="*80)

    plt.show()

print("\nDone!")
