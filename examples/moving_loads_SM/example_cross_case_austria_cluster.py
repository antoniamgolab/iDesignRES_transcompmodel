"""
Example: Cross-Case Comparison for Austria-Germany-Italy Border Cluster

This script demonstrates how to compare the Austria-Germany-Italy border region
across your 4 case studies (Var-Var, Var-Uni, Uni-Var, Uni-Uni).

Run this script to see a complete cross-case analysis.
"""

from sub_border_regions_cross_case import (
    analyze_sub_region_cross_case,
    load_case_data,
    summarize_cross_case_results
)
from sub_border_regions import SUB_BORDER_REGIONS
import os

# Check if results folder exists
if not os.path.exists('results'):
    print("ERROR: 'results' folder not found in current directory")
    print(f"Current directory: {os.getcwd()}")
    print("\nPlease run this script from: examples/moving_loads_SM/")
    exit(1)

# Define your 4 case studies
print("=" * 80)
print("AUSTRIA-GERMANY-ITALY BORDER CLUSTER: CROSS-CASE COMPARISON")
print("=" * 80)

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

print("\nCase Studies:")
for label, (case_name, run_id) in cases.items():
    print(f"  {label}:")
    print(f"    Study: {case_name}")
    print(f"    Run: {run_id}")

# Display Austria-Germany-Italy cluster details
print("\n" + "=" * 80)
print("SUB-BORDER REGION: Austria-Germany-Italy")
print("=" * 80)

austria_cluster = SUB_BORDER_REGIONS['Austria-Germany-Italy']
print(f"Description: {austria_cluster['description']}")
print(f"\nCountries: {', '.join(sorted(austria_cluster['countries']))}")
print(f"\nNUTS2 Regions ({len(austria_cluster['regions'])}):")

# Group by country
for country in sorted(austria_cluster['countries']):
    country_regions = [r for r in sorted(austria_cluster['regions']) if r.startswith(country)]
    print(f"  {country}: {', '.join(country_regions)}")

# Run the analysis
print("\n" + "=" * 80)
print("RUNNING CROSS-CASE ANALYSIS")
print("=" * 80)
print("\nThis will load data from all 4 case studies and compare electrification")
print("in the Austria-Germany-Italy border region...")

try:
    df_comparison, df_summary = analyze_sub_region_cross_case(
        cases=cases,
        sub_region_name='Austria-Germany-Italy',
        results_folder='results',
        years_to_plot=[2030, 2040, 2050],
        baseline_case='Var-Var',
        show_plots=True,
        verbose=True
    )

    # Additional analysis
    print("\n" + "=" * 80)
    print("KEY FINDINGS")
    print("=" * 80)

    for year in [2030, 2040, 2050]:
        year_data = df_summary[df_summary['Year'] == year]
        if len(year_data) > 0:
            print(f"\nYear {year}:")

            best_case = year_data.loc[year_data['Avg Electrification %'].idxmax()]
            worst_case = year_data.loc[year_data['Avg Electrification %'].idxmin()]

            print(f"  Highest electrification: {best_case['Case']} ({best_case['Avg Electrification %']:.2f}%)")
            print(f"  Lowest electrification:  {worst_case['Case']} ({worst_case['Avg Electrification %']:.2f}%)")
            print(f"  Range: {best_case['Avg Electrification %'] - worst_case['Avg Electrification %']:.2f} percentage points")

            # Show country-specific results for this year
            year_comp = df_comparison[df_comparison['year'] == year]
            print(f"\n  By country:")
            for country in sorted(year_comp['country'].unique()):
                country_data = year_comp[year_comp['country'] == country]
                print(f"    {country}:")
                for _, row in country_data.iterrows():
                    print(f"      {row['case']}: {row['electrification_pct']:.2f}%")

    # Export results
    print("\n" + "=" * 80)
    print("EXPORTING RESULTS")
    print("=" * 80)

    df_comparison.to_csv('austria_germany_italy_cross_case_comparison.csv', index=False)
    print("✓ Saved: austria_germany_italy_cross_case_comparison.csv")

    df_summary.to_csv('austria_germany_italy_cross_case_summary.csv', index=False)
    print("✓ Saved: austria_germany_italy_cross_case_summary.csv")

    # Create pivot table for paper
    pivot_table = df_summary.pivot_table(
        index='Case',
        columns='Year',
        values='Avg Electrification %'
    )
    pivot_table.to_csv('austria_germany_italy_summary_table.csv')
    print("✓ Saved: austria_germany_italy_summary_table.csv")

    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print("\nSummary Table for Paper/Presentation:")
    print(pivot_table.to_string(float_format=lambda x: f"{x:.2f}"))

except FileNotFoundError as e:
    print(f"\nERROR: Could not find required data files")
    print(f"Details: {e}")
    print("\nPlease ensure:")
    print("  1. You're running from examples/moving_loads_SM/")
    print("  2. The 'results' folder exists and contains your case study data")
    print("  3. The case study names and run IDs are correct")

except Exception as e:
    print(f"\nERROR during analysis: {e}")
    import traceback
    traceback.print_exc()
