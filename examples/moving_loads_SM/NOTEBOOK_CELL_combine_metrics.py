"""
NOTEBOOK CELL: Combine df_comparison with traffic metrics

Copy this into your results_representation.ipynb notebook
Place it AFTER you have df_comparison from analyze_sub_region_cross_case_preloaded()
"""

# =============================================================================
# CELL 1: Import and combine data
# =============================================================================

from combine_electrification_traffic_metrics import *

# Define cluster codes
CLUSTER_DE_DK_SE = ['DEF0', 'DK01', 'DK02', 'DK03', 'DK04', 'DK05', 'SE22', 'SE23']
CLUSTER_AT_DE_IT = ['AT31', 'AT32', 'AT33', 'AT34', 'DE14', 'DE21', 'DE22', 'DE27', 'ITH1', 'ITH3']

# Combine Germany-Denmark-Sweden cluster data
combined_de_dk_se, traffic_summary_de_dk_se = combine_electrification_traffic(
    df_comparison,
    traffic_metrics_file='nuts2_traffic_metrics.csv',
    cluster_name='Germany-Denmark-Sweden',
    cluster_codes=CLUSTER_DE_DK_SE
)

# Display combined data
display(combined_de_dk_se.head(10))


# =============================================================================
# CELL 2: Show summary statistics
# =============================================================================

display_summary(combined_de_dk_se, cluster_name='Germany-Denmark-Sweden')


# =============================================================================
# CELL 3: Visualize MWh/TKM over time
# =============================================================================

import matplotlib.pyplot as plt
import numpy as np

fig, axes = plt.subplots(1, 3, figsize=(18, 5))

years = sorted(combined_de_dk_se['year'].unique())
cases = sorted(combined_de_dk_se['case'].unique())
countries = sorted(combined_de_dk_se['country'].unique())

# Plot 1: MWh/TKM by country over years (for one scenario)
ax = axes[0]
baseline_case = cases[0]  # e.g., 'Var-Var'
baseline_data = combined_de_dk_se[combined_de_dk_se['case'] == baseline_case]

for country in countries:
    country_data = baseline_data[baseline_data['country'] == country]
    ax.plot(country_data['year'], country_data['MWh_per_TKM'],
           marker='o', label=country, linewidth=2, markersize=8)

ax.set_xlabel('Year', fontsize=12, fontweight='bold')
ax.set_ylabel('MWh/TKM', fontsize=12, fontweight='bold')
ax.set_title(f'Electricity Efficiency by Country\n({baseline_case})',
            fontsize=13, fontweight='bold')
ax.legend()
ax.grid(True, alpha=0.3)

# Plot 2: Total cluster electricity over time
ax = axes[1]
for case in cases:
    case_data = combined_de_dk_se[combined_de_dk_se['case'] == case]
    total_by_year = case_data.groupby('year')['electricity'].sum()
    ax.plot(total_by_year.index, total_by_year.values,
           marker='s', label=case, linewidth=2, markersize=8)

ax.set_xlabel('Year', fontsize=12, fontweight='bold')
ax.set_ylabel('Total Electricity (MWh)', fontsize=12, fontweight='bold')
ax.set_title('Total Cluster Electrification\nAcross Scenarios',
            fontsize=13, fontweight='bold')
ax.legend()
ax.grid(True, alpha=0.3)

# Plot 3: Average MWh/TKM by scenario
ax = axes[2]
for case in cases:
    case_data = combined_de_dk_se[combined_de_dk_se['case'] == case]
    avg_by_year = case_data.groupby('year')['MWh_per_TKM'].mean()
    ax.plot(avg_by_year.index, avg_by_year.values,
           marker='^', label=case, linewidth=2, markersize=8)

ax.set_xlabel('Year', fontsize=12, fontweight='bold')
ax.set_ylabel('Average MWh/TKM', fontsize=12, fontweight='bold')
ax.set_title('Average Efficiency Across Scenarios',
            fontsize=13, fontweight='bold')
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('electrification_efficiency_analysis.png', dpi=300, bbox_inches='tight')
plt.show()


# =============================================================================
# CELL 4: Create comparison table (Germany-Denmark-Sweden vs Austria-Germany-Italy)
# =============================================================================

# If you also have Austria-Germany-Italy data, you can compare:
# (Uncomment if you ran analysis for both clusters)

# combined_at_de_it, traffic_summary_at_de_it = combine_electrification_traffic(
#     df_comparison_at_de_it,  # Your AT-DE-IT df_comparison
#     traffic_metrics_file='nuts2_traffic_metrics.csv',
#     cluster_name='Austria-Germany-Italy',
#     cluster_codes=CLUSTER_AT_DE_IT
# )
#
# # Compare clusters
# comparison = pd.DataFrame({
#     'Cluster': ['DE-DK-SE', 'AT-DE-IT'],
#     'Total TKM': [
#         combined_de_dk_se['total_tkm'].iloc[0] * len(combined_de_dk_se['country'].unique()),
#         combined_at_de_it['total_tkm'].iloc[0] * len(combined_at_de_it['country'].unique())
#     ],
#     'Avg MWh/TKM': [
#         combined_de_dk_se['MWh_per_TKM'].mean(),
#         combined_at_de_it['MWh_per_TKM'].mean()
#     ]
# })
#
# display(comparison)


# =============================================================================
# CELL 5: Export results
# =============================================================================

# Export combined data
files = export_results(combined_de_dk_se, 'Germany-Denmark-Sweden')

print("\nExported files:")
for f in files:
    print(f"  - {f}")


# =============================================================================
# CELL 6: Quick analysis - Efficiency by country
# =============================================================================

# Calculate average MWh/TKM by country across all scenarios and years
efficiency_by_country = combined_de_dk_se.groupby('country').agg({
    'MWh_per_TKM': ['mean', 'std', 'min', 'max'],
    'electricity': 'mean',
    'total_tkm': 'first'
}).round(4)

print("\nEfficiency by Country (MWh/TKM):")
print(efficiency_by_country)

# Visualize
fig, ax = plt.subplots(figsize=(10, 6))

countries = efficiency_by_country.index
means = efficiency_by_country[('MWh_per_TKM', 'mean')]
stds = efficiency_by_country[('MWh_per_TKM', 'std')]

x = np.arange(len(countries))
ax.bar(x, means, yerr=stds, capsize=5, alpha=0.7, color='steelblue')
ax.set_xticks(x)
ax.set_xticklabels(countries, fontsize=12)
ax.set_ylabel('Average MWh/TKM', fontsize=12, fontweight='bold')
ax.set_title('Average Electricity Efficiency by Country\n(across all scenarios and years)',
            fontsize=13, fontweight='bold')
ax.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('efficiency_by_country.png', dpi=300, bbox_inches='tight')
plt.show()


# =============================================================================
# CELL 7: Filter specific scenario and year
# =============================================================================

# Example: Get MWh/TKM for Var-Var scenario in 2040
specific_data = combined_de_dk_se[
    (combined_de_dk_se['case'] == 'Var-Var') &
    (combined_de_dk_se['year'] == 2040)
][['country', 'electricity', 'total_tkm', 'MWh_per_TKM']]

print("\nVar-Var Scenario - Year 2040:")
display(specific_data)
