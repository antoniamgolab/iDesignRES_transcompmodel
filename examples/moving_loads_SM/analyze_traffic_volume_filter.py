"""
Analyze the impact of min_freight_threshold filter on INTERNATIONAL-ONLY routes

Calculate updated statistics for the 1000 trucks/year filter now that
cross_border_only = True
"""

import pandas as pd
from pathlib import Path
import numpy as np

# Load traffic data
data_dir = Path("data/Trucktraffic_NUTS3")
traffic_file = data_dir / "01_Trucktrafficflow.csv"

print("="*80)
print("ANALYZING TRAFFIC VOLUME FILTER IMPACT")
print("(International routes only - cross_border_only = True)")
print("="*80)

if not traffic_file.exists():
    print(f"[ERROR] Traffic file not found: {traffic_file}")
    exit(1)

# Load traffic data
truck_traffic = pd.read_csv(traffic_file)
print(f"\n1. Loaded traffic data: {len(truck_traffic):,} total routes")

# Calculate Total_distance if not present (same as preprocessing script)
if 'Total_distance' not in truck_traffic.columns:
    truck_traffic['Total_distance'] = (
        truck_traffic['Distance_from_origin_region_to_E_road'] +
        truck_traffic['Distance_within_E_road'] +
        truck_traffic['Distance_from_E_road_to_destination_region']
    )

# Filter to international routes only (cross-border)
# Extract country codes from NUTS-3 region IDs (first 2 characters)
truck_traffic['origin_country'] = truck_traffic['ID_origin_region'].astype(str).str[:2]
truck_traffic['dest_country'] = truck_traffic['ID_destination_region'].astype(str).str[:2]

# Keep only cross-border routes
international_traffic = truck_traffic[
    truck_traffic['origin_country'] != truck_traffic['dest_country']
].copy()

print(f"2. International routes only: {len(international_traffic):,} routes")
print(f"   (Removed {len(truck_traffic) - len(international_traffic):,} domestic routes)")

# Calculate baseline statistics
total_routes_international = len(international_traffic)
total_traffic_volume = international_traffic['Traffic_flow_trucks_2030'].sum()
total_tkm = (international_traffic['Traffic_flow_trucks_2030'] *
             international_traffic['Total_distance']).sum()

print(f"\n3. Baseline (international routes):")
print(f"   Routes: {total_routes_international:,}")
print(f"   Traffic volume: {total_traffic_volume:,.0f} trucks/year")
print(f"   Total TKM: {total_tkm/1e9:.2f} billion tkm")

# Analyze different threshold values
print("\n" + "="*80)
print("IMPACT OF DIFFERENT MINIMUM TRAFFIC THRESHOLDS")
print("="*80)

thresholds = [100, 500, 1000, 2000, 5000, 10000]

results = []

for threshold in thresholds:
    filtered = international_traffic[
        international_traffic['Traffic_flow_trucks_2030'] >= threshold
    ]

    routes_kept = len(filtered)
    routes_removed = total_routes_international - routes_kept
    routes_pct_kept = (routes_kept / total_routes_international * 100)

    traffic_kept = filtered['Traffic_flow_trucks_2030'].sum()
    traffic_pct_kept = (traffic_kept / total_traffic_volume * 100)

    tkm_kept = (filtered['Traffic_flow_trucks_2030'] * filtered['Total_distance']).sum()
    tkm_pct_kept = (tkm_kept / total_tkm * 100)

    results.append({
        'threshold': threshold,
        'routes_kept': routes_kept,
        'routes_removed': routes_removed,
        'routes_pct_kept': routes_pct_kept,
        'traffic_pct_kept': traffic_pct_kept,
        'tkm_pct_kept': tkm_pct_kept
    })

    print(f"\nThreshold: {threshold:,} trucks/year")
    print(f"  Routes:  {routes_kept:,} kept ({routes_pct_kept:.1f}%), {routes_removed:,} removed ({100-routes_pct_kept:.1f}%)")
    print(f"  Traffic: {traffic_pct_kept:.2f}% kept, {100-traffic_pct_kept:.2f}% removed")
    print(f"  TKM:     {tkm_pct_kept:.2f}% kept, {100-tkm_pct_kept:.2f}% removed")

