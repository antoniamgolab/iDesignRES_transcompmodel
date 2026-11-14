"""
QUICK CHECK: Why are there long breaks (>1.5h)?
Paste this into break_times.ipynb for immediate answers
"""

# ==============================================================================
# ISOLATE AND ANALYZE LONG STOPS
# ==============================================================================
import pandas as pd
import numpy as np
import re

threshold = 1.5  # hours
long_stops = df_timing[df_timing["total_stop_time"] > threshold].copy()

print("="*80)
print(f"LONG BREAKS INVESTIGATION (>{threshold}h)")
print("="*80)
print(f"\nFound: {len(long_stops)}/{len(df_timing)} routes ({len(long_stops)/len(df_timing)*100:.1f}%)")

# ==============================================================================
# QUESTION 1: Is it extra_break_time?
# ==============================================================================
print("\n" + "="*80)
print("Q1: IS IT EXTRA_BREAK_TIME?")
print("="*80)

# Get extra_break_time data
extra_break_data = loaded_runs[case_name]["output_data"].get("extra_break_time", {})

if extra_break_data and 'path_id' in long_stops.columns:
    from collections import defaultdict

    # Aggregate by path
    path_extra = defaultdict(float)

    for key, value in extra_break_data.items():
        if isinstance(value, str):
            value = float(value)
        if value > 0:
            # Parse path_id
            if isinstance(key, str):
                nums = re.findall(r'\d+', key)
                if len(nums) >= 4:
                    path_id = int(nums[2])
                    path_extra[path_id] = max(path_extra[path_id], value)
            else:
                path_id = key[1][2]
                path_extra[path_id] = max(path_extra[path_id], value)

    # Add to dataframe
    long_stops['extra_break_max'] = long_stops['path_id'].map(lambda p: path_extra.get(p, 0))

    print(f"\nRoutes with extra_break_time > 0: {len(long_stops[long_stops['extra_break_max'] > 0])}/{len(long_stops)}")
    print(f"Average extra_break_time: {long_stops['extra_break_max'].mean():.2f}h")
    print(f"Max extra_break_time: {long_stops['extra_break_max'].max():.2f}h")

    # Check if extra_break explains the long stops
    long_stops['extra_explains'] = long_stops['extra_break_max'] > 1.0

    print(f"\nRoutes where extra_break_time > 1h: {long_stops['extra_explains'].sum()}/{len(long_stops)}")

    if long_stops['extra_break_max'].mean() > 0.5:
        print("\n-> YES: Extra_break_time appears to be a major contributor!")
    else:
        print("\n-> NO: Extra_break_time is minimal, look elsewhere")
else:
    print("\n[INFO] extra_break_time data not available")

# ==============================================================================
# QUESTION 2: Is it coherent with mandatory breaks?
# ==============================================================================
print("\n" + "="*80)
print("Q2: IS IT COHERENT WITH MANDATORY BREAKS?")
print("="*80)

if 'path_id' in long_stops.columns:
    mandatory_breaks = loaded_runs[case_name]["input_data"]['MandatoryBreaks']
    breaks_dict = {}
    for mb in mandatory_breaks:
        if mb['path_id'] not in breaks_dict:
            breaks_dict[mb['path_id']] = []
        breaks_dict[mb['path_id']].append(mb)

    # Check top 5 worst cases
    print("\nTop 5 longest stops - checking mandatory break data:")
    print("-"*80)

    for idx, row in long_stops.nlargest(5, 'total_stop_time').iterrows():
        path_id = row['path_id']
        total_stop = row['total_stop_time']
        break_dur = row.get('actual_break_duration', 0)
        charging = row.get('charging_time', 0)

        print(f"\nPath {path_id}: Total={total_stop:.2f}h (Break={break_dur:.2f}h, Charge={charging:.2f}h)")

        # Mandatory break info
        if path_id in breaks_dict:
            first_break = breaks_dict[path_id][0]
            print(f"  Mandatory break #1: time_with_breaks={first_break['time_with_breaks']:.2f}h")
            print(f"  Actual break duration: {break_dur:.2f}h")
            print(f"  Difference: {break_dur - first_break['time_with_breaks']:.2f}h")

            if break_dur > first_break['time_with_breaks'] + 0.5:
                print(f"  -> INCOHERENT: {break_dur - first_break['time_with_breaks']:.2f}h EXTRA beyond mandatory!")
            else:
                print(f"  -> Coherent with mandatory break")
        else:
            print(f"  No mandatory break (path < 360km)")
            if break_dur > 1.0:
                print(f"  -> STRANGE: {break_dur:.2f}h break for short route!")

# ==============================================================================
# QUESTION 3: Are these long distance routes?
# ==============================================================================
print("\n" + "="*80)
print("Q3: ARE THESE LONG DISTANCE ROUTES?")
print("="*80)

