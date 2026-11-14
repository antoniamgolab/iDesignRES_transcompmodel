"""
Check which constraint is forcing excess fleet capacity
"""
import yaml
import os

results_dir = os.path.join(os.path.dirname(__file__), 'results', 'fleet_verification_compare')
scenario_dir = os.path.join(results_dir, 'scenario_001', 'with_fuel')

# Parameters
time_step = 4
W = 13.6
annual_range = 136750
spec_cons = 3.639

# Load all fleet-related variables
files = os.listdir(scenario_dir)

def load_and_sum_by_year(filename_pattern):
    """Load yaml and sum values by year"""
    matching = [f for f in files if filename_pattern in f]
    if not matching:
        return {}

    with open(os.path.join(scenario_dir, matching[0]), 'r') as f:
        data = yaml.safe_load(f)

    by_year = {}
    for key, val in data.items():
        v = float(val)
        year = int(str(key).split(',')[0].strip('('))
        if year not in by_year:
            by_year[year] = 0
        by_year[year] += v
    return by_year

# Load all variables
h_by_year = load_and_sum_by_year('_h_dict.yaml')
h_exist_by_year = load_and_sum_by_year('h_exist_dict')
h_plus_by_year = load_and_sum_by_year('h_plus_dict')
h_minus_by_year = load_and_sum_by_year('h_minus_dict')
f_by_year = load_and_sum_by_year('_f_dict.yaml')
s_by_year = load_and_sum_by_year('_s_dict.yaml')

print("=" * 80)
print("FLEET DYNAMICS BY YEAR")
print("=" * 80)

print(f"\n{'Year':<6} {'h (fleet)':<12} {'h_exist':<12} {'h_plus':<12} {'h_minus':<12} {'h_check':<12}")
print("-" * 70)

for year in sorted(h_by_year.keys()):
    h = h_by_year.get(year, 0)
    h_exist = h_exist_by_year.get(year, 0)
    h_plus = h_plus_by_year.get(year, 0)
    h_minus = h_minus_by_year.get(year, 0)

    # Check: h should equal h_exist - h_minus + h_plus
    h_check = h_exist - h_minus + h_plus
    diff = h - h_check

    print(f"{year:<6} {h:>10,.0f}   {h_exist:>10,.0f}   {h_plus:>10,.0f}   {h_minus:>10,.0f}   {diff:>+10,.0f}")

print("\n" + "=" * 80)
print("FLEET vs DEMAND COMPARISON")
print("=" * 80)

print(f"\n{'Year':<6} {'Fleet h':<12} {'Flow (kt)':<12} {'Energy (GWh)':<12} {'Required h':<12} {'Excess':<12}")
print("-" * 75)

for year in sorted(h_by_year.keys()):
    h = h_by_year.get(year, 0)
    f_kt = f_by_year.get(year, 0)
    s_mwh = s_by_year.get(year, 0)

    # Required h from energy: h = s / (spec_cons × annual_range)
    # s is in MWh, spec_cons in kWh/km, annual_range in km
    # h = s × 1000 / (spec_cons × annual_range)
    required_h = s_mwh * 1000 / (spec_cons * annual_range) if s_mwh > 0 else 0

    excess = h - required_h

    print(f"{year:<6} {h:>10,.0f}   {f_kt:>10,.0f}   {s_mwh/1000:>10,.0f}   {required_h:>10,.0f}   {excess:>+10,.0f}")

print("\n" + "=" * 80)
print("ANALYSIS: Where does excess come from?")
print("=" * 80)

# Check h_exist in first year - this is the initial fleet
first_year = min(h_by_year.keys())
print(f"\n1. INITIAL FLEET (year {first_year}):")
print(f"   h_exist: {h_exist_by_year.get(first_year, 0):,.0f}")
print(f"   h_plus:  {h_plus_by_year.get(first_year, 0):,.0f}")
print(f"   h:       {h_by_year.get(first_year, 0):,.0f}")

# Check if h_minus is ever > 0
total_h_minus = sum(h_minus_by_year.values())
print(f"\n2. RETIREMENTS (h_minus):")
print(f"   Total h_minus over horizon: {total_h_minus:,.0f}")
if total_h_minus > 0:
    print("   Vehicles ARE being retired")
else:
    print("   Vehicles are NOT being retired (h_minus = 0)")

# Check accumulation
print(f"\n3. FLEET ACCUMULATION:")
total_h_plus = sum(h_plus_by_year.values())
print(f"   Total purchases (h_plus): {total_h_plus:,.0f}")
print(f"   Total retirements (h_minus): {total_h_minus:,.0f}")
print(f"   Net change: {total_h_plus - total_h_minus:,.0f}")

# Expected vs actual
total_energy = sum(s_by_year.values())
expected_total_h = total_energy * 1000 / (spec_cons * annual_range)
actual_total_h = sum(h_by_year.values())
print(f"\n4. TOTAL COMPARISON:")
print(f"   Total fleet (sum of h): {actual_total_h:,.0f}")
print(f"   Required from energy:   {expected_total_h:,.0f}")
print(f"   Excess:                 {actual_total_h - expected_total_h:,.0f} ({(actual_total_h/expected_total_h - 1)*100:.0f}%)")
