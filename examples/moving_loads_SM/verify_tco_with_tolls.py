"""
TCO / Levelized Cost Calculation with TOLLS included
Verification that model now matches literature values
"""
import yaml
import os
import re

results_dir = os.path.join(os.path.dirname(__file__), 'results', 'fleet_verification_compare')
scenario_dir = os.path.join(results_dir, 'scenario_001', 'with_fuel')
input_dir = os.path.join(os.path.dirname(__file__), 'input_data', 'uncertainty_scenarios', 'scenario_001')

g_init = 2008
BEV_TV_ID = 1
ICEV_TV_ID = 0

# Toll rates (EUR/km) - from SM_preprocessing.py
# Sources: EU Directive 2022/362, IRU data, ICCT 2023
TOLL_ICEV = 0.10   # EUR/km for Euro VI diesel
TOLL_BEV = 0.036   # EUR/km for ZEV (64% reduction)

# Load TechVehicle data
with open(os.path.join(input_dir, 'TechVehicle.yaml'), 'r') as f:
    tech_vehicles = yaml.safe_load(f)

tv_data = {}
for tv in tech_vehicles:
    tv_data[tv['id']] = {
        'spec_cons': tv['spec_cons'],
        'W': tv['W'],
        'capital_cost': tv['capital_cost'],
        'maintenance_cost_annual': tv['maintenance_cost_annual'],
        'AnnualRange': tv['AnnualRange'],
        'Lifetime': tv['Lifetime']
    }

# Load path lengths
with open(os.path.join(input_dir, 'Path.yaml'), 'r') as f:
    paths = yaml.safe_load(f)
path_lengths = {p['id']: p['length'] for p in paths}

# Fuel prices
electricity_price = 0.15  # EUR/kWh
diesel_price = 0.1845  # EUR/kWh

# Load f_dict
files = os.listdir(scenario_dir)
f_file = [f for f in files if '_f_dict.yaml' in f][0]
with open(os.path.join(scenario_dir, f_file), 'r') as f:
    f_dict = yaml.safe_load(f)

print("=" * 80)
print("TCO VERIFICATION WITH TOLLS INCLUDED")
print("=" * 80)
print(f"\nToll rates (EU Eurovignette Directive 2022/362):")
print(f"  ICEV: {TOLL_ICEV:.2f} EUR/km")
print(f"  BEV:  {TOLL_BEV:.3f} EUR/km (64% ZEV discount)")

# Calculate for both BEV and ICEV
results = {}

for tv_id, tv_name in [(ICEV_TV_ID, 'ICEV'), (BEV_TV_ID, 'BEV')]:
    toll_rate = TOLL_ICEV if tv_name == 'ICEV' else TOLL_BEV

    total_flow = 0  # ktonnes
    total_tkm = 0  # Mtkm
    total_energy = 0  # MWh
    total_vkm = 0  # vehicle-km

    for key, val in f_dict.items():
        f_val = float(val)
        if f_val < 0.001:
            continue

        key_str = str(key)
        match = re.search(r'\((\d+),\s*\((\d+),\s*(\d+),\s*(\d+)\),\s*\((\d+),\s*(\d+)\),\s*(\d+)\)', key_str)
        if match:
            year = int(match.group(1))
            k_id = int(match.group(4))
            this_tv_id = int(match.group(6))
            g = int(match.group(7))

            if this_tv_id != tv_id:
                continue

            path_len = path_lengths.get(k_id, 0)
            idx = g - g_init

            if 0 <= idx < len(tv_data[tv_id]['spec_cons']):
                spec_cons = tv_data[tv_id]['spec_cons'][idx]
                W = tv_data[tv_id]['W'][idx]
            else:
                continue

            tkm = f_val * path_len / 1000  # Mtkm
            energy = (spec_cons / W) * path_len * f_val  # MWh
            vkm = f_val * 1000 * path_len / W  # vehicle-km (flow in tonnes × distance / payload)

            total_flow += f_val
            total_tkm += tkm
            total_energy += energy
            total_vkm += vkm

    results[tv_name] = {
        'flow': total_flow,
        'tkm': total_tkm,
        'energy': total_energy,
        'vkm': total_vkm,
        'toll_rate': toll_rate
    }

# Calculate costs per vehicle (using g=2032 parameters)
print("\n" + "=" * 80)
print("COST CALCULATION (g=2032 parameters)")
print("=" * 80)

