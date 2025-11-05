"""
Analyze all sub-border regions and create comparison plots
"""
from sub_border_regions_cross_case import *
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ============================================================================
# CELL 1: Analyze All Three Sub-Regions
# ============================================================================

case_labels = {
    "case_20251022_152235_var_var": "Var-Var",
    "case_20251022_152358_var_uni": "Var-Uni",
    "case_20251022_153056_uni_var": "Uni-Var",
    "case_20251022_153317_uni_uni": "Uni-Uni"
}

sub_region_names = [
    'Austria-Germany-Italy',
    'Denmark-Germany',
    'Norway-Sweden'
]

years_to_plot = [2030, 2040, 2050]

# Store results for all sub-regions
all_results = {}

for sub_region_name in sub_region_names:
    print(f"\n{'='*80}")
    print(f"Analyzing: {sub_region_name}")
    print('='*80)

    df_comparison, df_summary = analyze_sub_region_cross_case_preloaded(
        loaded_runs=loaded_runs,
        case_labels=case_labels,
        sub_region_name=sub_region_name,
        years_to_plot=years_to_plot,
        baseline_case='Var-Var',
        show_plots=False,  # Don't show plots yet
        verbose=True
    )

    all_results[sub_region_name] = {
        'comparison': df_comparison,
        'summary': df_summary
    }


# ============================================================================
# CELL 2: Combined Comparison Plot - All Sub-Regions for One Year
# ============================================================================

year = 2040  # Change to 2030 or 2050 if desired

fig, axes = plt.subplots(1, 3, figsize=(20, 6))

case_colors = {
    'Var-Var': '#1f77b4',
    'Var-Uni': '#ff7f0e',
    'Uni-Var': '#2ca02c',
    'Uni-Uni': '#d62728'
}

for idx, sub_region_name in enumerate(sub_region_names):
    ax = axes[idx]
    df_comparison = all_results[sub_region_name]['comparison']

    # Filter to selected year
    year_data = df_comparison[df_comparison['year'] == year]

    if len(year_data) == 0:
        ax.text(0.5, 0.5, f'No data for {year}',
               ha='center', va='center', transform=ax.transAxes)
        ax.set_title(sub_region_name)
        continue

    countries = sorted(year_data['country'].unique())
    cases = sorted(year_data['case'].unique())

    x = np.arange(len(countries))
    width = 0.8 / len(cases)

    for i, case in enumerate(cases):
        case_data = year_data[year_data['case'] == case]
        values = [case_data[case_data['country'] == c]['electrification_pct'].values[0]
                 if len(case_data[case_data['country'] == c]) > 0 else 0
                 for c in countries]

        offset = width * (i - len(cases)/2 + 0.5)
        ax.bar(x + offset, values, width, label=case,
               alpha=0.85, color=case_colors[case])

    ax.set_xlabel('Country', fontsize=12, fontweight='bold')
    ax.set_ylabel('Electrification %', fontsize=12, fontweight='bold')
    ax.set_title(f'{sub_region_name}\nYear {year}',
                fontsize=13, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(countries, fontsize=11)
    ax.legend(title='Scenario', fontsize=10, title_fontsize=11, loc='upper left')
    ax.grid(True, alpha=0.3, axis='y', linestyle='--')
    ax.set_ylim(0, 100)
    ax.set_axisbelow(True)

plt.tight_layout()
plt.savefig(f'all_subregions_comparison_{year}.png', dpi=300, bbox_inches='tight')
plt.show()


# ============================================================================
# CELL 3: Summary Table - Average Electrification Across Sub-Regions
# ============================================================================

summary_records = []

for sub_region_name in sub_region_names:
    df_summary = all_results[sub_region_name]['summary']

    for _, row in df_summary.iterrows():
        summary_records.append({
            'Sub-Region': sub_region_name,
            'Case': row['Case'],
            'Year': row['Year'],
            'Avg Electrification %': row['Avg Electrification %'],
            'Total Electricity (MWh)': row['Total Electricity (MWh)']
        })

df_combined_summary = pd.DataFrame(summary_records)

print("\n" + "="*100)
print("COMBINED SUMMARY: ALL SUB-BORDER REGIONS")
print("="*100)
print(df_combined_summary.to_string(index=False))
print("="*100)

# Pivot for easier comparison
for year in years_to_plot:
    print(f"\n{'='*80}")
    print(f"YEAR {year} - AVERAGE ELECTRIFICATION % BY SUB-REGION")
    print('='*80)

    year_data = df_combined_summary[df_combined_summary['Year'] == year]
    pivot = year_data.pivot(index='Case',
                            columns='Sub-Region',
                            values='Avg Electrification %')
    print(pivot.to_string())
    print('='*80)


# ============================================================================
# CELL 4: Time Series Comparison - All Sub-Regions by Scenario
# ============================================================================

fig, axes = plt.subplots(2, 2, figsize=(16, 12))
axes = axes.ravel()

scenarios = sorted(case_labels.values())

for idx, scenario in enumerate(scenarios):
    ax = axes[idx]

    for sub_region_name in sub_region_names:
        df_comparison = all_results[sub_region_name]['comparison']
        scenario_data = df_comparison[df_comparison['case'] == scenario]

        # Calculate average electrification across all countries per year
        avg_by_year = scenario_data.groupby('year')['electrification_pct'].mean()

        if len(avg_by_year) > 0:
            ax.plot(avg_by_year.index, avg_by_year.values,
                   marker='o', label=sub_region_name, linewidth=2.5, markersize=8)

    ax.set_xlabel('Year', fontsize=12, fontweight='bold')
    ax.set_ylabel('Average Electrification %', fontsize=12, fontweight='bold')
    ax.set_title(f'{scenario}', fontsize=13, fontweight='bold')
    ax.legend(fontsize=10, loc='best')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_ylim(0, 100)
    ax.set_axisbelow(True)

fig.suptitle('Sub-Border Region Comparison Across Scenarios',
            fontsize=16, fontweight='bold', y=0.995)

plt.tight_layout()
plt.savefig('subregions_time_series_comparison.png', dpi=300, bbox_inches='tight')
plt.show()


# ============================================================================
# CELL 5: Export Results
# ============================================================================

# Export all comparison data
for sub_region_name, results in all_results.items():
    filename = f"comparison_{sub_region_name.replace('-', '_').replace(' ', '_')}.csv"
    results['comparison'].to_csv(filename, index=False)
    print(f"Exported: {filename}")

# Export combined summary
df_combined_summary.to_csv('combined_summary_all_subregions.csv', index=False)
print("Exported: combined_summary_all_subregions.csv")

print("\n✓ Analysis complete!")