# Find the threshold closest to the original "remove 54% of routes while keeping 99.6% volume"
print("\n" + "="*80)
print("RECOMMENDED THRESHOLD FOR INTERNATIONAL ROUTES")
print("="*80)

print("\nOriginal SM_preprocessing.py (all routes including domestic):")
print("  Threshold: 1,000 trucks/year")
print("  Result: Removes 54% of OD-pairs while keeping 99.6% of freight volume")

# Check what 1000 threshold does for international routes
result_1000 = [r for r in results if r['threshold'] == 1000][0]

print(f"\nUpdated for cross_border_only = True (international routes only):")
print(f"  Threshold: 1,000 trucks/year")
print(f"  Result: Removes {100-result_1000['routes_pct_kept']:.1f}% of OD-pairs while keeping {result_1000['traffic_pct_kept']:.1f}% of traffic volume")
print(f"         (Keeps {result_1000['routes_kept']:,} of {total_routes_international:,} international routes)")
print(f"         (Keeps {result_1000['tkm_pct_kept']:.1f}% of TKM)")

# Show distribution of traffic volumes
print("\n" + "="*80)
print("TRAFFIC VOLUME DISTRIBUTION (International routes)")
print("="*80)

traffic_values = international_traffic['Traffic_flow_trucks_2030']

print(f"\nStatistics:")
print(f"  Mean:   {traffic_values.mean():,.1f} trucks/year")
print(f"  Median: {traffic_values.median():,.1f} trucks/year")
print(f"  Min:    {traffic_values.min():,.1f} trucks/year")
print(f"  Max:    {traffic_values.max():,.1f} trucks/year")

percentiles = [10, 25, 50, 75, 90, 95, 99]
print(f"\nPercentiles:")
for p in percentiles:
    value = np.percentile(traffic_values, p)
    print(f"  {p:2d}th: {value:,.1f} trucks/year")

# Show how many routes fall below common thresholds
print(f"\nRoutes below threshold:")
for threshold in [100, 500, 1000, 2000, 5000]:
    below = len(international_traffic[international_traffic['Traffic_flow_trucks_2030'] < threshold])
    pct = below / total_routes_international * 100
    print(f"  < {threshold:,}: {below:,} routes ({pct:.1f}%)")

# Recommendation
print("\n" + "="*80)
print("RECOMMENDATION")
print("="*80)

# Find threshold that removes ~50% of routes while keeping >99% volume
target_result = None
for r in results:
    if 45 <= (100 - r['routes_pct_kept']) <= 55 and r['traffic_pct_kept'] >= 99:
        target_result = r
        break

if target_result:
    print(f"""
For international routes, to achieve similar filtering as the original
(remove ~50% of routes while keeping >99% of traffic volume):

  Recommended threshold: {target_result['threshold']:,} trucks/year

  Impact:
    - Keeps {target_result['routes_kept']:,} routes ({target_result['routes_pct_kept']:.1f}%)
    - Removes {target_result['routes_removed']:,} routes ({100-target_result['routes_pct_kept']:.1f}%)
    - Retains {target_result['traffic_pct_kept']:.2f}% of traffic volume
    - Retains {target_result['tkm_pct_kept']:.2f}% of TKM
""")
else:
    print(f"""
For international routes with 1,000 trucks/year threshold:

  Impact:
    - Keeps {result_1000['routes_kept']:,} routes ({result_1000['routes_pct_kept']:.1f}%)
    - Removes {result_1000['routes_removed']:,} routes ({100-result_1000['routes_pct_kept']:.1f}%)
    - Retains {result_1000['traffic_pct_kept']:.2f}% of traffic volume
    - Retains {result_1000['tkm_pct_kept']:.2f}% of TKM

This is the default threshold from SM_preprocessing.py.
""")

print("="*80)
