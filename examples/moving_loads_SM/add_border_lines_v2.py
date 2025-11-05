"""
Update the three latitude visualization cells to add dashed lines showing country borders.
Finds cells by content markers instead of cell IDs.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import json

# Read the notebook
notebook_path = 'modal_shift.ipynb'
print(f"Reading {notebook_path}...")

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Content markers to identify the three cells
cell_markers = [
    'Modal Split by Latitude',
    'Total TKM by Latitude',
    'Stacked Area by Latitude'
]

print(f"\nSearching for {len(cell_markers)} cells to update...")

cells_updated = 0

for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] != 'code':
        continue

    source = ''.join(cell['source'])

    # Check if this is one of our target cells
    is_target_cell = False
    cell_name = None
    for marker in cell_markers:
        if marker in source:
            is_target_cell = True
            cell_name = marker
            break

    if not is_target_cell:
        continue

    print(f"\nFound cell {i}: {cell_name}")

    # Check if border lines code already exists
    if 'country_southern_borders.csv' in source:
        print(f"  - Already has border lines code, skipping...")
        continue

    # Find where centroids are loaded
    if 'centroids_df = pd.read_csv' not in source:
        print(f"  - No centroids loading found, skipping...")
        continue

    lines = source.split('\n')

    # Step 1: Add loading of borders CSV after centroids
    insert_idx = None
    for j, line in enumerate(lines):
        if 'centroids_df = pd.read_csv' in line:
            insert_idx = j + 1
            # Skip any blank lines
            while insert_idx < len(lines) and lines[insert_idx].strip() == '':
                insert_idx += 1
            break

    if insert_idx is None:
        print(f"  - Could not find insertion point, skipping...")
        continue

    # Insert border loading code
    border_load_code = [
        "",
        "# Load country southern borders for dashed lines",
        "borders_df = pd.read_csv('country_southern_borders.csv')",
        ""
    ]
    lines[insert_idx:insert_idx] = border_load_code
    print(f"  - Added border loading code at line {insert_idx}")

    # Step 2: Add border line plotting
    # Find where country labels are added (look for "Add country labels")
    plot_insert_idx = None
    for j, line in enumerate(lines):
        if '# Add country labels' in line:
            # Find the end of this section (next major comment or reduced indentation)
            for k in range(j+1, len(lines)):
                # Look for the next section or end of indented block
                if lines[k].strip().startswith('#') and 'country' not in lines[k].lower():
                    plot_insert_idx = k
                    break
                # Or if we find plt.tight_layout or plt.show
                if 'plt.tight_layout' in lines[k] or 'plt.show' in lines[k]:
                    plot_insert_idx = k
                    break
            break

    if plot_insert_idx is None:
        # Alternative: look for plt.tight_layout or plt.show
        for j, line in enumerate(lines):
            if 'plt.tight_layout' in line or 'plt.show' in line:
                plot_insert_idx = j
                break

    if plot_insert_idx is not None:
        # Add border lines plotting code
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
            "    xlim = ax.get_xlim()",
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
        print(f"  - Cell updated successfully!")
    else:
        print(f"  - Could not find plot insertion point, skipping...")

print(f"\n{cells_updated} cells updated.")

# Write the updated notebook
if cells_updated > 0:
    print(f"\nWriting updated notebook to {notebook_path}...")
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1)
    print("OK - Notebook updated with border lines!")
else:
    print("\nNo cells updated - no changes written.")
