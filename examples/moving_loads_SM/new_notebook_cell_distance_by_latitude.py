# ==============================================================================
# AVERAGE DISTANCE TO PREVIOUS NODE BY LATITUDE
# ==============================================================================
from scipy.ndimage import gaussian_filter1d

def calculate_average_distance_by_nuts2(case_study_name):
    """
    Calculate the average distance_from_previous for each NUTS2 region.

    This shows the average segment length connecting to each region,
    which indicates network density and geographic spacing.

    Returns:
        dict: {nuts2_id: {'lat': X, 'avg_distance_km': Y, 'num_segments': N}}
    """
    input_data = loaded_runs[case_study_name]["input_data"]

    # Load geographic elements and filter to NUTS2 nodes
    geo_elements = input_data['GeographicElement']
    nuts2_lookup = {}
    for geo in geo_elements:
        if geo['type'] == 'node' and 'nuts2_region' in geo and geo['nuts2_region']:
            nuts2_lookup[geo['id']] = {
                'nuts2': geo['nuts2_region'],
                'lat': geo['coordinate_lat'],
                'lon': geo['coordinate_long'],
                'country': geo.get('country', 'UNKNOWN')
            }

    print(f"Found {len(nuts2_lookup)} NUTS2 regions")

    # Load all paths
    paths = input_data['Path']

    # For each NUTS2 region, collect all incoming distances
    nuts2_distances = {}

    for path in paths:
        sequence = path['sequence']
        distance_from_previous = path['distance_from_previous']

        # Process each node in the path
        for i, node_id in enumerate(sequence):
            if node_id in nuts2_lookup:
                nuts2_id = nuts2_lookup[node_id]['nuts2']
                distance_km = distance_from_previous[i]

                # Initialize if needed
                if nuts2_id not in nuts2_distances:
                    nuts2_distances[nuts2_id] = {
                        'lat': nuts2_lookup[node_id]['lat'],
                        'country': nuts2_lookup[node_id]['country'],
                        'distances': []
                    }

                # Add this distance (if non-zero)
                if distance_km > 0:
                    nuts2_distances[nuts2_id]['distances'].append(distance_km)

    # Calculate average distance for each NUTS2 region
    nuts2_avg_distances = {}
    for nuts2_id, data in nuts2_distances.items():
        if data['distances']:
            avg_dist = sum(data['distances']) / len(data['distances'])
            nuts2_avg_distances[nuts2_id] = {
                'lat': data['lat'],
                'country': data['country'],
                'avg_distance_km': avg_dist,
                'num_segments': len(data['distances']),
                'min_distance_km': min(data['distances']),
                'max_distance_km': max(data['distances'])
            }

    return nuts2_avg_distances

# Calculate data
print("Calculating average distance to previous node by NUTS2 region...")
distance_data = calculate_average_distance_by_nuts2(case_name)

# Display summary statistics
print("\n" + "="*80)
print("SUMMARY: AVERAGE SEGMENT DISTANCES BY NUTS2 REGION")
print("="*80)

all_avg_distances = [d['avg_distance_km'] for d in distance_data.values()]
print(f"\nTotal NUTS2 regions with data: {len(distance_data)}")
print(f"Overall average segment length: {np.mean(all_avg_distances):.1f} km")
print(f"Median segment length: {np.median(all_avg_distances):.1f} km")
print(f"Min segment length: {np.min(all_avg_distances):.1f} km")
print(f"Max segment length: {np.max(all_avg_distances):.1f} km")
print(f"Std deviation: {np.std(all_avg_distances):.1f} km")

# Show by country
print("\n" + "="*80)
print("AVERAGE SEGMENT LENGTH BY COUNTRY")
print("="*80)

country_distances = {}
for nuts2_id, data in distance_data.items():
    country = data['country']
    if country not in country_distances:
        country_distances[country] = []
    country_distances[country].append(data['avg_distance_km'])

corridor_countries = ['IT', 'AT', 'DE', 'DK', 'NO', 'SE']
for country in sorted(corridor_countries):
    if country in country_distances:
        dists = country_distances[country]
        print(f"{country}: {np.mean(dists):>6.1f} km (n={len(dists):>2} regions, "
              f"range: {np.min(dists):.0f}-{np.max(dists):.0f} km)")

