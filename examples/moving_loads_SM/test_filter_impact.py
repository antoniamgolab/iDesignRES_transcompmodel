"""
Quick test to check if filtering problematic routes reduces extra_break_time issues
"""

import yaml
import os
from collections import defaultdict
from identify_long_edge_routes import (
    analyze_problematic_routes,
    check_if_problematic_causes_high_break_time
)

# Load data
case_folder = "case_20251106_112933"
input_path = os.path.join("input_data", case_folder)

def load_yaml_file(filename):
    filepath = os.path.join(input_path, filename)
    with open(filepath, 'r') as f:
        return yaml.safe_load(f)

print("="*80)
print("LOADING DATA")
print("="*80)

input_data = {
    'Path': load_yaml_file('Path.yaml'),
    'MandatoryBreaks': load_yaml_file('MandatoryBreaks.yaml')
}

print(f"Loaded {len(input_data['Path'])} paths")
print(f"Loaded {len(input_data['MandatoryBreaks'])} mandatory breaks")

# Analyze problematic routes
print("\n" + "="*80)
print("ANALYZING PROBLEMATIC ROUTES")
print("="*80)

problematic = analyze_problematic_routes(
    input_data,
    avg_segment_threshold=500.0,
    multi_break_threshold=2
)

print(f"\nFound {len(problematic['problematic_paths'])} problematic routes:")
print(f"  - Long edges: {len(problematic['long_edge_paths'])}")
print(f"  - Multi-breaks at same node: {len(problematic['multi_break_paths'])}")

# Check if results exist
results_path = os.path.join("results", case_folder)
result_files = []

if os.path.exists(results_path):
    result_files = [f for f in os.listdir(results_path) if 'extra_break_time' in f]

if result_files:
    print(f"\n" + "="*80)
    print("CHECKING CORRELATION WITH HIGH BREAK TIMES")
    print("="*80)

    # Load the most recent results file
    result_file = os.path.join(results_path, result_files[0])
    print(f"Loading: {result_file}")

    with open(result_file, 'r') as f:
        extra_break_time_data = yaml.safe_load(f)

    # Analyze correlation
    correlation = check_if_problematic_causes_high_break_time(
        extra_break_time_data,
        problematic,
        input_data
    )

    print(f"\nTop 50 routes with highest extra_break_time:")
    print(f"  - {correlation['overlap']} of 50 ({correlation['overlap_percentage']:.1f}%) are problematic routes")
    print(f"  - This means problematic routes are", end=" ")

    if correlation['overlap_percentage'] > 30:
        print("STRONGLY CORRELATED with high break times")
    elif correlation['overlap_percentage'] > 10:
        print("MODERATELY CORRELATED with high break times")
    else:
        print("WEAKLY CORRELATED with high break times")

    # Show top 10 with details
    print(f"\n{'-'*80}")
    print("TOP 10 ROUTES WITH HIGHEST EXTRA_BREAK_TIME:")
    print(f"{'-'*80}")

    for i, route_info in enumerate(correlation['top_paths_with_details'][:10], 1):
        path_id = route_info['path_id']
        break_time = route_info['max_break_time']
        is_prob = route_info['is_problematic']
        details = route_info['details']

        print(f"\n{i}. Path {path_id}: {break_time:.2f}h extra break time")
        print(f"   Problematic: {'YES' if is_prob else 'NO'}")

        if details:
            if 'path_length' in details:
                print(f"   Length: {details['path_length']:.1f} km, "
                      f"Avg segment: {details['avg_segment_length']:.1f} km")
            if 'multi_break_nodes' in details:
                for node_info in details['multi_break_nodes']:
                    print(f"   -> Node {node_info['geo_id']}: "
                          f"{node_info['num_breaks']} breaks")

    # Calculate impact of filtering
    print(f"\n" + "="*80)
    print("FILTERING IMPACT ESTIMATE")
    print("="*80)

    # Convert values to float and sum
    total_break_time = sum(
        float(v) if isinstance(v, str) else v
        for v in extra_break_time_data.values()
        if (float(v) if isinstance(v, str) else v) > 0
    )
    problematic_ids = set(problematic['problematic_paths'])

    # Calculate break time from problematic routes
    import re
    prob_break_time = 0
    for k, v in extra_break_time_data.items():
        # Convert value to float if string
        if isinstance(v, str):
            v = float(v)

        if v > 0:
            # Parse path_id from key (which might be a string)
            if isinstance(k, str):
                numbers = re.findall(r'\d+', k)
                if len(numbers) >= 4:
                    path_id = int(numbers[2])
                    if path_id in problematic_ids:
                        prob_break_time += v
            else:
                if k[1][2] in problematic_ids:
                    prob_break_time += v

    print(f"Total extra break time: {total_break_time:.2f}h")
    print(f"From problematic routes: {prob_break_time:.2f}h ({100*prob_break_time/total_break_time:.1f}%)")
    print(f"After filtering: {total_break_time - prob_break_time:.2f}h")
    print(f"Reduction: {100*prob_break_time/total_break_time:.1f}%")

else:
    print(f"\n[INFO] No results files found in {results_path}")
    print("Run the optimization model to generate extra_break_time data")

# Save detailed info for notebook use
print(f"\n" + "="*80)
print("SAVING DETAILED RESULTS")
print("="*80)

output = {
    'problematic_paths': problematic['problematic_paths'],
    'stats': problematic['stats'],
    'path_details': {
        str(k): v for k, v in problematic['path_details'].items()
    }
}

with open('problematic_routes_detailed.yaml', 'w') as f:
    yaml.dump(output, f)

print("Saved to: problematic_routes_detailed.yaml")
print("\nYou can now use this in break_times.ipynb to filter visualizations!")
