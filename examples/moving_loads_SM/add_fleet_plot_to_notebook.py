"""Script to add stacked bar plot cells to the charging_constraint_comparison.ipynb notebook."""

import json

# Read the notebook
with open('charging_constraint_comparison.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Create new markdown cell for section header
markdown_cell = {
    'cell_type': 'markdown',
    'metadata': {},
    'source': [
        '## Fleet Composition by Technology (ICEV vs BEV)\n',
        '\n',
        'This section shows stacked bar charts comparing fleet composition between BASELINE (no charging-at-breaks constraint) and CONSTRAINED (charging only at mandatory breaks) scenarios.'
    ]
}

# Create code cell for stacked bar plot - build source as a list of strings
code_source = '''def plot_fleet_by_technology_comparison(scenario="scenario_000"):
    """Plot stacked bar chart comparing fleet composition by technology for baseline vs constrained."""
    from collections import defaultdict
    import numpy as np

    # Load h_dict from both runs
    baseline_folder = os.path.join(BASELINE_DIR, scenario)
    constrained_folder = os.path.join(CONSTRAINED_DIR, scenario)

    baseline_h_file = get_latest_file(baseline_folder, "h_dict.yaml")
    constrained_h_file = get_latest_file(constrained_folder, "h_dict.yaml")

    if not baseline_h_file or not constrained_h_file:
        print(f"Missing h_dict files for {scenario}")
        return

    with open(baseline_h_file, "r") as f:
        baseline_h = yaml.safe_load(f)
    with open(constrained_h_file, "r") as f:
        constrained_h = yaml.safe_load(f)

    # Aggregate by year and tech for both
    def aggregate_h(h_dict):
        h_by_year = defaultdict(lambda: defaultdict(float))
        for key, value in h_dict.items():
            parts = key.strip("()").split(",")
            year = int(parts[0].strip())
            tech = int(parts[2].strip())  # tech_vehicle_id: 0=ICEV, 1=BEV
            h_by_year[year][tech] += float(value)
        return h_by_year

    baseline_agg = aggregate_h(baseline_h)
    constrained_agg = aggregate_h(constrained_h)

    years = sorted(set(baseline_agg.keys()) | set(constrained_agg.keys()))

    # Prepare data
    baseline_icev = [baseline_agg[y].get(0, 0) for y in years]
    baseline_bev = [baseline_agg[y].get(1, 0) for y in years]
    constrained_icev = [constrained_agg[y].get(0, 0) for y in years]
    constrained_bev = [constrained_agg[y].get(1, 0) for y in years]

    # Create figure
    fig, axes = plt.subplots(1, 2, figsize=(14, 6), sharey=True)

    x = np.arange(len(years))
    width = 0.7

    # BASELINE subplot
    ax1 = axes[0]
    bars1_icev = ax1.bar(x, baseline_icev, width, label="ICEV", color="#d62728", alpha=0.8)
    bars1_bev = ax1.bar(x, baseline_bev, width, bottom=baseline_icev, label="BEV", color="#2ca02c", alpha=0.8)
    ax1.set_xlabel("Year", fontsize=12)
    ax1.set_ylabel("Number of Vehicles", fontsize=12)
    ax1.set_title(f"BASELINE (no charging constraint) - {scenario}", fontsize=12)
    ax1.set_xticks(x)
    ax1.set_xticklabels(years, rotation=45)
    ax1.legend(loc="upper left")

    # Add BEV % labels
    for i, (icev, bev) in enumerate(zip(baseline_icev, baseline_bev)):
        total = icev + bev
        bev_pct = 100 * bev / total if total > 0 else 0
        ax1.annotate(f"{bev_pct:.0f}%", xy=(i, total), ha="center", va="bottom", fontsize=8, fontweight="bold")

    # CONSTRAINED subplot
    ax2 = axes[1]
    bars2_icev = ax2.bar(x, constrained_icev, width, label="ICEV", color="#d62728", alpha=0.8)
    bars2_bev = ax2.bar(x, constrained_bev, width, bottom=constrained_icev, label="BEV", color="#2ca02c", alpha=0.8)
    ax2.set_xlabel("Year", fontsize=12)
    ax2.set_title(f"CONSTRAINED (charging at breaks) - {scenario}", fontsize=12)
    ax2.set_xticks(x)
    ax2.set_xticklabels(years, rotation=45)
    ax2.legend(loc="upper left")

    # Add BEV % labels
    for i, (icev, bev) in enumerate(zip(constrained_icev, constrained_bev)):
        total = icev + bev
        bev_pct = 100 * bev / total if total > 0 else 0
        ax2.annotate(f"{bev_pct:.0f}%", xy=(i, total), ha="center", va="bottom", fontsize=8, fontweight="bold")

    plt.tight_layout()
    plt.savefig(f"figures/fleet_by_technology_comparison_{scenario}.pdf", dpi=150, bbox_inches="tight")
    plt.savefig(f"figures/fleet_by_technology_comparison_{scenario}.png", dpi=150, bbox_inches="tight")
    print(f"Saved: figures/fleet_by_technology_comparison_{scenario}.pdf")
    plt.show()

    # Print summary statistics
    print(f"\\nFleet Summary for {scenario}:")
    header = f"{'Year':<8} {'Base ICEV':<12} {'Base BEV':<12} {'Base BEV%':<12} {'Const ICEV':<12} {'Const BEV':<12} {'Const BEV%':<12}"
    print(header)
    print("-" * len(header))
    for i, year in enumerate(years):
        b_total = baseline_icev[i] + baseline_bev[i]
        c_total = constrained_icev[i] + constrained_bev[i]
        b_pct = 100 * baseline_bev[i] / b_total if b_total > 0 else 0
        c_pct = 100 * constrained_bev[i] / c_total if c_total > 0 else 0
        print(f"{year:<8} {baseline_icev[i]:<12.1f} {baseline_bev[i]:<12.1f} {b_pct:<12.1f} {constrained_icev[i]:<12.1f} {constrained_bev[i]:<12.1f} {c_pct:<12.1f}")

# Run for scenario_000
plot_fleet_by_technology_comparison("scenario_000")
'''

code_cell = {
    'cell_type': 'code',
    'execution_count': None,
    'metadata': {},
    'outputs': [],
    'source': code_source.split('\n')
}

# Convert source lines to proper format (add \n to each line except last)
code_cell['source'] = [line + '\n' if i < len(code_cell['source']) - 1 else line
                       for i, line in enumerate(code_cell['source'])]

# Add cells to notebook
nb['cells'].append(markdown_cell)
nb['cells'].append(code_cell)

# Save the notebook
with open('charging_constraint_comparison.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)

print('Added 2 new cells to the notebook:')
print('  - Markdown header for Fleet Composition section')
print('  - Code cell with stacked bar plot function')
print(f'Total cells now: {len(nb["cells"])}')
