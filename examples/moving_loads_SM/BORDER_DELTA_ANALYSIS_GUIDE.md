# Border Region Delta Analysis - Complete Guide

This guide explains the extended delta analysis capabilities for border NUTS2 regions in the `results_representation_border_regions.py` file.

## Overview

The delta analysis compares different temporal resolution scenarios (var_var, var_uni, uni_var, uni_uni) against a reference scenario, specifically focusing on **border regions only**. This is critical for understanding how different modeling assumptions affect cross-border transport electrification.

## Analysis Cells Added

### CELL 8: Enhanced Delta Analysis - Detailed Comparison
**What it does:**
- Country-by-country comparison of electricity consumption and electrification rates
- Shows reference → case transitions with absolute and percentage changes
- Identifies largest increases/decreases by country
- Detailed statistics for each scenario

**Key Metrics:**
- `delta_electricity_kWh`: Absolute change in electricity consumption
- `pct_change_electricity`: Percentage change in electricity consumption
- `delta_electrification_pct`: Change in electrification rate (percentage points)
- `delta_total_fuel_kWh`: Change in total fuel consumption

**Outputs:**
- `border_delta_analysis_2030.csv` - Detailed delta table for 2030
- `border_delta_analysis_2040.csv` - Detailed delta table for 2040
- Console output with detailed country-by-country comparisons

**Example Output:**
```
case_20251022_152358_var_uni vs case_20251022_152235_var_var:
  AT:
    Electricity:       3601.75 →  3500.00 (Δ -101.75 kWh, -2.82%)
    Electrification:     80.25% →    78.00% (Δ  -2.25 pp)
    Total Fuel:        4487.91 →  4489.12 (Δ   +1.21 kWh)
```

---

### CELL 8B: Visualize Delta Analysis - Heatmaps and Bar Charts
**What it does:**
- Creates comprehensive visualization of all deltas across scenarios and years
- Three-panel figure with heatmaps and bar charts

**Visualizations:**

1. **Heatmaps (Top panels)** - 2030 & 2040
   - Rows: Countries
   - Columns: Scenarios
   - Color: Green (positive) to Red (negative)
   - Values shown in cells

2. **Total Delta Bar Charts (Middle panels)**
   - Total electricity delta by scenario
   - Green bars = increase, Coral bars = decrease
   - Shows aggregate effect across all border regions

3. **Electrification Delta Comparison (Bottom panel)**
   - Side-by-side comparison of 2030 vs 2040
   - Shows average electrification rate changes
   - Identifies trends over time

**Output:**
- `border_delta_analysis_visualization.png` (18" × 12", 300 DPI)

---

### CELL 8C: Time Series Evolution of Border Region Deltas
**What it does:**
- Tracks how deltas evolve from 2020 to 2050
- Analyzes temporal patterns in scenario differences

**Years Analyzed:**
- 2020, 2024, 2028, 2030, 2034, 2038, 2040, 2044, 2048, 2050

**Plots:**
1. **Total Electricity Delta Evolution**
   - Line plot showing cumulative border electricity delta over time
   - One line per scenario
   - Zero reference line shows convergence/divergence

2. **Average Electrification Delta Evolution**
   - Shows how electrification rate differences change over time
   - Identifies whether scenarios converge or diverge

**Key Insights:**
- Early divergence (2020-2030): Different starting assumptions
- Mid-term trends (2030-2040): Technology adoption differences
- Long-term convergence (2040-2050): All scenarios reach high electrification

**Outputs:**
- `border_delta_time_series.png` (16" × 10")
- `border_delta_time_series.csv` - Full time series data

---

### CELL 8D: Border Corridor-Specific Analysis
**What it does:**
- Analyzes delta by specific cross-border corridors
- Groups border regions by geographic corridors

**Corridors Defined:**
1. **Austria-Germany**: AT31, AT32, AT33, AT34, DE14, DE21, DE22, DE27
2. **Austria-Italy**: AT32, AT33, ITH1, ITH3
3. **Germany-Denmark**: DEF0, DK03
4. **Norway-Sweden**: NO08, SE23

