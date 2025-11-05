"""
Calculate traffic metrics per NUTS-2 region from OD pair data

This script calculates for each NUTS-2 region:
1. Origin tonnes: freight originating from this region
2. Destination tonnes: freight destined for this region
3. Through tonnes: freight passing through this region
4. TKM (tonne-kilometers): freight * distance for each metric

Input:
- Odpair.yaml: Origin-destination pairs with freight flows
- Path.yaml: Route information (sequence of geographic elements)
- GeographicElement.yaml: Geographic elements with NUTS-2 region mapping

Output:
- CSV file with metrics per NUTS-2 region
"""

import yaml
import pandas as pd
import numpy as np
from pathlib import Path
from collections import defaultdict

print("="*80)
print("NUTS-2 REGION TRAFFIC METRICS CALCULATOR")
print("="*80)

# =============================================================================
# Configuration
# =============================================================================

# Input folder
INPUT_FOLDER = "input_data/case_20251022_152235_var_var"

# Output file
OUTPUT_CSV = "nuts2_traffic_metrics.csv"

# Which year to use from the F array (freight flow over time)
# 0 = first year, -1 = last year, or specify index
YEAR_INDEX = 0  # Use first year

# =============================================================================
# Load Data
# =============================================================================

print("\n1. Loading Geographic Elements...")
with open(f"{INPUT_FOLDER}/GeographicElement.yaml") as f:
    geo_elements = yaml.safe_load(f)
print(f"   Loaded {len(geo_elements)} geographic elements")

print("\n2. Loading OD Pairs...")
with open(f"{INPUT_FOLDER}/Odpair.yaml") as f:
    odpairs = yaml.safe_load(f)
print(f"   Loaded {len(odpairs)} OD pairs")

print("\n3. Loading Paths...")
with open(f"{INPUT_FOLDER}/Path.yaml") as f:
    paths = yaml.safe_load(f)
print(f"   Loaded {len(paths)} paths")

# =============================================================================
# Create Lookup Structures
# =============================================================================

print("\n4. Creating lookup structures...")

# Geographic element ID to NUTS-2 mapping
geo_id_to_nuts2 = {}
geo_id_to_name = {}
geo_id_to_length = {}

for geo in geo_elements:
    geo_id = geo['id']
    geo_id_to_nuts2[geo_id] = geo.get('nuts2_region', None)
    geo_id_to_name[geo_id] = geo['name']
    geo_id_to_length[geo_id] = geo.get('length', 0.0)

# Path ID to path data
path_id_to_path = {p['id']: p for p in paths}

# Get all unique NUTS-2 regions
all_nuts2 = sorted(set(v for v in geo_id_to_nuts2.values() if v is not None))
print(f"   Found {len(all_nuts2)} unique NUTS-2 regions")

# =============================================================================
# Calculate Metrics per NUTS-2
# =============================================================================

print("\n5. Calculating traffic metrics per NUTS-2 region...")

# Initialize metrics storage
metrics = {nuts2: {
    'origin_tonnes': 0.0,
    'destination_tonnes': 0.0,
    'through_tonnes': 0.0,
    'origin_tkm': 0.0,
    'destination_tkm': 0.0,
    'through_tkm': 0.0,
    'total_tonnes': 0.0,
    'total_tkm': 0.0
} for nuts2 in all_nuts2}

# Process each OD pair
total_processed = 0
skipped_no_nuts2 = 0

for idx, odpair in enumerate(odpairs):
    # Get freight flow for selected year
    freight_tonnes = odpair['F'][YEAR_INDEX] if odpair['F'] else 0.0

    if freight_tonnes == 0:
        continue

    # Get origin and destination
    origin_id = odpair['from']
    destination_id = odpair['to']
    path_id = odpair['path_id']

    # Get NUTS-2 for origin and destination
    origin_nuts2 = geo_id_to_nuts2.get(origin_id)
    dest_nuts2 = geo_id_to_nuts2.get(destination_id)

    # Get path sequence
    path = path_id_to_path.get(path_id)
    if path is None:
        continue

    path_sequence = path['sequence']
    path_length = path['length']

    # Calculate TKM for this OD pair
    tkm = freight_tonnes * path_length

    # Track origin
    if origin_nuts2:
        metrics[origin_nuts2]['origin_tonnes'] += freight_tonnes
        metrics[origin_nuts2]['origin_tkm'] += tkm
    else:
        skipped_no_nuts2 += 1

    # Track destination
    if dest_nuts2:
        metrics[dest_nuts2]['destination_tonnes'] += freight_tonnes
        metrics[dest_nuts2]['destination_tkm'] += tkm
    else:
        skipped_no_nuts2 += 1

    # Track through traffic (elements in path that are not origin or destination)
    through_elements = set(path_sequence) - {origin_id, destination_id}

    for elem_id in through_elements:
        elem_nuts2 = geo_id_to_nuts2.get(elem_id)
        if elem_nuts2:
            metrics[elem_nuts2]['through_tonnes'] += freight_tonnes
            metrics[elem_nuts2]['through_tkm'] += tkm

    total_processed += 1

    if (idx + 1) % 500 == 0:
        print(f"      Processed {idx + 1}/{len(odpairs)} OD pairs...")

