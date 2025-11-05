# Germany-Denmark-Sweden Cluster Guide

## 🆕 New Sub-Border Region Added

A new cross-border cluster has been added: **`Germany-Denmark-Sweden`**

### 📍 Geographic Coverage

This cluster includes:

#### **Denmark (Complete Coverage)**
- `DK01` - Hovedstaden (Capital Region)
- `DK02` - Sjælland (Zealand)
- `DK03` - Syddanmark (Southern Denmark)
- `DK04` - Midtjylland (Central Jutland)
- `DK05` - Nordjylland (Northern Jutland)

**All 5 NUTS2 regions of Denmark are included!**

#### **Germany (Border Region)**
- `DEF0` - Schleswig-Holstein (directly borders Denmark)

#### **Sweden (Öresund Connection)**
- `SE22` - Sydsverige (Southern Sweden)
- `SE23` - Västsverige (Western Sweden - includes Malmö/Öresund bridge connection)

### 🌉 Key Transport Connections

This cluster captures important transport corridors:
- 🚗 **Jutland Peninsula**: Road transport through Denmark from Germany to Scandinavia
- 🌉 **Öresund Bridge**: Denmark (Copenhagen) ↔ Sweden (Malmö)
- 🌉 **Great Belt Bridge**: Zealand ↔ Funen (within Denmark)
- 🚢 **Ferry Routes**: Multiple ferry connections between DK-DE and DK-SE

---

## 📊 Available Sub-Border Regions (Updated List)

| Cluster Name | Countries | NUTS2 Regions | Description |
|--------------|-----------|---------------|-------------|
| **Austria-Germany-Italy** | AT, DE, IT | 10 regions | Alpine border cluster around Austria |
| **Germany-Denmark-Sweden** | DE, DK, SE | 8 regions | **All of Denmark** with German & Swedish connections |
| Denmark-Germany | DK, DE | 2 regions | Partial Denmark-Germany connection |
| Norway-Sweden | NO, SE | 2 regions | Norway-Sweden border |

---

## 🚀 How to Use the New Cluster

### Option 1: Quick Analysis (Using Your Existing Notebook)

Replace your current cell with:

```python
# Reload module to pick up new cluster
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

# Analyze the NEW cluster
df_comparison, df_summary = analyze_sub_region_cross_case_preloaded(
    loaded_runs=loaded_runs,
    case_labels=case_labels,
    sub_region_name='Germany-Denmark-Sweden',  # <-- NEW!
    years_to_plot=[2030, 2040, 2050],
    baseline_case='Var-Var',
    show_plots=True,
    verbose=True
)

display(df_comparison)
display(df_summary)
```

### Option 2: Full Custom Plotting

Copy cells from:
```
notebook_cell_germany_denmark_sweden.py
```

This file contains 5 ready-to-use cells:
1. Data loading and analysis
2. Grouped bar chart (electrification % by country)
3. Denmark-focused time series (all 5 regions)
4. Delta analysis (vs. baseline scenario)
5. Summary statistics and CSV export

---

## 📈 What You'll Get

### Analysis Outputs

1. **df_comparison**: Detailed data with columns:
   - `case`: Scenario name
   - `country`: DE, DK, SE
   - `year`: 2030, 2040, 2050
   - `electrification_pct`: Percentage electrification
   - `electricity`: Total electricity consumption (MWh)
   - `total_fuel`: Total fuel consumption (MWh)
   - `sub_region`: 'Germany-Denmark-Sweden'

2. **df_summary**: Aggregated statistics:
   - Average electrification % per scenario
   - Min/Max values
   - Total electricity and fuel consumption

### Visualizations

When `show_plots=True`, you get 5 automatic plots:
1. Grouped bar chart - Electrification % (3 years)
2. Line charts - Electrification % by country over time
3. Grouped bar chart - Absolute electricity consumption (MWh)
4. Line charts - Electricity consumption by country
5. Delta plots - Differences vs. baseline scenario

---

