import json
import sys

with open('results_representation.ipynb', encoding='utf-8') as f:
    nb = json.load(f)

print(f"Total cells: {len(nb['cells'])}\n")

# Count cell types
types = {}
for c in nb['cells']:
    types[c['cell_type']] = types.get(c['cell_type'], 0) + 1

print("Cell types:")
for k, v in types.items():
    print(f"  {k}: {v}")

# Get markdown headers (section structure)
print("\n" + "="*80)
print("NOTEBOOK STRUCTURE (Markdown Headers):")
print("="*80)
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'markdown' and cell['source']:
        text = ''.join(cell['source'])
        if text.strip().startswith('#'):
            lines = text.strip().split('\n')
            for line in lines[:3]:  # First 3 lines
                if line.strip().startswith('#'):
                    print(f"Cell {i+1}: {line}")

# Get code cell summaries
print("\n" + "="*80)
print("CODE CELLS SUMMARY (first line of each):")
print("="*80)
code_cells = [(i, c) for i, c in enumerate(nb['cells']) if c['cell_type'] == 'code']
print(f"Total code cells: {len(code_cells)}\n")

for idx, (i, cell) in enumerate(code_cells[:30]):  # First 30 code cells
    if cell['source']:
        first_line = cell['source'][0][:100]
        print(f"Cell {i+1} (code #{idx+1}): {first_line}")
