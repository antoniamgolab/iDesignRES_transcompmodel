"""
Sub-Border Region Cross-Case Comparison

This module extends sub_border_regions.py to compare the same sub-border region
across multiple case studies/scenarios.

Example use case: Compare Austria-Germany-Italy border region electrification
across different infrastructure or policy scenarios.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Set, Optional, Tuple
import os
import yaml

from sub_border_regions import (
    SUB_BORDER_REGIONS,
    calculate_electrification_by_sub_border_region,
    get_sub_border_region_info
)


def compare_sub_region_across_cases_preloaded(
    loaded_runs: Dict[str, Dict[str, dict]],
    case_labels: Dict[str, str],
    sub_region_name: str,
    years_to_plot: List[int] = None,
    verbose: bool = True
) -> pd.DataFrame:
    """
    Compare a specific sub-border region across multiple pre-loaded case studies.

    This function is designed to work with data already loaded in your notebook,
    avoiding the need to reload from files.

    Parameters:
    -----------
    loaded_runs : dict
        Dictionary with structure:
        {
            "case_20251022_152235_var_var": {
                "input_data": {...},
                "output_data": {...}
            },
            ...
        }

    case_labels : dict
        Mapping from case_study_name to human-readable label:
        {
            "case_20251022_152235_var_var": "Var-Var",
            "case_20251022_152358_var_uni": "Var-Uni",
            ...
        }

    sub_region_name : str
        Name of sub-border region to analyze (e.g., 'Austria-Germany-Italy')

    years_to_plot : list, optional
        Years to analyze. Default: [2030, 2050]

    verbose : bool
        Print progress

    Returns:
    --------
    df_comparison : pd.DataFrame
        Combined DataFrame with columns: case, country, year, electrification_pct, etc.

    Example:
    --------
    # After loading your data in the notebook
    case_labels = {
        "case_20251022_152235_var_var": "Var-Var",
        "case_20251022_152358_var_uni": "Var-Uni",
        "case_20251022_153056_uni_var": "Uni-Var",
        "case_20251022_153317_uni_uni": "Uni-Uni"
    }

    df_comparison = compare_sub_region_across_cases_preloaded(
        loaded_runs=loaded_runs,
        case_labels=case_labels,
        sub_region_name='Austria-Germany-Italy',
        years_to_plot=[2030, 2040, 2050]
    )
    """
    if years_to_plot is None:
        years_to_plot = [2030, 2050]

    all_dfs = []

    for case_study_name, data in loaded_runs.items():
        # Get human-readable label
        case_label = case_labels.get(case_study_name, case_study_name)

        if verbose:
            print(f"\nProcessing case: {case_label}")
            print(f"  Study: {case_study_name}")

        input_data = data["input_data"]
        output_data = data["output_data"]

        if verbose:
            print(f"  Loaded {len(input_data)} input structures")
            print(f"  Loaded {len(output_data)} output variables")

        # Calculate electrification for this sub-region
        df, fuel_by_country, skip_counters = calculate_electrification_by_sub_border_region(
            input_data, output_data, sub_region_name, years_to_plot
        )

        # Add case label
        df['case'] = case_label
        df['case_study_name'] = case_study_name

        all_dfs.append(df)

        if verbose:
            print(f"  Found {len(df)} country-year combinations")

    # Combine all cases
    df_comparison = pd.concat(all_dfs, ignore_index=True)

    return df_comparison


def analyze_sub_region_cross_case_preloaded(
    loaded_runs: Dict[str, Dict[str, dict]],
    case_labels: Dict[str, str],
    sub_region_name: str,
    years_to_plot: List[int] = None,
    baseline_case: Optional[str] = None,
    show_plots: bool = True,
    verbose: bool = True
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Complete workflow for cross-case sub-border region analysis using pre-loaded data.

    This is the main function you should use in your notebook after loading data
    with your existing read_data() function.

    Parameters:
    -----------
    loaded_runs : dict
        Your loaded_runs dictionary from the notebook

    case_labels : dict
        Mapping from case_study_name to readable labels

    sub_region_name : str
        Sub-border region to analyze (e.g., 'Austria-Germany-Italy')

    years_to_plot : list, optional
        Years to analyze. Default: [2030, 2050]

    baseline_case : str, optional
        Case label to use as baseline for delta plots (e.g., 'Var-Var')

    show_plots : bool
        Display plots

    verbose : bool
        Print summaries

    Returns:
    --------
    df_comparison : pd.DataFrame
        Combined comparison data

    df_summary : pd.DataFrame
        Summary statistics

    Example:
    --------
    # In your notebook, after loading data:
    case_labels = {
        "case_20251022_152235_var_var": "Var-Var",
        "case_20251022_152358_var_uni": "Var-Uni",
        "case_20251022_153056_uni_var": "Uni-Var",
        "case_20251022_153317_uni_uni": "Uni-Uni"
    }

    df_comparison, df_summary = analyze_sub_region_cross_case_preloaded(
        loaded_runs=loaded_runs,
        case_labels=case_labels,
        sub_region_name='Austria-Germany-Italy',
        years_to_plot=[2030, 2040, 2050],
        baseline_case='Var-Var',
        show_plots=True,
        verbose=True
    )
    """
    if years_to_plot is None:
        years_to_plot = [2030, 2050]

    # Load and compare
    df_comparison = compare_sub_region_across_cases_preloaded(
        loaded_runs, case_labels, sub_region_name, years_to_plot, verbose=verbose
    )

    # Summarize
    df_summary = summarize_cross_case_results(
        df_comparison, sub_region_name, years_to_plot, verbose=verbose
    )

    # Plot
    if show_plots:
        # 1. Grouped bar chart - Electrification %
        fig1, axes1 = plot_cross_case_comparison(
            df_comparison, sub_region_name, years_to_plot,
            figsize=(16, 6), plot_type='grouped_bar'
        )
        plt.show()

        # 2. Line charts by country - Electrification %
        fig2, axes2 = plot_cross_case_comparison(
            df_comparison, sub_region_name, years_to_plot,
            figsize=(14, 8), plot_type='line'
        )
        plt.show()

        # 3. Absolute electricity consumption - Grouped bars
        fig3, axes3 = plot_absolute_electricity_comparison(
            df_comparison, sub_region_name, years_to_plot,
            figsize=(16, 6), plot_type='grouped_bar'
        )
        plt.show()

        # 4. Absolute electricity consumption - Line charts
        fig4, axes4 = plot_absolute_electricity_comparison(
            df_comparison, sub_region_name, years_to_plot,
            figsize=(14, 8), plot_type='line'
        )
        plt.show()

        # 5. Delta plot (if baseline specified)
        if baseline_case is not None:
            fig5, axes5 = plot_delta_across_cases(
                df_comparison, sub_region_name, baseline_case, years_to_plot
            )
            plt.show()

    return df_comparison, df_summary


