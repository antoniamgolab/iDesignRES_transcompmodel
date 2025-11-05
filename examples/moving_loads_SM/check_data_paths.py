"""
Quick check: Verify that data paths exist and files can be loaded

Run this first to test your paths before running the full calculation.
"""

import os
from pathlib import Path

print("="*80)
print("DATA PATH VERIFICATION")
print("="*80)

# Base directory
base_dir = Path(__file__).parent.parent.parent
print(f"\nBase directory: {base_dir}")

# Check network edges
print("\n" + "-"*80)
print("1. NETWORK EDGES")
print("-"*80)

network_paths = [
    base_dir / "data" / "Trucktraffic_NUTS3" / "04_network-edges",
    base_dir / "data" / "Trucktraffic_NUTS3" / "network-edges",
    base_dir / "data" / "04_network-edges",
]

network_found = None
for path in network_paths:
    print(f"\nTrying: {path}")
    if path.exists():
        print(f"  [OK] EXISTS!")
        if path.is_dir():
            files = list(path.glob("*"))
            print(f"  Contains {len(files)} files:")
            for f in files[:10]:  # Show first 10
                print(f"    - {f.name}")
            if len(files) > 10:
                print(f"    ... and {len(files) - 10} more files")

            # Check for geodata files
            geo_files = list(path.glob("*.shp")) + list(path.glob("*.geojson")) + list(path.glob("*.gpkg"))
            if geo_files:
                print(f"  [OK] Found {len(geo_files)} geodata files")
                network_found = path
                break
            else:
                print(f"  [X] No .shp, .geojson, or .gpkg files found")
        else:
            print(f"  (This is a file, not a directory)")
    else:
        print(f"  [X] Does not exist")

if network_found:
    print(f"\n[OK] Network edges found at: {network_found}")
else:
    print(f"\n[X] Network edges NOT FOUND")
    print(f"\nPlease check your data directory structure.")

# Check NUTS-2 shapefile
print("\n" + "-"*80)
print("2. NUTS-2 SHAPEFILE")
print("-"*80)

nuts2_paths = [
    base_dir / "data" / "NUTS_RG_20M_2021_4326.shp" / "NUTS_RG_20M_2021_4326.shp",
    base_dir / "data" / "NUTS_RG_20M_2021_4326.shp",
    base_dir / "data" / "NUTS" / "NUTS_RG_20M_2021_4326.shp",
]

nuts2_found = None
for path in nuts2_paths:
    print(f"\nTrying: {path}")
    if path.exists():
        print(f"  [OK] EXISTS!")
        if path.is_file():
            size_mb = path.stat().st_size / (1024 * 1024)
            print(f"  File size: {size_mb:.2f} MB")
            nuts2_found = path
            break
        elif path.is_dir():
            files = list(path.glob("*.shp"))
            if files:
                print(f"  Contains {len(files)} shapefiles:")
                for f in files:
                    print(f"    - {f.name}")
                nuts2_found = files[0]
                break
    else:
        print(f"  [X] Does not exist")

if nuts2_found:
    print(f"\n[OK] NUTS-2 shapefile found at: {nuts2_found}")
else:
    print(f"\n[X] NUTS-2 shapefile NOT FOUND")
    print(f"\nPlease check your data directory structure.")

# Test loading with geopandas
print("\n" + "="*80)
print("TESTING FILE LOADING")
print("="*80)

if network_found and nuts2_found:
    try:
        import geopandas as gpd

        print("\nLoading network edges...")
        edges = gpd.read_file(network_found)
        print(f"  [OK] Loaded {len(edges)} features")
        print(f"  CRS: {edges.crs}")
        print(f"  Columns: {edges.columns.tolist()}")

        print("\nLoading NUTS-2 regions...")
        nuts2 = gpd.read_file(nuts2_found)
        print(f"  [OK] Loaded {len(nuts2)} regions")
        print(f"  CRS: {nuts2.crs}")
        print(f"  Columns: {nuts2.columns.tolist()}")

        # Filter to NUTS-2
        if 'LEVL_CODE' in nuts2.columns:
            nuts2_filtered = nuts2[nuts2['LEVL_CODE'] == 2]
        elif 'NUTS_ID' in nuts2.columns:
            nuts2_filtered = nuts2[nuts2['NUTS_ID'].str.len() == 4]
        else:
            nuts2_filtered = nuts2

        print(f"  NUTS-2 regions after filtering: {len(nuts2_filtered)}")

        print("\n" + "="*80)
        print("[OK] ALL CHECKS PASSED!")
        print("="*80)
        print("\nYou can now run:")
        print("  python calculate_highway_km_per_nuts2.py")
        print("or")
        print("  python calculate_highway_km_simple.py")

    except ImportError:
        print("\n[X] Error: geopandas not installed")
        print("\nInstall with: pip install geopandas")
    except Exception as e:
        print(f"\n[X] Error loading files: {e}")
        import traceback
        traceback.print_exc()
else:
    print("\n" + "="*80)
    print("[X] CANNOT RUN CALCULATION")
    print("="*80)
    print("\nPlease ensure both network edges and NUTS-2 shapefile exist.")
