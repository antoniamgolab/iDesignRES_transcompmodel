"""
Test the InitialVehicleStock realignment functionality.
"""

import sys
sys.path.insert(0, '.')

from SM_preprocessing import SMParameterGenerator

# Create preprocessor with existing case folder
preprocessor = SMParameterGenerator(
    nuts3_data_dir="input_data/fixed_nuts_2",
    output_dir="input_data/test_realignment"
)

# Load the data (this will trigger realignment)
print("Loading data from fixed_nuts_2...")
preprocessor.load_nuts3_data()

# Show results
print("\n" + "=" * 80)
print("REALIGNMENT TEST COMPLETE")
print("=" * 80)

# Verify the stock is now aligned with model generations
model_params = preprocessor.generate_model_params()
y_init = model_params['y_init']
pre_y = model_params['pre_y']
time_step = model_params['time_step']
g_init = y_init - pre_y
model_generations = list(range(g_init, y_init, time_step))

print(f"\nModel parameters:")
print(f"  y_init: {y_init}")
print(f"  pre_y: {pre_y}")
print(f"  time_step: {time_step}")
print(f"  g_init: {g_init}")
print(f"  Model generations: {model_generations}")

# Check current years in stock
stock_years = sorted(set(item['year_of_purchase'] for item in preprocessor.initial_vehicle_stock))
print(f"\nStock years after realignment: {stock_years}")

# Verify all stock years are in model generations
all_aligned = all(y in model_generations for y in stock_years)
print(f"\nAll years aligned: {all_aligned}")

if all_aligned:
    print("[SUCCESS] InitialVehicleStock is now properly aligned with model generations!")
else:
    print("[ERROR] Some years are still misaligned!")
    misaligned = [y for y in stock_years if y not in model_generations]
    print(f"Misaligned years: {misaligned}")
