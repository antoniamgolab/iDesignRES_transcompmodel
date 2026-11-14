"""
TCO / Levelized Cost Calculation for BEVs
Connecting energy consumption to total cost of ownership
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

# Load fuel costs (simplified - use average electricity price)
# From FuelCost.yaml: electricity ~0.14-0.16 EUR/kWh in later years
electricity_price = 0.15  # EUR/kWh (average)
diesel_price = 0.1845  # EUR/kWh

# Load f_dict
files = os.listdir(scenario_dir)
f_file = [f for f in files if '_f_dict.yaml' in f][0]
with open(os.path.join(scenario_dir, f_file), 'r') as f:
    f_dict = yaml.safe_load(f)

# Load h_dict (fleet size)
h_file = [f for f in files if '_h_dict.yaml' in f and 'plus' not in f and 'minus' not in f and 'exist' not in f][0]
with open(os.path.join(scenario_dir, h_file), 'r') as f:
    h_dict = yaml.safe_load(f)

print("=" * 80)
print("TCO / LEVELIZED COST CALCULATION - BEV vs ICEV")
print("=" * 80)

# Calculate for both BEV and ICEV
results = {}

for tv_id, tv_name in [(ICEV_TV_ID, 'ICEV'), (BEV_TV_ID, 'BEV')]:
    total_flow = 0  # ktonnes
    total_tkm = 0  # Mtkm
    total_energy = 0  # MWh
    total_vehicles = 0  # vehicle-years

    by_year = {}

    # Process flows
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

            total_flow += f_val
            total_tkm += tkm
            total_energy += energy

            if year not in by_year:
                by_year[year] = {'flow': 0, 'tkm': 0, 'energy': 0, 'vehicles': 0}
            by_year[year]['flow'] += f_val
            by_year[year]['tkm'] += tkm
            by_year[year]['energy'] += energy

    # Process fleet (h)
    for key, val in h_dict.items():
        h_val = float(val)
        if h_val < 0.001:
            continue

        key_str = str(key).strip('()')
        parts = key_str.split(',')
        if len(parts) >= 4:
            year = int(parts[0].strip())
            this_tv_id = int(parts[2].strip())

            if this_tv_id != tv_id:
                continue

            total_vehicles += h_val
            if year in by_year:
                by_year[year]['vehicles'] += h_val

    results[tv_name] = {
        'flow': total_flow,
        'tkm': total_tkm,
        'energy': total_energy,
        'vehicles': total_vehicles,
        'by_year': by_year
    }

# Calculate costs
print("\n" + "=" * 80)
print("COST CALCULATION")
print("=" * 80)

for tv_name in ['ICEV', 'BEV']:
    tv_id = ICEV_TV_ID if tv_name == 'ICEV' else BEV_TV_ID
    r = results[tv_name]

    # Use representative generation for costs (e.g., g=2032)
    idx_2032 = 2032 - g_init
    capital = tv_data[tv_id]['capital_cost'][idx_2032]
    maintenance = tv_data[tv_id]['maintenance_cost_annual'][0][idx_2032]  # First sub-array
    annual_range = tv_data[tv_id]['AnnualRange'][idx_2032]
    lifetime = tv_data[tv_id]['Lifetime'][idx_2032]
    spec_cons = tv_data[tv_id]['spec_cons'][idx_2032]
    W = tv_data[tv_id]['W'][idx_2032]

    fuel_price = electricity_price if tv_name == 'BEV' else diesel_price

    print(f"\n{tv_name} (using g=2032 parameters):")
    print("-" * 50)
    print(f"  Capital cost:       {capital:>12,.0f} EUR/vehicle")
    print(f"  Maintenance/year:   {maintenance:>12,.0f} EUR/vehicle/year")
    print(f"  Annual range:       {annual_range:>12,.0f} km/year")
    print(f"  Lifetime:           {lifetime:>12} years")
    print(f"  spec_cons:          {spec_cons:>12.3f} kWh/km")
    print(f"  Payload W:          {W:>12.1f} tonnes")
    print(f"  Fuel price:         {fuel_price:>12.4f} EUR/kWh")

    # TCO calculation per vehicle over lifetime
    total_km = annual_range * lifetime
    total_energy_vehicle = spec_cons * total_km  # kWh
    fuel_cost = total_energy_vehicle * fuel_price  # EUR
    total_maintenance = maintenance * lifetime

    tco_per_vehicle = capital + fuel_cost + total_maintenance

    # Lifetime tkm per vehicle
    tkm_per_vehicle = total_km * W / 1000  # Mtkm

    # Levelized cost
    levelized_cost = tco_per_vehicle / (tkm_per_vehicle * 1000)  # EUR/tkm

    print(f"\n  TCO per vehicle:")
    print(f"    Capital:          {capital:>12,.0f} EUR")
    print(f"    Fuel ({total_km/1e6:.2f}M km):   {fuel_cost:>12,.0f} EUR")
    print(f"    Maintenance:      {total_maintenance:>12,.0f} EUR")
    print(f"    TOTAL TCO:        {tco_per_vehicle:>12,.0f} EUR")

    print(f"\n  Lifetime transport: {tkm_per_vehicle:,.0f} Mtkm = {tkm_per_vehicle*1000:,.0f} ktkm")
    print(f"  Levelized cost:     {levelized_cost:.4f} EUR/tkm = {levelized_cost*100:.2f} ct/tkm")

    # Store for comparison
    results[tv_name]['tco'] = tco_per_vehicle
    results[tv_name]['levelized'] = levelized_cost
    results[tv_name]['capital'] = capital
    results[tv_name]['fuel_cost'] = fuel_cost
    results[tv_name]['maintenance'] = total_maintenance
    results[tv_name]['tkm_per_vehicle'] = tkm_per_vehicle

# Model-based verification
print("\n" + "=" * 80)
print("MODEL-BASED VERIFICATION")
print("=" * 80)

for tv_name in ['ICEV', 'BEV']:
    r = results[tv_name]
    fuel_price = electricity_price if tv_name == 'BEV' else diesel_price

    print(f"\n{tv_name} from model results:")
    print("-" * 50)
    print(f"  Total flow:         {r['flow']:>15,.0f} ktonnes")
    print(f"  Total tkm:          {r['tkm']:>15,.0f} Mtkm")
    print(f"  Total energy:       {r['energy']/1e6:>15.3f} TWh")
    print(f"  Total vehicles:     {r['vehicles']:>15,.0f} vehicle-years")

    if r['tkm'] > 0:
        # Energy cost from model
        energy_cost = r['energy'] * 1000 * fuel_price  # MWh * 1000 * EUR/kWh = EUR
        print(f"\n  Energy cost (model): {energy_cost/1e9:>12.3f} billion EUR")

        # kWh per tkm from model
        kwh_per_tkm = r['energy'] / (r['tkm'] * 1000)  # MWh / Mtkm * 1000 = kWh/tkm
        print(f"  Energy intensity:    {kwh_per_tkm:.4f} kWh/tkm")
        print(f"  Energy cost/tkm:     {kwh_per_tkm * fuel_price:.4f} EUR/tkm = {kwh_per_tkm * fuel_price * 100:.2f} ct/tkm")

print("\n" + "=" * 80)
print("COMPARISON SUMMARY")
print("=" * 80)

print(f"\n{'Metric':<30} {'ICEV':>15} {'BEV':>15} {'Delta':>15}")
print("-" * 75)

icev = results['ICEV']
bev = results['BEV']

print(f"{'Flow share':<30} {icev['flow']/512949*100:>14.1f}% {bev['flow']/512949*100:>14.1f}%")
print(f"{'Energy (TWh)':<30} {icev['energy']/1e6:>15.2f} {bev['energy']/1e6:>15.2f} {(bev['energy']-icev['energy'])/1e6:>+15.2f}")
print(f"{'Levelized cost (EUR/tkm)':<30} {icev['levelized']:>15.4f} {bev['levelized']:>15.4f} {bev['levelized']-icev['levelized']:>+15.4f}")
print(f"{'Levelized cost (ct/tkm)':<30} {icev['levelized']*100:>15.2f} {bev['levelized']*100:>15.2f} {(bev['levelized']-icev['levelized'])*100:>+15.2f}")

# Cost components per tkm
print(f"\n{'Cost component (ct/tkm)':<30} {'ICEV':>15} {'BEV':>15}")
print("-" * 60)
for name in ['ICEV', 'BEV']:
    r = results[name]
    cap_per_tkm = r['capital'] / (r['tkm_per_vehicle'] * 1000) * 100
    maint_per_tkm = r['maintenance'] / (r['tkm_per_vehicle'] * 1000) * 100
    fuel_per_tkm = r['fuel_cost'] / (r['tkm_per_vehicle'] * 1000) * 100
    if name == 'ICEV':
        print(f"{'  Capital':<30} {cap_per_tkm:>15.2f}")
        print(f"{'  Maintenance':<30} {maint_per_tkm:>15.2f}")
        print(f"{'  Fuel/Energy':<30} {fuel_per_tkm:>15.2f}")
    else:
        icev_cap = results['ICEV']['capital'] / (results['ICEV']['tkm_per_vehicle'] * 1000) * 100
        icev_maint = results['ICEV']['maintenance'] / (results['ICEV']['tkm_per_vehicle'] * 1000) * 100
        icev_fuel = results['ICEV']['fuel_cost'] / (results['ICEV']['tkm_per_vehicle'] * 1000) * 100
        print(f"{'  Capital':<30} {icev_cap:>15.2f} {cap_per_tkm:>15.2f}")
        print(f"{'  Maintenance':<30} {icev_maint:>15.2f} {maint_per_tkm:>15.2f}")
        print(f"{'  Fuel/Energy':<30} {icev_fuel:>15.2f} {fuel_per_tkm:>15.2f}")

print("\n" + "=" * 80)
print("KEY INSIGHT: Energy to TCO Connection")
print("=" * 80)
print(f"""
The energy consumption from the model directly feeds into TCO:

  Energy (s) = SUM[(spec_cons/W) * path_length * f]

For BEV:
  - Model energy: {bev['energy']/1e6:.3f} TWh = {bev['energy']*1000:.0f} GWh
  - At {electricity_price:.2f} EUR/kWh = {bev['energy']*1000*electricity_price/1e6:.1f} million EUR energy cost
  - Per tkm: {bev['energy']/(bev['tkm']*1000)*electricity_price*100:.2f} ct/tkm (energy only)

For ICEV:
  - Model energy: {icev['energy']/1e6:.3f} TWh = {icev['energy']*1000:.0f} GWh
  - At {diesel_price:.4f} EUR/kWh = {icev['energy']*1000*diesel_price/1e6:.1f} million EUR fuel cost
  - Per tkm: {icev['energy']/(icev['tkm']*1000)*diesel_price*100:.2f} ct/tkm (fuel only)
""")
