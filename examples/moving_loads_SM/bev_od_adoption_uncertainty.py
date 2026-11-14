"""
BEV Adoption by Origin-Destination Pathway for Uncertainty Analysis

This module analyzes BEV adoption patterns across OD pathways,
grouped by GENeSYS-MOD scenarios.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple

plt.rcParams.update(plt.rcParamsDefault)
plt.rcParams.update({
    "text.usetex": False,  # Disable LaTeX
    "font.family": "serif",
    "font.serif": ["Palatino Linotype", "DejaVu Serif", "Times New Roman"],
    "mathtext.fontset": "cm",  # Computer Modern for math
    "font.size": 20,
    "axes.labelsize": 20
})
def load_cases_metadata(base_path: Path) -> Dict:
    """Load the cases.json metadata file."""
    cases_path = base_path / "input_data" / "uncertainty_scenarios" / "cases.json"
    with open(cases_path, 'r') as f:
        return json.load(f)


def load_yaml_file(filepath: Path) -> Dict:
    """Load a YAML file."""
    with open(filepath, 'r') as f:
        return yaml.safe_load(f)


def find_latest_result_file(scenario_folder: Path, variable: str) -> Optional[Path]:
    """Find the latest result file for a given variable."""
    pattern = f"*_{variable}_dict.yaml"
    files = list(scenario_folder.glob(pattern))
    if not files:
        return None
    return max(files, key=lambda x: x.stat().st_mtime)


def load_odpair_mapping(base_path: Path) -> Tuple[Dict, Dict]:
    """
    Load odpair and geographic element mappings from base case.

    Returns:
        Tuple of (odpair_map, geoid2country)
        - odpair_map: {odpair_id: (origin_geoid, dest_geoid)}
        - geoid2country: {geoid: country_code}
    """
    # Load from scenario_000 (or any scenario - they all share the same structure)
    scenario_path = base_path / "input_data" / "uncertainty_scenarios" / "scenario_000"

    odpair_map = {}
    geoid2country = {}

    # Load Odpair
    odpair_file = scenario_path / "Odpair.yaml"
    if odpair_file.exists():
        odpair_data = load_yaml_file(odpair_file)
        if isinstance(odpair_data, list):
            for entry in odpair_data:
                if isinstance(entry, dict):
                    odpair_id = entry.get('id')
                    origin = entry.get('from')
                    dest = entry.get('to')
                    if odpair_id is not None and origin is not None and dest is not None:
                        odpair_map[int(odpair_id)] = (int(origin), int(dest))

    # Load GeographicElement
    geo_file = scenario_path / "GeographicElement.yaml"
    if geo_file.exists():
        geo_data = load_yaml_file(geo_file)
        if isinstance(geo_data, list):
            for entry in geo_data:
                if isinstance(entry, dict):
                    geo_id = entry.get('id')
                    country = entry.get('country')
                    if geo_id is not None and country is not None:
                        geoid2country[int(geo_id)] = str(country)

    return odpair_map, geoid2country


def extract_bev_by_od(h_dict: Dict, odpair_map: Dict, geoid2country: Dict,
                      target_year: int = 2040, bev_tech_id: int = 1) -> pd.DataFrame:
    """
    Extract BEV counts by OD pair for a specific year.

    Args:
        h_dict: Vehicle fleet dictionary {(year, odpair_id, tech_id, generation): count}
        odpair_map: Mapping of odpair_id to (origin, dest) geo IDs
        geoid2country: Mapping of geo ID to country code
        target_year: Year to analyze
        bev_tech_id: Tech ID for BEV (default: 1)

    Returns:
        DataFrame with columns: origin_country, dest_country, bev_vehicles
    """
    od_vehicles = {}

    for key, value in h_dict.items():
        # Convert value to float if string
        if isinstance(value, str):
            value = float(value)

        if value < 0.01:
            continue

        # Parse key
        if isinstance(key, str):
            key_clean = key.strip('()').split(',')
            year = int(key_clean[0].strip())
            odpair_id = int(key_clean[1].strip())
            tech_id = int(key_clean[2].strip())
        else:
            year, odpair_id, tech_id, _ = key

        # Filter by year and tech
        if year != target_year or tech_id != bev_tech_id:
            continue

        # Get OD countries
        if odpair_id not in odpair_map:
            continue

        origin_geoid, dest_geoid = odpair_map[odpair_id]
        origin_country = geoid2country.get(origin_geoid)
        dest_country = geoid2country.get(dest_geoid)

        if origin_country is None or dest_country is None:
            continue

        # Aggregate
        od_key = (origin_country, dest_country)
        od_vehicles[od_key] = od_vehicles.get(od_key, 0.0) + value

    # Convert to DataFrame
    data = [{'origin_country': k[0], 'dest_country': k[1], 'bev_vehicles': v}
            for k, v in od_vehicles.items()]

    return pd.DataFrame(data)


def load_all_scenario_results(base_path: Path, cases_metadata: Dict) -> Dict:
    """
    Load h_dict results for all scenarios.

    Returns:
        Dict: {scenario_id: h_dict}
    """
    results = {}
    results_path = base_path / "results" / "uncertainty_analysis"

    for case in cases_metadata['cases']:
        scenario_id = case['case_id']
        scenario_folder = results_path / f"scenario_{scenario_id:03d}"

        if not scenario_folder.exists():
            print(f"Warning: Scenario folder not found: {scenario_folder}")
            continue

        h_file = find_latest_result_file(scenario_folder, 'h')
        if h_file:
            results[scenario_id] = load_yaml_file(h_file)
        else:
            print(f"Warning: No h_dict found for scenario {scenario_id}")

    return results


def create_bev_od_matrix_by_genesys(base_path: Path, target_year: int = 2040,
                                     preloaded_results: Dict = None,
                                     cases_metadata: Dict = None) -> Dict[str, pd.DataFrame]:
    """
    Create BEV country-to-country matrices for each GENeSYS scenario (averaged).

    Args:
        base_path: Path to moving_loads_SM folder
        target_year: Year to analyze
        preloaded_results: Optional pre-loaded results dict {scenario_id: {'h': h_dict, ...}}
        cases_metadata: Optional pre-loaded cases metadata

    Returns:
        Dict: {genesys_scenario: country_matrix_df}
    """
    print("=" * 80)
    print(f"BEV OD ADOPTION BY GENeSYS SCENARIO (Year: {target_year})")
    print("=" * 80)

    # Load metadata if not provided
    if cases_metadata is None:
        cases_metadata = load_cases_metadata(base_path)

    # Load mappings
    odpair_map, geoid2country = load_odpair_mapping(base_path)
    print(f"Loaded {len(odpair_map)} OD pairs, {len(geoid2country)} geographic elements")

    # Use preloaded results or load them
    if preloaded_results is not None:
        # Convert from notebook format {scenario_id: {'h': h_dict}} to just h_dicts
        all_results = {}
        for sid, data in preloaded_results.items():
            if isinstance(data, dict) and 'h' in data:
                all_results[sid] = data['h']
            else:
                all_results[sid] = data
        print(f"Using {len(all_results)} pre-loaded scenario results")
    else:
        loaded = load_all_scenario_results(base_path, cases_metadata)
        all_results = loaded
        print(f"Loaded {len(all_results)} scenario results")

    # Group scenarios by GENeSYS scenario
    genesys_scenarios = {}
    for case in cases_metadata['cases']:
        genesys = case['genesys_scenario']
        if genesys not in genesys_scenarios:
            genesys_scenarios[genesys] = []
        genesys_scenarios[genesys].append(case['case_id'])

    print(f"\nGENeSYS scenarios: {list(genesys_scenarios.keys())}")

    # Process each GENeSYS scenario
    matrices = {}

    for genesys_name, scenario_ids in genesys_scenarios.items():
        print(f"\nProcessing {genesys_name} ({len(scenario_ids)} scenarios)...")

        # Collect OD data from all scenarios in this group
        all_od_data = []

        for sid in scenario_ids:
            if sid not in all_results:
                continue

            od_df = extract_bev_by_od(all_results[sid], odpair_map, geoid2country, target_year)
            if not od_df.empty:
                od_df['scenario_id'] = sid
                all_od_data.append(od_df)

        if not all_od_data:
            print(f"  No data for {genesys_name}")
            continue

        # Combine and average
        combined = pd.concat(all_od_data, ignore_index=True)
        averaged = combined.groupby(['origin_country', 'dest_country'])['bev_vehicles'].mean().reset_index()

        # Create matrix
        countries = sorted(set(averaged['origin_country']) | set(averaged['dest_country']))
        matrix = pd.DataFrame(0.0, index=countries, columns=countries)

        for _, row in averaged.iterrows():
            matrix.loc[row['origin_country'], row['dest_country']] = row['bev_vehicles']

        matrices[genesys_name] = matrix
        print(f"  Matrix shape: {matrix.shape}, Total BEVs: {matrix.sum().sum():.0f}")

    return matrices


def create_bev_od_timeseries_by_genesys(base_path: Path,
                                         years: List[int] = None,
                                         preloaded_results: Dict = None,
                                         cases_metadata: Dict = None) -> pd.DataFrame:
    """
    Create time series of total BEV adoption by GENeSYS scenario.

    Args:
        base_path: Path to moving_loads_SM folder
        years: List of years to analyze (default: all available)
        preloaded_results: Optional pre-loaded results dict {scenario_id: {'h': h_dict, ...}}
        cases_metadata: Optional pre-loaded cases metadata

    Returns:
        DataFrame with columns: year, genesys_scenario, total_bevs, mean_bevs, std_bevs
    """
    if years is None:
        years = list(range(2020, 2061, 4))

    print("=" * 80)
    print("BEV ADOPTION TIME SERIES BY GENeSYS SCENARIO")
    print("=" * 80)

    # Load metadata if not provided
    if cases_metadata is None:
        cases_metadata = load_cases_metadata(base_path)

    # Load mappings
    odpair_map, geoid2country = load_odpair_mapping(base_path)

    # Use preloaded results or load them
    if preloaded_results is not None:
        all_results = {}
        for sid, data in preloaded_results.items():
            if isinstance(data, dict) and 'h' in data:
                all_results[sid] = data['h']
            else:
                all_results[sid] = data
        print(f"Using {len(all_results)} pre-loaded scenario results")
    else:
        all_results = load_all_scenario_results(base_path, cases_metadata)
        print(f"Loaded {len(all_results)} scenario results")

    # Group scenarios by GENeSYS
    genesys_scenarios = {}
    for case in cases_metadata['cases']:
        genesys = case['genesys_scenario']
        if genesys not in genesys_scenarios:
            genesys_scenarios[genesys] = []
        genesys_scenarios[genesys].append(case['case_id'])

    # Collect data
    timeseries_data = []

    for year in years:
        print(f"Processing year {year}...")

        for genesys_name, scenario_ids in genesys_scenarios.items():
            year_totals = []

            for sid in scenario_ids:
                if sid not in all_results:
                    continue

                od_df = extract_bev_by_od(all_results[sid], odpair_map, geoid2country, year)
                total_bevs = od_df['bev_vehicles'].sum() if not od_df.empty else 0
                year_totals.append(total_bevs)

            if year_totals:
                timeseries_data.append({
                    'year': year,
                    'genesys_scenario': genesys_name,
                    'mean_bevs': np.mean(year_totals),
                    'std_bevs': np.std(year_totals),
                    'min_bevs': np.min(year_totals),
                    'max_bevs': np.max(year_totals)
                })

    return pd.DataFrame(timeseries_data)


def plot_bev_od_matrices_comparison(matrices: Dict[str, pd.DataFrame],
                                     figsize: Tuple[int, int] = (16, 12),
                                     save_path: Optional[Path] = None):
    """
    Plot heatmaps comparing BEV OD matrices across GENeSYS scenarios.
    """
    n_scenarios = len(matrices)
    fig, axes = plt.subplots(2, 2, figsize=figsize)
    axes = axes.flatten()

    scenario_order = ['Go RES v1.2', 'NECPEssentials v1.2', 'REPowerEU++ v1.2', 'Trinity v1.2']

    for idx, scenario_name in enumerate(scenario_order):
        if scenario_name not in matrices:
            continue

        ax = axes[idx]
        matrix = matrices[scenario_name]

        # Plot heatmap
        im = ax.imshow(matrix.values, cmap='Blues', aspect='auto')

        # Labels
        ax.set_xticks(range(len(matrix.columns)))
        ax.set_xticklabels(matrix.columns, rotation=45, ha='right', fontsize=12)
        ax.set_yticks(range(len(matrix.index)))
        ax.set_yticklabels(matrix.index, fontsize=12)

        ax.set_xlabel('Destination Country')
        ax.set_ylabel('Origin Country')
        ax.set_title(f'{scenario_name.replace(" v1.2", "")}\nTotal: {matrix.sum().sum():.0f} BEVs')

        plt.colorbar(im, ax=ax, label='BEV Vehicles')

    plt.suptitle('BEV Fleet by Origin-Destination (Averaged within GENeSYS Scenario)',
                 fontsize=16, y=1.02)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=150)
        print(f"Saved to {save_path}")

    plt.show()


def plot_bev_od_matrices_with_deltas(matrices: Dict[str, pd.DataFrame],
                                      reference_scenario: str = 'Go RES v1.2',
                                      figsize: Tuple[int, int] = (18, 10),
                                      save_path: Optional[Path] = None):
    """
    Plot BEV OD matrices showing absolute values and deltas from reference scenario.

    Args:
        matrices: Dict of {scenario_name: matrix_df}
        reference_scenario: Scenario to use as baseline for deltas
        figsize: Figure size
        save_path: Path to save figure
    """
    scenario_order = ['Go RES v1.2', 'NECPEssentials v1.2', 'REPowerEU++ v1.2', 'Trinity v1.2']
    other_scenarios = [s for s in scenario_order if s != reference_scenario and s in matrices]

    if reference_scenario not in matrices:
        print(f"Reference scenario '{reference_scenario}' not found!")
        return

    ref_matrix = matrices[reference_scenario]

    # Calculate global color scale for absolute values (top row)
    abs_vmax = ref_matrix.values.max()
    for scenario_name in other_scenarios:
        abs_vmax = max(abs_vmax, matrices[scenario_name].values.max())

    # Calculate global color scale for deltas (bottom row)
    delta_vmax = 0
    for scenario_name in other_scenarios:
        delta = matrices[scenario_name] - ref_matrix
        delta_vmax = max(delta_vmax, abs(delta.values.min()), abs(delta.values.max()))

    # Create figure: top row = absolute values, bottom row = deltas from reference
    fig, axes = plt.subplots(2, len(other_scenarios) + 1, figsize=figsize)

    # Adjust subplot layout to make room for colorbars on the right
    fig.subplots_adjust(right=0.88, wspace=0.3, hspace=0.35)

    # Top row: Absolute values
    # First column: reference scenario
    ax = axes[0, 0]
    im_abs = ax.imshow(ref_matrix.values, cmap='Blues', aspect='auto', vmin=0, vmax=abs_vmax)
    ax.set_xticks(range(len(ref_matrix.columns)))
    ax.set_xticklabels(ref_matrix.columns, rotation=45, ha='right', fontsize=16)
    ax.set_yticks(range(len(ref_matrix.index)))
    ax.set_yticklabels(ref_matrix.index, fontsize=16)
    ax.set_title(f'{reference_scenario.replace(" v1.2", "")} (Reference)\nTotal: {ref_matrix.sum().sum():.0f}', fontsize=16)

    # Other scenarios (top row)
    for idx, scenario_name in enumerate(other_scenarios):
        ax = axes[0, idx + 1]
        matrix = matrices[scenario_name]
        im_abs = ax.imshow(matrix.values, cmap='Blues', aspect='auto', vmin=0, vmax=abs_vmax)
        ax.set_xticks(range(len(matrix.columns)))
        ax.set_xticklabels(matrix.columns, rotation=45, ha='right', fontsize=16)
        ax.set_yticks(range(len(matrix.index)))
        ax.set_yticklabels(matrix.index, fontsize=16)
        ax.set_title(f'{scenario_name.replace(" v1.2", "")}\nTotal: {matrix.sum().sum():.0f}', fontsize=16)

    # Add single colorbar for top row (in dedicated space on right)
    cbar_ax_top = fig.add_axes([0.90, 0.55, 0.02, 0.35])  # [left, bottom, width, height]
    cbar_abs = fig.colorbar(im_abs, cax=cbar_ax_top)
    cbar_abs.set_label('BEV Vehicles', fontsize=16)

    # Bottom row: Deltas
    # First column: empty or summary
    ax = axes[1, 0]
    ax.text(0.5, 0.5, f'Reference:\n{reference_scenario.replace(" v1.2", "")}',
            ha='center', va='center', fontsize=12, transform=ax.transAxes)
    ax.axis('off')

    # Delta heatmaps with consistent scale
    im_delta = None
    for idx, scenario_name in enumerate(other_scenarios):
        ax = axes[1, idx + 1]
        matrix = matrices[scenario_name]

        # Calculate delta (other - reference)
        delta = matrix - ref_matrix

        # Use diverging colormap for deltas with global scale
        im_delta = ax.imshow(delta.values, cmap='RdBu_r', aspect='auto', vmin=-delta_vmax, vmax=delta_vmax)

        ax.set_xticks(range(len(delta.columns)))
        ax.set_xticklabels(delta.columns, rotation=45, ha='right', fontsize=16)
        ax.set_yticks(range(len(delta.index)))
        ax.set_yticklabels(delta.index, fontsize=16)

        total_delta = delta.sum().sum()
        sign = '+' if total_delta >= 0 else ''
        scenario_short = scenario_name.replace(" v1.2", "")
        ref_short = reference_scenario.replace(" v1.2", "")
        ax.set_title(f'{scenario_short} - {ref_short}\nNet: {sign}{total_delta:.0f}', fontsize=16)
    # Add single colorbar for bottom row (in dedicated space on right)
    if im_delta is not None:
        cbar_ax_bot = fig.add_axes([0.90, 0.10, 0.02, 0.35])  # [left, bottom, width, height]
        cbar_delta = fig.colorbar(im_delta, cax=cbar_ax_bot)
        cbar_delta.set_label('Delta BEV Vehicles', fontsize=16)

    plt.suptitle('BEV Fleet by OD: Absolute Values (top) and Differences from Reference (bottom)',
                 fontsize=16, y=0.98)

    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=150)
        print(f"Saved to {save_path}")

    plt.show()

    # Print summary table
    print("\n=== Scenario Comparison Summary ===")
    print(f"Reference: {reference_scenario}")
    ref_total = ref_matrix.sum().sum()
    print(f"  Total BEVs: {ref_total:.0f}")
    for scenario_name in other_scenarios:
        other_total = matrices[scenario_name].sum().sum()
        diff = other_total - ref_total
        pct = (diff / ref_total) * 100 if ref_total > 0 else 0
        sign = '+' if diff >= 0 else ''
        print(f"\n{scenario_name}:")
        print(f"  Total BEVs: {other_total:.0f}")
        print(f"  Difference: {sign}{diff:.0f} ({sign}{pct:.1f}%)")


def create_bev_od_matrix_by_scenario_params(base_path: Path,
                                             genesys_scenario: str = 'Go RES v1.2',
                                             target_year: int = 2040,
                                             preloaded_results: Dict = None,
                                             cases_metadata: Dict = None) -> Dict[str, pd.DataFrame]:
    """
    Create BEV OD matrices for each combination of markup and tech cost within one GENeSYS scenario.

    Args:
        base_path: Path to moving_loads_SM folder
        genesys_scenario: GENeSYS scenario to analyze
        target_year: Year to analyze
        preloaded_results: Optional pre-loaded results
        cases_metadata: Optional pre-loaded cases metadata

    Returns:
        Dict: {param_label: matrix_df} where param_label is like "markup=15%, tech=0.7"
    """
    # Load metadata if not provided
    if cases_metadata is None:
        cases_metadata = load_cases_metadata(base_path)

    # Load mappings
    odpair_map, geoid2country = load_odpair_mapping(base_path)

    # Use preloaded results or load them
    if preloaded_results is not None:
        all_results = {}
        for sid, data in preloaded_results.items():
            if isinstance(data, dict) and 'h' in data:
                all_results[sid] = data['h']
            else:
                all_results[sid] = data
    else:
        all_results = load_all_scenario_results(base_path, cases_metadata)

    # Filter cases for the selected GENeSYS scenario
    selected_cases = [c for c in cases_metadata['cases'] if c['genesys_scenario'] == genesys_scenario]

    matrices = {}
    for case in selected_cases:
        sid = case['case_id']
        markup = case['charging_markup']
        tech_cost = case['tech_cost_multiplier']

        if sid not in all_results:
            continue

        od_df = extract_bev_by_od(all_results[sid], odpair_map, geoid2country, target_year)

        if od_df.empty:
            continue

        # Create matrix
        countries = sorted(set(od_df['origin_country']) | set(od_df['dest_country']))
        matrix = pd.DataFrame(0.0, index=countries, columns=countries)

        for _, row in od_df.iterrows():
            matrix.loc[row['origin_country'], row['dest_country']] = row['bev_vehicles']

        label = f"markup={int(markup*100)}%, tech={tech_cost}"
        matrices[label] = matrix

    return matrices


def plot_bev_od_by_markup_and_tech(base_path: Path,
                                    genesys_scenario: str = 'Go RES v1.2',
                                    target_year: int = 2040,
                                    preloaded_results: Dict = None,
                                    cases_metadata: Dict = None,
                                    figsize: Tuple[int, int] = (16, 10),
                                    save_path: Optional[Path] = None):
    """
    Plot BEV OD matrices showing variation by markup (rows) and tech cost (columns)
    for a single GENeSYS scenario.

    Layout:
        Columns: tech cost (0.7, 1.0, 1.3)
        Rows: markup (15%, 30%)
    """
    # Disable LaTeX rendering
    plt.rcParams['text.usetex'] = False

    matrices = create_bev_od_matrix_by_scenario_params(
        base_path, genesys_scenario, target_year, preloaded_results, cases_metadata
    )

    if not matrices:
        print(f"No data found for {genesys_scenario}")
        return

    # Define grid: rows = markup, cols = tech cost
    markups = [0.15, 0.30]
    tech_costs = [0.7, 1.0, 1.3]

    fig, axes = plt.subplots(len(markups), len(tech_costs), figsize=figsize)

    # Find global min/max for consistent color scale
    all_values = []
    for m in matrices.values():
        all_values.extend(m.values.flatten())
    vmax = max(all_values) if all_values else 1

    for i, markup in enumerate(markups):
        for j, tech in enumerate(tech_costs):
            ax = axes[i, j]
            label = f"markup={int(markup*100)}%, tech={tech}"

            if label not in matrices:
                ax.set_title(f'{label}\n(no data)')
                ax.axis('off')
                continue

            matrix = matrices[label]

            im = ax.imshow(matrix.values, cmap='Blues', aspect='auto', vmin=0, vmax=vmax)

            ax.set_xticks(range(len(matrix.columns)))
            ax.set_xticklabels(matrix.columns, rotation=45, ha='right', fontsize=7)
            ax.set_yticks(range(len(matrix.index)))
            ax.set_yticklabels(matrix.index, fontsize=7)

            total = matrix.sum().sum()
            ax.set_title(f'Markup: {int(markup*100)}%, Tech cost: {tech}x\nTotal: {total:.0f} BEVs', fontsize=10)

            if j == 0:
                ax.set_ylabel('Origin Country', fontsize=9)
            if i == len(markups) - 1:
                ax.set_xlabel('Dest Country', fontsize=9)

    # Add colorbar
    cbar = fig.colorbar(im, ax=axes, shrink=0.6, label='BEV Vehicles')

    plt.suptitle(f'BEV Fleet by OD for {genesys_scenario.replace(" v1.2", "")} ({target_year})\n'
                 f'Rows: Charging markup | Columns: Technology cost multiplier',
                 fontsize=14, y=1.02)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=150)
        print(f"Saved to {save_path}")

    plt.show()

    # Print summary
    print(f"\n=== {genesys_scenario} - Summary by Parameters ===")
    for label, matrix in sorted(matrices.items()):
        print(f"  {label}: {matrix.sum().sum():.0f} BEVs")

    return matrices


def plot_bev_totals_by_markup_and_tech(base_path: Path,
                                        target_year: int = 2040,
                                        preloaded_results: Dict = None,
                                        cases_metadata: Dict = None,
                                        figsize: Tuple[int, int] = (12, 8),
                                        save_path: Optional[Path] = None):
    """
    Plot bar chart showing total BEVs by markup and tech cost for all GENeSYS scenarios.
    """
    plt.rcParams['text.usetex'] = False

    # Load metadata if not provided
    if cases_metadata is None:
        cases_metadata = load_cases_metadata(base_path)

    odpair_map, geoid2country = load_odpair_mapping(base_path)

    # Use preloaded results or load them
    if preloaded_results is not None:
        all_results = {}
        for sid, data in preloaded_results.items():
            if isinstance(data, dict) and 'h' in data:
                all_results[sid] = data['h']
            else:
                all_results[sid] = data
    else:
        all_results = load_all_scenario_results(base_path, cases_metadata)

    # Collect totals
    data_rows = []
    for case in cases_metadata['cases']:
        sid = case['case_id']
        if sid not in all_results:
            continue

        od_df = extract_bev_by_od(all_results[sid], odpair_map, geoid2country, target_year)
        total_bevs = od_df['bev_vehicles'].sum() if not od_df.empty else 0

        data_rows.append({
            'genesys': case['genesys_scenario'].replace(' v1.2', ''),
            'markup': f"{int(case['charging_markup']*100)}%",
            'tech_cost': case['tech_cost_multiplier'],
            'total_bevs': total_bevs
        })

    df = pd.DataFrame(data_rows)

    # Create grouped bar chart
    fig, axes = plt.subplots(1, 2, figsize=figsize)

    # Plot 1: By markup (grouped by GENeSYS)
    ax1 = axes[0]
    markup_pivot = df.groupby(['genesys', 'markup'])['total_bevs'].mean().unstack()
    markup_pivot.plot(kind='bar', ax=ax1, color=['#16a085', '#d35400'])
    ax1.set_xlabel('GENeSYS Scenario', fontsize=11)
    ax1.set_ylabel('Total BEV Vehicles', fontsize=11)
    ax1.set_title(f'BEV Fleet by Charging Markup ({target_year})', fontsize=12)
    ax1.legend(title='Markup')
    ax1.tick_params(axis='x', rotation=45)
    ax1.grid(True, alpha=0.3, axis='y')

    # Plot 2: By tech cost (grouped by GENeSYS)
    ax2 = axes[1]
    tech_pivot = df.groupby(['genesys', 'tech_cost'])['total_bevs'].mean().unstack()
    tech_pivot.plot(kind='bar', ax=ax2, color=['#27ae60', '#2980b9', '#c0392b'])
    ax2.set_xlabel('GENeSYS Scenario', fontsize=11)
    ax2.set_ylabel('Total BEV Vehicles', fontsize=11)
    ax2.set_title(f'BEV Fleet by Technology Cost ({target_year})', fontsize=12)
    ax2.legend(title='Tech Cost', labels=['0.7x (optimistic)', '1.0x (reference)', '1.3x (pessimistic)'])
    ax2.tick_params(axis='x', rotation=45)
    ax2.grid(True, alpha=0.3, axis='y')

    plt.suptitle(f'Impact of Charging Markup and Technology Cost on BEV Adoption ({target_year})',
                 fontsize=14, y=1.02)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=150)
        print(f"Saved to {save_path}")

    plt.show()

    # Print summary
    print(f"\n=== Impact Summary ({target_year}) ===")
    print("\nBy Markup (averaged across tech costs):")
    for markup in df['markup'].unique():
        avg = df[df['markup'] == markup]['total_bevs'].mean()
        print(f"  {markup}: {avg:.0f} BEVs")

    print("\nBy Tech Cost (averaged across markups):")
    for tech in sorted(df['tech_cost'].unique()):
        avg = df[df['tech_cost'] == tech]['total_bevs'].mean()
        print(f"  {tech}x: {avg:.0f} BEVs")

    return df


def plot_bev_timeseries_by_genesys(timeseries_df: pd.DataFrame,
                                    figsize: Tuple[int, int] = (12, 7),
                                    save_path: Optional[Path] = None):
    """
    Plot BEV adoption time series by GENeSYS scenario.
    """
    fig, ax = plt.subplots(figsize=figsize)

    colors = {
        'Go RES v1.2': '#2ecc71',
        'NECPEssentials v1.2': '#3498db',
        'REPowerEU++ v1.2': '#9b59b6',
        'Trinity v1.2': '#e74c3c'
    }

    for scenario in colors.keys():
        scenario_data = timeseries_df[timeseries_df['genesys_scenario'] == scenario]
        if scenario_data.empty:
            continue

        ax.plot(scenario_data['year'], scenario_data['mean_bevs'],
                color=colors[scenario], linewidth=2, marker='o',
                label=scenario.replace(' v1.2', ''))

        ax.fill_between(scenario_data['year'],
                        scenario_data['mean_bevs'] - scenario_data['std_bevs'],
                        scenario_data['mean_bevs'] + scenario_data['std_bevs'],
                        color=colors[scenario], alpha=0.2)

    ax.set_xlabel('Year', fontsize=12)
    ax.set_ylabel('Total BEV Fleet (vehicles)', fontsize=12)
    ax.set_title('BEV Fleet Growth by GENeSYS-MOD Scenario\n(bands show variation across tech cost and charging markup)', fontsize=14)
    ax.legend(loc='upper left', fontsize=10)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=150)
        print(f"Saved to {save_path}")

    plt.show()


def plot_bev_od_bar_by_corridor(base_path: Path, target_year: int = 2040,
                                 top_n: int = 15,
                                 figsize: Tuple[int, int] = (14, 8),
                                 save_path: Optional[Path] = None,
                                 preloaded_matrices: Dict[str, pd.DataFrame] = None,
                                 preloaded_results: Dict = None,
                                 cases_metadata: Dict = None):
    """
    Plot bar chart of top OD corridors by BEV count, grouped by GENeSYS scenario.

    Args:
        preloaded_matrices: Optional pre-computed matrices from create_bev_od_matrix_by_genesys
        preloaded_results: Optional pre-loaded results (passed to create_bev_od_matrix_by_genesys)
        cases_metadata: Optional pre-loaded cases metadata
    """
    if preloaded_matrices is not None:
        matrices = preloaded_matrices
    else:
        matrices = create_bev_od_matrix_by_genesys(base_path, target_year,
                                                    preloaded_results, cases_metadata)

    # Get top corridors from all scenarios combined
    all_corridors = {}
    for scenario_name, matrix in matrices.items():
        for orig in matrix.index:
            for dest in matrix.columns:
                val = matrix.loc[orig, dest]
                if val > 0:
                    corridor = f"{orig}->{dest}"
                    if corridor not in all_corridors:
                        all_corridors[corridor] = {}
                    all_corridors[corridor][scenario_name] = val

    # Calculate average across scenarios and get top N
    corridor_avg = {c: np.mean(list(v.values())) for c, v in all_corridors.items()}
    top_corridors = sorted(corridor_avg.keys(), key=lambda x: corridor_avg[x], reverse=True)[:top_n]

    # Prepare data for plotting
    fig, ax = plt.subplots(figsize=figsize)

    x = np.arange(len(top_corridors))
    width = 0.2

    colors = {
        'Go RES v1.2': '#2ecc71',
        'NECPEssentials v1.2': '#3498db',
        'REPowerEU++ v1.2': '#9b59b6',
        'Trinity v1.2': '#e74c3c'
    }

    scenario_order = ['Go RES v1.2', 'NECPEssentials v1.2', 'REPowerEU++ v1.2', 'Trinity v1.2']

    for i, scenario in enumerate(scenario_order):
        values = [all_corridors.get(c, {}).get(scenario, 0) for c in top_corridors]
        ax.bar(x + i * width, values, width, label=scenario.replace(' v1.2', ''),
               color=colors[scenario])

    ax.set_xlabel('OD Corridor', fontsize=12)
    ax.set_ylabel('BEV Vehicles', fontsize=12)
    ax.set_title(f'Top {top_n} BEV Corridors by GENeSYS Scenario ({target_year})', fontsize=14)
    ax.set_xticks(x + width * 1.5)
    ax.set_xticklabels(top_corridors, rotation=45, ha='right', fontsize=9)
    ax.legend(loc='upper right', fontsize=10)
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=150)
        print(f"Saved to {save_path}")

    plt.show()

    return top_corridors, all_corridors


# Convenience function for notebook imports
def analyze_bev_od_uncertainty(base_path: Path = None, target_year: int = 2040):
    """
    Run full BEV OD analysis for uncertainty scenarios.

    Usage in notebook:
        from bev_od_adoption_uncertainty import analyze_bev_od_uncertainty
        results = analyze_bev_od_uncertainty()
    """
    if base_path is None:
        base_path = Path.cwd()

    print("Creating BEV OD matrices by GENeSYS scenario...")
    matrices = create_bev_od_matrix_by_genesys(base_path, target_year)

    print("\nCreating BEV time series by GENeSYS scenario...")
    timeseries = create_bev_od_timeseries_by_genesys(base_path)

    return {
        'matrices': matrices,
        'timeseries': timeseries
    }
