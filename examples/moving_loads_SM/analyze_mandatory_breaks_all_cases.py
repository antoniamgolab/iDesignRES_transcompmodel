"""
Analyze Mandatory Breaks Structure from Input Data for All Cases

This script analyzes the planned break patterns from the input data structure,
showing trip duration vs break duration for all scenarios.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


def analyze_mandatory_breaks_for_all_cases(loaded_runs, case_study_name_labels):
    """
    Analyzes mandatory breaks from input data for all loaded cases.

    Parameters:
    -----------
    loaded_runs : dict
        Dictionary with case_name keys containing 'input_data' and 'output_data'
    case_study_name_labels : dict
        Dictionary mapping case names to display labels

    Returns:
    --------
    fig : matplotlib.figure.Figure
        The figure with all subplots
    all_stats : dict
        Dictionary of statistics for each case
    """

    n_cases = len(loaded_runs)

    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    axes = axes.flatten()

    all_stats = {}

    for idx, (case_name, case_data) in enumerate(loaded_runs.items()):
        input_data = case_data['input_data']

        # Get the display label
        case_label = case_study_name_labels.get(case_name, case_name)

        # Load mandatory breaks from input data
        if 'MandatoryBreaks' not in input_data:
            print(f"WARNING: No MandatoryBreaks found in {case_name}")
            continue

        breaks = input_data["MandatoryBreaks"]
        df_breaks = pd.DataFrame(breaks)

        # Filter for second break (break_number == 2) - the first break AFTER driving starts
        # Note: break_number == 1 is typically at route origin (cumulative_driving_time = 0)
        df_breaks_filtered = df_breaks[df_breaks['break_number'] == 2].copy()

        # Calculate trip duration (driving time from route start to first ACTUAL break after driving)
        trip_data = []

        for _, row in df_breaks_filtered.iterrows():
            # For first break, trip_duration is just the cumulative_driving_time
            trip_duration = row['cumulative_driving_time']

            # Determine break duration based on event type
            if row['event_type'] == 'B':
                break_duration = 0.75  # 45 minutes
            else:  # 'R'
                break_duration = 9.0  # 9 hours

            trip_data.append({
                'path_id': row['path_id'],
                'path_length': row['path_length'],
                'break_number': row['break_number'],
                'trip_duration': trip_duration,
                'break_duration': break_duration,
                'event_type': row['event_type'],
                'charging_type': row.get('charging_type', 'unknown'),
                'cumulative_distance': row['cumulative_distance'],
                'num_drivers': row.get('num_drivers', 1)
            })

        df_trips = pd.DataFrame(trip_data)

        # Calculate statistics
        stats = {
            'total_breaks': len(df_trips),
            'short_breaks': len(df_trips[df_trips['event_type'] == 'B']),
            'rest_periods': len(df_trips[df_trips['event_type'] == 'R']),
            'avg_trip_duration': df_trips['trip_duration'].mean(),
            'max_trip_duration': df_trips['trip_duration'].max(),
            'fast_charging': len(df_trips[df_trips['charging_type'] == 'fast']),
            'slow_charging': len(df_trips[df_trips['charging_type'] == 'slow']),
        }

        all_stats[case_name] = stats

        # Plot on the corresponding subplot
        ax = axes[idx]

        # Separate short breaks and rest periods
        short_breaks = df_trips[df_trips['event_type'] == 'B']
        rest_periods = df_trips[df_trips['event_type'] == 'R']

        # Plot with different markers for charging type
        for charging in ['fast', 'slow']:
            sb_charging = short_breaks[short_breaks['charging_type'] == charging]
            rp_charging = rest_periods[rest_periods['charging_type'] == charging]

            if len(sb_charging) > 0:
                marker = 'o' if charging == 'fast' else 's'
                label = f'Short break ({charging})'
                ax.scatter(sb_charging['trip_duration'], sb_charging['break_duration'],
                          s=80, alpha=0.5, marker=marker, label=label)

            if len(rp_charging) > 0:
                marker = '^' if charging == 'fast' else 'v'
                label = f'Rest period ({charging})'
                ax.scatter(rp_charging['trip_duration'], rp_charging['break_duration'],
                          s=80, alpha=0.5, marker=marker, label=label)

        # Add 4.5 hour reference line (legal driving limit)
        ax.axvline(x=4.5, color='red', linestyle='--', linewidth=2,
                   label='4.5h legal limit', alpha=0.7)

        ax.set_xlabel('Driving Time to First Break (hours)', fontsize=11)
        ax.set_ylabel('Break Duration (hours)', fontsize=11)
        ax.set_title(f'{case_label}\n{stats["total_breaks"]} routes (2nd break = 1st after driving)',
                    fontsize=12, fontweight='bold')
        ax.legend(loc='best', fontsize=9)
        ax.grid(True, alpha=0.3)

        # Set y-axis to show both break durations clearly
        ax.set_ylim(-0.5, 10)

    plt.tight_layout()

    # Print summary statistics
    print("="*80)
    print("MANDATORY BREAKS ANALYSIS - FIRST BREAK AFTER DRIVING (ALL CASES)")
    print("Note: break_number=2 is the first break after driving starts")
    print("(break_number=1 is typically at route origin with 0 driving time)")
    print("="*80)
    for case_name, stats in all_stats.items():
        case_label = case_study_name_labels.get(case_name, case_name)
        print(f"\n{case_label}:")
        print(f"  Total routes analyzed: {stats['total_breaks']}")
        print(f"  - First break is short (0.75h): {stats['short_breaks']} routes")
        print(f"  - First break is rest (9h): {stats['rest_periods']} routes")
        print(f"  Average driving time to first break: {stats['avg_trip_duration']:.2f}h")
        print(f"  Maximum driving time to first break: {stats['max_trip_duration']:.2f}h")
        print(f"  Fast charging at first break: {stats['fast_charging']} routes")
        print(f"  Slow charging at first break: {stats['slow_charging']} routes")

    return fig, all_stats


# Example usage (to be called from notebook):
# fig, stats = analyze_mandatory_breaks_for_all_cases(loaded_runs, case_study_name_labels)
# plt.savefig('mandatory_breaks_all_cases.png', dpi=300, bbox_inches='tight')
# plt.show()
