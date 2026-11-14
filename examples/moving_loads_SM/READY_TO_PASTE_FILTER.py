"""
READY TO PASTE INTO break_times.ipynb

Add this cell BEFORE your visualization code
"""

# ==============================================================================
# FILTER LONG-EDGE ROUTES
# ==============================================================================
import yaml

# Load problematic routes (long edges with multiple breaks at same node)
with open('problematic_routes.yaml', 'r') as f:
    problematic_info = yaml.safe_load(f)

problematic_path_ids = set(problematic_info['problematic_paths'])

print(f"Loaded {len(problematic_path_ids)} problematic routes to exclude")

# Check if path_id column exists in df_timing
if 'path_id' not in df_timing.columns:
    print("\n[WARNING] 'path_id' column not found in df_timing")
    print("Available columns:", list(df_timing.columns))
    print("\nYou need to add 'path_id' when creating df_timing DataFrame")
    print("See FILTER_FOR_BREAK_TIMES_NOTEBOOK.md for instructions")
else:
    # Save original for comparison
    df_timing_original = df_timing.copy()

    # Filter out problematic routes
    df_timing = df_timing[~df_timing['path_id'].isin(problematic_path_ids)].copy()

    print(f"\nFiltering results:")
    print(f"  Original: {len(df_timing_original)} routes")
    print(f"  Filtered: {len(df_timing)} routes")
    print(f"  Removed: {len(df_timing_original) - len(df_timing)} routes ({100*(len(df_timing_original)-len(df_timing))/len(df_timing_original):.1f}%)")

    # Show impact on statistics
    if len(df_timing) > 0 and len(df_timing_original) > 0:
        print(f"\nImpact on stop time statistics:")
        print(f"  Original mean: {df_timing_original['total_stop_time'].mean():.2f}h")
        print(f"  Filtered mean: {df_timing['total_stop_time'].mean():.2f}h")
        diff = df_timing_original['total_stop_time'].mean() - df_timing['total_stop_time'].mean()
        print(f"  Change: {diff:.2f}h ({100*diff/df_timing_original['total_stop_time'].mean():.1f}%)")

print("\n" + "="*80)
print("Note: Based on analysis, long-edge routes are NOT causing high break times")
print("Filtering them is mainly useful for comparison and investigation")
print("="*80)
