"""
Identify paths with very long edges (likely ferries or data errors)
These cause unrealistic break time requirements
"""

import yaml
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict

# Load data
case_folder = "case_20251106_112933"
input_path = os.path.join("input_data", case_folder)

def load_yaml_file(filename):
    filepath = os.path.join(input_path, filename)
    with open(filepath, 'r') as f:
        return yaml.safe_load(f)

print("="*80)
print("IDENTIFYING PATHS WITH LONG EDGES (FERRIES/DATA ERRORS)")
print("="*80)

paths = load_yaml_file('Path.yaml')
print(f"\nLoaded {len(paths)} paths")

# ============================================================================
# ANALYZE EACH PATH FOR LONG EDGES
# ============================================================================

problematic_paths = []
edge_length_stats = []

for path in paths:
    path_id = path['id']

    # Get distances if available
    if 'distance_from_previous' in path:
        distances = path['distance_from_previous']
        cumulative = path.get('cumulative_distance', [])

        # Skip first (always 0)
        segment_distances = [d for i, d in enumerate(distances) if i > 0]

        if not segment_distances:
            continue

        max_segment = max(segment_distances)
        edge_length_stats.append({
            'path_id': path_id,
            'path_length': path['length'],
            'num_segments': len(segment_distances),
            'max_segment': max_segment,
            'avg_segment': np.mean(segment_distances),
            'all_segments': segment_distances
        })

        # Flag if any segment is very long (likely ferry or error)
        long_edges = [d for d in segment_distances if d > 500]

        if long_edges:
            problematic_paths.append({
                'path_id': path_id,
                'path_length': path['length'],
                'num_segments': len(segment_distances),
                'max_segment': max_segment,
                'long_edges': long_edges,
                'num_long_edges': len(long_edges),
                'all_segments': segment_distances
            })

# Convert to DataFrame
df_stats = pd.DataFrame(edge_length_stats)
df_problematic = pd.DataFrame(problematic_paths)

print("\n" + "="*80)
print("OVERALL STATISTICS")
print("="*80)

print(f"\nAll paths ({len(df_stats)}):")
print(f"  Max segment overall: {df_stats['max_segment'].max():.1f} km")
print(f"  Mean of max segments: {df_stats['max_segment'].mean():.1f} km")
print(f"  Median of max segments: {df_stats['max_segment'].median():.1f} km")

# ============================================================================
# PROBLEMATIC PATHS BY THRESHOLD
# ============================================================================

print("\n" + "="*80)
print("PATHS WITH LONG EDGES")
print("="*80)

thresholds = [500, 600, 700, 800, 900, 1000]

print(f"\nPaths with at least one edge exceeding threshold:")
for thresh in thresholds:
    count = len(df_stats[df_stats['max_segment'] > thresh])
    pct = count / len(df_stats) * 100
    print(f"  > {thresh:4d} km: {count:4d} paths ({pct:5.2f}%)")

print(f"\n" + "-"*80)
print(f"Recommended threshold: 800 km (likely ferries)")
print(f"Paths to filter: {len(df_stats[df_stats['max_segment'] > 800])}")
print("-"*80)

# ============================================================================
# TOP PROBLEMATIC PATHS
# ============================================================================

print("\n" + "="*80)
print("TOP 20 PATHS WITH LONGEST EDGES")
print("="*80)

top_20 = df_stats.nlargest(20, 'max_segment')

for idx, row in top_20.iterrows():
    print(f"\nPath {row['path_id']}: Max segment = {row['max_segment']:.1f} km")
    print(f"  Total length: {row['path_length']:.1f} km")
    print(f"  Number of segments: {row['num_segments']}")
    print(f"  Average segment: {row['avg_segment']:.1f} km")

    # Show all segments
    segments = row['all_segments']
    long_segs = [s for s in segments if s > 500]
    if long_segs:
        print(f"  Long segments (>500km): {[f'{s:.1f}' for s in long_segs]}")

