"""
READY TO PASTE: Replace the filter cell in break_times.ipynb
This filters out ferry routes (>800km edges) from visualization
"""

# ==============================================================================
# FILTER FERRY ROUTES FROM VISUALIZATION
# ==============================================================================
import yaml

# Load ferry routes (paths with edges >800km - likely ferries)
with open('ferry_routes.yaml', 'r') as f:
    ferry_info = yaml.safe_load(f)

ferry_path_ids = set(ferry_info['ferry_paths'])

print("="*80)
print("FILTERING FERRY ROUTES FROM BREAK TIME VISUALIZATION")
print("="*80)
print(f"\nFerry routes with edges >800km: {len(ferry_path_ids)}")
print(f"Ferry path IDs: {sorted(ferry_path_ids)}")
print(f"  (These are Germany-Sweden and Norway coastal ferries)")

# Check if path_id column exists
if 'path_id' not in df_timing.columns:
    print("\n[WARNING] 'path_id' column not found!")
    print("Available columns:", list(df_timing.columns))
else:
    # Save original
    df_timing_original = df_timing.copy()

    # Filter out ferry routes
    df_timing = df_timing[~df_timing['path_id'].isin(ferry_path_ids)].copy()

    print(f"\nFiltering results:")
    print(f"  Original: {len(df_timing_original)} routes")
    print(f"  Filtered: {len(df_timing)} routes")
    print(f"  Removed:  {len(df_timing_original) - len(df_timing)} routes ({(len(df_timing_original) - len(df_timing))/len(df_timing_original)*100:.1f}%)")

    # Show impact on statistics
    if len(df_timing) > 0:
        print(f"\nImpact on stop time statistics:")
        print(f"  Original mean: {df_timing_original['total_stop_time'].mean():.2f}h")
        print(f"  Filtered mean: {df_timing['total_stop_time'].mean():.2f}h")
        print(f"  Change: {df_timing_original['total_stop_time'].mean() - df_timing['total_stop_time'].mean():.2f}h")

        print(f"\n  Original max: {df_timing_original['total_stop_time'].max():.2f}h")
        print(f"  Filtered max: {df_timing['total_stop_time'].max():.2f}h")
        print(f"  Reduction: {df_timing_original['total_stop_time'].max() - df_timing['total_stop_time'].max():.2f}h")

        # Check extreme values
        extreme_threshold = 10.0
        extreme_orig = len(df_timing_original[df_timing_original['total_stop_time'] > extreme_threshold])
        extreme_filt = len(df_timing[df_timing['total_stop_time'] > extreme_threshold])

        print(f"\n  Routes with stop time >{extreme_threshold}h:")
        print(f"    Original: {extreme_orig}")
        print(f"    Filtered: {extreme_filt}")
        print(f"    Removed:  {extreme_orig - extreme_filt}")

print("\n" + "="*80)
print("Ferry routes excluded - now showing only truck driving routes")
print("="*80)
