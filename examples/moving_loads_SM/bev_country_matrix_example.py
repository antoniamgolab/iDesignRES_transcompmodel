"""
Example: Create BEV adoption matrix by country for a specific year

This shows how to:
1. Extract odpair-to-geo mappings and geo-to-country mappings
2. Filter for BEV flows in a specific year
3. Aggregate flows by origin_country -> destination_country
4. Create a country-to-country matrix
"""
import pandas as pd
import numpy as np


def _find_odpairs_and_geo(loaded_runs):
    """Extract odpair and geographic element mappings from loaded runs"""
    odpair_map = {}        # odpair_id -> (origin_geoid, dest_geoid)
    geoid2country = {}     # geoid -> country code/name

    for case_name, case in loaded_runs.items():
        inp = case.get("input_data", {}) or {}

        # Geographic elements
        geo_data = None
        for key in ("GeographicElement", "GeographicElements", "geographicelements",
                    "geographic_elements", "geoelements", "geo_elements"):
            if key in inp:
                geo_data = inp[key]
                break

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
        odpair_data = None
        for key in ("Odpair", "odpairs", "od_pairs", "odPairs", "ODpairs"):
            if key in inp:
                odpair_data = inp[key]
                break

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


def _find_electric_tech_ids(loaded_runs):
    """Find tech vehicle IDs that are BEVs (electricity fuel)"""
    electric_ids = set()

    for case in loaded_runs.values():
        inp = case.get("input_data", {}) or {}

        # Try to find tech vehicle data
        techvehicle_data = None
        for key in ("TechVehicle", "techvehicle", "tech_vehicle", "TechVehicles"):
            if key in inp:
                techvehicle_data = inp[key]
                break

        if not techvehicle_data:
            continue

        if isinstance(techvehicle_data, list):
            for tv in techvehicle_data:
                if not isinstance(tv, dict):
                    continue

                tv_id = tv.get('id')
                if tv_id is None:
                    continue

                # Check if it's electric (multiple nested structures possible)
                tech = tv.get('technology', {})
                if isinstance(tech, dict):
                    fuel = tech.get('fuel', {})
                    if isinstance(fuel, dict):
                        fuel_name = fuel.get('name', '').lower()
                        if 'electricity' in fuel_name or 'electric' in fuel_name:
                            electric_ids.add(int(tv_id))

    return electric_ids


def create_bev_country_matrix(loaded_runs, target_year=2030, case_name=None):
    """
    Create a country-to-country BEV adoption matrix for a specific year

    Args:
        loaded_runs: Dictionary of loaded run data
        target_year: Year to analyze (default: 2030)
        case_name: Specific case to analyze (default: first case)

    Returns:
        DataFrame with countries as both index and columns, values are BEV flows
    """
    # Get mappings
    odpair_map, geoid2country = _find_odpairs_and_geo(loaded_runs)
    electric_ids = _find_electric_tech_ids(loaded_runs)

    print(f"Found {len(odpair_map)} odpairs")
    print(f"Found {len(geoid2country)} geographic elements")
    print(f"Found {len(electric_ids)} BEV tech vehicle IDs: {electric_ids}")

    # Select case
    if case_name is None:
        case_name = list(loaded_runs.keys())[0]
        print(f"Using case: {case_name}")

    case_data = loaded_runs[case_name]
    output_data = case_data.get("output_data", {})

    # Get flow data
    f_data = output_data.get("f", {})
    if not f_data:
        print("WARNING: No flow data (f) found in output_data!")
        return pd.DataFrame()

    print(f"Found {len(f_data)} flow entries")

    # Aggregate flows by origin_country -> dest_country
    country_flows = {}  # (origin_country, dest_country) -> total_flow

    for flow_key, flow_value in f_data.items():
        # Flow key format: (year, (p, odpair_id, path_id), (mode_id, tv_id), gen)
        # or similar variations
        if not isinstance(flow_key, tuple) or len(flow_key) < 3:
            continue

        year = flow_key[0]
        if year != target_year:
            continue

        # Extract odpair_id and tv_id
        # Common format: (year, (p, odpair_id, path_id), (mode_id, tv_id), gen)
        odpair_id = None
        tv_id = None

        if len(flow_key) >= 2 and isinstance(flow_key[1], tuple) and len(flow_key[1]) >= 2:
            odpair_id = flow_key[1][1]  # (p, odpair_id, path_id)[1]

        if len(flow_key) >= 3 and isinstance(flow_key[2], tuple) and len(flow_key[2]) >= 2:
            tv_id = flow_key[2][1]  # (mode_id, tv_id)[1]

        # Filter for BEVs
        if tv_id not in electric_ids:
            continue

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

    print(f"Found {len(country_flows)} country-to-country BEV flows")

    # Create matrix
    if not country_flows:
        print("WARNING: No BEV flows found for this year!")
        return pd.DataFrame()

    # Get all countries
    all_countries = set()
    for (orig, dest) in country_flows.keys():
        all_countries.add(orig)
        all_countries.add(dest)

    all_countries = sorted(all_countries)
    print(f"Countries involved: {all_countries}")

    # Create matrix
    matrix = pd.DataFrame(
        np.zeros((len(all_countries), len(all_countries))),
        index=all_countries,
        columns=all_countries
    )

    for (orig, dest), flow in country_flows.items():
        matrix.loc[orig, dest] = flow

    return matrix


# ============================================================================
# USAGE IN JUPYTER NOTEBOOK
# ============================================================================
#
# After loading your runs:
# ```python
# odpair_map, geoid2country = _find_odpairs_and_geo(loaded_runs)
#
# # Create BEV matrix for 2030
# bev_matrix_2030 = create_bev_country_matrix(loaded_runs, target_year=2030)
#
# # Display
# print("BEV Flow Matrix 2030 (Origin countries as rows, Destination as columns):")
# print(bev_matrix_2030)
#
# # Visualize as heatmap
# import matplotlib.pyplot as plt
# import seaborn as sns
#
# plt.figure(figsize=(12, 10))
# sns.heatmap(bev_matrix_2030, annot=True, fmt='.0f', cmap='YlOrRd',
#             cbar_kws={'label': 'BEV Flow'})
# plt.title('BEV Adoption by Origin-Destination Country (2030)')
# plt.xlabel('Destination Country')
# plt.ylabel('Origin Country')
# plt.tight_layout()
# plt.show()
#
# # Compare multiple years
# for year in [2030, 2040, 2050]:
#     matrix = create_bev_country_matrix(loaded_runs, target_year=year)
#     print(f"\n{year}:")
#     print(matrix)
# ```