**Analysis:**
- Compares corridor-level electricity and electrification rates
- Shows which corridors are most sensitive to scenario assumptions
- Identifies regional patterns

**Visualizations:**
- 2×2 grid showing corridor deltas for 2030 and 2040
- Left panels: Electricity delta (kWh)
- Right panels: Electrification rate delta (%)
- Grouped bars by scenario for each corridor

**Why This Matters:**
- **Austria-Germany** is the largest corridor → most critical for policy
- **Austria-Italy** crosses Alpine regions → infrastructure challenges
- **Germany-Denmark** connects Scandinavia → integration effects
- **Norway-Sweden** shows Nordic cooperation patterns

**Outputs:**
- `border_corridor_delta_analysis.png` (16" × 12")
- `border_corridor_delta_analysis.csv` - Detailed corridor data

---

### CELL 8E: Summary Delta Table for Publication
**What it does:**
- Creates publication-ready summary table
- Combines all key metrics in one comprehensive table

**Table Structure:**
- Rows: All scenarios for both 2030 and 2040
- Columns:
  - Year
  - Scenario name
  - Type (Reference or Comparison)
  - Total Electricity (kWh)
  - Average Electrification (%)
  - Δ Electricity (kWh)
  - Δ Electricity (%)
  - Δ Electrification (pp)
  - Number of Countries

**Outputs:**
- `border_delta_summary_table.csv` - CSV format
- `border_delta_summary_table.tex` - LaTeX format for papers

**Usage in Papers:**
- Direct inclusion in manuscript tables
- LaTeX format ready for journal submission
- All metrics rounded to 2 decimal places

---

## Complete Output Files Summary

### CSV Data Files
1. `border_delta_analysis_2030.csv` - Detailed country deltas for 2030
2. `border_delta_analysis_2040.csv` - Detailed country deltas for 2040
3. `border_delta_time_series.csv` - Time evolution of deltas
4. `border_corridor_delta_analysis.csv` - Corridor-specific analysis
5. `border_delta_summary_table.csv` - Publication summary table

### Visualization Files
1. `border_delta_analysis_visualization.png` - Main delta heatmaps & bar charts
2. `border_delta_time_series.png` - Temporal evolution plots
3. `border_corridor_delta_analysis.png` - Corridor comparison charts

### LaTeX Files
1. `border_delta_summary_table.tex` - Publication-ready LaTeX table

---

## Interpretation Guide

### Positive Deltas (Δ > 0)
- **Electricity**: Scenario uses MORE electricity in border regions than reference
  - Possible causes: Higher demand, more flows, different route choices
- **Electrification**: Scenario has HIGHER electrification rate than reference
  - Possible causes: Faster EV adoption, better infrastructure availability

### Negative Deltas (Δ < 0)
- **Electricity**: Scenario uses LESS electricity in border regions than reference
  - Possible causes: Lower demand, fewer flows, modal shifts
- **Electrification**: Scenario has LOWER electrification rate than reference
  - Possible causes: Slower EV adoption, infrastructure constraints

### Percentage vs Percentage Points
- **Percentage change (%)**: Relative change in absolute values
  - Example: 1000 kWh → 1100 kWh = +10% change
- **Percentage points (pp)**: Absolute change in rates
  - Example: 75% → 80% = +5 percentage points

---

## Use Cases

### 1. Policy Analysis
**Question:** How do uniform vs variable temporal assumptions affect border region electrification?

**Answer from:**
- Cell 8: Country-by-country detailed comparison
- Cell 8B: Visual overview of all countries
- Cell 8E: Summary statistics

### 2. Infrastructure Planning
**Question:** Which border corridors are most affected by modeling assumptions?

**Answer from:**
- Cell 8D: Corridor-specific analysis
- Identify high-variance corridors needing robust planning

### 3. Temporal Dynamics
**Question:** Do scenarios converge or diverge over time?

