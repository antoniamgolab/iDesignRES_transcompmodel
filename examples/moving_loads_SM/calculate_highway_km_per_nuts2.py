"""
Calculate total highway kilometers per NUTS-2 region

This script:
1. Loads network edges (highways/roads) from truck traffic data
2. Loads NUTS-2 region boundaries
3. Spatially intersects edges with NUTS-2 regions
4. Calculates total km of highways in each NUTS-2 region
5. Exports results to CSV

Requirements:
- geopandas
- shapely
- pandas

Input data:
- Network edges: data/Trucktraffic_NUTS3/04_network-edges
- NUTS-2 shapefile: data/NUTS_RG_20M_2021_4326.shp/NUTS_RG_20M_2021_4326.shp
"""

import geopandas as gpd
import pandas as pd
import numpy as np
from pathlib import Path
import os
import sys
from shapely.geometry import LineString, MultiLineString
from shapely.ops import unary_union

# =============================================================================
# Configuration
# =============================================================================

# Base paths
BASE_DIR = Path(__file__).parent.parent.parent  # Go up to repo root
DATA_DIR = BASE_DIR / "data"

# Input paths (adjust these if your structure is different)
NETWORK_EDGES_PATH = DATA_DIR / "Trucktraffic_NUTS3" / "04_network-edges"
NUTS2_SHAPEFILE_PATH = DATA_DIR / "NUTS_RG_20M_2021_4326.shp" / "NUTS_RG_20M_2021_4326.shp"

# Alternative paths to try
ALTERNATIVE_NETWORK_PATHS = [
    DATA_DIR / "Trucktraffic_NUTS3" / "network-edges",
    DATA_DIR / "04_network-edges",
    DATA_DIR / "network_edges",
]

ALTERNATIVE_NUTS2_PATHS = [
    DATA_DIR / "NUTS_RG_20M_2021_4326.shp",
    DATA_DIR / "NUTS" / "NUTS_RG_20M_2021_4326.shp",
    DATA_DIR / "NUTS_RG_20M_2021_4326" / "NUTS_RG_20M_2021_4326.shp",
]

# Output
OUTPUT_CSV = Path(__file__).parent / "highway_km_per_nuts2.csv"

# CRS for distance calculations (use a projected CRS for accurate measurements)
DISTANCE_CRS = "EPSG:3035"  # ETRS89-extended / LAEA Europe (meters)


# =============================================================================
# Helper Functions
# =============================================================================

def find_file(primary_path, alternative_paths, file_description):
    """
    Try to find a file, checking primary path and alternatives
    """
    print(f"\nSearching for {file_description}...")

    # Try primary path
    if primary_path.exists():
        print(f"  ✓ Found at: {primary_path}")
        return primary_path

    # Try alternatives
    for alt_path in alternative_paths:
        if alt_path.exists():
            print(f"  ✓ Found at: {alt_path}")
            return alt_path

    # Not found
    print(f"  ✗ Not found!")
    print(f"    Primary path tried: {primary_path}")
    print(f"    Alternatives tried:")
    for alt_path in alternative_paths:
        print(f"      - {alt_path}")
    return None


def load_network_edges(network_path):
    """
    Load network edges from various possible formats
    """
    print(f"\nLoading network edges from: {network_path}")

    # If it's a directory, look for shapefiles or other geodata
    if network_path.is_dir():
        print(f"  Path is a directory, looking for geodata files...")

        # Try common formats
        for pattern in ["*.shp", "*.geojson", "*.gpkg", "*.json"]:
            files = list(network_path.glob(pattern))
            if files:
                print(f"  Found {len(files)} {pattern} files")
                gdf = gpd.read_file(files[0])
                print(f"  ✓ Loaded {len(gdf)} features from {files[0].name}")
                return gdf

        # If no files found, list what's there
        print(f"  Files in directory:")
        for item in network_path.iterdir():
            print(f"    - {item.name}")
        raise FileNotFoundError(f"No geodata files found in {network_path}")

    # If it's a file, load it directly
    elif network_path.is_file():
        gdf = gpd.read_file(network_path)
        print(f"  ✓ Loaded {len(gdf)} features")
        return gdf

    else:
        raise FileNotFoundError(f"Path not found: {network_path}")


