import json

with open('results_representation.ipynb', encoding='utf-8') as f:
    nb = json.load(f)

print("DETAILED ANALYSIS OF results_representation.ipynb")
print("="*100)

# Show markdown sections with their following code cells
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'markdown' and cell['source']:
        text = ''.join(cell['source'])
        print(f"\n{'='*100}")
        print(f"SECTION (Cell {i+1}):")
        print(''.join(cell['source'])[:500])

        # Show next few code cells after this markdown
        print(f"\n  Following code cells:")
        for j in range(i+1, min(i+5, len(nb['cells']))):
            if nb['cells'][j]['cell_type'] == 'code' and nb['cells'][j]['source']:
                code_preview = ''.join(nb['cells'][j]['source'])[:200]
                print(f"    Cell {j+1}: {code_preview.strip()[:200]}...")
            elif nb['cells'][j]['cell_type'] == 'markdown':
                break

print("\n" + "="*100)
print("\nIMPORTS AND DEPENDENCIES:")
print("="*100)
for i, cell in enumerate(nb['cells'][:10]):
    if cell['cell_type'] == 'code' and cell['source']:
        code = ''.join(cell['source'])
        if 'import' in code:
            print(f"\nCell {i+1}:")
            print(code)

print("\n" + "="*100)
print("\nKEY VARIABLES AND DATA STRUCTURES:")
print("="*100)
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code' and cell['source']:
        code = ''.join(cell['source'])
        # Look for key definitions
        if any(keyword in code for keyword in ['case_study_names', 'electrification', '_analysis', 'network_fees', 'BORDER']):
            if len(code) < 300:
                print(f"\nCell {i+1}:")
                print(code)
