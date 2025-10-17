import yaml
import pickle
import os

# Find the results file
results_dir = 'results/case_20251015_195344'
pkl_files = [f for f in os.listdir(results_dir) if f.endswith('.pkl')]
if pkl_files:
    results_file = os.path.join(results_dir, pkl_files[0])
    print(f"Loading: {results_file}")

    with open(results_file, 'rb') as f:
        output_data = pickle.load(f)

    # Load path data
    with open('output_data/sm_nuts3_complete/Path.yaml', 'r') as f:
        path_list_temp = yaml.safe_load(f)
    path_list = {p['id']: p for p in path_list_temp}

    # Load odpair data
    with open('output_data/sm_nuts3_complete/Odpair.yaml', 'r') as f:
        odpair_list_temp = yaml.safe_load(f)
    odpair_list = {o['id']: o for o in odpair_list_temp}

    print(f"\nTotal paths: {len(path_list)}")
    print(f"Total odpairs: {len(odpair_list)}")

    # Check odpair structure
    print("\nFirst 5 odpairs:")
    for i, (odpair_id, odpair_data) in enumerate(list(odpair_list.items())[:5]):
        print(f"  Odpair {odpair_id}: keys = {list(odpair_data.keys())}")
        if 'path_id' in odpair_data:
            path_id = odpair_data['path_id']
            if path_id in path_list:
                print(f"    path_id: {path_id}, path_length: {path_list[path_id]['length']} km")

    # Check f variable structure
    print("\nFirst 5 f keys:")
    for i, (key, value) in enumerate(list(output_data['f'].items())[:5]):
        print(f"  Key: {key}")
        print(f"    Length: {len(key)}, Types: {[type(k).__name__ for k in key]}")
        if value > 0:
            print(f"    Value: {value}")

    # Build route_lengths dictionary like the notebook does
    route_lengths = {}
    for odpair_id, odpair_data in odpair_list.items():
        path_id = odpair_data['path_id']
        path_data = path_list[path_id]
        length = path_data['length']
        route_lengths[odpair_id] = length

    print(f"\nroute_lengths dictionary size: {len(route_lengths)}")
    print(f"Sample route_lengths: {dict(list(route_lengths.items())[:5])}")

    # Check how many odpairs have paths > 100km
    long_routes = {k: v for k, v in route_lengths.items() if v > 100}
    print(f"\nRoutes > 100km: {len(long_routes)} out of {len(route_lengths)}")
    print(f"Length distribution:")
    print(f"  0-100 km: {sum(1 for v in route_lengths.values() if v < 100)}")
    print(f"  100-200 km: {sum(1 for v in route_lengths.values() if 100 <= v < 200)}")
    print(f"  200-300 km: {sum(1 for v in route_lengths.values() if 200 <= v < 300)}")
    print(f"  300-500 km: {sum(1 for v in route_lengths.values() if 300 <= v < 500)}")
    print(f"  500-1000 km: {sum(1 for v in route_lengths.values() if 500 <= v < 1000)}")
    print(f"  >1000 km: {sum(1 for v in route_lengths.values() if v >= 1000)}")

    # Now check what odpair_ids appear in f with BEV
    print("\nChecking which odpair_ids have BEV flow...")
    bev_vehicle_id = 1  # From the output you showed

    bev_odpairs = set()
    for key, value in output_data['f'].items():
        if value > 0:
            # Try different ways to extract odpair_id
            print(f"Checking key structure: {key}")
            # The key should be (year, odpair_id, (mode_id, vehicle_id), gen)
            year = key[0]
            odpair_id = key[1]
            mode_vehicle = key[2]
            gen = key[3]

            if isinstance(mode_vehicle, tuple) and len(mode_vehicle) >= 2:
                vehicle_id = mode_vehicle[1]
                if vehicle_id == bev_vehicle_id:
                    bev_odpairs.add(odpair_id)
                    if odpair_id in route_lengths:
                        print(f"  BEV flow on odpair {odpair_id}, path length: {route_lengths[odpair_id]} km")
                    else:
                        print(f"  BEV flow on odpair {odpair_id}, but odpair_id NOT in route_lengths!")
            break  # Just check first one for now

else:
    print("No .pkl files found in results directory")
