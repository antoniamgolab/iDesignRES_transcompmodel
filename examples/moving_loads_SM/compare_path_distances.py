"""
Compare Path Distances: Original vs NUTS-3 Aggregated
======================================================

This script compares path distances between:
1. Original traffic data (Total_distance from CSV)
2. NUTS-3 aggregated network paths (actual edge distances)

The key question: When we aggregate traffic to NUTS-3 regions, do the
distances from the truck traffic data match the distances in the NUTS-3 network?

Author: Claude Code
Date: 2025-10-15
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, Tuple


class PathDistanceComparator:
    """Compare path distances between original and NUTS-3 data."""

    def __init__(self,
                 original_traffic_path: str,
                 nuts3_traffic_path: str,
                 nuts3_nodes_path: str,
                 nuts3_edges_path: str):
        """
        Initialize comparator.

        Parameters:
        -----------
        original_traffic_path : str
            Path to original traffic CSV
        nuts3_traffic_path : str
            Path to NUTS-3 aggregated traffic CSV
        nuts3_nodes_path : str
            Path to NUTS-3 network nodes CSV
        nuts3_edges_path : str
            Path to NUTS-3 network edges CSV
        """
        self.orig_traffic_path = Path(original_traffic_path)
        self.nuts3_traffic_path = Path(nuts3_traffic_path)
        self.nuts3_nodes_path = Path(nuts3_nodes_path)
        self.nuts3_edges_path = Path(nuts3_edges_path)

        # Data storage
        self.orig_traffic = None
        self.nuts3_traffic = None
        self.nuts3_nodes = None
        self.nuts3_edges = None
        self.edge_lookup = {}
        self.nuts3_to_node = {}

        # Results
        self.comparison_results = []

    def load_data(self):
        """Load all data files."""
        print("="*80)
        print("LOADING DATA")
        print("="*80)

        # Original traffic
        if self.orig_traffic_path.exists():
            self.orig_traffic = pd.read_csv(self.orig_traffic_path)
            print(f"[OK] Original traffic: {len(self.orig_traffic):,} rows")
        else:
            print(f"[WARNING] Original traffic not found: {self.orig_traffic_path}")
            self.orig_traffic = pd.DataFrame()

        # NUTS-3 traffic
        self.nuts3_traffic = pd.read_csv(self.nuts3_traffic_path)
        print(f"[OK] NUTS-3 traffic: {len(self.nuts3_traffic):,} rows")

        # NUTS-3 network
        self.nuts3_nodes = pd.read_csv(self.nuts3_nodes_path)
        self.nuts3_edges = pd.read_csv(self.nuts3_edges_path)
        print(f"[OK] NUTS-3 network: {len(self.nuts3_nodes)} nodes, {len(self.nuts3_edges)} edges")

        # Calculate Total_distance for traffic data
        for df in [self.orig_traffic, self.nuts3_traffic]:
            if len(df) > 0 and 'Total_distance' not in df.columns:
                df['Total_distance'] = (
                    df['Distance_from_origin_region_to_E_road'] +
                    df['Distance_within_E_road'] +
                    df['Distance_from_E_road_to_destination_region']
                )

        # Build mappings
        self.nuts3_to_node = dict(zip(
            self.nuts3_nodes['ETISplus_Zone_ID'],
            self.nuts3_nodes['Network_Node_ID']
        ))

        # Build edge lookup
        for _, edge in self.nuts3_edges.iterrows():
            a = int(edge['Network_Node_A_ID'])
            b = int(edge['Network_Node_B_ID'])
            dist = edge['Distance']
            self.edge_lookup[(a, b)] = dist
            self.edge_lookup[(b, a)] = dist

        print(f"[OK] Created mappings: {len(self.nuts3_to_node)} NUTS-3 regions, {len(self.edge_lookup)//2} edges")

    def compare_distances(self):
        """
        Compare distances between traffic data and network edges.

        For each NUTS-3 OD-pair:
        1. Get reported distance from traffic data
        2. Get actual distance from NUTS-3 network (if direct edge exists)
        3. Calculate difference
        """
        print("\n" + "="*80)
        print("COMPARING PATH DISTANCES")
        print("="*80)

        # Group NUTS-3 traffic by OD-pair
        nuts3_od = self.nuts3_traffic.groupby(
            ['ID_origin_region', 'ID_destination_region']
        ).agg({
            'Total_distance': 'mean',
            'Traffic_flow_trucks_2030': 'sum'
        }).reset_index()

        print(f"\nUnique NUTS-3 OD-pairs: {len(nuts3_od):,}")

        # For each OD-pair, compare traffic distance vs network distance
        direct_edges = 0
        no_direct_edge = 0
        errors = []

        for idx, row in nuts3_od.iterrows():
            origin_nuts3 = row['ID_origin_region']
            dest_nuts3 = row['ID_destination_region']
            traffic_distance = row['Total_distance']
            traffic_flow = row['Traffic_flow_trucks_2030']

            # Map to network nodes
            origin_node = self.nuts3_to_node.get(origin_nuts3)
            dest_node = self.nuts3_to_node.get(dest_nuts3)

            if origin_node is None or dest_node is None:
                continue

            origin_node = int(origin_node)
            dest_node = int(dest_node)

            # Check if direct edge exists in NUTS-3 network
            if (origin_node, dest_node) in self.edge_lookup:
                network_distance = self.edge_lookup[(origin_node, dest_node)]
                has_direct_edge = True
                direct_edges += 1
            else:
                # No direct edge - would need pathfinding
                network_distance = None
                has_direct_edge = False
                no_direct_edge += 1

            # Calculate error (if direct edge exists)
            if network_distance is not None:
                abs_error = abs(network_distance - traffic_distance)
                rel_error = abs_error / traffic_distance if traffic_distance > 0 else 0
            else:
                abs_error = None
                rel_error = None

            # Store result
            self.comparison_results.append({
                'origin_nuts3': origin_nuts3,
                'dest_nuts3': dest_nuts3,
                'traffic_distance': traffic_distance,
                'network_distance': network_distance,
                'has_direct_edge': has_direct_edge,
                'absolute_error': abs_error,
                'relative_error': rel_error,
                'traffic_flow': traffic_flow
            })

            if (idx + 1) % 100 == 0:
                print(f"  Processed {idx+1}/{len(nuts3_od)} OD-pairs...")

        print(f"\n[OK] Comparison complete")
        print(f"  OD-pairs with direct edge: {direct_edges:,}")
        print(f"  OD-pairs without direct edge: {no_direct_edge:,}")
        print(f"  Percentage with direct edge: {100*direct_edges/(direct_edges+no_direct_edge):.1f}%")

    def compute_statistics(self) -> Dict:
        """Compute summary statistics of distance differences."""
        print("\n" + "="*80)
        print("DISTANCE COMPARISON STATISTICS")
        print("="*80)

        df = pd.DataFrame(self.comparison_results)

        # Overall
        stats = {
            'total_odpairs': len(df),
            'with_direct_edge': len(df[df['has_direct_edge']]),
            'without_direct_edge': len(df[~df['has_direct_edge']])
        }

        print(f"\nTotal OD-pairs: {stats['total_odpairs']:,}")
        print(f"  With direct edge: {stats['with_direct_edge']:,} ({100*stats['with_direct_edge']/stats['total_odpairs']:.1f}%)")
        print(f"  Without direct edge: {stats['without_direct_edge']:,} ({100*stats['without_direct_edge']/stats['total_odpairs']:.1f}%)")

        # For OD-pairs with direct edges, compute error statistics
        direct_df = df[df['has_direct_edge']].copy()

        if len(direct_df) > 0:
            stats['mean_traffic_distance'] = direct_df['traffic_distance'].mean()
            stats['mean_network_distance'] = direct_df['network_distance'].mean()
            stats['mean_abs_error'] = direct_df['absolute_error'].mean()
            stats['median_abs_error'] = direct_df['absolute_error'].median()
            stats['mean_rel_error'] = direct_df['relative_error'].mean()
            stats['median_rel_error'] = direct_df['relative_error'].median()
            stats['max_rel_error'] = direct_df['relative_error'].max()

            print(f"\nFor OD-pairs with direct edges:")
            print(f"  Mean traffic distance:   {stats['mean_traffic_distance']:.2f} km")
            print(f"  Mean network distance:   {stats['mean_network_distance']:.2f} km")
            print(f"  Mean absolute error:     {stats['mean_abs_error']:.2f} km")
            print(f"  Median absolute error:   {stats['median_abs_error']:.2f} km")
            print(f"  Mean relative error:     {100*stats['mean_rel_error']:.2f}%")
            print(f"  Median relative error:   {100*stats['median_rel_error']:.2f}%")
            print(f"  Max relative error:      {100*stats['max_rel_error']:.2f}%")

            # Weighted by traffic flow
            weighted_error = (direct_df['absolute_error'] * direct_df['traffic_flow']).sum() / direct_df['traffic_flow'].sum()
            stats['traffic_weighted_error'] = weighted_error
            print(f"  Traffic-weighted error:  {weighted_error:.2f} km ({100*weighted_error/stats['mean_traffic_distance']:.2f}%)")

            # Check how many are exact matches (zero error)
            exact_matches = len(direct_df[direct_df['absolute_error'] < 0.1])
            print(f"\n  Exact matches (error < 0.1 km): {exact_matches} ({100*exact_matches/len(direct_df):.1f}%)")

        return stats

    def create_visualizations(self, output_file: str = "path_distance_comparison.png"):
        """Create visualizations of distance comparison."""
        print("\n" + "="*80)
        print("CREATING VISUALIZATIONS")
        print("="*80)

        df = pd.DataFrame(self.comparison_results)
        direct_df = df[df['has_direct_edge']].copy()

        if len(direct_df) == 0:
            print("[WARNING] No direct edges found - cannot create visualizations")
            return

        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('Path Distance Comparison: Traffic Data vs NUTS-3 Network',
                     fontsize=16, fontweight='bold')

        # Plot 1: Traffic vs Network distance scatter
        ax = axes[0, 0]
        sample = direct_df.sample(min(1000, len(direct_df)))
        ax.scatter(sample['traffic_distance'], sample['network_distance'],
                  alpha=0.5, s=30, c='#4ecdc4', edgecolors='black', linewidths=0.5)

        # Add y=x line
        max_dist = max(sample['traffic_distance'].max(), sample['network_distance'].max())
        ax.plot([0, max_dist], [0, max_dist], 'r--', linewidth=2, label='Perfect match (y=x)')

        ax.set_xlabel('Traffic Reported Distance (km)', fontsize=11)
        ax.set_ylabel('NUTS-3 Network Distance (km)', fontsize=11)
        ax.set_title('Distance Comparison (Direct Edges Only)', fontsize=12, fontweight='bold')
        ax.legend()
        ax.grid(alpha=0.3)

        # Plot 2: Relative error distribution
        ax = axes[0, 1]
        ax.hist(direct_df['relative_error'] * 100, bins=50, color='#95e1d3',
               edgecolor='black', alpha=0.7)
        ax.axvline(direct_df['relative_error'].mean() * 100, color='red',
                  linestyle='--', linewidth=2,
                  label=f"Mean: {direct_df['relative_error'].mean()*100:.1f}%")
        ax.axvline(direct_df['relative_error'].median() * 100, color='orange',
                  linestyle='--', linewidth=2,
                  label=f"Median: {direct_df['relative_error'].median()*100:.1f}%")
        ax.set_xlabel('Relative Distance Error (%)', fontsize=11)
        ax.set_ylabel('Number of OD-pairs', fontsize=11)
        ax.set_title('Error Distribution', fontsize=12, fontweight='bold')
        ax.legend()
        ax.grid(alpha=0.3)

        # Plot 3: Error by distance bin
        ax = axes[1, 0]
        bins = [0, 50, 100, 200, 500, 1000, 2000, 10000]
        labels = ['0-50', '50-100', '100-200', '200-500', '500-1k', '1k-2k', '2k+']
        direct_df['distance_bin'] = pd.cut(direct_df['traffic_distance'],
                                           bins=bins, labels=labels)

        error_by_bin = direct_df.groupby('distance_bin')['relative_error'].mean() * 100
        count_by_bin = direct_df.groupby('distance_bin').size()

        x_pos = range(len(error_by_bin))
        bars = ax.bar(x_pos, error_by_bin.values, color='#f38181',
                     edgecolor='black', alpha=0.7)

        # Add count labels on bars
        for i, (bar, count) in enumerate(zip(bars, count_by_bin.values)):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'n={count}', ha='center', va='bottom', fontsize=8)

        ax.set_xticks(x_pos)
        ax.set_xticklabels(error_by_bin.index, rotation=45)
        ax.set_xlabel('Traffic Distance (km)', fontsize=11)
        ax.set_ylabel('Mean Relative Error (%)', fontsize=11)
        ax.set_title('Error by Distance Range', fontsize=12, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)

        # Plot 4: Direct edge vs no direct edge comparison
        ax = axes[1, 1]
        categories = ['With Direct\nEdge', 'Without Direct\nEdge']
        counts = [
            len(df[df['has_direct_edge']]),
            len(df[~df['has_direct_edge']])
        ]
        colors = ['#4ecdc4', '#ff6b6b']

        bars = ax.bar(categories, counts, color=colors, edgecolor='black', alpha=0.7)
        ax.set_ylabel('Number of OD-pairs', fontsize=11)
        ax.set_title('Network Connectivity', fontsize=12, fontweight='bold')

        # Add percentage labels
        total = sum(counts)
        for i, (bar, val) in enumerate(zip(bars, counts)):
            pct = 100 * val / total if total > 0 else 0
            ax.text(bar.get_x() + bar.get_width()/2., val,
                   f'{pct:.1f}%\n({val:,})',
                   ha='center', va='bottom', fontweight='bold', fontsize=10)

        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"[OK] Visualization saved to: {output_file}")

    def generate_report(self, output_file: str = "path_distance_comparison_report.txt"):
        """Generate detailed text report."""
        print("\n" + "="*80)
        print("GENERATING REPORT")
        print("="*80)

        df = pd.DataFrame(self.comparison_results)
        stats = self.compute_statistics()

        with open(output_file, 'w') as f:
            f.write("="*80 + "\n")
            f.write("PATH DISTANCE COMPARISON REPORT\n")
            f.write("Traffic Data vs NUTS-3 Network Distances\n")
            f.write("="*80 + "\n\n")

            f.write("RESEARCH QUESTION\n")
            f.write("-"*80 + "\n")
            f.write("Is there a difference in path lengths between the routes in truck traffic\n")
            f.write("data (original) and the NUTS-3 aggregated network?\n\n")

            f.write("METHODOLOGY\n")
            f.write("-"*80 + "\n")
            f.write("1. Load truck traffic data with reported Total_distance\n")
            f.write("2. Load NUTS-3 aggregated network with edge distances\n")
            f.write("3. For each OD-pair, compare:\n")
            f.write("   - Traffic reported distance (from CSV)\n")
            f.write("   - Network edge distance (from NUTS-3 graph)\n")
            f.write("4. Calculate absolute and relative errors\n\n")

            f.write("RESULTS\n")
            f.write("-"*80 + "\n\n")

            f.write(f"Total OD-pairs analyzed: {stats['total_odpairs']:,}\n\n")

            pct_direct = 100 * stats['with_direct_edge'] / stats['total_odpairs']
            pct_indirect = 100 * stats['without_direct_edge'] / stats['total_odpairs']

            f.write(f"Network Connectivity:\n")
            f.write(f"  OD-pairs with DIRECT edge:    {stats['with_direct_edge']:,} ({pct_direct:.1f}%)\n")
            f.write(f"  OD-pairs WITHOUT direct edge: {stats['without_direct_edge']:,} ({pct_indirect:.1f}%)\n\n")

            if stats['with_direct_edge'] > 0:
                f.write(f"Distance Comparison (Direct Edges Only):\n")
                f.write(f"  Mean traffic distance:       {stats['mean_traffic_distance']:.2f} km\n")
                f.write(f"  Mean network distance:       {stats['mean_network_distance']:.2f} km\n")
                f.write(f"  Mean absolute error:         {stats['mean_abs_error']:.2f} km\n")
                f.write(f"  Mean relative error:         {100*stats['mean_rel_error']:.2f}%\n")
                f.write(f"  Median relative error:       {100*stats['median_rel_error']:.2f}%\n")
                f.write(f"  Traffic-weighted error:      {stats['traffic_weighted_error']:.2f} km\n\n")

                direct_df = df[df['has_direct_edge']]
                exact_matches = len(direct_df[direct_df['absolute_error'] < 0.1])
                pct_exact = 100 * exact_matches / len(direct_df)
                f.write(f"  Exact matches (< 0.1 km):    {exact_matches} ({pct_exact:.1f}%)\n\n")

            f.write("KEY FINDINGS\n")
            f.write("-"*80 + "\n\n")

            if stats['with_direct_edge'] > 0:
                if stats['mean_rel_error'] < 0.05:
                    f.write("[+] VERY LOW error (<5% average)\n")
                    f.write("    Traffic distances match network distances very closely!\n")
                    f.write("    The NUTS-3 aggregation preserves distance accuracy.\n\n")
                elif stats['mean_rel_error'] < 0.15:
                    f.write("[+] LOW error (<15% average)\n")
                    f.write("    Traffic distances are reasonably well represented in network.\n")
                    f.write("    Acceptable for long-haul freight optimization.\n\n")
                else:
                    f.write("[!] MODERATE/HIGH error (>15% average)\n")
                    f.write("    Significant differences between traffic and network distances.\n")
                    f.write("    May need to review network edge distance calculations.\n\n")

            if pct_indirect > 50:
                f.write("[!] MANY indirect routes (>50%)\n")
                f.write("    More than half of OD-pairs lack direct edges in NUTS-3 network.\n")
                f.write("    Paths require intermediate nodes (multi-hop routing).\n")
                f.write("    This is EXPECTED for sparse NUTS-3 aggregation.\n\n")

            f.write("INTERPRETATION\n")
            f.write("-"*80 + "\n\n")
            f.write("The NUTS-3 aggregation creates a simplified network where:\n\n")
            f.write(f"1. {pct_direct:.1f}% of OD-pairs have DIRECT connections\n")
            f.write("   - These use actual edge distances from the network\n")
            f.write(f"   - Average error: {100*stats.get('mean_rel_error', 0):.1f}%\n\n")
            f.write(f"2. {pct_indirect:.1f}% of OD-pairs require MULTI-HOP routing\n")
            f.write("   - These use pathfinding (BFS) or fallback to traffic distance\n")
            f.write("   - More computation needed during preprocessing\n\n")

            f.write("ANSWER TO RESEARCH QUESTION:\n")
            if stats.get('mean_rel_error', 0) < 0.05:
                f.write("YES, there is a difference, but it is MINIMAL (<5% on average).\n")
                f.write("The NUTS-3 network distances closely match the traffic data.\n")
            elif stats.get('mean_rel_error', 0) < 0.15:
                f.write("YES, there is a SMALL difference (~{:.1f}% on average).\n".format(100*stats.get('mean_rel_error', 0)))
                f.write("This is acceptable for regional-scale planning.\n")
            else:
                f.write("YES, there is a SIGNIFICANT difference (>{:.1f}% on average).\n".format(100*stats.get('mean_rel_error', 0)))
                f.write("Network distances differ notably from traffic reported distances.\n")

        print(f"[OK] Report saved to: {output_file}")

    def run_full_comparison(self):
        """Execute complete comparison analysis."""
        print("\n" + "="*80)
        print("PATH DISTANCE COMPARISON ANALYSIS")
        print("="*80)

        self.load_data()
        self.compare_distances()
        stats = self.compute_statistics()
        self.generate_report()
        self.create_visualizations()

        print("\n" + "="*80)
        print("ANALYSIS COMPLETE")
        print("="*80)
        print("\nOutputs:")
        print("  - path_distance_comparison_report.txt")
        print("  - path_distance_comparison.png")

        return stats


def compare_path_distances(
    original_traffic_path: str = "data/Trucktraffic/01_Trucktrafficflow.csv",
    nuts3_traffic_path: str = "data/Trucktraffic_NUTS3/01_Trucktrafficflow.csv",
    nuts3_nodes_path: str = "data/Trucktraffic_NUTS3/03_network-nodes.csv",
    nuts3_edges_path: str = "data/Trucktraffic_NUTS3/04_network-edges.csv"
):
    """
    Convenience function to run path distance comparison.

    Returns:
    --------
    comparator : PathDistanceComparator
        Comparator with complete results
    """
    comparator = PathDistanceComparator(
        original_traffic_path,
        nuts3_traffic_path,
        nuts3_nodes_path,
        nuts3_edges_path
    )
    comparator.run_full_comparison()
    return comparator


if __name__ == "__main__":
    import sys

    print("\n" + "="*80)
    print("PATH DISTANCE COMPARISON: Original vs NUTS-3")
    print("="*80)
    print("\nResearch Question:")
    print("Is there a difference in the length of paths from the routes in")
    print("truck traffic data between the original data and NUTS-3 aggregation?")
    print("="*80 + "\n")

    # Default paths
    original_traffic = "data/Trucktraffic/01_Trucktrafficflow.csv"
    nuts3_traffic = "data/Trucktraffic_NUTS3/01_Trucktrafficflow.csv"
    nuts3_nodes = "data/Trucktraffic_NUTS3/03_network-nodes.csv"
    nuts3_edges = "data/Trucktraffic_NUTS3/04_network-edges.csv"

    # Allow command-line override
    if len(sys.argv) > 4:
        original_traffic = sys.argv[1]
        nuts3_traffic = sys.argv[2]
        nuts3_nodes = sys.argv[3]
        nuts3_edges = sys.argv[4]

    comparator = compare_path_distances(
        original_traffic,
        nuts3_traffic,
        nuts3_nodes,
        nuts3_edges
    )

    print("\n[SUCCESS] Done!")
