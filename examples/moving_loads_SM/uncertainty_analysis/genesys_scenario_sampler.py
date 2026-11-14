"""
GENeSYS-MOD Scenario-Based Sampler for Uncertainty Analysis
============================================================

Uses actual electricity price scenarios from GENeSYS-MOD output to construct
realistic uncertainty distributions.

Available scenarios in GENeSYS-MOD EU-EnVis-2060:
- Go RES v1.2 (base case used in SM_preprocessing.py)
- NECPEssentials v1.2
- REPowerEU++ v1.2
- Trinity v1.2

This module:
1. Reads electricity prices from all 4 GENeSYS scenarios
2. Uses them to define scenario-specific electricity price variations
3. Combines with other uncertain parameters (carbon price, markup, tech costs)
"""

import numpy as np
import pandas as pd
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import json


# GENeSYS-MOD scenario names
GENESYS_SCENARIOS = [
    'Go RES v1.2',
    'NECPEssentials v1.2',
    'REPowerEU++ v1.2',
    'Trinity v1.2'
]

BASE_SCENARIO = 'Go RES v1.2'

# Carbon price trajectories by scenario (EUR/tCO2)
# These are consistent with each scenario's climate ambition level
# Key years: 2020, 2030, 2040, 2050, 2060
CARBON_PRICE_TRAJECTORIES = {
    'Go RES v1.2': {
        # Most ambitious: early carbon neutrality, highest carbon prices
        2020: 30, 2030: 200, 2040: 500, 2050: 1000, 2060: 1000
    },
    'REPowerEU++ v1.2': {
        # Self-sufficient EU, strong climate action
        2020: 30, 2030: 150, 2040: 350, 2050: 700, 2060: 700
    },
    'NECPEssentials v1.2': {
        # Extension of current NECPs, moderate ambition
        2020: 30, 2030: 100, 2040: 250, 2050: 500, 2060: 500
    },
    'Trinity v1.2': {
        # Internal EU divisions, lowest ambition
        2020: 30, 2030: 80, 2040: 180, 2050: 350, 2060: 350
    }
}


def get_carbon_price_trajectory(scenario: str, start_year: int = 2020, end_year: int = 2060) -> Dict[int, float]:
    """
    Get interpolated carbon price trajectory for a scenario.

    Returns a dictionary with carbon price for each year from start_year to end_year.
    """
    if scenario not in CARBON_PRICE_TRAJECTORIES:
        raise ValueError(f"Unknown scenario: {scenario}")

    key_prices = CARBON_PRICE_TRAJECTORIES[scenario]
    key_years = sorted(key_prices.keys())
    key_values = [key_prices[y] for y in key_years]

    # Interpolate for all years
    trajectory = {}
    for year in range(start_year, end_year + 1):
        price = float(np.interp(year, key_years, key_values))
        trajectory[year] = price

    return trajectory


@dataclass
class GENeSYSElectricityScenario:
    """Electricity prices from a single GENeSYS scenario."""
    scenario_name: str
    prices_by_region_year: Dict[Tuple[str, int], float] = field(default_factory=dict)

    # Summary statistics
    mean_price: float = 0.0
    relative_to_base: float = 1.0  # Multiplier compared to base scenario


