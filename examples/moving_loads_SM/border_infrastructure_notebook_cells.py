"""
Border Infrastructure Analysis - Notebook Cells

Copy these cells directly into your results_representation.ipynb notebook.
Place them after you've loaded your data (loaded_runs and case_study_names).
"""

# ============================================================================
# CELL 1: Import Functions and Load Border Codes
# ============================================================================

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from infrastructure_analysis import get_infrastructure_data

def load_border_region_codes(border_codes_file="border_nuts2_codes.txt"):
    """Load border region codes from file."""
    with open(border_codes_file, 'r') as f:
        codes = {line.strip() for line in f if line.strip()}
    return codes

def calculate_border_infrastructure_capacity(
    input_data, output_data, border_nuts2_codes, year, fuel_name='electricity'
):
    """Calculate infrastructure capacity for border regions only."""
    infra_data = get_infrastructure_data(input_data, output_data)
    fuel_list = infra_data['fuel_list']
    fueling_infr_types_list = infra_data['fueling_infr_types_list']
    initial_fueling_infr = infra_data['initial_fueling_infr']
    investment_years = infra_data['investment_years']

    geographic_element_list = {d["id"]: d for d in input_data["GeographicElement"]}

    # Extract energy consumption
    energy_by_location = {}
    if 's' in output_data:
        for key, value in output_data['s'].items():
            s_year = key[0]
            if s_year != year:
                continue
            if len(key) >= 4:
                f_l = key[3]
                fuel_id, infr_id = f_l[0], f_l[1]
                geo_id = key[1] if isinstance(key[1], int) else (key[2] if len(key) > 2 and isinstance(key[2], int) else None)
                if geo_id is not None:
                    energy_key = (s_year, geo_id, fuel_id, infr_id)
                    energy_by_location[energy_key] = energy_by_location.get(energy_key, 0.0) + value

    records = []
    for geo_id, geo_data in geographic_element_list.items():
        geo_nuts2 = geo_data.get('nuts2_region')
        if geo_nuts2 not in border_nuts2_codes:
            continue

        country = geo_data.get('country', 'Unknown')
        for infr_id, infr_data in fueling_infr_types_list.items():
            for fuel_id, fuel_data in fuel_list.items():
                current_fuel_name = fuel_data["name"]
                if fuel_name and current_fuel_name != fuel_name:
                    continue
                if infr_data["fuel"] != current_fuel_name:
                    continue

                initial_key = (current_fuel_name, infr_id, geo_id)
                initial_capacity = initial_fueling_infr[initial_key]["installed_kW"] if initial_key in initial_fueling_infr else 0.0

                added_capacity = 0.0
                f_l = (fuel_id, infr_id)
                for inv_year in investment_years:
                    if inv_year <= year:
                        key_q = (inv_year, f_l, geo_id)
                        if key_q in output_data["q_fuel_infr_plus"]:
                            added_capacity += output_data["q_fuel_infr_plus"][key_q]

                total_capacity = initial_capacity + added_capacity
                energy_key = (year, geo_id, fuel_id, infr_id)
                energy_consumed = energy_by_location.get(energy_key, 0.0)

                utilization_rate = None
                if total_capacity > 0:
                    max_possible_energy = total_capacity * 8760
                    utilization_rate = energy_consumed / max_possible_energy if max_possible_energy > 0 else 0.0

                if total_capacity > 0:
                    records.append({
                        'geo_id': geo_id,
                        'geo_name': geo_data.get('name', 'Unknown'),
                        'nuts2_region': geo_nuts2,
                        'country': country,
                        'fuel': current_fuel_name,
                        'infrastructure_type': infr_data['fueling_type'],
                        'initial_capacity_kW': initial_capacity,
                        'added_capacity_kW': added_capacity,
                        'total_capacity_kW': total_capacity,
                        'energy_consumed_kWh': energy_consumed,
                        'utilization_rate': utilization_rate,
                        'utilization_pct': utilization_rate * 100 if utilization_rate else None
                    })

    return pd.DataFrame(records)

print("Functions loaded successfully!")

# ============================================================================
# CELL 2: Load Data and Calculate Infrastructure for All Scenarios
# ============================================================================

print("="*80)
print("BORDER REGION CHARGING INFRASTRUCTURE ANALYSIS")
print("="*80)

