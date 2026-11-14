"""
FIXED VERSION: Calculate flow counts by mode and technology
"""

import matplotlib.pyplot as plt
import numpy as np

def calculate_flow_count_by_mode_and_tech(case_study_name, loaded_runs):
    """
    Calculate number of active flows by mode and technology over time.
    FIXED: Correctly identifies ICEV vs BEV using the same logic as calculate_road_technology_split()

    Returns:
        dict: {year: {'rail': count, 'road_icev': count, 'road_bev': count}}
    """
    print("\n" + "="*80)
    print("CALCULATING FLOW COUNTS BY MODE AND TECHNOLOGY")
    print("="*80)

    # Load data
    input_data = loaded_runs[case_study_name]["input_data"]
    output_data = loaded_runs[case_study_name]["output_data"]

    f_data = output_data["f"]
    modes = input_data["Mode"]
    tech_vehicles = input_data["TechVehicle"]
    technologies = input_data["Technology"]

    # Create lookups
    mode_dict = {m['id']: m for m in modes}
    tv_dict = {tv['id']: tv for tv in tech_vehicles}
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

    # FIXED: Map tech_vehicle_id -> 'ICEV' or 'BEV' using Technology -> fuel lookup
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

        # Check fuel directly in Technology (not via Fuel lookup)
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

    # Count flows by year
    flow_counts = {}

    # DEBUG: Sample some keys
    sample_keys = list(f_data.keys())[:5]
    print(f"\nDEBUG: Sample flow keys:")
    for k in sample_keys:
        print(f"  {k}")

    for key, flow_value in f_data.items():
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

        # Only count flows with positive volume (use small threshold)
        if flow_value < 1e-6:
            continue

        # Initialize year if needed
        if year not in flow_counts:
            flow_counts[year] = {
                'rail': set(),
                'road_icev': set(),
                'road_bev': set()
            }

        # Create unique flow identifier (odpair_id, path_id)
        if isinstance(key[1], tuple) and len(key[1]) >= 3:
            odpair_id = key[1][1]
            path_id = key[1][2]
            flow_id = (odpair_id, path_id)
        else:
            continue

        # Categorize flow
        if mode_id == rail_mode_id:
            flow_counts[year]['rail'].add(flow_id)
        elif mode_id == road_mode_id:
            tech_type = tv_to_type.get(tv_id, 'other')
            if tech_type == 'BEV':
                flow_counts[year]['road_bev'].add(flow_id)
            elif tech_type == 'ICEV':
                flow_counts[year]['road_icev'].add(flow_id)
            # else: other/unknown -> skip

    # Convert sets to counts
    result = {}
    for year in sorted(flow_counts.keys()):
        result[year] = {
            'rail': len(flow_counts[year]['rail']),
            'road_icev': len(flow_counts[year]['road_icev']),
            'road_bev': len(flow_counts[year]['road_bev'])
        }

    # DEBUG: Show first year details
    if result:
        first_year = min(result.keys())
        print(f"\nDEBUG: Year {first_year} breakdown:")
        print(f"  Rail flows: {result[first_year]['rail']}")
        print(f"  Road ICEV flows: {result[first_year]['road_icev']}")
        print(f"  Road BEV flows: {result[first_year]['road_bev']}")

    return result


