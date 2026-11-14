"""
Investigate WHICH specific AT-DE routes exist in original vs processed data
"""
import pandas as pd
import yaml
from pathlib import Path

def check_which_regions_survived():
    """
    Check which NUTS2 regions from AT-DE routes are actually in the processed data
    """
    print("="*80)
    print("INVESTIGATING WHICH SPECIFIC ROUTES SURVIVED")
    print("="*80)

    # Load NUTS3 mapping
    nuts3 = pd.read_csv("data/Trucktraffic_NUTS3/02_NUTS-3-Regions.csv")
    id_to_country = dict(zip(nuts3['ETISPlus_Zone_ID'], nuts3['Country']))

    # Load truck traffic
    traffic = pd.read_csv("data/Trucktraffic_NUTS3/01_Trucktrafficflow.csv")
    traffic['origin_country'] = traffic['ID_origin_region'].map(id_to_country)
    traffic['dest_country'] = traffic['ID_destination_region'].map(id_to_country)

    # Get AT->DE routes
    at_de_routes = traffic[
        (traffic['origin_country'] == 'AT') &
        (traffic['dest_country'] == 'DE')
    ]

    print(f"\nOriginal AT->DE routes: {len(at_de_routes):,}")

    # Map NUTS3 to NUTS2 (first 4 characters)
    nuts3['NUTS2'] = nuts3['ETISPlus_Zone_ID'].astype(str).str[:3]

    # Get unique NUTS2 regions in AT->DE routes
    at_regions_in_routes = set()
    de_regions_in_routes = set()

    for _, route in at_de_routes.iterrows():
        orig_id = route['ID_origin_region']
        dest_id = route['ID_destination_region']

        # Look up NUTS3 entries
        orig_nuts3 = nuts3[nuts3['ETISPlus_Zone_ID'] == orig_id]
        dest_nuts3 = nuts3[nuts3['ETISPlus_Zone_ID'] == dest_id]

        if not orig_nuts3.empty:
            nuts2 = orig_nuts3['NUTS2'].values[0]
            at_regions_in_routes.add(nuts2)

        if not dest_nuts3.empty:
            nuts2 = dest_nuts3['NUTS2'].values[0]
            de_regions_in_routes.add(nuts2)

    print(f"\nUnique Austrian NUTS2 regions in AT->DE routes: {len(at_regions_in_routes)}")
    print(f"  {sorted(at_regions_in_routes)}")

    print(f"\nUnique German NUTS2 regions in AT->DE routes: {len(de_regions_in_routes)}")
    print(f"  {sorted(de_regions_in_routes)[:20]}")  # Show first 20

    # Load processed GeographicElement
    case_name = "case_20251107_105426_rail"
    input_dir = Path("input_data") / case_name

    geo_file = input_dir / "GeographicElement.yaml"
    with open(geo_file, 'r', encoding='utf-8') as f:
        geo_elements = yaml.safe_load(f)

    # Get NUTS2 regions in processed data
    processed_nuts2 = {}
    for geo in geo_elements:
        if geo['type'] == 'node':
            nuts2 = geo.get('nuts2_region', '')
            country = geo.get('country', '')
            if nuts2:
                processed_nuts2[nuts2] = country

    print(f"\n" + "-"*80)
    print("NUTS2 REGIONS IN PROCESSED DATA:")
    print("-"*80)
    print(f"\nTotal NUTS2 regions: {len(processed_nuts2)}")

    at_processed = [n for n, c in processed_nuts2.items() if c == 'AT']
    de_processed = [n for n, c in processed_nuts2.items() if c == 'DE']

    print(f"\nAustrian NUTS2 in processed data: {len(at_processed)}")
    print(f"  {sorted(at_processed)}")

    print(f"\nGerman NUTS2 in processed data: {len(de_processed)}")
    print(f"  {sorted(de_processed)}")

    # Check overlap
    print("\n" + "-"*80)
    print("OVERLAP ANALYSIS:")
    print("-"*80)

    at_missing = at_regions_in_routes - set(at_processed)
    de_missing = de_regions_in_routes - set(de_processed)

    print(f"\nAustrian NUTS2 in AT->DE routes but NOT in processed data:")
    print(f"  {sorted(at_missing) if at_missing else 'None - all present!'}")

    print(f"\nGerman NUTS2 in AT->DE routes but NOT in processed data:")
    print(f"  {sorted(de_missing)[:20] if de_missing else 'None - all present!'}")

    # Check if there are ANY Austrian or German NUTS2 combinations in processed odpairs
    print("\n" + "="*80)
    print("CHECKING PROCESSED ODPAIRS FOR AT/DE COMBINATIONS:")
    print("="*80)

    odpair_file = input_dir / "Odpair.yaml"
    with open(odpair_file, 'r', encoding='utf-8') as f:
        odpairs = yaml.safe_load(f)

    # Map geo_id to NUTS2
    geo_to_nuts2 = {}
    for geo in geo_elements:
        if geo['type'] == 'node':
            geo_id = geo['id']
            nuts2 = geo.get('nuts2_region', '')
            country = geo.get('country', '')
            if nuts2:
                geo_to_nuts2[geo_id] = (nuts2, country)

    # Check AT/DE combinations
    at_de_combinations = set()
    de_at_combinations = set()

    for odpair in odpairs:
        origin_geo = odpair.get('from')
        dest_geo = odpair.get('to')

        origin_info = geo_to_nuts2.get(origin_geo)
        dest_info = geo_to_nuts2.get(dest_geo)

        if origin_info and dest_info:
            orig_nuts2, orig_country = origin_info
            dest_nuts2, dest_country = dest_info

            if orig_country == 'AT' and dest_country == 'DE':
                at_de_combinations.add((orig_nuts2, dest_nuts2))
            elif orig_country == 'DE' and dest_country == 'AT':
                de_at_combinations.add((orig_nuts2, dest_nuts2))

    print(f"\nAT->DE NUTS2 combinations in processed data: {len(at_de_combinations)}")
    if at_de_combinations:
        print("  Examples:")
        for orig, dest in list(at_de_combinations)[:10]:
            print(f"    {orig} -> {dest}")
    else:
        print("  NONE! No AT->DE combinations at all!")

    print(f"\nDE->AT NUTS2 combinations in processed data: {len(de_at_combinations)}")
    if de_at_combinations:
        print("  Examples:")
        for orig, dest in list(de_at_combinations)[:10]:
            print(f"    {orig} -> {dest}")
    else:
        print("  NONE! No DE->AT combinations at all!")

    # Check if there's a geographic constraint
    print("\n" + "="*80)
    print("HYPOTHESIS: Are processed routes constrained to specific regions?")
    print("="*80)

    # Get all OD pairs by country
    all_country_pairs = {}
    for odpair in odpairs:
        origin_geo = odpair.get('from')
        dest_geo = odpair.get('to')

        origin_info = geo_to_nuts2.get(origin_geo)
        dest_info = geo_to_nuts2.get(dest_geo)

        if origin_info and dest_info:
            orig_country = origin_info[1]
            dest_country = dest_info[1]

            pair = (orig_country, dest_country)
            if pair not in all_country_pairs:
                all_country_pairs[pair] = 0
            all_country_pairs[pair] += 1

    print("\nAll country pairs in processed data:")
    for (orig, dest), count in sorted(all_country_pairs.items(), key=lambda x: x[1], reverse=True):
        print(f"  {orig} -> {dest}: {count:>4} OD pairs")

    # Check if all routes must involve Italy or specific countries
    italy_involvement = sum(1 for (o, d) in all_country_pairs.keys() if o == 'IT' or d == 'IT')
    total_pairs = len(all_country_pairs)

    print(f"\nCountry pairs involving Italy: {italy_involvement}/{total_pairs} ({italy_involvement/total_pairs*100:.1f}%)")

    if italy_involvement / total_pairs > 0.8:
        print("\n[HYPOTHESIS] Preprocessing may be filtering for routes involving Italy!")
        print("This would explain why AT->DE (doesn't involve Italy) is excluded")
        print("while IT->DE, IT->AT (involves Italy) are included")

    print("\n" + "="*80)


if __name__ == "__main__":
    check_which_regions_survived()
