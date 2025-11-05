"""
Additional cells for results_representation.ipynb to analyze border regions only

Copy these cells into your results_representation.ipynb notebook
"""

# ============================================================================
# CELL 1: Load Border Region Codes
# ============================================================================

from border_region_electrification_analysis import (
    load_border_region_codes,
    calculate_electrification_by_country_border_only,
    compare_border_vs_all_electrification,
    analyze_border_region_electrification
)

# Load the border region codes
border_nuts2_codes = load_border_region_codes("border_nuts2_codes.txt")
print(f"Loaded {len(border_nuts2_codes)} border region codes:")
print(sorted(border_nuts2_codes))

# ============================================================================
# CELL 2: Calculate Border Region Electrification for All Scenarios
# ============================================================================

# Calculate electrification for border regions only, for all runs
electrification_per_country_border = []

for run in loaded_runs:
    input_data = loaded_runs[run]["input_data"]
    output_data = loaded_runs[run]["output_data"]

    df_electrification_border, _, skip_counters = calculate_electrification_by_country_border_only(
        input_data,
        output_data,
        border_nuts2_codes,
        years_to_plot=range(2020, 2051, 2)
    )

    electrification_per_country_border.append(df_electrification_border)

    print(f"\n{run}:")
    print(f"  Entries processed for border regions: {len(df_electrification_border)}")
    print(f"  Entries filtered out (not border): {skip_counters['not_border_region']}")
    print(df_electrification_border.head())

# ============================================================================
# CELL 3: Compare Border vs All Regions (for one scenario)
# ============================================================================

# Compare border vs all regions for the first scenario
print("\nComparing Border vs All Regions for first scenario:")
run_name = list(loaded_runs.keys())[0]
input_data = loaded_runs[run_name]["input_data"]
output_data = loaded_runs[run_name]["output_data"]

df_comparison = compare_border_vs_all_electrification(
    input_data,
    output_data,
    border_nuts2_codes,
    years_to_plot=[2030, 2040]
)

print("\nComparison data:")
print(df_comparison.pivot_table(
    index=['country', 'year'],
    columns='region_type',
    values='electrification_pct'
))

# ============================================================================
# CELL 4: Visualize Border Region Electrification - 2030 (2x2 Grid)
# ============================================================================

import matplotlib.pyplot as plt
import numpy as np

fig, axes = plt.subplots(2, 2, figsize=(14, 10), sharey=True)
axes = axes.ravel()

for i, (case_name, df) in enumerate(zip(case_study_names, electrification_per_country_border)):
    ax = axes[i]

    # Filter for year 2030
    df_2030 = df[df['year'] == 2030]

    if df_2030.empty:
        ax.text(0.5, 0.5, "No data for 2030", ha='center', va='center')
        ax.set_title(f'{case_name}\n(Border Regions)')
        ax.set_xticks([])
        continue

    # Aggregate and sort
    vals = df_2030.groupby('country')['electricity'].mean().sort_values(ascending=False)

    if len(vals) == 0:
        ax.text(0.5, 0.5, "No border data", ha='center', va='center')
        ax.set_title(f'{case_name}\n(Border Regions)')
        continue

    # Plot
    vals.plot(kind='bar', ax=ax, color=f'C{i}')
    ax.set_title(f'{case_name}\n(Border Regions - 2030)', fontsize=10)
    ax.set_xlabel('')
    ax.set_ylabel('Electricity (kWh)' if i % 2 == 0 else '')
    ax.set_xticklabels(vals.index, rotation=45, ha='right')
    ax.grid(axis='y', alpha=0.3)

    # Add value labels on bars
    for j, (idx, val) in enumerate(vals.items()):
        ax.text(j, val, f'{val:.0f}', ha='center', va='bottom', fontsize=8)

plt.tight_layout()
plt.savefig('border_regions_electricity_2030.png', dpi=300, bbox_inches='tight')
plt.show()

print("Saved: border_regions_electricity_2030.png")

# ============================================================================
# CELL 5: Visualize Border Region Electrification - 2040 (2x2 Grid)
# ============================================================================

fig, axes = plt.subplots(2, 2, figsize=(14, 10), sharey=True)
axes = axes.ravel()

