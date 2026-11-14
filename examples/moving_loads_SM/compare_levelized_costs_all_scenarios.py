"""
Compare levelized transport costs across all 24 uncertainty scenarios.
Loads available results and creates comparison visualizations.

Scenario structure (24 scenarios):
- 4 GENeSYS scenarios: Go RES, NECPEssentials, REPowerEU++, Trinity
- 2 Charging markups: 15%, 30%
- 3 Tech cost multipliers: 0.7x, 1.0x, 1.3x
"""

import yaml
import os
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

# ============================================================================
# SCENARIO METADATA
# ============================================================================

# Scenario mapping: scenario_XXX -> (genesys_scenario, markup, tech_multiplier)
SCENARIO_PARAMS = {
    'scenario_000': ('Go RES', 0.15, 0.7),
    'scenario_001': ('Go RES', 0.15, 1.0),
    'scenario_002': ('Go RES', 0.15, 1.3),
    'scenario_003': ('Go RES', 0.30, 0.7),
    'scenario_004': ('Go RES', 0.30, 1.0),
    'scenario_005': ('Go RES', 0.30, 1.3),
    'scenario_006': ('NECPEssentials', 0.15, 0.7),
    'scenario_007': ('NECPEssentials', 0.15, 1.0),
    'scenario_008': ('NECPEssentials', 0.15, 1.3),
    'scenario_009': ('NECPEssentials', 0.30, 0.7),
    'scenario_010': ('NECPEssentials', 0.30, 1.0),
    'scenario_011': ('NECPEssentials', 0.30, 1.3),
    'scenario_012': ('REPowerEU++', 0.15, 0.7),
    'scenario_013': ('REPowerEU++', 0.15, 1.0),
    'scenario_014': ('REPowerEU++', 0.15, 1.3),
    'scenario_015': ('REPowerEU++', 0.30, 0.7),
    'scenario_016': ('REPowerEU++', 0.30, 1.0),
    'scenario_017': ('REPowerEU++', 0.30, 1.3),
    'scenario_018': ('Trinity', 0.15, 0.7),
    'scenario_019': ('Trinity', 0.15, 1.0),
    'scenario_020': ('Trinity', 0.15, 1.3),
    'scenario_021': ('Trinity', 0.30, 0.7),
    'scenario_022': ('Trinity', 0.30, 1.0),
    'scenario_023': ('Trinity', 0.30, 1.3),
}

# Carbon price trajectories (EUR/tCO2)
CARBON_PRICES = {
    'Go RES': {2020: 30, 2030: 200, 2040: 500, 2050: 1000, 2060: 1000},
    'REPowerEU++': {2020: 30, 2030: 150, 2040: 350, 2050: 700, 2060: 700},
    'NECPEssentials': {2020: 30, 2030: 100, 2040: 250, 2050: 500, 2060: 500},
    'Trinity': {2020: 30, 2030: 80, 2040: 180, 2050: 350, 2060: 350}
}

# Colors
GENESYS_COLORS = {
    'Go RES': '#1f77b4',
    'REPowerEU++': '#ff7f0e',
    'NECPEssentials': '#2ca02c',
    'Trinity': '#d62728'
}

# ============================================================================
# LOAD RESULTS
# ============================================================================

def load_all_results(results_dir):
    """Load summary_stats.yaml from all available scenarios."""
    results = {}

    pattern = os.path.join(results_dir, 'scenario_*/summary_stats.yaml')
    files = glob.glob(pattern)

    for filepath in sorted(files):
        scenario_name = os.path.basename(os.path.dirname(filepath))
        try:
            with open(filepath, 'r') as f:
                data = yaml.safe_load(f)
            results[scenario_name] = data
            print(f"  Loaded: {scenario_name}")
        except Exception as e:
            print(f"  Error loading {scenario_name}: {e}")

    return results


