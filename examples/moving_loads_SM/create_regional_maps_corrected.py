"""
Create regional analysis maps with corrected path distances showing:
1. Mandatory breaks by region (OLD vs NEW comparison)
2. Freight demand (tonnes) by region
3. Electricity/charging costs by region

Uses the corrected fixed_nuts_2 data.
"""

import yaml
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict
from pathlib import Path

try:
    import geopandas as gpd
    HAS_GEOPANDAS = True
except ImportError:
    HAS_GEOPANDAS = False
    print("Warning: geopandas not available, using scatter plots")

# Configuration
SCRIPT_DIR = Path(__file__).parent
GEO_DIR = SCRIPT_DIR / 'input_data' / 'fixed_nuts_2'
# Use a case directory for FuelCost.yaml (not in fixed_nuts_2)
FUEL_COST_DIR = SCRIPT_DIR / 'input_data' / 'case_20251110_160304_var_var'
SHAPEFILE_PATH = SCRIPT_DIR / 'data' / 'NUTS_RG_20M_2021_4326.shp' / 'NUTS_RG_20M_2021_4326.shp'
OUTPUT_DIR = SCRIPT_DIR / 'figures'


def load_data():
    """Load all required data files."""
    print("Loading data...")

    # Geographic elements
    with open(GEO_DIR / 'GeographicElement.yaml', 'r') as f:
        geo_elements = yaml.safe_load(f)

    nodes = {}
    for g in geo_elements:
        if g.get('type') == 'node':
            nodes[g['id']] = {
                'nuts2': g.get('nuts2_region'),
                'country': g.get('country'),
                'lat': g.get('coordinate_lat'),
                'lon': g.get('coordinate_long'),
            }
    print(f"  Loaded {len(nodes)} nodes")

    # Old breaks (backup)
    with open(GEO_DIR / 'MandatoryBreaks.yaml.backup', 'r') as f:
        old_breaks = yaml.safe_load(f)
    print(f"  Loaded {len(old_breaks)} old breaks")

    # New breaks (corrected)
    with open(GEO_DIR / 'MandatoryBreaks.yaml', 'r') as f:
        new_breaks = yaml.safe_load(f)
    print(f"  Loaded {len(new_breaks)} new breaks")

    # OD pairs (demand)
    with open(GEO_DIR / 'Odpair.yaml', 'r') as f:
        odpairs = yaml.safe_load(f)
    print(f"  Loaded {len(odpairs)} OD pairs")

    # Fuel costs (from a case directory since not in fixed_nuts_2)
    with open(FUEL_COST_DIR / 'FuelCost.yaml', 'r') as f:
        fuel_costs = yaml.safe_load(f)
    print(f"  Loaded {len(fuel_costs)} fuel cost entries")

    return nodes, old_breaks, new_breaks, odpairs, fuel_costs


def calculate_breaks_by_region(breaks, nodes):
    """Count breaks by NUTS2 region."""
    breaks_by_region = defaultdict(int)
    for b in breaks:
        geo_id = b.get('latest_geo_id')
        if geo_id in nodes:
            region = nodes[geo_id].get('nuts2')
            if region:
                breaks_by_region[region] += 1
    return dict(breaks_by_region)


def calculate_demand_by_region(odpairs, nodes):
    """Calculate total demand (tonnes) by origin and destination region."""
    demand_by_origin = defaultdict(float)
    demand_by_dest = defaultdict(float)

    for od in odpairs:
        # Use 'from'/'to' keys (not 'origin'/'destination')
        origin_id = od.get('from')
        dest_id = od.get('to')

        # Get demand from 'F' key (sum across years if list)
        demand = od.get('F', 0)
        if demand is None:
            demand = 0
        if isinstance(demand, list):
            demand = sum(demand)  # Total across all years

        # By origin
        if origin_id is not None and origin_id in nodes:
            region = nodes[origin_id].get('nuts2')
            if region:
                demand_by_origin[region] += demand

        # By destination
        if dest_id is not None and dest_id in nodes:
            region = nodes[dest_id].get('nuts2')
            if region:
                demand_by_dest[region] += demand

    # Combined (origin + destination)
    all_regions = set(demand_by_origin.keys()) | set(demand_by_dest.keys())
    demand_combined = {r: demand_by_origin.get(r, 0) + demand_by_dest.get(r, 0) for r in all_regions}

    return demand_combined


