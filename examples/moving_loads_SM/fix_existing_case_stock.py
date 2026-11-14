"""
Fix existing case InitialVehicleStock to align with model generations.

This script modifies the InitialVehicleStock.yaml in an existing case folder
to align year_of_purchase values with the model's generation grid.
"""

import yaml
from pathlib import Path

# Configuration
script_dir = Path(__file__).parent
case_folder = "case_20251107_214315_uni_uni"
input_dir = script_dir / "input_data" / case_folder

print("=" * 80)
print("FIX EXISTING CASE: InitialVehicleStock Realignment")
print("=" * 80)
print(f"Case folder: {case_folder}")

# Load Model parameters
with open(input_dir / "Model.yaml", 'r') as f:
    model = yaml.safe_load(f)

y_init = model['y_init']
pre_y = model.get('pre_y', 12)
time_step = model['time_step']
g_init = y_init - pre_y

model_generations = list(range(g_init, y_init, time_step))
print(f"\nModel parameters:")
print(f"  y_init: {y_init}")
print(f"  pre_y: {pre_y}")
print(f"  time_step: {time_step}")
print(f"  g_init: {g_init}")
print(f"  Model generations: {model_generations}")

# Load InitialVehicleStock
stock_file = input_dir / "InitialVehicleStock.yaml"
with open(stock_file, 'r') as f:
    initial_stock = yaml.safe_load(f)

print(f"\nLoaded {len(initial_stock)} stock entries")

# Get source years
source_years = sorted(set(item['year_of_purchase'] for item in initial_stock))
print(f"Source years: {source_years}")

# Check if realignment needed
misaligned_years = [y for y in source_years if y not in model_generations]
if not misaligned_years:
    print("\n[OK] Stock already aligned with model generations. No changes needed.")
    exit(0)

print(f"Misaligned years: {misaligned_years}")

# Map each source year to nearest model generation
def find_nearest_generation(year):
    if year in model_generations:
        return year
    return min(model_generations, key=lambda g: abs(g - year))

year_to_generation = {y: find_nearest_generation(y) for y in source_years}
print(f"Mapping: {year_to_generation}")

# Count stock before
total_before = sum(e['stock'] for e in initial_stock)
stock_by_year_before = {}
for item in initial_stock:
    year = item['year_of_purchase']
    stock_by_year_before[year] = stock_by_year_before.get(year, 0) + item['stock']

print(f"\nStock by year BEFORE:")
for year in sorted(stock_by_year_before.keys()):
    print(f"  {year}: {stock_by_year_before[year]:,.2f} vehicles")
print(f"  TOTAL: {total_before:,.2f} vehicles")

# Apply realignment
for entry in initial_stock:
    source_year = entry['year_of_purchase']
    target_gen = year_to_generation[source_year]
    entry['year_of_purchase'] = target_gen

# Count stock after
total_after = sum(e['stock'] for e in initial_stock)
stock_by_year_after = {}
for item in initial_stock:
    year = item['year_of_purchase']
    stock_by_year_after[year] = stock_by_year_after.get(year, 0) + item['stock']

print(f"\nStock by year AFTER:")
for year in sorted(stock_by_year_after.keys()):
    print(f"  {year}: {stock_by_year_after[year]:,.2f} vehicles")
print(f"  TOTAL: {total_after:,.2f} vehicles")

# Verify no stock lost
assert abs(total_before - total_after) < 0.01, f"Stock mismatch: {total_before} -> {total_after}"

# Backup original file
backup_file = input_dir / "InitialVehicleStock.yaml.backup"
import shutil
shutil.copy(stock_file, backup_file)
print(f"\nBackup saved to: {backup_file.name}")

# Save updated file
with open(stock_file, 'w') as f:
    yaml.dump(initial_stock, f, default_flow_style=False)

print(f"Updated file saved: {stock_file.name}")

print("\n" + "=" * 80)
print("[SUCCESS] InitialVehicleStock.yaml has been realigned!")
print("          You can now run SM_core_model.jl with correct initial stock.")
print("=" * 80)
