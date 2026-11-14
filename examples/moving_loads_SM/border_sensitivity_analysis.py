"""
Border Sensitivity Analysis

Compares border sensitivity scenarios (uniform/reverse electricity/network costs in border regions)
against the baseline uncertainty scenarios.

Analyzes the DE-AT-IT Southern Border region electricity demand and electrification patterns.
"""

import os
import yaml
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

# Southern Border NUTS2 regions
SOUTHERN_BORDER_REGIONS = {
    'AT': ['AT31', 'AT32', 'AT33', 'AT34'],
    'IT': ['ITH1', 'ITH3'],
    'DE': ['DE14', 'DE21', 'DE22', 'DE27', 'DEF0']
}

ALL_BORDER_NUTS2 = ['AT31', 'AT32', 'AT33', 'AT34', 'ITH1', 'ITH3',
                    'DE14', 'DE21', 'DE22', 'DE27', 'DEF0']

# Variant types
VARIANTS = ['border_uni_elec', 'border_rev_elec', 'border_uni_network', 'border_rev_network']

VARIANT_LABELS = {
    'baseline': 'Baseline (var_var)',
    'border_uni_elec': 'Border Uniform Elec.',
    'border_rev_elec': 'Border Reversed Elec.',
    'border_uni_network': 'Border Uniform Network',
    'border_rev_network': 'Border Reversed Network'
}

VARIANT_COLORS = {
    'baseline': '#2E86AB',
    'border_uni_elec': '#A23B72',
    'border_rev_elec': '#F18F01',
    'border_uni_network': '#C73E1D',
    'border_rev_network': '#3B1F2B'
}


