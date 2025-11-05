"""
Create a comprehensive diagnostic cell to understand the flow data structure
"""

import json

# Load the notebook
notebook_path = "results_SM.ipynb"
with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# The diagnostic cell code
diagnostic_code = '''# COMPREHENSIVE FLOW DATA STRUCTURE DIAGNOSTIC

import pandas as pd
from collections import Counter

print("=" * 80)
print("FLOW DATA STRUCTURE ANALYSIS")
print("=" * 80)

# Analyze all keys to understand structure
all_keys = list(output_data["f"].keys())
print(f"\\nTotal flow entries: {len(all_keys)}")

# Analyze first 10 keys
print(f"\\nFirst 10 keys:")
for i, key in enumerate(all_keys[:10]):
    print(f"  {i}: {key}")

# Analyze each component
odpair_ids = []
tv_ids = []
g_values = []
fourth_values = []

for key in all_keys:
    if len(key) == 4:
        odpair_ids.append(key[0])
        tv_ids.append(key[1])
        g_values.append(key[2])
        fourth_values.append(key[3])

print(f"\\n--- Component Analysis ---")

# Odpair IDs
unique_odpairs = sorted(set(odpair_ids))
print(f"\\nOdpair IDs (first element):")
print(f"  Count: {len(unique_odpairs)}")
print(f"  Range: {min(unique_odpairs)} to {max(unique_odpairs)}")
print(f"  Sample: {unique_odpairs[:10]}")

# TechVehicle IDs
unique_tvs = sorted(set(tv_ids))
print(f"\\nTechVehicle IDs (second element):")
print(f"  Count: {len(unique_tvs)}")
print(f"  Sample: {unique_tvs[:5]}")

# Generation values
unique_gs = sorted(set(g_values))
print(f"\\nGeneration values (third element):")
print(f"  Count: {len(unique_gs)}")
print(f"  All unique values: {unique_gs[:20]}")

# Fourth values
unique_fourths = sorted(set(fourth_values))
print(f"\\nFourth element:")
print(f"  Count: {len(unique_fourths)}")
print(f"  Range: {min(unique_fourths)} to {max(unique_fourths)}")
print(f"  Sample: {unique_fourths[:10]}")

# Check if fourth element equals first element
matches = sum(1 for k in all_keys if len(k) == 4 and k[0] == k[3])
print(f"  Entries where 4th element == 1st element: {matches}/{len(all_keys)}")

# Check if generation tuple contains year information
print(f"\\n--- Testing if year is in generation tuple ---")
if len(unique_gs) > 0:
    for g in unique_gs[:10]:
        if isinstance(g, tuple):
            print(f"  g = {g}, elements: {list(g)}")
        else:
            print(f"  g = {g} (not a tuple)")

# Try to find entries with different generation values
print(f"\\n--- Looking for patterns in generation values ---")
g_counter = Counter(g_values)
print(f"Most common generation values:")
for g, count in g_counter.most_common(10):
    print(f"  {g}: {count} entries")

# Check if maybe we need to look at a different variable
print(f"\\n--- Available output variables ---")
print(f"Output data keys: {list(output_data.keys())}")

# Check if there's a separate year dimension somewhere
print(f"\\n--- Checking input data structure ---")
print(f"Model parameters: {list(input_data['Model'].keys())}")
print(f"  y_init = {input_data['Model'].get('y_init', 'N/A')}")
print(f"  Y = {input_data['Model'].get('Y', 'N/A')}")
print(f"  time_step = {input_data['Model'].get('time_step', 'N/A')}")

# Try to understand the actual indexing
print(f"\\n--- Hypothesis Testing ---")
print(f"\\nHypothesis 1: Fourth element is year index (but matches odpair - UNLIKELY)")
print(f"Hypothesis 2: Year is in generation tuple g[0] or g[1]")
print(f"Hypothesis 3: All data is for a single year/generation")
print(f"Hypothesis 4: Flow keys don't include year dimension")

# Check generation elements if it's a tuple
sample_g = g_values[0]
if isinstance(sample_g, tuple) and len(sample_g) >= 2:
    print(f"\\nGeneration tuple structure (from first entry): {sample_g}")
    print(f"  g[0] = {sample_g[0]}")
    print(f"  g[1] = {sample_g[1]}")

    # Check range of g[0] and g[1]
    g0_values = [g[0] for g in g_values if isinstance(g, tuple) and len(g) >= 2]
    g1_values = [g[1] for g in g_values if isinstance(g, tuple) and len(g) >= 2]

    print(f"\\nRange of g[0]: {min(g0_values)} to {max(g0_values)} (unique: {len(set(g0_values))})")
    print(f"  Sample values: {sorted(set(g0_values))[:20]}")
    print(f"\\nRange of g[1]: {min(g1_values)} to {max(g1_values)} (unique: {len(set(g1_values))})")
    print(f"  Sample values: {sorted(set(g1_values))[:20]}")

    # If g[0] has more variety than g[1], it might be the year
    if len(set(g0_values)) > len(set(g1_values)):
        print(f"\\n*** g[0] has more variety - might be the year index! ***")
    elif len(set(g1_values)) > len(set(g0_values)):
        print(f"\\n*** g[1] has more variety - might be the year index! ***")
    else:
        print(f"\\n*** Both g[0] and g[1] have same variety ***")

print("\\n" + "=" * 80)
'''

# Find a good place to insert this diagnostic cell (before the electrification analysis)
target_idx = None
for idx, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if 'Electrification by Country Analysis' in source:
            target_idx = idx
            break

if target_idx is None:
    print("ERROR: Could not find insertion point")
else:
    # Insert the diagnostic cell before the electrification cell
    new_cell = {
        'cell_type': 'code',
        'execution_count': None,
        'metadata': {},
        'outputs': [],
        'source': diagnostic_code.split('\n')
    }

    # Check if there's already a diagnostic cell
    if target_idx > 0:
        prev_source = ''.join(nb['cells'][target_idx - 1].get('source', []))
        if 'FLOW DATA STRUCTURE ANALYSIS' in prev_source:
            # Replace existing diagnostic
            nb['cells'][target_idx - 1] = new_cell
            print(f"Replaced existing diagnostic cell at index {target_idx - 1}")
        else:
            # Insert new diagnostic
            nb['cells'].insert(target_idx, new_cell)
            print(f"Inserted new diagnostic cell at index {target_idx}")
    else:
        nb['cells'].insert(target_idx, new_cell)
        print(f"Inserted new diagnostic cell at index {target_idx}")

    # Save the notebook
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1)

    print("\nDiagnostic cell created successfully!")
    print("This cell will:")
    print("  1. Analyze all unique values of each key component")
    print("  2. Check if year might be in g[0] instead of g[1]")
    print("  3. Show patterns in generation values")
    print("  4. Test multiple hypotheses about the data structure")
    print("\nPlease run this diagnostic cell to understand the structure!")
