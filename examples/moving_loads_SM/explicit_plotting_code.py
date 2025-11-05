"""
Explicit plotting code for df_comparison
Copy these cells into your notebook to customize the plots yourself
"""

# =============================================================================
# CELL 1: Get the data WITHOUT automatic plotting
# =============================================================================
from sub_border_regions_cross_case import *
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Define readable labels for your cases
case_labels = {
    "case_20251022_152235_var_var": "Var-Var",
    "case_20251022_152358_var_uni": "Var-Uni",
    "case_20251022_153056_uni_var": "Uni-Var",
    "case_20251022_153317_uni_uni": "Uni-Uni"
}

# Run analysis WITHOUT showing plots (show_plots=False)
df_comparison, df_summary = analyze_sub_region_cross_case_preloaded(
    loaded_runs=loaded_runs,
    case_labels=case_labels,
    sub_region_name='Austria-Germany-Italy',
    years_to_plot=[2030, 2040, 2050],
    baseline_case='Var-Var',
    show_plots=False,  # <-- Set to False!
    verbose=True
)

# Display results
display(df_comparison)
display(df_summary)


# =============================================================================
# CELL 2: Plot 1 - Grouped Bar Chart (Electrification %)
# =============================================================================
years_to_plot = [2030, 2040, 2050]
sub_region_name = 'Austria-Germany-Italy'

fig, axes = plt.subplots(1, len(years_to_plot), figsize=(18, 6))
if len(years_to_plot) == 1:
    axes = [axes]

# Define custom colors for each case
case_colors = {
    'Var-Var': '#1f77b4',      # blue
    'Var-Uni': '#ff7f0e',      # orange
    'Uni-Var': '#2ca02c',      # green
    'Uni-Uni': '#d62728'       # red
}

