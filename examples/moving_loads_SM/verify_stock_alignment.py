"""
Verify Initial Vehicle Stock Alignment with Model Generations

The preprocessing uses time_step=2, but the model uses time_step=4.
This script quantifies how much initial stock is lost due to year misalignment.
"""

import yaml
from pathlib import Path

script_dir = Path(__file__).parent
input_dir = script_dir / "input_data" / "case_20251107_214315_uni_uni"

print("=" * 80)
print("INITIAL VEHICLE STOCK ALIGNMENT ANALYSIS")
print("=" * 80)

# Load Model parameters
with open(input_dir / "Model.yaml", 'r') as f:
    model = yaml.safe_load(f)

y_init = model['y_init']  # 2020
time_step = model['time_step']  # 4
pre_y = model.get('pre_y', 12)  # 12
g_init = y_init - pre_y  # 2008

print(f"\n1. MODEL TEMPORAL RESOLUTION")
print("-" * 80)
print(f"   y_init: {y_init}")
print(f"   time_step: {time_step}")
print(f"   pre_y: {pre_y}")
print(f"   g_init: {g_init}")

# Model generations (pre-period)
model_generations = list(range(g_init, y_init, time_step))
print(f"\n   Model pre-period generations: {model_generations}")

# Load InitialVehicleStock
with open(input_dir / "InitialVehicleStock.yaml", 'r') as f:
    initial_stock = yaml.safe_load(f)

# Get unique years in InitialVehicleStock
stock_years = sorted(set(item['year_of_purchase'] for item in initial_stock))
print(f"   InitialVehicleStock years: {stock_years}")

# Calculate stock by year
stock_by_year = {}
for item in initial_stock:
    year = item['year_of_purchase']
    if year not in stock_by_year:
        stock_by_year[year] = 0
    stock_by_year[year] += item['stock']

print(f"\n2. STOCK BY YEAR")
print("-" * 80)
total_stock = 0
matched_stock = 0
unmatched_stock = 0

for year in sorted(stock_by_year.keys()):
    stock = stock_by_year[year]
    total_stock += stock
    if year in model_generations:
        status = "[OK] MATCHES model generation"
        matched_stock += stock
    else:
        status = "[X] NO MATCH - will be ignored!"
        unmatched_stock += stock
    print(f"   {year}: {stock:,.2f} vehicles - {status}")

print(f"\n3. SUMMARY")
print("-" * 80)
print(f"   Total initial stock: {total_stock:,.2f} vehicles")
print(f"   Matched (used by model): {matched_stock:,.2f} vehicles ({matched_stock/total_stock*100:.1f}%)")
print(f"   Unmatched (IGNORED): {unmatched_stock:,.2f} vehicles ({unmatched_stock/total_stock*100:.1f}%)")

print(f"\n4. ROOT CAUSE")
print("-" * 80)
print(f"""
The InitialVehicleStock was created with time_step=2:
   Years: {stock_years}

But the model uses time_step=4:
   Generations: {model_generations}

In constraint_vehicle_aging (case 2), the model looks up:
   stock_index = findfirst(ivs -> ivs.year_of_purchase == g, ...)

Since only {len([y for y in stock_years if y in model_generations])}/{len(stock_years)} years align,
{unmatched_stock/total_stock*100:.0f}% of the initial stock is set to 0!

This forces the model to purchase {unmatched_stock:,.0f} additional vehicles
to cover the demand that the "missing" initial stock should have covered.
""")

print(f"\n5. SOLUTION")
print("-" * 80)
print(f"""
Option 1: Regenerate InitialVehicleStock with time_step=4
   - Modify SM_preprocessing.py to use time_step=4 in _create_vehicle_stock()
   - Redistribute stock: years should be {model_generations}

Option 2: Aggregate misaligned years to nearest model generation
   - 2010 -> 2008 or 2012
   - 2014 -> 2012 or 2016
   - 2018 -> 2016

Option 3: Sum all pre-period stock into a single "initial fleet"
   - Conceptually simpler
   - Use g = y_init for all initial stock (but may need model changes)
""")
