"""
Check if there are Austria->Italy, Germany->Italy routes in original data
"""
import pandas as pd

print("="*80)
print("CHECKING FOR CORRIDOR -> ITALY ROUTES IN ORIGINAL DATA")
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

# Check routes FROM corridor countries TO Italy
print("\n" + "-"*80)
print("ROUTES FROM CORRIDOR COUNTRIES TO ITALY")
print("-"*80)

for country in corridor_countries:
    routes_to_italy = traffic[
        (traffic['origin_country'] == country) &
        (traffic['dest_country'] == 'IT')
    ]

    if len(routes_to_italy) > 0:
        total_traffic = routes_to_italy['Traffic_flow_trucks_2030'].sum()
        print(f"\n{country} -> IT:")
        print(f"  Routes: {len(routes_to_italy):,}")
        print(f"  Traffic: {total_traffic:,.0f} trucks/year")

        # Show top 5 routes by traffic
        top_routes = routes_to_italy.nlargest(5, 'Traffic_flow_trucks_2030')
        print(f"  Top routes:")
        for _, route in top_routes.iterrows():
            orig_id = route['ID_origin_region']
            dest_id = route['ID_destination_region']
            traffic_vol = route['Traffic_flow_trucks_2030']

            orig_name = nuts3[nuts3['ETISPlus_Zone_ID'] == orig_id]['Name'].values[0]
            dest_name = nuts3[nuts3['ETISPlus_Zone_ID'] == dest_id]['Name'].values[0]

            print(f"    {orig_name} -> {dest_name}: {traffic_vol:,.0f} trucks/year")
    else:
        print(f"\n{country} -> IT: NO ROUTES")

# Check routes FROM Italy TO corridor countries
print("\n" + "-"*80)
print("ROUTES FROM ITALY TO CORRIDOR COUNTRIES")
print("-"*80)

for country in corridor_countries:
    routes_from_italy = traffic[
        (traffic['origin_country'] == 'IT') &
        (traffic['dest_country'] == country)
    ]

    if len(routes_from_italy) > 0:
        total_traffic = routes_from_italy['Traffic_flow_trucks_2030'].sum()
        print(f"\nIT -> {country}:")
        print(f"  Routes: {len(routes_from_italy):,}")
        print(f"  Traffic: {total_traffic:,.0f} trucks/year")

        # Show top 5 routes by traffic
        top_routes = routes_from_italy.nlargest(5, 'Traffic_flow_trucks_2030')
        print(f"  Top routes:")
        for _, route in top_routes.iterrows():
            orig_id = route['ID_origin_region']
            dest_id = route['ID_destination_region']
            traffic_vol = route['Traffic_flow_trucks_2030']

            orig_name = nuts3[nuts3['ETISPlus_Zone_ID'] == orig_id]['Name'].values[0]
            dest_name = nuts3[nuts3['ETISPlus_Zone_ID'] == dest_id]['Name'].values[0]

            print(f"    {orig_name} -> {dest_name}: {traffic_vol:,.0f} trucks/year")
    else:
        print(f"\nIT -> {country}: NO ROUTES")

# Summary
print("\n" + "="*80)
print("SUMMARY: ITALY <-> CORRIDOR ROUTES")
print("="*80)

corridor_to_italy = traffic[
    traffic['origin_country'].isin(corridor_countries) &
    (traffic['dest_country'] == 'IT')
]

italy_to_corridor = traffic[
    (traffic['origin_country'] == 'IT') &
    traffic['dest_country'].isin(corridor_countries)
]

print(f"\nTotal routes FROM corridor countries TO Italy: {len(corridor_to_italy):,}")
print(f"  Total traffic: {corridor_to_italy['Traffic_flow_trucks_2030'].sum():,.0f} trucks/year")

print(f"\nTotal routes FROM Italy TO corridor countries: {len(italy_to_corridor):,}")
print(f"  Total traffic: {italy_to_corridor['Traffic_flow_trucks_2030'].sum():,.0f} trucks/year")

total_bidirectional = len(corridor_to_italy) + len(italy_to_corridor)
total_traffic = corridor_to_italy['Traffic_flow_trucks_2030'].sum() + italy_to_corridor['Traffic_flow_trucks_2030'].sum()

print(f"\n[KEY FINDING] Total Italy <-> Corridor routes: {total_bidirectional:,}")
print(f"              Total traffic: {total_traffic:,.0f} trucks/year")
print(f"\nThese routes SHOULD appear as Italian OD pairs in the processed case!")
print("But they don't because of the preprocessing bug.")

print("\n" + "="*80)
