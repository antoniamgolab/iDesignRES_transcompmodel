"""
Simple distance-based metrics starting from electricity consumption

This avoids the complex TKM conversions and works directly from:
- Total electricity consumed (MWh)
- Total TKM (tonne-kilometers)
- Average truck load assumption

To get: kWh per 60 km of driving
"""

import pandas as pd
import numpy as np


def calculate_simple_distance_metrics(combined_df, avg_load_tonnes=15):
    """
    Calculate simple distance-based metrics from electricity and TKM

    Logic:
    1. Total distance traveled = total_tkm / avg_load_tonnes
       (because TKM = tonnes × km, so km = TKM / tonnes)

    2. Energy per km = total_electricity / total_distance

    3. Energy per 60 km = energy_per_km × 60

    Parameters:
    -----------
    combined_df : pd.DataFrame
        Must have columns: electricity (MWh), total_tkm
    avg_load_tonnes : float
        Average truck load in tonnes (default: 15)

    Returns:
    --------
    pd.DataFrame with additional columns for distance metrics
    """

    df = combined_df.copy()

    print(f"\n{'='*80}")
    print(f"CALCULATING DISTANCE METRICS (AVG LOAD: {avg_load_tonnes} tonnes)")
    print('='*80)

    # Step 1: Calculate total distance traveled (in km)
    # TKM = tonnes × km, so: km = TKM / tonnes
    df['total_km_traveled'] = df['total_tkm'] / avg_load_tonnes

    print(f"\nStep 1: Calculate total distance traveled")
    print(f"  Formula: total_km = total_tkm / {avg_load_tonnes}")
    print(f"  Example: {df['total_tkm'].iloc[0]:,.0f} TKM / {avg_load_tonnes} tonnes = {df['total_km_traveled'].iloc[0]:,.0f} km")

    # Step 2: Convert electricity to kWh
    df['electricity_kWh'] = df['electricity'] * 1000

    print(f"\nStep 2: Convert electricity to kWh")
    print(f"  Formula: kWh = MWh × 1,000")
    print(f"  Example: {df['electricity'].iloc[0]:,.0f} MWh × 1,000 = {df['electricity_kWh'].iloc[0]:,.0f} kWh")

    # Step 3: Calculate kWh per km
    df['kWh_per_km'] = df['electricity_kWh'] / df['total_km_traveled']

    print(f"\nStep 3: Calculate energy per kilometer")
    print(f"  Formula: kWh/km = total_kWh / total_km")
    print(f"  Example: {df['electricity_kWh'].iloc[0]:,.0f} kWh / {df['total_km_traveled'].iloc[0]:,.0f} km = {df['kWh_per_km'].iloc[0]:.4f} kWh/km")

    # Step 4: Calculate kWh per 60 km
    df['kWh_per_60km'] = df['kWh_per_km'] * 60

    print(f"\nStep 4: Calculate energy per 60 km")
    print(f"  Formula: kWh/60km = kWh/km × 60")
    print(f"  Example: {df['kWh_per_km'].iloc[0]:.4f} kWh/km × 60 = {df['kWh_per_60km'].iloc[0]:.2f} kWh per 60 km")

    # Step 5: Also calculate per 100 km for reference
    df['kWh_per_100km'] = df['kWh_per_km'] * 100

    print(f"\nStep 5: Calculate energy per 100 km (for reference)")
    print(f"  Formula: kWh/100km = kWh/km × 100")
    print(f"  Example: {df['kWh_per_km'].iloc[0]:.4f} kWh/km × 100 = {df['kWh_per_100km'].iloc[0]:.2f} kWh per 100 km")

    # Store the assumption used
    df['avg_load_assumed_tonnes'] = avg_load_tonnes

    return df


def display_distance_summary(df):
    """
    Display summary of distance-based metrics
    """

    print(f"\n{'='*80}")
    print("DISTANCE-BASED METRICS SUMMARY")
    print('='*80)

    # Summary by country
    print("\n" + "-"*80)
    print("BY COUNTRY (average across all years and scenarios):")
    print("-"*80)

    summary = df.groupby('country').agg({
        'electricity_kWh': 'mean',
        'total_km_traveled': 'mean',
        'kWh_per_km': 'mean',
        'kWh_per_60km': 'mean',
        'kWh_per_100km': 'mean'
    }).round(2)

    print(summary)

    # Interpretation
    print("\n" + "-"*80)
    print("WHAT DOES THIS MEAN?")
    print("-"*80)
    print(f"""
For an average truck carrying {df['avg_load_assumed_tonnes'].iloc[0]} tonnes:

- kWh_per_km: Energy consumed per kilometer of driving
- kWh_per_60km: Energy consumed in a 60 km trip
- kWh_per_100km: Energy consumed in a 100 km trip (like car consumption ratings)

Example interpretation for first row:
  "{df['country'].iloc[0]}: A truck consumes {df['kWh_per_60km'].iloc[0]:.1f} kWh every 60 km of driving"

This assumes the truck is carrying {df['avg_load_assumed_tonnes'].iloc[0]} tonnes on average.
""")


# =============================================================================
# NOTEBOOK CELL - Copy this into your notebook
# =============================================================================

"""
# After you have 'combined' dataframe:

from simple_distance_metrics import calculate_simple_distance_metrics, display_distance_summary

# Calculate distance metrics with 15 tonne average load
AVG_LOAD_TONNES = 15  # Adjust based on your fleet characteristics
combined_with_distance = calculate_simple_distance_metrics(combined, AVG_LOAD_TONNES)

# Display summary
display_distance_summary(combined_with_distance)

# Show results
display(combined_with_distance[[
    'case', 'country', 'year',
    'electricity', 'total_tkm', 'total_km_traveled',
    'kWh_per_km', 'kWh_per_60km', 'kWh_per_100km'
]].head(15))

# Visualize kWh per 60 km by country
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(10, 6))
for country in combined_with_distance['country'].unique():
    country_data = combined_with_distance[combined_with_distance['country'] == country]
    ax.plot(country_data['year'], country_data['kWh_per_60km'],
           marker='o', label=country, linewidth=2)

ax.set_xlabel('Year', fontsize=12, fontweight='bold')
ax.set_ylabel('kWh per 60 km', fontsize=12, fontweight='bold')
ax.set_title(f'Energy Consumption per 60 km\\n(Assuming {AVG_LOAD_TONNES} tonne average load)',
            fontsize=13, fontweight='bold')
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()
"""


# =============================================================================
# Example Usage
# =============================================================================

if __name__ == "__main__":
    print("="*80)
    print("SIMPLE DISTANCE METRICS CALCULATOR")
    print("="*80)
    print("\nThis module calculates distance-based energy metrics directly from:")
    print("  1. Total electricity consumption (MWh)")
    print("  2. Total TKM (tonne-kilometers)")
    print("  3. Average truck load assumption (tonnes)")
    print("\nImport this in your notebook after creating 'combined' dataframe.")
    print("\nSee code comments for usage example.")
