# How to Use Border Infrastructure Analysis

## Problem Solved

The original `border_infrastructure_analysis.py` tried to import itself, causing a `NameError` because `loaded_runs` wasn't defined yet.

## Solution

Use **`border_infrastructure_notebook_cells.py`** instead!

---

## Quick Start

### Option 1: Copy-Paste into Notebook (Recommended)

1. **Open** `results_representation.ipynb`

2. **After** the cells where you load data (cells with `loaded_runs` and `case_study_names`), add **8 new cells**

3. **Copy the content** from `border_infrastructure_notebook_cells.py`:
   - Cell 1: Import functions
   - Cell 2: Load data and calculate
   - Cell 3: Calculate deltas
   - Cell 4: Plot 1 - Capacity by scenario
   - Cell 5: Plot 2 - Capacity deltas
   - Cell 6: Plot 3 - Utilization comparison
   - Cell 7: Plot 4 - Summary table
   - Cell 8: Export data

4. **Run cells** in order

---

### Option 2: Run Entire File (Alternative)

In your notebook, after loading data:

```python
# Make sure loaded_runs and case_study_names are defined
# Then run:
%run border_infrastructure_notebook_cells.py
```

This will execute all 8 cells at once.

---

## What You'll Get

### 4 Plots (300 DPI PNG):
1. `border_infrastructure_capacity_by_scenario.png` - 2×2 grid comparing scenarios
2. `border_infrastructure_capacity_deltas.png` - Heatmaps + bars showing differences
3. `border_infrastructure_utilization.png` - Utilization rates comparison
4. `border_infrastructure_summary_table.png` - Complete summary table

### 3 Data Files (CSV):
5. `border_infrastructure_deltas.csv` - Detailed delta analysis
6. `border_infrastructure_all_scenarios.csv` - Complete dataset
7. `border_infrastructure_summary_stats.csv` - Summary statistics

---

## Cell Structure

### Cell 1: Functions (30 seconds)
Defines helper functions for loading border codes and calculating infrastructure

### Cell 2: Data Loading (1-2 minutes)
Loads border regions and calculates infrastructure for all scenarios and years

### Cell 3: Delta Calculation (10 seconds)
Computes differences vs reference scenario

### Cells 4-7: Plotting (30 seconds each)
Creates the 4 publication-ready plots

### Cell 8: Export (5 seconds)
Saves all data to CSV files

**Total Runtime: ~3-5 minutes** for 4 scenarios

---

## Requirements

Make sure these are already defined in your notebook:
- `loaded_runs` - Dictionary of your scenario data
- `case_study_names` - List of scenario names
- `border_nuts2_codes.txt` - File with border region codes (created by identify_border_regions.py)

And these are imported:
- `pandas`, `numpy`, `matplotlib`
- `infrastructure_analysis` module (from your existing code)

---

## Troubleshooting

### "NameError: name 'loaded_runs' is not defined"
**Solution:** Make sure you run the data loading cells FIRST before running infrastructure analysis

### "FileNotFoundError: border_nuts2_codes.txt"
**Solution:** Run `identify_border_regions.py` first to create this file

### "ModuleNotFoundError: No module named 'infrastructure_analysis'"
**Solution:** Make sure `infrastructure_analysis.py` exists in the same directory

### Plots are empty
**Solution:** Check that your results files contain infrastructure data (`q_fuel_infr_plus`, `s` variables)

---

## Comparison with Original File

| File | Use Case | Status |
|------|----------|--------|
| `border_infrastructure_analysis.py` | Original (had import error) | ❌ Don't use |
| `border_infrastructure_notebook_cells.py` | Ready for notebook | ✅ **Use this** |

---

## Example Notebook Structure

```python
# Cell 1-3: Your existing data loading cells
# (loads loaded_runs and case_study_names)

# NEW CELLS START HERE

# Cell 4: Copy Cell 1 from border_infrastructure_notebook_cells.py
# (Functions)

# Cell 5: Copy Cell 2 from border_infrastructure_notebook_cells.py
# (Data loading)

# Cell 6: Copy Cell 3 from border_infrastructure_notebook_cells.py
# (Delta calculation)

# Cell 7: Copy Cell 4 from border_infrastructure_notebook_cells.py
# (Plot 1)

# Cell 8: Copy Cell 5 from border_infrastructure_notebook_cells.py
# (Plot 2)

# Cell 9: Copy Cell 6 from border_infrastructure_notebook_cells.py
# (Plot 3)

# Cell 10: Copy Cell 7 from border_infrastructure_notebook_cells.py
# (Plot 4)

# Cell 11: Copy Cell 8 from border_infrastructure_notebook_cells.py
# (Export)
```

---

## Files Summary

| File | Purpose | Use It? |
|------|---------|---------|
| `border_infrastructure_analysis.py` | Original attempt | ❌ No (has error) |
| `border_infrastructure_notebook_cells.py` | Fixed version | ✅ **YES** |
| `BORDER_INFRASTRUCTURE_GUIDE.md` | Comprehensive documentation | 📖 Reference |
| `INFRASTRUCTURE_ANALYSIS_SUMMARY.txt` | Quick reference | 📝 Quick look |
| `HOW_TO_USE_INFRASTRUCTURE_ANALYSIS.md` | This file | 📘 Instructions |

---

## Ready to Use!

1. Open `border_infrastructure_notebook_cells.py`
2. Copy the 8 cells into your `results_representation.ipynb`
3. Run them after your data loading cells
4. Get 4 plots + 3 data files

That's it! No import errors, no complications. ✅
