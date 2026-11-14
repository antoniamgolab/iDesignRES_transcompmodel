"""
Create regional analysis maps showing:
1. Freight flow intensity by NUTS2 region
2. Weighted mandatory breaks by region
3. Levelized fuel prices (electricity + network fees) by region

For years: 2028, 2032, 2036
"""

import yaml
import os
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from collections import defaultdict
from pathlib import Path

# Try to import geopandas for proper maps
try:
    import geopandas as gpd
    HAS_GEOPANDAS = True
except ImportError:
    HAS_GEOPANDAS = False
    print("Warning: geopandas not available, using scatter plots instead of choropleth")

# Configuration
SCRIPT_DIR = Path(__file__).parent
GEO_DIR = SCRIPT_DIR / 'input_data' / 'uncertainty_scenarios_rail' / 'scenario_004'
RESULTS_DIR = SCRIPT_DIR / 'results' / 'uncertainty_scenarios' / 'scenario_004'
SHAPEFILE_PATH = SCRIPT_DIR / 'data' / 'NUTS_RG_20M_2021_4326.shp' / 'NUTS_RG_20M_2021_4326.shp'
OUTPUT_DIR = SCRIPT_DIR / 'figures'

TARGET_YEARS = [2028, 2032, 2036]
# Years from 2020 to 2060 with step 1 (41 years total in FuelCost)
ALL_YEARS = list(range(2020, 2061))


def load_geographic_elements():
    """Load geographic elements with coordinates."""
    with open(GEO_DIR / 'GeographicElement.yaml', 'r') as f:
        geo_elements = yaml.safe_load(f)

    nodes = {}
    for g in geo_elements:
        if g.get('type') == 'node':
            node_id = g['id']
            nodes[node_id] = {
                'name': g.get('name', f'Node_{node_id}'),
                'nuts2_region': g.get('nuts2_region'),
                'country': g.get('country'),
                'lat': g.get('coordinate_lat'),
                'lon': g.get('coordinate_long'),
            }
    return nodes


def load_paths():
    """Load path data."""
    with open(GEO_DIR / 'Path.yaml', 'r') as f:
        paths = yaml.safe_load(f)
    return {p['id']: p for p in paths}


def load_odpairs():
    """Load OD pair data."""
    with open(GEO_DIR / 'Odpair.yaml', 'r') as f:
        odpairs = yaml.safe_load(f)
    return {od['id']: od for od in odpairs}


def load_mandatory_breaks():
    """Load mandatory breaks data."""
    with open(GEO_DIR / 'MandatoryBreaks.yaml', 'r') as f:
        breaks = yaml.safe_load(f)
    return breaks


def load_fuel_costs():
    """Load fuel cost data (electricity prices)."""
    with open(GEO_DIR / 'FuelCost.yaml', 'r') as f:
        fuel_costs = yaml.safe_load(f)
    return fuel_costs


def load_network_connection_costs():
    """Load network connection costs."""
    with open(GEO_DIR / 'NetworkConnectionCosts.yaml', 'r') as f:
        network_costs = yaml.safe_load(f)
    return network_costs


def load_flow_data():
    """Load flow data from results."""
    f_files = [f for f in os.listdir(RESULTS_DIR) if '_f_dict.yaml' in f]
    if not f_files:
        print("No f_dict files found")
        return {}

    f_files.sort()
    latest_f = f_files[-1]
    print(f"Loading flow data from: {latest_f}")

    with open(RESULTS_DIR / latest_f, 'r') as f:
        f_dict = yaml.safe_load(f)
    return f_dict


def calculate_freight_flow_by_region(nodes, paths, odpairs, f_dict):
    """Calculate freight flow intensity by NUTS2 region for each year."""
    # Parse flow by path and year
    flow_by_path_year = defaultdict(lambda: defaultdict(float))

    for key_str, value in f_dict.items():
        # Format: (year, (mode, odpair, path), (mode, tv), gen)
        match = re.match(r'\((\d+),\s*\((\d+),\s*(\d+),\s*(\d+)\),\s*\((\d+),\s*(\d+)\),\s*(\d+)\)', key_str)
        if match:
            year = int(match.group(1))
            path_id = int(match.group(4))
            flow_by_path_year[path_id][year] += value

    # Aggregate by region (nodes on each path)
    flow_by_region_year = defaultdict(lambda: defaultdict(float))

    for path_id, year_flows in flow_by_path_year.items():
        if path_id in paths:
            sequence = paths[path_id].get('sequence', [])
            for geo_id in sequence:
                if geo_id in nodes:
                    region = nodes[geo_id].get('nuts2_region')
                    if region:
                        for year, flow in year_flows.items():
                            flow_by_region_year[region][year] += flow

    return flow_by_region_year


