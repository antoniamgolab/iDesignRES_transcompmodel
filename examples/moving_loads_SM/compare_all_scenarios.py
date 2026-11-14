"""
Comprehensive comparison of all 24 uncertainty analysis scenarios.
Compares BASELINE (no charging-at-breaks constraint) vs CONSTRAINED runs.
"""

import yaml
import os
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict
from glob import glob

# Directories
RESULTS_DIR = os.path.dirname(__file__)
BASELINE_DIR = os.path.join(RESULTS_DIR, "results", "uncertainty_analysis")
CONSTRAINED_DIR = os.path.join(RESULTS_DIR, "results", "uncertainty_analysis_with_breaks")
SCENARIOS_DIR = os.path.join(RESULTS_DIR, "input_data", "uncertainty_scenarios")

def get_latest_file(folder, pattern):
    """Get the most recent file matching a pattern in a folder."""
    files = glob(os.path.join(folder, f"*{pattern}"))
    if not files:
        return None
    return max(files, key=os.path.getmtime)

def get_scenario_metadata(scenario_folder):
    """Extract scenario parameters from case_metadata.yaml using regex."""
    meta_file = os.path.join(SCENARIOS_DIR, scenario_folder, 'case_metadata.yaml')
    if not os.path.exists(meta_file):
        return None

    with open(meta_file, 'r') as f:
        content = f.read()

    genesys = re.search(r'genesys_scenario: (.+)', content)
    charging = re.search(r'charging_markup: ([\d.]+)', content)
    tech_cost = re.search(r'tech_cost_multiplier: ([\d.]+)', content)
    carbon_2040 = re.search(r'2040: ([\d.]+)', content)

    return {
        'genesys': genesys.group(1).strip() if genesys else 'NA',
        'charging_markup': float(charging.group(1)) if charging else None,
        'tech_cost_mult': float(tech_cost.group(1)) if tech_cost else None,
        'carbon_2040': float(carbon_2040.group(1)) if carbon_2040 else None
    }

def aggregate_h_by_year_and_tech(h_dict):
    """Aggregate vehicle stock by year and technology."""
    if h_dict is None:
        return {}

    result = defaultdict(lambda: defaultdict(float))

    for key, value in h_dict.items():
        val = float(value) if isinstance(value, str) else value
        if val > 1e-6:
            parts = key.strip("()").split(",")
            year = int(parts[0].strip())
            tech = int(parts[2].strip())  # tech_vehicle_id: 0=ICEV, 1=BEV
            result[year][tech] += val

    return dict(result)

def calc_bev_share_by_year(h_agg, years):
    """Calculate BEV share as percentage of total fleet for each year."""
    bev_shares = {}
    for year in years:
        if year in h_agg:
            total = sum(h_agg[year].values())
            bev = h_agg[year].get(1, 0)
            bev_shares[year] = 100 * bev / total if total > 0 else 0
    return bev_shares

def load_scenario_results(scenario_folder, base_dir):
    """Load h_dict results for a scenario."""
    folder_path = os.path.join(base_dir, scenario_folder)
    if not os.path.exists(folder_path):
        return None

    h_file = get_latest_file(folder_path, "h_dict.yaml")
    if not h_file:
        return None

    with open(h_file, 'r') as f:
        return yaml.safe_load(f)

