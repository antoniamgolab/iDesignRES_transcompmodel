import json

with open('results_representation.ipynb', encoding='utf-8') as f:
    nb = json.load(f)

print("OUTPUT AND VISUALIZATION ANALYSIS")
print("="*100)

# Look for plotting and output code
plot_cells = []
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code' and cell['source']:
        code = ''.join(cell['source'])
        if any(keyword in code.lower() for keyword in ['plt.', 'fig,', 'savefig', 'subplot', 'to_csv', '.png', '.csv']):
            plot_cells.append((i+1, code[:400]))

print(f"\nFound {len(plot_cells)} cells with plotting/output code\n")

for cell_num, code in plot_cells[-15:]:  # Show last 15
    print(f"\n{'='*100}")
    print(f"Cell {cell_num}:")
    print(code)

# Look for analysis functions being called
print("\n" + "="*100)
print("\nANALYSIS FUNCTION CALLS:")
print("="*100)
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code' and cell['source']:
        code = ''.join(cell['source'])
        if 'analyze_' in code or 'calculate_' in code:
            lines = code.split('\n')[:10]
            print(f"\nCell {i+1}:")
            for line in lines:
                if 'analyze_' in line or 'calculate_' in line:
                    print(f"  {line.strip()}")