def load_nuts2_regions(nuts2_path):
    """
    Load NUTS-2 regions and filter to NUTS2 level
    """
    print(f"\nLoading NUTS-2 regions from: {nuts2_path}")

    gdf = gpd.read_file(nuts2_path)
    print(f"  ✓ Loaded {len(gdf)} total NUTS regions")

    # Filter to NUTS-2 level (4-character codes)
    if 'LEVL_CODE' in gdf.columns:
        gdf_nuts2 = gdf[gdf['LEVL_CODE'] == 2].copy()
    elif 'NUTS_ID' in gdf.columns:
        gdf_nuts2 = gdf[gdf['NUTS_ID'].str.len() == 4].copy()
    else:
        # Try to infer from ID length
        id_col = [c for c in gdf.columns if 'NUTS' in c or 'ID' in c][0]
        gdf_nuts2 = gdf[gdf[id_col].str.len() == 4].copy()

    print(f"  ✓ Filtered to {len(gdf_nuts2)} NUTS-2 regions")

    return gdf_nuts2


def calculate_length_in_region(edge_geom, region_geom, crs):
    """
    Calculate the length of an edge that falls within a region
    Returns length in kilometers
    """
    try:
        # Intersect edge with region
        intersection = edge_geom.intersection(region_geom)

        if intersection.is_empty:
            return 0.0

        # Calculate length in the projected CRS (meters)
        if isinstance(intersection, (LineString, MultiLineString)):
            # Create temporary GeoDataFrame for projection
            temp_gdf = gpd.GeoDataFrame(geometry=[intersection], crs=crs)
            temp_gdf_proj = temp_gdf.to_crs(DISTANCE_CRS)
            length_m = temp_gdf_proj.geometry.length.sum()
            return length_m / 1000.0  # Convert to km
        else:
            return 0.0

    except Exception as e:
        print(f"    Warning: Error calculating intersection: {e}")
        return 0.0


def calculate_highway_km_per_nuts2(edges_gdf, nuts2_gdf, method='spatial_join'):
    """
    Calculate total highway km per NUTS-2 region

    Parameters:
    -----------
    edges_gdf : GeoDataFrame
        Network edges (roads/highways)
    nuts2_gdf : GeoDataFrame
        NUTS-2 regions
    method : str
        'spatial_join' (faster) or 'intersection' (more accurate)

    Returns:
    --------
    pd.DataFrame with columns: NUTS2_CODE, highway_km
    """
    print(f"\nCalculating highway lengths per NUTS-2 region...")
    print(f"Method: {method}")

    # Ensure both are in the same CRS
    original_crs = edges_gdf.crs
    if edges_gdf.crs != nuts2_gdf.crs:
        print(f"  Reprojecting edges from {edges_gdf.crs} to {nuts2_gdf.crs}")
        edges_gdf = edges_gdf.to_crs(nuts2_gdf.crs)

    # Get NUTS-2 ID column name
    nuts2_id_col = None
    for col in ['NUTS_ID', 'nuts2', 'NUTS2', 'id', 'ID']:
        if col in nuts2_gdf.columns:
            nuts2_id_col = col
            break

    if nuts2_id_col is None:
        raise ValueError(f"Could not find NUTS-2 ID column. Available columns: {nuts2_gdf.columns.tolist()}")

    print(f"  Using NUTS-2 ID column: {nuts2_id_col}")

    results = []

    if method == 'spatial_join':
        # Faster method: spatial join
        print(f"  Performing spatial join...")

        # Spatial join edges with NUTS-2 regions
        joined = gpd.sjoin(edges_gdf, nuts2_gdf, how='inner', predicate='intersects')

        print(f"  Found {len(joined)} edge-region intersections")

        # Project to calculate accurate lengths
        print(f"  Projecting to {DISTANCE_CRS} for distance calculation...")
        joined_proj = joined.to_crs(DISTANCE_CRS)

        # Calculate lengths
        joined_proj['length_km'] = joined_proj.geometry.length / 1000.0

        # Group by NUTS-2 region
        results_df = joined_proj.groupby(nuts2_id_col)['length_km'].sum().reset_index()
        results_df.columns = ['NUTS2_CODE', 'highway_km']

    else:  # method == 'intersection'
        # More accurate but slower: calculate actual intersections
        print(f"  Calculating intersections for {len(nuts2_gdf)} regions...")

        for idx, region in nuts2_gdf.iterrows():
            nuts2_code = region[nuts2_id_col]
            region_geom = region.geometry

            # Find edges that intersect this region
            intersecting_edges = edges_gdf[edges_gdf.intersects(region_geom)]

            if len(intersecting_edges) == 0:
                total_km = 0.0
            else:
                # Calculate length of each edge within the region
                total_km = 0.0
                for _, edge in intersecting_edges.iterrows():
                    km = calculate_length_in_region(edge.geometry, region_geom, edges_gdf.crs)
                    total_km += km

            results.append({
                'NUTS2_CODE': nuts2_code,
                'highway_km': total_km
            })

            if (idx + 1) % 50 == 0:
                print(f"    Processed {idx + 1}/{len(nuts2_gdf)} regions...")

        results_df = pd.DataFrame(results)

    # Add regions with 0 km if they're missing
    all_nuts2_codes = nuts2_gdf[nuts2_id_col].unique()
    missing_codes = set(all_nuts2_codes) - set(results_df['NUTS2_CODE'])

    if missing_codes:
        print(f"  Adding {len(missing_codes)} regions with 0 km")
        missing_df = pd.DataFrame({
            'NUTS2_CODE': list(missing_codes),
            'highway_km': 0.0
        })
        results_df = pd.concat([results_df, missing_df], ignore_index=True)

    # Sort by NUTS2 code
    results_df = results_df.sort_values('NUTS2_CODE').reset_index(drop=True)

    print(f"  ✓ Calculated highway km for {len(results_df)} NUTS-2 regions")
    print(f"  Total highway km: {results_df['highway_km'].sum():.2f}")

    return results_df