def main():
    print("=" * 100)
    print("COMPREHENSIVE SCENARIO COMPARISON: BASELINE vs CONSTRAINED")
    print("=" * 100)

    years = [2020, 2024, 2028, 2032, 2036, 2040, 2044, 2048, 2052, 2056, 2060]
    scenarios = [f"scenario_{i:03d}" for i in range(24)]

    # Collect data for all scenarios
    results = []

    for scenario in scenarios:
        meta = get_scenario_metadata(scenario)
        if meta is None:
            continue

        # Load BASELINE results
        baseline_h = load_scenario_results(scenario, BASELINE_DIR)
        baseline_agg = aggregate_h_by_year_and_tech(baseline_h) if baseline_h else {}
        baseline_bev = calc_bev_share_by_year(baseline_agg, years) if baseline_agg else {}

        # Load CONSTRAINED results
        constrained_h = load_scenario_results(scenario, CONSTRAINED_DIR)
        constrained_agg = aggregate_h_by_year_and_tech(constrained_h) if constrained_h else {}
        constrained_bev = calc_bev_share_by_year(constrained_agg, years) if constrained_agg else {}

        # Store results
        for year in years:
            results.append({
                'scenario': scenario,
                'genesys': meta['genesys'],
                'charging_markup': meta['charging_markup'],
                'tech_cost_mult': meta['tech_cost_mult'],
                'carbon_2040': meta['carbon_2040'],
                'year': year,
                'baseline_bev_share': baseline_bev.get(year, 0),
                'constrained_bev_share': constrained_bev.get(year, 0),
                'baseline_total': sum(baseline_agg.get(year, {}).values()) if baseline_agg else 0,
                'constrained_total': sum(constrained_agg.get(year, {}).values()) if constrained_agg else 0,
            })

    df = pd.DataFrame(results)

    # Calculate delta (constrained - baseline)
    df['bev_share_delta'] = df['constrained_bev_share'] - df['baseline_bev_share']

    print("\n" + "=" * 100)
    print("BEV SHARE BY YEAR AND SCENARIO (2040)")
    print("=" * 100)

    # Filter for year 2040
    df_2040 = df[df['year'] == 2040].copy()

    print(f"\n{'Scenario':<14} {'GENeSYS':<20} {'Chrg':<6} {'Tech':<6} {'CO2':<6} {'BASE%':<8} {'CONST%':<8} {'Delta':<8}")
    print("-" * 100)
    for _, row in df_2040.sort_values('scenario').iterrows():
        print(f"{row['scenario']:<14} {row['genesys'][:18]:<20} {row['charging_markup']:<6.2f} {row['tech_cost_mult']:<6.1f} {row['carbon_2040']:<6.0f} {row['baseline_bev_share']:<8.1f} {row['constrained_bev_share']:<8.1f} {row['bev_share_delta']:<+8.1f}")

    # Summary statistics
    print("\n" + "=" * 100)
    print("SUMMARY STATISTICS FOR YEAR 2040")
    print("=" * 100)

    print(f"\nBaseline BEV Share:")
    print(f"  Mean: {df_2040['baseline_bev_share'].mean():.1f}%")
    print(f"  Std:  {df_2040['baseline_bev_share'].std():.1f}%")
    print(f"  Min:  {df_2040['baseline_bev_share'].min():.1f}%")
    print(f"  Max:  {df_2040['baseline_bev_share'].max():.1f}%")

    print(f"\nConstrained BEV Share:")
    print(f"  Mean: {df_2040['constrained_bev_share'].mean():.1f}%")
    print(f"  Std:  {df_2040['constrained_bev_share'].std():.1f}%")
    print(f"  Min:  {df_2040['constrained_bev_share'].min():.1f}%")
    print(f"  Max:  {df_2040['constrained_bev_share'].max():.1f}%")

    print(f"\nBEV Share Delta (Constrained - Baseline):")
    print(f"  Mean: {df_2040['bev_share_delta'].mean():+.1f} percentage points")
    print(f"  Std:  {df_2040['bev_share_delta'].std():.1f}")
    print(f"  Min:  {df_2040['bev_share_delta'].min():+.1f}")
    print(f"  Max:  {df_2040['bev_share_delta'].max():+.1f}")

    # Group by parameters
    print("\n" + "=" * 100)
    print("BEV SHARE BY PARAMETER (2040)")
    print("=" * 100)

    # By GENeSYS scenario
    print("\nBy GENeSYS Scenario:")
    for genesys in df_2040['genesys'].unique():
        subset = df_2040[df_2040['genesys'] == genesys]
        print(f"  {genesys[:20]:<22} BASE: {subset['baseline_bev_share'].mean():5.1f}%  CONST: {subset['constrained_bev_share'].mean():5.1f}%  Delta: {subset['bev_share_delta'].mean():+5.1f}")

    # By carbon price
    print("\nBy Carbon Price (2040):")
    for carbon in sorted(df_2040['carbon_2040'].unique()):
        subset = df_2040[df_2040['carbon_2040'] == carbon]
        print(f"  {carbon:6.0f} EUR/t  BASE: {subset['baseline_bev_share'].mean():5.1f}%  CONST: {subset['constrained_bev_share'].mean():5.1f}%  Delta: {subset['bev_share_delta'].mean():+5.1f}")

    # By charging markup
    print("\nBy Charging Markup:")
    for markup in sorted(df_2040['charging_markup'].unique()):
        subset = df_2040[df_2040['charging_markup'] == markup]
        print(f"  {markup*100:4.0f}%         BASE: {subset['baseline_bev_share'].mean():5.1f}%  CONST: {subset['constrained_bev_share'].mean():5.1f}%  Delta: {subset['bev_share_delta'].mean():+5.1f}")

    # By tech cost multiplier
    print("\nBy Tech Cost Multiplier:")
    for tech in sorted(df_2040['tech_cost_mult'].unique()):
        subset = df_2040[df_2040['tech_cost_mult'] == tech]
        print(f"  {tech:4.1f}x          BASE: {subset['baseline_bev_share'].mean():5.1f}%  CONST: {subset['constrained_bev_share'].mean():5.1f}%  Delta: {subset['bev_share_delta'].mean():+5.1f}")

    # ========================
    # CREATE VISUALIZATIONS
    # ========================

    os.makedirs("figures", exist_ok=True)

    # Figure 1: BEV share comparison heatmap for 2040
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Reshape data for heatmap
    pivot_base = df_2040.pivot_table(values='baseline_bev_share',
                                      index='genesys',
                                      columns='tech_cost_mult',
                                      aggfunc='mean')
    pivot_const = df_2040.pivot_table(values='constrained_bev_share',
                                       index='genesys',
                                       columns='tech_cost_mult',
                                       aggfunc='mean')

    im1 = axes[0].imshow(pivot_base.values, cmap='YlGn', aspect='auto', vmin=0, vmax=100)
    axes[0].set_title('BASELINE - BEV Share (%) in 2040', fontsize=12)
    axes[0].set_xticks(range(len(pivot_base.columns)))
    axes[0].set_xticklabels([f'{x:.1f}x' for x in pivot_base.columns])
    axes[0].set_yticks(range(len(pivot_base.index)))
    axes[0].set_yticklabels([s[:15] for s in pivot_base.index])
    axes[0].set_xlabel('Tech Cost Multiplier')
    axes[0].set_ylabel('GENeSYS Scenario')
    for i in range(len(pivot_base.index)):
        for j in range(len(pivot_base.columns)):
            axes[0].text(j, i, f'{pivot_base.values[i, j]:.0f}%', ha='center', va='center', fontsize=10)

    im2 = axes[1].imshow(pivot_const.values, cmap='YlGn', aspect='auto', vmin=0, vmax=100)
    axes[1].set_title('CONSTRAINED - BEV Share (%) in 2040', fontsize=12)
    axes[1].set_xticks(range(len(pivot_const.columns)))
    axes[1].set_xticklabels([f'{x:.1f}x' for x in pivot_const.columns])
    axes[1].set_yticks(range(len(pivot_const.index)))
    axes[1].set_yticklabels([s[:15] for s in pivot_const.index])
    axes[1].set_xlabel('Tech Cost Multiplier')

    plt.colorbar(im2, ax=axes[1], label='BEV Share (%)')
    plt.tight_layout()
    plt.savefig('figures/scenario_comparison_heatmap_2040.pdf', dpi=150, bbox_inches='tight')
    plt.savefig('figures/scenario_comparison_heatmap_2040.png', dpi=150, bbox_inches='tight')
    print("\nSaved: figures/scenario_comparison_heatmap_2040.pdf")

    # Figure 2: Time series of BEV share by GENeSYS scenario
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()

    genesys_scenarios = df['genesys'].unique()
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']

    for idx, genesys in enumerate(genesys_scenarios):
        ax = axes[idx]
        subset = df[df['genesys'] == genesys]

        # Average across all parameter combinations for this GENeSYS scenario
        baseline_ts = subset.groupby('year')['baseline_bev_share'].mean()
        constrained_ts = subset.groupby('year')['constrained_bev_share'].mean()

        ax.plot(baseline_ts.index, baseline_ts.values, 'o-', label='Baseline', color='blue', linewidth=2)
        ax.plot(constrained_ts.index, constrained_ts.values, 's--', label='Constrained', color='red', linewidth=2)
        ax.fill_between(baseline_ts.index, baseline_ts.values, constrained_ts.values, alpha=0.2, color='gray')

        ax.set_title(f'{genesys[:20]}', fontsize=12)
        ax.set_xlabel('Year')
        ax.set_ylabel('BEV Share (%)')
        ax.set_ylim(0, 100)
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3)

    plt.suptitle('BEV Share Over Time: Baseline vs Constrained', fontsize=14, y=1.02)
    plt.tight_layout()
    plt.savefig('figures/scenario_comparison_timeseries_by_genesys.pdf', dpi=150, bbox_inches='tight')
    plt.savefig('figures/scenario_comparison_timeseries_by_genesys.png', dpi=150, bbox_inches='tight')
    print("Saved: figures/scenario_comparison_timeseries_by_genesys.pdf")

    # Figure 3: Bar chart comparing all scenarios at 2040
    fig, ax = plt.subplots(figsize=(16, 8))

    x = np.arange(24)
    width = 0.35

    baseline_vals = df_2040.sort_values('scenario')['baseline_bev_share'].values
    constrained_vals = df_2040.sort_values('scenario')['constrained_bev_share'].values
    scenario_labels = df_2040.sort_values('scenario')['scenario'].values

    bars1 = ax.bar(x - width/2, baseline_vals, width, label='Baseline', color='#2ecc71', alpha=0.8)
    bars2 = ax.bar(x + width/2, constrained_vals, width, label='Constrained', color='#e74c3c', alpha=0.8)

    ax.set_xlabel('Scenario', fontsize=12)
    ax.set_ylabel('BEV Share (%)', fontsize=12)
    ax.set_title('BEV Share in 2040: All Scenarios Comparison', fontsize=14)
    ax.set_xticks(x)
    ax.set_xticklabels([s[-3:] for s in scenario_labels], rotation=45)
    ax.legend()
    ax.set_ylim(0, 100)
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig('figures/scenario_comparison_bar_2040.pdf', dpi=150, bbox_inches='tight')
    plt.savefig('figures/scenario_comparison_bar_2040.png', dpi=150, bbox_inches='tight')
    print("Saved: figures/scenario_comparison_bar_2040.pdf")

    # Figure 4: Delta analysis - effect of constraint by parameter
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # By GENeSYS
    ax1 = axes[0, 0]
    genesys_delta = df_2040.groupby('genesys')['bev_share_delta'].mean()
    colors = ['#3498db' if d >= 0 else '#e74c3c' for d in genesys_delta.values]
    ax1.barh(range(len(genesys_delta)), genesys_delta.values, color=colors, alpha=0.8)
    ax1.set_yticks(range(len(genesys_delta)))
    ax1.set_yticklabels([s[:15] for s in genesys_delta.index])
    ax1.set_xlabel('BEV Share Delta (percentage points)')
    ax1.set_title('Effect by GENeSYS Scenario')
    ax1.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
    ax1.grid(True, alpha=0.3, axis='x')

    # By Carbon Price
    ax2 = axes[0, 1]
    carbon_delta = df_2040.groupby('carbon_2040')['bev_share_delta'].mean()
    colors = ['#3498db' if d >= 0 else '#e74c3c' for d in carbon_delta.values]
    ax2.bar(range(len(carbon_delta)), carbon_delta.values, color=colors, alpha=0.8)
    ax2.set_xticks(range(len(carbon_delta)))
    ax2.set_xticklabels([f'{int(c)}' for c in carbon_delta.index])
    ax2.set_xlabel('Carbon Price 2040 (EUR/t)')
    ax2.set_ylabel('BEV Share Delta (pp)')
    ax2.set_title('Effect by Carbon Price')
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    ax2.grid(True, alpha=0.3, axis='y')

    # By Charging Markup
    ax3 = axes[1, 0]
    markup_delta = df_2040.groupby('charging_markup')['bev_share_delta'].mean()
    colors = ['#3498db' if d >= 0 else '#e74c3c' for d in markup_delta.values]
    ax3.bar(range(len(markup_delta)), markup_delta.values, color=colors, alpha=0.8)
    ax3.set_xticks(range(len(markup_delta)))
    ax3.set_xticklabels([f'{int(m*100)}%' for m in markup_delta.index])
    ax3.set_xlabel('Charging Markup')
    ax3.set_ylabel('BEV Share Delta (pp)')
    ax3.set_title('Effect by Charging Markup')
    ax3.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    ax3.grid(True, alpha=0.3, axis='y')

    # By Tech Cost Multiplier
    ax4 = axes[1, 1]
    tech_delta = df_2040.groupby('tech_cost_mult')['bev_share_delta'].mean()
    colors = ['#3498db' if d >= 0 else '#e74c3c' for d in tech_delta.values]
    ax4.bar(range(len(tech_delta)), tech_delta.values, color=colors, alpha=0.8)
    ax4.set_xticks(range(len(tech_delta)))
    ax4.set_xticklabels([f'{t:.1f}x' for t in tech_delta.index])
    ax4.set_xlabel('Tech Cost Multiplier')
    ax4.set_ylabel('BEV Share Delta (pp)')
    ax4.set_title('Effect by Tech Cost')
    ax4.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    ax4.grid(True, alpha=0.3, axis='y')

    plt.suptitle('Effect of Charging-at-Breaks Constraint on BEV Share (2040)', fontsize=14, y=1.02)
    plt.tight_layout()
    plt.savefig('figures/scenario_comparison_delta_analysis.pdf', dpi=150, bbox_inches='tight')
    plt.savefig('figures/scenario_comparison_delta_analysis.png', dpi=150, bbox_inches='tight')
    print("Saved: figures/scenario_comparison_delta_analysis.pdf")

    # Save summary to CSV
    df_2040.to_csv('scenario_comparison_summary_2040.csv', index=False)
    print("\nSaved: scenario_comparison_summary_2040.csv")

    print("\n" + "=" * 100)
    print("ANALYSIS COMPLETE")
    print("=" * 100)

if __name__ == "__main__":
    main()
