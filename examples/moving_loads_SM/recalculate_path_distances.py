"""
Recalculate Path.yaml distances using original E-road path data.

This script fixes the segment distance distribution by:
1. Matching Path.yaml entries to original traffic data rows
2. Using Edge_path_E_road to calculate actual road distances per NUTS2 region
3. Updating Path.yaml with corrected distance_from_previous and cumulative_distance
4. Optionally regenerating MandatoryBreaks.yaml

Author: Claude Code
Date: 2025-01
"""

import pandas as pd
import geopandas as gpd
import yaml
import ast
import numpy as np
from pathlib import Path
from shapely.geometry import Point
from collections import defaultdict
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')


class PathDistanceRecalculator:
    """Recalculate path segment distances using original E-road data."""

    def __init__(
        self,
        fixed_nuts2_dir: str = "input_data/fixed_nuts_2",
        traffic_data_dir: str = "data/Trucktraffic",
        shapefile_path: str = "data/NUTS_RG_20M_2021_4326.shp/NUTS_RG_20M_2021_4326.shp"
    ):
        self.fixed_nuts2_dir = Path(fixed_nuts2_dir)
        self.traffic_data_dir = Path(traffic_data_dir)
        self.shapefile_path = Path(shapefile_path)

        # Data storage
        self.paths = []
        self.geo_elements = []
        self.traffic_data = None
        self.network_edges = None

        # Mappings
        self.node_to_nuts2_code = {}  # NUTS2 node ID -> NUTS2 code
        self.nuts2_code_to_node = {}  # NUTS2 code -> NUTS2 node ID
        self.etis_to_nuts2 = {}       # ETISplus zone ID -> NUTS2 code
        self.edge_distances = {}      # Edge ID -> distance
        self.edge_endpoints = {}      # Edge ID -> (node_a, node_b)
        self.network_node_to_nuts2 = {}  # Network node ID -> NUTS2 code

    def load_data(self):
        """Load all required data."""
        print("=" * 70)
        print("LOADING DATA")
        print("=" * 70)

        # Load Path.yaml
        with open(self.fixed_nuts2_dir / 'Path.yaml', 'r') as f:
            self.paths = yaml.safe_load(f)
        print(f"[OK] Loaded {len(self.paths)} paths from Path.yaml")

        # Load GeographicElement.yaml
        with open(self.fixed_nuts2_dir / 'GeographicElement.yaml', 'r') as f:
            self.geo_elements = yaml.safe_load(f)

        # Build node ID <-> NUTS2 code mappings
        for g in self.geo_elements:
            if g.get('type') == 'node':
                node_id = g['id']
                nuts2_code = g.get('nuts2_region')
                if nuts2_code:
                    self.node_to_nuts2_code[node_id] = nuts2_code
                    self.nuts2_code_to_node[nuts2_code] = node_id
        print(f"[OK] Mapped {len(self.node_to_nuts2_code)} NUTS2 nodes")

        # Load traffic data
        self.traffic_data = pd.read_csv(self.traffic_data_dir / '01_Trucktrafficflow.csv')
        print(f"[OK] Loaded {len(self.traffic_data):,} traffic flow rows")

        # Load network edges
        self.network_edges = pd.read_csv(self.traffic_data_dir / '04_network-edges.csv')
        self.edge_distances = dict(zip(
            self.network_edges['Network_Edge_ID'],
            self.network_edges['Distance']
        ))
        for _, row in self.network_edges.iterrows():
            self.edge_endpoints[row['Network_Edge_ID']] = (
                row['Network_Node_A_ID'],
                row['Network_Node_B_ID']
            )
        print(f"[OK] Loaded {len(self.edge_distances)} network edges")

        # Load network nodes
        network_nodes = pd.read_csv(self.traffic_data_dir / '03_network-nodes.csv')

        # Load NUTS shapefile and map network nodes to NUTS2
        nuts_regions = gpd.read_file(self.shapefile_path)
        nuts2_regions = nuts_regions[nuts_regions['LEVL_CODE'] == 2].copy()

        nodes_gdf = gpd.GeoDataFrame(
            network_nodes,
            geometry=[Point(x, y) for x, y in
                      zip(network_nodes['Network_Node_X'], network_nodes['Network_Node_Y'])],
            crs='EPSG:4326'
        )
        nodes_with_nuts2 = gpd.sjoin(
            nodes_gdf, nuts2_regions[['NUTS_ID', 'geometry']],
            predicate='within', how='left'
        )
        self.network_node_to_nuts2 = dict(zip(
            nodes_with_nuts2['Network_Node_ID'],
            nodes_with_nuts2['NUTS_ID']
        ))
        print(f"[OK] Mapped {sum(1 for v in self.network_node_to_nuts2.values() if pd.notna(v))} network nodes to NUTS2")

        # Map ETISplus zones to NUTS2
        nuts3_regions = pd.read_csv(self.traffic_data_dir / '02_NUTS-3-Regions.csv')
        nuts3_gdf = gpd.GeoDataFrame(
            nuts3_regions,
            geometry=[Point(x, y) for x, y in
                      zip(nuts3_regions['Geometric_center_X'], nuts3_regions['Geometric_center_Y'])],
            crs='EPSG:4326'
        )
        nuts3_with_nuts2 = gpd.sjoin(
            nuts3_gdf, nuts2_regions[['NUTS_ID', 'geometry']],
            predicate='within', how='left'
        )
        self.etis_to_nuts2 = dict(zip(
            nuts3_with_nuts2['ETISPlus_Zone_ID'],
            nuts3_with_nuts2['NUTS_ID']
        ))
        print(f"[OK] Mapped {sum(1 for v in self.etis_to_nuts2.values() if pd.notna(v))} ETISplus zones to NUTS2")

        # Build traffic index for fast lookup
        self.build_traffic_index()

    def build_traffic_index(self):
        """Build an index for fast traffic data lookup."""
        print("  Building traffic data index...")

        # Add NUTS2 codes to traffic data
        self.traffic_data['origin_nuts2'] = self.traffic_data['ID_origin_region'].map(self.etis_to_nuts2)
        self.traffic_data['dest_nuts2'] = self.traffic_data['ID_destination_region'].map(self.etis_to_nuts2)

        # Build index: (origin_nuts2, dest_nuts2) -> list of row indices
        self.traffic_index = defaultdict(list)
        for idx, row in self.traffic_data.iterrows():
            key = (row['origin_nuts2'], row['dest_nuts2'])
            if pd.notna(key[0]) and pd.notna(key[1]):
                self.traffic_index[key].append(idx)

        print(f"  [OK] Indexed {len(self.traffic_index)} unique NUTS2 OD pairs")

    def find_matching_traffic_row(
        self,
        path: Dict,
        tolerance_km: float = 5.0
    ) -> Optional[pd.Series]:
        """
        Find the traffic data row that matches a path.

        Matches by: origin NUTS2, destination NUTS2, and distance (within tolerance).
        """
        # Get NUTS2 codes for path endpoints
        origin_nuts2 = self.node_to_nuts2_code.get(path['origin'])
        dest_nuts2 = self.node_to_nuts2_code.get(path['destination'])
        path_length = path['length']

        if not origin_nuts2 or not dest_nuts2:
            return None

        # Use index for fast lookup
        key = (origin_nuts2, dest_nuts2)
        if key not in self.traffic_index:
            return None

        # Check candidates by distance
        for idx in self.traffic_index[key]:
            row = self.traffic_data.iloc[idx]
            if abs(row['Total_distance'] - path_length) < tolerance_km:
                return row

        return None

    def calculate_segment_distances_from_edge_path(
        self,
        edge_path_str: str,
        nuts2_sequence: List[str]
    ) -> Optional[List[float]]:
        """
        Calculate road distances for each NUTS2 segment using the E-road path.

        Parameters:
        -----------
        edge_path_str : str
            String representation of edge ID list from traffic data
        nuts2_sequence : List[str]
            List of NUTS2 codes in the path sequence

        Returns:
        --------
        List[float] or None
            Distance for each segment, or None if calculation fails
        """
        try:
            edge_path = ast.literal_eval(edge_path_str)
        except:
            return None

        if not edge_path:
            return None

        # Track distance accumulated in each NUTS2 region
        region_distances = defaultdict(float)

        for edge_id in edge_path:
            if edge_id not in self.edge_endpoints:
                continue

            node_a, node_b = self.edge_endpoints[edge_id]
            dist = self.edge_distances.get(edge_id, 0)

            # Determine which NUTS2 region this edge is in
            nuts2_a = self.network_node_to_nuts2.get(node_a)
            nuts2_b = self.network_node_to_nuts2.get(node_b)

            # Use the first valid NUTS2
            edge_nuts2 = nuts2_a if pd.notna(nuts2_a) else nuts2_b

            if pd.notna(edge_nuts2):
                region_distances[edge_nuts2] += dist

        # Build segment distances in sequence order
        segment_distances = [0.0]  # First segment is always 0
        for i in range(1, len(nuts2_sequence)):
            nuts2_code = nuts2_sequence[i]
            dist = region_distances.get(nuts2_code, 0)
            segment_distances.append(dist)

        return segment_distances

    def recalculate_path_distances(self) -> Tuple[int, int, int]:
        """
        Recalculate all path distances using E-road data.

        Returns:
        --------
        Tuple[int, int, int]
            (paths_updated, paths_not_matched, paths_fallback)
        """
        print("\n" + "=" * 70)
        print("RECALCULATING PATH DISTANCES")
        print("=" * 70)

        paths_updated = 0
        paths_not_matched = 0
        paths_fallback = 0

        for i, path in enumerate(self.paths):
            if (i + 1) % 500 == 0:
                print(f"  Processing path {i + 1}/{len(self.paths)}...")

            # Get NUTS2 sequence for this path
            nuts2_sequence = [self.node_to_nuts2_code.get(n) for n in path['sequence']]

            # Find matching traffic row
            traffic_row = self.find_matching_traffic_row(path)

            if traffic_row is not None:
                # Calculate segment distances from E-road path
                edge_path_str = traffic_row['Edge_path_E_road']
                segment_distances = self.calculate_segment_distances_from_edge_path(
                    edge_path_str, nuts2_sequence
                )

                if segment_distances and sum(segment_distances) > 0:
                    # Scale to match total path length
                    total_from_edges = sum(segment_distances)
                    scale = path['length'] / total_from_edges
                    segment_distances = [d * scale for d in segment_distances]

                    # Update path (convert to Python floats for YAML serialization)
                    path['distance_from_previous'] = [float(d) for d in segment_distances]
                    path['cumulative_distance'] = [float(d) for d in np.cumsum(segment_distances)]
                    paths_updated += 1
                    continue

            # Fallback: use equal distribution or haversine
            paths_not_matched += 1

            # Simple fallback: equal distribution
            n_segments = len(path['sequence']) - 1
            if n_segments > 0:
                seg_dist = path['length'] / n_segments
                segment_distances = [0.0] + [seg_dist] * n_segments
                path['distance_from_previous'] = [float(d) for d in segment_distances]
                path['cumulative_distance'] = [float(d) for d in np.cumsum(segment_distances)]
                paths_fallback += 1

        print(f"\n[DONE] Path distance recalculation:")
        print(f"  Updated from E-road data: {paths_updated}")
        print(f"  Not matched (fallback):   {paths_not_matched}")
        print(f"  Using equal distribution: {paths_fallback}")

        return paths_updated, paths_not_matched, paths_fallback

    def save_updated_paths(self, output_path: Optional[str] = None):
        """Save the updated Path.yaml."""
        if output_path is None:
            output_path = self.fixed_nuts2_dir / 'Path.yaml'

        # Backup original
        backup_path = self.fixed_nuts2_dir / 'Path.yaml.backup'
        if not backup_path.exists():
            import shutil
            shutil.copy(self.fixed_nuts2_dir / 'Path.yaml', backup_path)
            print(f"[OK] Backed up original to {backup_path}")

        with open(output_path, 'w') as f:
            yaml.dump(self.paths, f, default_flow_style=False, allow_unicode=True)

        print(f"[OK] Saved updated paths to {output_path}")

    def run(self):
        """Run the full recalculation pipeline."""
        self.load_data()
        updated, not_matched, fallback = self.recalculate_path_distances()
        self.save_updated_paths()

        print("\n" + "=" * 70)
        print("RECALCULATION COMPLETE")
        print("=" * 70)
        print(f"Total paths: {len(self.paths)}")
        print(f"Successfully updated: {updated}")
        print(f"Used fallback: {fallback}")
        print("\nNext step: Regenerate MandatoryBreaks.yaml using SM_preprocessing.py")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Recalculate Path.yaml distances')
    parser.add_argument('--fixed-nuts2-dir', default='input_data/fixed_nuts_2',
                        help='Directory containing fixed_nuts_2 YAML files')
    parser.add_argument('--traffic-data-dir', default='data/Trucktraffic',
                        help='Directory containing original traffic CSV files')
    parser.add_argument('--dry-run', action='store_true',
                        help='Calculate but do not save changes')

    args = parser.parse_args()

    recalc = PathDistanceRecalculator(
        fixed_nuts2_dir=args.fixed_nuts2_dir,
        traffic_data_dir=args.traffic_data_dir
    )

    recalc.load_data()
    updated, not_matched, fallback = recalc.recalculate_path_distances()

    if not args.dry_run:
        recalc.save_updated_paths()
    else:
        print("\n[DRY RUN] Changes not saved.")
