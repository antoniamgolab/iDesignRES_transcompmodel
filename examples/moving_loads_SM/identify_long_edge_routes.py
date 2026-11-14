"""
Identify and filter routes with very long edges where multiple mandatory breaks
are assigned to the same node. This can cause high extra_break_time values.

Usage in notebook:
    from identify_long_edge_routes import analyze_problematic_routes, create_route_filter

    problematic_paths = analyze_problematic_routes(input_data)
    filter_func = create_route_filter(problematic_paths, mode='exclude')
"""

import yaml
from collections import defaultdict
from typing import Dict, List, Set, Tuple


def analyze_problematic_routes(
    input_data: dict,
    avg_segment_threshold: float = 500.0,  # km
    multi_break_threshold: int = 2  # number of breaks at same node
) -> Dict[str, any]:
    """
    Identify routes with very long edges that may have multiple breaks at same node.

    Args:
        input_data: Dictionary containing Path and MandatoryBreaks data
        avg_segment_threshold: Average segment length (km) above which a path is flagged
        multi_break_threshold: Number of breaks at same node to flag as problematic

    Returns:
        Dictionary containing:
        - 'long_edge_paths': List of path IDs with long average segments
        - 'multi_break_paths': List of path IDs with multiple breaks at same node
        - 'problematic_paths': Combined set of problematic path IDs
        - 'path_details': Detailed info about each problematic path
    """

    paths = input_data['Path']
    mandatory_breaks = input_data['MandatoryBreaks']

    # =========================================================================
    # 1. Find paths with long average segments
    # =========================================================================
    long_edge_paths = []
    path_segment_info = {}

    for path in paths:
        path_id = path['id']
        path_length = path['length']
        sequence = path['sequence']
        num_segments = len(sequence) - 1

        if num_segments > 0:
            avg_segment = path_length / num_segments

            path_segment_info[path_id] = {
                'path_length': path_length,
                'num_segments': num_segments,
                'avg_segment_length': avg_segment,
                'sequence': sequence
            }

            if avg_segment >= avg_segment_threshold:
                long_edge_paths.append(path_id)

    # =========================================================================
    # 2. Find paths with multiple breaks at the same node
    # =========================================================================

    # Group breaks by path and then by node
    breaks_by_path_node = defaultdict(lambda: defaultdict(list))

    for mb in mandatory_breaks:
        path_id = mb['path_id']
        geo_id = mb['latest_geo_id']
        breaks_by_path_node[path_id][geo_id].append(mb)

    # Find paths where any node has multiple breaks
    multi_break_paths = []
    multi_break_details = {}

    for path_id, nodes in breaks_by_path_node.items():
        for geo_id, breaks in nodes.items():
            if len(breaks) >= multi_break_threshold:
                multi_break_paths.append(path_id)

                if path_id not in multi_break_details:
                    multi_break_details[path_id] = []

                multi_break_details[path_id].append({
                    'geo_id': geo_id,
                    'num_breaks': len(breaks),
                    'break_numbers': [b['break_number'] for b in breaks],
                    'cumulative_distances': [b['cumulative_distance'] for b in breaks]
                })

    # Remove duplicates
    multi_break_paths = list(set(multi_break_paths))

    # =========================================================================
    # 3. Combine and create detailed info
    # =========================================================================

    problematic_paths = set(long_edge_paths + multi_break_paths)

    path_details = {}
    for path_id in problematic_paths:
        details = {
            'path_id': path_id,
            'is_long_edge': path_id in long_edge_paths,
            'has_multi_breaks': path_id in multi_break_paths
        }

        # Add segment info if available
        if path_id in path_segment_info:
            details.update(path_segment_info[path_id])

        # Add multi-break info if available
        if path_id in multi_break_details:
            details['multi_break_nodes'] = multi_break_details[path_id]

        path_details[path_id] = details

    return {
        'long_edge_paths': long_edge_paths,
        'multi_break_paths': multi_break_paths,
        'problematic_paths': list(problematic_paths),
        'path_details': path_details,
        'stats': {
            'total_paths': len(paths),
            'num_long_edge': len(long_edge_paths),
            'num_multi_break': len(multi_break_paths),
            'num_problematic': len(problematic_paths),
            'avg_segment_threshold': avg_segment_threshold,
            'multi_break_threshold': multi_break_threshold
        }
    }


