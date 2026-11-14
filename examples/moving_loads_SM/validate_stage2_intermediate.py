"""
Validate Stage 2 Intermediate Data - Check if Italy-Austria filter is actually needed

This checks the INTERMEDIATE data (after SM_preprocessing_nuts2_complete.py,
BEFORE SM_preprocessing.py) to see if there are problematic Italy paths.
"""
import yaml
from pathlib import Path


def check_stage2_data():
    """Check intermediate Stage 2 data for Italy-Austria paths"""

    print("="*80)
    print("VALIDATING STAGE 2 INTERMEDIATE DATA")
    print("="*80)

    # Load intermediate files from input_data/
    geo_file = Path("input_data/GeographicElement.yaml")
    path_file = Path("input_data/Path.yaml")

    if not geo_file.exists() or not path_file.exists():
        print("\n[ERROR] Intermediate files not found in input_data/")
        print("  Expected: GeographicElement.yaml and Path.yaml")
        return

    print(f"\nLoading intermediate Stage 2 data...")
    print(f"  GeographicElement: {geo_file}")
    print(f"  Path: {path_file}")

    with open(geo_file, 'r', encoding='utf-8') as f:
        geo_elements = yaml.safe_load(f)

    with open(path_file, 'r', encoding='utf-8') as f:
        paths = yaml.safe_load(f)

    # Build node lookup
    nodes = [g for g in geo_elements if g['type'] == 'node']
    node_lookup = {n['id']: n for n in nodes}

    print(f"\n  Nodes: {len(nodes)}")
    print(f"  Paths: {len(paths)}")

    # Analyze DE-IT paths
    print("\n" + "="*80)
    print("ANALYZING DE <-> IT PATHS (STAGE 2 INTERMEDIATE):")
    print("="*80)

    de_it_paths = []
    de_at_it_paths = []
    problem_paths = []

    for path in paths:
        path_id = path.get('id')
        sequence = path.get('sequence', [])

        if len(sequence) < 2:
            continue

        # Get countries for each node
        countries = []
        for node_id in sequence:
            node = node_lookup.get(node_id)
            if node:
                country = node.get('country', 'XX')
                countries.append(country)
            else:
                countries.append('UNKNOWN')

        origin_country = countries[0]
        dest_country = countries[-1]

        # Check for DE <-> IT paths
        if (origin_country == 'DE' and dest_country == 'IT') or (origin_country == 'IT' and dest_country == 'DE'):
            de_it_paths.append((path_id, sequence, countries))

            # Check if Austria is in the path
            if 'AT' in countries:
                de_at_it_paths.append((path_id, sequence, countries))
            else:
                problem_paths.append((path_id, sequence, countries))

    # Report findings
    print(f"\nDE <-> IT paths found: {len(de_it_paths)}")
    print(f"  Correctly routed via Austria: {len(de_at_it_paths)}")
    print(f"  [WARNING] PROBLEMATIC (skip Austria): {len(problem_paths)}")

    if problem_paths:
        print("\n" + "="*80)
        print("PROBLEMATIC PATHS IN STAGE 2 INTERMEDIATE DATA:")
        print("="*80)
        print("\nThese paths skip Austria and would be filtered by SM_preprocessing.py")

        for i, (path_id, sequence, countries) in enumerate(problem_paths[:10]):
            print(f"\nPath {path_id}:")
            print(f"  Countries: {' -> '.join(countries)}")
            print(f"  Node sequence: {sequence}")

            # Check for direct jumps
            for j in range(len(countries) - 1):
                if countries[j] == 'DE' and countries[j+1] == 'IT':
                    print(f"  [JUMP] DE node {sequence[j]} -> IT node {sequence[j+1]}")
                elif countries[j] == 'IT' and countries[j+1] == 'DE':
                    print(f"  [JUMP] IT node {sequence[j]} -> DE node {sequence[j+1]}")

        if len(problem_paths) > 10:
            print(f"\n... and {len(problem_paths) - 10} more problematic paths")

    # Verdict
    print("\n" + "="*80)
    print("VERDICT:")
    print("="*80)

    if problem_paths:
        print(f"\n[FILTER IS NECESSARY]")
        print(f"  {len(problem_paths)} problematic paths exist in Stage 2 intermediate data")
        print(f"  The Italy-Austria filter in SM_preprocessing.py removes these paths")
        print(f"  WITHOUT the filter, these physically impossible routes would reach the model")
    else:
        print(f"\n[FILTER IS UNNECESSARY]")
        print(f"  All {len(de_it_paths)} DE-IT paths correctly route through Austria")
        print(f"  The Italy-Austria filter in SM_preprocessing.py has nothing to filter")
        print(f"  The pathfinding in Stage 2 already creates geographically valid paths")

    print("\n" + "="*80)

    return {
        'total_de_it': len(de_it_paths),
        'correct': len(de_at_it_paths),
        'problematic': len(problem_paths)
    }


if __name__ == "__main__":
    check_stage2_data()