# ============================================================================
# DETAILED ANALYSIS OF PATH 2111
# ============================================================================

print("\n" + "="*80)
print("DETAILED LOOK AT PATH 2111 (YOUR EXAMPLE)")
print("="*80)

path_2111 = [p for p in paths if p['id'] == 2111][0]

if 'distance_from_previous' in path_2111:
    distances = path_2111['distance_from_previous']
    cumulative = path_2111['cumulative_distance']
    sequence = path_2111['sequence']

    print(f"\nPath 2111: {path_2111['length']:.1f} km total")
    print(f"Nodes: {len(sequence)}")
    print(f"\nSegment breakdown:")

    for i, (dist, cum, node) in enumerate(zip(distances, cumulative, sequence)):
        if i == 0:
            print(f"  Node {i} (ID={node}): Start")
        else:
            flag = " <- FERRY?" if dist > 800 else ""
            print(f"  Node {i} (ID={node}): +{dist:.1f} km (total: {cum:.1f} km){flag}")

# ============================================================================
# SAVE PROBLEMATIC PATH IDS
# ============================================================================

print("\n" + "="*80)
print("SAVING RESULTS")
print("="*80)

# Use 800km threshold as recommended
ferry_threshold = 800
ferry_paths = df_stats[df_stats['max_segment'] > ferry_threshold]['path_id'].tolist()

output = {
    'ferry_paths': ferry_paths,
    'threshold_km': ferry_threshold,
    'num_paths': len(ferry_paths),
    'total_paths': len(paths),
    'percentage': len(ferry_paths) / len(paths) * 100,
    'statistics': {
        'max_edge_in_dataset': float(df_stats['max_segment'].max()),
        'mean_max_edge': float(df_stats['max_segment'].mean()),
        'median_max_edge': float(df_stats['max_segment'].median())
    }
}

with open('ferry_routes.yaml', 'w') as f:
    yaml.dump(output, f)

print(f"\nSaved {len(ferry_paths)} ferry route IDs to: ferry_routes.yaml")
print(f"These are {len(ferry_paths)/len(paths)*100:.2f}% of all paths")

# ============================================================================
# VISUALIZATION
# ============================================================================

print("\n" + "="*80)
print("CREATING VISUALIZATIONS")
print("="*80)

fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# PLOT 1: Distribution of maximum segment lengths
ax1 = axes[0, 0]
ax1.hist(df_stats['max_segment'], bins=50, color='steelblue',
         alpha=0.7, edgecolor='black', linewidth=0.5)
ax1.axvline(x=800, color='red', linestyle='--', linewidth=2.5,
           label='Ferry threshold (800 km)')
ax1.axvline(x=df_stats['max_segment'].median(), color='green',
           linestyle='-', linewidth=2, label=f'Median: {df_stats["max_segment"].median():.1f} km')
ax1.set_xlabel('Maximum Segment Length (km)', fontsize=12, fontweight='bold')
ax1.set_ylabel('Number of Paths', fontsize=12, fontweight='bold')
ax1.set_title('Distribution of Maximum Segment Lengths',
             fontsize=13, fontweight='bold')
ax1.legend(fontsize=10)
ax1.grid(True, alpha=0.3, axis='y')
ax1.set_xlim(0, min(2000, df_stats['max_segment'].max() * 1.1))

# PLOT 2: Max segment vs total path length
ax2 = axes[0, 1]
scatter = ax2.scatter(df_stats['path_length'], df_stats['max_segment'],
                     c=df_stats['num_segments'], cmap='viridis',
                     s=50, alpha=0.6, edgecolors='black', linewidth=0.5)
ax2.axhline(y=800, color='red', linestyle='--', linewidth=2, label='800 km ferry threshold')
cbar = plt.colorbar(scatter, ax=ax2)
cbar.set_label('Number of Segments', rotation=270, labelpad=20)

