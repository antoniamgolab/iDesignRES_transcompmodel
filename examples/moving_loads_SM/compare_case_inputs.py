"""
Compare Input Files Across Multiple Cases

This script compares YAML input files across different case studies to identify
differences in parameters that should lead to different optimization results.
"""
import yaml
from pathlib import Path
import pandas as pd
import numpy as np


def load_case_inputs(case_name, input_dir="input_data"):
    """Load all YAML files for a case"""
    case_path = Path(input_dir) / case_name

    if not case_path.exists():
        print(f"[ERROR] Case directory not found: {case_path}")
        return None

    # Key files to compare
    files_to_load = [
        "GeographicElement.yaml",
        "Fuel.yaml",
        "Technology.yaml",
        "TechVehicle.yaml",
        "FuelingInfrTypes.yaml",
        "Mode.yaml",
        "Path.yaml",
        "Odpair.yaml"
    ]

    data = {}
    for filename in files_to_load:
        file_path = case_path / filename
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                data[filename] = yaml.safe_load(f)
        else:
            print(f"  [WARNING] File not found: {filename}")
            data[filename] = None

    return data


def compare_fuel_prices(cases_data, case_names):
    """Compare fuel prices across cases"""
    print("\n" + "="*80)
    print("FUEL PRICE COMPARISON")
    print("="*80)

    fuel_comparison = []

    for case_name in case_names:
        fuels = cases_data[case_name].get("Fuel.yaml", [])
        if not fuels:
            continue

        for fuel in fuels:
            fuel_id = fuel.get('id')
            fuel_name = fuel.get('name', 'unknown')
            prices = fuel.get('price', {})

            for year, price in prices.items():
                fuel_comparison.append({
                    'case': case_name,
                    'fuel_id': fuel_id,
                    'fuel_name': fuel_name,
                    'year': year,
                    'price': price
                })

    if fuel_comparison:
        df = pd.DataFrame(fuel_comparison)

        # Pivot to show prices side-by-side
        for fuel_name in df['fuel_name'].unique():
            fuel_df = df[df['fuel_name'] == fuel_name]
            print(f"\n{fuel_name}:")
            pivot = fuel_df.pivot_table(index='year', columns='case', values='price', aggfunc='first')
            print(pivot.to_string())

            # Check if all values are identical
            if len(pivot.columns) > 1:
                all_same = pivot.nunique(axis=1).max() == 1
                if all_same:
                    print(f"  [WARNING] ALL PRICES IDENTICAL FOR {fuel_name}")
                else:
                    print(f"  [OK] Prices vary across cases")


def compare_geographic_costs(cases_data, case_names):
    """Compare geographic element costs (e.g., network access costs)"""
    print("\n" + "="*80)
    print("GEOGRAPHIC ELEMENT COST COMPARISON")
    print("="*80)

    for case_name in case_names:
        geo_elements = cases_data[case_name].get("GeographicElement.yaml", [])
        if not geo_elements:
            continue

        # Check for cost-related fields
        nodes_with_costs = [g for g in geo_elements if g.get('type') == 'node' and 'cost' in g]
        edges_with_costs = [g for g in geo_elements if g.get('type') == 'edge' and 'cost' in g]

        print(f"\n{case_name}:")
        print(f"  Nodes with cost field: {len(nodes_with_costs)}")
        print(f"  Edges with cost field: {len(edges_with_costs)}")

        if nodes_with_costs:
            costs = [n['cost'] for n in nodes_with_costs[:5]]
            print(f"  Sample node costs: {costs}")
        if edges_with_costs:
            costs = [e['cost'] for e in edges_with_costs[:5]]
            print(f"  Sample edge costs: {costs}")


def compare_technology_costs(cases_data, case_names):
    """Compare technology and vehicle costs across cases"""
    print("\n" + "="*80)
    print("TECHNOLOGY & VEHICLE COST COMPARISON")
    print("="*80)

    for case_name in case_names:
        tech_vehicles = cases_data[case_name].get("TechVehicle.yaml", [])
        if not tech_vehicles:
            continue

        print(f"\n{case_name}:")
        for tv in tech_vehicles[:3]:  # Show first 3 vehicles
            tv_id = tv.get('id')
            capex = tv.get('capex', {})
            opex = tv.get('opex_var', {})

            print(f"  Vehicle {tv_id}:")
            if capex:
                print(f"    CAPEX (sample years): {dict(list(capex.items())[:3])}")
            if opex:
                print(f"    OPEX (sample years): {dict(list(opex.items())[:3])}")


