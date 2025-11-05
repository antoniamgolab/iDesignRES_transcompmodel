"""
Debug script to understand why BEV flows are not being found
"""
import pandas as pd
import numpy as np


def debug_bev_flows(loaded_runs, target_year=2030):
    """Debug why BEV flows are not being extracted"""

    # Select first case
    case_name = list(loaded_runs.keys())[0]
    print(f"Analyzing case: {case_name}")

    case_data = loaded_runs[case_name]
    input_data = case_data.get("input_data", {})
    output_data = case_data.get("output_data", {})

    print("\n" + "="*80)
    print("STEP 1: Check flow data availability")
    print("="*80)

    f_data = output_data.get("f", {})
    print(f"Flow data found: {len(f_data)} entries")

    if not f_data:
        print("ERROR: No flow data in output_data!")
        return

    # Show sample flow keys
    print("\nSample flow keys (first 5):")
    for i, key in enumerate(list(f_data.keys())[:5]):
        print(f"  {i+1}. {key}")
        print(f"      Value: {f_data[key]}")

    print("\n" + "="*80)
    print("STEP 2: Check TechVehicle data")
    print("="*80)

    # Find tech vehicle data
    techvehicle_data = None
    for key in ("TechVehicle", "techvehicle", "tech_vehicle", "TechVehicles"):
        if key in input_data:
            techvehicle_data = input_data[key]
            print(f"TechVehicle data found under key: '{key}'")
            break

    if not techvehicle_data:
        print("ERROR: No TechVehicle data found!")
        return

    print(f"TechVehicle data type: {type(techvehicle_data)}")

    if isinstance(techvehicle_data, list):
        print(f"Number of tech vehicles: {len(techvehicle_data)}")
        print("\nTech vehicle details:")
        electric_ids = set()

        for i, tv in enumerate(techvehicle_data):
            if not isinstance(tv, dict):
                continue

            tv_id = tv.get('id')
            tv_name = tv.get('name', 'unknown')

            # Extract fuel info
            tech = tv.get('technology', {})
            fuel_name = "unknown"

            if isinstance(tech, dict):
                fuel = tech.get('fuel', {})
                if isinstance(fuel, dict):
                    fuel_name = fuel.get('name', 'unknown')

            print(f"  TV {tv_id}: {tv_name} (fuel: {fuel_name})")

            # Check if electric
            if 'electricity' in fuel_name.lower() or 'electric' in fuel_name.lower():
                electric_ids.add(tv_id)
                print(f"    ✓ ELECTRIC!")

        print(f"\nFound {len(electric_ids)} BEV tech vehicle IDs: {electric_ids}")

    print("\n" + "="*80)
    print("STEP 3: Filter flows for target year and BEVs")
    print("="*80)

    print(f"Target year: {target_year}")
    print(f"BEV tech vehicle IDs: {electric_ids}")

    # Analyze flow keys
    year_counts = {}
    tv_counts = {}
    year_tv_flows = []

    for flow_key, flow_value in f_data.items():
        if not isinstance(flow_key, tuple):
            continue

        # Try to extract year and tv_id
        year = None
        tv_id = None

        # Common format: (year, (p, odpair_id, path_id), (mode_id, tv_id), gen)
        if len(flow_key) >= 1:
            year = flow_key[0]
            year_counts[year] = year_counts.get(year, 0) + 1

        if len(flow_key) >= 3 and isinstance(flow_key[2], tuple) and len(flow_key[2]) >= 2:
            tv_id = flow_key[2][1]
            tv_counts[tv_id] = tv_counts.get(tv_id, 0) + 1

        # Check if this matches our criteria
        if year == target_year and tv_id in electric_ids:
            year_tv_flows.append((flow_key, flow_value))

    print(f"\nYears found in flow data: {sorted(year_counts.keys())}")
    print(f"  Distribution: {year_counts}")

    print(f"\nTech vehicle IDs found in flow data: {sorted(tv_counts.keys())}")
    print(f"  Distribution: {tv_counts}")

    print(f"\nFlows matching year={target_year} AND tv_id in {electric_ids}:")
    print(f"  Count: {len(year_tv_flows)}")

    if year_tv_flows:
        print(f"\n  Sample matches (first 5):")
        for i, (key, val) in enumerate(year_tv_flows[:5]):
            print(f"    {i+1}. {key} = {val}")
    else:
        print("  ⚠️  NO MATCHES FOUND!")
        print("\n  Debugging:")
        print(f"    - Are there flows for year {target_year}? {target_year in year_counts}")
        print(f"    - Are there flows for BEV IDs {electric_ids}? {any(tv_id in electric_ids for tv_id in tv_counts.keys())}")

        # Check if there are ANY electric flows
        any_electric_flows = []
        for flow_key, flow_value in f_data.items():
            if len(flow_key) >= 3 and isinstance(flow_key[2], tuple) and len(flow_key[2]) >= 2:
                tv_id = flow_key[2][1]
                if tv_id in electric_ids:
                    any_electric_flows.append(flow_key)
                    if len(any_electric_flows) >= 3:
                        break

        if any_electric_flows:
            print(f"\n    Found BEV flows in OTHER years:")
            for key in any_electric_flows:
                print(f"      {key}")

    print("\n" + "="*80)
    print("STEP 4: Check odpair and geo mappings")
    print("="*80)

    # Quick check of mappings
    geo_data = None
    for key in ("GeographicElement", "GeographicElements", "geographicelements"):
        if key in input_data:
            geo_data = input_data[key]
            break

    if geo_data and isinstance(geo_data, list):
        print(f"Geographic elements: {len(geo_data)}")
        print(f"  Sample: geo_id={geo_data[0].get('id')} -> country={geo_data[0].get('country')}")

    odpair_data = None
    for key in ("Odpair", "odpairs", "od_pairs"):
        if key in input_data:
            odpair_data = input_data[key]
            break

    if odpair_data and isinstance(odpair_data, list):
        print(f"OD-pairs: {len(odpair_data)}")
        print(f"  Sample: odpair_id={odpair_data[0].get('id')}, {odpair_data[0].get('from')}->{odpair_data[0].get('to')}")

    print("\n" + "="*80)
    print("DIAGNOSIS COMPLETE")
    print("="*80)


# Example usage - add this cell to your notebook:
# debug_bev_flows(loaded_runs, target_year=2030)