# ==============================================================================
# BEAUTIFUL PLOT: AVERAGE DISTANCE BY LATITUDE
# ==============================================================================

# Prepare plotting data
plotting_data = []
for nuts2_id, metrics in distance_data.items():
    plotting_data.append({
        'nuts2': nuts2_id,
        'lat': metrics['lat'],
        'distance': metrics['avg_distance_km'],
        'num_segments': metrics['num_segments'],
        'country': metrics['country']
    })

# Sort by latitude
plotting_data.sort(key=lambda x: x['lat'])

# Extract arrays
lats = np.array([d['lat'] for d in plotting_data])
distances = np.array([d['distance'] for d in plotting_data])

# Apply Gaussian smoothing
sigma = 2.0
distances_smooth = gaussian_filter1d(distances, sigma=sigma)

# Set style
plt.style.use('seaborn-v0_8-darkgrid')

# Create figure
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 10), sharey=True,
                                gridspec_kw={'wspace': 0.15})

# ==============================================================================
# LEFT PANEL: SMOOTHED CURVE
# ==============================================================================

# Fill area plot
ax1.fill_betweenx(lats, 0, distances_smooth,
                  color='#3498DB', alpha=0.6, edgecolor='darkblue', linewidth=2)

# Add outline
ax1.plot(distances_smooth, lats, 'k-', linewidth=2.5, alpha=0.5)

# Styling
ax1.set_xlabel('Average Segment Distance (km)', fontsize=14, fontweight='bold', labelpad=10)
ax1.set_ylabel('Latitude (°N)', fontsize=14, fontweight='bold', labelpad=10)
ax1.set_title('Network Density\n(Smoothed)', fontsize=15, fontweight='bold', pad=15,
             bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgray', alpha=0.3))

ax1.grid(True, alpha=0.25, linestyle='--', linewidth=0.8)
ax1.set_xlim(left=0)

# Enhanced axis styling
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)
ax1.spines['left'].set_linewidth(1.5)
ax1.spines['bottom'].set_linewidth(1.5)
ax1.tick_params(axis='both', which='major', labelsize=11, width=1.5, length=6)

# ==============================================================================
# RIGHT PANEL: SCATTER PLOT (RAW DATA)
# ==============================================================================

# Color by country
country_colors = {
    'IT': '#E74C3C',  # Red
    'AT': '#F39C12',  # Orange
    'DE': '#3498DB',  # Blue
    'DK': '#2ECC71',  # Green
    'NO': '#9B59B6',  # Purple
    'SE': '#E67E22'   # Dark orange
}

for country in corridor_countries:
    country_data = [d for d in plotting_data if d['country'] == country]
    if country_data:
        country_lats = [d['lat'] for d in country_data]
        country_dists = [d['distance'] for d in country_data]

        ax2.scatter(country_dists, country_lats,
                   color=country_colors.get(country, '#95A5A6'),
                   s=80, alpha=0.7, edgecolor='black', linewidth=0.8,
                   label=country, zorder=5)

# Styling
ax2.set_xlabel('Average Segment Distance (km)', fontsize=14, fontweight='bold', labelpad=10)
ax2.set_title('By NUTS2 Region\n(Raw Data)', fontsize=15, fontweight='bold', pad=15,
             bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgray', alpha=0.3))

ax2.grid(True, alpha=0.25, linestyle='--', linewidth=0.8)
ax2.set_xlim(left=0)

# Enhanced axis styling
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)
ax2.spines['bottom'].set_linewidth(1.5)
ax2.tick_params(axis='both', which='major', labelsize=11, width=1.5, length=6)

# Legend
legend = ax2.legend(loc='lower right', fontsize=11, framealpha=0.95,
                   edgecolor='black', fancybox=True, shadow=True,
                   title='Country', title_fontsize=12)
legend.get_frame().set_linewidth(1.5)

# ==============================================================================
# ADD COUNTRY LABELS AND BORDERS
# ==============================================================================

# Load country data
country_centroids = pd.read_csv('country_centroids.csv')
borders_df = pd.read_csv('country_southern_borders.csv')

corridor_countries = ['IT', 'AT', 'DE', 'DK', 'NO', 'SE']
country_data = country_centroids[country_centroids['CNTR_CODE'].isin(corridor_countries)]

