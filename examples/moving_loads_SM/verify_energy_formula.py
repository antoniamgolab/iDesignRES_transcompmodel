"""
Verify s = (spec_cons / W) × path × flow directly
"""
import yaml
import os

results_dir = os.path.join(os.path.dirname(__file__), 'results', 'fleet_verification_compare')
scenario_dir = os.path.join(results_dir, 'scenario_001', 'with_fuel')
input_dir = os.path.join(os.path.dirname(__file__), 'input_data', 'uncertainty_scenarios', 'scenario_001')

# Load path lengths
with open(os.path.join(input_dir, 'Path.yaml'), 'r') as f:
    paths = yaml.safe_load(f)
path_lengths = {p['id']: p['length'] for p in paths}

# Load TechVehicle to get spec_cons and W
# ICEV: id=0, BEV: id=1
spec_cons = {0: 3.639, 1: 2.056}  # kWh/km
W = {0: 13.6, 1: 10.9}  # tonnes

# Load f_dict and s_dict
files = os.listdir(scenario_dir)
f_file = [f for f in files if '_f_dict.yaml' in f][0]
s_file = [f for f in files if '_s_dict.yaml' in f][0]

with open(os.path.join(scenario_dir, f_file), 'r') as f:
    f_dict = yaml.safe_load(f)

with open(os.path.join(scenario_dir, s_file), 'r') as f:
    s_dict = yaml.safe_load(f)

print("=" * 70)
print("VERIFY ENERGY FORMULA: s = (spec_cons / W) × path × flow")
print("=" * 70)

# The constraint sums s over origin and destination nodes
# Let's check a few specific cases

# First, understand the key formats
print("\nSample f_dict key:")
sample_f = list(f_dict.keys())[0]
print(f"  {sample_f}")

print("\nSample s_dict key:")
sample_s = list(s_dict.keys())[0]
print(f"  {sample_s}")

# Count entries
print(f"\nNumber of f_dict entries: {len(f_dict):,}")
print(f"Number of s_dict entries: {len(s_dict):,}")

# Total energy and flow
total_s = sum(float(v) for v in s_dict.values())
total_f = sum(float(v) for v in f_dict.values())

print(f"\nTotal s (energy in MWh): {total_s:,.0f}")
print(f"Total f (flow in ktonnes): {total_f:,.0f}")

# Expected energy if using average path
avg_path = sum(path_lengths.values()) / len(path_lengths)
# Assume mix of ICEV and BEV with weighted spec_cons/W
# For simplicity, use ICEV values
expected_s = (spec_cons[0] / W[0]) * avg_path * total_f * 1000  # flow in ktonnes, ×1000 to tonnes
# Result should be in kWh, divide by 1000 for MWh
expected_s_mwh = expected_s / 1000

print(f"\nExpected s (using avg path {avg_path:.0f} km): {expected_s_mwh:,.0f} MWh")
print(f"Actual s: {total_s:,.0f} MWh")
print(f"Ratio: {expected_s_mwh / total_s:.1f}x")

# Check constraint formula more carefully
# s = (spec_cons / W) × path × f
# Units: (kWh/km / tonnes) × km × ktonnes = kWh/t × km × 1000t = kWh × 1000 = MWh

print("\n" + "=" * 70)
print("UNIT ANALYSIS")
print("=" * 70)
print("""
From constraint_fueling_demand:
  sum(s[...]) = sum((spec_cons / W) × path_length × f)

Units:
  spec_cons = kWh/km
  W = tonnes
  path_length = km
  f = ktonnes (thousands of tonnes)

  (kWh/km / t) × km × kt = (kWh/t) × kt = kWh × 1000 = MWh ✓

So s should be in MWh, which matches the s_dict values.
""")

# Verify with a specific example
print("=" * 70)
print("VERIFY WITH SPECIFIC FLOW")
print("=" * 70)

# Pick a specific flow entry and find corresponding s entries
import re

# Get first flow entry with significant value
for fkey, fval in f_dict.items():
    fv = float(fval)
    if fv > 1:  # More than 1 ktonne
        fkey_str = str(fkey)
        # Parse: (year, (p, r, k), (mode, tv), g)
        match = re.search(r'\((\d+),\s*\((\d+),\s*(\d+),\s*(\d+)\),\s*\((\d+),\s*(\d+)\),\s*(\d+)\)', fkey_str)
        if match:
            year = int(match.group(1))
            p_id = int(match.group(2))
            r_id = int(match.group(3))
            k_id = int(match.group(4))
            mode_id = int(match.group(5))
            tv_id = int(match.group(6))
            g = int(match.group(7))

            path_len = path_lengths.get(k_id, 0)
            sc = spec_cons.get(tv_id, spec_cons[0])
            w = W.get(tv_id, W[0])

            # Expected energy for this flow
            expected_energy = (sc / w) * path_len * fv  # MWh (since f is ktonnes)

            print(f"\nFlow entry: year={year}, path={k_id}, tv={tv_id}, g={g}")
            print(f"  Flow f = {fv:.2f} ktonnes")
            print(f"  Path length = {path_len:.0f} km")
            print(f"  spec_cons = {sc:.3f} kWh/km, W = {w:.1f} t")
            print(f"  Expected s = ({sc}/{w}) × {path_len} × {fv:.2f} = {expected_energy:.2f} MWh")

            # Find corresponding s entries
            # s is indexed by (year, (p, r, k, node), tv, (fuel, level), g)
            # Sum s over all nodes for this (year, p, r, k, tv, g)
            total_s_for_flow = 0
            s_count = 0
            for skey, sval in s_dict.items():
                skey_str = str(skey)
                # Check if this s entry matches our flow
                if f", {k_id}," in skey_str and f", {tv_id}," in skey_str:
                    if skey_str.startswith(f"({year},"):
                        total_s_for_flow += float(sval)
                        s_count += 1

            print(f"  Actual s (sum over nodes) = {total_s_for_flow:.2f} MWh ({s_count} entries)")
            print(f"  Ratio expected/actual = {expected_energy/total_s_for_flow:.2f}x" if total_s_for_flow > 0 else "  No s entries found!")

            break
