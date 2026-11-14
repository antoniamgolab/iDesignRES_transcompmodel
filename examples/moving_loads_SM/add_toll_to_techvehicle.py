"""
Add toll_per_km to existing TechVehicle.yaml files
"""
import yaml
import os

# Toll rates from EU Eurovignette Directive 2022/362
TOLL_ICEV = 0.10   # EUR/km for Euro VI diesel
TOLL_BEV = 0.036   # EUR/km for ZEV (64% reduction)

# Years for toll array (same as capital_cost: 41 values for 2020-2060)
NUM_YEARS = 41

def add_tolls_to_techvehicle(input_dir):
    """Add toll_per_km to TechVehicle.yaml if not present."""
    tv_path = os.path.join(input_dir, 'TechVehicle.yaml')

    if not os.path.exists(tv_path):
        print(f"  TechVehicle.yaml not found in {input_dir}")
        return False

    with open(tv_path, 'r') as f:
        tech_vehicles = yaml.safe_load(f)

    modified = False
    for tv in tech_vehicles:
        if 'toll_per_km' not in tv:
            tv_id = tv.get('id', tv.get('name', 'unknown'))
            tv_name = tv.get('name', 'unknown')

            # Determine toll rate based on technology
            if tv_name.upper() == 'ICEV' or tv.get('technology') == 0:
                toll_rate = TOLL_ICEV
            elif tv_name.upper() == 'BEV' or tv.get('technology') == 1:
                toll_rate = TOLL_BEV
            else:
                toll_rate = TOLL_ICEV  # Default to ICEV rate

            tv['toll_per_km'] = [toll_rate] * NUM_YEARS
            print(f"  Added toll_per_km = {toll_rate} EUR/km to {tv_name} (id={tv_id})")
            modified = True
        else:
            print(f"  toll_per_km already exists for {tv.get('name', 'unknown')}")

    if modified:
        with open(tv_path, 'w') as f:
            yaml.dump(tech_vehicles, f, default_flow_style=False, allow_unicode=True)
        print(f"  Updated {tv_path}")

    return modified

# Find all scenario directories
base_dir = os.path.join(os.path.dirname(__file__), 'input_data', 'uncertainty_scenarios')

print("=" * 70)
print("ADDING TOLL_PER_KM TO TECHVEHICLE.YAML FILES")
print("=" * 70)
print(f"\nToll rates (EU Eurovignette Directive 2022/362):")
print(f"  ICEV: {TOLL_ICEV} EUR/km")
print(f"  BEV:  {TOLL_BEV} EUR/km")
print()

if os.path.isdir(base_dir):
    scenarios = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]

    for scenario in sorted(scenarios):
        scenario_dir = os.path.join(base_dir, scenario)
        print(f"\nProcessing {scenario}:")
        add_tolls_to_techvehicle(scenario_dir)
else:
    print(f"Directory not found: {base_dir}")

print("\n" + "=" * 70)
print("DONE")
print("=" * 70)
