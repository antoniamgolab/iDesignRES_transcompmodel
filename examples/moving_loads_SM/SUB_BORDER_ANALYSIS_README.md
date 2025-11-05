# Sub-Border Region Analysis: Complete Guide

## Overview

This suite of modules enables detailed analysis of electrification patterns in specific geographic clusters of border NUTS2 regions, both within a single case study and across multiple case studies/scenarios.

## What Problem Does This Solve?

**Research Question**: How does transport electrification in border regions differ:
1. Between specific geographic clusters (e.g., Austria-Germany-Italy vs. Denmark-Germany)?
2. Across different policy scenarios or infrastructure assumptions?
3. Between countries within a cross-border region?

**Example Use Case**: Analyzing the Austria-Germany-Italy border corridor (10 NUTS2 regions spanning 3 countries) to understand how different infrastructure rollout strategies affect electrification outcomes.

## Module Structure

### 1. Core Module: `sub_border_regions.py`
**Purpose**: Analyze sub-border regions within a single case study

**Features**:
- Define geographic clusters of border regions
- Calculate electrification by sub-border region
- Compare different clusters within one scenario
- Visualize results by country and region

**When to use**:
- Comparing Austria-Germany-Italy vs. Denmark-Germany in one scenario
- Understanding geographic differences within a single case

### 2. Cross-Case Module: `sub_border_regions_cross_case.py`
**Purpose**: Compare the same sub-border region across multiple case studies

**Features**:
- Load data from multiple case studies
- Compare same region across scenarios
- Calculate deltas relative to baseline
- Generate comparison visualizations

**When to use**:
- Comparing Austria-Germany-Italy across Var-Var, Var-Uni, Uni-Var, Uni-Uni cases
- Understanding impact of different scenarios on same region
- Identifying which scenario performs best for a specific border region

## Defined Sub-Border Regions

### Austria-Germany-Italy Cluster
- **Countries**: Austria (AT), Germany (DE), Italy (IT)
- **NUTS2 Regions (10)**:
  - AT: AT31, AT32, AT33, AT34
  - DE: DE14, DE21, DE22, DE27
  - IT: ITH1, ITH3
- **Rationale**: Tri-national Alpine border region with major cross-border transport corridors (Brenner Pass, etc.)

### Denmark-Germany Cluster
- **Countries**: Denmark (DK), Germany (DE)
- **NUTS2 Regions (2)**: DEF0, DK03
- **Rationale**: Nordic-Central European connection

### Norway-Sweden Cluster
- **Countries**: Norway (NO), Sweden (SE)
- **NUTS2 Regions (2)**: NO08, SE23
- **Rationale**: Nordic intra-regional connections

## Quick Start Examples

### Example 1: Single Case Analysis

```python
from sub_border_regions import analyze_sub_border_regions

# Analyze Austria-Germany-Italy in one case study
df_results = analyze_sub_border_regions(
    input_data,
    output_data,
    sub_region_name='Austria-Germany-Italy',
    years_to_plot=[2030, 2040, 2050],
    show_plots=True
)
```

### Example 2: Cross-Case Comparison

```python
from sub_border_regions_cross_case import analyze_sub_region_cross_case

# Define cases
cases = {
    'Var-Var': ('case_20251022_152235_var_var',
                'case_20251022_152235_var_var_cs_2025-10-23_08-22-09'),
    'Var-Uni': ('case_20251022_152358_var_uni',
                'case_20251022_152358_var_uni_cs_2025-10-23_08-56-23'),
    # ... more cases
}

# Compare across cases
df_comparison, df_summary = analyze_sub_region_cross_case(
    cases=cases,
    sub_region_name='Austria-Germany-Italy',
    years_to_plot=[2030, 2040, 2050],
    baseline_case='Var-Var',
    show_plots=True
)
```

## Files in This Suite

### Core Modules
- **`sub_border_regions.py`** - Single-case sub-border region analysis
- **`sub_border_regions_cross_case.py`** - Cross-case comparison module

