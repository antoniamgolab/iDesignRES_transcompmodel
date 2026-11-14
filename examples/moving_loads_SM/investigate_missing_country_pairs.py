"""
Investigate missing country pair flows: AT-DE, AT-DK, DE-DK, etc.
Where did they get lost in the preprocessing pipeline?
"""
import pandas as pd
import yaml
from pathlib import Path
from collections import Counter

def check_original_data():
    """
    Check if AT-DE, AT-DK, DE-DK routes exist in original truck traffic data
    """
    print("="*80)
    print("STEP 1: CHECKING ORIGINAL TRUCK TRAFFIC DATA")
    print("="*80)

    # Load NUTS3 regions mapping
    nuts3 = pd.read_csv("data/Trucktraffic_NUTS3/02_NUTS-3-Regions.csv")
    id_to_country = dict(zip(nuts3['ETISPlus_Zone_ID'], nuts3['Country']))

    # Load truck traffic
    traffic = pd.read_csv("data/Trucktraffic_NUTS3/01_Trucktrafficflow.csv")
    traffic['origin_country'] = traffic['ID_origin_region'].map(id_to_country)
    traffic['dest_country'] = traffic['ID_destination_region'].map(id_to_country)

    # Corridor countries
    corridor_countries = ['AT', 'DE', 'DK', 'SE', 'NO', 'FI']

    print("\nChecking specific country pairs:")
    print("-"*80)

    pairs_to_check = [
        ('AT', 'DE'), ('DE', 'AT'),
        ('AT', 'DK'), ('DK', 'AT'),
        ('DE', 'DK'), ('DK', 'DE'),
        ('DE', 'SE'), ('SE', 'DE'),
        ('AT', 'SE'), ('SE', 'AT'),
    ]

    original_pair_counts = {}

    for orig, dest in pairs_to_check:
        routes = traffic[
            (traffic['origin_country'] == orig) &
            (traffic['dest_country'] == dest)
        ]
        total_traffic = routes['Traffic_flow_trucks_2030'].sum()

        original_pair_counts[(orig, dest)] = len(routes)

        print(f"\n{orig} -> {dest}:")
        print(f"  Routes: {len(routes):,}")
        print(f"  Traffic: {total_traffic:,.0f} trucks/year")

        if len(routes) > 0:
            # Show top 3 routes
            top_routes = routes.nlargest(3, 'Traffic_flow_trucks_2030')
            print(f"  Top routes:")
            for _, route in top_routes.iterrows():
                orig_id = route['ID_origin_region']
                dest_id = route['ID_destination_region']
                traffic_vol = route['Traffic_flow_trucks_2030']

                orig_name = nuts3[nuts3['ETISPlus_Zone_ID'] == orig_id]['Name'].values[0]
                dest_name = nuts3[nuts3['ETISPlus_Zone_ID'] == dest_id]['Name'].values[0]

                print(f"    {orig_name} -> {dest_name}: {traffic_vol:,.0f} trucks/year")

    print("\n" + "="*80)
    return original_pair_counts


def check_processed_odpairs(case_name="case_20251107_105426_rail"):
    """
    Check if country pairs exist in processed Odpair.yaml
    """
    print("\n" + "="*80)
    print("STEP 2: CHECKING PROCESSED ODPAIR.YAML")
    print("="*80)

    input_dir = Path("input_data") / case_name

    # Load GeographicElement to get country mappings
    geo_file = input_dir / "GeographicElement.yaml"
    with open(geo_file, 'r', encoding='utf-8') as f:
        geo_elements = yaml.safe_load(f)

    # Create geo_id -> country mapping
    geo_to_country = {}
    for geo in geo_elements:
        if geo['type'] == 'node':
            geo_id = geo['id']
            country = geo.get('country')
            if country:
                geo_to_country[geo_id] = country

    print(f"\nLoaded {len(geo_elements)} geographic elements")
    print(f"Country mapping: {len(geo_to_country)} nodes")

    # Show countries in processed data
    countries_in_geo = set(geo_to_country.values())
    print(f"Countries in GeographicElement: {sorted(countries_in_geo)}")

    # Load Odpair
    odpair_file = input_dir / "Odpair.yaml"
    with open(odpair_file, 'r', encoding='utf-8') as f:
        odpairs = yaml.safe_load(f)

    print(f"\nTotal OD pairs: {len(odpairs)}")

    # Analyze country pairs in odpairs
    country_pairs = Counter()

    for odpair in odpairs:
        origin_geo = odpair.get('from')
        dest_geo = odpair.get('to')

        origin_country = geo_to_country.get(origin_geo, 'UNKNOWN')
        dest_country = geo_to_country.get(dest_geo, 'UNKNOWN')

        country_pairs[(origin_country, dest_country)] += 1

    print("\n" + "-"*80)
    print("COUNTRY PAIRS IN PROCESSED ODPAIR.YAML:")
    print("-"*80)

    # Check specific pairs
    pairs_to_check = [
        ('AT', 'DE'), ('DE', 'AT'),
        ('AT', 'DK'), ('DK', 'AT'),
        ('DE', 'DK'), ('DK', 'DE'),
        ('DE', 'SE'), ('SE', 'DE'),
        ('AT', 'SE'), ('SE', 'AT'),
        ('IT', 'DE'), ('DE', 'IT'),
        ('IT', 'AT'), ('AT', 'IT'),
    ]

    processed_pair_counts = {}

    for orig, dest in pairs_to_check:
        count = country_pairs.get((orig, dest), 0)
        processed_pair_counts[(orig, dest)] = count

        status = "[PRESENT]" if count > 0 else "[MISSING]"
        print(f"{orig} -> {dest}: {count:>4} OD pairs  {status}")

    # Show top 20 country pairs that DO exist
    print("\n" + "-"*80)
    print("TOP 20 COUNTRY PAIRS IN PROCESSED DATA:")
    print("-"*80)
    for (orig, dest), count in country_pairs.most_common(20):
        print(f"  {orig} -> {dest}: {count:>4} OD pairs")

    print("\n" + "="*80)
    return processed_pair_counts


