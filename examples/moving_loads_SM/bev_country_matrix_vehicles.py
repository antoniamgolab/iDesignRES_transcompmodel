"""
Create BEV country-to-country VEHICLE matrix (using h variable)

This version uses the h variable (absolute vehicle counts) instead of f (freight flows)
"""
import pandas as pd
import numpy as np


def _find_odpairs_and_geo(loaded_runs):
    """Extract odpair and geographic element mappings"""
    odpair_map = {}
    geoid2country = {}

    for case_name, case in loaded_runs.items():
        inp = case.get("input_data", {}) or {}

        # Geographic elements
        geo_data = inp.get("GeographicElement") or inp.get("GeographicElements")
        if geo_data and isinstance(geo_data, list):
            for entry in geo_data:
                if not isinstance(entry, dict):
                    continue
                geo_id = entry.get('id')
                country = entry.get('country')
                if geo_id is not None and country is not None:
                    try:
                        geoid2country[int(geo_id)] = str(country)
                    except (ValueError, TypeError):
                        pass

        # Odpairs
        odpair_data = inp.get("Odpair") or inp.get("odpairs")
        if odpair_data and isinstance(odpair_data, list):
            for entry in odpair_data:
                if not isinstance(entry, dict):
                    continue
                odpair_id = entry.get('id')
                origin = entry.get('from')
                dest = entry.get('to')
                if odpair_id is not None and origin is not None and dest is not None:
                    try:
                        odpair_map[int(odpair_id)] = (int(origin), int(dest))
                    except (ValueError, TypeError):
                        pass

    return odpair_map, geoid2country


def _find_electric_tech_ids(loaded_runs):
    """
    Find tech vehicle IDs that are BEVs (electricity fuel)
    """
    electric_ids = set()

    for case in loaded_runs.values():
        inp = case.get("input_data", {}) or {}

        # Load Technology table (maps technology_id -> fuel)
        tech_data = inp.get("Technology") or inp.get("technology")
        if not tech_data:
            continue

        # Create mapping: technology_id -> fuel_name
        tech_to_fuel = {}
        if isinstance(tech_data, list):
            for tech in tech_data:
                if isinstance(tech, dict):
                    tech_id = tech.get('id')
                    fuel = tech.get('fuel', '').lower()
                    if tech_id is not None:
                        tech_to_fuel[int(tech_id)] = fuel

        # Load TechVehicle table
        tv_data = inp.get("TechVehicle") or inp.get("techvehicle")
        if not tv_data:
            continue

        if isinstance(tv_data, list):
            for tv in tv_data:
                if not isinstance(tv, dict):
                    continue

                tv_id = tv.get('id')
                tech_id = tv.get('technology')

                if tv_id is None or tech_id is None:
                    continue

                # Look up fuel from technology mapping
                fuel_name = tech_to_fuel.get(int(tech_id), 'unknown')

                # Check if electric
                if 'electricity' in fuel_name or 'electric' in fuel_name:
                    electric_ids.add(int(tv_id))

    return electric_ids