for i, (case_name, df) in enumerate(zip(case_study_names, electrification_per_country_border)):
    ax = axes[i]

    # Filter for year 2040
    df_2040 = df[df['year'] == 2040]

    if df_2040.empty:
        ax.text(0.5, 0.5, "No data for 2040", ha='center', va='center')
        ax.set_title(f'{case_name}\n(Border Regions)')
        ax.set_xticks([])
        continue

    # Aggregate and sort
    vals = df_2040.groupby('country')['electricity'].mean().sort_values(ascending=False)

    if len(vals) == 0:
        ax.text(0.5, 0.5, "No border data", ha='center', va='center')
        ax.set_title(f'{case_name}\n(Border Regions)')
        continue

    # Plot
    vals.plot(kind='bar', ax=ax, color=f'C{i}')
    ax.set_title(f'{case_name}\n(Border Regions - 2040)', fontsize=10)
    ax.set_xlabel('')
    ax.set_ylabel('Electricity (kWh)' if i % 2 == 0 else '')
    ax.set_xticklabels(vals.index, rotation=45, ha='right')
    ax.grid(axis='y', alpha=0.3)

    # Add value labels on bars
    for j, (idx, val) in enumerate(vals.items()):
        ax.text(j, val, f'{val:.0f}', ha='center', va='bottom', fontsize=8)

plt.tight_layout()
plt.savefig('border_regions_electricity_2040.png', dpi=300, bbox_inches='tight')
plt.show()

print("Saved: border_regions_electricity_2040.png")

# ============================================================================
# CELL 6: Border vs All Regions Comparison (2x2 Grid for 2030)
# ============================================================================

from electrification_analysis import calculate_electrification_by_country

fig, axes = plt.subplots(2, 2, figsize=(16, 10))
axes = axes.ravel()

for i, (case_name, run) in enumerate(zip(case_study_names, loaded_runs.keys())):
    ax = axes[i]

    input_data = loaded_runs[run]["input_data"]
    output_data = loaded_runs[run]["output_data"]

    # Calculate both
    df_all, _, _ = calculate_electrification_by_country(
        input_data, output_data, years_to_plot=[2030]
    )
    df_border, _, _ = calculate_electrification_by_country_border_only(
        input_data, output_data, border_nuts2_codes, years_to_plot=[2030]
    )

    if df_all.empty or df_border.empty:
        ax.text(0.5, 0.5, "No data", ha='center', va='center')
        ax.set_title(case_name)
        continue

    # Merge data
    df_all_agg = df_all.groupby('country')['electricity'].mean()
    df_border_agg = df_border.groupby('country')['electricity'].mean()

    # Combine for plotting
    countries = sorted(set(df_all_agg.index) | set(df_border_agg.index))

    x = np.arange(len(countries))
    width = 0.35

    all_vals = [df_all_agg.get(c, 0) for c in countries]
    border_vals = [df_border_agg.get(c, 0) for c in countries]

    ax.bar(x - width/2, all_vals, width, label='All regions', alpha=0.8, color='steelblue')
    ax.bar(x + width/2, border_vals, width, label='Border regions', alpha=0.8, color='coral')

    ax.set_title(f'{case_name}\n(2030 Comparison)', fontsize=10)
    ax.set_xlabel('Country')
    ax.set_ylabel('Electricity (kWh)')
    ax.set_xticks(x)
    ax.set_xticklabels(countries, rotation=45, ha='right')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('border_vs_all_comparison_2030.png', dpi=300, bbox_inches='tight')
plt.show()

print("Saved: border_vs_all_comparison_2030.png")

# ============================================================================
# CELL 7: Create Summary Table - Border Region Electrification
# ============================================================================

# Create summary table comparing scenarios for border regions
summary_data = []

for case_name, df in zip(case_study_names, electrification_per_country_border):
    for year in [2030, 2040]:
        year_data = df[df['year'] == year]
        if len(year_data) > 0:
            summary_data.append({
                'scenario': case_name,
                'year': year,
                'avg_electrification_pct': year_data['electrification_pct'].mean(),
                'total_electricity_kWh': year_data['electricity'].sum(),
                'total_fuel_kWh': year_data['total_fuel'].sum(),
                'num_countries': year_data['country'].nunique()
            })

df_summary = pd.DataFrame(summary_data)

print("\n" + "=" * 80)
print("BORDER REGION ELECTRIFICATION SUMMARY")
print("=" * 80)
print(df_summary.to_string(index=False))
print("=" * 80)

