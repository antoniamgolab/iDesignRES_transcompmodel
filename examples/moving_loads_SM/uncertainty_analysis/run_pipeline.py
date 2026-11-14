"""
Uncertainty Analysis Pipeline
==============================

Main entry point for running the complete uncertainty analysis workflow.

Workflow:
1. Generate parameter samples (Latin Hypercube or other design)
2. Apply parameters to create scenario input folders
3. Generate and run Julia batch script
4. Collect and analyze results

IMPORTANT: This pipeline does NOT modify SM_preprocessing.py or its outputs.
Base case values are preserved - only multipliers/adjustments are applied.
"""

import argparse
from pathlib import Path
from datetime import datetime

from .parameter_sampler import ParameterSampler, ParameterDistribution
from .yaml_modifier import YAMLModifier
from .batch_runner import BatchRunner, create_batch_runner_from_scenarios
from .results_analyzer import analyze_uncertainty_results


def run_full_pipeline(
    base_case_path: Path,
    output_base_path: Path,
    n_scenarios: int = 10,
    sampling_method: str = 'lhs',
    seed: int = 42,
    run_model: bool = False,
    julia_executable: str = 'julia'
):
    """
    Run the complete uncertainty analysis pipeline.

    Parameters:
    -----------
    base_case_path : Path
        Path to base case input_data folder (from SM_preprocessing.py)
    output_base_path : Path
        Base path for outputs (scenarios, results, analysis)
    n_scenarios : int
        Number of scenarios to generate
    sampling_method : str
        Sampling method: 'lhs' (Latin Hypercube), 'factorial', 'oat', 'random'
    seed : int
        Random seed for reproducibility
    run_model : bool
        Whether to actually run the Julia model (False = generate script only)
    julia_executable : str
        Path to Julia executable
    """
    print("=" * 80)
    print("UNCERTAINTY ANALYSIS PIPELINE")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 80)

    base_case_path = Path(base_case_path)
    output_base_path = Path(output_base_path)

    # Paths
    scenarios_path = output_base_path / "input_data" / "uncertainty_scenarios"
    results_path = output_base_path / "results" / "uncertainty_analysis"

    # =========================================================================
    # STEP 1: Generate parameter samples
    # =========================================================================
    print("\n=== STEP 1: Generating Parameter Samples ===")

    sampler = ParameterSampler(seed=seed)

    # Optionally customize parameter distributions here
    # Example: narrower range for electricity price
    # sampler.set_parameter_distribution(
    #     'electricity_price_multiplier',
    #     ParameterDistribution(
    #         name='electricity_price_multiplier',
    #         distribution='uniform',
    #         low=0.9,
    #         high=1.1
    #     )
    # )

    if sampling_method == 'lhs':
        scenarios = sampler.generate_latin_hypercube(n_scenarios)
        print(f"Generated {len(scenarios)} Latin Hypercube samples")
    elif sampling_method == 'factorial':
        # For factorial, n_scenarios is interpreted as levels per parameter
        levels = max(2, int(n_scenarios ** 0.25))  # Approximate
        scenarios = sampler.generate_factorial_design(levels_per_param=levels)
        print(f"Generated {len(scenarios)} factorial design scenarios ({levels} levels)")
    elif sampling_method == 'oat':
        levels = max(3, n_scenarios // 4)
        scenarios = sampler.generate_one_at_a_time(n_levels=levels)
        print(f"Generated {len(scenarios)} OAT scenarios ({levels} levels)")
    else:  # random
        scenarios = sampler.generate_scenarios(n_scenarios)
        print(f"Generated {len(scenarios)} random samples")

    # Save scenarios
    scenarios_json = scenarios_path / "scenarios.json"
    scenarios_path.mkdir(parents=True, exist_ok=True)
    sampler.save_scenarios(scenarios, scenarios_json)

    # =========================================================================
    # STEP 2: Create scenario input folders
    # =========================================================================
    print("\n=== STEP 2: Creating Scenario Input Folders ===")

    modifier = YAMLModifier(base_case_path, scenarios_path)
    scenario_folders = modifier.apply_all_scenarios(scenarios)

    print(f"\nCreated {len(scenario_folders)} scenario folders")

    # =========================================================================
    # STEP 3: Generate batch runner script
    # =========================================================================
    print("\n=== STEP 3: Generating Julia Batch Script ===")

    runner = BatchRunner(
        scenario_folders=scenario_folders,
        results_base_path=results_path
    )

    # Generate the Julia script (goes in the moving_loads_SM directory)
    script_dir = base_case_path.parent  # e.g., examples/moving_loads_SM
    julia_script = runner.generate_julia_batch_script(script_dir)

    print(f"\nJulia batch script: {julia_script}")

    # =========================================================================
    # STEP 4: Run model (optional)
    # =========================================================================
    if run_model:
        print("\n=== STEP 4: Running Model ===")
        print("This may take several hours depending on scenario count...")

        results = runner.run(julia_executable=julia_executable)

        print(f"\nCompleted {len(results)} scenarios")
        for r in results:
            status_str = f"{r.status}"
            if r.status == 'SUCCESS':
                status_str += f" (obj={r.objective_value:.2e})"
            print(f"  Scenario {r.scenario_id}: {status_str}")

    else:
        print("\n=== STEP 4: Model Run SKIPPED ===")
        print("To run the model, execute:")
        print(f"  julia {julia_script}")
        print("\nOr re-run this script with --run flag")

    # =========================================================================
    # STEP 5: Analyze results (if available)
    # =========================================================================
    print("\n=== STEP 5: Results Analysis ===")

    if results_path.exists() and any(results_path.glob("scenario_*")):
        analysis_path = output_base_path / "analysis"
        analyzer = analyze_uncertainty_results(
            results_path=results_path,
            scenarios_json_path=scenarios_json,
            output_path=analysis_path
        )
        print(f"\nAnalysis saved to: {analysis_path}")
    else:
        print("No results found yet. Run the model first.")
        print(f"Results expected at: {results_path}")

    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "=" * 80)
    print("PIPELINE COMPLETE")
    print("=" * 80)
    print(f"\nOutputs:")
    print(f"  Scenarios JSON:    {scenarios_json}")
    print(f"  Scenario folders:  {scenarios_path}")
    print(f"  Julia script:      {julia_script}")
    print(f"  Results:           {results_path}")

    if not run_model:
        print(f"\nNext step: Run the Julia script to execute all scenarios")

    return {
        'scenarios_json': scenarios_json,
        'scenario_folders': scenario_folders,
        'julia_script': julia_script,
        'results_path': results_path
    }


