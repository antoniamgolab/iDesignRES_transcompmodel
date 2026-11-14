"""
INVESTIGATE LONG BREAKS (>1.5 hours)
Understand where these long stop times come from

Add this to break_times.ipynb to analyze routes with stop times > 1.5h
"""

# ==============================================================================
# ISOLATE ROUTES WITH LONG STOP TIMES (> 1.5 hours)
# ==============================================================================
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Filter routes with long stops
threshold = 1.5  # hours
long_stops = df_timing[df_timing["total_stop_time"] > threshold].copy()

print("="*80)
print(f"INVESTIGATING ROUTES WITH STOP TIMES > {threshold} HOURS")
print("="*80)
print(f"\nFound {len(long_stops)} routes with stop time > {threshold}h")
print(f"Percentage: {len(long_stops)/len(df_timing)*100:.1f}% of all routes")

# ==============================================================================
# COMPONENT BREAKDOWN
# ==============================================================================
print("\n" + "="*80)
print("COMPONENT BREAKDOWN FOR LONG STOPS")
print("="*80)

# Calculate what percentage comes from each component
if 'actual_break_duration' in long_stops.columns and 'charging_time' in long_stops.columns:
    long_stops['break_pct'] = (long_stops['actual_break_duration'] / long_stops['total_stop_time']) * 100
    long_stops['charging_pct'] = (long_stops['charging_time'] / long_stops['total_stop_time']) * 100

    print(f"\nAverage component breakdown (for stops > {threshold}h):")
    print(f"  Break duration: {long_stops['actual_break_duration'].mean():.2f}h ({long_stops['break_pct'].mean():.1f}%)")
    print(f"  Charging time: {long_stops['charging_time'].mean():.2f}h ({long_stops['charging_pct'].mean():.1f}%)")
    print(f"  Total: {long_stops['total_stop_time'].mean():.2f}h")

    # How many have significant charging?
    with_charging = long_stops[long_stops['charging_time'] > 0.5]
    without_charging = long_stops[long_stops['charging_time'] <= 0.5]

    print(f"\n  Routes with significant charging (>0.5h): {len(with_charging)} ({len(with_charging)/len(long_stops)*100:.1f}%)")
    print(f"  Routes without significant charging: {len(without_charging)} ({len(without_charging)/len(long_stops)*100:.1f}%)")

    if len(with_charging) > 0:
        print(f"\n  For routes WITH charging (>0.5h):")
        print(f"    Avg total stop: {with_charging['total_stop_time'].mean():.2f}h")
        print(f"    Avg charging: {with_charging['charging_time'].mean():.2f}h")
        print(f"    Avg break: {with_charging['actual_break_duration'].mean():.2f}h")

    if len(without_charging) > 0:
        print(f"\n  For routes WITHOUT significant charging:")
        print(f"    Avg total stop: {without_charging['total_stop_time'].mean():.2f}h")
        print(f"    Avg break: {without_charging['actual_break_duration'].mean():.2f}h")
        print(f"    -> This break time needs investigation!")

# ==============================================================================
# CHECK ROUTE CHARACTERISTICS
# ==============================================================================
print("\n" + "="*80)
print("ROUTE CHARACTERISTICS")
print("="*80)

