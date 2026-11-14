"""
Cost Component Breakdown Analysis for ICEV vs BEV
Analyzes the share of each cost component to explain why electricity prices have limited impact
"""
import yaml
import os

# Load scenario 000 input data
input_path = 'input_data/uncertainty_scenarios/scenario_000'
with open(f'{input_path}/TechVehicle.yaml', 'r') as f:
    tech_vehicles = yaml.safe_load(f)
with open(f'{input_path}/Model.yaml', 'r') as f:
    model_params = yaml.safe_load(f)
with open(f'{input_path}/Fuel.yaml', 'r') as f:
    fuels = yaml.safe_load(f)

# Get model parameters
y_init = model_params['y_init']
pre_y = model_params.get('pre_y', 12)
g_init = y_init - pre_y

# Get tech vehicle params
icev_tv = next(tv for tv in tech_vehicles if tv['id'] == 0)
bev_tv = next(tv for tv in tech_vehicles if tv['id'] == 1)

# Get fuel info
diesel_fuel = next(f for f in fuels if f['name'].lower() == 'diesel')
elec_fuel = next(f for f in fuels if f['name'].lower() == 'electricity')

print('=== COST COMPONENT BREAKDOWN FOR YEAR 2040 ===')
print()

year = 2040
year_idx = year - y_init
gen = 2032  # Representative generation
gen_idx = gen - g_init

# Calculate sample route (500km)
route_length = 500  # km
f_val = 1000  # tkm (1000 thousand tkm = 1 million tkm)

print(f'Sample route: {route_length} km, {f_val} thousand tkm')
print()

# =============================================
# ICEV COST COMPONENTS
# =============================================
print('=== ICEV (Diesel Truck) ===')

# Parameters
icev_spec_cons = icev_tv['spec_cons'][gen_idx]  # kWh/km
icev_W = icev_tv['W'][gen_idx]  # tonnes payload
icev_AR = icev_tv['AnnualRange'][gen_idx]  # km/year
icev_capital = icev_tv['capital_cost'][year_idx]  # EUR
maint_idx = min(year-gen, len(icev_tv['maintenance_cost_annual'][gen_idx])-1)
icev_maintenance = icev_tv['maintenance_cost_annual'][gen_idx][maint_idx]
icev_tank = icev_tv['tank_capacity'][gen_idx]

# Calculate num_vehicles
icev_num_vehicles = (route_length / (icev_W * icev_AR)) * 1000 * f_val

# Fuel cost
diesel_price = diesel_fuel['cost_per_kWh'][year_idx]  # EUR/kWh
icev_fuel_cost_route = route_length * icev_spec_cons * icev_num_vehicles * diesel_price

print(f'  spec_cons: {icev_spec_cons:.4f} kWh/km')
print(f'  W (payload): {icev_W:.2f} tonnes')
print(f'  AnnualRange: {icev_AR:.0f} km')
print(f'  capital_cost: {icev_capital:,.0f} EUR')
print(f'  maintenance_annual: {icev_maintenance:,.0f} EUR/vehicle/year')
print(f'  num_vehicles: {icev_num_vehicles:.4f}')
print(f'  diesel_price: {diesel_price:.4f} EUR/kWh')
print()

# Per 1000 tkm
icev_fuel_per_tkm = icev_fuel_cost_route / f_val
print(f'  FUEL COST PER 1000 tkm: {icev_fuel_per_tkm:.2f} EUR')

# =============================================
# BEV COST COMPONENTS
# =============================================
print()
print('=== BEV (Electric Truck) ===')

# Parameters
bev_spec_cons = bev_tv['spec_cons'][gen_idx]  # kWh/km
bev_W = bev_tv['W'][gen_idx]  # tonnes payload
bev_AR = bev_tv['AnnualRange'][gen_idx]  # km/year
bev_capital = bev_tv['capital_cost'][year_idx]  # EUR
maint_idx = min(year-gen, len(bev_tv['maintenance_cost_annual'][gen_idx])-1)
bev_maintenance = bev_tv['maintenance_cost_annual'][gen_idx][maint_idx]
bev_tank = bev_tv['tank_capacity'][gen_idx]

# Calculate num_vehicles
bev_num_vehicles = (route_length / (bev_W * bev_AR)) * 1000 * f_val

# Electricity cost
elec_price = elec_fuel['cost_per_kWh'][year_idx]  # EUR/kWh
# Add charging markup (15% in scenario 000)
charging_markup = 0.15
elec_price_with_markup = elec_price * (1 + charging_markup)

bev_fuel_cost_route = route_length * bev_spec_cons * bev_num_vehicles * elec_price_with_markup

