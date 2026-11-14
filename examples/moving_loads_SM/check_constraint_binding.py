"""
Check if constraint_vehicle_sizing is binding
Compare h with the theoretical minimum from the constraint
"""
import yaml
import os

results_dir = os.path.join(os.path.dirname(__file__), 'results', 'fleet_verification_compare')
scenario_dir = os.path.join(results_dir, 'scenario_001', 'with_fuel')
input_dir = os.path.join(os.path.dirname(__file__), 'input_data', 'uncertainty_scenarios', 'scenario_001')

# Parameters
W = 13.6
annual_range = 136750

# Load f_dict and parse with path info
files = os.listdir(scenario_dir)
f_file = [f for f in files if '_f_dict.yaml' in f][0]
h_file = [f for f in files if '_h_dict.yaml' in f and 'plus' not in f and 'minus' not in f and 'exist' not in f][0]

# Load path data to get lengths
path_file = os.path.join(input_dir, 'Path.yaml')
with open(path_file, 'r') as file:
    path_data = yaml.safe_load(file)

# Create path length lookup
path_lengths = {}
for p in path_data:
    path_lengths[p['id']] = p['length']

print(f"Loaded {len(path_lengths)} paths")
print(f"Path length range: {min(path_lengths.values()):.0f} - {max(path_lengths.values()):.0f} km")
print(f"Average path length: {sum(path_lengths.values())/len(path_lengths):.0f} km")

# Load f_dict
with open(os.path.join(scenario_dir, f_file), 'r') as file:
    f_dict = yaml.safe_load(file)

# Calculate required h from constraint for each (year, odpair, tv, g)
# h >= sum over paths of (path_length / (W × AnnualRange)) × 1000 × f

# Parse f to get required h
# Key format: (year, (p, r, k), (mode, tv), g)
required_h_by_key = {}
for key, val in f_dict.items():
    f_val = float(val)
    if f_val < 0.001:
        continue

    key_str = str(key)
    # Extract year
    year = int(key_str.split(',')[0].strip('('))

    # Extract path_id (k) from (p, r, k)
    # Format: (year, (p, r, k), (mode, tv), g)
    import re
    match = re.search(r'\((\d+),\s*(\d+),\s*(\d+)\)', key_str)
    if match:
        path_id = int(match.group(3))
        path_length = path_lengths.get(path_id, 0)

        # Extract tv_id
        match2 = re.search(r'\),\s*\((\d+),\s*(\d+)\),\s*(\d+)\)', key_str)
        if match2:
            tv_id = int(match2.group(2))
            g = int(match2.group(3))
            odpair_id = int(match.group(2))

            # Required h contribution from this flow
            req_h = (path_length / (W * annual_range)) * 1000 * f_val

            # Key for aggregation: (year, odpair, tv, g)
            h_key = (year, odpair_id, tv_id, g)
            if h_key not in required_h_by_key:
                required_h_by_key[h_key] = 0
            required_h_by_key[h_key] += req_h

# Load actual h
with open(os.path.join(scenario_dir, h_file), 'r') as file:
    h_dict = yaml.safe_load(file)

actual_h_by_key = {}
for key, val in h_dict.items():
    h_val = float(val)
    key_str = str(key).strip('()')
    parts = key_str.split(',')
    if len(parts) >= 4:
        year = int(parts[0].strip())
        odpair_id = int(parts[1].strip())
        tv_id = int(parts[2].strip())
        g = int(parts[3].strip())
        h_key = (year, odpair_id, tv_id, g)
        actual_h_by_key[h_key] = h_val

# Compare
print("\n" + "=" * 70)
print("CONSTRAINT BINDING ANALYSIS")
print("=" * 70)

total_required = 0
total_actual = 0
slack_cases = 0
binding_cases = 0

for h_key in required_h_by_key:
    req = required_h_by_key[h_key]
    act = actual_h_by_key.get(h_key, 0)
    total_required += req
    total_actual += act

    slack = act - req
    if slack > 0.01:  # significant slack
        slack_cases += 1
    else:
        binding_cases += 1

print(f"\nTotal required h (from constraint): {total_required:,.0f}")
print(f"Total actual h: {total_actual:,.0f}")
print(f"Total slack: {total_actual - total_required:,.0f} ({(total_actual/total_required - 1)*100:.1f}%)")
print(f"\nBinding cases: {binding_cases:,}")
print(f"Slack cases: {slack_cases:,}")

# Sample some slack cases
print("\n" + "=" * 70)
print("SAMPLE CASES WITH SLACK")
print("=" * 70)

count = 0
for h_key in sorted(required_h_by_key.keys()):
    req = required_h_by_key[h_key]
    act = actual_h_by_key.get(h_key, 0)
    slack = act - req
    if slack > 1 and count < 10:  # More than 1 vehicle slack
        year, odpair, tv, g = h_key
        print(f"({year}, OD={odpair}, TV={tv}, g={g}): Required={req:.2f}, Actual={act:.2f}, Slack={slack:.2f}")
        count += 1
