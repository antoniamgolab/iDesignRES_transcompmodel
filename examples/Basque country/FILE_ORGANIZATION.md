# File Organization Guide

This document categorizes all files in the Basque Country case study to help new users understand what is essential for running the model versus what is generated output.

---

## Essential Files (REQUIRED to run the model)

### Core Scripts

| File | Description | Must Have |
|------|-------------|-----------|
| `basque_cs.jl` | Main case study script - template for running optimization | YES |
| `basque_cs_rq2.jl` | Research Question 2 scenarios | YES (for RQ2 analysis) |
| `basque_cs_SA.jl` | Sensitivity analysis framework | Optional |
| `basque_cs_home_charging.jl` | Home charging policy scenarios | Optional |

### Input Data (data/ folder)

**Minimum required** - at least ONE complete input file:

| Recommended File | Description |
|------------------|-------------|
| `input_rq2_baseline_20250906.yaml` | Complete baseline scenario |
| `td_ONENODE_balanced_expansion_24092025.yaml` | Infrastructure expansion scenario |

**All input files** should be kept if you want to reproduce published results.

---

## Generated Files (DO NOT include in version control)

### Results Folder (results/)

**Everything in `results/` is auto-generated.** This includes:

```
results/
├── cs_2025-09-06_21-32-31/           # Timestamped run folder
│   ├── h_dict.yaml                   # Vehicle stock decisions
│   ├── h_plus_dict.yaml              # New vehicles
│   ├── h_minus_dict.yaml             # Retired vehicles
│   ├── q_fuel_infr_plus_dict.yaml    # Infrastructure additions
│   ├── detour_time_dict.yaml         # Detour penalties
│   └── metadata.yaml                 # Run configuration
└── ...                               # More run folders
```

**Recommendation**: Add to `.gitignore`:
```
examples/Basque country/results/
```

### Generated Visualizations

All PDF and PNG files are stored in the `figures/` subfolder (419 files):

```
figures/
├── bev_fleet_comparison.pdf
├── charging_capacity_per_region.pdf
├── electrification_rate_development_*.pdf
├── fueled_energy_by_income_and_charging_type_*.pdf
├── h_comparison_*.pdf
├── q_fuel_infr_*.pdf
├── rq_2_*.pdf
├── SA_*.pdf
└── ... (419 total files)
```

**Recommendation**: Add to `.gitignore`:
```
examples/Basque country/figures/
examples/Basque country/*.csv
```

---

## Analysis Files (OPTIONAL - for post-processing)

### Jupyter Notebooks

These notebooks are for analyzing results AFTER running the model:

| Notebook | Purpose | Essential? |
|----------|---------|------------|
| `final_visualization_rq1.ipynb` | RQ1 results plots | NO |
| `final_visualization_rq2.ipynb` | RQ2 results plots | NO |
| `results_analysis.ipynb` | General analysis | NO |
| `SA_visualization.ipynb` | Sensitivity analysis plots | NO |
| `h_comparison_mixed_sources.ipynb` | Vehicle fleet comparison | NO |

**Recommendation**: Keep 1-2 as templates, or add to `.gitignore`:
```
examples/Basque country/*.ipynb
```

### Python Utilities

| File | Purpose | Essential? |
|------|---------|------------|
| `regenerate_infrastructure_plot.py` | Recreate specific plots | NO |
| `reorganize_old_results.py` | File organization utility | NO |
| `update_regional_cell.py` | Notebook cell updates | NO |

---

## Recommended .gitignore Additions

Add these lines to the project's `.gitignore`:

```gitignore
# Basque Country generated outputs
examples/Basque country/results/
examples/Basque country/figures/
examples/Basque country/*.csv

# Keep only essential notebooks (optional)
# examples/Basque country/*.ipynb

# Python cache
examples/Basque country/__pycache__/
examples/Basque country/*.pyc
```

---

## Minimal Distribution Package

For sharing the model with a third party, include ONLY:

```
examples/Basque country/
├── README.md                              # Documentation
├── FILE_ORGANIZATION.md                   # This file
├── basque_cs.jl                           # Main run script
├── basque_cs_rq2.jl                       # RQ2 script (optional)
└── data/
    ├── input_rq2_baseline_20250906.yaml   # Baseline scenario
    └── td_ONENODE_balanced_expansion_24092025.yaml  # Alternative
```

**Total size**: ~5-10 MB (vs 63+ GB with all generated outputs)

---

## Full File Inventory

### By Category

**Category A: Essential Source Scripts** (keep all)
- `basque_cs.jl` (5.4 KB)
- `basque_cs_rq2.jl` (5.6 KB)
- `basque_cs_rq2_multiple.jl` (6.6 KB)
- `basque_cs_SA.jl` (6.1 KB)
- `basque_cs_SA_circuity.jl` (9.9 KB)
- `basque_cs_home_charging.jl` (7.1 KB)
- `calibration.jl` (3.6 KB)

**Category B: Input Data** (keep all in `data/`)
- 109 YAML files
- Organized by scenario type (baseline, expansion, sensitivity)

**Category C: Analysis Notebooks** (optional, exclude if not needed)
- 14+ Jupyter notebooks
- Used for visualization and post-processing

**Category D: Generated Outputs** (exclude from distribution)
- All files in `results/`
- All files in `figures/` (PDFs/PNGs)
- Statistics CSVs

**Category E: Utility Scripts** (optional)
- Python helper scripts
- Filter and reorganization utilities

---

## Size Comparison

| Category | Files | Size |
|----------|-------|------|
| Essential scripts | 7 | ~50 KB |
| Input data | 109 | ~50 MB |
| Analysis notebooks | 14 | ~25 MB |
| Generated results | 100+ runs | ~1 GB |
| Generated figures/ | 419 | ~500 MB |
| **Essential only** | **~120** | **~50 MB** |
| **Full directory** | **~600+** | **~2 GB** |

---

## Questions?

For questions about file organization or which files are needed for specific analyses, refer to the main README.md or contact the repository maintainers.
