# Border NUTS2 Regions Analysis

This directory contains tools to identify NUTS2 regions at international borders that have neighboring regions in your TransComp dataset.

## Overview

The border regions identification system helps you:
1. **Identify border regions**: Find NUTS2 regions located at international borders
2. **Find neighbors in dataset**: Check which neighboring regions exist in your GeographicElement data
3. **Generate cross-border pairs**: Create OD pairs for cross-border transport analysis
4. **Focus preprocessing**: Target specific regions for detailed analysis

## Results Summary

### Total Border Regions Found: **14**

| Country | Count | Border Regions |
|---------|-------|----------------|
| Austria (AT) | 4 | AT31, AT32, AT33, AT34 |
| Germany (DE) | 5 | DE14, DE21, DE22, DE27, DEF0 |
| Denmark (DK) | 1 | DK03 |
| Italy (IT) | 2 | ITH1, ITH3 |
| Norway (NO) | 1 | NO08 |
| Sweden (SE) | 1 | SE23 |

### Cross-Border Connections

#### Most Connected Border Regions
1. **AT33** (Austria): 4 foreign neighbors - DE21, DE27, ITH1, ITH3
2. **DE21** (Germany): 3 foreign neighbors - AT31, AT32, AT33

#### Key Border Corridors
- **Austria-Germany**: 8 cross-border connections
  - AT31 ↔ DE21, DE22
  - AT32 ↔ DE21
  - AT33 ↔ DE21, DE27
  - AT34 ↔ DE14, DE27

- **Austria-Italy**: 3 cross-border connections
  - AT32 ↔ ITH1
  - AT33 ↔ ITH1, ITH3

- **Germany-Denmark**: 1 cross-border connection
  - DEF0 ↔ DK03

- **Norway-Sweden**: 1 cross-border connection
  - NO08 ↔ SE23

## Files Generated

### Core Scripts
- **`identify_border_regions.py`** - Main analysis script with reusable functions
- **`example_border_region_usage.py`** - Example workflow demonstrating how to use the tools
- **`notebook_cell_example.py`** - Code snippets to copy into your Jupyter notebook

### Output Files
- **`border_regions_with_neighbors.txt`** - Human-readable list with all neighbors
- **`border_regions_analysis.csv`** - Detailed analysis with coordinates and neighbor counts
- **`border_nuts2_codes.txt`** - Simple list of border NUTS2 codes
- **`cross_border_od_pairs.csv`** - All bidirectional cross-border OD pairs (24 pairs)

## Usage

### Basic Usage in Python

```python
from identify_border_regions import identify_border_regions_with_neighbors

# Identify border regions
df_border_regions = identify_border_regions_with_neighbors(
    nuts_shapefile_path="data/NUTS_RG_20M_2021_4326.shp/NUTS_RG_20M_2021_4326.shp",
    geographic_element_yaml_path="input_data/case_nuts2_complete/GeographicElement.yaml",
    nuts_level=2,
    verbose=True
)

# Get list of border region codes
border_codes = df_border_regions[
    df_border_regions['is_border_region']
]['nuts_region'].tolist()
```

### Usage in Jupyter Notebook

See `notebook_cell_example.py` for complete examples to copy into your notebook.

Key functions available:
```python
# 1. Main analysis
df_border_regions = identify_border_regions_with_neighbors(...)

# 2. Filter to active borders only
df_active_borders = filter_border_regions_with_active_neighbors(
    df_border_regions,
    min_foreign_neighbors=1
)

# 3. Export results
export_border_regions_list(df_active_borders, "output.txt")
```

## Integration with TransComp Preprocessing

### Step 1: Load Border Regions
```python
import pandas as pd

# Load the analysis results
df_border = pd.read_csv('border_regions_analysis.csv')
border_nuts2_codes = df_border['nuts_region'].tolist()
```

### Step 2: Filter GeographicElements
```python
# Filter your geographic elements to focus on border regions
relevant_regions = set(border_nuts2_codes)

# Optionally include all neighbors
for _, row in df_border.iterrows():
    relevant_regions.update(eval(row['all_neighbors']))

# Filter GeographicElement data
filtered_geo_elements = [
    elem for elem in geographic_elements
    if elem.get('nuts2_region') in relevant_regions
]
```

### Step 3: Analyze Cross-Border Flows
```python
# Load cross-border pairs
df_cross_border = pd.read_csv('cross_border_od_pairs.csv')

# Filter your Odpair data to focus on cross-border transport
cross_border_odpairs = [
    odpair for odpair in odpairs
    if (odpair['origin_nuts2'], odpair['destination_nuts2'])
       in zip(df_cross_border['origin_nuts2'], df_cross_border['destination_nuts2'])
]
```

## Data Structure

### Border Regions DataFrame Columns
- `nuts_region`: NUTS2 region code (e.g., "AT31")
- `country`: ISO country code (e.g., "AT")
- `neighboring_countries`: Set of neighboring country codes
- `all_neighbors`: List of all neighboring NUTS2 regions in dataset
- `foreign_neighbors`: List of neighboring regions in different countries
- `num_all_neighbors`: Total number of neighbors in dataset
- `num_foreign_neighbors`: Number of foreign neighbors
- `is_border_region`: Boolean indicating if region is at border
- `centroid_lat`: Latitude of region centroid
- `centroid_lon`: Longitude of region centroid

## Applications

### 1. Cross-Border Infrastructure Planning
Focus charging infrastructure expansion on regions with significant cross-border transport flows.

### 2. International Transport Analysis
Analyze vehicle flows across borders to understand:
- Cross-border electrification needs
- International charging station placement
- Border-crossing delay impacts

### 3. Policy Analysis
Study effects of:
- National vs. international charging policies
- Cross-border grid connections
- Harmonized vs. divergent technology adoption

### 4. Reduced Model Creation
Create smaller test cases focusing on:
- Specific border corridors (e.g., Austria-Germany)
- Multi-country regions (e.g., Alps: AT-DE-IT)
- Single border pairs for validation

## Notes and Warnings

1. **Geographic CRS Warning**: The script shows a warning about centroid calculations in geographic CRS. This is acceptable for visualization but consider reprojecting to a projected CRS (e.g., EPSG:3035 for Europe) for precise distance calculations.

2. **Neighbor Detection**: Regions are considered neighbors if their geometries "touch" (share a boundary). This uses GeoPandas `.touches()` method.

3. **Dataset Coverage**: Only regions present in both the NUTS shapefile AND your GeographicElement.yaml file are analyzed.

4. **Path Data**: The current Path.yaml analysis shows mostly self-loops (origin=destination). Cross-border paths may need to be generated separately if not present.

## Future Enhancements

Potential improvements:
- [ ] Add distance calculations between border region centroids
- [ ] Generate missing cross-border paths automatically
- [ ] Calculate border-crossing angles and suitable locations
- [ ] Integrate with OD demand data to prioritize high-volume corridors
- [ ] Add visualization of cross-border flow intensities

## Questions?

For issues or questions about the border regions analysis:
1. Check the generated output files for detailed data
2. Review `example_border_region_usage.py` for usage patterns
3. Modify `identify_border_regions.py` parameters as needed

## Citation

When using this analysis in publications, please acknowledge:
- NUTS 2021 boundaries (© EuroGeographics for the administrative boundaries)
- TransComp model framework
