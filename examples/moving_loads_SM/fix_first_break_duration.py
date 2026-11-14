import json

with open('break_times.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Find cell 8 (first break timing analysis)
target_cell_idx = 8

print(f"Fixing cell {target_cell_idx} (first break timing analysis)")

# Replace with corrected cell
corrected_cell = {
    'cell_type': 'code',
    'execution_count': None,
    'metadata': {},
    'outputs': [],
    'source': [
        '# Break Timing Analysis: First Mandatory Break (4.5 hour rule)\n',
        '# Filter for num_drivers=1, break_number=1, event_type="B"\n',
        '\n',
        'first_breaks = [mb for mb in mandatory_breaks \n',
        '                if mb.get("num_drivers") == 1 \n',
        '                and mb.get("break_number") == 1 \n',
        '                and mb.get("event_type") == "B"]\n',
        '\n',
        'print(f"Found {len(first_breaks)} first mandatory breaks (4.5h rule)")\n',
        '\n',
        '# Analyze break timing and duration\n',
        'break_timing_data = []\n',
        '\n',
        'for mb in first_breaks:\n',
        '    path_id = mb["path_id"]\n',
        '    break_location = mb["latest_geo_id"]\n',
        '    cumulative_driving_time = mb["cumulative_driving_time"]  # When break occurs (hours)\n',
        '    time_with_breaks = mb["time_with_breaks"]  # Time including mandatory break\n',
        '    min_break_duration = time_with_breaks - cumulative_driving_time  # Minimum required (0.75h)\n',
        '    \n',
        '    path = path_dict.get(path_id)\n',
        '    if not path:\n',
        '        continue\n',
        '    \n',
        '    # Get actual break duration from optimization results\n',
        '    # Actual = Mandatory + Slack (extra_break_time)\n',
        '    for key, tt_value in travel_time.items():\n',
        '        year, prkg, tv_id, gen = key\n',
        '        prod_id, od_id, key_path_id, geo_id = prkg\n',
        '        \n',
        '        if key_path_id == path_id and geo_id == break_location:\n',
        '            # Get flow to calculate number of vehicles\n',
        '            flow_key = (year, (prod_id, od_id, path_id), (1, tv_id), gen)\n',
        '            flow_val = flow.get(flow_key, 0)\n',
        '            \n',
        '            if flow_val < 1e-6:\n',
        '                continue\n',
        '            \n',
        '            # Calculate number of vehicles\n',
        '            tv = tv_dict.get(tv_id)\n',
        '            if not tv:\n',
        '                continue\n',
        '            \n',
        '            gen_idx = gen - g_init\n',
        '            W = tv["W"][gen_idx]\n',
        '            AnnualRange = tv["AnnualRange"][gen_idx]\n',
        '            \n',
        '            num_vehicles = (path["length"] / (W * AnnualRange)) * 1000 * flow_val\n',
        '            \n',
        '            # Get extra slack from extra_break_time\n',
        '            extra_key = (year, prkg, tv_id, gen)\n',
        '            extra_time = extra_break_time.get(extra_key, 0)\n',
        '            extra_slack = extra_time / num_vehicles if num_vehicles > 0 else 0\n',
        '            \n',
        '            # CORRECTED: Actual break duration = mandatory + slack\n',
        '            actual_break_duration = min_break_duration + extra_slack\n',
        '            \n',
        '            break_timing_data.append({\n',
        '                "path_id": path_id,\n',
        '                "year": year,\n',
        '                "generation": gen,\n',
        '                "vehicle_type": tv_id,\n',
        '                "cumulative_driving_time": cumulative_driving_time,  # When break occurs\n',
        '                "min_break_duration": min_break_duration,  # Minimum required (0.75h)\n',
        '                "extra_slack": extra_slack,  # Slack from optimizer\n',
        '                "actual_break_duration": actual_break_duration,  # Total = mandatory + slack\n',
        '                "num_vehicles": num_vehicles\n',
        '            })\n',
        '\n',
        'df_timing = pd.DataFrame(break_timing_data)\n',
        'print(f"Analyzed {len(df_timing)} break timing entries")\n',
        'print(f"\\\\nBreak timing statistics:")\n',
        "print(f\"  Avg driving time before break: {df_timing['cumulative_driving_time'].mean():.2f}h\")\n",
        "print(f\"  Min driving time before break: {df_timing['cumulative_driving_time'].min():.2f}h\")\n",
        "print(f\"  Max driving time before break: {df_timing['cumulative_driving_time'].max():.2f}h\")\n",
        'print(f"\\\\nBreak duration statistics:")\n',
        "print(f\"  Required minimum: {df_timing['min_break_duration'].mean():.2f}h (45 min)\")\n",
        "print(f\"  Avg extra slack: {df_timing['extra_slack'].mean():.2f}h ({df_timing['extra_slack'].mean()*60:.1f} min)\")\n",
        "print(f\"  Avg actual duration: {df_timing['actual_break_duration'].mean():.2f}h ({df_timing['actual_break_duration'].mean()*60:.1f} min)\")\n",
        "print(f\"  Min actual duration: {df_timing['actual_break_duration'].min():.2f}h\")\n",
        "print(f\"  Max actual duration: {df_timing['actual_break_duration'].max():.2f}h\")\n"
    ]
}

# Replace the cell
nb['cells'][target_cell_idx] = corrected_cell

# Save updated notebook
with open('break_times.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print('\\nFixed first break timing analysis!')
print('CORRECTED: actual_break_duration = min_break_duration + extra_slack')
print('BEFORE: Was using just extra_slack (WRONG - showed 0.0h for minimum breaks)')
print('NOW: Shows total break duration (mandatory 0.75h + slack)')
print('\\nNow the Y-axis will show actual break durations >= 0.75h, not 0.0h')
