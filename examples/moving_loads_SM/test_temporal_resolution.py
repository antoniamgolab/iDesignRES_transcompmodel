"""
Test script for variable temporal resolution implementation.

This script validates that the preprocessing changes correctly handle
different time_step values (annual, biennial, quinquennial).

Usage:
    python test_temporal_resolution.py
"""

import sys
from pathlib import Path

# Add the current directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from SM_preprocessing_nuts2_complete import CompleteSMNUTS2Preprocessor


def test_vehicle_stock_generation():
    """Test that vehicle stock is generated correctly for different time_steps."""
    print("="*80)
    print("TESTING VARIABLE TEMPORAL RESOLUTION")
    print("="*80)

    # Create a dummy preprocessor instance
    data_dir = Path(__file__).parent / "data" / "Trucktraffic_NUTS3"
    output_dir = Path(__file__).parent / "test_output"

    preprocessor = CompleteSMNUTS2Preprocessor(str(data_dir), str(output_dir))

    # Test parameters
    traffic_flow = 1000.0  # tkm/year
    distance = 500.0  # km
    start_id = 1
    y_init = 2020
    prey_y = 10

    # Calculate expected number of vehicles
    nb_vehicles = traffic_flow * (distance / (13.6 * 136750))

    print(f"\nTest Configuration:")
    print(f"  Traffic flow: {traffic_flow} tkm/year")
    print(f"  Distance: {distance} km")
    print(f"  Expected vehicles: {nb_vehicles:.6f}")
    print(f"  y_init: {y_init}, prey_y: {prey_y}")
    print(f"  Pre-period: {y_init - prey_y} to {y_init - 1}")

    # Test configurations
    test_cases = [
        {"time_step": 1, "name": "Annual", "expected_years": 10, "expected_factor": 0.10},
        {"time_step": 2, "name": "Biennial", "expected_years": 5, "expected_factor": 0.20},
        {"time_step": 5, "name": "Quinquennial", "expected_years": 2, "expected_factor": 0.50},
    ]

    all_passed = True

    for test_case in test_cases:
        time_step = test_case["time_step"]
        name = test_case["name"]
        expected_years = test_case["expected_years"]
        expected_factor = test_case["expected_factor"]

        print("\n" + "-"*80)
        print(f"TEST CASE: {name} (time_step={time_step})")
        print("-"*80)

        # Reset preprocessor state
        preprocessor.initial_vehicle_stock = []
        preprocessor.time_step = time_step

        # Generate vehicle stock
        vehicle_ids = preprocessor._create_vehicle_stock(
            traffic_flow, distance, start_id, y_init, prey_y
        )

        # Get created stock entries
        stock_entries = preprocessor.initial_vehicle_stock

        # Extract years
        years = [entry['year_of_purchase'] for entry in stock_entries]
        stocks = [entry['stock'] for entry in stock_entries]

        # Calculate total stock
        total_stock = sum(stocks)

        # Expected years
        expected_year_list = list(range(y_init - prey_y, y_init, time_step))

        # Validate
        passed = True

        # Check 1: Number of entries
        if len(stock_entries) != expected_years:
            print(f"  [FAIL] Expected {expected_years} stock entries, got {len(stock_entries)}")
            passed = False
            all_passed = False
        else:
            print(f"  [PASS] Correct number of stock entries ({len(stock_entries)})")

        # Check 2: Years match expected
        if years != expected_year_list:
            print(f"  [FAIL] Years don't match")
            print(f"    Expected: {expected_year_list}")
            print(f"    Got:      {years}")
            passed = False
            all_passed = False
        else:
            print(f"  [PASS] Years correct: {years}")

        # Check 3: Each stock entry has correct proportion
        expected_stock_per_entry = nb_vehicles * expected_factor
        for i, stock in enumerate(stocks):
            if abs(stock - expected_stock_per_entry) > 1e-5:
                print(f"  [FAIL] Stock entry {i} has wrong value")
                print(f"    Expected: {expected_stock_per_entry:.6f}")
                print(f"    Got:      {stock:.6f}")
                passed = False
                all_passed = False
                break
        else:
            print(f"  [PASS] Each entry has {expected_factor*100:.0f}% of vehicles ({expected_stock_per_entry:.6f})")

        # Check 4: Total stock equals expected vehicles (allow small rounding error)
        if abs(total_stock - nb_vehicles) > 0.001:  # Relaxed tolerance for rounding
            print(f"  [FAIL] Total stock doesn't match expected")
            print(f"    Expected: {nb_vehicles:.6f}")
            print(f"    Got:      {total_stock:.6f}")
            passed = False
            all_passed = False
        else:
            print(f"  [PASS] Total stock = {total_stock:.6f} (100% of vehicles)")

        # Check 5: Vehicle IDs are correct (IDs skip by 2 because BEV IDs are reserved but not created)
        # Expected IDs: [1, 3, 5, ...] for ICEV (BEV gets even IDs but entries not created)
        expected_ids = list(range(start_id, start_id + 2*expected_years, 2))
        actual_ids = [entry['id'] for entry in stock_entries]
        if actual_ids != expected_ids:
            print(f"  [FAIL] Vehicle IDs don't match")
            print(f"    Expected: {expected_ids}")
            print(f"    Got:      {actual_ids}")
            passed = False
            all_passed = False
        else:
            print(f"  [PASS] Vehicle IDs correct (skipping BEV IDs): {actual_ids}")

        if passed:
            print(f"\n  [PASS] {name} test PASSED")
        else:
            print(f"\n  [FAIL] {name} test FAILED")

    print("\n" + "="*80)
    if all_passed:
        print("[PASS] ALL TESTS PASSED!")
        print("="*80)
        print("\nVariable temporal resolution is working correctly.")
        print("Ready to proceed with Julia implementation.")
        return True
    else:
        print("[FAIL] SOME TESTS FAILED")
        print("="*80)
        print("\nPlease review the failures above and fix the implementation.")
        return False