# If we have path_id, get route details from input data
if 'path_id' in long_stops.columns:
    # Get unique path IDs
    long_stop_path_ids = long_stops['path_id'].unique()

    print(f"\nUnique routes with long stops: {len(long_stop_path_ids)}")

    # Load path data to check lengths
    paths = loaded_runs[case_name]["input_data"]['Path']
    paths_dict = {p['id']: p for p in paths}

    # Get path lengths
    long_stops['path_length'] = long_stops['path_id'].map(
        lambda pid: paths_dict.get(pid, {}).get('length', np.nan)
    )
    long_stops['num_nodes'] = long_stops['path_id'].map(
        lambda pid: len(paths_dict.get(pid, {}).get('sequence', [])) if pid in paths_dict else np.nan
    )
    long_stops['avg_segment'] = long_stops.apply(
        lambda row: row['path_length'] / (row['num_nodes'] - 1) if row['num_nodes'] > 1 else np.nan,
        axis=1
    )

    print(f"\nPath length statistics:")
    print(f"  Mean: {long_stops['path_length'].mean():.1f} km")
    print(f"  Median: {long_stops['path_length'].median():.1f} km")
    print(f"  Min: {long_stops['path_length'].min():.1f} km")
    print(f"  Max: {long_stops['path_length'].max():.1f} km")

    print(f"\nAverage segment length:")
    print(f"  Mean: {long_stops['avg_segment'].mean():.1f} km")
    print(f"  Median: {long_stops['avg_segment'].median():.1f} km")

    # Compare with all routes
    all_path_lengths = [paths_dict[pid]['length'] for pid in df_timing['path_id'].unique()
                       if pid in paths_dict]
    print(f"\nComparison with all routes:")
    print(f"  All routes avg length: {np.mean(all_path_lengths):.1f} km")
    print(f"  Long stop routes avg: {long_stops['path_length'].mean():.1f} km")
    print(f"  Difference: {long_stops['path_length'].mean() - np.mean(all_path_lengths):.1f} km "
          f"({(long_stops['path_length'].mean() - np.mean(all_path_lengths))/np.mean(all_path_lengths)*100:.1f}%)")

# ==============================================================================
# CHECK MANDATORY BREAKS FROM INPUT DATA
# ==============================================================================
print("\n" + "="*80)
print("CHECKING MANDATORY BREAKS FROM INPUT DATA")
print("="*80)

if 'path_id' in long_stops.columns:
    mandatory_breaks = loaded_runs[case_name]["input_data"]['MandatoryBreaks']
    breaks_dict = {}
    for mb in mandatory_breaks:
        if mb['path_id'] not in breaks_dict:
            breaks_dict[mb['path_id']] = []
        breaks_dict[mb['path_id']].append(mb)

    # For each long stop route, check the mandatory break time
    print(f"\nChecking first 10 routes with longest stops:")
    print("-"*80)

    top_10 = long_stops.nlargest(10, 'total_stop_time')

    for idx, row in top_10.iterrows():
        path_id = row['path_id']
        total_stop = row['total_stop_time']
        break_dur = row.get('actual_break_duration', np.nan)
        charging = row.get('charging_time', np.nan)

        print(f"\nPath {path_id}: Total stop = {total_stop:.2f}h ({total_stop*60:.0f} min)")
        print(f"  Break: {break_dur:.2f}h, Charging: {charging:.2f}h")

        # Get mandatory break info
        if path_id in breaks_dict:
            path_breaks = breaks_dict[path_id]
            print(f"  Mandatory breaks: {len(path_breaks)}")
            for i, mb in enumerate(path_breaks[:3], 1):  # Show first 3
                print(f"    Break #{mb['break_number']}: "
                      f"Time with breaks = {mb['time_with_breaks']:.2f}h "
                      f"(at {mb['cumulative_distance']:.0f} km)")
        else:
            print(f"  Mandatory breaks: 0 (path < 360km)")

        # Get path info
        if path_id in paths_dict:
            path = paths_dict[path_id]
            print(f"  Path length: {path['length']:.1f} km, Nodes: {len(path['sequence'])}")

# ==============================================================================
# EXTRACT EXTRA_BREAK_TIME FOR THESE ROUTES
# ==============================================================================
print("\n" + "="*80)
print("CHECKING EXTRA_BREAK_TIME FROM MODEL OUTPUT")
print("="*80)

# Load extra_break_time data
extra_break_time_data = loaded_runs[case_name]["output_data"].get("extra_break_time", {})

