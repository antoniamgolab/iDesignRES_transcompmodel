"""
BEV Technology Share by Latitude - Similar to Modal Split Visualization

This creates a 4-subplot figure showing BEV share across latitude for different case studies,
similar to the modal_split.ipynb visualization but for technology shift (ICEV → BEV).
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter1d


def calculate_tkm_by_nuts2_and_tech(loaded_runs, case_study_name, target_year=2052):
    """
    Calculate TKM passing through each NUTS2 region by technology (ICEV vs BEV) and year.

    Uses distance_from_previous to assign TKM to each node in path sequence.

    Returns:
        dict: {nuts2_id: {'icev': tkm, 'bev': tkm, 'lat': latitude, 'nuts2': nuts2_code}}
    """
    input_data = loaded_runs[case_study_name]["input_data"]
    output_data = loaded_runs[case_study_name]["output_data"]
    f_data = output_data["f"]

    # Identify BEV tech vehicles
    tech_data = input_data.get("Technology") or input_data.get("technology", [])
    tv_data = input_data.get("TechVehicle") or input_data.get("techvehicle", [])

    # Create mapping: technology_id -> fuel_name
    tech_to_fuel = {}
    if isinstance(tech_data, list):
        for tech in tech_data:
            if isinstance(tech, dict):
                tech_id = tech.get('id')
                fuel = tech.get('fuel', '').lower()
                if tech_id is not None:
                    tech_to_fuel[int(tech_id)] = fuel

    # Find BEV tech vehicle IDs
    bev_tv_ids = set()
    if isinstance(tv_data, list):
        for tv in tv_data:
            if not isinstance(tv, dict):
                continue
            tv_id = tv.get('id')
            tech_id = tv.get('technology')

            if tv_id is None or tech_id is None:
                continue

            fuel_name = tech_to_fuel.get(int(tech_id), 'unknown')
            if 'electricity' in fuel_name or 'electric' in fuel_name:
                bev_tv_ids.add(int(tv_id))

    print(f"  BEV tech vehicle IDs: {bev_tv_ids}")

    # Load geographic elements and filter to NUTS2 nodes
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

    # Load paths
    paths = {p['id']: p for p in input_data['Path']}

    # Initialize: {geo_id: {tech: tkm}}
    tkm_by_geo_tech = {}

    # Process each flow
    for key, flow_value in f_data.items():
        year, (prod_id, od_id, path_id), (mode_id, tv_id), gen = key

        if year != target_year or flow_value <= 0:
            continue

        # Get path data
        path = paths[path_id]
        sequence = path['sequence']
        distance_from_previous = path['distance_from_previous']

        # Determine technology
        tech_type = 'bev' if tv_id in bev_tv_ids else 'icev'

        # Assign TKM to each node based on distance_from_previous
        for i, node_id in enumerate(sequence):
            # Only process NUTS2 nodes
            if node_id not in nuts2_lookup:
                continue

            # TKM = flow × distance traveled TO this node
            segment_distance = distance_from_previous[i]
            tkm_segment = flow_value * segment_distance

            # Initialize if needed
            if node_id not in tkm_by_geo_tech:
                tkm_by_geo_tech[node_id] = {
                    'icev': 0.0,
                    'bev': 0.0,
                    'lat': nuts2_lookup[node_id]['lat'],
                    'nuts2': nuts2_lookup[node_id]['nuts2']
                }

            # Add to appropriate technology
            tkm_by_geo_tech[node_id][tech_type] += tkm_segment

    return tkm_by_geo_tech


def calculate_bev_share_by_latitude(tkm_by_geo_tech):
    """
    Calculate BEV and total freight volume for each NUTS2 region.

    Returns:
        list: [(latitude, bev_tkm, total_tkm), ...] sorted by latitude
    """
    results = []

    for geo_id, data in tkm_by_geo_tech.items():
        icev_tkm = data['icev']
        bev_tkm = data['bev']
        total_tkm = icev_tkm + bev_tkm

        if total_tkm > 0:
            results.append((data['lat'], bev_tkm, total_tkm))

    # Sort by latitude
    results.sort(key=lambda x: x[0])
    return results


def plot_bev_share_by_latitude_4cases(loaded_runs, case_studies, year=2052,
                                       case_labels=None, country_centroids_csv='country_centroids.csv'):
    """
    Create 4-subplot figure showing BEV share by latitude for different case studies.

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
    if len(case_studies) != 4:
        print(f"Warning: Expected 4 case studies, got {len(case_studies)}")

    # Calculate BEV share data for each case
    print("="*80)
    print(f"CALCULATING BEV SHARE BY LATITUDE (Year: {year})")
    print("="*80)

    bev_share_data = {}
    for case_name in case_studies:
        print(f"\nProcessing: {case_name}")
        tkm_data = calculate_tkm_by_nuts2_and_tech(loaded_runs, case_name, target_year=year)
        bev_share_data[case_name] = calculate_bev_share_by_latitude(tkm_data)

        data = bev_share_data[case_name]
        if data:
            bev_tkms = [x[1] for x in data]
            total_tkms = [x[2] for x in data]
            print(f"  Regions with traffic: {len(data)}")
            print(f"  BEV TKM range: {min(bev_tkms)/1e6:.1f}M to {max(bev_tkms)/1e6:.1f}M")
            print(f"  Total freight volume: {sum(total_tkms)/1e6:.1f}M TKM")

    # Create figure with 4 subplots
    fig, axes = plt.subplots(1, 4, figsize=(12, 8), sharey=True)

    colors = ['#E74C3C', '#3498DB', '#2ECC71', '#F39C12']  # Red, Blue, Green, Orange

    for idx, (ax, case_name, color) in enumerate(zip(axes, case_studies, colors)):
        data = bev_share_data[case_name]

        if not data:
            ax.text(0.5, 0.5, 'No data', ha='center', va='center', transform=ax.transAxes)
            continue

        # Extract data
        latitudes = np.array([x[0] for x in data])
        bev_tkms = np.array([x[1] for x in data])  # BEV freight volume
        total_tkms = np.array([x[2] for x in data])

        # Calculate ICEV freight volume
        icev_tkms = total_tkms - bev_tkms

        # Convert to millions for readability
        bev_tkms_millions = bev_tkms / 1e6
        icev_tkms_millions = icev_tkms / 1e6

        # Smooth the data for continuous areas
        if len(latitudes) > 3:
            # Sort data by latitude
            sort_idx = np.argsort(latitudes)
            lat_sorted = latitudes[sort_idx]
            bev_sorted = bev_tkms_millions[sort_idx]
            icev_sorted = icev_tkms_millions[sort_idx]

            # Apply Gaussian smoothing
            bev_smoothed = gaussian_filter1d(bev_sorted, sigma=1.5)
            icev_smoothed = gaussian_filter1d(icev_sorted, sigma=1.5)

            # Create stacked areas
            # Bottom layer: ICEV (lighter shade)
            ax.fill_betweenx(lat_sorted, 0, icev_smoothed,
                            color=color, alpha=0.4, label='ICEV', zorder=2)

            # Top layer: BEV (darker shade, stacked on top of ICEV)
            ax.fill_betweenx(lat_sorted, icev_smoothed, icev_smoothed + bev_smoothed,
                            color=color, alpha=0.7, label='BEV', zorder=3)

            # Add outline for clarity
            ax.plot(icev_smoothed + bev_smoothed, lat_sorted,
                   color=color, linewidth=2, alpha=0.9, zorder=4)

        else:
            # Not enough points for smoothing - use original data
            ax.fill_betweenx(latitudes, 0, icev_tkms_millions,
                            color=color, alpha=0.4, label='ICEV', zorder=2)
            ax.fill_betweenx(latitudes, icev_tkms_millions, icev_tkms_millions + bev_tkms_millions,
                            color=color, alpha=0.7, label='BEV', zorder=3)

        # Formatting
        ax.set_xlabel('Freight Volume (Million TKM)', fontsize=13, fontweight='bold')

        # Use custom label if provided
        if case_labels and case_name in case_labels:
            title = case_labels[case_name]
        else:
            title = case_name

        ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
        ax.grid(True, alpha=0.3, linestyle='--')

        # Set x-axis limit based on data (with some padding)
        if len(icev_tkms_millions) > 0 and len(bev_tkms_millions) > 0:
            max_tkm = np.max(icev_tkms_millions + bev_tkms_millions)
            ax.set_xlim(0, max_tkm * 0.5)

        if idx == 0:
            ax.set_ylabel('Latitude (°N)', fontsize=13, fontweight='bold')
            # Add legend to first subplot
            ax.legend(loc='upper left', fontsize=11, framealpha=0.9)

    # Overall title
    fig.suptitle(f'Freight Volume by Latitude: Year {year}\nScandinavian-Mediterranean Corridor',
                 fontsize=16, fontweight='bold', y=1.02)

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
                           fontsize=11, fontweight='bold', va='center', ha='left',
                           bbox=dict(boxstyle='round,pad=0.4', facecolor='white',
                                   edgecolor='#666', alpha=0.9, linewidth=1.5),
                           zorder=10)

        print("\nCountry labels added to latitude plots")
    except Exception as e:
        print(f"\nWarning: Could not add country labels: {e}")

    plt.tight_layout()
    output_file = f'stacked_area_tkm_by_latitude_{year}.pdf'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\n[OK] Stacked area plot saved as '{output_file}'")
    plt.show()

    return bev_share_data