# Export to CSV
df_summary.to_csv('border_regions_electrification_summary.csv', index=False)
print("\nExported to: border_regions_electrification_summary.csv")

# ============================================================================
# CELL 8: Enhanced Delta Analysis - Border Regions Detailed Comparison
# ============================================================================

# Use first scenario (var_var) as reference
reference_scenario = case_study_names[0]
reference_df = electrification_per_country_border[0]

print(f"\nBORDER REGION DELTA ANALYSIS (compared to reference: {reference_scenario})")
print("=" * 80)

# Create comprehensive delta tables
delta_tables = {}

for year in [2030, 2040]:
    print(f"\n{'='*80}")
    print(f"YEAR {year} - DETAILED COUNTRY-BY-COUNTRY COMPARISON")
    print(f"{'='*80}\n")

    # Get reference values
    ref_data = reference_df[reference_df['year'] == year].set_index('country')

    # Create comparison table for this year
    comparison_data = []

    for case_name, df in zip(case_study_names, electrification_per_country_border):
        case_data = df[df['year'] == year].set_index('country')

        # Calculate differences for each country
        common_countries = sorted(set(ref_data.index) & set(case_data.index))

        for country in common_countries:
            ref_elec = ref_data.loc[country, 'electricity']
            ref_pct = ref_data.loc[country, 'electrification_pct']
            ref_total = ref_data.loc[country, 'total_fuel']

            case_elec = case_data.loc[country, 'electricity']
            case_pct = case_data.loc[country, 'electrification_pct']
            case_total = case_data.loc[country, 'total_fuel']

            delta_elec = case_elec - ref_elec
            delta_pct = case_pct - ref_pct
            delta_total = case_total - ref_total
            pct_change_elec = (delta_elec / ref_elec * 100) if ref_elec > 0 else 0

            comparison_data.append({
                'scenario': case_name,
                'country': country,
                'ref_electricity_kWh': ref_elec,
                'case_electricity_kWh': case_elec,
                'delta_electricity_kWh': delta_elec,
                'pct_change_electricity': pct_change_elec,
                'ref_electrification_pct': ref_pct,
                'case_electrification_pct': case_pct,
                'delta_electrification_pct': delta_pct,
                'ref_total_fuel_kWh': ref_total,
                'case_total_fuel_kWh': case_total,
                'delta_total_fuel_kWh': delta_total
            })

    # Create DataFrame
    df_delta = pd.DataFrame(comparison_data)
    delta_tables[year] = df_delta

    # Display summary by scenario
    for case_name in case_study_names:
        if case_name == reference_scenario:
            continue

        print(f"\n{case_name} vs {reference_scenario}:")
        print("-" * 80)

        case_delta = df_delta[df_delta['scenario'] == case_name]

        # Print country-by-country comparison
        print("\nBy Country:")
        for _, row in case_delta.iterrows():
            print(f"  {row['country']}:")
            print(f"    Electricity:      {row['ref_electricity_kWh']:>10.2f} → {row['case_electricity_kWh']:>10.2f} "
                  f"(Δ {row['delta_electricity_kWh']:+10.2f} kWh, {row['pct_change_electricity']:+6.2f}%)")
            print(f"    Electrification:  {row['ref_electrification_pct']:>10.2f}% → {row['case_electrification_pct']:>10.2f}% "
                  f"(Δ {row['delta_electrification_pct']:+10.2f} pp)")
            print(f"    Total Fuel:       {row['ref_total_fuel_kWh']:>10.2f} → {row['case_total_fuel_kWh']:>10.2f} "
                  f"(Δ {row['delta_total_fuel_kWh']:+10.2f} kWh)")

        # Overall statistics
        print(f"\n  Overall Statistics:")
        print(f"    Avg Δ electrification:    {case_delta['delta_electrification_pct'].mean():+.2f} percentage points")
        print(f"    Total Δ electricity:      {case_delta['delta_electricity_kWh'].sum():+.2f} kWh")
        print(f"    Avg % change electricity: {case_delta['pct_change_electricity'].mean():+.2f}%")
        print(f"    Total Δ fuel:             {case_delta['delta_total_fuel_kWh'].sum():+.2f} kWh")
        print(f"    Countries compared:       {len(case_delta)}")

        # Identify biggest changes
        max_increase = case_delta.loc[case_delta['delta_electricity_kWh'].idxmax()]
        max_decrease = case_delta.loc[case_delta['delta_electricity_kWh'].idxmin()]

        print(f"\n  Largest Changes:")
        print(f"    Max increase: {max_increase['country']} ({max_increase['delta_electricity_kWh']:+.2f} kWh)")
        print(f"    Max decrease: {max_decrease['country']} ({max_decrease['delta_electricity_kWh']:+.2f} kWh)")