def calc_levelized_costs(data, scenario_name):
    """Calculate levelized costs from scenario data."""
    obj_value = float(data.get('objective_value', 0))
    tonnes_by_year = data.get('tonnes_by_year', {})
    fleet_by_year = data.get('fleet_by_year', {})
    energy_by_year = data.get('energy_by_year', {})

    # Total tonnes transported (sum BEV + ICEV for all years)
    total_tonnes = 0
    total_bev_tonnes = 0
    total_icev_tonnes = 0
    for year, tech_data in tonnes_by_year.items():
        if isinstance(tech_data, dict):
            bev_val = float(tech_data.get('BEV', 0))
            icev_val = float(tech_data.get('ICEV', 0))
            total_bev_tonnes += bev_val
            total_icev_tonnes += icev_val
            total_tonnes += bev_val + icev_val

    # Total fleet-years (fleet * 4 years per period)
    total_fleet_years = 0
    total_bev_fleet_years = 0
    total_icev_fleet_years = 0
    time_step = 4
    for year, tech_data in fleet_by_year.items():
        if isinstance(tech_data, dict):
            bev_fleet = float(tech_data.get('BEV', 0))
            icev_fleet = float(tech_data.get('ICEV', 0))
            total_bev_fleet_years += bev_fleet * time_step
            total_icev_fleet_years += icev_fleet * time_step
            total_fleet_years += (bev_fleet + icev_fleet) * time_step

    # Total energy (MWh)
    total_energy = sum(float(v) for v in energy_by_year.values()) if isinstance(energy_by_year, dict) else 0

    # Calculate levelized costs
    eur_per_tonne = obj_value / total_tonnes if total_tonnes > 0 else 0
    eur_per_vehicle_year = obj_value / total_fleet_years if total_fleet_years > 0 else 0
    eur_per_mwh = obj_value / total_energy if total_energy > 0 else 0

    # BEV share
    bev_share_tonnes = total_bev_tonnes / total_tonnes * 100 if total_tonnes > 0 else 0
    bev_share_fleet = total_bev_fleet_years / total_fleet_years * 100 if total_fleet_years > 0 else 0

    # Get scenario params
    genesys, markup, tech_mult = SCENARIO_PARAMS.get(scenario_name, ('Unknown', 0, 0))

    return {
        'scenario': scenario_name,
        'genesys': genesys,
        'markup': markup,
        'tech_mult': tech_mult,
        'objective_eur': obj_value,
        'total_tonnes': total_tonnes,
        'total_fleet_years': total_fleet_years,
        'total_energy_mwh': total_energy,
        'eur_per_tonne': eur_per_tonne,
        'eur_per_vehicle_year': eur_per_vehicle_year,
        'eur_per_mwh': eur_per_mwh,
        'bev_share_tonnes': bev_share_tonnes,
        'bev_share_fleet': bev_share_fleet,
        'carbon_price_2040': CARBON_PRICES.get(genesys, {}).get(2040, 0)
    }


# ============================================================================
# VISUALIZATION
# ============================================================================

