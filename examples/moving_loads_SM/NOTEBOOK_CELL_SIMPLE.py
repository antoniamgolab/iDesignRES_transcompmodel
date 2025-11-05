"""
SIMPLE NOTEBOOK CELL - Add this right after your data loading cells

This is the simplest way to use the sub-border region cross-case analysis
with your existing loaded_runs dictionary.
"""

# =============================================================================
# CELL: Austria-Germany-Italy Cross-Case Analysis
# =============================================================================

from sub_border_regions_cross_case import analyze_sub_region_cross_case_preloaded

# Define readable labels for your cases
case_labels = {
    "case_20251022_152235_var_var": "Var-Var",
    "case_20251022_152358_var_uni": "Var-Uni",
    "case_20251022_153056_uni_var": "Uni-Var",
    "case_20251022_153317_uni_uni": "Uni-Uni"
}

# Run the analysis using your pre-loaded data
df_comparison, df_summary = analyze_sub_region_cross_case_preloaded(
    loaded_runs=loaded_runs,  # Your existing loaded_runs dictionary
    case_labels=case_labels,
    sub_region_name='Austria-Germany-Italy',
    years_to_plot=[2030, 2040, 2050],
    baseline_case='Var-Var',
    show_plots=True,
    verbose=True
)

# Display results
print("\nComparison Data:")
display(df_comparison)

print("\nSummary Statistics:")
display(df_summary)


# =============================================================================
# OPTIONAL: Export Results
# =============================================================================

# Uncomment to save results
# df_comparison.to_csv('austria_germany_italy_comparison.csv', index=False)
# df_summary.to_csv('austria_germany_italy_summary.csv', index=False)


# =============================================================================
# OPTIONAL: Create Custom Analysis
# =============================================================================

# Example: Compare Austria only across all cases
austria_data = df_comparison[df_comparison['country'] == 'AT']
print("\nAustria Border Regions - Electrification by Case:")
austria_pivot = austria_data.pivot(index='year', columns='case', values='electrification_pct')
display(austria_pivot)

# Plot Austria results
austria_pivot.plot(kind='line', marker='o', figsize=(10, 6))
plt.title('Austria Border Regions: Electrification Across Cases', fontsize=14, fontweight='bold')
plt.ylabel('Electrification %')
plt.xlabel('Year')
plt.grid(True, alpha=0.3)
plt.ylim(0, 100)
plt.legend(title='Case')
plt.show()
