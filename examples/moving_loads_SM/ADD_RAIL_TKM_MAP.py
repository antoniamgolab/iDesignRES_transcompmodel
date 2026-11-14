"""
ADD TO modal_shift.ipynb:
Map visualization showing where RAIL TKM are concentrated with scatter plots

This creates a map similar to existing freight distribution but specifically
for RAIL mode, showing geographical distribution of rail freight
"""

# ==============================================================================
# RAIL TKM SPATIAL DISTRIBUTION MAP
# ==============================================================================
import matplotlib.pyplot as plt
import numpy as np

def calculate_rail_tkm_by_nuts2(case_name, loaded_runs, year):
    """
    Calculate rail TKM (tonne-kilometers) by NUTS2 region for a specific year

    Args:
        case_name: Name of the case study
        loaded_runs: Dict containing loaded data
        year: Year to analyze

    Returns:
        Dict with NUTS2 regions as keys and their rail TKM, coordinates, etc.
    """
    print(f"\nCalculating RAIL TKM by NUTS2 for year {year}...")

    # Load data
    f_data = loaded_runs[case_name]["output_data"]["f"]
    paths = loaded_runs[case_name]["input_data"]["Path"]
    odpairs = loaded_runs[case_name]["input_data"]["Odpair"]
    geo_elements = loaded_runs[case_name]["input_data"]["GeographicElement"]
    modes = loaded_runs[case_name]["input_data"]["Mode"]

    # Create lookups
    geo_dict = {geo['id']: geo for geo in geo_elements}
    path_dict = {p['id']: p for p in paths}
    odpair_dict = {od['id']: od for od in odpairs}
    mode_dict = {m['id']: m for m in modes}

    # Find rail mode ID
    rail_mode_id = None
    for mode in modes:
        if mode['name'].lower() == 'rail':
            rail_mode_id = mode['id']
            break

    if rail_mode_id is None:
        print("[ERROR] Rail mode not found!")
        return {}

    print(f"  Rail mode ID: {rail_mode_id}")

    # Aggregate rail TKM by NUTS2 region
    nuts2_data = {}

    for key, flow_value in f_data.items():
        # Parse key: (year, (prod_id, odpair_id, path_id), (mode_id, tv_id), gen)
        key_year = key[0]

        if key_year != year:
            continue

        mode_id = key[2][0]

        # Only process rail
        if mode_id != rail_mode_id:
            continue

        path_id = key[1][2]
        odpair_id = key[1][1]

        # Get path and odpair info
        path = path_dict.get(path_id)
        odpair = odpair_dict.get(odpair_id)

        if not path or not odpair:
            continue

        # Calculate TKM: flow (tonnes) × path length (km)
        tkm = flow_value * path['length']

        # Assign TKM to origin and destination NUTS2 regions
        origin_geo = geo_dict.get(path['sequence'][0])
        dest_geo = geo_dict.get(path['sequence'][-1])

        for geo in [origin_geo, dest_geo]:
            if not geo:
                continue

            nuts2 = geo.get('nuts2_region', 'Unknown')

            if nuts2 not in nuts2_data:
                nuts2_data[nuts2] = {
                    'tkm': 0,
                    'lat': geo.get('coordinate_lat', 0),
                    'lon': geo.get('coordinate_long', 0),
                    'country': geo.get('country', 'Unknown'),
                    'name': geo.get('name', nuts2)
                }

            # Add half of TKM to each end (origin and destination)
            nuts2_data[nuts2]['tkm'] += tkm / 2

    print(f"  Found {len(nuts2_data)} NUTS2 regions with rail freight")
    print(f"  Total rail TKM: {sum(d['tkm'] for d in nuts2_data.values()) / 1e9:.2f} billion tkm")

    return nuts2_data


