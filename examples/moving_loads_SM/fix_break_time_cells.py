"""
Fix the break time comparison cells with correct column names
"""

import json

# Load the existing notebook
notebook_path = r"C:\Users\simuser\Documents\AntoniaGolab\Scand_Med_analysis\SM_baby_2\iDesignRES_transcompmodel\examples\moving_loads_SM\charging_constraint_comparison.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Remove the last 5 cells (the ones we added with wrong column names)
nb['cells'] = nb['cells'][:-5]

# New cells with CORRECT column names
new_cells = [
    # Markdown header
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## 6. Break Time Comparison for Both-Electrified OD Pairs\n",
            "\n",
            "This section analyzes how break times differ between baseline and constrained cases\n",
            "for OD pairs that are electrified (>=50% BEV share) in **both** scenarios.\n",
            "\n",
            "Key metrics:\n",
            "- **extra_break_time**: Additional slack time added by optimizer beyond mandatory 45-min break\n",
            "- **actual_break_duration**: min_break_duration (0.75h) + extra_break_time\n",
            "- **total_stop_time**: break_duration + charging_time"
        ]
    },
    # Code cell to load data
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Load break time comparison results\n",
            "break_comparison_df = pd.read_csv('break_time_comparison_both_electrified.csv')\n",
            "print(f\"Loaded {len(break_comparison_df)} OD pairs with break time comparison\")\n",
            "print(f\"\\nColumns: {list(break_comparison_df.columns)}\")\n",
            "break_comparison_df.head(10)"
        ]
    },
    # Code cell for summary statistics - FIXED COLUMN NAMES
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Summary statistics for break time comparison\n",
            "print(\"=\"*80)\n",
            "print(\"BREAK TIME COMPARISON SUMMARY\")\n",
            "print(\"=\"*80)\n",
            "\n",
            "# Calculate key statistics\n",
            "n_increased = (break_comparison_df['diff_total_stop'] > 0).sum()\n",
            "n_decreased = (break_comparison_df['diff_total_stop'] < 0).sum()\n",
            "n_unchanged = (break_comparison_df['diff_total_stop'] == 0).sum()\n",
            "\n",
            "print(f\"\\nOD pairs analyzed: {len(break_comparison_df)}\")\n",
            "print(f\"  Stop time increased: {n_increased} ({100*n_increased/len(break_comparison_df):.1f}%)\")\n",
            "print(f\"  Stop time decreased: {n_decreased} ({100*n_decreased/len(break_comparison_df):.1f}%)\")\n",
            "print(f\"  Stop time unchanged: {n_unchanged} ({100*n_unchanged/len(break_comparison_df):.1f}%)\")\n",
            "\n",
            "# Aggregate differences\n",
            "print(f\"\\nAggregate differences:\")\n",
            "print(f\"  Total baseline stop time: {break_comparison_df['baseline_total_stop'].sum():,.1f}h\")\n",
            "print(f\"  Total constrained stop time: {break_comparison_df['constrained_total_stop'].sum():,.1f}h\")\n",
            "print(f\"  Net difference: {break_comparison_df['diff_total_stop'].sum():+,.1f}h\")\n",
            "\n",
            "# Mean per OD pair\n",
            "print(f\"\\nMean per OD pair:\")\n",
            "print(f\"  Baseline total stop: {break_comparison_df['baseline_total_stop'].mean():.2f}h\")\n",
            "print(f\"  Constrained total stop: {break_comparison_df['constrained_total_stop'].mean():.2f}h\")\n",
            "print(f\"  Mean difference: {break_comparison_df['diff_total_stop'].mean():+.2f}h\")"
        ]
    },
    # Code cell for visualization - FIXED COLUMN NAMES
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Visualize break time comparison\n",
            "fig, axes = plt.subplots(1, 3, figsize=(15, 5))\n",
            "\n",
            "# 1. Distribution of total stop time differences\n",
            "ax1 = axes[0]\n",
            "ax1.hist(break_comparison_df['diff_total_stop'], bins=50, edgecolor='black', alpha=0.7)\n",
            "ax1.axvline(0, color='red', linestyle='--', linewidth=2, label='No change')\n",
            "ax1.axvline(break_comparison_df['diff_total_stop'].mean(), color='green', linestyle='-', linewidth=2, label=f'Mean: {break_comparison_df[\"diff_total_stop\"].mean():+.1f}h')\n",
            "ax1.set_xlabel('Total Stop Time Difference (h)')\n",
            "ax1.set_ylabel('Number of OD Pairs')\n",
            "ax1.set_title('Distribution of Stop Time Changes')\n",
            "ax1.legend()\n",
            "\n",
            "# 2. Scatter: baseline vs constrained total stop time\n",
            "ax2 = axes[1]\n",
            "ax2.scatter(break_comparison_df['baseline_total_stop'], break_comparison_df['constrained_total_stop'], alpha=0.5, s=20)\n",
            "max_val = max(break_comparison_df['baseline_total_stop'].max(), break_comparison_df['constrained_total_stop'].max())\n",
            "ax2.plot([0, max_val], [0, max_val], 'r--', label='Equal stop time')\n",
            "ax2.set_xlabel('Baseline Total Stop Time (h)')\n",
            "ax2.set_ylabel('Constrained Total Stop Time (h)')\n",
            "ax2.set_title('Baseline vs Constrained Stop Time')\n",
            "ax2.legend()\n",
            "\n",
            "# 3. Stop time difference vs route length\n",
            "ax3 = axes[2]\n",
            "ax3.scatter(break_comparison_df['path_length'], break_comparison_df['diff_total_stop'], alpha=0.5, s=20)\n",
            "ax3.axhline(0, color='red', linestyle='--', linewidth=1)\n",
            "ax3.set_xlabel('Route Length (km)')\n",
            "ax3.set_ylabel('Stop Time Difference (h)')\n",
            "ax3.set_title('Stop Time Change vs Route Length')\n",
            "\n",
            "plt.tight_layout()\n",
            "plt.savefig('figures/break_time_comparison_both_electrified.pdf', bbox_inches='tight', dpi=150)\n",
            "plt.savefig('figures/break_time_comparison_both_electrified.png', bbox_inches='tight', dpi=150)\n",
            "plt.show()\n",
            "print(\"Saved: figures/break_time_comparison_both_electrified.pdf\")"
        ]
    },
    # Code cell for top changes - FIXED COLUMN NAMES
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Top 10 OD pairs with largest stop time changes\n",
            "print(\"=\"*80)\n",
            "print(\"TOP 10 OD PAIRS WITH LARGEST STOP TIME INCREASE\")\n",
            "print(\"=\"*80)\n",
            "top_increase = break_comparison_df.nlargest(10, 'diff_total_stop')[['odpair_id', 'path_id', 'path_length', 'baseline_total_stop', 'constrained_total_stop', 'diff_total_stop']]\n",
            "print(top_increase.to_string(index=False))\n",
            "\n",
            "print(\"\\n\" + \"=\"*80)\n",
            "print(\"TOP 10 OD PAIRS WITH LARGEST STOP TIME DECREASE\")\n",
            "print(\"=\"*80)\n",
            "top_decrease = break_comparison_df.nsmallest(10, 'diff_total_stop')[['odpair_id', 'path_id', 'path_length', 'baseline_total_stop', 'constrained_total_stop', 'diff_total_stop']]\n",
            "print(top_decrease.to_string(index=False))"
        ]
    }
]

# Add the new cells at the end
nb['cells'].extend(new_cells)

# Save the updated notebook
with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)

print(f"Fixed: replaced last 5 cells with corrected column names")
print(f"Total cells now: {len(nb['cells'])}")