for idx, year in enumerate(years_to_plot):
    ax = axes[idx]

    # Filter to this year
    year_data = df_comparison[df_comparison['year'] == year]

    if len(year_data) == 0:
        ax.text(0.5, 0.5, f'No data for {year}',
               ha='center', va='center', transform=ax.transAxes)
        ax.set_title(f'Year {year}')
        continue

    # Get unique countries and cases
    countries = sorted(year_data['country'].unique())
    cases = sorted(year_data['case'].unique())

    x = np.arange(len(countries))
    width = 0.8 / len(cases)

    # Plot bars for each case
    for i, case in enumerate(cases):
        case_data = year_data[year_data['case'] == case]
        values = [case_data[case_data['country'] == c]['electrification_pct'].values[0]
                 if len(case_data[case_data['country'] == c]) > 0 else 0
                 for c in countries]

        offset = width * (i - len(cases)/2 + 0.5)
        color = case_colors.get(case, None)  # Use custom colors
        ax.bar(x + offset, values, width, label=case, alpha=0.85, color=color)

    # Customize appearance
    ax.set_xlabel('Country', fontsize=12, fontweight='bold')
    ax.set_ylabel('Electrification %', fontsize=12, fontweight='bold')
    ax.set_title(f'{sub_region_name}\nYear {year}', fontsize=13, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(countries, fontsize=11)
    ax.legend(title='Scenario', fontsize=10, title_fontsize=11)
    ax.grid(True, alpha=0.3, axis='y', linestyle='--')
    ax.set_ylim(0, 100)
    ax.set_axisbelow(True)

plt.tight_layout()
plt.savefig('border_electrification_grouped_bars.png', dpi=300, bbox_inches='tight')
plt.show()


# =============================================================================
# CELL 3: Plot 2 - Line Charts by Country (Electrification %)
# =============================================================================
countries = sorted(df_comparison['country'].unique())
n_countries = len(countries)
n_cols = min(3, n_countries)
n_rows = (n_countries + n_cols - 1) // n_cols

fig, axes = plt.subplots(n_rows, n_cols, figsize=(16, 5*n_rows))

# Ensure axes is always 2D for consistent indexing
if n_rows == 1 and n_cols == 1:
    axes = np.array([[axes]])
elif n_rows == 1:
    axes = axes.reshape(1, -1)
elif n_cols == 1:
    axes = axes.reshape(-1, 1)

# Define markers and colors
case_styles = {
    'Var-Var': {'color': '#1f77b4', 'marker': 'o', 'linestyle': '-'},
    'Var-Uni': {'color': '#ff7f0e', 'marker': 's', 'linestyle': '--'},
    'Uni-Var': {'color': '#2ca02c', 'marker': '^', 'linestyle': '-.'},
    'Uni-Uni': {'color': '#d62728', 'marker': 'D', 'linestyle': ':'}
}

for idx, country in enumerate(countries):
    row = idx // n_cols
    col = idx % n_cols
    ax = axes[row, col]

    country_data = df_comparison[df_comparison['country'] == country]

    for case in sorted(country_data['case'].unique()):
        case_data = country_data[country_data['case'] == case].sort_values('year')
        style = case_styles.get(case, {})

        ax.plot(case_data['year'], case_data['electrification_pct'],
               marker=style.get('marker', 'o'),
               color=style.get('color', None),
               linestyle=style.get('linestyle', '-'),
               label=case, linewidth=2.5, markersize=8)

    ax.set_xlabel('Year', fontsize=11, fontweight='bold')
    ax.set_ylabel('Electrification %', fontsize=11, fontweight='bold')
    ax.set_title(f'{country}', fontsize=12, fontweight='bold')
    ax.legend(fontsize=9, loc='best')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_ylim(0, 100)
    ax.set_axisbelow(True)

# Hide empty subplots
for idx in range(n_countries, n_rows * n_cols):
    row = idx // n_cols
    col = idx % n_cols
    axes[row, col].axis('off')

fig.suptitle(f'{sub_region_name} - Electrification Across Scenarios',
            fontsize=16, fontweight='bold', y=1.00)

plt.tight_layout()
plt.savefig('border_electrification_lines.png', dpi=300, bbox_inches='tight')
plt.show()


# =============================================================================
# CELL 4: Plot 3 - Absolute Electricity Consumption (MWh) - Grouped Bars
# =============================================================================
fig, axes = plt.subplots(1, len(years_to_plot), figsize=(18, 6))
if len(years_to_plot) == 1:
    axes = [axes]

for idx, year in enumerate(years_to_plot):
    ax = axes[idx]

    year_data = df_comparison[df_comparison['year'] == year]

    if len(year_data) == 0:
        ax.text(0.5, 0.5, f'No data for {year}',
               ha='center', va='center', transform=ax.transAxes)
        ax.set_title(f'Year {year}')
        continue

    countries = sorted(year_data['country'].unique())
    cases = sorted(year_data['case'].unique())

    x = np.arange(len(countries))
    width = 0.8 / len(cases)

    for i, case in enumerate(cases):
        case_data = year_data[year_data['case'] == case]
        values = [case_data[case_data['country'] == c]['electricity'].values[0]
                 if len(case_data[case_data['country'] == c]) > 0 else 0
                 for c in countries]

        offset = width * (i - len(cases)/2 + 0.5)
        color = case_colors.get(case, None)
        ax.bar(x + offset, values, width, label=case, alpha=0.85, color=color)

    ax.set_xlabel('Country', fontsize=12, fontweight='bold')
    ax.set_ylabel('Electricity Consumption (MWh)', fontsize=12, fontweight='bold')
    ax.set_title(f'{sub_region_name}\nYear {year}', fontsize=13, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(countries, fontsize=11)
    ax.legend(title='Scenario', fontsize=10, title_fontsize=11)
    ax.grid(True, alpha=0.3, axis='y', linestyle='--')
    ax.set_axisbelow(True)

plt.tight_layout()
plt.savefig('border_electricity_consumption_bars.png', dpi=300, bbox_inches='tight')
plt.show()


# =============================================================================
# CELL 5: Plot 4 - Absolute Electricity Consumption - Line Charts
# =============================================================================
fig, axes = plt.subplots(n_rows, n_cols, figsize=(16, 5*n_rows))

# Ensure axes is always 2D
if n_rows == 1 and n_cols == 1:
    axes = np.array([[axes]])
elif n_rows == 1:
    axes = axes.reshape(1, -1)
elif n_cols == 1:
    axes = axes.reshape(-1, 1)

for idx, country in enumerate(countries):
    row = idx // n_cols
    col = idx % n_cols
    ax = axes[row, col]

    country_data = df_comparison[df_comparison['country'] == country]

    for case in sorted(country_data['case'].unique()):
        case_data = country_data[country_data['case'] == case].sort_values('year')
        style = case_styles.get(case, {})

        ax.plot(case_data['year'], case_data['electricity'],
               marker=style.get('marker', 'o'),
               color=style.get('color', None),
               linestyle=style.get('linestyle', '-'),
               label=case, linewidth=2.5, markersize=8)

    ax.set_xlabel('Year', fontsize=11, fontweight='bold')
    ax.set_ylabel('Electricity (MWh)', fontsize=11, fontweight='bold')
    ax.set_title(f'{country}', fontsize=12, fontweight='bold')
    ax.legend(fontsize=9, loc='best')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)

# Hide empty subplots
for idx in range(n_countries, n_rows * n_cols):
    row = idx // n_cols
    col = idx % n_cols
    axes[row, col].axis('off')

fig.suptitle(f'{sub_region_name} - Electricity Consumption (MWh) Across Scenarios',
            fontsize=16, fontweight='bold', y=1.00)

plt.tight_layout()
plt.savefig('border_electricity_consumption_lines.png', dpi=300, bbox_inches='tight')
plt.show()


# =============================================================================
# CELL 6: Plot 5 - Delta Plot (vs. Baseline)
# =============================================================================
baseline_case = 'Var-Var'

# Calculate deltas
baseline_data = df_comparison[df_comparison['case'] == baseline_case].copy()
baseline_data = baseline_data.set_index(['country', 'year'])

df_deltas = []
for case in df_comparison['case'].unique():
    if case == baseline_case:
        continue

    case_data = df_comparison[df_comparison['case'] == case].copy()
    case_data = case_data.set_index(['country', 'year'])

    # Calculate delta
    for idx in case_data.index:
        if idx in baseline_data.index:
            delta = case_data.loc[idx, 'electrification_pct'] - baseline_data.loc[idx, 'electrification_pct']
            df_deltas.append({
                'case': case,
                'country': idx[0],
                'year': idx[1],
                'delta_pct': delta
            })

df_deltas = pd.DataFrame(df_deltas)

# Plot deltas
fig, axes = plt.subplots(1, len(years_to_plot), figsize=(18, 6))
if len(years_to_plot) == 1:
    axes = [axes]

for idx, year in enumerate(years_to_plot):
    ax = axes[idx]

    year_data = df_deltas[df_deltas['year'] == year]

    if len(year_data) == 0:
        ax.text(0.5, 0.5, f'No data for {year}',
               ha='center', va='center', transform=ax.transAxes)
        ax.set_title(f'Year {year}')
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

    ax.set_xlabel('Country', fontsize=12, fontweight='bold')
    ax.set_ylabel(f'Δ Electrification % (vs. {baseline_case})', fontsize=12, fontweight='bold')
    ax.set_title(f'{sub_region_name}\nYear {year}', fontsize=13, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(countries, fontsize=11)
    ax.legend(title='Scenario', fontsize=10, title_fontsize=11)
    ax.grid(True, alpha=0.3, axis='y', linestyle='--')
    ax.axhline(y=0, color='black', linestyle='-', linewidth=1.5)
    ax.set_axisbelow(True)

plt.tight_layout()
plt.savefig('border_electrification_deltas.png', dpi=300, bbox_inches='tight')
plt.show()


# =============================================================================
# CELL 7: Summary Statistics Table
# =============================================================================
print("\n" + "="*100)
print(f"SUMMARY STATISTICS: {sub_region_name}")
print("="*100)
print(df_summary.to_string(index=False))
print("="*100)

# Export summary to LaTeX
latex_table = df_summary.to_latex(index=False, float_format="%.2f")
print("\nLaTeX Table:")
print(latex_table)
