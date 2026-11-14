"""
Analyze the OD pairs in the dataset: which countries, routes, etc.
"""

import yaml
from pathlib import Path
from collections import Counter, defaultdict

def analyze_odpairs(case_name):
    """
    Analyze OD pairs to understand what's in the dataset.
    """
    print("\n" + "="*80)
    print(f"ANALYZING OD PAIRS IN: {case_name}")
    print("="*80)

    # Load input data
    input_dir = Path("input_data") / case_name

    # Load GeographicElement
    geo_file = input_dir / "GeographicElement.yaml"
    with open(geo_file, 'r', encoding='utf-8') as f:
        geo_elements = yaml.safe_load(f)

    # Create geo_id -> NUTS2 mapping
    geo_to_nuts2 = {}
    geo_to_name = {}
    for geo in geo_elements:
        if geo['type'] == 'node':
            geo_id = geo['id']
            if 'nuts2_region' in geo and geo['nuts2_region']:
                geo_to_nuts2[geo_id] = geo['nuts2_region']
            if 'name' in geo:
                geo_to_name[geo_id] = geo['name']

    print(f"\nLoaded {len(geo_elements)} geographic elements")
    print(f"  Nodes with NUTS2: {len(geo_to_nuts2)}")

    # Load Odpairs
    odpair_file = input_dir / "Odpair.yaml"
    with open(odpair_file, 'r', encoding='utf-8') as f:
        odpairs = yaml.safe_load(f)

    print(f"  Total OD pairs: {len(odpairs)}")

    # Analyze OD pairs
    origin_countries = Counter()
    dest_countries = Counter()
    od_country_pairs = Counter()

    italy_origins = []
    italy_dests = []

    domestic_count = 0
    international_count = 0

    for odpair in odpairs:
        origin_geo = odpair.get('origin')
        dest_geo = odpair.get('destination')

        origin_nuts2 = geo_to_nuts2.get(origin_geo, 'UNKNOWN')
        dest_nuts2 = geo_to_nuts2.get(dest_geo, 'UNKNOWN')

        # Get country codes
        origin_country = origin_nuts2[:2].upper() if len(origin_nuts2) >= 2 else 'UNK'
        dest_country = dest_nuts2[:2].upper() if len(dest_nuts2) >= 2 else 'UNK'

        origin_countries[origin_country] += 1
        dest_countries[dest_country] += 1
        od_country_pairs[(origin_country, dest_country)] += 1

        # Check if Italy involved
        if origin_country == 'IT':
            italy_origins.append({
                'odpair_id': odpair['id'],
                'origin': origin_nuts2,
                'dest': dest_nuts2,
                'origin_name': geo_to_name.get(origin_geo, ''),
                'dest_name': geo_to_name.get(dest_geo, '')
            })

        if dest_country == 'IT':
            italy_dests.append({
                'odpair_id': odpair['id'],
                'origin': origin_nuts2,
                'dest': dest_nuts2,
                'origin_name': geo_to_name.get(origin_geo, ''),
                'dest_name': geo_to_name.get(dest_geo, '')
            })

        # Count domestic vs international
        if origin_country == dest_country:
            domestic_count += 1
        else:
            international_count += 1

    # Print summary
    print("\n" + "-"*80)
    print("OVERALL BREAKDOWN")
    print("-"*80)
    print(f"\nDomestic routes (same country):     {domestic_count:>6} ({domestic_count/len(odpairs)*100:>5.1f}%)")
    print(f"International routes (cross-border): {international_count:>6} ({international_count/len(odpairs)*100:>5.1f}%)")

    # Origin countries
    print("\n" + "-"*80)
    print("ORIGIN COUNTRIES")
    print("-"*80)
    print(f"\n{'Country':<10} {'# OD Pairs':<12} {'Percentage':<12}")
    print("-" * 40)
    for country, count in origin_countries.most_common(10):
        pct = count / len(odpairs) * 100
        print(f"{country:<10} {count:>10}   {pct:>10.1f}%")

    # Destination countries
    print("\n" + "-"*80)
    print("DESTINATION COUNTRIES")
    print("-"*80)
    print(f"\n{'Country':<10} {'# OD Pairs':<12} {'Percentage':<12}")
    print("-" * 40)
    for country, count in dest_countries.most_common(10):
        pct = count / len(odpairs) * 100
        print(f"{country:<10} {count:>10}   {pct:>10.1f}%")

    # Top OD country pairs
    print("\n" + "-"*80)
    print("TOP 20 ORIGIN-DESTINATION COUNTRY PAIRS")
    print("-"*80)
    print(f"\n{'Origin':<10} {'Destination':<12} {'# OD Pairs':<12} {'Percentage':<12}")
    print("-" * 50)
    for (orig, dest), count in od_country_pairs.most_common(20):
        pct = count / len(odpairs) * 100
        print(f"{orig:<10} {dest:<12} {count:>10}   {pct:>10.1f}%")

    # Italy analysis
    print("\n" + "="*80)
    print("ITALY ANALYSIS")
    print("="*80)

    print(f"\nOD pairs ORIGINATING from Italy (IT):  {len(italy_origins)}")
    print(f"OD pairs DESTINED for Italy (IT):      {len(italy_dests)}")

    if len(italy_origins) > 0:
        print("\nSample OD pairs FROM Italy:")
        for od in italy_origins[:10]:
            print(f"  {od['origin']} ({od['origin_name']}) -> {od['dest']} ({od['dest_name']})")

    if len(italy_dests) > 0:
        print("\nSample OD pairs TO Italy:")
        for od in italy_dests[:10]:
            print(f"  {od['origin']} ({od['origin_name']}) -> {od['dest']} ({od['dest_name']})")

    if len(italy_origins) == 0 and len(italy_dests) == 0:
        print("\n[WARNING] NO OD PAIRS INVOLVE ITALY AS ORIGIN OR DESTINATION!")
        print("    This dataset only includes Italy as a transit country.")
        print("    Freight 'in Italy' is passing through on routes between other countries.")

    print("\n" + "="*80)

    return {
        'total_odpairs': len(odpairs),
        'domestic': domestic_count,
        'international': international_count,
        'origin_countries': dict(origin_countries),
        'dest_countries': dict(dest_countries),
        'italy_origins': len(italy_origins),
        'italy_dests': len(italy_dests)
    }


