"""
HISTOGRAM: First Break Total Stop Time Distribution
Add this cell to break_times.ipynb
"""

# ==============================================================================
# HISTOGRAM: FIRST BREAK TOTAL STOP TIME FREQUENCY
# ==============================================================================
import matplotlib.pyplot as plt
import numpy as np

fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# ==============================================================================
# PLOT 1: Total Stop Time Distribution (Main histogram)
# ==============================================================================
ax1 = axes[0, 0]

# Create histogram
n, bins, patches = ax1.hist(df_timing["total_stop_time"],
                            bins=50,
                            color='steelblue',
                            alpha=0.7,
                            edgecolor='black',
                            linewidth=0.5)

# Color coding based on regulatory threshold (0.75h = 45 min)
for i, patch in enumerate(patches):
    if bins[i] < 0.75:
        patch.set_facecolor('coral')  # Below minimum (non-compliant)
        patch.set_alpha(0.6)
    elif bins[i] < 2.0:
        patch.set_facecolor('steelblue')  # Normal range
        patch.set_alpha(0.7)
    else:
        patch.set_facecolor('orange')  # Long stops (might be charging)
        patch.set_alpha(0.7)

# Add vertical line at regulatory minimum (45 min)
ax1.axvline(x=0.75, color='red', linestyle='--', linewidth=2.5,
           label='EU 45 min minimum', zorder=10)

# Add mean and median lines
mean_val = df_timing["total_stop_time"].mean()
median_val = df_timing["total_stop_time"].median()
ax1.axvline(x=mean_val, color='darkgreen', linestyle='-', linewidth=2,
           label=f'Mean: {mean_val:.2f}h ({mean_val*60:.0f} min)', zorder=10)
ax1.axvline(x=median_val, color='purple', linestyle='-.', linewidth=2,
           label=f'Median: {median_val:.2f}h ({median_val*60:.0f} min)', zorder=10)

ax1.set_xlabel('Total Stop Time at First Break (hours)', fontsize=12, fontweight='bold')
ax1.set_ylabel('Frequency (Number of Routes)', fontsize=12, fontweight='bold')
ax1.set_title(f'Distribution of First Break Total Stop Time\n(n={len(df_timing)} routes)',
             fontsize=13, fontweight='bold')
ax1.legend(loc='upper right', fontsize=10)
ax1.grid(True, alpha=0.3, axis='y')

# Add text box with statistics
stats_text = f"""Statistics:
Min: {df_timing["total_stop_time"].min():.2f}h ({df_timing["total_stop_time"].min()*60:.0f} min)
Max: {df_timing["total_stop_time"].max():.2f}h ({df_timing["total_stop_time"].max()*60:.0f} min)
Std: {df_timing["total_stop_time"].std():.2f}h
< 45 min: {len(df_timing[df_timing["total_stop_time"] < 0.75])} ({len(df_timing[df_timing["total_stop_time"] < 0.75])/len(df_timing)*100:.1f}%)
> 2h: {len(df_timing[df_timing["total_stop_time"] > 2])} ({len(df_timing[df_timing["total_stop_time"] > 2])/len(df_timing)*100:.1f}%)"""

ax1.text(0.98, 0.97, stats_text,
        transform=ax1.transAxes,
        verticalalignment='top',
        horizontalalignment='right',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
        fontsize=9,
        family='monospace')

# ==============================================================================
# PLOT 2: Log Scale Histogram (to see long tail)
# ==============================================================================
ax2 = axes[0, 1]

ax2.hist(df_timing["total_stop_time"],
        bins=50,
        color='coral',
        alpha=0.7,
        edgecolor='black',
        linewidth=0.5)

ax2.set_yscale('log')
ax2.axvline(x=0.75, color='red', linestyle='--', linewidth=2.5,
           label='EU 45 min minimum')
ax2.axvline(x=mean_val, color='darkgreen', linestyle='-', linewidth=2,
           label=f'Mean: {mean_val:.2f}h')
ax2.axvline(x=median_val, color='purple', linestyle='-.', linewidth=2,
           label=f'Median: {median_val:.2f}h')