# Export delta tables
for year, df_delta in delta_tables.items():
    filename = f'border_delta_analysis_{year}.csv'
    df_delta.to_csv(filename, index=False)
    print(f"\nExported: {filename}")

print("\n" + "=" * 80)

# ============================================================================
# CELL 8B: Visualize Delta Analysis - Heatmaps and Bar Charts
# ============================================================================

print("\nCreating delta visualization plots...")

# Create figure with multiple subplots
fig = plt.figure(figsize=(18, 12))
gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)

for year_idx, year in enumerate([2030, 2040]):
    df_delta = delta_tables[year]

    # Exclude reference scenario
    df_delta_plot = df_delta[df_delta['scenario'] != reference_scenario]

    # 1. Heatmap of electricity deltas
    ax1 = fig.add_subplot(gs[year_idx, 0])

    pivot_elec = df_delta_plot.pivot(index='country', columns='scenario', values='delta_electricity_kWh')
    im = ax1.imshow(pivot_elec.values, cmap='RdYlGn', aspect='auto')

    ax1.set_xticks(np.arange(len(pivot_elec.columns)))
    ax1.set_yticks(np.arange(len(pivot_elec.index)))
    ax1.set_xticklabels(pivot_elec.columns, rotation=45, ha='right')
    ax1.set_yticklabels(pivot_elec.index)

    # Add values to heatmap
    for i in range(len(pivot_elec.index)):
        for j in range(len(pivot_elec.columns)):
            text = ax1.text(j, i, f'{pivot_elec.values[i, j]:.0f}',
                          ha="center", va="center", color="black", fontsize=8)

    ax1.set_title(f'Δ Electricity Consumption ({year}) [kWh]', fontweight='bold')
    plt.colorbar(im, ax=ax1, label='Δ kWh')

    # 2. Bar chart of total deltas by scenario
    ax2 = fig.add_subplot(gs[year_idx, 1])

    scenario_totals = df_delta_plot.groupby('scenario')['delta_electricity_kWh'].sum()
    colors = ['coral' if x < 0 else 'lightgreen' for x in scenario_totals.values]

    ax2.bar(range(len(scenario_totals)), scenario_totals.values, color=colors, alpha=0.7)
    ax2.set_xticks(range(len(scenario_totals)))
    ax2.set_xticklabels(scenario_totals.index, rotation=45, ha='right')
    ax2.set_ylabel('Total Δ Electricity (kWh)')
    ax2.set_title(f'Total Border Electricity Delta by Scenario ({year})', fontweight='bold')
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    ax2.grid(axis='y', alpha=0.3)

    # Add value labels
    for i, v in enumerate(scenario_totals.values):
        ax2.text(i, v, f'{v:+.0f}', ha='center', va='bottom' if v > 0 else 'top', fontsize=9)

# 3. Electrification percentage delta comparison (both years)
ax3 = fig.add_subplot(gs[2, :])

all_years_data = []
for year in [2030, 2040]:
    df_delta = delta_tables[year]
    df_delta_plot = df_delta[df_delta['scenario'] != reference_scenario]

    for scenario in df_delta_plot['scenario'].unique():
        scenario_data = df_delta_plot[df_delta_plot['scenario'] == scenario]
        all_years_data.append({
            'year': year,
            'scenario': scenario,
            'avg_delta_pct': scenario_data['delta_electrification_pct'].mean()
        })

df_years_comparison = pd.DataFrame(all_years_data)
pivot_years = df_years_comparison.pivot(index='scenario', columns='year', values='avg_delta_pct')

x = np.arange(len(pivot_years.index))
width = 0.35

ax3.bar(x - width/2, pivot_years[2030], width, label='2030', alpha=0.8, color='steelblue')
ax3.bar(x + width/2, pivot_years[2040], width, label='2040', alpha=0.8, color='coral')

