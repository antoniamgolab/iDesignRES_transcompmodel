"""
FIXED: Create BEV country-to-country flow matrix

This version correctly handles the data structure where:
- TechVehicle has 'technology' as an ID reference
- Technology table maps ID -> fuel type
"""
import pandas as pd
import numpy as np


def _find_odpairs_and_geo(loaded_runs):
    """Extract odpair and geographic element mappings"""
    odpair_map = {}
    geoid2country = {}

    for case_name, case in loaded_runs.items():
        inp = case.get("input_data", {}) or {}

        # Geographic elements
        geo_data = inp.get("GeographicElement") or inp.get("GeographicElements")
        if geo_data and isinstance(geo_data, list):
            for entry in geo_data:
                if not isinstance(entry, dict):
                    continue
                geo_id = entry.get('id')
                country = entry.get('country')
                if geo_id is not None and country is not None:
                    try:
                        geoid2country[int(geo_id)] = str(country)
                    except (ValueError, TypeError):
                        pass

        # Odpairs
        odpair_data = inp.get("Odpair") or inp.get("odpairs")
        if odpair_data and isinstance(odpair_data, list):
            for entry in odpair_data:
                if not isinstance(entry, dict):
                    continue
                odpair_id = entry.get('id')
                origin = entry.get('from')
                dest = entry.get('to')
                if odpair_id is not None and origin is not None and dest is not None:
                    try:
                        odpair_map[int(odpair_id)] = (int(origin), int(dest))
                    except (ValueError, TypeError):
                        pass

    return odpair_map, geoid2country


def _find_electric_tech_ids_FIXED(loaded_runs):
    """
    Find tech vehicle IDs that are BEVs (electricity fuel)

    FIXED: Correctly handles cross-referencing TechVehicle -> Technology -> Fuel
    """
    electric_ids = set()

    for case in loaded_runs.values():
        inp = case.get("input_data", {}) or {}

        # Load Technology table (maps technology_id -> fuel)
        tech_data = inp.get("Technology") or inp.get("technology")
        if not tech_data:
            print("  WARNING: No Technology data found")
            continue

        # Create mapping: technology_id -> fuel_name
        tech_to_fuel = {}
        if isinstance(tech_data, list):
            for tech in tech_data:
                if isinstance(tech, dict):
                    tech_id = tech.get('id')
                    fuel = tech.get('fuel', '').lower()
                    if tech_id is not None:
                        tech_to_fuel[int(tech_id)] = fuel
                        print(f"    Tech {tech_id}: fuel={fuel}")

        # Load TechVehicle table
        tv_data = inp.get("TechVehicle") or inp.get("techvehicle")
        if not tv_data:
            print("  WARNING: No TechVehicle data found")
            continue

        if isinstance(tv_data, list):
            for tv in tv_data:
                if not isinstance(tv, dict):
                    continue

                tv_id = tv.get('id')
                tv_name = tv.get('name', 'unknown')
                tech_id = tv.get('technology')

                if tv_id is None or tech_id is None:
                    continue

                # Look up fuel from technology mapping
                fuel_name = tech_to_fuel.get(int(tech_id), 'unknown')

                print(f"    TV {tv_id} ({tv_name}): technology={tech_id} -> fuel={fuel_name}")

                # Check if electric
                if 'electricity' in fuel_name or 'electric' in fuel_name:
                    electric_ids.add(int(tv_id))
                    print(f"      ✓ ELECTRIC!")

    return electric_ids


