"""
Find which case includes rail mode by checking Mode.yaml files
"""

import os
import yaml

results_dir = "results"

print("="*80)
print("SEARCHING FOR CASES WITH RAIL MODE")
print("="*80)

if not os.path.exists(results_dir):
    print(f"\n[ERROR] Results directory not found: {results_dir}")
    exit(1)

# Find all case directories
cases = [d for d in os.listdir(results_dir) if os.path.isdir(os.path.join(results_dir, d))]
cases.sort()

print(f"\nFound {len(cases)} case(s):\n")

rail_cases = []
road_only_cases = []

for case_name in cases:
    case_path = os.path.join(results_dir, case_name)
    mode_file = os.path.join(case_path, "Mode.yaml")

    if not os.path.exists(mode_file):
        print(f"  {case_name}: [Mode.yaml not found]")
        continue

    # Load Mode.yaml
    with open(mode_file, 'r', encoding='utf-8') as f:
        modes = yaml.safe_load(f)

    # Check for rail mode
    mode_names = [m['name'].lower() for m in modes]
    has_rail = any('rail' in name for name in mode_names)

    if has_rail:
        rail_cases.append(case_name)
        print(f"  ✓ {case_name}: HAS RAIL")
        print(f"    Modes: {[m['name'] for m in modes]}")
    else:
        road_only_cases.append(case_name)
        print(f"  ✗ {case_name}: ROAD ONLY")
        print(f"    Modes: {[m['name'] for m in modes]}")

    print()

# Summary
print("="*80)
print("SUMMARY")
print("="*80)

if rail_cases:
    print(f"\n✓ Cases WITH rail mode ({len(rail_cases)}):")
    for case in rail_cases:
        print(f"  - {case}")
else:
    print("\n[WARNING] No cases with rail mode found!")

if road_only_cases:
    print(f"\n✗ Cases WITHOUT rail mode ({len(road_only_cases)}):")
    for case in road_only_cases:
        print(f"  - {case}")

# Instructions
print("\n" + "="*80)
print("INSTRUCTIONS")
print("="*80)

if rail_cases:
    print(f"""
To use the rail TKM map visualization, update your notebook with:

    case_study_names = ["{rail_cases[0]}"]

Then reload your data and run the rail map code.
""")
else:
    print("""
No cases with rail mode found. To create a case with rail:

1. Check your input Mode.yaml configuration
2. Ensure it includes both 'road' and 'rail' modes
3. Re-run your model with modal shift enabled
""")
