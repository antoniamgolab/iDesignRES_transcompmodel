# How to Filter Problematic Routes in break_times.ipynb

## Method 1: Quick Filter Using Saved File

Add this cell at the beginning of your notebook:

```python
import yaml

# Load the pre-identified problematic routes
with open('problematic_routes.yaml', 'r') as f:
    problematic_info = yaml.safe_load(f)

problematic_path_ids = set(problematic_info['problematic_paths'])

print(f"Loaded {len(problematic_path_ids)} problematic routes")
print(f"Stats: {problematic_info['stats']}")

# Create filter function
def is_not_problematic(path_id):
    """Returns True if path should be kept (i.e., not problematic)"""
    return path_id not in problematic_path_ids

# Or if you want ONLY problematic routes
def is_problematic(path_id):
    """Returns True if path is problematic"""
    return path_id in problematic_path_ids
```

## Method 2: Full Analysis in Notebook

Add this cell to analyze directly:

```python
from identify_long_edge_routes import (
    analyze_problematic_routes,
    create_route_filter,
    print_problematic_routes_summary,
    filter_dataframe_by_routes
)

# Analyze problematic routes
problematic_routes = analyze_problematic_routes(
    loaded_runs[case_name]["input_data"],
    avg_segment_threshold=500.0,  # Flag routes >500km avg segment
    multi_break_threshold=2       # Flag nodes with 2+ breaks
)

# Print summary
print_problematic_routes_summary(problematic_routes)

# Create filter function
filter_func = create_route_filter(problematic_routes, mode='exclude')
```

## Applying the Filter to Your Visualizations

### Example 1: Filter DataFrame

```python
# Assuming you have a DataFrame 'df' with 'path_id' column
df_filtered = filter_dataframe_by_routes(
    df,
    problematic_routes,
    path_column='path_id',
    mode='exclude'  # Use 'include' to keep ONLY problematic routes
)

print(f"Original: {len(df)} rows")
print(f"Filtered: {len(df_filtered)} rows")
```

### Example 2: Filter When Aggregating extra_break_time

```python
# Original code (unfiltered)
for key, value in extra_break_time_data.items():
    if value > 0:
        year, (prod_id, od_id, path_id, geo_id), tv_id, gen = key
        # ... process data

# Filtered version
filter_func = create_route_filter(problematic_routes, mode='exclude')

for key, value in extra_break_time_data.items():
    if value > 0:
        year, (prod_id, od_id, path_id, geo_id), tv_id, gen = key

        # Skip problematic routes
        if not filter_func(path_id):
            continue

        # ... process data
```

### Example 3: Filter When Creating Lists

```python
# Filter a list of path IDs
path_ids_filtered = [
    path_id for path_id in all_path_ids
    if filter_func(path_id)
]

# Or using pandas
df['keep'] = df['path_id'].apply(filter_func)
df_filtered = df[df['keep']]
```

## Comparing Filtered vs Unfiltered

Create side-by-side comparison:

```python
import matplotlib.pyplot as plt

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

# Plot 1: All routes
plot_break_times(ax1, all_data, title="All Routes")

# Plot 2: Filtered routes (excluding problematic)
df_filtered = filter_dataframe_by_routes(all_data, problematic_routes, mode='exclude')
plot_break_times(ax2, df_filtered, title="Excluding Long-Edge Routes")

plt.tight_layout()
plt.show()
```

## Check Correlation with High Break Times

```python
from identify_long_edge_routes import check_if_problematic_causes_high_break_time

# Check if problematic routes correlate with high extra_break_time
correlation_results = check_if_problematic_causes_high_break_time(
    extra_break_time_data=output_data['extra_break_time'],
    problematic_routes=problematic_routes,
    input_data=loaded_runs[case_name]["input_data"]
)

print(f"Top 50 routes with highest break time: {correlation_results['top_50_high_break_time']}")
print(f"Of these, {correlation_results['overlap']} ({correlation_results['overlap_percentage']:.1f}%) are problematic routes")

# Show details of top routes
import pandas as pd
top_routes_df = pd.DataFrame(correlation_results['top_paths_with_details'][:20])
print("\nTop 20 routes with highest extra_break_time:")
print(top_routes_df[['path_id', 'max_break_time', 'is_problematic']])
```

## Custom Thresholds

Adjust thresholds to be more/less strict:

```python
# More strict: flag routes with >400km avg segments
problematic_strict = analyze_problematic_routes(
    input_data,
    avg_segment_threshold=400.0,
    multi_break_threshold=2
)

# Less strict: only flag very long routes (>700km avg)
problematic_lenient = analyze_problematic_routes(
    input_data,
    avg_segment_threshold=700.0,
    multi_break_threshold=3  # Need 3+ breaks at same node
)

print(f"Strict: {len(problematic_strict['problematic_paths'])} routes")
print(f"Lenient: {len(problematic_lenient['problematic_paths'])} routes")
```

## Summary Statistics

```python
stats = problematic_routes['stats']

print("="*60)
print("PROBLEMATIC ROUTES SUMMARY")
print("="*60)
print(f"Total paths: {stats['total_paths']}")
print(f"Problematic: {stats['num_problematic']} ({100*stats['num_problematic']/stats['total_paths']:.1f}%)")
print(f"  - Long edges: {stats['num_long_edge']}")
print(f"  - Multi-breaks at same node: {stats['num_multi_break']}")
print()
print(f"Thresholds used:")
print(f"  - Avg segment: >{stats['avg_segment_threshold']} km")
print(f"  - Breaks per node: >={stats['multi_break_threshold']}")
```

## Results from Your Data

Based on the analysis just run:

- **Total paths**: 1261
- **Problematic paths**: 15 (1.2%)
  - 15 with long edges (>500km avg segment)
  - 3 with multiple breaks at same node

**Most problematic routes:**
1. Path 5409: 1812 km, avg segment 906 km, **4 breaks at node 72**
2. Path 5289: 899 km, avg segment 899 km, **2 breaks at node 68**
3. Path 5129: 1924 km, avg segment 641 km, **3 breaks at node 69**

These are likely the routes causing high `extra_break_time` values!
