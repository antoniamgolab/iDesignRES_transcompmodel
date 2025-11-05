"""
Calculate country centroids based on actual NUTS2 regions in the dataset.
This fixes the issue where entire country centroids (e.g., NO at 68.69°N)
fall outside the plot range of actual NUTS2 regions (e.g., NO at 59-61°N).
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
        lon = geo['coordinate_long']
        nuts2 = geo['nuts2_region']

        country_regions[country].append({
            'nuts2': nuts2,
            'lat': lat,
            'lon': lon
        })

# Calculate centroids for each country based on NUTS2 regions
print("\nCountry centroids based on NUTS2 regions in dataset:")
print("=" * 60)

centroids = []
for country in sorted(country_regions.keys()):
    regions = country_regions[country]
    n = len(regions)

    avg_lat = sum(r['lat'] for r in regions) / n
    avg_lon = sum(r['lon'] for r in regions) / n

    lat_min = min(r['lat'] for r in regions)
    lat_max = max(r['lat'] for r in regions)

    print(f"{country}: {n} regions, lat range: {lat_min:.2f}-{lat_max:.2f}°N, centroid: {avg_lat:.2f}°N, {avg_lon:.2f}°E")

    centroids.append({
        'country': country,
        'lat': avg_lat,
        'lon': avg_lon
    })

# Write to CSV
output_file = 'country_centroids.csv'
print(f"\nWriting centroids to {output_file}...")

with open(output_file, 'w', encoding='utf-8') as f:
    f.write('CNTR_CODE,centroid_lat,centroid_lon\n')
    for c in centroids:
        f.write(f"{c['country']},{c['lat']},{c['lon']}\n")

print("OK - Centroids calculated successfully!")
print(f"\nNote: These centroids are based on the actual NUTS2 regions in the dataset,")
print(f"not the entire country geometry. This ensures labels appear within the plot range.")
