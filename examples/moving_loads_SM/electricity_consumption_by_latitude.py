"""
Electricity Consumption by Latitude - BEV Energy Demand Analysis

This creates a 4-subplot figure showing electricity consumption by BEV vehicles
across latitude for different case studies.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter1d


def calculate_electricity_by_nuts2(loaded_runs, case_study_name, target_year=2052):
    """
    Calculate electricity consumption (GWh) by NUTS2 region from the s variable.

    Uses the energy supply data (s) from optimization output which directly
    tells us how much electricity was consumed at each location.

    Returns:
        dict: {nuts2_id: {'electricity_gwh': value, 'lat': latitude, 'nuts2': nuts2_code, infra_types...}}
    """
    input_data = loaded_runs[case_study_name]["input_data"]
    output_data = loaded_runs[case_study_name]["output_data"]
    s_data = output_data["s"]

    # NUTS2 lookup
    geo_elements = input_data['GeographicElement']
    nuts2_lookup = {}
    for geo in geo_elements:
        if geo['type'] == 'node' and 'nuts2_region' in geo and geo['nuts2_region']:
            nuts2_lookup[geo['id']] = {
                'nuts2': geo['nuts2_region'],
                'lat': geo['coordinate_lat'],
                'lon': geo['coordinate_long']
            }

    print(f"  Found {len(nuts2_lookup)} NUTS2 regions")

    # Identify electricity fuel IDs
    fuels = input_data['Fuel']
    electricity_fuel_ids = [f['id'] for f in fuels if 'electric' in f['name'].lower()]
    print(f"  Electricity fuel IDs: {electricity_fuel_ids}")

    # Map fueling infrastructure IDs to types (only electricity entries)
    fueling_infra_types = input_data.get('FuelingInfrTypes', [])
    infra_id_to_type = {}
    for infra in fueling_infra_types:
        if infra.get('fuel', '').lower() == 'electricity':
            infra_id_to_type[infra['id']] = infra['fueling_type']

    print(f"  Electricity infrastructure types: {infra_id_to_type}")

    # Scaling factor for energy values
    SCALING_FACTOR = 1000

    # Initialize: {geo_id: {infra_type: kwh, 'lat': X, 'nuts2': Y}}
    electricity_by_geo = {}

    # Process energy supply data
    for key_str, energy_value_scaled in s_data.items():
        # Parse key
        key = eval(key_str) if isinstance(key_str, str) else key_str
        year, (_, _, _, geo_id), _, (fuel_id, fueling_infra_id), _ = key

        # Convert energy_value_scaled to float (YAML may load as string)
        energy_value = float(energy_value_scaled) if isinstance(energy_value_scaled, str) else energy_value_scaled

        if year != target_year or energy_value <= 0:
            continue

        if fuel_id not in electricity_fuel_ids:
            continue

        if geo_id not in nuts2_lookup:
            continue

        # Calculate actual energy in kWh
        energy_kwh = energy_value * SCALING_FACTOR

        # Get infrastructure type
        infra_type = infra_id_to_type.get(fueling_infra_id, f'infra_{fueling_infra_id}')

        # Initialize if needed
        if geo_id not in electricity_by_geo:
            electricity_by_geo[geo_id] = {
                'lat': nuts2_lookup[geo_id]['lat'],
                'nuts2': nuts2_lookup[geo_id]['nuts2']
            }

        # Add electricity consumption for this infrastructure type
        electricity_by_geo[geo_id][infra_type] = electricity_by_geo[geo_id].get(infra_type, 0.0) + energy_kwh

    # Calculate total electricity in GWh for each region
    for geo_id in electricity_by_geo:
        total_kwh = sum(v for k, v in electricity_by_geo[geo_id].items() if k not in ('lat', 'nuts2'))
        electricity_by_geo[geo_id]['electricity_gwh'] = total_kwh / 1e6

    return electricity_by_geo


def calculate_electricity_by_latitude(electricity_by_geo):
    """
    Calculate electricity consumption for each NUTS2 region.

    Returns:
        list: [(latitude, electricity_gwh), ...] sorted by latitude
    """
    results = []

    for geo_id, data in electricity_by_geo.items():
        electricity_gwh = data.get('electricity_gwh', 0)

        if electricity_gwh > 0:
            results.append((data['lat'], electricity_gwh))

    # Sort by latitude
    results.sort(key=lambda x: x[0])
    return results


def plot_electricity_by_latitude_4cases(loaded_runs, case_studies, year=2052,
                                         case_labels=None, country_centroids_csv='country_centroids.csv'):
    """
    Create multi-subplot figure showing electricity consumption by latitude for different case studies.

    Parameters:
    -----------
    loaded_runs : dict
        Dictionary of loaded case data
    case_studies : list
        List of 4 case study names to plot
    year : int
        Year to analyze (default: 2052)
    case_labels : dict
        Optional dict mapping case names to display labels
    country_centroids_csv : str
        Path to country centroids CSV file
    """
    # Calculate electricity consumption data for each case
    print("="*80)
    print(f"CALCULATING ELECTRICITY CONSUMPTION BY LATITUDE (Year: {year})")
    print("="*80)

    electricity_data = {}
    for case_name in case_studies:
        print(f"\nProcessing: {case_name}")
        elec_data = calculate_electricity_by_nuts2(loaded_runs, case_name, target_year=year)
        electricity_data[case_name] = calculate_electricity_by_latitude(elec_data)

        data = electricity_data[case_name]
        if data:
            elec_values = [x[1] for x in data]
            print(f"  Regions with BEV traffic: {len(data)}")
            print(f"  Electricity range: {min(elec_values):.1f} to {max(elec_values):.1f} GWh")
            print(f"  Total electricity demand: {sum(elec_values):.1f} GWh")

    # Create figure with subplots (flexible number based on case studies)
    n_cases = len(case_studies)
    fig, axes = plt.subplots(1, n_cases, figsize=(3*n_cases, 8), sharey=True, sharex=True)

    # Handle single case
    if n_cases == 1:
        axes = [axes]

    colors = ['#E74C3C', '#3498DB', '#2ECC71', '#F39C12', '#9B59B6', '#1ABC9C']  # Extended color palette

    # Find global maximum across all cases for consistent x-axis scaling
    global_max_elec = 0
    for case_name in case_studies:
        data = electricity_data[case_name]
        if data:
            electricity_gwh = np.array([x[1] for x in data])
            global_max_elec = max(global_max_elec, np.max(electricity_gwh))

    for idx, (ax, case_name) in enumerate(zip(axes, case_studies)):
        color = colors[idx % len(colors)]  # Cycle through colors if needed
        data = electricity_data[case_name]

        if not data:
            ax.text(0.5, 0.5, 'No data', ha='center', va='center', transform=ax.transAxes)
            continue

        # Extract data
        latitudes = np.array([x[0] for x in data])
        electricity_gwh = np.array([x[1] for x in data])

        # Smooth the data for continuous area
        if len(latitudes) > 3:
            # Sort data by latitude
            sort_idx = np.argsort(latitudes)
            lat_sorted = latitudes[sort_idx]
            elec_sorted = electricity_gwh[sort_idx]

            # Apply Gaussian smoothing
            elec_smoothed = gaussian_filter1d(elec_sorted, sigma=1.5)

            # Create area plot
            ax.fill_betweenx(lat_sorted, 0, elec_smoothed,
                            color=color, alpha=0.6, label='BEV Electricity', zorder=2)

            # Add outline for clarity
            ax.plot(elec_smoothed, lat_sorted,
                   color=color, linewidth=2, alpha=0.9, zorder=3)

        else:
            # Not enough points for smoothing
            ax.fill_betweenx(latitudes, 0, electricity_gwh,
                            color=color, alpha=0.6, label='BEV Electricity', zorder=2)

        # Formatting
        ax.set_xlabel('Electricity Consumption\\(GWh)', fontsize=15, fontweight='bold')

        # Use custom label if provided
        if case_labels and case_name in case_labels:
            title = case_labels[case_name]
        else:
            title = case_name

        ax.set_title(title, fontsize=17, fontweight='bold', pad=15)
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.tick_params(axis='both', labelsize=14)

        if idx == 0:
            ax.set_ylabel('Latitude (°N)', fontsize=16, fontweight='bold')

    # Set consistent x-axis limit for all subplots to 0.15 GWh
    for ax in axes:
        ax.set_xlim(0, 0.15)

    # Overall title
    fig.suptitle(f'BEV Electricity Consumption by Latitude: Year {year}\nScandinavian-Mediterranean Corridor',
                 fontsize=18, fontweight='bold', y=1.02)

    # Add country labels
    try:
        country_centroids = pd.read_csv(country_centroids_csv)
        corridor_countries = ['IT', 'AT', 'DE', 'DK', 'NO', 'SE']
        country_data = country_centroids[country_centroids['CNTR_CODE'].isin(corridor_countries)]

        for ax in axes:
            ylim = ax.get_ylim()

            for _, row in country_data.iterrows():
                country_code = row['CNTR_CODE']
                lat = row['centroid_lat']

                if ylim[0] <= lat <= ylim[1]:
                    ax.axhline(lat, color='gray', linestyle=':', alpha=0.3, linewidth=1.0, zorder=1)
                    ax.text(1.03, lat, country_code, transform=ax.get_yaxis_transform(),
                           fontsize=13, fontweight='bold', va='center', ha='left',
                           bbox=dict(boxstyle='round,pad=0.4', facecolor='white',
                                   edgecolor='#666', alpha=0.9, linewidth=1.5),
                           zorder=10)

        print("\nCountry labels added to latitude plots")
    except Exception as e:
        print(f"\nWarning: Could not add country labels: {e}")

    plt.tight_layout()
    output_file = f'electricity_consumption_by_latitude_{year}.svg'
    plt.savefig(output_file, format='svg', bbox_inches='tight')
    print(f"\n[OK] Electricity consumption plot saved as '{output_file}'")
    plt.show()

    return electricity_data


def plot_latitude_comparison_two_cases(loaded_runs, case1_name, case2_name, case1_label, case2_label,
                                        year=2040, country_centroids_csv='country_centroids.csv'):
    """
    Create a single narrow plot comparing two cases with overlapping curves.

    Parameters:
    -----------
    loaded_runs : dict
        Dictionary of loaded case data
    case1_name : str
        Name of first case study (e.g., "case_20251110_160304_var_var")
    case2_name : str
        Name of second case study (e.g., "case_20251110_160604_uni_uni")
    case1_label : str
        Display label for case 1
    case2_label : str
        Display label for case 2
    year : int
        Year to analyze (default: 2040)
    country_centroids_csv : str
        Path to country centroids CSV file
    """
    print("="*80)
    print(f"TWO-CASE LATITUDE COMPARISON (Year: {year})")
    print("="*80)

    # Calculate electricity for both cases
    elec_data1_dict = calculate_electricity_by_nuts2(loaded_runs, case1_name, target_year=year)
    elec_data1 = calculate_electricity_by_latitude(elec_data1_dict)

    elec_data2_dict = calculate_electricity_by_nuts2(loaded_runs, case2_name, target_year=year)
    elec_data2 = calculate_electricity_by_latitude(elec_data2_dict)

    print(f"\n{case1_label}:")
    print(f"  Regions: {len(elec_data1)}")
    print(f"  Total: {sum([x[1] for x in elec_data1]):.2f} GWh")

    print(f"\n{case2_label}:")
    print(f"  Regions: {len(elec_data2)}")
    print(f"  Total: {sum([x[1] for x in elec_data2]):.2f} GWh")

    # Create narrow figure (3 cm ≈ 1.18 inches width, taller for readability)
    fig, ax = plt.subplots(figsize=(1.18, 8))

    # Colors for the two cases
    color1 = '#840032'  # Red
    color2 = '#99b2dd'  # Blue

    # Process data for smooth curves
    if len(elec_data1) > 3:
        lats1 = np.array([x[0] for x in elec_data1])
        elec1 = np.array([x[1] for x in elec_data1])
        sort_idx1 = np.argsort(lats1)
        lat_sorted1 = lats1[sort_idx1]
        elec_sorted1 = elec1[sort_idx1]
        elec_smoothed1 = gaussian_filter1d(elec_sorted1, sigma=1.5)
    else:
        lat_sorted1 = np.array([x[0] for x in elec_data1])
        elec_smoothed1 = np.array([x[1] for x in elec_data1])

    if len(elec_data2) > 3:
        lats2 = np.array([x[0] for x in elec_data2])
        elec2 = np.array([x[1] for x in elec_data2])
        sort_idx2 = np.argsort(lats2)
        lat_sorted2 = lats2[sort_idx2]
        elec_sorted2 = elec2[sort_idx2]
        elec_smoothed2 = gaussian_filter1d(elec_sorted2, sigma=1.5)
    else:
        lat_sorted2 = np.array([x[0] for x in elec_data2])
        elec_smoothed2 = np.array([x[1] for x in elec_data2])

    # Plot overlapping curves with high transparency
    ax.plot(elec_smoothed1, lat_sorted1, color=color1, linewidth=3, alpha=0.7,
            label=case1_label, zorder=3)
    ax.plot(elec_smoothed2, lat_sorted2, color=color2, linewidth=3, alpha=0.7,
            label=case2_label, zorder=3)

    # Formatting
    ax.set_xlabel('Electricity (GWh)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Latitude (°N)', fontsize=14, fontweight='bold')
    ax.set_xlim(0, 0.15)
    ax.set_ylim(39, 68.5)
    # Position legend in upper left with small offset from corner
    # bbox_to_anchor: (x, y) where (0,0) is bottom-left, (1,1) is top-right
    # (0.05, 0.97) means 5% from left edge, 97% from bottom (slightly inset from top-left corner)
    ax.legend(loc='upper left', bbox_to_anchor=(-0.05, 1.1), fontsize=10, framealpha=0.9)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.tick_params(axis='both', labelsize=12)

    # Add country labels
    try:
        country_centroids = pd.read_csv(country_centroids_csv)
        corridor_countries = ['IT', 'AT', 'DE', 'DK', 'NO', 'SE']
        country_data = country_centroids[country_centroids['CNTR_CODE'].isin(corridor_countries)]

        ylim = ax.get_ylim()
        for _, row in country_data.iterrows():
            country_code = row['CNTR_CODE']
            lat = row['centroid_lat']

            if ylim[0] <= lat <= ylim[1]:
                ax.axhline(lat, color='gray', linestyle=':', alpha=0.3, linewidth=0.8, zorder=1)
                ax.text(1.03, lat, country_code, transform=ax.get_yaxis_transform(),
                       fontsize=11, fontweight='bold', va='center', ha='left',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                               edgecolor='#666', alpha=0.9, linewidth=1.0),
                       zorder=10)
    except Exception as e:
        print(f"\nWarning: Could not add country labels: {e}")

    plt.tight_layout()
    output_file = f'latitude_comparison_{year}.svg'
    plt.savefig(output_file, format='svg', bbox_inches='tight')
    print(f"\n[OK] Narrow latitude comparison saved as '{output_file}'")
    plt.show()

    # Calculate delta (difference) by latitude
    print("\n" + "="*80)
    print("DELTA ANALYSIS: Energy Difference by Latitude")
    print("="*80)
    print(f"Delta = {case1_label} - {case2_label}")
    print("="*80)

    # Create common latitude grid for delta calculation
    # Match latitudes from both datasets
    lat_dict1 = {lat: elec for lat, elec in elec_data1}
    lat_dict2 = {lat: elec for lat, elec in elec_data2}

    all_lats = sorted(set(lat_dict1.keys()) | set(lat_dict2.keys()))

    delta_data = []
    for lat in all_lats:
        val1 = lat_dict1.get(lat, 0.0)
        val2 = lat_dict2.get(lat, 0.0)
        delta = val1 - val2
        if abs(delta) > 0.001:  # Only show significant differences
            delta_data.append({
                'Latitude': f"{lat:.1f}°N",
                f'{case1_label} (GWh)': f"{val1:.3f}",
                f'{case2_label} (GWh)': f"{val2:.3f}",
                'Delta (GWh)': f"{delta:+.3f}"
            })

    if delta_data:
        df_delta = pd.DataFrame(delta_data)
        print("\n" + df_delta.to_string(index=False))

        # Save to CSV
        df_delta.to_csv(f'latitude_delta_{year}.csv', index=False)
        print(f"\n[OK] Delta data saved to 'latitude_delta_{year}.csv'")
    else:
        print("\nNo significant differences found")

    print("="*80)

    return {
        'case1': elec_data1,
        'case2': elec_data2,
        'delta': delta_data
    }


def analyze_electricity_by_latitude_band(electricity_data, band_width=5):
    """
    Group NUTS2 regions into latitude bands and calculate total electricity consumption.

    Parameters:
    -----------
    electricity_data : list
        List of (latitude, electricity_gwh) tuples
    band_width : int
        Width of latitude bands in degrees (default: 5)
    """
    if not electricity_data:
        print("No data to analyze")
        return

    # Define latitude bands
    lat_min = min(x[0] for x in electricity_data)
    lat_max = max(x[0] for x in electricity_data)

    # Create bands
    bands = []
    current = int(lat_min / band_width) * band_width
    while current <= lat_max:
        bands.append((current, current + band_width))
        current += band_width

    print(f"{'Latitude Band':<20} {'# Regions':>12} {'Electricity (GWh)':>18}")
    print("-" * 60)

    for band_min, band_max in bands:
        # Filter data for this band
        band_data = [x for x in electricity_data if band_min <= x[0] < band_max]

        if band_data:
            n_regions = len(band_data)
            total_electricity = sum([x[1] for x in band_data])

            print(f"{band_min:2d}°N - {band_max:2d}°N{' ':<7} {n_regions:12d} {total_electricity:18.1f}")


# ==============================================================================
# USAGE EXAMPLE IN JUPYTER NOTEBOOK
# ==============================================================================
"""
# Import
from electricity_consumption_by_latitude import plot_electricity_by_latitude_4cases, analyze_electricity_by_latitude_band

