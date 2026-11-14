import json

with open('break_times.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Find the cumulative break analysis cell (should be around index -6 or -7)
# Look for the cell with "cumulative_break_data = []"
target_cell_idx = None
for i, cell in enumerate(nb['cells']):
    if cell.get('cell_type') == 'code':
        source = ''.join(cell.get('source', []))
        if 'cumulative_break_data = []' in source and 'cumulative_actual_time +=' in source:
            target_cell_idx = i
            break

if target_cell_idx is None:
    print("ERROR: Could not find cumulative break analysis cell!")
    exit(1)

print(f"Found cumulative break cell at index {target_cell_idx}")

# Replace the cell with corrected calculation
corrected_cell = {
    'cell_type': 'code',
    'execution_count': None,
    'metadata': {},
    'outputs': [],
    'source': [
        '# Cumulative Break Time Analysis\n',
        '# Calculate total break time accumulated along each route\n',
        '\n',
        '# Group mandatory breaks by path_id and num_drivers\n',
        'from collections import defaultdict\n',
        '\n',
        'path_breaks = defaultdict(list)\n',
        'for mb in mandatory_breaks:\n',
        '    if mb.get("num_drivers") == 1:  # Only single-driver routes\n',
        '        path_id = mb["path_id"]\n',
        '        path_breaks[path_id].append(mb)\n',
        '\n',
        '# Sort breaks by break_number for each path\n',
        'for path_id in path_breaks:\n',
        '    path_breaks[path_id].sort(key=lambda x: x.get("break_number", 0))\n',
        '\n',
        'print(f"Found {len(path_breaks)} paths with breaks")\n',
        '\n',
        '# Calculate cumulative break times from input data AND optimization results\n',
        'cumulative_break_data = []\n',
        '\n',
        'for path_id, breaks in path_breaks.items():\n',
        '    cumulative_mandatory_time = 0.0\n',
        '    cumulative_actual_time = 0.0\n',
        '    \n',
        '    path = path_dict.get(path_id)\n',
        '    if not path:\n',
        '        continue\n',
        '    \n',
        '    for mb in breaks:\n',
        '        # Mandatory break time from input data\n',
        '        cumulative_driving_time = mb["cumulative_driving_time"]\n',
        '        time_with_breaks = mb["time_with_breaks"]\n',
        '        this_mandatory_duration = time_with_breaks - cumulative_driving_time\n',
        '        cumulative_mandatory_time += this_mandatory_duration\n',
        '        \n',
        '        # Get actual break duration from optimization results\n',
        '        # actual = mandatory + slack (extra_break_time)\n',
        '        break_location = mb["latest_geo_id"]\n',
        '        extra_break_slack = 0.0\n',
        '        \n',
        '        # Find matching travel_time entries for this break location\n',
        '        for key, tt_value in travel_time.items():\n',
        '            year, prkg, tv_id, gen = key\n',
        '            prod_id, od_id, key_path_id, geo_id = prkg\n',
        '            \n',
        '            if key_path_id == path_id and geo_id == break_location:\n',
        '                # Get flow to calculate number of vehicles\n',
        '                flow_key = (year, (prod_id, od_id, path_id), (1, tv_id), gen)\n',
        '                flow_val = flow.get(flow_key, 0)\n',
        '                \n',
        '                if flow_val < 1e-6:\n',
        '                    continue\n',
        '                \n',
        '                # Calculate number of vehicles\n',
        '                tv = tv_dict.get(tv_id)\n',
        '                if not tv:\n',
        '                    continue\n',
        '                \n',
        '                gen_idx = gen - g_init\n',
        '                W = tv["W"][gen_idx]\n',
        '                AnnualRange = tv["AnnualRange"][gen_idx]\n',
        '                \n',
        '                num_vehicles = (path["length"] / (W * AnnualRange)) * 1000 * flow_val\n',
        '                \n',
        '                # Get slack from extra_break_time (per vehicle)\n',
        '                extra_key = (year, prkg, tv_id, gen)\n',
        '                extra_time = extra_break_time.get(extra_key, 0)\n',
        '                extra_break_slack = extra_time / num_vehicles if num_vehicles > 0 else 0\n',
        '                break  # Use first matching entry\n',
        '        \n',
        '        # CORRECTED: Actual break = mandatory + slack\n',
        '        this_actual_duration = this_mandatory_duration + extra_break_slack\n',
        '        cumulative_actual_time += this_actual_duration\n',
        '        \n',
        '        cumulative_break_data.append({\n',
        '            "path_id": path_id,\n',
        '            "break_number": mb["break_number"],\n',
        '            "event_type": mb["event_type"],\n',
        '            "cumulative_driving_time": cumulative_driving_time,\n',
        '            "this_mandatory_duration": this_mandatory_duration,\n',
        '            "extra_slack": extra_break_slack,\n',
        '            "this_actual_duration": this_actual_duration,\n',
        '            "cumulative_mandatory_time": cumulative_mandatory_time,\n',
        '            "cumulative_actual_time": cumulative_actual_time,\n',
        '            "total_time_mandatory": cumulative_driving_time + cumulative_mandatory_time,\n',
        '            "total_time_actual": cumulative_driving_time + cumulative_actual_time\n',
        '        })\n',
        '\n',
        'df_cumulative = pd.DataFrame(cumulative_break_data)\n',
        'print(f"Analyzed {len(df_cumulative)} cumulative break points")\n',
        'print(f"\\nCumulative break statistics:")\n',
        "print(f\"  Max cumulative mandatory breaks: {df_cumulative['cumulative_mandatory_time'].max():.2f}h\")\n",
        "print(f\"  Max cumulative actual breaks (with slack): {df_cumulative['cumulative_actual_time'].max():.2f}h\")\n",
        "print(f\"  Avg mandatory breaks per path: {df_cumulative.groupby('path_id')['cumulative_mandatory_time'].max().mean():.2f}h\")\n",
        "print(f\"  Avg actual breaks per path: {df_cumulative.groupby('path_id')['cumulative_actual_time'].max().mean():.2f}h\")\n",
        "print(f\"  Max driving time: {df_cumulative['cumulative_driving_time'].max():.2f}h\")\n"
    ]
}

# Replace the cell
nb['cells'][target_cell_idx] = corrected_cell

# Save updated notebook
with open('break_times.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print(f'\\nFixed cumulative break duration calculation!')
print('CORRECTED: actual_break_duration = mandatory_duration + extra_break_slack')
print('BEFORE: Was using just extra_break_time (WRONG)')
print('NOW: Uses mandatory + extra_break_time (CORRECT)')
