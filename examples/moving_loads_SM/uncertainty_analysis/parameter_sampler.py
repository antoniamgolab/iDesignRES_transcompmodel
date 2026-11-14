"""
Parameter Sampler for Uncertainty Analysis
==========================================

Defines uncertain parameters and their distributions.
Generates sample sets for scenario runs.

Parameters:
- electricity_price_multiplier: Scales all electricity prices (default: 1.0)
- carbon_price: Absolute carbon price in EUR/tCO2 (default: 0)
- charging_markup: Additional markup on charging costs as fraction (default: 0)
- tech_cost_multiplier: Scales BEV technology costs (default: 1.0)
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
import json
from pathlib import Path


@dataclass
class ParameterDistribution:
    """Defines a parameter's uncertainty distribution."""
    name: str
    distribution: str  # 'uniform', 'normal', 'triangular', 'discrete'
    low: float
    high: float
    mode: Optional[float] = None  # For triangular distribution
    discrete_values: Optional[List[float]] = None  # For discrete distribution

    def sample(self, rng: np.random.Generator) -> float:
        """Draw a single sample from the distribution."""
        if self.distribution == 'uniform':
            return rng.uniform(self.low, self.high)
        elif self.distribution == 'normal':
            mean = (self.low + self.high) / 2
            std = (self.high - self.low) / 4  # 95% within range
            return np.clip(rng.normal(mean, std), self.low, self.high)
        elif self.distribution == 'triangular':
            mode = self.mode if self.mode is not None else (self.low + self.high) / 2
            return rng.triangular(self.low, mode, self.high)
        elif self.distribution == 'discrete':
            if self.discrete_values is None:
                raise ValueError("discrete_values must be provided for discrete distribution")
            return rng.choice(self.discrete_values)
        else:
            raise ValueError(f"Unknown distribution: {self.distribution}")


@dataclass
class UncertaintyScenario:
    """A single scenario with sampled parameter values."""
    scenario_id: int
    electricity_price_multiplier: float
    carbon_price: float  # EUR/tCO2
    charging_markup: float  # Fraction (0.0 = no markup, 0.2 = 20% markup)
    tech_cost_multiplier: float  # Multiplier for BEV costs

    def to_dict(self) -> Dict:
        return {
            'scenario_id': self.scenario_id,
            'electricity_price_multiplier': self.electricity_price_multiplier,
            'carbon_price': self.carbon_price,
            'charging_markup': self.charging_markup,
            'tech_cost_multiplier': self.tech_cost_multiplier
        }

    @classmethod
    def from_dict(cls, d: Dict) -> 'UncertaintyScenario':
        return cls(**d)