if extra_break_time_data and 'path_id' in long_stops.columns:
    # Aggregate extra_break_time by path_id
    from collections import defaultdict
    import re

    path_extra_break = defaultdict(lambda: {'max': 0, 'sum': 0, 'count': 0})

    for key, value in extra_break_time_data.items():
        # Convert value to float
        if isinstance(value, str):
            value = float(value)

        if value > 0:
            # Parse key to get path_id
            if isinstance(key, str):
                numbers = re.findall(r'\d+', key)
                if len(numbers) >= 4:
                    path_id = int(numbers[2])
                    path_extra_break[path_id]['max'] = max(path_extra_break[path_id]['max'], value)
                    path_extra_break[path_id]['sum'] += value
                    path_extra_break[path_id]['count'] += 1
            else:
                path_id = key[1][2]
                path_extra_break[path_id]['max'] = max(path_extra_break[path_id]['max'], value)
                path_extra_break[path_id]['sum'] += value
                path_extra_break[path_id]['count'] += 1

    # Add to long_stops dataframe
    long_stops['extra_break_time_max'] = long_stops['path_id'].map(
        lambda pid: path_extra_break[pid]['max'] if pid in path_extra_break else 0
    )
    long_stops['extra_break_time_sum'] = long_stops['path_id'].map(
        lambda pid: path_extra_break[pid]['sum'] if pid in path_extra_break else 0
    )

    print(f"\nExtra break time statistics for long stop routes:")
    print(f"  Routes with extra_break_time > 0: {len(long_stops[long_stops['extra_break_time_max'] > 0])}")
    print(f"  Avg max extra_break_time: {long_stops['extra_break_time_max'].mean():.2f}h")
    print(f"  Median max extra_break_time: {long_stops['extra_break_time_max'].median():.2f}h")
    print(f"  Max extra_break_time: {long_stops['extra_break_time_max'].max():.2f}h")

    # Check correlation
    correlation = long_stops[['total_stop_time', 'extra_break_time_max', 'charging_time']].corr()
    print(f"\nCorrelation with total_stop_time:")
    print(f"  extra_break_time: {correlation.loc['total_stop_time', 'extra_break_time_max']:.3f}")
    print(f"  charging_time: {correlation.loc['total_stop_time', 'charging_time']:.3f}")

    # Top 10 by extra_break_time
    print(f"\nTop 10 routes by extra_break_time:")
    top_extra = long_stops.nlargest(10, 'extra_break_time_max')
    for idx, row in top_extra.iterrows():
        print(f"  Path {row['path_id']}: extra_break={row['extra_break_time_max']:.2f}h, "
              f"total_stop={row['total_stop_time']:.2f}h, "
              f"charging={row['charging_time']:.2f}h")

# ==============================================================================
# VISUALIZATION: WHAT CAUSES LONG STOPS?
# ==============================================================================
print("\n" + "="*80)
print("CREATING VISUALIZATION")
print("="*80)

fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# PLOT 1: Component breakdown
ax1 = axes[0, 0]
if 'actual_break_duration' in long_stops.columns:
    # Stacked bar showing components
    sample = long_stops.nlargest(30, 'total_stop_time')
    x = range(len(sample))

    ax1.bar(x, sample['actual_break_duration'], label='Break Duration',
           color='steelblue', alpha=0.8)
    ax1.bar(x, sample['charging_time'], bottom=sample['actual_break_duration'],
           label='Charging Time', color='coral', alpha=0.8)

    ax1.set_xlabel('Routes (sorted by total stop time)', fontsize=11)
    ax1.set_ylabel('Time (hours)', fontsize=11)
    ax1.set_title(f'Component Breakdown: Top 30 Longest Stops\n(> {threshold}h total)',
                 fontsize=12, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3, axis='y')

# PLOT 2: Total stop time vs path length
ax2 = axes[0, 1]
if 'path_length' in long_stops.columns:
    scatter = ax2.scatter(long_stops['path_length'], long_stops['total_stop_time'],
                         c=long_stops['charging_time'], cmap='YlOrRd',
                         s=100, alpha=0.6, edgecolors='black', linewidth=0.5)

    cbar = plt.colorbar(scatter, ax=ax2)
    cbar.set_label('Charging Time (h)', rotation=270, labelpad=20)

    ax2.set_xlabel('Path Length (km)', fontsize=11)
    ax2.set_ylabel('Total Stop Time (hours)', fontsize=11)
    ax2.set_title('Stop Time vs Path Length\n(Color = Charging Time)',
                 fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3)

