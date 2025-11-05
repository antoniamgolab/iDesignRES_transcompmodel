"""
Notebook cell for analyzing the new Germany-Denmark-Sweden cluster

This cluster includes:
- ALL 5 Danish NUTS2 regions (DK01, DK02, DK03, DK04, DK05)
- German region bordering Denmark: DEF0 (Schleswig-Holstein)
- Swedish regions connected via Öresund bridge: SE22, SE23 (Southern Sweden)

Total: 8 NUTS2 regions across 3 countries
"""

# =============================================================================
# CELL 1: Analyze Germany-Denmark-Sweden Cluster (All of Denmark)
# =============================================================================

# Reload module to pick up the new cluster definition
import importlib
import sub_border_regions_cross_case
importlib.reload(sub_border_regions_cross_case)
from sub_border_regions_cross_case import *

# Define readable labels for your cases
case_labels = {
    "case_20251022_152235_var_var": "Var-Var",
    "case_20251022_152358_var_uni": "Var-Uni",
    "case_20251022_153056_uni_var": "Uni-Var",
    "case_20251022_153317_uni_uni": "Uni-Uni"
}

# Run analysis for the NEW Germany-Denmark-Sweden cluster
df_comparison_dks, df_summary_dks = analyze_sub_region_cross_case_preloaded(
    loaded_runs=loaded_runs,
    case_labels=case_labels,
    sub_region_name='Germany-Denmark-Sweden',  # <-- NEW CLUSTER!
    years_to_plot=[2030, 2040, 2050],
    baseline_case='Var-Var',
    show_plots=False,  # Set to True if you want automatic plots
    verbose=True
)

# Display results
display(df_comparison_dks)
display(df_summary_dks)


# =============================================================================
# CELL 2: Custom Visualization - Grouped Bars by Country
# =============================================================================

import matplotlib.pyplot as plt
import numpy as np

years_to_plot = [2030, 2040, 2050]

fig, axes = plt.subplots(1, len(years_to_plot), figsize=(20, 6))

case_colors = {
    'Var-Var': '#1f77b4',
    'Var-Uni': '#ff7f0e',
    'Uni-Var': '#2ca02c',
    'Uni-Uni': '#d62728'
}

