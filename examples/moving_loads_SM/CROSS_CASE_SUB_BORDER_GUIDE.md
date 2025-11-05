# Cross-Case Sub-Border Region Comparison Guide

## Overview

This guide explains how to compare the same sub-border region across multiple case studies/scenarios. This is essential for analyzing how different policy scenarios, infrastructure assumptions, or parameter settings affect electrification in specific geographic regions like the Austria-Germany-Italy border cluster.

## Your Case Studies

Based on your `results_representation.ipynb`, you have 4 case studies with a 2x2 design (var/uni × var/uni):

| Case Label | Case Study Name | Run ID |
|------------|----------------|--------|
| Var-Var | case_20251022_152235_var_var | case_20251022_152235_var_var_cs_2025-10-23_08-22-09 |
| Var-Uni | case_20251022_152358_var_uni | case_20251022_152358_var_uni_cs_2025-10-23_08-56-23 |
| Uni-Var | case_20251022_153056_uni_var | case_20251022_153056_uni_var_cs_2025-10-23_09-36-37 |
| Uni-Uni | case_20251022_153317_uni_uni | case_20251022_153317_uni_uni_cs_2025-10-23_10-09-32 |

## Quick Start

### Basic Cross-Case Comparison

```python
from sub_border_regions_cross_case import analyze_sub_region_cross_case

# Define your cases
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

# Compare Austria-Germany-Italy cluster across all cases
df_comparison, df_summary = analyze_sub_region_cross_case(
    cases=cases,
    sub_region_name='Austria-Germany-Italy',
    results_folder='results',
    years_to_plot=[2030, 2040, 2050],
    baseline_case='Var-Var',
    show_plots=True,
    verbose=True
)
```

## What You Get

### 1. Comparison DataFrame

Contains detailed electrification data for each case-country-year combination:

| Column | Description |
|--------|-------------|
| `case` | Case label (e.g., 'Var-Var') |
| `country` | Country code (AT, DE, IT) |
| `year` | Analysis year |
| `electrification_pct` | Percentage of electrified transport |
| `electricity` | Electricity consumption (MWh) |
| `total_fuel` | Total fuel consumption (MWh) |
| `sub_region` | Sub-border region name |

### 2. Summary DataFrame

Aggregated statistics by case and year:

| Column | Description |
|--------|-------------|
| `Case` | Case label |
| `Year` | Year |
| `Countries` | Number of countries with data |
| `Avg Electrification %` | Average across countries |
| `Min Electrification %` | Minimum value |
| `Max Electrification %` | Maximum value |
| `Total Electricity (MWh)` | Total electricity consumption |
| `Total Fuel (MWh)` | Total fuel consumption |

### 3. Visualizations

The module generates three types of plots automatically:

#### Grouped Bar Charts (by year)
Shows electrification by country with grouped bars for each case

#### Line Charts (by country)
Tracks electrification over time for each case, separated by country

#### Delta Charts (relative to baseline)
Shows differences from baseline case, with green bars for improvements and red for decreases

## Advanced Usage

### Compare Specific Cases Only

```python
# Compare only two cases
cases_subset = {
    'Var-Var': ('case_20251022_152235_var_var',
                'case_20251022_152235_var_var_cs_2025-10-23_08-22-09'),
    'Uni-Uni': ('case_20251022_153317_uni_uni',
                'case_20251022_153317_uni_uni_cs_2025-10-23_10-09-32')
}

df_comparison = compare_sub_region_across_cases(
    cases=cases_subset,
    sub_region_name='Austria-Germany-Italy',
    years_to_plot=[2030, 2050],
    verbose=True
)
```

### Custom Delta Analysis

```python
from sub_border_regions_cross_case import plot_delta_across_cases

# Create delta plot comparing to a specific baseline
fig, axes = plot_delta_across_cases(
    df_comparison,
    sub_region_name='Austria-Germany-Italy',
    baseline_case='Var-Var',
    years_to_plot=[2030, 2040, 2050]
)
plt.savefig('austria_cluster_deltas.png', dpi=300, bbox_inches='tight')
```