def load_yaml_file(filepath: str) -> dict:
    """Load a YAML file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def load_scenario_data(results_dir: str, input_dir: str) -> dict:
    """
    Load output and input data for a scenario.

    Returns dict with 'input_data' and 'output_data' keys.
    """
    data = {'input_data': {}, 'output_data': {}}

    # Load input data
    input_files = ['GeographicElement.yaml', 'Fuel.yaml', 'TechVehicle.yaml',
                   'Technology.yaml', 'Odpair.yaml', 'Path.yaml']
    for fname in input_files:
        fpath = os.path.join(input_dir, fname)
        if os.path.exists(fpath):
            key = fname.replace('.yaml', '')
            data['input_data'][key] = load_yaml_file(fpath)

    # Load output data (s_dict for energy supply)
    for fname in os.listdir(results_dir):
        if fname.endswith('_s_dict.yaml'):
            data['output_data']['s'] = load_yaml_file(os.path.join(results_dir, fname))
            break

    # Load f_dict for flow data
    for fname in os.listdir(results_dir):
        if fname.endswith('_f_dict.yaml'):
            data['output_data']['f'] = load_yaml_file(os.path.join(results_dir, fname))
            break

    return data


def calculate_border_electricity(data: dict, target_year: int,
                                  border_regions: dict = SOUTHERN_BORDER_REGIONS) -> dict:
    """
    Calculate electricity consumption in border regions by country.

    Returns: {country: electricity_GWh}
    """
    input_data = data['input_data']
    s_data = data['output_data'].get('s', {})

    if not s_data:
        return {c: 0.0 for c in border_regions.keys()}

    # Create NUTS2 lookup
    geo_elements = input_data.get('GeographicElement', [])
    nuts2_lookup = {}
    for geo in geo_elements:
        if geo.get('type') == 'node' and geo.get('nuts2_region'):
            nuts2_lookup[geo['id']] = geo['nuts2_region']

    # Identify electricity fuel IDs
    fuels = input_data.get('Fuel', [])
    electricity_fuel_ids = [f['id'] for f in fuels if 'electric' in f.get('name', '').lower()]

    SCALING_FACTOR = 1000

    # Aggregate by NUTS2
    electricity_by_nuts2 = defaultdict(float)

    for key_str, energy_value in s_data.items():
        try:
            key = eval(key_str) if isinstance(key_str, str) else key_str
            year, (_, _, _, geo_id), _, (fuel_id, _), _ = key

            energy = float(energy_value) if isinstance(energy_value, str) else energy_value

            if year != target_year or energy <= 0:
                continue
            if fuel_id not in electricity_fuel_ids:
                continue
            if geo_id not in nuts2_lookup:
                continue

            nuts2_code = nuts2_lookup[geo_id]
            electricity_by_nuts2[nuts2_code] += energy * SCALING_FACTOR
        except:
            continue

    # Aggregate by country
    result = {}
    for country, nuts2_codes in border_regions.items():
        total_kwh = sum(electricity_by_nuts2.get(code, 0.0) for code in nuts2_codes)
        result[country] = total_kwh / 1e6  # Convert to GWh

    return result


def calculate_electrification_rate(data: dict, target_year: int,
                                    border_regions: dict = SOUTHERN_BORDER_REGIONS) -> dict:
    """
    Calculate BEV electrification rate in border regions.

    Returns: {country: electrification_pct}
    """
    input_data = data['input_data']
    f_data = data['output_data'].get('f', {})

    if not f_data:
        return {c: 0.0 for c in border_regions.keys()}

    # Create lookups
    geo_elements = input_data.get('GeographicElement', [])
    nuts2_lookup = {geo['id']: geo.get('nuts2_region', '') for geo in geo_elements}

    odpairs = input_data.get('Odpair', [])
    odpair_origin = {od['id']: od['from'] for od in odpairs}

    # Get BEV tech vehicle IDs
    techvehicles = input_data.get('TechVehicle', [])
    technologies = input_data.get('Technology', [])
    fuels = input_data.get('Fuel', [])

    elec_fuel_ids = {f['id'] for f in fuels if 'electric' in f.get('name', '').lower()}
    elec_tech_ids = {t['id'] for t in technologies if t.get('fuel') in elec_fuel_ids}
    bev_tv_ids = {tv['id'] for tv in techvehicles if tv.get('technology') in elec_tech_ids}

    # Aggregate flows by country and technology type
    flows_by_country = {c: {'bev': 0.0, 'total': 0.0} for c in border_regions.keys()}

    for key_str, flow_value in f_data.items():
        try:
            key = eval(key_str) if isinstance(key_str, str) else key_str
            year, (_, odpair_id, _), (_, tv_id), _ = key

            flow = float(flow_value) if isinstance(flow_value, str) else flow_value

            if year != target_year or flow <= 0:
                continue

            # Get origin NUTS2
            origin_geo_id = odpair_origin.get(odpair_id)
            if origin_geo_id is None:
                continue
            origin_nuts2 = nuts2_lookup.get(origin_geo_id, '')

            # Check if in border region
            for country, nuts2_codes in border_regions.items():
                if origin_nuts2 in nuts2_codes:
                    flows_by_country[country]['total'] += flow
                    if tv_id in bev_tv_ids:
                        flows_by_country[country]['bev'] += flow
                    break
        except:
            continue

    # Calculate percentages
    result = {}
    for country, flows in flows_by_country.items():
        if flows['total'] > 0:
            result[country] = (flows['bev'] / flows['total']) * 100
        else:
            result[country] = 0.0

    return result


def load_all_scenarios(script_dir: Path, scenario_ids: List[str] = None) -> dict:
    """
    Load all baseline and border sensitivity scenarios.

    Returns: {
        'baseline': {scenario_id: data},
        'border_uni_elec': {scenario_id: data},
        ...
    }
    """
    if scenario_ids is None:
        scenario_ids = [f'scenario_{i:03d}' for i in range(24)]

    results = {
        'baseline': {},
        'border_uni_elec': {},
        'border_rev_elec': {},
        'border_uni_network': {},
        'border_rev_network': {}
    }

    # Load baseline scenarios
    baseline_results_dir = script_dir / 'results' / 'uncertainty_analysis'
    baseline_input_dir = script_dir / 'input_data' / 'uncertainty_scenarios'

    for scenario_id in scenario_ids:
        results_path = baseline_results_dir / scenario_id
        input_path = baseline_input_dir / scenario_id

        if results_path.exists() and input_path.exists():
            try:
                data = load_scenario_data(str(results_path), str(input_path))
                if data['output_data'].get('s'):
                    results['baseline'][scenario_id] = data
                    print(f"  Loaded baseline: {scenario_id}")
            except Exception as e:
                print(f"  Error loading baseline {scenario_id}: {e}")

    # Load border sensitivity scenarios
    bs_results_dir = script_dir / 'results' / 'bs'
    bs_input_dir = script_dir / 'input_data' / 'border_sensitivity'

    for variant in VARIANTS:
        for scenario_id in scenario_ids:
            folder_name = f'{scenario_id}_{variant}'
            results_path = bs_results_dir / folder_name
            input_path = bs_input_dir / folder_name

            if results_path.exists() and input_path.exists():
                try:
                    data = load_scenario_data(str(results_path), str(input_path))
                    if data['output_data'].get('s'):
                        results[variant][scenario_id] = data
                        print(f"  Loaded {variant}: {scenario_id}")
                except Exception as e:
                    print(f"  Error loading {variant} {scenario_id}: {e}")

    return results


def analyze_border_electricity(all_data: dict, target_year: int) -> pd.DataFrame:
    """
    Analyze border electricity for all scenarios and variants.

    Returns DataFrame with columns: scenario_id, variant, AT, IT, DE, total
    """
    rows = []

    for variant, scenarios in all_data.items():
        for scenario_id, data in scenarios.items():
            elec = calculate_border_electricity(data, target_year)
            rows.append({
                'scenario_id': scenario_id,
                'variant': variant,
                'AT': elec.get('AT', 0),
                'IT': elec.get('IT', 0),
                'DE': elec.get('DE', 0),
                'total': sum(elec.values())
            })

    return pd.DataFrame(rows)


def analyze_electrification_rate(all_data: dict, target_year: int) -> pd.DataFrame:
    """
    Analyze electrification rates for all scenarios and variants.
    """
    rows = []

    for variant, scenarios in all_data.items():
        for scenario_id, data in scenarios.items():
            rates = calculate_electrification_rate(data, target_year)
            rows.append({
                'scenario_id': scenario_id,
                'variant': variant,
                'AT': rates.get('AT', 0),
                'IT': rates.get('IT', 0),
                'DE': rates.get('DE', 0),
                'avg': np.mean(list(rates.values()))
            })

    return pd.DataFrame(rows)


def plot_border_electricity_comparison(df: pd.DataFrame, target_year: int,
                                        figsize: Tuple = (14, 10)):
    """
    Create comparison plots for border electricity consumption.
    """
    fig, axes = plt.subplots(2, 2, figsize=figsize)

    countries = ['AT', 'IT', 'DE']

    # Get variants that have data
    variants_with_data = df['variant'].unique()

    # Plot 1: Total electricity by variant (box plot)
    ax1 = axes[0, 0]
    variant_data = []
    variant_labels = []
    for variant in ['baseline'] + VARIANTS:
        if variant in variants_with_data:
            data = df[df['variant'] == variant]['total'].values
            if len(data) > 0:
                variant_data.append(data)
                variant_labels.append(VARIANT_LABELS.get(variant, variant))

    if variant_data:
        bp = ax1.boxplot(variant_data, labels=variant_labels, patch_artist=True)
        colors = [VARIANT_COLORS.get(v, 'gray') for v in ['baseline'] + VARIANTS if v in variants_with_data]
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)

    ax1.set_ylabel('Total Electricity (GWh)')
    ax1.set_title(f'Border Region Total Electricity - {target_year}')
    ax1.tick_params(axis='x', rotation=45)
    ax1.grid(True, alpha=0.3)

    # Plot 2: By country grouped bar
    ax2 = axes[0, 1]
    x = np.arange(len(countries))
    width = 0.15

    for i, variant in enumerate(['baseline'] + VARIANTS):
        if variant not in variants_with_data:
            continue
        variant_df = df[df['variant'] == variant]
        means = [variant_df[c].mean() for c in countries]
        offset = (i - 2) * width
        bars = ax2.bar(x + offset, means, width,
                       label=VARIANT_LABELS.get(variant, variant),
                       color=VARIANT_COLORS.get(variant, 'gray'), alpha=0.8)

    ax2.set_ylabel('Electricity (GWh)')
    ax2.set_title(f'Electricity by Country - {target_year}')
    ax2.set_xticks(x)
    ax2.set_xticklabels(countries)
    ax2.legend(loc='upper right', fontsize=8)
    ax2.grid(True, alpha=0.3, axis='y')

    # Plot 3: Delta from baseline (percentage)
    ax3 = axes[1, 0]

    if 'baseline' in variants_with_data:
        baseline_means = df[df['variant'] == 'baseline'].groupby('scenario_id')['total'].mean()

        for i, variant in enumerate(VARIANTS):
            if variant not in variants_with_data:
                continue
            variant_df = df[df['variant'] == variant]

            deltas = []
            for scenario_id in variant_df['scenario_id'].unique():
                if scenario_id in baseline_means.index:
                    baseline_val = baseline_means[scenario_id]
                    variant_val = variant_df[variant_df['scenario_id'] == scenario_id]['total'].values
                    if len(variant_val) > 0 and baseline_val > 0:
                        delta_pct = ((variant_val[0] - baseline_val) / baseline_val) * 100
                        deltas.append(delta_pct)

            if deltas:
                ax3.bar(i, np.mean(deltas),
                       color=VARIANT_COLORS.get(variant, 'gray'), alpha=0.8,
                       label=VARIANT_LABELS.get(variant, variant))
                ax3.errorbar(i, np.mean(deltas), yerr=np.std(deltas),
                            color='black', capsize=5)

    ax3.axhline(y=0, color='black', linestyle='--', linewidth=0.5)
    ax3.set_ylabel('Change from Baseline (%)')
    ax3.set_title(f'Electricity Change vs Baseline - {target_year}')
    ax3.set_xticks(range(len(VARIANTS)))
    ax3.set_xticklabels([VARIANT_LABELS[v].replace(' ', '\n') for v in VARIANTS], fontsize=8)
    ax3.grid(True, alpha=0.3, axis='y')

    # Plot 4: Distribution comparison
    ax4 = axes[1, 1]

    for variant in ['baseline'] + VARIANTS:
        if variant not in variants_with_data:
            continue
        data = df[df['variant'] == variant]['total'].values
        if len(data) > 0:
            ax4.hist(data, bins=15, alpha=0.5,
                    label=VARIANT_LABELS.get(variant, variant),
                    color=VARIANT_COLORS.get(variant, 'gray'))

    ax4.set_xlabel('Total Electricity (GWh)')
    ax4.set_ylabel('Frequency')
    ax4.set_title(f'Distribution of Border Electricity - {target_year}')
    ax4.legend(fontsize=8)
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def create_summary_table(df: pd.DataFrame) -> pd.DataFrame:
    """Create summary statistics table."""
    summary_rows = []

    for variant in ['baseline'] + VARIANTS:
        variant_df = df[df['variant'] == variant]
        if len(variant_df) == 0:
            continue

        summary_rows.append({
            'Variant': VARIANT_LABELS.get(variant, variant),
            'N': len(variant_df),
            'AT Mean (GWh)': variant_df['AT'].mean(),
            'AT Std': variant_df['AT'].std(),
            'IT Mean (GWh)': variant_df['IT'].mean(),
            'IT Std': variant_df['IT'].std(),
            'DE Mean (GWh)': variant_df['DE'].mean(),
            'DE Std': variant_df['DE'].std(),
            'Total Mean (GWh)': variant_df['total'].mean(),
            'Total Std': variant_df['total'].std()
        })

    return pd.DataFrame(summary_rows)


def run_analysis(script_dir: Path = None, years: List[int] = [2032, 2040, 2052],
                 save_figures: bool = True):
    """
    Run complete border sensitivity analysis.
    """
    if script_dir is None:
        script_dir = Path(__file__).parent

    print("=" * 80)
    print("BORDER SENSITIVITY ANALYSIS")
    print("Comparing baseline vs border region price/cost alterations")
    print("=" * 80)
    print(f"\nSouthern Border Regions (DE-AT-IT):")
    for country, regions in SOUTHERN_BORDER_REGIONS.items():
        print(f"  {country}: {', '.join(regions)}")

    # Load all scenarios
    print("\nLoading scenarios...")
    all_data = load_all_scenarios(script_dir)

    # Count loaded scenarios
    for variant, scenarios in all_data.items():
        print(f"  {variant}: {len(scenarios)} scenarios")

    results = {}

    for year in years:
        print(f"\n{'=' * 60}")
        print(f"ANALYZING YEAR {year}")
        print('=' * 60)

        # Analyze electricity
        df_elec = analyze_border_electricity(all_data, year)

        if len(df_elec) > 0:
            # Create summary table
            summary = create_summary_table(df_elec)
            print(f"\nSummary Statistics (Year {year}):")
            print(summary.to_string(index=False))

            # Create plots
            fig = plot_border_electricity_comparison(df_elec, year)

            if save_figures:
                fig_path = script_dir / 'figures' / f'border_sensitivity_electricity_{year}.pdf'
                fig_path.parent.mkdir(exist_ok=True)
                fig.savefig(fig_path, bbox_inches='tight', dpi=150)
                print(f"\nSaved figure: {fig_path}")

            plt.show()

            results[year] = {
                'df_electricity': df_elec,
                'summary': summary
            }
        else:
            print(f"  No data available for year {year}")

    return results


# For use in Jupyter notebook
def analyze_border_sensitivity_notebook(loaded_runs: dict = None,
                                         script_dir: str = None,
                                         years: List[int] = [2032, 2040]):
    """
    Notebook-friendly version that can use pre-loaded data or load fresh.
    """
    if script_dir is None:
        script_dir = Path(__file__).parent
    else:
        script_dir = Path(script_dir)

    return run_analysis(script_dir, years, save_figures=True)


if __name__ == "__main__":
    script_dir = Path(__file__).parent
    results = run_analysis(script_dir, years=[2032, 2040, 2052])
