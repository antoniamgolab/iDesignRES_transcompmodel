"""
Suggested update for modal_shift.ipynb distance bins
Replace the distance_bins and bin_labels in your analyze_modal_split_by_distance function
"""

# OPTION 1: Remove >2000km category (recommended)
distance_bins = [0, 200, 500, 1000, 1500, 2000]
bin_labels = ['0-200km', '200-500km', '500-1000km', '1000-1500km', '>1500km']

# OPTION 2: More granular for long routes
distance_bins = [0, 200, 500, 1000, 1500, 1800, 2500]
bin_labels = ['0-200km', '200-500km', '500-1000km', '1000-1500km', '1500-1800km', '>1800km']

# OPTION 3: Keep but rename last bin
distance_bins = [0, 200, 500, 1000, 1500, 10000]
bin_labels = ['0-200km', '200-500km', '500-1000km', '1000-1500km', '>1500km']

print("Recommended: Use OPTION 1 or OPTION 3")
print("\nIn your notebook, replace:")
print("  distance_bins = [0, 200, 500, 1000, 1500, 2000, 10000]")
print("  bin_labels = ['0-200km', '200-500km', '500-1000km', '1000-1500km', '1500-2000km', '>2000km']")
print("\nWith:")
print("  distance_bins = [0, 200, 500, 1000, 1500, 2000]")
print("  bin_labels = ['0-200km', '200-500km', '500-1000km', '1000-1500km', '>1500km']")