def analyze_bev_by_latitude_band(bev_share_data, band_width=5):
    """
    Group NUTS2 regions into latitude bands and calculate total freight volume.

    Parameters:
    -----------
    bev_share_data : list
        List of (latitude, bev_tkm, total_tkm) tuples
    band_width : int
        Width of latitude bands in degrees (default: 5)
    """
    if not bev_share_data:
        print("No data to analyze")
        return

    # Define latitude bands
    lat_min = min(x[0] for x in bev_share_data)
    lat_max = max(x[0] for x in bev_share_data)

    # Create bands
    bands = []
    current = int(lat_min / band_width) * band_width
    while current <= lat_max:
        bands.append((current, current + band_width))
        current += band_width

    print(f"{'Latitude Band':<20} {'# Regions':>12} {'BEV TKM (M)':>14} {'Total TKM (M)':>15}")
    print("-" * 70)

    for band_min, band_max in bands:
        # Filter data for this band
        band_data = [x for x in bev_share_data if band_min <= x[0] < band_max]

        if band_data:
            n_regions = len(band_data)
            total_bev_tkm = sum([x[1] for x in band_data])
            total_tkm = sum([x[2] for x in band_data])

            print(f"{band_min:2d}°N - {band_max:2d}°N{' ':<7} {n_regions:12d} {total_bev_tkm/1e6:13.1f} {total_tkm/1e6:14.1f}")


# ==============================================================================
# USAGE EXAMPLE IN JUPYTER NOTEBOOK
# ==============================================================================
"""
# Import
from bev_share_by_latitude import plot_bev_share_by_latitude_4cases, analyze_bev_by_latitude_band

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
bev_data = plot_bev_share_by_latitude_4cases(
    loaded_runs,
    case_studies,
    year=2052,
    case_labels=case_labels,
    country_centroids_csv='country_centroids.csv'
)

# Print detailed statistics for each case
print("\n" + "="*80)
print("BEV SHARE BY LATITUDE BAND")
print("="*80)

for case_name in case_studies:
    label = case_labels.get(case_name, case_name)
    print(f"\n{label}:")
    analyze_bev_by_latitude_band(bev_data[case_name])

# Compare across years
for year in [2032, 2040, 2052]:
    print(f"\n{'='*80}")
    print(f"YEAR: {year}")
    print('='*80)
    bev_data_year = plot_bev_share_by_latitude_4cases(
        loaded_runs,
        case_studies,
        year=year,
        case_labels=case_labels
    )
"""