for tv_name in ['ICEV', 'BEV']:
    tv_id = ICEV_TV_ID if tv_name == 'ICEV' else BEV_TV_ID
    r = results[tv_name]

    idx_2032 = 2032 - g_init
    capital = tv_data[tv_id]['capital_cost'][idx_2032 - (2020 - g_init)]  # capital_cost is indexed from 2020
    maintenance = tv_data[tv_id]['maintenance_cost_annual'][0][idx_2032 - (2020 - g_init)]
    annual_range = tv_data[tv_id]['AnnualRange'][idx_2032]
    lifetime = tv_data[tv_id]['Lifetime'][idx_2032]
    spec_cons = tv_data[tv_id]['spec_cons'][idx_2032]
    W = tv_data[tv_id]['W'][idx_2032]

    fuel_price = electricity_price if tv_name == 'BEV' else diesel_price
    toll_rate = TOLL_BEV if tv_name == 'BEV' else TOLL_ICEV

    # TCO calculation per vehicle over lifetime
    total_km = annual_range * lifetime
    total_energy_vehicle = spec_cons * total_km  # kWh
    fuel_cost = total_energy_vehicle * fuel_price  # EUR
    total_maintenance = maintenance * lifetime
    toll_cost = toll_rate * total_km  # EUR

    tco_per_vehicle = capital + fuel_cost + total_maintenance + toll_cost

    # Lifetime tkm per vehicle
    tkm_per_vehicle = total_km * W / 1000  # Mtkm

    # Levelized cost components (ct/tkm)
    capital_per_tkm = capital / (tkm_per_vehicle * 1000) * 100
    fuel_per_tkm = fuel_cost / (tkm_per_vehicle * 1000) * 100
    maint_per_tkm = total_maintenance / (tkm_per_vehicle * 1000) * 100
    toll_per_tkm = toll_cost / (tkm_per_vehicle * 1000) * 100
    total_per_tkm = tco_per_vehicle / (tkm_per_vehicle * 1000) * 100

    print(f"\n{tv_name}:")
    print("-" * 50)
    print(f"  Parameters (g=2032):")
    print(f"    Capital:      {capital:>12,.0f} EUR")
    print(f"    Maintenance:  {maintenance:>12,.0f} EUR/year")
    print(f"    spec_cons:    {spec_cons:>12.3f} kWh/km")
    print(f"    Payload W:    {W:>12.1f} tonnes")
    print(f"    Toll rate:    {toll_rate:>12.3f} EUR/km")

    print(f"\n  TCO per vehicle (lifetime = {lifetime} years, {total_km/1e6:.2f}M km):")
    print(f"    Capital:      {capital:>12,.0f} EUR")
    print(f"    Fuel/Energy:  {fuel_cost:>12,.0f} EUR")
    print(f"    Maintenance:  {total_maintenance:>12,.0f} EUR")
    print(f"    Tolls:        {toll_cost:>12,.0f} EUR")
    print(f"    ----------------------------------------")
    print(f"    TOTAL TCO:    {tco_per_vehicle:>12,.0f} EUR")

    print(f"\n  Levelized cost (ct/tkm):")
    print(f"    Capital:      {capital_per_tkm:>12.2f} ct/tkm")
    print(f"    Fuel/Energy:  {fuel_per_tkm:>12.2f} ct/tkm")
    print(f"    Maintenance:  {maint_per_tkm:>12.2f} ct/tkm")
    print(f"    Tolls:        {toll_per_tkm:>12.2f} ct/tkm")
    print(f"    ----------------------------------------")
    print(f"    TOTAL:        {total_per_tkm:>12.2f} ct/tkm")

    results[tv_name]['capital'] = capital
    results[tv_name]['fuel_cost'] = fuel_cost
    results[tv_name]['maintenance'] = total_maintenance
    results[tv_name]['toll_cost'] = toll_cost
    results[tv_name]['tco'] = tco_per_vehicle
    results[tv_name]['levelized'] = total_per_tkm / 100  # EUR/tkm
    results[tv_name]['tkm_per_vehicle'] = tkm_per_vehicle
    results[tv_name]['W'] = W

# Comparison summary
print("\n" + "=" * 80)
print("COMPARISON SUMMARY")
print("=" * 80)

icev = results['ICEV']
bev = results['BEV']