## 🔍 Key Research Questions This Cluster Addresses

1. **Denmark's Role**: How does complete Danish electrification vary across scenarios?
2. **Cross-Border Effects**: Impact of German and Swedish policies on Danish transport electrification
3. **Öresund Region**: Copenhagen-Malmö corridor electrification patterns
4. **North-South Corridor**: Germany → Denmark → Sweden freight transport electrification
5. **Island Connections**: Zealand and Funen electrification (within Denmark)

---

## 📂 Files Created/Modified

### Modified:
- ✅ `sub_border_regions.py` - Added Germany-Denmark-Sweden cluster definition

### Created:
- ✅ `notebook_cell_germany_denmark_sweden.py` - 5 ready-to-use notebook cells
- ✅ `GERMANY_DENMARK_SWEDEN_CLUSTER_GUIDE.md` - This guide
- ✅ Updated `display_subregion_info.py` - Shows all available clusters

---

## 💡 Tips

### Focus on Denmark Only

If you want to isolate Denmark's electrification:

```python
# Filter for Denmark only
dk_only = df_comparison[df_comparison['country'] == 'DK']

# Plot Denmark's evolution
import matplotlib.pyplot as plt
for case in dk_only['case'].unique():
    case_data = dk_only[dk_only['case'] == case]
    plt.plot(case_data['year'], case_data['electrification_pct'],
             marker='o', label=case, linewidth=2)

plt.xlabel('Year')
plt.ylabel('Electrification %')
plt.title('Denmark Electrification (All 5 NUTS2 Regions)')
plt.legend()
plt.grid(True)
plt.show()
```

### Compare All 4 Clusters

```python
cluster_names = [
    'Austria-Germany-Italy',
    'Germany-Denmark-Sweden',
    'Denmark-Germany',
    'Norway-Sweden'
]

for cluster_name in cluster_names:
    df, summary = analyze_sub_region_cross_case_preloaded(
        loaded_runs=loaded_runs,
        case_labels=case_labels,
        sub_region_name=cluster_name,
        years_to_plot=[2030, 2040, 2050],
        baseline_case='Var-Var',
        show_plots=False,
        verbose=True
    )
    print(f"\n{cluster_name} Summary:")
    print(summary)
```

---

## 🗺️ Geographic Context

### Why This Cluster Matters

Denmark is a **critical transit region** for North European transport:

1. **Gateway Position**: Bridge between Continental Europe and Scandinavia
2. **Modal Diversity**: Significant ferry, road, and rail freight
3. **Island Nation**: Internal transport includes major bridges and ferries
4. **EU-Scandinavia Link**: Part of major TEN-T corridors
5. **Policy Innovation**: Denmark has ambitious electrification targets

### NUTS2 Region Details

- **DK01 (Copenhagen)**: Major urban center, ferry hub, Öresund bridge
- **DK02 (Zealand)**: Central transport node with Great Belt bridge
- **DK03 (Southern Denmark)**: German border crossing point
- **DK04 (Central Jutland)**: Major freight corridor
- **DK05 (Northern Jutland)**: Ferry connections to Scandinavia

---

## ✅ Verification

To verify the cluster is working:

```python
from sub_border_regions import get_sub_border_region_info

df_info = get_sub_border_region_info()
print(df_info[df_info['cluster_name'] == 'Germany-Denmark-Sweden'])
```

Expected output:
```
cluster_name: Germany-Denmark-Sweden
description: Cross-border cluster including all of Denmark with adjacent German and Swedish regions
num_regions: 8
countries: DE, DK, SE
regions: DEF0, DK01, DK02, DK03, DK04, DK05, SE22, SE23
```

---

## 📧 Questions?

If you need to modify the cluster (add/remove regions):
1. Edit `sub_border_regions.py`
2. Modify the `SUB_BORDER_REGIONS` dictionary
3. Reload the module in your notebook: `importlib.reload(sub_border_regions)`

---

**Happy analyzing!** 🎉