for ax in [ax1, ax2]:
    ylim = ax.get_ylim()

    # Add country labels (only on left panel)
    if ax == ax1:
        for _, row in country_data.iterrows():
            country_code = row['CNTR_CODE']
            lat = row['centroid_lat']

            if ylim[0] <= lat <= ylim[1]:
                ax.text(-0.12, lat, country_code, transform=ax.get_yaxis_transform(),
                       fontsize=11, fontweight='bold', va='center', ha='right',
                       bbox=dict(boxstyle='round,pad=0.4', facecolor='#FFE44D',
                                edgecolor='black', linewidth=1.2, alpha=0.9))

    # Add border lines
    for _, row in borders_df.iterrows():
        country = row['CNTR_CODE']
        border_lat = row['southern_border_lat']

        if country in corridor_countries and ylim[0] <= border_lat <= ylim[1]:
            ax.axhline(y=border_lat, color='#34495E', linestyle='--',
                      linewidth=1.2, alpha=0.5, zorder=1)

# Overall title
fig.suptitle('Average Network Segment Distance by Latitude\n' +
            'Scandinavian-Mediterranean Corridor',
            fontsize=18, fontweight='bold', y=0.98,
            bbox=dict(boxstyle='round,pad=0.8', facecolor='lightblue', alpha=0.2))

# Save with high quality
plt.savefig('distance_by_latitude.png', dpi=400,
            bbox_inches='tight', facecolor='white', edgecolor='none')
print("\n✓ High-quality plot saved as 'distance_by_latitude.png' (400 DPI)")
plt.show()

# ==============================================================================
# ADDITIONAL ANALYSIS: TOP/BOTTOM REGIONS
# ==============================================================================

print("\n" + "="*80)
print("TOP 10 REGIONS WITH LONGEST AVERAGE SEGMENT DISTANCES")
print("="*80)

sorted_by_distance = sorted(plotting_data, key=lambda x: x['distance'], reverse=True)

print(f"{'Rank':<6} {'NUTS2':<8} {'Country':<10} {'Latitude':>10} {'Avg Distance':>15} {'# Segments':>12}")
print("-" * 80)

for i, d in enumerate(sorted_by_distance[:10], 1):
    print(f"{i:<6} {d['nuts2']:<8} {d['country']:<10} {d['lat']:>10.2f} {d['distance']:>15.1f} km {d['num_segments']:>12}")

print("\n" + "="*80)
print("TOP 10 REGIONS WITH SHORTEST AVERAGE SEGMENT DISTANCES")
print("="*80)

print(f"{'Rank':<6} {'NUTS2':<8} {'Country':<10} {'Latitude':>10} {'Avg Distance':>15} {'# Segments':>12}")
print("-" * 80)

for i, d in enumerate(sorted_by_distance[-10:][::-1], 1):
    print(f"{i:<6} {d['nuts2']:<8} {d['country']:<10} {d['lat']:>10.2f} {d['distance']:>15.1f} km {d['num_segments']:>12}")

# ==============================================================================
# INTERPRETATION GUIDE
# ==============================================================================

print("\n" + "="*80)
print("INTERPRETATION GUIDE: NETWORK SEGMENT DISTANCES")
print("="*80)
print("""
📏 WHAT THIS SHOWS:
   • Average distance between consecutive nodes in paths passing through each NUTS2 region
   • Indicates network density: shorter distances = denser network
   • Based on all path sequences in the model, not flow-weighted

🔍 KEY INSIGHTS:
   • HIGH values (long distances):
     - Sparse network coverage
     - Regions serving as waypoints between distant areas
     - Potentially lower infrastructure density

   • LOW values (short distances):
     - Dense network coverage
     - Many nearby connection points
     - Potentially high infrastructure density
     - Urban/metropolitan regions

📊 COMPARISON:
   • Left panel: Smoothed trend showing geographic patterns
   • Right panel: Raw data colored by country

🌍 GEOGRAPHIC PATTERNS:
   • Northern regions (NO, SE, DK): May have longer distances due to geography
   • Central regions (DE, AT): Typically denser networks
   • Southern regions (IT): Varies by region (Alps vs plains)

⚠️  IMPORTANT NOTES:
   • This is NOT flow-weighted (doesn't account for traffic volume)
   • Represents network topology, not actual freight patterns
   • Based on distance_from_previous array in Path data structure
   • Zero distances (self-loops) are excluded from averages
""")
