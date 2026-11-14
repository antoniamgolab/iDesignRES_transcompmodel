"""
YAML Modifier for GENeSYS-Based Uncertainty Analysis
=====================================================

Applies GENeSYS scenario electricity prices to YAML files.
Unlike the simple multiplier approach, this uses actual scenario prices
by region and year from the GENeSYS-MOD output.

Key difference from yaml_modifier.py:
- Reads actual prices from GENeSYS scenarios
- Applies region-specific and year-specific prices
- PRESERVES year-to-year price trajectories from each scenario
- More accurate representation of scenario uncertainty

IMPORTANT: Each GENeSYS scenario has a different price TRAJECTORY over time,
not just a different level. This modifier preserves those trajectories by
applying year-specific ratios rather than a single multiplier.
"""

import yaml
import shutil
import pandas as pd
import numpy as np
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Handle imports for both direct execution and module import
try:
    from .genesys_scenario_sampler import (
        ScenarioBasedUncertaintyCase,
        GENeSYSScenarioSampler,
        GENESYS_SCENARIOS,
        BASE_SCENARIO,
        get_carbon_price_trajectory
    )
except ImportError:
    # Direct execution - use absolute import
    _script_dir = Path(__file__).parent
    if str(_script_dir) not in sys.path:
        sys.path.insert(0, str(_script_dir))
    from genesys_scenario_sampler import (
        ScenarioBasedUncertaintyCase,
        GENeSYSScenarioSampler,
        GENESYS_SCENARIOS,
        BASE_SCENARIO,
        get_carbon_price_trajectory
    )


