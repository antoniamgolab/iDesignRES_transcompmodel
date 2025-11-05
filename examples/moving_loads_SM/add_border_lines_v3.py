"""
Update latitude visualization cells to add dashed lines showing country borders.
Targets cells that have both 'centroid' and 'Add country labels' in their content.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import json

# Read the notebook
notebook_path = 'modal_shift.ipynb'
print(f"Reading {notebook_path}...")

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

print(f"\nSearching for cells with country labels...")

cells_updated = 0

for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] != 'code':
        continue

    source = ''.join(cell['source'])

    # Target cells that have both centroids and country labels
    has_centroids = 'centroid' in source
    has_labels = 'Add country labels' in source

    if not (has_centroids and has_labels):
        continue

    print(f"\nFound cell {i} with centroids and country labels")

    # Check if border lines code already exists
    if 'country_southern_borders.csv' in source:
        print(f"  - Already has border lines code, skipping...")
        continue

    lines = source.split('\n')

    # Step 1: Add loading of borders CSV after centroids
    insert_idx = None
    for j, line in enumerate(lines):
        if 'pd.read_csv' in line and 'centroid' in line:
            insert_idx = j + 1
            break

    if insert_idx is None:
        print(f"  - Could not find centroid loading, skipping...")
        continue

    # Insert border loading code
    border_load_code = [
        "",
        "# Load country southern borders for dashed lines",
        "borders_df = pd.read_csv('country_southern_borders.csv')"
    ]
    lines[insert_idx:insert_idx] = border_load_code
    print(f"  - Added border loading code at line {insert_idx}")

    # Step 2: Add border line plotting after country labels
    # Find plt.tight_layout() as a reliable insertion point
    plot_insert_idx = None
    for j, line in enumerate(lines):
        if 'plt.tight_layout()' in line:
            plot_insert_idx = j
            break

    if plot_insert_idx is None:
        print(f"  - Could not find plt.tight_layout(), skipping...")
        continue

    # Add border lines plotting code BEFORE plt.tight_layout()
    border_plot_code = [
        "",
        "# Add dashed lines for country southern borders",
        "corridor_countries = ['IT', 'AT', 'DE', 'DK', 'SE', 'NO']",
        "if isinstance(axes, np.ndarray):",
        "    ax_list = axes.flatten()",
        "else:",
        "    ax_list = [axes]",
        "",
        "for ax in ax_list:",
        "    ylim = ax.get_ylim()",
        "    ",
        "    for _, row in borders_df.iterrows():",
        "        country = row['CNTR_CODE']",
        "        border_lat = row['southern_border_lat']",
        "        ",
        "        if country in corridor_countries and ylim[0] <= border_lat <= ylim[1]:",
        "            ax.axhline(y=border_lat, color='gray', linestyle='--', ",
        "                      linewidth=0.8, alpha=0.5, zorder=1)",
        ""
    ]
    lines[plot_insert_idx:plot_insert_idx] = border_plot_code
    print(f"  - Added border plotting code at line {plot_insert_idx}")

    # Update the cell source
    cell['source'] = '\n'.join(lines)
    cells_updated += 1
    print(f"  - Cell {i} updated successfully!")

print(f"\n{cells_updated} cells updated.")

# Write the updated notebook
if cells_updated > 0:
    print(f"\nWriting updated notebook to {notebook_path}...")
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1)
    print("OK - Notebook updated with border lines!")
else:
    print("\nNo cells updated - no changes written.")