def create_route_filter(
    problematic_routes: Dict,
    mode: str = 'exclude'
) -> callable:
    """
    Create a filter function to include/exclude problematic routes.

    Args:
        problematic_routes: Output from analyze_problematic_routes()
        mode: 'exclude' to filter out problematic routes, 'include' to keep only them

    Returns:
        Function that takes a path_id and returns True if it should be kept
    """
    problematic_path_ids = set(problematic_routes['problematic_paths'])

    if mode == 'exclude':
        # Return True if path should be KEPT (i.e., not problematic)
        return lambda path_id: path_id not in problematic_path_ids
    elif mode == 'include':
        # Return True if path is problematic (only keep problematic ones)
        return lambda path_id: path_id in problematic_path_ids
    else:
        raise ValueError(f"mode must be 'exclude' or 'include', got '{mode}'")


def print_problematic_routes_summary(problematic_routes: Dict):
    """
    Print a summary of problematic routes found.
    """
    stats = problematic_routes['stats']

    print("="*80)
    print("PROBLEMATIC ROUTES ANALYSIS")
    print("="*80)
    print(f"\nTotal paths analyzed: {stats['total_paths']}")
    print(f"Average segment threshold: {stats['avg_segment_threshold']:.1f} km")
    print(f"Multi-break threshold: {stats['multi_break_threshold']} breaks per node")
    print()
    print(f"Paths with long edges: {stats['num_long_edge']}")
    print(f"Paths with multiple breaks at same node: {stats['num_multi_break']}")
    print(f"Total problematic paths: {stats['num_problematic']}")
    print(f"Percentage problematic: {100*stats['num_problematic']/stats['total_paths']:.1f}%")

    # Show some examples
    print("\n" + "-"*80)
    print("EXAMPLE PROBLEMATIC PATHS (first 10):")
    print("-"*80)

    path_details = problematic_routes['path_details']
    for i, (path_id, details) in enumerate(list(path_details.items())[:10]):
        print(f"\nPath {path_id}:")
        if 'path_length' in details:
            print(f"  Length: {details['path_length']:.1f} km")
            print(f"  Segments: {details['num_segments']}")
            print(f"  Avg segment: {details['avg_segment_length']:.1f} km")

        if details['is_long_edge']:
            print(f"  [!] Has long edges")

        if details['has_multi_breaks'] and 'multi_break_nodes' in details:
            print(f"  [!] Multiple breaks at same node:")
            for node_info in details['multi_break_nodes']:
                print(f"      Node {node_info['geo_id']}: "
                      f"{node_info['num_breaks']} breaks "
                      f"(breaks #{node_info['break_numbers']})")


def filter_dataframe_by_routes(
    df,
    problematic_routes: Dict,
    path_column: str = 'path_id',
    mode: str = 'exclude'
):
    """
    Filter a DataFrame to include/exclude problematic routes.

    Args:
        df: DataFrame with route data
        problematic_routes: Output from analyze_problematic_routes()
        path_column: Name of column containing path IDs
        mode: 'exclude' to remove problematic routes, 'include' to keep only them

    Returns:
        Filtered DataFrame
    """
    filter_func = create_route_filter(problematic_routes, mode=mode)
    mask = df[path_column].apply(filter_func)
    return df[mask]


# ===========================================================================
# HELPER FUNCTIONS FOR SPECIFIC ANALYSES
# ===========================================================================