def calculate_weighted_breaks_by_region(nodes, paths, odpairs, breaks, f_dict):
    """Calculate mandatory breaks weighted by flow for each region."""
    # First get flow by path and year
    flow_by_path_year = defaultdict(lambda: defaultdict(float))

    for key_str, value in f_dict.items():
        match = re.match(r'\((\d+),\s*\((\d+),\s*(\d+),\s*(\d+)\),\s*\((\d+),\s*(\d+)\),\s*(\d+)\)', key_str)
        if match:
            year = int(match.group(1))
            path_id = int(match.group(4))
            flow_by_path_year[path_id][year] += value

    # Now weight breaks by flow
    weighted_breaks_by_region_year = defaultdict(lambda: defaultdict(float))
    break_count_by_region = defaultdict(lambda: defaultdict(int))

    for brk in breaks:
        path_id = brk.get('path_id')
        # Use latest_geo_id from MandatoryBreaks structure
        geo_id = brk.get('latest_geo_id')
        # Break duration is 0.75 hours (45 min standard)
        break_duration = 0.75

        if geo_id is not None and geo_id in nodes:
            region = nodes[geo_id].get('nuts2_region')
            if region:
                for year in TARGET_YEARS:
                    flow = flow_by_path_year.get(path_id, {}).get(year, 0)
                    if flow > 0:
                        weighted_breaks_by_region_year[region][year] += break_duration * flow
                        break_count_by_region[region][year] += 1

    return weighted_breaks_by_region_year, break_count_by_region


def calculate_levelized_fuel_prices(nodes, fuel_costs, network_costs):
    """Calculate levelized fuel prices by region (electricity prices only)."""
    prices_by_region_year = defaultdict(lambda: defaultdict(float))

    # Create mapping from location (geo_id) to electricity prices
    geo_to_elec_price = {}
    for fc in fuel_costs:
        if fc.get('fuel') == 'electricity':
            geo_id = fc.get('location')
            # Use cost_per_kWh field (41 values for years 2020-2060)
            prices = fc.get('cost_per_kWh', [])
            if geo_id is not None and prices:
                # Only store first entry per geo_id (type 1 charging)
                if geo_id not in geo_to_elec_price:
                    geo_to_elec_price[geo_id] = prices

    # Calculate electricity price for each region
    for geo_id, node in nodes.items():
        region = node.get('nuts2_region')
        if region:
            elec_prices = geo_to_elec_price.get(geo_id, [])

            for year in TARGET_YEARS:
                # Year index: 2028 = index 8, 2032 = index 12, 2036 = index 16
                year_idx = year - 2020

                if year_idx < len(elec_prices):
                    elec_price = elec_prices[year_idx]
                    if elec_price > 0:
                        prices_by_region_year[region][year] = elec_price

    return prices_by_region_year


def create_maps(nodes, flow_by_region, weighted_breaks, fuel_prices):
    """Create choropleth maps for the three metrics."""

    # Prepare data for mapping
    regions_data = []
    for geo_id, node in nodes.items():
        region = node.get('nuts2_region')
        if region and node.get('lat') and node.get('lon'):
            for year in TARGET_YEARS:
                regions_data.append({
                    'nuts2': region,
                    'year': year,
                    'lat': node['lat'],
                    'lon': node['lon'],
                    'country': node.get('country'),
                    'flow': flow_by_region.get(region, {}).get(year, 0),
                    'weighted_breaks': weighted_breaks.get(region, {}).get(year, 0),
                    'fuel_price': fuel_prices.get(region, {}).get(year, 0),
                })

    df = pd.DataFrame(regions_data)

    # Drop duplicates (same region appears multiple times)
    df = df.drop_duplicates(subset=['nuts2', 'year'])

    print(f"\nData summary:")
    print(f"  Regions: {df['nuts2'].nunique()}")
    print(f"  Years: {df['year'].unique()}")
    print(f"  Flow range: {df['flow'].min():.0f} - {df['flow'].max():.0f}")
    print(f"  Weighted breaks range: {df['weighted_breaks'].min():.2f} - {df['weighted_breaks'].max():.2f}")
    print(f"  Fuel price range: {df['fuel_price'].min():.4f} - {df['fuel_price'].max():.4f}")

    if HAS_GEOPANDAS and SHAPEFILE_PATH.exists():
        create_choropleth_maps(df)
    else:
        create_scatter_maps(df)