def compare_original_vs_processed(original_counts, processed_counts):
    """
    Compare original vs processed to see what was lost
    """
    print("\n" + "="*80)
    print("STEP 3: COMPARISON - ORIGINAL vs PROCESSED")
    print("="*80)

    print(f"\n{'Origin':<8} {'Dest':<8} {'Original':<12} {'Processed':<12} {'Lost':<12} {'Status'}")
    print("-"*70)

    all_pairs = set(original_counts.keys()) | set(processed_counts.keys())

    for pair in sorted(all_pairs):
        orig, dest = pair
        original = original_counts.get(pair, 0)
        processed = processed_counts.get(pair, 0)
        lost = original - processed

        if original > 0:
            status = "[OK]" if processed > 0 else "[LOST ALL]"
        else:
            status = "N/A"

        print(f"{orig:<8} {dest:<8} {original:>10,}   {processed:>10,}   {lost:>10,}   {status}")

    print("\n" + "="*80)
    print("KEY FINDINGS:")
    print("="*80)

    lost_pairs = [(p, original_counts[p]) for p in original_counts if processed_counts.get(p, 0) == 0 and original_counts[p] > 0]

    if lost_pairs:
        print(f"\n[!] {len(lost_pairs)} country pairs COMPLETELY LOST in preprocessing:")
        for pair, count in sorted(lost_pairs, key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {pair[0]} -> {pair[1]}: {count:,} routes lost")
    else:
        print("\n[OK] No country pairs completely lost")

    print("\n" + "="*80)


def investigate_preprocessing_filters(case_name="case_20251107_105426_rail"):
    """
    Investigate which preprocessing filters might be removing these routes
    """
    print("\n" + "="*80)
    print("STEP 4: INVESTIGATING PREPROCESSING FILTERS")
    print("="*80)

    print("\nPossible reasons for missing country pairs:")
    print("-"*80)

    print("\n1. CROSS_BORDER_ONLY filter:")
    print("   - Removes domestic routes (e.g., AT->AT)")
    print("   - Should NOT remove AT->DE, AT->DK, DE->DK")
    print("   - Status: NOT the cause for corridor country pairs")

    print("\n2. MIN_DISTANCE filter:")
    print("   - May filter out short-distance routes")
    print("   - Could remove AT->DE if distance < threshold")
    print("   - Need to check: preprocessing script parameters")

    print("\n3. MIN_TRAFFIC_THRESHOLD filter:")
    print("   - Default: 100 trucks/year")
    print("   - Could remove low-volume routes")
    print("   - But original data shows high volumes for AT->DE, DE->DK")

    print("\n4. MAX_ODPAIRS limit:")
    print("   - Selects top N OD pairs by traffic volume")
    print("   - Could filter out some pairs if limit is too low")
    print("   - Need to check: how many OD pairs were requested")

    print("\n5. NUTS2 AGGREGATION:")
    print("   - Groups NUTS3 regions into NUTS2")
    print("   - Should preserve country-level flows")
    print("   - Status: Should NOT remove country pairs")

    print("\n6. PATH FINDING FAILURE:")
    print("   - Some OD pairs may not have valid paths in the network")
    print("   - If no path exists in processed network, OD pair is dropped")
    print("   - Status: LIKELY CULPRIT for missing pairs")

    print("\n" + "="*80)
    print("RECOMMENDATION:")
    print("="*80)
    print("\nCheck preprocessing log for:")
    print("  - 'No valid path found' messages")
    print("  - MAX_ODPAIRS parameter value")
    print("  - MIN_DISTANCE parameter value")
    print("  - Number of OD pairs before/after each filter")

    print("\n" + "="*80)


if __name__ == "__main__":
    # Run all checks
    print("\n" + "="*80)
    print("INVESTIGATING MISSING COUNTRY PAIR FLOWS")
    print("="*80)
    print("\nChecking: AT-DE, AT-DK, DE-DK, and other corridor pairs")
    print("="*80)

    # Step 1: Check original data
    original_counts = check_original_data()

    # Step 2: Check processed data
    processed_counts = check_processed_odpairs()

    # Step 3: Compare
    compare_original_vs_processed(original_counts, processed_counts)

    # Step 4: Investigate why
    investigate_preprocessing_filters()

    print("\n" + "="*80)
    print("INVESTIGATION COMPLETE")
    print("="*80)
