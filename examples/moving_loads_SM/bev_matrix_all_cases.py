"""
Create BEV country matrices for ALL case studies
"""
from bev_country_matrix_FIXED import create_bev_country_matrix_FIXED
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


def create_bev_matrices_all_cases(loaded_runs, target_year=2030):
    """
    Create BEV country matrices for all cases in loaded_runs

    Returns:
        dict: {case_name: matrix_dataframe}
    """
    results = {}

    print("="*80)
    print(f"CREATING BEV MATRICES FOR ALL CASES (Year: {target_year})")
    print("="*80)

    for case_name in loaded_runs.keys():
        print(f"\n--- Processing: {case_name} ---")
        matrix = create_bev_country_matrix_FIXED(loaded_runs, target_year=target_year, case_name=case_name)
        results[case_name] = matrix

    return results


def compare_bev_matrices(matrices_dict, metric='total'):
    """
    Compare BEV flows across different cases

    Args:
        matrices_dict: {case_name: matrix_df} from create_bev_matrices_all_cases()
        metric: 'total' (sum of all flows) or 'diagonal' (within-country flows)

    Returns:
        DataFrame with comparison
    """
    comparison = {}

    for case_name, matrix in matrices_dict.items():
        if matrix.empty:
            comparison[case_name] = {'total': 0, 'diagonal': 0, 'cross_border': 0}
            continue

        total_flow = matrix.sum().sum()
        diagonal_flow = sum(matrix.loc[c, c] for c in matrix.index if c in matrix.columns)
        cross_border_flow = total_flow - diagonal_flow

        comparison[case_name] = {
            'total': total_flow,
            'diagonal': diagonal_flow,
            'cross_border': cross_border_flow,
            'cross_border_pct': (cross_border_flow / total_flow * 100) if total_flow > 0 else 0
        }

    return pd.DataFrame(comparison).T


def plot_bev_matrices_comparison(matrices_dict, figsize=(15, 10), case_labels=None):
    """
    Create side-by-side heatmaps for all cases

    Args:
        matrices_dict: {case_name: matrix_df} from create_bev_matrices_all_cases()
        figsize: Figure size (width, height)
        case_labels: Optional dict mapping case_name -> display_label
                     Example: {"case_20251028_091344_var_var": "Base case"}
    """
    n_cases = len(matrices_dict)

    # Filter out empty matrices
    valid_matrices = {k: v for k, v in matrices_dict.items() if not v.empty}
    n_valid = len(valid_matrices)

    if n_valid == 0:
        print("No valid matrices to plot!")
        return

    # Calculate layout
    n_cols = min(2, n_valid)  # Max 2 columns
    n_rows = (n_valid + n_cols - 1) // n_cols

    fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize)
    if n_valid == 1:
        axes = [axes]
    else:
        axes = axes.flatten() if n_valid > 1 else [axes]

    # Find global min/max for consistent color scale
    all_values = []
    for matrix in valid_matrices.values():
        all_values.extend(matrix.values.flatten())
    vmin, vmax = min(all_values), max(all_values)

    for idx, (case_name, matrix) in enumerate(valid_matrices.items()):
        ax = axes[idx]

        sns.heatmap(matrix, annot=True, fmt='.1f', cmap='YlOrRd',
                    vmin=vmin, vmax=vmax,
                    cbar_kws={'label': 'BEV Flow (1000 tkm)'},
                    ax=ax)

        # Use custom label if provided, otherwise use case_name
        display_label = case_labels.get(case_name, case_name) if case_labels else case_name

        ax.set_title(f'{display_label}\nTotal: {matrix.sum().sum():.1f}', fontsize=10)
        ax.set_xlabel('Destination Country')
        ax.set_ylabel('Origin Country')

    # Hide unused subplots
    for idx in range(n_valid, len(axes)):
        axes[idx].axis('off')

    plt.tight_layout()
    plt.savefig('bev_matrices_comparison.png', dpi=300)
    plt.show()


# =============================================================================
# USAGE EXAMPLES
# =============================================================================
#
# In your Jupyter notebook:
#
# ```python
# # Import
# from bev_matrix_all_cases import create_bev_matrices_all_cases, compare_bev_matrices, plot_bev_matrices_comparison
#
# # Define custom labels for your cases
# case_study_name_labels = {
#     "case_20251028_091344_var_var": "Base case",
#     "case_20251028_091411_var_uni": "Uniform network fees",
#     "case_20251028_091502_uni_var": "Uniform electricity prices",
#     "case_20251028_091635_uni_uni": "Uniform electricity prices and network fees"
# }
#
# # Create matrices for all cases
# matrices_2030 = create_bev_matrices_all_cases(loaded_runs, target_year=2030)
#
# # Display each matrix
# for case_name, matrix in matrices_2030.items():
#     label = case_study_name_labels.get(case_name, case_name)
#     print(f"\n{'='*80}")
#     print(f"CASE: {label}")
#     print('='*80)
#     if not matrix.empty:
#         print(matrix)
#         print(f"\nTotal: {matrix.sum().sum():.2f} (1000 tkm)")
#     else:
#         print("No BEV flows")
#
# # Compare cases
# comparison = compare_bev_matrices(matrices_2030)
# print("\nCOMPARISON ACROSS CASES:")
# print(comparison)
#
# # Visualize side-by-side WITH CUSTOM LABELS
# plot_bev_matrices_comparison(matrices_2030, case_labels=case_study_name_labels)
#
# # Compare multiple years with custom labels
# for year in [2030, 2040, 2050]:
#     print(f"\n{'='*80}")
#     print(f"YEAR: {year}")
#     print('='*80)
#     matrices = create_bev_matrices_all_cases(loaded_runs, target_year=year)
#     comparison = compare_bev_matrices(matrices)
#     print(comparison)
#
#     # Plot with custom labels
#     plot_bev_matrices_comparison(matrices, case_labels=case_study_name_labels)
# ```
