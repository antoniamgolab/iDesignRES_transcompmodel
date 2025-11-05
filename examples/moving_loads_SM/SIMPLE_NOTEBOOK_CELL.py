"""
SIMPLE NOTEBOOK CELL - Copy this directly into your notebook

Place this AFTER you have df_comparison from analyze_sub_region_cross_case_preloaded()
"""

# =============================================================================
# Load traffic metrics and combine with df_comparison
# =============================================================================

import pandas as pd
import numpy as np

# Load traffic metrics
traffic_df = pd.read_csv('nuts2_traffic_metrics.csv')

# Define cluster codes
CLUSTER_DE_DK_SE = ['DEF0', 'DK01', 'DK02', 'DK03', 'DK04', 'DK05', 'SE22', 'SE23']

# Map NUTS2 to country
NUTS2_TO_COUNTRY = {
    'DEF0': 'DE',
    'DK01': 'DK', 'DK02': 'DK', 'DK03': 'DK', 'DK04': 'DK', 'DK05': 'DK',
    'SE22': 'SE', 'SE23': 'SE'
}

# Filter to cluster and aggregate by country
traffic_cluster = traffic_df[traffic_df['NUTS2_CODE'].isin(CLUSTER_DE_DK_SE)].copy()
traffic_cluster['country'] = traffic_cluster['NUTS2_CODE'].map(NUTS2_TO_COUNTRY)

traffic_by_country = traffic_cluster.groupby('country').agg({
    'total_tonnes': 'sum',
    'total_tkm': 'sum'
}).reset_index()

print("Traffic by country:")
print(traffic_by_country)

# Merge with df_comparison
combined = df_comparison.merge(traffic_by_country, on='country', how='left')

# Calculate MWh/TKM
combined['MWh_per_TKM'] = combined['electricity'] / combined['total_tkm']

# Display result
print("\nCombined data with MWh/TKM:")
display(combined[['case', 'country', 'year', 'electricity', 'total_tkm', 'MWh_per_TKM']].head(15))

# Summary by year and case
print("\nMWh/TKM by year and scenario:")
pivot = combined.pivot_table(
    values='MWh_per_TKM',
    index=['country', 'year'],
    columns='case',
    aggfunc='mean'
)
display(pivot)

# Save results
combined.to_csv('combined_electrification_traffic_de_dk_se.csv', index=False)
print("\nSaved to: combined_electrification_traffic_de_dk_se.csv")