def get_routes_with_highest_break_time(
    extra_break_time_data: dict,
    input_data: dict,
    top_n: int = 20
) -> List[Tuple[int, float]]:
    """
    Get routes with highest extra_break_time values.

    Args:
        extra_break_time_data: The extra_break_time dictionary from results
        input_data: Input data with Path information
        top_n: Number of top routes to return

    Returns:
        List of (path_id, max_extra_break_time) tuples
    """
    # Aggregate extra_break_time by path_id
    path_break_times = defaultdict(float)

    for key, value in extra_break_time_data.items():
        # Convert value to float if it's a string
        if isinstance(value, str):
            value = float(value)

        if value > 0:
            # Key is a string like "(2028, (1, 1, 5409, 68), 1, 2028)"
            # Parse it to extract path_id
            if isinstance(key, str):
                # Extract path_id from string representation
                # Format: (year, (prod_id, od_id, path_id, geo_id), tv_id, gen)
                try:
                    # Quick parsing: find the 3rd number in the inner tuple
                    import re
                    numbers = re.findall(r'\d+', key)
                    if len(numbers) >= 4:
                        path_id = int(numbers[2])  # 3rd number is path_id
                    else:
                        continue
                except:
                    continue
            else:
                # Key format: (year, (prod_id, od_id, path_id, geo_id), tv_id, gen)
                path_id = key[1][2]

            path_break_times[path_id] = max(path_break_times[path_id], value)

    # Sort by break time
    sorted_paths = sorted(path_break_times.items(), key=lambda x: x[1], reverse=True)

    return sorted_paths[:top_n]


def check_if_problematic_causes_high_break_time(
    extra_break_time_data: dict,
    problematic_routes: Dict,
    input_data: dict
) -> Dict:
    """
    Check correlation between problematic routes and high extra_break_time.

    Returns:
        Dictionary with analysis results
    """
    top_break_time_paths = get_routes_with_highest_break_time(
        extra_break_time_data, input_data, top_n=50
    )

    top_path_ids = [p[0] for p in top_break_time_paths]
    problematic_path_ids = set(problematic_routes['problematic_paths'])

    overlap = set(top_path_ids) & problematic_path_ids

    return {
        'top_50_high_break_time': len(top_path_ids),
        'problematic_routes_total': len(problematic_path_ids),
        'overlap': len(overlap),
        'overlap_percentage': 100 * len(overlap) / len(top_path_ids) if top_path_ids else 0,
        'overlapping_path_ids': list(overlap),
        'top_paths_with_details': [
            {
                'path_id': path_id,
                'max_break_time': break_time,
                'is_problematic': path_id in problematic_path_ids,
                'details': problematic_routes['path_details'].get(path_id, {})
            }
            for path_id, break_time in top_break_time_paths
        ]
    }


if __name__ == "__main__":
    """
    Example standalone usage
    """
    import os

    # Load data
    case_folder = "case_20251106_112933"
    input_path = os.path.join("input_data", case_folder)

    def load_yaml(filename):
        filepath = os.path.join(input_path, filename)
        with open(filepath, 'r') as f:
            return yaml.safe_load(f)

    input_data = {
        'Path': load_yaml('Path.yaml'),
        'MandatoryBreaks': load_yaml('MandatoryBreaks.yaml')
    }

    # Analyze
    problematic = analyze_problematic_routes(
        input_data,
        avg_segment_threshold=500.0,  # Flag paths with >500km average segments
        multi_break_threshold=2  # Flag nodes with 2+ breaks
    )

    # Print summary
    print_problematic_routes_summary(problematic)

    # Save to file for use in notebook
    print("\n" + "="*80)
    print("SAVING RESULTS")
    print("="*80)

    output_file = "problematic_routes.yaml"
    with open(output_file, 'w') as f:
        yaml.dump({
            'problematic_paths': problematic['problematic_paths'],
            'stats': problematic['stats']
        }, f)

    print(f"Saved problematic route IDs to: {output_file}")
    print("You can load this in your notebook to filter visualizations")