ax3.set_xlabel('Scenario')
ax3.set_ylabel('Avg Δ Electrification (%)')
ax3.set_title('Average Electrification Delta vs Reference (Border Regions)', fontweight='bold')
ax3.set_xticks(x)
ax3.set_xticklabels(pivot_years.index, rotation=45, ha='right')
ax3.legend()
ax3.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
ax3.grid(axis='y', alpha=0.3)

# Add value labels
for i, scenario in enumerate(pivot_years.index):
    v1 = pivot_years.loc[scenario, 2030]
    v2 = pivot_years.loc[scenario, 2040]
    ax3.text(i - width/2, v1, f'{v1:+.1f}', ha='center', va='bottom' if v1 > 0 else 'top', fontsize=8)
    ax3.text(i + width/2, v2, f'{v2:+.1f}', ha='center', va='bottom' if v2 > 0 else 'top', fontsize=8)

plt.savefig('border_delta_analysis_visualization.png', dpi=300, bbox_inches='tight')
plt.show()

print("Saved: border_delta_analysis_visualization.png")

# ============================================================================
# CELL 8C: Time Series Evolution of Border Region Deltas
# ============================================================================

print("\nAnalyzing temporal evolution of deltas...")

# Calculate deltas for multiple years
years_to_analyze = [2020, 2024, 2028, 2030, 2034, 2038, 2040, 2044, 2048, 2050]

time_series_deltas = []

for year in years_to_analyze:
    ref_year = reference_df[reference_df['year'] == year]

    if len(ref_year) == 0:
        continue

    ref_year_indexed = ref_year.set_index('country')

    for case_idx, (case_name, df) in enumerate(zip(case_study_names, electrification_per_country_border)):
        if case_name == reference_scenario:
            continue

        case_year = df[df['year'] == year]

        if len(case_year) == 0:
            continue

        case_year_indexed = case_year.set_index('country')

        common_countries = set(ref_year_indexed.index) & set(case_year_indexed.index)

        for country in common_countries:
            ref_elec = ref_year_indexed.loc[country, 'electricity']
            case_elec = case_year_indexed.loc[country, 'electricity']
            ref_pct = ref_year_indexed.loc[country, 'electrification_pct']
            case_pct = case_year_indexed.loc[country, 'electrification_pct']

            time_series_deltas.append({
                'year': year,
                'scenario': case_name,
                'country': country,
                'delta_electricity_kWh': case_elec - ref_elec,
                'delta_electrification_pct': case_pct - ref_pct
            })

df_time_series = pd.DataFrame(time_series_deltas)

# Plot time series
fig, axes = plt.subplots(2, 1, figsize=(16, 10))

# Plot 1: Delta electricity over time by scenario
ax1 = axes[0]

for scenario in df_time_series['scenario'].unique():
    scenario_data = df_time_series[df_time_series['scenario'] == scenario]
    yearly_totals = scenario_data.groupby('year')['delta_electricity_kWh'].sum()

    ax1.plot(yearly_totals.index, yearly_totals.values, marker='o', linewidth=2, label=scenario)

ax1.set_xlabel('Year')
ax1.set_ylabel('Total Δ Electricity (kWh)')
ax1.set_title('Border Region Electricity Delta Evolution (vs Reference Scenario)', fontweight='bold')
ax1.legend()
ax1.grid(True, alpha=0.3)
ax1.axhline(y=0, color='black', linestyle='--', linewidth=1)

# Plot 2: Average electrification delta over time
ax2 = axes[1]

for scenario in df_time_series['scenario'].unique():
    scenario_data = df_time_series[df_time_series['scenario'] == scenario]
    yearly_avg = scenario_data.groupby('year')['delta_electrification_pct'].mean()

    ax2.plot(yearly_avg.index, yearly_avg.values, marker='s', linewidth=2, label=scenario)

ax2.set_xlabel('Year')
ax2.set_ylabel('Avg Δ Electrification (%)')
ax2.set_title('Border Region Electrification Rate Delta Evolution (vs Reference Scenario)', fontweight='bold')
ax2.legend()
ax2.grid(True, alpha=0.3)
ax2.axhline(y=0, color='black', linestyle='--', linewidth=1)

plt.tight_layout()
plt.savefig('border_delta_time_series.png', dpi=300, bbox_inches='tight')
plt.show()

