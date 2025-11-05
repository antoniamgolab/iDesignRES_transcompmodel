"""
Calculate southern border latitudes for each country based on NUTS2 regions.
This will be used to draw dashed lines showing approximate country borders.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import yaml
from collections import defaultdict

# Read GeographicElement.yaml
geo_file = r'input_data\case_20251103_114421\GeographicElement.yaml'
print(f"Reading {geo_file}...")

with open(geo_file, 'r', encoding='utf-8') as f:
    geo_elements = yaml.safe_load(f)

# Collect NUTS2 regions by country
country_regions = defaultdict(list)

for geo in geo_elements:
    if geo.get('type') == 'node' and 'nuts2_region' in geo and geo['nuts2_region']:
        country = geo['country']
        lat = geo['coordinate_lat']
        nuts2 = geo['nuts2_region']

        country_regions[country].append({
            'nuts2': nuts2,
            'lat': lat
        })

# Calculate min (southern) latitude for each country
print("\nSouthern border latitudes (minimum latitude of NUTS2 regions):")
print("=" * 70)

borders = []
for country in sorted(country_regions.keys()):
    regions = country_regions[country]

    lat_min = min(r['lat'] for r in regions)
    lat_max = max(r['lat'] for r in regions)

    # Find the region at the southern border
    southern_region = min(regions, key=lambda r: r['lat'])

    print(f"{country}: {lat_min:.4f}°N (region: {southern_region['nuts2']}, span: {lat_min:.2f}-{lat_max:.2f}°N)")

    borders.append({
        'country': country,
        'border_lat': lat_min,
        'southern_region': southern_region['nuts2']
    })

# Write to CSV
output_file = 'country_southern_borders.csv'
print(f"\nWriting borders to {output_file}...")

with open(output_file, 'w', encoding='utf-8') as f:
    f.write('CNTR_CODE,southern_border_lat,southern_region\n')
    for b in borders:
        f.write(f"{b['country']},{b['border_lat']},{b['southern_region']}\n")

print("OK - Country borders calculated successfully!")
print(f"\nNote: These are the minimum latitudes (southern borders) of NUTS2 regions.")
print(f"Dashed lines at these latitudes will show approximate country transitions.")
