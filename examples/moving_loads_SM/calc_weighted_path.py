"""
Calculate flow-weighted average path length
"""
import yaml
import os
import re

results_dir = os.path.join(os.path.dirname(__file__), 'results', 'fleet_verification_compare')
scenario_dir = os.path.join(results_dir, 'scenario_001', 'with_fuel')
input_dir = os.path.join(os.path.dirname(__file__), 'input_data', 'uncertainty_scenarios', 'scenario_001')

# Load path lengths
with open(os.path.join(input_dir, 'Path.yaml'), 'r') as f:
    paths = yaml.safe_load(f)
path_lengths = {p['id']: p['length'] for p in paths}

# Load f_dict
files = os.listdir(scenario_dir)
f_file = [f for f in files if '_f_dict.yaml' in f][0]
with open(os.path.join(scenario_dir, f_file), 'r') as f:
    f_dict = yaml.safe_load(f)

# Calculate flow-weighted path length
total_tkm = 0  # tonne-km
total_flow = 0  # tonnes

for key, val in f_dict.items():
    flow = float(val) * 1000  # ktonnes to tonnes
    if flow < 0.001:
        continue

    # Extract path_id from key
    match = re.search(r'\((\d+),\s*(\d+),\s*(\d+)\)', str(key))
    if match:
        path_id = int(match.group(3))
        path_len = path_lengths.get(path_id, 0)
        total_tkm += flow * path_len
        total_flow += flow

weighted_avg_path = total_tkm / total_flow if total_flow > 0 else 0
simple_avg_path = sum(path_lengths.values()) / len(path_lengths)

print("=" * 60)
print("PATH LENGTH ANALYSIS")
print("=" * 60)

print(f"\nSimple average path length: {simple_avg_path:.0f} km")
print(f"Flow-weighted average path: {weighted_avg_path:.0f} km")
print(f"Ratio: {weighted_avg_path / simple_avg_path:.2f}")

print(f"\nTotal flow: {total_flow/1e9:.2f} billion tonnes")
print(f"Total tkm: {total_tkm/1e12:.2f} trillion tkm")

# Now recalculate expected energy with flow-weighted path
spec_cons_avg = 3.0  # Weighted average of ICEV (3.639) and BEV (2.056)
W_avg = 12.5  # Weighted average

expected_energy = (spec_cons_avg / W_avg) * total_tkm / 1e6  # MWh
print(f"\nExpected energy (weighted path): {expected_energy/1e6:.1f} TWh")
print(f"Actual energy: 60.6 TWh")
print(f"Ratio: {expected_energy/1e6 / 60.6:.2f}")

# Also check energy per tkm
actual_energy_mwh = 60597831
actual_kwh_per_tkm = actual_energy_mwh * 1000 / total_tkm
print(f"\nActual energy per tkm: {actual_kwh_per_tkm:.4f} kWh/tkm")
print(f"Expected (ICEV): {3.639/13.6:.4f} kWh/tkm")
print(f"Expected (BEV): {2.056/10.9:.4f} kWh/tkm")
