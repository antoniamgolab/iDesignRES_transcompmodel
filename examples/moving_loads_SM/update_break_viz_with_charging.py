import json

with open('break_times.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Update visualization cell (cell 9) to show break + charging
updated_viz = {
    'cell_type': 'code',
    'execution_count': None,
    'metadata': {},
    'outputs': [],
    'source': [
        '# Visualization: Break Timing vs Duration (with Charging Time)\n',
        'fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))\n',
        '\n',
        '# LEFT PLOT: Total stop time (break + charging)\n',
        'scatter = ax1.scatter(df_timing["cumulative_driving_time"], \n',
        '                     df_timing["total_stop_time"],\n',
        '                     c=df_timing["year"], \n',
        '                     cmap="viridis",\n',
        '                     s=100, \n',
        '                     alpha=0.6,\n',
        '                     edgecolors="black",\n',
        '                     linewidth=0.5,\n',
        '                     label="Total stop time (break + charging)")\n',
        '\n',
        '# Add colorbar for years\n',
        'cbar = plt.colorbar(scatter, ax=ax1)\n',
        'cbar.set_label("Year", rotation=270, labelpad=20)\n',
        '\n',
        '# Shading zones\n',
        'ax1.axvspan(0, 4.5, alpha=0.1, color="green", label="Compliant: Break within 4.5h", zorder=0)\n',
        'if df_timing["cumulative_driving_time"].max() > 4.5:\n',
        '    ax1.axvspan(4.5, df_timing["cumulative_driving_time"].max() * 1.05, \n',
        '               alpha=0.15, color="red", label="Violation: Break after 4.5h", zorder=0)\n',
        '\n',
        '# Mark the 4.5 hour regulatory threshold\n',
        'ax1.axvline(x=4.5, color="red", linestyle="--", linewidth=2.5, \n',
        '           label="EU 4.5h driving limit", zorder=2)\n',
        '\n',
        '# Mark the minimum required break duration (0.75h = 45 min)\n',
        'ax1.axhline(y=0.75, color="orange", linestyle="--", linewidth=2,\n',
        '           label="EU 45 min minimum break", zorder=2)\n',
        '\n',
        'ax1.set_xlabel("Cumulative Driving Time Before Break (hours)", fontsize=12, fontweight="bold")\n',
        'ax1.set_ylabel("Total Stop Time: Break + Charging (hours)", fontsize=12, fontweight="bold")\n',
        'ax1.set_title("First Break Stop Time Analysis\\\\n(Total time = Break duration + Charging time)", \n',
        '             fontsize=13, fontweight="bold")\n',
        'ax1.legend(loc="upper left", fontsize=9, framealpha=0.9)\n',
        'ax1.grid(True, alpha=0.3)\n',
        '\n',
        '# RIGHT PLOT: Break vs Charging time breakdown\n',
        '# Create stacked bars showing break and charging components\n',
        'routes_with_charging = df_timing[df_timing["charging_time"] > 0.01].sort_values("total_stop_time", ascending=False).head(30)\n',
        'routes_no_charging = df_timing[df_timing["charging_time"] <= 0.01].sample(min(20, len(df_timing[df_timing["charging_time"] <= 0.01])))\n',
        'sample_routes = pd.concat([routes_with_charging, routes_no_charging]).sort_values("cumulative_driving_time")\n',
        '\n',
        'x_pos = range(len(sample_routes))\n',
        'ax2.bar(x_pos, sample_routes["actual_break_duration"], \n',
        '       label="Break time (mandatory + slack)", color="steelblue", alpha=0.8)\n',
        'ax2.bar(x_pos, sample_routes["charging_time"], \n',
        '       bottom=sample_routes["actual_break_duration"],\n',
        '       label="Charging time", color="coral", alpha=0.8)\n',
        '\n',
        '# Add horizontal line at 0.75h\n',
        'ax2.axhline(y=0.75, color="orange", linestyle="--", linewidth=2, \n',
        '           label="45 min minimum", zorder=10)\n',
        '\n',
        'ax2.set_xlabel(f"Sample Routes (n={len(sample_routes)})", fontsize=12, fontweight="bold")\n',
        'ax2.set_ylabel("Time (hours)", fontsize=12, fontweight="bold")\n',
        'ax2.set_title("Break vs Charging Time Breakdown\\\\n(Top 30 with charging + 20 without)", \n',
        '             fontsize=13, fontweight="bold")\n',
        'ax2.legend(loc="upper left", fontsize=10, framealpha=0.9)\n',
        'ax2.grid(True, alpha=0.3, axis="y")\n',
        'ax2.set_xticks([])  # Hide x-tick labels for clarity\n',
        '\n',
        'plt.tight_layout()\n',
        'plt.savefig("break_timing_with_charging_analysis.png", dpi=300, bbox_inches="tight")\n',
        'plt.show()\n',
        '\n',
        'print("\\\\nPlot saved as \\"break_timing_with_charging_analysis.png\\"")\n',
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
        '      f"({len(over_limit)/len(df_timing)*100:.1f}%)")\n',
        '\n',
        'print(f"\\\\nCharging impact:")\n',
        'charging_routes = df_timing[df_timing["charging_time"] > 0.01]\n',
        'print(f"  Routes with charging at break: {len(charging_routes)} ({len(charging_routes)/len(df_timing)*100:.1f}%)")\n',
        'if len(charging_routes) > 0:\n',
        "    print(f\"  Avg charging time (when charging): {charging_routes['charging_time'].mean():.2f}h ({charging_routes['charging_time'].mean()*60:.0f} min)\")\n",
        "    print(f\"  Max total stop time: {df_timing['total_stop_time'].max():.2f}h ({df_timing['total_stop_time'].max()*60:.0f} min)\")\n"
    ]
}

nb['cells'][9] = updated_viz

# Save updated notebook
with open('break_times.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print('Updated visualization to show break + charging time breakdown!')
print('\\nLEFT PLOT: Total stop time (break + charging) vs driving time')
print('RIGHT PLOT: Stacked bar chart showing break vs charging components')
print('\\nThis explains why some stops are > 1 hour!')
