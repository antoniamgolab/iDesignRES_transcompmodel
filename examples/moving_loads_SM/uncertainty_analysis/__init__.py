# Uncertainty Analysis Framework for TransComp Model
# This framework applies parameter variations ON TOP of the base preprocessing
# without modifying SM_preprocessing.py

"""
Uncertainty Analysis Framework
==============================

This framework enables systematic uncertainty analysis by:
1. Using SM_preprocessing.py to generate base case (UNCHANGED)
2. Applying multipliers/adjustments to YAML files post-preprocessing
3. Running multiple scenarios with sampled parameters
4. Collecting and analyzing results

Key principle: SM_preprocessing.py values are HOLY - never modified.

Components:
-----------
- parameter_sampler.py: Defines parameter distributions and sampling methods
  (Latin Hypercube, Factorial, One-At-a-Time, Random)

- yaml_modifier.py: Applies parameter multipliers to YAML input files
  (electricity price, carbon price, charging markup, BEV tech costs)

- batch_runner.py: Generates Julia batch script and orchestrates runs

- results_analyzer.py: Collects results and computes sensitivity/robustness

- run_pipeline.py: Main entry point for the complete workflow

Usage:
------
    # RECOMMENDED: Use GENeSYS-based pipeline with actual scenario data
    python -m uncertainty_analysis.run_genesys_pipeline --base-case input_data/case_nuts2_complete

    # Or with custom parameters:
    python -m uncertainty_analysis.run_genesys_pipeline -b input_data/case_nuts2_complete --design factorial --carbon 0 100 --markup 0 0.25

    # Alternative: Generic pipeline with arbitrary multipliers
    python -m uncertainty_analysis.run_pipeline --base-case input_data/case_nuts2_complete -n 20

GENeSYS-MOD Scenarios:
---------------------
The GENeSYS-based approach uses actual electricity price scenarios:
- Go RES v1.2 (base case, multiplier = 1.000)
- NECPEssentials v1.2 (multiplier ≈ 0.705)
- REPowerEU++ v1.2 (multiplier ≈ 0.659)
- Trinity v1.2 (multiplier ≈ 0.615)
"""

# Generic sampler (arbitrary multipliers)
from .parameter_sampler import ParameterSampler, ParameterDistribution, UncertaintyScenario
from .yaml_modifier import YAMLModifier
from .run_pipeline import run_full_pipeline

# GENeSYS-based sampler (recommended)
from .genesys_scenario_sampler import (
    GENeSYSScenarioSampler,
    ScenarioBasedUncertaintyCase,
    GENESYS_SCENARIOS,
    BASE_SCENARIO,
    CARBON_PRICE_TRAJECTORIES,
    get_carbon_price_trajectory
)
from .yaml_modifier_genesys import YAMLModifierGENeSYS
from .run_genesys_pipeline import run_genesys_pipeline

# Common modules
from .batch_runner import BatchRunner, create_batch_runner_from_scenarios
from .results_analyzer import ResultsAnalyzer, analyze_uncertainty_results

__all__ = [
    # Generic approach
    'ParameterSampler',
    'ParameterDistribution',
    'UncertaintyScenario',
    'YAMLModifier',
    'run_full_pipeline',
    # GENeSYS-based approach (recommended)
    'GENeSYSScenarioSampler',
    'ScenarioBasedUncertaintyCase',
    'YAMLModifierGENeSYS',
    'run_genesys_pipeline',
    'GENESYS_SCENARIOS',
    'BASE_SCENARIO',
    'CARBON_PRICE_TRAJECTORIES',
    'get_carbon_price_trajectory',
    # Common
    'BatchRunner',
    'create_batch_runner_from_scenarios',
    'ResultsAnalyzer',
    'analyze_uncertainty_results',
]
