"""
Add mandatory breaks validation cell to results_SM.ipynb
"""
import json
from pathlib import Path
import sys

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Read the notebook
notebook_path = Path("results_SM.ipynb")
with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Create markdown header cell
markdown_cell = {
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "## Mandatory Breaks Validation\n",
        "\n",
        "Validate and visualize mandatory breaks from the input data according to EU Regulation (EC) No 561/2006."
    ]
}

# Create code cell with validation logic
code_cell = {
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
'''"""
Mandatory Breaks Validation and Visualization

This section validates and visualizes the mandatory breaks from the input data.
It checks:
1. Total travel time for each path
2. Break intervals (should be ~4.5h of driving between breaks)
3. Break durations (45min for breaks, 9h for rests)
4. Distance and time progression along paths
"""

import yaml
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Configuration
SHORT_BREAK_INTERVAL = 4.5  # hours
SHORT_BREAK_DURATION = 0.75  # hours (45 minutes)
DAILY_REST_DURATION = 9.0  # hours

# Load mandatory breaks from input data
with open(input_dir / "MandatoryBreaks.yaml", 'r') as f:
    breaks = yaml.safe_load(f)
df_breaks = pd.DataFrame(breaks)

print(f"Loaded {len(df_breaks)} mandatory breaks from {df_breaks['path_id'].nunique()} paths")

# Summary statistics
print("\\n" + "="*80)
print("MANDATORY BREAKS SUMMARY")
print("="*80)

print(f"\\nTotal paths with breaks: {df_breaks['path_id'].nunique()}")
print(f"Total mandatory breaks: {len(df_breaks)}")
print(f"  - Type B (short breaks): {len(df_breaks[df_breaks['event_type'] == 'B'])}")
print(f"  - Type R (rest periods): {len(df_breaks[df_breaks['event_type'] == 'R'])}")

print(f"\\nCharging type distribution:")
print(f"  - Fast charging: {len(df_breaks[df_breaks['charging_type'] == 'fast'])}")
print(f"  - Slow charging: {len(df_breaks[df_breaks['charging_type'] == 'slow'])}")

# Path characteristics
path_summary = df_breaks.groupby('path_id').agg({
    'path_length': 'first',
    'total_driving_time': 'first',
    'num_drivers': 'first',
    'break_number': 'max'
}).reset_index()

print(f"\\nPath characteristics:")
print(f"  Average path length: {path_summary['path_length'].mean():.1f} km")
print(f"  Average driving time: {path_summary['total_driving_time'].mean():.2f} h")
print(f"  Average breaks per path: {path_summary['break_number'].mean():.1f}")

# Validate break timing
print("\\n" + "="*80)
print("BREAK TIMING VALIDATION")
print("="*80)

timing_issues = []
for path_id, path_breaks in df_breaks.groupby('path_id'):
    path_breaks = path_breaks.sort_values('break_number')

    prev_driving_time = 0.0
    for idx, row in path_breaks.iterrows():
        time_since_last = row['cumulative_driving_time'] - prev_driving_time

        # Check if timing is correct (within 10% tolerance or first break)
        timing_ok = abs(time_since_last - SHORT_BREAK_INTERVAL) < 0.5 or time_since_last == 0.0

        if not timing_ok:
            timing_issues.append({
                'path_id': path_id,
                'path_length': row['path_length'],
                'total_time': row['total_driving_time'],
                'break_number': row['break_number'],
                'time_since_last': time_since_last,
                'expected': SHORT_BREAK_INTERVAL,
                'deviation': abs(time_since_last - SHORT_BREAK_INTERVAL)
            })

        prev_driving_time = row['cumulative_driving_time']

if timing_issues:
    print(f"\\n⚠️ Found {len(timing_issues)} breaks with timing issues:")
    df_issues = pd.DataFrame(timing_issues)
    print(df_issues.to_string(index=False))
else:
    print("\\n✓ All breaks have correct timing!")

# Create visualizations
fig, axes = plt.subplots(2, 2, figsize=(15, 10))
fig.suptitle('Mandatory Breaks Analysis', fontsize=16, fontweight='bold')

# 1. Break intervals distribution
ax = axes[0, 0]
intervals = []
for path_id, path_breaks in df_breaks.groupby('path_id'):
    path_breaks = path_breaks.sort_values('break_number')
    prev_time = 0.0
    for _, row in path_breaks.iterrows():
        interval = row['cumulative_driving_time'] - prev_time
        if interval > 0:
            intervals.append(interval)
        prev_time = row['cumulative_driving_time']

if intervals:
    ax.hist(intervals, bins=20, edgecolor='black', alpha=0.7)
    ax.axvline(SHORT_BREAK_INTERVAL, color='red', linestyle='--', linewidth=2,
               label=f'Target: {SHORT_BREAK_INTERVAL}h')
ax.set_xlabel('Time between breaks (hours)', fontsize=12)
ax.set_ylabel('Frequency', fontsize=12)
ax.set_title('Distribution of Break Intervals', fontsize=13, fontweight='bold')
ax.legend()
ax.grid(True, alpha=0.3)

# 2. Path length vs number of breaks
ax = axes[0, 1]
scatter = ax.scatter(path_summary['path_length'], path_summary['break_number'],
                     c=path_summary['total_driving_time'], cmap='viridis', s=100, alpha=0.7)
ax.set_xlabel('Path length (km)', fontsize=12)
ax.set_ylabel('Number of breaks', fontsize=12)
ax.set_title('Path Length vs Number of Breaks', fontsize=13, fontweight='bold')
ax.grid(True, alpha=0.3)
cbar = plt.colorbar(scatter, ax=ax)
cbar.set_label('Total driving time (h)', fontsize=10)

# 3. Cumulative time progression
ax = axes[1, 0]
for path_id, path_breaks in df_breaks.groupby('path_id'):
    path_breaks = path_breaks.sort_values('break_number')
    plot_x = [0] + list(path_breaks['cumulative_distance'])
    plot_y = [0] + list(path_breaks['time_with_breaks'])
    ax.plot(plot_x, plot_y, marker='o', linewidth=2, markersize=6,
            label=f"Path {path_id} ({path_breaks.iloc[0]['path_length']:.0f} km)", alpha=0.7)

ax.set_xlabel('Cumulative distance (km)', fontsize=12)
ax.set_ylabel('Total time with breaks (hours)', fontsize=12)
ax.set_title('Time Progression Along Paths', fontsize=13, fontweight='bold')
ax.legend(fontsize=8, loc='upper left')
ax.grid(True, alpha=0.3)

# 4. Break type distribution
ax = axes[1, 1]
event_counts = df_breaks.groupby(['event_type', 'charging_type']).size().reset_index(name='count')
x_pos = np.arange(len(event_counts))
colors = ['#2E86AB' if ct == 'fast' else '#A23B72' for ct in event_counts['charging_type']]
bars = ax.bar(x_pos, event_counts['count'], color=colors, alpha=0.7, edgecolor='black')
ax.set_xticks(x_pos)
ax.set_xticklabels([f"{row['event_type']}\\n({row['charging_type']})"
                     for _, row in event_counts.iterrows()], fontsize=10)
ax.set_ylabel('Count', fontsize=12)
ax.set_title('Break Types and Charging Distribution', fontsize=13, fontweight='bold')
ax.grid(True, alpha=0.3, axis='y')

for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'{int(height)}', ha='center', va='bottom', fontsize=11, fontweight='bold')

plt.tight_layout()
plt.show()

print("\\n" + "="*80)
print("VALIDATION COMPLETE")
print("="*80)'''
    ]
}

# Add cells to notebook
nb['cells'].extend([markdown_cell, code_cell])

# Save updated notebook
with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print(f"✓ Added mandatory breaks validation section to {notebook_path}")
print(f"  Total cells: {len(nb['cells'])}")
