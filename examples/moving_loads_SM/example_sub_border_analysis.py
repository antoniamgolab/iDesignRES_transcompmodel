"""
Example: Sub-Border Region Analysis

This script demonstrates how to use the sub_border_regions module to analyze
electrification in specific geographic clusters, such as the Austria-Germany-Italy
border region.
"""

from sub_border_regions import (
    analyze_sub_border_regions,
    get_sub_border_region_info,
    SUB_BORDER_REGIONS
)

# Display available sub-border regions
print("Available Sub-Border Region Clusters:")
print("=" * 80)
df_info = get_sub_border_region_info()
print(df_info.to_string(index=False))
print("\n")

# Show detailed region information
for cluster_name, cluster_info in SUB_BORDER_REGIONS.items():
    print(f"\n{cluster_name}:")
    print(f"  Description: {cluster_info['description']}")
    print(f"  Countries: {', '.join(sorted(cluster_info['countries']))}")
    print(f"  NUTS2 Regions ({len(cluster_info['regions'])}):")
    for region in sorted(cluster_info['regions']):
        print(f"    - {region}")

print("\n" + "=" * 80)
print("\nTo use with your data, load your input_data and output_data first:")
print("""
# Example 1: Analyze Austria-Germany-Italy cluster only
df_austria_cluster = analyze_sub_border_regions(
    input_data,
    output_data,
    years_to_plot=[2030, 2040, 2050],
    sub_region_name='Austria-Germany-Italy',
    show_plots=True,
    verbose=True
)

# Access results by country
austria_results = df_austria_cluster[df_austria_cluster['country'] == 'AT']
germany_results = df_austria_cluster[df_austria_cluster['country'] == 'DE']
italy_results = df_austria_cluster[df_austria_cluster['country'] == 'IT']

# Example 2: Analyze all sub-border regions and compare
df_all, results_by_region = analyze_sub_border_regions(
    input_data,
    output_data,
    years_to_plot=[2030, 2040, 2050],
    show_plots=True,
    verbose=True
)

# Compare electrification across clusters
import pandas as pd
comparison = df_all.groupby(['sub_region', 'year'])['electrification_pct'].mean()
print(comparison)

# Example 3: Focus on specific regions within Austria-Germany-Italy cluster
austria_german_italian_regions = SUB_BORDER_REGIONS['Austria-Germany-Italy']['regions']
print(f"Analyzing {len(austria_german_italian_regions)} NUTS2 regions:")
print(sorted(austria_german_italian_regions))
""")