def create_comparison_chart(df, output_dir):
    """Create comprehensive comparison charts."""

    fig, axes = plt.subplots(2, 3, figsize=(16, 10))

    # Sort by objective value for consistent ordering
    df_sorted = df.sort_values('objective_eur')

    # Color by GENeSYS scenario
    colors = [GENESYS_COLORS.get(g, 'gray') for g in df_sorted['genesys']]

    # ============================
    # Plot 1: Total System Cost (Objective Value)
    # ============================
    ax = axes[0, 0]
    bars = ax.barh(range(len(df_sorted)), df_sorted['objective_eur'] / 1e9, color=colors)
    ax.set_yticks(range(len(df_sorted)))
    ax.set_yticklabels([f"{s}\n({p[0][:6]}, {int(p[1]*100)}%, {p[2]}x)"
                        for s, p in zip(df_sorted['scenario'],
                                       zip(df_sorted['genesys'], df_sorted['markup'], df_sorted['tech_mult']))],
                      fontsize=8)
    ax.set_xlabel('Total System Cost (Billion EUR)')
    ax.set_title('Total System Cost by Scenario', fontweight='bold')
    ax.grid(axis='x', alpha=0.3)

    # ============================
    # Plot 2: EUR per Tonne
    # ============================
    ax = axes[0, 1]
    ax.barh(range(len(df_sorted)), df_sorted['eur_per_tonne'], color=colors)
    ax.set_yticks(range(len(df_sorted)))
    ax.set_yticklabels(df_sorted['scenario'], fontsize=8)
    ax.set_xlabel('EUR per Tonne')
    ax.set_title('Levelized Cost per Tonne Transported', fontweight='bold')
    ax.grid(axis='x', alpha=0.3)

    # ============================
    # Plot 3: EUR per Vehicle-Year
    # ============================
    ax = axes[0, 2]
    ax.barh(range(len(df_sorted)), df_sorted['eur_per_vehicle_year'] / 1000, color=colors)
    ax.set_yticks(range(len(df_sorted)))
    ax.set_yticklabels(df_sorted['scenario'], fontsize=8)
    ax.set_xlabel('EUR per Vehicle-Year (thousands)')
    ax.set_title('Levelized Cost per Vehicle-Year', fontweight='bold')
    ax.grid(axis='x', alpha=0.3)

    # ============================
    # Plot 4: BEV Share (%)
    # ============================
    ax = axes[1, 0]
    ax.barh(range(len(df_sorted)), df_sorted['bev_share_tonnes'], color=colors)
    ax.set_yticks(range(len(df_sorted)))
    ax.set_yticklabels(df_sorted['scenario'], fontsize=8)
    ax.set_xlabel('BEV Share (%)')
    ax.set_title('BEV Share of Total Tonnes Transported', fontweight='bold')
    ax.set_xlim(0, 100)
    ax.grid(axis='x', alpha=0.3)

    # ============================
    # Plot 5: Carbon Price vs Levelized Cost
    # ============================
    ax = axes[1, 1]
    for genesys in GENESYS_COLORS:
        mask = df['genesys'] == genesys
        if mask.any():
            ax.scatter(df.loc[mask, 'carbon_price_2040'],
                      df.loc[mask, 'eur_per_tonne'],
                      c=GENESYS_COLORS[genesys],
                      label=genesys, s=100, alpha=0.7)
    ax.set_xlabel('Carbon Price 2040 (EUR/tCO2)')
    ax.set_ylabel('EUR per Tonne')
    ax.set_title('Carbon Price vs Levelized Cost', fontweight='bold')
    ax.legend(loc='upper left', fontsize=9)
    ax.grid(True, alpha=0.3)

    # ============================
    # Plot 6: Tech Cost vs Levelized Cost
    # ============================
    ax = axes[1, 2]
    for genesys in GENESYS_COLORS:
        mask = df['genesys'] == genesys
        if mask.any():
            ax.scatter(df.loc[mask, 'tech_mult'],
                      df.loc[mask, 'eur_per_tonne'],
                      c=GENESYS_COLORS[genesys],
                      label=genesys, s=100, alpha=0.7)
    ax.set_xlabel('Tech Cost Multiplier')
    ax.set_ylabel('EUR per Tonne')
    ax.set_title('Tech Cost Multiplier vs Levelized Cost', fontweight='bold')
    ax.legend(loc='upper left', fontsize=9)
    ax.grid(True, alpha=0.3)

    # Add legend
    legend_elements = [Patch(facecolor=GENESYS_COLORS[g], label=g) for g in GENESYS_COLORS]
    fig.legend(handles=legend_elements, loc='upper center', ncol=4, fontsize=10,
               bbox_to_anchor=(0.5, 1.02))

    plt.tight_layout(rect=[0, 0, 1, 0.96])

    # Save
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'levelized_cost_comparison_all_scenarios.pdf')
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.savefig(output_path.replace('.pdf', '.png'), dpi=150, bbox_inches='tight')
    print(f"\nSaved: {output_path}")

    return fig