def plot_rail_tkm_map(nuts2_data, year, case_name):
    """
    Create map showing rail TKM distribution with scatter plots

    Args:
        nuts2_data: Dict from calculate_rail_tkm_by_nuts2
        year: Year being visualized
        case_name: Name of case study for title
    """
    fig, ax = plt.subplots(figsize=(14, 16))

    # Extract data for plotting
    lats = [data['lat'] for data in nuts2_data.values()]
    lons = [data['lon'] for data in nuts2_data.values()]
    tkm_values = np.array([data['tkm'] for data in nuts2_data.values()])

    # Convert to billions for better readability
    tkm_billions = tkm_values / 1e9

    # Create scatter plot with size proportional to TKM
    # Use log scale for better visual distribution
    sizes = 100 + (tkm_billions ** 0.5) * 200  # Square root scaling for better visibility

    # Color based on TKM amount
    scatter = ax.scatter(lons, lats,
                        s=sizes,
                        c=tkm_billions,
                        cmap='YlOrRd',  # Yellow-Orange-Red colormap
                        alpha=0.6,
                        edgecolors='black',
                        linewidth=1)

    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label('Rail TKM (Billion tkm)', rotation=270, labelpad=25, fontsize=12)

    # Add labels for largest regions
    threshold = np.percentile(tkm_billions, 75)  # Top 25%

    for nuts2, data in nuts2_data.items():
        if data['tkm'] / 1e9 > threshold:
            ax.annotate(nuts2,
                       (data['lon'], data['lat']),
                       fontsize=8,
                       bbox=dict(boxstyle='round,pad=0.3',
                                facecolor='white',
                                alpha=0.7,
                                edgecolor='none'),
                       ha='center')

    # Formatting
    ax.set_xlabel('Longitude', fontsize=12, fontweight='bold')
    ax.set_ylabel('Latitude', fontsize=12, fontweight='bold')
    ax.set_title(f'Rail Freight Distribution - Year {year}\n' +
                f'Scandinavian-Mediterranean Corridor\n' +
                f'(Bubble size = Rail TKM volume)',
                fontsize=14, fontweight='bold', pad=20)

    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_aspect('equal', adjustable='box')

    # Add statistics box
    total_rail_tkm = sum(data['tkm'] for data in nuts2_data.values()) / 1e9
    num_regions = len(nuts2_data)
    avg_tkm = total_rail_tkm / num_regions if num_regions > 0 else 0

    stats_text = f"""Statistics:
Total Rail TKM: {total_rail_tkm:.2f}B tkm
Active Regions: {num_regions}
Avg per Region: {avg_tkm:.2f}B tkm"""

    ax.text(0.02, 0.98, stats_text,
           transform=ax.transAxes,
           verticalalignment='top',
           bbox=dict(boxstyle='round',
                    facecolor='wheat',
                    alpha=0.8),
           fontsize=10,
           family='monospace')

    plt.tight_layout()
    plt.savefig(f'rail_tkm_map_{year}.png', dpi=300, bbox_inches='tight')
    plt.show()

    print(f"\nMap saved as: rail_tkm_map_{year}.png")


# ==============================================================================
# USAGE EXAMPLE - ADD THIS CELL TO YOUR NOTEBOOK
# ==============================================================================

# Select year and case to visualize
year_to_plot = 2052
case_name = "case_20251106_112933"  # Update with your case name

# Calculate rail TKM by region
rail_nuts2_data = calculate_rail_tkm_by_nuts2(case_name, loaded_runs, year_to_plot)

# Create the map
plot_rail_tkm_map(rail_nuts2_data, year_to_plot, case_name)

# Optional: Create maps for multiple years
print("\n" + "="*80)
print("CREATING MAPS FOR MULTIPLE YEARS")
print("="*80)

years_to_plot = [2028, 2036, 2044, 2052]

fig, axes = plt.subplots(2, 2, figsize=(20, 22))
axes = axes.flatten()

for idx, year in enumerate(years_to_plot):
    ax = axes[idx]

    # Calculate for this year
    rail_nuts2_data = calculate_rail_tkm_by_nuts2(case_name, loaded_runs, year)

    if not rail_nuts2_data:
        print(f"No data for year {year}")
        continue

    # Extract data
    lats = [data['lat'] for data in rail_nuts2_data.values()]
    lons = [data['lon'] for data in rail_nuts2_data.values()]
    tkm_values = np.array([data['tkm'] for data in rail_nuts2_data.values()])
    tkm_billions = tkm_values / 1e9

    # Size scaling
    sizes = 100 + (tkm_billions ** 0.5) * 200

    # Plot
    scatter = ax.scatter(lons, lats,
                        s=sizes,
                        c=tkm_billions,
                        cmap='YlOrRd',
                        alpha=0.6,
                        edgecolors='black',
                        linewidth=1,
                        vmin=0,
                        vmax=tkm_billions.max() * 1.1)

    # Add labels for largest regions
    threshold = np.percentile(tkm_billions, 80)
    for nuts2, data in rail_nuts2_data.items():
        if data['tkm'] / 1e9 > threshold:
            ax.annotate(nuts2,
                       (data['lon'], data['lat']),
                       fontsize=7,
                       bbox=dict(boxstyle='round,pad=0.3',
                                facecolor='white',
                                alpha=0.7,
                                edgecolor='none'),
                       ha='center')

    # Formatting
    ax.set_xlabel('Longitude', fontsize=11)
    ax.set_ylabel('Latitude', fontsize=11)
    ax.set_title(f'Year {year}\nTotal Rail: {tkm_billions.sum():.2f}B tkm',
                fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_aspect('equal', adjustable='box')

# Add shared colorbar
fig.colorbar(scatter, ax=axes, fraction=0.046, pad=0.04,
            label='Rail TKM (Billion tkm)')

plt.suptitle('Rail Freight Distribution Over Time\nScandinavian-Mediterranean Corridor',
            fontsize=16, fontweight='bold', y=0.995)
plt.tight_layout()
plt.savefig('rail_tkm_map_time_series.png', dpi=300, bbox_inches='tight')
plt.show()

print("\nTime series map saved as: rail_tkm_map_time_series.png")