# =============================================================================
# Main Function
# =============================================================================

def main():
    """
    Main workflow
    """
    print("="*80)
    print("HIGHWAY KILOMETERS PER NUTS-2 REGION CALCULATOR")
    print("="*80)

    # Find input files
    network_path = find_file(NETWORK_EDGES_PATH, ALTERNATIVE_NETWORK_PATHS, "network edges")
    nuts2_path = find_file(NUTS2_SHAPEFILE_PATH, ALTERNATIVE_NUTS2_PATHS, "NUTS-2 shapefile")

    if network_path is None:
        print("\n✗ Error: Could not find network edges data!")
        print("\nPlease specify the correct path in the script configuration.")
        return 1

    if nuts2_path is None:
        print("\n✗ Error: Could not find NUTS-2 shapefile!")
        print("\nPlease specify the correct path in the script configuration.")
        return 1

    # Load data
    try:
        edges_gdf = load_network_edges(network_path)
    except Exception as e:
        print(f"\n✗ Error loading network edges: {e}")
        return 1

    try:
        nuts2_gdf = load_nuts2_regions(nuts2_path)
    except Exception as e:
        print(f"\n✗ Error loading NUTS-2 regions: {e}")
        return 1

    # Print data info
    print("\n" + "="*80)
    print("DATA SUMMARY:")
    print("="*80)
    print(f"Network edges:")
    print(f"  - Features: {len(edges_gdf)}")
    print(f"  - CRS: {edges_gdf.crs}")
    print(f"  - Columns: {edges_gdf.columns.tolist()}")

    print(f"\nNUTS-2 regions:")
    print(f"  - Regions: {len(nuts2_gdf)}")
    print(f"  - CRS: {nuts2_gdf.crs}")
    print(f"  - Columns: {nuts2_gdf.columns.tolist()}")

    # Calculate highway km per NUTS-2
    results_df = calculate_highway_km_per_nuts2(
        edges_gdf,
        nuts2_gdf,
        method='spatial_join'  # Change to 'intersection' for more accuracy (slower)
    )

    # Display top regions
    print("\n" + "="*80)
    print("TOP 10 REGIONS BY HIGHWAY KM:")
    print("="*80)
    print(results_df.nlargest(10, 'highway_km').to_string(index=False))

    # Export to CSV
    print(f"\n" + "="*80)
    print(f"EXPORTING RESULTS")
    print("="*80)
    results_df.to_csv(OUTPUT_CSV, index=False)
    print(f"✓ Results saved to: {OUTPUT_CSV}")

    # Summary statistics
    print("\n" + "="*80)
    print("SUMMARY STATISTICS:")
    print("="*80)
    print(f"Total regions: {len(results_df)}")
    print(f"Total highway km: {results_df['highway_km'].sum():.2f}")
    print(f"Average km per region: {results_df['highway_km'].mean():.2f}")
    print(f"Median km per region: {results_df['highway_km'].median():.2f}")
    print(f"Max km in a region: {results_df['highway_km'].max():.2f}")
    print(f"Regions with 0 km: {(results_df['highway_km'] == 0).sum()}")

    print("\n" + "="*80)
    print("✓ DONE!")
    print("="*80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
