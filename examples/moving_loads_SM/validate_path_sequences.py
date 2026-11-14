"""
Validate Path Sequences - Check if DE->IT routes physically pass through Austria

This script analyzes Path.yaml to check if the node sequences make geographic sense.
Routes from Germany to Italy should pass through Austria, not "teleport" directly.
"""
import yaml
from pathlib import Path
from collections import Counter


def load_case_data(case_dir):
    """Load GeographicElement.yaml and Path.yaml"""
    geo_file = Path(case_dir) / "GeographicElement.yaml"
    path_file = Path(case_dir) / "Path.yaml"

    with open(geo_file, 'r', encoding='utf-8') as f:
        geo_elements = yaml.safe_load(f)

    with open(path_file, 'r', encoding='utf-8') as f:
        paths = yaml.safe_load(f)

    return geo_elements, paths


def analyze_path_sequences(geo_elements, paths):
    """Analyze path sequences for geographic validity"""

    print("="*80)
    print("PATH SEQUENCE VALIDATION")
    print("="*80)

    # Build node lookup
    nodes = [g for g in geo_elements if g['type'] == 'node']
    node_lookup = {n['id']: n for n in nodes}

    print(f"\nTotal nodes: {len(nodes)}")
    print(f"Total paths: {len(paths)}")

    # Analyze each path
    print("\n" + "="*80)
    print("ANALYZING PATH SEQUENCES:")
    print("="*80)

    problem_paths = []
    de_it_paths = []
    de_at_it_paths = []

    for path in paths:
        path_id = path.get('id')
        sequence = path.get('sequence', [])
        length = path.get('length', 0)

        if len(sequence) < 2:
            continue

        # Get countries for each node in sequence
        countries = []
        for node_id in sequence:
            node = node_lookup.get(node_id)
            if node:
                country = node.get('country', 'XX')
                countries.append(country)
            else:
                countries.append('UNKNOWN')

        # Check origin and destination
        origin_country = countries[0]
        dest_country = countries[-1]

        # Check for DE->IT or IT->DE paths
        if (origin_country == 'DE' and dest_country == 'IT') or (origin_country == 'IT' and dest_country == 'DE'):
            de_it_paths.append((path_id, sequence, countries, length))

            # Check if Austria is in the path
            if 'AT' in countries:
                de_at_it_paths.append((path_id, sequence, countries, length))
            else:
                problem_paths.append((path_id, sequence, countries, length))

    # Report findings
    print(f"\nDE <-> IT paths found: {len(de_it_paths)}")
    print(f"  Correctly routed via Austria: {len(de_at_it_paths)}")
    print(f"  [WARNING] PROBLEMATIC (skip Austria): {len(problem_paths)}")

    if problem_paths:
        print("\n" + "="*80)
        print("PROBLEMATIC PATHS (DE/IT without passing through Austria):")
        print("="*80)

        for i, (path_id, sequence, countries, length) in enumerate(problem_paths[:10]):
            print(f"\nPath {path_id}:")
            print(f"  Length: {length:.1f} km")
            print(f"  Sequence length: {len(sequence)} nodes")
            print(f"  Countries: {' -> '.join(countries)}")
            print(f"  Node IDs: {sequence}")

            # Check for direct jumps
            for j in range(len(countries) - 1):
                if countries[j] == 'DE' and countries[j+1] == 'IT':
                    print(f"  [WARNING] DIRECT JUMP: DE node {sequence[j]} -> IT node {sequence[j+1]}")
                elif countries[j] == 'IT' and countries[j+1] == 'DE':
                    print(f"  [WARNING] DIRECT JUMP: IT node {sequence[j]} -> DE node {sequence[j+1]}")

        if len(problem_paths) > 10:
            print(f"\n... and {len(problem_paths) - 10} more problematic paths")

    if de_at_it_paths:
        print("\n" + "="*80)
        print("CORRECT PATHS (DE <-> IT via Austria):")
        print("="*80)

        for i, (path_id, sequence, countries, length) in enumerate(de_at_it_paths[:5]):
            print(f"\nPath {path_id}:")
            print(f"  Length: {length:.1f} km")
            print(f"  Countries: {' -> '.join(countries)}")
            print(f"  Node IDs: {sequence}")

        if len(de_at_it_paths) > 5:
            print(f"\n... and {len(de_at_it_paths) - 5} more correct paths")

    # Summary statistics
    print("\n" + "="*80)
    print("SUMMARY:")
    print("="*80)

    total_paths = len(paths)
    de_it_count = len(de_it_paths)
    correct_count = len(de_at_it_paths)
    problem_count = len(problem_paths)

    print(f"\nTotal paths: {total_paths}")
    print(f"DE <-> IT paths: {de_it_count} ({de_it_count/total_paths*100:.1f}%)")
    print(f"  [OK] Correct (via Austria): {correct_count} ({correct_count/de_it_count*100:.1f}% of DE-IT)" if de_it_count > 0 else "  [OK] Correct (via Austria): 0")
    print(f"  [X] Problematic (skip Austria): {problem_count} ({problem_count/de_it_count*100:.1f}% of DE-IT)" if de_it_count > 0 else "  [X] Problematic (skip Austria): 0")

    # Analyze all path lengths by country transition
    print("\n" + "="*80)
    print("PATH ANALYSIS BY ORIGIN-DESTINATION:")
    print("="*80)

    od_pairs = Counter()
    for path in paths:
        sequence = path.get('sequence', [])
        if len(sequence) < 2:
            continue

        origin_node = node_lookup.get(sequence[0])
        dest_node = node_lookup.get(sequence[-1])

        if origin_node and dest_node:
            origin_country = origin_node.get('country', 'XX')
            dest_country = dest_node.get('country', 'XX')
            od_pairs[(origin_country, dest_country)] += 1

    print(f"\nMost common country pairs:")
    for (orig, dest), count in od_pairs.most_common(20):
        print(f"  {orig} → {dest}: {count} paths")

    print("\n" + "="*80)

    return {
        'total_paths': total_paths,
        'de_it_paths': de_it_count,
        'correct_paths': correct_count,
        'problem_paths': problem_count
    }


def main():
    """Main function"""
    # Check most recent case directory
    input_data_dir = Path("input_data")

    # Find all case directories
    case_dirs = [d for d in input_data_dir.iterdir() if d.is_dir() and d.name.startswith("case_")]

    if not case_dirs:
        print("No case directories found in input_data/")
        return

    # Use most recent case
    most_recent = max(case_dirs, key=lambda d: d.stat().st_mtime)

    print(f"\nAnalyzing: {most_recent}")
    print("="*80)

    geo_elements, paths = load_case_data(most_recent)
    results = analyze_path_sequences(geo_elements, paths)

    # Final verdict
    print("\n" + "="*80)
    print("VERDICT:")
    print("="*80)

    if results['problem_paths'] == 0:
        print("\n[OK] ALL DE-IT PATHS CORRECTLY ROUTE THROUGH AUSTRIA!")
        print("  The Italy-Austria filter in SM_preprocessing.py may no longer be needed.")
    else:
        print(f"\n[WARNING] {results['problem_paths']} DE-IT PATHS SKIP AUSTRIA!")
        print("  The Italy-Austria filter is still necessary to prevent physically impossible routes.")
        print("  Root cause: Pathfinding creates direct DE-IT connections without intermediate nodes.")


if __name__ == "__main__":
    main()
