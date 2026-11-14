"""
Create Border Region Sensitivity Scenarios

This script takes existing var_var scenarios (with variable electricity prices and
variable network costs) and creates 4 new variants where ONLY the Southern Border
regions (DE-AT-IT Alps crossing) have altered pricing:

1. border_uni_elec: Border regions get uniform (averaged) electricity prices
2. border_rev_elec: Border regions get reversed electricity prices (high<->low)
3. border_uni_network: Border regions get uniform (averaged) network costs
4. border_rev_network: Border regions get reversed network costs

Southern Border Regions (NUTS2):
  AT: AT31, AT32, AT33, AT34
  IT: ITH1, ITH3
  DE: DE14, DE21, DE22, DE27, DEF0
"""

import os
import yaml
import shutil
from pathlib import Path
from typing import Dict, List, Set
from copy import deepcopy

# Southern Border NUTS2 regions
SOUTHERN_BORDER_REGIONS = {
    'AT31', 'AT32', 'AT33', 'AT34',  # Austria
    'ITH1', 'ITH3',                   # Italy
    'DE14', 'DE21', 'DE22', 'DE27', 'DEF0'  # Germany
}

def load_yaml(filepath: str) -> List[Dict]:
    """Load YAML file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def save_yaml(data: List[Dict], filepath: str):
    """Save data to YAML file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

def get_geo_id_to_nuts2_mapping(geo_elements: List[Dict]) -> Dict[int, str]:
    """Create mapping from geo element ID to NUTS2 region."""
    mapping = {}
    for geo in geo_elements:
        geo_id = geo.get('id')
        nuts2 = geo.get('nuts2_region')
        if geo_id is not None and nuts2:
            mapping[geo_id] = nuts2
    return mapping

def get_border_geo_ids(geo_elements: List[Dict], border_regions: Set[str]) -> Set[int]:
    """Get geo element IDs that are in border regions."""
    border_ids = set()
    for geo in geo_elements:
        if geo.get('nuts2_region') in border_regions:
            border_ids.add(geo['id'])
    return border_ids

def calculate_average_prices(fuel_costs: List[Dict], geo_id_to_nuts2: Dict[int, str],
                             border_regions: Set[str], fuel_type: str = 'electricity') -> List[float]:
    """
    Calculate average electricity prices across border regions.
    Returns average cost_per_kWh array.
    """
    prices_by_infr_type = {}  # {infr_type: [list of price arrays]}

    for fc in fuel_costs:
        if fc.get('fuel') != fuel_type:
            continue

        geo_id = fc.get('location')
        nuts2 = geo_id_to_nuts2.get(geo_id)

        if nuts2 in border_regions:
            infr_type = fc.get('fueling_infr_type_id')
            if infr_type not in prices_by_infr_type:
                prices_by_infr_type[infr_type] = []
            prices_by_infr_type[infr_type].append(fc['cost_per_kWh'])

    # Calculate average for each infrastructure type
    avg_prices = {}
    for infr_type, price_arrays in prices_by_infr_type.items():
        if price_arrays:
            num_years = len(price_arrays[0])
            avg_prices[infr_type] = [
                sum(arr[y] for arr in price_arrays) / len(price_arrays)
                for y in range(num_years)
            ]

    return avg_prices

def get_country_prices(fuel_costs: List[Dict], geo_elements: List[Dict],
                      border_regions: Set[str], fuel_type: str = 'electricity') -> Dict:
    """
    Get electricity prices by country for border regions.
    Returns {country: {infr_type: cost_per_kWh array}}
    """
    # Get geo_id to country mapping
    geo_to_country = {}
    geo_to_nuts2 = {}
    for geo in geo_elements:
        geo_to_country[geo['id']] = geo.get('country', '')
        geo_to_nuts2[geo['id']] = geo.get('nuts2_region', '')

    country_prices = {}  # {country: {infr_type: [list of price arrays]}}

    for fc in fuel_costs:
        if fc.get('fuel') != fuel_type:
            continue

        geo_id = fc.get('location')
        nuts2 = geo_to_nuts2.get(geo_id)
        country = geo_to_country.get(geo_id)

        if nuts2 in border_regions and country:
            infr_type = fc.get('fueling_infr_type_id')

            if country not in country_prices:
                country_prices[country] = {}
            if infr_type not in country_prices[country]:
                country_prices[country][infr_type] = []

            country_prices[country][infr_type].append(fc['cost_per_kWh'])

    # Average within each country
    result = {}
    for country, infr_data in country_prices.items():
        result[country] = {}
        for infr_type, price_arrays in infr_data.items():
            if price_arrays:
                num_years = len(price_arrays[0])
                result[country][infr_type] = [
                    sum(arr[y] for arr in price_arrays) / len(price_arrays)
                    for y in range(num_years)
                ]

    return result

