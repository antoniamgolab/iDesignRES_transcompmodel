"""
Verify that in the constrained case, charging (s variable) only happens at MandatoryBreak locations.
"""

import yaml
import os
import re
from collections import defaultdict

BASE_DIR = r"C:\Users\simuser\Documents\AntoniaGolab\Scand_Med_analysis\SM_baby_2\iDesignRES_transcompmodel\examples\moving_loads_SM"

# Load MandatoryBreaks to get allowed break geo_ids per path
print("Loading MandatoryBreaks.yaml...")
with open(os.path.join(BASE_DIR, "input_data", "uncertainty_scenarios", "scenario_000", "MandatoryBreaks.yaml"), 'r') as f:
    mandatory_breaks = yaml.safe_load(f)

# Build lookup: path_id -> set of break geo_ids
break_geo_ids_by_path = defaultdict(set)
for mb in mandatory_breaks:
    path_id = mb['path_id']
    geo_id = mb['latest_geo_id']
    break_geo_ids_by_path[path_id].add(geo_id)

print(f"Loaded {len(mandatory_breaks)} mandatory breaks for {len(break_geo_ids_by_path)} paths")

# Load constrained s_dict
print("\nLoading constrained s_dict...")
constrained_dir = os.path.join(BASE_DIR, "results", "uncertainty_analysis_charging_at_breaks", "scenario_000")
s_file = None
for f in os.listdir(constrained_dir):
    if f.endswith("_s_dict.yaml"):
        s_file = os.path.join(constrained_dir, f)
        break

if not s_file:
    print("ERROR: No s_dict file found!")
    exit(1)

print(f"Loading: {os.path.basename(s_file)}")
with open(s_file, 'r') as f:
    s_dict = yaml.safe_load(f)

print(f"Loaded {len(s_dict)} s variable entries")

# Parse s variable keys and check locations
# s key format: "(year, (prod_id, odpair_id, path_id, geo_id), tv_id, (fuel_tuple), gen)"
# Example: "(2040, (0, 2206, 2206, 22), 0, (1, 0), 2040)"

violations = []
valid_charges = []
total_nonzero = 0

def parse_s_key(key_str):
    """Parse the s variable key string."""
    # Use regex to extract numbers
    # Format: (year, (prod_id, odpair_id, path_id, geo_id), tv_id, (f1, f2), gen)
    numbers = re.findall(r'-?\d+', key_str)
    # numbers = [year, prod_id, odpair_id, path_id, geo_id, tv_id, f1, f2, gen]
    year = int(numbers[0])
    prod_id = int(numbers[1])
    odpair_id = int(numbers[2])
    path_id = int(numbers[3])
    geo_id = int(numbers[4])
    tv_id = int(numbers[5])
    gen = int(numbers[-1])  # Last number is generation
    return year, prod_id, odpair_id, path_id, geo_id, tv_id, gen

for key, value in s_dict.items():
    val = float(value) if isinstance(value, str) else value
    if val < 1e-6:  # Skip zero values
        continue

    total_nonzero += 1

    # Parse key
    year, prod_id, odpair_id, path_id, geo_id, tv_id, gen = parse_s_key(key)

    # Check if this path has mandatory breaks
    if path_id in break_geo_ids_by_path:
        allowed_geo_ids = break_geo_ids_by_path[path_id]
        if geo_id in allowed_geo_ids:
            valid_charges.append({
                'year': year, 'path_id': path_id, 'geo_id': geo_id,
                'tv_id': tv_id, 'value': val
            })
        else:
            violations.append({
                'year': year, 'path_id': path_id, 'geo_id': geo_id,
                'tv_id': tv_id, 'value': val,
                'allowed_geo_ids': list(allowed_geo_ids)
            })
    else:
        # Path has no mandatory breaks - charging should still be allowed anywhere
        # (constraint only applies to paths WITH mandatory breaks)
        valid_charges.append({
            'year': year, 'path_id': path_id, 'geo_id': geo_id,
            'tv_id': tv_id, 'value': val, 'note': 'no_breaks_required'
        })

print("\n" + "="*80)
print("VERIFICATION RESULTS")
print("="*80)
print(f"\nTotal non-zero charging entries: {total_nonzero}")
print(f"Valid charges (at break locations or paths without breaks): {len(valid_charges)}")
print(f"VIOLATIONS (charging at non-break locations): {len(violations)}")

# Count charges at paths with vs without mandatory breaks
charges_with_breaks = [c for c in valid_charges if c.get('note') != 'no_breaks_required']
charges_no_breaks = [c for c in valid_charges if c.get('note') == 'no_breaks_required']
print(f"\n  At break locations (paths with breaks): {len(charges_with_breaks)}")
print(f"  At any location (paths without breaks): {len(charges_no_breaks)}")

if violations:
    print("\n" + "="*80)
    print("CONSTRAINT VIOLATIONS FOUND!")
    print("="*80)
    print("\nFirst 20 violations:")
    for v in violations[:20]:
        print(f"  Path {v['path_id']}, Geo {v['geo_id']}: {v['value']:.2f} kWh (tv={v['tv_id']})")
        print(f"    Allowed geo_ids: {sorted(v['allowed_geo_ids'])}")
else:
    print("\n" + "="*80)
    print("SUCCESS: All charging happens at allowed locations!")
    print("="*80)

# Summary by path
print("\n" + "="*80)
print("CHARGING SUMMARY BY PATH (first 10 paths WITH mandatory breaks)")
print("="*80)

charges_by_path = defaultdict(list)
for vc in charges_with_breaks:
    charges_by_path[vc['path_id']].append(vc)

count = 0
for path_id, charges in sorted(charges_by_path.items()):
    if count >= 10:
        break
    count += 1

    allowed = break_geo_ids_by_path.get(path_id, set())
    geo_ids_used = set(c['geo_id'] for c in charges)
    total_kwh = sum(c['value'] for c in charges)

    print(f"\nPath {path_id}:")
    print(f"  Allowed break geo_ids: {sorted(allowed)}")
    print(f"  Geo_ids with charging: {sorted(geo_ids_used)}")
    print(f"  Match: {'YES' if geo_ids_used <= allowed else 'NO - VIOLATION!'}")
    print(f"  Total charged: {total_kwh:,.1f} kWh")
