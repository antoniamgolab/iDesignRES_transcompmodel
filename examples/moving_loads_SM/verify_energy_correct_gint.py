"""
Verify energy calculation with correct g_init = 2008
"""
import yaml
import os
import re

results_dir = os.path.join(os.path.dirname(__file__), 'results', 'fleet_verification_compare')
scenario_dir = os.path.join(results_dir, 'scenario_001', 'with_fuel')
input_dir = os.path.join(os.path.dirname(__file__), 'input_data', 'uncertainty_scenarios', 'scenario_001')

# Model parameters
g_init = 2008  # CORRECT: y_init - pre_y = 2020 - 12 = 2008

# Load TechVehicle data
with open(os.path.join(input_dir, 'TechVehicle.yaml'), 'r') as f:
    tech_vehicles = yaml.safe_load(f)

# Build lookup for spec_cons and W by tech vehicle id
tv_data = {}
for tv in tech_vehicles:
    tv_id = tv['id']
    tv_data[tv_id] = {
        'spec_cons': tv['spec_cons'],  # array indexed from g_init
        'W': tv['W']  # array indexed from g_init
    }

print("=" * 70)
print("TECH VEHICLE DATA")
print("=" * 70)
for tv_id, data in tv_data.items():
    print(f"\nTV {tv_id}:")
    print(f"  spec_cons array length: {len(data['spec_cons'])}")
    print(f"  W array length: {len(data['W'])}")
    # Show values at key generations
    for g in [2008, 2012, 2016, 2020, 2032, 2052]:
        idx = g - g_init  # 0-based for Python
        if 0 <= idx < len(data['spec_cons']):
            print(f"  g={g} (idx={idx}): spec_cons={data['spec_cons'][idx]:.3f}, W={data['W'][idx]:.1f}")

# Load path lengths
with open(os.path.join(input_dir, 'Path.yaml'), 'r') as f:
    paths = yaml.safe_load(f)
path_lengths = {p['id']: p['length'] for p in paths}

# Load f_dict
files = os.listdir(scenario_dir)
f_file = [f for f in files if '_f_dict.yaml' in f][0]
with open(os.path.join(scenario_dir, f_file), 'r') as f:
    f_dict = yaml.safe_load(f)

print("\n" + "=" * 70)
print("EXPECTED ENERGY CALCULATION (with correct g_init = 2008)")
print("=" * 70)

# Calculate expected energy: s = (spec_cons / W) * path_length * f
total_expected_energy = 0
total_flow = 0
flows_by_gen = {}
energy_by_gen = {}

for key, val in f_dict.items():
    f_val = float(val)
    if f_val < 0.001:
        continue

    key_str = str(key)
    # Parse: (year, (p, r, k), (mode, tv), g)
    match = re.search(r'\((\d+),\s*\((\d+),\s*(\d+),\s*(\d+)\),\s*\((\d+),\s*(\d+)\),\s*(\d+)\)', key_str)
    if match:
        year = int(match.group(1))
        p_id = int(match.group(2))
        r_id = int(match.group(3))
        k_id = int(match.group(4))
        mode_id = int(match.group(5))
        tv_id = int(match.group(6))
        g = int(match.group(7))

        path_len = path_lengths.get(k_id, 0)

        # Get spec_cons and W for this generation
        if tv_id in tv_data:
            idx = g - g_init  # 0-based Python index
            if 0 <= idx < len(tv_data[tv_id]['spec_cons']):
                spec_cons = tv_data[tv_id]['spec_cons'][idx]
                W = tv_data[tv_id]['W'][idx]
            else:
                print(f"WARNING: Index {idx} out of range for g={g}, tv={tv_id}")
                continue
        else:
            print(f"WARNING: TV {tv_id} not found")
            continue

        # Expected energy: (spec_cons / W) * path_length * f
        # f is in ktonnes, result is in MWh
        expected_e = (spec_cons / W) * path_len * f_val

        total_expected_energy += expected_e
        total_flow += f_val

        if g not in flows_by_gen:
            flows_by_gen[g] = 0
            energy_by_gen[g] = 0
        flows_by_gen[g] += f_val
        energy_by_gen[g] += expected_e

# Load actual s_dict
s_file = [f for f in files if '_s_dict.yaml' in f][0]
with open(os.path.join(scenario_dir, s_file), 'r') as f:
    s_dict = yaml.safe_load(f)

total_actual_energy = sum(float(v) for v in s_dict.values())

print(f"\nTotal expected energy (from constraint formula): {total_expected_energy/1e6:.2f} TWh")
print(f"Total actual energy (s variable):               {total_actual_energy/1e6:.2f} TWh")
print(f"Ratio actual/expected: {total_actual_energy/total_expected_energy:.3f}")
print(f"Gap: {(total_actual_energy - total_expected_energy)/1e6:.2f} TWh ({(total_actual_energy/total_expected_energy - 1)*100:.1f}%)")

print("\n" + "=" * 70)
print("BREAKDOWN BY GENERATION")
print("=" * 70)
print(f"{'Gen':<8} {'Flow (kt)':<15} {'Expected E (TWh)':<20} {'Avg spec_cons/W':<15}")
print("-" * 60)
for g in sorted(flows_by_gen.keys()):
    flow = flows_by_gen[g]
    energy = energy_by_gen[g]
    avg_ratio = energy / (flow * sum(path_lengths.values())/len(path_lengths)) if flow > 0 else 0
    print(f"{g:<8} {flow:>12,.0f}   {energy/1e6:>16.3f}   {avg_ratio:>12.4f}")

print(f"\nTotal flow: {total_flow:,.0f} ktonnes")