def load_case_data(
    case_study_name: str,
    run_id: str,
    results_folder: str = "results",
    variables_to_read: List[str] = None
) -> Tuple[dict, dict]:
    """
    Load input and output data for a single case study.

    Parameters:
    -----------
    case_study_name : str
        Name of the case study (e.g., 'case_20251022_152235_var_var')

    run_id : str
        Run identifier (e.g., 'case_20251022_152235_var_var_cs_2025-10-23_08-22-09')

    results_folder : str
        Path to results folder. Default: 'results'

    variables_to_read : list, optional
        List of output variables to load. Default: ['f', 'h', 's']

    Returns:
    --------
    input_data : dict
        Dictionary containing input data structures

    output_data : dict
        Dictionary containing output variables
    """
    if variables_to_read is None:
        variables_to_read = ['f', 'h', 's']

    input_data = {}
    output_data = {}

    # Load input data (YAML files)
    input_folder = os.path.join(results_folder, case_study_name)
    if os.path.exists(input_folder):
        for file_name in os.listdir(input_folder):
            if file_name.endswith(".yaml") and not any(var in file_name for var in variables_to_read):
                file_path = os.path.join(input_folder, file_name)
                with open(file_path, "r") as file:
                    key_name = file_name.replace(".yaml", "")
                    input_data[key_name] = yaml.safe_load(file)

    # Load output data (result variables)
    for variable in variables_to_read:
        file_path = os.path.join(
            results_folder,
            case_study_name,
            f"{run_id}_{variable}_dict.yaml"
        )
        if os.path.exists(file_path):
            with open(file_path, "r") as file:
                output_data[variable] = yaml.safe_load(file)

    return input_data, output_data