def test_model_params():
    """Test that Model params include time_step."""
    print("\n" + "="*80)
    print("TESTING MODEL PARAMETERS")
    print("="*80)

    data_dir = Path(__file__).parent / "data" / "Trucktraffic_NUTS3"
    output_dir = Path(__file__).parent / "test_output"

    # Import the SM_preprocessing to test generate_model_params
    from SM_preprocessing import SMParameterGenerator

    preprocessor = SMParameterGenerator()
    model_params = preprocessor.generate_model_params()

    print("\nModel parameters:")
    for key, value in model_params.items():
        print(f"  {key}: {value}")

    # Validate time_step exists
    if 'time_step' not in model_params:
        print("\n[FAIL] FAIL: 'time_step' not found in Model parameters")
        return False
    else:
        print(f"\n[PASS] PASS: 'time_step' found in Model parameters")
        print(f"  Value: {model_params['time_step']}")

    # Validate default value
    if model_params['time_step'] != 1:
        print(f"[FAIL] FAIL: Default time_step should be 1, got {model_params['time_step']}")
        return False
    else:
        print(f"[PASS] PASS: Default time_step is 1 (annual resolution)")

    print("\n" + "="*80)
    print("[PASS] MODEL PARAMETERS TEST PASSED")
    print("="*80)
    return True


