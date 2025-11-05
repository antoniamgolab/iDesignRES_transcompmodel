"""Quick check that synthetic nodes are properly saved."""
import yaml

# Load the new case
case_dir = "input_data/case_20251029_154754"

paths = yaml.safe_load(open(f"{case_dir}/Path.yaml"))
breaks = yaml.safe_load(open(f"{case_dir}/MandatoryBreaks.yaml"))

# Check path 2665
path = next((p for p in paths if p['id'] == 2665), None)
print("=" * 80)
print("PATH 2665 (70 -> 56, 3266km)")
print("=" * 80)
print(f"Number of nodes in sequence: {len(path['sequence'])}")
print(f"Sequence: {path['sequence']}")
print(f"Cumulative distances: {[round(d, 1) for d in path['cumulative_distance']]}")
print()

# Check mandatory breaks
path_breaks = [b for b in breaks if b['path_id'] == 2665]
print("=" * 80)
print(f"MANDATORY BREAKS FOR PATH 2665 ({len(path_breaks)} breaks)")
print("=" * 80)

for b in path_breaks:
    print(f"Break #{b['break_number']:2d}: "
          f"geo_id={b['latest_geo_id']:3d}, "
          f"node_idx={b['latest_node_idx']:2d}, "
          f"time={b['cumulative_driving_time']:5.1f}h, "
          f"dist={b['cumulative_distance']:6.0f}km")

print()
print("=" * 80)
print("VERIFICATION")
print("=" * 80)

# Verify breaks reference correct geo_ids
origin_geo = path['sequence'][0]
breaks_at_origin = sum(1 for b in path_breaks if b['latest_geo_id'] == origin_geo)
breaks_at_destination = sum(1 for b in path_breaks if b['latest_geo_id'] != origin_geo)

print(f"Origin geo_id: {origin_geo}")
print(f"Breaks at origin geo_id: {breaks_at_origin}")
print(f"Breaks at non-origin geo_id: {breaks_at_destination}")
print()

if breaks_at_origin > 0:
    print("WARNING: Some breaks still reference origin geo_id!")
    print("This will cause conflicts with Julia origin constraint (travel_time=0)")
else:
    print("OK: All breaks reference non-origin geo_ids")
    print("No conflict with Julia origin constraint!")

print()
print("Done!")
