"""Analyze: are long routes preferentially shifted to rail?"""
import yaml, re, pathlib
from collections import defaultdict
import numpy as np

BASE = pathlib.Path(__file__).resolve().parent
INPUT_BASE = BASE / 'input_data/uncertainty_scenarios'
INPUT_RAIL = BASE / 'input_data/uncertainty_scenarios_rail'
RESULTS_BASE = BASE / 'results/uncertainty_scenarios_v2'
RESULTS_RAIL = BASE / 'results/rail'

YEAR_MAPPING = {i: 2020 + (i - 1) * 4 for i in range(1, 15)}
YEAR_TO_INDEX = {v: k for k, v in YEAR_MAPPING.items()}

# Load geo
with open(BASE / 'input_data/fixed_nuts_2/GeographicElement.yaml') as f:
    geo_data = yaml.safe_load(f)
geo_len = {g['id']: g.get('length', 0) for g in geo_data if g.get('type') == 'edge'}
geo_id_to_country = {g['id']: g.get('country', '') for g in geo_data if g.get('type') == 'node'}

# Load paths (from fixed_nuts_2 for distance calc)
with open(BASE / 'input_data/fixed_nuts_2/Path.yaml') as f:
    all_paths = yaml.load(f, Loader=yaml.UnsafeLoader)
path_distance = {}
for p in all_paths:
    pid = int(p['id'])
    seq = [int(x) for x in p['sequence']]
    path_distance[pid] = sum(geo_len.get(g, 0) for g in seq)

# Load odpairs (scenario_000 for baseline mapping)
with open(INPUT_BASE / 'scenario_000/Odpair.yaml') as f:
    odpairs = yaml.load(f, Loader=yaml.UnsafeLoader)
od_info = {}
for od in odpairs:
    od_id = int(od['id'])
    pid = int(od['path_id'])
    od_info[od_id] = {
        'path_id': pid,
        'distance_km': path_distance.get(pid, 0),
        'orig': geo_id_to_country.get(int(od['from']), ''),
        'dest': geo_id_to_country.get(int(od['to']), ''),
    }

# Also load rail odpairs (may have different mapping)
with open(INPUT_RAIL / 'scenario_004/Odpair.yaml') as f:
    odpairs_rail = yaml.load(f, Loader=yaml.UnsafeLoader)
od_info_rail = {}
for od in odpairs_rail:
    od_id = int(od['id'])
    pid = int(od['path_id'])
    od_info_rail[od_id] = {
        'path_id': pid,
        'distance_km': path_distance.get(pid, 0),
        'orig': geo_id_to_country.get(int(od['from']), ''),
        'dest': geo_id_to_country.get(int(od['to']), ''),
    }

# Parse f_dict
f_re = re.compile(
    r'\((\d+),\s*\((\d+),\s*(\d+),\s*(\d+)\),\s*\((\d+),\s*(\d+)\),\s*(\d+)\):\s*(.+)')


def load_f_dict(filepath):
    flows = defaultdict(float)  # (year, od_id, mode): tonnes
    with open(filepath) as f:
        for line in f:
            m = f_re.match(line.strip())
            if not m:
                continue
            year = int(m.group(1))
            od_id = int(m.group(3))
            mode = int(m.group(5))
            val = float(m.group(8))
            flows[(year, od_id, mode)] += val  # sum across tech and vintage
    return dict(flows)


print("Loading rail f_dict...")
f_rail = load_f_dict(
    RESULTS_RAIL / 'scenario_004/scenario_004_cs_2026-02-14_20-52-20_f_dict.yaml')

print("Loading baseline f_dict...")
f_base = load_f_dict(
    RESULTS_BASE / 'scenario_000/scenario_000_cs_2026-02-14_18-25-42_f_dict.yaml')

# For each year, compute rail share by distance bin
distance_bins = [0, 500, 1000, 1500, 2000, 2500, 3000, 4000, 6000]
bin_labels = [f"{distance_bins[i]}-{distance_bins[i+1]}" for i in range(len(distance_bins)-1)]

years = [2032, 2036, 2040, 2048]

for year in years:
    print(f"\n===== {year} =====")

    # Aggregate by distance bin
    road_by_bin = defaultdict(float)
    rail_by_bin = defaultdict(float)
    total_by_bin = defaultdict(float)

    # Use rail scenario flows
    all_ods_this_year = set()
    for (y, od_id, mode) in f_rail:
        if y == year:
            all_ods_this_year.add(od_id)

    for od_id in all_ods_this_year:
        info = od_info_rail.get(od_id, od_info.get(od_id))
        if info is None:
            continue
        dist = info['distance_km']

        # Find bin
        bin_idx = -1
        for i in range(len(distance_bins) - 1):
            if distance_bins[i] <= dist < distance_bins[i + 1]:
                bin_idx = i
                break
        if bin_idx == -1:
            bin_idx = len(distance_bins) - 2  # last bin

        road_val = f_rail.get((year, od_id, 1), 0)
        rail_val = f_rail.get((year, od_id, 2), 0)
        road_by_bin[bin_idx] += road_val
        rail_by_bin[bin_idx] += rail_val
        total_by_bin[bin_idx] += road_val + rail_val

    print(f"{'Distance (km)':>15} {'Road (kt)':>10} {'Rail (kt)':>10} {'Total (kt)':>10} {'Rail %':>8} {'# ODs':>6}")
    for i in range(len(distance_bins) - 1):
        road = road_by_bin[i]
        rail = rail_by_bin[i]
        total = total_by_bin[i]
        pct = rail / total * 100 if total > 0 else 0
        # Count ODs in this bin
        n_ods = sum(1 for od_id in all_ods_this_year
                    if od_info_rail.get(od_id, od_info.get(od_id, {})).get('distance_km', 0) >= distance_bins[i]
                    and od_info_rail.get(od_id, od_info.get(od_id, {})).get('distance_km', 0) < distance_bins[i+1])
        print(f"{bin_labels[i]:>15} {road:>10.0f} {rail:>10.0f} {total:>10.0f} {pct:>7.1f}% {n_ods:>6}")

    # Summary stats
    total_road = sum(road_by_bin.values())
    total_rail = sum(rail_by_bin.values())
    total_all = total_road + total_rail
    print(f"{'TOTAL':>15} {total_road:>10.0f} {total_rail:>10.0f} {total_all:>10.0f} "
          f"{total_rail/total_all*100:>7.1f}%")

    # Weighted average distance for rail vs road
    road_dist_sum = 0
    road_vol_sum = 0
    rail_dist_sum = 0
    rail_vol_sum = 0
    for od_id in all_ods_this_year:
        info = od_info_rail.get(od_id, od_info.get(od_id))
        if info is None:
            continue
        dist = info['distance_km']
        rv = f_rail.get((year, od_id, 1), 0)
        rlv = f_rail.get((year, od_id, 2), 0)
        road_dist_sum += rv * dist
        road_vol_sum += rv
        rail_dist_sum += rlv * dist
        rail_vol_sum += rlv

    avg_road_dist = road_dist_sum / road_vol_sum if road_vol_sum > 0 else 0
    avg_rail_dist = rail_dist_sum / rail_vol_sum if rail_vol_sum > 0 else 0
    print(f"\n  Volume-weighted avg distance: Road = {avg_road_dist:.0f} km, Rail = {avg_rail_dist:.0f} km")
    print(f"  Rail routes are {avg_rail_dist/avg_road_dist:.1f}x longer on average" if avg_road_dist > 0 else "")
