import json

with open('break_times.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Find the visualization cell with print statements
target_cell_idx = None
for i, cell in enumerate(nb['cells']):
    if cell.get('cell_type') == 'code':
        source = ''.join(cell.get('source', []))
        if 'Avg slack per break:' in source and 'cumulative_break_time_analysis.png' in source:
            target_cell_idx = i
            break

if target_cell_idx is None:
    print("ERROR: Could not find visualization cell with print statements!")
    exit(1)

print(f"Found visualization cell at index {target_cell_idx}")

# Get the existing cell and update the print statements
cell = nb['cells'][target_cell_idx]
source_lines = cell['source']

# Find and replace the print statements section
new_source = []
skip_until_tight_layout = False

for i, line in enumerate(source_lines):
    if 'print(f"\\\\nBreak time comparison:")' in line:
        # Replace the break time comparison section
        new_source.append('        print(f"\\\\nBreak time comparison:")\n')
        new_source.append("        print(f\"  Avg mandatory break per event: {df_cumulative['this_mandatory_duration'].mean():.3f}h ({df_cumulative['this_mandatory_duration'].mean()*60:.1f} min)\")\n")
        new_source.append("        print(f\"  Avg actual break per event: {df_cumulative['this_actual_duration'].mean():.3f}h ({df_cumulative['this_actual_duration'].mean()*60:.1f} min)\")\n")
        new_source.append("        print(f\"  Avg extra slack per break: {df_cumulative['extra_slack'].mean():.3f}h ({df_cumulative['extra_slack'].mean()*60:.1f} min)\")\n")
        new_source.append("        print(f\"  Total slack = Actual - Mandatory: {(df_cumulative['this_actual_duration'] - df_cumulative['this_mandatory_duration']).sum():.2f}h\")\n")
        skip_until_tight_layout = True
        continue

    if skip_until_tight_layout:
        if 'plt.tight_layout()' in line:
            skip_until_tight_layout = False
            new_source.append(line)
        continue
    else:
        new_source.append(line)

cell['source'] = new_source

# Save updated notebook
with open('break_times.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print('\\nUpdated print statements in visualization cell!')
print('Now correctly shows:')
print('  - Mandatory break per event')
print('  - Actual break per event (mandatory + slack)')
print('  - Extra slack per break')