print(f'  spec_cons: {bev_spec_cons:.4f} kWh/km')
print(f'  W (payload): {bev_W:.2f} tonnes')
print(f'  AnnualRange: {bev_AR:.0f} km')
print(f'  capital_cost: {bev_capital:,.0f} EUR')
print(f'  maintenance_annual: {bev_maintenance:,.0f} EUR/vehicle/year')
print(f'  num_vehicles: {bev_num_vehicles:.4f}')
print(f'  elec_price (base): {elec_price:.4f} EUR/kWh')
print(f'  elec_price (+15% markup): {elec_price_with_markup:.4f} EUR/kWh')
print()

# Per 1000 tkm
bev_fuel_per_tkm = bev_fuel_cost_route / f_val
print(f'  FUEL COST PER 1000 tkm: {bev_fuel_per_tkm:.2f} EUR')

# =============================================
# COMPARISON
# =============================================
print()
print('=== FUEL COST COMPARISON ===')
print(f'  ICEV fuel cost per 1000 tkm: {icev_fuel_per_tkm:.2f} EUR')
print(f'  BEV fuel cost per 1000 tkm:  {bev_fuel_per_tkm:.2f} EUR')
if icev_fuel_per_tkm > 0:
    print(f'  BEV advantage:               {icev_fuel_per_tkm - bev_fuel_per_tkm:.2f} EUR/1000tkm ({100*(icev_fuel_per_tkm - bev_fuel_per_tkm)/icev_fuel_per_tkm:.1f}% savings)')
print()

# =============================================
# ANNUAL COST COMPARISON (including capital and maintenance)
# =============================================
print('=== ANNUAL COST COMPARISON (per vehicle-year) ===')

# Assuming vehicle drives full AnnualRange per year
icev_annual_fuel = icev_AR * icev_spec_cons * diesel_price
bev_annual_fuel = bev_AR * bev_spec_cons * elec_price_with_markup

# Capital amortized over lifetime (assume 12 years)
lifetime = 12
icev_annual_capital = icev_capital / lifetime
bev_annual_capital = bev_capital / lifetime

print()
print('ICEV per vehicle per year:')
icev_total_annual = icev_annual_fuel + icev_maintenance + icev_annual_capital
print(f'  Fuel:        {icev_annual_fuel:>12,.0f} EUR ({100*icev_annual_fuel/icev_total_annual:>5.1f}%)')
print(f'  Maintenance: {icev_maintenance:>12,.0f} EUR ({100*icev_maintenance/icev_total_annual:>5.1f}%)')
print(f'  Capital:     {icev_annual_capital:>12,.0f} EUR ({100*icev_annual_capital/icev_total_annual:>5.1f}%)')
print(f'  TOTAL:       {icev_total_annual:>12,.0f} EUR')

print()
print('BEV per vehicle per year:')
bev_total_annual = bev_annual_fuel + bev_maintenance + bev_annual_capital
print(f'  Fuel:        {bev_annual_fuel:>12,.0f} EUR ({100*bev_annual_fuel/bev_total_annual:>5.1f}%)')
print(f'  Maintenance: {bev_maintenance:>12,.0f} EUR ({100*bev_maintenance/bev_total_annual:>5.1f}%)')
print(f'  Capital:     {bev_annual_capital:>12,.0f} EUR ({100*bev_annual_capital/bev_total_annual:>5.1f}%)')
print(f'  TOTAL:       {bev_total_annual:>12,.0f} EUR')

print()
print('=== SUMMARY ===')
print(f'BEV vs ICEV total annual cost: {bev_total_annual - icev_total_annual:+,.0f} EUR ({100*(bev_total_annual/icev_total_annual - 1):+.1f}%)')
print()
print('Cost component shares (total annual):')
print(f'           ICEV%     BEV%')
print(f'  Fuel:    {100*icev_annual_fuel/icev_total_annual:>5.1f}%   {100*bev_annual_fuel/bev_total_annual:>5.1f}%')
print(f'  Maint:   {100*icev_maintenance/icev_total_annual:>5.1f}%   {100*bev_maintenance/bev_total_annual:>5.1f}%')
print(f'  Capital: {100*icev_annual_capital/icev_total_annual:>5.1f}%   {100*bev_annual_capital/bev_total_annual:>5.1f}%')

print()
print('=== WHY FUEL COST HAS LIMITED IMPACT ===')
print()
print(f'For ICEV: fuel costs are {100*icev_annual_fuel/icev_total_annual:.1f}% of total annual costs')
print(f'For BEV: fuel costs are {100*bev_annual_fuel/bev_total_annual:.1f}% of total annual costs')
print()
print(f'Capital costs dominate:')
print(f'  - ICEV capital: {100*icev_annual_capital/icev_total_annual:.1f}% of total')
print(f'  - BEV capital:  {100*bev_annual_capital/bev_total_annual:.1f}% of total')
print()
print('The tech_cost_multiplier affects capital costs (the dominant component),')
print('while electricity price only affects fuel costs (a smaller share).')
print()
print('This explains why tech_cost (0.7x vs 1.0x vs 1.3x) has a much larger')
print('impact on BEV adoption than electricity price variations.')