### Create Custom Visualizations

```python
import matplotlib.pyplot as plt
import seaborn as sns

# Example: Heatmap of electrification across cases and countries for 2050
data_2050 = df_comparison[df_comparison['year'] == 2050]
pivot = data_2050.pivot(index='country', columns='case', values='electrification_pct')

plt.figure(figsize=(10, 6))
sns.heatmap(pivot, annot=True, fmt='.1f', cmap='RdYlGn', vmin=0, vmax=100)
plt.title('2050 Electrification: Austria-Germany-Italy Border', fontsize=14, fontweight='bold')
plt.xlabel('Case')
plt.ylabel('Country')
plt.tight_layout()
plt.show()
```

### Country-Specific Analysis

```python
# Focus on Austria only
austria_data = df_comparison[df_comparison['country'] == 'AT']

# Compare across cases
austria_pivot = austria_data.pivot(index='year', columns='case', values='electrification_pct')
print("\nAustria Electrification (%) by Case:")
print(austria_pivot)

# Plot
austria_pivot.plot(kind='line', marker='o', figsize=(10, 6))
plt.title('Austria (Border Regions): Electrification Across Cases')
plt.ylabel('Electrification %')
plt.xlabel('Year')
plt.grid(True, alpha=0.3)
plt.ylim(0, 100)
plt.show()
```

## Analytical Questions You Can Answer

### 1. Which case achieves highest electrification?
```python
# For each year, identify best performing case
for year in [2030, 2040, 2050]:
    year_summary = df_summary[df_summary['Year'] == year]
    best = year_summary.loc[year_summary['Avg Electrification %'].idxmax()]
    print(f"{year}: {best['Case']} with {best['Avg Electrification %']:.2f}%")
```

### 2. How much do results vary across countries within a case?
```python
# Calculate coefficient of variation for each case-year
for case in df_comparison['case'].unique():
    case_data = df_comparison[df_comparison['case'] == case]
    for year in [2030, 2040, 2050]:
        year_data = case_data[case_data['year'] == year]
        mean = year_data['electrification_pct'].mean()
        std = year_data['electrification_pct'].std()
        cv = (std / mean) * 100 if mean > 0 else 0
        print(f"{case} {year}: CV = {cv:.1f}%")
```

### 3. What's the delta between best and worst case?
```python
# Calculate range for each country-year
for year in [2030, 2040, 2050]:
    print(f"\n{year}:")
    year_data = df_comparison[df_comparison['year'] == year]
    for country in sorted(year_data['country'].unique()):
        country_data = year_data[year_data['country'] == country]
        min_val = country_data['electrification_pct'].min()
        max_val = country_data['electrification_pct'].max()
        range_val = max_val - min_val
        print(f"  {country}: {min_val:.1f}% to {max_val:.1f}% (range: {range_val:.1f} pp)")
```

### 4. How does electricity consumption differ?
```python
# Compare total electricity by case
elec_by_case = df_comparison.groupby(['case', 'year'])['electricity'].sum().reset_index()
elec_pivot = elec_by_case.pivot(index='year', columns='case', values='electricity')

print("\nTotal Electricity Consumption (MWh):")
print(elec_pivot)

# Calculate percentage difference from baseline
baseline_elec = elec_pivot['Var-Var']
for case in ['Var-Uni', 'Uni-Var', 'Uni-Uni']:
    pct_diff = ((elec_pivot[case] - baseline_elec) / baseline_elec) * 100
    print(f"\n{case} vs Var-Var:")
    print(pct_diff)
```

## Integration with Existing Notebooks

### Option 1: Add to results_representation.ipynb

Copy cells from `notebook_cell_cross_case_sub_border.py` into your existing notebook.

### Option 2: Import in Your Analysis

