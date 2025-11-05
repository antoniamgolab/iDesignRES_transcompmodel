"""
Example: How to use border regions identification in your preprocessing workflow
"""

from identify_border_regions import (
    identify_border_regions_with_neighbors,
    filter_border_regions_with_active_neighbors
)
import pandas as pd

# Step 1: Identify border regions
df_all_regions = identify_border_regions_with_neighbors(
    nuts_shapefile_path="data/NUTS_RG_20M_2021_4326.shp/NUTS_RG_20M_2021_4326.shp",
    geographic_element_yaml_path="input_data/case_nuts2_complete/GeographicElement.yaml",
    nuts_level=2,
    verbose=True
)

# Step 2: Filter to only border regions with foreign neighbors
df_border_regions = filter_border_regions_with_active_neighbors(
    df_all_regions,
    min_foreign_neighbors=1
)

print(f"\nFound {len(df_border_regions)} border regions with foreign neighbors")

# Step 3: Get list of border region codes for further processing
border_nuts2_codes = df_border_regions['nuts_region'].tolist()
print(f"\nBorder NUTS2 codes: {border_nuts2_codes}")

# Step 4: Create a mapping of border regions to their foreign neighbors
border_neighbor_map = {}
for _, row in df_border_regions.iterrows():
    border_neighbor_map[row['nuts_region']] = {
        'country': row['country'],
        'foreign_neighbors': row['foreign_neighbors'],
        'all_neighbors': row['all_neighbors'],
        'neighboring_countries': list(row['neighboring_countries'])
    }

print("\nBorder region neighbor mapping:")
for region, info in border_neighbor_map.items():
    print(f"  {region}: {info['foreign_neighbors']}")

# Step 5: Example - Filter your preprocessing to focus on border regions
# You can now use border_nuts2_codes to filter your GeographicElement data

# Example: Get all border regions from a specific country
at_border_regions = df_border_regions[df_border_regions['country'] == 'AT']
print(f"\nAustrian border regions: {at_border_regions['nuts_region'].tolist()}")

# Example: Get regions with high cross-border connectivity (>= 3 foreign neighbors)
highly_connected = df_border_regions[df_border_regions['num_foreign_neighbors'] >= 3]
print(f"\nHighly connected border regions (>=3 foreign neighbors):")
print(highly_connected[['nuts_region', 'country', 'foreign_neighbors', 'num_foreign_neighbors']])

# Step 6: Export for use in other scripts
# Save just the border region codes
with open('border_nuts2_codes.txt', 'w') as f:
    for code in border_nuts2_codes:
        f.write(f"{code}\n")
print("\nBorder NUTS2 codes exported to border_nuts2_codes.txt")

# Step 7: Create a cross-border pairs list for OD pair analysis
cross_border_pairs = []
for _, row in df_border_regions.iterrows():
    origin = row['nuts_region']
    for neighbor in row['foreign_neighbors']:
        # Add both directions
        cross_border_pairs.append((origin, neighbor))
        cross_border_pairs.append((neighbor, origin))

# Remove duplicates
cross_border_pairs = list(set(cross_border_pairs))
print(f"\nFound {len(cross_border_pairs)} unique cross-border OD pairs")

# Export cross-border pairs
df_cross_border = pd.DataFrame(cross_border_pairs, columns=['origin_nuts2', 'destination_nuts2'])
df_cross_border.to_csv('cross_border_od_pairs.csv', index=False)
print("Cross-border OD pairs exported to cross_border_od_pairs.csv")
