"""
Visualize the distribution of mandatory breaks after fixes.
Shows:
- Histogram of break timing
- Break timing vs route length
- Before/after comparison (if old data available)
"""

import yaml
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

def load_latest_case():
    """Find and load the most recent case."""
    input_dir = Path("input_data")
    case_dirs = sorted(input_dir.glob("case_*"))
    if not case_dirs:
        print("ERROR: No case directories found!")
        return None, None

    latest = case_dirs[-1]
    print(f"Loading case: {latest.name}")
    return latest, latest.name

def load_data(case_dir):
    """Load MandatoryBreaks and Path data."""
    with open(case_dir / "MandatoryBreaks.yaml") as f:
        breaks = yaml.safe_load(f)

    with open(case_dir / "Path.yaml") as f:
        paths = yaml.safe_load(f)

    return pd.DataFrame(breaks), pd.DataFrame(paths)

def create_visualizations(df_breaks, df_paths, case_name):
    """Create comprehensive break distribution visualizations."""

    # Create figure directory
    os.makedirs('figures', exist_ok=True)

    print("\n" + "="*80)
    print("MANDATORY BREAKS ANALYSIS")
    print("="*80)

    # Basic statistics
    print(f"\nTotal breaks: {len(df_breaks)}")
    print(f"Total paths: {len(df_paths)}")
    print(f"Average breaks per path: {len(df_breaks)/len(df_paths):.2f}")

    # Analyze break distribution
    print(f"\nBreak timing statistics:")
    print(f"  Mean: {df_breaks['cumulative_driving_time'].mean():.2f}h")
    print(f"  Median: {df_breaks['cumulative_driving_time'].median():.2f}h")
    print(f"  Min: {df_breaks['cumulative_driving_time'].min():.2f}h")
    print(f"  Max: {df_breaks['cumulative_driving_time'].max():.2f}h")

    # Count breaks at origin
    breaks_at_origin = (df_breaks['cumulative_driving_time'] == 0).sum()
    print(f"\nBreaks at origin (0h): {breaks_at_origin} ({100*breaks_at_origin/len(df_breaks):.1f}%)")

    # Check if fix worked
    if breaks_at_origin < len(df_breaks) * 0.1:
        print("✓ FIX SUCCESSFUL: Most breaks are not at origin!")
    else:
        print("✗ WARNING: Many breaks still at origin!")

    # Create 2x2 subplot figure
    fig = plt.figure(figsize=(16, 12))

    # ========================================================================
    # Plot 1: Histogram of all breaks
    # ========================================================================
    ax1 = plt.subplot(2, 2, 1)

    bins = np.arange(0, df_breaks['cumulative_driving_time'].max() + 0.5, 0.5)
    counts, edges, patches = ax1.hist(df_breaks['cumulative_driving_time'],
                                       bins=bins,
                                       edgecolor='black',
                                       alpha=0.7,
                                       color='steelblue')

    # Add reference lines at 4.5h intervals
    for i in range(1, 5):
        target = i * 4.5
        if target <= df_breaks['cumulative_driving_time'].max():
            ax1.axvline(x=target, color='red', linestyle='--', linewidth=1.5,
                       alpha=0.6, label=f'{target}h limit' if i == 1 else '')

    ax1.set_xlabel('Cumulative Driving Time (hours)', fontsize=11, fontweight='bold')
    ax1.set_ylabel('Number of Breaks', fontsize=11, fontweight='bold')
    ax1.set_title('Distribution of All Mandatory Breaks', fontsize=12, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3, axis='y')

    # ========================================================================
    # Plot 2: Histogram excluding origin (0h) breaks
    # ========================================================================
    ax2 = plt.subplot(2, 2, 2)

    df_nonzero = df_breaks[df_breaks['cumulative_driving_time'] > 0].copy()

    if len(df_nonzero) > 0:
        bins2 = np.arange(0, df_nonzero['cumulative_driving_time'].max() + 0.5, 0.5)
        counts2, edges2, patches2 = ax2.hist(df_nonzero['cumulative_driving_time'],
                                             bins=bins2,
                                             edgecolor='black',
                                             alpha=0.7,
                                             color='coral')

        # Add reference lines
        for i in range(1, 5):
            target = i * 4.5
            if target <= df_nonzero['cumulative_driving_time'].max():
                ax2.axvline(x=target, color='red', linestyle='--', linewidth=1.5,
                           alpha=0.6)

        ax2.set_xlabel('Cumulative Driving Time (hours)', fontsize=11, fontweight='bold')
        ax2.set_ylabel('Number of Breaks', fontsize=11, fontweight='bold')
        ax2.set_title('Breaks After Driving Started (excluding 0h)', fontsize=12, fontweight='bold')
        ax2.grid(True, alpha=0.3, axis='y')

    # ========================================================================
    # Plot 3: Break timing vs path length
    # ========================================================================
    ax3 = plt.subplot(2, 2, 3)

    # Merge breaks with path data
    df_merged = df_breaks.merge(df_paths[['id', 'length']],
                                  left_on='path_id',
                                  right_on='id',
                                  how='left')

    # Scatter plot
    scatter = ax3.scatter(df_merged['length'],
                          df_merged['cumulative_driving_time'],
                          c=df_merged['break_number'],
                          cmap='viridis',
                          alpha=0.6,
                          s=30)

    # Add reference lines
    x_max = df_merged['length'].max()
    for i in range(1, 5):
        target_time = i * 4.5
        target_dist = target_time * 80  # 80 km/h
        if target_dist <= x_max:
            ax3.axhline(y=target_time, color='red', linestyle='--',
                       linewidth=1, alpha=0.4)
            ax3.axvline(x=target_dist, color='blue', linestyle=':',
                       linewidth=1, alpha=0.4)

    ax3.set_xlabel('Path Length (km)', fontsize=11, fontweight='bold')
    ax3.set_ylabel('Cumulative Driving Time to Break (hours)', fontsize=11, fontweight='bold')
    ax3.set_title('Break Timing vs Route Length', fontsize=12, fontweight='bold')
    ax3.grid(True, alpha=0.3)

    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax3)
    cbar.set_label('Break Number', fontsize=10)

    # ========================================================================
    # Plot 4: Distribution by break number
    # ========================================================================
    ax4 = plt.subplot(2, 2, 4)

    # Group by break number
    break_numbers = sorted(df_breaks['break_number'].unique())

    for bn in break_numbers[:5]:  # Show first 5 break numbers
        df_bn = df_breaks[df_breaks['break_number'] == bn]
        ax4.hist(df_bn['cumulative_driving_time'],
                bins=20,
                alpha=0.5,
                label=f'Break {bn} (n={len(df_bn)})',
                edgecolor='black')

    # Add reference lines
    for i in range(1, 5):
        target = i * 4.5
        ax4.axvline(x=target, color='red', linestyle='--',
                   linewidth=1.5, alpha=0.6)

    ax4.set_xlabel('Cumulative Driving Time (hours)', fontsize=11, fontweight='bold')
    ax4.set_ylabel('Number of Breaks', fontsize=11, fontweight='bold')
    ax4.set_title('Distribution by Break Number', fontsize=12, fontweight='bold')
    ax4.legend(fontsize=9)
    ax4.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()

    # Save figure
    output_path = f'figures/mandatory_breaks_distribution_{case_name}.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\nFigure saved: {output_path}")

    plt.show()

    # ========================================================================
    # Additional analysis table
    # ========================================================================
    print("\n" + "="*80)
    print("BREAK TIMING BY BREAK NUMBER")
    print("="*80)

    for bn in sorted(df_breaks['break_number'].unique())[:5]:
        df_bn = df_breaks[df_breaks['break_number'] == bn]
        expected_time = bn * 4.5

        print(f"\nBreak Number {bn} (expected ~{expected_time}h):")
        print(f"  Count: {len(df_bn)}")
        print(f"  Mean time: {df_bn['cumulative_driving_time'].mean():.2f}h")
        print(f"  Median time: {df_bn['cumulative_driving_time'].median():.2f}h")
        print(f"  Std dev: {df_bn['cumulative_driving_time'].std():.2f}h")
        print(f"  Min: {df_bn['cumulative_driving_time'].min():.2f}h")
        print(f"  Max: {df_bn['cumulative_driving_time'].max():.2f}h")

        # Check how many are close to expected
        tolerance = 0.5  # 30 minutes
        close_to_expected = ((df_bn['cumulative_driving_time'] >= expected_time - tolerance) &
                             (df_bn['cumulative_driving_time'] <= expected_time + tolerance)).sum()
        print(f"  Within ±0.5h of expected: {close_to_expected} ({100*close_to_expected/len(df_bn):.1f}%)")


if __name__ == "__main__":
    print("="*80)
    print("MANDATORY BREAKS VISUALIZATION")
    print("="*80)

    # Load latest case
    case_dir, case_name = load_latest_case()
    if case_dir is None:
        exit(1)

    # Load data
    print("\nLoading data...")
    df_breaks, df_paths = load_data(case_dir)

    print(f"  Loaded {len(df_breaks)} breaks")
    print(f"  Loaded {len(df_paths)} paths")

    # Create visualizations
    create_visualizations(df_breaks, df_paths, case_name)

    print("\n" + "="*80)
    print("VISUALIZATION COMPLETE")
    print("="*80)
