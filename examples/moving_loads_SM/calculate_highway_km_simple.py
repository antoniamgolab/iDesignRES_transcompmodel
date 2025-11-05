"""
Simple version: Calculate highway km per NUTS-2 region

Edit the paths below to match your data location, then run:
    python calculate_highway_km_simple.py
"""

import geopandas as gpd
import pandas as pd

# =============================================================================
# EDIT THESE PATHS TO MATCH YOUR DATA
# =============================================================================

# Path to your network edges (roads/highways)
# This can be a .shp file, .geojson, .gpkg, or directory containing shapefiles
NETWORK_PATH = r"C:\Github\SM\iDesignRES_transcompmodel\data\Trucktraffic_NUTS3\04_network-edges"

# Path to NUTS-2 shapefile
NUTS2_PATH = r"C:\Github\SM\iDesignRES_transcompmodel\data\NUTS_RG_20M_2021_4326.shp\NUTS_RG_20M_2021_4326.shp"

# Output CSV filename
OUTPUT_CSV = "highway_km_per_nuts2.csv"

# CRS for distance calculation (meters) - don't change unless you know what you're doing
DISTANCE_CRS = "EPSG:3035"  # LAEA Europe


# =============================================================================
# MAIN SCRIPT - NO NEED TO EDIT BELOW THIS LINE
# =============================================================================

def main():
    print("Loading data...")

    # Load network edges
    print(f"  Loading network from: {NETWORK_PATH}")
    edges = gpd.read_file(NETWORK_PATH)
    print(f"  ✓ Loaded {len(edges)} network edges")

    # Load NUTS-2 regions
    print(f"  Loading NUTS-2 from: {NUTS2_PATH}")
    nuts2 = gpd.read_file(NUTS2_PATH)

    # Filter to NUTS-2 level (4-character codes)
    if 'LEVL_CODE' in nuts2.columns:
        nuts2 = nuts2[nuts2['LEVL_CODE'] == 2].copy()
    elif 'NUTS_ID' in nuts2.columns:
        nuts2 = nuts2[nuts2['NUTS_ID'].str.len() == 4].copy()

    print(f"  ✓ Loaded {len(nuts2)} NUTS-2 regions")

    # Ensure same CRS
    if edges.crs != nuts2.crs:
        print(f"  Reprojecting edges to match NUTS-2 CRS...")
        edges = edges.to_crs(nuts2.crs)

    # Spatial join: find which edges intersect which regions
    print("\nPerforming spatial join...")
    joined = gpd.sjoin(edges, nuts2, how='inner', predicate='intersects')
    print(f"  ✓ Found {len(joined)} edge-region intersections")

    # Get NUTS-2 ID column
    nuts2_col = 'NUTS_ID' if 'NUTS_ID' in nuts2.columns else nuts2.columns[0]

    # Project to calculate accurate distances
    print(f"\nCalculating lengths in {DISTANCE_CRS}...")
    joined_proj = joined.to_crs(DISTANCE_CRS)

    # Calculate length in km
    joined_proj['length_km'] = joined_proj.geometry.length / 1000.0

    # Sum by NUTS-2 region
    print("  Summing by NUTS-2 region...")
    results = joined_proj.groupby(nuts2_col)['length_km'].sum().reset_index()
    results.columns = ['NUTS2_CODE', 'highway_km']

    # Add regions with 0 km
    all_nuts2 = nuts2[nuts2_col].unique()
    missing = set(all_nuts2) - set(results['NUTS2_CODE'])
    if missing:
        missing_df = pd.DataFrame({
            'NUTS2_CODE': list(missing),
            'highway_km': 0.0
        })
        results = pd.concat([results, missing_df], ignore_index=True)

    # Sort
    results = results.sort_values('NUTS2_CODE').reset_index(drop=True)

    # Display summary
    print("\n" + "="*70)
    print("RESULTS SUMMARY")
    print("="*70)
    print(f"Total regions: {len(results)}")
    print(f"Total highway km: {results['highway_km'].sum():.2f}")
    print(f"Average km per region: {results['highway_km'].mean():.2f}")

    print("\nTop 10 regions by highway km:")
    print(results.nlargest(10, 'highway_km').to_string(index=False))

    # Save to CSV
    results.to_csv(OUTPUT_CSV, index=False)
    print(f"\n✓ Results saved to: {OUTPUT_CSV}")

    return results


if __name__ == "__main__":
    try:
        df = main()
    except FileNotFoundError as e:
        print(f"\n✗ Error: File not found!")
        print(f"  {e}")
        print("\nPlease check the paths at the top of this script.")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
