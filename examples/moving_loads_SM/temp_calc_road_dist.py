"""Calculate actual road distances by NUTS2 segment from E-road path data."""
import pandas as pd
import geopandas as gpd
import ast
from pathlib import Path
from shapely.geometry import Point
from collections import defaultdict

# Load data
data_dir = Path(r'C:\Users\simuser\Documents\AntoniaGolab\Scand_Med_analysis\SM_baby_2\iDesignRES_transcompmodel\examples\moving_loads_SM\data\Trucktraffic')

traffic = pd.read_csv(data_dir / '01_Trucktrafficflow.csv')
edges = pd.read_csv(data_dir / '04_network-edges.csv')
nodes = pd.read_csv(data_dir / '03_network-nodes.csv')

# Load NUTS2 shapefile
shapefile_dir = Path(r'C:\Users\simuser\Documents\AntoniaGolab\Scand_Med_analysis\SM_baby_2\iDesignRES_transcompmodel\examples\moving_loads_SM\data\NUTS_RG_20M_2021_4326.shp')
nuts_regions = gpd.read_file(shapefile_dir / 'NUTS_RG_20M_2021_4326.shp')
nuts2_regions = nuts_regions[nuts_regions['LEVL_CODE'] == 2].copy()

# Map network nodes to NUTS2
nodes_gdf = gpd.GeoDataFrame(
    nodes,
    geometry=[Point(x, y) for x, y in zip(nodes['Network_Node_X'], nodes['Network_Node_Y'])],
    crs='EPSG:4326'
)
nodes_with_nuts2 = gpd.sjoin(nodes_gdf, nuts2_regions[['NUTS_ID', 'geometry']], predicate='within', how='left')
node_to_nuts2 = dict(zip(nodes_with_nuts2['Network_Node_ID'], nodes_with_nuts2['NUTS_ID']))

# Build edge lookups
edge_distances = dict(zip(edges['Network_Edge_ID'], edges['Distance']))
edge_endpoints = {row['Network_Edge_ID']: (row['Network_Node_A_ID'], row['Network_Node_B_ID'])
                  for _, row in edges.iterrows()}

print('Calculating road distances by NUTS2 segment...')

# Find a path through the Brenner corridor (Austria -> Italy)
brenner_paths = traffic[
    (traffic['Name_origin_region'].str.contains('Tirol|Innsbruck', case=False, na=False)) &
    (traffic['Name_destination_region'].str.contains('Verona|Trento|Bolzano|Venezia', case=False, na=False))
].head(5)

print(f'Found {len(brenner_paths)} Brenner corridor paths')

if len(brenner_paths) > 0:
    example = brenner_paths.iloc[0]
    print(f'\nExample: {example["Name_origin_region"]} -> {example["Name_destination_region"]}')
    print(f'Total distance: {example["Total_distance"]:.1f} km')

    edge_path = ast.literal_eval(example['Edge_path_E_road'])

    current_nuts2 = None
    segment_distances = defaultdict(float)
    nuts2_sequence = []

    for edge_id in edge_path:
        if edge_id not in edge_endpoints:
            continue
        node_a, node_b = edge_endpoints[edge_id]
        dist = edge_distances.get(edge_id, 0)

        nuts2_a = node_to_nuts2.get(node_a)
        nuts2_b = node_to_nuts2.get(node_b)
        edge_nuts2 = nuts2_a if pd.notna(nuts2_a) else nuts2_b

        if edge_nuts2 and edge_nuts2 != current_nuts2:
            if current_nuts2:
                nuts2_sequence.append(current_nuts2)
            current_nuts2 = edge_nuts2

        if current_nuts2:
            segment_distances[current_nuts2] += dist

    if current_nuts2:
        nuts2_sequence.append(current_nuts2)

    print(f'\nNUTS2 sequence: {" -> ".join(nuts2_sequence)}')
    print(f'\nRoad distances by NUTS2 region:')
    for nuts2 in nuts2_sequence:
        print(f'  {nuts2}: {segment_distances[nuts2]:.1f} km')
    print(f'\nSum: {sum(segment_distances.values()):.1f} km')
    print(f'Distance_within_E_road: {example["Distance_within_E_road"]:.1f} km')
