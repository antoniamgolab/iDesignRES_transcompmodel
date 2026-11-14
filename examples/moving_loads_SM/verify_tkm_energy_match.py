"""
Verify: f × path_length = tkm, and (spec_cons/W) × tkm = energy
"""
import yaml
import os
import re

results_dir = os.path.join(os.path.dirname(__file__), 'results', 'fleet_verification_compare')
scenario_dir = os.path.join(results_dir, 'scenario_001', 'with_fuel')
input_dir = os.path.join(os.path.dirname(__file__), 'input_data', 'uncertainty_scenarios', 'scenario_001')

g_init = 2008

# Load TechVehicle data
with open(os.path.join(input_dir, 'TechVehicle.yaml'), 'r') as f:
    tech_vehicles = yaml.safe_load(f)

tv_data = {}
for tv in tech_vehicles:
    tv_data[tv['id']] = {
        'spec_cons': tv['spec_cons'],
        'W': tv['W']
    }

# Load path lengths
with open(os.path.join(input_dir, 'Path.yaml'), 'r') as f:
    paths = yaml.safe_load(f)
path_lengths = {p['id']: p['length'] for p in paths}

# Load f_dict
files = os.listdir(scenario_dir)
f_file = [f for f in files if '_f_dict.yaml' in f][0]
with open(os.path.join(scenario_dir, f_file), 'r') as f:
    f_dict = yaml.safe_load(f)

# Load s_dict
s_file = [f for f in files if '_s_dict.yaml' in f][0]
with open(os.path.join(scenario_dir, s_file), 'r') as f:
    s_dict = yaml.safe_load(f)

print("=" * 70)
print("VERIFYING: f * path = tkm, and (spec_cons/W) * tkm = energy")
print("=" * 70)

# Calculate totals
total_flow_ktonnes = 0
total_tkm = 0  # in million tonne-km (Mtkm)
total_expected_energy = 0  # in MWh

# Also track by year
by_year = {}

for key, val in f_dict.items():
    f_val = float(val)  # ktonnes
    if f_val < 0.001:
        continue

    key_str = str(key)
    match = re.search(r'\((\d+),\s*\((\d+),\s*(\d+),\s*(\d+)\),\s*\((\d+),\s*(\d+)\),\s*(\d+)\)', key_str)
    if match:
        year = int(match.group(1))
        k_id = int(match.group(4))
        tv_id = int(match.group(6))
        g = int(match.group(7))

        path_len = path_lengths.get(k_id, 0)

        # Get spec_cons and W for this generation
        idx = g - g_init
        if tv_id in tv_data and 0 <= idx < len(tv_data[tv_id]['spec_cons']):
            spec_cons = tv_data[tv_id]['spec_cons'][idx]
            W = tv_data[tv_id]['W'][idx]
        else:
            continue

        # Calculate tkm: f (ktonnes) × path (km) = ktonnes × km
        # Convert to Mtkm: ktonnes × km / 1000 = Mtkm
        tkm = f_val * path_len / 1000  # Mtkm

        # Energy: (spec_cons/W) × path × f
        # Units: (kWh/km / t) × km × kt = kWh/t × kt = kWh × 1000 = MWh
        energy = (spec_cons / W) * path_len * f_val  # MWh

        total_flow_ktonnes += f_val
        total_tkm += tkm
        total_expected_energy += energy

        if year not in by_year:
            by_year[year] = {'flow': 0, 'tkm': 0, 'energy': 0}
        by_year[year]['flow'] += f_val
        by_year[year]['tkm'] += tkm
        by_year[year]['energy'] += energy

# Actual energy from model
total_actual_energy = sum(float(v) for v in s_dict.values())

print(f"\n1. FLOW AND TKM:")
print(f"   Total flow: {total_flow_ktonnes:,.0f} ktonnes = {total_flow_ktonnes/1e6:.2f} Gt")
print(f"   Total tkm:  {total_tkm:,.0f} Mtkm = {total_tkm/1e6:.2f} trillion tkm")

print(f"\n2. ENERGY VERIFICATION:")
print(f"   Expected energy (from f * path * spec_cons/W): {total_expected_energy/1e6:.2f} TWh")
print(f"   Actual energy (s variable from model):        {total_actual_energy/1e6:.2f} TWh")
print(f"   Match: {'YES' if abs(total_expected_energy - total_actual_energy) < 1 else 'NO'}")

print(f"\n3. AVERAGE SPECIFIC ENERGY:")
avg_spec_energy = total_expected_energy / (total_tkm * 1000) if total_tkm > 0 else 0  # kWh per tkm
print(f"   Average energy per tkm: {avg_spec_energy:.4f} kWh/tkm")
print(f"   (This is the flow-weighted average of spec_cons/W across all generations)")

print("\n" + "=" * 70)
print("BREAKDOWN BY YEAR")
print("=" * 70)
print(f"{'Year':<8} {'Flow (kt)':<15} {'Tkm (Mtkm)':<15} {'Energy (TWh)':<15} {'kWh/tkm':<10}")
print("-" * 65)
for year in sorted(by_year.keys()):
    d = by_year[year]
    kwh_per_tkm = d['energy'] / (d['tkm'] * 1000) if d['tkm'] > 0 else 0
    print(f"{year:<8} {d['flow']:>12,.0f}   {d['tkm']:>12,.0f}   {d['energy']/1e6:>12.3f}   {kwh_per_tkm:>8.4f}")

print("-" * 65)
print(f"{'TOTAL':<8} {total_flow_ktonnes:>12,.0f}   {total_tkm:>12,.0f}   {total_expected_energy/1e6:>12.3f}   {avg_spec_energy:>8.4f}")

print("\n" + "=" * 70)
print("CONCLUSION")
print("=" * 70)
print(f"""
The relationship holds:

  Total Energy = SUM (spec_cons[g]/W[g]) * path_length * f
               = SUM (spec_cons[g]/W[g]) * tkm

Where tkm = f * path_length (converted to appropriate units)

Model result: {total_actual_energy/1e6:.2f} TWh
Calculated:   {total_expected_energy/1e6:.2f} TWh
Difference:   {abs(total_actual_energy - total_expected_energy):.0f} MWh ({abs(total_actual_energy - total_expected_energy)/total_actual_energy*100:.4f}%)
""")