@dataclass
class ScenarioBasedUncertaintyCase:
    """
    An uncertainty case combining:
    - Electricity prices from a GENeSYS scenario
    - Carbon price (embedded in GENeSYS scenario)
    - Charging markup (CPO service fee on electricity)
    - Diesel markup (taxation/levy on diesel fuel)
    - Technology cost multiplier (time-dependent: grows with forecast horizon)

    The tech_cost_multiplier is applied with growing uncertainty over time:
    - 2020: multiplier = 1.0 (no deviation from base case)
    - 2060: multiplier = specified value (e.g., 0.7 or 1.3)
    - Intermediate years: linear interpolation

    This reflects that near-term BEV costs are more certain while
    long-term costs have higher uncertainty.
    """
    case_id: int
    genesys_scenario: str
    electricity_price_multiplier: float  # Relative to Go RES v1.2
    carbon_price: float  # EUR/tCO2 (not independently varied - embedded in scenario)
    charging_markup: float  # Fraction markup on electricity (0.0 = no markup)
    diesel_markup: float  # Fraction markup on diesel (taxation, e.g., 0.5 = 50% tax)
    tech_cost_multiplier: float  # Multiplier for BEV costs at 2060 (grows from 1.0 at 2020)

    # Store actual prices by region-year if needed
    electricity_prices: Optional[Dict[Tuple[str, int], float]] = None

    def to_dict(self) -> Dict:
        return {
            'case_id': self.case_id,
            'genesys_scenario': self.genesys_scenario,
            'electricity_price_multiplier': self.electricity_price_multiplier,
            'carbon_price': self.carbon_price,
            'charging_markup': self.charging_markup,
            'diesel_markup': self.diesel_markup,
            'tech_cost_multiplier': self.tech_cost_multiplier
        }


