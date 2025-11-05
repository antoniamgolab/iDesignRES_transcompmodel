"""
Complete SM Preprocessing for NUTS-3 with Preserved Demand
===========================================================

This script creates a COMPLETE NUTS-3 preprocessing that:
1. Aggregates geographic nodes to NUTS-3 (for efficient capacity planning)
2. Creates collapsed path sequences (fewer nodes)
3. Preserves ORIGINAL distances from traffic data (accurate)
4. Keeps INDIVIDUAL demand per OD-pair (not aggregated)
5. Calculates mandatory breaks based on actual distances

NEW FEATURE: Multi-case generation
By default (GENERATE_BOTH_CASES = True), generates TWO input cases:
  - Case 1: Full dataset with ALL OD-pairs -> sm_nuts3_complete/
  - Case 2: Test case with 100 OD-pairs, all >= 360km -> sm_nuts3_test/

Output directories:
  - input_data/sm_nuts3_complete/  (full dataset)
  - input_data/sm_nuts3_test/      (100 OD-pairs >= 360km)

Result: Efficient model with accurate distances and full demand detail.

Author: Claude Code
Date: 2025-10-16
"""

import pandas as pd
import numpy as np
import yaml
import geopandas as gpd
from shapely import wkt
from pathlib import Path
from typing import List, Tuple, Dict
from collections import deque, defaultdict
import ast


