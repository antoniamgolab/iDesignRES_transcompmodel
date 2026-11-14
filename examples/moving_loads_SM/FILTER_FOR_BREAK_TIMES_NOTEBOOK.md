# Filtering Routes in break_times.ipynb

## Step 1: Add This Cell BEFORE Your Visualization

```python
# ==============================================================================
# LOAD ROUTE FILTER
# ==============================================================================
import yaml

# Load pre-identified problematic routes (long edges with multiple breaks at same node)
with open('problematic_routes.yaml', 'r') as f:
    problematic_info = yaml.safe_load(f)

problematic_path_ids = set(problematic_info['problematic_paths'])

print("="*80)
print("ROUTE FILTERING")
print("="*80)
print(f"Loaded {len(problematic_path_ids)} problematic routes")
print(f"  - Long edges (>500km avg segment): {problematic_info['stats']['num_long_edge']}")
print(f"  - Multiple breaks at same node: {problematic_info['stats']['num_multi_break']}")
print()

# Create filter function
def is_not_problematic(path_id):
    """Returns True if route should be kept (i.e., not a long-edge problematic route)"""
    return path_id not in problematic_path_ids

# Apply filter to df_timing
df_timing_original = df_timing.copy()  # Keep original for comparison

if 'path_id' in df_timing.columns:
    df_timing_filtered = df_timing[df_timing['path_id'].apply(is_not_problematic)].copy()

    print(f"DataFrame filtering results:")
    print(f"  Original: {len(df_timing_original)} routes")
    print(f"  Filtered: {len(df_timing_filtered)} routes")
    print(f"  Removed: {len(df_timing_original) - len(df_timing_filtered)} routes")
    print()

    # Use filtered DataFrame for visualization
    df_timing = df_timing_filtered
else:
    print("[WARNING] 'path_id' column not found in df_timing")
    print("Available columns:", list(df_timing.columns))
```

## Step 2: If path_id Column Doesn't Exist

If you get a warning about missing `path_id`, add it when you create `df_timing`:

```python
# When creating df_timing, make sure to include path_id
# Example modification:

first_breaks_data = []
for key, value in extra_break_time_data.items():
    if value > 0:
        year, (prod_id, od_id, path_id, geo_id), tv_id, gen = key  # Extract all components

        # ... your existing code ...

        first_breaks_data.append({
            'year': year,
            'path_id': path_id,  # ADD THIS LINE
            'geo_id': geo_id,
            'tv_id': tv_id,
            'cumulative_driving_time': cumulative_driving_time,
            'actual_break_duration': actual_break_duration,
            'charging_time': charging_time,
            'total_stop_time': total_stop_time,
            # ... other fields
        })

df_timing = pd.DataFrame(first_breaks_data)
```

## Step 3: Add Comparison Visualization (Optional)

Show the difference between filtered and unfiltered data:

```python
# ==============================================================================
# COMPARISON: FILTERED vs UNFILTERED
# ==============================================================================

fig, axes = plt.subplots(2, 2, figsize=(18, 14))

# Common plot settings
def plot_break_analysis(ax, df, title_suffix):
    scatter = ax.scatter(df["cumulative_driving_time"],
                        df["total_stop_time"],
                        c=df["year"],
                        cmap="viridis",
                        s=100,
                        alpha=0.3,
                        edgecolors="black",
                        linewidth=0.5)

    # Shading
    ax.axvspan(0, 4.5, alpha=0.1, color="green", zorder=0)
    if df["cumulative_driving_time"].max() > 4.5:
        ax.axvspan(4.5, df["cumulative_driving_time"].max() * 1.05,
                   alpha=0.15, color="red", zorder=0)

    # Regulatory lines
    ax.axvline(x=4.5, color="red", linestyle="--", linewidth=2.5,
               label="EU 4.5h limit", zorder=2)
    ax.axhline(y=0.75, color="orange", linestyle="--", linewidth=2,
               label="EU 45 min minimum", zorder=2)

    ax.set_xlabel("Cumulative Driving Time (hours)", fontsize=11)
    ax.set_ylabel("Total Stop Time (hours)", fontsize=11)
    ax.set_title(f"Break Timing Analysis - {title_suffix}\\nn={len(df)} routes",
                 fontsize=12, fontweight="bold")
    ax.legend(loc="upper left", fontsize=9)
    ax.grid(True, alpha=0.3)

    return scatter

# TOP ROW: Scatter plots
scatter1 = plot_break_analysis(axes[0, 0], df_timing_original, "All Routes")
cbar1 = plt.colorbar(scatter1, ax=axes[0, 0])
cbar1.set_label("Year", rotation=270, labelpad=15)

scatter2 = plot_break_analysis(axes[0, 1], df_timing_filtered, "Filtered (Exclude Long Edges)")
cbar2 = plt.colorbar(scatter2, ax=axes[0, 1])
cbar2.set_label("Year", rotation=270, labelpad=15)

# BOTTOM ROW: Statistics comparison
def plot_statistics(ax, df_orig, df_filt):
    categories = ['Total Routes', 'With Charging', 'Over 4.5h', 'Over 45min Stop']

    orig_values = [
        len(df_orig),
        len(df_orig[df_orig["charging_time"] > 0.01]),
        len(df_orig[df_orig["cumulative_driving_time"] > 4.5]),
        len(df_orig[df_orig["total_stop_time"] > 0.75])
    ]

    filt_values = [
        len(df_filt),
        len(df_filt[df_filt["charging_time"] > 0.01]),
        len(df_filt[df_filt["cumulative_driving_time"] > 4.5]),
        len(df_filt[df_filt["total_stop_time"] > 0.75])
    ]

    x = range(len(categories))
    width = 0.35

    ax.bar([i - width/2 for i in x], orig_values, width, label='All Routes',
           alpha=0.8, color='steelblue')
    ax.bar([i + width/2 for i in x], filt_values, width, label='Filtered',
           alpha=0.8, color='coral')

    ax.set_xlabel('Category', fontsize=11)
    ax.set_ylabel('Count', fontsize=11)
    ax.set_title('Route Count Comparison', fontsize=12, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(categories, rotation=15, ha='right')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')

plot_statistics(axes[1, 0], df_timing_original, df_timing_filtered)

# Distribution comparison
def plot_distribution(ax, df_orig, df_filt):
    ax.hist(df_orig["total_stop_time"], bins=30, alpha=0.5,
            label=f'All Routes (n={len(df_orig)})', color='steelblue')
    ax.hist(df_filt["total_stop_time"], bins=30, alpha=0.5,
            label=f'Filtered (n={len(df_filt)})', color='coral')

    ax.axvline(df_orig["total_stop_time"].mean(), color='steelblue',
               linestyle='--', linewidth=2, label=f'Mean (All): {df_orig["total_stop_time"].mean():.2f}h')
    ax.axvline(df_filt["total_stop_time"].mean(), color='coral',
               linestyle='--', linewidth=2, label=f'Mean (Filtered): {df_filt["total_stop_time"].mean():.2f}h')

    ax.set_xlabel('Total Stop Time (hours)', fontsize=11)
    ax.set_ylabel('Frequency', fontsize=11)
    ax.set_title('Stop Time Distribution Comparison', fontsize=12, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)

plot_distribution(axes[1, 1], df_timing_original, df_timing_filtered)

plt.tight_layout()
plt.savefig("break_timing_filtered_comparison.png", dpi=300, bbox_inches="tight")
plt.show()

print("\\nComparison plot saved as 'break_timing_filtered_comparison.png'")
```

