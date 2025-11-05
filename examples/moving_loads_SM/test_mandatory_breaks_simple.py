"""
Simple test to demonstrate the mandatory breaks analysis.

This loads one case's input data directly and runs the analysis.
"""

import os
import yaml
import matplotlib.pyplot as plt
from analyze_mandatory_breaks_all_cases import analyze_mandatory_breaks_for_all_cases


def load_single_case_input(case_name):
    """Load input data for a single case"""
    input_folder = os.path.join(os.getcwd(), "input_data", case_name)

    input_data = {}
    for file_name in os.listdir(input_folder):
        if file_name.endswith(".yaml"):
            key_name = os.path.splitext(file_name)[0]
            with open(os.path.join(input_folder, file_name)) as file:
                input_data[key_name] = yaml.safe_load(file)

    return input_data


def main():
    """Main test function"""

    # Load just one case for testing
    case_name = "case_20251028_091344_var_var"
    print(f"Loading input data from: input_data/{case_name}/")

    input_data = load_single_case_input(case_name)

    print(f"Loaded {len(input_data)} input data files")
    print(f"Keys: {list(input_data.keys())[:10]}...")

    # Check if MandatoryBreaks exists
    if 'MandatoryBreaks' in input_data:
        breaks = input_data['MandatoryBreaks']
        print(f"\nMandatoryBreaks loaded: {len(breaks)} breaks found")
        if breaks:
            print(f"First break example: {breaks[0]}")
    else:
        print("\nERROR: No MandatoryBreaks found in input data!")
        return

    # Create mock loaded_runs structure
    loaded_runs = {
        case_name: {
            "input_data": input_data,
            "output_data": {}
        }
    }

    case_labels = {
        case_name: "Test Case"
    }

    # Run the analysis
    print("\n" + "="*80)
    print("Running mandatory breaks analysis...")
    print("="*80)

    fig, stats = analyze_mandatory_breaks_for_all_cases(loaded_runs, case_labels)

    # Create figures directory if it doesn't exist
    os.makedirs('figures', exist_ok=True)

    # Save the figure
    output_path = 'figures/mandatory_breaks_test_simple.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\nFigure saved to: {output_path}")

    plt.show()

    print("\n" + "="*80)
    print("Test completed successfully!")
    print("="*80)


if __name__ == "__main__":
    main()
