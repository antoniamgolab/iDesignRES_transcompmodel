"""
Test script for mandatory breaks analysis.

This script loads the data and runs the mandatory breaks analysis to verify it works correctly.
"""

import os
import sys
import yaml
import matplotlib.pyplot as plt

# Add the current directory to path to import the analysis function
sys.path.insert(0, os.path.dirname(__file__))

from analyze_mandatory_breaks_all_cases import analyze_mandatory_breaks_for_all_cases


def process_key(key):
    """Convert string key to a tuple"""
    try:
        return eval(key)
    except (SyntaxError, ValueError) as e:
        raise ValueError(f"Failed to parse key: {key}") from e


def process_value(value):
    """Convert string value to float"""
    return float(value)


def read_data(case_study_name, input_folder_name, variables_to_read, run_id):
    """
    Read input and output data for a case.

    Parameters:
    -----------
    case_study_name : str
        Name of the case study
    input_folder_name : str
        Path to the results folder
    variables_to_read : list
        List of variable names to read
    run_id : int
        Run ID (for backwards compatibility, not used)

    Returns:
    --------
    input_data : dict
        Input data from YAML file
    output_data : dict
        Output data dictionary with loaded variables
    """
    current_path = os.getcwd()
    print("Current path:", current_path)
    file_results = os.path.normpath(current_path + "/results")
    print("File results:", file_results)

    folder_path = os.path.join(input_folder_name, case_study_name)

    # Find all files in the folder
    files = os.listdir(folder_path)

    # Load input YAML
    input_file = [f for f in files if f.endswith('_input_data.yaml')][0]
    input_path = os.path.join(folder_path, input_file)
    with open(input_path, 'r') as f:
        input_data = yaml.safe_load(f)
    print(f"Loaded {input_path} into input_data")

    # Load output variables
    output_data = {}
    for var in variables_to_read:
        var_file = [f for f in files if f.endswith(f'_{var}_dict.yaml')]
        if var_file:
            var_path = os.path.join(folder_path, var_file[0])
            with open(var_path, 'r') as f:
                var_data = yaml.safe_load(f)
            output_data[var] = var_data
            print(f"Loaded {var_path} into output_data under variable '{var}'")
        else:
            print(f"WARNING: No file found for variable '{var}' in {case_study_name}")

    return input_data, output_data


def main():
    """Main test function"""

    # Define case studies
    case_study_names = [
        "case_20251028_091344_var_var",
        "case_20251028_091411_var_uni",
        "case_20251028_091502_uni_var",
        "case_20251028_091635_uni_uni"
    ]

    case_study_name_labels = {
        "case_20251028_091344_var_var": "Base case",
        "case_20251028_091411_var_uni": "Uniform electricity prices",
        "case_20251028_091502_uni_var": "Uniform network fees",
        "case_20251028_091635_uni_uni": "Uniform electricity prices and network fees"
    }

    # Variables to read (only need input data for mandatory breaks analysis)
    variables_to_read = []

    # Results folder path
    results_path = os.path.join(os.getcwd(), "results")

    # Load all runs
    loaded_runs = {}
    for ij in range(len(case_study_names)):
        case_study_name = case_study_names[ij]
        try:
            input_data, output_data = read_data(case_study_name, results_path, variables_to_read, ij)
            loaded_runs[case_study_name] = {
                "input_data": input_data,
                "output_data": output_data
            }
            print(f"Successfully loaded {case_study_name}")
        except Exception as e:
            print(f"ERROR loading {case_study_name}: {e}")

    print(f"\nLoaded {len(loaded_runs)} cases")

    # Run the mandatory breaks analysis
    print("\n" + "="*80)
    print("Running mandatory breaks analysis...")
    print("="*80)

    fig, stats = analyze_mandatory_breaks_for_all_cases(loaded_runs, case_study_name_labels)

    # Create figures directory if it doesn't exist
    os.makedirs('figures', exist_ok=True)

    # Save the figure
    output_path = 'figures/mandatory_breaks_all_cases_test.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\nFigure saved to: {output_path}")

    plt.show()

    print("\n" + "="*80)
    print("Test completed successfully!")
    print("="*80)


if __name__ == "__main__":
    main()