def test_edge_cases():
    """Test edge cases for temporal resolution."""
    print("\n" + "="*80)
    print("TESTING EDGE CASES")
    print("="*80)

    data_dir = Path(__file__).parent / "data" / "Trucktraffic_NUTS3"
    output_dir = Path(__file__).parent / "test_output"

    preprocessor = CompleteSMNUTS2Preprocessor(str(data_dir), str(output_dir))

    traffic_flow = 1000.0
    distance = 500.0
    start_id = 1
    y_init = 2020
    prey_y = 10

    nb_vehicles = traffic_flow * (distance / (13.6 * 136750))

    # Edge case 1: time_step larger than prey_y
    print("\nEdge Case 1: time_step=15 (larger than prey_y=10)")
    preprocessor.initial_vehicle_stock = []
    preprocessor.time_step = 15

    vehicle_ids = preprocessor._create_vehicle_stock(
        traffic_flow, distance, start_id, y_init, prey_y
    )

    stock_entries = preprocessor.initial_vehicle_stock
    years = [entry['year_of_purchase'] for entry in stock_entries]
    total_stock = sum([entry['stock'] for entry in stock_entries])

    print(f"  Generated {len(stock_entries)} stock entries")
    print(f"  Years: {years}")
    print(f"  Total stock: {total_stock:.6f} (expected: {nb_vehicles:.6f})")

    if len(stock_entries) == 1 and years == [2010] and abs(total_stock - nb_vehicles) < 1e-5:
        print("  [PASS] PASS: Correctly generated single entry with 100% of vehicles")
    else:
        print("  [FAIL] FAIL: Edge case handling incorrect")
        return False

    # Edge case 2: time_step=10 (equals prey_y)
    print("\nEdge Case 2: time_step=10 (equals prey_y=10)")
    preprocessor.initial_vehicle_stock = []
    preprocessor.time_step = 10

    vehicle_ids = preprocessor._create_vehicle_stock(
        traffic_flow, distance, start_id, y_init, prey_y
    )

    stock_entries = preprocessor.initial_vehicle_stock
    years = [entry['year_of_purchase'] for entry in stock_entries]
    total_stock = sum([entry['stock'] for entry in stock_entries])

    print(f"  Generated {len(stock_entries)} stock entries")
    print(f"  Years: {years}")
    print(f"  Total stock: {total_stock:.6f} (expected: {nb_vehicles:.6f})")

    if len(stock_entries) == 1 and years == [2010] and abs(total_stock - nb_vehicles) < 1e-5:
        print("  [PASS] PASS: Correctly generated single entry with 100% of vehicles")
    else:
        print("  [FAIL] FAIL: Edge case handling incorrect")
        return False

    print("\n" + "="*80)
    print("[PASS] EDGE CASES TEST PASSED")
    print("="*80)
    return True


def main():
    """Run all tests."""
    print("\n")
    print("=" * 80)
    print("  TEMPORAL RESOLUTION TEST SUITE".center(80))
    print("=" * 80)

    # Run tests
    test1_passed = test_vehicle_stock_generation()
    test2_passed = test_model_params()
    test3_passed = test_edge_cases()

    # Summary
    print("\n\n")
    print("=" * 80)
    print("  TEST SUMMARY".center(80))
    print("=" * 80)

    print("\nTest Results:")
    print(f"  1. Vehicle Stock Generation: {'[PASS] PASS' if test1_passed else '[FAIL] FAIL'}")
    print(f"  2. Model Parameters:         {'[PASS] PASS' if test2_passed else '[FAIL] FAIL'}")
    print(f"  3. Edge Cases:               {'[PASS] PASS' if test3_passed else '[FAIL] FAIL'}")

    all_passed = test1_passed and test2_passed and test3_passed

    if all_passed:
        print("\n" + "="*80)
        print("[SUCCESS] SUCCESS! All tests passed!")
        print("="*80)
        print("\nThe preprocessing implementation is correct and ready to use.")
        print("\nNext steps:")
        print("  1. Run actual preprocessing with time_step=1 (baseline)")
        print("  2. Run with time_step=2 to test biennial resolution")
        print("  3. Proceed with Julia implementation (see TEMPORAL_RESOLUTION_JULIA_PLAN.md)")
        return 0
    else:
        print("\n" + "="*80)
        print("[FAIL] FAILURE: Some tests failed")
        print("="*80)
        print("\nPlease review the failures and fix the implementation.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
