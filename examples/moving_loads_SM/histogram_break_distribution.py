"""
Create histogram of break distribution by driving time.

Shows the distribution of first breaks across different time intervals.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import yaml
import os


def create_break_histogram(case_name="case_20251028_091344_var_var", break_number=1):
    """
    Create histogram of break distribution by driving time.

    Parameters:
    -----------
    case_name : str
        Name of the case to analyze
    break_number : int
        Which break to analyze (1 = first, 2 = second, etc.)
    """

    # Load input data
    input_folder = os.path.join(os.getcwd(), "input_data", case_name)

    input_data = {}
    for file_name in os.listdir(input_folder):
        if file_name.endswith(".yaml"):
            key_name = os.path.splitext(file_name)[0]
            with open(os.path.join(input_folder, file_name)) as file:
                input_data[key_name] = yaml.safe_load(file)

    if 'MandatoryBreaks' not in input_data:
        print("ERROR: No MandatoryBreaks found in input data!")
        return

    # Load mandatory breaks
    breaks = input_data['MandatoryBreaks']
    df_breaks = pd.DataFrame(breaks)

    # Filter for specified break number
    df_filtered = df_breaks[df_breaks['break_number'] == break_number].copy()

    print("="*80)
    print(f"BREAK DISTRIBUTION HISTOGRAM - break_number = {break_number}")
    print(f"Case: {case_name}")
    print("="*80)
    print(f"\nTotal routes: {len(df_filtered)}")
    print(f"Driving time to break {break_number}:")
    print(f"  Mean: {df_filtered['cumulative_driving_time'].mean():.3f} hours")
    print(f"  Median: {df_filtered['cumulative_driving_time'].median():.3f} hours")
    print(f"  Min: {df_filtered['cumulative_driving_time'].min():.3f} hours")
    print(f"  Max: {df_filtered['cumulative_driving_time'].max():.3f} hours")
    print(f"  Std: {df_filtered['cumulative_driving_time'].std():.3f} hours")

    # Count how many are exactly 0
    zero_count = (df_filtered['cumulative_driving_time'] == 0).sum()
    print(f"\nBreaks at exactly 0 hours: {zero_count} ({100*zero_count/len(df_filtered):.1f}%)")

    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    # Histogram 1: Full range with fine bins
    bins1 = np.arange(0, df_filtered['cumulative_driving_time'].max() + 0.25, 0.25)
    counts1, edges1, patches1 = ax1.hist(df_filtered['cumulative_driving_time'],
                                         bins=bins1,
                                         edgecolor='black',
                                         alpha=0.7,
                                         color='steelblue')

    # Add 4.5h reference line
    ax1.axvline(x=4.5, color='red', linestyle='--', linewidth=2,
                label='4.5h legal limit', alpha=0.7)

    ax1.set_xlabel('Driving Time to Break (hours)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Number of Routes', fontsize=12, fontweight='bold')
    ax1.set_title(f'Break Distribution - break_number = {break_number}\n'
                  f'Full Range (bins = 0.25h)',
                  fontsize=13, fontweight='bold')
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3, axis='y')

    # Add statistics box
    stats_text = f'n = {len(df_filtered)}\n'
    stats_text += f'Mean = {df_filtered["cumulative_driving_time"].mean():.2f}h\n'
    stats_text += f'Median = {df_filtered["cumulative_driving_time"].median():.2f}h\n'
    stats_text += f'Max = {df_filtered["cumulative_driving_time"].max():.2f}h\n'
    stats_text += f'At 0h = {zero_count} ({100*zero_count/len(df_filtered):.1f}%)'

    ax1.text(0.98, 0.97, stats_text,
             transform=ax1.transAxes,
             fontsize=10,
             verticalalignment='top',
             horizontalalignment='right',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    # Histogram 2: Zoomed in (excluding 0, showing 0-5 hours)
    df_nonzero = df_filtered[df_filtered['cumulative_driving_time'] > 0].copy()
    df_zoom = df_nonzero[df_nonzero['cumulative_driving_time'] <= 5].copy()

    if len(df_zoom) > 0:
        bins2 = np.arange(0, 5.25, 0.25)
        counts2, edges2, patches2 = ax2.hist(df_zoom['cumulative_driving_time'],
                                            bins=bins2,
                                            edgecolor='black',
                                            alpha=0.7,
                                            color='coral')

        # Add 4.5h reference line
        ax2.axvline(x=4.5, color='red', linestyle='--', linewidth=2,
                    label='4.5h legal limit', alpha=0.7)

        ax2.set_xlabel('Driving Time to Break (hours)', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Number of Routes', fontsize=12, fontweight='bold')
        ax2.set_title(f'Break Distribution - break_number = {break_number}\n'
                      f'Zoomed (0-5h, excluding 0h, bins = 0.25h)',
                      fontsize=13, fontweight='bold')
        ax2.legend(fontsize=10)
        ax2.grid(True, alpha=0.3, axis='y')
        ax2.set_xlim(0, 5)

        # Add statistics box for zoomed view
        stats_text2 = f'n = {len(df_zoom)} (excl. 0h)\n'
        stats_text2 += f'Mean = {df_zoom["cumulative_driving_time"].mean():.2f}h\n'
        stats_text2 += f'Median = {df_zoom["cumulative_driving_time"].median():.2f}h\n'
        stats_text2 += f'> 4.5h = {(df_zoom["cumulative_driving_time"] > 4.5).sum()}'

        ax2.text(0.98, 0.97, stats_text2,
                 transform=ax2.transAxes,
                 fontsize=10,
                 verticalalignment='top',
                 horizontalalignment='right',
                 bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))

    plt.tight_layout()

    # Save figure
    os.makedirs('figures', exist_ok=True)
    output_path = f'figures/break_distribution_histogram_break{break_number}.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\nFigure saved to: {output_path}")

    plt.show()

    # Print detailed distribution
    print("\n" + "="*80)
    print("DETAILED DISTRIBUTION")
    print("="*80)

    bins_analysis = [0, 0.01, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 6.0, 7.0, 8.0, 10.0, 100.0]
    df_filtered['time_bin'] = pd.cut(df_filtered['cumulative_driving_time'],
                                      bins=bins_analysis,
                                      include_lowest=True)
    time_dist = df_filtered['time_bin'].value_counts().sort_index()

    print(f"\nDistribution by time intervals:")
    for interval, count in time_dist.items():
        pct = 100 * count / len(df_filtered)
        print(f"  {interval}: {count:4d} routes ({pct:5.1f}%)")

    return df_filtered


if __name__ == "__main__":
    # Create histogram for break_number = 1
    df_break1 = create_break_histogram(break_number=1)

    # Also create for break_number = 2 for comparison
    print("\n\n")
    df_break2 = create_break_histogram(break_number=2)
