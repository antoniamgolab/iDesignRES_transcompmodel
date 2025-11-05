"""
Convert MWh/TKM to kWh/100km

Two interpretations:
1. kWh per 100 tonne-km (freight transport efficiency)
2. kWh per 100 km for average vehicle (requires average load assumption)
"""

import pandas as pd
import numpy as np

# =============================================================================
# Conversion Functions
# =============================================================================

def convert_MWh_TKM_to_kWh_100tkm(df, input_col='MWh_per_TKM', output_col='kWh_per_100tkm'):
    """
    Convert MWh/TKM to kWh per 100 tonne-km

    This keeps the freight component (tonne) in the metric.

    Conversion:
    - 1 MWh = 1,000 kWh
    - 1 TKM = 1 tonne × 1 km
    - 100 TKM = 100 tonne-km

    Formula: MWh/TKM × 1000 × 100 = kWh per 100 tonne-km
    """
    df = df.copy()
    df[output_col] = df[input_col] * 100000  # × 1000 (MWh→kWh) × 100 (per 100 tkm)
    return df


def convert_MWh_TKM_to_kWh_100km_per_vehicle(df, input_col='MWh_per_TKM',
                                             output_col='kWh_per_100km',
                                             avg_load_tonnes=15):
    """
    Convert MWh/TKM to kWh per 100 km for an average vehicle

    This assumes an average truck load.

    Parameters:
    -----------
    avg_load_tonnes : float
        Average freight load per vehicle in tonnes (default: 15 tonnes)
        Typical values:
        - Light truck: 5-10 tonnes
        - Medium truck: 10-15 tonnes
        - Heavy truck: 15-25 tonnes

    Formula:
    MWh/TKM × 1000 × 100 × avg_load_tonnes = kWh per 100 km
    """
    df = df.copy()
    df[output_col] = df[input_col] * 100000 * avg_load_tonnes
    df['avg_load_tonnes'] = avg_load_tonnes
    return df


# =============================================================================
# Complete Conversion Workflow
# =============================================================================

def add_all_efficiency_metrics(df, avg_load_tonnes=15):
    """
    Add all efficiency metrics to dataframe

    Adds:
    - kWh_per_TKM: kWh per tonne-kilometer
    - kWh_per_100tkm: kWh per 100 tonne-kilometers (freight efficiency)
    - kWh_per_100km: kWh per 100 km (vehicle efficiency, assumes avg load)
    """
    df = df.copy()

    # 1. kWh per TKM
    df['kWh_per_TKM'] = df['MWh_per_TKM'] * 1000

    # 2. kWh per 100 tonne-km (freight transport efficiency)
    df['kWh_per_100tkm'] = df['MWh_per_TKM'] * 100000

    # 3. kWh per 100 km for average vehicle
    df['kWh_per_100km'] = df['MWh_per_TKM'] * 100000 * avg_load_tonnes
    df['avg_load_tonnes_assumed'] = avg_load_tonnes

    return df


# =============================================================================
# NOTEBOOK CELL - Copy this into your notebook
# =============================================================================

"""
# After you have 'combined' dataframe with MWh_per_TKM:

# Option 1: kWh per 100 tonne-km (freight efficiency metric)
combined['kWh_per_100tkm'] = combined['MWh_per_TKM'] * 100000

# Option 2: kWh per 100 km (vehicle efficiency, assumes 15 tonne average load)
AVG_LOAD_TONNES = 15  # Adjust this based on your truck fleet
combined['kWh_per_100km'] = combined['MWh_per_TKM'] * 100000 * AVG_LOAD_TONNES

# Display
display(combined[['case', 'country', 'year', 'MWh_per_TKM', 'kWh_per_100tkm', 'kWh_per_100km']].head(10))

# Typical values for reference:
# - Electric trucks: 100-200 kWh per 100 km (full load)
# - Depends on: truck size, load, terrain, speed
"""


# =============================================================================
# Example Usage
# =============================================================================

if __name__ == "__main__":
    print("="*80)
    print("CONVERSION: MWh/TKM → kWh/100km")
    print("="*80)

    # Example data
    example_data = {
        'case': ['Var-Var', 'Var-Var', 'Var-Uni'],
        'country': ['DE', 'DK', 'DE'],
        'year': [2030, 2030, 2030],
        'electricity': [50000, 25000, 48000],
        'total_tkm': [1086388952, 1444468673, 1086388952],
        'MWh_per_TKM': [0.000046, 0.000017, 0.000044]
    }

    df = pd.DataFrame(example_data)

    print("\nOriginal data (MWh/TKM):")
    print(df)

    # Add all metrics
    df = add_all_efficiency_metrics(df, avg_load_tonnes=15)

    print("\n" + "="*80)
    print("WITH ALL EFFICIENCY METRICS:")
    print("="*80)
    print(df[['case', 'country', 'year', 'MWh_per_TKM', 'kWh_per_TKM',
              'kWh_per_100tkm', 'kWh_per_100km']].to_string(index=False))

    print("\n" + "="*80)
    print("INTERPRETATION:")
    print("="*80)
    print("""
    1. MWh_per_TKM: Original metric (energy per tonne-kilometer)

    2. kWh_per_TKM: Energy per tonne-kilometer in kWh
       - Same as MWh_per_TKM × 1000

    3. kWh_per_100tkm: Energy per 100 tonne-kilometers
       - Freight transport efficiency metric
       - Accounts for freight weight
       - Formula: MWh_per_TKM × 100,000

    4. kWh_per_100km: Energy per 100 km for average vehicle
       - Vehicle efficiency metric (like car consumption)
       - Assumes 15 tonne average load (adjustable)
       - Formula: MWh_per_TKM × 100,000 × avg_load_tonnes
       - Comparable to: "My truck uses 150 kWh per 100 km"

    Note: For freight transport, kWh_per_100tkm is the standard metric
          because it accounts for the amount of freight moved.
    """)

    print("\n" + "="*80)
    print("TYPICAL VALUES FOR ELECTRIC TRUCKS:")
    print("="*80)
    print("""
    Vehicle consumption (kWh per 100 km):
    - Light electric truck (empty): 50-80 kWh/100km
    - Heavy electric truck (empty): 80-120 kWh/100km
    - Heavy electric truck (full load, 20-25t): 150-200 kWh/100km
    - Tesla Semi (claimed): ~125 kWh/100km at full load

    Freight efficiency (kWh per 100 tonne-km):
    - Efficient electric truck: 5-8 kWh/100tkm
    - Typical electric truck: 8-12 kWh/100tkm
    - Depends on: truck size, payload utilization, terrain
    """)