print(f"   Total OD pairs processed: {total_processed}")
print(f"   Skipped (no NUTS-2): {skipped_no_nuts2}")

# Calculate totals
for nuts2 in all_nuts2:
    m = metrics[nuts2]
    # Note: We don't simply sum origin + destination + through because that would triple-count
    # Total tonnes is the sum of unique flows (origin + through is a good proxy)
    m['total_tonnes'] = m['origin_tonnes'] + m['destination_tonnes'] + m['through_tonnes']
    m['total_tkm'] = m['origin_tkm'] + m['destination_tkm'] + m['through_tkm']

# =============================================================================
# Create Results DataFrame
# =============================================================================

print("\n6. Creating results dataframe...")

results_data = []
for nuts2 in all_nuts2:
    m = metrics[nuts2]
    results_data.append({
        'NUTS2_CODE': nuts2,
        'origin_tonnes': m['origin_tonnes'],
        'destination_tonnes': m['destination_tonnes'],
        'through_tonnes': m['through_tonnes'],
        'total_tonnes': m['total_tonnes'],
        'origin_tkm': m['origin_tkm'],
        'destination_tkm': m['destination_tkm'],
        'through_tkm': m['through_tkm'],
        'total_tkm': m['total_tkm']
    })

results_df = pd.DataFrame(results_data)
results_df = results_df.sort_values('NUTS2_CODE').reset_index(drop=True)

# =============================================================================
# Display Summary
# =============================================================================

print("\n" + "="*80)
print("SUMMARY STATISTICS")
print("="*80)

print(f"\nTotal regions analyzed: {len(results_df)}")
print(f"\nTotal tonnes (sum across all regions):")
print(f"  Origin: {results_df['origin_tonnes'].sum():,.0f}")
print(f"  Destination: {results_df['destination_tonnes'].sum():,.0f}")
print(f"  Through: {results_df['through_tonnes'].sum():,.0f}")

print(f"\nTotal TKM (sum across all regions):")
print(f"  Origin: {results_df['origin_tkm'].sum():,.0f}")
print(f"  Destination: {results_df['destination_tkm'].sum():,.0f}")
print(f"  Through: {results_df['through_tkm'].sum():,.0f}")

print("\n" + "-"*80)
print("TOP 10 REGIONS BY TOTAL TONNES:")
print("-"*80)
top_tonnes = results_df.nlargest(10, 'total_tonnes')[['NUTS2_CODE', 'origin_tonnes', 'destination_tonnes', 'through_tonnes', 'total_tonnes']]
print(top_tonnes.to_string(index=False))

print("\n" + "-"*80)
print("TOP 10 REGIONS BY TOTAL TKM:")
print("-"*80)
top_tkm = results_df.nlargest(10, 'total_tkm')[['NUTS2_CODE', 'origin_tkm', 'destination_tkm', 'through_tkm', 'total_tkm']]
# Format large numbers
for col in ['origin_tkm', 'destination_tkm', 'through_tkm', 'total_tkm']:
    top_tkm[col] = top_tkm[col].apply(lambda x: f"{x:,.0f}")
print(top_tkm.to_string(index=False))

print("\n" + "-"*80)
print("GERMANY-DENMARK-SWEDEN CLUSTER:")
print("-"*80)
cluster_codes = ['DEF0', 'DK01', 'DK02', 'DK03', 'DK04', 'DK05', 'SE22', 'SE23']
cluster_results = results_df[results_df['NUTS2_CODE'].isin(cluster_codes)].copy()

if len(cluster_results) > 0:
    print(cluster_results[['NUTS2_CODE', 'origin_tonnes', 'destination_tonnes', 'through_tonnes', 'total_tonnes']].to_string(index=False))
    print(f"\nCluster totals:")
    print(f"  Origin tonnes: {cluster_results['origin_tonnes'].sum():,.0f}")
    print(f"  Destination tonnes: {cluster_results['destination_tonnes'].sum():,.0f}")
    print(f"  Through tonnes: {cluster_results['through_tonnes'].sum():,.0f}")
    print(f"  Total TKM: {cluster_results['total_tkm'].sum():,.0f}")
else:
    print("  No data found for cluster regions")

# =============================================================================
# Save Results
# =============================================================================

print("\n" + "="*80)
print("SAVING RESULTS")
print("="*80)

results_df.to_csv(OUTPUT_CSV, index=False)
print(f"[OK] Results saved to: {OUTPUT_CSV}")

# Also save a formatted version for easy reading
output_formatted = OUTPUT_CSV.replace('.csv', '_formatted.csv')
results_formatted = results_df.copy()
for col in results_df.columns:
    if col != 'NUTS2_CODE':
        results_formatted[col] = results_formatted[col].apply(lambda x: f"{x:,.2f}")
results_formatted.to_csv(output_formatted, index=False)
print(f"[OK] Formatted version saved to: {output_formatted}")

print("="*80)
print("[OK] DONE!")
print("="*80)