def create_bev_country_matrix_FIXED(loaded_runs, target_year=2030, case_name=None):
    """
    Create a country-to-country BEV flow matrix for a specific year

    FIXED version with correct BEV identification
    """
    print("="*80)
    print("CREATING BEV COUNTRY MATRIX")
    print("="*80)

    # Get mappings
    print("\nStep 1: Loading geographic and odpair mappings...")
    odpair_map, geoid2country = _find_odpairs_and_geo(loaded_runs)
    print(f"  Found {len(odpair_map)} odpairs")
    print(f"  Found {len(geoid2country)} geographic elements")

    print("\nStep 2: Identifying BEV tech vehicles...")
    electric_ids = _find_electric_tech_ids_FIXED(loaded_runs)
    print(f"  Found {len(electric_ids)} BEV tech vehicle IDs: {electric_ids}")

    if not electric_ids:
        print("  ERROR: No BEV tech vehicles identified!")
        return pd.DataFrame()

    # Select case
    if case_name is None:
        case_name = list(loaded_runs.keys())[0]
    print(f"\nStep 3: Processing case '{case_name}'...")

    case_data = loaded_runs[case_name]
    output_data = case_data.get("output_data", {})

    # Get flow data
    f_data = output_data.get("f", {})
    if not f_data:
        print("  ERROR: No flow data (f) found!")
        return pd.DataFrame()

    print(f"  Found {len(f_data)} flow entries")

    # Aggregate flows by origin_country -> dest_country
    print(f"\nStep 4: Filtering for year={target_year} and BEV flows...")
    country_flows = {}  # (origin_country, dest_country) -> total_flow

    flows_found = 0
    for flow_key, flow_value in f_data.items():
        if not isinstance(flow_key, tuple) or len(flow_key) < 3:
            continue

        year = flow_key[0]
        if year != target_year:
            continue

        # Extract odpair_id and tv_id
        # Format: (year, (p, odpair_id, path_id), (mode_id, tv_id), gen)
        odpair_id = None
        tv_id = None

        if len(flow_key) >= 2 and isinstance(flow_key[1], tuple) and len(flow_key[1]) >= 2:
            odpair_id = flow_key[1][1]

        if len(flow_key) >= 3 and isinstance(flow_key[2], tuple) and len(flow_key[2]) >= 2:
            tv_id = flow_key[2][1]

        # Filter for BEVs
        if tv_id not in electric_ids:
            continue

        flows_found += 1

        # Get origin and destination from odpair
        if odpair_id not in odpair_map:
            continue

        origin_geoid, dest_geoid = odpair_map[odpair_id]

        # Get countries
        origin_country = geoid2country.get(origin_geoid)
        dest_country = geoid2country.get(dest_geoid)

        if origin_country is None or dest_country is None:
            continue

        # Aggregate
        key = (origin_country, dest_country)
        country_flows[key] = country_flows.get(key, 0.0) + flow_value

    print(f"  Found {flows_found} BEV flows for year {target_year}")
    print(f"  Aggregated into {len(country_flows)} country-to-country pairs")

    # Create matrix
    if not country_flows:
        print("  WARNING: No country-level flows after aggregation!")
        return pd.DataFrame()

    # Get all countries
    all_countries = set()
    for (orig, dest) in country_flows.keys():
        all_countries.add(orig)
        all_countries.add(dest)

    all_countries = sorted(all_countries)
    print(f"  Countries: {all_countries}")

    # Create matrix
    matrix = pd.DataFrame(
        np.zeros((len(all_countries), len(all_countries))),
        index=all_countries,
        columns=all_countries
    )

    for (orig, dest), flow in country_flows.items():
        matrix.loc[orig, dest] = flow

    print(f"\n✓ Matrix created successfully!")
    print(f"  Shape: {matrix.shape}")
    print(f"  Total flow: {matrix.sum().sum():.2f}")
    print("="*80)

    return matrix


# =============================================================================
# USAGE IN JUPYTER NOTEBOOK
# =============================================================================
#
# In your notebook, add these cells:
#
# ```python
# # Cell 1: Import the fixed function
# import sys
# sys.path.insert(0, '.')
# from bev_country_matrix_FIXED import create_bev_country_matrix_FIXED
#
# # Cell 2: Create BEV matrix for 2030
# bev_matrix_2030 = create_bev_country_matrix_FIXED(loaded_runs, target_year=2030)
# print(bev_matrix_2030)
#
# # Cell 3: Visualize as heatmap
# import matplotlib.pyplot as plt
# import seaborn as sns
#
# if not bev_matrix_2030.empty:
#     plt.figure(figsize=(12, 10))
#     sns.heatmap(bev_matrix_2030, annot=True, fmt='.1f', cmap='YlOrRd',
#                 cbar_kws={'label': 'BEV Flow (1000 tkm)'})
#     plt.title(f'BEV Freight Flows by Country (2030)')
#     plt.xlabel('Destination Country')
#     plt.ylabel('Origin Country')
#     plt.tight_layout()
#     plt.show()
# else:
#     print("No BEV flows to display")
#
# # Cell 4: Compare multiple years
# for year in [2030, 2040, 2050]:
#     print(f"\n{'='*80}")
#     print(f"BEV FLOWS {year}")
#     print('='*80)
#     matrix = create_bev_country_matrix_FIXED(loaded_runs, target_year=year)
#     if not matrix.empty:
#         print(matrix)
#         print(f"\nTotal: {matrix.sum().sum():.2f} (1000 tkm)")
# ```
