"""
CORRECTED: Calculate VOLUME (tonnes) by mode and technology, not flow count
"""

import matplotlib.pyplot as plt
import numpy as np

def calculate_volume_by_mode_and_tech(case_study_name, loaded_runs):
    """
    Calculate total VOLUME (tonnes) transported by mode and technology over time.

    Sums the f variable values (tonnes) by:
    - Rail
    - Road + ICEV
    - Road + BEV

    Returns:
        dict: {year: {'rail': tonnes, 'road_icev': tonnes, 'road_bev': tonnes}}
    """
    print("\n" + "="*80)
    print("CALCULATING VOLUME (TONNES) BY MODE AND TECHNOLOGY")
    print("="*80)

    # Load data
    input_data = loaded_runs[case_study_name]["input_data"]
    output_data = loaded_runs[case_study_name]["output_data"]

    f_data = output_data["f"]
    modes = input_data["Mode"]
    tech_vehicles = input_data["TechVehicle"]
    technologies = input_data["Technology"]

    # Create lookups
    tech_dict = {t['id']: t for t in technologies}

    # Identify mode IDs
    road_mode_id = None
    rail_mode_id = None

    for mode in modes:
        mode_name = mode['name'].lower().strip()
        if 'road' in mode_name:
            road_mode_id = mode['id']
        elif 'rail' in mode_name:
            rail_mode_id = mode['id']

    print(f"\nMode IDs:")
    print(f"  Road: {road_mode_id}")
    print(f"  Rail: {rail_mode_id}")

    # Map tech_vehicle_id -> 'ICEV' or 'BEV'
    tv_to_type = {}

    for tv in tech_vehicles:
        tv_id = tv['id']
        tech_id = tv.get('technology')

        if tech_id is None:
            tv_to_type[tv_id] = 'other'
            continue

        tech = tech_dict.get(tech_id)
        if tech is None:
            tv_to_type[tv_id] = 'other'
            continue

        # Check fuel directly in Technology
        fuel_name = tech.get('fuel', '').lower()

        if 'electric' in fuel_name or 'electricity' in fuel_name:
            tv_to_type[tv_id] = 'BEV'
        elif 'diesel' in fuel_name or 'gasoline' in fuel_name or 'petrol' in fuel_name or 'ice' in fuel_name:
            tv_to_type[tv_id] = 'ICEV'
        else:
            # If no clear match, check the name
            tv_name = tv.get('name', '').lower()
            if 'bev' in tv_name or 'electric' in tv_name:
                tv_to_type[tv_id] = 'BEV'
            elif 'icev' in tv_name or 'diesel' in tv_name:
                tv_to_type[tv_id] = 'ICEV'
            else:
                tv_to_type[tv_id] = 'other'

    print(f"\nTech Vehicle Types:")
    bev_tvs = [tv_id for tv_id, t in tv_to_type.items() if t == 'BEV']
    icev_tvs = [tv_id for tv_id, t in tv_to_type.items() if t == 'ICEV']
    print(f"  BEV tech vehicles: {len(bev_tvs)} - IDs: {sorted(bev_tvs)[:5]}")
    print(f"  ICEV tech vehicles: {len(icev_tvs)} - IDs: {sorted(icev_tvs)[:5]}")

    # SCALING FACTOR: f is scaled by 1000 in the model
    SCALING_FACTOR = 1000

    # Sum volumes by year
    volumes = {}

    for key, flow_value_scaled in f_data.items():
        # Key format: (year, (prod_id, odpair_id, path_id), (mode_id, tv_id), gen)
        if not isinstance(key, tuple) or len(key) < 3:
            continue

        year = key[0]

        # Extract mode_id and tv_id
        if isinstance(key[2], tuple) and len(key[2]) >= 2:
            mode_id = key[2][0]
            tv_id = key[2][1]
        else:
            continue

        # Only count flows with positive volume
        if flow_value_scaled < 1e-6:
            continue

        # Convert to actual tonnes (apply scaling)
        flow_tonnes = flow_value_scaled * SCALING_FACTOR

        # Initialize year if needed
        if year not in volumes:
            volumes[year] = {
                'rail': 0.0,
                'road_icev': 0.0,
                'road_bev': 0.0
            }

        # Add volume to appropriate category
        if mode_id == rail_mode_id:
            volumes[year]['rail'] += flow_tonnes
        elif mode_id == road_mode_id:
            tech_type = tv_to_type.get(tv_id, 'other')
            if tech_type == 'BEV':
                volumes[year]['road_bev'] += flow_tonnes
            elif tech_type == 'ICEV':
                volumes[year]['road_icev'] += flow_tonnes
            # else: other/unknown -> skip

    # Convert to sorted dict
    result = {year: volumes[year] for year in sorted(volumes.keys())}

    # DEBUG: Show first year details
    if result:
        first_year = min(result.keys())
        total = sum(result[first_year].values())
        print(f"\nDEBUG: Year {first_year} breakdown:")
        print(f"  Rail:       {result[first_year]['rail']:>12,.0f} tonnes ({result[first_year]['rail']/total*100:>5.1f}%)")
        print(f"  Road ICEV:  {result[first_year]['road_icev']:>12,.0f} tonnes ({result[first_year]['road_icev']/total*100:>5.1f}%)")
        print(f"  Road BEV:   {result[first_year]['road_bev']:>12,.0f} tonnes ({result[first_year]['road_bev']/total*100:>5.1f}%)")
        print(f"  TOTAL:      {total:>12,.0f} tonnes")

    return result


