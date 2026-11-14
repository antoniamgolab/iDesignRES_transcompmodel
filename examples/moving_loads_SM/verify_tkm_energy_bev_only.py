"""
Verify: f * path_length = tkm, and (spec_cons/W) * tkm = energy
FOR BEVs ONLY (tv_id = 1)
"""
import yaml
import os
import re

results_dir = os.path.join(os.path.dirname(__file__), 'results', 'fleet_verification_compare')
scenario_dir = os.path.join(results_dir, 'scenario_001', 'with_fuel')
input_dir = os.path.join(os.path.dirname(__file__), 'input_data', 'uncertainty_scenarios', 'scenario_001')

g_init = 2008
BEV_TV_ID = 1  # BEV tech vehicle ID

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
print("VERIFYING BEV ONLY: f * path = tkm, (spec_cons/W) * tkm = energy")
print("=" * 70)

# Show BEV parameters at key generations
print("\nBEV (TV=1) parameters by generation:")
print(f"{'Gen':<8} {'spec_cons':<12} {'W':<8} {'spec_cons/W':<12}")
print("-" * 42)
for g in [2008, 2012, 2016, 2020, 2024, 2028, 2032, 2040, 2052]:
    idx = g - g_init
    if 0 <= idx < len(tv_data[BEV_TV_ID]['spec_cons']):
        sc = tv_data[BEV_TV_ID]['spec_cons'][idx]
        w = tv_data[BEV_TV_ID]['W'][idx]
        print(f"{g:<8} {sc:<12.3f} {w:<8.1f} {sc/w:<12.4f}")

# Calculate totals - BEV ONLY
total_flow_ktonnes = 0
total_tkm = 0  # in million tonne-km (Mtkm)
total_expected_energy = 0  # in MWh

by_year = {}
by_gen = {}

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

        # FILTER: BEV only
        if tv_id != BEV_TV_ID:
            continue

        path_len = path_lengths.get(k_id, 0)

        idx = g - g_init
        if tv_id in tv_data and 0 <= idx < len(tv_data[tv_id]['spec_cons']):
            spec_cons = tv_data[tv_id]['spec_cons'][idx]
            W = tv_data[tv_id]['W'][idx]
        else:
            continue

        # tkm: f (ktonnes) * path (km) / 1000 = Mtkm
        tkm = f_val * path_len / 1000

        # Energy: (spec_cons/W) * path * f = MWh
        energy = (spec_cons / W) * path_len * f_val

        total_flow_ktonnes += f_val
        total_tkm += tkm
        total_expected_energy += energy

        if year not in by_year:
            by_year[year] = {'flow': 0, 'tkm': 0, 'energy': 0}
        by_year[year]['flow'] += f_val
        by_year[year]['tkm'] += tkm
        by_year[year]['energy'] += energy

        if g not in by_gen:
            by_gen[g] = {'flow': 0, 'tkm': 0, 'energy': 0}
        by_gen[g]['flow'] += f_val
        by_gen[g]['tkm'] += tkm
        by_gen[g]['energy'] += energy

# Calculate actual BEV energy from s_dict
# s_dict keys include tv_id, need to filter for BEV
total_actual_energy = 0
for key, val in s_dict.items():
    key_str = str(key)
    # Check if this is a BEV entry (tv_id = 1)
    # Key format includes tv_id
    if f', {BEV_TV_ID}, ' in key_str or f', {BEV_TV_ID})' in key_str:
        total_actual_energy += float(val)

print("\n" + "=" * 70)
print("BEV RESULTS")
print("=" * 70)

print(f"\n1. FLOW AND TKM (BEV only):")
print(f"   Total BEV flow: {total_flow_ktonnes:,.0f} ktonnes = {total_flow_ktonnes/1e6:.3f} Gt")
print(f"   Total BEV tkm:  {total_tkm:,.0f} Mtkm = {total_tkm/1e6:.3f} trillion tkm")

print(f"\n2. ENERGY VERIFICATION (BEV only):")
print(f"   Expected energy (from f * path * spec_cons/W): {total_expected_energy/1e6:.3f} TWh")
print(f"   Actual energy (s variable, BEV filtered):     {total_actual_energy/1e6:.3f} TWh")
diff_pct = abs(total_expected_energy - total_actual_energy) / total_expected_energy * 100 if total_expected_energy > 0 else 0
print(f"   Match: {'YES' if diff_pct < 0.1 else 'NO'} (diff: {diff_pct:.4f}%)")

print(f"\n3. AVERAGE BEV SPECIFIC ENERGY:")
avg_spec_energy = total_expected_energy / (total_tkm * 1000) if total_tkm > 0 else 0
print(f"   Average BEV energy per tkm: {avg_spec_energy:.4f} kWh/tkm")

print("\n" + "=" * 70)
print("BEV BREAKDOWN BY YEAR")
print("=" * 70)
print(f"{'Year':<8} {'Flow (kt)':<15} {'Tkm (Mtkm)':<15} {'Energy (GWh)':<15} {'kWh/tkm':<10}")
print("-" * 65)
for year in sorted(by_year.keys()):
    d = by_year[year]
    kwh_per_tkm = d['energy'] / (d['tkm'] * 1000) if d['tkm'] > 0 else 0
    print(f"{year:<8} {d['flow']:>12,.0f}   {d['tkm']:>12,.0f}   {d['energy']/1e3:>12,.1f}   {kwh_per_tkm:>8.4f}")
print("-" * 65)
print(f"{'TOTAL':<8} {total_flow_ktonnes:>12,.0f}   {total_tkm:>12,.0f}   {total_expected_energy/1e3:>12,.1f}   {avg_spec_energy:>8.4f}")

print("\n" + "=" * 70)
print("BEV BREAKDOWN BY GENERATION")
print("=" * 70)
print(f"{'Gen':<8} {'Flow (kt)':<15} {'Tkm (Mtkm)':<15} {'Energy (GWh)':<15} {'kWh/tkm':<10}")
print("-" * 65)
for g in sorted(by_gen.keys()):
    d = by_gen[g]
    kwh_per_tkm = d['energy'] / (d['tkm'] * 1000) if d['tkm'] > 0 else 0
    print(f"{g:<8} {d['flow']:>12,.0f}   {d['tkm']:>12,.0f}   {d['energy']/1e3:>12,.1f}   {kwh_per_tkm:>8.4f}")

print("\n" + "=" * 70)
print("CONCLUSION")
print("=" * 70)
print(f"""
BEV Energy Verification:

  Model result (s, BEV): {total_actual_energy/1e6:.3f} TWh
  Calculated:            {total_expected_energy/1e6:.3f} TWh
  Difference:            {abs(total_actual_energy - total_expected_energy):.0f} MWh

BEV share of total:
  Flow: {total_flow_ktonnes/512949*100:.1f}% of total flow
  Energy: {total_expected_energy/60598000*100:.1f}% of total energy
""")
