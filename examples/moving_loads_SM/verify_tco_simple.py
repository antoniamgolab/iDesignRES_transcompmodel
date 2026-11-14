"""
Simple TCO verification from model outputs
"""
import yaml
import os
import re

results_dir = os.path.join(os.path.dirname(__file__), 'results', 'fleet_verification_compare')
scenario_dir = os.path.join(results_dir, 'scenario_001', 'with_fuel')

# Parameters
time_step = 4
annual_range = 136750  # km/year
capacity = 25  # tonnes

tv_params = {
    0: {'name': 'ICEV', 'capital': 145571, 'maint': 20703, 'spec_cons': 3.639, 'fuel_price': 0.1845},
    1: {'name': 'BEV', 'capital': 557714, 'maint': 14364, 'spec_cons': 2.056, 'fuel_price': 0.17}
}

print("=" * 70)
print("SIMPLE TCO VERIFICATION")
print("=" * 70)

# ============================================================================
# Load and parse all data
# ============================================================================

# Find files
files = os.listdir(scenario_dir)
h_file = [f for f in files if '_h_dict.yaml' in f and 'plus' not in f and 'minus' not in f and 'exist' not in f][0]
h_plus_file = [f for f in files if 'h_plus_dict' in f][0]
s_file = [f for f in files if '_s_dict.yaml' in f][0]
f_file = [f for f in files if '_f_dict.yaml' in f][0]

# Regex pattern to extract tv_id from key
# Key format: (year, (...), tv_id, (...), gen) or (year, (..., node), tv_id, (...), gen)

def get_tv_id_from_key(key_str):
    """Extract tv_id which is the standalone integer after a tuple"""
    # Pattern: look for ), followed by space and a single digit, followed by ,
    match = re.search(r'\),\s*(\d+),', key_str)
    if match:
        return int(match.group(1))
    return None

# Load h (fleet)
with open(os.path.join(scenario_dir, h_file), 'r') as f:
    h_dict = yaml.safe_load(f)

fleet_years = {0: 0.0, 1: 0.0}
for key, val in h_dict.items():
    v = float(val)
    tv_id = get_tv_id_from_key(str(key))
    if tv_id in [0, 1]:
        fleet_years[tv_id] += v * time_step

# Load h_plus (purchases)
with open(os.path.join(scenario_dir, h_plus_file), 'r') as f:
    h_plus_dict = yaml.safe_load(f)

purchases = {0: 0.0, 1: 0.0}
for key, val in h_plus_dict.items():
    v = float(val)
    tv_id = get_tv_id_from_key(str(key))
    if tv_id in [0, 1]:
        purchases[tv_id] += v

# Load s (energy) - values are in MWh
with open(os.path.join(scenario_dir, s_file), 'r') as f:
    s_dict = yaml.safe_load(f)

energy_mwh = {0: 0.0, 1: 0.0}
for key, val in s_dict.items():
    v = float(val)
    tv_id = get_tv_id_from_key(str(key))
    if tv_id in [0, 1]:
        energy_mwh[tv_id] += v

# Load f (flow) - values in thousands of tonnes
with open(os.path.join(scenario_dir, f_file), 'r') as f:
    f_dict = yaml.safe_load(f)

flow_ktonnes = {0: 0.0, 1: 0.0}
for key, val in f_dict.items():
    v = float(val)
    # For f, the key format is different: (year, (p,r,k), (mode, tv_id), gen)
    # Need to find tv_id in the (mode, tv_id) tuple
    match = re.search(r'\((\d+),\s*(\d+)\),\s*\d+\)', str(key))
    if match:
        tv_id = int(match.group(2))
        if tv_id in [0, 1]:
            flow_ktonnes[tv_id] += v * time_step

print("\n--- Raw Data from Model ---")
print(f"\nFleet-years:        ICEV: {fleet_years[0]:>12,.0f}    BEV: {fleet_years[1]:>12,.0f}")
print(f"Purchases:          ICEV: {purchases[0]:>12,.0f}    BEV: {purchases[1]:>12,.0f}")
print(f"Energy (MWh):       ICEV: {energy_mwh[0]:>12,.0f}    BEV: {energy_mwh[1]:>12,.0f}")
print(f"Flow (ktonnes):     ICEV: {flow_ktonnes[0]:>12,.0f}    BEV: {flow_ktonnes[1]:>12,.0f}")

# ============================================================================
# Calculate derived metrics
# ============================================================================

print("\n--- Derived Metrics ---")