```python
# In your notebook
from sub_border_regions_cross_case import analyze_sub_region_cross_case

# Use the pre-loaded cases dict
df_austria_comp, df_austria_sum = analyze_sub_region_cross_case(
    cases=cases,  # Your existing cases dict
    sub_region_name='Austria-Germany-Italy',
    results_folder='results',
    years_to_plot=[2030, 2040, 2050],
    show_plots=True
)
```

## Comparing Multiple Sub-Border Regions Across Cases

```python
# Compare all three sub-border regions across all cases
sub_regions = ['Austria-Germany-Italy', 'Denmark-Germany', 'Norway-Sweden']
all_results = {}

for sub_region in sub_regions:
    df_comp, df_sum = analyze_sub_region_cross_case(
        cases=cases,
        sub_region_name=sub_region,
        results_folder='results',
        years_to_plot=[2030, 2040, 2050],
        show_plots=False,
        verbose=False
    )
    all_results[sub_region] = {'comparison': df_comp, 'summary': df_sum}

# Create combined summary
combined_summary = []
for sub_region, results in all_results.items():
    df_sum = results['summary'].copy()
    df_sum['Sub-Region'] = sub_region
    combined_summary.append(df_sum)

df_combined = pd.concat(combined_summary, ignore_index=True)
print("\nCombined Summary Across All Sub-Border Regions:")
print(df_combined)
```

## Export Options

### CSV Files
```python
# Export main comparison
df_comparison.to_csv('austria_cross_case_comparison.csv', index=False)

# Export summary
df_summary.to_csv('austria_cross_case_summary.csv', index=False)
```

### LaTeX Tables
```python
# Create LaTeX-ready summary table
latex_table = df_summary.pivot_table(
    index='Case',
    columns='Year',
    values='Avg Electrification %'
)
print(latex_table.to_latex(float_format='%.1f'))
```

### Excel with Multiple Sheets
```python
with pd.ExcelWriter('austria_cross_case_analysis.xlsx') as writer:
    df_comparison.to_excel(writer, sheet_name='Detailed Data', index=False)
    df_summary.to_excel(writer, sheet_name='Summary', index=False)

    # Add country-specific sheets
    for country in df_comparison['country'].unique():
        country_data = df_comparison[df_comparison['country'] == country]
        country_data.to_excel(writer, sheet_name=f'Country_{country}', index=False)
```

## Files in This Module

- **`sub_border_regions_cross_case.py`**: Main cross-case comparison module
- **`notebook_cell_cross_case_sub_border.py`**: Ready-to-use notebook cells
- **`CROSS_CASE_SUB_BORDER_GUIDE.md`**: This guide

## Related Documentation

- `SUB_BORDER_REGIONS_GUIDE.md` - Single-case sub-border region analysis
- `BORDER_REGIONS_README.md` - Border region identification methodology
- `border_region_electrification_analysis.py` - All border regions analysis

## Troubleshooting

### Issue: "No data found for case X"
**Solution**: Check that case_study_name and run_id match exactly with folder names in `results/`

### Issue: "KeyError: 'f'"
**Solution**: Ensure the flow variable 'f' exists in your output files. Check `variables_to_read` parameter.

### Issue: Empty DataFrames
**Solution**: Verify that your years_to_plot match years in your data. Use `verbose=True` to see what's being loaded.

### Issue: Missing countries in comparison
**Solution**: Check that all cases have the same NUTS2 regions defined. Some cases may have filtered regions.

## Best Practices for Scientific Analysis

1. **Always specify a baseline**: Use the most "neutral" or "standard" case as baseline for delta calculations

2. **Document case differences**: Clearly note what varies between cases (infrastructure, policy, parameters)

3. **Check data consistency**: Verify all cases use the same geographic boundaries and input assumptions

4. **Statistical significance**: When differences are small (<5 percentage points), consider if they're meaningful given model uncertainty

5. **Export reproducibility info**: Save case definitions and parameters with your results

6. **Visualize uncertainty**: If you have multiple runs per case, show error bars or ranges