class YAMLModifierGENeSYS:
    """
    Applies GENeSYS scenario parameters to YAML input files.

    Key principle: Base case from SM_preprocessing.py is NEVER modified.
    This creates copies and applies scenario-specific adjustments.

    IMPORTANT: This modifier preserves year-to-year price TRAJECTORIES from
    GENeSYS scenarios, not just average levels. Each scenario has different
    dynamics (e.g., Go RES drops sharply 2030-2035, others decline gradually).
    """

    def __init__(
        self,
        base_case_path: Path,
        output_base_path: Path,
        genesys_sampler: GENeSYSScenarioSampler,
        genesys_data_path: Optional[Path] = None
    ):
        """
        Initialize the modifier.

        Parameters:
        -----------
        base_case_path : Path
            Path to base case input_data folder (from SM_preprocessing.py)
        output_base_path : Path
            Path where scenario folders will be created
        genesys_sampler : GENeSYSScenarioSampler
            Sampler with loaded GENeSYS scenario data
        genesys_data_path : Path, optional
            Path to GENeSYS fuel costs CSV (for loading year-specific ratios)
        """
        self.base_case_path = Path(base_case_path)
        self.output_base_path = Path(output_base_path)
        self.sampler = genesys_sampler

        if not self.base_case_path.exists():
            raise ValueError(f"Base case path does not exist: {self.base_case_path}")

        self.output_base_path.mkdir(parents=True, exist_ok=True)

        # Load base case FuelCost to understand the structure
        self.base_fuel_cost = self._load_yaml(self.base_case_path / "FuelCost.yaml")
        self._analyze_base_fuel_cost()

        # Load year-specific price ratios from GENeSYS data
        self.year_ratios = {}  # scenario -> {(region, year): ratio_vs_base}
        self.oil_prices = {}  # scenario -> {(region, year): price_EUR_per_kWh}
        if genesys_data_path:
            self._load_year_specific_ratios(genesys_data_path)
            self._load_oil_prices(genesys_data_path)
        else:
            # Try to find the data path from sampler
            self._load_year_specific_ratios(self.sampler.genesys_path)
            self._load_oil_prices(self.sampler.genesys_path)

    def _load_year_specific_ratios(self, genesys_path: Path):
        """
        Load year-specific price ratios for each scenario.

        For each (scenario, region, year), compute the ratio vs base scenario.
        This preserves the temporal trajectory of each scenario.

        IMPORTANT: GENeSYS has data at 5-year intervals (2018, 2025, 2030, ...),
        but the model may use different years (e.g., 2020, 2022, 2024, ...).
        We interpolate ratios for intermediate years.
        """
        print("Loading year-specific electricity price ratios...")

        df = pd.read_csv(genesys_path)
        df.columns = df.columns.str.strip()

        # Filter for Power (electricity)
        power_df = df[df['Fuel'] == 'Power'].copy()

        # Get GENeSYS years
        genesys_years = sorted(power_df['Year'].unique())
        print(f"  GENeSYS years: {[int(y) for y in genesys_years]}")

        # Get base scenario prices as a dictionary for faster lookup
        base_df = power_df[power_df['Model Version'] == BASE_SCENARIO].copy()
        base_prices = {}
        for _, row in base_df.iterrows():
            region = row['Region']
            year = int(row['Year'])
            base_prices[(region, year)] = float(row['Value'])

        # Get all regions
        regions = power_df['Region'].unique()

        # Compute ratios for each scenario at GENeSYS years first
        raw_ratios = {}  # scenario -> region -> {year: ratio}
        for scenario in GENESYS_SCENARIOS:
            scenario_prices = power_df[power_df['Model Version'] == scenario].copy()
            raw_ratios[scenario] = {}

            for _, row in scenario_prices.iterrows():
                region = row['Region']
                year = int(row['Year'])
                price = float(row['Value'])

                if region not in raw_ratios[scenario]:
                    raw_ratios[scenario][region] = {}

                # Get base price for same region/year
                base_price = base_prices.get((region, year), 0)
                if base_price > 0:
                    ratio = price / base_price
                else:
                    ratio = 1.0

                raw_ratios[scenario][region][year] = ratio

        # Now interpolate to get ratios for ALL model years (2020-2060)
        model_years = list(range(2020, 2061))  # All possible years

        for scenario in GENESYS_SCENARIOS:
            self.year_ratios[scenario] = {}

            for region in regions:
                if region not in raw_ratios[scenario]:
                    continue

                region_ratios = raw_ratios[scenario][region]
                known_years = sorted(region_ratios.keys())
                known_ratios = [region_ratios[y] for y in known_years]

                # Interpolate for all model years
                for year in model_years:
                    if year in region_ratios:
                        # Use exact value if available
                        ratio = region_ratios[year]
                    else:
                        # Interpolate/extrapolate
                        ratio = float(np.interp(year, known_years, known_ratios))

                    self.year_ratios[scenario][(region, year)] = ratio

        # Print sample ratios to show interpolated trajectories
        print("\n  Interpolated ratios for DE (sample):")
        for scenario in GENESYS_SCENARIOS:
            ratios = [self.year_ratios[scenario].get(('DE', y), 1.0) for y in [2020, 2025, 2030, 2035, 2040, 2050]]
            print(f"    {scenario}: 2020={ratios[0]:.3f}, 2025={ratios[1]:.3f}, "
                  f"2030={ratios[2]:.3f}, 2035={ratios[3]:.3f}, 2040={ratios[4]:.3f}, 2050={ratios[5]:.3f}")

    def _load_oil_prices(self, genesys_path: Path):
        """
        Load GENeSYS Oil prices for diesel fuel cost calculation.

        Oil prices are loaded in EUR/MWh and converted to EUR/kWh for the model.
        These represent commodity prices WITHOUT carbon costs (carbon is applied
        separately by the model via GeographicElement.carbon_price).

        Note: Oil prices in GENeSYS vary by scenario due to demand effects:
        - High-ambition scenarios (Go RES): lower oil prices due to demand destruction
        - Low-ambition scenarios (Trinity): higher oil prices due to continued demand
        """
        print("\nLoading GENeSYS Oil prices for diesel...")

        df = pd.read_csv(genesys_path)
        df.columns = df.columns.str.strip()

        # Filter for Oil in EUR/MWh
        oil_df = df[(df['Fuel'] == 'Oil') & (df['Unit'] == 'Fuel Costs in EUR/MWh')].copy()

        if oil_df.empty:
            print("  [WARN] No Oil price data found in EUR/MWh, trying MEUR/PJ...")
            oil_df = df[(df['Fuel'] == 'Oil') & (df['Unit'] == 'Fuel Costs in MEUR/PJ')].copy()
            # Convert MEUR/PJ to EUR/kWh: 1 PJ = 277,777,778 kWh, so MEUR/PJ * 1e6 / 277777778 = EUR/kWh
            conversion_factor = 1e6 / 277777778  # ~0.0036
        else:
            # Convert EUR/MWh to EUR/kWh: divide by 1000
            conversion_factor = 1 / 1000

        genesys_years = sorted(oil_df['Year'].unique())
        regions = oil_df['Region'].unique()
        model_years = list(range(2020, 2061))

        for scenario in GENESYS_SCENARIOS:
            self.oil_prices[scenario] = {}
            scenario_df = oil_df[oil_df['Model Version'] == scenario]

            for region in regions:
                region_df = scenario_df[scenario_df['Region'] == region]
                if region_df.empty:
                    continue

                # Get known prices at GENeSYS years
                known_years = []
                known_prices = []
                for _, row in region_df.iterrows():
                    year = int(row['Year'])
                    price_eur_kwh = float(row['Value']) * conversion_factor
                    known_years.append(year)
                    known_prices.append(price_eur_kwh)

                # Sort by year
                sorted_pairs = sorted(zip(known_years, known_prices))
                known_years = [p[0] for p in sorted_pairs]
                known_prices = [p[1] for p in sorted_pairs]

                # Interpolate for all model years
                for year in model_years:
                    price = float(np.interp(year, known_years, known_prices))
                    self.oil_prices[scenario][(region, year)] = price

        # Print sample prices
        print("\n  Oil prices for DE (EUR/kWh, before markup):")
        for scenario in GENESYS_SCENARIOS:
            prices = [self.oil_prices[scenario].get(('DE', y), 0) for y in [2020, 2030, 2040, 2050, 2060]]
            print(f"    {scenario}: 2020={prices[0]:.4f}, 2030={prices[1]:.4f}, "
                  f"2040={prices[2]:.4f}, 2050={prices[3]:.4f}, 2060={prices[4]:.4f}")

    def _load_yaml(self, filepath: Path) -> List[Dict]:
        """Load a YAML file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _save_yaml(self, data: List[Dict], filepath: Path):
        """Save data to YAML file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    def _analyze_base_fuel_cost(self):
        """Analyze base case FuelCost.yaml structure."""
        print("Analyzing base case FuelCost.yaml structure...")

        # Find electricity entries
        self.elec_entries = []
        for i, entry in enumerate(self.base_fuel_cost):
            fuel = entry.get('fuel', '')
            # Check for electricity (could be string 'electricity' or numeric id)
            if fuel == 'electricity' or fuel == 0 or str(fuel).lower() == 'electricity':
                self.elec_entries.append(i)
                geo_id = entry.get('geographic_element', entry.get('geo_element'))
                cost = entry.get('cost_per_kWh', [])
                print(f"  Found electricity entry {i}: geo={geo_id}, n_years={len(cost) if isinstance(cost, list) else 1}")

        print(f"  Total electricity entries: {len(self.elec_entries)}")

    def _copy_base_case(self, case_id: int, backup_existing: bool = True) -> Path:
        """
        Copy base case to new scenario folder.

        Parameters:
        -----------
        case_id : int
            The case ID for the scenario folder name
        backup_existing : bool
            If True and folder exists, rename it with timestamp before overwriting.
            If False, delete existing folder (old behavior).
        """
        scenario_folder = self.output_base_path / f"scenario_{case_id:03d}"

        if scenario_folder.exists():
            if backup_existing:
                # Create timestamped backup of existing folder
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_folder = self.output_base_path / f"scenario_{case_id:03d}_backup_{timestamp}"
                print(f"  Backing up existing scenario to: {backup_folder.name}")
                shutil.move(str(scenario_folder), str(backup_folder))
            else:
                shutil.rmtree(scenario_folder)

        shutil.copytree(self.base_case_path, scenario_folder)
        return scenario_folder

    def _apply_electricity_prices(
        self,
        scenario_path: Path,
        case: ScenarioBasedUncertaintyCase
    ):
        """
        Apply electricity price adjustments from GENeSYS scenario.

        IMPORTANT: This applies YEAR-SPECIFIC ratios to preserve the temporal
        trajectory of each GENeSYS scenario. Different scenarios have different
        price dynamics over time (e.g., Go RES drops sharply 2030-2035, others
        decline more gradually).

        The adjustment for each year is:
            base_price[y] * ratio[scenario, region, year] * (1 + markup)
        """
        fuel_cost_path = scenario_path / "FuelCost.yaml"

        if not fuel_cost_path.exists():
            print(f"  [WARN] FuelCost.yaml not found in {scenario_path}")
            return

        data = self._load_yaml(fuel_cost_path)

        # Load geographic elements to get location -> country mapping
        geo_path = scenario_path / "GeographicElement.yaml"
        location_to_country = {}
        if geo_path.exists():
            geo_data = self._load_yaml(geo_path)
            for geo in geo_data:
                loc_id = geo.get('id')
                country = geo.get('country', '')
                if loc_id is not None and country:
                    location_to_country[loc_id] = country

        # Markup factor (applies uniformly across all years)
        markup_factor = 1 + case.charging_markup

        # Get the year-specific ratios for this scenario
        scenario_ratios = self.year_ratios.get(case.genesys_scenario, {})

        # Years in the model (2020-2060, 41 years)
        model_years = list(range(2020, 2061))

        modified_count = 0
        for entry in data:
            fuel = entry.get('fuel', '')
            if fuel == 'electricity' or fuel == 0 or str(fuel).lower() == 'electricity':
                location_id = entry.get('location', entry.get('geographic_element'))
                country = location_to_country.get(location_id, '')

                cost_per_kwh = entry.get('cost_per_kWh', [])

                if isinstance(cost_per_kwh, list):
                    new_costs = []
                    for i, cost in enumerate(cost_per_kwh):
                        year = model_years[i] if i < len(model_years) else model_years[-1]

                        # Get year-specific ratio for this country/year
                        # Fall back to overall scenario multiplier if specific ratio not found
                        ratio = scenario_ratios.get(
                            (country, year),
                            case.electricity_price_multiplier
                        )

                        new_cost = cost * ratio * markup_factor
                        new_costs.append(new_cost)

                    entry['cost_per_kWh'] = new_costs
                else:
                    # Single value - apply average multiplier
                    entry['cost_per_kWh'] = cost_per_kwh * case.electricity_price_multiplier * markup_factor

                modified_count += 1

        self._save_yaml(data, fuel_cost_path)

        # Show sample of year-specific adjustments
        sample_country = 'DE' if 'DE' in location_to_country.values() else list(location_to_country.values())[0] if location_to_country else 'N/A'
        if scenario_ratios and sample_country != 'N/A':
            r2030 = scenario_ratios.get((sample_country, 2030), case.electricity_price_multiplier)
            r2040 = scenario_ratios.get((sample_country, 2040), case.electricity_price_multiplier)
            r2050 = scenario_ratios.get((sample_country, 2050), case.electricity_price_multiplier)
            print(f"  Applied year-specific price ratios ({case.genesys_scenario}, +{case.charging_markup:.0%} markup)")
            print(f"    Sample ({sample_country}): 2030={r2030:.3f}x, 2040={r2040:.3f}x, 2050={r2050:.3f}x")
            print(f"    Modified {modified_count} electricity entries")
        else:
            print(f"  Applied uniform multiplier x{case.electricity_price_multiplier:.3f} "
                  f"(+{case.charging_markup:.0%} markup) to {modified_count} entries")

    def _apply_carbon_price_trajectory(
        self,
        scenario_path: Path,
        genesys_scenario: str,
        start_year: int = 2020,
        end_year: int = 2060
    ):
        """
        Apply scenario-specific carbon price trajectory to GeographicElement.yaml.

        Each GENeSYS scenario has its own carbon price trajectory that is consistent
        with its climate ambition level. The trajectory is interpolated to provide
        one carbon price per year.

        Parameters:
        -----------
        scenario_path : Path
            Path to scenario folder
        genesys_scenario : str
            Name of the GENeSYS scenario (determines carbon price trajectory)
        start_year : int
            First year of the model horizon
        end_year : int
            Last year of the model horizon
        """
        geo_element_path = scenario_path / "GeographicElement.yaml"

        if not geo_element_path.exists():
            print(f"  [WARN] GeographicElement.yaml not found in {scenario_path}")
            return

        # Get the interpolated carbon price trajectory for this scenario
        carbon_trajectory = get_carbon_price_trajectory(genesys_scenario, start_year, end_year)
        carbon_prices_list = [carbon_trajectory[y] for y in range(start_year, end_year + 1)]

        data = self._load_yaml(geo_element_path)

        modified_count = 0
        for entry in data:
            if 'carbon_price' in entry:
                n_years = len(entry['carbon_price'])
                # Apply the trajectory (truncate or extend if needed)
                if n_years <= len(carbon_prices_list):
                    entry['carbon_price'] = carbon_prices_list[:n_years]
                else:
                    # Extend with last value if needed
                    entry['carbon_price'] = carbon_prices_list + [carbon_prices_list[-1]] * (n_years - len(carbon_prices_list))
                modified_count += 1

        self._save_yaml(data, geo_element_path)

        # Print summary
        p2020 = carbon_trajectory.get(2020, carbon_prices_list[0])
        p2030 = carbon_trajectory.get(2030, carbon_prices_list[10] if len(carbon_prices_list) > 10 else carbon_prices_list[-1])
        p2040 = carbon_trajectory.get(2040, carbon_prices_list[20] if len(carbon_prices_list) > 20 else carbon_prices_list[-1])
        p2050 = carbon_trajectory.get(2050, carbon_prices_list[30] if len(carbon_prices_list) > 30 else carbon_prices_list[-1])
        print(f"  Applied carbon price trajectory ({genesys_scenario}) to {modified_count} regions:")
        print(f"    2020: {p2020:.0f}, 2030: {p2030:.0f}, 2040: {p2040:.0f}, 2050: {p2050:.0f} EUR/tCO2")

    def _fix_icev_spec_cons(self, scenario_path: Path):
        """
        Fix ICEV spec_cons values by dividing by 100.

        The source data has spec_cons in kWh/100km, but the model expects kWh/km.
        This fix converts:
        - 363.9 kWh/100km -> 3.639 kWh/km

        Without this fix, driving range calculation is wrong:
        - Wrong: range = 5529 * 0.8 / 363.9 = 12.15 km
        - Correct: range = 5529 * 0.8 / 3.639 = 1,215 km
        """
        tech_vehicle_path = scenario_path / "TechVehicle.yaml"

        if not tech_vehicle_path.exists():
            print(f"  [WARN] TechVehicle.yaml not found in {scenario_path}")
            return

        data = self._load_yaml(tech_vehicle_path)

        modified_count = 0
        for entry in data:
            tech_id = entry.get('technology', -1)
            name = entry.get('name', '').lower()

            # ICEV identification: technology id = 0 or name contains 'icev'/'diesel'
            is_icev = (tech_id == 0) or ('icev' in name) or ('diesel' in name)

            if is_icev and 'spec_cons' in entry:
                spec_cons = entry['spec_cons']
                if isinstance(spec_cons, list):
                    # Check if values look like kWh/100km (> 10)
                    if spec_cons and spec_cons[0] > 10:
                        entry['spec_cons'] = [s / 100 for s in spec_cons]
                        modified_count += 1
                elif spec_cons > 10:
                    entry['spec_cons'] = spec_cons / 100
                    modified_count += 1

        self._save_yaml(data, tech_vehicle_path)

        if modified_count > 0:
            sample_old = 363.9
            sample_new = 3.639
            print(f"  Fixed ICEV spec_cons: divided by 100 ({modified_count} entries)")
            print(f"    Example: {sample_old:.1f} kWh/100km -> {sample_new:.3f} kWh/km")
        else:
            print(f"  ICEV spec_cons already correct (values < 10 kWh/km)")

    def _apply_tech_cost_multiplier(
        self,
        scenario_path: Path,
        multiplier: float,
        start_year: int = 2020,
        end_year: int = 2060,
        time_dependent: bool = True
    ):
        """
        Apply technology cost multiplier to BEV vehicles in TechVehicle.yaml.

        If time_dependent=True (default), uncertainty grows with time:
        - Near-term (start_year): multiplier = 1.0 (no deviation)
        - Long-term (end_year): multiplier = user-specified value
        - Intermediate years: linear interpolation

        This reflects that near-term BEV costs are more certain (current market data)
        while long-term costs have higher uncertainty.

        Example: multiplier=0.9 with time_dependent=True means:
        - 2020: 1.00 (0% deviation)
        - 2030: 0.975 (-2.5% deviation)
        - 2040: 0.95 (-5% deviation)
        - 2050: 0.925 (-7.5% deviation)
        - 2060: 0.90 (-10% deviation)
        """
        tech_vehicle_path = scenario_path / "TechVehicle.yaml"

        if not tech_vehicle_path.exists():
            print(f"  [WARN] TechVehicle.yaml not found in {scenario_path}")
            return

        data = self._load_yaml(tech_vehicle_path)

        modified_count = 0
        for entry in data:
            tech_id = entry.get('technology', -1)
            name = entry.get('name', '').lower()

            # BEV identification: technology id = 1 or name contains 'bev'/'electric'
            # Note: ICEV is technology=0, BEV is typically technology=1
            is_bev = (tech_id == 1) or ('bev' in name) or ('electric' in name)

            if is_bev and 'capital_cost' in entry:
                capital_cost = entry['capital_cost']
                if isinstance(capital_cost, list):
                    n_years = len(capital_cost)
                    if time_dependent:
                        # Calculate year-specific multipliers with growing uncertainty
                        year_multipliers = []
                        for i in range(n_years):
                            year = start_year + i
                            # Linear interpolation: 1.0 at start_year, multiplier at end_year
                            progress = (year - start_year) / (end_year - start_year)
                            progress = max(0.0, min(1.0, progress))  # Clamp to [0, 1]
                            year_mult = 1.0 + progress * (multiplier - 1.0)
                            year_multipliers.append(year_mult)
                        entry['capital_cost'] = [c * m for c, m in zip(capital_cost, year_multipliers)]
                    else:
                        # Uniform multiplier (original behavior)
                        entry['capital_cost'] = [c * multiplier for c in capital_cost]
                else:
                    entry['capital_cost'] = capital_cost * multiplier
                modified_count += 1

        self._save_yaml(data, tech_vehicle_path)

        if time_dependent:
            deviation_2060 = (multiplier - 1.0) * 100
            print(f"  Applied time-dependent tech cost multiplier to {modified_count} BEV entries")
            print(f"    2020: 1.000 (0.0%), 2040: {1.0 + 0.5*(multiplier-1.0):.3f} ({0.5*deviation_2060:.1f}%), "
                  f"2060: {multiplier:.3f} ({deviation_2060:.1f}%)")
        else:
            print(f"  Applied uniform tech cost multiplier x{multiplier:.3f} to {modified_count} BEV entries")

    def _apply_diesel_prices(
        self,
        scenario_path: Path,
        case: ScenarioBasedUncertaintyCase
    ):
        """
        Apply GENeSYS Oil prices to diesel in FuelCost.yaml.

        Uses scenario-specific, year-specific Oil prices from GENeSYS-MOD,
        then applies the diesel markup (taxation) on top.

        IMPORTANT: Carbon costs are NOT added here - they are applied by the
        model via GeographicElement.carbon_price × emission_factor.

        The final diesel price per year is:
            diesel_price[y] = oil_price[scenario, country, y] × (1 + markup)

        Parameters:
        -----------
        scenario_path : Path
            Path to scenario folder
        case : ScenarioBasedUncertaintyCase
            The case containing genesys_scenario and diesel_markup
        """
        fuel_cost_path = scenario_path / "FuelCost.yaml"

        if not fuel_cost_path.exists():
            print(f"  [WARN] FuelCost.yaml not found in {scenario_path}")
            return

        data = self._load_yaml(fuel_cost_path)

        # Load geographic elements to get location -> country mapping
        geo_path = scenario_path / "GeographicElement.yaml"
        location_to_country = {}
        if geo_path.exists():
            geo_data = self._load_yaml(geo_path)
            for geo in geo_data:
                loc_id = geo.get('id')
                country = geo.get('country', '')
                if loc_id is not None and country:
                    location_to_country[loc_id] = country

        # Get oil prices for this scenario
        scenario_oil = self.oil_prices.get(case.genesys_scenario, {})
        markup_factor = 1 + case.diesel_markup

        # Model years (2020-2060, 41 years)
        model_years = list(range(2020, 2061))

        modified_count = 0
        for entry in data:
            fuel = entry.get('fuel', '')
            if str(fuel).lower() == 'diesel' and 'cost_per_kWh' in entry:
                location_id = entry.get('location', entry.get('geographic_element'))
                country = location_to_country.get(location_id, '')

                cost_per_kwh = entry.get('cost_per_kWh', [])

                if isinstance(cost_per_kwh, list):
                    new_costs = []
                    for i, _ in enumerate(cost_per_kwh):
                        year = model_years[i] if i < len(model_years) else model_years[-1]

                        # Get GENeSYS oil price for this country/year
                        # Fall back to DE if country not found
                        oil_price = scenario_oil.get(
                            (country, year),
                            scenario_oil.get(('DE', year), 0.04)  # Default ~40 EUR/MWh
                        )

                        # Apply markup (taxation)
                        new_cost = oil_price * markup_factor
                        new_costs.append(new_cost)

                    entry['cost_per_kWh'] = new_costs
                else:
                    # Single value - use 2040 price as representative
                    oil_price = scenario_oil.get(
                        (country, 2040),
                        scenario_oil.get(('DE', 2040), 0.04)
                    )
                    entry['cost_per_kWh'] = oil_price * markup_factor

                modified_count += 1

        self._save_yaml(data, fuel_cost_path)

        # Print summary
        sample_country = 'DE' if 'DE' in location_to_country.values() else list(location_to_country.values())[0] if location_to_country else 'DE'
        if scenario_oil:
            p2030 = scenario_oil.get((sample_country, 2030), 0) * markup_factor
            p2040 = scenario_oil.get((sample_country, 2040), 0) * markup_factor
            p2050 = scenario_oil.get((sample_country, 2050), 0) * markup_factor
            print(f"  Applied GENeSYS Oil prices ({case.genesys_scenario}) + {case.diesel_markup:.0%} markup")
            print(f"    Sample ({sample_country}): 2030={p2030:.4f}, 2040={p2040:.4f}, 2050={p2050:.4f} EUR/kWh")
            print(f"    Modified {modified_count} diesel entries")
        else:
            print(f"  [WARN] No oil prices found for {case.genesys_scenario}, keeping base prices")

    def apply_case(self, case: ScenarioBasedUncertaintyCase) -> Path:
        """
        Apply a complete uncertainty case to create a new input folder.

        Parameters:
        -----------
        case : ScenarioBasedUncertaintyCase
            The case with parameter values to apply

        Returns:
        --------
        Path : Path to the created scenario folder
        """
        print(f"\n=== Applying Case {case.case_id}: {case.genesys_scenario} ===")
        print(f"  electricity_multiplier: {case.electricity_price_multiplier:.3f}")
        print(f"  charging_markup: {case.charging_markup:.1%}")
        print(f"  diesel_markup: {case.diesel_markup:.1%}")
        print(f"  tech_cost_multiplier: {case.tech_cost_multiplier:.3f}")

        # Step 1: Copy base case
        scenario_path = self._copy_base_case(case.case_id)

        # Step 1b: Update Model.yaml with correct temporal parameters
        self._update_model_yaml(scenario_path)

        # Step 1c: Fix ICEV spec_cons (divide by 100 to convert kWh/100km to kWh/km)
        self._fix_icev_spec_cons(scenario_path)

        # Step 2: Apply electricity price adjustment (year-specific from GENeSYS)
        self._apply_electricity_prices(scenario_path, case)

        # Step 3: Apply carbon price trajectory (scenario-specific, year-by-year)
        self._apply_carbon_price_trajectory(scenario_path, case.genesys_scenario)

        # Step 4: Apply GENeSYS Oil prices to diesel (+ markup/taxation)
        self._apply_diesel_prices(scenario_path, case)

        # Step 5: Apply tech cost multiplier (time-dependent)
        self._apply_tech_cost_multiplier(scenario_path, case.tech_cost_multiplier)

        # Step 6: Save case metadata
        self._save_case_metadata(scenario_path, case)

        print(f"  Case {case.case_id} ready at: {scenario_path}")
        return scenario_path

    def _update_model_yaml(self, scenario_path: Path):
        """
        Update Model.yaml with correct temporal and solver parameters.

        Ensures consistent model configuration across all scenarios:
        - Y: 41 (years 2020-2060)
        - y_init: 2020
        - pre_y: 12 (generations start from 2008)
        - time_step: 2 (2-year time steps)
        - investment_period: 4
        - alpha_f, beta_f, alpha_h, beta_h: regularization parameters
        """
        model_yaml_path = scenario_path / "Model.yaml"

        model_config = {
            'Y': 41,
            'y_init': 2020,
            'pre_y': 12,
            'time_step': 4,
            'gamma': 0.0001,
            'discount_rate': 0.05,
            'budget_penalty_plus': 10000,
            'budget_penalty_minus': 10000,
            'budget_penalty_yearly_plus': 10000000,
            'budget_penalty_yearly_minus': 10000000,
            'investment_period': 4,
            'pre_age_sell': False,
            'alpha_f': 0.01,
            'beta_f': 0.01,
            'alpha_h': 0.1,
            'beta_h': 0.1
        }

        with open(model_yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(model_config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

        print(f"  Updated Model.yaml: Y=41, time_step=4, investment_period=4")

    def _save_case_metadata(self, scenario_path: Path, case: ScenarioBasedUncertaintyCase):
        """Save case parameters as metadata file."""
        # Get carbon price trajectory for this scenario
        carbon_trajectory = get_carbon_price_trajectory(case.genesys_scenario)
        carbon_summary = {
            2020: carbon_trajectory[2020],
            2030: carbon_trajectory[2030],
            2040: carbon_trajectory[2040],
            2050: carbon_trajectory[2050],
            2060: carbon_trajectory[2060]
        }

        metadata = {
            'case_id': case.case_id,
            'genesys_scenario': case.genesys_scenario,
            'parameters': {
                'electricity_price_multiplier': case.electricity_price_multiplier,
                'charging_markup': case.charging_markup,
                'diesel_markup': case.diesel_markup,
                'tech_cost_multiplier': case.tech_cost_multiplier,
                'carbon_price_trajectory': carbon_summary
            },
            'base_case': str(self.base_case_path),
            'base_scenario_for_electricity': BASE_SCENARIO
        }

        metadata_path = scenario_path / "case_metadata.yaml"
        with open(metadata_path, 'w') as f:
            yaml.dump(metadata, f, default_flow_style=False)

    def apply_all_cases(self, cases: List[ScenarioBasedUncertaintyCase]) -> List[Path]:
        """Apply multiple cases and return list of created folder paths."""
        paths = []
        for case in cases:
            path = self.apply_case(case)
            paths.append(path)

        print(f"\n=== Created {len(paths)} scenario folders ===")
        return paths


if __name__ == "__main__":
    from pathlib import Path
    from genesys_scenario_sampler import GENeSYSScenarioSampler

    # Paths
    genesys_path = Path("data/GENeSYS-MOD_EU-EnVis-2060_v1.2.0_native/output_endogenous_fuelcosts.csv")
    base_case = Path("input_data/case_nuts2_complete")
    output_path = Path("input_data/uncertainty_scenarios_genesys")

    if genesys_path.exists() and base_case.exists():
        # Create sampler
        sampler = GENeSYSScenarioSampler(genesys_path, seed=42)

        # Generate a few test cases (4 GENeSYS scenarios × 1 markup × 1 tech = 4 cases)
        cases = sampler.generate_discrete_genesys_cases(
            charging_markups=[0.15],
            tech_multipliers=[1.0]
        )

        # Apply to YAML files
        modifier = YAMLModifierGENeSYS(base_case, output_path, sampler)
        scenario_paths = modifier.apply_all_cases(cases[:4])  # Just first 4 for testing

        print("\nCreated scenario folders:")
        for p in scenario_paths:
            print(f"  {p}")
    else:
        print("Required paths not found. Please adjust paths.")
