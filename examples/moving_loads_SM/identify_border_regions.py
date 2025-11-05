"""
Identify NUTS2 Border Regions with Neighbors

This script identifies NUTS2 regions that:
1. Are located at international borders (have neighbors in different countries)
2. Have corresponding GeographicElement entries in the dataset
3. Have neighboring regions that also exist in the GeographicElement data

Usage:
    border_regions = identify_border_regions_with_neighbors(
        nuts_shapefile_path="data/NUTS_RG_20M_2021_4326.shp/NUTS_RG_20M_2021_4326.shp",
        geographic_element_yaml_path="input_data/case_nuts2_complete/GeographicElement.yaml",
        nuts_level=2
    )
"""

import geopandas as gpd
import yaml
import pandas as pd
from shapely.geometry import Point
from typing import Dict, List, Tuple, Set


def load_geographic_elements(yaml_path: str) -> Dict:
    """
    Load GeographicElement data from YAML file.

    Returns:
        dict with:
            - 'elements': list of all geographic elements
            - 'nuts2_set': set of NUTS2 region codes present in data
            - 'by_nuts2': dict mapping nuts2_region to list of elements
            - 'by_country': dict mapping country to list of nuts2 regions
    """
    with open(yaml_path, 'r') as f:
        geo_elements = yaml.safe_load(f)

    # Extract NUTS2 regions present in the dataset
    nuts2_set = set()
    by_nuts2 = {}
    by_country = {}

    for elem in geo_elements:
        if elem.get('type') == 'node' and 'nuts2_region' in elem:
            nuts2_code = elem['nuts2_region']
            country = elem.get('country', 'Unknown')

            nuts2_set.add(nuts2_code)

            if nuts2_code not in by_nuts2:
                by_nuts2[nuts2_code] = []
            by_nuts2[nuts2_code].append(elem)

            if country not in by_country:
                by_country[country] = set()
            by_country[country].add(nuts2_code)

    return {
        'elements': geo_elements,
        'nuts2_set': nuts2_set,
        'by_nuts2': by_nuts2,
        'by_country': by_country
    }


def identify_border_regions_with_neighbors(
    nuts_shapefile_path: str,
    geographic_element_yaml_path: str,
    nuts_level: int = 2,
    verbose: bool = True
) -> pd.DataFrame:
    """
    Identify NUTS2 regions at international borders that have neighbors in the dataset.

    Parameters:
    -----------
    nuts_shapefile_path : str
        Path to NUTS shapefile (e.g., "data/NUTS_RG_20M_2021_4326.shp/...")

    geographic_element_yaml_path : str
        Path to GeographicElement.yaml file

    nuts_level : int
        NUTS level to analyze (default: 2)

    verbose : bool
        Print progress information

    Returns:
    --------
    pd.DataFrame with columns:
        - nuts_region: NUTS2 region code
        - country: Country code
        - neighboring_countries: Set of neighboring country codes
        - neighbors_in_dataset: List of neighboring NUTS2 regions present in dataset
        - num_neighbors_in_dataset: Number of neighbors in dataset
        - is_border_region: Boolean indicating if at international border
        - geometry: Shapely geometry
        - centroid_lat: Centroid latitude
        - centroid_lon: Centroid longitude
    """

    if verbose:
        print(f"Loading NUTS shapefile from {nuts_shapefile_path}...")

    # Load NUTS regions shapefile
    nuts_regions = gpd.read_file(nuts_shapefile_path)

    # Filter to specified NUTS level
    nuts_filtered = nuts_regions[nuts_regions['LEVL_CODE'] == nuts_level].copy()

    if verbose:
        print(f"Found {len(nuts_filtered)} NUTS{nuts_level} regions")

    # Load GeographicElement data
    if verbose:
        print(f"Loading GeographicElement data from {geographic_element_yaml_path}...")

    geo_data = load_geographic_elements(geographic_element_yaml_path)
    nuts_in_dataset = geo_data['nuts2_set']

    if verbose:
        print(f"Found {len(nuts_in_dataset)} NUTS{nuts_level} regions in GeographicElement data")

    # Filter to only regions present in the dataset
    nuts_filtered = nuts_filtered[nuts_filtered['NUTS_ID'].isin(nuts_in_dataset)].copy()

    if verbose:
        print(f"Analyzing {len(nuts_filtered)} regions present in both shapefile and dataset...")

    # Create spatial index for efficient neighbor finding
    nuts_filtered['centroid_lon'] = nuts_filtered.geometry.centroid.x
    nuts_filtered['centroid_lat'] = nuts_filtered.geometry.centroid.y

    # Identify neighbors for each region
    border_regions_data = []

    for idx, row in nuts_filtered.iterrows():
        nuts_code = row['NUTS_ID']
        country = row['CNTR_CODE']
        geometry = row['geometry']

        # Find neighboring regions (regions that share a boundary)
        neighbors = nuts_filtered[nuts_filtered.geometry.touches(geometry)]

        # Separate neighbors by country
        foreign_neighbors = neighbors[neighbors['CNTR_CODE'] != country]
        all_neighbors = neighbors

        # Filter neighbors to only those in the dataset
        neighbors_in_dataset = all_neighbors[all_neighbors['NUTS_ID'].isin(nuts_in_dataset)]
        foreign_neighbors_in_dataset = foreign_neighbors[foreign_neighbors['NUTS_ID'].isin(nuts_in_dataset)]

        neighboring_countries = set(foreign_neighbors['CNTR_CODE'].unique())

        # Determine if this is a border region (has neighbors in different countries)
        is_border_region = len(foreign_neighbors) > 0

        border_regions_data.append({
            'nuts_region': nuts_code,
            'country': country,
            'neighboring_countries': neighboring_countries,
            'all_neighbors': list(neighbors_in_dataset['NUTS_ID']),
            'foreign_neighbors': list(foreign_neighbors_in_dataset['NUTS_ID']),
            'num_all_neighbors': len(neighbors_in_dataset),
            'num_foreign_neighbors': len(foreign_neighbors_in_dataset),
            'is_border_region': is_border_region,
            'geometry': geometry,
            'centroid_lat': row['centroid_lat'],
            'centroid_lon': row['centroid_lon']
        })

    # Create DataFrame
    df_border_regions = pd.DataFrame(border_regions_data)

    # Sort by country and nuts_region
    df_border_regions = df_border_regions.sort_values(['country', 'nuts_region'])

    if verbose:
        print("\n" + "=" * 80)
        print("BORDER REGIONS ANALYSIS SUMMARY")
        print("=" * 80)
        print(f"Total regions analyzed: {len(df_border_regions)}")
        print(f"Border regions (with foreign neighbors): {df_border_regions['is_border_region'].sum()}")
        print(f"Internal regions (no foreign neighbors): {(~df_border_regions['is_border_region']).sum()}")
        print(f"\nBorder regions with foreign neighbors in dataset: "
              f"{(df_border_regions['num_foreign_neighbors'] > 0).sum()}")

        # Summary by country
        print("\nBorder regions by country:")
        country_summary = df_border_regions[df_border_regions['is_border_region']].groupby('country').size()
        for country, count in country_summary.items():
            print(f"  {country}: {count} border regions")

        print("=" * 80)

    return df_border_regions