ax2.set_xlabel('Total Stop Time (hours)', fontsize=12, fontweight='bold')
ax2.set_ylabel('Frequency (log scale)', fontsize=12, fontweight='bold')
ax2.set_title('Distribution with Log Scale\n(Shows long tail)',
             fontsize=13, fontweight='bold')
ax2.legend(loc='upper right', fontsize=10)
ax2.grid(True, alpha=0.3, which='both')

# ==============================================================================
# PLOT 3: Break Time vs Charging Time Breakdown
# ==============================================================================
ax3 = axes[1, 0]

# Create side-by-side histograms for break and charging components
bins_time = np.linspace(0, max(df_timing["total_stop_time"].max(),
                               df_timing["actual_break_duration"].max()), 40)

ax3.hist(df_timing["actual_break_duration"], bins=bins_time,
        alpha=0.6, label='Break Duration (mandatory + slack)',
        color='steelblue', edgecolor='black', linewidth=0.5)

# Only plot charging if there are routes with charging
if df_timing["charging_time"].max() > 0:
    ax3.hist(df_timing["charging_time"], bins=bins_time,
            alpha=0.6, label='Charging Time',
            color='orange', edgecolor='black', linewidth=0.5)

ax3.axvline(x=0.75, color='red', linestyle='--', linewidth=2.5,
           label='EU 45 min minimum')

ax3.set_xlabel('Time (hours)', fontsize=12, fontweight='bold')
ax3.set_ylabel('Frequency', fontsize=12, fontweight='bold')
ax3.set_title('Break vs Charging Time Components', fontsize=13, fontweight='bold')
ax3.legend(loc='upper right', fontsize=10)
ax3.grid(True, alpha=0.3, axis='y')

# ==============================================================================
# PLOT 4: Cumulative Distribution Function (CDF)
# ==============================================================================
ax4 = axes[1, 1]

# Sort data for CDF
sorted_times = np.sort(df_timing["total_stop_time"])
cumulative = np.arange(1, len(sorted_times) + 1) / len(sorted_times) * 100

ax4.plot(sorted_times, cumulative, linewidth=2.5, color='steelblue')
ax4.fill_between(sorted_times, cumulative, alpha=0.3, color='steelblue')

# Mark key percentiles
percentiles = [25, 50, 75, 90, 95]
for p in percentiles:
    val = np.percentile(df_timing["total_stop_time"], p)
    ax4.axvline(x=val, color='gray', linestyle=':', linewidth=1.5, alpha=0.7)
    ax4.text(val, 5, f'P{p}\n{val:.2f}h',
            rotation=90, verticalalignment='bottom',
            fontsize=8, bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))

# Regulatory minimum
ax4.axvline(x=0.75, color='red', linestyle='--', linewidth=2.5,
           label='EU 45 min minimum')

# Mark what percentage is below minimum
pct_below = len(df_timing[df_timing["total_stop_time"] < 0.75]) / len(df_timing) * 100
ax4.axhline(y=pct_below, color='red', linestyle=':', linewidth=1.5, alpha=0.5)
ax4.text(ax4.get_xlim()[1]*0.7, pct_below + 2,
        f'{pct_below:.1f}% below 45 min',
        fontsize=9, bbox=dict(boxstyle='round', facecolor='pink', alpha=0.7))

ax4.set_xlabel('Total Stop Time (hours)', fontsize=12, fontweight='bold')
ax4.set_ylabel('Cumulative Percentage (%)', fontsize=12, fontweight='bold')
ax4.set_title('Cumulative Distribution Function (CDF)', fontsize=13, fontweight='bold')
ax4.legend(loc='lower right', fontsize=10)
ax4.grid(True, alpha=0.3)
ax4.set_ylim(0, 100)

plt.tight_layout()
plt.savefig('first_break_stop_time_histogram.png', dpi=300, bbox_inches='tight')
plt.show()

# ==============================================================================
# PRINT DETAILED STATISTICS
# ==============================================================================
print("="*80)
print("FIRST BREAK STOP TIME - DETAILED STATISTICS")
print("="*80)

