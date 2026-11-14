"""
Check if long edges (likely ferries) are international routes
by examining the country/location of start and end nodes
"""

import yaml
import os
import pandas as pd

# Load data
case_folder = "case_20251106_112933"
input_path = os.path.join("input_data", case_folder)

def load_yaml_file(filename):
    filepath = os.path.join(input_path, filename)
    with open(filepath, 'r') as f:
        return yaml.safe_load(f)

print("="*80)
print("CHECKING IF LONG EDGES ARE INTERNATIONAL ROUTES")
print("="*80)

# Load paths and geographic elements
paths = load_yaml_file('Path.yaml')
geo_elements = load_yaml_file('GeographicElement.yaml')

# Create lookup for geographic elements
geo_dict = {geo['id']: geo for geo in geo_elements}

print(f"\nLoaded {len(paths)} paths")
print(f"Loaded {len(geo_elements)} geographic elements")

# Check what info is available in geographic elements
print("\n" + "="*80)
print("GEOGRAPHIC ELEMENT DATA STRUCTURE")
print("="*80)

sample_geo = geo_elements[0]
print(f"\nSample geographic element (ID={sample_geo['id']}):")
for key, value in sample_geo.items():
    print(f"  {key}: {value}")

# ============================================================================
# ANALYZE LONG EDGES
# ============================================================================

print("\n" + "="*80)
print("ANALYZING LONG EDGES")
print("="*80)

thresholds = [500, 600, 700, 800]

for threshold in thresholds:
    print(f"\n{'='*80}")
    print(f"EDGES > {threshold} KM")
    print(f"{'='*80}")

    long_edge_paths = []

    for path in paths:
        path_id = path['id']

        if 'distance_from_previous' in path and 'sequence' in path:
            distances = path['distance_from_previous']
            sequence = path['sequence']

            # Find long edges
            for i, dist in enumerate(distances):
                if i == 0:
                    continue

                if dist > threshold:
                    start_node_id = sequence[i-1]
                    end_node_id = sequence[i]

                    start_geo = geo_dict.get(start_node_id, {})
                    end_geo = geo_dict.get(end_node_id, {})

                    edge_info = {
                        'path_id': path_id,
                        'segment_idx': i,
                        'distance': dist,
                        'start_node_id': start_node_id,
                        'end_node_id': end_node_id,
                        'start_name': start_geo.get('name', 'Unknown'),
                        'end_name': end_geo.get('name', 'Unknown'),
                        'start_country': start_geo.get('country', 'Unknown'),
                        'end_country': end_geo.get('country', 'Unknown'),
                        'start_nuts2': start_geo.get('nuts2', 'Unknown'),
                        'end_nuts2': end_geo.get('nuts2', 'Unknown'),
                    }

                    # Check if international
                    edge_info['is_international'] = (
                        edge_info['start_country'] != edge_info['end_country']
                        and edge_info['start_country'] != 'Unknown'
                        and edge_info['end_country'] != 'Unknown'
                    )

                    long_edge_paths.append(edge_info)

    if long_edge_paths:
        print(f"\nFound {len(long_edge_paths)} edges > {threshold} km")

        # Count international vs domestic
        international = [e for e in long_edge_paths if e['is_international']]
        domestic = [e for e in long_edge_paths if not e['is_international']]

        print(f"  International: {len(international)} ({len(international)/len(long_edge_paths)*100:.1f}%)")
        print(f"  Domestic: {len(domestic)} ({len(domestic)/len(long_edge_paths)*100:.1f}%)")

        # Show details
        if threshold >= 800:  # Show details for ferry threshold
            print(f"\n  Detailed breakdown:")
            print(f"  {'-'*76}")

            for i, edge in enumerate(sorted(long_edge_paths, key=lambda x: x['distance'], reverse=True), 1):
                intl_flag = "[INTL]" if edge['is_international'] else "[DOM] "

                print(f"\n  {i}. Path {edge['path_id']}, Segment {edge['segment_idx']}: {edge['distance']:.1f} km {intl_flag}")
                print(f"     From: {edge['start_name']} ({edge['start_country']}, {edge['start_nuts2']})")
                print(f"     To:   {edge['end_name']} ({edge['end_country']}, {edge['end_nuts2']})")

                if edge['is_international']:
                    print(f"     -> International: {edge['start_country']} to {edge['end_country']}")

# ============================================================================
# SUMMARY FOR 800KM THRESHOLD (FERRIES)
# ============================================================================

print("\n" + "="*80)
print("SUMMARY: FERRY ROUTES (>800 KM)")
print("="*80)

ferry_edges = []
for path in paths:
    if 'distance_from_previous' in path and 'sequence' in path:
        distances = path['distance_from_previous']
        sequence = path['sequence']

        for i, dist in enumerate(distances):
            if i > 0 and dist > 800:
                start_node_id = sequence[i-1]
                end_node_id = sequence[i]
                start_geo = geo_dict.get(start_node_id, {})
                end_geo = geo_dict.get(end_node_id, {})

                ferry_edges.append({
                    'path_id': path['id'],
                    'distance': dist,
                    'start_country': start_geo.get('country', 'Unknown'),
                    'end_country': end_geo.get('country', 'Unknown'),
                    'start_name': start_geo.get('name', 'Unknown'),
                    'end_name': end_geo.get('name', 'Unknown'),
                    'is_international': (
                        start_geo.get('country', '') != end_geo.get('country', '')
                        and start_geo.get('country', '') != ''
                        and end_geo.get('country', '') != ''
                    )
                })

if ferry_edges:
    df_ferry = pd.DataFrame(ferry_edges)

    print(f"\nTotal ferry routes (edges >800km): {len(df_ferry)}")
    print(f"International ferries: {df_ferry['is_international'].sum()} ({df_ferry['is_international'].sum()/len(df_ferry)*100:.1f}%)")
    print(f"Domestic ferries: {(~df_ferry['is_international']).sum()} ({(~df_ferry['is_international']).sum()/len(df_ferry)*100:.1f}%)")

    print("\nCountry pairs for international ferries:")
    international_ferries = df_ferry[df_ferry['is_international']]
    for idx, row in international_ferries.iterrows():
        print(f"  {row['start_country']} -> {row['end_country']}: {row['distance']:.0f} km")
        print(f"    ({row['start_name']} to {row['end_name']})")

    # Save ferry info with country data
    ferry_info = {
        'ferry_edges': ferry_edges,
        'threshold_km': 800,
        'num_ferries': len(ferry_edges),
        'num_international': int(df_ferry['is_international'].sum()),
        'num_domestic': int((~df_ferry['is_international']).sum()),
    }

    with open('ferry_routes_with_countries.yaml', 'w') as f:
        yaml.dump(ferry_info, f)

    print(f"\nSaved detailed ferry information to: ferry_routes_with_countries.yaml")

else:
    print("\nNo ferry routes (>800km) found")

print("\n" + "="*80)
