"""
Analyze Initial Vehicle Stock vs Transport Demand

Investigates whether the initial vehicle stock is sufficient to cover the demand.
"""

import yaml
from pathlib import Path

# Set up paths
script_dir = Path(__file__).parent
input_dir = script_dir / "input_data" / "case_20251107_214315_uni_uni"

print("=" * 80)
print("INITIAL VEHICLE STOCK vs TRANSPORT DEMAND ANALYSIS")
print("=" * 80)

# Load Model parameters first
print("\n1. Loading Model parameters...")
with open(input_dir / "Model.yaml", 'r') as f:
    model_params = yaml.safe_load(f)

y_init = model_params['y_init']
time_step = model_params['time_step']
Y = model_params['Y']
pre_y = model_params.get('pre_y', 12)
print(f"   y_init: {y_init}")
print(f"   time_step: {time_step} years")
print(f"   Y (total years): {Y}")

# Calculate model years array
g_init = y_init - pre_y
modeled_years = [y_init + i * time_step for i in range((Y - pre_y) // time_step + 1)]
print(f"   Modeled years: {modeled_years}")

# Load InitialVehicleStock
print("\n2. Loading Initial Vehicle Stock...")
with open(input_dir / "InitialVehicleStock.yaml", 'r') as f:
    initial_stock = yaml.safe_load(f)

# Calculate total initial stock
stock_by_tech = {}
stock_by_id = {}
total_stock = 0
for item in initial_stock:
    tv = item['techvehicle']
    stock = item['stock']
    stock_id = item['id']
    total_stock += stock
    stock_by_id[stock_id] = item
    if tv not in stock_by_tech:
        stock_by_tech[tv] = 0
    stock_by_tech[tv] += stock

print(f"   Total initial vehicle stock: {total_stock:,.2f} vehicles")
print(f"   By technology:")
for tv, stock in sorted(stock_by_tech.items()):
    tech_name = "ICEV" if tv == 0 else "BEV"
    print(f"      {tech_name} (id={tv}): {stock:,.2f} vehicles")

# Load TechVehicles
print("\n3. Loading TechVehicles...")
with open(input_dir / "TechVehicle.yaml", 'r') as f:
    techvehicles = yaml.safe_load(f)

# Capacity is a list by year, get initial year value (index 0 = g_init = 2008)
# y_init = 2020, g_init = 2008, so index for y_init = (2020 - 2008) = 12
y_init_idx = y_init - g_init
print(f"   Index for y_init ({y_init}): {y_init_idx}")

tv_capacity = {}
for tv in techvehicles:
    tech_name = "ICEV" if tv['technology'] == 0 else "BEV"
    w_list = tv.get('W', [25])
    capacity = w_list[y_init_idx] if isinstance(w_list, list) and len(w_list) > y_init_idx else w_list[0] if isinstance(w_list, list) else w_list
    tv_capacity[tv['id']] = capacity
    print(f"      ID {tv['id']} ({tech_name}): {capacity:.2f} tonnes capacity")

# Load Odpairs to understand demand
print("\n4. Loading OD Pairs (demand)...")
with open(input_dir / "Odpair.yaml", 'r') as f:
    odpairs = yaml.safe_load(f)

# F is demand in tonnes for each year (list indexed by year from y_init)
# Index 0 = year 2020 (y_init)
total_demand_y_init = 0
num_odpairs_with_demand = 0
for odp in odpairs:
    f_list = odp.get('F', [])
    if f_list and len(f_list) > 0:
        demand_y_init = f_list[0]  # Index 0 = first modeled year = y_init
        total_demand_y_init += demand_y_init
        if demand_y_init > 0:
            num_odpairs_with_demand += 1

print(f"   Total OD pairs: {len(odpairs)}")
print(f"   OD pairs with demand in {y_init}: {num_odpairs_with_demand}")
print(f"   Total demand in {y_init}: {total_demand_y_init:,.0f} tonnes")

# Load Paths for distance
print("\n5. Loading Paths...")
with open(input_dir / "Path.yaml", 'r') as f:
    paths = yaml.safe_load(f)

path_by_id = {}
for path in paths:
    path_by_id[path['id']] = path

# Estimate average distance
total_distance = 0
num_paths = 0
for path in paths:
    if 'length' in path:
        total_distance += path['length']
        num_paths += 1

avg_distance = total_distance / num_paths if num_paths > 0 else 500
print(f"   Number of paths: {len(paths)}")
print(f"   Average path length: {avg_distance:,.0f} km")

# Calculate vehicle requirements
print("\n6. Calculating Vehicle Requirements...")
print("=" * 80)

# The model uses constraint_vehicle_sizing which calculates:
# h[y,r,tv,g] >= sum(f over all paths and products) / (W * num_vehicle_trips_per_year)
#
# Where num_vehicle_trips_per_year = (annual_driving_hours / trip_duration)
# trip_duration = path_length_km / speed_kmh

# From EU regulations and typical trucking:
ANNUAL_DRIVING_HOURS = 2250  # ~9h/day * 250 days
AVG_SPEED_KMH = 60  # km/h for trucks

# For each OD pair, calculate required vehicles
total_vehicles_needed = 0
vehicle_needs_by_odpair = {}

for odp in odpairs:
    path_id = odp.get('path_id', odp['id'])
    path = path_by_id.get(path_id, {})
    path_length = path.get('length', avg_distance)

    # F is demand in tonnes (not 1000 tonnes) for this OD pair
    f_list = odp.get('F', [])
    demand_tonnes = f_list[0] if f_list else 0  # Year y_init

    if demand_tonnes <= 0:
        continue

    # Round trip duration in hours
    round_trip_hours = (path_length * 2) / AVG_SPEED_KMH

    # Trips per year per vehicle
    trips_per_year = ANNUAL_DRIVING_HOURS / round_trip_hours if round_trip_hours > 0 else 100

    # Capacity per vehicle per year (using ICEV capacity as baseline)
    icev_capacity = tv_capacity.get(0, 10.2)
    tonnes_per_vehicle_per_year = icev_capacity * trips_per_year

    # Vehicles needed for this OD pair
    vehicles_needed = demand_tonnes / tonnes_per_vehicle_per_year

    vehicle_needs_by_odpair[odp['id']] = {
        'demand': demand_tonnes,
        'path_length': path_length,
        'trips_per_year': trips_per_year,
        'vehicles_needed': vehicles_needed
    }

    total_vehicles_needed += vehicles_needed

print(f"   Parameters used:")
print(f"      Annual driving hours per vehicle: {ANNUAL_DRIVING_HOURS}")
print(f"      Average speed: {AVG_SPEED_KMH} km/h")
print(f"      ICEV capacity: {tv_capacity.get(0, 10.2):.1f} tonnes")
print()

# Show top OD pairs by vehicle requirement
sorted_odpairs = sorted(vehicle_needs_by_odpair.items(), key=lambda x: x[1]['vehicles_needed'], reverse=True)
print(f"   Top 10 OD pairs by vehicle requirement:")
for i, (odp_id, info) in enumerate(sorted_odpairs[:10]):
    print(f"      {i+1}. OD pair {odp_id}: {info['vehicles_needed']:,.1f} vehicles "
          f"(demand: {info['demand']:,.0f}t, path: {info['path_length']:,.0f}km)")

print()
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"   Total demand in {y_init}: {total_demand_y_init:,.0f} tonnes")
print(f"   Total vehicles needed: {total_vehicles_needed:,.0f}")
print(f"   Initial vehicle stock: {total_stock:,.0f}")
print(f"   Gap: {total_vehicles_needed - total_stock:,.0f} vehicles")
print()

if total_vehicles_needed > total_stock:
    gap_pct = (total_vehicles_needed - total_stock) / total_vehicles_needed * 100
    stock_pct = total_stock / total_vehicles_needed * 100
    print(f"   *** CRITICAL: INSUFFICIENT INITIAL STOCK ***")
    print(f"   Initial stock covers only {stock_pct:.1f}% of requirement")
    print(f"   Model must purchase {total_vehicles_needed - total_stock:,.0f} new vehicles in year {y_init}")
    print()
    print("   IMPLICATION:")
    print("   Without constraint_flow_shift, the model can choose BEV for ALL new purchases,")
    print("   explaining the sudden jump to BEV transport while ICEVs sit unused.")
else:
    print("   Initial stock appears sufficient")

print()
print("=" * 80)
print("RECOMMENDATIONS")
print("=" * 80)
print("""
1. INCREASE INITIAL VEHICLE STOCK
   - The initial stock should match the fleet needed for year 2020 demand
   - Current: ~4,832 vehicles
   - Required: ~{:,.0f} vehicles

2. OR: MODIFY HOW INITIAL STOCK IS USED
   - Currently, initial stock is distributed across OD pairs but may not match
     the actual demand pattern
   - Consider setting initial stock proportional to demand per OD pair

3. OR: ADD TECHNOLOGY SHARE CONSTRAINT FOR INITIAL YEAR
   - Force the model to use existing ICEV fleet first before buying BEVs
   - This is what constraint_flow_shift tries to do, but needs correct parameters
""".format(total_vehicles_needed))

# Check initial stock distribution per OD pair
print("\n7. Checking Initial Stock Distribution per OD Pair...")
print("=" * 80)

# Each odpair has vehicle_stock_init which references InitialVehicleStock IDs
odpairs_with_stock = 0
total_stock_via_odpairs = 0

for odp in odpairs[:10]:  # Sample first 10
    stock_ids = odp.get('vehicle_stock_init', [])
    odpair_stock = sum(stock_by_id.get(sid, {}).get('stock', 0) for sid in stock_ids)

    demand_y_init = odp.get('F', [0])[0]
    path_id = odp.get('path_id', odp['id'])
    path = path_by_id.get(path_id, {})
    path_length = path.get('length', avg_distance)

    # Calculate vehicles needed
    round_trip_hours = (path_length * 2) / AVG_SPEED_KMH
    trips_per_year = ANNUAL_DRIVING_HOURS / round_trip_hours if round_trip_hours > 0 else 100
    vehicles_needed = demand_y_init / (tv_capacity.get(0, 10.2) * trips_per_year)

    if odpair_stock > 0:
        odpairs_with_stock += 1
        total_stock_via_odpairs += odpair_stock

    print(f"   OD pair {odp['id']}: stock={odpair_stock:.1f}, needed={vehicles_needed:.1f}, "
          f"gap={vehicles_needed - odpair_stock:.1f}")

print(f"\n   Total stock via OD pairs (sample): {total_stock_via_odpairs:.1f}")
print(f"   OD pairs with stock (in sample): {odpairs_with_stock}/{10}")
