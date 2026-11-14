"""
Cross-check TCO per km using actual model outputs:
- Flow (f) to get tonnes transported
- Fleet (h) to get vehicle counts
- Energy (s) to get fuel consumption
- Path lengths from input data
"""

import yaml
import os

results_dir = os.path.join(os.path.dirname(__file__), 'results', 'fleet_verification_compare')
input_dir = os.path.join(os.path.dirname(__file__), 'input_data', 'uncertainty_scenarios', 'scenario_001')

# Parameters
time_step = 4
years = [2020, 2024, 2028, 2032, 2036, 2040, 2044, 2048, 2052, 2056, 2060]

# Vehicle parameters
tv_params = {
    0: {'name': 'ICEV', 'capital': 145571, 'maint': 20703, 'fuel_price': 0.1845},
    1: {'name': 'BEV', 'capital': 557714, 'maint': 14364, 'fuel_price': 0.17}
}

scenario = 'scenario_001'
config = 'with_fuel'
scenario_dir = os.path.join(results_dir, scenario, config)

print("=" * 70)
print("CROSS-CHECK: TCO from Model Outputs")
print("=" * 70)

# ============================================================================
# 1. Load h_dict to get fleet by technology
# ============================================================================
h_files = [f for f in os.listdir(scenario_dir) if '_h_dict.yaml' in f and 'plus' not in f and 'minus' not in f and 'exist' not in f]
fleet_years = {0: 0.0, 1: 0.0}  # fleet-years by technology

if h_files:
    with open(os.path.join(scenario_dir, h_files[0]), 'r') as f:
        h_dict = yaml.safe_load(f)

    for key, value in h_dict.items():
        val = float(value)
        if val > 0.001:
            # Key format: (year, odpair_id, tv_id, generation)
            key_str = str(key).strip('()')
            parts = key_str.split(',')
            if len(parts) >= 3:
                try:
                    tv_id = int(parts[2].strip())
                    if tv_id in [0, 1]:
                        fleet_years[tv_id] += val * time_step  # vehicle-years
                except:
                    pass

print(f"\n1. FLEET (from h_dict):")
print(f"   ICEV fleet-years: {fleet_years[0]:,.0f}")
print(f"   BEV fleet-years:  {fleet_years[1]:,.0f}")

# ============================================================================
# 2. Load h_plus_dict to get purchases
# ============================================================================
h_plus_files = [f for f in os.listdir(scenario_dir) if 'h_plus_dict' in f]
purchases = {0: 0.0, 1: 0.0}  # number of vehicles purchased

if h_plus_files:
    with open(os.path.join(scenario_dir, h_plus_files[0]), 'r') as f:
        h_plus = yaml.safe_load(f)

    for key, value in h_plus.items():
        val = float(value)
        if val > 0.001:
            key_str = str(key).strip('()')
            parts = key_str.split(',')
            if len(parts) >= 3:
                try:
                    tv_id = int(parts[2].strip())
                    if tv_id in [0, 1]:
                        purchases[tv_id] += val
                except:
                    pass

print(f"\n2. PURCHASES (from h_plus_dict):")
print(f"   ICEV purchased: {purchases[0]:,.0f} vehicles")
print(f"   BEV purchased:  {purchases[1]:,.0f} vehicles")

# ============================================================================
# 3. Load s_dict to get energy consumption by technology
# ============================================================================
s_files = [f for f in os.listdir(scenario_dir) if '_s_dict' in f and f.endswith('.yaml')]
energy_mwh = {0: 0.0, 1: 0.0}

if s_files:
    with open(os.path.join(scenario_dir, s_files[0]), 'r') as f:
        s_dict = yaml.safe_load(f)

    for key, value in s_dict.items():
        val = float(value)  # MWh
        # Key format includes tv_id - need to parse
        # Format: (year, path_tuple, tv_id, fuel_level_tuple, generation)
        key_str = str(key)
        # Find tv_id after the path tuple closes
        parts = key_str.split('),')
        if len(parts) >= 2:
            try:
                tv_part = parts[1].strip().lstrip(' ')
                tv_id = int(tv_part.split(',')[0].strip())
                if tv_id in [0, 1]:
                    energy_mwh[tv_id] += val
            except:
                pass

print(f"\n3. ENERGY CONSUMPTION (from s_dict):")
print(f"   ICEV energy: {energy_mwh[0]:,.0f} MWh")
print(f"   BEV energy:  {energy_mwh[1]:,.0f} MWh")

# ============================================================================
# 4. Load f_dict to get flow (tonnes) by technology
# ============================================================================
f_files = [f for f in os.listdir(scenario_dir) if '_f_dict.yaml' in f]
flow_ktonnes = {0: 0.0, 1: 0.0}

if f_files:
    with open(os.path.join(scenario_dir, f_files[0]), 'r') as f:
        f_dict = yaml.safe_load(f)

    for key, value in f_dict.items():
        val = float(value)  # thousands of tonnes
        if val > 0.001:
            # Key format: (year, (p, r, k), (mode, tv_id), generation)
            key_str = str(key)
            # Parse to find tv_id
            parts = key_str.split('),')
            if len(parts) >= 2:
                try:
                    # Mode and tv_id are in the second tuple
                    mode_tv_part = parts[1].strip()
                    if mode_tv_part.startswith('('):
                        mode_tv_part = mode_tv_part[1:]
                    nums = mode_tv_part.split(',')
                    if len(nums) >= 2:
                        tv_id = int(nums[1].strip().rstrip(')'))
                        if tv_id in [0, 1]:
                            flow_ktonnes[tv_id] += val * time_step
                except:
                    pass

