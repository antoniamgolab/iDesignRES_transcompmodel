"""
Notebook Cell Example: Cross-Case Sub-Border Region Comparison

Add these cells to your results_representation.ipynb notebook to compare
sub-border regions across different case studies/scenarios.
"""

# =============================================================================
# CELL 1: Import and Setup for Cross-Case Comparison
# =============================================================================
from sub_border_regions_cross_case import (
    analyze_sub_region_cross_case,
    compare_sub_region_across_cases,
    plot_cross_case_comparison,
    plot_delta_across_cases,
    summarize_cross_case_results
)
from sub_border_regions import get_sub_border_region_info
import pandas as pd
import matplotlib.pyplot as plt

# Define your case studies
cases = {
    'Var-Var': ('case_20251022_152235_var_var',
                'case_20251022_152235_var_var_cs_2025-10-23_08-22-09'),
    'Var-Uni': ('case_20251022_152358_var_uni',
                'case_20251022_152358_var_uni_cs_2025-10-23_08-56-23'),
    'Uni-Var': ('case_20251022_153056_uni_var',
                'case_20251022_153056_uni_var_cs_2025-10-23_09-36-37'),
    'Uni-Uni': ('case_20251022_153317_uni_uni',
                'case_20251022_153317_uni_uni_cs_2025-10-23_10-09-32')
}

# Display available sub-border regions
print("Available Sub-Border Regions for Analysis:")
df_info = get_sub_border_region_info()
display(df_info)


# =============================================================================
# CELL 2: Compare Austria-Germany-Italy Cluster Across All Cases
# =============================================================================
# Run complete cross-case analysis for Austria-Germany-Italy border region
df_austria_comparison, df_austria_summary = analyze_sub_region_cross_case(
    cases=cases,
    sub_region_name='Austria-Germany-Italy',
    results_folder='results',
    years_to_plot=[2030, 2040, 2050],
    baseline_case='Var-Var',  # Use Var-Var as baseline for delta comparisons
    show_plots=True,
    verbose=True
)

# Display raw comparison data
print("\nDetailed Comparison Data:")
display(df_austria_comparison)


# =============================================================================
# CELL 3: Analyze Summary Statistics
# =============================================================================
# Display summary table
print("Summary Statistics by Case and Year:")
display(df_austria_summary)

# Calculate some interesting metrics
print("\n" + "=" * 80)
print("KEY INSIGHTS")
print("=" * 80)

for year in [2030, 2040, 2050]:
    year_data = df_austria_summary[df_austria_summary['Year'] == year]
    if len(year_data) > 0:
        print(f"\nYear {year}:")
        best_case = year_data.loc[year_data['Avg Electrification %'].idxmax()]
        worst_case = year_data.loc[year_data['Avg Electrification %'].idxmin()]

        print(f"  Highest electrification: {best_case['Case']} ({best_case['Avg Electrification %']:.2f}%)")
        print(f"  Lowest electrification: {worst_case['Case']} ({worst_case['Avg Electrification %']:.2f}%)")
        print(f"  Range: {best_case['Avg Electrification %'] - worst_case['Avg Electrification %']:.2f} percentage points")


# =============================================================================
# CELL 4: Country-Specific Analysis Within Austria-Germany-Italy Cluster
# =============================================================================
# Compare how each country performs across cases
countries = sorted(df_austria_comparison['country'].unique())

for country in countries:
    print(f"\n{'=' * 80}")
    print(f"Country: {country}")
    print('=' * 80)

    country_data = df_austria_comparison[df_austria_comparison['country'] == country]

    # Pivot to show case comparison
    pivot = country_data.pivot_table(
        index='year',
        columns='case',
        values='electrification_pct'
    )

    print("\nElectrification % by Case and Year:")
    display(pivot)

    # Calculate which case is best for this country
    for year in [2030, 2040, 2050]:
        year_data = country_data[country_data['year'] == year]
        if len(year_data) > 0:
            best = year_data.loc[year_data['electrification_pct'].idxmax()]
            print(f"  {year}: Best case = {best['case']} ({best['electrification_pct']:.2f}%)")


# =============================================================================
# CELL 5: Custom Delta Analysis - Compare to Baseline
# =============================================================================
# Calculate and visualize differences from baseline case (Var-Var)
baseline_case = 'Var-Var'

# Calculate deltas manually for detailed analysis
baseline_data = df_austria_comparison[df_austria_comparison['case'] == baseline_case].copy()
baseline_data = baseline_data.set_index(['country', 'year'])

df_deltas = []
for case in df_austria_comparison['case'].unique():
    if case == baseline_case:
        continue

    case_data = df_austria_comparison[df_austria_comparison['case'] == case].copy()
    case_data = case_data.set_index(['country', 'year'])

    for idx in case_data.index:
        if idx in baseline_data.index:
            delta_pct = case_data.loc[idx, 'electrification_pct'] - baseline_data.loc[idx, 'electrification_pct']
            delta_elec = case_data.loc[idx, 'electricity'] - baseline_data.loc[idx, 'electricity']

            df_deltas.append({
                'case': case,
                'country': idx[0],
                'year': idx[1],
                'delta_electrification_pct': delta_pct,
                'delta_electricity_MWh': delta_elec,
                'baseline_pct': baseline_data.loc[idx, 'electrification_pct'],
                'case_pct': case_data.loc[idx, 'electrification_pct']
            })

df_deltas = pd.DataFrame(df_deltas)

print(f"\nDifferences from Baseline ({baseline_case}):")
display(df_deltas)

# Summary of deltas
print(f"\n{'=' * 80}")
print(f"DELTA SUMMARY (vs. {baseline_case})")
print('=' * 80)

