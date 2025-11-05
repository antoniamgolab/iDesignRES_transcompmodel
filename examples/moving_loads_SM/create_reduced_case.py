"""
Create a reduced case from case_nuts2_complete for memory-constrained runs.

Filters OD-pairs by:
- Minimum distance (e.g., >= 500 km for long-distance freight)
- Top N by demand
"""

import yaml
from pathlib import Path
import shutil

def create_reduced_case(
    source_dir="input_data/case_nuts2_complete",
    output_dir="input_data/case_nuts2_reduced",
    min_distance_km=500,
    max_odpairs=1000
):
    """
    Create a reduced case by filtering OD-pairs.

    Parameters:
    -----------
    source_dir : str
        Source directory with full case
    output_dir : str
        Output directory for reduced case
    min_distance_km : float
        Minimum distance to include OD-pair (default: 500km for long-distance)
    max_odpairs : int
        Maximum number of OD-pairs to include (default: 1000)
    """
    source_path = Path(source_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"Creating reduced case from {source_dir}")
    print(f"Filters: min_distance={min_distance_km}km, max_odpairs={max_odpairs}")

    # Load paths to get distances
    with open(source_path / "Path.yaml", 'r') as f:
        paths = yaml.safe_load(f)

    path_dict = {p['id']: p for p in paths}

    # Load OD-pairs
    with open(source_path / "Odpair.yaml", 'r') as f:
        odpairs = yaml.safe_load(f)

    print(f"Original OD-pairs: {len(odpairs)}")

    # Filter OD-pairs by distance
    filtered_odpairs = []
    for odp in odpairs:
        path_id = odp['path_id']
        if path_id in path_dict:
            distance = path_dict[path_id]['length']
            if distance >= min_distance_km:
                filtered_odpairs.append(odp)

    print(f"After distance filter (>= {min_distance_km}km): {len(filtered_odpairs)}")

    # Sort by total demand (sum of F array) and take top N
    filtered_odpairs.sort(key=lambda x: sum(x.get('F', [0])), reverse=True)
    filtered_odpairs = filtered_odpairs[:max_odpairs]

    print(f"After demand filter (top {max_odpairs}): {len(filtered_odpairs)}")

    # Get IDs of kept OD-pairs and paths
    kept_odpair_ids = {odp['id'] for odp in filtered_odpairs}
    kept_path_ids = {odp['path_id'] for odp in filtered_odpairs}

    # Filter paths
    filtered_paths = [p for p in paths if p['id'] in kept_path_ids]
    print(f"Filtered paths: {len(filtered_paths)}")

    # Get all geographic elements used by filtered paths
    kept_geo_ids = set()
    for path in filtered_paths:
        for geo_id in path['sequence']:
            kept_geo_ids.add(geo_id)

    # Load and filter geographic elements
    with open(source_path / "GeographicElement.yaml", 'r') as f:
        geo_elements = yaml.safe_load(f)
    filtered_geo = [g for g in geo_elements if g['id'] in kept_geo_ids]
    print(f"Filtered geographic elements: {len(filtered_geo)}")

    # Load and filter initial vehicle stock
    with open(source_path / "InitialVehicleStock.yaml", 'r') as f:
        vehicle_stock = yaml.safe_load(f)
    filtered_stock = [v for v in vehicle_stock if v.get('odpair_id', v.get('odpair', v.get('id'))) in kept_odpair_ids]
    print(f"Filtered vehicle stock: {len(filtered_stock)}")

    # Load and filter mandatory breaks
    with open(source_path / "MandatoryBreaks.yaml", 'r') as f:
        breaks = yaml.safe_load(f)
    filtered_breaks = [b for b in breaks if b['path_id'] in kept_path_ids]
    print(f"Filtered mandatory breaks: {len(filtered_breaks)}")

    # Filter FuelCost by geographic elements
    with open(source_path / "FuelCost.yaml", 'r') as f:
        fuel_costs = yaml.safe_load(f)
    filtered_fuel_costs = [fc for fc in fuel_costs if fc['location'] in kept_geo_ids]
    print(f"Filtered fuel costs: {len(filtered_fuel_costs)}")

    # Filter InitialFuelInfr by geographic elements
    with open(source_path / "InitialFuelInfr.yaml", 'r') as f:
        fuel_infr = yaml.safe_load(f)
    filtered_fuel_infr = [fi for fi in fuel_infr if fi['allocation'] in kept_geo_ids]
    print(f"Filtered initial fuel infrastructure: {len(filtered_fuel_infr)}")

    # Save filtered files
    with open(output_path / "Odpair.yaml", 'w') as f:
        yaml.dump(filtered_odpairs, f, default_flow_style=False, sort_keys=False)

    with open(output_path / "Path.yaml", 'w') as f:
        yaml.dump(filtered_paths, f, default_flow_style=False, sort_keys=False)

    with open(output_path / "GeographicElement.yaml", 'w') as f:
        yaml.dump(filtered_geo, f, default_flow_style=False, sort_keys=False)

    with open(output_path / "InitialVehicleStock.yaml", 'w') as f:
        yaml.dump(filtered_stock, f, default_flow_style=False, sort_keys=False)

    with open(output_path / "MandatoryBreaks.yaml", 'w') as f:
        yaml.dump(filtered_breaks, f, default_flow_style=False, sort_keys=False)

    with open(output_path / "FuelCost.yaml", 'w') as f:
        yaml.dump(filtered_fuel_costs, f, default_flow_style=False, sort_keys=False)

    with open(output_path / "InitialFuelInfr.yaml", 'w') as f:
        yaml.dump(filtered_fuel_infr, f, default_flow_style=False, sort_keys=False)

    # Copy parameter files that don't need filtering
    for filename in [
        "Technology.yaml", "Fuel.yaml", "FuelingInfrTypes.yaml",
        "Mode.yaml", "Vehicletype.yaml", "TechVehicle.yaml",
        "Product.yaml", "FinancialStatus.yaml", "Regiontype.yaml",
        "Speed.yaml", "Model.yaml", "NetworkConnectionCosts.yaml",
        "InitialModeInfr.yaml", "SpatialFlexibilityEdges.yaml"
    ]:
        if (source_path / filename).exists():
            shutil.copy(source_path / filename, output_path / filename)

    print(f"\n✓ Reduced case created in {output_dir}")
    print(f"  OD-pairs: {len(odpairs)} → {len(filtered_odpairs)}")
    print(f"  Paths: {len(paths)} → {len(filtered_paths)}")
    print(f"  Geographic elements: {len(geo_elements)} → {len(filtered_geo)}")
    print(f"\nExpected memory reduction: ~{100 * (1 - len(filtered_odpairs)/len(odpairs)):.0f}%")


if __name__ == "__main__":
    # Create reduced case with long-distance routes (>= 500km) and top 1000 by demand
    create_reduced_case(
        source_dir="input_data/case_nuts2_complete",
        output_dir="input_data/case_nuts2_reduced",
        min_distance_km=500,  # Long-distance freight only
        max_odpairs=1000      # Reduce from 5,329 to 1,000 (81% reduction)
    )
