"""
Analyze freight flows involving Italy: origin and destination countries
"""

import yaml
from pathlib import Path
from collections import defaultdict
import pandas as pd

def analyze_italy_freight(case_name, loaded_runs, year=2040):
    """
    Analyze freight flows involving Italy by origin/destination country.

    Args:
        case_name: Case study name
        loaded_runs: Loaded data dictionary
        year: Year to analyze (default: 2040)
    """
    print("\n" + "="*80)
    print(f"ANALYZING ITALY FREIGHT FLOWS - YEAR {year}")
    print("="*80)

    # Load data
    input_data = loaded_runs[case_name]["input_data"]
    output_data = loaded_runs[case_name]["output_data"]

    f_data = output_data["f"]
    odpairs = input_data["Odpair"]
    geo_elements = input_data["GeographicElement"]

    # Create geo_id -> NUTS2 mapping
    geo_to_nuts2 = {}
    for geo in geo_elements:
        if geo['type'] == 'node' and 'nuts2_region' in geo and geo['nuts2_region']:
            geo_to_nuts2[geo['id']] = geo['nuts2_region']

    # Create odpair_id -> (origin_geo, dest_geo) mapping
    odpair_to_geo = {}
    for odpair in odpairs:
        odpair_id = odpair['id']
        origin_geo = odpair.get('origin')
        dest_geo = odpair.get('destination')
        odpair_to_geo[odpair_id] = (origin_geo, dest_geo)

    print(f"\nLoaded {len(odpairs)} OD pairs")
    print(f"Mapped {len(geo_to_nuts2)} geographic elements to NUTS2 regions")

    # Debug: Check sample Italy NUTS2 regions
    italy_geo_ids = [geo_id for geo_id, nuts2 in geo_to_nuts2.items() if nuts2.startswith('IT')]
    print(f"Found {len(italy_geo_ids)} Italian geographic nodes: {italy_geo_ids[:5]}")

    # Debug: Check if any odpairs have Italian origins/destinations
    italy_odpairs = 0
    for odpair_id, (orig, dest) in odpair_to_geo.items():
        orig_nuts = geo_to_nuts2.get(orig, '')
        dest_nuts = geo_to_nuts2.get(dest, '')
        if orig_nuts.startswith('IT') or dest_nuts.startswith('IT'):
            italy_odpairs += 1
            if italy_odpairs <= 3:  # Show first 3
                print(f"  Sample: Odpair {odpair_id}: {orig_nuts} → {dest_nuts}")

    print(f"Found {italy_odpairs} OD pairs involving Italy")

    # SCALING FACTOR
    SCALING_FACTOR = 1000

    # Aggregate flows by origin-destination country pairs
    italy_flows = defaultdict(float)  # (origin_country, dest_country) -> tonnes

    processed_count = 0
    italy_count = 0

    for key_str, flow_value_scaled in f_data.items():
        # Parse key (might be string representation of tuple)
        if isinstance(key_str, str):
            key = eval(key_str)
        else:
            key = key_str

        # Filter by year
        if not isinstance(key, tuple) or len(key) < 2:
            continue

        flow_year = key[0]
        if flow_year != year:
            continue

        processed_count += 1

        # Get odpair_id
        if not isinstance(key[1], tuple) or len(key[1]) < 2:
            continue

        odpair_id = key[1][1]

        # Get origin and destination geo IDs
        if odpair_id not in odpair_to_geo:
            continue

        origin_geo, dest_geo = odpair_to_geo[odpair_id]

        # Get NUTS2 regions
        origin_nuts2 = geo_to_nuts2.get(origin_geo)
        dest_nuts2 = geo_to_nuts2.get(dest_geo)

        if not origin_nuts2 or not dest_nuts2:
            continue

        # Extract country codes (first 2 characters of NUTS2)
        origin_country = origin_nuts2[:2].upper()
        dest_country = dest_nuts2[:2].upper()

        # Only include flows involving Italy (IT)
        if origin_country != 'IT' and dest_country != 'IT':
            continue

        italy_count += 1

        # Convert to tonnes
        flow_tonnes = flow_value_scaled * SCALING_FACTOR

        # Add to aggregation
        od_pair = (origin_country, dest_country)
        italy_flows[od_pair] += flow_tonnes

    # Calculate totals
    total_volume = sum(italy_flows.values())

    print(f"\nProcessed {processed_count} flows for year {year}")
    print(f"Found {italy_count} flows involving Italy")
    print(f"Total freight involving Italy: {total_volume/1e6:.2f} Mt")

    if total_volume == 0:
        print("\n[WARNING] No freight found involving Italy!")
        print("  - Check if year exists in data")
        print("  - Check if Italy (IT) NUTS2 regions are in geo mapping")
        print("  - Sample NUTS2 countries found:", list(set(n[:2] for n in geo_to_nuts2.values()))[:10])
        return None

    # Separate into categories
    italy_domestic = italy_flows.get(('IT', 'IT'), 0)
    italy_exports = sum(v for (o, d), v in italy_flows.items() if o == 'IT' and d != 'IT')
    italy_imports = sum(v for (o, d), v in italy_flows.items() if o != 'IT' and d == 'IT')
    italy_transit = sum(v for (o, d), v in italy_flows.items() if o != 'IT' and d != 'IT')

    print("\n" + "-"*80)
    print("BREAKDOWN BY TYPE")
    print("-"*80)
    print(f"\nDomestic (IT → IT):        {italy_domestic/1e6:>8.2f} Mt ({italy_domestic/total_volume*100:>5.1f}%)")
    print(f"Exports (IT → other):      {italy_exports/1e6:>8.2f} Mt ({italy_exports/total_volume*100:>5.1f}%)")
    print(f"Imports (other → IT):      {italy_imports/1e6:>8.2f} Mt ({italy_imports/total_volume*100:>5.1f}%)")
    print(f"Transit (other → other):   {italy_transit/1e6:>8.2f} Mt ({italy_transit/total_volume*100:>5.1f}%)")

    # Top origin countries to Italy
    print("\n" + "-"*80)
    print("TOP ORIGIN COUNTRIES TO ITALY (IMPORTS)")
    print("-"*80)

    imports_by_country = defaultdict(float)
    for (o, d), v in italy_flows.items():
        if d == 'IT' and o != 'IT':
            imports_by_country[o] += v

    imports_sorted = sorted(imports_by_country.items(), key=lambda x: x[1], reverse=True)

    print(f"\n{'Country':<10} {'Volume (Mt)':<15} {'Percentage':<12}")
    print("-" * 40)
    for country, volume in imports_sorted[:10]:
        pct = volume / italy_imports * 100 if italy_imports > 0 else 0
        print(f"{country:<10} {volume/1e6:>12.2f}   {pct:>10.1f}%")

    # Top destination countries from Italy
    print("\n" + "-"*80)
    print("TOP DESTINATION COUNTRIES FROM ITALY (EXPORTS)")
    print("-"*80)

    exports_by_country = defaultdict(float)
    for (o, d), v in italy_flows.items():
        if o == 'IT' and d != 'IT':
            exports_by_country[d] += v

    exports_sorted = sorted(exports_by_country.items(), key=lambda x: x[1], reverse=True)

    print(f"\n{'Country':<10} {'Volume (Mt)':<15} {'Percentage':<12}")
    print("-" * 40)
    for country, volume in exports_sorted[:10]:
        pct = volume / italy_exports * 100 if italy_exports > 0 else 0
        print(f"{country:<10} {volume/1e6:>12.2f}   {pct:>10.1f}%")

    # Top OD pairs involving Italy
    print("\n" + "-"*80)
    print("TOP 15 ORIGIN-DESTINATION PAIRS INVOLVING ITALY")
    print("-"*80)

    flows_sorted = sorted(italy_flows.items(), key=lambda x: x[1], reverse=True)

    print(f"\n{'Origin':<10} {'Destination':<12} {'Volume (Mt)':<15} {'Percentage':<12} {'Type':<15}")
    print("-" * 70)
    for (o, d), volume in flows_sorted[:15]:
        pct = volume / total_volume * 100

        # Categorize
        if o == 'IT' and d == 'IT':
            flow_type = 'Domestic'
        elif o == 'IT':
            flow_type = 'Export'
        elif d == 'IT':
            flow_type = 'Import'
        else:
            flow_type = 'Transit'

        print(f"{o:<10} {d:<12} {volume/1e6:>12.2f}   {pct:>10.1f}%   {flow_type:<15}")

    print("\n" + "="*80)

    return {
        'total': total_volume,
        'domestic': italy_domestic,
        'exports': italy_exports,
        'imports': italy_imports,
        'transit': italy_transit,
        'imports_by_country': dict(imports_by_country),
        'exports_by_country': dict(exports_by_country),
        'all_flows': dict(italy_flows)
    }


