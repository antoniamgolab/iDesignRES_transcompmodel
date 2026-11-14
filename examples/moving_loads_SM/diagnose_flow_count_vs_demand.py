"""
Diagnostic: Compare flow count vs demand growth

Compares:
1. Total F (demand) from Odpair input by year
2. Total flow volume from output f data by year
3. Flow count (number of active routes) by year

This helps understand if flow count behavior is correct or if there's a bug.
"""

import yaml
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

def diagnose_flow_count_vs_demand(case_study_name, loaded_runs):
    """
    Compare demand growth vs flow count growth.
    """
    print("\n" + "="*80)
    print("DIAGNOSTIC: FLOW COUNT VS DEMAND GROWTH")
    print("="*80)

    # Load data
    input_data = loaded_runs[case_study_name]["input_data"]
    output_data = loaded_runs[case_study_name]["output_data"]

    odpairs = input_data["Odpair"]
    f_data = output_data["f"]
    modes = input_data["Mode"]
    tech_vehicles = input_data["TechVehicle"]
    technologies = input_data["Technology"]

    # Get years from first odpair
    years = list(range(len(odpairs[0]['F'])))

    # Check if years in output data are indices or actual years
    sample_year = list(f_data.keys())[0][0] if f_data else 0
    if sample_year >= 2000:  # Likely actual years
        actual_years = None  # We'll use years directly from output
        use_actual_years = True
    else:  # Indices
        actual_years = [2022 + i for i in years]  # Adjust base year if needed
        use_actual_years = False

    print(f"\nYears in data: {len(years)} years (input)")
    print(f"  Input year indices: {min(years)} to {max(years)}")
    if not use_actual_years:
        print(f"  Actual years: {min(actual_years)} to {max(actual_years)}")

    # === 1. Calculate total input demand (F) by year ===
    print("\n" + "-"*80)
    print("1. TOTAL INPUT DEMAND (F) BY YEAR")
    print("-"*80)

    total_input_demand = {}
    for year_idx in years:
        total_f = sum(odpair['F'][year_idx] for odpair in odpairs)
        total_input_demand[year_idx] = total_f

    for year_idx in sorted(total_input_demand.keys())[::5]:  # Every 5th year
        year_display = year_idx if use_actual_years else actual_years[year_idx]
        print(f"  Year {year_display}: {total_input_demand[year_idx]:,.0f} tonnes")

    # Calculate growth
    first_year_demand = total_input_demand[min(years)]
    last_year_demand = total_input_demand[max(years)]
    demand_growth = (last_year_demand / first_year_demand - 1) * 100
    first_year_display = min(years) if use_actual_years else actual_years[min(years)]
    last_year_display = max(years) if use_actual_years else actual_years[max(years)]
    print(f"\n  Growth from {first_year_display} to {last_year_display}: {demand_growth:+.1f}%")

    # === 2. Calculate total output flow volume by year ===
    print("\n" + "-"*80)
    print("2. TOTAL OUTPUT FLOW VOLUME BY YEAR")
    print("-"*80)

    total_output_volume = {}

    for key, flow_value in f_data.items():
        if not isinstance(key, tuple) or len(key) < 1:
            continue

        year = key[0]

        if year not in total_output_volume:
            total_output_volume[year] = 0.0

        total_output_volume[year] += flow_value

    for year in sorted(total_output_volume.keys())[::5]:  # Every 5th year
        print(f"  Year {year}: {total_output_volume[year]:,.0f} tonnes")

    # Calculate growth
    first_year_output = total_output_volume[min(total_output_volume.keys())]
    last_year_output = total_output_volume[max(total_output_volume.keys())]
    output_growth = (last_year_output / first_year_output - 1) * 100
    print(f"\n  Growth: {output_growth:+.1f}%")

    # === 3. Calculate flow count by year ===
    print("\n" + "-"*80)
    print("3. FLOW COUNT (ACTIVE ROUTES) BY YEAR")
    print("-"*80)

    # Create lookups for mode categorization
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

        fuel_name = tech.get('fuel', '').lower()

        if 'electric' in fuel_name or 'electricity' in fuel_name:
            tv_to_type[tv_id] = 'BEV'
        elif 'diesel' in fuel_name or 'gasoline' in fuel_name or 'petrol' in fuel_name or 'ice' in fuel_name:
            tv_to_type[tv_id] = 'ICEV'
        else:
            tv_name = tv.get('name', '').lower()
            if 'bev' in tv_name or 'electric' in tv_name:
                tv_to_type[tv_id] = 'BEV'
            elif 'icev' in tv_name or 'diesel' in tv_name:
                tv_to_type[tv_id] = 'ICEV'
            else:
                tv_to_type[tv_id] = 'other'

    # Count flows by year
    flow_counts = {}
    flow_volumes = {}  # Track volume per category too

    for key, flow_value in f_data.items():
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
        if flow_value < 1e-6:
            continue

        # Initialize year if needed
        if year not in flow_counts:
            flow_counts[year] = {
                'rail': set(),
                'road_icev': set(),
                'road_bev': set()
            }
            flow_volumes[year] = {
                'rail': 0.0,
                'road_icev': 0.0,
                'road_bev': 0.0
            }

        # Create unique flow identifier
        if isinstance(key[1], tuple) and len(key[1]) >= 3:
            odpair_id = key[1][1]
            path_id = key[1][2]
            flow_id = (odpair_id, path_id)
        else:
            continue

        # Categorize flow
        if mode_id == rail_mode_id:
            flow_counts[year]['rail'].add(flow_id)
            flow_volumes[year]['rail'] += flow_value
        elif mode_id == road_mode_id:
            tech_type = tv_to_type.get(tv_id, 'other')
            if tech_type == 'BEV':
                flow_counts[year]['road_bev'].add(flow_id)
                flow_volumes[year]['road_bev'] += flow_value
            elif tech_type == 'ICEV':
                flow_counts[year]['road_icev'].add(flow_id)
                flow_volumes[year]['road_icev'] += flow_value

    # Convert sets to counts
    flow_count_by_year = {}
    for year in sorted(flow_counts.keys()):
        total_count = (len(flow_counts[year]['rail']) +
                      len(flow_counts[year]['road_icev']) +
                      len(flow_counts[year]['road_bev']))
        flow_count_by_year[year] = {
            'total': total_count,
            'rail': len(flow_counts[year]['rail']),
            'road_icev': len(flow_counts[year]['road_icev']),
            'road_bev': len(flow_counts[year]['road_bev'])
        }

    for year in sorted(flow_count_by_year.keys())[::5]:  # Every 5th year
        counts = flow_count_by_year[year]
        print(f"  Year {year}: {counts['total']:,} flows " +
              f"(Rail: {counts['rail']}, ICEV: {counts['road_icev']}, BEV: {counts['road_bev']})")

    # Calculate growth
    first_year_count = flow_count_by_year[min(flow_count_by_year.keys())]['total']
    last_year_count = flow_count_by_year[max(flow_count_by_year.keys())]['total']
    count_growth = (last_year_count / first_year_count - 1) * 100
    print(f"\n  Growth: {count_growth:+.1f}%")

    # === 4. Compare metrics ===
    print("\n" + "="*80)
    print("COMPARISON")
    print("="*80)

    output_years = sorted(total_output_volume.keys())
    print(f"\nGrowth rates from {output_years[0]} to {output_years[-1]}:")
    print(f"  Input demand (F):     {demand_growth:+6.1f}%")
    print(f"  Output flow volume:   {output_growth:+6.1f}%")
    print(f"  Flow count:           {count_growth:+6.1f}%")

    print("\n" + "-"*80)
    print("INTERPRETATION")
    print("-"*80)

    # Check if demand and output match
    demand_diff = abs(demand_growth - output_growth)
    if demand_diff < 1.0:
        print("\n[OK] Input demand matches output volume - model conserves mass")
    else:
        print(f"\n[WARNING] Input demand ({demand_growth:+.1f}%) differs from output volume ({output_growth:+.1f}%)")
        print("  This might indicate an issue with the model or data processing")

    # Explain flow count behavior
    print(f"\nFlow count growth ({count_growth:+.1f}%) vs demand growth ({demand_growth:+.1f}%):")

    if abs(count_growth - demand_growth) < 5.0:
        print("  [INFO] Flow count grows proportionally with demand")
        print("  This means new routes are being activated as demand grows")
    elif count_growth < demand_growth:
        print("  [INFO] Flow count grows slower than demand")
        print("  This is NORMAL and means:")
        print("    - Existing routes handle more freight (route consolidation)")
        print("    - The model is efficiently using available capacity")
        print("    - Economies of scale in route utilization")
    else:
        print("  [INFO] Flow count grows faster than demand")
        print("  This means:")
        print("    - More routes are being activated")
        print("    - Freight is being distributed across more paths")
        print("    - Might indicate modal/technology shifts opening new routes")

    # === 5. Calculate average flow volume ===
    print("\n" + "-"*80)
    print("AVERAGE FLOW VOLUME PER ROUTE")
    print("-"*80)

    print("\nYear | Avg Volume (tonnes/route) | Total Volume | Route Count")
    print("-" * 70)

    for year in sorted(flow_count_by_year.keys())[::5]:
        total_vol = total_output_volume[year]
        total_count = flow_count_by_year[year]['total']
        avg_vol = total_vol / total_count if total_count > 0 else 0
        print(f"{year} | {avg_vol:>24,.0f} | {total_vol:>12,.0f} | {total_count:>11,}")

    # === 6. Volume by category ===
    print("\n" + "-"*80)
    print("VOLUME BY MODE/TECHNOLOGY")
    print("-"*80)

    print("\nShowing first, middle, and last year:")
    years_to_show = [min(flow_volumes.keys()),
                     min(flow_volumes.keys()) + len(flow_volumes)//2,
                     max(flow_volumes.keys())]

    for year in years_to_show:
        if year in flow_volumes:
            vols = flow_volumes[year]
            total_vol = vols['rail'] + vols['road_icev'] + vols['road_bev']

            rail_pct = vols['rail'] / total_vol * 100 if total_vol > 0 else 0
            icev_pct = vols['road_icev'] / total_vol * 100 if total_vol > 0 else 0
            bev_pct = vols['road_bev'] / total_vol * 100 if total_vol > 0 else 0

            print(f"\nYear {year}:")
            print(f"  Total volume: {total_vol:,.0f} tonnes")
            print(f"    Rail:       {vols['rail']:>12,.0f} ({rail_pct:>5.1f}%)")
            print(f"    Road ICEV:  {vols['road_icev']:>12,.0f} ({icev_pct:>5.1f}%)")
            print(f"    Road BEV:   {vols['road_bev']:>12,.0f} ({bev_pct:>5.1f}%)")

    print("\n" + "="*80)

    return {
        'years': output_years,
        'input_demand': total_input_demand,
        'output_volume': total_output_volume,
        'flow_counts': flow_count_by_year,
        'flow_volumes': flow_volumes
    }