for tv_id in [0, 1]:
    name = tv_params[tv_id]['name']

    # Vehicle-km = fleet-years × annual_range
    vkm = fleet_years[tv_id] * annual_range

    # Tonne-km = flow × average_path_length
    # Calculate avg path length from: vkm = (flow / capacity) × path_length
    # So path_length = vkm × capacity / flow
    if flow_ktonnes[tv_id] > 0:
        avg_path = vkm * capacity / (flow_ktonnes[tv_id] * 1000)
        tkm = flow_ktonnes[tv_id] * 1000 * avg_path
    else:
        avg_path = 0
        tkm = 0

    # Expected energy = spec_cons × vkm
    expected_energy = tv_params[tv_id]['spec_cons'] * vkm / 1e6  # MWh

    # Actual energy per vkm
    actual_per_vkm = energy_mwh[tv_id] * 1e6 / vkm if vkm > 0 else 0  # kWh/km

    print(f"\n{name}:")
    print(f"  Vehicle-km:        {vkm/1e9:.2f} billion km")
    print(f"  Avg path length:   {avg_path:.0f} km")
    print(f"  Tonne-km:          {tkm/1e9:.2f} billion tkm")
    print(f"  Expected energy:   {expected_energy/1e6:.2f} TWh (spec_cons x vkm)")
    print(f"  Actual energy:     {energy_mwh[tv_id]/1e6:.2f} TWh (from s_dict)")
    print(f"  Ratio expected/actual: {expected_energy/energy_mwh[tv_id]:.2f}x")
    print(f"  Actual kWh/km:     {actual_per_vkm:.3f} (expected: {tv_params[tv_id]['spec_cons']:.3f})")

# ============================================================================
# TCO Calculation
# ============================================================================

print("\n" + "=" * 70)
print("TCO CALCULATION")
print("=" * 70)

for tv_id in [0, 1]:
    name = tv_params[tv_id]['name']

    vkm = fleet_years[tv_id] * annual_range

    # Costs
    capital = purchases[tv_id] * tv_params[tv_id]['capital']
    maintenance = fleet_years[tv_id] * tv_params[tv_id]['maint']
    fuel = energy_mwh[tv_id] * 1000 * tv_params[tv_id]['fuel_price']  # MWh to kWh

    total = capital + maintenance + fuel

    print(f"\n{name}:")
    print(f"  Capital:     {capital/1e9:>8.2f} B EUR  ({capital/total*100:5.1f}%)")
    print(f"  Maintenance: {maintenance/1e9:>8.2f} B EUR  ({maintenance/total*100:5.1f}%)")
    print(f"  Fuel:        {fuel/1e9:>8.2f} B EUR  ({fuel/total*100:5.1f}%)")
    print(f"  TOTAL:       {total/1e9:>8.2f} B EUR")

    if vkm > 0:
        print(f"\n  Per km:")
        print(f"    Capital:     {capital/vkm:.4f} EUR/km")
        print(f"    Maintenance: {maintenance/vkm:.4f} EUR/km")
        print(f"    Fuel:        {fuel/vkm:.4f} EUR/km")
        print(f"    TOTAL:       {total/vkm:.4f} EUR/km")

# ============================================================================
# Comparison with theoretical
# ============================================================================

print("\n" + "=" * 70)
print("COMPARISON: MODEL vs THEORETICAL (EUR/km)")
print("=" * 70)

print(f"\n{'Component':<12} {'ICEV Model':>12} {'ICEV Theory':>12} {'BEV Model':>12} {'BEV Theory':>12}")
print("-" * 62)

for comp in ['Capital', 'Maint', 'Fuel', 'TOTAL']:
    if comp == 'Capital':
        icev_m = purchases[0] * tv_params[0]['capital'] / (fleet_years[0] * annual_range) if fleet_years[0] > 0 else 0
        bev_m = purchases[1] * tv_params[1]['capital'] / (fleet_years[1] * annual_range) if fleet_years[1] > 0 else 0
        icev_t = tv_params[0]['capital'] / (12 * annual_range)
        bev_t = tv_params[1]['capital'] / (12 * annual_range)
    elif comp == 'Maint':
        icev_m = tv_params[0]['maint'] / annual_range
        bev_m = tv_params[1]['maint'] / annual_range
        icev_t = icev_m
        bev_t = bev_m
    elif comp == 'Fuel':
        icev_m = energy_mwh[0] * 1000 * tv_params[0]['fuel_price'] / (fleet_years[0] * annual_range) if fleet_years[0] > 0 else 0
        bev_m = energy_mwh[1] * 1000 * tv_params[1]['fuel_price'] / (fleet_years[1] * annual_range) if fleet_years[1] > 0 else 0
        icev_t = tv_params[0]['spec_cons'] * tv_params[0]['fuel_price']
        bev_t = tv_params[1]['spec_cons'] * tv_params[1]['fuel_price']
    else:  # TOTAL
        icev_m = (purchases[0] * tv_params[0]['capital'] + fleet_years[0] * tv_params[0]['maint'] +
                  energy_mwh[0] * 1000 * tv_params[0]['fuel_price']) / (fleet_years[0] * annual_range) if fleet_years[0] > 0 else 0
        bev_m = (purchases[1] * tv_params[1]['capital'] + fleet_years[1] * tv_params[1]['maint'] +
                  energy_mwh[1] * 1000 * tv_params[1]['fuel_price']) / (fleet_years[1] * annual_range) if fleet_years[1] > 0 else 0
        icev_t = tv_params[0]['capital'] / (12 * annual_range) + tv_params[0]['maint'] / annual_range + tv_params[0]['spec_cons'] * tv_params[0]['fuel_price']
        bev_t = tv_params[1]['capital'] / (12 * annual_range) + tv_params[1]['maint'] / annual_range + tv_params[1]['spec_cons'] * tv_params[1]['fuel_price']

    print(f"{comp:<12} {icev_m:>12.4f} {icev_t:>12.4f} {bev_m:>12.4f} {bev_t:>12.4f}")