# Define your 4 case studies
case_studies = [
    "case_20251107_153441_var_var",
    "case_20251107_160348_var_uni",
    "case_20251107_164008_uni_var",
    "case_20251107_153651_uni_uni"
]

# Define custom labels
case_labels = {
    "case_20251107_153441_var_var": "Base Case\n(Var. Prices and Costs)",
    "case_20251107_160348_var_uni": "Uniform Network Costs",
    "case_20251107_164008_uni_var": "Uniform Electricity Prices",
    "case_20251107_153651_uni_uni": "Uniform Prices and Costs"
}

# Create plot for year 2052
elec_data = plot_electricity_by_latitude_4cases(
    loaded_runs,
    case_studies,
    year=2052,
    case_labels=case_labels,
    country_centroids_csv='country_centroids.csv'
)

# Print detailed statistics for each case
print("\n" + "="*80)
print("ELECTRICITY CONSUMPTION BY LATITUDE BAND")
print("="*80)

for case_name in case_studies:
    label = case_labels.get(case_name, case_name)
    print(f"\n{label}:")
    analyze_electricity_by_latitude_band(elec_data[case_name])

# Compare across years
for year in [2032, 2040, 2052]:
    print(f"\n{'='*80}")
    print(f"YEAR: {year}")
    print('='*80)
    elec_data_year = plot_electricity_by_latitude_4cases(
        loaded_runs,
        case_studies,
        year=year,
        case_labels=case_labels
    )
"""
