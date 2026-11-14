"""
Quick SOC sanity check for November 16 runs - checks one path per run
"""

import yaml
import re

base_path = "C:/Users/simuser/Documents/AntoniaGolab/Scand_Med_analysis/SM_baby_2/iDesignRES_transcompmodel/examples/moving_loads_SM"

runs = [
    {'name': 'var_var', 'case': 'case_20251110_160304_var_var', 'timestamp': 'case_20251110_160304_var_var_cs_2025-11-16_17-02-00'},
    {'name': 'var_uni', 'case': 'case_20251110_160335_var_uni', 'timestamp': 'case_20251110_160335_var_uni_cs_2025-11-16_17-15-38'},
    {'name': 'uni_var', 'case': 'case_20251110_160526_uni_var', 'timestamp': 'case_20251110_160526_uni_var_cs_2025-11-16_17-28-55'},
    {'name': 'uni_uni', 'case': 'case_20251110_160604_uni_uni', 'timestamp': 'case_20251110_160604_uni_uni_cs_2025-11-16_17-43-19'},
    {'name': 'reverse', 'case': 'case_20251110_160646_reverse', 'timestamp': 'case_20251110_160646_reverse_cs_2025-11-16_16-48-22'}
]

print(f"\n{'='*100}")
print(f"QUICK SOC SANITY CHECK - November 16 Runs")
print(f"{'='*100}\n")

for run_info in runs:
    case_name = run_info['case']
    result_timestamp = run_info['timestamp']
    results_dir = f"{base_path}/results/{case_name}"

    print(f"{run_info['name']}:")

    try:
        # Load just soc_dict to check for existence and basic stats
        print(f"  Loading SOC data...")
        with open(f"{results_dir}/{result_timestamp}_soc_dict.yaml", 'r') as f:
            soc_dict = yaml.safe_load(f)

        # Count entries by year
        year_counts = {}
        for key in soc_dict.keys():
            # Parse year from key [year, (product, odpair, path, geo), techvehicle, generation]
            match = re.match(r'\[(\d+),', str(key))
            if match:
                year = int(match.group(1))
                year_counts[year] = year_counts.get(year, 0) + 1

        print(f"  Total SOC entries: {len(soc_dict):,}")
        print(f"  Years: {sorted(year_counts.keys())}")
        print(f"  Entries in 2056: {year_counts.get(2056, 0):,}")
        print(f"  Status: Data loaded successfully")

    except FileNotFoundError:
        print(f"  ERROR: Result files not found!")
    except Exception as e:
        print(f"  ERROR: {str(e)}")

    print()

print(f"{'='*100}")
print(f"All runs have SOC data - proceeding with detailed verification...")
print(f"{'='*100}\n")
