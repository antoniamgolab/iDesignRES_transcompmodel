import json

with open('break_times.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Add analysis cell after the visualization to understand long stops
analysis_cell = {
    'cell_type': 'code',
    'execution_count': None,
    'metadata': {},
    'outputs': [],
    'source': [
        '# Analysis: Why are some stops so long?\n',
        '# Breakdown of the longest stops\n',
        '\n',
        'print("="*80)\n',
        'print("ANALYSIS: LONGEST STOP TIMES")\n',
        'print("="*80)\n',
        '\n',
        '# Get top 10 longest stops\n',
        'longest_stops = df_timing.nlargest(10, "total_stop_time")\n',
        '\n',
        'print(f"\\nTop 10 longest stops (out of {len(df_timing)} first breaks):")\n',
        'print()\n',
        'for idx, row in longest_stops.iterrows():\n',
        '    print(f"Route {row[\'path_id\']}, Year {row[\'year\']}, Gen {row[\'generation\']}, TV {row[\'vehicle_type\']}")\n',
        '    print(f"  Driving before break:  {row[\'cumulative_driving_time\']:.2f}h ({row[\'cumulative_driving_time\']*60:.0f} min)")\n',
        '    print(f"  Mandatory break:       {row[\'min_break_duration\']:.2f}h ({row[\'min_break_duration\']*60:.0f} min) [REQUIRED]")\n',
        '    print(f"  Extra slack:           {row[\'extra_slack\']:.2f}h ({row[\'extra_slack\']*60:.0f} min) [OPTIMIZER ADDED]")\n',
        '    print(f"  Actual break total:    {row[\'actual_break_duration\']:.2f}h ({row[\'actual_break_duration\']*60:.0f} min)")\n',
        '    print(f"  Charging time:         {row[\'charging_time\']:.2f}h ({row[\'charging_time\']*60:.0f} min) [CHARGING]")\n',
        '    print(f"  TOTAL STOP TIME:       {row[\'total_stop_time\']:.2f}h ({row[\'total_stop_time\']*60:.0f} min)")\n',
        '    \n',
        '    # Calculate percentages\n',
        '    total = row["total_stop_time"]\n',
        '    if total > 0:\n',
        '        pct_mandatory = (row["min_break_duration"] / total) * 100\n',
        '        pct_slack = (row["extra_slack"] / total) * 100\n',
        '        pct_charging = (row["charging_time"] / total) * 100\n',
        '        print(f"  Breakdown: {pct_mandatory:.1f}% mandatory, {pct_slack:.1f}% slack, {pct_charging:.1f}% charging")\n',
        '    print()\n',
        '\n',
        '# Summary statistics\n',
        'print("="*80)\n',
        'print("OVERALL STATISTICS")\n',
        'print("="*80)\n',
        'print(f"\\nAll {len(df_timing)} first breaks:")\n',
        'print(f"  Avg mandatory break:  {df_timing[\'min_break_duration\'].mean():.2f}h ({df_timing[\'min_break_duration\'].mean()*60:.0f} min)")\n',
        'print(f"  Avg extra slack:      {df_timing[\'extra_slack\'].mean():.2f}h ({df_timing[\'extra_slack\'].mean()*60:.0f} min)")\n',
        'print(f"  Avg charging:         {df_timing[\'charging_time\'].mean():.2f}h ({df_timing[\'charging_time\'].mean()*60:.0f} min)")\n',
        'print(f"  Avg total stop:       {df_timing[\'total_stop_time\'].mean():.2f}h ({df_timing[\'total_stop_time\'].mean()*60:.0f} min)")\n',
        '\n',
        '# What\'s driving the cost?\n',
        'print(f"\\nWhat makes stops long?")\n',
        'total_time_all = df_timing[\'total_stop_time\'].sum()\n',
        'mandatory_all = df_timing[\'min_break_duration\'].sum()\n',
        'slack_all = df_timing[\'extra_slack\'].sum()\n',
        'charging_all = df_timing[\'charging_time\'].sum()\n',
        '\n',
        'print(f"  Mandatory breaks:  {(mandatory_all/total_time_all)*100:.1f}% of total stop time")\n',
        'print(f"  Extra slack:       {(slack_all/total_time_all)*100:.1f}% of total stop time")\n',
        'print(f"  Charging:          {(charging_all/total_time_all)*100:.1f}% of total stop time")\n',
        '\n',
        '# Distribution\n',
        'print(f"\\nDistribution of stop times:")\n',
        'print(f"  < 1h:   {(df_timing[\'total_stop_time\'] < 1.0).sum()} routes ({(df_timing[\'total_stop_time\'] < 1.0).sum()/len(df_timing)*100:.1f}%)")\n',
        'print(f"  1-2h:   {((df_timing[\'total_stop_time\'] >= 1.0) & (df_timing[\'total_stop_time\'] < 2.0)).sum()} routes")\n',
        'print(f"  2-3h:   {((df_timing[\'total_stop_time\'] >= 2.0) & (df_timing[\'total_stop_time\'] < 3.0)).sum()} routes")\n',
        'print(f"  > 3h:   {(df_timing[\'total_stop_time\'] >= 3.0).sum()} routes")\n',
        '\n',
        '# Are long stops due to slack or charging?\n',
        'long_stops = df_timing[df_timing[\'total_stop_time\'] > 1.5]\n',
        'if len(long_stops) > 0:\n',
        '    print(f"\\nFor stops > 1.5h ({len(long_stops)} routes):")\n',
        '    print(f"  Avg slack:    {long_stops[\'extra_slack\'].mean():.2f}h ({long_stops[\'extra_slack\'].mean()*60:.0f} min)")\n',
        '    print(f"  Avg charging: {long_stops[\'charging_time\'].mean():.2f}h ({long_stops[\'charging_time\'].mean()*60:.0f} min)")\n',
        '    print(f"  Main driver: {\'CHARGING\' if long_stops[\'charging_time\'].mean() > long_stops[\'extra_slack\'].mean() else \'SLACK\'}")\n'
    ]
}

# Insert after visualization (cell 9), before sample display
nb['cells'].insert(10, analysis_cell)

# Save updated notebook
with open('break_times.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print('Added analysis cell to understand long stops!')
print('\nThis will show:')
print('  - Top 10 longest stops with detailed breakdown')
print('  - Whether long stops are due to SLACK or CHARGING')
print('  - Distribution of stop times')
print('  - What percentage of total time is mandatory vs slack vs charging')
