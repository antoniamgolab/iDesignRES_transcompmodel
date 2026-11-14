"""
Check what filters were applied to the newest case
"""

import os
import yaml
from pathlib import Path

# Find the most recent case directory
input_dir = Path("input_data")
case_dirs = [d for d in input_dir.iterdir() if d.is_dir() and d.name.startswith("case_")]
case_dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)

if not case_dirs:
    print("[ERROR] No case directories found!")
    exit(1)

newest_case = case_dirs[0]
print("="*80)
print(f"ANALYZING NEWEST CASE: {newest_case.name}")
print("="*80)

# Load Odpair.yaml
odpair_file = newest_case / "Odpair.yaml"
if not odpair_file.exists():
    print(f"[ERROR] Odpair.yaml not found in {newest_case.name}")
    exit(1)

with open(odpair_file, 'r', encoding='utf-8') as f:
    odpairs = yaml.safe_load(f)

print(f"\nTotal odpairs: {len(odpairs)}")

# Load GeographicElement to check country distribution
geo_file = newest_case / "GeographicElement.yaml"
if not geo_file.exists():
    print(f"[ERROR] GeographicElement.yaml not found")
    exit(1)

with open(geo_file, 'r', encoding='utf-8') as f:
    geo_elements = yaml.safe_load(f)

# Create mapping
geo_to_country = {}
for geo in geo_elements:
    geo_id = geo.get('id')
    country = geo.get('country')
    if geo_id and country:
        geo_to_country[geo_id] = country

# Analyze odpairs
international = []
domestic = []

for odpair in odpairs:
    origin_id = odpair.get('from')
    dest_id = odpair.get('to')

    if origin_id and dest_id:
        origin_country = geo_to_country.get(origin_id, 'UNKNOWN')
        dest_country = geo_to_country.get(dest_id, 'UNKNOWN')

        if origin_country == dest_country:
            domestic.append((origin_country, odpair.get('id')))
        else:
            international.append((origin_country, dest_country, odpair.get('id')))

print("\n" + "="*80)
print("ROUTE TYPE BREAKDOWN")
print("="*80)
print(f"International: {len(international)} ({len(international)/len(odpairs)*100:.1f}%)")
print(f"Domestic:      {len(domestic)} ({len(domestic)/len(odpairs)*100:.1f}%)")

if domestic:
    print("\n[WARNING] Domestic routes found! CROSS_BORDER_ONLY filter may not have been applied.")
    domestic_by_country = {}
    for country, odpair_id in domestic:
        domestic_by_country[country] = domestic_by_country.get(country, 0) + 1

    print("\nDomestic routes by country:")
    for country, count in sorted(domestic_by_country.items()):
        print(f"  {country}: {count}")
else:
    print("\n[OK] NO domestic routes - cross-border filter was applied successfully")

# Show international pairs
if international:
    print("\n" + "="*80)
    print("INTERNATIONAL ROUTE PAIRS")
    print("="*80)

    pair_counts = {}
    for origin, dest, _ in international:
        pair = f"{origin} -> {dest}"
        pair_counts[pair] = pair_counts.get(pair, 0) + 1

    print(f"\nCountry pairs: {len(pair_counts)}")
    for pair, count in sorted(pair_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {pair}: {count} routes")

# Compare with previous case
print("\n" + "="*80)
print("COMPARISON WITH PREVIOUS CASE")
print("="*80)

# Check case_20251106_102427 (the one from results_representation.ipynb)
prev_case = input_dir / "case_20251106_102427"
if prev_case.exists():
    prev_odpair_file = prev_case / "Odpair.yaml"
    if prev_odpair_file.exists():
        with open(prev_odpair_file, 'r', encoding='utf-8') as f:
            prev_odpairs = yaml.safe_load(f)

        print(f"\nPrevious case (case_20251106_102427): {len(prev_odpairs)} odpairs")
        print(f"Current case ({newest_case.name}): {len(odpairs)} odpairs")
        print(f"Difference: {len(prev_odpairs) - len(odpairs)} odpairs removed")
        print(f"Reduction: {(1 - len(odpairs)/len(prev_odpairs))*100:.1f}%")

# Check if there are other active filters
print("\n" + "="*80)
print("CHECKING FOR OTHER FILTERS")
print("="*80)

# Check for distance info in odpairs
if odpairs:
    sample_odpair = odpairs[0]
    if 'distance' in sample_odpair or 'length' in sample_odpair:
        distances = []
        for odpair in odpairs:
            dist = odpair.get('distance') or odpair.get('length')
            if dist:
                distances.append(dist)

        if distances:
            print(f"\nDistance range: {min(distances):.1f} - {max(distances):.1f} km")
            print(f"Average distance: {sum(distances)/len(distances):.1f} km")
            print(f"Median distance: {sorted(distances)[len(distances)//2]:.1f} km")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)

if len(odpairs) == 280:
    print(f"""
The case has {len(odpairs)} odpairs, which seems low for international freight.

Possible reasons:
1. Other filters are active (MIN_DISTANCE_KM, MAX_ODpair)
2. NUTS boundary filtering removed many routes
3. The Scandinavian-Mediterranean corridor has limited international connections
4. The traffic data filtering excluded low-volume routes

Check SM_preprocessing_nuts2_complete.py configuration:
- MAX_ODpair setting
- MIN_DISTANCE_KM setting
- Traffic flow thresholds
""")
else:
    print(f"\nCase has {len(odpairs)} odpairs")

print(f"\nCase directory: {newest_case}")
print("="*80)