def main():
    parser = argparse.ArgumentParser(
        description='Run uncertainty analysis for TransComp model',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate 20 LHS scenarios (no model run)
  python run_pipeline.py --base-case input_data/case_nuts2_complete -n 20

  # Generate and run 10 scenarios
  python run_pipeline.py --base-case input_data/case_nuts2_complete -n 10 --run

  # Use factorial design with 2 levels (16 scenarios)
  python run_pipeline.py --base-case input_data/case_nuts2_complete --method factorial -n 2
        """
    )

    parser.add_argument(
        '--base-case', '-b',
        type=Path,
        default=Path('input_data/case_nuts2_complete'),
        help='Path to base case input folder (default: input_data/case_nuts2_complete)'
    )

    parser.add_argument(
        '--output', '-o',
        type=Path,
        default=Path('.'),
        help='Base output path (default: current directory)'
    )

    parser.add_argument(
        '-n', '--n-scenarios',
        type=int,
        default=10,
        help='Number of scenarios (default: 10)'
    )

    parser.add_argument(
        '--method', '-m',
        choices=['lhs', 'factorial', 'oat', 'random'],
        default='lhs',
        help='Sampling method (default: lhs = Latin Hypercube)'
    )

    parser.add_argument(
        '--seed', '-s',
        type=int,
        default=42,
        help='Random seed (default: 42)'
    )

    parser.add_argument(
        '--run', '-r',
        action='store_true',
        help='Run the model after generating scenarios'
    )

    parser.add_argument(
        '--julia',
        type=str,
        default='julia',
        help='Path to Julia executable (default: julia)'
    )

    args = parser.parse_args()

    run_full_pipeline(
        base_case_path=args.base_case,
        output_base_path=args.output,
        n_scenarios=args.n_scenarios,
        sampling_method=args.method,
        seed=args.seed,
        run_model=args.run,
        julia_executable=args.julia
    )


if __name__ == "__main__":
    main()
