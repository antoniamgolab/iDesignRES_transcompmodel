"""
Compare Vehicle Stock Formulas: Preprocessing vs Model

Identifies the discrepancy between initial vehicle stock calculation
in SM_preprocessing.py and constraint_vehicle_sizing in the model.
"""

import yaml
from pathlib import Path

script_dir = Path(__file__).parent
input_dir = script_dir / "input_data" / "case_20251107_214315_uni_uni"

print("=" * 80)
print("VEHICLE STOCK FORMULA COMPARISON")
print("=" * 80)

# =============================================================================
# PREPROCESSING FORMULA (SM_preprocessing_nuts2_complete.py line 926)
# =============================================================================
print("\n1. PREPROCESSING FORMULA")
print("-" * 80)
print("""
From SM_preprocessing_nuts2_complete.py line 926:

    nb_vehicles = traffic_flow * (distance / (13.6 * (1-0.25) * 136750))

Where:
    traffic_flow = F[0] (demand in tonnes for year y_init)
    distance = path length in km
    13.6 = gross vehicle capacity (tonnes)
    (1-0.25) = 0.75 = load factor (accounts for empty return trips)
    136750 = annual range (km/year/vehicle)

Effective capacity: 13.6 * 0.75 = 10.2 tonnes

Simplified formula:
    nb_vehicles = traffic_flow * distance / (10.2 * 136750)
    nb_vehicles = traffic_flow * distance / 1,394,850
""")

# Calculate preprocessing constant
PREP_CAPACITY = 13.6 * 0.75  # = 10.2
PREP_ANNUAL_RANGE = 136750
PREP_DENOMINATOR = PREP_CAPACITY * PREP_ANNUAL_RANGE

print(f"Preprocessing denominator: {PREP_CAPACITY} * {PREP_ANNUAL_RANGE} = {PREP_DENOMINATOR:,.0f}")

# =============================================================================
# MODEL FORMULA (constraint_vehicle_sizing in model_functions.jl)
# =============================================================================
print("\n2. MODEL FORMULA (constraint_vehicle_sizing)")
print("-" * 80)
print("""
From model_functions.jl line 414-426:

    h[y,r,tv,g] >= sum(
        (k.length / (W[g] * AnnualRange[g])) * 1000 * f[y,...]
        for k in r.paths
    )

Where:
    h = vehicle stock (number of vehicles)
    k.length = path length in km
    W[g] = vehicle capacity (tonnes) for generation g
    AnnualRange[g] = annual range (km/year/vehicle) for generation g
    f = flow variable in 1000 tonnes
    1000 = conversion factor (f is in 1000 tonnes)

Simplified formula:
    vehicles_needed = demand_tonnes * path_length / (W * AnnualRange)
""")

# Load TechVehicle parameters
with open(input_dir / "TechVehicle.yaml", 'r') as f:
    techvehicles = yaml.safe_load(f)

# Get model parameters for ICEV (id=0)
icev = techvehicles[0]
MODEL_W = icev['W'][12]  # Index 12 = year 2020 (g_init=2008, so 2020-2008=12)
MODEL_ANNUAL_RANGE = icev['AnnualRange'][12]
MODEL_DENOMINATOR = MODEL_W * MODEL_ANNUAL_RANGE

print(f"Model parameters (ICEV, year 2020):")
print(f"    W (capacity): {MODEL_W} tonnes")
print(f"    AnnualRange: {MODEL_ANNUAL_RANGE:,.0f} km/year")
print(f"    Denominator: {MODEL_W} * {MODEL_ANNUAL_RANGE} = {MODEL_DENOMINATOR:,.0f}")

# =============================================================================
# COMPARISON
# =============================================================================
print("\n3. FORMULA COMPARISON")
print("-" * 80)
print(f"    Preprocessing denominator: {PREP_DENOMINATOR:,.0f}")
print(f"    Model denominator:         {MODEL_DENOMINATOR:,.0f}")
print(f"    Ratio: {PREP_DENOMINATOR / MODEL_DENOMINATOR:.4f}")

if abs(PREP_DENOMINATOR - MODEL_DENOMINATOR) < 1:
    print("\n    [MATCH] The formulas use identical denominators!")
else:
    print(f"\n    [MISMATCH] Difference: {PREP_DENOMINATOR - MODEL_DENOMINATOR:,.0f}")

# =============================================================================
# STOCK DISTRIBUTION ACROSS GENERATIONS
# =============================================================================
print("\n4. STOCK DISTRIBUTION ACROSS GENERATIONS")
print("-" * 80)

# Load Model parameters
with open(input_dir / "Model.yaml", 'r') as f:
    model_params = yaml.safe_load(f)

y_init = model_params['y_init']
time_step = model_params['time_step']
pre_y = model_params.get('pre_y', 12)

