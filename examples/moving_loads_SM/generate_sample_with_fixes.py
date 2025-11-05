"""
Generate a small sample with the fixed mandatory breaks logic.
This creates a quick test case for visualization.
"""

import sys
from pathlib import Path

# Import the preprocessing class
from SM_preprocessing_nuts2_complete import CompleteSMNUTS2Preprocessor

print("="*80)
print("GENERATING SAMPLE WITH FIXED MANDATORY BREAKS")
print("="*80)
print("\nConfiguration:")
print("  - Tolerance: (1/2) * gap to limit")
print("  - Synthetic nodes for single-node paths")
print("  - Sample size: 200 OD-pairs for quick testing")
print("  - Cross-border only: False (includes domestic Italian routes)")
print("="*80)

# Configuration for quick sample
MAX_ODPAIRS = 200  # Small sample for quick testing
MIN_DISTANCE_KM = None  # No distance filter
CROSS_BORDER_ONLY = False  # Include all routes

# Paths
script_dir = Path(__file__).parent
data_dir = script_dir / "data" / "Trucktraffic_NUTS3"
output_dir = script_dir / "input_data"

# Initialize preprocessor
print("\n[1/6] Initializing preprocessor...")
preprocessor = CompleteSMNUTS2Preprocessor(data_dir, output_dir)

# Run preprocessing with sample configuration
print("\n[2/6] Running preprocessing pipeline...")
preprocessor.run_complete_preprocessing(
    max_odpairs=MAX_ODPAIRS,
    min_distance_km=MIN_DISTANCE_KM,
    cross_border_only=CROSS_BORDER_ONLY,
    aggregate_odpairs=True  # Keep aggregation
)

print("\n[3/6] Generating complete input data for Julia...")
# The rest happens in SM_preprocessing.py when we load and regenerate
from SM_preprocessing import TransportPreprocessor

# Find the generated case directory
case_dirs = sorted(output_dir.glob("case_*"))
if not case_dirs:
    print("ERROR: No case directory found!")
    sys.exit(1)

latest_case = case_dirs[-1]
print(f"[4/6] Loading data from: {latest_case.name}")

# Initialize SM_preprocessing
sm_prep = TransportPreprocessor(data_dir, output_dir)

# Load the nuts2 data
print("[5/6] Loading NUTS2 data and regenerating mandatory breaks...")
components = sm_prep.load_components_from_yaml(latest_case)

# Regenerate mandatory breaks with the fixed algorithm
print("[6/6] Applying fixes:")
print("  - Synthetic nodes for single-node paths")
print("  - Dynamic tolerance (1/2) * gap")
print("  - Saving corrected data...")

# Save updated components
sm_prep.save_components_to_yaml(components, latest_case)

print("\n" + "="*80)
print("SAMPLE GENERATION COMPLETE!")
print("="*80)
print(f"\nOutput directory: {latest_case}")
print(f"\nGenerated files:")
print(f"  - MandatoryBreaks.yaml (corrected)")
print(f"  - Path.yaml")
print(f"  - Odpair.yaml")
print(f"  - GeographicElement.yaml")
print(f"  - And all other input files...")

print("\nNext steps:")
print("  1. Run: python visualize_break_distribution.py")
print("  2. Check: figures/mandatory_breaks_*.png")

print("\n" + "="*80)
