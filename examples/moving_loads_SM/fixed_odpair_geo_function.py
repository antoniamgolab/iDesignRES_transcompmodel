def _find_odpairs_and_geo(loaded_runs):
    """
    Extract odpair and geographic element mappings from loaded runs.

    Returns:
        odpair_map: dict mapping odpair_id -> (origin_geoid, dest_geoid)
        geoid2country: dict mapping geoid -> country code
    """
    odpair_map = {}        # odpair_id -> (origin_geoid, dest_geoid)
    geoid2country = {}     # geoid -> country code/name

    # Search through cases for odpair definitions and geographic elements
    for case_name, case in loaded_runs.items():
        inp = case.get("input_data", {}) or {}

        # ========== GEOGRAPHIC ELEMENTS ==========
        # Try different possible key names (case-sensitive)
        geo_data = None
        for key in ("GeographicElement", "GeographicElements", "geographicelements",
                    "geographic_elements", "geoelements", "geo_elements", "geographicelement"):
            if key in inp:
                geo_data = inp[key]
                break

        if geo_data and isinstance(geo_data, list):
            # Process list of geographic element dicts
            for entry in geo_data:
                if not isinstance(entry, dict):
                    continue

                geo_id = entry.get('id')
                country = entry.get('country')

                if geo_id is not None and country is not None:
                    try:
                        geoid2country[int(geo_id)] = str(country)
                    except (ValueError, TypeError):
                        pass  # Skip entries with invalid id or country

        # ========== ODPAIRS ==========
        # Try different possible key names
        odpair_data = None
        for key in ("Odpair", "odpairs", "od_pairs", "odPairs", "od_pair_list",
                    "ODpairs", "odpair", "od_pair"):
            if key in inp:
                odpair_data = inp[key]
                break

        if odpair_data and isinstance(odpair_data, list):
            # Process list of odpair dicts
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
                        pass  # Skip entries with invalid values

    return odpair_map, geoid2country


# Example usage in results_representation.ipynb:
# odpair_map, geoid2country = _find_odpairs_and_geo(loaded_runs)
#
# Now you can use these to create country-to-country flow matrices:
#
# For each odpair with BEV flow:
#   odpair_id -> (origin_geoid, dest_geoid) from odpair_map
#   origin_geoid -> origin_country from geoid2country
#   dest_geoid -> dest_country from geoid2country
#   Then aggregate flows by (origin_country, dest_country)
