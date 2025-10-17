"""
Spatial Aggregation to NUTS-3 Resolution
=========================================

This module provides functions to aggregate TransComp model input data from
high spatial resolution (individual nodes/edges) to NUTS-3 regional level.

Main purpose: Reduce model size to handle larger datasets by consolidating
geographic elements while preserving essential transport network structure.

Author: Claude Code
Date: 2025-10-14
"""

import yaml
import numpy as np
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple, Any
import copy


class NUTS3Aggregator:
    """
    Aggregates TransComp model data to NUTS-3 resolution.

    Key challenges solved:
    1. Geographic nodes are consolidated to NUTS-3 centroids
    2. Paths are simplified by removing intra-regional segments
    3. OD-pairs with same NUTS-3 origin/destination are merged
    4. Infrastructure is aggregated by region
    """

    def __init__(self, input_dir: str, output_dir: str):
        """
        Initialize aggregator.

        Parameters:
        -----------
        input_dir : str
            Path to input case directory with YAML files
        output_dir : str
            Path to output directory for aggregated files
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Storage for loaded and processed data
        self.geo_elements = []
        self.paths = []
        self.odpairs = []

        # Mapping structures
        self.node_to_nuts3 = {}  # original_node_id -> nuts3_region
        self.nuts3_nodes = {}    # nuts3_region -> aggregated_node_data
        self.node_id_mapping = {}  # original_node_id -> new_nuts3_node_id

    def load_yaml(self, filename: str) -> List[Dict]:
        """Load YAML file and return data."""
        filepath = self.input_dir / filename
        if not filepath.exists():
            print(f"Warning: {filename} not found, skipping...")
            return []
        with open(filepath, 'r') as f:
            data = yaml.safe_load(f)
        return data if data else []

    def save_yaml(self, data: List[Dict], filename: str):
        """Save data to YAML file with proper formatting."""
        filepath = self.output_dir / filename
        with open(filepath, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        print(f"[OK] Saved {filename}")

    def aggregate_geographic_elements(self):
        """
        Aggregate nodes by NUTS-3 region.

        Strategy:
        - Group nodes by nuts3_region
        - Create one representative node per NUTS-3 region
        - Use centroid of coordinates (weighted by demand if available)
        - Preserve all time-series data (carbon_price, etc.)
        """
        print("\n" + "="*80)
        print("1. AGGREGATING GEOGRAPHIC ELEMENTS")
        print("="*80)

        self.geo_elements = self.load_yaml("GeographicElement.yaml")

        # Filter nodes only (type == 'node')
        nodes = [elem for elem in self.geo_elements if elem.get('type') == 'node']
        print(f"  Original nodes: {len(nodes)}")

        # Group nodes by NUTS-3 region
        nuts3_groups = defaultdict(list)
        for node in nodes:
            nuts3 = node.get('nuts3_region')
            if nuts3:
                self.node_to_nuts3[node['id']] = nuts3
                nuts3_groups[nuts3].append(node)

        print(f"  NUTS-3 regions found: {len(nuts3_groups)}")

        # Create aggregated nodes (one per NUTS-3 region)
        aggregated_nodes = []
        new_node_id = 0

        for nuts3, node_group in sorted(nuts3_groups.items()):
            # Calculate centroid coordinates
            lats = [n['coordinate_lat'] for n in node_group]
            lons = [n['coordinate_long'] for n in node_group]
            avg_lat = np.mean(lats)
            avg_lon = np.mean(lons)

            # Use data from first node as template
            template = node_group[0]

            # Create aggregated node
            agg_node = {
                'id': new_node_id,
                'name': f"nuts3_{nuts3}",
                'type': 'node',
                'nuts3_region': nuts3,
                'country': template.get('country', 'XX'),
                'coordinate_lat': avg_lat,
                'coordinate_long': avg_lon,
                'from': 999999,
                'to': 999999,
                'length': 0.0,
                'carbon_price': template.get('carbon_price', [])
            }

            aggregated_nodes.append(agg_node)

            # Create mapping from all original nodes to new NUTS-3 node
            for node in node_group:
                self.node_id_mapping[node['id']] = new_node_id

            # Store for reference
            self.nuts3_nodes[nuts3] = agg_node

            new_node_id += 1

        print(f"  Aggregated to {len(aggregated_nodes)} NUTS-3 nodes")
        print(f"  Reduction: {len(nodes)} -> {len(aggregated_nodes)} "
              f"({100*(1-len(aggregated_nodes)/len(nodes)):.1f}% reduction)")

        return aggregated_nodes

    def aggregate_paths(self):
        """
        Aggregate paths by collapsing intra-regional segments.

        Strategy:
        - For each path, map nodes to NUTS-3 regions
        - Remove consecutive nodes in same NUTS-3 region
        - Keep only inter-regional transitions
        - Aggregate distances within each region
        - Recalculate cumulative distances

        Example:
        Original:  [A1, A2, A3, B1, B2, C1]  (A, B, C are NUTS-3 regions)
        Aggregated: [A, B, C]
        """
        print("\n" + "="*80)
        print("2. AGGREGATING PATHS")
        print("="*80)

        self.paths = self.load_yaml("Path.yaml")
        print(f"  Original paths: {len(self.paths)}")

        aggregated_paths = []
        total_nodes_before = 0
        total_nodes_after = 0

        for path_idx, path in enumerate(self.paths):
            sequence = path.get('sequence', [])
            distances = path.get('distance_from_previous', [])
            cum_distances = path.get('cumulative_distance', [])

            if not sequence:
                continue

            total_nodes_before += len(sequence)

            # Map nodes to NUTS-3 regions
            nuts3_sequence = []
            for node_id in sequence:
                nuts3 = self.node_to_nuts3.get(node_id)
                if nuts3:
                    nuts3_sequence.append(nuts3)
                else:
                    # Node not found - might be edge, keep original
                    nuts3_sequence.append(f"unknown_{node_id}")

            # Collapse consecutive same-region nodes
            simplified_nuts3 = [nuts3_sequence[0]]
            segment_distances = [0.0]  # First node has 0 distance

            current_segment_distance = 0.0

            for i in range(1, len(nuts3_sequence)):
                current_segment_distance += distances[i]

                # Check if we're entering a new region
                if nuts3_sequence[i] != nuts3_sequence[i-1]:
                    simplified_nuts3.append(nuts3_sequence[i])
                    segment_distances.append(current_segment_distance)
                    current_segment_distance = 0.0

            # If there's remaining distance in last segment, add to last distance
            if current_segment_distance > 0 and len(segment_distances) > 0:
                segment_distances[-1] += current_segment_distance

            # Calculate new cumulative distances
            new_cum_distances = np.cumsum(segment_distances).tolist()

            # Map NUTS-3 regions back to aggregated node IDs
            new_sequence = []
            for nuts3 in simplified_nuts3:
                if isinstance(nuts3, str) and nuts3.startswith("unknown_"):
                    # Skip unknown nodes
                    continue
                else:
                    agg_node = self.nuts3_nodes.get(nuts3)
                    if agg_node:
                        new_sequence.append(agg_node['id'])

            # Skip paths that became too short
            if len(new_sequence) < 2:
                print(f"  Warning: Path {path_idx} collapsed to {len(new_sequence)} nodes, skipping")
                continue

            total_nodes_after += len(new_sequence)

            # Create aggregated path
            agg_path = {
                'id': path_idx,
                'origin': path.get('origin'),
                'destination': path.get('destination'),
                'length': new_cum_distances[-1] if new_cum_distances else 0.0,
                'sequence': new_sequence,
                'distance_from_previous': segment_distances[:len(new_sequence)],
                'cumulative_distance': new_cum_distances[:len(new_sequence)]
            }

            aggregated_paths.append(agg_path)

        print(f"  Paths kept: {len(aggregated_paths)}")
        print(f"  Total nodes in paths: {total_nodes_before} -> {total_nodes_after}")
        print(f"  Average path length: {total_nodes_before/len(self.paths):.1f} -> "
              f"{total_nodes_after/len(aggregated_paths):.1f} nodes")

        return aggregated_paths

    def aggregate_odpairs(self):
        """
        Aggregate OD-pairs with same NUTS-3 origin and destination.

        Strategy:
        - Group OD-pairs by (origin_nuts3, destination_nuts3, product, purpose)
        - Sum demand (F values) across years
        - Aggregate vehicle stock
        - Assign aggregated path_id
        """
        print("\n" + "="*80)
        print("3. AGGREGATING OD-PAIRS")
        print("="*80)

        self.odpairs = self.load_yaml("Odpair.yaml")
        print(f"  Original OD-pairs: {len(self.odpairs)}")

        # Group OD-pairs
        odpair_groups = defaultdict(list)

        for odp in self.odpairs:
            origin_node = odp.get('from')
            dest_node = odp.get('to')

            # Map to NUTS-3
            origin_nuts3 = self.node_to_nuts3.get(origin_node, f"unknown_{origin_node}")
            dest_nuts3 = self.node_to_nuts3.get(dest_node, f"unknown_{dest_node}")

            # Group key
            key = (
                origin_nuts3,
                dest_nuts3,
                odp.get('product', 'freight'),
                odp.get('purpose', 'long-haul'),
                odp.get('region_type', 'highway'),
                odp.get('financial_status', 'any')
            )

            odpair_groups[key].append(odp)

        print(f"  Grouped into {len(odpair_groups)} unique NUTS-3 OD-pairs")

        # Aggregate each group
        aggregated_odpairs = []
        new_odp_id = 0

        for (origin_nuts3, dest_nuts3, product, purpose, region_type, fin_status), odp_group in odpair_groups.items():
            # Sum demand across all years
            n_years = len(odp_group[0].get('F', []))
            aggregated_F = [0.0] * n_years

            for odp in odp_group:
                F_values = odp.get('F', [])
                for year_idx in range(min(len(F_values), n_years)):
                    aggregated_F[year_idx] += F_values[year_idx]

            # Concatenate vehicle stock (or sum if preferred)
            all_vehicle_stock = []
            for odp in odp_group:
                all_vehicle_stock.extend(odp.get('vehicle_stock_init', []))

            # Get aggregated node IDs
            origin_node = self.nuts3_nodes.get(origin_nuts3)
            dest_node = self.nuts3_nodes.get(dest_nuts3)

            if not origin_node or not dest_node:
                continue

            # Create aggregated OD-pair
            agg_odp = {
                'id': new_odp_id,
                'path_id': new_odp_id,  # Will match with aggregated paths
                'from': origin_node['id'],
                'to': dest_node['id'],
                'product': product,
                'purpose': purpose,
                'region_type': region_type,
                'financial_status': fin_status,
                'F': aggregated_F,
                'vehicle_stock_init': all_vehicle_stock,
                'travel_time_budget': odp_group[0].get('travel_time_budget', 0.0)
            }

            aggregated_odpairs.append(agg_odp)
            new_odp_id += 1

        print(f"  Aggregated to {len(aggregated_odpairs)} OD-pairs")
        print(f"  Reduction: {len(self.odpairs)} -> {len(aggregated_odpairs)} "
              f"({100*(1-len(aggregated_odpairs)/len(self.odpairs)):.1f}% reduction)")

        return aggregated_odpairs

    def aggregate_infrastructure(self):
        """
        Aggregate fueling and mode infrastructure by NUTS-3 region.

        Returns dict with aggregated infrastructure data.
        """
        print("\n" + "="*80)
        print("4. AGGREGATING INFRASTRUCTURE")
        print("="*80)

        # Aggregate InitialFuelInfr
        fuel_infr = self.load_yaml("InitialFuelInfr.yaml")
        print(f"  Original fuel infrastructure entries: {len(fuel_infr)}")

        # Group by NUTS-3 and fuel type
        fuel_infr_groups = defaultdict(lambda: defaultdict(list))

        for infr in fuel_infr:
            # Field is 'allocation', not 'geographic_element'
            geo_id = infr.get('allocation')
            nuts3 = self.node_to_nuts3.get(geo_id)

            if nuts3:
                # Group by fuel type and charging type
                fuel = infr.get('fuel', 'unknown')
                infr_type = infr.get('type', 'unknown')
                income = infr.get('income_class', 'any')
                key = (fuel, infr_type, income)
                fuel_infr_groups[nuts3][key].append(infr)

        # Aggregate capacity
        aggregated_fuel_infr = []
        infr_id = 0

        for nuts3, fuel_types in fuel_infr_groups.items():
            nuts3_node = self.nuts3_nodes.get(nuts3)
            if not nuts3_node:
                continue

            for (fuel, infr_type, income), infr_list in fuel_types.items():
                # Sum installed capacity
                aggregated_kW = sum(infr.get('installed_kW', 0) for infr in infr_list)

                # Use template from first entry
                template = infr_list[0]

                agg_infr = {
                    'id': infr_id,
                    'allocation': nuts3_node['id'],
                    'fuel': fuel,
                    'type': infr_type,
                    'income_class': income,
                    'by_income_class': template.get('by_income_class', False),
                    'installed_kW': aggregated_kW
                }

                aggregated_fuel_infr.append(agg_infr)
                infr_id += 1

        print(f"  Aggregated to {len(aggregated_fuel_infr)} fuel infrastructure entries")

        # Aggregate InitialModeInfr (similar process)
        mode_infr = self.load_yaml("InitialModeInfr.yaml")
        print(f"  Original mode infrastructure entries: {len(mode_infr)}")

        mode_infr_groups = defaultdict(lambda: defaultdict(list))

        for infr in mode_infr:
            # Field is 'allocation', not 'geographic_element'
            geo_id = infr.get('allocation')
            nuts3 = self.node_to_nuts3.get(geo_id)

            if nuts3:
                mode = infr.get('mode', 'unknown')
                mode_infr_groups[nuts3][mode].append(infr)

        aggregated_mode_infr = []
        infr_id = 0

        for nuts3, modes in mode_infr_groups.items():
            nuts3_node = self.nuts3_nodes.get(nuts3)
            if not nuts3_node:
                continue

            for mode, infr_list in modes.items():
                # Sum infrastructure capacity
                aggregated_capacity = sum(infr.get('installed_capacity', 0) for infr in infr_list)

                # Use template from first entry
                template = infr_list[0]

                agg_infr = {
                    'id': infr_id,
                    'allocation': nuts3_node['id'],
                    'mode': mode,
                    'installed_capacity': aggregated_capacity
                }

                aggregated_mode_infr.append(agg_infr)
                infr_id += 1

        print(f"  Aggregated to {len(aggregated_mode_infr)} mode infrastructure entries")

        return {
            'fuel_infr': aggregated_fuel_infr,
            'mode_infr': aggregated_mode_infr
        }

    def copy_passthrough_files(self):
        """
        Copy files that don't require aggregation.

        These include: Technology, Fuel, FuelCost, FuelingInfrTypes,
        Mode, Vehicletype, TechVehicle, Product, FinancialStatus,
        Regiontype, Speed, Model, NetworkConnectionCosts
        """
        print("\n" + "="*80)
        print("5. COPYING PASSTHROUGH FILES")
        print("="*80)

        passthrough_files = [
            "Technology.yaml",
            "Fuel.yaml",
            "FuelCost.yaml",
            "FuelingInfrTypes.yaml",
            "Mode.yaml",
            "Vehicletype.yaml",
            "TechVehicle.yaml",
            "Product.yaml",
            "FinancialStatus.yaml",
            "Regiontype.yaml",
            "Speed.yaml",
            "Model.yaml",
            "NetworkConnectionCosts.yaml",
            "InitialVehicleStock.yaml",
            "MandatoryBreaks.yaml"
        ]

        for filename in passthrough_files:
            filepath = self.input_dir / filename
            if filepath.exists():
                data = self.load_yaml(filename)
                self.save_yaml(data, filename)

    def aggregate_spatial_flexibility_edges(self):
        """
        Aggregate SpatialFlexibilityEdges to inter-regional connections only.
        """
        print("\n" + "="*80)
        print("6. AGGREGATING SPATIAL FLEXIBILITY EDGES")
        print("="*80)

        edges = self.load_yaml("SpatialFlexibilityEdges.yaml")

        if not edges:
            print("  No spatial flexibility edges found")
            return []

        print(f"  Original edges: {len(edges)}")

        # Map edges to NUTS-3 pairs
        nuts3_edge_groups = defaultdict(list)

        for edge in edges:
            from_id = edge.get('from_id')
            to_id = edge.get('to_id')

            from_nuts3 = self.node_to_nuts3.get(from_id)
            to_nuts3 = self.node_to_nuts3.get(to_id)

            if from_nuts3 and to_nuts3 and from_nuts3 != to_nuts3:
                # Only keep inter-regional edges
                key = (from_nuts3, to_nuts3)
                nuts3_edge_groups[key].append(edge)

        # Create aggregated edges
        aggregated_edges = []
        edge_id = 0

        for (from_nuts3, to_nuts3), edge_group in nuts3_edge_groups.items():
            from_node = self.nuts3_nodes.get(from_nuts3)
            to_node = self.nuts3_nodes.get(to_nuts3)

            if not from_node or not to_node:
                continue

            # Average flexibility score
            avg_flexibility = np.mean([e.get('flexibility_score', 1.0) for e in edge_group])

            agg_edge = {
                'id': edge_id,
                'from_id': from_node['id'],
                'to_id': to_node['id'],
                'flexibility_score': avg_flexibility
            }

            aggregated_edges.append(agg_edge)
            edge_id += 1

        print(f"  Aggregated to {len(aggregated_edges)} inter-regional edges")

        return aggregated_edges

    def run_aggregation(self):
        """
        Execute full aggregation pipeline.
        """
        print("\n" + "="*80)
        print("NUTS-3 SPATIAL AGGREGATION")
        print("="*80)
        print(f"Input:  {self.input_dir}")
        print(f"Output: {self.output_dir}")

        # Step 1: Aggregate geographic elements
        aggregated_nodes = self.aggregate_geographic_elements()
        self.save_yaml(aggregated_nodes, "GeographicElement.yaml")

        # Step 2: Aggregate paths
        aggregated_paths = self.aggregate_paths()
        self.save_yaml(aggregated_paths, "Path.yaml")

        # Step 3: Aggregate OD-pairs
        aggregated_odpairs = self.aggregate_odpairs()
        self.save_yaml(aggregated_odpairs, "Odpair.yaml")

        # Step 4: Aggregate infrastructure
        infr_data = self.aggregate_infrastructure()
        self.save_yaml(infr_data['fuel_infr'], "InitialFuelInfr.yaml")
        self.save_yaml(infr_data['mode_infr'], "InitialModeInfr.yaml")

        # Step 5: Aggregate spatial flexibility edges
        aggregated_edges = self.aggregate_spatial_flexibility_edges()
        if aggregated_edges:
            self.save_yaml(aggregated_edges, "SpatialFlexibilityEdges.yaml")

        # Step 6: Copy passthrough files
        self.copy_passthrough_files()

        print("\n" + "="*80)
        print("[SUCCESS] AGGREGATION COMPLETE")
        print("="*80)
        print(f"\nAggregated case saved to: {self.output_dir}")

        # Print summary statistics
        self.print_summary()

    def print_summary(self):
        """Print summary statistics of aggregation."""
        print("\nSUMMARY STATISTICS:")
        print("-" * 80)
        print(f"  NUTS-3 regions:     {len(self.nuts3_nodes)}")
        print(f"  Aggregated nodes:   {len(self.nuts3_nodes)}")
        print(f"  Node mapping size:  {len(self.node_id_mapping)}")
        print(f"  Output directory:   {self.output_dir}")
        print("-" * 80)


def aggregate_case_to_nuts3(input_case_dir: str, output_case_dir: str):
    """
    Convenience function to aggregate a case to NUTS-3 resolution.

    Parameters:
    -----------
    input_case_dir : str
        Path to input case directory
    output_case_dir : str
        Path to output case directory

    Example:
    --------
    >>> aggregate_case_to_nuts3(
    ...     "input_data/case_1_20251014_101827",
    ...     "input_data/case_1_20251014_101827_nuts3"
    ... )
    """
    aggregator = NUTS3Aggregator(input_case_dir, output_case_dir)
    aggregator.run_aggregation()
    return aggregator


if __name__ == "__main__":
    # Example usage
    import sys

    if len(sys.argv) > 2:
        input_dir = sys.argv[1]
        output_dir = sys.argv[2]
    else:
        # Default directories
        input_dir = "input_data/case_1_20251014_101827"
        output_dir = "input_data/case_1_20251014_101827_nuts3"

    print(f"\nStarting NUTS-3 aggregation...")
    print(f"Input:  {input_dir}")
    print(f"Output: {output_dir}")

    aggregator = aggregate_case_to_nuts3(input_dir, output_dir)

    print("\n[SUCCESS] Done!")
