"""
Debug the h variable structure to understand why BEV vehicles aren't being found
"""
import pandas as pd

def debug_h_variable(loaded_runs, case_name=None):
    """
    Examine the structure of the h variable (vehicle counts)
    """
    # Select case
    if case_name is None:
        case_name = list(loaded_runs.keys())[0]

    print("="*80)
    print(f"DEBUGGING H VARIABLE FOR: {case_name}")
    print("="*80)

    case_data = loaded_runs[case_name]
    output_data = case_data.get("output_data", {})

    # Get h data
    h_data = output_data.get("h", {})

    if not h_data:
        print("\n[ERROR] No h data found!")
        return

    print(f"\nTotal h entries: {len(h_data)}")

    # Sample some keys
    print("\n" + "-"*80)
    print("SAMPLE H KEYS (first 10):")
    print("-"*80)

    for i, (key, value) in enumerate(list(h_data.items())[:10]):
        print(f"{i+1}. Key: {key}")
        print(f"   Value: {value}")
        print(f"   Key type: {type(key)}")
        if isinstance(key, tuple):
            print(f"   Key length: {len(key)}")
            for j, element in enumerate(key):
                print(f"     [{j}]: {element} (type: {type(element)})")
        print()

    # Extract years
    print("-"*80)
    print("YEARS IN H DATA:")
    print("-"*80)

    years = set()
    for key in h_data.keys():
        if isinstance(key, tuple) and len(key) >= 1:
            years.add(key[0])

    years = sorted(years)
    print(f"Unique years: {years}")
    print(f"Total unique years: {len(years)}")

    # Extract tech vehicle IDs
    print("\n" + "-"*80)
    print("TECH VEHICLE IDs IN H DATA:")
    print("-"*80)

    tv_ids = set()
    for key in h_data.keys():
        if isinstance(key, tuple) and len(key) >= 3:
            if isinstance(key[2], tuple) and len(key[2]) >= 2:
                tv_id = key[2][1]
                tv_ids.add(tv_id)

    tv_ids = sorted(tv_ids)
    print(f"Unique tech vehicle IDs: {tv_ids}")
    print(f"Total unique tech vehicle IDs: {len(tv_ids)}")

    # Count entries per year and tech vehicle
    print("\n" + "-"*80)
    print("ENTRIES PER YEAR AND TECH VEHICLE:")
    print("-"*80)

    year_tv_counts = {}
    for key, value in h_data.items():
        if not isinstance(key, tuple) or len(key) < 3:
            continue

        year = key[0]
        if isinstance(key[2], tuple) and len(key[2]) >= 2:
            tv_id = key[2][1]

            if year not in year_tv_counts:
                year_tv_counts[year] = {}

            if tv_id not in year_tv_counts[year]:
                year_tv_counts[year][tv_id] = 0

            year_tv_counts[year][tv_id] += 1

    # Show for first 3 years
    for i, year in enumerate(sorted(year_tv_counts.keys())[:3]):
        print(f"\nYear {year}:")
        for tv_id, count in sorted(year_tv_counts[year].items()):
            print(f"  Tech Vehicle {tv_id}: {count} entries (total vehicles: {sum(h_data[k] for k in h_data.keys() if isinstance(k, tuple) and len(k) >= 3 and k[0] == year and isinstance(k[2], tuple) and len(k[2]) >= 2 and k[2][1] == tv_id):.2f})")

    # Check if BEV (ID 1) exists in any year
    print("\n" + "-"*80)
    print("BEV (Tech Vehicle ID 1) ANALYSIS:")
    print("-"*80)

    bev_years = {}
    for key, value in h_data.items():
        if not isinstance(key, tuple) or len(key) < 3:
            continue

        year = key[0]
        if isinstance(key[2], tuple) and len(key[2]) >= 2:
            tv_id = key[2][1]

            if tv_id == 1:
                if year not in bev_years:
                    bev_years[year] = {'count': 0, 'total_vehicles': 0}

                bev_years[year]['count'] += 1
                bev_years[year]['total_vehicles'] += value

    if bev_years:
        print(f"\nBEV entries found in {len(bev_years)} years:")
        for year in sorted(bev_years.keys()):
            print(f"  Year {year}: {bev_years[year]['count']} entries, {bev_years[year]['total_vehicles']:.2f} total vehicles")
    else:
        print("\n[WARNING] NO BEV ENTRIES FOUND!")
        print("Tech Vehicle ID 1 does not appear in h data")
        print(f"Available tech vehicle IDs: {tv_ids}")

    print("\n" + "="*80)

    return {
        'years': years,
        'tv_ids': tv_ids,
        'bev_years': bev_years,
        'year_tv_counts': year_tv_counts
    }


# Usage in notebook:
"""
from debug_h_variable import debug_h_variable

# Debug h variable
debug_info = debug_h_variable(loaded_runs, case_name='case_20251107_153441_var_var')
"""
