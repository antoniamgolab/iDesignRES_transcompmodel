"""
Final TCO verification from model outputs
With correct key parsing for each variable type
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
print("FINAL TCO VERIFICATION")
print("=" * 70)

# Find files
files = os.listdir(scenario_dir)
h_file = [f for f in files if '_h_dict.yaml' in f and 'plus' not in f and 'minus' not in f and 'exist' not in f][0]
h_plus_file = [f for f in files if 'h_plus_dict' in f][0]
s_file = [f for f in files if '_s_dict.yaml' in f][0]
f_file = [f for f in files if '_f_dict.yaml' in f][0]

# ============================================================================
# h and h_plus: Key format is (year, odpair_id, tv_id, generation)
# Example: (2040, 2336, 1, 2040)
# tv_id is the 3rd element (index 2)
# ============================================================================

def parse_h_key(key_str):
    """Parse (year, odpair_id, tv_id, generation)"""
    # Remove parentheses and split
    inner = key_str.strip('()')
    parts = inner.split(',')
    if len(parts) >= 3:
        try:
            return int(parts[2].strip())
        except:
            pass
    return None

# Load h (fleet)
with open(os.path.join(scenario_dir, h_file), 'r') as f:
    h_dict = yaml.safe_load(f)

fleet_years = {0: 0.0, 1: 0.0}
for key, val in h_dict.items():
    v = float(val)
    tv_id = parse_h_key(str(key))
    if tv_id in [0, 1]:
        fleet_years[tv_id] += v * time_step

# Load h_plus (purchases)
with open(os.path.join(scenario_dir, h_plus_file), 'r') as f:
    h_plus_dict = yaml.safe_load(f)

purchases = {0: 0.0, 1: 0.0}
for key, val in h_plus_dict.items():
    v = float(val)
    tv_id = parse_h_key(str(key))
    if tv_id in [0, 1]:
        purchases[tv_id] += v

# ============================================================================
# s: Key format is (year, (p, r, k, node), tv_id, (fuel, level), generation)
# Example: (2024, (0, 1508, 1508, 10), 0, (1, 0), 2020)
# tv_id is after the path tuple, before the fuel tuple
# ============================================================================

def parse_s_key(key_str):
    """Parse s key to get tv_id"""
    # After the inner tuple closes, we have: ), tv_id, (
    match = re.search(r'\),\s*(\d+),\s*\(', key_str)
    if match:
        return int(match.group(1))
    return None

with open(os.path.join(scenario_dir, s_file), 'r') as f:
    s_dict = yaml.safe_load(f)

energy_mwh = {0: 0.0, 1: 0.0}
for key, val in s_dict.items():
    v = float(val)
    tv_id = parse_s_key(str(key))
    if tv_id in [0, 1]:
        energy_mwh[tv_id] += v

# ============================================================================
# f: Key format is (year, (p, r, k), (mode, tv_id), generation)
# Example: (2024, (0, 1508, 1508), (0, 0), 2020)
# tv_id is in the last tuple before generation
# ============================================================================

def parse_f_key(key_str):
    """Parse f key to get tv_id from (mode, tv_id) tuple"""
    # Find the (mode, tv_id) pattern before the final generation
    # Pattern: ), (mode, tv_id), gen)
    match = re.search(r'\),\s*\((\d+),\s*(\d+)\),\s*\d+\)', key_str)
    if match:
        return int(match.group(2))
    return None

with open(os.path.join(scenario_dir, f_file), 'r') as f:
    f_dict = yaml.safe_load(f)

flow_ktonnes = {0: 0.0, 1: 0.0}
for key, val in f_dict.items():
    v = float(val)
    tv_id = parse_f_key(str(key))
    if tv_id in [0, 1]:
        flow_ktonnes[tv_id] += v * time_step

# ============================================================================
# RESULTS
# ============================================================================

print("\n--- Raw Data from Model ---")
print(f"\nFleet-years:        ICEV: {fleet_years[0]:>12,.0f}    BEV: {fleet_years[1]:>12,.0f}")
print(f"Purchases:          ICEV: {purchases[0]:>12,.0f}    BEV: {purchases[1]:>12,.0f}")
print(f"Energy (MWh):       ICEV: {energy_mwh[0]:>12,.0f}    BEV: {energy_mwh[1]:>12,.0f}")
print(f"Flow (ktonnes):     ICEV: {flow_ktonnes[0]:>12,.0f}    BEV: {flow_ktonnes[1]:>12,.0f}")

# ============================================================================
# TCO CALCULATION
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
    print(f"  Capital:     {capital/1e9:>8.2f} B EUR  ({capital/total*100 if total > 0 else 0:5.1f}%)")
    print(f"  Maintenance: {maintenance/1e9:>8.2f} B EUR  ({maintenance/total*100 if total > 0 else 0:5.1f}%)")
    print(f"  Fuel:        {fuel/1e9:>8.2f} B EUR  ({fuel/total*100 if total > 0 else 0:5.1f}%)")
    print(f"  TOTAL:       {total/1e9:>8.2f} B EUR")

    if vkm > 0:
        print(f"\n  EUR per km (from model outputs):")
        print(f"    Capital:     {capital/vkm:.4f} EUR/km")
        print(f"    Maintenance: {maintenance/vkm:.4f} EUR/km")
        print(f"    Fuel:        {fuel/vkm:.4f} EUR/km")
        print(f"    TOTAL:       {total/vkm:.4f} EUR/km")

        # Energy per km check
        actual_kwh_per_km = energy_mwh[tv_id] * 1000 / vkm
        print(f"\n  Energy check:")
        print(f"    Actual:   {actual_kwh_per_km:.3f} kWh/km")
        print(f"    Expected: {tv_params[tv_id]['spec_cons']:.3f} kWh/km (from spec_cons)")
        print(f"    Ratio:    {actual_kwh_per_km / tv_params[tv_id]['spec_cons']:.2%}")

# ============================================================================
# Comparison with theoretical
# ============================================================================

print("\n" + "=" * 70)
print("COMPARISON: MODEL OUTPUT vs THEORETICAL (EUR/km)")
print("=" * 70)

print(f"\n{'Component':<12} {'ICEV Model':>12} {'ICEV Theory':>12} {'BEV Model':>12} {'BEV Theory':>12}")
print("-" * 62)

icev_vkm = fleet_years[0] * annual_range
bev_vkm = fleet_years[1] * annual_range

# Capital
icev_cap_m = purchases[0] * tv_params[0]['capital'] / icev_vkm if icev_vkm > 0 else 0
bev_cap_m = purchases[1] * tv_params[1]['capital'] / bev_vkm if bev_vkm > 0 else 0
icev_cap_t = tv_params[0]['capital'] / (12 * annual_range)
bev_cap_t = tv_params[1]['capital'] / (12 * annual_range)
print(f"{'Capital':<12} {icev_cap_m:>12.4f} {icev_cap_t:>12.4f} {bev_cap_m:>12.4f} {bev_cap_t:>12.4f}")

# Maintenance
icev_maint = tv_params[0]['maint'] / annual_range
bev_maint = tv_params[1]['maint'] / annual_range
print(f"{'Maintenance':<12} {icev_maint:>12.4f} {icev_maint:>12.4f} {bev_maint:>12.4f} {bev_maint:>12.4f}")

# Fuel
icev_fuel_m = energy_mwh[0] * 1000 * tv_params[0]['fuel_price'] / icev_vkm if icev_vkm > 0 else 0
bev_fuel_m = energy_mwh[1] * 1000 * tv_params[1]['fuel_price'] / bev_vkm if bev_vkm > 0 else 0
icev_fuel_t = tv_params[0]['spec_cons'] * tv_params[0]['fuel_price']
bev_fuel_t = tv_params[1]['spec_cons'] * tv_params[1]['fuel_price']
print(f"{'Fuel':<12} {icev_fuel_m:>12.4f} {icev_fuel_t:>12.4f} {bev_fuel_m:>12.4f} {bev_fuel_t:>12.4f}")

print("-" * 62)

# Total
icev_tot_m = icev_cap_m + icev_maint + icev_fuel_m
bev_tot_m = bev_cap_m + bev_maint + bev_fuel_m
icev_tot_t = icev_cap_t + icev_maint + icev_fuel_t
bev_tot_t = bev_cap_t + bev_maint + bev_fuel_t
print(f"{'TOTAL':<12} {icev_tot_m:>12.4f} {icev_tot_t:>12.4f} {bev_tot_m:>12.4f} {bev_tot_t:>12.4f}")

print("\n" + "=" * 70)
print("KEY FINDING: FUEL DISCREPANCY")
print("=" * 70)
if icev_vkm > 0:
    print(f"\nThe fuel cost from model output ({icev_fuel_m:.4f} EUR/km) is much LOWER")
    print(f"than theoretical ({icev_fuel_t:.4f} EUR/km).")
    print(f"\nThis is because the model's s variable (energy) is only {energy_mwh[0] * 1000 / icev_vkm / tv_params[0]['spec_cons']:.1%}")
    print(f"of what spec_cons x vehicle-km would give.")
    print(f"\nPossible reasons:")
    print(f"  1. s only counts energy at charging/fueling locations, not total consumed")
    print(f"  2. Different accounting for loaded vs empty trips")
    print(f"  3. Unit conversion issue in s variable")
