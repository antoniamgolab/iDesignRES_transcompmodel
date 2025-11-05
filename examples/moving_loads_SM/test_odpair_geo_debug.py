#!/usr/bin/env python3
"""
Debug script for _find_odpairs_and_geo function
"""
import yaml
import os
from pathlib import Path

# Simulate the loaded_runs structure based on how data is loaded
def load_case_data(input_folder):
    """Load a case's input data from YAML files"""
    input_data = {}

    folder_path = Path(input_folder)
    if not folder_path.exists():
        print(f"Folder not found: {input_folder}")
        return input_data

    # Load each YAML file
    for yaml_file in folder_path.glob("*.yaml"):
        key_name = yaml_file.stem  # Filename without extension
        print(f"Loading {yaml_file.name}...")
        try:
            with open(yaml_file, 'r') as f:
                input_data[key_name] = yaml.safe_load(f)
        except Exception as e:
            print(f"  Error loading {yaml_file.name}: {e}")

    return input_data


def _find_odpairs_and_geo_FIXED(loaded_runs):
    """Fixed version of the function"""
    odpair_map = {}        # odpair_id -> (origin_geoid, dest_geoid)
    geoid2country = {}     # geoid -> country code/name

    # Search through cases for odpair definitions and geographic elements
    for case_name, case in loaded_runs.items():
        print(f"\n=== Processing case: {case_name} ===")
        inp = case.get("input_data", {}) or {}

        print(f"  Available keys in input_data: {list(inp.keys())}")

        # ========== GEOGRAPHIC ELEMENTS ==========
        # Try different possible key names
        geo_key_found = None
        for key in ("GeographicElement", "GeographicElements", "geographicelements",
                    "geographic_elements", "geoelements", "geo_elements", "geographicelement"):
            if key in inp:
                geo_key_found = key
                break

        if geo_key_found:
            print(f"  Found geographic data under key: '{geo_key_found}'")
            items = inp[geo_key_found]

            # Check what type it is
            print(f"  Geographic data type: {type(items)}")

            if isinstance(items, list):
                print(f"  Geographic data is a list with {len(items)} items")
                # List of dicts (most common in YAML)
                for i, entry in enumerate(items):
                    if not isinstance(entry, dict):
                        continue

                    # Extract geo_id
                    geo_id = entry.get('id')

                    # Extract country
                    country = entry.get('country')

                    if geo_id is not None and country is not None:
                        geoid2country[int(geo_id)] = str(country)
                        if i < 3:  # Show first 3
                            print(f"    geo_id={geo_id} -> country={country}")
            else:
                print(f"  WARNING: Geographic data is not a list (type={type(items)})")
        else:
            print(f"  WARNING: No geographic element data found!")

        # ========== ODPAIRS ==========
        odpair_key_found = None
        for key in ("Odpair", "odpairs", "od_pairs", "odPairs", "od_pair_list",
                    "ODpairs", "odpair", "od_pair"):
            if key in inp:
                odpair_key_found = key
                break

        if odpair_key_found:
            print(f"  Found odpair data under key: '{odpair_key_found}'")
            items = inp[odpair_key_found]

            print(f"  Odpair data type: {type(items)}")

            if isinstance(items, list):
                print(f"  Odpair data is a list with {len(items)} items")
                # List of dicts (most common in YAML)
                for i, entry in enumerate(items):
                    if not isinstance(entry, dict):
                        continue

                    # Extract odpair_id
                    odpair_id = entry.get('id')

                    # Extract origin and destination
                    origin = entry.get('from')
                    dest = entry.get('to')

                    if odpair_id is not None and origin is not None and dest is not None:
                        try:
                            odpair_map[int(odpair_id)] = (int(origin), int(dest))
                            if i < 3:  # Show first 3
                                print(f"    odpair_id={odpair_id}: {origin} -> {dest}")
                        except (ValueError, TypeError) as e:
                            print(f"    WARNING: Could not convert odpair {odpair_id}: {e}")
            else:
                print(f"  WARNING: Odpair data is not a list (type={type(items)})")
        else:
            print(f"  WARNING: No odpair data found!")

    print(f"\n=== RESULTS ===")
    print(f"Total geoid2country mappings: {len(geoid2country)}")
    print(f"Total odpair mappings: {len(odpair_map)}")

    # Show samples
    if geoid2country:
        print(f"\nSample geoid2country (first 5):")
        for i, (gid, country) in enumerate(list(geoid2country.items())[:5]):
            print(f"  {gid} -> {country}")

    if odpair_map:
        print(f"\nSample odpair_map (first 5):")
        for i, (oid, (orig, dest)) in enumerate(list(odpair_map.items())[:5]):
            print(f"  {oid}: {orig} -> {dest}")

    return odpair_map, geoid2country


if __name__ == "__main__":
    # Test with the latest case
    case_folder = "input_data/case_20251029_154754"

    print("=" * 80)
    print("LOADING DATA")
    print("=" * 80)

    # Load the case data
    input_data = load_case_data(case_folder)

    # Create a mock loaded_runs structure
    loaded_runs = {
        "test_case": {
            "input_data": input_data
        }
    }

    print("\n" + "=" * 80)
    print("RUNNING _find_odpairs_and_geo_FIXED")
    print("=" * 80)

    # Test the fixed function
    odpair_map, geoid2country = _find_odpairs_and_geo_FIXED(loaded_runs)

    print("\n" + "=" * 80)
    print("DONE")
    print("=" * 80)