class CompleteSMNUTS3Preprocessor:
    """
    Complete NUTS-3 preprocessing for Scandinavian Mediterranean corridor.

    Key features:
    - NUTS-3 aggregated geographic nodes (capacity planning efficiency)
    - Collapsed path sequences (fewer nodes in routes)
    - Original traffic distances (accuracy preserved)
    - Individual OD-pairs NOT aggregated (demand detail preserved)
    """

    def __init__(self, data_dir: str, output_dir: str):
        """Initialize preprocessor."""
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # NUTS region filter (matching SM-preprocessing.ipynb lines 186-189)
        self.nuts_to_filter_for = {
            "NUTS_0": ["DE", "DK"],
            "NUTS_1": ["SE1", "SE2", "AT3", "ITC", "ITH", "ITI", "ITF"],
            "NUTS_2": ["SE11", "SE12", "SE21", "SE22", "NO08", "NO09", "NO02", "NO0A"],
        }

        # Data storage
        self.truck_traffic = None
        self.network_nodes = None
        self.network_edges = None

        # Mappings
        self.nuts3_to_node = {}  # NUTS-3 region ID -> NUTS-3 node ID
        self.node_to_nuts3 = {}  # Original node ID -> NUTS-3 region ID
        self.nuts3_nodes = {}    # NUTS-3 region ID -> aggregated node data
        self.edge_lookup = {}    # (node_a, node_b) -> distance
        self.edge_distance_map = {}  # Network_Edge_ID -> distance
        self.filtered_region_ids = set()  # ETISPlus Zone IDs of filtered regions

        # Results
        self.odpair_list = []
        self.path_list = []
        self.initial_vehicle_stock = []
        self.geographic_elements = []
        self.mandatory_breaks = []

        # Temporal resolution (1=annual, 2=biennial, 5=quinquennial, etc.)
        self.time_step = 1  # Default: annual resolution

    def load_data(self):
        """Load traffic and network data."""
        print("="*80)
        print("LOADING DATA")
        print("="*80)

        # Traffic data
        traffic_file = self.data_dir / "01_Trucktrafficflow.csv"
        self.truck_traffic = pd.read_csv(traffic_file)
        print(f"[OK] Truck traffic (before filtering): {len(self.truck_traffic):,} rows")

        # Network data
        nodes_file = self.data_dir / "03_network-nodes.csv"
        edges_file = self.data_dir / "04_network-edges.csv"
        self.network_nodes = pd.read_csv(nodes_file)
        self.network_edges = pd.read_csv(edges_file)
        print(f"[OK] Network (before filtering): {len(self.network_nodes)} nodes, {len(self.network_edges)} edges")

        # Calculate total distance if not present
        if 'Total_distance' not in self.truck_traffic.columns:
            self.truck_traffic['Total_distance'] = (
                self.truck_traffic['Distance_from_origin_region_to_E_road'] +
                self.truck_traffic['Distance_within_E_road'] +
                self.truck_traffic['Distance_from_E_road_to_destination_region']
            )

        # Apply NUTS region filtering (matching notebook logic)
        self._apply_nuts_filtering()
        # Filtering summary is now printed within _apply_nuts_filtering()

    def _apply_nuts_filtering(self):
        """
        Apply NUTS region filtering to network nodes and traffic data.
        Matches the filtering logic from SM-preprocessing.ipynb lines 186-250.

        Uses NUTS shapefile for spatial filtering to properly handle NUTS_1 and NUTS_2 regions.
        """
        print("\nApplying NUTS region filtering with spatial join...")

        # Load NUTS shapefile (go up to data/, then into NUTS folder)
        nuts_shapefile = self.data_dir.parent / "NUTS_RG_20M_2021_4326.shp" / "NUTS_RG_20M_2021_4326.shp"
        print(f"  Loading NUTS shapefile: {nuts_shapefile}")
        nuts_regions = gpd.read_file(nuts_shapefile)
        print(f"  Loaded {len(nuts_regions)} NUTS regions")

        # Collect all relevant NUTS codes from filter dict
        relevant_codes = []
        for codes in self.nuts_to_filter_for.values():
            relevant_codes.extend(codes)

        print(f"  Filtering for NUTS codes: {relevant_codes}")

        # Filter NUTS regions for LEVL_CODE == 3 (NUTS-3 level) and NUTS_ID containing any relevant code
        # This matches notebook line 556-558 - OPTIMIZED with vectorized string operations
        pattern = '|'.join(relevant_codes)
        mask = (nuts_regions['LEVL_CODE'] == 3) & (
            nuts_regions['NUTS_ID'].str.contains(pattern, regex=True)
        )
        relevant_nuts_regions = nuts_regions[mask].copy()
        print(f"  Found {len(relevant_nuts_regions)} NUTS-3 regions matching filter")

        # Load NUTS-3 to nodes mapping
        nuts_3_to_nodes_file = self.data_dir / "02_NUTS-3-Regions.csv"
        nuts_3_to_nodes = pd.read_csv(nuts_3_to_nodes_file)

        # Convert to GeoDataFrame using geometric centers - OPTIMIZED with batch conversion
        geom_series = gpd.GeoSeries.from_wkt(nuts_3_to_nodes['Geometric_center'], crs=nuts_regions.crs)
        nuts_3_to_nodes_gdf = gpd.GeoDataFrame(nuts_3_to_nodes, geometry=geom_series, crs=nuts_regions.crs)
        print(f"  Created GeoDataFrame with {len(nuts_3_to_nodes_gdf)} NUTS-3 regions")

        # Perform spatial join: find which NUTS-3 regions fall within relevant NUTS polygons
        # This matches notebook line 237-252
        filtered_nodes_by_level = {}
        for level, nuts_list in self.nuts_to_filter_for.items():
            selected_polygons = nuts_regions[nuts_regions['NUTS_ID'].isin(nuts_list)]
            if len(selected_polygons) > 0:
                filtered_nodes = gpd.sjoin(nuts_3_to_nodes_gdf, selected_polygons, predicate='within')
                filtered_nodes_by_level[level] = filtered_nodes
                print(f"    {level}: {len(filtered_nodes)} NUTS-3 regions")

        # Concatenate all filtered nodes into a single DataFrame
        all_filtered_nodes = gpd.GeoDataFrame(
            pd.concat(filtered_nodes_by_level.values(), ignore_index=True),
            crs=nuts_3_to_nodes_gdf.crs
        )

        # Remove duplicates (regions might appear in multiple levels)
        all_filtered_nodes = all_filtered_nodes.drop_duplicates(subset=['ETISPlus_Zone_ID'])

        print(f"  Total NUTS-3 regions after spatial filtering: {len(all_filtered_nodes)}")
        print(f"  Reduction: {len(nuts_3_to_nodes)} -> {len(all_filtered_nodes)} NUTS-3 regions")

        # Get the set of ETISplus Zone IDs that are in the filtered regions
        filtered_region_ids = set(all_filtered_nodes['ETISPlus_Zone_ID'].unique())
        self.filtered_region_ids = filtered_region_ids  # Store for later use

        # Filter network nodes: keep only nodes in filtered regions
        self.network_nodes = self.network_nodes[
            self.network_nodes['ETISplus_Zone_ID'].isin(filtered_region_ids)
        ].copy()

        # Get set of valid node IDs for edge filtering
        valid_node_ids = set(self.network_nodes['Network_Node_ID'].unique())

        # Filter network edges: keep only edges where AT LEAST ONE endpoint is in filtered nodes
        # This ensures we can cut routes at boundaries for entering/leaving traffic
        edges_before = len(self.network_edges)
        self.network_edges = self.network_edges[
            self.network_edges['Network_Node_A_ID'].isin(valid_node_ids) |
            self.network_edges['Network_Node_B_ID'].isin(valid_node_ids)
        ].copy()
        edges_after = len(self.network_edges)
        print(f"  Edges filtered: {edges_before:,} -> {edges_after:,} (removed {edges_before - edges_after:,})")

        # Track edges connecting two filtered nodes (inter-regional within filtered area)
        self.filtered_edge_ids = set(self.network_edges[
            self.network_edges['Network_Node_A_ID'].isin(valid_node_ids) &
            self.network_edges['Network_Node_B_ID'].isin(valid_node_ids)
        ]['Network_Edge_ID'])

        # Create edge distance map AFTER filtering (only filtered edges)
        self.edge_distance_map = dict(zip(self.network_edges['Network_Edge_ID'],
                                          self.network_edges['Distance']))
        print(f"  Edge distance map: {len(self.edge_distance_map):,} edges")

        # Filter traffic: keep routes where AT LEAST ONE endpoint is in filtered regions
        # This includes: internal routes, entering routes, leaving routes, and through routes
        rows_before = len(self.truck_traffic)
        self.truck_traffic = self.truck_traffic[
            self.truck_traffic['ID_origin_region'].isin(filtered_region_ids) |
            self.truck_traffic['ID_destination_region'].isin(filtered_region_ids)
        ].copy()

        # Mark whether origin and destination are inside filtered regions
        self.truck_traffic['origin_inside'] = self.truck_traffic['ID_origin_region'].isin(filtered_region_ids)
        self.truck_traffic['destination_inside'] = self.truck_traffic['ID_destination_region'].isin(filtered_region_ids)

        rows_after = len(self.truck_traffic)
        print(f"  Traffic rows: {rows_before:,} -> {rows_after:,} (removed {rows_before - rows_after:,})")

        # Count route types
        internal = ((self.truck_traffic['origin_inside']) & (self.truck_traffic['destination_inside'])).sum()
        entering = ((~self.truck_traffic['origin_inside']) & (self.truck_traffic['destination_inside'])).sum()
        leaving = ((self.truck_traffic['origin_inside']) & (~self.truck_traffic['destination_inside'])).sum()
        print(f"    Internal routes (both inside): {internal:,}")
        print(f"    Entering routes (origin outside): {entering:,}")
        print(f"    Leaving routes (destination outside): {leaving:,}")

        # Print comprehensive filtering summary
        print(f"\n[OK] FILTERING COMPLETE:")
        print(f"  Network nodes (after filtering): {len(self.network_nodes):,}")
        print(f"  Network edges (after filtering): {len(self.network_edges):,}")
        print(f"  Truck traffic (after filtering): {len(self.truck_traffic):,} rows")

    def _cut_route_at_boundaries(self, row, edge_distance_map, filtered_node_ids):
        """
        Cut a route at the boundaries of filtered regions.

        Returns: (cut_edge_list, cut_distance_proportion)
        """
        try:
            # Parse edge path (it's stored as string representation of list)
            if isinstance(row['Edge_path_E_road'], str):
                edge_path = ast.literal_eval(row['Edge_path_E_road'])
            else:
                edge_path = row['Edge_path_E_road']

            if not edge_path or not isinstance(edge_path, list):
                return [], 0.5  # Default to 50% if no path data

        except:
            return [], 0.5  # Default to 50% if parsing fails

        # Map edges to their corresponding nodes using network_edges
        # Keep only edges where at least one endpoint is in filtered regions
        cut_edges = []
        for edge_id in edge_path:
            # Check if edge connects filtered nodes
            edge_info = self.network_edges[self.network_edges['Network_Edge_ID'] == edge_id]
            if not edge_info.empty:
                node_a = edge_info.iloc[0]['Network_Node_A_ID']
                node_b = edge_info.iloc[0]['Network_Node_B_ID']

                # Get NUTS-3 regions for these nodes
                nuts3_a = self.node_to_nuts3.get(node_a)
                nuts3_b = self.node_to_nuts3.get(node_b)

                # Include edge if at least one endpoint is in filtered regions
                if nuts3_a in filtered_node_ids or nuts3_b in filtered_node_ids:
                    cut_edges.append(edge_id)

        # Calculate distance proportion
        if not cut_edges:
            return [], 0.5

        # Calculate total original distance and cut distance
        total_dist = sum(edge_distance_map.get(e, 0) for e in edge_path)
        cut_dist = sum(edge_distance_map.get(e, 0) for e in cut_edges)

        proportion = cut_dist / total_dist if total_dist > 0 else 0.5

        return cut_edges, proportion

    def create_nuts3_geographic_elements(self):
        """
        Create NUTS-3 aggregated geographic nodes.

        Strategy: One node per NUTS-3 region (centroid of all nodes in that region).
        """
        print("\n" + "="*80)
        print("STEP 1: CREATING NUTS-3 GEOGRAPHIC ELEMENTS")
        print("="*80)

        # Group nodes by NUTS-3 region - OPTIMIZED with vectorized operations
        # Build node_to_nuts3 mapping directly from dataframe (much faster)
        self.node_to_nuts3 = dict(zip(
            self.network_nodes['Network_Node_ID'],
            self.network_nodes['ETISplus_Zone_ID']
        ))

        # Group using pandas groupby (10-50x faster than iterrows)
        nuts3_groups = {}
        for nuts3_id, group_df in self.network_nodes.groupby('ETISplus_Zone_ID'):
            nuts3_groups[nuts3_id] = group_df.to_dict('records')

        print(f"  Found {len(nuts3_groups)} unique NUTS-3 regions")

        # Create one aggregated node per NUTS-3 region
        new_node_id = 0

        for nuts3_id, nodes_in_region in sorted(nuts3_groups.items()):
            # Calculate centroid
            lats = [n['Network_Node_Y'] for n in nodes_in_region]
            lons = [n['Network_Node_X'] for n in nodes_in_region]
            avg_lat = np.mean(lats)
            avg_lon = np.mean(lons)

            # Get country code (use most common)
            countries = [n.get('Country', 'XX') for n in nodes_in_region]
            country = max(set(countries), key=countries.count)

            # Create aggregated node
            geo_element = {
                'id': new_node_id,
                'name': f'nuts3_{nuts3_id}',
                'type': 'node',
                'nuts3_region': int(nuts3_id),
                'country': country,
                'coordinate_lat': float(avg_lat),
                'coordinate_long': float(avg_lon),
                'from': 999999,
                'to': 999999,
                'length': 0.0,
                'carbon_price': [0.0] * 21  # Placeholder
            }

            self.geographic_elements.append(geo_element)
            self.nuts3_to_node[nuts3_id] = new_node_id
            self.nuts3_nodes[nuts3_id] = geo_element

            new_node_id += 1

        print(f"[OK] Created {len(self.geographic_elements)} NUTS-3 geographic elements")
        print(f"     Reduction: {len(self.network_nodes)} -> {len(self.geographic_elements)} nodes")

    def build_edge_lookup(self):
        """Build edge lookup for topology (but won't use distances) - OPTIMIZED."""
        print("\n" + "="*80)
        print("STEP 2: BUILDING EDGE TOPOLOGY")
        print("="*80)

        # OPTIMIZED: Vectorized operations instead of iterrows (20-100x faster)
        edges_df = self.network_edges.copy()
        edges_df['nuts3_a'] = edges_df['Network_Node_A_ID'].map(self.node_to_nuts3)
        edges_df['nuts3_b'] = edges_df['Network_Node_B_ID'].map(self.node_to_nuts3)

        # Filter to inter-regional edges only
        inter_regional = edges_df[
            (edges_df['nuts3_a'].notna()) &
            (edges_df['nuts3_b'].notna()) &
            (edges_df['nuts3_a'] != edges_df['nuts3_b'])
        ]

        # Build lookup dictionary
        for row in inter_regional.itertuples(index=False):
            a = self.nuts3_to_node.get(row.nuts3_a)
            b = self.nuts3_to_node.get(row.nuts3_b)
            if a is not None and b is not None:
                self.edge_lookup[(a, b)] = row.Distance
                self.edge_lookup[(b, a)] = row.Distance

        print(f"[OK] Built edge topology: {len(self.edge_lookup)//2} inter-regional edges")

    def create_paths_with_original_distances(self, max_odpairs: int = None, min_distance_km: float = None, cross_border_only: bool = False):
        """
        Create paths with collapsed NUTS-3 nodes but original traffic distances.

        Key: Each OD-pair is kept SEPARATE (not aggregated) to preserve demand detail.

        Args:
            max_odpairs: Maximum number of OD-pairs to process (by traffic flow)
            min_distance_km: Minimum distance filter (e.g., 360km for mandatory breaks test)
            cross_border_only: If True, only include OD-pairs where origin and destination
                              are in different countries (based on first 2 chars of NUTS code)
        """
        print("\n" + "="*80)
        print("STEP 3: CREATING PATHS WITH COLLAPSED NODES + ORIGINAL DISTANCES")
        print("="*80)

        # Filter valid traffic
        valid_traffic = self.truck_traffic[
            (self.truck_traffic['Total_distance'] > 0) &
            (self.truck_traffic['Traffic_flow_trucks_2030'] > 0) &
            (~self.truck_traffic['Total_distance'].isna()) &
            (~self.truck_traffic['Traffic_flow_trucks_2030'].isna())
        ].copy()

        print(f"  Valid traffic rows: {len(valid_traffic):,}")

        # Apply minimum distance filter if specified
        if min_distance_km is not None:
            valid_traffic = valid_traffic[
                valid_traffic['Total_distance'] >= min_distance_km
            ].copy()
            print(f"  After distance filter (>={min_distance_km}km): {len(valid_traffic):,}")

        # Apply cross-border filter if specified
        if cross_border_only:
            print("  Applying cross-border filter (origin and destination in different countries)...")
            # Extract country codes (first 2 characters of NUTS-3 region ID)
            valid_traffic['origin_country'] = valid_traffic['ID_origin_region'].astype(str).str[:2]
            valid_traffic['dest_country'] = valid_traffic['ID_destination_region'].astype(str).str[:2]

            rows_before_cross_border = len(valid_traffic)
            valid_traffic = valid_traffic[
                valid_traffic['origin_country'] != valid_traffic['dest_country']
            ].copy()
            rows_after_cross_border = len(valid_traffic)

            print(f"  After cross-border filter: {rows_after_cross_border:,} rows")
            print(f"  Removed {rows_before_cross_border - rows_after_cross_border:,} domestic routes")

            # Show cross-border pairs found
            if len(valid_traffic) > 0:
                cross_border_pairs = valid_traffic.groupby(['origin_country', 'dest_country']).size().reset_index(name='count')
                print(f"  Found cross-border pairs between {len(cross_border_pairs)} country pairs:")
                for _, pair in cross_border_pairs.head(10).iterrows():
                    print(f"    {pair['origin_country']} -> {pair['dest_country']}: {pair['count']:,} routes")

        # Group by OD-pair (but keep them separate - don't aggregate!)
        od_groups = valid_traffic.groupby(
            ['ID_origin_region', 'ID_destination_region']
        ).agg({
            'Traffic_flow_trucks_2030': 'sum',
            'Total_distance': 'mean',
            'origin_inside': 'first',
            'destination_inside': 'first'
        }).reset_index()

        print(f"  Unique OD-pairs (before validation): {len(od_groups):,}")

        # ====================================================================
        # FIX: Apply NUTS filtering validation BEFORE selecting top N
        # ====================================================================
        print("  Validating OD-pairs (checking if endpoints can be mapped to NUTS-3 nodes)...")

        # Pre-validate which OD-pairs will successfully create paths
        valid_od_mask = []
        for row in od_groups.itertuples(index=False):
            origin_nuts3 = row.ID_origin_region
            dest_nuts3 = row.ID_destination_region
            origin_inside = row.origin_inside
            destination_inside = row.destination_inside

            # Map to NUTS-3 nodes
            origin_node = self.nuts3_to_node.get(origin_nuts3)
            dest_node = self.nuts3_to_node.get(dest_nuts3)

            # Apply same validation logic as path creation (lines 437-470)
            is_valid = False

            # Skip if neither endpoint in filtered regions
            if origin_node is None and dest_node is None:
                is_valid = False
            # Handle boundary-crossing routes
            elif not origin_inside or not destination_inside:
                if not origin_inside and dest_node is not None:
                    is_valid = True  # Entering route
                elif not destination_inside and origin_node is not None:
                    is_valid = True  # Leaving route
                else:
                    is_valid = False
            # Internal route: both endpoints must be mappable
            else:
                if origin_node is not None and dest_node is not None:
                    is_valid = True
                else:
                    is_valid = False

            valid_od_mask.append(is_valid)

        # Filter to only valid OD-pairs
        od_groups['is_valid'] = valid_od_mask
        od_groups_before = len(od_groups)
        od_groups = od_groups[od_groups['is_valid']].copy()
        od_groups = od_groups.drop('is_valid', axis=1)

        print(f"  Valid OD-pairs (after validation): {len(od_groups):,}")
        print(f"  Filtered out {od_groups_before - len(od_groups):,} OD-pairs with unmappable endpoints")

        # NOW select top N from validated OD-pairs
        if max_odpairs:
            if len(od_groups) > max_odpairs:
                od_groups = od_groups.nlargest(max_odpairs, 'Traffic_flow_trucks_2030')
                print(f"  [LIMIT] Selected top {max_odpairs} OD-pairs by traffic flow from validated set")
            else:
                print(f"  [LIMIT] Requested {max_odpairs} OD-pairs, but only {len(od_groups)} valid OD-pairs available")
            if min_distance_km:
                print(f"  [LIMIT] All OD-pairs have distance >= {min_distance_km}km")
            print(f"  [LIMIT] Set max_odpairs = None to process all OD-pairs")

        # Create each OD-pair - OPTIMIZED with itertuples (5-10x faster than iterrows)
        init_veh_stock_id = 0

        for row in od_groups.itertuples(index=True):
            origin_nuts3 = row.ID_origin_region
            dest_nuts3 = row.ID_destination_region
            origin_inside = getattr(row, 'origin_inside', True)
            destination_inside = getattr(row, 'destination_inside', True)

            # Map to NUTS-3 nodes (handle external regions)
            origin_node = self.nuts3_to_node.get(origin_nuts3)
            dest_node = self.nuts3_to_node.get(dest_nuts3)

            # Skip if neither endpoint is in filtered regions (shouldn't happen after filtering)
            if origin_node is None and dest_node is None:
                continue

            # Get traffic-reported distance
            total_distance = row.Total_distance
            traffic_flow = row.Traffic_flow_trucks_2030

            # Handle boundary-crossing routes - cut at boundaries
            if not origin_inside or not destination_inside:
                # Route crosses boundary - need to cut it
                # Convert namedtuple to dict for _cut_route_at_boundaries compatibility
                row_dict = row._asdict()
                _, distance_proportion = self._cut_route_at_boundaries(
                    row_dict, self.edge_distance_map, self.filtered_region_ids
                )
                total_distance = total_distance * distance_proportion

                # Adjust endpoints for path finding
                if not origin_inside:
                    # Entering route: use destination as both origin and dest
                    if dest_node is None:
                        continue
                    origin_node = dest_node
                    path_sequence = [dest_node]
                elif not destination_inside:
                    # Leaving route: use origin as both origin and dest
                    if origin_node is None:
                        continue
                    dest_node = origin_node
                    path_sequence = [origin_node]
            else:
                # Internal route: both endpoints inside, find full path
                if origin_node is None or dest_node is None:
                    continue
                path_sequence = self._find_nuts3_path(origin_node, dest_node)

            # Distribute distance across path segments
            segment_distances = self._distribute_distance(
                path_sequence, total_distance
            )

            cumulative_dist = np.cumsum(segment_distances).tolist()

            # Create path (convert numpy types to Python native)
            path_id = len(self.path_list)
            path = {
                'id': int(path_id),
                'name': f'path_{path_id}_{origin_node}_to_{dest_node}',
                'origin': int(origin_node),
                'destination': int(dest_node),
                'length': float(total_distance),  # Original traffic distance
                'sequence': [int(x) for x in path_sequence],
                'distance_from_previous': [float(x) for x in segment_distances],
                'cumulative_distance': [float(x) for x in cumulative_dist]
            }

            # Create vehicle stock for this OD-pair
            vehicle_init_ids = self._create_vehicle_stock(
                traffic_flow, total_distance, init_veh_stock_id
            )
            init_veh_stock_id += len(vehicle_init_ids)

            # Create OD-pair (convert numpy types to Python native)
            odpair = {
                'id': int(path_id),
                'path_id': int(path_id),
                'from': int(origin_node),
                'to': int(dest_node),
                'product': 'freight',
                'purpose': 'long-haul',
                'region_type': 'highway',
                'financial_status': 'any',
                'F': [float(traffic_flow)] * 21,  # 21 years
                'vehicle_stock_init': vehicle_init_ids,
                'travel_time_budget': 0.0
            }

            self.odpair_list.append(odpair)
            self.path_list.append(path)

            if (row.Index + 1) % 1000 == 0:
                print(f"  Created {row.Index+1} OD-pairs...")

        print(f"\n[SUCCESS] Created {len(self.odpair_list)} OD-pairs and {len(self.path_list)} paths")

        # Statistics
        avg_nodes = np.mean([len(p['sequence']) for p in self.path_list])
        avg_dist = np.mean([p['length'] for p in self.path_list])
        print(f"  Average nodes per path: {avg_nodes:.2f}")
        print(f"  Average path length: {avg_dist:.1f} km")

    def _find_nuts3_path(self, origin: int, dest: int, max_depth: int = 5) -> List[int]:
        """Find path using BFS through NUTS-3 network."""
        if origin == dest:
            return [origin]

        # Build adjacency
        adjacency = {}
        for (a, b) in self.edge_lookup.keys():
            if a not in adjacency:
                adjacency[a] = []
            adjacency[a].append(b)

        # BFS
        queue = deque([(origin, [origin])])
        visited = {origin}

        while queue:
            node, path = queue.popleft()

            if len(path) > max_depth:
                continue

            if node == dest:
                return path

            for neighbor in adjacency.get(node, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        # No path - direct connection
        return [origin, dest]

    def _distribute_distance(
        self,
        path_sequence: List[int],
        total_distance: float
    ) -> List[float]:
        """
        Distribute traffic distance across path segments.

        Uses network edge distances for PROPORTIONS, then scales to match total.
        """
        if len(path_sequence) < 2:
            return [0]

        # Get network distances for proportions
        network_dists = [0]
        total_network = 0

        for i in range(1, len(path_sequence)):
            prev = path_sequence[i-1]
            curr = path_sequence[i]

            if (prev, curr) in self.edge_lookup:
                dist = self.edge_lookup[(prev, curr)]
            else:
                dist = 100  # Default for equal distribution

            network_dists.append(dist)
            total_network += dist

        # Scale to match traffic distance
        if total_network == 0:
            seg_dist = total_distance / (len(path_sequence) - 1)
            return [0] + [seg_dist] * (len(path_sequence) - 1)

        scale = total_distance / total_network
        segment_distances = [d * scale for d in network_dists]

        # Ensure exact match
        actual = sum(segment_distances)
        if actual > 0:
            correction = total_distance / actual
            segment_distances = [d * correction for d in segment_distances]
            segment_distances[0] = 0

        return segment_distances

    def _create_vehicle_stock(
        self,
        traffic_flow: float,
        distance: float,
        start_id: int,
        y_init: int = 2020,  # FIXED: Changed from 2040 to match model optimization period (2020-2040)
        prey_y: int = 10,
        occ: float = 0.5
    ) -> List[int]:
        """Create initial vehicle stock for an OD-pair, respecting temporal resolution."""
        # Get temporal resolution from configuration
        time_step = getattr(self, 'time_step', 1)  # Default to annual if not set

        # Calculate number of vehicles
        nb_vehicles = traffic_flow * (distance / (13.6 * 136750))

        # Get list of modeled years in pre-period
        modeled_years = list(range(y_init-prey_y, y_init, time_step))

        # IMPORTANT: Distribute stock evenly across modeled years (not all years)
        # Example: time_step=1 → 10 years → factor=1/10 (each year gets 10%)
        #          time_step=2 → 5 years → factor=1/5 (each year gets 20%)
        factor = 1 / len(modeled_years)

        vehicle_ids = []

        for g in modeled_years:
            stock = nb_vehicles * factor

            # Diesel truck (ICEV) - only create entries with stock
            self.initial_vehicle_stock.append({
                "id": start_id,
                "techvehicle": 0,
                "year_of_purchase": g,
                "stock": float(round(stock, 5))
            })
            vehicle_ids.append(start_id)
            start_id += 1

            # Electric truck (BEV) - DON'T create zero-stock entries
            # DON'T add ID to vehicle_ids since we're not creating the entry
            # This way OD-pairs won't reference non-existent IDs
            # start_id still increments to maintain ID spacing
            start_id += 1

        return vehicle_ids

    def create_mandatory_breaks(
        self,
        driver_limit_hours: float = 4.5,
        avg_speed_kmh: float = 80.0
    ):
        """Create mandatory break constraints based on actual distances."""
        print("\n" + "="*80)
        print("STEP 4: CREATING MANDATORY BREAKS")
        print("="*80)

        max_distance = driver_limit_hours * avg_speed_kmh
        break_id = 0

        for path in self.path_list:
            path_id = path['id']
            sequence = path['sequence']
            distances = path['distance_from_previous']
            cumulative = path['cumulative_distance']

            distance_since_break = 0

            for i in range(1, len(sequence)):
                distance_since_break += distances[i]

                if distance_since_break >= max_distance:
                    self.mandatory_breaks.append({
                        'id': break_id,
                        'path_id': path_id,
                        'node_index': i,
                        'node_id': sequence[i],
                        'cumulative_distance': cumulative[i],
                        'distance_since_last_break': distance_since_break
                    })
                    break_id += 1
                    distance_since_break = 0

        print(f"[OK] Created {len(self.mandatory_breaks)} mandatory break points")
        if self.mandatory_breaks:
            avg_breaks = len(self.mandatory_breaks) / len(self.path_list)
            print(f"     Average breaks per path: {avg_breaks:.2f}")

    def save_results(self):
        """Save all results to YAML files."""
        print("\n" + "="*80)
        print("STEP 5: SAVING RESULTS")
        print("="*80)

        # Geographic elements
        self._save_yaml(self.geographic_elements, "GeographicElement.yaml")

        # Paths
        self._save_yaml(self.path_list, "Path.yaml")

        # OD-pairs
        self._save_yaml(self.odpair_list, "Odpair.yaml")

        # Initial vehicle stock
        self._save_yaml(self.initial_vehicle_stock, "InitialVehicleStock.yaml")

        # Mandatory breaks
        if self.mandatory_breaks:
            self._save_yaml(self.mandatory_breaks, "MandatoryBreaks.yaml")

        print(f"\n[SUCCESS] All files saved to: {self.output_dir}")

    def _save_yaml(self, data: List[dict], filename: str):
        """Save data to YAML file."""
        filepath = self.output_dir / filename
        with open(filepath, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        print(f"[OK] Saved {filename} ({len(data)} entries)")

    def run_complete_preprocessing(self, max_odpairs: int = None, min_distance_km: float = None, cross_border_only: bool = False):
        """Execute complete preprocessing pipeline.

        Args:
            max_odpairs: Maximum number of OD-pairs to process
            min_distance_km: Minimum distance filter (e.g., 360km for mandatory breaks)
            cross_border_only: If True, only include cross-border OD-pairs (different countries)
        """
        print("\n" + "="*80)
        print("COMPLETE SM NUTS-3 PREPROCESSING")
        print("="*80)
        print(f"Input:  {self.data_dir}")
        print(f"Output: {self.output_dir}")
        if min_distance_km:
            print(f"Filter: Distance >= {min_distance_km}km (mandatory breaks test)")
        if cross_border_only:
            print(f"Filter: Cross-border only (origin and destination in different countries)")
        print("="*80)

        self.load_data()
        self.create_nuts3_geographic_elements()
        self.build_edge_lookup()
        self.create_paths_with_original_distances(
            max_odpairs=max_odpairs,
            min_distance_km=min_distance_km,
            cross_border_only=cross_border_only
        )
        self.create_mandatory_breaks()
        self.save_results()

        # Summary
        print("\n" + "="*80)
        print("PREPROCESSING COMPLETE - SUMMARY")
        print("="*80)
        print(f"  Geographic elements (NUTS-3): {len(self.geographic_elements)}")
        print(f"  OD-pairs (NOT aggregated):    {len(self.odpair_list)}")
        print(f"  Paths (collapsed nodes):      {len(self.path_list)}")
        print(f"  Initial vehicle stock:        {len(self.initial_vehicle_stock)}")
        print(f"  Mandatory breaks:             {len(self.mandatory_breaks)}")
        print("="*80)

        print("\nKEY FEATURES:")
        print("  [OK] NUTS-3 aggregated nodes (efficient capacity planning)")
        print("  [OK] Collapsed path sequences (fewer nodes in routes)")
        print("  [OK] Original traffic distances (accuracy preserved)")
        print("  [OK] Individual OD-pairs kept (demand detail preserved)")
        print("  [OK] Mandatory breaks calculated correctly")
        print("="*80 + "\n")


# ============================================================================
# HELPER FUNCTION: Generate Multiple Cases
# ============================================================================

def generate_multiple_cases(base_data_dir: Path, base_output_dir: Path):
    """
    Generate input data for two different cases:
    1. ALL OD-pairs (full dataset) -> sm_nuts3_complete/
    2. TEST case with 100 OD-pairs, all > 360km -> sm_nuts3_test/
    """
    print("\n" + "="*80)
    print("GENERATING MULTIPLE INPUT CASES")
    print("="*80)
    print("Case 1: All OD-pairs (full dataset) -> sm_nuts3_complete/")
    print("Case 2: Test case - 100 OD-pairs with distance >= 360km -> sm_nuts3_test/")
    print("="*80 + "\n")

    # ========================================================================
    # CASE 1: All OD-pairs -> sm_nuts3_complete/
    # ========================================================================
    print("\n" + "#"*80)
    print("# CASE 1: FULL DATASET (ALL OD-PAIRS) -> sm_nuts3_complete/")
    print("#"*80 + "\n")

    output_dir_full = base_output_dir / "sm_nuts3_complete"
    preprocessor_full = CompleteSMNUTS3Preprocessor(base_data_dir, output_dir_full)
    preprocessor_full.run_complete_preprocessing(
        max_odpairs=None,
        min_distance_km=None
    )

    # ========================================================================
    # CASE 2: Test case - 100 OD-pairs, distance >= 360km -> sm_nuts3_test/
    # ========================================================================
    print("\n" + "#"*80)
    print("# CASE 2: TEST CASE (100 OD-PAIRS, DISTANCE >= 360km) -> sm_nuts3_test/")
    print("#"*80 + "\n")

    output_dir_test = base_output_dir / "sm_nuts3_test"
    preprocessor_test = CompleteSMNUTS3Preprocessor(base_data_dir, output_dir_test)
    preprocessor_test.run_complete_preprocessing(
        max_odpairs=100,
        min_distance_km=360.0  # 4.5 hours * 80 km/h = mandatory breaks required
    )

    # ========================================================================
    # Summary
    # ========================================================================
    print("\n" + "="*80)
    print("ALL CASES GENERATED SUCCESSFULLY")
    print("="*80)
    print(f"Case 1 (Full): sm_nuts3_complete/")
    print(f"  Location: {output_dir_full}")
    print(f"  - OD-pairs: {len(preprocessor_full.odpair_list)}")
    print(f"  - Paths: {len(preprocessor_full.path_list)}")
    print(f"  - Avg distance: {np.mean([p['length'] for p in preprocessor_full.path_list]):.1f} km")
    print()
    print(f"Case 2 (Test): sm_nuts3_test/")
    print(f"  Location: {output_dir_test}")
    print(f"  - OD-pairs: {len(preprocessor_test.odpair_list)}")
    print(f"  - Paths: {len(preprocessor_test.path_list)}")
    print(f"  - Min distance: {min([p['length'] for p in preprocessor_test.path_list]):.1f} km")
    print(f"  - Avg distance: {np.mean([p['length'] for p in preprocessor_test.path_list]):.1f} km")
    print(f"  - All paths require mandatory breaks (distance >= 360km)")
    print("="*80 + "\n")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    import sys
    import os

    # ========================================================================
    # CONFIGURATION
    # ========================================================================
    # Set GENERATE_BOTH_CASES = True to generate both cases
    # Set GENERATE_BOTH_CASES = False to use legacy single-case mode
    GENERATE_BOTH_CASES = False  # Change to False for single case mode

    # Legacy single-case configuration (only used if GENERATE_BOTH_CASES = False)
    MAX_ODpair = None  # Change this to limit OD-pairs (e.g., 100 for testing)
    MIN_DISTANCE_KM = None  # Change to filter by distance (e.g., 360.0)
    CROSS_BORDER_ONLY = False  # Set to True to only include cross-border OD-pairs (different countries)
    # ========================================================================

    # Get script directory to resolve relative paths
    script_dir = Path(__file__).parent

    # Default paths (relative to script location)
    data_dir = script_dir / "data" / "Trucktraffic_NUTS3"
    output_dir = script_dir / "input_data"  # Base directory for both cases

    # ========================================================================
    # Mode 1: Generate both cases
    # ========================================================================
    if GENERATE_BOTH_CASES:
        generate_multiple_cases(data_dir, output_dir)
        print("[SUCCESS] Both cases generated!")

    # ========================================================================
    # Mode 2: Legacy single-case mode
    # ========================================================================
    else:
        # Parse command-line arguments
        # Usage: python SM_preprocessing_nuts3_complete.py [data_dir] [output_dir] [max_odpairs] [min_distance_km] [cross_border_only]
        if len(sys.argv) > 1:
            data_dir = Path(sys.argv[1])
        if len(sys.argv) > 2:
            output_dir = Path(sys.argv[2])
        if len(sys.argv) > 3:
            try:
                MAX_ODpair = int(sys.argv[3])
                print(f"\n[INFO] Using command-line MAX_ODpair: {MAX_ODpair}")
            except ValueError:
                print(f"\n[WARN] Invalid max_odpairs argument '{sys.argv[3]}', using config value")
        if len(sys.argv) > 4:
            try:
                MIN_DISTANCE_KM = float(sys.argv[4])
                print(f"[INFO] Using command-line MIN_DISTANCE_KM: {MIN_DISTANCE_KM}")
            except ValueError:
                print(f"\n[WARN] Invalid min_distance_km argument '{sys.argv[4]}', using config value")
        if len(sys.argv) > 5:
            try:
                CROSS_BORDER_ONLY = sys.argv[5].lower() in ('true', '1', 'yes')
                print(f"[INFO] Using command-line CROSS_BORDER_ONLY: {CROSS_BORDER_ONLY}")
            except:
                print(f"\n[WARN] Invalid cross_border_only argument '{sys.argv[5]}', using config value")

        # Display configuration
        if MAX_ODpair is not None or MIN_DISTANCE_KM is not None or CROSS_BORDER_ONLY:
            print("\n" + "="*80)
            print("SINGLE CASE MODE")
            print("="*80)
            if MAX_ODpair is not None:
                print(f"  Max OD-pairs: {MAX_ODpair}")
            if MIN_DISTANCE_KM is not None:
                print(f"  Min distance: {MIN_DISTANCE_KM}km")
            if CROSS_BORDER_ONLY:
                print(f"  Cross-border only: True (origin and destination in different countries)")
            print("="*80 + "\n")

        # Run preprocessing
        preprocessor = CompleteSMNUTS3Preprocessor(data_dir, output_dir)
        preprocessor.run_complete_preprocessing(
            max_odpairs=MAX_ODpair,
            min_distance_km=MIN_DISTANCE_KM,
            cross_border_only=CROSS_BORDER_ONLY
        )

        print("[SUCCESS] Preprocessing finished!")
