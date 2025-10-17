"""
Aggregation Error Analysis
===========================

Quantifies the error introduced by NUTS-3 spatial aggregation.

This tool compares original high-resolution data with aggregated data to
estimate:
1. Distance errors (network vs. straight-line distances)
2. Traffic distribution errors
3. Infrastructure placement errors
4. Network topology preservation

Author: Claude Code
Date: 2025-10-14
"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Tuple, Dict
from scipy.spatial.distance import euclidean
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')


class AggregationErrorAnalyzer:
    """
    Analyzes errors introduced by NUTS-3 spatial aggregation.

    Compares original vs. aggregated data to quantify:
    - Distance approximation errors
    - Traffic flow redistribution errors
    - Network connectivity preservation
    - Infrastructure allocation errors
    """

    def __init__(self, original_dir: str = "data/Trucktraffic",
                 aggregated_dir: str = "data/Trucktraffic_NUTS3"):
        """Initialize analyzer."""
        self.original_dir = Path(original_dir)
        self.aggregated_dir = Path(aggregated_dir)

        # Data storage
        self.orig_nodes = None
        self.orig_edges = None
        self.agg_nodes = None
        self.agg_edges = None
        self.nuts3_regions = None

        # Results storage
        self.errors = {}

    def load_data(self):
        """Load both original and aggregated datasets."""
        print("="*80)
        print("LOADING DATA FOR ERROR ANALYSIS")
        print("="*80)

        # Original data
        self.orig_nodes = pd.read_csv(self.original_dir / "03_network-nodes.csv")
        self.orig_edges = pd.read_csv(self.original_dir / "04_network-edges.csv")
        print(f"[OK] Loaded original: {len(self.orig_nodes)} nodes, {len(self.orig_edges)} edges")

        # Aggregated data
        self.agg_nodes = pd.read_csv(self.aggregated_dir / "03_network-nodes.csv")
        self.agg_edges = pd.read_csv(self.aggregated_dir / "04_network-edges.csv")
        print(f"[OK] Loaded aggregated: {len(self.agg_nodes)} nodes, {len(self.agg_edges)} edges")

        # NUTS-3 regions
        self.nuts3_regions = pd.read_csv(self.original_dir / "02_NUTS-3-Regions.csv")
        print(f"[OK] Loaded {len(self.nuts3_regions)} NUTS-3 regions")

    def analyze_distance_errors(self) -> Dict:
        """
        Analyze distance approximation errors.

        Types of errors:
        1. Intra-regional distance loss (edges removed)
        2. Inter-regional distance approximation (aggregated edges)
        3. Centroid displacement error

        Returns:
        --------
        distance_errors : dict
            Various distance error metrics
        """
        print("\n" + "="*80)
        print("1. DISTANCE ERROR ANALYSIS")
        print("="*80)

        errors = {}

        # 1. Intra-regional distance loss
        # Map nodes to NUTS-3
        node_to_nuts3 = dict(zip(
            self.orig_nodes['Network_Node_ID'],
            self.orig_nodes['ETISplus_Zone_ID']
        ))

        # Classify edges as intra vs inter regional
        orig_edges = self.orig_edges.copy()
        orig_edges['NUTS3_A'] = orig_edges['Network_Node_A_ID'].map(node_to_nuts3)
        orig_edges['NUTS3_B'] = orig_edges['Network_Node_B_ID'].map(node_to_nuts3)
        orig_edges['is_intra_regional'] = orig_edges['NUTS3_A'] == orig_edges['NUTS3_B']

        intra_edges = orig_edges[orig_edges['is_intra_regional']]
        inter_edges = orig_edges[~orig_edges['is_intra_regional']]

        intra_distance = intra_edges['Distance'].sum()
        inter_distance = inter_edges['Distance'].sum()
        total_distance = orig_edges['Distance'].sum()

        errors['intra_regional_distance_km'] = intra_distance
        errors['inter_regional_distance_km'] = inter_distance
        errors['total_distance_km'] = total_distance
        errors['intra_regional_fraction'] = intra_distance / total_distance

        print(f"\nIntra-regional distance (lost in aggregation):")
        print(f"  Distance: {intra_distance:,.0f} km ({100*intra_distance/total_distance:.1f}%)")
        print(f"  Edges:    {len(intra_edges):,} / {len(orig_edges):,} edges")

        # 2. Inter-regional distance comparison
        # For edges that exist in both, compare distances
        agg_distance_total = self.agg_edges['Distance'].sum()

        errors['agg_inter_regional_distance_km'] = agg_distance_total
        errors['distance_ratio'] = agg_distance_total / inter_distance

        print(f"\nInter-regional distance comparison:")
        print(f"  Original inter-regional: {inter_distance:,.0f} km")
        print(f"  Aggregated total:        {agg_distance_total:,.0f} km")
        print(f"  Ratio:                   {agg_distance_total/inter_distance:.3f}")

        if agg_distance_total > inter_distance:
            print(f"  [NOTE] Aggregated distance is HIGHER (summing parallel paths)")

        # 3. Centroid displacement error
        # For each NUTS-3, calculate distance from true centroid to representative node
        centroid_errors = []

        for nuts3_id in self.nuts3_regions['ETISPlus_Zone_ID']:
            # Get all original nodes in this region
            region_nodes = self.orig_nodes[
                self.orig_nodes['ETISplus_Zone_ID'] == nuts3_id
            ]

            if len(region_nodes) == 0:
                continue

            # Calculate true centroid
            true_centroid_x = region_nodes['Network_Node_X'].mean()
            true_centroid_y = region_nodes['Network_Node_Y'].mean()

            # Get representative node
            rep_node = self.agg_nodes[
                self.agg_nodes['ETISplus_Zone_ID'] == nuts3_id
            ]

            if len(rep_node) > 0:
                rep_x = rep_node['Network_Node_X'].iloc[0]
                rep_y = rep_node['Network_Node_Y'].iloc[0]

                # Euclidean distance (rough approximation)
                # For accurate distance, would need haversine formula
                displacement = euclidean([true_centroid_x, true_centroid_y],
                                       [rep_x, rep_y])

                # Approximate conversion to km (1 degree ≈ 111 km at equator)
                displacement_km = displacement * 111

                centroid_errors.append({
                    'nuts3_id': nuts3_id,
                    'displacement_km': displacement_km,
                    'num_nodes': len(region_nodes)
                })

        centroid_df = pd.DataFrame(centroid_errors)

        if len(centroid_df) > 0:
            errors['centroid_displacement_mean_km'] = centroid_df['displacement_km'].mean()
            errors['centroid_displacement_median_km'] = centroid_df['displacement_km'].median()
            errors['centroid_displacement_max_km'] = centroid_df['displacement_km'].max()
            errors['centroid_displacement_std_km'] = centroid_df['displacement_km'].std()

            print(f"\nCentroid displacement (representative node vs. true centroid):")
            print(f"  Mean:   {errors['centroid_displacement_mean_km']:.1f} km")
            print(f"  Median: {errors['centroid_displacement_median_km']:.1f} km")
            print(f"  Max:    {errors['centroid_displacement_max_km']:.1f} km")
            print(f"  Std:    {errors['centroid_displacement_std_km']:.1f} km")

        self.errors['distance'] = errors
        return errors

    def analyze_traffic_errors(self) -> Dict:
        """
        Analyze traffic flow redistribution errors.

        Compares traffic on original edges vs. aggregated edges to see
        how traffic is redistributed.

        Returns:
        --------
        traffic_errors : dict
            Traffic redistribution metrics
        """
        print("\n" + "="*80)
        print("2. TRAFFIC FLOW ERROR ANALYSIS")
        print("="*80)

        errors = {}

        # Get traffic columns
        traffic_cols = [col for col in self.orig_edges.columns if 'Traffic_flow' in col]

        if not traffic_cols:
            print("[SKIP] No traffic flow columns found")
            return errors

        # Map nodes to NUTS-3
        node_to_nuts3 = dict(zip(
            self.orig_nodes['Network_Node_ID'],
            self.orig_nodes['ETISplus_Zone_ID']
        ))

        orig_edges = self.orig_edges.copy()
        orig_edges['NUTS3_A'] = orig_edges['Network_Node_A_ID'].map(node_to_nuts3)
        orig_edges['NUTS3_B'] = orig_edges['Network_Node_B_ID'].map(node_to_nuts3)
        orig_edges['is_intra_regional'] = orig_edges['NUTS3_A'] == orig_edges['NUTS3_B']

        intra_edges = orig_edges[orig_edges['is_intra_regional']]
        inter_edges = orig_edges[~orig_edges['is_intra_regional']]

        for traffic_col in traffic_cols:
            year = traffic_col.split('_')[-1]

            total_traffic = orig_edges[traffic_col].sum()
            intra_traffic = intra_edges[traffic_col].sum()
            inter_traffic = inter_edges[traffic_col].sum()
            agg_traffic = self.agg_edges[traffic_col].sum()

            errors[f'total_traffic_{year}'] = total_traffic
            errors[f'intra_traffic_{year}'] = intra_traffic
            errors[f'inter_traffic_{year}'] = inter_traffic
            errors[f'intra_fraction_{year}'] = intra_traffic / total_traffic if total_traffic > 0 else 0
            errors[f'agg_traffic_{year}'] = agg_traffic
            errors[f'traffic_preserved_{year}'] = agg_traffic / inter_traffic if inter_traffic > 0 else 0

            print(f"\nTraffic flow ({year}):")
            print(f"  Total original:      {total_traffic:,.0f} trucks")
            print(f"  Intra-regional:      {intra_traffic:,.0f} trucks ({100*intra_traffic/total_traffic:.1f}%)")
            print(f"  Inter-regional:      {inter_traffic:,.0f} trucks ({100*inter_traffic/total_traffic:.1f}%)")
            print(f"  Aggregated total:    {agg_traffic:,.0f} trucks")
            print(f"  Preservation ratio:  {agg_traffic/inter_traffic:.3f}")

        self.errors['traffic'] = errors
        return errors

    def analyze_network_topology_errors(self) -> Dict:
        """
        Analyze network connectivity preservation.

        Metrics:
        - Average degree (edges per node)
        - Clustering coefficient
        - Path redundancy

        Returns:
        --------
        topology_errors : dict
            Network topology metrics
        """
        print("\n" + "="*80)
        print("3. NETWORK TOPOLOGY ANALYSIS")
        print("="*80)

        errors = {}

        # Node degree distribution
        orig_degree = defaultdict(int)
        for _, edge in self.orig_edges.iterrows():
            orig_degree[edge['Network_Node_A_ID']] += 1
            orig_degree[edge['Network_Node_B_ID']] += 1

        agg_degree = defaultdict(int)
        for _, edge in self.agg_edges.iterrows():
            agg_degree[edge['Network_Node_A_ID']] += 1
            agg_degree[edge['Network_Node_B_ID']] += 1

        orig_avg_degree = np.mean(list(orig_degree.values())) if orig_degree else 0
        agg_avg_degree = np.mean(list(agg_degree.values())) if agg_degree else 0

        errors['orig_avg_degree'] = orig_avg_degree
        errors['agg_avg_degree'] = agg_avg_degree
        errors['degree_ratio'] = agg_avg_degree / orig_avg_degree if orig_avg_degree > 0 else 0

        print(f"\nNetwork connectivity:")
        print(f"  Original avg degree:   {orig_avg_degree:.2f} edges/node")
        print(f"  Aggregated avg degree: {agg_avg_degree:.2f} edges/node")
        print(f"  Degree ratio:          {agg_avg_degree/orig_avg_degree:.3f}")

        # Edge density
        orig_density = len(self.orig_edges) / (len(self.orig_nodes) * (len(self.orig_nodes) - 1) / 2)
        agg_density = len(self.agg_edges) / (len(self.agg_nodes) * (len(self.agg_nodes) - 1) / 2)

        errors['orig_density'] = orig_density
        errors['agg_density'] = agg_density
        errors['density_ratio'] = agg_density / orig_density if orig_density > 0 else 0

        print(f"\nNetwork density:")
        print(f"  Original:    {orig_density:.6f}")
        print(f"  Aggregated:  {agg_density:.6f}")
        print(f"  Ratio:       {agg_density/orig_density:.3f}")

        self.errors['topology'] = errors
        return errors

    def estimate_optimization_error(self) -> Dict:
        """
        Estimate error impact on optimization results.

        This provides bounds on how aggregation might affect:
        - Infrastructure placement decisions
        - Technology adoption patterns
        - Cost estimates

        Returns:
        --------
        opt_errors : dict
            Estimated optimization error bounds
        """
        print("\n" + "="*80)
        print("4. OPTIMIZATION ERROR ESTIMATION")
        print("="*80)

        errors = {}

        # Distance-based cost error
        # If costs scale with distance, estimate error bounds
        dist_errors = self.errors.get('distance', {})

        intra_frac = dist_errors.get('intra_regional_fraction', 0)

        # Lower bound: All intra-regional trips are short (ignore them)
        # Upper bound: Intra-regional trips same cost as inter-regional
        errors['cost_error_lower_bound'] = 0.0
        errors['cost_error_upper_bound'] = intra_frac

        print(f"\nCost estimation error bounds:")
        print(f"  Lower bound: {100*errors['cost_error_lower_bound']:.1f}%")
        print(f"  Upper bound: {100*errors['cost_error_upper_bound']:.1f}%")
        print(f"  (Assumes distance-proportional costs)")

        # Infrastructure placement error
        # Centroid displacement affects optimal charging station placement
        centroid_error = dist_errors.get('centroid_displacement_mean_km', 0)

        errors['infra_placement_error_km'] = centroid_error
        errors['infra_placement_error_relative'] = centroid_error / 50 if centroid_error > 0 else 0  # Relative to typical station spacing (50km)

        print(f"\nInfrastructure placement error:")
        print(f"  Mean displacement: {centroid_error:.1f} km")
        print(f"  Relative error:    {100*errors['infra_placement_error_relative']:.1f}% (vs. 50km typical spacing)")

        # Traffic assignment error
        traffic_errors = self.errors.get('traffic', {})
        traffic_preservation = traffic_errors.get('traffic_preserved_2030', 1.0)

        errors['traffic_assignment_error'] = abs(1 - traffic_preservation)

        print(f"\nTraffic assignment error:")
        print(f"  Preservation ratio: {traffic_preservation:.3f}")
        print(f"  Assignment error:   {100*errors['traffic_assignment_error']:.1f}%")

        self.errors['optimization'] = errors
        return errors

    def generate_error_report(self, output_file: str = "aggregation_error_report.txt"):
        """Generate comprehensive error analysis report."""
        print("\n" + "="*80)
        print("GENERATING ERROR REPORT")
        print("="*80)

        with open(output_file, 'w') as f:
            f.write("="*80 + "\n")
            f.write("NUTS-3 AGGREGATION ERROR ANALYSIS REPORT\n")
            f.write("="*80 + "\n\n")

            # Summary
            f.write("EXECUTIVE SUMMARY\n")
            f.write("-"*80 + "\n\n")

            dist_err = self.errors.get('distance', {})
            traffic_err = self.errors.get('traffic', {})
            topo_err = self.errors.get('topology', {})
            opt_err = self.errors.get('optimization', {})

            f.write(f"Spatial Resolution Reduction:\n")
            f.write(f"  Nodes:  {len(self.orig_nodes):,} -> {len(self.agg_nodes):,} ")
            f.write(f"({100*(1-len(self.agg_nodes)/len(self.orig_nodes)):.1f}% reduction)\n")
            f.write(f"  Edges:  {len(self.orig_edges):,} -> {len(self.agg_edges):,} ")
            f.write(f"({100*(1-len(self.agg_edges)/len(self.orig_edges)):.1f}% reduction)\n\n")

            f.write(f"Key Error Metrics:\n")
            f.write(f"  Intra-regional distance lost:     {100*dist_err.get('intra_regional_fraction', 0):.1f}%\n")
            f.write(f"  Intra-regional traffic lost:      {100*traffic_err.get('intra_fraction_2030', 0):.1f}%\n")
            f.write(f"  Mean centroid displacement:       {dist_err.get('centroid_displacement_mean_km', 0):.1f} km\n")
            f.write(f"  Cost error upper bound:           {100*opt_err.get('cost_error_upper_bound', 0):.1f}%\n")
            f.write(f"  Infrastructure placement error:   {opt_err.get('infra_placement_error_km', 0):.1f} km\n\n")

            # Detailed sections
            f.write("\n" + "="*80 + "\n")
            f.write("DETAILED ANALYSIS\n")
            f.write("="*80 + "\n\n")

            # Distance errors
            f.write("1. DISTANCE ERRORS\n")
            f.write("-"*80 + "\n\n")
            for key, value in dist_err.items():
                f.write(f"  {key}: {value}\n")

            # Traffic errors
            f.write("\n2. TRAFFIC FLOW ERRORS\n")
            f.write("-"*80 + "\n\n")
            for key, value in traffic_err.items():
                f.write(f"  {key}: {value}\n")

            # Topology errors
            f.write("\n3. NETWORK TOPOLOGY\n")
            f.write("-"*80 + "\n\n")
            for key, value in topo_err.items():
                f.write(f"  {key}: {value}\n")

            # Optimization errors
            f.write("\n4. OPTIMIZATION IMPACT\n")
            f.write("-"*80 + "\n\n")
            for key, value in opt_err.items():
                f.write(f"  {key}: {value}\n")

            # Recommendations
            f.write("\n" + "="*80 + "\n")
            f.write("RECOMMENDATIONS\n")
            f.write("="*80 + "\n\n")

            intra_frac = dist_err.get('intra_regional_fraction', 0)
            centroid_error = dist_err.get('centroid_displacement_mean_km', 0)

            if intra_frac < 0.2:
                f.write("[+] Low intra-regional fraction (<20%) - aggregation is SAFE\n")
            elif intra_frac < 0.4:
                f.write("[~] Moderate intra-regional fraction (20-40%) - aggregation is ACCEPTABLE\n")
            else:
                f.write("[-] High intra-regional fraction (>40%) - aggregation may introduce significant errors\n")

            if centroid_error < 10:
                f.write("[+] Low centroid displacement (<10km) - representative nodes are GOOD\n")
            elif centroid_error < 25:
                f.write("[~] Moderate centroid displacement (10-25km) - representative nodes are ACCEPTABLE\n")
            else:
                f.write("[-] High centroid displacement (>25km) - representative nodes may not be ideal\n")

            f.write("\n")
            f.write("Use Cases:\n")
            f.write("  - Regional infrastructure planning:    [+] SUITABLE\n")
            f.write("  - Long-term policy analysis:           [+] SUITABLE\n")
            f.write("  - Inter-regional traffic flows:        [+] SUITABLE\n")
            f.write("  - Local routing optimization:          [-] NOT SUITABLE\n")
            f.write("  - Precise facility siting:             [-] NOT SUITABLE\n")

        print(f"[OK] Report saved to: {output_file}")

    def create_visualization(self, output_file: str = "aggregation_error_visualization.png"):
        """Create error visualization plots."""
        print("\n" + "="*80)
        print("CREATING ERROR VISUALIZATIONS")
        print("="*80)

        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('NUTS-3 Aggregation Error Analysis', fontsize=16, fontweight='bold')

        # Plot 1: Distance breakdown
        ax = axes[0, 0]
        dist_err = self.errors.get('distance', {})

        categories = ['Intra-regional\n(lost)', 'Inter-regional\n(preserved)']
        values = [
            dist_err.get('intra_regional_distance_km', 0),
            dist_err.get('inter_regional_distance_km', 0)
        ]
        colors = ['#ff6b6b', '#4ecdc4']

        ax.bar(categories, values, color=colors, alpha=0.7, edgecolor='black')
        ax.set_ylabel('Distance (km)', fontsize=12)
        ax.set_title('Distance Distribution', fontsize=13, fontweight='bold')
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1000:.0f}k'))

        # Add percentage labels
        total = sum(values)
        for i, (cat, val) in enumerate(zip(categories, values)):
            pct = 100 * val / total if total > 0 else 0
            ax.text(i, val, f'{pct:.1f}%', ha='center', va='bottom', fontweight='bold')

        # Plot 2: Traffic breakdown
        ax = axes[0, 1]
        traffic_err = self.errors.get('traffic', {})

        categories = ['Intra-regional\n(lost)', 'Inter-regional\n(preserved)']
        values = [
            traffic_err.get('intra_traffic_2030', 0),
            traffic_err.get('inter_traffic_2030', 0)
        ]

        ax.bar(categories, values, color=colors, alpha=0.7, edgecolor='black')
        ax.set_ylabel('Traffic Flow (trucks)', fontsize=12)
        ax.set_title('Traffic Flow Distribution (2030)', fontsize=13, fontweight='bold')
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1e6:.1f}M'))

        # Add percentage labels
        total = sum(values)
        for i, (cat, val) in enumerate(zip(categories, values)):
            pct = 100 * val / total if total > 0 else 0
            ax.text(i, val, f'{pct:.1f}%', ha='center', va='bottom', fontweight='bold')

        # Plot 3: Network topology comparison
        ax = axes[1, 0]
        topo_err = self.errors.get('topology', {})

        metrics = ['Avg Degree', 'Density\n(×1000)']
        original = [
            topo_err.get('orig_avg_degree', 0),
            topo_err.get('orig_density', 0) * 1000
        ]
        aggregated = [
            topo_err.get('agg_avg_degree', 0),
            topo_err.get('agg_density', 0) * 1000
        ]

        x = np.arange(len(metrics))
        width = 0.35

        ax.bar(x - width/2, original, width, label='Original', color='#95e1d3', edgecolor='black')
        ax.bar(x + width/2, aggregated, width, label='Aggregated', color='#f38181', edgecolor='black')

        ax.set_ylabel('Value', fontsize=12)
        ax.set_title('Network Topology Comparison', fontsize=13, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(metrics)
        ax.legend()

        # Plot 4: Error summary
        ax = axes[1, 1]
        opt_err = self.errors.get('optimization', {})

        error_types = [
            'Cost Error\n(upper bound)',
            'Infra Placement\n(vs 50km)',
            'Traffic\nAssignment'
        ]
        error_values = [
            100 * opt_err.get('cost_error_upper_bound', 0),
            100 * opt_err.get('infra_placement_error_relative', 0),
            100 * opt_err.get('traffic_assignment_error', 0)
        ]
        colors_err = ['#ff6b6b', '#feca57', '#48dbfb']

        bars = ax.barh(error_types, error_values, color=colors_err, alpha=0.7, edgecolor='black')
        ax.set_xlabel('Error (%)', fontsize=12)
        ax.set_title('Estimated Optimization Errors', fontsize=13, fontweight='bold')
        ax.axvline(x=10, color='orange', linestyle='--', alpha=0.5, label='10% threshold')
        ax.axvline(x=20, color='red', linestyle='--', alpha=0.5, label='20% threshold')
        ax.legend()

        # Add value labels
        for i, (bar, val) in enumerate(zip(bars, error_values)):
            ax.text(val + 1, i, f'{val:.1f}%', va='center', fontweight='bold')

        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"[OK] Visualization saved to: {output_file}")

    def run_full_analysis(self):
        """Execute complete error analysis."""
        print("\n" + "="*80)
        print("NUTS-3 AGGREGATION ERROR ANALYSIS")
        print("="*80)

        # Load data
        self.load_data()

        # Run analyses
        self.analyze_distance_errors()
        self.analyze_traffic_errors()
        self.analyze_network_topology_errors()
        self.estimate_optimization_error()

        # Generate outputs
        self.generate_error_report()
        self.create_visualization()

        # Print summary
        print("\n" + "="*80)
        print("ANALYSIS COMPLETE")
        print("="*80)
        print("\nOutputs generated:")
        print("  - aggregation_error_report.txt")
        print("  - aggregation_error_visualization.png")

        return self.errors


def analyze_aggregation_error(original_dir: str = "data/Trucktraffic",
                              aggregated_dir: str = "data/Trucktraffic_NUTS3"):
    """
    Convenience function to run complete error analysis.

    Parameters:
    -----------
    original_dir : str
        Directory with original data
    aggregated_dir : str
        Directory with aggregated data

    Returns:
    --------
    analyzer : AggregationErrorAnalyzer
        Analyzer with results

    Example:
    --------
    >>> analyzer = analyze_aggregation_error()
    >>> print(f"Intra-regional fraction: {analyzer.errors['distance']['intra_regional_fraction']:.1%}")
    """
    analyzer = AggregationErrorAnalyzer(original_dir, aggregated_dir)
    analyzer.run_full_analysis()
    return analyzer


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 2:
        original_dir = sys.argv[1]
        aggregated_dir = sys.argv[2]
    else:
        original_dir = "data/Trucktraffic"
        aggregated_dir = "data/Trucktraffic_NUTS3"

    print("\nStarting aggregation error analysis...")
    print(f"Original:   {original_dir}")
    print(f"Aggregated: {aggregated_dir}\n")

    analyzer = analyze_aggregation_error(original_dir, aggregated_dir)

    print("\n[SUCCESS] Done!")
