"""
Notebook Cell Example: Sub-Border Region Analysis

Add these cells to your results_representation.ipynb notebook to analyze
electrification by sub-border region clusters.
"""

# =============================================================================
# CELL 1: Import and Setup
# =============================================================================
from sub_border_regions import (
    analyze_sub_border_regions,
    get_sub_border_region_info,
    SUB_BORDER_REGIONS,
    calculate_electrification_by_sub_border_region,
    plot_single_sub_region_detail
)
import pandas as pd
import matplotlib.pyplot as plt

# Display available sub-border region clusters
print("Available Sub-Border Region Clusters:")
df_info = get_sub_border_region_info()
display(df_info)


# =============================================================================
# CELL 2: Analyze Austria-Germany-Italy Cluster
# =============================================================================
# Focus on the Austria-Germany-Italy border region cluster
df_austria_cluster = analyze_sub_border_regions(
    input_data,
    output_data,
    years_to_plot=[2030, 2040, 2050],
    sub_region_name='Austria-Germany-Italy',
    show_plots=True,
    verbose=True
)

# Display results
print("\nAustria-Germany-Italy Cluster Results:")
display(df_austria_cluster)


# =============================================================================
# CELL 3: Compare Countries within Austria-Germany-Italy Cluster
# =============================================================================
# Compare electrification across AT, DE, IT within this cluster
fig, ax = plt.subplots(figsize=(10, 6))

for country in sorted(df_austria_cluster['country'].unique()):
    country_data = df_austria_cluster[df_austria_cluster['country'] == country]
    ax.plot(country_data['year'], country_data['electrification_pct'],
           marker='o', label=country, linewidth=2, markersize=8)

ax.set_xlabel('Year', fontsize=12)
ax.set_ylabel('Electrification %', fontsize=12)
ax.set_title('Electrification in Austria-Germany-Italy Border Cluster', fontsize=14, fontweight='bold')
ax.legend(title='Country', fontsize=10)
ax.grid(True, alpha=0.3)
ax.set_ylim(0, 100)

plt.tight_layout()
plt.show()


# =============================================================================
# CELL 4: Analyze All Sub-Border Regions and Compare
# =============================================================================
# Compare all sub-border region clusters
df_all_clusters, results_by_cluster = analyze_sub_border_regions(
    input_data,
    output_data,
    years_to_plot=[2030, 2040, 2050],
    show_plots=True,
    verbose=True
)

# Create summary comparison table
summary = df_all_clusters.groupby(['sub_region', 'year']).agg({
    'electrification_pct': 'mean',
    'electricity': 'sum',
    'total_fuel': 'sum'
}).reset_index()

summary.columns = ['Sub-Region', 'Year', 'Avg Electrification %',
                   'Total Electricity (MWh)', 'Total Fuel (MWh)']

print("\nSummary by Sub-Border Region:")
display(summary)


# =============================================================================
# CELL 5: Detailed Regional Breakdown for Austria-Germany-Italy
# =============================================================================
# Show which specific NUTS2 regions are included
austria_cluster_regions = SUB_BORDER_REGIONS['Austria-Germany-Italy']['regions']

print(f"Austria-Germany-Italy Cluster includes {len(austria_cluster_regions)} NUTS2 regions:")
print("\nBy country:")

# Organize by country
for country in ['AT', 'DE', 'IT']:
    country_regions = [r for r in sorted(austria_cluster_regions) if r.startswith(country)]
    print(f"\n{country}: {len(country_regions)} regions")
    for region in country_regions:
        print(f"  - {region}")


# =============================================================================
# CELL 6: Export Results
# =============================================================================
# Save Austria-Germany-Italy cluster results to CSV
df_austria_cluster.to_csv('austria_germany_italy_cluster_electrification.csv', index=False)
print("Results saved to: austria_germany_italy_cluster_electrification.csv")

# Save all clusters comparison
df_all_clusters.to_csv('all_sub_border_clusters_electrification.csv', index=False)
print("Results saved to: all_sub_border_clusters_electrification.csv")

# Save summary table
summary.to_csv('sub_border_clusters_summary.csv', index=False)
print("Summary saved to: sub_border_clusters_summary.csv")