def plot_modal_split_volume(volume_data, case_name, figsize=(10, 6), max_year=2048):
    """
    Create stacked bar chart showing modal split by VOLUME (tonnes) over time.

    Args:
        volume_data: Output from calculate_volume_by_mode_and_tech()
        case_name: Case study name for title
        figsize: Figure size
        max_year: Maximum year to display (default: 2048)
    """
    fig, ax = plt.subplots(figsize=figsize)

    # Extract data and filter by max_year
    years = sorted([y for y in volume_data.keys() if y <= max_year])
    rail_volumes = [volume_data[y]['rail'] for y in years]
    road_icev_volumes = [volume_data[y]['road_icev'] for y in years]
    road_bev_volumes = [volume_data[y]['road_bev'] for y in years]

    # Calculate totals
    totals = [rail_volumes[i] + road_icev_volumes[i] + road_bev_volumes[i]
              for i in range(len(years))]

    # Convert to millions of tonnes for better readability
    rail_mt = np.array([v / 1e6 for v in rail_volumes])
    icev_mt = np.array([v / 1e6 for v in road_icev_volumes])
    bev_mt = np.array([v / 1e6 for v in road_bev_volumes])

    # Bar width
    width = 1.5  # Adjust based on year spacing

    # Create stacked bar chart
    p1 = ax.bar(years, rail_mt, width, label='Rail',
                color='#669bbc', alpha=0.9, edgecolor='white', linewidth=0.5)

    p2 = ax.bar(years, icev_mt, width, bottom=rail_mt, label='Road (ICEV)',
                color='#dc2f02', alpha=0.6, edgecolor='white', linewidth=0.5)

    p3 = ax.bar(years, bev_mt, width, bottom=rail_mt + icev_mt, label='Road (BEV)',
                color='#74c69d', alpha=0.9, edgecolor='white', linewidth=0.5)

    # Formatting
    ax.set_xlabel('Year', fontsize=14, fontweight='bold')
    ax.set_ylabel('Freight Volume (Million Tonnes)', fontsize=14, fontweight='bold')
    ax.set_title('Shift to rail and adoption of Battery Electric Vehicles by Volume\nScandinavian-Mediterranean Corridor',
                fontsize=16, fontweight='bold', pad=20)

    ax.legend(loc='upper left', fontsize=14, framealpha=0.9)
    ax.grid(True, alpha=0.3, linestyle='--', axis='x')
    ax.set_axisbelow(True)

    # Add percentage labels for selected years
    label_years = years[::4]  # Every 4th year for bar charts
    for year in label_years:
        if year in volume_data:
            idx = years.index(year)
            total = totals[idx]

            if total == 0:
                continue

            rail_pct = rail_volumes[idx] / total * 100
            icev_pct = road_icev_volumes[idx] / total * 100
            bev_pct = road_bev_volumes[idx] / total * 100

            # Add text labels (using Mt values for positioning)
            y_pos_rail = rail_mt[idx] / 2
            y_pos_icev = rail_mt[idx] + icev_mt[idx] / 2
            y_pos_bev = rail_mt[idx] + icev_mt[idx] + bev_mt[idx] / 2

            # if rail_pct > 5:  # Only show if >5%
            #     ax.text(year, y_pos_rail, f'{rail_pct:.0f}%',
            #            ha='center', va='center', fontsize=9, fontweight='bold',
            #            color='white')

            # if icev_pct > 5:
            #     ax.text(year, y_pos_icev, f'{icev_pct:.0f}%',
            #            ha='center', va='center', fontsize=9, fontweight='bold',
            #            color='white')

            # if bev_pct > 5:
            #     ax.text(year, y_pos_bev, f'{bev_pct:.0f}%',
            #            ha='center', va='center', fontsize=9, fontweight='bold',
            #            color='white')

    # Set x-axis to show every year
    ax.set_xticks(years)
    ax.set_xticklabels(years, rotation=45, ha='right', fontsize=12)

    plt.tight_layout()
    plt.savefig(f'modal_split_volume.svg', bbox_inches='tight')
    plt.show()

    print(f"\nFigure saved as: modal_split_volume_{case_name}.png")


def print_volume_summary(volume_data):
    """
    Print summary statistics of volumes.

    Args:
        volume_data: Output from calculate_volume_by_mode_and_tech()
    """
    print("\n" + "="*80)
    print("VOLUME SUMMARY BY YEAR (Million Tonnes)")
    print("="*80)

    for year in sorted(volume_data.keys()):
        rail = volume_data[year]['rail']
        road_icev = volume_data[year]['road_icev']
        road_bev = volume_data[year]['road_bev']
        total = rail + road_icev + road_bev

        if total == 0:
            continue

        rail_pct = rail / total * 100
        icev_pct = road_icev / total * 100
        bev_pct = road_bev / total * 100

        print(f"\nYear {year}:")
        print(f"  Total volume: {total/1e6:>8.2f} Mt")
        print(f"  Rail:         {rail/1e6:>8.2f} Mt ({rail_pct:>5.1f}%)")
        print(f"  Road (ICEV):  {road_icev/1e6:>8.2f} Mt ({icev_pct:>5.1f}%)")
        print(f"  Road (BEV):   {road_bev/1e6:>8.2f} Mt ({bev_pct:>5.1f}%)")


# ==============================================================================
# USAGE
# ==============================================================================
"""
# In your notebook, replace the flow count functions with these:
volume_data = calculate_volume_by_mode_and_tech(case_name, loaded_runs)
print_volume_summary(volume_data)
plot_modal_split_volume(volume_data, case_name)
"""
