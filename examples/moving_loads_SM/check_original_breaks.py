import yaml

# Check original breaks from nuts2 data
breaks = yaml.safe_load(open('input_data/nuts2_international_360_tol_one_third/MandatoryBreaks.yaml'))
path_breaks = [b for b in breaks if b['path_id'] == 2665]

print("Original breaks (nuts2_international_360_tol_one_third):")
print(f"Total: {len(path_breaks)}")
for b in path_breaks[:5]:
    print(f"  Break #{b['break_number']}: geo_id={b['latest_geo_id']}, "
          f"time={b['cumulative_driving_time']:.1f}h, dist={b['cumulative_distance']:.0f}km")