if 'path_id' in long_stops.columns:
    paths = loaded_runs[case_name]["input_data"]['Path']
    paths_dict = {p['id']: p for p in paths}

    # Add path characteristics
    long_stops['path_length'] = long_stops['path_id'].map(lambda p: paths_dict.get(p, {}).get('length', np.nan))
    long_stops['num_nodes'] = long_stops['path_id'].map(lambda p: len(paths_dict.get(p, {}).get('sequence', [])))

    # Compare with all routes
    all_lengths = [paths_dict[pid]['length'] for pid in df_timing['path_id'].unique() if pid in paths_dict]

    print(f"\nPath length comparison:")
    print(f"  All routes:       Mean={np.mean(all_lengths):.1f}km, Median={np.median(all_lengths):.1f}km")
    print(f"  Long stop routes: Mean={long_stops['path_length'].mean():.1f}km, Median={long_stops['path_length'].median():.1f}km")
    print(f"  Difference:       {long_stops['path_length'].mean() - np.mean(all_lengths):.1f}km ({(long_stops['path_length'].mean() - np.mean(all_lengths))/np.mean(all_lengths)*100:.1f}%)")

    if long_stops['path_length'].mean() > np.mean(all_lengths) * 1.2:
        print("\n-> YES: Long stop routes are SIGNIFICANTLY LONGER")
    elif long_stops['path_length'].mean() > np.mean(all_lengths) * 1.05:
        print("\n-> SOMEWHAT: Long stop routes are slightly longer")
    else:
        print("\n-> NO: Long stop routes are NOT particularly longer")

    # Distribution
    print(f"\nDistance distribution for long stop routes:")
    bins = [0, 360, 720, 1000, 1500, 10000]
    labels = ['<360km', '360-720km', '720-1000km', '1000-1500km', '>1500km']
    long_stops['distance_bin'] = pd.cut(long_stops['path_length'], bins=bins, labels=labels)

    for label in labels:
        count = len(long_stops[long_stops['distance_bin'] == label])
        if count > 0:
            pct = count / len(long_stops) * 100
            avg_stop = long_stops[long_stops['distance_bin'] == label]['total_stop_time'].mean()
            print(f"  {label:15s}: {count:3d} routes ({pct:4.1f}%) - Avg stop: {avg_stop:.2f}h")

# ==============================================================================
# QUESTION 4: What's the breakdown?
# ==============================================================================
print("\n" + "="*80)
print("Q4: WHAT'S THE BREAKDOWN?")
print("="*80)

if 'charging_time' in long_stops.columns and 'actual_break_duration' in long_stops.columns:
    total_stop_sum = long_stops['total_stop_time'].sum()
    break_sum = long_stops['actual_break_duration'].sum()
    charging_sum = long_stops['charging_time'].sum()

    print(f"\nTotal time breakdown for {len(long_stops)} routes with stops > {threshold}h:")
    print(f"  Total stop time:   {total_stop_sum:.1f}h (100%)")
    print(f"  Break duration:    {break_sum:.1f}h ({break_sum/total_stop_sum*100:.1f}%)")
    print(f"  Charging time:     {charging_sum:.1f}h ({charging_sum/total_stop_sum*100:.1f}%)")

    # Categorize routes
    charging_dominant = long_stops[long_stops['charging_time'] / long_stops['total_stop_time'] > 0.5]
    break_dominant = long_stops[long_stops['actual_break_duration'] / long_stops['total_stop_time'] > 0.5]

    print(f"\nRoute categorization:")
    print(f"  Charging-dominant (>50% charging): {len(charging_dominant)} ({len(charging_dominant)/len(long_stops)*100:.1f}%)")
    print(f"  Break-dominant (>50% break):      {len(break_dominant)} ({len(break_dominant)/len(long_stops)*100:.1f}%)")

    if len(charging_dominant) > len(break_dominant):
        print("\n-> CHARGING is the main cause of long stops")
    else:
        print("\n-> BREAK DURATION (incl. extra_break_time) is the main cause")

# ==============================================================================
# FINAL ANSWER
# ==============================================================================
print("\n" + "="*80)
print("FINAL ANSWER: WHERE DO LONG BREAKS COME FROM?")
print("="*80)

causes = []

if 'extra_break_max' in long_stops.columns:
    if long_stops['extra_break_max'].mean() > 0.5:
        causes.append(f"Extra_break_time (avg {long_stops['extra_break_max'].mean():.2f}h)")

if 'charging_time' in long_stops.columns:
    if long_stops['charging_time'].mean() > 0.5:
        causes.append(f"Charging time (avg {long_stops['charging_time'].mean():.2f}h)")

if 'path_length' in long_stops.columns:
    if long_stops['path_length'].mean() > np.mean(all_lengths) * 1.2:
        causes.append(f"Longer routes (avg {long_stops['path_length'].mean():.1f}km)")

print("\nMain contributors to long breaks:")
for i, cause in enumerate(causes, 1):
    print(f"  {i}. {cause}")

if not causes:
    print("  [UNCLEAR] - Need deeper investigation")

print("\n" + "="*80)

# Create summary dataframe
summary = long_stops[['path_id', 'total_stop_time', 'actual_break_duration', 'charging_time']].copy()
if 'extra_break_max' in long_stops.columns:
    summary['extra_break_max'] = long_stops['extra_break_max']
if 'path_length' in long_stops.columns:
    summary['path_length'] = long_stops['path_length']

print("\nTop 10 longest stops with full details:")
print(summary.nlargest(10, 'total_stop_time').to_string())
