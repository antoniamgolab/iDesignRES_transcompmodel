"""
Check column names in traffic data
"""

import pandas as pd
from pathlib import Path

data_dir = Path("data/Trucktraffic_NUTS3")
traffic_file = data_dir / "01_Trucktrafficflow.csv"

truck_traffic = pd.read_csv(traffic_file)

print("Columns in traffic data:")
print(truck_traffic.columns.tolist())

print(f"\nFirst few rows:")
print(truck_traffic.head())