class GENeSYSScenarioSampler:
    """
    Generates uncertainty cases using GENeSYS-MOD scenario data.

    Instead of arbitrary multipliers, this uses actual model scenarios
    for electricity prices, combined with other uncertain parameters.
    """

    def __init__(
        self,
        genesys_fuel_costs_path: Path,
        base_scenario: str = BASE_SCENARIO,
        seed: int = 42
    ):
        """
        Initialize the sampler with GENeSYS-MOD data.

        Parameters:
        -----------
        genesys_fuel_costs_path : Path
            Path to output_endogenous_fuelcosts.csv
        base_scenario : str
            The scenario used as reference (default: 'Go RES v1.2')
        seed : int
            Random seed for other parameter sampling
        """
        self.genesys_path = Path(genesys_fuel_costs_path)
        self.base_scenario = base_scenario
        self.rng = np.random.default_rng(seed)

        # Load GENeSYS data
        self.genesys_scenarios: Dict[str, GENeSYSElectricityScenario] = {}
        self._load_genesys_data()

        # Parameter ranges for other uncertainties
        self.carbon_price_range = (0.0, 200.0)  # EUR/tCO2
        self.charging_markup_range = (0.0, 0.5)  # 0-50% markup
        self.tech_cost_multiplier_range = (0.8, 1.2)  # ±20% BEV costs

    def _load_genesys_data(self):
        """Load and process GENeSYS-MOD fuel cost data."""
        if not self.genesys_path.exists():
            raise FileNotFoundError(f"GENeSYS data not found: {self.genesys_path}")

        df = pd.read_csv(self.genesys_path)
        df.columns = df.columns.str.strip()

        # Filter for Power (electricity) only
        power_df = df[df['Fuel'] == 'Power'].copy()

        # Calculate base scenario mean for normalization
        base_power = power_df[power_df['Model Version'] == self.base_scenario]
        base_mean = base_power['Value'].mean()

        print(f"Loading GENeSYS-MOD electricity price scenarios...")
        print(f"Base scenario: {self.base_scenario} (mean: {base_mean:.2f} MEUR/PJ)")

        for scenario in GENESYS_SCENARIOS:
            scenario_data = power_df[power_df['Model Version'] == scenario]

            if scenario_data.empty:
                print(f"  [WARN] Scenario '{scenario}' not found in data")
                continue

            genesys_scenario = GENeSYSElectricityScenario(scenario_name=scenario)

            # Store prices by (region, year)
            for _, row in scenario_data.iterrows():
                region = row['Region']
                year = int(row['Year'])
                price = row['Value']
                genesys_scenario.prices_by_region_year[(region, year)] = price

            # Calculate summary statistics
            genesys_scenario.mean_price = scenario_data['Value'].mean()
            genesys_scenario.relative_to_base = genesys_scenario.mean_price / base_mean

            self.genesys_scenarios[scenario] = genesys_scenario

            print(f"  {scenario}: {genesys_scenario.relative_to_base:.3f}x base "
                  f"(mean: {genesys_scenario.mean_price:.2f} MEUR/PJ)")

    def get_scenario_multipliers(self) -> Dict[str, float]:
        """Get electricity price multipliers for each GENeSYS scenario."""
        return {
            name: scenario.relative_to_base
            for name, scenario in self.genesys_scenarios.items()
        }

    def generate_discrete_genesys_cases(
        self,
        charging_markups: Optional[List[float]] = None,
        diesel_markups: Optional[List[float]] = None,
        tech_multipliers: Optional[List[float]] = None
    ) -> List[ScenarioBasedUncertaintyCase]:
        """
        Generate uncertainty cases using discrete GENeSYS scenarios.

        Creates a full factorial combination of:
        - 4 GENeSYS electricity scenarios (each with embedded carbon budget)
        - Specified charging markups (default: [0.15, 0.30])
        - Specified diesel markups (default: [0.50] = 50% tax, representing EU average)
        - Specified tech multipliers (default: [0.7, 1.0, 1.3])

        Note: Carbon prices are NOT varied independently because each GENeSYS
        scenario already embeds consistent carbon budget constraints that
        determine the electricity generation mix and prices.

        Returns list of all combinations.
        """
        from itertools import product

        # Default parameter values
        if charging_markups is None:
            charging_markups = [0.15, 0.30]
        if diesel_markups is None:
            # EU average diesel taxation ~50% on top of wholesale price
            # This represents energy tax + VAT (excl. carbon pricing which is in GENeSYS)
            diesel_markups = [0.50]
        if tech_multipliers is None:
            # ±30% at 2060 (time-dependent: grows from 0% at 2020)
            tech_multipliers = [0.7, 1.0, 1.3]

        cases = []
        case_id = 0

        genesys_names = list(self.genesys_scenarios.keys())

        for genesys, charging_mk, diesel_mk, tech in product(
            genesys_names, charging_markups, diesel_markups, tech_multipliers
        ):
            scenario = self.genesys_scenarios[genesys]

            case = ScenarioBasedUncertaintyCase(
                case_id=case_id,
                genesys_scenario=genesys,
                electricity_price_multiplier=scenario.relative_to_base,
                carbon_price=0.0,  # Not used - embedded in GENeSYS scenario
                charging_markup=charging_mk,
                diesel_markup=diesel_mk,
                tech_cost_multiplier=tech
            )
            cases.append(case)
            case_id += 1

        print(f"\nGenerated {len(cases)} discrete factorial cases:")
        print(f"  {len(genesys_names)} GENeSYS scenarios × "
              f"{len(charging_markups)} charging markups × "
              f"{len(diesel_markups)} diesel markups × "
              f"{len(tech_multipliers)} tech multipliers")

        return cases

    def generate_lhs_within_genesys_bounds(
        self,
        n_samples: int = 20
    ) -> List[ScenarioBasedUncertaintyCase]:
        """
        Generate Latin Hypercube samples where electricity prices are
        bounded by the range of GENeSYS scenarios.

        This uses the min/max of GENeSYS scenario multipliers to define
        the electricity price uncertainty range.
        """
        multipliers = list(self.get_scenario_multipliers().values())
        elec_min = min(multipliers)
        elec_max = max(multipliers)

        print(f"\nElectricity price multiplier range from GENeSYS: [{elec_min:.3f}, {elec_max:.3f}]")

        # Generate LHS samples for 4 parameters
        n_params = 4
        lhs_samples = np.zeros((n_samples, n_params))

        for i in range(n_params):
            intervals = np.linspace(0, 1, n_samples + 1)
            points = self.rng.uniform(intervals[:-1], intervals[1:])
            self.rng.shuffle(points)
            lhs_samples[:, i] = points

        cases = []
        for i in range(n_samples):
            # Map [0,1] to parameter ranges
            elec_mult = elec_min + lhs_samples[i, 0] * (elec_max - elec_min)
            carbon = self.carbon_price_range[0] + lhs_samples[i, 1] * (
                self.carbon_price_range[1] - self.carbon_price_range[0]
            )
            markup = self.charging_markup_range[0] + lhs_samples[i, 2] * (
                self.charging_markup_range[1] - self.charging_markup_range[0]
            )
            tech = self.tech_cost_multiplier_range[0] + lhs_samples[i, 3] * (
                self.tech_cost_multiplier_range[1] - self.tech_cost_multiplier_range[0]
            )

            # Find closest GENeSYS scenario
            closest_scenario = min(
                self.genesys_scenarios.keys(),
                key=lambda s: abs(self.genesys_scenarios[s].relative_to_base - elec_mult)
            )

            case = ScenarioBasedUncertaintyCase(
                case_id=i,
                genesys_scenario=closest_scenario,
                electricity_price_multiplier=elec_mult,
                carbon_price=carbon,
                charging_markup=markup,
                tech_cost_multiplier=tech
            )
            cases.append(case)

        print(f"Generated {n_samples} LHS samples within GENeSYS bounds")
        return cases

    def generate_oat_sensitivity(
        self,
        n_levels: int = 5
    ) -> List[ScenarioBasedUncertaintyCase]:
        """
        Generate One-At-a-Time sensitivity analysis cases.

        Base case: Go RES v1.2, carbon=0, markup=0, tech=1.0
        Then vary each parameter while holding others at base values.
        """
        cases = []
        case_id = 0

        # Base values
        base_elec = 1.0  # Go RES v1.2
        base_carbon = 50.0  # Mid-range
        base_markup = 0.0
        base_tech = 1.0

        # Base case
        cases.append(ScenarioBasedUncertaintyCase(
            case_id=case_id,
            genesys_scenario='Go RES v1.2',
            electricity_price_multiplier=base_elec,
            carbon_price=base_carbon,
            charging_markup=base_markup,
            tech_cost_multiplier=base_tech
        ))
        case_id += 1

        # Vary GENeSYS scenario (discrete)
        for scenario_name, scenario in self.genesys_scenarios.items():
            if scenario_name == 'Go RES v1.2':
                continue  # Skip base
            cases.append(ScenarioBasedUncertaintyCase(
                case_id=case_id,
                genesys_scenario=scenario_name,
                electricity_price_multiplier=scenario.relative_to_base,
                carbon_price=base_carbon,
                charging_markup=base_markup,
                tech_cost_multiplier=base_tech
            ))
            case_id += 1

        # Vary carbon price
        carbon_levels = np.linspace(
            self.carbon_price_range[0],
            self.carbon_price_range[1],
            n_levels
        )
        for carbon in carbon_levels:
            cases.append(ScenarioBasedUncertaintyCase(
                case_id=case_id,
                genesys_scenario='Go RES v1.2',
                electricity_price_multiplier=base_elec,
                carbon_price=carbon,
                charging_markup=base_markup,
                tech_cost_multiplier=base_tech
            ))
            case_id += 1

        # Vary charging markup
        markup_levels = np.linspace(
            self.charging_markup_range[0],
            self.charging_markup_range[1],
            n_levels
        )
        for markup in markup_levels:
            cases.append(ScenarioBasedUncertaintyCase(
                case_id=case_id,
                genesys_scenario='Go RES v1.2',
                electricity_price_multiplier=base_elec,
                carbon_price=base_carbon,
                charging_markup=markup,
                tech_cost_multiplier=base_tech
            ))
            case_id += 1

        # Vary tech cost multiplier
        tech_levels = np.linspace(
            self.tech_cost_multiplier_range[0],
            self.tech_cost_multiplier_range[1],
            n_levels
        )
        for tech in tech_levels:
            cases.append(ScenarioBasedUncertaintyCase(
                case_id=case_id,
                genesys_scenario='Go RES v1.2',
                electricity_price_multiplier=base_elec,
                carbon_price=base_carbon,
                charging_markup=base_markup,
                tech_cost_multiplier=tech
            ))
            case_id += 1

        print(f"Generated {len(cases)} OAT sensitivity cases")
        print(f"  1 base case + 3 GENeSYS scenarios + {n_levels}×3 parameter variations")

        return cases

    def get_electricity_prices_for_case(
        self,
        case: ScenarioBasedUncertaintyCase
    ) -> Dict[Tuple[str, int], float]:
        """
        Get the full electricity price table for a case.

        Uses the GENeSYS scenario prices and applies any additional multiplier
        if the case uses an interpolated electricity price.
        """
        genesys = self.genesys_scenarios.get(case.genesys_scenario)
        if genesys is None:
            raise ValueError(f"Unknown GENeSYS scenario: {case.genesys_scenario}")

        # Apply additional adjustment if multiplier differs from scenario's native multiplier
        adjustment = case.electricity_price_multiplier / genesys.relative_to_base

        adjusted_prices = {}
        for (region, year), price in genesys.prices_by_region_year.items():
            adjusted_prices[(region, year)] = price * adjustment

        return adjusted_prices

    def save_cases(self, cases: List[ScenarioBasedUncertaintyCase], filepath: Path):
        """Save cases to JSON file."""
        data = {
            'n_cases': len(cases),
            'base_scenario': self.base_scenario,
            'genesys_multipliers': self.get_scenario_multipliers(),
            'parameter_ranges': {
                'carbon_price': self.carbon_price_range,
                'charging_markup': self.charging_markup_range,
                'tech_cost_multiplier': self.tech_cost_multiplier_range
            },
            'cases': [c.to_dict() for c in cases]
        }

        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"Saved {len(cases)} cases to {filepath}")

    @staticmethod
    def load_cases(filepath: Path) -> List[ScenarioBasedUncertaintyCase]:
        """Load cases from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)

        cases = []
        for c in data['cases']:
            case = ScenarioBasedUncertaintyCase(
                case_id=c['case_id'],
                genesys_scenario=c['genesys_scenario'],
                electricity_price_multiplier=c['electricity_price_multiplier'],
                carbon_price=c['carbon_price'],
                charging_markup=c['charging_markup'],
                tech_cost_multiplier=c['tech_cost_multiplier']
            )
            cases.append(case)

        print(f"Loaded {len(cases)} cases from {filepath}")
        return cases


if __name__ == "__main__":
    # Example usage
    from pathlib import Path

    # Path to GENeSYS data
    genesys_path = Path("data/GENeSYS-MOD_EU-EnVis-2060_v1.2.0_native/output_endogenous_fuelcosts.csv")

    if genesys_path.exists():
        sampler = GENeSYSScenarioSampler(genesys_path, seed=42)

        print("\n" + "=" * 60)
        print("GENeSYS Scenario Electricity Price Multipliers:")
        print("=" * 60)
        for name, mult in sampler.get_scenario_multipliers().items():
            print(f"  {name}: {mult:.3f}x")

        print("\n" + "=" * 60)
        print("Example: Discrete Factorial Design")
        print("=" * 60)
        discrete_cases = sampler.generate_discrete_genesys_cases(
            carbon_prices=[0, 100],
            charging_markups=[0, 0.25],
            tech_multipliers=[1.0]
        )
        print(f"First 5 cases:")
        for c in discrete_cases[:5]:
            print(f"  {c.case_id}: {c.genesys_scenario} | CO2={c.carbon_price:.0f} | "
                  f"markup={c.charging_markup:.0%} | tech={c.tech_cost_multiplier:.2f}")

        print("\n" + "=" * 60)
        print("Example: LHS Within GENeSYS Bounds")
        print("=" * 60)
        lhs_cases = sampler.generate_lhs_within_genesys_bounds(n_samples=10)
        for c in lhs_cases[:5]:
            print(f"  {c.case_id}: elec={c.electricity_price_multiplier:.3f}x | "
                  f"CO2={c.carbon_price:.0f} | markup={c.charging_markup:.1%} | "
                  f"tech={c.tech_cost_multiplier:.2f}")

        print("\n" + "=" * 60)
        print("Example: OAT Sensitivity")
        print("=" * 60)
        oat_cases = sampler.generate_oat_sensitivity(n_levels=3)
    else:
        print(f"GENeSYS data not found at: {genesys_path}")
        print("Please adjust the path to match your data location.")