## Step 4: Print Detailed Filtering Stats

```python
# ==============================================================================
# DETAILED FILTERING STATISTICS
# ==============================================================================

print("="*80)
print("DETAILED FILTERING IMPACT")
print("="*80)

# Routes removed
removed_routes = df_timing_original[~df_timing_original['path_id'].apply(is_not_problematic)]

print(f"\\nRemoved routes (long edges):")
print(f"  Count: {len(removed_routes)}")
if len(removed_routes) > 0:
    print(f"  Avg total stop time: {removed_routes['total_stop_time'].mean():.2f}h")
    print(f"  Max total stop time: {removed_routes['total_stop_time'].max():.2f}h")
    print(f"  Avg driving time: {removed_routes['cumulative_driving_time'].mean():.2f}h")
    print(f"  Path IDs: {sorted(removed_routes['path_id'].unique())[:10]}...")

print(f"\\nRetained routes (normal edges):")
print(f"  Count: {len(df_timing_filtered)}")
print(f"  Avg total stop time: {df_timing_filtered['total_stop_time'].mean():.2f}h")
print(f"  Max total stop time: {df_timing_filtered['total_stop_time'].max():.2f}h")
print(f"  Avg driving time: {df_timing_filtered['cumulative_driving_time'].mean():.2f}h")

# Statistical comparison
print(f"\\nStop time statistics:")
print(f"  Original mean: {df_timing_original['total_stop_time'].mean():.2f}h")
print(f"  Filtered mean: {df_timing_filtered['total_stop_time'].mean():.2f}h")
print(f"  Difference: {df_timing_original['total_stop_time'].mean() - df_timing_filtered['total_stop_time'].mean():.2f}h "
      f"({100*(df_timing_original['total_stop_time'].mean() - df_timing_filtered['total_stop_time'].mean())/df_timing_original['total_stop_time'].mean():.1f}%)")
```

## Quick Reference: Filter Modes

```python
# EXCLUDE problematic routes (recommended)
df_timing_filtered = df_timing[df_timing['path_id'].apply(is_not_problematic)]

# INCLUDE ONLY problematic routes (for investigation)
df_timing_problematic_only = df_timing[df_timing['path_id'].apply(lambda x: x in problematic_path_ids)]

# No filter (use original)
df_timing_all = df_timing.copy()
```

## Custom Threshold Filter

If you want different thresholds than the default (500km):

```python
from identify_long_edge_routes import analyze_problematic_routes

# Analyze with custom thresholds
problematic_custom = analyze_problematic_routes(
    loaded_runs[case_name]["input_data"],
    avg_segment_threshold=400.0,  # More strict: flag >400km avg segments
    multi_break_threshold=2        # Flag nodes with 2+ breaks
)

custom_path_ids = set(problematic_custom['problematic_paths'])

# Filter
df_timing_custom_filtered = df_timing[~df_timing['path_id'].isin(custom_path_ids)]

print(f"Custom filter removed {len(df_timing) - len(df_timing_custom_filtered)} routes")
```

## Remember

Based on the analysis:
- **Long-edge routes are NOT causing high break times**
- Filtering them may not significantly change your visualization
- But it's useful for **comparison** and **understanding model behavior**
- The real high break times (1500-3200h) come from different routes with normal segment lengths
