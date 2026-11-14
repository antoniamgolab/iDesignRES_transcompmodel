"""
GENeSYS-Based Uncertainty Analysis Pipeline
===========================================

Main entry point for uncertainty analysis using GENeSYS-MOD scenarios.

This pipeline uses actual electricity price scenarios from GENeSYS-MOD:
- Go RES v1.2 (base case, multiplier = 1.0)
- NECPEssentials v1.2 (multiplier ≈ 0.70)
- REPowerEU++ v1.2 (multiplier ≈ 0.66)
- Trinity v1.2 (multiplier ≈ 0.62)

Each GENeSYS scenario includes an internally consistent carbon budget constraint,
so carbon prices are NOT varied independently (they are already embedded in the
electricity prices and overall system optimization of each scenario).
See: Camarinha-Matos et al. (2025), https://doi.org/10.1016/j.rser.2025.115758

Combined with:
- Charging markup: 15-30% (CPO service margin on electricity)
- Diesel markup: 50% (EU average taxation on diesel, fixed)
- BEV technology costs: ±30% at 2060 (time-dependent uncertainty growing from 0% at 2020)

The technology cost uncertainty is applied with growing deviation over time,
reflecting that near-term BEV costs are more certain while long-term projections
have higher uncertainty.

IMPORTANT: SM_preprocessing.py values are HOLY - never modified directly.
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

# Handle imports for both direct execution and module import
if __name__ == "__main__":
    # Direct execution - add parent directory to path
    _script_dir = Path(__file__).parent
    sys.path.insert(0, str(_script_dir))
    from genesys_scenario_sampler import GENeSYSScenarioSampler, ScenarioBasedUncertaintyCase
    from yaml_modifier_genesys import YAMLModifierGENeSYS
    from batch_runner import BatchRunner
    from results_analyzer import analyze_uncertainty_results
else:
    # Module import
    from .genesys_scenario_sampler import GENeSYSScenarioSampler, ScenarioBasedUncertaintyCase
    from .yaml_modifier_genesys import YAMLModifierGENeSYS
    from .batch_runner import BatchRunner
    from .results_analyzer import analyze_uncertainty_results


def run_preprocessing(
    nuts_data_dir: str = "input_data/fixed_nuts_2",
    output_case_name: str = "case_nuts2_complete",
    electricity_prices_variable: bool = True,
    network_costs_variable: bool = True,
    include_rail_mode: bool = False,
    filter_low_volume: bool = True,
    min_freight_threshold: float = 100.0
) -> Path:
    """
    Run SM_preprocessing.py to create a base case folder.

    This is an optional integrated step that generates the base case
    from raw NUTS data before scenario generation.

    Parameters:
    -----------
    nuts_data_dir : str
        Directory with preprocessed NUTS data
    output_case_name : str
        Name for the output case folder
    electricity_prices_variable : bool
        Use location-specific electricity prices
    network_costs_variable : bool
        Use location-specific network costs
    include_rail_mode : bool
        Include rail as transport mode
    filter_low_volume : bool
        Filter out low-volume OD-pairs
    min_freight_threshold : float
        Minimum freight threshold (trucks/year)

    Returns:
    --------
    Path : Path to the generated base case folder
    """
    import sys

    # Add parent directory to path for importing SM_preprocessing
    script_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(script_dir))

    from SM_preprocessing import SMParameterGenerator

    print("\n" + "=" * 80)
    print("STEP 0: RUNNING SM_PREPROCESSING")
    print("=" * 80)
    print(f"  Input data: {nuts_data_dir}")
    print(f"  Output case: {output_case_name}")
    print(f"  Electricity prices: {'variable' if electricity_prices_variable else 'uniform'}")
    print(f"  Network costs: {'variable' if network_costs_variable else 'uniform'}")
    print(f"  Rail mode: {'included' if include_rail_mode else 'excluded'}")
    print(f"  Low-volume filter: {'enabled' if filter_low_volume else 'disabled'}")
    if filter_low_volume:
        print(f"  Threshold: {min_freight_threshold:,.0f} trucks/year")

    preprocessor = SMParameterGenerator(
        nuts3_data_dir=nuts_data_dir,
        case_name=output_case_name,
        electricity_prices_variable=electricity_prices_variable,
        network_costs_variable=network_costs_variable,
        include_rail_mode=include_rail_mode,
        filter_low_volume=filter_low_volume,
        min_freight_threshold=min_freight_threshold
    )

    preprocessor.run()

    print(f"\n  Base case created: {preprocessor.output_dir}")
    return preprocessor.output_dir


def run_genesys_pipeline(
    base_case_path: Path,
    genesys_data_path: Path,
    output_base_path: Path,
    design: str = 'factorial',
    n_samples: int = 20,
    seed: int = 42,
    charging_markups: list = None,
    tech_multipliers: list = None,
    run_model: bool = False,
    julia_executable: str = 'julia',
    # New preprocessing options
    run_preprocessing_first: bool = False,
    preprocessing_nuts_data: str = "input_data/fixed_nuts_2",
    preprocessing_elec_variable: bool = True,
    preprocessing_network_variable: bool = True,
    preprocessing_include_rail: bool = False,
    preprocessing_filter_volume: bool = True,
    preprocessing_threshold: float = 1000.0
):
    """
    Run uncertainty analysis using GENeSYS-MOD scenarios.

    Parameters:
    -----------
    base_case_path : Path
        Path to base case input_data folder (from SM_preprocessing.py).
        Ignored if run_preprocessing_first=True.
    genesys_data_path : Path
        Path to GENeSYS-MOD output_endogenous_fuelcosts.csv
    output_base_path : Path
        Base path for outputs
    design : str
        Experimental design: 'factorial', 'lhs', 'oat'
    n_samples : int
        Number of samples for LHS design
    seed : int
        Random seed
    charging_markups : list
        Charging markup levels (default: [0.15, 0.30])
    tech_multipliers : list
        Tech cost multiplier levels at 2060 (default: [0.7, 1.0, 1.3])
        These are applied with time-dependent uncertainty: 1.0 at 2020,
        interpolating to the specified value at 2060.
    run_model : bool
        Whether to run Julia model
    julia_executable : str
        Path to Julia
    run_preprocessing_first : bool
        If True, run SM_preprocessing.py first to create the base case.
        The base_case_path is then set to the generated folder.
    preprocessing_nuts_data : str
        Input NUTS data directory for preprocessing
    preprocessing_elec_variable : bool
        Use variable electricity prices in preprocessing
    preprocessing_network_variable : bool
        Use variable network costs in preprocessing
    preprocessing_include_rail : bool
        Include rail mode in preprocessing
    preprocessing_filter_volume : bool
        Filter low-volume OD-pairs in preprocessing
    preprocessing_threshold : float
        Minimum freight threshold for filtering

    Note: Carbon prices are NOT independently varied because they are already
    embedded in each GENeSYS-MOD scenario through their carbon budget constraints.

    Note: Technology cost uncertainty grows with time to reflect that near-term
    costs are more certain than long-term projections.
    """
    print("=" * 80)
    print("GENeSYS-BASED UNCERTAINTY ANALYSIS PIPELINE")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 80)

    # =========================================================================
    # STEP 0 (Optional): Run SM_preprocessing to create base case
    # =========================================================================
    if run_preprocessing_first:
        base_case_path = run_preprocessing(
            nuts_data_dir=preprocessing_nuts_data,
            output_case_name="case_nuts2_complete",
            electricity_prices_variable=preprocessing_elec_variable,
            network_costs_variable=preprocessing_network_variable,
            include_rail_mode=preprocessing_include_rail,
            filter_low_volume=preprocessing_filter_volume,
            min_freight_threshold=preprocessing_threshold
        )
    else:
        base_case_path = Path(base_case_path)

    genesys_data_path = Path(genesys_data_path)
    output_base_path = Path(output_base_path)

    # Paths
    scenarios_path = output_base_path / "input_data" / "uncertainty_scenarios"
    results_path = output_base_path / "results" / "uncertainty_analysis"

    # =========================================================================
    # STEP 1: Load GENeSYS data and create sampler
    # =========================================================================
    print("\n=== STEP 1: Loading GENeSYS-MOD Scenario Data ===")

    if not genesys_data_path.exists():
        raise FileNotFoundError(f"GENeSYS data not found: {genesys_data_path}")

    sampler = GENeSYSScenarioSampler(genesys_data_path, seed=seed)

    print("\nGENeSYS Scenario Multipliers (relative to Go RES v1.2):")
    for name, mult in sampler.get_scenario_multipliers().items():
        print(f"  {name}: {mult:.3f}x")

    # =========================================================================
    # STEP 2: Generate uncertainty cases
    # =========================================================================
    print(f"\n=== STEP 2: Generating Cases ({design} design) ===")

    if design == 'factorial':
        # Default parameter levels
        if charging_markups is None:
            # Charging markup represents CPO service fees and profit margin
            # 15% = competitive mature market (depot charging, high-volume contracts)
            # 30% = current public charging conditions (based on Milence 2024 pricing)
            # Reference: Lanz et al. (2022) Nature Communications, doi:10.1038/s41467-022-32835-7
            charging_markups = [0.15, 0.30]
        if tech_multipliers is None:
            tech_multipliers = [0.7, 1.0, 1.3]

        # Note: Carbon prices are NOT varied independently because each GENeSYS
        # scenario already embeds consistent carbon budget constraints
        # Diesel markup defaults to 50% (EU average taxation) - single value, not varied
        cases = sampler.generate_discrete_genesys_cases(
            charging_markups=charging_markups,
            tech_multipliers=tech_multipliers
            # diesel_markups defaults to [0.50] in sampler
        )

        print(f"\nFactorial design:")
        print(f"  4 GENeSYS scenarios × "
              f"{len(charging_markups)} charging markup × {len(tech_multipliers)} tech = {len(cases)} cases")

    elif design == 'lhs':
        cases = sampler.generate_lhs_within_genesys_bounds(n_samples=n_samples)
        print(f"\nLatin Hypercube design: {len(cases)} samples")

    elif design == 'oat':
        cases = sampler.generate_oat_sensitivity(n_levels=5)
        print(f"\nOne-At-a-Time design: {len(cases)} cases")

    else:
        raise ValueError(f"Unknown design: {design}")

    # Save cases to JSON
    cases_json = scenarios_path / "cases.json"
    scenarios_path.mkdir(parents=True, exist_ok=True)
    sampler.save_cases(cases, cases_json)

    # =========================================================================
    # STEP 3: Create scenario input folders
    # =========================================================================
    print("\n=== STEP 3: Creating Scenario Input Folders ===")

    modifier = YAMLModifierGENeSYS(base_case_path, scenarios_path, sampler)
    scenario_folders = modifier.apply_all_cases(cases)

    print(f"\nCreated {len(scenario_folders)} scenario folders")

    # =========================================================================
    # STEP 4: Generate Julia batch script
    # =========================================================================
    print("\n=== STEP 4: Generating Julia Batch Script ===")

    runner = BatchRunner(
        scenario_folders=scenario_folders,
        results_base_path=results_path
    )

    script_dir = base_case_path.parent  # examples/moving_loads_SM
    julia_script = runner.generate_julia_batch_script(script_dir)

    print(f"\nJulia batch script: {julia_script}")

    # =========================================================================
    # STEP 5: Run model (optional)
    # =========================================================================
    if run_model:
        print("\n=== STEP 5: Running Model ===")
        print(f"Running {len(cases)} scenarios - this may take many hours...")

        results = runner.run(julia_executable=julia_executable)

        successful = sum(1 for r in results if r.status == 'SUCCESS')
        print(f"\nCompleted: {successful}/{len(results)} successful")

    else:
        print("\n=== STEP 5: Model Run SKIPPED ===")
        print("To run the model:")
        print(f"  julia {julia_script}")

    # =========================================================================
    # STEP 6: Analyze results (if available)
    # =========================================================================
    print("\n=== STEP 6: Results Analysis ===")

    if results_path.exists() and any(results_path.glob("scenario_*")):
        analysis_path = output_base_path / "analysis"
        analyzer = analyze_uncertainty_results(
            results_path=results_path,
            scenarios_json_path=cases_json,
            output_path=analysis_path
        )
    else:
        print("No results found yet. Run the model first.")

    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "=" * 80)
    print("PIPELINE COMPLETE")
    print("=" * 80)
    print(f"\nOutputs:")
    print(f"  Cases JSON:        {cases_json}")
    print(f"  Scenario folders:  {scenarios_path}")
    print(f"  Julia script:      {julia_script}")
    print(f"  Results:           {results_path}")

    # Print case summary table
    print("\n=== Case Summary ===")
    print(f"{'ID':>4} | {'GENeSYS Scenario':<22} | {'Elec':>6} | {'ChgMk':>6} | {'DslMk':>6} | {'Tech':>5}")
    print("-" * 70)
    for c in cases[:10]:  # First 10
        print(f"{c.case_id:4d} | {c.genesys_scenario:<22} | "
              f"{c.electricity_price_multiplier:6.3f} | "
              f"{c.charging_markup:6.0%} | {c.diesel_markup:6.0%} | {c.tech_cost_multiplier:5.2f}")
    if len(cases) > 10:
        print(f"... and {len(cases) - 10} more cases")

    return {
        'cases_json': cases_json,
        'scenario_folders': scenario_folders,
        'julia_script': julia_script,
        'results_path': results_path,
        'n_cases': len(cases)
    }


def main():
    parser = argparse.ArgumentParser(
        description='Run GENeSYS-based uncertainty analysis for TransComp model',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # STANDARD WORKFLOW: Use existing base case
  # Factorial design with default parameters (24 cases = 4 scenarios × 2 markups × 3 tech)
  python run_genesys_pipeline.py --base-case input_data/case_nuts2_complete

  # Reduced factorial (8 cases)
  python run_genesys_pipeline.py -b input_data/case_nuts2_complete --markup 0.15 0.30 --tech 1.0

  # LHS design with 30 samples
  python run_genesys_pipeline.py -b input_data/case_nuts2_complete --design lhs -n 30

  # INTEGRATED WORKFLOW: Run SM_preprocessing first, then generate scenarios
  # Full integrated pipeline (creates base case + 24 scenarios in one command)
  python run_genesys_pipeline.py --integrated --nuts-data input_data/fixed_nuts_2

  # Integrated with uniform electricity prices
  python run_genesys_pipeline.py --integrated --uniform-elec

  # Integrated with rail mode included
  python run_genesys_pipeline.py --integrated --include-rail

Note: Carbon prices are NOT varied independently - each GENeSYS scenario already
embeds consistent carbon budget constraints.
        """
    )

    parser.add_argument(
        '--base-case', '-b',
        type=Path,
        default=Path('input_data/case_nuts2_complete'),
        help='Path to base case input folder'
    )

    parser.add_argument(
        '--genesys', '-g',
        type=Path,
        default=Path('data/GENeSYS-MOD_EU-EnVis-2060_v1.2.0_native/output_endogenous_fuelcosts.csv'),
        help='Path to GENeSYS fuel costs CSV'
    )

    parser.add_argument(
        '--output', '-o',
        type=Path,
        default=Path('.'),
        help='Base output path'
    )

    parser.add_argument(
        '--design', '-d',
        choices=['factorial', 'lhs', 'oat'],
        default='factorial',
        help='Experimental design'
    )

    parser.add_argument(
        '-n', '--n-samples',
        type=int,
        default=20,
        help='Number of samples for LHS design'
    )

    parser.add_argument(
        '--seed', '-s',
        type=int,
        default=42,
        help='Random seed'
    )

    parser.add_argument(
        '--markup',
        type=float,
        nargs='+',
        default=None,
        help='Charging markup levels (e.g., --markup 0.15 0.30)'
    )

    parser.add_argument(
        '--tech',
        type=float,
        nargs='+',
        default=None,
        help='Tech cost multiplier levels (e.g., --tech 0.9 1.0 1.1)'
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
        help='Path to Julia executable'
    )

    # Integrated preprocessing options
    parser.add_argument(
        '--integrated', '-i',
        action='store_true',
        help='Run SM_preprocessing first to create base case (integrated pipeline)'
    )

    parser.add_argument(
        '--nuts-data',
        type=str,
        default='input_data/fixed_nuts_2',
        help='NUTS data directory for preprocessing (only with --integrated)'
    )

    parser.add_argument(
        '--uniform-elec',
        action='store_true',
        help='Use uniform electricity prices in preprocessing (default: variable)'
    )

    parser.add_argument(
        '--uniform-network',
        action='store_true',
        help='Use uniform network costs in preprocessing (default: variable)'
    )

    parser.add_argument(
        '--include-rail',
        action='store_true',
        help='Include rail mode in preprocessing'
    )

    parser.add_argument(
        '--no-volume-filter',
        action='store_true',
        help='Disable low-volume OD-pair filtering in preprocessing'
    )

    parser.add_argument(
        '--volume-threshold',
        type=float,
        default=100.0,
        help='Minimum freight threshold for filtering (default: 100 trucks/year)'
    )

    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Delete existing scenario folders instead of backing them up (default: backup with timestamp)'
    )

    args = parser.parse_args()

    run_genesys_pipeline(
        base_case_path=args.base_case,
        genesys_data_path=args.genesys,
        output_base_path=args.output,
        design=args.design,
        n_samples=args.n_samples,
        seed=args.seed,
        charging_markups=args.markup,
        tech_multipliers=args.tech,
        run_model=args.run,
        julia_executable=args.julia,
        # Integrated preprocessing options
        run_preprocessing_first=args.integrated,
        preprocessing_nuts_data=args.nuts_data,
        preprocessing_elec_variable=not args.uniform_elec,
        preprocessing_network_variable=not args.uniform_network,
        preprocessing_include_rail=args.include_rail,
        preprocessing_filter_volume=not args.no_volume_filter,
        preprocessing_threshold=args.volume_threshold
    )


if __name__ == "__main__":
    main()