# Load border region codes
border_nuts2_codes = load_border_region_codes("border_nuts2_codes.txt")
print(f"\nAnalyzing {len(border_nuts2_codes)} border regions:")
print(sorted(border_nuts2_codes))

# Analyze all scenarios
print("\nCalculating border infrastructure for all scenarios...")
years_to_analyze = [2030, 2040, 2050]

border_infra_data = {}
for scenario_name, run_name in zip(case_study_names, loaded_runs.keys()):
    input_data = loaded_runs[run_name]["input_data"]
    output_data = loaded_runs[run_name]["output_data"]

    scenario_records = []
    for year in years_to_analyze:
        print(f"  Processing {scenario_name} - {year}...")

        df_infra = calculate_border_infrastructure_capacity(
            input_data, output_data, border_nuts2_codes, year, fuel_name='electricity'
        )

        if len(df_infra) > 0:
            # Aggregate by country
            agg_data = []
            for country in df_infra['country'].unique():
                country_data = df_infra[df_infra['country'] == country]
                for infr_type in country_data['infrastructure_type'].unique():
                    type_data = country_data[country_data['infrastructure_type'] == infr_type]
                    total_capacity = type_data['total_capacity_kW'].sum()
                    total_energy = type_data['energy_consumed_kWh'].sum()
                    max_possible = total_capacity * 8760
                    utilization = (total_energy / max_possible * 100) if max_possible > 0 else 0.0

                    agg_data.append({
                        'country': country,
                        'infrastructure_type': infr_type,
                        'total_capacity_kW': total_capacity,
                        'total_capacity_MW': total_capacity / 1000,
                        'total_energy_kWh': total_energy,
                        'utilization_pct': utilization
                    })

            df_agg = pd.DataFrame(agg_data)
            df_agg['year'] = year
            df_agg['scenario'] = scenario_name
            scenario_records.append(df_agg)

    if scenario_records:
        border_infra_data[scenario_name] = pd.concat(scenario_records, ignore_index=True)

print("\nData collection complete!")
for scenario, df in border_infra_data.items():
    print(f"  {scenario}: {len(df)} records")

# ============================================================================
# CELL 3: Calculate Deltas vs Reference Scenario
# ============================================================================

print("\n" + "="*80)
print("CALCULATING INFRASTRUCTURE DELTAS VS REFERENCE SCENARIO")
print("="*80)

reference_scenario = case_study_names[0]
print(f"\nReference scenario: {reference_scenario}")

delta_infra_records = []
for year in years_to_analyze:
    ref_data = border_infra_data[reference_scenario]
    ref_year = ref_data[ref_data['year'] == year]

    for scenario_name in case_study_names:
        if scenario_name == reference_scenario:
            continue

        case_data = border_infra_data[scenario_name]
        case_year = case_data[case_data['year'] == year]

        for _, ref_row in ref_year.iterrows():
            country = ref_row['country']
            infr_type = ref_row['infrastructure_type']

            case_match = case_year[
                (case_year['country'] == country) &
                (case_year['infrastructure_type'] == infr_type)
            ]

            if len(case_match) > 0:
                case_row = case_match.iloc[0]
                delta_infra_records.append({
                    'year': year,
                    'scenario': scenario_name,
                    'country': country,
                    'infrastructure_type': infr_type,
                    'ref_capacity_MW': ref_row['total_capacity_MW'],
                    'case_capacity_MW': case_row['total_capacity_MW'],
                    'delta_capacity_MW': case_row['total_capacity_MW'] - ref_row['total_capacity_MW'],
                    'pct_change_capacity': ((case_row['total_capacity_MW'] - ref_row['total_capacity_MW']) /
                                           ref_row['total_capacity_MW'] * 100) if ref_row['total_capacity_MW'] > 0 else 0,
                    'ref_utilization_pct': ref_row['utilization_pct'],
                    'case_utilization_pct': case_row['utilization_pct'],
                    'delta_utilization_pct': case_row['utilization_pct'] - ref_row['utilization_pct']
                })

df_delta_infra = pd.DataFrame(delta_infra_records)
print(f"\nDelta records created: {len(df_delta_infra)}")
df_delta_infra.to_csv('border_infrastructure_deltas.csv', index=False)
print("Exported: border_infrastructure_deltas.csv")

# ============================================================================
# CELL 4: PLOT 1 - Total Border Infrastructure Capacity by Scenario (2×2)
# ============================================================================