**Answer from:**
- Cell 8C: Time series analysis
- Shows whether differences are transient or persistent

### 4. Publication Figures
**Question:** What figures/tables to include in paper?

**Recommended:**
- Cell 8B visualization: Main delta overview
- Cell 8D corridor charts: Regional analysis
- Cell 8E summary table: Compact comparison

---

## Statistical Significance Notes

The current analysis shows:
- **Absolute deltas** (kWh differences)
- **Relative deltas** (% changes)
- **Rate deltas** (percentage point changes)

For publication, consider adding:
- Standard deviations across countries
- Statistical tests (t-tests, ANOVA)
- Confidence intervals
- Sensitivity analysis ranges

---

## Customization

### Changing Reference Scenario
```python
# In CELL 8, line 260
reference_scenario = case_study_names[1]  # Change to second scenario
```

### Adding More Years
```python
# In CELL 8C, line 471
years_to_analyze = range(2020, 2051, 1)  # Every year
```

### Defining Custom Corridors
```python
# In CELL 8D, line 567
corridors = {
    'My-Custom-Corridor': {
        'AT': ['AT31', 'AT32'],
        'DE': ['DE21']
    }
}
```

### Export Formats
```python
# Add Excel export
df_summary_delta.to_excel('border_delta_summary.xlsx', index=False)

# Add JSON export
df_summary_delta.to_json('border_delta_summary.json', orient='records')
```

---

## Integration with Existing Analysis

The border delta analysis complements:
- **Cell 4-5**: Border region absolute values (2030, 2040)
- **Cell 6**: Border vs All comparison
- **Cell 7**: Summary statistics
- **Cell 8-8E**: Delta analysis (NEW!)
- **Cell 9**: Data export

**Recommended Workflow:**
1. Run Cells 1-3: Load data and border codes
2. Run Cells 4-6: Visualize absolute values
3. Run Cell 7: Review summary statistics
4. Run Cells 8-8E: Perform comprehensive delta analysis
5. Run Cell 9: Export all data

---

## Tips for Interpretation

### Large Electricity Deltas
- Check if total demand changed (Δ Total Fuel)
- Verify if it's substitution (diesel → electric) or new demand
- Compare with electrification rate change

### Large Electrification Rate Deltas
- Small absolute electricity changes can cause large rate changes
- Focus on countries with significant absolute flows
- Consider baseline electrification level

### Corridor Analysis Insights
- **Austria-Germany**: Expect largest absolute deltas (most flows)
- **Germany-Denmark**: Expect highest rates (small base)
- **Austria-Italy**: Expect infrastructure constraints (Alpine terrain)
- **Norway-Sweden**: Expect high electrification (Nordic leadership)

---

## Troubleshooting

### No Data for Certain Years
- Check that `years_to_plot` in Cell 2 includes desired years
- Verify optimization results contain those years

### Empty Corridor Analysis
- Ensure `border_regions_analysis.csv` exists (run identify_border_regions.py first)
- Check that corridor country codes match data

### Visualization Errors
- Ensure matplotlib has enough memory for large figures
- Reduce DPI if needed: `dpi=150` instead of `dpi=300`

---

## Citation

When using this delta analysis in publications:

```
The delta analysis compares border region electrification across scenarios
using a reference baseline approach. Deltas are calculated for electricity
consumption (kWh), total fuel use (kWh), and electrification rates (%).
Corridor-specific analysis groups regions by geographic proximity to assess
cross-border policy impacts.
```

---

## Next Steps

Consider extending with:
1. **Statistical testing**: Add p-values, confidence intervals
2. **Sensitivity analysis**: Test robustness to input parameters
3. **Cost analysis**: Link electricity deltas to infrastructure costs
4. **Emissions analysis**: Calculate CO2 implications of deltas
5. **Network analysis**: Visualize flows between corridor regions

---

## Questions?

For support:
- Check console output for detailed statistics
- Review CSV exports for raw data
- Examine PNG files for visual patterns
- Consult original scenario definitions for context
