"""
Verify that constraint_demand_coverage is satisfied in the optimization results.

The constraint requires:
For each year y and OD pair r:
  sum(f[y, (r.product.id, r.id, k.id), mv, g]
      for all paths k in r.paths,
      for all mode-vehicle pairs mv,
      for all generations g from g_init to y)
  == r.F[index] * (1/1000)

Where r.F is the demand in tonnes, and f is in tonnes, so the (1/1000) converts to kilotonnes.
"""

import yaml
import re
from collections import defaultdict

# Configuration
case_name = "case_20251110_160646_reverse"
result_timestamp = "case_20251110_160646_reverse_cs_2025-11-16_16-48-22"
base_path = "C:/Users/simuser/Documents/AntoniaGolab/Scand_Med_analysis/SM_baby_2/iDesignRES_transcompmodel/examples/moving_loads_SM"
input_dir = f"{base_path}/input_data/{case_name}"
results_dir = f"{base_path}/results/{case_name}"

print(f"\n{'='*80}")
print(f"VERIFYING DEMAND COVERAGE CONSTRAINT")
print(f"Case: {result_timestamp}")
print(f"{'='*80}\n")

# Load input data
print("Loading input data...")
with open(f"{input_dir}/Odpair.yaml", 'r') as f:
    odpairs = yaml.safe_load(f)

# Load results
print("Loading f_dict...")
with open(f"{results_dir}/{result_timestamp}_f_dict.yaml", 'r') as f:
    f_dict = yaml.safe_load(f)

print(f"Loaded {len(f_dict):,} flow entries\n")

# Model parameters
y_init = 2020
time_step = 4
g_init = 2020

# Parse function for f_dict keys: (year, (product, odpair, path), (mode, techvehicle), generation)
def parse_f_key(key_str):
    pattern = r'\((\d+),\s*\((\d+),\s*(\d+),\s*(\d+)\),\s*\((\d+),\s*(\d+)\),\s*(\d+)\)'
    match = re.match(pattern, key_str)
    if match:
        return {
            'year': int(match.group(1)),
            'product': int(match.group(2)),
            'odpair': int(match.group(3)),
            'path': int(match.group(4)),
            'mode': int(match.group(5)),
            'techvehicle': int(match.group(6)),
            'generation': int(match.group(7))
        }
    return None

# Organize flows by year and odpair
flows_by_year_odpair = defaultdict(lambda: defaultdict(float))

for key_str, value in f_dict.items():
    parsed = parse_f_key(key_str)
    if parsed:
        year = parsed['year']
        odpair_id = parsed['odpair']
        val = float(value) if isinstance(value, str) else value
        flows_by_year_odpair[year][odpair_id] += val

print(f"{'='*80}")
print("DEMAND CONSTRAINT VERIFICATION")
print(f"{'='*80}\n")

# Check constraint for each year and OD pair
violations = []
total_checks = 0
passed_checks = 0

# Get unique years from flows
years = sorted(set(flows_by_year_odpair.keys()))

print(f"Checking {len(odpairs)} OD pairs across {len(years)} years...\n")

for odpair in odpairs:
    odpair_id = odpair['id']
    product_id = odpair['product']

    # Get demand array F for this OD pair
    demand_array = odpair['F']

    for year in years:
        total_checks += 1

        # Calculate demand for this year
        # Index calculation: (y-y_init+1) to min((y-y_init+time_step), length(r.F))
        start_idx = year - y_init  # Python 0-indexed, Julia starts at 1, so this is actually (y-y_init+1)-1
        end_idx = min(year - y_init + time_step - 1, len(demand_array) - 1)

        # Sum demand for the relevant time period
        demand_sum = sum(demand_array[i] for i in range(start_idx, end_idx + 1))

        # Convert to kilotonnes as in the constraint (multiply by 1/1000)
        demand_kt = demand_sum * (1/1000)

        # Get total flow for this year and OD pair (already summed across all paths, modes, vehicles, generations)
        flow_sum = flows_by_year_odpair[year].get(odpair_id, 0)

        # Check if constraint is satisfied (with small tolerance for numerical errors)
        difference = abs(flow_sum - demand_kt)
        tolerance = 1e-6  # Small tolerance for floating point comparison

        is_satisfied = difference < tolerance

        if is_satisfied:
            passed_checks += 1
        else:
            violations.append({
                'year': year,
                'odpair': odpair_id,
                'product': product_id,
                'demand_kt': demand_kt,
                'flow_sum': flow_sum,
                'difference': difference
            })

print(f"{'='*80}")
print("RESULTS")
print(f"{'='*80}\n")

print(f"Total constraint checks: {total_checks:,}")
print(f"Passed: {passed_checks:,} ({100*passed_checks/total_checks:.2f}%)")
print(f"Violations: {len(violations):,}\n")

if violations:
    print(f"{'='*80}")
    print(f"VIOLATIONS FOUND (showing first 20)")
    print(f"{'='*80}\n")
    print(f"{'Year':<8} {'OD Pair':<10} {'Product':<10} {'Demand (kt)':<15} {'Flow (kt)':<15} {'Diff (kt)':<15}")
    print("-" * 88)

    for i, v in enumerate(violations[:20]):
        print(f"{v['year']:<8} {v['odpair']:<10} {v['product']:<10} {v['demand_kt']:<15.6f} {v['flow_sum']:<15.6f} {v['difference']:<15.6f}")

    if len(violations) > 20:
        print(f"\n... and {len(violations) - 20} more violations")

    print(f"\n{'='*80}")
    print("VIOLATION STATISTICS")
    print(f"{'='*80}\n")

    max_violation = max(violations, key=lambda x: x['difference'])
    print(f"Maximum violation:")
    print(f"  Year: {max_violation['year']}")
    print(f"  OD Pair: {max_violation['odpair']}")
    print(f"  Demand: {max_violation['demand_kt']:.6f} kt")
    print(f"  Flow: {max_violation['flow_sum']:.6f} kt")
    print(f"  Difference: {max_violation['difference']:.6f} kt")
else:
    print("✓ ALL DEMAND COVERAGE CONSTRAINTS SATISFIED!")
    print("  The constraint is properly enforced in the optimization.")

print(f"\n{'='*80}\n")