# ==============================================================================
# STANDALONE EXECUTION
# ==============================================================================

if __name__ == "__main__":
    import pickle
    from pathlib import Path

    # Case to analyze
    case_name = "case_20251107_105426_rail"
    year_to_analyze = 2040

    print("="*80)
    print(f"Loading case: {case_name}")
    print("="*80)

    # Find case directory
    results_dir = Path("results")
    case_dir = results_dir / case_name

    if not case_dir.exists():
        print(f"[ERROR] Case directory not found: {case_dir}")
        exit(1)

    # Load input data
    input_dir = Path("input_data") / case_name
    if not input_dir.exists():
        print(f"[ERROR] Input directory not found: {input_dir}")
        exit(1)

    print(f"\nLoading input data from: {input_dir}")

    # Load YAML files
    input_data = {}
    for yaml_file in ['Odpair.yaml', 'GeographicElement.yaml']:
        file_path = input_dir / yaml_file
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                key = yaml_file.replace('.yaml', '')
                input_data[key] = yaml.safe_load(f)
                print(f"  Loaded {key}: {len(input_data[key])} entries")

    print(f"\nLoading output data from: {case_dir}")

    # Load f_dict from results
    f_dict_file = list(case_dir.glob("*_f_dict.yaml"))[0]
    with open(f_dict_file, 'r', encoding='utf-8') as f:
        f_data = yaml.safe_load(f)
        print(f"  Loaded f: {len(f_data)} flow entries")

    # Create loaded_runs structure
    loaded_runs = {
        case_name: {
            "input_data": input_data,
            "output_data": {"f": f_data}
        }
    }

    # Run analysis
    italy_data = analyze_italy_freight(case_name, loaded_runs, year=year_to_analyze)

    print(f"\n[SUCCESS] Italy freight analysis completed for year {year_to_analyze}")


# ==============================================================================
# USAGE IN NOTEBOOK
# ==============================================================================
"""
# If you want to use in notebook:
from analyze_italy_freight import analyze_italy_freight
italy_data = analyze_italy_freight('case_20251107_105426_rail', loaded_runs, year=2040)
"""
