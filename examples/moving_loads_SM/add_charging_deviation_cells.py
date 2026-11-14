"""
Add charging deviation analysis cells to charging_constraint_comparison.ipynb
Analyzes how much BEV charging in the baseline case deviates from break locations.
"""

import json

# Load the existing notebook
notebook_path = r"C:\Users\simuser\Documents\AntoniaGolab\Scand_Med_analysis\SM_baby_2\iDesignRES_transcompmodel\examples\moving_loads_SM\charging_constraint_comparison.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# New cells to add
new_cells = [
    # Markdown header
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## 7. Baseline Charging Deviation Analysis\n",
            "\n",
            "This section analyzes how much BEV charging in the **baseline** case (without `constraint_charging_at_breaks_only`)\n",
            "deviates from mandatory break locations.\n",
            "\n",
            "Key question: What percentage of BEV charging happens at non-break locations in the baseline?\n",
            "\n",
            "This shows the \"opportunity cost\" of not enforcing charging at breaks - the baseline optimizer\n",
            "spreads charging across the entire route rather than concentrating it at break locations."
        ]
    },
    # Code cell to load MandatoryBreaks and build lookup
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Load MandatoryBreaks to identify allowed break locations\n",
            "import re\n",
            "from collections import defaultdict\n",
            "\n",
            "print('Loading MandatoryBreaks...')\n",
            "with open(os.path.join(SCENARIO_DIR, 'MandatoryBreaks.yaml'), 'r') as f:\n",
            "    mandatory_breaks = yaml.safe_load(f)\n",
            "\n",
            "# Build lookup: path_id -> set of break geo_ids\n",
            "break_geo_ids_by_path = defaultdict(set)\n",
            "for mb in mandatory_breaks:\n",
            "    break_geo_ids_by_path[mb['path_id']].add(mb['latest_geo_id'])\n",
            "\n",
            "print(f'Loaded {len(mandatory_breaks)} mandatory breaks for {len(break_geo_ids_by_path)} paths')"
        ]
    },
    # Code cell to analyze baseline charging deviation for all years
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Analyze baseline BEV charging deviation from break locations - ALL YEARS\n",
            "\n",
            "def parse_s_key(key_str):\n",
            "    \"\"\"Parse the s variable key string to extract components.\"\"\"\n",
            "    numbers = re.findall(r'-?\\d+', key_str)\n",
            "    year = int(numbers[0])\n",
            "    path_id = int(numbers[3])\n",
            "    geo_id = int(numbers[4])\n",
            "    tv_id = int(numbers[5])\n",
            "    return year, path_id, geo_id, tv_id\n",
            "\n",
            "# Load baseline s_dict\n",
            "print('Loading baseline s_dict...')\n",
            "baseline_s_file = None\n",
            "for f in os.listdir(BASELINE_DIR):\n",
            "    if f.endswith('_s_dict.yaml'):\n",
            "        baseline_s_file = os.path.join(BASELINE_DIR, f)\n",
            "        break\n",
            "\n",
            "print(f'Loading: {os.path.basename(baseline_s_file)}')\n",
            "with open(baseline_s_file, 'r') as f:\n",
            "    baseline_s = yaml.safe_load(f)\n",
            "\n",
            "print(f'Loaded {len(baseline_s):,} s variable entries')\n",
            "\n",
            "# Analyze by year (BEV only = tv_id=1)\n",
            "deviation_by_year = defaultdict(lambda: {\n",
            "    'at_break_entries': 0, 'at_break_kwh': 0.0,\n",
            "    'not_at_break_entries': 0, 'not_at_break_kwh': 0.0,\n",
            "    'short_path_entries': 0, 'short_path_kwh': 0.0\n",
            "})\n",
            "\n",
            "print('\\nAnalyzing BEV charging locations...')\n",
            "for key, value in baseline_s.items():\n",
            "    val = float(value)\n",
            "    if val < 1e-6:\n",
            "        continue\n",
            "    \n",
            "    year, path_id, geo_id, tv_id = parse_s_key(key)\n",
            "    \n",
            "    # BEV only (tv_id=1)\n",
            "    if tv_id != 1:\n",
            "        continue\n",
            "    \n",
            "    if path_id in break_geo_ids_by_path:\n",
            "        allowed = break_geo_ids_by_path[path_id]\n",
            "        if geo_id in allowed:\n",
            "            deviation_by_year[year]['at_break_entries'] += 1\n",
            "            deviation_by_year[year]['at_break_kwh'] += val\n",
            "        else:\n",
            "            deviation_by_year[year]['not_at_break_entries'] += 1\n",
            "            deviation_by_year[year]['not_at_break_kwh'] += val\n",
            "    else:\n",
            "        deviation_by_year[year]['short_path_entries'] += 1\n",
            "        deviation_by_year[year]['short_path_kwh'] += val\n",
            "\n",
            "print('Analysis complete!')"
        ]
    },
    # Code cell to display results table
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Display baseline charging deviation results\n",
            "print('='*100)\n",
            "print('BASELINE BEV CHARGING DEVIATION FROM MANDATORY BREAK LOCATIONS')\n",
            "print('='*100)\n",
            "print()\n",
            "print('In the baseline case (without constraint_charging_at_breaks_only), BEV charging can happen anywhere.')\n",
            "print('This analysis shows what percentage of charging occurs at non-break locations.')\n",
            "print()\n",
            "\n",
            "# Create summary dataframe\n",
            "deviation_data = []\n",
            "for year in sorted(deviation_by_year.keys()):\n",
            "    d = deviation_by_year[year]\n",
            "    total_kwh = d['at_break_kwh'] + d['not_at_break_kwh'] + d['short_path_kwh']\n",
            "    total_entries = d['at_break_entries'] + d['not_at_break_entries'] + d['short_path_entries']\n",
            "    \n",
            "    if total_kwh > 0:\n",
            "        pct_at_break = 100 * d['at_break_kwh'] / total_kwh\n",
            "        pct_not_at_break = 100 * d['not_at_break_kwh'] / total_kwh\n",
            "        pct_short = 100 * d['short_path_kwh'] / total_kwh\n",
            "    else:\n",
            "        pct_at_break = pct_not_at_break = pct_short = 0\n",
            "    \n",
            "    deviation_data.append({\n",
            "        'Year': year,\n",
            "        'Total BEV kWh': total_kwh,\n",
            "        'At Break kWh': d['at_break_kwh'],\n",
            "        'Not at Break kWh': d['not_at_break_kwh'],\n",
            "        '% At Break': pct_at_break,\n",
            "        '% Not at Break': pct_not_at_break,\n",
            "        'Entries at Break': d['at_break_entries'],\n",
            "        'Entries NOT at Break': d['not_at_break_entries']\n",
            "    })\n",
            "\n",
            "deviation_df = pd.DataFrame(deviation_data)\n",
            "print(deviation_df.to_string(index=False))\n",
            "\n",
            "# Summary statistics\n",
            "print()\n",
            "print('='*100)\n",
            "print('SUMMARY')\n",
            "print('='*100)\n",
            "total_at_break = deviation_df['At Break kWh'].sum()\n",
            "total_not_at_break = deviation_df['Not at Break kWh'].sum()\n",
            "total_all = total_at_break + total_not_at_break\n",
            "print(f'Total BEV energy charged (all years): {total_all:,.0f} kWh')\n",
            "print(f'  At break locations: {total_at_break:,.0f} kWh ({100*total_at_break/total_all:.1f}%)')\n",
            "print(f'  NOT at break locations: {total_not_at_break:,.0f} kWh ({100*total_not_at_break/total_all:.1f}%)')\n",
            "print()\n",
            "print('*** In the CONSTRAINED case, 100% of charging is forced to break locations ***')"
        ]
    },
    # Code cell to visualize deviation over time
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Visualize baseline charging deviation over time\n",
            "fig, axes = plt.subplots(1, 2, figsize=(14, 5))\n",
            "\n",
            "# 1. Stacked bar chart: kWh at break vs not at break\n",
            "ax1 = axes[0]\n",
            "years = deviation_df['Year'].values\n",
            "at_break = deviation_df['At Break kWh'].values\n",
            "not_at_break = deviation_df['Not at Break kWh'].values\n",
            "\n",
            "ax1.bar(years, at_break, label='At Break Locations', color='green', alpha=0.7)\n",
            "ax1.bar(years, not_at_break, bottom=at_break, label='NOT at Break Locations', color='red', alpha=0.7)\n",
            "ax1.set_xlabel('Year')\n",
            "ax1.set_ylabel('BEV Charging Energy (kWh)')\n",
            "ax1.set_title('Baseline: BEV Charging Location Distribution')\n",
            "ax1.legend()\n",
            "ax1.tick_params(axis='x', rotation=45)\n",
            "\n",
            "# 2. Line chart: percentage not at break over time\n",
            "ax2 = axes[1]\n",
            "ax2.plot(years, deviation_df['% Not at Break'].values, 'ro-', linewidth=2, markersize=8)\n",
            "ax2.axhline(0, color='green', linestyle='--', linewidth=2, label='Constrained case (0%)')\n",
            "ax2.fill_between(years, 0, deviation_df['% Not at Break'].values, alpha=0.3, color='red')\n",
            "ax2.set_xlabel('Year')\n",
            "ax2.set_ylabel('% of BEV Charging NOT at Break Locations')\n",
            "ax2.set_title('Baseline: Deviation from Break-Only Charging')\n",
            "ax2.set_ylim(0, 100)\n",
            "ax2.legend()\n",
            "ax2.tick_params(axis='x', rotation=45)\n",
            "\n",
            "plt.tight_layout()\n",
            "plt.savefig('figures/baseline_charging_deviation_from_breaks.pdf', bbox_inches='tight', dpi=150)\n",
            "plt.savefig('figures/baseline_charging_deviation_from_breaks.png', bbox_inches='tight', dpi=150)\n",
            "plt.show()\n",
            "print('Saved: figures/baseline_charging_deviation_from_breaks.pdf')"
        ]
    },
    # Code cell for interpretation
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Interpretation\n",
            "avg_deviation = deviation_df['% Not at Break'].mean()\n",
            "max_deviation = deviation_df['% Not at Break'].max()\n",
            "max_dev_year = deviation_df.loc[deviation_df['% Not at Break'].idxmax(), 'Year']\n",
            "\n",
            "print('='*80)\n",
            "print('INTERPRETATION')\n",
            "print('='*80)\n",
            "print(f'''\n",
            "In the BASELINE case (without constraint_charging_at_breaks_only):\n",
            "\n",
            "- Average {avg_deviation:.1f}% of BEV charging energy occurs at NON-break locations\n",
            "- Maximum deviation: {max_deviation:.1f}% in year {max_dev_year}\n",
            "\n",
            "This means the optimizer in the baseline case \"spreads\" charging across the route,\n",
            "not just at mandatory break locations. This is optimal from a pure cost perspective\n",
            "but may not reflect real-world operational constraints where drivers can only\n",
            "charge during their mandatory rest breaks.\n",
            "\n",
            "When the constraint_charging_at_breaks_only is applied (CONSTRAINED case):\n",
            "- 100% of BEV charging is forced to break locations\n",
            "- This may result in slightly longer stop times at breaks\n",
            "- But better reflects real-world truck driver regulations\n",
            "''')"
        ]
    }
]

# Add the new cells at the end
nb['cells'].extend(new_cells)

# Save the updated notebook
with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)

print(f"Successfully added {len(new_cells)} cells to the notebook")
print(f"Total cells now: {len(nb['cells'])}")