for idx, year in enumerate(years_to_plot):
    ax = axes[idx]

    year_data = df_comparison_dks[df_comparison_dks['year'] == year]

    if len(year_data) == 0:
        continue

    countries = sorted(year_data['country'].unique())
    cases = sorted(year_data['case'].unique())

    x = np.arange(len(countries))
    width = 0.8 / len(cases)

    for i, case in enumerate(cases):
        case_data = year_data[year_data['case'] == case]
        values = [case_data[case_data['country'] == c]['electrification_pct'].values[0]
                 if len(case_data[case_data['country'] == c]) > 0 else 0
                 for c in countries]

        offset = width * (i - len(cases)/2 + 0.5)
        ax.bar(x + offset, values, width, label=case,
               alpha=0.85, color=case_colors[case])

    ax.set_xlabel('Country', fontsize=13, fontweight='bold')
    ax.set_ylabel('Electrification %', fontsize=13, fontweight='bold')
    ax.set_title(f'Germany-Denmark-Sweden Cluster\nYear {year}',
                fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(countries, fontsize=12)
    ax.legend(title='Scenario', fontsize=11, title_fontsize=12)
    ax.grid(True, alpha=0.3, axis='y', linestyle='--')
    ax.set_ylim(0, 100)
    ax.set_axisbelow(True)

plt.tight_layout()
plt.savefig('germany_denmark_sweden_cluster_electrification.png', dpi=300, bbox_inches='tight')
plt.show()


# =============================================================================
# CELL 3: Focus on Denmark - All 5 Regions Over Time
# =============================================================================

fig, ax = plt.subplots(figsize=(12, 7))

# Filter for Denmark only
dk_data = df_comparison_dks[df_comparison_dks['country'] == 'DK']

case_styles = {
    'Var-Var': {'color': '#1f77b4', 'marker': 'o', 'linestyle': '-'},
    'Var-Uni': {'color': '#ff7f0e', 'marker': 's', 'linestyle': '--'},
    'Uni-Var': {'color': '#2ca02c', 'marker': '^', 'linestyle': '-.'},
    'Uni-Uni': {'color': '#d62728', 'marker': 'D', 'linestyle': ':'}
}

for case in sorted(dk_data['case'].unique()):
    case_data = dk_data[dk_data['case'] == case].sort_values('year')
    style = case_styles.get(case, {})

    ax.plot(case_data['year'], case_data['electrification_pct'],
           marker=style.get('marker', 'o'),
           color=style.get('color', None),
           linestyle=style.get('linestyle', '-'),
           label=case, linewidth=3, markersize=10)

ax.set_xlabel('Year', fontsize=13, fontweight='bold')
ax.set_ylabel('Electrification %', fontsize=13, fontweight='bold')
ax.set_title('Denmark Electrification Across All Scenarios\n(All 5 NUTS2 regions)',
            fontsize=15, fontweight='bold')
ax.legend(fontsize=12, loc='best', title='Scenario', title_fontsize=13)
ax.grid(True, alpha=0.3, linestyle='--')
ax.set_ylim(0, 100)
ax.set_axisbelow(True)

plt.tight_layout()
plt.savefig('denmark_electrification_all_regions.png', dpi=300, bbox_inches='tight')
plt.show()


# =============================================================================
# CELL 4: Delta Analysis - Comparison vs Baseline (Var-Var)
# =============================================================================

baseline_case = 'Var-Var'

# Calculate deltas
baseline_data = df_comparison_dks[df_comparison_dks['case'] == baseline_case].copy()
baseline_data = baseline_data.set_index(['country', 'year'])

df_deltas_dks = []
for case in df_comparison_dks['case'].unique():
    if case == baseline_case:
        continue

    case_data = df_comparison_dks[df_comparison_dks['case'] == case].copy()
    case_data = case_data.set_index(['country', 'year'])

    for idx in case_data.index:
        if idx in baseline_data.index:
            delta = case_data.loc[idx, 'electrification_pct'] - baseline_data.loc[idx, 'electrification_pct']
            df_deltas_dks.append({
                'case': case,
                'country': idx[0],
                'year': idx[1],
                'delta_pct': delta
            })

df_deltas_dks = pd.DataFrame(df_deltas_dks)

# Plot deltas
fig, axes = plt.subplots(1, len(years_to_plot), figsize=(20, 6))

for idx, year in enumerate(years_to_plot):
    ax = axes[idx]

    year_data = df_deltas_dks[df_deltas_dks['year'] == year]

    if len(year_data) == 0:
        continue

    countries = sorted(year_data['country'].unique())
    cases = sorted(year_data['case'].unique())

    x = np.arange(len(countries))
    width = 0.8 / len(cases)

    for i, case in enumerate(cases):
        case_data = year_data[year_data['case'] == case]
        values = [case_data[case_data['country'] == c]['delta_pct'].values[0]
                 if len(case_data[case_data['country'] == c]) > 0 else 0
                 for c in countries]

        offset = width * (i - len(cases)/2 + 0.5)
        bars = ax.bar(x + offset, values, width, label=case, alpha=0.85)

        # Color bars: green for positive, red for negative
        for bar, val in zip(bars, values):
            if val > 0:
                bar.set_color('green')
            elif val < 0:
                bar.set_color('red')
            else:
                bar.set_color('gray')

    ax.set_xlabel('Country', fontsize=13, fontweight='bold')
    ax.set_ylabel(f'Δ Electrification % (vs. {baseline_case})', fontsize=13, fontweight='bold')
    ax.set_title(f'Germany-Denmark-Sweden\nYear {year}', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(countries, fontsize=12)
    ax.legend(title='Scenario', fontsize=11, title_fontsize=12)
    ax.grid(True, alpha=0.3, axis='y', linestyle='--')
    ax.axhline(y=0, color='black', linestyle='-', linewidth=1.5)
    ax.set_axisbelow(True)

plt.tight_layout()
plt.savefig('germany_denmark_sweden_deltas.png', dpi=300, bbox_inches='tight')
plt.show()


# =============================================================================
# CELL 5: Summary Statistics
# =============================================================================

print("\n" + "="*100)
print("GERMANY-DENMARK-SWEDEN CLUSTER SUMMARY")
print("="*100)
print("\nCluster composition:")
print("  - Denmark (ALL regions): DK01, DK02, DK03, DK04, DK05")
print("  - Germany (Schleswig-Holstein): DEF0")
print("  - Sweden (Southern Sweden/Öresund): SE22, SE23")
print("  - Total: 8 NUTS2 regions across 3 countries")
print("\n" + df_summary_dks.to_string(index=False))
print("="*100)

# Export results
df_comparison_dks.to_csv('germany_denmark_sweden_comparison.csv', index=False)
df_summary_dks.to_csv('germany_denmark_sweden_summary.csv', index=False)
print("\n✓ Results exported to CSV files")
