"""
COPY THIS CODE INTO YOUR SM-preprocessing.ipynb NOTEBOOK

This cell identifies border NUTS2 regions and their foreign neighbors
for further processing in your TransComp preprocessing workflow.
"""

# ============================================================================
# CELL: Identify Border NUTS2 Regions with Foreign Neighbors
# ============================================================================

from identify_border_regions import (
    identify_border_regions_with_neighbors,
    filter_border_regions_with_active_neighbors
)

# Load NUTS shapefile (already done in your notebook)
# nuts_regions = gpd.read_file("data/NUTS_RG_20M_2021_4326.shp/NUTS_RG_20M_2021_4326.shp")

# Identify border regions from your GeographicElement data
df_border_regions = identify_border_regions_with_neighbors(
    nuts_shapefile_path="data/NUTS_RG_20M_2021_4326.shp/NUTS_RG_20M_2021_4326.shp",
    geographic_element_yaml_path="input_data/case_nuts2_complete/GeographicElement.yaml",
    nuts_level=2,
    verbose=True
)

# Filter to only border regions with foreign neighbors in dataset
df_border_only = filter_border_regions_with_active_neighbors(
    df_border_regions,
    min_foreign_neighbors=1
)

# Extract lists for processing
border_nuts2_codes = df_border_only['nuts_region'].tolist()
print(f"\nIdentified {len(border_nuts2_codes)} border NUTS2 regions:")
print(border_nuts2_codes)

# Create dictionary mapping border regions to their foreign neighbors
border_neighbor_dict = {}
for _, row in df_border_only.iterrows():
    border_neighbor_dict[row['nuts_region']] = row['foreign_neighbors']

# Display summary
print("\nBorder regions and their foreign neighbors:")
for region, neighbors in border_neighbor_dict.items():
    print(f"  {region}: {', '.join(neighbors)}")

# ============================================================================
# CELL: Filter GeographicElements to Border Regions Only (Optional)
# ============================================================================

# If you want to focus preprocessing only on border regions and their neighbors
relevant_nuts2_codes = set(border_nuts2_codes)

# Add all neighbors (both foreign and domestic) to the relevant set
for _, row in df_border_only.iterrows():
    relevant_nuts2_codes.update(row['all_neighbors'])

print(f"\nTotal NUTS2 regions to process (border + neighbors): {len(relevant_nuts2_codes)}")
print(f"Codes: {sorted(relevant_nuts2_codes)}")

# Filter your geographic_elements list (from YAML) to only relevant regions
# Example:
# relevant_geo_elements = [
#     elem for elem in geographic_elements
#     if elem.get('nuts2_region') in relevant_nuts2_codes
# ]

# ============================================================================
# CELL: Visualize Border Regions on Map
# ============================================================================

import matplotlib.pyplot as plt

# Filter NUTS shapefile to show border regions
nuts_filtered = nuts_regions[nuts_regions['LEVL_CODE'] == 2].copy()
border_geom = nuts_filtered[nuts_filtered['NUTS_ID'].isin(border_nuts2_codes)]
all_dataset_geom = nuts_filtered[nuts_filtered['NUTS_ID'].isin(df_border_regions['nuts_region'])]

# Create map
fig, ax = plt.subplots(1, 1, figsize=(12, 10))

# Plot all regions in dataset (light gray)
all_dataset_geom.plot(ax=ax, color='lightgray', edgecolor='gray', linewidth=0.5, label='Dataset regions')

# Highlight border regions (red)
border_geom.plot(ax=ax, color='red', alpha=0.6, edgecolor='darkred', linewidth=1.0, label='Border regions')

# Add region labels for border regions
for idx, row in border_geom.iterrows():
    centroid = row.geometry.centroid
    ax.text(centroid.x, centroid.y, row['NUTS_ID'],
            fontsize=8, ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))

ax.set_title('NUTS2 Border Regions in Dataset', fontsize=14, fontweight='bold')
ax.legend(loc='upper right')
ax.set_xlabel('Longitude')
ax.set_ylabel('Latitude')
plt.tight_layout()
plt.show()

print(f"\nVisualized {len(border_geom)} border regions")

# ============================================================================
# CELL: Create Cross-Border OD Pairs for Analysis
# ============================================================================

# Generate all bidirectional cross-border OD pairs
cross_border_pairs = []
for _, row in df_border_only.iterrows():
    origin = row['nuts_region']
    for neighbor in row['foreign_neighbors']:
        cross_border_pairs.append({
            'origin': origin,
            'destination': neighbor,
            'origin_country': row['country'],
            'destination_country': df_border_only[df_border_only['nuts_region'] == neighbor]['country'].iloc[0]
                                   if neighbor in border_nuts2_codes else 'Unknown'
        })

import pandas as pd
df_cross_border_pairs = pd.DataFrame(cross_border_pairs)

print(f"\nGenerated {len(df_cross_border_pairs)} directional cross-border OD pairs")
print("\nSample cross-border pairs:")
print(df_cross_border_pairs.head(10))

# You can now use these pairs to filter your Odpair data or
# to specifically analyze cross-border transport flows