print("Saved: border_delta_time_series.png")

# Export time series data
df_time_series.to_csv('border_delta_time_series.csv', index=False)
print("Exported: border_delta_time_series.csv")

# ============================================================================
# CELL 8D: Border Corridor-Specific Analysis
# ============================================================================

print("\nAnalyzing specific border corridors...")

# Load border region connections
border_regions_df = pd.read_csv('border_regions_analysis.csv')

# Define major corridors
corridors = {
    'Austria-Germany': {'AT': ['AT31', 'AT32', 'AT33', 'AT34'], 'DE': ['DE14', 'DE21', 'DE22', 'DE27']},
    'Austria-Italy': {'AT': ['AT32', 'AT33'], 'IT': ['ITH1', 'ITH3']},
    'Germany-Denmark': {'DE': ['DEF0'], 'DK': ['DK03']},
    'Norway-Sweden': {'NO': ['NO08'], 'SE': ['SE23']}
}

# Analyze each corridor
corridor_analysis = []

for corridor_name, countries_regions in corridors.items():
    print(f"\n{corridor_name} Corridor:")
    print("-" * 60)

    # Get all regions in this corridor
    corridor_nuts2 = []
    for country, regions in countries_regions.items():
        corridor_nuts2.extend(regions)

    # Calculate metrics for reference scenario
    for year in [2030, 2040]:
        ref_data_year = reference_df[reference_df['year'] == year]

        # Filter to corridor countries
        corridor_countries = list(countries_regions.keys())

        ref_corridor = ref_data_year[ref_data_year['country'].isin(corridor_countries)]
        ref_total_elec = ref_corridor['electricity'].sum()
        ref_avg_pct = ref_corridor['electrification_pct'].mean()

        # Compare with other scenarios
        for case_name, df in zip(case_study_names, electrification_per_country_border):
            if case_name == reference_scenario:
                continue

            case_data_year = df[df['year'] == year]
            case_corridor = case_data_year[case_data_year['country'].isin(corridor_countries)]

            case_total_elec = case_corridor['electricity'].sum()
            case_avg_pct = case_corridor['electrification_pct'].mean()

            delta_elec = case_total_elec - ref_total_elec
            delta_pct = case_avg_pct - ref_avg_pct

            corridor_analysis.append({
                'corridor': corridor_name,
                'year': year,
                'scenario': case_name,
                'ref_electricity_kWh': ref_total_elec,
                'case_electricity_kWh': case_total_elec,
                'delta_electricity_kWh': delta_elec,
                'ref_avg_electrification_pct': ref_avg_pct,
                'case_avg_electrification_pct': case_avg_pct,
                'delta_electrification_pct': delta_pct
            })

            print(f"  {year} - {case_name}:")
            print(f"    Electricity:      {ref_total_elec:>10.2f} → {case_total_elec:>10.2f} (Δ {delta_elec:+10.2f} kWh)")
            print(f"    Avg Electrif.:    {ref_avg_pct:>10.2f}% → {case_avg_pct:>10.2f}% (Δ {delta_pct:+10.2f} pp)")

# Create DataFrame and visualize
df_corridor = pd.DataFrame(corridor_analysis)

# Visualize corridor deltas
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

