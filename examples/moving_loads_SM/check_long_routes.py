"""
Check if there are routes > 2000km in the dataset
"""
import yaml

# Load paths
with open('input_data/case_20251106_102427/Path.yaml', 'r') as f:
    paths = yaml.safe_load(f)

print("="*80)
print("ROUTE LENGTH ANALYSIS")
print("="*80)

# Analyze path lengths
lengths = [p['length'] for p in paths]
max_length = max(lengths)
min_length = min(lengths)
avg_length = sum(lengths) / len(lengths)

print(f"\nTotal paths: {len(paths)}")
print(f"Min length: {min_length:.1f} km")
print(f"Max length: {max_length:.1f} km")
print(f"Avg length: {avg_length:.1f} km")

# Distribution by bins
bins = [
    (0, 200),
    (200, 500),
    (500, 1000),
    (1000, 1500),
    (1500, 2000),
    (2000, 10000)
]

print(f"\n{'Category':<20} {'Count':>10} {'Percentage':>12}")
print("-" * 45)

for lower, upper in bins:
    if upper == 10000:
        label = f">{lower}km"
        count = sum(1 for l in lengths if l > lower)
    else:
        label = f"{lower}-{upper}km"
        count = sum(1 for l in lengths if lower < l <= upper)

    pct = (count / len(paths)) * 100
    print(f"{label:<20} {count:>10} {pct:>11.1f}%")

# Show longest routes
print(f"\n{'='*80}")
print("TOP 10 LONGEST ROUTES")
print("="*80)

sorted_paths = sorted(paths, key=lambda p: p['length'], reverse=True)[:10]

print(f"\n{'Path ID':<10} {'Length (km)':>15} {'Origin':>10} {'Destination':>10} {'Nodes':>10}")
print("-" * 60)

for p in sorted_paths:
    print(f"{p['id']:<10} {p['length']:>15.1f} {p['origin']:>10} {p['destination']:>10} {len(p['sequence']):>10}")

# Check if any > 2000km
over_2000 = [p for p in paths if p['length'] > 2000]

print(f"\n{'='*80}")
print(f"ROUTES > 2000km: {len(over_2000)}")
print("="*80)

if len(over_2000) > 0:
    print("\nThese routes exist but may have ZERO FLOW in the optimization results!")
    for p in over_2000[:20]:  # Show first 20
        print(f"  Path {p['id']}: {p['length']:.1f} km (Node {p['origin']} → Node {p['destination']})")
else:
    print("\nNO routes longer than 2000km exist in the input data.")
    print("The >2000km bin will always be empty.")
