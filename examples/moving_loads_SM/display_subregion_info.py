"""
Quick reference: Display available sub-border regions
"""
from sub_border_regions import SUB_BORDER_REGIONS, get_sub_border_region_info
import pandas as pd

print("\n" + "="*100)
print("AVAILABLE SUB-BORDER REGIONS")
print("="*100)

# Get overview as DataFrame
df_info = get_sub_border_region_info()
print("\nOverview Table:")
print(df_info.to_string(index=False))

# Detailed information
print("\n" + "="*100)
print("DETAILED INFORMATION")
print("="*100)

for cluster_name, info in SUB_BORDER_REGIONS.items():
    print(f"\n{cluster_name}")
    print("-" * 100)
    print(f"Description:  {info['description']}")
    print(f"Countries:    {', '.join(sorted(info['countries']))}")
    print(f"Num Regions:  {len(info['regions'])}")
    print(f"NUTS2 Codes:  {', '.join(sorted(info['regions']))}")
    print(f"Plot Color:   {info['color']}")

print("\n" + "="*100)
print("\nUSAGE EXAMPLES:")
print("="*100)

print("""
# Analyze Austria-Germany-Italy cluster:
df_comparison, df_summary = analyze_sub_region_cross_case_preloaded(
    loaded_runs=loaded_runs,
    case_labels=case_labels,
    sub_region_name='Austria-Germany-Italy',  # <-- Use any cluster name
    years_to_plot=[2030, 2040, 2050],
    baseline_case='Var-Var',
    show_plots=True,
    verbose=True
)

# Other options:
#   sub_region_name='Denmark-Germany'
#   sub_region_name='Norway-Sweden'
""")
