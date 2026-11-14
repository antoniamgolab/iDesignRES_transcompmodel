# Modal Split Analysis - Corrected Code

Replace the entire cell in `modal_shift.ipynb` with this corrected version.

## Complete Cell Code

```python
# ==============================================================================
# MODAL SPLIT BY ROUTE LENGTH - SIDE-BY-SIDE COMPARISON
# ==============================================================================

def analyze_modal_split_by_distance(case_study_name, selected_years=[2028, 2036, 2044]):
    """
    Analyze modal split (rail %) by route length categories.
    Returns both rail TKM and total TKM per category.
    """
    input_data = loaded_runs[case_study_name]["input_data"]
    output_data = loaded_runs[case_study_name]["output_data"]
    f_data = output_data["f"]
    paths = {p['id']: p for p in input_data['Path']}

    # Define distance bins - CORRECTED to match labels
    # 360km = 4.5h * 80km/h (minimum distance for mandatory breaks)
    distance_bins = [360, 500, 1000, 1500, 10000]
    bin_labels = ['360-500km', '500-1000km', '1000-1500km', '>1500km']

    # Initialize results: {year: {bin_label: {'road': tkm, 'rail': tkm, 'total': tkm}}}
    results = {year: {label: {'road': 0.0, 'rail': 0.0} for label in bin_labels} for year in selected_years}

    # Process flows
    for key, flow_value in f_data.items():
        year, (prod_id, od_id, path_id), (mode_id, tv_id), gen = key

        # Only selected years
        if year in selected_years and flow_value > 0:
            path_length = paths[path_id]['length']
            tkm = flow_value * path_length

            # Determine mode
            mode_name = 'rail' if mode_id == 2 else 'road'

            # Find bin - CORRECTED to check both lower and upper bounds
            for i in range(len(bin_labels)):
                lower_bound = distance_bins[i]
                upper_bound = distance_bins[i+1]

                if lower_bound < path_length <= upper_bound:
                    results[year][bin_labels[i]][mode_name] += tkm
                    break

    # Calculate totals and percentages
    for year in selected_years:
        for label in bin_labels:
            total = results[year][label]['road'] + results[year][label]['rail']
            results[year][label]['total'] = total
            results[year][label]['rail_pct'] = (results[year][label]['rail'] / total * 100) if total > 0 else 0

    return results, bin_labels

# Calculate
modal_split_data, bin_labels = analyze_modal_split_by_distance(case_name)

# DEBUG: Check data values
print("="*80)
print("DEBUG: Data Check")
print("="*80)
test_year = 2028
for label in bin_labels:
    data = modal_split_data[test_year][label]
    print(f"{label}: Rail={data['rail']/1e9:.4f}B, Road={data['road']/1e9:.4f}B, Total={data['total']/1e9:.4f}B")
print()

# ==============================================================================
# PLOT: SIDE-BY-SIDE RAIL VS ROAD COMPARISON
# ==============================================================================

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))

x = np.arange(len(bin_labels))
width = 0.25
years = [2028, 2036, 2044]
colors = ['#3498DB', '#2ECC71', '#F39C12']

# LEFT PLOT: Rail TKM
for i, year in enumerate(years):
    rail_tkm = [modal_split_data[year][label]['rail'] / 1e9 for label in bin_labels]

    bars = ax1.bar(x + i*width, rail_tkm, width,
                   label=f'{year}',
                   alpha=0.85, color=colors[i],
                   edgecolor='black', linewidth=1.2)

    # Add values on top
    for bar in bars:
        height = bar.get_height()
        if height > 0.01:
            ax1.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                    f'{height:.2f}B',
                    ha='center', va='bottom', fontsize=9,
                    fontweight='bold')

ax1.set_xlabel('Route Length Category', fontsize=13, fontweight='bold')
ax1.set_ylabel('Rail Freight Volume (Billion TKM)', fontsize=13, fontweight='bold')
ax1.set_title('RAIL Freight Volume by Distance Category',
              fontsize=14, fontweight='bold', color='#27AE60')
ax1.set_xticks(x + width)
ax1.set_xticklabels(bin_labels, rotation=0, fontsize=11)
ax1.legend(title='Year', fontsize=11)
ax1.grid(True, alpha=0.3, axis='y', linestyle='--')

# RIGHT PLOT: Road TKM
for i, year in enumerate(years):
    road_tkm = [modal_split_data[year][label]['road'] / 1e9 for label in bin_labels]

    bars = ax2.bar(x + i*width, road_tkm, width,
                   label=f'{year}',
                   alpha=0.85, color=colors[i],
                   edgecolor='black', linewidth=1.2)

    # Add values on top
    for bar in bars:
        height = bar.get_height()
        if height > 0.01:
            ax2.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                    f'{height:.2f}B',
                    ha='center', va='bottom', fontsize=9,
                    fontweight='bold')

ax2.set_xlabel('Route Length Category', fontsize=13, fontweight='bold')
ax2.set_ylabel('Road Freight Volume (Billion TKM)', fontsize=13, fontweight='bold')
ax2.set_title('ROAD Freight Volume by Distance Category',
              fontsize=14, fontweight='bold', color='#E74C3C')
ax2.set_xticks(x + width)
ax2.set_xticklabels(bin_labels, rotation=0, fontsize=11)
ax2.legend(title='Year', fontsize=11)
ax2.grid(True, alpha=0.3, axis='y', linestyle='--')

# Match y-axis scales for fair comparison
y_max = max(ax1.get_ylim()[1], ax2.get_ylim()[1])
ax1.set_ylim(0, y_max)
ax2.set_ylim(0, y_max)

plt.tight_layout()
plt.savefig('freight_volume_rail_vs_road.png', dpi=300, bbox_inches='tight')
print("✓ Side-by-side TKM plot saved as 'freight_volume_rail_vs_road.png'")
plt.show()

# ==============================================================================
# PRINT DETAILED STATISTICS
# ==============================================================================

print("\n" + "="*80)
print("MODAL SPLIT BY DISTANCE CATEGORY")
print("="*80)

for year in [2028, 2036, 2044]:
    print(f"\n{'='*80}")
    print(f"YEAR {year}")
    print(f"{'='*80}")
    print(f"{'Category':<20} {'Total (B tkm)':>15} {'Rail (B tkm)':>15} {'Road (B tkm)':>15} {'Rail %':>10}")
    print("-" * 80)

    year_total_tkm = 0
    year_total_rail = 0

    for label in bin_labels:
        total = modal_split_data[year][label]['total']
        rail = modal_split_data[year][label]['rail']
        road = modal_split_data[year][label]['road']
        rail_pct = modal_split_data[year][label]['rail_pct']

        year_total_tkm += total
        year_total_rail += rail

        if total > 0:
            print(f"{label:<20} {total/1e9:>15.3f} {rail/1e9:>15.3f} {road/1e9:>15.3f} {rail_pct:>9.1f}%")

    print("-" * 80)
    overall_rail_pct = (year_total_rail / year_total_tkm * 100) if year_total_tkm > 0 else 0
    print(f"{'TOTAL':<20} {year_total_tkm/1e9:>15.3f} {year_total_rail/1e9:>15.3f} {(year_total_tkm-year_total_rail)/1e9:>15.3f} {overall_rail_pct:>9.1f}%")

print("\n" + "="*80)
print("INTERPRETATION GUIDE")
print("="*80)
print("LEFT PLOT (Rail):")
print("  - Bars growing taller = Rail TKM is INCREASING")
print("  - Bars shrinking = Rail TKM is DECREASING")
print("\nRIGHT PLOT (Road):")
print("  - Bars growing = Road TKM is INCREASING")
print("  - Bars shrinking = Road TKM is DECREASING")
print("\nIf rail bars grow but road bars grow faster → rail percentage decreases")
print("This means rail is growing but not capturing all new freight demand")
```

## Key Fixes Applied

1. **Distance bins match labels:**
   - `distance_bins = [360, 500, 1000, 1500, 10000]`
   - `bin_labels = ['360-500km', '500-1000km', '1000-1500km', '>1500km']`

2. **Corrected binning logic:**
   - Now checks BOTH lower and upper bounds: `lower_bound < path_length <= upper_bound`
   - Previous code only checked upper bound, causing incorrect categorization

3. **Side-by-side plots:**
   - LEFT: Rail freight volume (green title)
   - RIGHT: Road freight volume (red title)
   - Same Y-axis scale for fair comparison

4. **Debug output:**
   - Shows data values before plotting
   - Helps identify if bins are empty or values are too small

## Expected Output

You should see:
- Two plots side-by-side with bars showing TKM values
- Numbers on top of bars (e.g., "2.45B", "3.10B")
- Console output showing exact values in a table
- Clear comparison of rail vs road growth patterns

## Troubleshooting

If you still see empty plots:
1. Check the DEBUG output - are the values all 0.00B?
2. Check if your selected years exist in the flow data
3. Verify that routes are longer than 360km
4. Make sure `case_name` variable is correctly defined