def create_bev_vehicle_matrix(loaded_runs, target_year=2030, case_name=None):
    """
    Create a country-to-country BEV VEHICLE COUNT matrix for a specific year

    Uses h variable (absolute vehicles) instead of f (freight flows)

    Args:
        loaded_runs: Dictionary of loaded case data
        target_year: Year to analyze (default: 2030)
        case_name: Specific case to analyze (default: first case)

    Returns:
        DataFrame: Country-to-country matrix of BEV vehicle counts
    """
    print("="*80)
    print("CREATING BEV VEHICLE COUNT MATRIX (using h variable)")
    print("="*80)

    # Get mappings
    print("\nStep 1: Loading geographic and odpair mappings...")
    odpair_map, geoid2country = _find_odpairs_and_geo(loaded_runs)
    print(f"  Found {len(odpair_map)} odpairs")
    print(f"  Found {len(geoid2country)} geographic elements")

    print("\nStep 2: Identifying BEV tech vehicles...")
    electric_ids = _find_electric_tech_ids(loaded_runs)
    print(f"  Found {len(electric_ids)} BEV tech vehicle IDs: {electric_ids}")

    if not electric_ids:
        print("  ERROR: No BEV tech vehicles identified!")
        return pd.DataFrame()

    # Select case
    if case_name is None:
        case_name = list(loaded_runs.keys())[0]
    print(f"\nStep 3: Processing case '{case_name}'...")

    case_data = loaded_runs[case_name]
    output_data = case_data.get("output_data", {})

    # Get VEHICLE data (h variable)
    h_data = output_data.get("h", {})
    if not h_data:
        print("  ERROR: No vehicle data (h) found!")
        return pd.DataFrame()

    print(f"  Found {len(h_data)} vehicle entries")

    # Aggregate vehicles by origin_country -> dest_country
    print(f"\nStep 4: Filtering for year={target_year} and BEV vehicles...")
    country_vehicles = {}  # (origin_country, dest_country) -> total_vehicles

    vehicles_found = 0
    for vehicle_key, vehicle_count in h_data.items():
        if not isinstance(vehicle_key, tuple) or len(vehicle_key) < 4:
            continue

        # h variable structure: (year, route_id, tech_vehicle_id, generation_year)
        year = vehicle_key[0]
        route_id = vehicle_key[1]
        tv_id = vehicle_key[2]
        gen_year = vehicle_key[3]

        if year != target_year:
            continue

        # Filter for BEVs
        if tv_id not in electric_ids:
            continue

        vehicles_found += 1

        # Get origin and destination from odpair
        # route_id appears to be the odpair_id
        if route_id not in odpair_map:
            continue

        origin_geoid, dest_geoid = odpair_map[route_id]

        # Get countries
        origin_country = geoid2country.get(origin_geoid)
        dest_country = geoid2country.get(dest_geoid)

        if origin_country is None or dest_country is None:
            continue

        # Aggregate vehicle counts
        key = (origin_country, dest_country)
        country_vehicles[key] = country_vehicles.get(key, 0.0) + vehicle_count

    print(f"  Found {vehicles_found} BEV vehicle entries for year {target_year}")
    print(f"  Aggregated into {len(country_vehicles)} country-to-country pairs")

    # Create matrix
    if not country_vehicles:
        print("  WARNING: No country-level vehicles after aggregation!")
        return pd.DataFrame()

    # Get all countries
    all_countries = set()
    for (orig, dest) in country_vehicles.keys():
        all_countries.add(orig)
        all_countries.add(dest)

    all_countries = sorted(all_countries)
    print(f"  Countries: {all_countries}")

    # Create matrix
    matrix = pd.DataFrame(
        np.zeros((len(all_countries), len(all_countries))),
        index=all_countries,
        columns=all_countries
    )

    for (orig, dest), vehicle_count in country_vehicles.items():
        matrix.loc[orig, dest] = vehicle_count

    print(f"\n✓ Matrix created successfully!")
    print(f"  Shape: {matrix.shape}")
    print(f"  Total vehicles: {matrix.sum().sum():.2f}")
    print("="*80)

    return matrix


def create_bev_vehicle_matrices_all_cases(loaded_runs, target_year=2030):
    """
    Create BEV vehicle count matrices for all cases

    Returns:
        dict: {case_name: matrix_dataframe}
    """
    results = {}

    print("="*80)
    print(f"CREATING BEV VEHICLE MATRICES FOR ALL CASES (Year: {target_year})")
    print("="*80)

    for case_name in loaded_runs.keys():
        print(f"\n--- Processing: {case_name} ---")
        matrix = create_bev_vehicle_matrix(loaded_runs, target_year=target_year, case_name=case_name)
        results[case_name] = matrix

    return results


def compare_bev_vehicle_matrices(matrices_dict):
    """
    Compare BEV vehicle counts across different cases

    Args:
        matrices_dict: {case_name: matrix_df} from create_bev_vehicle_matrices_all_cases()

    Returns:
        DataFrame with comparison
    """
    comparison = {}

    for case_name, matrix in matrices_dict.items():
        if matrix.empty:
            comparison[case_name] = {'total': 0, 'diagonal': 0, 'cross_border': 0}
            continue

        total_vehicles = matrix.sum().sum()
        diagonal_vehicles = sum(matrix.loc[c, c] for c in matrix.index if c in matrix.columns)
        cross_border_vehicles = total_vehicles - diagonal_vehicles

        comparison[case_name] = {
            'total': total_vehicles,
            'diagonal': diagonal_vehicles,
            'cross_border': cross_border_vehicles,
            'cross_border_pct': (cross_border_vehicles / total_vehicles * 100) if total_vehicles > 0 else 0
        }

    return pd.DataFrame(comparison).T