### Example Scripts
- **`example_sub_border_analysis.py`** - Standalone single-case example
- **`example_cross_case_austria_cluster.py`** - Complete cross-case workflow with your 4 cases

### Notebook Integration
- **`notebook_cell_sub_border_analysis.py`** - Cells for single-case analysis
- **`notebook_cell_cross_case_sub_border.py`** - Cells for cross-case comparison

### Documentation
- **`SUB_BORDER_REGIONS_GUIDE.md`** - Detailed guide for single-case analysis
- **`CROSS_CASE_SUB_BORDER_GUIDE.md`** - Detailed guide for cross-case comparison
- **`SUB_BORDER_ANALYSIS_README.md`** - This file (overview)

## Typical Workflow

### For Scientific Paper Analysis

1. **Define Research Questions**
   ```
   - Does electrification differ between border regions?
   - How do different scenarios affect the Austria-Germany-Italy corridor?
   - Which countries adopt electrification fastest in border regions?
   ```

2. **Run Cross-Case Analysis**
   ```bash
   cd examples/moving_loads_SM
   python example_cross_case_austria_cluster.py
   ```

3. **Generate Comparison Plots**
   - Grouped bar charts by year and case
   - Line charts showing trends over time
   - Delta plots showing differences from baseline

4. **Create Summary Tables**
   - Export CSV files for detailed data
   - Generate LaTeX tables for paper
   - Create Excel workbooks with multiple sheets

5. **Analyze Results**
   - Identify best-performing scenarios
   - Calculate statistical significance
   - Understand country-specific differences

### For Jupyter Notebook Analysis

1. **Import your case studies** (you already have this in `results_representation.ipynb`)

2. **Add cross-case analysis cells** (copy from `notebook_cell_cross_case_sub_border.py`)

3. **Run analysis** for Austria-Germany-Italy cluster

4. **Create custom visualizations** based on your research questions

5. **Export results** for paper/presentation

## Adding New Sub-Border Regions

To define additional sub-border region clusters, edit `sub_border_regions.py`:

```python
SUB_BORDER_REGIONS = {
    # ... existing regions ...

    'Your-New-Region': {
        'description': 'Description of the cluster',
        'regions': {
            'NUTS2_1', 'NUTS2_2', 'NUTS2_3',
            # ... more regions
        },
        'countries': {'AT', 'DE'},  # Country codes
        'color': 'steelblue'  # Color for plots
    }
}
```

### Example: France-Germany Border
```python
'France-Germany': {
    'description': 'France-Germany border regions along the Rhine',
    'regions': {
        'DE12', 'DE13', 'DE14',  # Saarland, Rhineland-Palatinate, etc.
        'FRF1', 'FRF2', 'FRF3',  # Grand Est regions
    },
    'countries': {'FR', 'DE'},
    'color': 'forestgreen'
}
```

## Output Data Structure

### Single-Case Analysis Output
```
country  year  electrification_pct  total_fuel  electricity  sub_region              region_type
AT       2030  45.2                 125000      56500        Austria-Germany-Italy   border_Austria-Germany-Italy
DE       2030  38.7                 310000      120000       Austria-Germany-Italy   border_Austria-Germany-Italy
```

### Cross-Case Analysis Output
```
case      country  year  electrification_pct  electricity  total_fuel  sub_region
Var-Var   AT       2030  45.2                 56500        125000      Austria-Germany-Italy
Var-Uni   AT       2030  48.1                 60000        125000      Austria-Germany-Italy
Uni-Var   AT       2030  42.3                 52800        125000      Austria-Germany-Italy
```

## Visualizations Generated

### Single-Case Analysis
1. **Sub-region comparison**: Grouped bars comparing different sub-regions
2. **Detailed region plot**: Country-level breakdown with time series

