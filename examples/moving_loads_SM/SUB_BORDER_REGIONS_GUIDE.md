# Sub-Border Region Analysis Guide

## Overview

The sub-border region analysis module allows you to analyze electrification patterns in specific geographic clusters of border NUTS2 regions. This is useful for studying cross-border dynamics in specific areas like the Austria-Germany-Italy border region.

## Defined Sub-Border Regions

### 1. Austria-Germany-Italy Cluster
**Description**: NUTS2 regions around Austria with adjacent German and Italian regions

**NUTS2 Regions (10)**:
- **Austria (4)**: AT31, AT32, AT33, AT34
- **Germany (4)**: DE14, DE21, DE22, DE27
- **Italy (2)**: ITH1, ITH3

**Geographic Context**:
- Forms a tri-national border region in the Alps
- Key transport corridors between Central and Southern Europe
- Includes major cross-border routes (e.g., Brenner Pass)

### 2. Denmark-Germany Cluster
**Description**: NUTS2 regions connecting Denmark and Germany

**NUTS2 Regions (2)**:
- **Germany (1)**: DEF0 (Schleswig-Holstein)
- **Denmark (1)**: DK03 (Syddanmark)

**Geographic Context**:
- Nordic-Central European connection
- Important for Scandinavian freight routes

### 3. Norway-Sweden Cluster
**Description**: NUTS2 regions connecting Norway and Sweden

**NUTS2 Regions (2)**:
- **Norway (1)**: NO08 (Trøndelag)
- **Sweden (1)**: SE23 (Västernorrlands län)

**Geographic Context**:
- Nordic intra-regional connections
- Lower traffic volumes but strategic for Norway-Sweden trade

## Usage

### Basic Usage

```python
from sub_border_regions import analyze_sub_border_regions

# Analyze a specific sub-border region
df_results = analyze_sub_border_regions(
    input_data,
    output_data,
    years_to_plot=[2030, 2040, 2050],
    sub_region_name='Austria-Germany-Italy',
    show_plots=True,
    verbose=True
)
```

### Analyze All Sub-Border Regions

```python
# Get results for all defined clusters
df_all, results_by_cluster = analyze_sub_border_regions(
    input_data,
    output_data,
    years_to_plot=[2030, 2040, 2050],
    show_plots=True,
    verbose=True
)

# Compare across clusters
summary = df_all.groupby(['sub_region', 'year'])['electrification_pct'].mean()
```

### Access Sub-Region Information

```python
from sub_border_regions import get_sub_border_region_info, SUB_BORDER_REGIONS

# Get overview table
df_info = get_sub_border_region_info()
print(df_info)

# Access specific cluster details
austria_cluster = SUB_BORDER_REGIONS['Austria-Germany-Italy']
print(f"Regions: {austria_cluster['regions']}")
print(f"Countries: {austria_cluster['countries']}")
```

## Adding New Sub-Border Regions

To define additional sub-border region clusters, edit the `SUB_BORDER_REGIONS` dictionary in `sub_border_regions.py`:

```python
SUB_BORDER_REGIONS = {
    'Your-New-Cluster': {
        'description': 'Description of the cluster',
        'regions': {
            'NUTS2_CODE_1',
            'NUTS2_CODE_2',
            'NUTS2_CODE_3',
            # ... more regions
        },
        'countries': {'AT', 'DE'},  # Country codes
        'color': 'steelblue'  # Color for plots
    }
}
```

### Example: Creating a France-Germany Border Cluster

```python
'France-Germany': {
    'description': 'NUTS2 regions along France-Germany border',
    'regions': {
        'DE12', 'DE13', 'DE14',  # Saarland, Rhineland-Palatinate, etc.
        'FRF1', 'FRF2', 'FRF3',  # Alsace, Lorraine, etc.
    },
    'countries': {'FR', 'DE'},
    'color': 'forestgreen'
}
```

## Visualizations

The module provides several visualization functions:

### 1. Single Sub-Region Detail
```python
from sub_border_regions import plot_single_sub_region_detail

fig, axes = plot_single_sub_region_detail(
    df_results,
    'Austria-Germany-Italy',
    years_to_plot=[2030, 2040, 2050]
)
```

**Generates**:
- Bar chart: Electrification by country and year
- Line chart: Electricity consumption over time

### 2. Cross-Cluster Comparison
```python
from sub_border_regions import plot_sub_region_comparison

fig, axes = plot_sub_region_comparison(
    df_all_clusters,
    years_to_plot=[2030, 2040, 2050]
)
```

**Generates**:
- Grouped bar charts comparing all clusters side-by-side

## Output Data Structure

### DataFrame Columns

The analysis returns a pandas DataFrame with the following columns:

| Column | Type | Description |
|--------|------|-------------|
| `country` | str | Country code (e.g., 'AT', 'DE', 'IT') |
| `year` | int | Analysis year |
| `electrification_pct` | float | Percentage of electrified transport (0-100) |
| `total_fuel` | float | Total fuel consumption (MWh) |
| `electricity` | float | Electricity consumption (MWh) |
| `sub_region` | str | Sub-border region cluster name |
| `region_type` | str | Type indicator (e.g., 'border_Austria-Germany-Italy') |

### Example Output

```
   country  year  electrification_pct  total_fuel  electricity        sub_region                   region_type
0       AT  2030                 45.2    125000.0      56500.0  Austria-Germany-Italy  border_Austria-Germany-Italy
1       DE  2030                 38.7    310000.0     120000.0  Austria-Germany-Italy  border_Austria-Germany-Italy
2       IT  2030                 52.1     98000.0      51000.0  Austria-Germany-Italy  border_Austria-Germany-Italy
```

## Integration with Existing Analysis

The sub-border region module extends the existing `border_region_electrification_analysis` module:

- **Base module**: Analyzes all border regions together
- **Sub-border module**: Analyzes specific geographic clusters within border regions

You can combine both approaches:

```python
from border_region_electrification_analysis import analyze_border_region_electrification
from sub_border_regions import analyze_sub_border_regions

# Compare: All borders vs. Austria-Germany-Italy cluster
df_all_borders = analyze_border_region_electrification(
    input_data, output_data,
    years_to_plot=[2030, 2050]
)

df_austria_cluster = analyze_sub_border_regions(
    input_data, output_data,
    years_to_plot=[2030, 2050],
    sub_region_name='Austria-Germany-Italy'
)

# Compare results
print(f"All borders avg: {df_all_borders['electrification_pct'].mean():.2f}%")
print(f"Austria cluster: {df_austria_cluster['electrification_pct'].mean():.2f}%")
```

## Files

- **`sub_border_regions.py`**: Main module with analysis functions
- **`example_sub_border_analysis.py`**: Standalone example script
- **`notebook_cell_sub_border_analysis.py`**: Notebook cell examples
- **`SUB_BORDER_REGIONS_GUIDE.md`**: This guide

## See Also

- `BORDER_REGIONS_README.md` - Overview of border region identification
- `border_region_electrification_analysis.py` - Base border region analysis
- `border_regions_with_neighbors.txt` - Complete border region mapping