def compare_sub_region_across_cases(
    cases: Dict[str, Tuple[str, str]],
    sub_region_name: str,
    results_folder: str = "results",
    years_to_plot: List[int] = None,
    variables_to_read: List[str] = None,
    verbose: bool = True
) -> pd.DataFrame:
    """
    Compare a specific sub-border region across multiple case studies.

    Parameters:
    -----------
    cases : dict
        Dictionary mapping case label to (case_study_name, run_id) tuple
        Example: {
            'Var-Var': ('case_20251022_152235_var_var',
                       'case_20251022_152235_var_var_cs_2025-10-23_08-22-09'),
            'Var-Uni': ('case_20251022_152358_var_uni',
                       'case_20251022_152358_var_uni_cs_2025-10-23_08-56-23')
        }

    sub_region_name : str
        Name of sub-border region to analyze (e.g., 'Austria-Germany-Italy')

    results_folder : str
        Path to results folder

    years_to_plot : list, optional
        Years to analyze. Default: [2030, 2050]

    variables_to_read : list, optional
        Output variables to load. Default: ['f']

    verbose : bool
        Print progress

    Returns:
    --------
    df_comparison : pd.DataFrame
        Combined DataFrame with columns: case_label, country, year, electrification_pct, etc.
    """
    if years_to_plot is None:
        years_to_plot = [2030, 2050]

    if variables_to_read is None:
        variables_to_read = ['f']

    all_dfs = []

    for case_label, (case_study_name, run_id) in cases.items():
        if verbose:
            print(f"\nLoading case: {case_label}")
            print(f"  Study: {case_study_name}")
            print(f"  Run: {run_id}")

        # Load data
        input_data, output_data = load_case_data(
            case_study_name, run_id, results_folder, variables_to_read
        )

        if verbose:
            print(f"  Loaded {len(input_data)} input structures")
            print(f"  Loaded {len(output_data)} output variables")

        # Calculate electrification for this sub-region
        df, fuel_by_country, skip_counters = calculate_electrification_by_sub_border_region(
            input_data, output_data, sub_region_name, years_to_plot
        )

        # Add case label
        df['case'] = case_label

        all_dfs.append(df)

        if verbose:
            print(f"  Found {len(df)} country-year combinations")

    # Combine all cases
    df_comparison = pd.concat(all_dfs, ignore_index=True)

    return df_comparison