def create_reversed_country_prices(country_prices: Dict) -> Dict:
    """
    Create reversed price mapping.
    Countries with highest average prices get lowest prices and vice versa.
    """
    if not country_prices:
        return {}

    # Get all infrastructure types
    infr_types = set()
    for country_data in country_prices.values():
        infr_types.update(country_data.keys())

    reversed_prices = {}

    for infr_type in infr_types:
        # Get countries with this infr_type and their average prices
        countries_with_prices = []
        for country, data in country_prices.items():
            if infr_type in data:
                avg_price = sum(data[infr_type]) / len(data[infr_type])
                countries_with_prices.append((country, data[infr_type], avg_price))

        if len(countries_with_prices) > 1:
            # Sort by average price (ascending)
            sorted_countries = sorted(countries_with_prices, key=lambda x: x[2])

            # Get the price arrays in ascending order
            sorted_price_arrays = [x[1] for x in sorted_countries]

            # Reverse: assign highest prices to lowest price country and vice versa
            reversed_price_arrays = sorted_price_arrays[::-1]

            # Create mapping
            for i, (country, _, _) in enumerate(sorted_countries):
                if country not in reversed_prices:
                    reversed_prices[country] = {}
                reversed_prices[country][infr_type] = reversed_price_arrays[i]
        else:
            # Only one country, keep same prices
            for country, prices, _ in countries_with_prices:
                if country not in reversed_prices:
                    reversed_prices[country] = {}
                reversed_prices[country][infr_type] = prices

    return reversed_prices

def apply_uniform_electricity_to_border(fuel_costs: List[Dict], geo_elements: List[Dict],
                                        border_regions: Set[str]) -> List[Dict]:
    """
    Apply uniform (averaged) electricity prices to border regions only.
    Non-border regions keep their original variable prices.
    """
    geo_id_to_nuts2 = get_geo_id_to_nuts2_mapping(geo_elements)

    # Calculate average prices for border regions
    avg_prices = calculate_average_prices(fuel_costs, geo_id_to_nuts2, border_regions)

    modified_costs = deepcopy(fuel_costs)

    for fc in modified_costs:
        if fc.get('fuel') != 'electricity':
            continue

        geo_id = fc.get('location')
        nuts2 = geo_id_to_nuts2.get(geo_id)

        # Only modify border regions
        if nuts2 in border_regions:
            infr_type = fc.get('fueling_infr_type_id')
            if infr_type in avg_prices:
                fc['cost_per_kWh'] = avg_prices[infr_type]

    return modified_costs

def apply_reversed_electricity_to_border(fuel_costs: List[Dict], geo_elements: List[Dict],
                                         border_regions: Set[str]) -> List[Dict]:
    """
    Apply reversed electricity prices to border regions only.
    Countries with high prices in the original get low prices and vice versa.
    Non-border regions keep their original variable prices.
    """
    geo_id_to_country = {geo['id']: geo.get('country', '') for geo in geo_elements}
    geo_id_to_nuts2 = get_geo_id_to_nuts2_mapping(geo_elements)

    # Get country prices for border regions
    country_prices = get_country_prices(fuel_costs, geo_elements, border_regions)

    # Create reversed mapping
    reversed_prices = create_reversed_country_prices(country_prices)

    print(f"  Original country avg prices (border): ", end="")
    for country, data in country_prices.items():
        if 1 in data:  # slow charging
            avg = sum(data[1]) / len(data[1])
            print(f"{country}={avg:.4f} ", end="")
    print()

    print(f"  Reversed country avg prices (border): ", end="")
    for country, data in reversed_prices.items():
        if 1 in data:
            avg = sum(data[1]) / len(data[1])
            print(f"{country}={avg:.4f} ", end="")
    print()

    modified_costs = deepcopy(fuel_costs)

    for fc in modified_costs:
        if fc.get('fuel') != 'electricity':
            continue

        geo_id = fc.get('location')
        nuts2 = geo_id_to_nuts2.get(geo_id)
        country = geo_id_to_country.get(geo_id)

        # Only modify border regions
        if nuts2 in border_regions and country in reversed_prices:
            infr_type = fc.get('fueling_infr_type_id')
            if infr_type in reversed_prices[country]:
                fc['cost_per_kWh'] = reversed_prices[country][infr_type]

    return modified_costs

