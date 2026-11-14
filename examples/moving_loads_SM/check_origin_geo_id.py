"""
Check if the origin geo ID in results matches path.sequence[1].id
to verify if the initial SOC constraint condition is being satisfied.
"""

import yaml
import re

base_path = "C:/Users/simuser/Documents/AntoniaGolab/Scand_Med_analysis/SM_baby_2/iDesignRES_transcompmodel/examples/moving_loads_SM"

# Use var_var run, path 2228
case_name = "case_20251110_160304_var_var"
result_timestamp = "case_20251110_160304_var_var_cs_2025-11-16_17-02-00"
input_dir = f"{base_path}/input_data/{case_name}"
results_dir = f"{base_path}/results/{case_name}"

year = 2056
path_id = 2228
tv_id = 1  # BEV

print(f"\n{'='*100}")
print(f"ORIGIN GEO ID VERIFICATION - Path {path_id}")
print(f"{'='*100}\n")

# Load input data
print("Loading input data...")
with open(f"{input_dir}/Path.yaml", 'r') as f:
    paths = yaml.safe_load(f)

# Load results
print("Loading results...")
with open(f"{results_dir}/{result_timestamp}_f_dict.yaml", 'r') as f:
    f_dict = yaml.safe_load(f)
with open(f"{results_dir}/{result_timestamp}_soc_dict.yaml", 'r') as f:
    soc_dict = yaml.safe_load(f)

# Get path info
path_info = next(p for p in paths if p['id'] == path_id)
sequence = path_info['sequence']

print(f"Path {path_id} information:")
print(f"  Sequence length: {len(sequence)}")
print(f"  Sequence type: {type(sequence[0])}")

# Extract geo IDs from sequence
if isinstance(sequence[0], dict):
    origin_geo = sequence[0]['id']
    print(f"  Origin geo ID (sequence[0]['id']): {origin_geo}")
    print(f"  First few nodes: {[node['id'] for node in sequence[:3]]}")
else:
    origin_geo = sequence[0]
    print(f"  Origin geo ID (sequence[0]): {origin_geo}")
    print(f"  First few nodes: {sequence[:3]}")

# Parse f_dict keys
def parse_f_key(key_str):
    pattern = r'\((\d+),\s*\((\d+),\s*(\d+),\s*(\d+)\),\s*\((\d+),\s*(\d+)\),\s*(\d+)\)'
    match = re.match(pattern, key_str)
    if match:
        return {
            'year': int(match.group(1)),
            'product': int(match.group(2)),
            'odpair': int(match.group(3)),
            'path': int(match.group(4)),
            'mode': int(match.group(5)),
            'techvehicle': int(match.group(6)),
            'generation': int(match.group(7))
        }
    return None

# Find flow entries for this path
print(f"\n{'='*100}")
print(f"FLOW ENTRIES FOR PATH {path_id}, YEAR {year}, BEV")
print(f"{'='*100}\n")

flow_entries = []
for key_str, value in f_dict.items():
    parsed = parse_f_key(key_str)
    if parsed and parsed['year'] == year and parsed['path'] == path_id and parsed['techvehicle'] == tv_id:
        val = float(value) if isinstance(value, str) else value
        if val > 0.01:
            flow_entries.append({
                'key': key_str,
                'parsed': parsed,
                'value': val
            })

print(f"Found {len(flow_entries)} flow entries:")
for entry in flow_entries:
    p = entry['parsed']
    print(f"  Product: {p['product']}, OD pair: {p['odpair']}, Generation: {p['generation']}, Flow: {entry['value']:.2f} t/year")

# Check SOC entries at origin
print(f"\n{'='*100}")
print(f"SOC ENTRIES AT ORIGIN (geo={origin_geo})")
print(f"{'='*100}\n")

soc_at_origin = []
for key_str, value in soc_dict.items():
    # SOC key format: (year, (product, odpair, path, geo), techvehicle, generation)
    # Try to parse it
    pattern = r'\((\d+),\s*\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\),\s*(\d+),\s*(\d+)\)'
    match = re.match(pattern, key_str)
    if match:
        parsed = {
            'year': int(match.group(1)),
            'product': int(match.group(2)),
            'odpair': int(match.group(3)),
            'path': int(match.group(4)),
            'geo': int(match.group(5)),
            'techvehicle': int(match.group(6)),
            'generation': int(match.group(7))
        }

        if (parsed['year'] == year and parsed['path'] == path_id and
            parsed['techvehicle'] == tv_id and parsed['geo'] == origin_geo):
            val = float(value) if isinstance(value, str) else value
            soc_at_origin.append({
                'key': key_str,
                'parsed': parsed,
                'value': val
            })

if soc_at_origin:
    print(f"Found {len(soc_at_origin)} SOC entries at origin:")
    for entry in soc_at_origin:
        p = entry['parsed']
        print(f"  Product: {p['product']}, OD pair: {p['odpair']}, Generation: {p['generation']}")
        print(f"  SOC: {entry['value']:.2f} kWh = {entry['value']/1e6:.6f} GWh")
else:
    print(f"*** NO SOC entries found at origin (geo={origin_geo}) ***")
    print(f"\nLet me check what geo IDs actually exist in SOC results for this path...")

    geo_ids_in_soc = set()
    for key_str, value in soc_dict.items():
        pattern = r'\((\d+),\s*\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\),\s*(\d+),\s*(\d+)\)'
        match = re.match(pattern, key_str)
        if match:
            parsed = {
                'year': int(match.group(1)),
                'path': int(match.group(4)),
                'geo': int(match.group(5)),
                'techvehicle': int(match.group(6))
            }
            if parsed['year'] == year and parsed['path'] == path_id and parsed['techvehicle'] == tv_id:
                geo_ids_in_soc.add(parsed['geo'])

    print(f"\nGeo IDs found in SOC results for path {path_id}, year {year}, BEV:")
    print(f"  {sorted(geo_ids_in_soc)}")
    print(f"\nOrigin geo from Path.yaml: {origin_geo}")

    if origin_geo not in geo_ids_in_soc:
        print(f"\n*** ERROR: Origin geo {origin_geo} is NOT in SOC results! ***")
        print(f"This means the initial SOC constraint is likely not being applied.")
    else:
        print(f"\n✓ Origin geo {origin_geo} exists in SOC results")

print(f"\n{'='*100}\n")
