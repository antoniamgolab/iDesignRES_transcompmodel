"""Quick test to verify the module imports correctly"""

try:
    from sub_border_regions_cross_case import analyze_sub_region_cross_case_preloaded
    print("SUCCESS: analyze_sub_region_cross_case_preloaded imported")
    print(f"  Function type: {type(analyze_sub_region_cross_case_preloaded)}")
    print(f"  Docstring preview: {analyze_sub_region_cross_case_preloaded.__doc__[:100]}...")
except ImportError as e:
    print(f"FAILED: {e}")

try:
    from sub_border_regions_cross_case import compare_sub_region_across_cases_preloaded
    print("SUCCESS: compare_sub_region_across_cases_preloaded imported")
except ImportError as e:
    print(f"FAILED: {e}")

# List all available functions
import sub_border_regions_cross_case
import inspect

print("\nAll functions in sub_border_regions_cross_case:")
for name, obj in inspect.getmembers(sub_border_regions_cross_case):
    if inspect.isfunction(obj) and not name.startswith('_'):
        print(f"  - {name}")
