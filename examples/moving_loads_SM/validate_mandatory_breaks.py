"""
Validation and Visualization of Mandatory Breaks Data

This script validates and visualizes the mandatory breaks generated according to EU Regulation (EC) No 561/2006.
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
from pathlib import Path
import sys

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Configuration
CASE_DIR = Path("input_data/case_20251015_195344")
SHORT_BREAK_INTERVAL = 4.5  # hours
SHORT_BREAK_DURATION = 0.75  # hours (45 minutes)
DAILY_REST_DURATION = 9.0  # hours
DAILY_DRIVING_LIMIT_1_DRIVER = 9.0  # hours
DAILY_DRIVING_LIMIT_2_DRIVERS = 18.0  # hours


def load_mandatory_breaks():
    """Load mandatory breaks from YAML file."""
    with open(CASE_DIR / "MandatoryBreaks.yaml", 'r') as f:
        breaks = yaml.safe_load(f)
    return pd.DataFrame(breaks)


def load_paths():
    """Load path data from YAML file."""
    with open(CASE_DIR / "Path.yaml", 'r') as f:
        paths = yaml.safe_load(f)
    return pd.DataFrame(paths)


def validate_break_timing(df):
    """Validate that breaks occur at proper intervals."""
    print("\n" + "="*80)
    print("BREAK TIMING VALIDATION")
    print("="*80)

    validation_results = []

    # Group by path_id to check intervals within each path
    for path_id, path_breaks in df.groupby('path_id'):
        path_breaks = path_breaks.sort_values('break_number')

        print(f"\nPath {path_id} (Length: {path_breaks.iloc[0]['path_length']:.1f} km, "
              f"Total driving time: {path_breaks.iloc[0]['total_driving_time']:.2f} h, "
              f"Drivers: {path_breaks.iloc[0]['num_drivers']})")

        prev_driving_time = 0.0

        for idx, row in path_breaks.iterrows():
            # Calculate time since last break (or start)
            time_since_last = row['cumulative_driving_time'] - prev_driving_time

            # Calculate distance since last break
            if idx == path_breaks.index[0]:
                dist_since_last = row['cumulative_distance']
            else:
                prev_row = path_breaks.loc[path_breaks.index[path_breaks.index.get_loc(idx)-1]]
                dist_since_last = row['cumulative_distance'] - prev_row['cumulative_distance']

            # Expected duration for this event type
            expected_duration = SHORT_BREAK_DURATION if row['event_type'] == 'B' else DAILY_REST_DURATION
            actual_duration = row['time_with_breaks'] - row['cumulative_driving_time']

            # Validate timing
            timing_ok = abs(time_since_last - SHORT_BREAK_INTERVAL) < 0.1 or time_since_last == 0.0
            duration_ok = abs(actual_duration - expected_duration) < 0.01

            status = "✓" if (timing_ok and duration_ok) else "✗"

            print(f"  Break {row['break_number']}: {status}")
            print(f"    Type: {row['event_type']} ({row['event_name']}) at node {row['latest_node_idx']} (geo_id: {row['latest_geo_id']})")
            print(f"    Cumulative distance: {row['cumulative_distance']:.2f} km (+{dist_since_last:.2f} km)")
            print(f"    Cumulative driving time: {row['cumulative_driving_time']:.2f} h (+{time_since_last:.2f} h)")
            print(f"    Time since last break: {time_since_last:.2f} h (expected: ~{SHORT_BREAK_INTERVAL:.1f} h)")
            print(f"    Break duration: {actual_duration:.2f} h (expected: {expected_duration:.2f} h)")
            print(f"    Total time with breaks: {row['time_with_breaks']:.2f} h")
            print(f"    Charging type: {row['charging_type']}")

            validation_results.append({
                'path_id': path_id,
                'break_number': row['break_number'],
                'time_since_last': time_since_last,
                'expected_interval': SHORT_BREAK_INTERVAL,
                'timing_ok': timing_ok,
                'duration_ok': duration_ok,
                'event_type': row['event_type']
            })

            prev_driving_time = row['cumulative_driving_time']

        # Check time remaining after last break
        total_time = path_breaks.iloc[0]['total_driving_time']
        time_after_last = total_time - prev_driving_time
        print(f"\n  Time remaining after last break: {time_after_last:.2f} h")
        print(f"  Total breaks: {len(path_breaks)}")

    return pd.DataFrame(validation_results)


def plot_break_intervals(df):
    """Plot break intervals across all paths."""
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('Mandatory Breaks Analysis', fontsize=16, fontweight='bold')

    # 1. Break intervals distribution
    ax = axes[0, 0]
    intervals = []
    for path_id, path_breaks in df.groupby('path_id'):
        path_breaks = path_breaks.sort_values('break_number')
        prev_time = 0.0
        for _, row in path_breaks.iterrows():
            interval = row['cumulative_driving_time'] - prev_time
            if interval > 0:  # Skip first break if at origin
                intervals.append(interval)
            prev_time = row['cumulative_driving_time']

    ax.hist(intervals, bins=20, edgecolor='black', alpha=0.7)
    ax.axvline(SHORT_BREAK_INTERVAL, color='red', linestyle='--', linewidth=2, label=f'Target: {SHORT_BREAK_INTERVAL}h')
    ax.set_xlabel('Time between breaks (hours)', fontsize=12)
    ax.set_ylabel('Frequency', fontsize=12)
    ax.set_title('Distribution of Break Intervals', fontsize=13, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 2. Path length vs number of breaks
    ax = axes[0, 1]
    path_summary = df.groupby('path_id').agg({
        'path_length': 'first',
        'total_driving_time': 'first',
        'break_number': 'max'
    }).reset_index()

    scatter = ax.scatter(path_summary['path_length'], path_summary['break_number'],
                         c=path_summary['total_driving_time'], cmap='viridis', s=100, alpha=0.7)
    ax.set_xlabel('Path length (km)', fontsize=12)
    ax.set_ylabel('Number of breaks', fontsize=12)
    ax.set_title('Path Length vs Number of Breaks', fontsize=13, fontweight='bold')
    ax.grid(True, alpha=0.3)
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('Total driving time (h)', fontsize=10)

    # 3. Cumulative time progression by path
    ax = axes[1, 0]
    for path_id, path_breaks in df.groupby('path_id'):
        path_breaks = path_breaks.sort_values('break_number')

        # Create plot data with origin point
        plot_x = [0] + list(path_breaks['cumulative_distance'])
        plot_y = [0] + list(path_breaks['time_with_breaks'])

        ax.plot(plot_x, plot_y, marker='o', linewidth=2, markersize=6,
                label=f"Path {path_id} ({path_breaks.iloc[0]['path_length']:.0f} km)", alpha=0.7)

        # Mark break locations
        ax.scatter(path_breaks['cumulative_distance'], path_breaks['time_with_breaks'],
                  c='red', s=50, zorder=5, alpha=0.5)

    ax.set_xlabel('Cumulative distance (km)', fontsize=12)
    ax.set_ylabel('Total time with breaks (hours)', fontsize=12)
    ax.set_title('Time Progression Along Paths (including breaks)', fontsize=13, fontweight='bold')
    ax.legend(fontsize=8, loc='upper left')
    ax.grid(True, alpha=0.3)

    # 4. Break type and charging type distribution
    ax = axes[1, 1]

    # Count by event type
    event_counts = df.groupby(['event_type', 'charging_type']).size().reset_index(name='count')

    x_pos = np.arange(len(event_counts))
    colors = ['#2E86AB' if ct == 'fast' else '#A23B72' for ct in event_counts['charging_type']]
    bars = ax.bar(x_pos, event_counts['count'], color=colors, alpha=0.7, edgecolor='black')

    ax.set_xticks(x_pos)
    ax.set_xticklabels([f"{row['event_type']}\n({row['charging_type']})"
                        for _, row in event_counts.iterrows()], fontsize=10)
    ax.set_ylabel('Count', fontsize=12)
    ax.set_title('Break Types and Charging Distribution', fontsize=13, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')

    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}',
                ha='center', va='bottom', fontsize=11, fontweight='bold')

    plt.tight_layout()

    # Save figure
    output_file = CASE_DIR / "mandatory_breaks_validation.pdf"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\n✓ Visualization saved to: {output_file}")

    return fig


def plot_individual_paths(df):
    """Create detailed plots for individual paths showing break positions."""
    paths = df['path_id'].unique()
    n_paths = len(paths)

    fig, axes = plt.subplots(n_paths, 2, figsize=(15, 4*n_paths))
    if n_paths == 1:
        axes = axes.reshape(1, -1)

    fig.suptitle('Individual Path Analysis', fontsize=16, fontweight='bold')

    for i, path_id in enumerate(paths):
        path_breaks = df[df['path_id'] == path_id].sort_values('break_number')

        # Left plot: Distance progression
        ax_dist = axes[i, 0]

        # Plot driving segments
        distances = [0] + list(path_breaks['cumulative_distance'])
        driving_times = [0] + list(path_breaks['cumulative_driving_time'])

        ax_dist.plot(distances, driving_times, 'b-', linewidth=2, label='Driving time')
        ax_dist.scatter(path_breaks['cumulative_distance'], path_breaks['cumulative_driving_time'],
                       c='red', s=100, zorder=5, label='Break locations', marker='s')

        # Add break annotations
        for _, row in path_breaks.iterrows():
            ax_dist.annotate(f"B{row['break_number']}\n({row['event_type']})",
                           xy=(row['cumulative_distance'], row['cumulative_driving_time']),
                           xytext=(10, 10), textcoords='offset points',
                           fontsize=8, bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))

        ax_dist.set_xlabel('Cumulative distance (km)', fontsize=11)
        ax_dist.set_ylabel('Cumulative driving time (hours)', fontsize=11)
        ax_dist.set_title(f'Path {path_id}: Distance vs Driving Time\n'
                         f'(Length: {path_breaks.iloc[0]["path_length"]:.0f} km, '
                         f'Drivers: {path_breaks.iloc[0]["num_drivers"]})',
                         fontsize=12, fontweight='bold')
        ax_dist.legend()
        ax_dist.grid(True, alpha=0.3)

        # Right plot: Time with breaks
        ax_time = axes[i, 1]

        # Create timeline showing driving + break periods
        timeline_x = [0]
        timeline_y = [0]

        for _, row in path_breaks.iterrows():
            # Add driving segment
            timeline_x.append(row['cumulative_distance'])
            timeline_y.append(row['cumulative_driving_time'])

            # Add break segment (horizontal line - distance doesn't change)
            timeline_x.append(row['cumulative_distance'])
            timeline_y.append(row['time_with_breaks'])

        # Add final segment to destination
        total_length = path_breaks.iloc[0]['path_length']
        total_time = path_breaks.iloc[0]['total_driving_time']
        timeline_x.append(total_length)
        timeline_y.append(timeline_y[-1] + (total_time - path_breaks.iloc[-1]['cumulative_driving_time']))

        ax_time.plot(timeline_x, timeline_y, 'g-', linewidth=2, label='Total time (driving + breaks)')

        # Mark break periods
        for _, row in path_breaks.iterrows():
            ax_time.plot([row['cumulative_distance'], row['cumulative_distance']],
                        [row['cumulative_driving_time'], row['time_with_breaks']],
                        'r-', linewidth=4, alpha=0.5, label='Break' if _ == path_breaks.index[0] else '')

        ax_time.set_xlabel('Cumulative distance (km)', fontsize=11)
        ax_time.set_ylabel('Total time (hours)', fontsize=11)
        ax_time.set_title(f'Path {path_id}: Total Time Including Breaks\n'
                         f'(Total: {total_time:.2f}h driving + breaks)',
                         fontsize=12, fontweight='bold')
        ax_time.legend()
        ax_time.grid(True, alpha=0.3)

    plt.tight_layout()

    # Save figure
    output_file = CASE_DIR / "mandatory_breaks_individual_paths.pdf"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Individual path analysis saved to: {output_file}")

    return fig


def generate_summary_statistics(df):
    """Generate summary statistics for the mandatory breaks."""
    print("\n" + "="*80)
    print("SUMMARY STATISTICS")
    print("="*80)

    print(f"\nTotal paths with breaks: {df['path_id'].nunique()}")
    print(f"Total mandatory breaks: {len(df)}")
    print(f"  - Type B (short breaks): {len(df[df['event_type'] == 'B'])}")
    print(f"  - Type R (rest periods): {len(df[df['event_type'] == 'R'])}")

    print(f"\nCharging type distribution:")
    print(f"  - Fast charging: {len(df[df['charging_type'] == 'fast'])}")
    print(f"  - Slow charging: {len(df[df['charging_type'] == 'slow'])}")

    print(f"\nPath characteristics:")
    path_summary = df.groupby('path_id').agg({
        'path_length': 'first',
        'total_driving_time': 'first',
        'num_drivers': 'first',
        'break_number': 'max'
    })

    print(f"  Average path length: {path_summary['path_length'].mean():.1f} km (range: {path_summary['path_length'].min():.0f}-{path_summary['path_length'].max():.0f})")
    print(f"  Average driving time: {path_summary['total_driving_time'].mean():.2f} h (range: {path_summary['total_driving_time'].min():.2f}-{path_summary['total_driving_time'].max():.2f})")
    print(f"  Average breaks per path: {path_summary['break_number'].mean():.1f} (range: {path_summary['break_number'].min():.0f}-{path_summary['break_number'].max():.0f})")

    print(f"\nDriver distribution:")
    driver_counts = path_summary['num_drivers'].value_counts().sort_index()
    for drivers, count in driver_counts.items():
        print(f"  {drivers} driver(s): {count} paths")


def main():
    """Main validation workflow."""
    print("="*80)
    print("MANDATORY BREAKS VALIDATION AND VISUALIZATION")
    print("="*80)
    print(f"\nCase directory: {CASE_DIR}")

    # Load data
    print("\nLoading data...")
    df = load_mandatory_breaks()
    print(f"✓ Loaded {len(df)} mandatory breaks from {df['path_id'].nunique()} paths")

    # Generate summary statistics
    generate_summary_statistics(df)

    # Validate break timing
    validation_df = validate_break_timing(df)

    # Check validation results
    print("\n" + "="*80)
    print("VALIDATION RESULTS")
    print("="*80)
    timing_ok = validation_df['timing_ok'].sum()
    duration_ok = validation_df['duration_ok'].sum()
    total = len(validation_df)

    print(f"\nTiming validation: {timing_ok}/{total} breaks have correct intervals")
    print(f"Duration validation: {duration_ok}/{total} breaks have correct durations")

    if timing_ok == total and duration_ok == total:
        print("\n✓ ALL VALIDATIONS PASSED!")
    else:
        print("\n✗ SOME VALIDATIONS FAILED - review output above")

    # Create visualizations
    print("\n" + "="*80)
    print("CREATING VISUALIZATIONS")
    print("="*80)

    plot_break_intervals(df)
    plot_individual_paths(df)

    print("\n" + "="*80)
    print("VALIDATION COMPLETE")
    print("="*80)
    print("\nPlots have been saved to the case directory.")


if __name__ == "__main__":
    main()
