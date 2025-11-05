# ⚡ Quick Start: Germany-Denmark-Sweden Cluster

## ✅ What Was Done

A new sub-border region cluster has been added: **`Germany-Denmark-Sweden`**

### Included Regions:
- 🇩🇰 **All 5 Danish NUTS2 regions**: DK01, DK02, DK03, DK04, DK05
- 🇩🇪 **German border region**: DEF0 (Schleswig-Holstein)
- 🇸🇪 **Swedish Öresund regions**: SE22, SE23

**Total: 8 regions across 3 countries**

---

## 🚀 To Use It Right Now

### In Your Notebook - Single Cell:

```python
# Reload module to pick up changes
import importlib
import sub_border_regions_cross_case
importlib.reload(sub_border_regions_cross_case)
from sub_border_regions_cross_case import *

case_labels = {
    "case_20251022_152235_var_var": "Var-Var",
    "case_20251022_152358_var_uni": "Var-Uni",
    "case_20251022_153056_uni_var": "Uni-Var",
    "case_20251022_153317_uni_uni": "Uni-Uni"
}

# Run analysis
df_comparison, df_summary = analyze_sub_region_cross_case_preloaded(
    loaded_runs=loaded_runs,
    case_labels=case_labels,
    sub_region_name='Germany-Denmark-Sweden',  # <-- THE NEW CLUSTER
    years_to_plot=[2030, 2040, 2050],
    baseline_case='Var-Var',
    show_plots=True,  # Set False if you want custom plots
    verbose=True
)

display(df_comparison)
display(df_summary)
```

**That's it!** 🎉

---

## 📊 All Available Clusters Now:

1. `'Austria-Germany-Italy'` - 10 regions (AT, DE, IT)
2. `'Germany-Denmark-Sweden'` - 8 regions (DE, DK, SE) **← NEW!**
3. `'Denmark-Germany'` - 2 regions (DK, DE) - partial Denmark
4. `'Norway-Sweden'` - 2 regions (NO, SE)

---

## 📂 Files to Check Out

- **`notebook_cell_germany_denmark_sweden.py`** - 5 ready-to-use cells with custom plots
- **`GERMANY_DENMARK_SWEDEN_CLUSTER_GUIDE.md`** - Complete documentation
- **`display_subregion_info.py`** - Run this to see all clusters

---

## 🔍 Verify It Works

```python
from sub_border_regions import get_sub_border_region_info
df_info = get_sub_border_region_info()
print(df_info)
```

You should see `Germany-Denmark-Sweden` with 8 regions!

---

**Modified file**: `sub_border_regions.py` (lines 23-63)
