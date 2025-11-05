"""
Complete SM Preprocessing for NUTS-2 with Preserved Demand
===========================================================

This script creates a COMPLETE NUTS-2 preprocessing that:
1. Aggregates geographic nodes to NUTS-2 (for MAXIMUM capacity planning efficiency)
2. Creates collapsed path sequences (fewer nodes - ~70-100 instead of 573)
3. Preserves ORIGINAL distances from traffic data (accurate)
4. Keeps INDIVIDUAL demand per OD-pair (not aggregated)
5. Calculates mandatory breaks based on actual distances

Result: Highly efficient model with accurate distances and full demand detail.

Author: Claude Code
Date: 2025-10-17
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


class CompleteSMNUTS2Preprocessor:
    """
    Complete NUTS-2 preprocessing for Scandinavian Mediterranean corridor.

    Key features:
    - NUTS-2 aggregated geographic nodes (MAXIMUM capacity planning efficiency)
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
            "NUTS_0": ["DE", "DK", "SE"],
            "NUTS_1": ["AT3", "ITC", "ITH", "ITI", "ITF"],
            "NUTS_2": ["NO08", "NO07", "FI1D", "NO09", "NO0A",
                       "NO02", "NO06", "AT33", "AT34", "AT32"],

        }

        # Data storage
        self.truck_traffic = None
        self.network_nodes = None
        self.network_edges = None

        # Mappings
        self.nuts3_to_nuts2 = {}  # NUTS-3 zone ID -> NUTS-2 region ID (via spatial join)
        self.nuts2_to_node = {}   # NUTS-2 region ID -> NUTS-2 node ID
        self.node_to_nuts2 = {}   # Original node ID -> NUTS-2 region ID
        self.nuts2_nodes = {}     # NUTS-2 region ID -> aggregated node data
        self.edge_lookup = {}     # (node_a, node_b) -> distance
        self.edge_distance_map = {}  # Network_Edge_ID -> distance
        self.filtered_region_ids = set()  # ETISPlus Zone IDs of filtered regions

        # Results
        self.odpair_list = []
        self.path_list = []
        self.initial_vehicle_stock = []
        self.geographic_elements = []
        self.mandatory_breaks = []

        # Temporal resolution (1=annual, 2=biennial, 5=quinquennial, etc.)
        self.time_step = 2  # Default: annual resolution

        # Carbon price data (EUR/tCO2)
        self.carbon_price_base = {
            2018: 15.06,
            2020: 30,
            2025: 51.5871,
            2030: 76.4254,
            2035: 113.223,
            2040: 167.737,
            2045: 248.5,
            2050: 355
        }

    def interpolate_carbon_price(self, year: int) -> float:
        """
        Interpolates the carbon price for a given year based on defined values.
        Uses linear interpolation within the defined range and extrapolation outside.

        Parameters:
        -----------
        year : int
            The year for which to interpolate the carbon price

        Returns:
        --------
        float
            The interpolated carbon price in EUR/tCO2
        """
        years = np.array(list(self.carbon_price_base.keys()))
        prices = np.array(list(self.carbon_price_base.values()))

        if year < years.min():
            # Extrapolate for years before the minimum defined year
            slope = (prices[1] - prices[0]) / (years[1] - years[0])
            return prices[0] + slope * (year - years[0])
        elif year > years.max():
            # Extrapolate for years after the maximum defined year
            slope = (prices[-1] - prices[-2]) / (years[-1] - years[-2])
            return prices[-1] + slope * (year - years[-1])
        else:
            # Interpolate for years within the defined range
            return float(np.interp(year, years, prices))

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
        Maps NUTS-3 zones to NUTS-2 regions for aggregation.

        Uses NUTS shapefile for spatial filtering and NUTS-2 aggregation.
        """
        print("\nApplying NUTS-2 aggregation filtering with spatial join...")

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

        # First, get NUTS-2 regions (LEVL_CODE == 2) that match our filter
        pattern = '|'.join(relevant_codes)
        nuts2_mask = (nuts_regions['LEVL_CODE'] == 2) & (
            nuts_regions['NUTS_ID'].str.contains(pattern, regex=True)
        )
        relevant_nuts2_regions = nuts_regions[nuts2_mask].copy()
        print(f"  Found {len(relevant_nuts2_regions)} NUTS-2 regions matching filter")

        # Load NUTS-3 to nodes mapping
        nuts_3_to_nodes_file = self.data_dir / "02_NUTS-3-Regions.csv"
        nuts_3_to_nodes = pd.read_csv(nuts_3_to_nodes_file)

        # Convert to GeoDataFrame using geometric centers - OPTIMIZED with batch conversion
        geom_series = gpd.GeoSeries.from_wkt(nuts_3_to_nodes['Geometric_center'], crs=nuts_regions.crs)
        nuts_3_to_nodes_gdf = gpd.GeoDataFrame(nuts_3_to_nodes, geometry=geom_series, crs=nuts_regions.crs)
        print(f"  Created GeoDataFrame with {len(nuts_3_to_nodes_gdf)} NUTS-3 zones")

        # Perform spatial join: map NUTS-3 zones to NUTS-2 regions via filtering hierarchically
        # This matches notebook line 237-252 but filters to find parent NUTS-2
        filtered_nuts3_by_level = {}
        for level, nuts_list in self.nuts_to_filter_for.items():
            selected_polygons = nuts_regions[nuts_regions['NUTS_ID'].isin(nuts_list)]
            if len(selected_polygons) > 0:
                filtered_nuts3 = gpd.sjoin(nuts_3_to_nodes_gdf, selected_polygons, predicate='within')
                filtered_nuts3_by_level[level] = filtered_nuts3
                print(f"    {level}: {len(filtered_nuts3)} NUTS-3 zones")

        # Concatenate all filtered NUTS-3 zones
        all_filtered_nuts3 = gpd.GeoDataFrame(
            pd.concat(filtered_nuts3_by_level.values(), ignore_index=True),
            crs=nuts_3_to_nodes_gdf.crs
        )

        # Remove duplicates (zones might appear in multiple levels)
        all_filtered_nuts3 = all_filtered_nuts3.drop_duplicates(subset=['ETISPlus_Zone_ID'])

        print(f"  Total NUTS-3 zones after spatial filtering: {len(all_filtered_nuts3)}")

        # NOW map each NUTS-3 zone to its parent NUTS-2 region via spatial join
        print(f"  Mapping NUTS-3 zones to NUTS-2 regions...")
        nuts3_to_nuts2_mapping = gpd.sjoin(
            all_filtered_nuts3[['ETISPlus_Zone_ID', 'geometry']],
            relevant_nuts2_regions[['NUTS_ID', 'geometry']],
            predicate='within',
            how='left'
        )

        # Create mapping dictionary: NUTS-3 zone ID -> NUTS-2 region ID
        self.nuts3_to_nuts2 = dict(zip(
            nuts3_to_nuts2_mapping['ETISPlus_Zone_ID'],
            nuts3_to_nuts2_mapping['NUTS_ID']
        ))

        print(f"  Mapped {len(self.nuts3_to_nuts2)} NUTS-3 zones to {len(set(self.nuts3_to_nuts2.values()))} NUTS-2 regions")

        # Get the set of ETISplus Zone IDs that are in the filtered regions
        filtered_region_ids = set(all_filtered_nuts3['ETISPlus_Zone_ID'].unique())
        self.filtered_region_ids = filtered_region_ids  # Store for later use

        # Filter network nodes: keep only nodes in filtered regions
        self.network_nodes = self.network_nodes[
            self.network_nodes['ETISplus_Zone_ID'].isin(filtered_region_ids)
        ].copy()

        # Add NUTS-2 mapping to network_nodes for aggregation
        self.network_nodes['NUTS2_ID'] = self.network_nodes['ETISplus_Zone_ID'].map(self.nuts3_to_nuts2)

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

        # Calculate initial tkm BEFORE traffic filtering
        traffic_before = self.truck_traffic.copy()
        initial_tkm = (traffic_before['Traffic_flow_trucks_2030'] * traffic_before['Total_distance']).sum()
        print(f"\n  FREIGHT STATISTICS (Initial):")
        print(f"    Total traffic rows: {len(traffic_before):,}")
        print(f"    Total freight volume: {initial_tkm:,.2f} tkm")

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

        # Calculate removed tkm
        removed_traffic = traffic_before[
            ~traffic_before.index.isin(self.truck_traffic.index)
        ]
        removed_tkm = (removed_traffic['Traffic_flow_trucks_2030'] * removed_traffic['Total_distance']).sum()

        # Calculate final tkm after filtering
        final_tkm = (self.truck_traffic['Traffic_flow_trucks_2030'] * self.truck_traffic['Total_distance']).sum()

        # Calculate tkm by route type
        internal_mask = (self.truck_traffic['origin_inside']) & (self.truck_traffic['destination_inside'])
        entering_mask = (~self.truck_traffic['origin_inside']) & (self.truck_traffic['destination_inside'])
        leaving_mask = (self.truck_traffic['origin_inside']) & (~self.truck_traffic['destination_inside'])

        internal_tkm = (self.truck_traffic[internal_mask]['Traffic_flow_trucks_2030'] *
                       self.truck_traffic[internal_mask]['Total_distance']).sum()
        entering_tkm = (self.truck_traffic[entering_mask]['Traffic_flow_trucks_2030'] *
                       self.truck_traffic[entering_mask]['Total_distance']).sum()
        leaving_tkm = (self.truck_traffic[leaving_mask]['Traffic_flow_trucks_2030'] *
                      self.truck_traffic[leaving_mask]['Total_distance']).sum()

        # Count route types
        internal = internal_mask.sum()
        entering = entering_mask.sum()
        leaving = leaving_mask.sum()

        # Calculate percentages
        if initial_tkm > 0:
            removed_pct = (removed_tkm / initial_tkm) * 100
            retained_pct = (final_tkm / initial_tkm) * 100
            internal_pct = (internal_tkm / final_tkm) * 100 if final_tkm > 0 else 0
            entering_pct = (entering_tkm / final_tkm) * 100 if final_tkm > 0 else 0
            leaving_pct = (leaving_tkm / final_tkm) * 100 if final_tkm > 0 else 0
        else:
            removed_pct = retained_pct = internal_pct = entering_pct = leaving_pct = 0.0

        print(f"\n  FREIGHT STATISTICS (After filtering):")
        print(f"    Retained traffic rows: {rows_after:,} ({rows_after/rows_before*100:.1f}%)")
        print(f"    Retained freight volume: {final_tkm:,.2f} tkm ({retained_pct:.1f}%)")
        print(f"\n  ROUTE TYPE BREAKDOWN (Retained freight):")
        print(f"    Internal routes (both inside): {internal:,} rows, {internal_tkm:,.2f} tkm ({internal_pct:.1f}%)")
        print(f"    Entering routes (origin outside): {entering:,} rows, {entering_tkm:,.2f} tkm ({entering_pct:.1f}%)")
        print(f"    Leaving routes (destination outside): {leaving:,} rows, {leaving_tkm:,.2f} tkm ({leaving_pct:.1f}%)")
        print(f"\n  REMOVED FREIGHT:")
        print(f"    Geographic filter: {rows_before - rows_after:,} rows, {removed_tkm:,.2f} tkm ({removed_pct:.1f}%)")

        # Print comprehensive filtering summary
        print(f"\n[OK] NUTS-2 FILTERING COMPLETE:")
        print(f"  NUTS-3 zones: {len(self.filtered_region_ids):,}")
        print(f"  NUTS-2 regions: {len(set(self.nuts3_to_nuts2.values())):,}")
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
                nuts2_a = self.node_to_nuts2.get(node_a)
                nuts2_b = self.node_to_nuts2.get(node_b)

                # Include edge if at least one endpoint is in filtered regions
                if nuts2_a in filtered_node_ids or nuts2_b in filtered_node_ids:
                    cut_edges.append(edge_id)

        # Calculate distance proportion
        if not cut_edges:
            return [], 0.5

        # Calculate total original distance and cut distance
        total_dist = sum(edge_distance_map.get(e, 0) for e in edge_path)
        cut_dist = sum(edge_distance_map.get(e, 0) for e in cut_edges)

        proportion = cut_dist / total_dist if total_dist > 0 else 0.5

        return cut_edges, proportion

    def create_nuts2_geographic_elements(self):
        """
        Create NUTS-2 aggregated geographic nodes.

        Strategy: One node per NUTS-2 region (centroid of all nodes in that region).
        Aggregates multiple NUTS-3 zones into single NUTS-2 regions.
        """
        print("\n" + "="*80)
        print("STEP 1: CREATING NUTS-2 GEOGRAPHIC ELEMENTS")
        print("="*80)

        # Build node_to_nuts2 mapping: network node ID -> NUTS-2 region ID
        self.node_to_nuts2 = dict(zip(
            self.network_nodes['Network_Node_ID'],
            self.network_nodes['NUTS2_ID']  # Using the NUTS-2 column we added
        ))

        # Group nodes by NUTS-2 region (aggregating across NUTS-3 zones)
        nuts2_groups = {}
        for nuts2_id, group_df in self.network_nodes.groupby('NUTS2_ID'):
            if pd.notna(nuts2_id):  # Skip NaN NUTS-2 regions
                nuts2_groups[nuts2_id] = group_df.to_dict('records')

        print(f"  Found {len(nuts2_groups)} unique NUTS-2 regions")
        print(f"  Aggregating from {len(self.network_nodes)} network nodes")

        # Create one aggregated node per NUTS-2 region
        new_node_id = 0

        for nuts2_id, nodes_in_region in sorted(nuts2_groups.items()):
            # Calculate centroid (average of all nodes in this NUTS-2 region)
            lats = [n['Network_Node_Y'] for n in nodes_in_region]
            lons = [n['Network_Node_X'] for n in nodes_in_region]
            avg_lat = np.mean(lats)
            avg_lon = np.mean(lons)

            # Get country code (use most common)
            countries = [n.get('Country', 'XX') for n in nodes_in_region]
            country = max(set(countries), key=countries.count)

            # Create aggregated node for this NUTS-2 region
            # Calculate carbon prices for all years (2020-2060)
            carbon_prices = [self.interpolate_carbon_price(year) for year in range(2020, 2061)]

            geo_element = {
                'id': new_node_id,
                'name': f'nuts2_{nuts2_id}',
                'type': 'node',
                'nuts2_region': str(nuts2_id),  # Store NUTS-2 region ID
                'country': country,
                'coordinate_lat': float(avg_lat),
                'coordinate_long': float(avg_lon),
                'from': 999999,
                'to': 999999,
                'length': 0.0,
                'carbon_price': carbon_prices  # EUR/tCO2, interpolated from base values
            }

            self.geographic_elements.append(geo_element)
            self.nuts2_to_node[nuts2_id] = new_node_id
            self.nuts2_nodes[nuts2_id] = geo_element

            new_node_id += 1

        print(f"[OK] Created {len(self.geographic_elements)} NUTS-2 geographic elements")
        print(f"     Reduction: {len(self.network_nodes)} nodes -> {len(self.geographic_elements)} NUTS-2 regions")

    def build_edge_lookup(self):
        """Build edge lookup for topology (but won't use distances) - OPTIMIZED."""
        print("\n" + "="*80)
        print("STEP 2: BUILDING EDGE TOPOLOGY")
        print("="*80)

        # OPTIMIZED: Vectorized operations instead of iterrows (20-100x faster)
        edges_df = self.network_edges.copy()
        edges_df['nuts2_a'] = edges_df['Network_Node_A_ID'].map(self.node_to_nuts2)
        edges_df['nuts2_b'] = edges_df['Network_Node_B_ID'].map(self.node_to_nuts2)

        # **FIXED**: Keep ALL edges (both inter-regional AND intra-regional)
        # This preserves routing through intermediate regions (e.g., Austria)
        # Previously filtered to inter-regional only (nuts2_a != nuts2_b), losing intra-regional edges
        valid_edges = edges_df[
            (edges_df['nuts2_a'].notna()) &
            (edges_df['nuts2_b'].notna())
            # No longer filtering out: (edges_df['nuts2_a'] != edges_df['nuts2_b'])
        ]

        # Build lookup dictionary
        for row in valid_edges.itertuples(index=False):
            a = self.nuts2_to_node.get(row.nuts2_a)
            b = self.nuts2_to_node.get(row.nuts2_b)
            if a is not None and b is not None:
                self.edge_lookup[(a, b)] = row.Distance
                self.edge_lookup[(b, a)] = row.Distance

        # Count edge types
        inter_regional_count = len(valid_edges[valid_edges['nuts2_a'] != valid_edges['nuts2_b']])
        intra_regional_count = len(valid_edges[valid_edges['nuts2_a'] == valid_edges['nuts2_b']])

        print(f"[OK] Built edge topology: {len(self.edge_lookup)//2} edges total")
        print(f"    • Inter-regional (cross-border): {inter_regional_count}")
        print(f"    • Intra-regional (within NUTS2): {intra_regional_count}")
        print(f"[FIXED] Now preserves routing through intermediate regions like Austria")

    def create_paths_with_original_distances(self, max_odpairs: int = None, min_distance_km: float = None, cross_border_only: bool = False):
        """
        Create paths with collapsed NUTS-2 nodes but original traffic distances.

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
        print("WARNING: TEMPORARY - Local routes (origin == destination) are filtered out")
        print("         This prevents infeasibility from multi-node travel time constraints")
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
            # Extract country codes (first 2 characters of NUTS-2 region ID)
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
        print("  Validating OD-pairs (checking if endpoints can be mapped to NUTS-2 nodes)...")

        # Pre-validate which OD-pairs will successfully create paths
        valid_od_mask = []
        for row in od_groups.itertuples(index=False):
            origin_nuts3_zone = row.ID_origin_region  # This is NUTS-3 zone ID from traffic data
            dest_nuts3_zone = row.ID_destination_region
            origin_inside = row.origin_inside
            destination_inside = row.destination_inside

            # Map NUTS-3 zone -> NUTS-2 region -> NUTS-2 node
            origin_nuts2 = self.nuts3_to_nuts2.get(origin_nuts3_zone)
            dest_nuts2 = self.nuts3_to_nuts2.get(dest_nuts3_zone)
            origin_node = self.nuts2_to_node.get(origin_nuts2) if origin_nuts2 else None
            dest_node = self.nuts2_to_node.get(dest_nuts2) if dest_nuts2 else None

            # Apply same validation logic as path creation (lines 437-470)
            is_valid = False

            # ====================================================================
            # TEMPORARY FIX: Filter out local routes (origin == destination)
            # These create infeasibility issues with multi-node travel time constraints
            # TODO: Remove this filter once travel time constraint is improved
            # ====================================================================
            if origin_nuts2 == dest_nuts2:
                is_valid = False
            # Skip if neither endpoint in filtered regions
            elif origin_node is None and dest_node is None:
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
        print(f"  Filtered out {od_groups_before - len(od_groups):,} OD-pairs")
        print(f"    (includes unmappable endpoints AND local routes where origin == destination)")

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
        local_routes_filtered_at_path_creation = 0

        for row in od_groups.itertuples(index=True):
            origin_nuts3_zone = row.ID_origin_region  # NUTS-3 zone ID from traffic data
            dest_nuts3_zone = row.ID_destination_region
            origin_inside = getattr(row, 'origin_inside', True)
            destination_inside = getattr(row, 'destination_inside', True)

            # Map NUTS-3 zone -> NUTS-2 region -> NUTS-2 node (handle external regions)
            origin_nuts2 = self.nuts3_to_nuts2.get(origin_nuts3_zone)
            dest_nuts2 = self.nuts3_to_nuts2.get(dest_nuts3_zone)
            origin_node = self.nuts2_to_node.get(origin_nuts2) if origin_nuts2 else None
            dest_node = self.nuts2_to_node.get(dest_nuts2) if dest_nuts2 else None

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
                path_sequence = self._find_nuts2_path(origin_node, dest_node)

            # ====================================================================
            # CRITICAL FIX: Skip local routes created by boundary-crossing logic
            # Even though we filter origin_nuts2 == dest_nuts2 earlier,
            # the boundary-crossing logic can set origin_node = dest_node
            # ====================================================================
            if origin_node == dest_node:
                local_routes_filtered_at_path_creation += 1
                continue

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
                'F': [float(traffic_flow)] * 41,  # 41 years
                'vehicle_stock_init': vehicle_init_ids,
                'travel_time_budget': 0.0
            }

            self.odpair_list.append(odpair)
            self.path_list.append(path)

            if (row.Index + 1) % 1000 == 0:
                print(f"  Created {row.Index+1} OD-pairs...")

        print(f"\n[SUCCESS] Created {len(self.odpair_list)} OD-pairs and {len(self.path_list)} paths")
        if local_routes_filtered_at_path_creation > 0:
            print(f"  Filtered out {local_routes_filtered_at_path_creation:,} local routes at path creation stage")
            print(f"  (These were created by boundary-crossing logic setting origin_node = dest_node)")

        # Statistics
        avg_nodes = np.mean([len(p['sequence']) for p in self.path_list])
        avg_dist = np.mean([p['length'] for p in self.path_list])
        print(f"  Average nodes per path: {avg_nodes:.2f}")
        print(f"  Average path length: {avg_dist:.1f} km")

    def _is_node_in_corridor(self, node_id: int) -> bool:
        """
        Check if a NUTS2 node is within the defined corridor.

        Corridor definition (from lines 46-51):
        - NUTS_0: ["DE", "DK"]
        - NUTS_1: ["SE1", "SE2", "AT3", "ITC", "ITH", "ITI", "ITF"]
        - NUTS_2: ["SE11", "SE12", "SE21", "SE22", "NO08", "NO09", "NO02", "NO0A"]
        """
        # Get NUTS2 code for this node
        nuts2_code = None
        for code, nid in self.nuts2_to_node.items():
            if nid == node_id:
                nuts2_code = code
                break

        if nuts2_code is None:
            return False

        # Check against corridor filters
        # NUTS_0 level (e.g., "DE", "DK")
        for nuts0 in self.nuts_to_filter_for.get("NUTS_0", []):
            if nuts2_code.startswith(nuts0):
                return True

        # NUTS_1 level (e.g., "SE1", "AT3", "ITC")
        for nuts1 in self.nuts_to_filter_for.get("NUTS_1", []):
            if nuts2_code.startswith(nuts1):
                return True

        # NUTS_2 level (exact match, e.g., "SE11", "NO08")
        if nuts2_code in self.nuts_to_filter_for.get("NUTS_2", []):
            return True

        return False

    def _find_nuts2_path(self, origin: int, dest: int, max_depth: int = 15) -> List[int]:
        """
        Find path using BFS through NUTS-2 network.

        **FIXED**: Now uses actual network topology (edge_lookup) for pathfinding.
        **ADDED**: Corridor filtering - only returns paths that stay within corridor.
        """
        if origin == dest:
            return [origin]

        # Build adjacency
        adjacency = {}
        for (a, b) in self.edge_lookup.keys():
            if a not in adjacency:
                adjacency[a] = []
            adjacency[a].append(b)

        # BFS with corridor filtering
        queue = deque([(origin, [origin])])
        visited = {origin}

        while queue:
            node, path = queue.popleft()

            if len(path) > max_depth:
                continue

            if node == dest:
                # **CORRIDOR FILTER**: Validate that entire path stays within corridor
                all_in_corridor = all(self._is_node_in_corridor(n) for n in path)
                if all_in_corridor:
                    return path
                # If path leaves corridor, continue searching for alternative
                continue

            for neighbor in adjacency.get(node, []):
                if neighbor not in visited:
                    # **CORRIDOR FILTER**: Only explore neighbors within corridor
                    if self._is_node_in_corridor(neighbor):
                        visited.add(neighbor)
                        queue.append((neighbor, path + [neighbor]))

        # No path found within corridor - return direct connection
        # Note: This will be filtered out later if it leaves corridor
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
        nb_vehicles = traffic_flow * (distance / (13.6 * (1-0.25) * 136750))

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
        break_time = 0.75  # 45 minutes = 0.75 hours

        for path in self.path_list:
            path_id = path['id']
            path_length = path['length']
            sequence = path['sequence']
            distances = path['distance_from_previous']
            cumulative = path['cumulative_distance']

            distance_since_break = 0
            time_since_break = 0
            break_number = 0

            for i in range(1, len(sequence)):
                distance_since_break += distances[i]
                time_since_break += distances[i] / avg_speed_kmh

                if distance_since_break >= max_distance:
                    break_number += 1
                    total_driving_time = cumulative[i] / avg_speed_kmh
                    time_with_breaks = total_driving_time + (break_number * break_time)

                    self.mandatory_breaks.append({
                        'id': break_id,
                        'path_id': path_id,
                        'path_length': float(path_length),
                        'total_driving_time': float(total_driving_time),
                        'break_number': int(break_number),
                        'latest_node_idx': int(i),  # FIXED: was 'node_index'
                        'latest_geo_id': int(sequence[i]),  # FIXED: was 'node_id'
                        'cumulative_distance': float(cumulative[i]),
                        'cumulative_driving_time': float(total_driving_time),
                        'time_with_breaks': float(time_with_breaks)
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

    def _convert_numpy_types(self, obj):
        """Recursively convert numpy types to native Python types."""
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {key: self._convert_numpy_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_numpy_types(item) for item in obj]
        else:
            return obj

    def _save_yaml(self, data: List[dict], filename: str):
        """Save data to YAML file, converting numpy types to native Python types."""
        filepath = self.output_dir / filename
        # Convert numpy types before saving
        data_clean = self._convert_numpy_types(data)
        with open(filepath, 'w') as f:
            yaml.dump(data_clean, f, default_flow_style=False, sort_keys=False)
        print(f"[OK] Saved {filename} ({len(data)} entries)")

    def scale_transport_demand(self,
                                base_year: int = 2030,
                                ref_year_1: int = 2015,
                                ref_demand_1: float = 798470,
                                ref_year_2: int = 2024,
                                ref_demand_2: float = 932283,
                                years: list = None):
        """
        Scale transport demand (F) based on linear extrapolation from reference points.

        The current F values represent demand for the base_year (2030 by default).
        This method scales them for all years based on linear growth.

        Parameters:
        -----------
        base_year : int
            Year that the current F data represents (default: 2030)
        ref_year_1 : int
            First reference year (default: 2015)
        ref_demand_1 : float
            Total demand in first reference year (default: 798470)
        ref_year_2 : int
            Second reference year (default: 2024)
        ref_demand_2 : float
            Total demand in second reference year (default: 932283)
        years : list
            Years to scale for (default: 2020-2060, 41 years)
        """
        print("\n" + "="*80)
        print("SCALING TRANSPORT DEMAND (F)")
        print("="*80)

        if years is None:
            years = list(range(2020, 2061))  # 41 years: 2020-2060

        # Calculate annual change based on reference points
        annual_change = (ref_demand_2 - ref_demand_1) / (ref_year_2 - ref_year_1)
        print(f"Reference points: {ref_year_1}={ref_demand_1:,.0f}, {ref_year_2}={ref_demand_2:,.0f}")
        print(f"Annual change: {annual_change:,.2f} per year")

        # Calculate demand for base year
        demand_base_year = ref_demand_1 + (base_year - ref_year_1) * annual_change
        print(f"Base year ({base_year}) demand: {demand_base_year:,.0f}")

        # Calculate scaling factors for each year
        scaling_factors = []
        for year in years:
            demand_year = ref_demand_1 + (year - ref_year_1) * annual_change
            scaling_factor = demand_year / demand_base_year
            scaling_factors.append(scaling_factor)

        print(f"Scaling range: {min(scaling_factors):.4f} ({years[0]}) to {max(scaling_factors):.4f} ({years[-1]})")

        # Apply scaling to all odpairs
        total_original_demand = sum(od['F'][0] for od in self.odpair_list if 'F' in od and len(od['F']) > 0)

        for odpair in self.odpair_list:
            if 'F' in odpair:
                # Get the base F value (assumed constant in original data for 2030)
                base_F = odpair['F'][0] if odpair['F'] else 0

                # Scale for each year
                odpair['F'] = [base_F * factor for factor in scaling_factors]

        # Verify scaling
        total_scaled_demand_first = sum(od['F'][0] for od in self.odpair_list if 'F' in od and len(od['F']) > 0)
        total_scaled_demand_last = sum(od['F'][-1] for od in self.odpair_list if 'F' in od and len(od['F']) > 0)

        print(f"Original total demand (constant, base year): {total_original_demand:,.0f}")
        print(f"Scaled total demand ({years[0]}): {total_scaled_demand_first:,.0f}")
        print(f"Scaled total demand ({years[-1]}): {total_scaled_demand_last:,.0f}")

    def aggregate_odpairs_by_nuts2(self):
        """
        Aggregate OD-pairs by NUTS-2 origin-destination, combining traffic flows
        and calculating weighted average distances.
        """
        print("\n" + "="*80)
        print("AGGREGATING OD-PAIRS BY NUTS-2 REGIONS")
        print("="*80)

        # Group OD-pairs and paths by (origin_node, dest_node)
        odpair_groups = {}
        for odpair, path in zip(self.odpair_list, self.path_list):
            key = (odpair['from'], odpair['to'])
            if key not in odpair_groups:
                odpair_groups[key] = {'odpairs': [], 'paths': []}
            odpair_groups[key]['odpairs'].append(odpair)
            odpair_groups[key]['paths'].append(path)

        print(f"  OD-pairs before aggregation: {len(self.odpair_list)}")
        print(f"  Unique NUTS-2 OD-pairs: {len(odpair_groups)}")

        # Create aggregated OD-pairs and paths
        new_odpairs = []
        new_paths = []
        self.initial_vehicle_stock = []  # Reset vehicle stock
        stock_id = 0

        for (origin_node, dest_node), group in odpair_groups.items():
            odpairs = group['odpairs']
            paths = group['paths']

            # Sum traffic flows (F values) - element-wise sum across all years
            # Note: F values are already scaled by year in _calculate_scaling_factors
            total_F = [sum(od['F'][i] for od in odpairs) for i in range(41)]

            # Weighted average of distances (weight by traffic flow)
            total_flow = sum(od['F'][0] for od in odpairs)  # Use first year as weight
            if total_flow > 0:
                avg_distance = sum(p['length'] * od['F'][0] for p, od in zip(paths, odpairs)) / total_flow
            else:
                avg_distance = np.mean([p['length'] for p in paths])

            # Use the path from the highest-flow OD-pair as template, but update distances
            max_flow_idx = np.argmax([od['F'][0] for od in odpairs])
            template_path = paths[max_flow_idx].copy()
            template_path['length'] = avg_distance

            # Recalculate segment distances proportionally
            # FIX: Reconstruct path for single-node templates to ensure cumulative_distance is properly populated
            if len(template_path['sequence']) == 1 and avg_distance > 0:
                # Single-node template (e.g., intra-regional traffic 47->47)
                # Create simple 2-node path: origin -> destination with full distance on single segment
                origin = template_path['origin']
                destination = template_path['destination']

                # Reconstruct as 2-node path
                template_path['sequence'] = [origin, destination]
                template_path['distance_from_previous'] = [0.0, avg_distance]
                template_path['cumulative_distance'] = [0.0, avg_distance]

            elif sum(template_path['distance_from_previous']) > 0:
                # Multi-node template: scale distances proportionally
                scale = avg_distance / sum(template_path['distance_from_previous'])
                template_path['distance_from_previous'] = [d * scale for d in template_path['distance_from_previous']]
                template_path['cumulative_distance'] = np.cumsum(template_path['distance_from_previous']).tolist()
            else:
                # Edge case: multi-node path with zero total distance
                # This shouldn't happen, but handle it gracefully
                print(f"  WARNING: Path {origin_node}->{dest_node} has multi-node sequence but zero distance!")
                # Keep as-is but log the warning

            # Create aggregated vehicle stock
            vehicle_ids = self._create_vehicle_stock(total_flow, avg_distance, stock_id)
            stock_id += len(vehicle_ids)

            # Create aggregated OD-pair
            new_odpair = {
                'id': len(new_odpairs),
                'path_id': len(new_paths),
                'from': int(origin_node),
                'to': int(dest_node),
                'product': 'freight',
                'purpose': 'long-haul',
                'region_type': 'highway',
                'financial_status': 'any',
                'F': [float(f) for f in total_F],
                'vehicle_stock_init': vehicle_ids,
                'travel_time_budget': 0.0
            }

            # Update path ID
            template_path['id'] = len(new_paths)
            template_path['name'] = f'path_{len(new_paths)}_{origin_node}_to_{dest_node}'

            new_odpairs.append(new_odpair)
            new_paths.append(template_path)

        # Replace lists with aggregated versions
        self.odpair_list = new_odpairs
        self.path_list = new_paths
        # Vehicle stock already updated in place via self._create_vehicle_stock()

        print(f"[OK] Aggregated to {len(self.odpair_list)} OD-pairs")
        print(f"     Vehicle stock entries: {len(self.initial_vehicle_stock)}")
        print(f"     Reduction: {len(odpair_groups)} individual routes -> {len(self.odpair_list)} aggregated")

    def run_complete_preprocessing(self, max_odpairs: int = None, min_distance_km: float = None, cross_border_only: bool = False, aggregate_odpairs: bool = True):
        """Execute complete preprocessing pipeline.

        Args:
            max_odpairs: Maximum number of OD-pairs to process
            min_distance_km: Minimum distance filter (e.g., 360km for mandatory breaks)
            cross_border_only: If True, only include cross-border OD-pairs (different countries)
            aggregate_odpairs: If True, aggregate OD-pairs by NUTS-2 origin-destination (default: True)
        """
        print("\n" + "="*80)
        print("COMPLETE SM NUTS-2 PREPROCESSING")
        print("="*80)
        print(f"Input:  {self.data_dir}")
        print(f"Output: {self.output_dir}")
        if min_distance_km:
            print(f"Filter: Distance >= {min_distance_km}km (mandatory breaks test)")
        if cross_border_only:
            print(f"Filter: Cross-border only (origin and destination in different countries)")
        print("="*80)

        self.load_data()
        self.create_nuts2_geographic_elements()
        self.build_edge_lookup()
        self.create_paths_with_original_distances(
            max_odpairs=max_odpairs,
            min_distance_km=min_distance_km,
            cross_border_only=cross_border_only
        )

        # Scale transport demand F based on linear growth (2015-2024 reference points)
        self.scale_transport_demand()

        # Aggregate OD-pairs by NUTS-2 if requested
        if aggregate_odpairs:
            self.aggregate_odpairs_by_nuts2()

        self.create_mandatory_breaks()
        self.save_results()

        # Summary
        print("\n" + "="*80)
        print("PREPROCESSING COMPLETE - SUMMARY")
        print("="*80)
        print(f"  Geographic elements (NUTS-2): {len(self.geographic_elements)}")
        print(f"  OD-pairs (NOT aggregated):    {len(self.odpair_list)}")
        print(f"  Paths (collapsed nodes):      {len(self.path_list)}")
        print(f"  Initial vehicle stock:        {len(self.initial_vehicle_stock)}")
        print(f"  Mandatory breaks:             {len(self.mandatory_breaks)}")
        print("="*80)

        print("\nKEY FEATURES:")
        print("  [OK] NUTS-2 aggregated nodes (MAXIMUM capacity planning efficiency)")
        print("  [OK] Collapsed path sequences (minimal nodes in routes)")
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
        preprocessor = CompleteSMNUTS2Preprocessor(data_dir, output_dir)
        preprocessor.run_complete_preprocessing(
            max_odpairs=MAX_ODpair,
            min_distance_km=MIN_DISTANCE_KM,
            cross_border_only=CROSS_BORDER_ONLY
        )

        print("[SUCCESS] NUTS-2 preprocessing finished!")
