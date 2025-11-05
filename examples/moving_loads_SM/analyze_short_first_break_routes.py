"""
Analyze routes with first breaks occurring before 1 hour of driving.

This helps identify why some routes have very early breaks.
"""

import pandas as pd
import yaml
import os


def analyze_short_break_routes(case_name="case_20251028_091344_var_var"):
    """
    Analyze routes with first break before 1 hour of driving.

    Parameters:
    -----------
    case_name : str
        Name of the case to analyze
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
        return None

    # Load mandatory breaks
    breaks = input_data['MandatoryBreaks']
    df_breaks = pd.DataFrame(breaks)

    # Filter for first break only
    df_first_breaks = df_breaks[df_breaks['break_number'] == 1].copy()

    print("="*80)
    print(f"ANALYZING ROUTES FROM: {case_name}")
    print("="*80)
    print(f"\nTotal routes: {len(df_first_breaks)}")

    # Filter for breaks occurring before 1 hour
    df_short = df_first_breaks[df_first_breaks['cumulative_driving_time'] < 1.0].copy()

    print(f"Routes with first break BEFORE 1 hour: {len(df_short)}")
    print(f"Percentage: {100 * len(df_short) / len(df_first_breaks):.1f}%")

    # Statistics on these short routes
    print("\n" + "-"*80)
    print("STATISTICS FOR ROUTES WITH FIRST BREAK < 1 HOUR")
    print("-"*80)

    print(f"\nDriving time to first break:")
    print(f"  Mean: {df_short['cumulative_driving_time'].mean():.3f} hours")
    print(f"  Median: {df_short['cumulative_driving_time'].median():.3f} hours")
    print(f"  Min: {df_short['cumulative_driving_time'].min():.3f} hours")
    print(f"  Max: {df_short['cumulative_driving_time'].max():.3f} hours")

    print(f"\nTotal path characteristics:")
    print(f"  Average path length: {df_short['path_length'].mean():.1f} km")
    print(f"  Average total driving time: {df_short['total_driving_time'].mean():.2f} hours")
    print(f"  Min path length: {df_short['path_length'].min():.1f} km")
    print(f"  Max path length: {df_short['path_length'].max():.1f} km")

    print(f"\nNumber of drivers:")
    print(df_short['num_drivers'].value_counts().sort_index())

    print(f"\nCharging type at first break:")
    print(df_short['charging_type'].value_counts())

    print(f"\nEvent type at first break:")
    print(df_short['event_type'].value_counts())

    # Show some examples
    print("\n" + "-"*80)
    print("EXAMPLE ROUTES (first 20)")
    print("-"*80)

    cols_to_show = [
        'path_id', 'path_length', 'total_driving_time',
        'cumulative_driving_time', 'num_drivers', 'event_type', 'charging_type'
    ]

    print(df_short[cols_to_show].head(20).to_string(index=False))

    # Check if these are very short routes overall
    print("\n" + "-"*80)
    print("ROUTE LENGTH ANALYSIS")
    print("-"*80)

    # Very short routes (< 100 km)
    very_short = df_short[df_short['path_length'] < 100]
    print(f"\nRoutes < 100 km: {len(very_short)} ({100*len(very_short)/len(df_short):.1f}% of early breaks)")

    # Short routes (100-300 km)
    short = df_short[(df_short['path_length'] >= 100) & (df_short['path_length'] < 300)]
    print(f"Routes 100-300 km: {len(short)} ({100*len(short)/len(df_short):.1f}% of early breaks)")

    # Medium routes (300-500 km)
    medium = df_short[(df_short['path_length'] >= 300) & (df_short['path_length'] < 500)]
    print(f"Routes 300-500 km: {len(medium)} ({100*len(medium)/len(df_short):.1f}% of early breaks)")

    # Long routes (>= 500 km)
    long_routes = df_short[df_short['path_length'] >= 500]
    print(f"Routes >= 500 km: {len(long_routes)} ({100*len(long_routes)/len(df_short):.1f}% of early breaks)")

    # For long routes with early breaks, investigate further
    if len(long_routes) > 0:
        print("\n" + "-"*80)
        print(f"INVESTIGATING {len(long_routes)} LONG ROUTES WITH EARLY BREAKS")
        print("-"*80)
        print("\nThese are routes >= 500 km but with first break < 1 hour:")
        print(long_routes[cols_to_show].to_string(index=False))

        print("\nPossible reasons:")
        print("1. Multi-driver routes (can take breaks earlier)")
        print("2. Charging stops needed for short-range EVs")
        print("3. Strategic break placement for route optimization")

    # Distribution plot
    print("\n" + "-"*80)
    print("DISTRIBUTION OF FIRST BREAK TIME")
    print("-"*80)

    bins = [0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]
    df_first_breaks['time_bin'] = pd.cut(df_first_breaks['cumulative_driving_time'], bins=bins)
    time_dist = df_first_breaks['time_bin'].value_counts().sort_index()

    print("\nFirst break time distribution (all routes):")
    for interval, count in time_dist.items():
        pct = 100 * count / len(df_first_breaks)
        print(f"  {interval}: {count:4d} routes ({pct:5.1f}%)")

    return df_short


if __name__ == "__main__":
    df_short = analyze_short_break_routes()

    # Save to CSV for further analysis
    if df_short is not None:
        output_file = "short_first_break_routes.csv"
        df_short.to_csv(output_file, index=False)
        print(f"\n{'='*80}")
        print(f"Full data saved to: {output_file}")
        print(f"{'='*80}")