def create_scatter_maps(df):
    """Create scatter plot maps when geopandas is not available."""
    fig, axes = plt.subplots(3, 3, figsize=(18, 16))

    metrics = [
        ('flow', 'Freight Flow (kt)', 'YlOrRd'),
        ('weighted_breaks', 'Weighted Breaks (h × kt)', 'Blues'),
        ('fuel_price', 'Fuel Price (EUR/kWh)', 'Greens'),
    ]

    for row, (metric, title, cmap) in enumerate(metrics):
        for col, year in enumerate(TARGET_YEARS):
            ax = axes[row, col]

            year_data = df[df['year'] == year]

            # Normalize for color
            values = year_data[metric].values
            if values.max() > values.min():
                norm = (values - values.min()) / (values.max() - values.min())
            else:
                norm = np.zeros_like(values)

            # Size based on value
            sizes = 50 + 200 * norm

            scatter = ax.scatter(
                year_data['lon'], year_data['lat'],
                c=values, cmap=cmap, s=sizes, alpha=0.7, edgecolors='black', linewidths=0.5
            )

            ax.set_xlim(4, 32)
            ax.set_ylim(44, 72)
            ax.set_title(f'{title}\n{year}', fontsize=11)
            ax.set_xlabel('Longitude')
            ax.set_ylabel('Latitude')

            plt.colorbar(scatter, ax=ax, shrink=0.6)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'regional_analysis_scatter_maps.pdf', dpi=150, bbox_inches='tight')
    plt.savefig(OUTPUT_DIR / 'regional_analysis_scatter_maps.png', dpi=150, bbox_inches='tight')
    print(f"\nSaved scatter maps to {OUTPUT_DIR / 'regional_analysis_scatter_maps.pdf'}")
    plt.close()


def create_choropleth_maps(df):
    """Create proper choropleth maps using geopandas."""
    # Load NUTS shapefile
    gdf = gpd.read_file(SHAPEFILE_PATH)

    # Filter to NUTS2 level and relevant countries
    countries = ['AT', 'DE', 'DK', 'IT', 'NO', 'SE']
    gdf_nuts2 = gdf[(gdf['LEVL_CODE'] == 2) & (gdf['CNTR_CODE'].isin(countries))].copy()

    print(f"Loaded {len(gdf_nuts2)} NUTS2 regions from shapefile")

    # Create figure
    fig, axes = plt.subplots(3, 3, figsize=(18, 18))

    metrics = [
        ('flow', 'Freight Flow (kt)', 'YlOrRd'),
        ('weighted_breaks', 'Weighted Breaks (h × kt)', 'Blues'),
        ('fuel_price', 'Fuel Price (EUR/kWh)', 'Greens'),
    ]

    for row, (metric, title, cmap) in enumerate(metrics):
        for col, year in enumerate(TARGET_YEARS):
            ax = axes[row, col]

            # Get year-specific data
            year_data = df[df['year'] == year].copy()

            # Merge with shapefile
            gdf_merged = gdf_nuts2.merge(
                year_data[['nuts2', metric]],
                left_on='NUTS_ID',
                right_on='nuts2',
                how='left'
            )

            # Plot
            gdf_merged.plot(
                column=metric,
                ax=ax,
                cmap=cmap,
                legend=True,
                legend_kwds={'shrink': 0.6, 'label': title},
                missing_kwds={'color': 'lightgrey'},
                edgecolor='black',
                linewidth=0.3
            )

            ax.set_xlim(4, 32)
            ax.set_ylim(44, 72)
            ax.set_title(f'{title}\n{year}', fontsize=12, fontweight='bold')
            ax.axis('off')

    plt.suptitle('Regional Analysis: Freight Flow, Breaks, and Fuel Prices', fontsize=14, fontweight='bold', y=0.98)
    plt.tight_layout()

    plt.savefig(OUTPUT_DIR / 'regional_analysis_choropleth_maps.pdf', dpi=150, bbox_inches='tight')
    plt.savefig(OUTPUT_DIR / 'regional_analysis_choropleth_maps.png', dpi=150, bbox_inches='tight')
    print(f"\nSaved choropleth maps to {OUTPUT_DIR / 'regional_analysis_choropleth_maps.pdf'}")
    plt.close()


def main():
    """Main function to create regional analysis maps."""
    print("="*80)
    print("CREATING REGIONAL ANALYSIS MAPS")
    print("="*80)

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load data
    print("\n1. Loading data...")
    nodes = load_geographic_elements()
    print(f"   Loaded {len(nodes)} nodes")

    paths = load_paths()
    print(f"   Loaded {len(paths)} paths")

    odpairs = load_odpairs()
    print(f"   Loaded {len(odpairs)} OD pairs")

    breaks = load_mandatory_breaks()
    print(f"   Loaded {len(breaks)} mandatory breaks")

    fuel_costs = load_fuel_costs()
    print(f"   Loaded {len(fuel_costs)} fuel cost entries")

    network_costs = load_network_connection_costs()
    print(f"   Loaded {len(network_costs)} network cost entries")

    f_dict = load_flow_data()
    print(f"   Loaded {len(f_dict)} flow entries")

    # Calculate metrics
    print("\n2. Calculating metrics...")

    print("   - Freight flow by region...")
    flow_by_region = calculate_freight_flow_by_region(nodes, paths, odpairs, f_dict)

    print("   - Weighted breaks by region...")
    weighted_breaks, break_counts = calculate_weighted_breaks_by_region(nodes, paths, odpairs, breaks, f_dict)

    print("   - Fuel prices by region...")
    fuel_prices = calculate_levelized_fuel_prices(nodes, fuel_costs, network_costs)

    # Create maps
    print("\n3. Creating maps...")
    create_maps(nodes, flow_by_region, weighted_breaks, fuel_prices)

    print("\n" + "="*80)
    print("COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()
