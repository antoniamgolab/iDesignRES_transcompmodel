"""
Fixed distance bins to match the labels
"""

# CORRECTED VERSION
# Note: 360km is the minimum distance for mandatory breaks (4.5h * 80 km/h)
distance_bins = [360, 500, 1000, 1500, 10000]
bin_labels = ['360-500km', '500-1000km', '1000-1500km', '>1500km']

print("="*80)
print("FIXED DISTANCE BINS")
print("="*80)
print(f"\ndistance_bins = {distance_bins}")
print(f"bin_labels = {bin_labels}")
print()
print("Mapping:")
for i, label in enumerate(bin_labels):
    lower = distance_bins[i]
    upper = distance_bins[i+1]
    if upper == 10000:
        print(f"  Bin {i}: {label:15s} -> {lower} < length")
    else:
        print(f"  Bin {i}: {label:15s} -> {lower} < length <= {upper}")

print()
print("="*80)
print("IMPORTANT: Update your loop logic too!")
print("="*80)
print("""
The current loop doesn't check lower bounds:
    for i, upper_bound in enumerate(distance_bins[1:]):
        if path_length <= upper_bound:
            results[year][bin_labels[i]][mode_name] += tkm
            break

REPLACE WITH:
    for i in range(len(bin_labels)):
        lower_bound = distance_bins[i]
        upper_bound = distance_bins[i+1]

        if lower_bound < path_length <= upper_bound:
            results[year][bin_labels[i]][mode_name] += tkm
            break
""")