def get_network_costs_by_country(network_costs: List[Dict], geo_elements: List[Dict],
                                 border_regions: Set[str]) -> Dict:
    """Get network costs by country for border regions."""
    geo_to_country = {geo['id']: geo.get('country', '') for geo in geo_elements}
    geo_to_nuts2 = {geo['id']: geo.get('nuts2_region', '') for geo in geo_elements}

    country_costs = {}  # {country: [list of cost arrays]}

    for nc in network_costs:
        geo_id = nc.get('location')
        nuts2 = geo_to_nuts2.get(geo_id)
        country = geo_to_country.get(geo_id)

        if nuts2 in border_regions and country:
            if country not in country_costs:
                country_costs[country] = []
            country_costs[country].append(nc['network_cost_per_kW'])

    # Average within each country
    result = {}
    for country, cost_arrays in country_costs.items():
        if cost_arrays:
            num_years = len(cost_arrays[0])
            result[country] = [
                sum(arr[y] for arr in cost_arrays) / len(cost_arrays)
                for y in range(num_years)
            ]

    return result

def apply_uniform_network_to_border(network_costs: List[Dict], geo_elements: List[Dict],
                                    border_regions: Set[str]) -> List[Dict]:
    """Apply uniform network costs to border regions only."""
    geo_to_nuts2 = {geo['id']: geo.get('nuts2_region', '') for geo in geo_elements}

    # Calculate average network cost for border regions
    border_costs = []
    for nc in network_costs:
        geo_id = nc.get('location')
        if geo_to_nuts2.get(geo_id) in border_regions:
            border_costs.append(nc['network_cost_per_kW'])

    if not border_costs:
        return network_costs

    # Calculate average
    num_years = len(border_costs[0])
    avg_cost = [
        sum(arr[y] for arr in border_costs) / len(border_costs)
        for y in range(num_years)
    ]

    modified_costs = deepcopy(network_costs)

    for nc in modified_costs:
        geo_id = nc.get('location')
        if geo_to_nuts2.get(geo_id) in border_regions:
            nc['network_cost_per_kW'] = avg_cost

    return modified_costs

def apply_reversed_network_to_border(network_costs: List[Dict], geo_elements: List[Dict],
                                     border_regions: Set[str]) -> List[Dict]:
    """Apply reversed network costs to border regions only."""
    geo_to_country = {geo['id']: geo.get('country', '') for geo in geo_elements}
    geo_to_nuts2 = {geo['id']: geo.get('nuts2_region', '') for geo in geo_elements}

    # Get country costs for border regions
    country_costs = get_network_costs_by_country(network_costs, geo_elements, border_regions)

    if len(country_costs) <= 1:
        return network_costs

    # Sort countries by average cost
    sorted_countries = sorted(
        country_costs.items(),
        key=lambda x: sum(x[1]) / len(x[1])
    )

    # Create reversed mapping
    reversed_costs = {}
    reversed_cost_arrays = [x[1] for x in sorted_countries][::-1]
    for i, (country, _) in enumerate(sorted_countries):
        reversed_costs[country] = reversed_cost_arrays[i]

    print(f"  Original country avg network costs (border): ", end="")
    for country, costs in country_costs.items():
        avg = sum(costs) / len(costs)
        print(f"{country}={avg:.2f} ", end="")
    print()

    print(f"  Reversed country avg network costs (border): ", end="")
    for country, costs in reversed_costs.items():
        avg = sum(costs) / len(costs)
        print(f"{country}={avg:.2f} ", end="")
    print()

    modified_costs = deepcopy(network_costs)

    for nc in modified_costs:
        geo_id = nc.get('location')
        nuts2 = geo_to_nuts2.get(geo_id)
        country = geo_to_country.get(geo_id)

        if nuts2 in border_regions and country in reversed_costs:
            nc['network_cost_per_kW'] = reversed_costs[country]

    return modified_costs

