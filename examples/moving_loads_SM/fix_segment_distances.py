"""
Fix for SM_preprocessing_nuts2_complete.py
==========================================

This module provides the correct method to distribute path distances across
NUTS2 segments using the actual E-road path data.

Instead of using edge_lookup (which has tiny local segment distances),
we traverse the E-road path and sum distances by NUTS2 region.
"""
import pandas as pd
import geopandas as gpd
import ast
from pathlib import Path
from shapely.geometry import Point
from collections import defaultdict
from typing import List, Dict, Tuple


class RoadDistanceCalculator:
    """Calculate actual road distances between NUTS2 regions using E-road paths."""

    def __init__(self, data_dir: str = "data/Trucktraffic"):
        self.data_dir = Path(data_dir)
        self.edge_distances = {}
        self.edge_endpoints = {}
        self.node_to_nuts2 = {}

    def load_data(self, shapefile_path: str):
        """Load network data and NUTS2 mapping."""
        # Load network edges
        edges = pd.read_csv(self.data_dir / '04_network-edges.csv')
        self.edge_distances = dict(zip(edges['Network_Edge_ID'], edges['Distance']))
        self.edge_endpoints = {
            row['Network_Edge_ID']: (row['Network_Node_A_ID'], row['Network_Node_B_ID'])
            for _, row in edges.iterrows()
        }

        # Load nodes and map to NUTS2
        nodes = pd.read_csv(self.data_dir / '03_network-nodes.csv')
        nuts_regions = gpd.read_file(shapefile_path)
        nuts2_regions = nuts_regions[nuts_regions['LEVL_CODE'] == 2].copy()

        nodes_gdf = gpd.GeoDataFrame(
            nodes,
            geometry=[Point(x, y) for x, y in zip(nodes['Network_Node_X'], nodes['Network_Node_Y'])],
            crs='EPSG:4326'
        )
        nodes_with_nuts2 = gpd.sjoin(nodes_gdf, nuts2_regions[['NUTS_ID', 'geometry']],
                                      predicate='within', how='left')
        self.node_to_nuts2 = dict(zip(nodes_with_nuts2['Network_Node_ID'],
                                       nodes_with_nuts2['NUTS_ID']))

        print(f"[OK] Loaded {len(self.edge_distances)} edges")
        print(f"[OK] Mapped {sum(1 for v in self.node_to_nuts2.values() if pd.notna(v))} nodes to NUTS2")

    def calculate_segment_distances(
        self,
        edge_path_str: str,
        nuts2_sequence: List[int],
        nuts2_to_code: Dict[int, str]
    ) -> List[float]:
        """
        Calculate road distances for each segment in the NUTS2 sequence.

        Parameters:
        -----------
        edge_path_str : str
            String representation of edge ID list, e.g., "[1034974, 1008535, ...]"
        nuts2_sequence : List[int]
            Sequence of NUTS2 node IDs in the path
        nuts2_to_code : Dict[int, str]
            Mapping from node ID to NUTS2 code (e.g., {8: 'DE21', 2: 'AT33'})

        Returns:
        --------
        List[float]
            Distance for each segment (same length as nuts2_sequence)
            First element is always 0 (origin)
        """
        # Parse edge path
        try:
            edge_path = ast.literal_eval(edge_path_str)
        except:
            # Fallback to equal distribution
            return None

        # Get NUTS2 codes for the sequence
        nuts2_codes = [nuts2_to_code.get(n) for n in nuts2_sequence]

        # Track distance by NUTS2 region
        region_distances = defaultdict(float)

        for edge_id in edge_path:
            if edge_id not in self.edge_endpoints:
                continue

            node_a, node_b = self.edge_endpoints[edge_id]
            dist = self.edge_distances.get(edge_id, 0)

            # Determine which NUTS2 region this edge is in
            nuts2_a = self.node_to_nuts2.get(node_a)
            nuts2_b = self.node_to_nuts2.get(node_b)
            edge_nuts2 = nuts2_a if pd.notna(nuts2_a) else nuts2_b

            if pd.notna(edge_nuts2):
                region_distances[edge_nuts2] += dist

        # Build segment distances in sequence order
        segment_distances = [0.0]  # First segment is always 0
        for i in range(1, len(nuts2_codes)):
            nuts2_code = nuts2_codes[i]
            dist = region_distances.get(nuts2_code, 0)
            segment_distances.append(dist)

        return segment_distances


def fix_distribute_distance(
    self,
    path_sequence: List[int],
    total_distance: float,
    edge_path_str: str = None
) -> List[float]:
    """
    FIXED: Distribute traffic distance using actual E-road path data.

    This replaces the broken edge_lookup approach with proper road distance calculation.
    """
    if len(path_sequence) < 2:
        return [0]

    # If we have E-road path data, use it for proper distribution
    if edge_path_str and hasattr(self, 'road_distance_calculator'):
        segment_dists = self.road_distance_calculator.calculate_segment_distances(
            edge_path_str,
            path_sequence,
            {n: self.node_to_nuts2_code.get(n) for n in path_sequence}
        )

        if segment_dists:
            # Scale to match total distance
            total_from_edges = sum(segment_dists)
            if total_from_edges > 0:
                scale = total_distance / total_from_edges
                return [d * scale for d in segment_dists]

    # Fallback: Use haversine distances for proportioning
    import math

    def haversine_km(lat1, lon1, lat2, lon2):
        R = 6371
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat, dlon = lat2 - lat1, lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
        return R * 2 * math.asin(math.sqrt(a))

    # Calculate haversine proportions
    network_dists = [0]
    for i in range(1, len(path_sequence)):
        prev, curr = path_sequence[i-1], path_sequence[i]
        prev_geo = self.node_coords[prev]
        curr_geo = self.node_coords[curr]
        dist = haversine_km(prev_geo['lat'], prev_geo['lon'],
                           curr_geo['lat'], curr_geo['lon'])
        network_dists.append(dist * 1.3)  # Road factor

    # Scale to match total
    total_network = sum(network_dists)
    if total_network > 0:
        scale = total_distance / total_network
        return [d * scale for d in network_dists]

    # Final fallback: equal distribution
    seg_dist = total_distance / (len(path_sequence) - 1)
    return [0] + [seg_dist] * (len(path_sequence) - 1)


if __name__ == "__main__":
    # Test the fix
    calc = RoadDistanceCalculator()
    shapefile = "data/NUTS_RG_20M_2021_4326.shp/NUTS_RG_20M_2021_4326.shp"
    calc.load_data(shapefile)

    # Test with a sample path
    test_edge_path = "[1034974, 1008535, 1008552]"
    test_sequence = [8, 2, 58]  # DE21 -> AT33 -> ITH1
    test_mapping = {8: 'DE21', 2: 'AT33', 58: 'ITH1'}

    result = calc.calculate_segment_distances(test_edge_path, test_sequence, test_mapping)
    print(f"Segment distances: {result}")