print(f"\n4. FLOW (from f_dict, in thousand-tonnes × years):")
print(f"   ICEV flow: {flow_ktonnes[0]:,.0f} ktonnes")
print(f"   BEV flow:  {flow_ktonnes[1]:,.0f} ktonnes")

# ============================================================================
# 5. Calculate vehicle-km from fleet-years and annual range
# ============================================================================
annual_range = 136750  # km/year
vehicle_km = {
    0: fleet_years[0] * annual_range,
    1: fleet_years[1] * annual_range
}

print(f"\n5. VEHICLE-KM (fleet-years x {annual_range:,} km/year):")
print(f"   ICEV: {vehicle_km[0]/1e9:.2f} billion km")
print(f"   BEV:  {vehicle_km[1]/1e9:.2f} billion km")

# ============================================================================
# 6. Calculate costs
# ============================================================================
print("\n" + "=" * 70)
print("COST CALCULATION FROM MODEL OUTPUTS")
print("=" * 70)

for tv_id in [0, 1]:
    name = tv_params[tv_id]['name']

    # Capital = purchases × capital_cost
    capital = purchases[tv_id] * tv_params[tv_id]['capital']

    # Maintenance = fleet-years × annual maintenance
    maintenance = fleet_years[tv_id] * tv_params[tv_id]['maint']

    # Fuel = energy (MWh) × 1000 (to kWh) × price
    fuel = energy_mwh[tv_id] * 1000 * tv_params[tv_id]['fuel_price']

    total = capital + maintenance + fuel

    # Per km
    if vehicle_km[tv_id] > 0:
        capital_per_km = capital / vehicle_km[tv_id]
        maint_per_km = maintenance / vehicle_km[tv_id]
        fuel_per_km = fuel / vehicle_km[tv_id]
        total_per_km = total / vehicle_km[tv_id]
    else:
        capital_per_km = maint_per_km = fuel_per_km = total_per_km = 0

    print(f"\n{name}:")
    print(f"  Total costs:")
    print(f"    Capital:     {capital/1e9:>8.2f} B EUR")
    print(f"    Maintenance: {maintenance/1e9:>8.2f} B EUR")
    print(f"    Fuel:        {fuel/1e9:>8.2f} B EUR")
    print(f"    TOTAL:       {total/1e9:>8.2f} B EUR")

    print(f"\n  Per km (vehicle-km = {vehicle_km[tv_id]/1e9:.2f}B km):")
    if total_per_km > 0:
        print(f"    Capital:     {capital_per_km:.4f} EUR/km  ({capital/total*100:5.1f}%)")
        print(f"    Maintenance: {maint_per_km:.4f} EUR/km  ({maintenance/total*100:5.1f}%)")
        print(f"    Fuel:        {fuel_per_km:.4f} EUR/km  ({fuel/total*100:5.1f}%)")
        print(f"    TOTAL:       {total_per_km:.4f} EUR/km")
    else:
        print(f"    (No vehicle-km for {name})")

# ============================================================================
# 7. Compare with theoretical values
# ============================================================================
print("\n" + "=" * 70)
print("COMPARISON: Model Output vs Theoretical (from parameters)")
print("=" * 70)

print(f"\n{'Component':<15} {'ICEV Model':<12} {'ICEV Theory':<12} {'BEV Model':<12} {'BEV Theory':<12}")
print("-" * 65)

# Theoretical values
icev_cap_theory = 145571 / (12 * 136750)
icev_maint_theory = 20703 / 136750
icev_fuel_theory = 3.639 * 0.1845

bev_cap_theory = 557714 / (12 * 136750)
bev_maint_theory = 14364 / 136750
bev_fuel_theory = 2.056 * 0.17

# Model values (calculate if we have data)
if vehicle_km[0] > 0:
    icev_cap_model = purchases[0] * tv_params[0]['capital'] / vehicle_km[0]
    icev_maint_model = fleet_years[0] * tv_params[0]['maint'] / vehicle_km[0]
    icev_fuel_model = energy_mwh[0] * 1000 * tv_params[0]['fuel_price'] / vehicle_km[0]
else:
    icev_cap_model = icev_maint_model = icev_fuel_model = 0

if vehicle_km[1] > 0:
    bev_cap_model = purchases[1] * tv_params[1]['capital'] / vehicle_km[1]
    bev_maint_model = fleet_years[1] * tv_params[1]['maint'] / vehicle_km[1]
    bev_fuel_model = energy_mwh[1] * 1000 * tv_params[1]['fuel_price'] / vehicle_km[1]
else:
    bev_cap_model = bev_maint_model = bev_fuel_model = 0

print(f"{'Capital':<15} {icev_cap_model:>10.4f}   {icev_cap_theory:>10.4f}   {bev_cap_model:>10.4f}   {bev_cap_theory:>10.4f}")
print(f"{'Maintenance':<15} {icev_maint_model:>10.4f}   {icev_maint_theory:>10.4f}   {bev_maint_model:>10.4f}   {bev_maint_theory:>10.4f}")
print(f"{'Fuel':<15} {icev_fuel_model:>10.4f}   {icev_fuel_theory:>10.4f}   {bev_fuel_model:>10.4f}   {bev_fuel_theory:>10.4f}")
print("-" * 65)
icev_total_model = icev_cap_model + icev_maint_model + icev_fuel_model
icev_total_theory = icev_cap_theory + icev_maint_theory + icev_fuel_theory
bev_total_model = bev_cap_model + bev_maint_model + bev_fuel_model
bev_total_theory = bev_cap_theory + bev_maint_theory + bev_fuel_theory
print(f"{'TOTAL':<15} {icev_total_model:>10.4f}   {icev_total_theory:>10.4f}   {bev_total_model:>10.4f}   {bev_total_theory:>10.4f}")