for year_idx, year in enumerate([2030, 2040]):
    year_data = df_corridor[df_corridor['year'] == year]

    # Electricity delta by corridor
    ax1 = axes[year_idx, 0]
    pivot_elec = year_data.pivot(index='corridor', columns='scenario', values='delta_electricity_kWh')

    x = np.arange(len(pivot_elec.index))
    width = 0.25

    for i, scenario in enumerate(pivot_elec.columns):
        offset = (i - len(pivot_elec.columns)/2 + 0.5) * width
        bars = ax1.bar(x + offset, pivot_elec[scenario], width, label=scenario, alpha=0.8)

        # Add value labels
        for j, v in enumerate(pivot_elec[scenario]):
            if not pd.isna(v):
                ax1.text(j + offset, v, f'{v:+.0f}', ha='center',
                        va='bottom' if v > 0 else 'top', fontsize=7, rotation=0)

    ax1.set_xlabel('Corridor')
    ax1.set_ylabel('Δ Electricity (kWh)')
    ax1.set_title(f'Border Corridor Electricity Deltas ({year})', fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(pivot_elec.index, rotation=45, ha='right')
    ax1.legend()
    ax1.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    ax1.grid(axis='y', alpha=0.3)

    # Electrification delta by corridor
    ax2 = axes[year_idx, 1]
    pivot_pct = year_data.pivot(index='corridor', columns='scenario', values='delta_electrification_pct')

    for i, scenario in enumerate(pivot_pct.columns):
        offset = (i - len(pivot_pct.columns)/2 + 0.5) * width
        bars = ax2.bar(x + offset, pivot_pct[scenario], width, label=scenario, alpha=0.8)

        # Add value labels
        for j, v in enumerate(pivot_pct[scenario]):
            if not pd.isna(v):
                ax2.text(j + offset, v, f'{v:+.1f}', ha='center',
                        va='bottom' if v > 0 else 'top', fontsize=7, rotation=0)

    ax2.set_xlabel('Corridor')
    ax2.set_ylabel('Δ Electrification (%)')
    ax2.set_title(f'Border Corridor Electrification Rate Deltas ({year})', fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(pivot_pct.index, rotation=45, ha='right')
    ax2.legend()
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    ax2.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('border_corridor_delta_analysis.png', dpi=300, bbox_inches='tight')
plt.show()

print("\nSaved: border_corridor_delta_analysis.png")

# Export corridor analysis
df_corridor.to_csv('border_corridor_delta_analysis.csv', index=False)
print("Exported: border_corridor_delta_analysis.csv")

# ============================================================================
# CELL 8E: Summary Delta Table for Publication
# ============================================================================

print("\nCreating publication-ready summary table...")

# Create comprehensive summary table
summary_delta_data = []

for year in [2030, 2040]:
    df_delta = delta_tables[year]

    for scenario in case_study_names:
        scenario_data = df_delta[df_delta['scenario'] == scenario]

        if scenario == reference_scenario:
            # Add reference scenario stats
            ref_data = reference_df[reference_df['year'] == year]
            summary_delta_data.append({
                'Year': year,
                'Scenario': scenario,
                'Type': 'Reference',
                'Total Electricity (kWh)': ref_data['electricity'].sum(),
                'Avg Electrification (%)': ref_data['electrification_pct'].mean(),
                'Δ Electricity (kWh)': 0.0,
                'Δ Electricity (%)': 0.0,
                'Δ Electrification (pp)': 0.0,
                'Countries': len(ref_data)
            })
        else:
            # Add delta stats
            if len(scenario_data) > 0:
                total_ref_elec = scenario_data['ref_electricity_kWh'].sum()
                total_case_elec = scenario_data['case_electricity_kWh'].sum()
                pct_change = ((total_case_elec - total_ref_elec) / total_ref_elec * 100) if total_ref_elec > 0 else 0

                summary_delta_data.append({
                    'Year': year,
                    'Scenario': scenario,
                    'Type': 'Comparison',
                    'Total Electricity (kWh)': total_case_elec,
                    'Avg Electrification (%)': scenario_data['case_electrification_pct'].mean(),
                    'Δ Electricity (kWh)': scenario_data['delta_electricity_kWh'].sum(),
                    'Δ Electricity (%)': pct_change,
                    'Δ Electrification (pp)': scenario_data['delta_electrification_pct'].mean(),
                    'Countries': len(scenario_data)
                })

df_summary_delta = pd.DataFrame(summary_delta_data)

print("\n" + "=" * 100)
print("BORDER REGION DELTA SUMMARY TABLE (for Publication)")
print("=" * 100)
print(df_summary_delta.to_string(index=False))
print("=" * 100)

# Export with formatting
df_summary_delta.to_csv('border_delta_summary_table.csv', index=False)
df_summary_delta.to_latex('border_delta_summary_table.tex', index=False, float_format="%.2f")

print("\nExported:")
print("  - border_delta_summary_table.csv")
print("  - border_delta_summary_table.tex (for LaTeX)")

# ============================================================================
# CELL 9: Export Border Region Data for Further Analysis
# ============================================================================

# Export all border region electrification data
for case_name, df in zip(case_study_names, electrification_per_country_border):
    filename = f'border_electrification_{case_name}.csv'
    df.to_csv(filename, index=False)
    print(f"Exported: {filename}")

print("\nAll border region data exported successfully!")