def filter_border_regions_with_active_neighbors(
    df_border_regions: pd.DataFrame,
    min_foreign_neighbors: int = 1
) -> pd.DataFrame:
    """
    Filter to only border regions that have a minimum number of foreign neighbors in the dataset.

    Parameters:
    -----------
    df_border_regions : pd.DataFrame
        Output from identify_border_regions_with_neighbors()

    min_foreign_neighbors : int
        Minimum number of foreign neighbors required (default: 1)

    Returns:
    --------
    pd.DataFrame filtered to border regions meeting the criteria
    """
    filtered = df_border_regions[
        (df_border_regions['is_border_region']) &
        (df_border_regions['num_foreign_neighbors'] >= min_foreign_neighbors)
    ].copy()

    return filtered


def export_border_regions_list(
    df_border_regions: pd.DataFrame,
    output_file: str = "border_regions_list.txt",
    include_neighbors: bool = True
):
    """
    Export list of border regions to a text file for easy reference.

    Parameters:
    -----------
    df_border_regions : pd.DataFrame
        Output from identify_border_regions_with_neighbors()

    output_file : str
        Path to output text file

    include_neighbors : bool
        Whether to include neighbor information
    """
    with open(output_file, 'w') as f:
        f.write("NUTS2 Border Regions with Neighboring Regions in Dataset\n")
        f.write("=" * 80 + "\n\n")

        for _, row in df_border_regions.iterrows():
            f.write(f"{row['nuts_region']} ({row['country']})\n")

            if include_neighbors:
                if row['foreign_neighbors']:
                    f.write(f"  Foreign neighbors: {', '.join(row['foreign_neighbors'])}\n")
                if row['all_neighbors']:
                    f.write(f"  All neighbors: {', '.join(row['all_neighbors'])}\n")
                f.write(f"  Neighboring countries: {', '.join(row['neighboring_countries'])}\n")

            f.write("\n")

    print(f"Border regions list exported to {output_file}")


# Example usage
if __name__ == "__main__":
    # Configuration
    NUTS_SHAPEFILE = "data/NUTS_RG_20M_2021_4326.shp/NUTS_RG_20M_2021_4326.shp"
    GEOGRAPHIC_ELEMENT_YAML = "input_data/case_nuts2_complete/GeographicElement.yaml"

    # Identify border regions
    df_all_regions = identify_border_regions_with_neighbors(
        nuts_shapefile_path=NUTS_SHAPEFILE,
        geographic_element_yaml_path=GEOGRAPHIC_ELEMENT_YAML,
        nuts_level=2,
        verbose=True
    )

    # Filter to only border regions with foreign neighbors in the dataset
    df_border_only = filter_border_regions_with_active_neighbors(
        df_all_regions,
        min_foreign_neighbors=1
    )

    print(f"\nBorder regions with foreign neighbors in dataset: {len(df_border_only)}")
    print("\nSample border regions:")
    print(df_border_only[['nuts_region', 'country', 'foreign_neighbors', 'num_foreign_neighbors']].head(10))

    # Export to text file
    export_border_regions_list(df_border_only, "border_regions_with_neighbors.txt")

    # Export to CSV for further processing
    df_border_only.drop(columns=['geometry']).to_csv('border_regions_analysis.csv', index=False)
    print("\nDetailed analysis exported to border_regions_analysis.csv")
