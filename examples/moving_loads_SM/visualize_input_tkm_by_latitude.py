"""
Visualize INPUT demand (F) TKM distribution by latitude.
This shows where the demand is BEFORE optimization.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import yaml
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
from scipy.ndimage import gaussian_filter1d
import pandas as pd

# Load data
case_study_name = 'case_20251103_114421'
input_dir = f'input_data/{case_study_name}'

print("=" * 80)
print("VISUALIZING INPUT DEMAND (F) TKM BY LATITUDE")
print("=" * 80)

# Load geographic elements
print("\nLoading GeographicElement.yaml...")
with open(f'{input_dir}/GeographicElement.yaml', 'r', encoding='utf-8') as f:
    geo_elements = yaml.safe_load(f)

# Load OD pairs (contains input demand F)
print("Loading Odpair.yaml...")
with open(f'{input_dir}/Odpair.yaml', 'r', encoding='utf-8') as f:
    odpairs = yaml.safe_load(f)

# Load paths
print("Loading Path.yaml...")
with open(f'{input_dir}/Path.yaml', 'r', encoding='utf-8') as f:
    paths = yaml.safe_load(f)

# Create NUTS2 lookup
nuts2_lookup = {}
for geo in geo_elements:
    if geo['type'] == 'node' and 'nuts2_region' in geo and geo['nuts2_region']:
        nuts2_lookup[geo['id']] = {
            'nuts2': geo['nuts2_region'],
            'lat': geo['coordinate_lat'],
            'lon': geo['coordinate_long'],
            'country': geo['country']
        }

# Create path lookup
path_lookup = {}
for path in paths:
    path_lookup[path['id']] = {
        'sequence': path['sequence'],
        'distance_from_previous': path['distance_from_previous']
    }

print(f"\nFound {len(nuts2_lookup)} NUTS2 nodes")
print(f"Found {len(odpairs)} OD pairs")
print(f"Found {len(paths)} paths")

# Calculate TKM by NUTS2 region for first 3 years
print("\nCalculating TKM by NUTS2 region for years 0, 1, 2...")

# We'll calculate for 3 time snapshots (years 0, 10, 20 in the demand array)
year_indices = [0, 10, 20]  # First year, year 10, year 20
year_labels = ['Year 1', 'Year 11', 'Year 21']

tkm_by_nuts2_year = {
    year_idx: defaultdict(float) for year_idx in year_indices
}

for od in odpairs:
    odpair_id = od['id']
    path_id = od.get('path_id')
    F_values = od['F']  # List of demand by year

    if path_id is None or path_id not in path_lookup:
        continue

    path_info = path_lookup[path_id]
    sequence = path_info['sequence']
    distance_from_previous = path_info['distance_from_previous']

    # Calculate for each year
    for year_idx in year_indices:
        if year_idx < len(F_values):
            demand = F_values[year_idx]

            # Calculate TKM through each NUTS2 node
            for i, node_id in enumerate(sequence):
                if node_id not in nuts2_lookup:
                    continue

                node_info = nuts2_lookup[node_id]
                nuts2 = node_info['nuts2']
                lat = node_info['lat']

                segment_distance = distance_from_previous[i]
                tkm_segment = demand * segment_distance

                tkm_by_nuts2_year[year_idx][(nuts2, lat)] += tkm_segment

print("\nPreparing visualization data...")

# Prepare data for plotting
fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharey=True)
fig.suptitle('INPUT Demand (F) - TKM Distribution by Latitude', fontsize=16, fontweight='bold')

# Load country centroids for labels
centroids_df = pd.read_csv('country_centroids.csv')
borders_df = pd.read_csv('country_southern_borders.csv')

for idx, (year_idx, year_label) in enumerate(zip(year_indices, year_labels)):
    ax = axes[idx]

    tkm_data = tkm_by_nuts2_year[year_idx]

    if not tkm_data:
        ax.text(0.5, 0.5, 'No data', ha='center', va='center', transform=ax.transAxes)
        ax.set_title(year_label)
        continue

    # Extract latitude and TKM
    lats = []
    tkms = []
    for (nuts2, lat), tkm in tkm_data.items():
        lats.append(lat)
        tkms.append(tkm)

    # Sort by latitude
    sorted_indices = np.argsort(lats)
    lats_sorted = np.array(lats)[sorted_indices]
    tkms_sorted = np.array(tkms)[sorted_indices]

    # Apply Gaussian smoothing
    sigma = 2.0  # Smoothing parameter
    tkms_smoothed = gaussian_filter1d(tkms_sorted, sigma=sigma)

    # Plot
    ax.fill_betweenx(lats_sorted, 0, tkms_smoothed / 1e6,  # Convert to million TKM
                     color='steelblue', alpha=0.6, edgecolor='darkblue', linewidth=1.5)

    ax.set_xlabel('TKM (millions)', fontsize=12)
    if idx == 0:
        ax.set_ylabel('Latitude (°N)', fontsize=12)
    ax.set_title(year_label, fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle='--')

    # Add country labels on the right y-axis
    ax2 = ax.twinx()
    ax2.set_ylim(ax.get_ylim())
    ax2.set_ylabel('')

    # Add country code labels
    ylim = ax.get_ylim()
    corridor_countries = ['IT', 'AT', 'DE', 'DK', 'SE', 'NO']

    for _, row in centroids_df.iterrows():
        country = row['CNTR_CODE']
        lat = row['centroid_lat']

        if country in corridor_countries and ylim[0] <= lat <= ylim[1]:
            ax2.text(1.02, lat, country, transform=ax2.get_yaxis_transform(),
                    fontsize=10, fontweight='bold', va='center',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))

    # Add border lines
    for _, row in borders_df.iterrows():
        country = row['CNTR_CODE']
        border_lat = row['southern_border_lat']

        if country in corridor_countries and ylim[0] <= border_lat <= ylim[1]:
            ax.axhline(y=border_lat, color='gray', linestyle='--',
                      linewidth=0.8, alpha=0.5, zorder=1)

    ax2.set_yticks([])

    # Add statistics
    total_tkm = tkms_sorted.sum() / 1e9  # Convert to billion
    max_tkm_idx = np.argmax(tkms_smoothed)
    max_lat = lats_sorted[max_tkm_idx]

    ax.text(0.02, 0.98, f'Total: {total_tkm:.1f}B TKM\nPeak: {max_lat:.1f}°N',
           transform=ax.transAxes, fontsize=10,
           verticalalignment='top',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

plt.tight_layout()

# Save figure
output_file = 'input_demand_tkm_by_latitude.png'
plt.savefig(output_file, dpi=300, bbox_inches='tight')
print(f"\nSaved visualization to: {output_file}")

# Print summary statistics
print("\n" + "=" * 80)
print("SUMMARY STATISTICS")
print("=" * 80)

for year_idx, year_label in zip(year_indices, year_labels):
    tkm_data = tkm_by_nuts2_year[year_idx]

    if not tkm_data:
        continue

    # Group by country
    country_tkm = defaultdict(float)
    for (nuts2, lat), tkm in tkm_data.items():
        # Find country for this NUTS2
        for node_id, info in nuts2_lookup.items():
            if info['nuts2'] == nuts2:
                country_tkm[info['country']] += tkm
                break

    total_tkm = sum(tkm_data.values())

    print(f"\n{year_label}:")
    print(f"  Total TKM: {total_tkm/1e9:.2f} billion")
    print(f"  TKM by country:")
    for country in sorted(country_tkm.keys()):
        tkm = country_tkm[country]
        pct = 100 * tkm / total_tkm if total_tkm > 0 else 0
        print(f"    {country}: {tkm/1e9:>8.2f}B ({pct:>5.1f}%)")

# Also create a detailed table of top regions
print("\n" + "=" * 80)
print("TOP 20 NUTS2 REGIONS BY INPUT TKM (Year 1)")
print("=" * 80)

year_0_data = [(nuts2, lat, tkm) for (nuts2, lat), tkm in tkm_by_nuts2_year[0].items()]
year_0_data.sort(key=lambda x: x[2], reverse=True)

print(f"{'Rank':<6} {'NUTS2':<10} {'Country':<8} {'Latitude':>10} {'TKM (millions)':>18}")
print("-" * 80)

for rank, (nuts2, lat, tkm) in enumerate(year_0_data[:20], 1):
    # Find country
    country = 'UNK'
    for node_id, info in nuts2_lookup.items():
        if info['nuts2'] == nuts2:
            country = info['country']
            break

    print(f"{rank:<6} {nuts2:<10} {country:<8} {lat:>10.2f} {tkm/1e6:>18,.1f}")

print("\nVisualization complete!")
print(f"Check '{output_file}' to see the INPUT demand TKM distribution by latitude.")