fig, axes = plt.subplots(2, 2, figsize=(16, 12))
axes = axes.ravel()

infr_types = ['fast_charging_station', 'slow_charging_station']
colors = {'fast_charging_station': 'steelblue', 'slow_charging_station': 'coral'}

for i, scenario_name in enumerate(case_study_names):
    ax = axes[i]
    scenario_data = border_infra_data[scenario_name]

    plot_data = []
    for year in years_to_analyze:
        year_data = scenario_data[scenario_data['year'] == year]
        for infr_type in infr_types:
            type_data = year_data[year_data['infrastructure_type'] == infr_type]
            total_capacity = type_data['total_capacity_MW'].sum()
            plot_data.append({'year': year, 'infrastructure_type': infr_type, 'total_capacity_MW': total_capacity})

    df_plot = pd.DataFrame(plot_data)

    if len(df_plot) > 0:
        x = np.arange(len(years_to_analyze))
        width = 0.35

        for j, infr_type in enumerate(infr_types):
            infr_data = df_plot[df_plot['infrastructure_type'] == infr_type]
            offset = (j - 0.5) * width
            values = [infr_data[infr_data['year'] == year]['total_capacity_MW'].sum() for year in years_to_analyze]
            bars = ax.bar(x + offset, values, width, label=infr_type.replace('_', ' ').title(),
                         color=colors.get(infr_type, 'gray'), alpha=0.8)

            for k, v in enumerate(values):
                if v > 0:
                    ax.text(k + offset, v, f'{v:.1f}', ha='center', va='bottom', fontsize=8)

        ax.set_xlabel('Year', fontweight='bold')
        ax.set_ylabel('Total Capacity (MW)', fontweight='bold')
        ax.set_title(f'{scenario_name}\nBorder Region Charging Infrastructure', fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(years_to_analyze)
        ax.legend(loc='upper left')
        ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('border_infrastructure_capacity_by_scenario.png', dpi=300, bbox_inches='tight')
plt.show()
print("Plot 1 saved: border_infrastructure_capacity_by_scenario.png")

# ============================================================================
# CELL 5: PLOT 2 - Border Infrastructure Capacity Deltas (Heatmap + Bars)
# ============================================================================

fig = plt.figure(figsize=(18, 10))
gs = fig.add_gridspec(2, 3, hspace=0.3, wspace=0.3)

df_delta_fast = df_delta_infra[df_delta_infra['infrastructure_type'] == 'fast_charging_station']

for year_idx, year in enumerate([2030, 2040, 2050]):
    year_data = df_delta_fast[df_delta_fast['year'] == year]
    if len(year_data) == 0:
        continue

    # Heatmap
    ax_heat = fig.add_subplot(gs[0, year_idx])
    pivot_capacity = year_data.pivot(index='country', columns='scenario', values='delta_capacity_MW')

    if not pivot_capacity.empty:
        im = ax_heat.imshow(pivot_capacity.values, cmap='RdYlGn', aspect='auto',
                           vmin=-pivot_capacity.abs().max().max(), vmax=pivot_capacity.abs().max().max())
        ax_heat.set_xticks(np.arange(len(pivot_capacity.columns)))
        ax_heat.set_yticks(np.arange(len(pivot_capacity.index)))
        ax_heat.set_xticklabels(pivot_capacity.columns, rotation=45, ha='right', fontsize=8)
        ax_heat.set_yticklabels(pivot_capacity.index, fontsize=9)

        for i in range(len(pivot_capacity.index)):
            for j in range(len(pivot_capacity.columns)):
                val = pivot_capacity.values[i, j]
                if not pd.isna(val):
                    text_color = 'white' if abs(val) > pivot_capacity.abs().max().max() * 0.5 else 'black'
                    ax_heat.text(j, i, f'{val:.1f}', ha="center", va="center", color=text_color, fontsize=7)

        ax_heat.set_title(f'{year} - Δ Fast Charging Capacity (MW)', fontweight='bold', fontsize=10)
        plt.colorbar(im, ax=ax_heat, label='Δ MW', fraction=0.046, pad=0.04)

    # Bar chart
    ax_bar = fig.add_subplot(gs[1, year_idx])
    scenario_totals = year_data.groupby('scenario')['delta_capacity_MW'].sum().sort_values()
    colors_bar = ['coral' if x < 0 else 'lightgreen' for x in scenario_totals.values]
    ax_bar.barh(range(len(scenario_totals)), scenario_totals.values, color=colors_bar, alpha=0.7)
    ax_bar.set_yticks(range(len(scenario_totals)))
    ax_bar.set_yticklabels(scenario_totals.index, fontsize=8)
    ax_bar.set_xlabel('Total Δ Capacity (MW)', fontweight='bold')
    ax_bar.set_title(f'{year} - Total Border Δ', fontweight='bold', fontsize=10)
    ax_bar.axvline(x=0, color='black', linestyle='-', linewidth=0.8)
    ax_bar.grid(axis='x', alpha=0.3)

    for i, v in enumerate(scenario_totals.values):
        h_align = 'left' if v > 0 else 'right'
        offset = 0.02 * (scenario_totals.abs().max())
        x_pos = v + offset if v > 0 else v - offset
        ax_bar.text(x_pos, i, f'{v:+.1f}', va='center', ha=h_align, fontsize=8)

plt.savefig('border_infrastructure_capacity_deltas.png', dpi=300, bbox_inches='tight')
plt.show()
print("Plot 2 saved: border_infrastructure_capacity_deltas.png")

# ============================================================================
# CELL 6: PLOT 3 - Border Infrastructure Utilization Comparison
# ============================================================================

fig, axes = plt.subplots(1, 3, figsize=(18, 6))

for year_idx, year in enumerate([2030, 2040, 2050]):
    ax = axes[year_idx]
    plot_data = []

    for scenario_name in case_study_names:
        scenario_data = border_infra_data[scenario_name]
        year_data = scenario_data[scenario_data['year'] == year]
        fast_data = year_data[year_data['infrastructure_type'] == 'fast_charging_station']

        if len(fast_data) > 0:
            total_capacity = fast_data['total_capacity_MW'].sum()
            if total_capacity > 0:
                weighted_util = (fast_data['utilization_pct'] * fast_data['total_capacity_MW']).sum() / total_capacity
            else:
                weighted_util = 0
            plot_data.append({'scenario': scenario_name, 'utilization_pct': weighted_util, 'total_capacity_MW': total_capacity})

    if plot_data:
        df_util_plot = pd.DataFrame(plot_data)
        x = np.arange(len(df_util_plot))
        bars = ax.bar(x, df_util_plot['utilization_pct'], alpha=0.7,
                     color=['steelblue' if s == reference_scenario else 'coral' for s in df_util_plot['scenario']])
        ax.set_xticks(x)
        ax.set_xticklabels(df_util_plot['scenario'], rotation=45, ha='right')
        ax.set_ylabel('Utilization Rate (%)', fontweight='bold')
        ax.set_title(f'{year} - Fast Charging Utilization\n(Border Regions)', fontweight='bold')
        ax.set_ylim(0, min(100, df_util_plot['utilization_pct'].max() * 1.2))
        ax.grid(axis='y', alpha=0.3)

        for i, (idx, row) in enumerate(df_util_plot.iterrows()):
            ax.text(i, row['utilization_pct'], f"{row['utilization_pct']:.1f}%\n({row['total_capacity_MW']:.1f} MW)",
                   ha='center', va='bottom', fontsize=8)

        if len(df_util_plot) > 0:
            ref_util = df_util_plot[df_util_plot['scenario'] == reference_scenario]['utilization_pct']
            if len(ref_util) > 0:
                ax.axhline(y=ref_util.iloc[0], color='gray', linestyle='--', linewidth=1,
                          label=f'Reference ({ref_util.iloc[0]:.1f}%)')
                ax.legend(loc='upper right', fontsize=8)

plt.tight_layout()
plt.savefig('border_infrastructure_utilization.png', dpi=300, bbox_inches='tight')
plt.show()
print("Plot 3 saved: border_infrastructure_utilization.png")

# ============================================================================
# CELL 7: PLOT 4 - Summary Table Visualization
# ============================================================================

fig, ax = plt.subplots(1, 1, figsize=(16, 10))
ax.axis('tight')
ax.axis('off')

summary_table_data = []
for year in years_to_analyze:
    for scenario_name in case_study_names:
        scenario_data = border_infra_data[scenario_name]
        year_data = scenario_data[scenario_data['year'] == year]

        fast_data = year_data[year_data['infrastructure_type'] == 'fast_charging_station']
        slow_data = year_data[year_data['infrastructure_type'] == 'slow_charging_station']

        fast_capacity = fast_data['total_capacity_MW'].sum()
        slow_capacity = slow_data['total_capacity_MW'].sum()
        total_capacity = fast_capacity + slow_capacity

        if total_capacity > 0:
            fast_util = ((fast_data['utilization_pct'] * fast_data['total_capacity_MW']).sum() /
                        fast_data['total_capacity_MW'].sum()) if fast_data['total_capacity_MW'].sum() > 0 else 0
            slow_util = ((slow_data['utilization_pct'] * slow_data['total_capacity_MW']).sum() /
                        slow_data['total_capacity_MW'].sum()) if slow_data['total_capacity_MW'].sum() > 0 else 0
        else:
            fast_util, slow_util = 0, 0

        if scenario_name != reference_scenario:
            delta_year = df_delta_fast[(df_delta_fast['year'] == year) & (df_delta_fast['scenario'] == scenario_name)]
            delta_cap = delta_year['delta_capacity_MW'].sum() if len(delta_year) > 0 else 0
            delta_str = f"{delta_cap:+.1f}"
        else:
            delta_str = "REF"

        summary_table_data.append([year, scenario_name, f"{fast_capacity:.1f}", f"{slow_capacity:.1f}",
                                  f"{total_capacity:.1f}", delta_str, f"{fast_util:.1f}%", f"{slow_util:.1f}%"])

col_labels = ['Year', 'Scenario', 'Fast (MW)', 'Slow (MW)', 'Total (MW)', 'Δ Fast (MW)', 'Fast Util.', 'Slow Util.']
table = ax.table(cellText=summary_table_data, colLabels=col_labels, cellLoc='center', loc='center', bbox=[0, 0, 1, 1])
table.auto_set_font_size(False)
table.set_fontsize(9)
table.scale(1, 2)

for i in range(len(col_labels)):
    cell = table[(0, i)]
    cell.set_facecolor('#4472C4')
    cell.set_text_props(weight='bold', color='white')

for i in range(1, len(summary_table_data) + 1):
    for j in range(len(col_labels)):
        cell = table[(i, j)]
        cell.set_facecolor('#E7E6E6' if i % 2 == 0 else 'white')
        if summary_table_data[i-1][1] == reference_scenario:
            cell.set_facecolor('#D9E2F3')

ax.set_title('Border Region Charging Infrastructure Summary\n(All Scenarios and Years)', fontweight='bold', fontsize=14, pad=20)
plt.savefig('border_infrastructure_summary_table.png', dpi=300, bbox_inches='tight')
plt.show()
print("Plot 4 saved: border_infrastructure_summary_table.png")

# ============================================================================
# CELL 8: Export Summary Statistics
# ============================================================================

all_data_combined = pd.concat([df for df in border_infra_data.values()], ignore_index=True)
all_data_combined.to_csv('border_infrastructure_all_scenarios.csv', index=False)
print("Exported: border_infrastructure_all_scenarios.csv")

summary_stats = []
for scenario in case_study_names:
    scenario_data = border_infra_data[scenario]
    for year in years_to_analyze:
        year_data = scenario_data[scenario_data['year'] == year]
        for infr_type in ['fast_charging_station', 'slow_charging_station']:
            type_data = year_data[year_data['infrastructure_type'] == infr_type]
            if len(type_data) > 0:
                total_cap = type_data['total_capacity_MW'].sum()
                avg_util = ((type_data['utilization_pct'] * type_data['total_capacity_MW']).sum() / total_cap) if total_cap > 0 else 0
                summary_stats.append({
                    'scenario': scenario,
                    'year': year,
                    'infrastructure_type': infr_type,
                    'total_capacity_MW': total_cap,
                    'countries_count': type_data['country'].nunique(),
                    'avg_utilization_pct': avg_util
                })

df_summary_stats = pd.DataFrame(summary_stats)
df_summary_stats.to_csv('border_infrastructure_summary_stats.csv', index=False)
print("Exported: border_infrastructure_summary_stats.csv")

print("\n" + "="*80)
print("BORDER INFRASTRUCTURE ANALYSIS COMPLETE")
print("="*80)
print("\nGenerated:")
print("  - 4 visualizations (PNG, 300 DPI)")
print("  - 3 data files (CSV)")