print(f"Model parameters:")
print(f"    y_init: {y_init}")
print(f"    time_step: {time_step}")
print(f"    pre_y: {pre_y}")

# Preprocessing uses these defaults (from _create_vehicle_stock):
PREP_Y_INIT = 2020
PREP_PREY_Y = 10
PREP_TIME_STEP = 2  # Default in preprocessing

prep_modeled_years = list(range(PREP_Y_INIT - PREP_PREY_Y, PREP_Y_INIT, PREP_TIME_STEP))
print(f"\nPreprocessing defaults:")
print(f"    y_init: {PREP_Y_INIT}")
print(f"    prey_y: {PREP_PREY_Y}")
print(f"    time_step: {PREP_TIME_STEP}")
print(f"    Pre-period years: {prep_modeled_years}")
print(f"    Number of years: {len(prep_modeled_years)}")

# What the model actually uses
model_g_init = y_init - pre_y
model_modeled_gens = list(range(model_g_init, y_init, time_step))
print(f"\nModel actual settings:")
print(f"    g_init: {model_g_init}")
print(f"    Pre-period generations: {model_modeled_gens}")
print(f"    Number of generations: {len(model_modeled_gens)}")

# =============================================================================
# THE KEY ISSUE
# =============================================================================
print("\n5. IDENTIFIED DISCREPANCY")
print("-" * 80)
print("""
The preprocessing _create_vehicle_stock function:
1. Calculates total nb_vehicles for the OD-pair
2. Divides by len(modeled_years) to distribute across pre-period years

PROBLEM: The preprocessing may use different time_step than the model!

Preprocessing default: time_step = 2 (implicit from original code)
Model actual: time_step = 4 (from Model.yaml)
""")

# Check what time_step preprocessing actually used
print("\n6. CHECKING ACTUAL PREPROCESSING TIME_STEP")
print("-" * 80)

# Load InitialVehicleStock to see what years were created
with open(input_dir / "InitialVehicleStock.yaml", 'r') as f:
    initial_stock = yaml.safe_load(f)

years_in_stock = sorted(set(item['year_of_purchase'] for item in initial_stock))
print(f"Years in InitialVehicleStock: {years_in_stock}")

# Infer time_step from the data
if len(years_in_stock) >= 2:
    inferred_time_step = years_in_stock[1] - years_in_stock[0]
    print(f"Inferred time_step from data: {inferred_time_step}")

# Check if stock was created with time_step=2 but model uses time_step=4
print("\n7. ROOT CAUSE ANALYSIS")
print("-" * 80)

# The key insight: preprocessing divides nb_vehicles by number of years
# If preprocessing used time_step=2: 5 years in pre-period
# If model uses time_step=4: 3 generations (2008, 2012, 2016) active in 2020

print("""
CRITICAL FINDING:

The preprocessing calculates:
    nb_vehicles = demand * distance / (W * AnnualRange)

Then distributes it across pre-period years:
    stock_per_year = nb_vehicles / len(modeled_years)

For model to have enough vehicles, we need:
    sum(stock_per_year for all years) = nb_vehicles

This should work IF:
1. All pre-period years are included in the model
2. Vehicles from all years are still active (not retired)
3. The time_step matches between preprocessing and model
""")

# Calculate actual total stock
total_initial_stock = sum(item['stock'] for item in initial_stock)
print(f"\nActual total initial stock: {total_initial_stock:,.2f} vehicles")

# Load Odpairs and calculate expected total
with open(input_dir / "Odpair.yaml", 'r') as f:
    odpairs = yaml.safe_load(f)

with open(input_dir / "Path.yaml", 'r') as f:
    paths = yaml.safe_load(f)

path_by_id = {p['id']: p for p in paths}

expected_total = 0
for odp in odpairs:
    path_id = odp.get('path_id', odp['id'])
    path = path_by_id.get(path_id, {})
    distance = path.get('length', 0)
    demand = odp.get('F', [0])[0]  # Year y_init demand

    if demand > 0 and distance > 0:
        expected_vehicles = demand * distance / MODEL_DENOMINATOR
        expected_total += expected_vehicles

print(f"Expected total (model formula): {expected_total:,.2f} vehicles")
print(f"Ratio: {total_initial_stock / expected_total:.4f}")

print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)

ratio = total_initial_stock / expected_total
if ratio < 0.6:
    print(f"""
The initial vehicle stock is only {ratio*100:.1f}% of what the model requires.

POSSIBLE CAUSES:
1. time_step mismatch between preprocessing and model
2. Vehicle lifetime issues (vehicles retired before y_init)
3. Preprocessing uses different formula parameters

SOLUTION:
Scale the initial vehicle stock by {1/ratio:.2f}x to match model requirements.
""")
else:
    print(f"Initial stock appears adequate ({ratio*100:.1f}% of requirement)")