for case in df_deltas['case'].unique():
    case_deltas = df_deltas[df_deltas['case'] == case]
    print(f"\n{case}:")
    print(f"  Average delta: {case_deltas['delta_electrification_pct'].mean():+.2f} percentage points")
    print(f"  Max increase: {case_deltas['delta_electrification_pct'].max():+.2f} percentage points")
    print(f"  Max decrease: {case_deltas['delta_electrification_pct'].min():+.2f} percentage points")


# =============================================================================
# CELL 6: Compare All Sub-Border Regions Across Cases
# =============================================================================
# If you want to compare multiple sub-border regions across cases
sub_regions_to_compare = ['Austria-Germany-Italy', 'Denmark-Germany', 'Norway-Sweden']

all_comparisons = {}

for sub_region in sub_regions_to_compare:
    print(f"\nAnalyzing: {sub_region}...")

    df_comp = compare_sub_region_across_cases(
        cases=cases,
        sub_region_name=sub_region,
        results_folder='results',
        years_to_plot=[2030, 2040, 2050],
        verbose=False
    )

    all_comparisons[sub_region] = df_comp

    # Quick summary
    summary = df_comp.groupby(['case', 'year'])['electrification_pct'].mean().reset_index()
    print(f"\nAverage electrification by case:")
    display(summary.pivot(index='year', columns='case', values='electrification_pct'))


# =============================================================================
# CELL 7: Create Custom Comparison Visualization
# =============================================================================
# Create a custom plot comparing specific aspects
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# Plot 1: Average electrification by case over time
ax1 = axes[0, 0]
for case in sorted(df_austria_comparison['case'].unique()):
    case_data = df_austria_comparison[df_austria_comparison['case'] == case]
    avg_by_year = case_data.groupby('year')['electrification_pct'].mean()
    ax1.plot(avg_by_year.index, avg_by_year.values, marker='o', label=case, linewidth=2.5)

ax1.set_xlabel('Year', fontsize=12)
ax1.set_ylabel('Average Electrification %', fontsize=12)
ax1.set_title('Austria-Germany-Italy: Average Electrification Across Cases', fontsize=13, fontweight='bold')
ax1.legend(title='Case')
ax1.grid(True, alpha=0.3)
ax1.set_ylim(0, 100)

# Plot 2: Total electricity consumption by case
ax2 = axes[0, 1]
for case in sorted(df_austria_comparison['case'].unique()):
    case_data = df_austria_comparison[df_austria_comparison['case'] == case]
    total_by_year = case_data.groupby('year')['electricity'].sum()
    ax2.plot(total_by_year.index, total_by_year.values, marker='s', label=case, linewidth=2.5)

ax2.set_xlabel('Year', fontsize=12)
ax2.set_ylabel('Total Electricity (MWh)', fontsize=12)
ax2.set_title('Austria-Germany-Italy: Total Electricity Consumption', fontsize=13, fontweight='bold')
ax2.legend(title='Case')
ax2.grid(True, alpha=0.3)

# Plot 3: Electrification by country for 2050
ax3 = axes[1, 0]
year_2050 = df_austria_comparison[df_austria_comparison['year'] == 2050]
if len(year_2050) > 0:
    pivot_2050 = year_2050.pivot_table(
        index='country',
        columns='case',
        values='electrification_pct'
    )
    pivot_2050.plot(kind='bar', ax=ax3, width=0.8, alpha=0.85)
    ax3.set_xlabel('Country', fontsize=12)
    ax3.set_ylabel('Electrification %', fontsize=12)
    ax3.set_title('2050 Electrification by Country', fontsize=13, fontweight='bold')
    ax3.legend(title='Case', fontsize=9)
    ax3.set_xticklabels(ax3.get_xticklabels(), rotation=0)
    ax3.grid(True, alpha=0.3, axis='y')
    ax3.set_ylim(0, 100)

# Plot 4: Standard deviation across countries (measure of variability)
ax4 = axes[1, 1]
for case in sorted(df_austria_comparison['case'].unique()):
    case_data = df_austria_comparison[df_austria_comparison['case'] == case]
    std_by_year = case_data.groupby('year')['electrification_pct'].std()
    ax4.plot(std_by_year.index, std_by_year.values, marker='^', label=case, linewidth=2.5)

ax4.set_xlabel('Year', fontsize=12)
ax4.set_ylabel('Std Dev of Electrification %', fontsize=12)
ax4.set_title('Variability Across Countries', fontsize=13, fontweight='bold')
ax4.legend(title='Case')
ax4.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()


# =============================================================================
# CELL 8: Export Results
# =============================================================================
# Save all results to CSV files

# Main comparison data
df_austria_comparison.to_csv('austria_germany_italy_cross_case_comparison.csv', index=False)
print("Saved: austria_germany_italy_cross_case_comparison.csv")

# Summary statistics
df_austria_summary.to_csv('austria_germany_italy_cross_case_summary.csv', index=False)
print("Saved: austria_germany_italy_cross_case_summary.csv")

# Delta analysis
df_deltas.to_csv('austria_germany_italy_delta_analysis.csv', index=False)
print("Saved: austria_germany_italy_delta_analysis.csv")

# Create a final summary table for LaTeX/paper
final_summary = df_austria_summary.pivot_table(
    index=['Case'],
    columns='Year',
    values='Avg Electrification %'
)
print("\nFinal Summary Table (for paper/presentation):")
display(final_summary)

# Save for LaTeX
final_summary.to_csv('austria_germany_italy_final_summary_table.csv')
print("\nSaved: austria_germany_italy_final_summary_table.csv")
