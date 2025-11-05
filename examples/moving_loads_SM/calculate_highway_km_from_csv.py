"""
Calculate highway km per NUTS-2 region from CSV network data

This version is specifically for your data format:
- Network edges: CSV with node IDs and Distance column
- Network nodes: CSV with coordinates
- NUTS-2: Shapefile

Usage:
    python calculate_highway_km_from_csv.py
"""

import pandas as pd
import geopandas as gpd
from shapely.geometry import LineString, Point
import numpy as np

print("="*80)
print("HIGHWAY KILOMETERS PER NUTS-2 REGION (CSV VERSION)")
print("="*80)

# =============================================================================
# File paths (relative to script location)
# =============================================================================

EDGES_CSV = "data/Trucktraffic_NUTS3/04_network-edges.csv"
NODES_CSV = "data/Trucktraffic_NUTS3/03_network-nodes.csv"
NUTS2_SHP = "data/NUTS_RG_20M_2021_4326.shp/NUTS_RG_20M_2021_4326.shp"
OUTPUT_CSV = "highway_km_per_nuts2.csv"

# =============================================================================
# Load data
# =============================================================================

print("\n1. Loading network edges...")
edges_df = pd.read_csv(EDGES_CSV)
print(f"   Loaded {len(edges_df)} edges")
print(f"   Columns: {edges_df.columns.tolist()}")

print("\n2. Loading network nodes...")
nodes_df = pd.read_csv(NODES_CSV)
print(f"   Loaded {len(nodes_df)} nodes")
print(f"   Columns: {nodes_df.columns.tolist()}")

print("\n3. Loading NUTS-2 regions...")
nuts2_gdf = gpd.read_file(NUTS2_SHP)
print(f"   Loaded {len(nuts2_gdf)} NUTS regions")

# Filter to NUTS-2 (4-character codes)
if 'LEVL_CODE' in nuts2_gdf.columns:
    nuts2_gdf = nuts2_gdf[nuts2_gdf['LEVL_CODE'] == 2].copy()
elif 'NUTS_ID' in nuts2_gdf.columns:
    nuts2_gdf = nuts2_gdf[nuts2_gdf['NUTS_ID'].str.len() == 4].copy()

print(f"   Filtered to {len(nuts2_gdf)} NUTS-2 regions")

# Get NUTS-2 ID column
nuts2_col = 'NUTS_ID' if 'NUTS_ID' in nuts2_gdf.columns else [c for c in nuts2_gdf.columns if 'NUTS' in c or 'ID' in c][0]
print(f"   Using column: {nuts2_col}")

# =============================================================================
# Create geometries from CSV
# =============================================================================

print("\n4. Creating edge geometries from node coordinates...")

# Create node lookup dictionary
node_coords = {}
for _, row in nodes_df.iterrows():
    node_id = row['Network_Node_ID']
    x = row['Network_Node_X']
    y = row['Network_Node_Y']
    node_coords[node_id] = (x, y)

print(f"   Created coordinate lookup for {len(node_coords)} nodes")

# Create LineString geometries for edges
geometries = []
valid_indices = []

print("   Building edge geometries...")
for idx, row in edges_df.iterrows():
    node_a = row['Network_Node_A_ID']
    node_b = row['Network_Node_B_ID']

    if node_a in node_coords and node_b in node_coords:
        coord_a = node_coords[node_a]
        coord_b = node_coords[node_b]
        line = LineString([coord_a, coord_b])
        geometries.append(line)
        valid_indices.append(idx)

    if (idx + 1) % 10000 == 0:
        print(f"      Processed {idx + 1}/{len(edges_df)} edges...")

print(f"   Created {len(geometries)} valid edge geometries")

# Create GeoDataFrame
edges_gdf = gpd.GeoDataFrame(
    edges_df.loc[valid_indices].copy(),
    geometry=geometries,
    crs="EPSG:4326"  # WGS84 (lat/lon)
)

print(f"   Edge GeoDataFrame CRS: {edges_gdf.crs}")

# =============================================================================
# Spatial join
# =============================================================================

print("\n5. Performing spatial join with NUTS-2 regions...")

# Ensure same CRS
if edges_gdf.crs != nuts2_gdf.crs:
    print(f"   Reprojecting edges from {edges_gdf.crs} to {nuts2_gdf.crs}")
    edges_gdf = edges_gdf.to_crs(nuts2_gdf.crs)

# Spatial join
print("   Joining edges with regions (this may take a while)...")
joined = gpd.sjoin(edges_gdf, nuts2_gdf, how='inner', predicate='intersects')
print(f"   Found {len(joined)} edge-region intersections")

# =============================================================================
# Calculate total km per region
# =============================================================================

print("\n6. Summing distances per NUTS-2 region...")

# Use the Distance column from the CSV (already in km)
results = joined.groupby(nuts2_col)['Distance'].sum().reset_index()
results.columns = ['NUTS2_CODE', 'highway_km']

# Add regions with 0 km
all_nuts2_codes = nuts2_gdf[nuts2_col].unique()
missing_codes = set(all_nuts2_codes) - set(results['NUTS2_CODE'])

if missing_codes:
    print(f"   Adding {len(missing_codes)} regions with 0 km")
    missing_df = pd.DataFrame({
        'NUTS2_CODE': list(missing_codes),
        'highway_km': 0.0
    })
    results = pd.concat([results, missing_df], ignore_index=True)

# Sort by code
results = results.sort_values('NUTS2_CODE').reset_index(drop=True)

# =============================================================================
# Display results
# =============================================================================

print("\n" + "="*80)
print("RESULTS")
print("="*80)

print(f"\nTotal regions: {len(results)}")
print(f"Total highway km: {results['highway_km'].sum():.2f}")
print(f"Average km per region: {results['highway_km'].mean():.2f}")
print(f"Median km per region: {results['highway_km'].median():.2f}")

print("\nTop 20 regions by highway km:")
print(results.nlargest(20, 'highway_km').to_string(index=False))

# For Germany-Denmark-Sweden cluster
print("\n" + "-"*80)
print("GERMANY-DENMARK-SWEDEN CLUSTER:")
print("-"*80)
cluster_codes = ['DEF0', 'DK01', 'DK02', 'DK03', 'DK04', 'DK05', 'SE22', 'SE23']
cluster_results = results[results['NUTS2_CODE'].isin(cluster_codes)]
print(cluster_results.to_string(index=False))
print(f"\nTotal in cluster: {cluster_results['highway_km'].sum():.2f} km")

# =============================================================================
# Save results
# =============================================================================

print("\n" + "="*80)
results.to_csv(OUTPUT_CSV, index=False)
print(f"[OK] Results saved to: {OUTPUT_CSV}")
print("="*80)
