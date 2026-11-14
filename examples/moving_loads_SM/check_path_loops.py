"""
Check if any paths visit the same geographic location multiple times
"""
import yaml
from pathlib import Path
from collections import Counter


def check_for_loops(case_name, input_dir="input_data"):
    """Check if any paths have repeated geographic elements"""
    file_path = Path(input_dir) / case_name / "Path.yaml"

    if not file_path.exists():
        print(f"[ERROR] Path.yaml not found: {file_path}")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        paths = yaml.safe_load(f)

    print("="*80)
    print("PATH LOOP ANALYSIS")
    print("="*80)
    print(f"Analyzing: {case_name}")
    print(f"Total paths: {len(paths):,}\n")

    paths_with_loops = []

    for path in paths:
        path_id = path.get('id')
        sequence = path.get('sequence', [])

        # Count occurrences of each geographic element
        element_counts = Counter(sequence)

        # Find elements that appear more than once
        repeated_elements = {elem: count for elem, count in element_counts.items() if count > 1}

        if repeated_elements:
            paths_with_loops.append({
                'path_id': path_id,
                'origin': path.get('origin'),
                'destination': path.get('destination'),
                'total_length': path.get('length'),
                'sequence_length': len(sequence),
                'repeated_elements': repeated_elements,
                'sequence': sequence
            })

    # Summary
    print(f"Paths with loops (repeated locations): {len(paths_with_loops)}")
    print(f"Percentage: {len(paths_with_loops)/len(paths)*100:.2f}%\n")

    if paths_with_loops:
        print("="*80)
        print("PATHS WITH REPEATED LOCATIONS")
        print("="*80)

        # Show first 10 examples
        for i, path_info in enumerate(paths_with_loops[:10], 1):
            print(f"\n[{i}] Path {path_info['path_id']}: "
                  f"{path_info['origin']} → {path_info['destination']}")
            print(f"    Length: {path_info['total_length']:.2f} km")
            print(f"    Sequence length: {path_info['sequence_length']} nodes")
            print(f"    Repeated locations:")
            for elem, count in path_info['repeated_elements'].items():
                print(f"      - Node {elem}: visited {count} times")

            # Show where in sequence
            seq = path_info['sequence']
            for elem, count in path_info['repeated_elements'].items():
                positions = [i for i, x in enumerate(seq) if x == elem]
                print(f"        Positions in sequence: {positions}")

        if len(paths_with_loops) > 10:
            print(f"\n... and {len(paths_with_loops) - 10} more paths with loops")

        # Statistics on repeated elements
        print("\n" + "="*80)
        print("STATISTICS ON REPEATED VISITS")
        print("="*80)

        all_repetitions = []
        for path_info in paths_with_loops:
            for count in path_info['repeated_elements'].values():
                all_repetitions.append(count)

        max_visits = max(all_repetitions)
        print(f"Maximum visits to a single location: {max_visits}")
        print(f"\nDistribution of repeat counts:")
        repeat_dist = Counter(all_repetitions)
        for count in sorted(repeat_dist.keys()):
            print(f"  {count} visits: {repeat_dist[count]} occurrences")

    else:
        print("[OK] No loops found - all paths visit each location at most once")

    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)


if __name__ == "__main__":
    case_name = "case_20251107_194948_var_var"
    check_for_loops(case_name)