def compare_fueling_infrastructure(cases_data, case_names):
    """Compare fueling infrastructure types and costs"""
    print("\n" + "="*80)
    print("FUELING INFRASTRUCTURE COMPARISON")
    print("="*80)

    infra_comparison = []

    for case_name in case_names:
        infra_types = cases_data[case_name].get("FuelingInfrTypes.yaml", [])
        if not infra_types:
            continue

        for infra in infra_types:
            infra_id = infra.get('id')
            infra_type = infra.get('fueling_type', 'unknown')
            fuel = infra.get('fuel', 'unknown')
            capex = infra.get('capex', {})
            opex = infra.get('opex', {})

            # Get a sample cost (2032)
            capex_2032 = capex.get(2032, 0)
            opex_2032 = opex.get(2032, 0)

            infra_comparison.append({
                'case': case_name,
                'infra_id': infra_id,
                'type': infra_type,
                'fuel': fuel,
                'capex_2032': capex_2032,
                'opex_2032': opex_2032
            })

    if infra_comparison:
        df = pd.DataFrame(infra_comparison)

        # Show by infrastructure type
        for infra_type in df['type'].unique():
            type_df = df[df['type'] == infra_type]
            print(f"\n{infra_type}:")
            for _, row in type_df.iterrows():
                print(f"  {row['case']}: CAPEX={row['capex_2032']}, OPEX={row['opex_2032']}")

            # Check if all identical
            if len(type_df) > 1:
                capex_same = type_df['capex_2032'].nunique() == 1
                opex_same = type_df['opex_2032'].nunique() == 1
                if capex_same and opex_same:
                    print(f"  [WARNING]  ALL COSTS IDENTICAL FOR {infra_type}")
                else:
                    print(f"  [OK] Costs vary across cases")


def compare_modes(cases_data, case_names):
    """Compare mode costs across cases"""
    print("\n" + "="*80)
    print("MODE COST COMPARISON")
    print("="*80)

    for case_name in case_names:
        modes = cases_data[case_name].get("Mode.yaml", [])
        if not modes:
            continue

        print(f"\n{case_name}:")
        for mode in modes:
            mode_id = mode.get('id')
            mode_name = mode.get('name', 'unknown')
            cost_per_tkm = mode.get('cost_per_tkm', {})
            cost_per_ukm = mode.get('cost_per_ukm', {})

            if cost_per_tkm or cost_per_ukm:
                print(f"  Mode {mode_name} (id={mode_id}):")
                if cost_per_tkm:
                    print(f"    cost_per_tkm (2032): {cost_per_tkm.get(2032, 'N/A')}")
                if cost_per_ukm:
                    print(f"    cost_per_ukm (2032): {cost_per_ukm.get(2032, 'N/A')}")


def hash_data_structure(data):
    """Create a simple hash of a data structure for comparison"""
    import hashlib
    import json

    # Convert to JSON string and hash
    json_str = json.dumps(data, sort_keys=True, default=str)
    return hashlib.md5(json_str.encode()).hexdigest()


def compare_file_hashes(cases_data, case_names):
    """Compare file hashes to quickly identify identical files"""
    print("\n" + "="*80)
    print("FILE HASH COMPARISON (Quick Identical File Detection)")
    print("="*80)

    files = ["Fuel.yaml", "Technology.yaml", "TechVehicle.yaml",
             "FuelingInfrTypes.yaml", "Mode.yaml", "GeographicElement.yaml"]

    for filename in files:
        print(f"\n{filename}:")
        hashes = {}

        for case_name in case_names:
            data = cases_data[case_name].get(filename)
            if data is not None:
                file_hash = hash_data_structure(data)
                hashes[case_name] = file_hash
                print(f"  {case_name}: {file_hash[:16]}...")

        # Check if all hashes are identical
        if len(set(hashes.values())) == 1:
            print(f"  [WARNING]  ALL FILES IDENTICAL!")
        else:
            print(f"  [OK] Files differ across cases")
            # Show which are the same
            hash_groups = {}
            for case, h in hashes.items():
                if h not in hash_groups:
                    hash_groups[h] = []
                hash_groups[h].append(case)

            if len(hash_groups) > 1:
                print(f"  Groups of identical files:")
                for i, (h, cases) in enumerate(hash_groups.items(), 1):
                    print(f"    Group {i}: {cases}")


def main():
    """Main comparison function"""
    case_names = [
        "case_20251107_194948_var_var",
        "case_20251107_214135_var_uni",
        "case_20251107_214220_uni_var",
        "case_20251107_214315_uni_uni",
    ]

    print("="*80)
    print("CASE INPUT FILE COMPARISON")
    print("="*80)
    print(f"\nComparing {len(case_names)} cases:")
    for name in case_names:
        print(f"  - {name}")

    # Load all case data
    print("\n" + "="*80)
    print("LOADING CASE DATA")
    print("="*80)

    cases_data = {}
    for case_name in case_names:
        print(f"\nLoading: {case_name}")
        data = load_case_inputs(case_name)
        if data:
            cases_data[case_name] = data
            print(f"  [OK] Loaded {len([k for k, v in data.items() if v is not None])} files")
        else:
            print(f"  [FAILED] Failed to load case")

    if not cases_data:
        print("\n[ERROR] No cases loaded successfully")
        return

    # Run comparisons
    compare_file_hashes(cases_data, case_names)
    compare_fuel_prices(cases_data, case_names)
    compare_geographic_costs(cases_data, case_names)
    compare_technology_costs(cases_data, case_names)
    compare_fueling_infrastructure(cases_data, case_names)
    compare_modes(cases_data, case_names)

    # Summary
    print("\n" + "="*80)
    print("COMPARISON COMPLETE")
    print("="*80)
    print("\nLook for [WARNING]  warnings indicating identical values across cases")
    print("Expected differences based on case names:")
    print("  var_var: Variable electricity prices AND variable network costs")
    print("  var_uni: Variable electricity prices, uniform network costs")
    print("  uni_var: Uniform electricity prices, variable network costs")
    print("  uni_uni: Uniform electricity prices AND uniform network costs")
    print("="*80)


if __name__ == "__main__":
    main()
