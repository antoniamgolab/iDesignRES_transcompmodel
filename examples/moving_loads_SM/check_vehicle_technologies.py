"""
Check what vehicle technologies are present in November 16 reverse case
"""

import yaml
from collections import defaultdict

# Configuration
result_timestamp = "case_20251110_160646_reverse_cs_2025-11-16_16-48-22"
case_name = "case_20251110_160646_reverse"
base_path = "C:/Users/simuser/Documents/AntoniaGolab/Scand_Med_analysis/SM_baby_2/iDesignRES_transcompmodel/examples/moving_loads_SM"
results_dir = f"{base_path}/results/{case_name}"

print(f"\n{'='*80}")
print(f"ANALYZING VEHICLE TECHNOLOGIES IN {result_timestamp}")
print(f"{'='*80}\n")

# Load f_dict
print("Loading f_dict...")
with open(f"{results_dir}/{result_timestamp}_f_dict.yaml", 'r') as f:
    f_dict = yaml.safe_load(f)

print(f"Total entries: {len(f_dict)}\n")

# Analyze by techvehicle ID
tech_stats = defaultdict(lambda: {'count': 0, 'total_flow': 0, 'years': set(), 'positive_count': 0})

for key, value in f_dict.items():
    if isinstance(key, tuple) and len(key) == 4:
        year, (product, odpair, path), (mode, techvehicle), generation = key

        tech_stats[techvehicle]['count'] += 1
        tech_stats[techvehicle]['years'].add(year)
        tech_stats[techvehicle]['total_flow'] += abs(value)
        if value > 0.1:  # Significant flow
            tech_stats[techvehicle]['positive_count'] += 1

print("VEHICLE TECHNOLOGY DISTRIBUTION:")
print("-" * 80)
for tech_id in sorted(tech_stats.keys()):
    stats = tech_stats[tech_id]
    print(f"\nTechVehicle ID {tech_id}:")
    print(f"  Total entries: {stats['count']:,}")
    print(f"  Entries with significant flow (>0.1): {stats['positive_count']:,}")
    print(f"  Total flow: {stats['total_flow']:,.2f} tonnes/year")
    print(f"  Years covered: {sorted(stats['years'])}")

# Check year distribution
print(f"\n{'='*80}")
print("YEAR DISTRIBUTION ACROSS ALL TECHNOLOGIES:")
print("-" * 80)

year_stats = defaultdict(lambda: {'count': 0, 'positive_count': 0, 'total_flow': 0, 'by_tech': defaultdict(float)})

for key, value in f_dict.items():
    if isinstance(key, tuple) and len(key) == 4:
        year, (product, odpair, path), (mode, techvehicle), generation = key

        year_stats[year]['count'] += 1
        year_stats[year]['total_flow'] += abs(value)
        year_stats[year]['by_tech'][techvehicle] += abs(value)
        if value > 0.1:
            year_stats[year]['positive_count'] += 1

for year in sorted(year_stats.keys()):
    stats = year_stats[year]
    print(f"\nYear {year}:")
    print(f"  Total entries: {stats['count']:,}")
    print(f"  Entries with significant flow: {stats['positive_count']:,}")
    print(f"  Total flow: {stats['total_flow']:,.2f} tonnes/year")
    print(f"  By technology:")
    for tech_id in sorted(stats['by_tech'].keys()):
        print(f"    Tech {tech_id}: {stats['by_tech'][tech_id]:,.2f} tonnes/year")

# Specifically check year 2056
print(f"\n{'='*80}")
print("DETAILED CHECK FOR YEAR 2056:")
print("-" * 80)

year_2056_entries = [(key, value) for key, value in f_dict.items()
                     if isinstance(key, tuple) and len(key) == 4 and key[0] == 2056]

print(f"\nTotal entries for year 2056: {len(year_2056_entries)}")

if year_2056_entries:
    print("\nSample entries (first 20):")
    for i, (key, value) in enumerate(year_2056_entries[:20]):
        year, (product, odpair, path), (mode, techvehicle), generation = key
        print(f"  {i+1}. Path {path}, Tech {techvehicle}, Gen {generation}: {value:,.6f} tonnes/year")

    # Count by technology for 2056
    tech_2056 = defaultdict(lambda: {'count': 0, 'total_flow': 0})
    for key, value in year_2056_entries:
        year, (product, odpair, path), (mode, techvehicle), generation = key
        tech_2056[techvehicle]['count'] += 1
        tech_2056[techvehicle]['total_flow'] += abs(value)

    print("\nBy technology in 2056:")
    for tech_id in sorted(tech_2056.keys()):
        stats = tech_2056[tech_id]
        print(f"  Tech {tech_id}: {stats['count']:,} entries, {stats['total_flow']:,.6f} tonnes/year total")
else:
    print("\nNo entries found for year 2056!")

print(f"\n{'='*80}\n")