ax2.set_xlabel('Total Path Length (km)', fontsize=12, fontweight='bold')
ax2.set_ylabel('Maximum Segment Length (km)', fontsize=12, fontweight='bold')
ax2.set_title('Max Segment vs Total Path Length',
             fontsize=13, fontweight='bold')
ax2.legend(fontsize=10)
ax2.grid(True, alpha=0.3)

# PLOT 3: Paths above different thresholds
ax3 = axes[1, 0]
thresholds_plot = [400, 500, 600, 700, 800, 900, 1000]
counts = [len(df_stats[df_stats['max_segment'] > t]) for t in thresholds_plot]
percentages = [c / len(df_stats) * 100 for c in counts]

bars = ax3.bar(range(len(thresholds_plot)), counts, color='coral', alpha=0.7,
              edgecolor='black', linewidth=1)

# Highlight 800km threshold
bars[thresholds_plot.index(800)].set_color('red')
bars[thresholds_plot.index(800)].set_alpha(0.9)

ax3.set_xlabel('Edge Length Threshold (km)', fontsize=12, fontweight='bold')
ax3.set_ylabel('Number of Paths', fontsize=12, fontweight='bold')
ax3.set_title('Paths Exceeding Different Thresholds',
             fontsize=13, fontweight='bold')
ax3.set_xticks(range(len(thresholds_plot)))
ax3.set_xticklabels([f'>{t}' for t in thresholds_plot])
ax3.grid(True, alpha=0.3, axis='y')

# Add percentage labels on bars
for i, (bar, pct) in enumerate(zip(bars, percentages)):
    height = bar.get_height()
    ax3.text(bar.get_x() + bar.get_width()/2., height,
            f'{pct:.1f}%',
            ha='center', va='bottom', fontsize=9)

# PLOT 4: Top 15 longest edges
ax4 = axes[1, 1]
top_15 = df_stats.nlargest(15, 'max_segment').sort_values('max_segment')

y_pos = range(len(top_15))
colors = ['red' if x > 800 else 'steelblue' for x in top_15['max_segment']]

ax4.barh(y_pos, top_15['max_segment'], color=colors, alpha=0.7,
        edgecolor='black', linewidth=0.5)
ax4.axvline(x=800, color='red', linestyle='--', linewidth=2,
           label='800 km threshold', zorder=10)

ax4.set_yticks(y_pos)
ax4.set_yticklabels([f"Path {pid}" for pid in top_15['path_id']], fontsize=9)
ax4.set_xlabel('Maximum Segment Length (km)', fontsize=12, fontweight='bold')
ax4.set_title('Top 15 Paths with Longest Edges',
             fontsize=13, fontweight='bold')
ax4.legend(fontsize=10)
ax4.grid(True, alpha=0.3, axis='x')

# Add value labels
for i, (pos, val, pid) in enumerate(zip(y_pos, top_15['max_segment'], top_15['path_id'])):
    ax4.text(val, pos, f' {val:.0f}km',
            va='center', fontsize=8)

plt.tight_layout()
plt.savefig('ferry_routes_analysis.png', dpi=300, bbox_inches='tight')
plt.show()

print("\nPlot saved as: ferry_routes_analysis.png")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "="*80)
print("SUMMARY")
print("="*80)

print(f"""
Total paths analyzed: {len(paths)}
Paths with edges > 800 km: {len(ferry_paths)} ({len(ferry_paths)/len(paths)*100:.2f}%)

These long edges are likely:
  1. Ferry routes (e.g., Sweden-Poland across Baltic Sea)
  2. Network data errors (missing intermediate nodes)

Impact on break time analysis:
  - These paths have unrealistic mandatory break requirements
  - Cause massive extra_break_time values (like the 736h in Path 2111)
  - Should be FILTERED from break time visualizations

Recommendation:
  - Filter paths with max segment > 800 km
  - OR identify ferries in network data and exclude from break logic
  - OR add intermediate virtual nodes to break up long edges

Files created:
  - ferry_routes.yaml: List of problematic path IDs
  - ferry_routes_analysis.png: Visualization
""")

print("="*80)
