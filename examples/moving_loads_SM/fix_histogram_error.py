"""
Common Histogram Errors and Fixes
==================================

Troubleshooting guide for the truck traffic histogram.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# COMMON ERROR 1: Missing or NaN values
# =====================================
# Error: ValueError: Weights and data have different length
# Fix:

def fix_missing_values(df):
    """Remove rows with missing distance or traffic data."""
    print(f"Original rows: {len(df)}")

    # Check for missing values
    print(f"Missing Total_distance: {df['Total_distance'].isna().sum()}")
    print(f"Missing Traffic_flow_trucks_2030: {df['Traffic_flow_trucks_2030'].isna().sum()}")

    # Remove rows with missing data
    df_clean = df.dropna(subset=['Total_distance', 'Traffic_flow_trucks_2030'])

    print(f"After removing NaN: {len(df_clean)}")
    return df_clean


# COMMON ERROR 2: Infinite values
# ================================
# Error: ValueError: Weights and data have different length (after filtering inf)
# Fix:

def fix_infinite_values(df):
    """Remove rows with infinite values."""
    print(f"Infinite Total_distance: {np.isinf(df['Total_distance']).sum()}")
    print(f"Infinite Traffic: {np.isinf(df['Traffic_flow_trucks_2030']).sum()}")

    # Remove infinite values
    df_clean = df[~np.isinf(df['Total_distance']) &
                  ~np.isinf(df['Traffic_flow_trucks_2030'])]

    return df_clean


# COMMON ERROR 3: Empty dataframe after filtering
# ===============================================
# Error: ValueError: zero-size array to reduction operation minimum which has no identity
# Fix:

def check_empty(df):
    """Check if dataframe is empty after filtering."""
    if len(df) == 0:
        print("[ERROR] No data left after filtering!")
        print("Check your filter conditions.")
        return False
    return True


# COMMON ERROR 4: Negative distances
# ==================================
# Might cause weird histogram behavior
# Fix:

def fix_negative_values(df):
    """Remove or fix negative distances."""
    negative_count = (df['Total_distance'] < 0).sum()
    if negative_count > 0:
        print(f"[WARNING] Found {negative_count} negative distances")
        print("Removing negative values...")
        df = df[df['Total_distance'] >= 0]
    return df


# COMPLETE SOLUTION
# =================

def plot_truck_traffic_histogram_robust(filtered_truck_traffic):
    """
    Robust version that handles all common errors.
    """
    print("="*80)
    print("CREATING TRUCK TRAFFIC HISTOGRAM")
    print("="*80)

    # Make a copy to avoid modifying original
    df = filtered_truck_traffic.copy()

    # Step 1: Check initial data
    print(f"\nInitial data shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")

    # Step 2: Clean data
    print("\n1. Checking for missing values...")
    df = fix_missing_values(df)

    print("\n2. Checking for infinite values...")
    df = fix_infinite_values(df)

    print("\n3. Checking for negative values...")
    df = fix_negative_values(df)

    print("\n4. Checking if data remains...")
    if not check_empty(df):
        return None

    # Step 3: Get statistics BEFORE plotting
    print("\n5. Computing statistics...")
    avg = df['Total_distance'].mean()
    min_val = df['Total_distance'].min()
    max_val = df['Total_distance'].max()

    print(f"   Average distance: {avg:.2f} km")
    print(f"   Min distance:     {min_val:.2f} km")
    print(f"   Max distance:     {max_val:.2f} km")
    print(f"   Total routes:     {len(df):,}")

    # Step 4: Create histogram
    print("\n6. Creating histogram...")

    try:
        plt.figure(figsize=(10, 6))

        # Use explicit data and weights as arrays
        distances = df['Total_distance'].values
        weights = df['Traffic_flow_trucks_2030'].values

        print(f"   Distance array length: {len(distances)}")
        print(f"   Weights array length:  {len(weights)}")

        # Check if lengths match
        if len(distances) != len(weights):
            print(f"[ERROR] Length mismatch! {len(distances)} vs {len(weights)}")
            return None

        # Create histogram
        n, bins, patches = plt.hist(
            distances,
            bins=50,
            weights=weights,
            color='skyblue',
            edgecolor='black',
            alpha=0.7
        )

        plt.xlabel('Total Distance (km)', fontsize=12)
        plt.ylabel('Weighted Truck Traffic (2030)', fontsize=12)
        plt.title('Weighted Distribution of Total Distance (by Truck Traffic 2030)',
                 fontsize=13, fontweight='bold')
        plt.grid(True, linestyle='--', alpha=0.5)

        # Add statistics to plot
        plt.axvline(avg, color='red', linestyle='--', linewidth=2,
                   label=f'Mean: {avg:.0f} km')
        plt.legend()

        plt.tight_layout()
        plt.savefig('truck_traffic_histogram.png', dpi=300, bbox_inches='tight')
        print("[OK] Histogram saved to truck_traffic_histogram.png")

        plt.show()

        return df

    except Exception as e:
        print(f"\n[ERROR] Failed to create histogram: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return None


# DIAGNOSTIC FUNCTION
# ===================

def diagnose_data(filtered_truck_traffic):
    """
    Run comprehensive diagnostics on your data.
    """
    print("="*80)
    print("DATA DIAGNOSTICS")
    print("="*80)

    df = filtered_truck_traffic

    print(f"\n1. BASIC INFO:")
    print(f"   Shape: {df.shape}")
    print(f"   Columns: {df.columns.tolist()}")

    print(f"\n2. REQUIRED COLUMNS:")
    required = ['Total_distance', 'Traffic_flow_trucks_2030']
    for col in required:
        if col in df.columns:
            print(f"   ✓ {col} - EXISTS")
        else:
            print(f"   ✗ {col} - MISSING!")
            print(f"   Available columns: {df.columns.tolist()}")
            return False

    print(f"\n3. DATA QUALITY:")
    for col in required:
        data = df[col]
        print(f"\n   {col}:")
        print(f"     Count:    {data.count()}")
        print(f"     Missing:  {data.isna().sum()}")
        print(f"     Infinite: {np.isinf(data).sum()}")
        print(f"     Min:      {data.min()}")
        print(f"     Max:      {data.max()}")
        print(f"     Mean:     {data.mean()}")
        print(f"     Median:   {data.median()}")

    print(f"\n4. SAMPLE DATA:")
    print(df[required].head(10))

    return True


# USAGE EXAMPLE
# =============

if __name__ == "__main__":
    # Example: Load aggregated truck traffic data
    try:
        # Adjust path as needed
        truck_traffic = pd.read_csv("data/Trucktraffic_NUTS3/01_Trucktrafficflow.csv")

        # Apply your filtering
        # filtered_truck_traffic = truck_traffic[your_conditions]
        filtered_truck_traffic = truck_traffic  # Replace with your filter

        # Run diagnostics
        print("\nRunning diagnostics...")
        if diagnose_data(filtered_truck_traffic):
            print("\n" + "="*80)
            print("Data looks good! Creating histogram...")
            print("="*80)

            # Create histogram
            result = plot_truck_traffic_histogram_robust(filtered_truck_traffic)

            if result is not None:
                print("\n[SUCCESS] Histogram created successfully!")
            else:
                print("\n[FAILED] Could not create histogram")

    except FileNotFoundError:
        print("[ERROR] Data file not found")
        print("Please adjust the file path in the script")
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