def plot_modal_split_flow_count(flow_data, case_name, figsize=(14, 8)):
    """
    Create stacked area chart showing modal split by flow count over time.

    Args:
        flow_data: Output from calculate_flow_count_by_mode_and_tech()
        case_name: Case study name for title
        figsize: Figure size
    """
    fig, ax = plt.subplots(figsize=figsize)

    # Extract data
    years = sorted(flow_data.keys())
    rail_counts = [flow_data[y]['rail'] for y in years]
    road_icev_counts = [flow_data[y]['road_icev'] for y in years]
    road_bev_counts = [flow_data[y]['road_bev'] for y in years]

    # Calculate totals
    totals = [rail_counts[i] + road_icev_counts[i] + road_bev_counts[i]
              for i in range(len(years))]

    # Create stacked area plot
    ax.fill_between(years, 0, rail_counts,
                     label='Rail', color='#3498DB', alpha=0.8)

    ax.fill_between(years, rail_counts,
                     [rail_counts[i] + road_icev_counts[i] for i in range(len(years))],
                     label='Road (ICEV)', color='#E74C3C', alpha=0.8)

    ax.fill_between(years,
                     [rail_counts[i] + road_icev_counts[i] for i in range(len(years))],
                     totals,
                     label='Road (BEV)', color='#2ECC71', alpha=0.8)

    # Formatting
    ax.set_xlabel('Year', fontsize=12, fontweight='bold')
    ax.set_ylabel('Number of Active Flows', fontsize=12, fontweight='bold')
    ax.set_title('Modal Split by Flow Count\nScandinavian-Mediterranean Corridor',
                fontsize=14, fontweight='bold', pad=20)

    ax.legend(loc='upper left', fontsize=11, framealpha=0.9)
    ax.grid(True, alpha=0.3, linestyle='--')

    # Add percentage labels for selected years
    label_years = years[::8]  # Every 8th year
    for year in label_years:
        if year in flow_data:
            idx = years.index(year)
            total = totals[idx]

            if total == 0:
                continue

            rail_pct = rail_counts[idx] / total * 100
            icev_pct = road_icev_counts[idx] / total * 100
            bev_pct = road_bev_counts[idx] / total * 100

            # Add text labels
            y_pos_rail = rail_counts[idx] / 2
            y_pos_icev = rail_counts[idx] + road_icev_counts[idx] / 2
            y_pos_bev = rail_counts[idx] + road_icev_counts[idx] + road_bev_counts[idx] / 2

            if rail_pct > 3:  # Only show if >3%
                ax.text(year, y_pos_rail, f'{rail_pct:.1f}%',
                       ha='center', va='center', fontsize=9,
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))

            if icev_pct > 3:
                ax.text(year, y_pos_icev, f'{icev_pct:.1f}%',
                       ha='center', va='center', fontsize=9,
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))

            if bev_pct > 3:
                ax.text(year, y_pos_bev, f'{bev_pct:.1f}%',
                       ha='center', va='center', fontsize=9,
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))

    plt.tight_layout()
    plt.savefig(f'modal_split_flow_count_{case_name}.png', dpi=300, bbox_inches='tight')
    plt.show()

    print(f"\nFigure saved as: modal_split_flow_count_{case_name}.png")


def print_flow_count_summary(flow_data):
    """
    Print summary statistics of flow counts.

    Args:
        flow_data: Output from calculate_flow_count_by_mode_and_tech()
    """
    print("\n" + "="*80)
    print("FLOW COUNT SUMMARY BY YEAR")
    print("="*80)

    for year in sorted(flow_data.keys()):
        rail = flow_data[year]['rail']
        road_icev = flow_data[year]['road_icev']
        road_bev = flow_data[year]['road_bev']
        total = rail + road_icev + road_bev

        if total == 0:
            continue

        rail_pct = rail / total * 100
        icev_pct = road_icev / total * 100
        bev_pct = road_bev / total * 100

        print(f"\nYear {year}:")
        print(f"  Total flows: {total:,}")
        print(f"  Rail:        {rail:6,} ({rail_pct:5.1f}%)")
        print(f"  Road (ICEV): {road_icev:6,} ({icev_pct:5.1f}%)")
        print(f"  Road (BEV):  {road_bev:6,} ({bev_pct:5.1f}%)")


# ==============================================================================
# USAGE
# ==============================================================================
"""
# Replace the functions in your notebook with these fixed versions
flow_count_data = calculate_flow_count_by_mode_and_tech(case_name, loaded_runs)
print_flow_count_summary(flow_count_data)
plot_modal_split_flow_count(flow_count_data, case_name)
"""
