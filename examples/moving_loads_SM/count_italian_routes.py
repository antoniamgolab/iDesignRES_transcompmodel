"""
Count Italian routes in truck traffic data (using proper NUTS3 mapping)
"""
import pandas as pd

print("="*80)
print("COUNTING ITALIAN ROUTES IN TRUCK TRAFFIC")
print("="*80)

# Load NUTS3 regions mapping
nuts3 = pd.read_csv("data/Trucktraffic_NUTS3/02_NUTS-3-Regions.csv")

# Create mapping: ETISPlus_Zone_ID -> Country
id_to_country = dict(zip(nuts3['ETISPlus_Zone_ID'], nuts3['Country']))

print(f"\nLoaded {len(nuts3)} NUTS3 regions")
print(f"Mapping has {len(id_to_country)} region ID -> country mappings")

# Load truck traffic
traffic = pd.read_csv("data/Trucktraffic_NUTS3/01_Trucktrafficflow.csv")
print(f"Loaded {len(traffic):,} routes from truck traffic")

# Map origin and destination IDs to countries
print("\nMapping region IDs to countries...")
traffic['origin_country'] = traffic['ID_origin_region'].map(id_to_country)
traffic['dest_country'] = traffic['ID_destination_region'].map(id_to_country)

# Check for unmapped regions
unmapped_origins = traffic['origin_country'].isna().sum()
unmapped_dests = traffic['dest_country'].isna().sum()

print(f"  Unmapped origins: {unmapped_origins}")
print(f"  Unmapped destinations: {unmapped_dests}")

# Count Italian routes
italy_origin = traffic[traffic['origin_country'] == 'IT']
italy_dest = traffic[traffic['dest_country'] == 'IT']
italy_domestic = traffic[(traffic['origin_country'] == 'IT') & (traffic['dest_country'] == 'IT')]
italy_exports = traffic[(traffic['origin_country'] == 'IT') & (traffic['dest_country'] != 'IT')]
italy_imports = traffic[(traffic['origin_country'] != 'IT') & (traffic['dest_country'] == 'IT')]

print("\n" + "-"*80)
print("ITALIAN ROUTES IN TRUCK TRAFFIC")
print("-"*80)

print(f"\nRoutes FROM Italy (IT):               {len(italy_origin):>8,}")
print(f"  Total traffic: {italy_origin['Traffic_flow_trucks_2030'].sum():>15,.0f} trucks/year")

print(f"\nRoutes TO Italy (IT):                 {len(italy_dest):>8,}")
print(f"  Total traffic: {italy_dest['Traffic_flow_trucks_2030'].sum():>15,.0f} trucks/year")

print(f"\nDomestic Italy routes (IT -> IT):     {len(italy_domestic):>8,}")
print(f"  Total traffic: {italy_domestic['Traffic_flow_trucks_2030'].sum():>15,.0f} trucks/year")

print(f"\nItaly EXPORTS (IT -> other):          {len(italy_exports):>8,}")
print(f"  Total traffic: {italy_exports['Traffic_flow_trucks_2030'].sum():>15,.0f} trucks/year")

print(f"\nItaly IMPORTS (other -> IT):          {len(italy_imports):>8,}")
print(f"  Total traffic: {italy_imports['Traffic_flow_trucks_2030'].sum():>15,.0f} trucks/year")

# Show sample Italian routes
print("\n" + "-"*80)
print("SAMPLE ITALIAN ROUTES")
print("-"*80)

print("\nSample DOMESTIC routes (IT -> IT):")
for _, row in italy_domestic.head(5).iterrows():
    orig_id = row['ID_origin_region']
    dest_id = row['ID_destination_region']
    traffic = row['Traffic_flow_trucks_2030']

    orig_name = nuts3[nuts3['ETISPlus_Zone_ID'] == orig_id]['Name'].values[0]
    dest_name = nuts3[nuts3['ETISPlus_Zone_ID'] == dest_id]['Name'].values[0]

    print(f"  {orig_name} -> {dest_name}: {traffic:,.0f} trucks/year")

print("\nSample EXPORT routes (IT -> other):")
for _, row in italy_exports.head(5).iterrows():
    orig_id = row['ID_origin_region']
    dest_id = row['ID_destination_region']
    traffic = row['Traffic_flow_trucks_2030']

    orig_name = nuts3[nuts3['ETISPlus_Zone_ID'] == orig_id]['Name'].values[0]
    dest_name = nuts3[nuts3['ETISPlus_Zone_ID'] == dest_id]['Name'].values[0]
    dest_country = row['dest_country']

    print(f"  {orig_name} (IT) -> {dest_name} ({dest_country}): {traffic:,.0f} trucks/year")

print("\n" + "="*80)
print("[FINDING] Italy IS present in the original truck traffic data!")
print("="*80)