print(f"\n{'Component (ct/tkm)':<25} {'ICEV':>12} {'BEV':>12} {'Delta':>12}")
print("-" * 65)
print(f"{'Capital':<25} {icev['capital']/(icev['tkm_per_vehicle']*1000)*100:>12.2f} {bev['capital']/(bev['tkm_per_vehicle']*1000)*100:>12.2f} {(bev['capital']/(bev['tkm_per_vehicle']*1000) - icev['capital']/(icev['tkm_per_vehicle']*1000))*100:>+12.2f}")
print(f"{'Fuel/Energy':<25} {icev['fuel_cost']/(icev['tkm_per_vehicle']*1000)*100:>12.2f} {bev['fuel_cost']/(bev['tkm_per_vehicle']*1000)*100:>12.2f} {(bev['fuel_cost']/(bev['tkm_per_vehicle']*1000) - icev['fuel_cost']/(icev['tkm_per_vehicle']*1000))*100:>+12.2f}")
print(f"{'Maintenance':<25} {icev['maintenance']/(icev['tkm_per_vehicle']*1000)*100:>12.2f} {bev['maintenance']/(bev['tkm_per_vehicle']*1000)*100:>12.2f} {(bev['maintenance']/(bev['tkm_per_vehicle']*1000) - icev['maintenance']/(icev['tkm_per_vehicle']*1000))*100:>+12.2f}")
print(f"{'Tolls':<25} {icev['toll_cost']/(icev['tkm_per_vehicle']*1000)*100:>12.2f} {bev['toll_cost']/(bev['tkm_per_vehicle']*1000)*100:>12.2f} {(bev['toll_cost']/(bev['tkm_per_vehicle']*1000) - icev['toll_cost']/(icev['tkm_per_vehicle']*1000))*100:>+12.2f}")
print("-" * 65)
print(f"{'TOTAL':<25} {icev['levelized']*100:>12.2f} {bev['levelized']*100:>12.2f} {(bev['levelized'] - icev['levelized'])*100:>+12.2f}")

# Per-km comparison
print(f"\n{'Per km (EUR/km)':<25} {'ICEV':>12} {'BEV':>12}")
print("-" * 50)
icev_per_km = icev['tco'] / (icev['tkm_per_vehicle'] * 1000 / icev['W'])
bev_per_km = bev['tco'] / (bev['tkm_per_vehicle'] * 1000 / bev['W'])
print(f"{'Total TCO':<25} {icev_per_km:>12.2f} {bev_per_km:>12.2f}")

# Literature comparison
print("\n" + "=" * 80)
print("COMPARISON WITH LITERATURE (ICCT 2023)")
print("=" * 80)

# ICCT values (2023)
icct_diesel = 1.08  # EUR/km
icct_bev_2023 = 1.14  # EUR/km (2023, before parity)

print(f"\n{'Source':<30} {'Diesel/ICEV':>15} {'BEV':>15}")
print("-" * 60)
print(f"{'ICCT 2023 (EUR/km)':<30} {icct_diesel:>15.2f} {icct_bev_2023:>15.2f}")
print(f"{'Our model with tolls (EUR/km)':<30} {icev_per_km:>15.2f} {bev_per_km:>15.2f}")
print(f"{'Difference':<30} {icev_per_km - icct_diesel:>+15.2f} {bev_per_km - icct_bev_2023:>+15.2f}")

print(f"\nNote: Our model uses 2032 parameters where BEV costs have declined")
print(f"      ICCT 2023 projects BEV parity by 2025-2026, our 2032 shows BEV advantage")

print("\n" + "=" * 80)
print("KEY FINDINGS")
print("=" * 80)
print(f"""
WITH TOLLS INCLUDED (EU Eurovignette Directive):

  BEV advantage over ICEV: {(icev['levelized'] - bev['levelized'])*100:.2f} ct/tkm

  Cost breakdown (ct/tkm):
                          ICEV      BEV     Delta
    Capital:              {icev['capital']/(icev['tkm_per_vehicle']*1000)*100:.2f}     {bev['capital']/(bev['tkm_per_vehicle']*1000)*100:.2f}    {(bev['capital']/(bev['tkm_per_vehicle']*1000) - icev['capital']/(icev['tkm_per_vehicle']*1000))*100:+.2f}
    Fuel/Energy:          {icev['fuel_cost']/(icev['tkm_per_vehicle']*1000)*100:.2f}     {bev['fuel_cost']/(bev['tkm_per_vehicle']*1000)*100:.2f}    {(bev['fuel_cost']/(bev['tkm_per_vehicle']*1000) - icev['fuel_cost']/(icev['tkm_per_vehicle']*1000))*100:+.2f}
    Maintenance:          {icev['maintenance']/(icev['tkm_per_vehicle']*1000)*100:.2f}     {bev['maintenance']/(bev['tkm_per_vehicle']*1000)*100:.2f}    {(bev['maintenance']/(bev['tkm_per_vehicle']*1000) - icev['maintenance']/(icev['tkm_per_vehicle']*1000))*100:+.2f}
    Tolls:                {icev['toll_cost']/(icev['tkm_per_vehicle']*1000)*100:.2f}     {bev['toll_cost']/(bev['tkm_per_vehicle']*1000)*100:.2f}    {(bev['toll_cost']/(bev['tkm_per_vehicle']*1000) - icev['toll_cost']/(icev['tkm_per_vehicle']*1000))*100:+.2f}
    ----------------------------------------
    TOTAL:                {icev['levelized']*100:.2f}     {bev['levelized']*100:.2f}    {(bev['levelized'] - icev['levelized'])*100:+.2f}

  Sources:
  - EU Directive 2022/362 (Eurovignette)
  - IRU toll data 2024
  - ICCT (2023): Total cost of ownership comparison
""")
