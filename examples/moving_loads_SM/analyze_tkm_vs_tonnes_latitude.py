"""
Compare TKM vs tonnes by latitude to see if the Italy peak is due to long distances
or actual freight volume.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import yaml
from collections import defaultdict
import numpy as np

# Load data
case_study_name = 'case_20251103_114421'
input_dir = f'input_data/{case_study_name}'
results_dir = f'results/{case_study_name}'

print("=" * 80)
print("TKM vs TONNES ANALYSIS BY LATITUDE")
print("=" * 80)

# Load data
with open(f'{input_dir}/GeographicElement.yaml', 'r', encoding='utf-8') as f:
    geo_elements = yaml.safe_load(f)

with open(f'{input_dir}/Path.yaml', 'r', encoding='utf-8') as f:
    paths = yaml.safe_load(f)

import glob
f_dict_files = glob.glob(f'{results_dir}/*_f_dict.yaml')
f_dict_file = sorted(f_dict_files)[-1]
with open(f_dict_file, 'r', encoding='utf-8') as f:
    f_data_raw = yaml.safe_load(f)

# Create lookups
nuts2_lookup = {}
for geo in geo_elements:
    if geo['type'] == 'node' and 'nuts2_region' in geo and geo['nuts2_region']:
        nuts2_lookup[geo['id']] = {
            'nuts2': geo['nuts2_region'],
            'lat': geo['coordinate_lat'],
            'country': geo['country']
        }

path_lookup = {}
for path in paths:
    path_lookup[path['id']] = {
        'sequence': path['sequence'],
        'distance_from_previous': path['distance_from_previous']
    }

SCALING_FACTOR = 1000

# ============================================================================
# Calculate both TKM and TONNES by NUTS2 for year 2030
# ============================================================================
print("\n" + "=" * 80)
print("CALCULATING TKM AND TONNES BY NUTS2 (year 2030)")
print("=" * 80)

tkm_by_nuts2 = defaultdict(float)
tonnes_by_nuts2 = defaultdict(float)
avg_distance_by_nuts2 = defaultdict(lambda: {'total_tkm': 0, 'total_tonnes': 0})

for key_str, value in f_data_raw.items():
    flow_value_kt = float(value)

    if flow_value_kt < 0.00001:
        continue

    key_tuple = eval(key_str)
    year, (product_id, odpair_id, path_id), (mode_id, techvehicle_id), generation = key_tuple

    if year != 2030:
        continue

    if path_id not in path_lookup:
        continue

    flow_value_tonnes = flow_value_kt * SCALING_FACTOR
    path_info = path_lookup[path_id]
    sequence = path_info['sequence']
    distance_from_previous = path_info['distance_from_previous']

    # Calculate for each NUTS2 node
    for i, node_id in enumerate(sequence):
        if node_id not in nuts2_lookup:
            continue

        nuts2 = nuts2_lookup[node_id]['nuts2']
        segment_distance = distance_from_previous[i]
        tkm_segment = flow_value_tonnes * segment_distance

        tkm_by_nuts2[nuts2] += tkm_segment
        tonnes_by_nuts2[nuts2] += flow_value_tonnes

        avg_distance_by_nuts2[nuts2]['total_tkm'] += tkm_segment
        avg_distance_by_nuts2[nuts2]['total_tonnes'] += flow_value_tonnes

# Calculate average distance per tonne for each NUTS2
avg_distance_km = {}
for nuts2, data in avg_distance_by_nuts2.items():
    if data['total_tonnes'] > 0:
        avg_distance_km[nuts2] = data['total_tkm'] / data['total_tonnes']
    else:
        avg_distance_km[nuts2] = 0

# ============================================================================
# Compare Italian regions
# ============================================================================
print("\n" + "=" * 80)
print("ITALIAN REGIONS: TKM vs TONNES COMPARISON")
print("=" * 80)

italian_comparison = []

for nuts2 in tkm_by_nuts2.keys():
    # Check if Italian
    is_italian = False
    lat = 0
    for node_id, info in nuts2_lookup.items():
        if info['nuts2'] == nuts2:
            is_italian = (info['country'] == 'IT')
            lat = info['lat']
            break

    if not is_italian:
        continue

    tkm = tkm_by_nuts2[nuts2]
    tonnes = tonnes_by_nuts2[nuts2]
    avg_dist = avg_distance_km.get(nuts2, 0)

    italian_comparison.append({
        'nuts2': nuts2,
        'lat': lat,
        'tkm': tkm,
        'tonnes': tonnes,
        'avg_dist': avg_dist
    })

# Sort by TKM
italian_comparison.sort(key=lambda x: x['tkm'], reverse=True)

print(f"\n{'Rank':<6} {'NUTS2':<10} {'Latitude':>10} {'TKM (M)':>12} {'Tonnes (k)':>12} {'Avg Dist (km)':>15} {'TKM Rank':>10} {'Tonnes Rank':>12}")
print("-" * 110)

# Also sort by tonnes to get tonnes rank
tonnes_sorted = sorted(italian_comparison, key=lambda x: x['tonnes'], reverse=True)
tonnes_rank = {r['nuts2']: i+1 for i, r in enumerate(tonnes_sorted)}

for i, region in enumerate(italian_comparison[:15], 1):
    t_rank = tonnes_rank[region['nuts2']]
    print(f"{i:<6} {region['nuts2']:<10} {region['lat']:>10.2f} {region['tkm']/1e6:>12.1f} {region['tonnes']/1e3:>12.1f} {region['avg_dist']:>15.1f} {i:>10} {t_rank:>12}")

# ============================================================================
# Compare all countries
# ============================================================================
print("\n" + "=" * 80)
print("ALL COUNTRIES: TKM vs TONNES COMPARISON")
print("=" * 80)

country_tkm = defaultdict(float)
country_tonnes = defaultdict(float)

for nuts2 in tkm_by_nuts2.keys():
    # Get country
    country = 'UNKNOWN'
    for node_id, info in nuts2_lookup.items():
        if info['nuts2'] == nuts2:
            country = info['country']
            break

    country_tkm[country] += tkm_by_nuts2[nuts2]
    country_tonnes[country] += tonnes_by_nuts2[nuts2]

print(f"\n{'Country':<10} {'TKM (billions)':>18} {'Tonnes (millions)':>20} {'Avg Dist (km)':>15} {'TKM Rank':>10} {'Tonnes Rank':>12}")
print("-" * 100)

country_data = []
for country in country_tkm.keys():
    tkm = country_tkm[country]
    tonnes = country_tonnes[country]
    avg_dist = tkm / tonnes if tonnes > 0 else 0

    country_data.append({
        'country': country,
        'tkm': tkm,
        'tonnes': tonnes,
        'avg_dist': avg_dist
    })

country_data.sort(key=lambda x: x['tkm'], reverse=True)
tonnes_rank_country = {c['country']: i+1 for i, c in enumerate(sorted(country_data, key=lambda x: x['tonnes'], reverse=True))}

for i, c in enumerate(country_data, 1):
    t_rank = tonnes_rank_country[c['country']]
    print(f"{c['country']:<10} {c['tkm']/1e9:>18.2f} {c['tonnes']/1e6:>20.1f} {c['avg_dist']:>15.1f} {i:>10} {t_rank:>12}")

# ============================================================================
# Analysis: Does Italy rank high due to distance or volume?
# ============================================================================
print("\n" + "=" * 80)
print("DIAGNOSIS: IS ITALY'S PEAK DUE TO DISTANCE OR VOLUME?")
print("=" * 80)

italy_tkm_rank = next((i+1 for i, c in enumerate(country_data) if c['country'] == 'IT'), None)
italy_tonnes_rank = tonnes_rank_country.get('IT', None)

italy_data = next((c for c in country_data if c['country'] == 'IT'), None)

if italy_data:
    print(f"\nItaly:")
    print(f"  - TKM rank: #{italy_tkm_rank}")
    print(f"  - Tonnes rank: #{italy_tonnes_rank}")
    print(f"  - Average distance: {italy_data['avg_dist']:.1f} km")
    print(f"  - TKM: {italy_data['tkm']/1e9:.2f} billion")
    print(f"  - Tonnes: {italy_data['tonnes']/1e6:.1f} million")

    if italy_tkm_rank == italy_tonnes_rank:
        print(f"\n✓ Italy ranks #{italy_tkm_rank} by BOTH TKM and tonnes")
        print("  The high TKM is due to HIGH FREIGHT VOLUME, not just distance.")
    elif italy_tkm_rank < italy_tonnes_rank:
        print(f"\n⚠️  Italy ranks HIGHER in TKM (#{italy_tkm_rank}) than tonnes (#{italy_tonnes_rank})")
        print("  This suggests freight travels LONGER DISTANCES through Italy.")
    else:
        print(f"\n⚠️  Italy ranks LOWER in TKM (#{italy_tkm_rank}) than tonnes (#{italy_tonnes_rank})")
        print("  This suggests freight travels SHORTER DISTANCES through Italy.")

# ============================================================================
# Suggestions for visualization
# ============================================================================
print("\n" + "=" * 80)
print("VISUALIZATION RECOMMENDATIONS")
print("=" * 80)

print("""
Based on the analysis, here are recommended visualizations:

1. **TONNES BY LATITUDE** (recommended)
   - Shows actual freight volume independent of distance
   - Better for understanding freight DENSITY at each latitude
   - Not affected by path length through regions
   - Good for comparing regional freight activity

2. **TKM BY LATITUDE** (current)
   - Shows transport work (volume × distance)
   - Captures economic/environmental impact
   - Can be inflated by long paths through regions
   - Good for infrastructure planning

3. **AVERAGE DISTANCE BY LATITUDE**
   - Shows how far freight typically travels through each region
   - Helps identify transit corridors vs destination regions
   - Complements both tonnes and TKM visualizations

4. **COMBINED VISUALIZATION**
   - Three panels: Tonnes, TKM, and Avg Distance
   - Shows complete picture of freight patterns

5. **NORMALIZED BY LATITUDE SPAN**
   - Account for physical size of regions at different latitudes
   - Regions at higher latitudes cover less km per degree
   - Could normalize by cos(latitude) if appropriate

RECOMMENDATION:
Create a 2-panel visualization:
  - Panel 1: TONNES by latitude (freight volume)
  - Panel 2: TKM by latitude (transport work)

This shows both:
  - WHERE freight is located (tonnes)
  - HOW MUCH WORK is done transporting it (TKM)
""")

# Calculate if normalization would change ranking
print("\nDoes latitude affect distance representation?")
print("At higher latitudes, 1° longitude represents fewer km, but latitude is vertical (N-S).")
print("Since we're plotting by latitude (N-S axis), no cos(latitude) correction is needed.")
print("However, regions at same latitude may have different N-S extents.")

# Check if Italian regions have unusually long N-S paths
print("\nAverage distance through top 5 regions (all countries):")
all_regions_sorted = sorted(
    [(nuts2, tkm_by_nuts2[nuts2], tonnes_by_nuts2[nuts2], avg_distance_km.get(nuts2, 0))
     for nuts2 in tkm_by_nuts2.keys()],
    key=lambda x: x[1],
    reverse=True
)

for i, (nuts2, tkm, tonnes, avg_dist) in enumerate(all_regions_sorted[:5], 1):
    country = 'UNK'
    for node_id, info in nuts2_lookup.items():
        if info['nuts2'] == nuts2:
            country = info['country']
            break
    print(f"  {i}. {nuts2} ({country}): {avg_dist:.1f} km average distance")
