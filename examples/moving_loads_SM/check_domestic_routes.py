"""
Check if input data contains domestic routes (e.g., DE to DE)
"""

import yaml
import os

# Update this to match your current case
case_name = "case_20251106_102427"  # From results_representation.ipynb
input_folder = f"input_data/{case_name}"

print("="*80)
print(f"CHECKING FOR DOMESTIC ROUTES IN: {case_name}")
print("="*80)

# Load Odpair data
odpair_file = os.path.join(input_folder, "Odpair.yaml")

if not os.path.exists(odpair_file):
    print(f"\n[ERROR] Odpair.yaml not found at: {odpair_file}")
    exit(1)

print(f"\nLoading: {odpair_file}")

with open(odpair_file, 'r', encoding='utf-8') as f:
    odpairs = yaml.safe_load(f)

# Load GeographicElement to map geo_id -> country
geo_file = os.path.join(input_folder, "GeographicElement.yaml")

if not os.path.exists(geo_file):
    print(f"\n[ERROR] GeographicElement.yaml not found at: {geo_file}")
    exit(1)

with open(geo_file, 'r', encoding='utf-8') as f:
    geo_elements = yaml.safe_load(f)

# Create mapping: geo_id -> country
geo_to_country = {}
for geo in geo_elements:
    geo_id = geo.get('id')
    country = geo.get('country')
    if geo_id and country:
        geo_to_country[geo_id] = country

print(f"\nLoaded {len(geo_elements)} geographic elements")
print(f"Loaded {len(odpairs)} odpairs")

# Categorize odpairs
international_routes = []
domestic_routes = []

for odpair in odpairs:
    odpair_id = odpair.get('id')
    origin_id = odpair.get('from')
    dest_id = odpair.get('to')

    if not all([odpair_id, origin_id, dest_id]):
        continue

    origin_country = geo_to_country.get(origin_id, 'UNKNOWN')
    dest_country = geo_to_country.get(dest_id, 'UNKNOWN')

    if origin_country == dest_country:
        domestic_routes.append({
            'odpair_id': odpair_id,
            'origin_id': origin_id,
            'dest_id': dest_id,
            'country': origin_country
        })
    else:
        international_routes.append({
            'odpair_id': odpair_id,
            'origin_id': origin_id,
            'dest_id': dest_id,
            'origin_country': origin_country,
            'dest_country': dest_country
        })

# Results
print("\n" + "="*80)
print("RESULTS")
print("="*80)

total = len(domestic_routes) + len(international_routes)
print(f"\nTotal odpairs analyzed: {total}")
print(f"  International routes: {len(international_routes)} ({len(international_routes)/total*100:.1f}%)")
print(f"  Domestic routes: {len(domestic_routes)} ({len(domestic_routes)/total*100:.1f}%)")

# Show domestic routes by country
if domestic_routes:
    print("\n" + "="*80)
    print("DOMESTIC ROUTES BREAKDOWN")
    print("="*80)

    domestic_by_country = {}
    for route in domestic_routes:
        country = route['country']
        domestic_by_country[country] = domestic_by_country.get(country, 0) + 1

    for country, count in sorted(domestic_by_country.items()):
        print(f"  {country}: {count} domestic odpairs ({count/len(domestic_routes)*100:.1f}% of domestic)")

    # Show first few examples
    print("\n  Examples of domestic routes:")
    for route in domestic_routes[:5]:
        print(f"    Odpair {route['odpair_id']}: {route['country']} (geo {route['origin_id']} -> {route['dest_id']})")

else:
    print("\n✓ NO DOMESTIC ROUTES FOUND - All routes are international!")

# Show international examples
if international_routes:
    print("\n" + "="*80)
    print("INTERNATIONAL ROUTES EXAMPLES")
    print("="*80)

    for route in international_routes[:10]:
        print(f"  Odpair {route['odpair_id']}: {route['origin_country']} -> {route['dest_country']}")

print("\n" + "="*80)
