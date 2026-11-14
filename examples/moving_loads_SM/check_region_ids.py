"""
Check what region IDs from truck traffic data represent
"""
import pandas as pd

# Load NUTS3 regions mapping
nuts3 = pd.read_csv("data/Trucktraffic_NUTS3/02_NUTS-3-Regions.csv")

# Load truck traffic
traffic = pd.read_csv("data/Trucktraffic_NUTS3/01_Trucktrafficflow.csv")

# Sample region IDs from truck traffic
sample_ids = [101010101, 101010201, 101010203, 101020101, 118120200]

print("="*80)
print("CHECKING REGION IDs FROM TRUCK TRAFFIC")
print("="*80)

print(f"\nTotal regions in NUTS3 mapping: {len(nuts3)}")
print(f"Total routes in truck traffic: {len(traffic)}")

print("\n" + "-"*80)
print("SAMPLE TRUCK TRAFFIC REGION IDs")
print("-"*80)

for sid in sample_ids:
    match = nuts3[nuts3['ETISPlus_Zone_ID'] == sid]
    if len(match) > 0:
        name = match['Name'].values[0]
        country = match['Country'].values[0]
        print(f"{sid:>12} -> {name:<30} ({country})")
    else:
        print(f"{sid:>12} -> NOT FOUND IN NUTS3 MAPPING")

# Check country distribution in truck traffic
print("\n" + "-"*80)
print("CHECKING IF ITALIAN REGION IDs EXIST IN TRUCK TRAFFIC")
print("-"*80)

# Get all Italian ETISPlus_Zone_IDs
italian_ids = set(nuts3[nuts3['Country'] == 'IT']['ETISPlus_Zone_ID'].values)
print(f"\nItalian NUTS3 regions in mapping: {len(italian_ids)}")
print(f"Sample Italian IDs: {sorted(list(italian_ids))[:10]}")

# Check if any Italian IDs appear in truck traffic
traffic_origin_ids = set(traffic['ID_origin_region'].values)
traffic_dest_ids = set(traffic['ID_destination_region'].values)
all_traffic_ids = traffic_origin_ids | traffic_dest_ids

print(f"\nUnique origin IDs in traffic: {len(traffic_origin_ids)}")
print(f"Unique destination IDs in traffic: {len(traffic_dest_ids)}")
print(f"Total unique region IDs in traffic: {len(all_traffic_ids)}")

# Find intersection
italian_in_traffic_origins = italian_ids & traffic_origin_ids
italian_in_traffic_dests = italian_ids & traffic_dest_ids
italian_in_traffic_any = italian_ids & all_traffic_ids

print(f"\nItalian IDs as ORIGINS in traffic: {len(italian_in_traffic_origins)}")
print(f"Italian IDs as DESTINATIONS in traffic: {len(italian_in_traffic_dests)}")
print(f"Italian IDs appearing ANYWHERE in traffic: {len(italian_in_traffic_any)}")

if len(italian_in_traffic_any) > 0:
    print(f"\nSample Italian IDs found in traffic: {sorted(list(italian_in_traffic_any))[:10]}")
else:
    print("\n[FINDING] NO ITALIAN REGION IDs FOUND IN TRUCK TRAFFIC DATA!")
    print("  This confirms Italy was never included in the source dataset.")

# Check what countries ARE in the traffic data
print("\n" + "-"*80)
print("WHICH COUNTRIES ARE IN TRUCK TRAFFIC?")
print("-"*80)

# Map traffic IDs to countries
traffic_ids_to_check = list(all_traffic_ids)[:100]  # Sample first 100
countries_found = set()

for tid in traffic_ids_to_check:
    match = nuts3[nuts3['ETISPlus_Zone_ID'] == tid]
    if len(match) > 0:
        countries_found.add(match['Country'].values[0])

print(f"\nCountries found in traffic data (sample of 100 IDs): {sorted(countries_found)}")

print("\n" + "="*80)
