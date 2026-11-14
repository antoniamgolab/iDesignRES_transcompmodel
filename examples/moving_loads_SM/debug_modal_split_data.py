"""
Debug script to check what's in modal_split_data
Add this cell BEFORE your plotting code
"""

# Check the data structure
print("="*80)
print("DEBUGGING MODAL SPLIT DATA")
print("="*80)

print("\nYears available:", list(modal_split_data.keys()))
print("Bin labels:", bin_labels)

# Check one year in detail
test_year = 2028
print(f"\n{test_year} data structure:")
for label in bin_labels:
    data = modal_split_data[test_year][label]
    print(f"\n{label}:")
    print(f"  rail: {data['rail']:.2e}")
    print(f"  road: {data['road']:.2e}")
    print(f"  total: {data['total']:.2e}")
    print(f"  rail_pct: {data['rail_pct']:.1f}%")
    print(f"  rail (billions): {data['rail']/1e9:.4f}")
    print(f"  road (billions): {data['road']/1e9:.4f}")

print("\n" + "="*80)
print("CHECK: Are the values all zero or very small?")
print("="*80)