print(f"\nOverall statistics (n={len(df_timing)} routes):")
print(f"  Mean: {mean_val:.3f}h ({mean_val*60:.1f} min)")
print(f"  Median: {median_val:.3f}h ({median_val*60:.1f} min)")
print(f"  Std Dev: {df_timing['total_stop_time'].std():.3f}h ({df_timing['total_stop_time'].std()*60:.1f} min)")
print(f"  Min: {df_timing['total_stop_time'].min():.3f}h ({df_timing['total_stop_time'].min()*60:.1f} min)")
print(f"  Max: {df_timing['total_stop_time'].max():.3f}h ({df_timing['total_stop_time'].max()*60:.1f} min)")

print(f"\nPercentiles:")
for p in [10, 25, 50, 75, 90, 95, 99]:
    val = np.percentile(df_timing["total_stop_time"], p)
    print(f"  P{p:2d}: {val:.3f}h ({val*60:.1f} min)")

print(f"\nCompliance with EU regulations:")
below_min = df_timing[df_timing["total_stop_time"] < 0.75]
at_or_above = df_timing[df_timing["total_stop_time"] >= 0.75]
print(f"  Below 45 min: {len(below_min):4d} ({len(below_min)/len(df_timing)*100:5.1f}%) - NON-COMPLIANT")
print(f"  At/above 45 min: {len(at_or_above):4d} ({len(at_or_above)/len(df_timing)*100:5.1f}%) - COMPLIANT")

print(f"\nStop time ranges:")
ranges = [
    (0, 0.5, "< 30 min"),
    (0.5, 0.75, "30-45 min"),
    (0.75, 1.0, "45-60 min (minimal compliance)"),
    (1.0, 2.0, "1-2 hours (normal)"),
    (2.0, 5.0, "2-5 hours (with charging)"),
    (5.0, 10.0, "5-10 hours (long charging)"),
    (10.0, float('inf'), "> 10 hours (very long)")
]

for low, high, desc in ranges:
    in_range = df_timing[(df_timing["total_stop_time"] >= low) &
                         (df_timing["total_stop_time"] < high)]
    if len(in_range) > 0:
        print(f"  {desc:30s}: {len(in_range):4d} ({len(in_range)/len(df_timing)*100:5.1f}%)")

print(f"\nBreak vs Charging breakdown:")
print(f"  Routes with charging (>0.01h): {len(df_timing[df_timing['charging_time'] > 0.01]):4d} "
      f"({len(df_timing[df_timing['charging_time'] > 0.01])/len(df_timing)*100:5.1f}%)")
print(f"  Routes without charging: {len(df_timing[df_timing['charging_time'] <= 0.01]):4d} "
      f"({len(df_timing[df_timing['charging_time'] <= 0.01])/len(df_timing)*100:5.1f}%)")

if len(df_timing[df_timing['charging_time'] > 0.01]) > 0:
    charging_routes = df_timing[df_timing['charging_time'] > 0.01]
    print(f"\nFor routes WITH charging:")
    print(f"  Avg break time: {charging_routes['actual_break_duration'].mean():.3f}h ({charging_routes['actual_break_duration'].mean()*60:.1f} min)")
    print(f"  Avg charging time: {charging_routes['charging_time'].mean():.3f}h ({charging_routes['charging_time'].mean()*60:.1f} min)")
    print(f"  Avg total stop: {charging_routes['total_stop_time'].mean():.3f}h ({charging_routes['total_stop_time'].mean()*60:.1f} min)")

if len(df_timing[df_timing['charging_time'] <= 0.01]) > 0:
    no_charging = df_timing[df_timing['charging_time'] <= 0.01]
    print(f"\nFor routes WITHOUT charging:")
    print(f"  Avg break time: {no_charging['actual_break_duration'].mean():.3f}h ({no_charging['actual_break_duration'].mean()*60:.1f} min)")
    print(f"  Avg total stop: {no_charging['total_stop_time'].mean():.3f}h ({no_charging['total_stop_time'].mean()*60:.1f} min)")

print("\n" + "="*80)
print("Plot saved as 'first_break_stop_time_histogram.png'")
print("="*80)