def create_border_variants(source_dir: str, output_base_dir: str, scenario_name: str):
    """
    Create 4 border region variants from a source var_var scenario.

    Parameters:
    -----------
    source_dir : str
        Path to source input_data directory (var_var scenario)
    output_base_dir : str
        Base path for output directories
    scenario_name : str
        Name prefix for output scenarios
    """
    print(f"\nProcessing: {scenario_name}")
    print("=" * 60)

    # Load source files
    geo_elements = load_yaml(os.path.join(source_dir, 'GeographicElement.yaml'))
    fuel_costs = load_yaml(os.path.join(source_dir, 'FuelCost.yaml'))

    # Check if NetworkConnectionCosts exists
    network_costs_file = os.path.join(source_dir, 'NetworkConnectionCosts.yaml')
    has_network_costs = os.path.exists(network_costs_file)
    if has_network_costs:
        network_costs = load_yaml(network_costs_file)
    else:
        network_costs = None
        print("  Warning: No NetworkConnectionCosts.yaml found")

    # Count border region elements
    border_geo_ids = get_border_geo_ids(geo_elements, SOUTHERN_BORDER_REGIONS)
    print(f"  Found {len(border_geo_ids)} geographic elements in border regions")

    variants = [
        ('border_uni_elec', 'Border Uniform Electricity Prices'),
        ('border_rev_elec', 'Border Reversed Electricity Prices'),
        ('border_uni_network', 'Border Uniform Network Costs'),
        ('border_rev_network', 'Border Reversed Network Costs'),
    ]

    for variant_suffix, description in variants:
        print(f"\n  Creating {description}...")

        # Create output directory
        output_dir = os.path.join(output_base_dir, f"{scenario_name}_{variant_suffix}")
        os.makedirs(output_dir, exist_ok=True)

        # Copy all files from source
        for filename in os.listdir(source_dir):
            src_file = os.path.join(source_dir, filename)
            if os.path.isfile(src_file):
                shutil.copy2(src_file, output_dir)

        # Apply modifications based on variant
        if variant_suffix == 'border_uni_elec':
            modified_fc = apply_uniform_electricity_to_border(
                fuel_costs, geo_elements, SOUTHERN_BORDER_REGIONS)
            save_yaml(modified_fc, os.path.join(output_dir, 'FuelCost.yaml'))

        elif variant_suffix == 'border_rev_elec':
            modified_fc = apply_reversed_electricity_to_border(
                fuel_costs, geo_elements, SOUTHERN_BORDER_REGIONS)
            save_yaml(modified_fc, os.path.join(output_dir, 'FuelCost.yaml'))

        elif variant_suffix == 'border_uni_network' and has_network_costs:
            modified_nc = apply_uniform_network_to_border(
                network_costs, geo_elements, SOUTHERN_BORDER_REGIONS)
            save_yaml(modified_nc, os.path.join(output_dir, 'NetworkConnectionCosts.yaml'))

        elif variant_suffix == 'border_rev_network' and has_network_costs:
            modified_nc = apply_reversed_network_to_border(
                network_costs, geo_elements, SOUTHERN_BORDER_REGIONS)
            save_yaml(modified_nc, os.path.join(output_dir, 'NetworkConnectionCosts.yaml'))

        print(f"    Saved to: {output_dir}")

def main():
    """Main function to create border region scenarios for all uncertainty scenarios."""

    script_dir = Path(__file__).parent
    uncertainty_base = script_dir / "input_data" / "uncertainty_scenarios"
    output_base = script_dir / "input_data" / "border_sensitivity"

    # Create output base directory
    output_base.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("CREATING BORDER REGION SENSITIVITY SCENARIOS")
    print("=" * 70)
    print(f"\nSouthern Border Regions: {sorted(SOUTHERN_BORDER_REGIONS)}")
    print(f"Source: {uncertainty_base}")
    print(f"Output: {output_base}")

    # Find all scenario directories
    if not uncertainty_base.exists():
        print(f"\nERROR: Uncertainty scenarios directory not found: {uncertainty_base}")
        return

    scenarios = sorted([d for d in uncertainty_base.iterdir() if d.is_dir() and d.name.startswith('scenario_')])

    if not scenarios:
        print("\nNo scenario directories found!")
        return

    print(f"\nFound {len(scenarios)} scenarios")

    for scenario_path in scenarios:
        scenario_name = scenario_path.name
        create_border_variants(
            source_dir=str(scenario_path),
            output_base_dir=str(output_base),
            scenario_name=scenario_name
        )

    print("\n" + "=" * 70)
    print("COMPLETED")
    print("=" * 70)
    print(f"\nCreated {len(scenarios) * 4} border sensitivity scenarios")
    print(f"Output directory: {output_base}")

if __name__ == "__main__":
    main()