# PLOT 3: Extra break time contribution
ax3 = axes[1, 0]
if 'extra_break_time_max' in long_stops.columns:
    ax3.scatter(long_stops['extra_break_time_max'], long_stops['total_stop_time'],
               s=100, alpha=0.6, color='purple', edgecolors='black', linewidth=0.5)

    # Add diagonal line (if extra_break_time explained everything)
    max_val = max(long_stops['extra_break_time_max'].max(), long_stops['total_stop_time'].max())
    ax3.plot([0, max_val], [0, max_val], 'r--', linewidth=2, alpha=0.5,
            label='If extra_break_time = total_stop_time')

    ax3.set_xlabel('Max Extra Break Time (hours)', fontsize=11)
    ax3.set_ylabel('Total Stop Time (hours)', fontsize=11)
    ax3.set_title('Extra Break Time vs Total Stop Time',
                 fontsize=12, fontweight='bold')
    ax3.legend()
    ax3.grid(True, alpha=0.3)

# PLOT 4: Distribution by year
ax4 = axes[1, 1]
if 'year' in long_stops.columns:
    year_data = long_stops.groupby('year')['total_stop_time'].agg(['mean', 'max', 'count'])

    x = range(len(year_data))
    ax4.bar(x, year_data['mean'], alpha=0.7, color='steelblue',
           label='Mean stop time')
    ax4.plot(x, year_data['max'], 'ro-', linewidth=2, markersize=8,
            label='Max stop time')

    ax4_twin = ax4.twinx()
    ax4_twin.plot(x, year_data['count'], 'gs-', linewidth=2, markersize=8,
                 label='Count')

    ax4.set_xlabel('Year', fontsize=11)
    ax4.set_ylabel('Stop Time (hours)', fontsize=11, color='steelblue')
    ax4_twin.set_ylabel('Count', fontsize=11, color='green')
    ax4.set_title('Long Stops by Year\n(Mean, Max, Count)',
                 fontsize=12, fontweight='bold')
    ax4.set_xticks(x)
    ax4.set_xticklabels(year_data.index)
    ax4.grid(True, alpha=0.3)

    # Combine legends
    lines1, labels1 = ax4.get_legend_handles_labels()
    lines2, labels2 = ax4_twin.get_legend_handles_labels()
    ax4.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

plt.tight_layout()
plt.savefig('long_stops_investigation.png', dpi=300, bbox_inches='tight')
plt.show()

print("\nPlot saved as 'long_stops_investigation.png'")

# ==============================================================================
# SUMMARY AND CONCLUSIONS
# ==============================================================================
print("\n" + "="*80)
print("SUMMARY: WHERE DO LONG BREAKS COME FROM?")
print("="*80)

if 'actual_break_duration' in long_stops.columns and 'charging_time' in long_stops.columns:
    total_break = long_stops['actual_break_duration'].sum()
    total_charging = long_stops['charging_time'].sum()
    total_stop = long_stops['total_stop_time'].sum()

    print(f"\nFor {len(long_stops)} routes with stop time > {threshold}h:")
    print(f"  Total stop time: {total_stop:.2f}h")
    print(f"  From break duration: {total_break:.2f}h ({total_break/total_stop*100:.1f}%)")
    print(f"  From charging: {total_charging:.2f}h ({total_charging/total_stop*100:.1f}%)")

    print(f"\nMain contributors:")
    if total_charging/total_stop > 0.5:
        print(f"  -> CHARGING is the primary cause ({total_charging/total_stop*100:.1f}%)")
    else:
        print(f"  -> BREAK DURATION is the primary cause ({total_break/total_stop*100:.1f}%)")
        print(f"     This includes mandatory breaks + extra_break_time slack")

if 'path_length' in long_stops.columns:
    avg_length_long_stops = long_stops['path_length'].mean()
    if 'path_id' in df_timing.columns:
        all_lengths = [paths_dict[pid]['length'] for pid in df_timing['path_id'].unique()
                      if pid in paths_dict]
        avg_length_all = np.mean(all_lengths)

        if avg_length_long_stops > avg_length_all * 1.2:
            print(f"\n  -> Long stop routes are LONGER than average")
            print(f"     ({avg_length_long_stops:.1f} km vs {avg_length_all:.1f} km)")
        else:
            print(f"\n  -> Long stop routes are NOT significantly longer")
            print(f"     ({avg_length_long_stops:.1f} km vs {avg_length_all:.1f} km)")

print("\n" + "="*80)