class ParameterSampler:
    """
    Generates parameter samples for uncertainty analysis.

    Default parameter ranges (can be customized):
    - electricity_price_multiplier: 0.7 - 1.3 (±30% variation)
    - carbon_price: 0 - 200 EUR/tCO2
    - charging_markup: 0.0 - 0.5 (0% - 50% markup)
    - tech_cost_multiplier: 0.8 - 1.2 (±20% variation)
    """

    def __init__(self, seed: int = 42):
        self.rng = np.random.default_rng(seed)

        # Default parameter distributions
        self.parameters = {
            'electricity_price_multiplier': ParameterDistribution(
                name='electricity_price_multiplier',
                distribution='uniform',
                low=0.7,
                high=1.3
            ),
            'carbon_price': ParameterDistribution(
                name='carbon_price',
                distribution='uniform',
                low=0.0,
                high=200.0
            ),
            'charging_markup': ParameterDistribution(
                name='charging_markup',
                distribution='uniform',
                low=0.0,
                high=0.5
            ),
            'tech_cost_multiplier': ParameterDistribution(
                name='tech_cost_multiplier',
                distribution='uniform',
                low=0.8,
                high=1.2
            )
        }

    def set_parameter_distribution(self, param_name: str, distribution: ParameterDistribution):
        """Override the distribution for a specific parameter."""
        if param_name not in self.parameters:
            raise ValueError(f"Unknown parameter: {param_name}")
        self.parameters[param_name] = distribution

    def sample_single(self) -> Dict[str, float]:
        """Generate a single sample of all parameters."""
        return {
            name: dist.sample(self.rng)
            for name, dist in self.parameters.items()
        }

    def generate_scenarios(self, n_scenarios: int) -> List[UncertaintyScenario]:
        """Generate n random scenarios."""
        scenarios = []
        for i in range(n_scenarios):
            sample = self.sample_single()
            scenario = UncertaintyScenario(
                scenario_id=i,
                electricity_price_multiplier=sample['electricity_price_multiplier'],
                carbon_price=sample['carbon_price'],
                charging_markup=sample['charging_markup'],
                tech_cost_multiplier=sample['tech_cost_multiplier']
            )
            scenarios.append(scenario)
        return scenarios

    def generate_latin_hypercube(self, n_scenarios: int) -> List[UncertaintyScenario]:
        """
        Generate scenarios using Latin Hypercube Sampling for better coverage.
        Each parameter range is divided into n equal intervals, and exactly
        one sample is drawn from each interval.
        """
        n_params = len(self.parameters)
        param_names = list(self.parameters.keys())

        # Generate LHS samples (values between 0 and 1)
        lhs_samples = np.zeros((n_scenarios, n_params))
        for i in range(n_params):
            # Create n equally spaced intervals and sample one point from each
            intervals = np.linspace(0, 1, n_scenarios + 1)
            points = self.rng.uniform(intervals[:-1], intervals[1:])
            self.rng.shuffle(points)
            lhs_samples[:, i] = points

        # Transform to actual parameter values
        scenarios = []
        for i in range(n_scenarios):
            sample = {}
            for j, name in enumerate(param_names):
                dist = self.parameters[name]
                # Map [0,1] to [low, high]
                sample[name] = dist.low + lhs_samples[i, j] * (dist.high - dist.low)

            scenario = UncertaintyScenario(
                scenario_id=i,
                electricity_price_multiplier=sample['electricity_price_multiplier'],
                carbon_price=sample['carbon_price'],
                charging_markup=sample['charging_markup'],
                tech_cost_multiplier=sample['tech_cost_multiplier']
            )
            scenarios.append(scenario)

        return scenarios

    def generate_factorial_design(self, levels_per_param: int = 2) -> List[UncertaintyScenario]:
        """
        Generate a full factorial design with specified levels per parameter.
        For 4 parameters with 2 levels each: 2^4 = 16 scenarios
        For 4 parameters with 3 levels each: 3^4 = 81 scenarios
        """
        from itertools import product

        param_names = list(self.parameters.keys())

        # Generate level values for each parameter
        param_levels = {}
        for name, dist in self.parameters.items():
            if levels_per_param == 2:
                param_levels[name] = [dist.low, dist.high]
            else:
                param_levels[name] = np.linspace(dist.low, dist.high, levels_per_param).tolist()

        # Generate all combinations
        scenarios = []
        all_combinations = product(*[param_levels[name] for name in param_names])

        for i, combo in enumerate(all_combinations):
            sample = dict(zip(param_names, combo))
            scenario = UncertaintyScenario(
                scenario_id=i,
                electricity_price_multiplier=sample['electricity_price_multiplier'],
                carbon_price=sample['carbon_price'],
                charging_markup=sample['charging_markup'],
                tech_cost_multiplier=sample['tech_cost_multiplier']
            )
            scenarios.append(scenario)

        return scenarios

    def generate_one_at_a_time(self, n_levels: int = 5) -> List[UncertaintyScenario]:
        """
        Generate One-At-a-Time (OAT) scenarios for sensitivity analysis.
        Each parameter is varied while others are held at their central value.

        Returns: (n_params * n_levels) + 1 scenarios (including base case)
        """
        param_names = list(self.parameters.keys())
        scenarios = []
        scenario_id = 0

        # Base case: all parameters at central values
        central_values = {}
        for name, dist in self.parameters.items():
            central_values[name] = (dist.low + dist.high) / 2

        base_scenario = UncertaintyScenario(
            scenario_id=scenario_id,
            **central_values
        )
        scenarios.append(base_scenario)
        scenario_id += 1

        # Vary each parameter one at a time
        for param_name in param_names:
            dist = self.parameters[param_name]
            levels = np.linspace(dist.low, dist.high, n_levels)

            for level in levels:
                sample = central_values.copy()
                sample[param_name] = level

                scenario = UncertaintyScenario(
                    scenario_id=scenario_id,
                    **sample
                )
                scenarios.append(scenario)
                scenario_id += 1

        return scenarios

    def save_scenarios(self, scenarios: List[UncertaintyScenario], filepath: Path):
        """Save scenarios to JSON file."""
        data = {
            'n_scenarios': len(scenarios),
            'parameter_distributions': {
                name: {
                    'distribution': dist.distribution,
                    'low': dist.low,
                    'high': dist.high,
                    'mode': dist.mode
                }
                for name, dist in self.parameters.items()
            },
            'scenarios': [s.to_dict() for s in scenarios]
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"Saved {len(scenarios)} scenarios to {filepath}")

    @staticmethod
    def load_scenarios(filepath: Path) -> List[UncertaintyScenario]:
        """Load scenarios from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)

        scenarios = [UncertaintyScenario.from_dict(s) for s in data['scenarios']]
        print(f"Loaded {len(scenarios)} scenarios from {filepath}")
        return scenarios


if __name__ == "__main__":
    # Example usage
    sampler = ParameterSampler(seed=42)

    print("=== Parameter Distributions ===")
    for name, dist in sampler.parameters.items():
        print(f"  {name}: {dist.distribution} [{dist.low}, {dist.high}]")

    print("\n=== Latin Hypercube Sample (10 scenarios) ===")
    scenarios = sampler.generate_latin_hypercube(10)
    for s in scenarios:
        print(f"  S{s.scenario_id}: elec={s.electricity_price_multiplier:.2f}, "
              f"CO2={s.carbon_price:.0f}, markup={s.charging_markup:.2f}, "
              f"tech={s.tech_cost_multiplier:.2f}")

    print("\n=== Factorial Design (2 levels) ===")
    factorial_scenarios = sampler.generate_factorial_design(levels_per_param=2)
    print(f"  Generated {len(factorial_scenarios)} scenarios")

    print("\n=== OAT Design (5 levels) ===")
    oat_scenarios = sampler.generate_one_at_a_time(n_levels=5)
    print(f"  Generated {len(oat_scenarios)} scenarios")