def analyze_original_traffic_data():
    """
    Analyze the ORIGINAL truck traffic data before preprocessing.
    """
    import pandas as pd

    print("\n" + "="*80)
    print("ANALYZING ORIGINAL TRUCK TRAFFIC DATA")
    print("="*80)

    # Load original traffic data
    data_dir = Path("data/Trucktraffic_NUTS3")
    traffic_file = data_dir / "01_Trucktrafficflow.csv"

    if not traffic_file.exists():
        print(f"[ERROR] Original traffic file not found: {traffic_file}")
        return

    truck_traffic = pd.read_csv(traffic_file)
    print(f"\nLoaded {len(truck_traffic):,} routes from original data")

    # Show sample region IDs to understand the format
    print(f"\nSample region IDs from original data:")
    sample_origins = truck_traffic['ID_origin_region'].head(10).tolist()
    print(f"  Origins: {sample_origins}")
    sample_dests = truck_traffic['ID_destination_region'].head(10).tolist()
    print(f"  Destinations: {sample_dests}")

    # Extract country codes from NUTS-3 region IDs (first 2 characters)
    truck_traffic['origin_country'] = truck_traffic['ID_origin_region'].astype(str).str[:2]
    truck_traffic['dest_country'] = truck_traffic['ID_destination_region'].astype(str).str[:2]

    # Count by origin country
    origin_counts = truck_traffic['origin_country'].value_counts()
    print("\n" + "-"*80)
    print("ORIGIN COUNTRIES IN ORIGINAL DATA")
    print("-"*80)
    print(f"\n{'Country':<10} {'# Routes':<12} {'Total Traffic (trucks/yr)':<25}")
    print("-" * 50)
    for country in origin_counts.head(10).index:
        count = origin_counts[country]
        traffic = truck_traffic[truck_traffic['origin_country'] == country]['Traffic_flow_trucks_2030'].sum()
        print(f"{country:<10} {count:>10,}   {traffic:>23,.0f}")

    # Count by destination country
    dest_counts = truck_traffic['dest_country'].value_counts()
    print("\n" + "-"*80)
    print("DESTINATION COUNTRIES IN ORIGINAL DATA")
    print("-"*80)
    print(f"\n{'Country':<10} {'# Routes':<12} {'Total Traffic (trucks/yr)':<25}")
    print("-" * 50)
    for country in dest_counts.head(10).index:
        count = dest_counts[country]
        traffic = truck_traffic[truck_traffic['dest_country'] == country]['Traffic_flow_trucks_2030'].sum()
        print(f"{country:<10} {count:>10,}   {traffic:>23,.0f}")

    # Italy specific analysis
    print("\n" + "="*80)
    print("ITALY IN ORIGINAL DATA")
    print("="*80)

    italy_origin = truck_traffic[truck_traffic['origin_country'] == 'IT']
    italy_dest = truck_traffic[truck_traffic['dest_country'] == 'IT']

    print(f"\nRoutes FROM Italy: {len(italy_origin):,}")
    print(f"  Total traffic: {italy_origin['Traffic_flow_trucks_2030'].sum():,.0f} trucks/year")

    print(f"\nRoutes TO Italy: {len(italy_dest):,}")
    print(f"  Total traffic: {italy_dest['Traffic_flow_trucks_2030'].sum():,.0f} trucks/year")

    # Domestic Italy
    italy_domestic = truck_traffic[
        (truck_traffic['origin_country'] == 'IT') &
        (truck_traffic['dest_country'] == 'IT')
    ]
    print(f"\nDomestic Italy routes (IT->IT): {len(italy_domestic):,}")
    print(f"  Total traffic: {italy_domestic['Traffic_flow_trucks_2030'].sum():,.0f} trucks/year")

    # International Italy (cross-border)
    italy_international = truck_traffic[
        ((truck_traffic['origin_country'] == 'IT') & (truck_traffic['dest_country'] != 'IT')) |
        ((truck_traffic['origin_country'] != 'IT') & (truck_traffic['dest_country'] == 'IT'))
    ]
    print(f"\nInternational Italy routes (cross-border): {len(italy_international):,}")
    print(f"  Total traffic: {italy_international['Traffic_flow_trucks_2030'].sum():,.0f} trucks/year")

    print("\n" + "="*80)


if __name__ == "__main__":
    # First analyze original data
    analyze_original_traffic_data()

    # Then analyze processed case
    print("\n\n")
    case_name = "case_20251107_105426_rail"

    print("="*80)
    print(f"OD PAIR ANALYSIS - PROCESSED CASE")
    print("="*80)

    result = analyze_odpairs(case_name)

    print(f"\n[SUCCESS] Analysis completed!")
    print(f"  Original data has Italy: Check above")
    print(f"  Processed case Italy OD pairs: {result['italy_origins'] + result['italy_dests']}")
