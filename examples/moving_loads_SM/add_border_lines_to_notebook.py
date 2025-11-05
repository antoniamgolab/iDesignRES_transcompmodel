"""
Update the three latitude visualization cells to add dashed lines showing country borders.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import json

# Read the notebook
notebook_path = 'modal_shift.ipynb'
print(f"Reading {notebook_path}...")

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# The three cells to update
cell_ids_to_update = ['yl37ynop316', 'novbsw8eg3w', 'nmxacw407x7']

print(f"\nSearching for cells to update: {cell_ids_to_update}")

cells_updated = 0

for cell in nb['cells']:
    cell_id = cell['metadata'].get('id', '')

    if cell_id in cell_ids_to_update:
        print(f"\nUpdating cell {cell_id}...")

        source = ''.join(cell['source'])

        # Check if border lines code already exists
        if 'country_southern_borders.csv' in source:
            print(f"  - Cell {cell_id} already has border lines code, skipping...")
            continue

        # Find where to insert the border lines code
        # Insert right after loading country centroids and before the plotting loop

        if 'centroids_df = pd.read_csv' in source:
            # Split at the line after reading centroids
            lines = source.split('\n')

            # Find the index where centroids_df is read
            insert_idx = None
            for i, line in enumerate(lines):
                if 'centroids_df = pd.read_csv' in line:
                    # Insert after this line (and any following blank lines)
                    insert_idx = i + 1
                    while insert_idx < len(lines) and lines[insert_idx].strip() == '':
                        insert_idx += 1
                    break

            if insert_idx is not None:
                # Create the border lines code
                border_code = [
                    "",
                    "# Load country southern borders for dashed lines",
                    "borders_df = pd.read_csv('country_southern_borders.csv')",
                    ""
                ]

                # Insert the code
                lines[insert_idx:insert_idx] = border_code

                # Now find where to add the actual border lines to the plot
                # This should be after the country labels are added
                plot_insert_idx = None
                for i, line in enumerate(lines):
                    if 'Add country labels' in line or 'for idx, ax in enumerate' in line:
                        # Find the end of the country label loop
                        indent_level = len(line) - len(line.lstrip())
                        for j in range(i+1, len(lines)):
                            if lines[j].strip() and not lines[j].startswith(' ' * (indent_level + 1)):
                                plot_insert_idx = j
                                break
                        break

                if plot_insert_idx is not None:
                    # Add code to draw border lines
                    border_plot_code = [
                        "",
                        "    # Add dashed lines for country borders",
                        "    corridor_countries = ['IT', 'AT', 'DE', 'DK', 'SE', 'NO']",
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

                # Reconstruct the source
                cell['source'] = '\n'.join(lines)
                cells_updated += 1
                print(f"  - Cell {cell_id} updated successfully!")

print(f"\n{cells_updated} cells updated.")

# Write the updated notebook
print(f"\nWriting updated notebook to {notebook_path}...")
with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)

print("OK - Notebook updated with border lines!")