def create_carbon_price_comparison(df, output_dir):
    """Create carbon price impact visualization."""

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # ============================
    # Plot 1: Carbon price trajectories
    # ============================
    ax = axes[0]
    years = np.arange(2020, 2061, 4)

    for genesys, trajectory in CARBON_PRICES.items():
        # Interpolate
        cp_values = []
        sorted_years = sorted(trajectory.keys())
        for y in years:
            if y <= sorted_years[0]:
                cp_values.append(trajectory[sorted_years[0]])
            elif y >= sorted_years[-1]:
                cp_values.append(trajectory[sorted_years[-1]])
            else:
                for i in range(len(sorted_years) - 1):
                    if sorted_years[i] <= y <= sorted_years[i+1]:
                        t = (y - sorted_years[i]) / (sorted_years[i+1] - sorted_years[i])
                        val = trajectory[sorted_years[i]] * (1-t) + trajectory[sorted_years[i+1]] * t
                        cp_values.append(val)
                        break

        ax.plot(years, cp_values, 'o-', label=genesys, color=GENESYS_COLORS[genesys],
                linewidth=2, markersize=5)

    ax.set_xlabel('Year', fontsize=11)
    ax.set_ylabel('Carbon Price (EUR/tCO2)', fontsize=11)
    ax.set_title('Carbon Price Trajectories by GENeSYS Scenario', fontsize=12, fontweight='bold')
    ax.legend(loc='upper left', fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(2018, 2062)

    # ============================
    # Plot 2: Levelized cost by GENeSYS scenario (if data available)
    # ============================
    ax = axes[1]

    if len(df) > 0:
        # Group by GENeSYS scenario
        genesys_costs = df.groupby('genesys')['eur_per_tonne'].mean()

        x_pos = range(len(genesys_costs))
        bars = ax.bar(x_pos, genesys_costs.values,
                     color=[GENESYS_COLORS.get(g, 'gray') for g in genesys_costs.index])
        ax.set_xticks(x_pos)
        ax.set_xticklabels(genesys_costs.index, fontsize=10)
        ax.set_ylabel('EUR per Tonne (avg)', fontsize=11)
        ax.set_title('Average Levelized Cost by GENeSYS Scenario', fontsize=12, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)

        # Add value labels
        for bar, val in zip(bars, genesys_costs.values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                   f'{val:.1f}', ha='center', va='bottom', fontsize=10)
    else:
        ax.text(0.5, 0.5, 'No results available yet', ha='center', va='center',
               transform=ax.transAxes, fontsize=14)

    plt.tight_layout()

    # Save
    output_path = os.path.join(output_dir, 'carbon_price_vs_levelized_cost.pdf')
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.savefig(output_path.replace('.pdf', '.png'), dpi=150, bbox_inches='tight')
    print(f"Saved: {output_path}")

    return fig


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    # Paths
    base_dir = os.path.dirname(__file__)
    results_dir = os.path.join(base_dir, 'results', 'uncertainty_scenarios')
    output_dir = os.path.join(base_dir, 'figures')

    print("=" * 80)
    print("LEVELIZED COST COMPARISON - ALL UNCERTAINTY SCENARIOS")
    print("=" * 80)

    # Load results
    print("\nLoading available results...")
    results = load_all_results(results_dir)
    print(f"\nLoaded {len(results)} scenarios")

    if len(results) == 0:
        print("\nNo results found. Run SM_batch.jl first to generate scenario results.")
        exit(1)

    # Calculate levelized costs
    print("\nCalculating levelized costs...")
    cost_data = []
    for scenario, data in results.items():
        costs = calc_levelized_costs(data, scenario)
        cost_data.append(costs)

    df = pd.DataFrame(cost_data)

    # Print summary table
    print("\n" + "=" * 100)
    print("LEVELIZED COST SUMMARY")
    print("=" * 100)
    print(f"\n{'Scenario':<14} {'GENeSYS':<14} {'Markup':<8} {'Tech':<6} {'Obj (B EUR)':<12} {'EUR/t':<10} {'BEV%':<8}")
    print("-" * 80)

    for _, row in df.sort_values('scenario').iterrows():
        print(f"{row['scenario']:<14} {row['genesys']:<14} {int(row['markup']*100)}%{'':<5} {row['tech_mult']:<6.1f} "
              f"{row['objective_eur']/1e9:<12.2f} {row['eur_per_tonne']:<10.1f} {row['bev_share_tonnes']:<8.1f}")

    # Create visualizations
    print("\nCreating visualizations...")
    create_comparison_chart(df, output_dir)
    create_carbon_price_comparison(df, output_dir)

    # Save data to CSV
    csv_path = os.path.join(output_dir, 'levelized_cost_comparison_all_scenarios.csv')
    df.to_csv(csv_path, index=False)
    print(f"Saved: {csv_path}")

    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print(f"Results from {len(results)}/24 scenarios processed")
    print("Re-run this script after more scenarios complete to update the visualization.")
    print("=" * 80)
