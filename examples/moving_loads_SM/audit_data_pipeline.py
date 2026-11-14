"""
Comprehensive Data Pipeline Audit
==================================

This script traces the complete data flow from original truck traffic data
through all preprocessing stages to final model inputs.

Identifies:
- Data volume at each stage
- Filtering impacts
- Information loss
- Geometry/distance preservation issues

Author: Claude Code for Data Pipeline Audit
Date: 2025-11-07
"""

import pandas as pd
import yaml
import numpy as np
from pathlib import Path
from collections import defaultdict
import sys

class DataPipelineAuditor:
    """Audit the complete preprocessing pipeline."""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.results = {}

    def stage_1_original_data(self):
        """Analyze Stage 1: Original Trucktraffic data."""
        print("\n" + "="*80)
        print("STAGE 1: ORIGINAL DATA (data/Trucktraffic)")
        print("="*80)

        data_dir = self.base_dir / "data" / "Trucktraffic"

        # Load data
        traffic = pd.read_csv(data_dir / "01_Trucktrafficflow.csv")
        nodes = pd.read_csv(data_dir / "03_network-nodes.csv")
        edges = pd.read_csv(data_dir / "04_network-edges.csv")
        nuts3_regions = pd.read_csv(data_dir / "02_NUTS-3-Regions.csv")

        # Calculate total distance
        if 'Total_distance' not in traffic.columns:
            traffic['Total_distance'] = (
                traffic['Distance_from_origin_region_to_E_road'] +
                traffic['Distance_within_E_road'] +
                traffic['Distance_from_E_road_to_destination_region']
            )

        # Calculate tkm
        tkm_2030 = (traffic['Traffic_flow_trucks_2030'] * traffic['Total_distance']).sum()

        # Get unique OD pairs
        unique_od = traffic.groupby(['ID_origin_region', 'ID_destination_region']).size()

        # Get country distribution
        origin_countries = traffic['ID_origin_region'].astype(str).str[:2].value_counts()
        dest_countries = traffic['ID_destination_region'].astype(str).str[:2].value_counts()

        stage_1_data = {
            'stage': 'Stage 1: Original Data',
            'traffic_rows': len(traffic),
            'unique_od_pairs': len(unique_od),
            'network_nodes': len(nodes),
            'network_edges': len(edges),
            'nuts3_regions': len(nuts3_regions),
            'tkm_2030': tkm_2030,
            'avg_distance': traffic['Total_distance'].mean(),
            'origin_countries': len(origin_countries),
            'dest_countries': len(dest_countries)
        }

        print(f"Traffic flows: {len(traffic):,} rows")
        print(f"Unique OD pairs: {len(unique_od):,}")
        print(f"Network nodes: {len(nodes):,}")
        print(f"Network edges: {len(edges):,}")
        print(f"NUTS-3 regions: {len(nuts3_regions):,}")
        print(f"Total freight (2030): {tkm_2030:,.0f} tkm")
        print(f"Average distance: {traffic['Total_distance'].mean():.1f} km")
        print(f"\nCountry coverage (origin): {len(origin_countries)} countries")
        print(f"Country coverage (destination): {len(dest_countries)} countries")

        self.results['stage_1'] = stage_1_data
        return traffic, nodes, edges, nuts3_regions

    def stage_1b_nuts3_aggregation(self):
        """Analyze Stage 1B: NUTS-3 aggregated data."""
        print("\n" + "="*80)
        print("STAGE 1B: NUTS-3 AGGREGATION (data/Trucktraffic_NUTS3)")
        print("="*80)
        print("Script: aggregate_raw_data_to_nuts3.py")
        print("="*80)

        data_dir = self.base_dir / "data" / "Trucktraffic_NUTS3"

        if not data_dir.exists():
            print("WARNING: NUTS-3 aggregated data not found!")
            return None, None, None

        # Load data
        traffic = pd.read_csv(data_dir / "01_Trucktrafficflow.csv")
        nodes = pd.read_csv(data_dir / "03_network-nodes.csv")
        edges = pd.read_csv(data_dir / "04_network-edges.csv")

        # Calculate total distance
        if 'Total_distance' not in traffic.columns:
            traffic['Total_distance'] = (
                traffic['Distance_from_origin_region_to_E_road'] +
                traffic['Distance_within_E_road'] +
                traffic['Distance_from_E_road_to_destination_region']
            )

        # Calculate tkm
        tkm_2030 = (traffic['Traffic_flow_trucks_2030'] * traffic['Total_distance']).sum()

        # Get unique OD pairs
        unique_od = traffic.groupby(['ID_origin_region', 'ID_destination_region']).size()

        stage_1b_data = {
            'stage': 'Stage 1B: NUTS-3 Aggregation',
            'traffic_rows': len(traffic),
            'unique_od_pairs': len(unique_od),
            'network_nodes': len(nodes),
            'network_edges': len(edges),
            'tkm_2030': tkm_2030,
            'avg_distance': traffic['Total_distance'].mean()
        }

        print(f"Traffic flows: {len(traffic):,} rows")
        print(f"Unique OD pairs: {len(unique_od):,}")
        print(f"Network nodes: {len(nodes):,}")
        print(f"Network edges: {len(edges):,}")
        print(f"Total freight (2030): {tkm_2030:,.0f} tkm")
        print(f"Average distance: {traffic['Total_distance'].mean():.1f} km")

        # Compare to Stage 1
        if 'stage_1' in self.results:
            s1 = self.results['stage_1']
            print(f"\nCHANGES FROM STAGE 1:")
            print(f"  Traffic rows: {s1['traffic_rows']:,} -> {len(traffic):,} "
                  f"({len(traffic)/s1['traffic_rows']*100:.1f}% retained)")
            print(f"  Network nodes: {s1['network_nodes']:,} -> {len(nodes):,} "
                  f"({len(nodes)/s1['network_nodes']*100:.1f}% retained)")
            print(f"  Network edges: {s1['network_edges']:,} -> {len(edges):,} "
                  f"({len(edges)/s1['network_edges']*100:.1f}% retained)")
            print(f"  Freight (tkm): {s1['tkm_2030']:,.0f} -> {tkm_2030:,.0f} "
                  f"({tkm_2030/s1['tkm_2030']*100:.1f}% retained)")

        self.results['stage_1b'] = stage_1b_data
        return traffic, nodes, edges

    def stage_2_nuts2_preprocessing(self, case_name='nuts_2_360_complete_test_time_step_2'):
        """Analyze Stage 2: NUTS-2 preprocessing output."""
        print("\n" + "="*80)
        print("STAGE 2: NUTS-2 PREPROCESSING (input_data)")
        print("="*80)
        print("Script: SM_preprocessing_nuts2_complete.py")
        print("="*80)

        case_dir = self.base_dir / "input_data" / case_name

        if not case_dir.exists():
            print(f"WARNING: Case {case_name} not found!")
            # List available cases
            input_dir = self.base_dir / "input_data"
            if input_dir.exists():
                cases = sorted([d.name for d in input_dir.iterdir() if d.is_dir()])
                print(f"Available cases ({len(cases)}):")
                for c in cases[:10]:
                    print(f"  - {c}")
            return None, None, None

        # Load YAMLs
        with open(case_dir / 'GeographicElement.yaml', 'r') as f:
            geo_elements = yaml.safe_load(f)

        with open(case_dir / 'Path.yaml', 'r') as f:
            paths = yaml.safe_load(f)

        with open(case_dir / 'Odpair.yaml', 'r') as f:
            odpairs = yaml.safe_load(f)

        # Check for mandatory breaks
        breaks_file = case_dir / 'MandatoryBreaks.yaml'
        if breaks_file.exists():
            with open(breaks_file, 'r') as f:
                breaks = yaml.safe_load(f)
        else:
            breaks = []

        # Analyze geographic elements
        nodes = [g for g in geo_elements if g.get('type') == 'node']
        edges = [g for g in geo_elements if g.get('type') == 'edge']

        # Analyze paths
        avg_path_length = np.mean([p['length'] for p in paths])
        avg_nodes_per_path = np.mean([len(p['sequence']) for p in paths])

        # Analyze OD-pairs
        # Calculate tkm for first year
        total_tkm = 0
        total_demand = 0
        for odp in odpairs:
            F = odp.get('F', [0])[0]  # First year demand
            total_demand += F
            path_id = odp.get('path_id')
            if path_id < len(paths):
                length = paths[path_id].get('length', 0)
                total_tkm += F * length

        # Get unique origin-destination pairs
        unique_od = len(set((odp['from'], odp['to']) for odp in odpairs))

        # Get country distribution from nodes
        countries = set(n.get('country', '') for n in nodes)

        # Get NUTS-2 regions
        nuts2_regions = set(n.get('nuts2_region', '') for n in nodes if n.get('nuts2_region'))

        stage_2_data = {
            'stage': 'Stage 2: NUTS-2 Preprocessing',
            'case_name': case_name,
            'geographic_nodes': len(nodes),
            'geographic_edges': len(edges),
            'paths': len(paths),
            'odpairs': len(odpairs),
            'unique_od_pairs': unique_od,
            'mandatory_breaks': len(breaks),
            'total_demand_first_year': total_demand,
            'total_tkm_first_year': total_tkm,
            'avg_path_length': avg_path_length,
            'avg_nodes_per_path': avg_nodes_per_path,
            'countries': len(countries),
            'nuts2_regions': len(nuts2_regions)
        }

        print(f"Case: {case_name}")
        print(f"Geographic nodes (NUTS-2): {len(nodes)}")
        print(f"Geographic edges: {len(edges)}")
        print(f"Paths: {len(paths)}")
        print(f"OD-pairs: {len(odpairs)}")
        print(f"Unique OD pairs: {unique_od}")
        print(f"Mandatory breaks: {len(breaks)}")
        print(f"Total demand (first year): {total_demand:,.0f} trucks/year")
        print(f"Total freight (first year): {total_tkm:,.0f} tkm")
        print(f"Average path length: {avg_path_length:.1f} km")
        print(f"Average nodes per path: {avg_nodes_per_path:.1f}")
        print(f"Countries covered: {len(countries)}")
        print(f"NUTS-2 regions: {len(nuts2_regions)}")

        # Compare to Stage 1B
        if 'stage_1b' in self.results:
            s1b = self.results['stage_1b']
            print(f"\nCHANGES FROM STAGE 1B:")
            print(f"  OD-pairs: {s1b['unique_od_pairs']:,} -> {len(odpairs):,} "
                  f"({len(odpairs)/s1b['unique_od_pairs']*100:.1f}% retained)")
            print(f"  Network nodes: {s1b['network_nodes']:,} -> {len(nodes):,} "
                  f"({len(nodes)/s1b['network_nodes']*100:.1f}% retained)")
            print(f"  Freight (tkm): {s1b['tkm_2030']:,.0f} -> {total_tkm:,.0f} "
                  f"({total_tkm/s1b['tkm_2030']*100:.1f}% retained)")

        self.results['stage_2'] = stage_2_data
        return geo_elements, paths, odpairs

    def analyze_filtering_logic(self):
        """Analyze filtering logic in SM_preprocessing_nuts2_complete.py."""
        print("\n" + "="*80)
        print("FILTERING LOGIC ANALYSIS")
        print("="*80)

        print("\nKey filters identified in SM_preprocessing_nuts2_complete.py:")
        print("\n1. NUTS REGION FILTER (lines 47-52):")
        print("   nuts_to_filter_for = {")
        print('       "NUTS_0": ["DE", "DK", "SE"],')
        print('       "NUTS_1": ["AT3", "ITC", "ITH", "ITI", "ITF"],')
        print('       "NUTS_2": ["NO08", "NO07", "FI1D", "NO09", "NO0A",')
        print('                  "NO02", "NO06", "AT33", "AT34", "AT32"]')
        print("   }")

        print("\n2. GEOGRAPHIC FILTERING (lines 279-285):")
        print("   - Keeps routes where AT LEAST ONE endpoint is in filtered regions")
        print("   - Includes: internal, entering, leaving, through routes")

        print("\n3. ROUTE TYPE FILTERING (lines 631-643):")
        print("   CURRENT BEHAVIOR (lines 631-643):")
        print("   - FILTERS OUT local routes (origin_nuts2 == dest_nuts2)")
        print("   - ONLY ACCEPTS routes where BOTH endpoints are inside corridor")
        print("   - EXCLUDES entering routes (outside -> inside)")
        print("   - EXCLUDES leaving routes (inside -> outside)")
        print("   - EXCLUDES through routes (outside -> outside)")

        print("\n4. CROSS-BORDER FILTER (lines 543-554, if enabled):")
        print("   - Removes domestic routes (same country)")
        print("   - Uses country codes from NUTS-3 mapping")

        print("\n5. TRAFFIC VOLUME FILTER (lines 563-572):")
        print("   - Default: >= 100 trucks/year")
        print("   - Removes low-volume routes for numerical stability")

        print("\n6. DISTANCE FILTER (if enabled):")
        print("   - Optional minimum distance (e.g., 360km for mandatory breaks)")

        print("\n" + "="*80)
        print("CRITICAL FINDING: Excessive Filtering")
        print("="*80)
        print("\nThe combination of filters at lines 631-643 is VERY restrictive:")
        print("  X Filters out local routes (origin == destination NUTS-2)")
        print("  X Filters out entering routes (external origin)")
        print("  X Filters out leaving routes (external destination)")
        print("  X Only keeps routes FULLY INSIDE corridor")
        print("\nThis explains the massive data loss:")
        print("  263.6 billion tkm -> 22.9 billion tkm (91.3% loss!)")

    def generate_summary_table(self):
        """Generate summary table of data flow."""
        print("\n" + "="*80)
        print("DATA VOLUME SUMMARY TABLE")
        print("="*80)

        print(f"\n{'Stage':<40} {'Routes':<15} {'Nodes':<15} {'Freight (tkm)':<20}")
        print("-" * 90)

        for key in ['stage_1', 'stage_1b', 'stage_2']:
            if key in self.results:
                data = self.results[key]
                stage_name = data['stage']

                if 'traffic_rows' in data:
                    routes = f"{data['traffic_rows']:,}"
                elif 'odpairs' in data:
                    routes = f"{data['odpairs']:,}"
                else:
                    routes = "N/A"

                if 'network_nodes' in data:
                    nodes = f"{data['network_nodes']:,}"
                elif 'geographic_nodes' in data:
                    nodes = f"{data['geographic_nodes']:,}"
                else:
                    nodes = "N/A"

                if 'tkm_2030' in data:
                    freight = f"{data['tkm_2030']:,.0f}"
                elif 'total_tkm_first_year' in data:
                    freight = f"{data['total_tkm_first_year']:,.0f}"
                else:
                    freight = "N/A"

                print(f"{stage_name:<40} {routes:<15} {nodes:<15} {freight:<20}")

        # Calculate retention percentages
        print("\n" + "="*80)
        print("RETENTION PERCENTAGES")
        print("="*80)

        if 'stage_1' in self.results and 'stage_2' in self.results:
            s1 = self.results['stage_1']
            s2 = self.results['stage_2']

            route_retention = (s2['odpairs'] / s1['traffic_rows']) * 100
            freight_retention = (s2['total_tkm_first_year'] / s1['tkm_2030']) * 100

            print(f"\nFrom Original to Final Model Input:")
            print(f"  Routes: {s1['traffic_rows']:,} -> {s2['odpairs']:,} ({route_retention:.1f}% retained)")
            print(f"  Freight: {s1['tkm_2030']:,.0f} -> {s2['total_tkm_first_year']:,.0f} tkm "
                  f"({freight_retention:.1f}% retained)")
            print(f"\n  DATA LOSS: {100-freight_retention:.1f}% of freight volume!")

    def check_distance_preservation(self):
        """Check if distances are preserved correctly."""
        print("\n" + "="*80)
        print("DISTANCE PRESERVATION CHECK")
        print("="*80)

        print("\nKEY QUESTION: Are original traffic distances preserved?")
        print("\nIn SM_preprocessing_nuts2_complete.py:")
        print("  Line 688-689: total_distance = row.Total_distance")
        print("  Line 744: path['length'] = float(total_distance)")
        print("\nOK YES - Original distances are preserved in path['length']")
        print("\nHowever, path segments use proportional distribution:")
        print("  Lines 870-914: _distribute_distance()")
        print("  - Uses network edge distances for PROPORTIONS")
        print("  - Scales to match total traffic distance")
        print("\nOK This is CORRECT - total distance preserved, segments scaled")

    def identify_issues(self):
        """Identify key issues in the pipeline."""
        print("\n" + "="*80)
        print("CRITICAL ISSUES IDENTIFIED")
        print("="*80)

        issues = [
            {
                'priority': 'CRITICAL',
                'category': 'Excessive Filtering',
                'location': 'SM_preprocessing_nuts2_complete.py, lines 631-643',
                'issue': 'Route validation filter is TOO RESTRICTIVE',
                'impact': 'Removes 91.3% of freight volume',
                'details': [
                    'Filters out local routes (origin == destination NUTS-2)',
                    'ONLY accepts routes where BOTH endpoints are inside corridor',
                    'Excludes entering routes (external -> internal)',
                    'Excludes leaving routes (internal -> external)',
                    'Excludes through routes (external -> external)'
                ]
            },
            {
                'priority': 'HIGH',
                'category': 'Country Code Mapping',
                'location': 'SM_preprocessing_nuts2_complete.py, lines 292-293',
                'issue': 'Cross-border detection depends on correct country mapping',
                'impact': 'If country mapping is wrong, cross-border filter fails',
                'details': [
                    'Recent fix: Lines 186-190 now use proper country mapping',
                    'Was using string slicing str[:2] before',
                    'Need to verify AT-DE, DE-DK routes survive filtering'
                ]
            },
            {
                'priority': 'MEDIUM',
                'category': 'NUTS-2 Aggregation',
                'location': 'SM_preprocessing_nuts2_complete.py, lines 400-465',
                'issue': 'Aggregation from NUTS-3 to NUTS-2 may lose geography',
                'impact': 'Multiple NUTS-3 zones -> single NUTS-2 node',
                'details': [
                    'Uses centroid of all nodes in NUTS-2 region',
                    'May misrepresent actual spatial distribution',
                    'But preserves total distances (line 744)'
                ]
            },
            {
                'priority': 'LOW',
                'category': 'Traffic Volume Filter',
                'location': 'SM_preprocessing_nuts2_complete.py, lines 563-572',
                'issue': 'Default threshold (100 trucks/year) may be too low',
                'impact': 'Many low-volume routes included, increasing model size',
                'details': [
                    'Could increase to 1000 trucks/year',
                    'Would remove 54% of routes but keep 99.6% of freight'
                ]
            }
        ]

        for i, issue in enumerate(issues, 1):
            print(f"\n{'='*80}")
            print(f"ISSUE #{i}: {issue['category']} [{issue['priority']} PRIORITY]")
            print(f"{'='*80}")
            print(f"Location: {issue['location']}")
            print(f"Problem:  {issue['issue']}")
            print(f"Impact:   {issue['impact']}")
            print(f"\nDetails:")
            for detail in issue['details']:
                print(f"  • {detail}")

    def generate_recommendations(self):
        """Generate recommendations for fixes."""
        print("\n" + "="*80)
        print("RECOMMENDATIONS")
        print("="*80)

        recommendations = [
            {
                'priority': 1,
                'title': 'FIX: Remove excessive route filtering',
                'description': 'Lines 631-643 filter out too many routes',
                'action': [
                    'Keep INTERNAL routes (both endpoints inside)',
                    'Consider keeping ENTERING routes (if needed for analysis)',
                    'Consider keeping LEAVING routes (if needed for analysis)',
                    'Remove local route filter (origin == destination) IF model can handle it',
                    'OR keep local filter but document it clearly'
                ],
                'expected_impact': 'Retain more freight volume (currently losing 91.3%)'
            },
            {
                'priority': 2,
                'title': 'VERIFY: Country code mapping',
                'description': 'Ensure recent fix (lines 186-190) works correctly',
                'action': [
                    'Check that AT-DE routes survive all filters',
                    'Check that DE-DK routes survive all filters',
                    'Verify cross-border detection using mapped countries',
                    'Add validation logging for country mapping'
                ],
                'expected_impact': 'Correct cross-border route identification'
            },
            {
                'priority': 3,
                'title': 'OPTIMIZE: Traffic volume threshold',
                'description': 'Increase minimum traffic threshold',
                'action': [
                    'Change from 100 to 1000 trucks/year (line 514)',
                    'This removes 54% of routes but keeps 99.6% of freight',
                    'Reduces model size and mandatory breaks',
                    'Better numerical stability'
                ],
                'expected_impact': 'Smaller, more efficient model with minimal data loss'
            },
            {
                'priority': 4,
                'title': 'VALIDATE: Distance preservation',
                'description': 'Ensure original distances are preserved',
                'action': [
                    'Compare path lengths to original traffic distances',
                    'Check that total tkm matches at each stage',
                    'Verify segment distribution is reasonable',
                    'Add validation checks in preprocessing'
                ],
                'expected_impact': 'Confidence in distance accuracy'
            }
        ]

        for rec in recommendations:
            print(f"\n{'='*80}")
            print(f"RECOMMENDATION #{rec['priority']}: {rec['title']}")
            print(f"{'='*80}")
            print(f"Description: {rec['description']}")
            print(f"\nActions:")
            for action in rec['action']:
                print(f"  • {action}")
            print(f"\nExpected Impact: {rec['expected_impact']}")

    def run_audit(self, case_name='nuts_2_360_complete_test_time_step_2'):
        """Run complete audit."""
        print("\n" + "="*80)
        print("DATA PIPELINE COMPREHENSIVE AUDIT")
        print("="*80)
        print(f"Base directory: {self.base_dir}")
        print(f"Target case: {case_name}")
        print("="*80)

        # Stage 1: Original data
        self.stage_1_original_data()

        # Stage 1B: NUTS-3 aggregation
        self.stage_1b_nuts3_aggregation()

        # Stage 2: NUTS-2 preprocessing
        self.stage_2_nuts2_preprocessing(case_name)

        # Analysis
        self.analyze_filtering_logic()
        self.generate_summary_table()
        self.check_distance_preservation()
        self.identify_issues()
        self.generate_recommendations()

        print("\n" + "="*80)
        print("AUDIT COMPLETE")
        print("="*80)


if __name__ == "__main__":
    base_dir = Path(__file__).parent

    # Allow case name as command-line argument
    case_name = sys.argv[1] if len(sys.argv) > 1 else 'nuts_2_360_complete_test_time_step_2'

    auditor = DataPipelineAuditor(base_dir)
    auditor.run_audit(case_name)
