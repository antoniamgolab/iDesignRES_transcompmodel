"""
Verify that country labels will appear within the plot range.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import pandas as pd
import yaml

# Read country centroids
centroids_df = pd.read_csv('country_centroids.csv')

# Read geographic elements to get data range
geo_file = r'input_data\case_20251103_114421\GeographicElement.yaml'
with open(geo_file, 'r', encoding='utf-8') as f:
    geo_elements = yaml.safe_load(f)

# Get latitude range of NUTS2 regions
nuts2_lats = []
for geo in geo_elements:
    if geo.get('type') == 'node' and 'nuts2_region' in geo and geo['nuts2_region']:
        nuts2_lats.append(geo['coordinate_lat'])

data_lat_min = min(nuts2_lats)
data_lat_max = max(nuts2_lats)

print("=" * 70)
print("COUNTRY LABEL VERIFICATION")
print("=" * 70)
print(f"\nData latitude range: {data_lat_min:.2f}°N to {data_lat_max:.2f}°N")
print(f"\nCountry centroids:")
print("-" * 70)

corridor_countries = ['IT', 'AT', 'DE', 'DK', 'SE', 'NO']
for country in corridor_countries:
    row = centroids_df[centroids_df['CNTR_CODE'] == country]
    if not row.empty:
        lat = row.iloc[0]['centroid_lat']
        in_range = data_lat_min <= lat <= data_lat_max
        status = "OK - IN RANGE" if in_range else "WARNING - OUT OF RANGE"
        print(f"{country}: {lat:6.2f}°N  [{status}]")
    else:
        print(f"{country}: NOT FOUND")

print("-" * 70)
print("\nAll countries should show 'OK - IN RANGE' for labels to appear correctly.")
