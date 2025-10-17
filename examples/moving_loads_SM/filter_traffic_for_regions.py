"""
Traffic Filtering Helper
=========================

This script should be run BEFORE calling create_nuts3_paths_from_traffic()
in the SM-preprocessing.ipynb notebook.

It filters the traffic data to only include OD-pairs where BOTH the origin
and destination are within the filtered network regions.

Usage in notebook:
    %run filter_traffic_for_regions.py

    # Then continue with create_nuts3_paths_from_traffic call
"""

import pandas as pd

def filter_traffic_for_network_regions(traffic_df, network_nodes_df):
    """
    Filter traffic to only include OD-pairs within the network regions.

    Parameters:
    -----------
    traffic_df : pd.DataFrame
        Truck traffic data with ID_origin_region and ID_destination_region columns
    network_nodes_df : pd.DataFrame
        Network nodes with ETISplus_Zone_ID column

    Returns:
    --------
    filtered_traffic : pd.DataFrame
        Traffic data filtered to only include OD-pairs within network regions
    """
    # Get set of region IDs in the network
    network_region_ids = set(network_nodes_df['ETISplus_Zone_ID'].unique())

    print("=" * 80)
    print("FILTERING TRAFFIC DATA FOR NETWORK REGIONS")
    print("=" * 80)
    print(f"Network regions: {len(network_region_ids)}")
    print(f"Traffic rows before filtering: {len(traffic_df):,}")

    # Filter: keep only traffic where BOTH origin AND destination are in network
    filtered_traffic = traffic_df[
        traffic_df['ID_origin_region'].isin(network_region_ids) &
        traffic_df['ID_destination_region'].isin(network_region_ids)
    ].copy()

    print(f"Traffic rows after filtering: {len(filtered_traffic):,}")
    print(f"Rows removed: {len(traffic_df) - len(filtered_traffic):,}")
    print(f"Percentage kept: {100 * len(filtered_traffic) / len(traffic_df):.1f}%")
    print("=" * 80)

    return filtered_traffic


# Auto-detect and filter traffic data in notebook environment
if __name__ == "__main__":
    # Try to detect variables in the notebook namespace
    try:
        # Check if we're running in a notebook
        get_ipython()

        # Try to find traffic variable
        traffic_var = None
        traffic_var_name = None
        for var_name in ['long_haul_truck_traffic', 'filtered_truck_traffic', 'truck_traffic']:
            if var_name in dir():
                traffic_var = eval(var_name)
                traffic_var_name = var_name
                print(f"Found traffic data: {var_name} ({len(traffic_var):,} rows)")
                break

        # Try to find nodes variable
        nodes_var = None
        nodes_var_name = None
        for var_name in ['filtered_network_nodes', 'network_nodes']:
            if var_name in dir():
                nodes_var = eval(var_name)
                nodes_var_name = var_name
                print(f"Found network nodes: {var_name} ({len(nodes_var):,} nodes)")
                break

        if traffic_var is not None and nodes_var is not None:
            # Filter the traffic
            filtered = filter_traffic_for_network_regions(traffic_var, nodes_var)

            # Update the variable in the notebook namespace
            globals()[traffic_var_name] = filtered

            print(f"\n[OK] Updated {traffic_var_name} with filtered data")
            print(f"[OK] Ready to call create_nuts3_paths_from_traffic()")
        else:
            print("[ERROR] Could not find required variables in notebook")
            print("Make sure you have:")
            print("  - Traffic data: long_haul_truck_traffic, filtered_truck_traffic, or truck_traffic")
            print("  - Network nodes: filtered_network_nodes or network_nodes")

    except NameError:
        # Not in notebook, print usage
        print(__doc__)