def calculate_fuel_costs_by_region(fuel_costs, nodes, year_idx=12):
    """Calculate electricity costs by region for a specific year (default: 2032)."""
    costs_by_region = {}

    for fc in fuel_costs:
        if fc.get('fuel') == 'electricity':
            geo_id = fc.get('location')
            if geo_id in nodes:
                region = nodes[geo_id].get('nuts2')
                costs = fc.get('cost_per_kWh', [])
                if region and costs and year_idx < len(costs):
                    # Only store first (avoid duplicates from charging types)
                    if region not in costs_by_region:
                        costs_by_region[region] = costs[year_idx]

    return costs_by_region


def create_maps(nodes, old_breaks_region, new_breaks_region, demand_region, costs_region):
    """Create choropleth or scatter maps."""

    # Prepare data
    all_regions = set(old_breaks_region.keys()) | set(new_breaks_region.keys()) | set(demand_region.keys()) | set(costs_region.keys())

    # Get coordinates for each region
    region_coords = {}
    for node_id, node in nodes.items():
        region = node.get('nuts2')
        if region and region not in region_coords:
            if node.get('lat') and node.get('lon'):
                region_coords[region] = (node['lat'], node['lon'])

    df = pd.DataFrame([{
        'nuts2': r,
        'lat': region_coords.get(r, (None, None))[0],
        'lon': region_coords.get(r, (None, None))[1],
        'old_breaks': old_breaks_region.get(r, 0),
        'new_breaks': new_breaks_region.get(r, 0),
        'break_change': new_breaks_region.get(r, 0) - old_breaks_region.get(r, 0),
        'demand': demand_region.get(r, 0),
        'elec_cost': costs_region.get(r, 0),
    } for r in all_regions])

    df = df.dropna(subset=['lat', 'lon'])

    print(f"\nData summary:")
    print(f"  Regions: {len(df)}")
    print(f"  Old breaks range: {df['old_breaks'].min():.0f} - {df['old_breaks'].max():.0f}")
    print(f"  New breaks range: {df['new_breaks'].min():.0f} - {df['new_breaks'].max():.0f}")
    print(f"  Demand range: {df['demand'].min():.0f} - {df['demand'].max():.0f}")
    print(f"  Elec cost range: {df['elec_cost'].min():.4f} - {df['elec_cost'].max():.4f}")

    if HAS_GEOPANDAS and SHAPEFILE_PATH.exists():
        create_choropleth_maps(df)
    else:
        create_scatter_maps(df)