def plot_bev_vehicle_matrices_comparison(matrices_dict, figsize=(15, 10), case_labels=None, year=2030):
    """
    Create side-by-side heatmaps for all cases (vehicle counts)

    Args:
        matrices_dict: {case_name: matrix_df} from create_bev_vehicle_matrices_all_cases()
        figsize: Figure size (width, height)
        case_labels: Optional dict mapping case_name -> display_label
    """
    import matplotlib.pyplot as plt
    import seaborn as sns

    n_cases = len(matrices_dict)

    # Filter out empty matrices
    valid_matrices = {k: v for k, v in matrices_dict.items() if not v.empty}
    n_valid = len(valid_matrices)

    if n_valid == 0:
        print("No valid matrices to plot!")
        return

    # Calculate layout
    n_cols = min(2, n_valid)  # Max 2 columns
    n_rows = (n_valid + n_cols - 1) // n_cols

    fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize)
    if n_valid == 1:
        axes = [axes]
    else:
        axes = axes.flatten() if n_valid > 1 else [axes]

    # Find global min/max for consistent color scale
    all_values = []
    for matrix in valid_matrices.values():
        all_values.extend(matrix.values.flatten())
    vmin, vmax = min(all_values), max(all_values)

    for idx, (case_name, matrix) in enumerate(valid_matrices.items()):
        ax = axes[idx]

        sns.heatmap(matrix, annot=True, fmt='.0f', cmap='YlOrRd',
                    vmin=vmin, vmax=vmax,
                    cbar_kws={'label': 'BEV Vehicle Count'},
                    ax=ax)

        # Use custom label if provided, otherwise use case_name
        display_label = case_labels.get(case_name, case_name) if case_labels else case_name

        ax.set_title(f'{display_label}\nTotal: {matrix.sum().sum():.0f} vehicles', fontsize=10)
        ax.set_xlabel('Destination Country')
        ax.set_ylabel('Origin Country')

    # Hide unused subplots
    for idx in range(n_valid, len(axes)):
        axes[idx].axis('off')

    plt.tight_layout()
    plt.savefig(f'bev_vehicle_matrices_comparison_{year}.pdf')
    plt.show()


# =============================================================================
# USAGE IN JUPYTER NOTEBOOK
# =============================================================================
"""
# Import
from bev_country_matrix_vehicles import create_bev_vehicle_matrix, create_bev_vehicle_matrices_all_cases, compare_bev_vehicle_matrices, plot_bev_vehicle_matrices_comparison

# Single case, single year
bev_vehicle_matrix_2030 = create_bev_vehicle_matrix(loaded_runs, target_year=2030)
print(bev_vehicle_matrix_2030)

# Visualize
import matplotlib.pyplot as plt
import seaborn as sns

if not bev_vehicle_matrix_2030.empty:
    plt.figure(figsize=(12, 10))
    sns.heatmap(bev_vehicle_matrix_2030, annot=True, fmt='.0f', cmap='YlOrRd',
                cbar_kws={'label': 'BEV Vehicle Count'})
    plt.title(f'BEV Vehicle Counts by Country (2030)')
    plt.xlabel('Destination Country')
    plt.ylabel('Origin Country')
    plt.tight_layout()
    plt.show()

# All cases comparison
case_study_name_labels = {
    "case_20251107_105426_rail": "Base case",
    # Add your other cases here
}

vehicle_matrices_2030 = create_bev_vehicle_matrices_all_cases(loaded_runs, target_year=2030)
comparison = compare_bev_vehicle_matrices(vehicle_matrices_2030)
print("\nCOMPARISON ACROSS CASES:")
print(comparison)

# Plot comparison
plot_bev_vehicle_matrices_comparison(vehicle_matrices_2030, case_labels=case_study_name_labels)

# Multiple years
for year in [2030, 2040, 2050]:
    print(f"\n{'='*80}")
    print(f"YEAR: {year}")
    print('='*80)
    vehicle_matrices = create_bev_vehicle_matrices_all_cases(loaded_runs, target_year=year)
    comparison = compare_bev_vehicle_matrices(vehicle_matrices)
    print(comparison)
    plot_bev_vehicle_matrices_comparison(vehicle_matrices, case_labels=case_study_name_labels)
"""
