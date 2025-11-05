# Integration Guide: Sub-Border Region Analysis with Your Notebook

## Overview

The sub-border region cross-case analysis now works **directly with your existing `loaded_runs` dictionary**, so you don't need to reload data or change your data loading process.

## Your Current Notebook Structure

Your `results_representation.ipynb` currently has:

```python
# 1. Your data loading function
def read_data(case_study_name, input_folder_name, variables_to_read, run_id):
    # ... your existing code ...
    return input_data, output_data

# 2. Your case definitions
case_study_names = [
    "case_20251022_152235_var_var",
    "case_20251022_152358_var_uni",
    "case_20251022_153056_uni_var",
    "case_20251022_153317_uni_uni"
]

runs = [
    "case_20251022_152235_var_var_cs_2025-10-23_08-22-09",
    "case_20251022_152358_var_uni_cs_2025-10-23_08-56-23",
    "case_20251022_153056_uni_var_cs_2025-10-23_09-36-37",
    "case_20251022_153317_uni_uni_cs_2025-10-23_10-09-32"
]

# 3. Load all runs
loaded_runs = {}
for ij in range(len(case_study_names)):
    case_study_name = case_study_names[ij]
    results_file = runs[ij]
    input_data, output_data = read_data(results_file, case_study_name, variables_to_read, ij)
    loaded_runs[case_study_name] = {
        "input_data": input_data,
        "output_data": output_data
    }
```

## What to Add - SIMPLE VERSION (One Cell)

**Add this cell immediately after your data loading code:**

```python
# =============================================================================
# Austria-Germany-Italy Border Region: Cross-Case Analysis
# =============================================================================

from sub_border_regions_cross_case import analyze_sub_region_cross_case_preloaded

# Map case names to readable labels
case_labels = {
    "case_20251022_152235_var_var": "Var-Var",
    "case_20251022_152358_var_uni": "Var-Uni",
    "case_20251022_153056_uni_var": "Uni-Var",
    "case_20251022_153317_uni_uni": "Uni-Uni"
}

# Run analysis using your pre-loaded data
df_comparison, df_summary = analyze_sub_region_cross_case_preloaded(
    loaded_runs=loaded_runs,
    case_labels=case_labels,
    sub_region_name='Austria-Germany-Italy',
    years_to_plot=[2030, 2040, 2050],
    baseline_case='Var-Var',
    show_plots=True,
    verbose=True
)

# Display results
display(df_comparison)
display(df_summary)
```

That's it! This will:
- Use your existing `loaded_runs` dictionary
- Analyze the Austria-Germany-Italy border cluster (10 NUTS2 regions)
- Compare all 4 cases
- Generate 3 sets of plots automatically
- Print summary statistics

## Expected Output

### Console Output
```
Processing case: Var-Var
  Study: case_20251022_152235_var_var
  Loaded 15 input structures
  Loaded 9 output variables
  Found 3 country-year combinations

Processing case: Var-Uni
  ...

================================================================================
CROSS-CASE COMPARISON: Austria-Germany-Italy
================================================================================
Case      Year  Countries  Avg Electrification %  Min Electrification %  ...
Var-Var   2030  3          45.23                  38.71                  ...
Var-Uni   2030  3          48.15                  41.22                  ...
...
```

### Visualizations Generated

1. **Grouped Bar Charts** (3 subplots for 2030, 2040, 2050)
   - Each country shown with bars for all 4 cases side-by-side
   - Easy to compare which case performs best

2. **Line Charts by Country** (separate subplot per country)
   - Time trends from 2030-2050
   - All 4 cases shown as different lines
   - Good for understanding temporal evolution

3. **Delta Charts** (differences from Var-Var baseline)
   - Shows how much better/worse each case is vs. baseline
   - Green bars = improvement, Red bars = decline
   - Helps identify which scenarios add value

### DataFrames Returned

**`df_comparison`** (detailed data):
```
   case     country  year  electrification_pct  electricity  total_fuel  sub_region
0  Var-Var  AT       2030  45.2                 56500        125000      Austria-Germany-Italy
1  Var-Var  DE       2030  38.7                 120000       310000      Austria-Germany-Italy
2  Var-Var  IT       2030  52.1                 51000        98000       Austria-Germany-Italy
3  Var-Uni  AT       2030  48.1                 60000        125000      Austria-Germany-Italy
...
```

**`df_summary`** (aggregated statistics):
```
   Case      Year  Countries  Avg Electrification %  Total Electricity (MWh)
0  Var-Var   2030  3          45.33                  227500
1  Var-Uni   2030  3          48.20                  240000
...
```

## What to Add - DETAILED VERSION (Multiple Cells)

If you want more control and custom analysis, add these cells:

### Cell 1: Import and Setup
```python
from sub_border_regions_cross_case import (
    analyze_sub_region_cross_case_preloaded,
    compare_sub_region_across_cases_preloaded,
    plot_cross_case_comparison,
    plot_delta_across_cases
)
from sub_border_regions import get_sub_border_region_info

# Define case labels
case_labels = {
    "case_20251022_152235_var_var": "Var-Var",
    "case_20251022_152358_var_uni": "Var-Uni",
    "case_20251022_153056_uni_var": "Uni-Var",
    "case_20251022_153317_uni_uni": "Uni-Uni"
}

# Show available sub-border regions
print("Available Sub-Border Regions:")
display(get_sub_border_region_info())
```