### Cross-Case Analysis
1. **Grouped bar charts**: Cases compared side-by-side for each year
2. **Line charts by country**: Time series showing all cases per country
3. **Delta plots**: Differences from baseline with color-coded bars
4. **Custom plots**: Create your own based on the DataFrames

## Integration with Existing Analysis

This module extends your existing border region analysis:

| Module | Scope | Geographic Level | Case Studies |
|--------|-------|------------------|--------------|
| `border_region_electrification_analysis.py` | All border regions together | NUTS2 | Single |
| `sub_border_regions.py` | Specific clusters | Regional clusters | Single |
| `sub_border_regions_cross_case.py` | Specific clusters | Regional clusters | Multiple |

**Recommended approach**: Use all three for comprehensive analysis:
1. Overall border vs. non-border comparison
2. Sub-regional comparisons within one scenario
3. Cross-scenario comparison for key sub-regions

## Common Use Cases

### Use Case 1: Paper on Border Region Electrification
**Goal**: Compare Austria-Germany-Italy cluster across 4 scenarios

**Steps**:
1. Run `example_cross_case_austria_cluster.py`
2. Generate summary table for paper
3. Create delta plots showing scenario impacts
4. Export LaTeX tables

### Use Case 2: Policy Analysis
**Goal**: Identify which scenario maximizes electrification in Austria border regions

**Steps**:
1. Load cross-case comparison
2. Filter to Austria only
3. Rank scenarios by electrification %
4. Calculate percentage improvements

### Use Case 3: Geographic Comparison
**Goal**: Compare electrification patterns across different border clusters

**Steps**:
1. Analyze all sub-border regions in one case
2. Compare averages across clusters
3. Identify geographic patterns
4. Relate to infrastructure availability

## Troubleshooting

### "No data found"
- Check case study names match folder names exactly
- Verify run IDs are correct
- Ensure results folder is in correct location

### Missing visualizations
- Verify matplotlib is installed
- Check `show_plots=True` parameter
- Run in interactive environment (Jupyter) for best results

### Empty DataFrames
- Confirm years_to_plot match your data years
- Check that NUTS2 codes exist in your GeographicElement data
- Use `verbose=True` to see what's being loaded

### Inconsistent results across cases
- Verify all cases use same geographic boundaries
- Check input data consistency
- Ensure all cases completed successfully

## Best Practices

1. **Document case differences**: Keep clear notes on what varies between scenarios

2. **Use consistent baselines**: Always compare to the same baseline case

3. **Check data quality**: Verify all cases loaded successfully before comparing

4. **Export everything**: Save raw data, summaries, and plots for reproducibility

5. **Statistical rigor**: Consider uncertainty when interpreting small differences

6. **Version control**: Track which versions of input data were used

## Support and Extension

### Adding Custom Analysis
The modules return pandas DataFrames, so you can easily:
- Create custom visualizations
- Calculate additional metrics
- Export to different formats
- Integrate with other analysis tools

### Example Custom Analysis
```python
# Calculate year-over-year growth rates
df_comparison['year_numeric'] = df_comparison['year'].astype(int)
df_sorted = df_comparison.sort_values(['case', 'country', 'year_numeric'])

df_sorted['growth_rate'] = df_sorted.groupby(['case', 'country'])['electrification_pct'].pct_change() * 100

print("Average annual growth rate by case:")
print(df_sorted.groupby('case')['growth_rate'].mean())
```

## Related Documentation

- **Border region identification**: `BORDER_REGIONS_README.md`
- **Border infrastructure analysis**: `BORDER_INFRASTRUCTURE_GUIDE.md`
- **Electrification analysis**: `border_region_electrification_analysis.py`

## Citation

When using these modules in publications, please cite:
- The TransComp model documentation
- This specific analysis module (if contributing significant findings)

## Questions?

For questions or issues:
1. Check the detailed guides (SUB_BORDER_REGIONS_GUIDE.md, CROSS_CASE_SUB_BORDER_GUIDE.md)
2. Review example scripts
3. Examine notebook cell examples
4. Check troubleshooting section above
