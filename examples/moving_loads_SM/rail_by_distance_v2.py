"""Analyze: are long routes preferentially shifted to rail? V2 with correct distances."""
import yaml, re, pathlib, math
from collections import defaultdict
import numpy as np

BASE = pathlib.Path(__file__).resolve().parent
INPUT_RAIL = BASE / 'input_data/uncertainty_scenarios_rail'
RESULTS_RAIL = BASE / 'results/rail'

YEAR_MAPPING = {i: 2020 + (i - 1) * 4 for i in range(1, 15)}
YEAR_TO_INDEX = {v: k for k, v in YEAR_MAPPING.items()}

# Load geo
with open(BASE / 'input_data/fixed_nuts_2/GeographicElement.yaml') as f:
    geo_data = yaml.safe_load(f)

node_coords = {}
edge_info = {}
geo_id_to_country = {}
for g in geo_data:
    if g.get('type') == 'node':
        node_coords[g['id']] = (g.get('coordinate_lat', 0), g.get('coordinate_long', 0))
        geo_id_to_country[g['id']] = g.get('country', '')
    elif g.get('type') == 'edge':
        edge_info[g['id']] = {'from': g.get('from'), 'to': g.get('to'), 'length': g.get('length', 0)}

node_pair_dist = {}
for eid, info in edge_info.items():
    node_pair_dist[(info['from'], info['to'])] = info['length']
    node_pair_dist[(info['to'], info['from'])] = info['length']


def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


def path_dist(seq):
    d = 0
    for i in range(len(seq) - 1):
        n1, n2 = seq[i], seq[i + 1]
        if (n1, n2) in node_pair_dist:
            d += node_pair_dist[(n1, n2)]
        elif n1 in node_coords and n2 in node_coords:
            lat1, lon1 = node_coords[n1]
            lat2, lon2 = node_coords[n2]
            d += haversine(lat1, lon1, lat2, lon2)
    return d


# Load rail paths and odpairs
with open(INPUT_RAIL / 'scenario_004/Path.yaml') as f:
    rail_paths = yaml.load(f, Loader=yaml.UnsafeLoader)
path_distance = {}
for p in rail_paths:
    pid = int(p['id'])
    seq = [int(x) for x in p['sequence']]
    path_distance[pid] = path_dist(seq)

with open(INPUT_RAIL / 'scenario_004/Odpair.yaml') as f:
    odpairs = yaml.load(f, Loader=yaml.UnsafeLoader)
od_info = {}
for od in odpairs:
    od_id = int(od['id'])
    pid = int(od['path_id'])
    od_info[od_id] = {
        'distance_km': path_distance.get(pid, 0),
        'orig': geo_id_to_country.get(int(od['from']), ''),
        'dest': geo_id_to_country.get(int(od['to']), ''),
    }

# Parse f_dict
f_re = re.compile(
    r'\((\d+),\s*\((\d+),\s*(\d+),\s*(\d+)\),\s*\((\d+),\s*(\d+)\),\s*(\d+)\):\s*(.+)')


def load_f_dict(filepath):
    flows = defaultdict(float)
    with open(filepath) as f:
        for line in f:
            m = f_re.match(line.strip())
            if not m:
                continue
            year = int(m.group(1))
            od_id = int(m.group(3))
            mode = int(m.group(5))
            val = float(m.group(8))
            flows[(year, od_id, mode)] += val
    return dict(flows)


print("Loading rail f_dict...")
f_rail = load_f_dict(
    RESULTS_RAIL / 'scenario_004/scenario_004_cs_2026-02-14_20-52-20_f_dict.yaml')

distance_bins = [0, 300, 500, 700, 900, 1100, 1400, 2000]
bin_labels = [f"{distance_bins[i]}-{distance_bins[i+1]}" for i in range(len(distance_bins) - 1)]

years = [2032, 2040, 2048]

for year in years:
    print(f"\n===== {year} =====")

    road_by_bin = defaultdict(float)
    rail_by_bin = defaultdict(float)
    total_by_bin = defaultdict(float)
    ods_by_bin = defaultdict(int)

    all_ods = set()
    for (y, od_id, mode) in f_rail:
        if y == year:
            all_ods.add(od_id)

    for od_id in all_ods:
        info = od_info.get(od_id)
        if info is None:
            continue
        dist = info['distance_km']

        bin_idx = len(distance_bins) - 2
        for i in range(len(distance_bins) - 1):
            if distance_bins[i] <= dist < distance_bins[i + 1]:
                bin_idx = i
                break

        road_val = f_rail.get((year, od_id, 1), 0)
        rail_val = f_rail.get((year, od_id, 2), 0)
        road_by_bin[bin_idx] += road_val
        rail_by_bin[bin_idx] += rail_val
        total_by_bin[bin_idx] += road_val + rail_val
        ods_by_bin[bin_idx] += 1

    print(f"{'Distance (km)':>15} {'Road (kt)':>10} {'Rail (kt)':>10} {'Total (kt)':>10} "
          f"{'Rail %':>8} {'# ODs':>6}")
    for i in range(len(distance_bins) - 1):
        road = road_by_bin[i]
        rail = rail_by_bin[i]
        total = total_by_bin[i]
        pct = rail / total * 100 if total > 0 else 0
        print(f"{bin_labels[i]:>15} {road:>10.0f} {rail:>10.0f} {total:>10.0f} "
              f"{pct:>7.1f}% {ods_by_bin[i]:>6}")

    total_road = sum(road_by_bin.values())
    total_rail = sum(rail_by_bin.values())
    total_all = total_road + total_rail
    print(f"{'TOTAL':>15} {total_road:>10.0f} {total_rail:>10.0f} {total_all:>10.0f} "
          f"{total_rail / total_all * 100:>7.1f}%")

    # Weighted average distance
    road_dist_sum = sum(f_rail.get((year, od, 1), 0) * od_info.get(od, {}).get('distance_km', 0)
                        for od in all_ods if od in od_info)
    road_vol_sum = sum(f_rail.get((year, od, 1), 0) for od in all_ods)
    rail_dist_sum = sum(f_rail.get((year, od, 2), 0) * od_info.get(od, {}).get('distance_km', 0)
                        for od in all_ods if od in od_info)
    rail_vol_sum = sum(f_rail.get((year, od, 2), 0) for od in all_ods)

    avg_road = road_dist_sum / road_vol_sum if road_vol_sum > 0 else 0
    avg_rail = rail_dist_sum / rail_vol_sum if rail_vol_sum > 0 else 0
    print(f"\n  Weighted avg distance: Road = {avg_road:.0f} km, Rail = {avg_rail:.0f} km")
    if avg_road > 0:
        print(f"  Rail routes are {avg_rail / avg_road:.2f}x longer on average")

    # Correlation: distance vs rail share (by OD pair)
    dists_list = []
    rail_shares = []
    for od_id in all_ods:
        info = od_info.get(od_id)
        if info is None:
            continue
        rv = f_rail.get((year, od_id, 1), 0)
        rlv = f_rail.get((year, od_id, 2), 0)
        total = rv + rlv
        if total > 0:
            dists_list.append(info['distance_km'])
            rail_shares.append(rlv / total * 100)

    corr = np.corrcoef(dists_list, rail_shares)[0, 1]
    print(f"  Correlation (distance vs rail share): r = {corr:.3f}")
