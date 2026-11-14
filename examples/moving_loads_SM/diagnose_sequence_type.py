"""
Diagnose the sequence type issue at line 3610 of model_functions.jl

This script checks:
1. What type are sequence elements after YAML loading?
2. What values are in p_r_k_g_pairs for path 2228?
3. Would the condition `geo_id == path.sequence[1].id` ever be true?
"""

import yaml

base_path = "C:/Users/simuser/Documents/AntoniaGolab/Scand_Med_analysis/SM_baby_2/iDesignRES_transcompmodel/examples/moving_loads_SM"
case_name = "case_20251110_160304_var_var"
input_dir = f"{base_path}/input_data/{case_name}"

print(f"\n{'='*100}")
print(f"INVESTIGATING SEQUENCE TYPE IN PATH.YAML")
print(f"{'='*100}\n")

# Load Path.yaml
print("Loading Path.yaml...")
with open(f"{input_dir}/Path.yaml", 'r') as f:
    paths = yaml.safe_load(f)

# Check path 2228
path_2228 = next(p for p in paths if p['id'] == 2228)

print(f"Path 2228 information:")
print(f"  ID: {path_2228['id']}")
print(f"  Length: {path_2228['length']:.2f} km")
print(f"  Sequence: {path_2228['sequence']}")
print(f"  Sequence type: {type(path_2228['sequence'])}")
print(f"  First element: {path_2228['sequence'][0]}")
print(f"  First element type: {type(path_2228['sequence'][0])}")

# Check if sequence elements are integers or dicts
if isinstance(path_2228['sequence'][0], dict):
    print(f"\n  → Sequence elements are DICTIONARIES with .id field")
    print(f"  → path.sequence[1].id would be: {path_2228['sequence'][0]['id']}")
elif isinstance(path_2228['sequence'][0], int):
    print(f"\n  → Sequence elements are INTEGERS (plain IDs)")
    print(f"  → path.sequence[1].id would FAIL - integers don't have .id attribute!")
    print(f"  → Should use path.sequence[1] directly instead")

print(f"\n{'='*100}")
print(f"CHECKING HOW p_r_k_g_pairs WOULD BE CONSTRUCTED")
print(f"{'='*100}\n")

# Simulate p_r_k_g_pairs construction for path 2228
# We need to check odpairs that use this path

with open(f"{input_dir}/Odpairs.yaml", 'r') as f:
    odpairs = yaml.safe_load(f)

print("Finding odpairs that use path 2228...")
odpairs_with_2228 = []
for odpair in odpairs:
    if 'paths' in odpair:
        path_ids = [p['id'] if isinstance(p, dict) else p for p in odpair['paths']]
        if 2228 in path_ids:
            odpairs_with_2228.append(odpair)
            print(f"  OD pair {odpair['id']} (product {odpair['product_id']}) uses path 2228")

if odpairs_with_2228:
    print(f"\nFor path 2228, p_r_k_g_pairs would contain:")
    print(f"  Sequence for path 2228: {path_2228['sequence']}")

    for odpair in odpairs_with_2228[:3]:  # Just first 3 to avoid clutter
        product_id = odpair['product_id']
        odpair_id = odpair['id']
        path_id = 2228

        print(f"\n  For product={product_id}, odpair={odpair_id}, path={path_id}:")
        for geo_id in path_2228['sequence']:
            print(f"    ({product_id}, {odpair_id}, {path_id}, {geo_id})")

            # Check if condition at line 3610 would be true
            origin_geo = path_2228['sequence'][0]
            if geo_id == origin_geo:
                print(f"      → This is the ORIGIN - condition at line 3610 should be TRUE")
                print(f"      → Checking: geo_id ({geo_id}) == path.sequence[1] ({origin_geo})")

                if isinstance(origin_geo, int):
                    print(f"      → PROBLEM: path.sequence[1] is int, but code tries path.sequence[1].id")
                    print(f"      → This will cause AttributeError: 'int' object has no attribute 'id'")
                else:
                    print(f"      → OK: path.sequence[1] is dict/object with .id field")

print(f"\n{'='*100}")
print(f"CONCLUSION")
print(f"{'='*100}\n")

if isinstance(path_2228['sequence'][0], int):
    print("CRITICAL BUG IDENTIFIED:")
    print("  - In YAML files, path sequences are stored as plain integers")
    print("  - Python yaml.safe_load() preserves them as integers")
    print("  - Line 3610 in model_functions.jl tries to access path.sequence[1].id")
    print("  - But if Julia also loads them as integers, this would fail!")
    print("")
    print("HOWEVER:")
    print("  - Julia's TransComp module may convert integers to GeographicElement objects")
    print("  - Need to check support_functions.jl to see how Path structs are created")
    print("  - The fact that p_r_k_g_pairs uses 'el.id' suggests Julia DOES convert them")
    print("")
    print("NEXT STEP:")
    print("  - Read support_functions.jl to find where Path objects are constructed")
    print("  - Check if YAML integers are converted to GeographicElement objects")
else:
    print("Sequence elements are dictionaries/objects - line 3610 should work correctly")

print(f"\n{'='*100}\n")