# ==============================================================================
# STANDALONE EXECUTION
# ==============================================================================

if __name__ == "__main__":
    from pathlib import Path

    print("\n" + "="*80)
    print("ERROR: This script requires data from modal_shift.ipynb")
    print("="*80)
    print("\nThe results data structure is already loaded in your notebook.")
    print("\nTo run this diagnostic:")
    print("  1. Open modal_shift.ipynb")
    print("  2. Make sure you've run the cells that load the data (loaded_runs)")
    print("  3. Copy the diagnose_flow_count_vs_demand() function into a cell")
    print("  4. Run: diagnostic_data = diagnose_flow_count_vs_demand(case_name, loaded_runs)")
    print("\nOr, if you want to use this as a standalone script, you need to")
    print("tell me which case you want to analyze from the results/ directory.")
    print("\n" + "="*80)

    # Show available cases
    results_dir = Path("results")
    if results_dir.exists():
        case_dirs = [d for d in results_dir.iterdir() if d.is_dir() and d.name.startswith("case_")]
        case_dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        if case_dirs:
            print(f"\nAvailable cases in results/ (showing 10 most recent):")
            for i, case_dir in enumerate(case_dirs[:10]):
                print(f"  {i+1}. {case_dir.name}")
            print("\nMost recent: " + case_dirs[0].name)

    print("\n" + "="*80)

# ==============================================================================
# USAGE IN NOTEBOOK
# ==============================================================================
"""
# In your notebook:
diagnostic_data = diagnose_flow_count_vs_demand(case_name, loaded_runs)
"""