def plot_cross_case_comparison(
    df_comparison: pd.DataFrame,
    sub_region_name: str,
    years_to_plot: List[int] = None,
    figsize: Tuple[int, int] = (16, 6),
    plot_type: str = 'grouped_bar'
) -> Tuple:
    """
    Create comparison plots across case studies for a sub-border region.

    Parameters:
    -----------
    df_comparison : pd.DataFrame
        Output from compare_sub_region_across_cases()

    sub_region_name : str
        Name of sub-border region

    years_to_plot : list, optional
        Years to plot

    figsize : tuple
        Figure size

    plot_type : str
        'grouped_bar' or 'line'

    Returns:
    --------
    fig, axes : matplotlib figure and axes
    """
    if years_to_plot is None:
        years_to_plot = sorted(df_comparison['year'].unique())

    if plot_type == 'grouped_bar':
        fig, axes = plt.subplots(1, len(years_to_plot), figsize=figsize)
        if len(years_to_plot) == 1:
            axes = [axes]

        for idx, year in enumerate(years_to_plot):
            ax = axes[idx]

            # Filter to this year
            year_data = df_comparison[df_comparison['year'] == year]

            if len(year_data) == 0:
                ax.text(0.5, 0.5, f'No data for {year}',
                       ha='center', va='center', transform=ax.transAxes)
                ax.set_title(f'Year {year}')
                continue

            # Pivot for grouped bar chart
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
                ax.bar(x + offset, values, width, label=case, alpha=0.85)

            ax.set_xlabel('Country', fontsize=11)
            ax.set_ylabel('Electrification %', fontsize=11)
            ax.set_title(f'{sub_region_name}\nYear {year}', fontsize=12, fontweight='bold')
            ax.set_xticks(x)
            ax.set_xticklabels(countries)
            ax.legend(title='Case', fontsize=9)
            ax.grid(True, alpha=0.3, axis='y')
            ax.set_ylim(0, 100)

    elif plot_type == 'line':
        countries = sorted(df_comparison['country'].unique())
        n_countries = len(countries)
        n_cols = min(3, n_countries)
        n_rows = (n_countries + n_cols - 1) // n_cols

        fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize)

        # Ensure axes is always a 2D array for consistent indexing
        if n_rows == 1 and n_cols == 1:
            axes = np.array([[axes]])
        elif n_rows == 1:
            axes = axes.reshape(1, -1)
        elif n_cols == 1:
            axes = axes.reshape(-1, 1)

        for idx, country in enumerate(countries):
            row = idx // n_cols
            col = idx % n_cols
            ax = axes[row, col]  # axes is always 2D after reshape

            country_data = df_comparison[df_comparison['country'] == country]

            for case in sorted(country_data['case'].unique()):
                case_data = country_data[country_data['case'] == case]
                ax.plot(case_data['year'], case_data['electrification_pct'],
                       marker='o', label=case, linewidth=2, markersize=6)

            ax.set_xlabel('Year', fontsize=10)
            ax.set_ylabel('Electrification %', fontsize=10)
            ax.set_title(f'{country}', fontsize=11, fontweight='bold')
            ax.legend(fontsize=8)
            ax.grid(True, alpha=0.3)
            ax.set_ylim(0, 100)

        # Hide empty subplots
        for idx in range(n_countries, n_rows * n_cols):
            row = idx // n_cols
            col = idx % n_cols
            ax = axes[row, col]  # axes is always 2D after reshape
            ax.axis('off')

        fig.suptitle(f'{sub_region_name} - Electrification Across Cases',
                    fontsize=14, fontweight='bold', y=1.02)

    plt.tight_layout()
    return fig, axes


