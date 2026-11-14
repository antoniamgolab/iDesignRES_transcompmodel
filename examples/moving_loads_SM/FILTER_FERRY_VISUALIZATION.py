"""
FILTER FERRY ROUTES IN BREAK_TIMES VISUALIZATION
(Keep ferries in model, but exclude from break time plots)

Paste this into break_times.ipynb BEFORE your visualization code
"""

# ==============================================================================
# LOAD FERRY ROUTE FILTER
# ==============================================================================
import yaml

# Load ferry routes info
with open('ferry_routes.yaml', 'r') as f:
    ferry_info = yaml.safe_load(f)

ferry_path_ids = set(ferry_info['ferry_paths'])

print("="*80)
print("FILTERING FERRY ROUTES FROM VISUALIZATION")
print("="*80)
print(f"\nFerry routes to exclude: {len(ferry_path_ids)}")
print(f"Ferry path IDs: {sorted(ferry_path_ids)}")

# Check if path_id column exists in df_timing
if 'path_id' not in df_timing.columns:
    print("\n[WARNING] 'path_id' column not found in df_timing")
    print("Available columns:", list(df_timing.columns))
    print("\nYou need to add 'path_id' when creating df_timing DataFrame")
else:
    # Save original for comparison
    df_timing_original = df_timing.copy()

    # Filter out ferry routes
    df_timing_no_ferries = df_timing[~df_timing['path_id'].isin(ferry_path_ids)].copy()

    print(f"\nFiltering results:")
    print(f"  Original:       {len(df_timing_original)} routes")
    print(f"  Without ferries: {len(df_timing_no_ferries)} routes")
    print(f"  Removed:        {len(df_timing_original) - len(df_timing_no_ferries)} routes")

    # Show impact on statistics
    if len(df_timing_no_ferries) > 0:
        print(f"\nImpact on stop time statistics:")
        print(f"  Original mean stop time:  {df_timing_original['total_stop_time'].mean():.2f}h")
        print(f"  Filtered mean stop time:  {df_timing_no_ferries['total_stop_time'].mean():.2f}h")

        print(f"\n  Original max stop time:   {df_timing_original['total_stop_time'].max():.2f}h")
        print(f"  Filtered max stop time:   {df_timing_no_ferries['total_stop_time'].max():.2f}h")

        # Check how many extreme values (>10h) are removed
        extreme_original = len(df_timing_original[df_timing_original['total_stop_time'] > 10])
        extreme_filtered = len(df_timing_no_ferries[df_timing_no_ferries['total_stop_time'] > 10])

        print(f"\n  Routes with stop time >10h:")
        print(f"    Original:  {extreme_original}")
        print(f"    Filtered:  {extreme_filtered}")
        print(f"    Removed:   {extreme_original - extreme_filtered}")

    # Use filtered version for visualization
    print(f"\n{'='*80}")
    print("Using df_timing_no_ferries for visualizations")
    print("(Ferry routes with >800km edges excluded)")
    print(f"{'='*80}")

    # Option 1: Replace df_timing (excludes ferries from ALL plots)
    df_timing = df_timing_no_ferries

    # Option 2: Keep both for comparison (uncomment if you want to compare)
    # df_timing_with_ferries = df_timing_original
    # df_timing = df_timing_no_ferries

print("\n" + "="*80)
print("Note: Ferry routes are still in the MODEL, only excluded from VISUALIZATION")
print("="*80)
