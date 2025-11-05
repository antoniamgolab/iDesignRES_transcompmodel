# Highway Kilometers per NUTS-2 Region - User Guide

## 📋 What This Script Does

Calculates the total kilometers of highways/roads in each NUTS-2 region by:
1. Loading network edges (road segments) from truck traffic data
2. Loading NUTS-2 region boundaries from shapefile
3. Spatially intersecting roads with regions
4. Calculating total length in each region
5. Exporting results to CSV

## 📂 Required Input Files

### 1. Network Edges
**Path**: `data/Trucktraffic_NUTS3/04_network-edges/`

This should contain road network data in one of these formats:
- `.shp` (Shapefile)
- `.geojson` (GeoJSON)
- `.gpkg` (GeoPackage)

### 2. NUTS-2 Boundaries
**Path**: `data/NUTS_RG_20M_2021_4326.shp/NUTS_RG_20M_2021_4326.shp`

Official NUTS regions shapefile from Eurostat.

## 🚀 How to Run

### Method 1: Direct Execution
```bash
cd C:\Github\SM\iDesignRES_transcompmodel\examples\moving_loads_SM
python calculate_highway_km_per_nuts2.py
```

### Method 2: From Jupyter Notebook
```python
%run calculate_highway_km_per_nuts2.py
```

## ⚙️ Configuration

If your data paths are different, edit these lines in the script:

```python
# Line ~28-29
NETWORK_EDGES_PATH = DATA_DIR / "Trucktraffic_NUTS3" / "04_network-edges"
NUTS2_SHAPEFILE_PATH = DATA_DIR / "NUTS_RG_20M_2021_4326.shp" / "NUTS_RG_20M_2021_4326.shp"
```

## 📤 Output

### CSV File: `highway_km_per_nuts2.csv`

Format:
```csv
NUTS2_CODE,highway_km
AT11,1234.56
AT12,987.65
...
```

Columns:
- `NUTS2_CODE`: NUTS-2 region code (e.g., AT11, DE21)
- `highway_km`: Total kilometers of highways in that region

## 🔧 Two Methods Available

### 1. Spatial Join (Default - Faster)
```python
method='spatial_join'
```
- Faster computation
- Good approximation
- Recommended for large datasets

### 2. Intersection (More Accurate)
```python
method='intersection'
```
- Precise calculation
- Clips edges at region boundaries
- Slower but more accurate

To change the method, edit line ~377 in the script:
```python
results_df = calculate_highway_km_per_nuts2(
    edges_gdf,
    nuts2_gdf,
    method='intersection'  # Change here
)
```

## 📊 Expected Output

When run successfully, you'll see:
```
================================================================================
HIGHWAY KILOMETERS PER NUTS-2 REGION CALCULATOR
================================================================================

Searching for network edges...
  ✓ Found at: data/Trucktraffic_NUTS3/04_network-edges

Loading network edges from: ...
  ✓ Loaded 15234 features

Loading NUTS-2 regions from: ...
  ✓ Loaded 1234 total NUTS regions
  ✓ Filtered to 242 NUTS-2 regions

Calculating highway lengths per NUTS-2 region...
  ✓ Calculated highway km for 242 NUTS-2 regions
  Total highway km: 123456.78

================================================================================
TOP 10 REGIONS BY HIGHWAY KM:
================================================================================
NUTS2_CODE  highway_km
      DE21     5432.10
      FR10     4321.09
      ...

✓ Results saved to: highway_km_per_nuts2.csv
```

## 🐛 Troubleshooting

### Problem: "Could not find network edges"
**Solution**: Check that the path exists:
```python
import os
path = "C:/Github/SM/iDesignRES_transcompmodel/data/Trucktraffic_NUTS3/04_network-edges"
print(os.path.exists(path))
print(os.listdir(path))  # See what's in the directory
```

### Problem: "Could not find NUTS-2 shapefile"
**Solution**: The script tries multiple alternative paths. Add yours:
```python
ALTERNATIVE_NUTS2_PATHS = [
    DATA_DIR / "your_path_here" / "NUTS_RG_20M_2021_4326.shp",
]
```

### Problem: "No geodata files found"
**Solution**: The network edges directory should contain `.shp`, `.geojson`, or `.gpkg` files.

### Problem: Memory error with large datasets
**Solution**: Use the 'spatial_join' method (default) instead of 'intersection'

## 📝 Script Features

✅ Automatic file format detection (shp, geojson, gpkg)
✅ Tries multiple alternative paths
✅ Handles different CRS automatically
✅ Accurate distance calculation using projected CRS (EPSG:3035)
✅ Progress reporting
✅ Summary statistics
✅ Exports to CSV

## 🔍 Verifying Results

After running, check the output:

```python
import pandas as pd

# Load results
df = pd.read_csv('highway_km_per_nuts2.csv')

# Check specific regions
print(df[df['NUTS2_CODE'].isin(['DK01', 'DK02', 'DK03', 'DK04', 'DK05'])])

# Summary
print(df.describe())

# Regions with most highways
print(df.nlargest(20, 'highway_km'))
```

## 🗺️ Understanding the Results

- **High km regions**: Usually larger regions or major transport corridors
- **0 km regions**: Islands or regions without data coverage
- **Total km**: Sum across all regions (should match your network total)

## ⚠️ Important Notes

1. **CRS Matters**: The script uses EPSG:3035 (LAEA Europe) for accurate distance calculations in meters
2. **Edge Cases**: Highways crossing region boundaries are counted in both regions (spatial_join) or split (intersection)
3. **Data Quality**: Results depend on the completeness of your network edges data

## 📧 Need Help?

If you get errors:
1. Check the error message - it usually tells you what's wrong
2. Verify file paths exist
3. Check that files are valid shapefiles/geodata
4. Make sure you have geopandas installed: `pip install geopandas`

---

**File created**: `calculate_highway_km_per_nuts2.py`
**Output file**: `highway_km_per_nuts2.csv`