def plot_absolute_electricity_comparison(
    df_comparison: pd.DataFrame,
    sub_region_name: str,
    years_to_plot: List[int] = None,
    figsize: Tuple[int, int] = (16, 6),
    plot_type: str = 'grouped_bar'
) -> Tuple:
    """
    Create comparison plots showing absolute electricity consumption (MWh) across cases.

    Parameters:
    -----------
    df_comparison : pd.DataFrame
        Output from compare_sub_region_across_cases_preloaded()

    sub_region_name : str
        Name of sub-border region

    years_to_plot : list, optional
        Years to plot

    figsize : tuple
        Figure size

    plot_type : str
        'grouped_bar' or 'line'

    Returns:
    --------
    fig, axes : matplotlib figure and axes
    """
    if years_to_plot is None:
        years_to_plot = sorted(df_comparison['year'].unique())

    if plot_type == 'grouped_bar':
        fig, axes = plt.subplots(1, len(years_to_plot), figsize=figsize)
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
                ax.bar(x + offset, values, width, label=case, alpha=0.85)

            ax.set_xlabel('Country', fontsize=11)
            ax.set_ylabel('Electricity Consumption (MWh)', fontsize=11)
            ax.set_title(f'{sub_region_name}\nYear {year}', fontsize=12, fontweight='bold')
            ax.set_xticks(x)
            ax.set_xticklabels(countries)
            ax.legend(title='Case', fontsize=9)
            ax.grid(True, alpha=0.3, axis='y')

    elif plot_type == 'line':
        countries = sorted(df_comparison['country'].unique())
        n_countries = len(countries)
        n_cols = min(3, n_countries)
        n_rows = (n_countries + n_cols - 1) // n_cols

        fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize)

        # Ensure axes is always a 2D array for consistent indexing
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
                case_data = country_data[country_data['case'] == case]
                ax.plot(case_data['year'], case_data['electricity'],
                       marker='o', label=case, linewidth=2, markersize=6)

            ax.set_xlabel('Year', fontsize=10)
            ax.set_ylabel('Electricity (MWh)', fontsize=10)
            ax.set_title(f'{country}', fontsize=11, fontweight='bold')
            ax.legend(fontsize=8)
            ax.grid(True, alpha=0.3)

        # Hide empty subplots
        for idx in range(n_countries, n_rows * n_cols):
            row = idx // n_cols
            col = idx % n_cols
            ax = axes[row, col]
            ax.axis('off')

        fig.suptitle(f'{sub_region_name} - Electricity Consumption (MWh) Across Cases',
                    fontsize=14, fontweight='bold', y=1.02)

    plt.tight_layout()
    return fig, axes


def plot_delta_across_cases(
    df_comparison: pd.DataFrame,
    sub_region_name: str,
    baseline_case: str,
    years_to_plot: List[int] = None,
    figsize: Tuple[int, int] = (14, 6)
) -> Tuple:
    """
    Plot differences in electrification relative to a baseline case.

    Parameters:
    -----------
    df_comparison : pd.DataFrame
        Output from compare_sub_region_across_cases()

    sub_region_name : str
        Name of sub-border region

    baseline_case : str
        Case label to use as baseline

    years_to_plot : list, optional
        Years to plot

    figsize : tuple
        Figure size

    Returns:
    --------
    fig, axes : matplotlib figure and axes
    """
    if years_to_plot is None:
        years_to_plot = sorted(df_comparison['year'].unique())

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

    # Plot
    fig, axes = plt.subplots(1, len(years_to_plot), figsize=figsize)
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

        ax.set_xlabel('Country', fontsize=11)
        ax.set_ylabel(f'Δ Electrification % (vs. {baseline_case})', fontsize=11)
        ax.set_title(f'{sub_region_name}\nYear {year}', fontsize=12, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(countries)
        ax.legend(title='Case', fontsize=9)
        ax.grid(True, alpha=0.3, axis='y')
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8)

    plt.tight_layout()
    return fig, axes


def summarize_cross_case_results(
    df_comparison: pd.DataFrame,
    sub_region_name: str,
    years_to_plot: List[int] = None,
    verbose: bool = True
) -> pd.DataFrame:
    """
    Create summary table comparing cases for a sub-border region.

    Parameters:
    -----------
    df_comparison : pd.DataFrame
        Output from compare_sub_region_across_cases()

    sub_region_name : str
        Name of sub-border region

    years_to_plot : list, optional
        Years to summarize

    verbose : bool
        Print summary

    Returns:
    --------
    df_summary : pd.DataFrame
        Summary statistics by case and year
    """
    if years_to_plot is None:
        years_to_plot = sorted(df_comparison['year'].unique())

    summary_data = []

    for case in sorted(df_comparison['case'].unique()):
        case_data = df_comparison[df_comparison['case'] == case]

        for year in years_to_plot:
            year_data = case_data[case_data['year'] == year]

            if len(year_data) > 0:
                summary_data.append({
                    'Case': case,
                    'Year': year,
                    'Countries': len(year_data),
                    'Avg Electrification %': year_data['electrification_pct'].mean(),
                    'Min Electrification %': year_data['electrification_pct'].min(),
                    'Max Electrification %': year_data['electrification_pct'].max(),
                    'Total Electricity (MWh)': year_data['electricity'].sum(),
                    'Total Fuel (MWh)': year_data['total_fuel'].sum()
                })

    df_summary = pd.DataFrame(summary_data)

    if verbose and len(df_summary) > 0:
        print("\n" + "=" * 100)
        print(f"CROSS-CASE COMPARISON: {sub_region_name}")
        print("=" * 100)
        print(df_summary.to_string(index=False))
        print("=" * 100)

    return df_summary


