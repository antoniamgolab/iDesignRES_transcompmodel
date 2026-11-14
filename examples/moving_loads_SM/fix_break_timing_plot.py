import json

with open('break_times.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Find and replace the visualization cell (should be cell index -4)
viz_cell_updated = {
    'cell_type': 'code',
    'execution_count': None,
    'metadata': {},
    'outputs': [],
    'source': [
        '# Visualization: Break Timing vs Duration\n',
        'fig, ax = plt.subplots(figsize=(12, 8))\n',
        '\n',
        '# Plot actual break durations\n',
        'scatter = ax.scatter(df_timing["cumulative_driving_time"], \n',
        '                    df_timing["actual_break_duration"],\n',
        '                    c=df_timing["year"], \n',
        '                    cmap="viridis",\n',
        '                    s=100, \n',
        '                    alpha=0.6,\n',
        '                    edgecolors="black",\n',
        '                    linewidth=0.5,\n',
        '                    label="Actual break duration")\n',
        '\n',
        '# Add colorbar for years\n',
        'cbar = plt.colorbar(scatter, ax=ax)\n',
        'cbar.set_label("Year", rotation=270, labelpad=20)\n',
        '\n',
        '# Shading zones\n',
        '# GREEN: Compliant driving time (0 to 4.5h)\n',
        'ax.axvspan(0, 4.5, alpha=0.1, color="green", label="Compliant: Break within 4.5h", zorder=0)\n',
        '\n',
        '# RED: Non-compliant driving time (after 4.5h)\n',
        'if df_timing["cumulative_driving_time"].max() > 4.5:\n',
        '    ax.axvspan(4.5, df_timing["cumulative_driving_time"].max() * 1.05, \n',
        '              alpha=0.15, color="red", label="Violation: Break after 4.5h", zorder=0)\n',
        '\n',
        '# Mark the 4.5 hour regulatory threshold\n',
        'ax.axvline(x=4.5, color="red", linestyle="--", linewidth=2.5, \n',
        '          label="EU 4.5h driving limit", zorder=2)\n',
        '\n',
        '# Mark the minimum required break duration (0.75h = 45 min)\n',
        'ax.axhline(y=0.75, color="orange", linestyle="--", linewidth=2,\n',
        '          label="EU 45 min minimum break", zorder=2)\n',
        '\n',
        'ax.set_xlabel("Cumulative Driving Time Before Break (hours)", fontsize=12, fontweight="bold")\n',
        'ax.set_ylabel("Break Duration (hours)", fontsize=12, fontweight="bold")\n',
        'ax.set_title("First Mandatory Break Timing Analysis\\n(EU Regulation: 4.5h driving → 45min break)", \n',
        '            fontsize=14, fontweight="bold")\n',
        'ax.legend(loc="upper left", fontsize=10, framealpha=0.9)\n',
        'ax.grid(True, alpha=0.3)\n',
        '\n',
        '# Add text annotations\n',
        'ax.text(4.5 - 0.1, ax.get_ylim()[1] * 0.98, "Max driving limit →", \n',
        '       color="red", fontsize=10, ha="right", va="top", fontweight="bold")\n',
        'ax.text(0.05, 0.75 + 0.02, "Min break duration →", \n',
        '       color="orange", fontsize=10, va="bottom", fontweight="bold")\n',
        '\n',
        'plt.tight_layout()\n',
        'plt.savefig("break_timing_analysis.png", dpi=300, bbox_inches="tight")\n',
        'plt.show()\n',
        '\n',
        'print("\\\\nPlot saved as \\"break_timing_analysis.png\\"")\n',
        'print(f"\\\\nCompliance check:")\n',
        'compliant = df_timing[\n',
        '    (df_timing["cumulative_driving_time"] <= 4.5) & \n',
        '    (df_timing["actual_break_duration"] >= 0.75)\n',
        ']\n',
        'print(f"  Routes with breaks within 4.5h: {len(compliant)}/{len(df_timing)} "\n',
        '      f"({len(compliant)/len(df_timing)*100:.1f}%)")\n',
        '\n',
        'over_limit = df_timing[df_timing["cumulative_driving_time"] > 4.5]\n',
        'print(f"  Routes with breaks AFTER 4.5h: {len(over_limit)}/{len(df_timing)} "\n',
        '      f"({len(over_limit)/len(df_timing)*100:.1f}%)")\n'
    ]
}

# Replace the visualization cell (index -4: last is violations, -2 is 4-panel viz, -3 is sample, -4 is new viz)
nb['cells'][-4] = viz_cell_updated

# Save updated notebook
with open('break_times.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print('Fixed break timing visualization in break_times.ipynb')
print('Now shows:')
print('  - GREEN zone (0-4.5h): Compliant driving time before break')
print('  - RED zone (after 4.5h): Non-compliant driving time (violations)')
print('  - Red vertical line at 4.5h: Maximum driving limit')
