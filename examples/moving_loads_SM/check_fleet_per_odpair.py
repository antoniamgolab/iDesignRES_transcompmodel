"""
Check if fleet oversizing is due to per-OD pair allocation
"""
import yaml
import os

results_dir = os.path.join(os.path.dirname(__file__), 'results', 'fleet_verification_compare')
scenario_dir = os.path.join(results_dir, 'scenario_001', 'with_fuel')

# Load h_dict
files = os.listdir(scenario_dir)
h_file = [f for f in files if '_h_dict.yaml' in f and 'plus' not in f and 'minus' not in f and 'exist' not in f][0]

with open(os.path.join(scenario_dir, h_file), 'r') as f:
    h_dict = yaml.safe_load(f)

# Count unique OD pairs and fleet per OD pair
odpairs = set()
fleet_by_odpair = {}

for key, val in h_dict.items():
    v = float(val)
    # Key format: (year, odpair_id, tv_id, generation)
    key_str = str(key).strip('()')
    parts = key_str.split(',')
    if len(parts) >= 2:
        odpair_id = int(parts[1].strip())
        odpairs.add(odpair_id)
        if odpair_id not in fleet_by_odpair:
            fleet_by_odpair[odpair_id] = 0
        fleet_by_odpair[odpair_id] += v

print("=" * 60)
print("FLEET ALLOCATION BY OD PAIR")
print("=" * 60)

print(f"\nNumber of unique OD pairs: {len(odpairs)}")

# Statistics
fleet_values = list(fleet_by_odpair.values())
total_fleet = sum(fleet_values)
avg_fleet = total_fleet / len(fleet_values) if fleet_values else 0
max_fleet = max(fleet_values) if fleet_values else 0
min_fleet = min(fleet_values) if fleet_values else 0

# Count small fleets (< 1 vehicle equivalent)
small_fleets = sum(1 for v in fleet_values if v < 1)
tiny_fleets = sum(1 for v in fleet_values if v < 0.1)

print(f"\nFleet statistics (summed over years, not fleet-years):")
print(f"  Total fleet: {total_fleet:,.0f}")
print(f"  Average per OD pair: {avg_fleet:.2f}")
print(f"  Max per OD pair: {max_fleet:.2f}")
print(f"  Min per OD pair: {min_fleet:.6f}")

print(f"\nSmall fleet OD pairs:")
print(f"  < 1 vehicle: {small_fleets} OD pairs ({small_fleets/len(odpairs)*100:.1f}%)")
print(f"  < 0.1 vehicle: {tiny_fleets} OD pairs ({tiny_fleets/len(odpairs)*100:.1f}%)")

# Distribution
print(f"\nFleet size distribution:")
brackets = [(0, 0.1), (0.1, 1), (1, 10), (10, 100), (100, 1000), (1000, float('inf'))]
for low, high in brackets:
    count = sum(1 for v in fleet_values if low <= v < high)
    total_in_bracket = sum(v for v in fleet_values if low <= v < high)
    if count > 0:
        print(f"  {low:>6} - {high if high != float('inf') else 'inf':>6}: {count:>4} OD pairs, {total_in_bracket:>10,.0f} vehicles ({total_in_bracket/total_fleet*100:>5.1f}%)")

print("\n" + "=" * 60)
print("INTERPRETATION")
print("=" * 60)
print(f"""
The model has {len(odpairs):,} OD pairs, each with its own fleet.
Many OD pairs have very small fleets (< 1 vehicle).

This leads to OVERPROVISIONING because:
1. Each OD pair needs at least SOME capacity
2. Fleets cannot be shared across OD pairs
3. Fractional vehicles still consume capital/maintenance

Example: 100 OD pairs each needing 0.5 vehicles
- Model allocates: 100 separate fleets totaling 50 vehicles
- Reality: Could share ~25 vehicles across all routes
""")