def analyze_sub_region_cross_case(
    cases: Dict[str, Tuple[str, str]],
    sub_region_name: str,
    results_folder: str = "results",
    years_to_plot: List[int] = None,
    baseline_case: Optional[str] = None,
    show_plots: bool = True,
    verbose: bool = True
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Complete workflow for cross-case sub-border region analysis.

    Parameters:
    -----------
    cases : dict
        Dictionary mapping case label to (case_study_name, run_id) tuple

    sub_region_name : str
        Sub-border region to analyze

    results_folder : str
        Path to results folder

    years_to_plot : list, optional
        Years to analyze

    baseline_case : str, optional
        Case to use as baseline for delta plots

    show_plots : bool
        Display plots

    verbose : bool
        Print summaries

    Returns:
    --------
    df_comparison : pd.DataFrame
        Combined comparison data

    df_summary : pd.DataFrame
        Summary statistics
    """
    if years_to_plot is None:
        years_to_plot = [2030, 2050]

    # Load and compare
    df_comparison = compare_sub_region_across_cases(
        cases, sub_region_name, results_folder, years_to_plot,
        variables_to_read=['f'], verbose=verbose
    )

    # Summarize
    df_summary = summarize_cross_case_results(
        df_comparison, sub_region_name, years_to_plot, verbose=verbose
    )

    # Plot
    if show_plots:
        # Grouped bar chart
        fig1, axes1 = plot_cross_case_comparison(
            df_comparison, sub_region_name, years_to_plot,
            figsize=(16, 6), plot_type='grouped_bar'
        )
        plt.show()

        # Line charts by country
        fig2, axes2 = plot_cross_case_comparison(
            df_comparison, sub_region_name, years_to_plot,
            figsize=(14, 8), plot_type='line'
        )
        plt.show()

        # Delta plot (if baseline specified)
        if baseline_case is not None:
            fig3, axes3 = plot_delta_across_cases(
                df_comparison, sub_region_name, baseline_case, years_to_plot
            )
            plt.show()

    return df_comparison, df_summary


# Example usage
if __name__ == "__main__":
    print("Sub-Border Region Cross-Case Comparison Module")
    print("=" * 80)
    print("\nExample usage:")
    print("""
from sub_border_regions_cross_case import analyze_sub_region_cross_case

# Define your cases
cases = {
    'Var-Var': ('case_20251022_152235_var_var',
                'case_20251022_152235_var_var_cs_2025-10-23_08-22-09'),
    'Var-Uni': ('case_20251022_152358_var_uni',
                'case_20251022_152358_var_uni_cs_2025-10-23_08-56-23'),
    'Uni-Var': ('case_20251022_153056_uni_var',
                'case_20251022_153056_uni_var_cs_2025-10-23_09-36-37'),
    'Uni-Uni': ('case_20251022_153317_uni_uni',
                'case_20251022_153317_uni_uni_cs_2025-10-23_10-09-32')
}

# Compare Austria-Germany-Italy across all cases
df_comparison, df_summary = analyze_sub_region_cross_case(
    cases=cases,
    sub_region_name='Austria-Germany-Italy',
    results_folder='results',
    years_to_plot=[2030, 2040, 2050],
    baseline_case='Var-Var',  # Show deltas relative to this case
    show_plots=True,
    verbose=True
)

# Export results
df_comparison.to_csv('austria_cluster_cross_case_comparison.csv', index=False)
df_summary.to_csv('austria_cluster_summary.csv', index=False)
    """)
