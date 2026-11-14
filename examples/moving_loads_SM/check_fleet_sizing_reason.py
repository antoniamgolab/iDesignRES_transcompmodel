"""
Check why fleet is larger than demand requires
"""
import yaml
import os

results_dir = os.path.join(os.path.dirname(__file__), 'results', 'fleet_verification_compare')
scenario_dir = os.path.join(results_dir, 'scenario_001', 'with_fuel')

# Parameters
W = 13.6  # tonnes
annual_range = 136750  # km/year
time_step = 4

# Load data
files = os.listdir(scenario_dir)
h_file = [f for f in files if '_h_dict.yaml' in f and 'plus' not in f and 'minus' not in f and 'exist' not in f][0]
f_file = [f for f in files if '_f_dict.yaml' in f][0]

# Parse h by year
with open(os.path.join(scenario_dir, h_file), 'r') as f:
    h_dict = yaml.safe_load(f)

fleet_by_year = {}
for key, val in h_dict.items():
    v = float(val)
    key_str = str(key).strip('()')
    parts = key_str.split(',')
    year = int(parts[0].strip())
    if year not in fleet_by_year:
        fleet_by_year[year] = 0
    fleet_by_year[year] += v

# Parse f by year (need to estimate path length from constraint)
with open(os.path.join(scenario_dir, f_file), 'r') as f:
    f_dict = yaml.safe_load(f)

flow_by_year = {}
for key, val in f_dict.items():
    v = float(val)
    # Extract year from key
    key_str = str(key)
    year = int(key_str.split(',')[0].strip('('))
    if year not in flow_by_year:
        flow_by_year[year] = 0
    flow_by_year[year] += v  # in ktonnes

print("=" * 70)
print("FLEET VS DEMAND BY YEAR")
print("=" * 70)

print(f"\n{'Year':<8} {'Fleet':<12} {'Flow (Mt)':<12} {'Required h':<12} {'Utilization':<12}")
print("-" * 60)

# Assume average path = 141 km (from earlier calculation)
avg_path = 141

for year in sorted(fleet_by_year.keys()):
    fleet = fleet_by_year[year]
    flow_kt = flow_by_year.get(year, 0)
    flow_t = flow_kt * 1000  # tonnes

    # Required fleet = (flow * path) / (W * annual_range)
    tkm = flow_t * avg_path
    required_h = tkm / (W * annual_range)

    # Utilization = required / actual
    utilization = required_h / fleet * 100 if fleet > 0 else 0

    print(f"{year:<8} {fleet:>10,.0f}   {flow_t/1e6:>10.2f}   {required_h:>10,.0f}   {utilization:>10.1f}%")

print("\n" + "=" * 70)
print("ANALYSIS: Why is utilization so low?")
print("=" * 70)

# Check fleet sizing constraint
print(f"""
The constraint says:
  h >= (path_length / (W x AnnualRange)) x 1000 x f

With path={avg_path} km, W={W}t, AnnualRange={annual_range} km:
  h >= {avg_path / (W * annual_range) * 1000:.6f} x f

For flow f=1000 ktonnes:
  h >= {avg_path / (W * annual_range) * 1000 * 1000:.1f} vehicles

But actual fleet is much higher. Possible reasons:
1. Path lengths vary - some routes are MUCH longer than 141 km average
2. Fleet must handle PEAK demand, not average
3. Vehicle aging/stock shift constraints prevent fast downsizing
4. Initial fleet (year 2020) is locked in from historical data
""")

# Check path length distribution needed to explain the fleet
print("\n" + "=" * 70)
print("REVERSE CALCULATION: What path length explains the fleet?")
print("=" * 70)

for year in [2020, 2040, 2056]:
    if year in fleet_by_year and year in flow_by_year:
        fleet = fleet_by_year[year]
        flow_t = flow_by_year[year] * 1000

        # If h = (path * flow) / (W * annual_range)
        # Then path = h * W * annual_range / flow
        implied_path = fleet * W * annual_range / flow_t if flow_t > 0 else 0

        print(f"Year {year}:")
        print(f"  Fleet: {fleet:,.0f}, Flow: {flow_t/1e6:.2f} Mt")
        print(f"  Implied average path: {implied_path:,.0f} km")
