"""
Analyze the structure and content of modal_shift.ipynb
"""

import json

# Read notebook with proper encoding
with open('modal_shift.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

print("="*80)
print("MODAL_SHIFT.IPYNB ANALYSIS")
print("="*80)

print(f"\nTotal cells: {len(nb['cells'])}")

# Categorize cells
markdown_cells = [c for c in nb['cells'] if c['cell_type'] == 'markdown']
code_cells = [c for c in nb['cells'] if c['cell_type'] == 'code']

print(f"  Markdown cells: {len(markdown_cells)}")
print(f"  Code cells: {len(code_cells)}")

# Extract main sections from markdown cells
print("\n" + "="*80)
print("MAIN SECTIONS (from markdown headers)")
print("="*80)

for i, cell in enumerate(markdown_cells):
    source = ''.join(cell['source'])
    lines = source.split('\n')

    # Look for headers
    for line in lines:
        if line.startswith('# '):
            print(f"\n{line}")
        elif line.startswith('## '):
            print(f"  {line}")

# Extract key code patterns
print("\n" + "="*80)
print("KEY CODE PATTERNS")
print("="*80)

key_patterns = [
    'def ',
    'analyze_',
    'plot_',
    'calculate_',
    'TKM',
    'modal_split',
    'freight',
    'distance',
]

print("\nFunctions and key operations:")
for i, cell in enumerate(code_cells):
    source = ''.join(cell['source'])

    # Look for function definitions
    for line in source.split('\n'):
        line = line.strip()
        if line.startswith('def '):
            func_name = line.split('(')[0].replace('def ', '')
            print(f"  Cell {i}: {func_name}")
            break

# Extract plots
print("\n" + "="*80)
print("VISUALIZATIONS")
print("="*80)

plot_count = 0
for i, cell in enumerate(code_cells):
    source = ''.join(cell['source'])

    if 'plt.subplots' in source or 'fig,' in source:
        plot_count += 1
        # Extract title or description
        lines = source.split('\n')
        title_line = None
        for line in lines:
            if 'set_title' in line or 'suptitle' in line:
                title_line = line
                break

        if title_line:
            # Remove unicode characters
            title_line = title_line.encode('ascii', 'ignore').decode('ascii')
            print(f"\nPlot {plot_count} (Cell {i}): {title_line[:80]}")
        else:
            print(f"\nPlot {plot_count} (Cell {i}): [No title found]")
            # Show first few meaningful lines
            for line in lines[:5]:
                if line.strip() and not line.strip().startswith('#'):
                    line_clean = line.encode('ascii', 'ignore').decode('ascii')
                    print(f"  {line_clean[:80]}")
                    break

print(f"\nTotal plots found: {plot_count}")

# Extract data files being loaded
print("\n" + "="*80)
print("DATA FILES LOADED")
print("="*80)

for i, cell in enumerate(code_cells):
    source = ''.join(cell['source'])

    if 'load' in source.lower() or 'yaml' in source.lower():
        lines = source.split('\n')
        for line in lines:
            if 'load' in line.lower() or '.yaml' in line.lower() or '.csv' in line.lower():
                print(f"  Cell {i}: {line.strip()[:80]}")

print("\n" + "="*80)