### Cell 2: Run Analysis
```python
df_comparison, df_summary = analyze_sub_region_cross_case_preloaded(
    loaded_runs=loaded_runs,
    case_labels=case_labels,
    sub_region_name='Austria-Germany-Italy',
    years_to_plot=[2030, 2040, 2050],
    baseline_case='Var-Var',
    show_plots=True,
    verbose=True
)
```

### Cell 3: Country-Specific Analysis
```python
# Analyze Austria only
austria_data = df_comparison[df_comparison['country'] == 'AT']
print("Austria Border Regions - Electrification %:")
austria_pivot = austria_data.pivot(index='year', columns='case', values='electrification_pct')
display(austria_pivot)

# Which case is best for Austria?
for year in [2030, 2040, 2050]:
    year_data = austria_data[austria_data['year'] == year]
    best = year_data.loc[year_data['electrification_pct'].idxmax()]
    print(f"{year}: Best case = {best['case']} ({best['electrification_pct']:.2f}%)")
```

### Cell 4: Export Results
```python
# Save to CSV
df_comparison.to_csv('austria_cluster_comparison.csv', index=False)
df_summary.to_csv('austria_cluster_summary.csv', index=False)

# Create summary table for paper
paper_table = df_summary.pivot_table(
    index='Case',
    columns='Year',
    values='Avg Electrification %'
)
display(paper_table)

# Save for LaTeX
paper_table.to_csv('austria_cluster_paper_table.csv')
print(paper_table.to_latex(float_format='%.1f'))
```

## Comparison with electrification_analysis

You mentioned your existing `electrification_analysis` - the sub-border region analysis works the same way:

| Feature | electrification_analysis | sub_border_regions |
|---------|-------------------------|-------------------|
| Uses your loaded data | ✓ | ✓ |
| No data reloading | ✓ | ✓ |
| Works in notebook | ✓ | ✓ |
| Multiple visualizations | ✓ | ✓ |
| **Focus** | All regions or all borders | Specific border clusters |
| **Cross-case** | Single case | Multiple cases |

## Advantages of Pre-loaded Data Functions

✅ **No file path issues** - Uses data you already loaded
✅ **Faster** - No reloading from disk
✅ **Consistent** - Same data structures you're already using
✅ **Flexible** - Easy to add/remove cases
✅ **Integrated** - Works with your existing workflow

## Troubleshooting

### "KeyError: 'case_20251022_152235_var_var'"
**Solution**: Make sure your `case_labels` keys match the keys in `loaded_runs` exactly

### "NameError: name 'loaded_runs' is not defined"
**Solution**: Make sure you run your data loading cells before the analysis cell

### Empty plots or "No data found"
**Solution**: Check that:
- Your data includes years 2030, 2040, 2050
- The border NUTS2 regions exist in your GeographicElement data
- The 'f' variable is in your output_data

### Want different years
**Solution**: Change `years_to_plot=[2025, 2030, 2035, 2040, 2045, 2050]`

## Adding More Sub-Border Regions

The module includes 3 pre-defined regions:
1. **Austria-Germany-Italy** (10 regions)
2. **Denmark-Germany** (2 regions)
3. **Norway-Sweden** (2 regions)

To analyze a different region, just change:
```python
sub_region_name='Denmark-Germany'
```

To add your own custom regions, edit `SUB_BORDER_REGIONS` in `sub_border_regions.py`.

## Complete Example for Your Notebook

Here's the complete code to add after your data loading:

```python
# After your data loading cells...

# =============================================================================
# AUSTRIA-GERMANY-ITALY BORDER CLUSTER ANALYSIS
# =============================================================================

from sub_border_regions_cross_case import analyze_sub_region_cross_case_preloaded
import matplotlib.pyplot as plt

# Define case labels
case_labels = {
    "case_20251022_152235_var_var": "Var-Var",
    "case_20251022_152358_var_uni": "Var-Uni",
    "case_20251022_153056_uni_var": "Uni-Var",
    "case_20251022_153317_uni_uni": "Uni-Uni"
}

# Run complete analysis
df_comparison, df_summary = analyze_sub_region_cross_case_preloaded(
    loaded_runs=loaded_runs,
    case_labels=case_labels,
    sub_region_name='Austria-Germany-Italy',
    years_to_plot=[2030, 2040, 2050],
    baseline_case='Var-Var',
    show_plots=True,
    verbose=True
)

# Show results
print("\n" + "="*80)
print("DETAILED RESULTS")
print("="*80)
display(df_comparison)

print("\n" + "="*80)
print("SUMMARY STATISTICS")
print("="*80)
display(df_summary)

# Export
df_comparison.to_csv('austria_cluster_comparison.csv', index=False)
df_summary.to_csv('austria_cluster_summary.csv', index=False)
print("\nResults saved to CSV files")
```

## Next Steps

1. **Copy the simple cell** from `NOTEBOOK_CELL_SIMPLE.py` into your notebook
2. **Run it** - it should work immediately with your existing `loaded_runs`
3. **Customize** - adjust years, baseline case, or add more analysis
4. **Export** - save results for your paper

## Support Files

- **`NOTEBOOK_CELL_SIMPLE.py`** - Copy-paste ready cell
- **`notebook_cell_cross_case_sub_border.py`** - More detailed examples
- **`CROSS_CASE_SUB_BORDER_GUIDE.md`** - Complete reference guide

## Questions?

The module is designed to work exactly like your existing analysis functions - just pass in your `loaded_runs` dictionary and get results!
