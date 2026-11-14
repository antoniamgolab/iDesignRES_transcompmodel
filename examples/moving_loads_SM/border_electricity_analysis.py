"""
Border Region Electricity Analysis - Southern Border Focus

Analyzes electricity consumption in the southern border region (Germany-Austria-Italy)
comparing across different case studies.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def get_border_region_groups():
    """
    Define southern border region clusters (Alps crossing).

    Returns:
        dict: {'southern_border_by_country': {'AT': [...], 'IT': [...], 'DE': [...]}}
    """
    # Southern border regions grouped by country
    southern_border_by_country = {
        'AT': ['AT31', 'AT32', 'AT33', 'AT34'],
        'IT': ['ITH1', 'ITH3'],
        'DE': ['DE14', 'DE21', 'DE22', 'DE27', 'DEF0']
    }

    return {
        'southern_border_by_country': southern_border_by_country,
        'all_southern_border': ['AT31', 'AT32', 'AT33', 'AT34', 'ITH1', 'ITH3',
                                'DE14', 'DE21', 'DE22', 'DE27', 'DEF0']
    }


def calculate_border_electricity(loaded_runs, case_study_name, target_year=2052, border_regions=None):
    """
    Calculate electricity consumption in specific border regions by country.

    Parameters:
    -----------
    loaded_runs : dict
        Dictionary of loaded case data
    case_study_name : str
        Name of the case study
    target_year : int
        Year to analyze
    border_regions : dict
        Dictionary mapping countries to lists of NUTS2 codes

    Returns:
        dict: {country: electricity_gwh}
    """
    input_data = loaded_runs[case_study_name]["input_data"]
    output_data = loaded_runs[case_study_name]["output_data"]
    s_data = output_data["s"]

    # NUTS2 lookup
    geo_elements = input_data['GeographicElement']
    nuts2_lookup = {}
    for geo in geo_elements:
        if geo['type'] == 'node' and 'nuts2_region' in geo and geo['nuts2_region']:
            nuts2_lookup[geo['id']] = geo['nuts2_region']

    # Identify electricity fuel IDs
    fuels = input_data['Fuel']
    electricity_fuel_ids = [f['id'] for f in fuels if 'electric' in f['name'].lower()]

    # Scaling factor for energy values
    SCALING_FACTOR = 1000

    # Initialize electricity by NUTS2 region
    electricity_by_nuts2 = {}

    # Process energy supply data
    for key_str, energy_value_scaled in s_data.items():
        # Parse key
        key = eval(key_str) if isinstance(key_str, str) else key_str
        year, (_, _, _, geo_id), _, (fuel_id, fueling_infra_id), _ = key

        # Convert energy_value_scaled to float (YAML may load as string)
        energy_value = float(energy_value_scaled) if isinstance(energy_value_scaled, str) else energy_value_scaled

        if year != target_year or energy_value <= 0:
            continue

        if fuel_id not in electricity_fuel_ids:
            continue

        if geo_id not in nuts2_lookup:
            continue

        nuts2_code = nuts2_lookup[geo_id]

        # Calculate actual energy in kWh
        energy_kwh = energy_value * SCALING_FACTOR

        # Aggregate by NUTS2 region
        electricity_by_nuts2[nuts2_code] = electricity_by_nuts2.get(nuts2_code, 0.0) + energy_kwh

    # Aggregate by country for border regions
    electricity_by_country = {}

    for country, nuts2_codes in border_regions.items():
        total_kwh = sum(electricity_by_nuts2.get(code, 0.0) for code in nuts2_codes)
        electricity_by_country[country] = total_kwh / 1e6  # Convert to GWh

    return electricity_by_country


def plot_border_electricity_comparison(loaded_runs, case_studies, year=2052, case_labels=None):
    """
    Create bar plot comparing electricity consumption in southern border regions
    across different case studies for two year snapshots (2036 and 2048).

    Parameters:
    -----------
    loaded_runs : dict
        Dictionary of loaded case data
    case_studies : list
        List of case study names
    year : int
        Ignored (kept for backwards compatibility). Always uses years [2036, 2048]
    case_labels : dict
        Optional dict mapping case names to display labels
    """
    # Use fixed years for comparison
    years = [2036, 2044]

    print("="*80)
    print(f"SOUTHERN BORDER ELECTRICITY ANALYSIS (Years: {years})")
    print("="*80)
    print("\nSouthern Border: Germany-Austria-Italy (Alps Crossing)")

    # Get border region definitions
    border_groups = get_border_region_groups()
    southern_border = border_groups['southern_border_by_country']

    print(f"\nRegions included:")
    for country, codes in southern_border.items():
        print(f"  {country}: {', '.join(codes)}")

    # Calculate electricity for each case study and year
    results_by_year = {}
    for target_year in years:
        print(f"\n{'='*40}")
        print(f"YEAR {target_year}")
        print('='*40)
        results = {}
        for case_name in case_studies:
            print(f"\nProcessing: {case_name}")
            elec_by_country = calculate_border_electricity(
                loaded_runs, case_name, target_year=target_year, border_regions=southern_border
            )
            results[case_name] = elec_by_country

            print(f"  Electricity consumption by country:")
            for country, gwh in elec_by_country.items():
                print(f"    {country}: {gwh:.2f} GWh")
            total = sum(elec_by_country.values())
            print(f"  Total: {total:.2f} GWh")

        results_by_year[target_year] = results

    # Create subplots for each year (vertically stacked)
    # Wider and less tall: 16x9 instead of 14x12
    fig, axes = plt.subplots(2, 1, figsize=(16, 9), sharex=True)

    # Prepare data for plotting - grouped by country (Germany, Austria, Italy order)
    countries = ['DE', 'AT', 'IT']
    country_labels = {'DE': 'Germany', 'AT': 'Austria', 'IT': 'Italy'}

    # Create country positions with gaps between them
    gap = 0.5  # Gap between country groups
    x = np.array([0, 1 + gap, 2 + 2*gap])  # Add progressive gaps
    width = 0.15  # Width of each bar

    # Colors for case studies
    case_colors = ['#E74C3C', '#3498DB', '#2ECC71', '#F39C12', '#9B59B6']  # Red, Blue, Green, Orange, Purple

    # Create case study labels
    case_names = []
    for case in case_studies:
        if case_labels and case in case_labels:
            # Clean up label (remove newlines)
            label = case_labels[case].replace('\n', ' ')
        else:
            label = case
        case_names.append(label)

    # Plot for each year
    for year_idx, target_year in enumerate(years):
        ax = axes[year_idx]
        results = results_by_year[target_year]

        # Plot bars for each case study
        for i, case in enumerate(case_studies):
            values = [results[case].get(country, 0.0) for country in countries]

            n_cases = len(case_studies)
            offset = width * (i - (n_cases - 1) / 2)  # Center the bars around each country
            bars = ax.bar(x + offset, values, width,
                         label=case_names[i] if year_idx == 0 else None,  # Only show legend in first subplot
                         color=case_colors[i],
                         alpha=0.8,
                         edgecolor='white',
                         linewidth=1.5)

            # Add value labels on bars (larger font)
            for bar in bars:
                height = bar.get_height()
                if height > 0.01:  # Only show if > 0.01
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{height:.2f}',
                           ha='center', va='bottom', fontsize=11, fontweight='bold')

        # Formatting (larger fonts)
        if year_idx == 1:  # Only show x-label on bottom plot
            ax.set_xlabel('Country', fontsize=16, fontweight='bold')
        ax.set_ylabel('Electricity Consumption (GWh)', fontsize=16, fontweight='bold')
        ax.set_title(f'Year {target_year}', fontsize=18, fontweight='bold', pad=15)

        # Set x-axis labels (larger font)
        ax.set_xticks(x)
        ax.set_xticklabels([country_labels[c] for c in countries], fontsize=14)

        # Set y-axis tick labels (larger font)
        ax.tick_params(axis='y', labelsize=14)

        if year_idx == 0:  # Legend in top plot (larger font)
            ax.legend(loc='upper left', fontsize=13, framealpha=0.9)
        ax.grid(True, alpha=0.3, axis='y', linestyle='--')

    # Overall title (larger font)
    fig.suptitle('Southern Border Electricity Consumption: Case Study Comparison\n(Germany-Austria-Italy Alps Crossing)',
                 fontsize=18, fontweight='bold', y=0.995)

    plt.tight_layout()
    output_file = f'southern_border_electricity_2036_2044.pdf'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\n[OK] Plot saved as '{output_file}'")
    plt.show()

    return results_by_year


def create_summary_table(results_by_year, case_labels=None):
    """
    Create a summary table of electricity consumption by country, case, and year.

    Parameters:
    -----------
    results_by_year : dict
        Dictionary from plot_border_electricity_comparison {year: {case: {country: gwh}}}
    case_labels : dict
        Optional dict mapping case names to display labels
    """
    print("\n" + "="*80)
    print("SUMMARY TABLE: Southern Border Electricity Consumption (GWh)")
    print("="*80)

    # Create DataFrame with multi-year data
    data = []
    for year, results in sorted(results_by_year.items()):
        for case_name, country_data in results.items():
            label = case_labels.get(case_name, case_name) if case_labels else case_name
            label = label.replace('\n', ' ')  # Clean up newlines

            row = {
                'Year': year,
                'Case Study': label,
                'Germany (DE)': country_data.get('DE', 0.0),
                'Austria (AT)': country_data.get('AT', 0.0),
                'Italy (IT)': country_data.get('IT', 0.0),
            }
            row['Total'] = row['Germany (DE)'] + row['Austria (AT)'] + row['Italy (IT)']
            data.append(row)

    df = pd.DataFrame(data)

    # Print tables by year
    for year in sorted(results_by_year.keys()):
        year_df = df[df['Year'] == year].drop('Year', axis=1)
        print(f"\n{'='*80}")
        print(f"Year {year}")
        print('='*80)
        print(year_df.to_string(index=False))

    print("\n" + "="*80)

    return df


# ==============================================================================
# USAGE EXAMPLE IN JUPYTER NOTEBOOK
# ==============================================================================
"""
# Import
from border_electricity_analysis import plot_border_electricity_comparison, create_summary_table

# Define your 4 case studies
case_studies = [
    "case_20251107_153441_var_var",
    "case_20251107_160348_var_uni",
    "case_20251107_164008_uni_var",
    "case_20251107_153651_uni_uni"
]

# Define custom labels
case_labels = {
    "case_20251107_153441_var_var": "Base Case\\n(Var. Prices and Costs)",
    "case_20251107_160348_var_uni": "Uniform Network Costs",
    "case_20251107_164008_uni_var": "Uniform Electricity Prices",
    "case_20251107_153651_uni_uni": "Uniform Prices and Costs"
}

# Create comparison plot for year 2052
results = plot_border_electricity_comparison(
    loaded_runs,
    case_studies,
    year=2052,
    case_labels=case_labels
)

# Print summary table
df = create_summary_table(results, case_labels)

# Compare across years
for year in [2032, 2040, 2052]:
    print(f"\\n{'='*80}")
    print(f"YEAR: {year}")
    print('='*80)
    results_year = plot_border_electricity_comparison(
        loaded_runs,
        case_studies,
        year=year,
        case_labels=case_labels
    )
"""