def create_scatter_maps(df):
    """Create scatter plot maps."""
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))

    # Row 1: Breaks comparison
    # Old breaks
    ax = axes[0, 0]
    scatter = ax.scatter(df['lon'], df['lat'], c=df['old_breaks'], cmap='Reds',
                         s=50 + df['old_breaks']/5, alpha=0.7, edgecolors='black', linewidths=0.3)
    ax.set_xlim(4, 32)
    ax.set_ylim(44, 72)
    ax.set_title('OLD: Mandatory Breaks\n(before distance fix)', fontsize=11)
    plt.colorbar(scatter, ax=ax, shrink=0.6, label='Break count')

    # New breaks
    ax = axes[0, 1]
    scatter = ax.scatter(df['lon'], df['lat'], c=df['new_breaks'], cmap='Reds',
                         s=50 + df['new_breaks']/5, alpha=0.7, edgecolors='black', linewidths=0.3)
    ax.set_xlim(4, 32)
    ax.set_ylim(44, 72)
    ax.set_title('NEW: Mandatory Breaks\n(after distance fix)', fontsize=11)
    plt.colorbar(scatter, ax=ax, shrink=0.6, label='Break count')

    # Change in breaks
    ax = axes[0, 2]
    colors = df['break_change']
    scatter = ax.scatter(df['lon'], df['lat'], c=colors, cmap='RdBu_r',
                         s=50 + abs(df['break_change'])/3, alpha=0.7, edgecolors='black', linewidths=0.3,
                         vmin=-800, vmax=800)
    ax.set_xlim(4, 32)
    ax.set_ylim(44, 72)
    ax.set_title('CHANGE: Breaks\n(red=decrease, blue=increase)', fontsize=11)
    plt.colorbar(scatter, ax=ax, shrink=0.6, label='Change')

    # Row 2: Demand and costs
    # Demand
    ax = axes[1, 0]
    scatter = ax.scatter(df['lon'], df['lat'], c=df['demand'], cmap='YlOrRd',
                         s=50 + df['demand']/1e5, alpha=0.7, edgecolors='black', linewidths=0.3)
    ax.set_xlim(4, 32)
    ax.set_ylim(44, 72)
    ax.set_title('Freight Demand\n(tonnes, all years)', fontsize=11)
    plt.colorbar(scatter, ax=ax, shrink=0.6, label='Tonnes')

    # Electricity costs
    ax = axes[1, 1]
    valid_costs = df[df['elec_cost'] > 0]
    scatter = ax.scatter(valid_costs['lon'], valid_costs['lat'], c=valid_costs['elec_cost'], cmap='Greens',
                         s=100, alpha=0.7, edgecolors='black', linewidths=0.3)
    ax.set_xlim(4, 32)
    ax.set_ylim(44, 72)
    ax.set_title('Electricity Costs\n(EUR/kWh, 2032)', fontsize=11)
    plt.colorbar(scatter, ax=ax, shrink=0.6, label='EUR/kWh')

    # Summary text
    ax = axes[1, 2]
    ax.axis('off')
    summary_text = f"""
    SUMMARY OF CORRECTIONS

    Total Breaks:
      OLD: {df['old_breaks'].sum():,}
      NEW: {df['new_breaks'].sum():,}
      Change: {df['new_breaks'].sum() - df['old_breaks'].sum():+,}

    Biggest Decreases (artifact removed):
      ITH2: {df[df['nuts2']=='ITH2']['break_change'].values[0] if 'ITH2' in df['nuts2'].values else 'N/A':+.0f}
      ITH3: {df[df['nuts2']=='ITH3']['break_change'].values[0] if 'ITH3' in df['nuts2'].values else 'N/A':+.0f}

    Biggest Increases (now correct):
      SE23: {df[df['nuts2']=='SE23']['break_change'].values[0] if 'SE23' in df['nuts2'].values else 'N/A':+.0f}
      ITH5: {df[df['nuts2']=='ITH5']['break_change'].values[0] if 'ITH5' in df['nuts2'].values else 'N/A':+.0f}
    """
    ax.text(0.1, 0.5, summary_text, transform=ax.transAxes, fontsize=10,
            verticalalignment='center', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.suptitle('Regional Analysis Maps (with Corrected Path Distances)', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()

    plt.savefig(OUTPUT_DIR / 'regional_maps_corrected.pdf', bbox_inches='tight', dpi=150)
    plt.savefig(OUTPUT_DIR / 'regional_maps_corrected.png', bbox_inches='tight', dpi=150)
    print(f"\nSaved: {OUTPUT_DIR / 'regional_maps_corrected.pdf'}")
    plt.close()


def create_choropleth_maps(df):
    """Create proper choropleth maps using geopandas."""
    gdf = gpd.read_file(SHAPEFILE_PATH)
    countries = ['AT', 'DE', 'DK', 'IT', 'NO', 'SE']
    gdf_nuts2 = gdf[(gdf['LEVL_CODE'] == 2) & (gdf['CNTR_CODE'].isin(countries))].copy()

    print(f"  Loaded {len(gdf_nuts2)} NUTS2 regions from shapefile")

    # Merge with our data
    gdf_merged = gdf_nuts2.merge(df, left_on='NUTS_ID', right_on='nuts2', how='left')

    fig, axes = plt.subplots(2, 3, figsize=(18, 14))

    # Row 1: Breaks comparison
    # Old breaks
    ax = axes[0, 0]
    gdf_merged.plot(column='old_breaks', ax=ax, cmap='Reds', legend=True,
                    legend_kwds={'shrink': 0.6, 'label': 'Break count'},
                    missing_kwds={'color': 'lightgrey'}, edgecolor='black', linewidth=0.3)
    ax.set_xlim(4, 32)
    ax.set_ylim(44, 72)
    ax.set_title('OLD: Mandatory Breaks\n(before distance fix)', fontsize=12, fontweight='bold')
    ax.axis('off')

    # New breaks
    ax = axes[0, 1]
    gdf_merged.plot(column='new_breaks', ax=ax, cmap='Reds', legend=True,
                    legend_kwds={'shrink': 0.6, 'label': 'Break count'},
                    missing_kwds={'color': 'lightgrey'}, edgecolor='black', linewidth=0.3)
    ax.set_xlim(4, 32)
    ax.set_ylim(44, 72)
    ax.set_title('NEW: Mandatory Breaks\n(after distance fix)', fontsize=12, fontweight='bold')
    ax.axis('off')

    # Change in breaks
    ax = axes[0, 2]
    vmax = max(abs(gdf_merged['break_change'].min()), abs(gdf_merged['break_change'].max()))
    gdf_merged.plot(column='break_change', ax=ax, cmap='RdBu_r', legend=True,
                    legend_kwds={'shrink': 0.6, 'label': 'Change'},
                    missing_kwds={'color': 'lightgrey'}, edgecolor='black', linewidth=0.3,
                    vmin=-vmax, vmax=vmax)
    ax.set_xlim(4, 32)
    ax.set_ylim(44, 72)
    ax.set_title('CHANGE: Breaks\n(red=decrease, blue=increase)', fontsize=12, fontweight='bold')
    ax.axis('off')

    # Row 2: Demand and costs
    # Demand
    ax = axes[1, 0]
    gdf_merged.plot(column='demand', ax=ax, cmap='YlOrRd', legend=True,
                    legend_kwds={'shrink': 0.6, 'label': 'Tonnes'},
                    missing_kwds={'color': 'lightgrey'}, edgecolor='black', linewidth=0.3)
    ax.set_xlim(4, 32)
    ax.set_ylim(44, 72)
    ax.set_title('Freight Demand\n(tonnes, all years)', fontsize=12, fontweight='bold')
    ax.axis('off')

    # Electricity costs
    ax = axes[1, 1]
    gdf_merged.plot(column='elec_cost', ax=ax, cmap='Greens', legend=True,
                    legend_kwds={'shrink': 0.6, 'label': 'EUR/kWh'},
                    missing_kwds={'color': 'lightgrey'}, edgecolor='black', linewidth=0.3)
    ax.set_xlim(4, 32)
    ax.set_ylim(44, 72)
    ax.set_title('Electricity Costs\n(EUR/kWh, 2032)', fontsize=12, fontweight='bold')
    ax.axis('off')

    # Summary text
    ax = axes[1, 2]
    ax.axis('off')

    # Get specific values
    ith2_change = df[df['nuts2']=='ITH2']['break_change'].values[0] if 'ITH2' in df['nuts2'].values else 0
    ith3_change = df[df['nuts2']=='ITH3']['break_change'].values[0] if 'ITH3' in df['nuts2'].values else 0
    se23_change = df[df['nuts2']=='SE23']['break_change'].values[0] if 'SE23' in df['nuts2'].values else 0
    ith5_change = df[df['nuts2']=='ITH5']['break_change'].values[0] if 'ITH5' in df['nuts2'].values else 0

    summary_text = f"""
SUMMARY OF CORRECTIONS

Total Breaks:
  OLD: {int(df['old_breaks'].sum()):,}
  NEW: {int(df['new_breaks'].sum()):,}
  Change: {int(df['new_breaks'].sum() - df['old_breaks'].sum()):+,}

Biggest Decreases (artifact removed):
  ITH2 (Trentino): {int(ith2_change):+,}
  ITH3 (Veneto):   {int(ith3_change):+,}

Biggest Increases (now correct):
  SE23 (Västsverige): {int(se23_change):+,}
  ITH5 (Emilia-R.):   {int(ith5_change):+,}

The ITH2/ITH3 concentration was an
artifact of incorrect distance
proportioning in the Brenner corridor.
    """
    ax.text(0.05, 0.5, summary_text, transform=ax.transAxes, fontsize=11,
            verticalalignment='center', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.suptitle('Regional Analysis Maps (with Corrected Path Distances)', fontsize=14, fontweight='bold', y=0.98)
    plt.tight_layout()

    plt.savefig(OUTPUT_DIR / 'regional_maps_corrected.pdf', bbox_inches='tight', dpi=150)
    plt.savefig(OUTPUT_DIR / 'regional_maps_corrected.png', bbox_inches='tight', dpi=150)
    print(f"\nSaved: {OUTPUT_DIR / 'regional_maps_corrected.pdf'}")
    plt.close()


def main():
    print("="*80)
    print("CREATING REGIONAL ANALYSIS MAPS (CORRECTED DATA)")
    print("="*80)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load data
    nodes, old_breaks, new_breaks, odpairs, fuel_costs = load_data()

    # Calculate metrics by region
    print("\nCalculating metrics...")
    old_breaks_region = calculate_breaks_by_region(old_breaks, nodes)
    new_breaks_region = calculate_breaks_by_region(new_breaks, nodes)
    demand_region = calculate_demand_by_region(odpairs, nodes)
    costs_region = calculate_fuel_costs_by_region(fuel_costs, nodes)

    print(f"  Regions with old breaks: {len(old_breaks_region)}")
    print(f"  Regions with new breaks: {len(new_breaks_region)}")
    print(f"  Regions with demand: {len(demand_region)}")
    print(f"  Regions with costs: {len(costs_region)}")

    # Create maps
    print("\nCreating maps...")
    create_maps(nodes, old_breaks_region, new_breaks_region, demand_region, costs_region)

    print("\n" + "="*80)
    print("COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()
