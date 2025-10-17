"""
SM Preprocessing - Parameter File Generator
===========================================

This script loads preprocessed NUTS-3 geographic/path data and generates
all parameter files (Technology, Fuel, FuelingInfrTypes, etc.) with
configurable parameters.

Workflow:
1. Run SM_preprocessing_nuts3_complete.py first (creates sm_nuts3_test and sm_nuts3_complete)
2. Run this script to generate parameter files with different configurations
3. Creates complete input data set in input_data/case_XXX/

Default: Uses sm_nuts3_test (100 OD-pairs >= 360km) for fast testing
Alternative: Use sm_nuts3_complete (all OD-pairs) for full analysis

This allows creating multiple input file sets with varying parameters!

Author: Claude Code
Date: 2025-10-16
"""

import yaml
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import numpy as np
import pandas as pd


class SMParameterGenerator:
    """
    Generate parameter YAML files for TransComp model.
    Loads preprocessed NUTS-3 data and adds configurable parameters.
    """

    def __init__(self,
                 nuts3_data_dir: str = "input_data/sm_nuts3_test",  # TEST CASE: 100 OD-pairs >= 360km
                 # nuts3_data_dir: str = "input_data/sm_nuts3_complete",  # FULL CASE: All OD-pairs
                 output_dir: str = None,
                 case_name: str = None,
                 electricity_prices_variable: bool = False):
        """
        Initialize parameter generator.

        Parameters:
        -----------
        nuts3_data_dir : str
            Directory containing preprocessed NUTS-3 data (GeographicElement, Path, Odpair)
        output_dir : str
            Output directory for complete case (default: input_data/case_XXX)
        case_name : str
            Custom case name (default: auto-generated with timestamp)
        electricity_prices_variable : bool
            If True, use location-specific electricity prices from GENeSYS-MOD data
            If False, use uniform average prices for all locations (default: False)
        """
        self.script_dir = Path(__file__).parent
        self.nuts3_data_dir = self.script_dir / nuts3_data_dir
        self.electricity_prices_variable = electricity_prices_variable

        # Generate case name with timestamp
        if case_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            case_name = f"case_{timestamp}"

        if output_dir is None:
            output_dir = self.script_dir / "input_data" / case_name
        else:
            output_dir = Path(output_dir)

        self.output_dir = output_dir
        self.case_name = case_name

        # Data holders
        self.geographic_elements = []
        self.paths = []
        self.odpairs = []
        self.initial_vehicle_stock = []
        self.mandatory_breaks = []

        # NUTS region filter (matching SM-preprocessing.ipynb lines 186-189)
        self.nuts_to_filter_for = {
            "NUTS_0": ["DE", "DK"],
            "NUTS_1": ["SE1", "SE2", "AT3", "ITC", "ITH", "ITI", "ITF"],
            "NUTS_2": ["SE11", "SE12", "SE21", "SE22", "NO08", "NO09", "NO02", "NO0A"],
        }

        # Electricity price data (loaded when needed)
        self.elec_prices_df = None
        self.av_electricity_tax = None

    def _filter_by_nuts_regions(self, geographic_elements, paths, odpairs):
        """
        Filter geographic elements, paths, and OD-pairs by NUTS regions.
        Matches the filtering logic from SM-preprocessing.ipynb.

        Note: Preprocessed data has country codes but not full NUTS IDs.
        We extract country codes from NUTS_0 level in the filter dict.
        """
        # Extract country codes from NUTS_0 level
        # NUTS_0: ["DE", "DK"] and also from NUTS_1/2: ["SE1", "AT3", "ITC", ...] -> SE, AT, IT, NO
        relevant_countries = set()

        # Add NUTS_0 countries directly
        relevant_countries.update(self.nuts_to_filter_for.get("NUTS_0", []))

        # Extract country codes from NUTS_1 and NUTS_2 (first 2 characters)
        for level in ["NUTS_1", "NUTS_2"]:
            for code in self.nuts_to_filter_for.get(level, []):
                if len(code) >= 2:
                    relevant_countries.add(code[:2])

        print(f"  Filtering by countries: {sorted(relevant_countries)}")

        # Filter geographic elements (nodes) by country
        filtered_nodes = []
        for geo in geographic_elements:
            if geo['type'] == 'node':
                country = geo.get('country', '')
                if country in relevant_countries:
                    filtered_nodes.append(geo)

        # Get IDs of filtered nodes
        filtered_node_ids = {node['id'] for node in filtered_nodes}
        print(f"  Found {len(filtered_nodes)} nodes in relevant countries")

        # Filter edges - keep only edges where both endpoints are in filtered nodes
        filtered_edges = []
        for geo in geographic_elements:
            if geo['type'] == 'edge':
                # Check if both from_node and to_node are in filtered nodes
                from_node = geo.get('from_node')
                to_node = geo.get('to_node')
                if from_node in filtered_node_ids and to_node in filtered_node_ids:
                    filtered_edges.append(geo)

        filtered_geographic_elements = filtered_nodes + filtered_edges

        # Filter paths - keep only paths where all nodes in sequence are in filtered nodes
        filtered_paths = []
        for path in paths:
            sequence = path.get('sequence', [])
            if all(node_id in filtered_node_ids for node_id in sequence):
                filtered_paths.append(path)

        # Get IDs of filtered paths
        filtered_path_ids = {path['id'] for path in filtered_paths}

        # Filter OD-pairs - keep only those where 'from' and 'to' nodes are in filtered nodes
        # and the path_id is in filtered paths
        filtered_odpairs = []
        for odpair in odpairs:
            from_node = odpair.get('from')
            to_node = odpair.get('to')
            path_id = odpair.get('path_id')

            # Check if both from and to nodes are in filtered nodes
            # and the path is in filtered paths
            if (from_node in filtered_node_ids and
                to_node in filtered_node_ids and
                path_id in filtered_path_ids):
                filtered_odpairs.append(odpair)

        print(f"  Found {len(filtered_odpairs)} OD-pairs with valid paths and nodes")

        return filtered_geographic_elements, filtered_paths, filtered_odpairs

    def load_nuts3_data(self):
        """Load preprocessed NUTS-3 geographic and path data, then filter by NUTS regions."""
        print("="*80)
        print("LOADING PREPROCESSED NUTS-3 DATA")
        print("="*80)
        print(f"Source: {self.nuts3_data_dir}")
        print()

        # Load geographic elements
        geo_file = self.nuts3_data_dir / "GeographicElement.yaml"
        if geo_file.exists():
            with open(geo_file, 'r') as f:
                all_geographic_elements = yaml.safe_load(f)
            print(f"[OK] Loaded {len(all_geographic_elements)} geographic elements (before filtering)")
        else:
            raise FileNotFoundError(f"GeographicElement.yaml not found in {self.nuts3_data_dir}")

        # Load paths
        path_file = self.nuts3_data_dir / "Path.yaml"
        if path_file.exists():
            with open(path_file, 'r') as f:
                all_paths = yaml.safe_load(f)
            print(f"[OK] Loaded {len(all_paths)} paths (before filtering)")
        else:
            raise FileNotFoundError(f"Path.yaml not found in {self.nuts3_data_dir}")

        # Load OD-pairs
        odpair_file = self.nuts3_data_dir / "Odpair.yaml"
        if odpair_file.exists():
            with open(odpair_file, 'r') as f:
                all_odpairs = yaml.safe_load(f)
            print(f"[OK] Loaded {len(all_odpairs)} OD-pairs (before filtering)")
        else:
            raise FileNotFoundError(f"Odpair.yaml not found in {self.nuts3_data_dir}")

        # Apply NUTS filtering (matching SM-preprocessing.ipynb)
        print()
        print("Applying NUTS region filter...")
        self.geographic_elements, self.paths, self.odpairs = self._filter_by_nuts_regions(
            all_geographic_elements, all_paths, all_odpairs
        )
        print(f"[FILTERED] {len(self.geographic_elements)} geographic elements")
        print(f"[FILTERED] {len(self.paths)} paths")
        print(f"[FILTERED] {len(self.odpairs)} OD-pairs")

        # Load initial vehicle stock
        stock_file = self.nuts3_data_dir / "InitialVehicleStock.yaml"
        if stock_file.exists():
            with open(stock_file, 'r') as f:
                self.initial_vehicle_stock = yaml.safe_load(f)
            print(f"[OK] Loaded {len(self.initial_vehicle_stock)} initial vehicle stock entries")
        else:
            print("[SKIP] InitialVehicleStock.yaml not found (will generate default)")
            self.initial_vehicle_stock = []

        # Load mandatory breaks
        breaks_file = self.nuts3_data_dir / "MandatoryBreaks.yaml"
        if breaks_file.exists():
            with open(breaks_file, 'r') as f:
                self.mandatory_breaks = yaml.safe_load(f)
            print(f"[OK] Loaded {len(self.mandatory_breaks)} mandatory breaks")
        else:
            print("[SKIP] MandatoryBreaks.yaml not found")
            self.mandatory_breaks = []

        print()

    def generate_technology_params(self) -> List[Dict]:
        """Generate Technology parameter list."""
        return [
            {'id': 0, 'name': 'ICEV', 'fuel': 'diesel'},
            {'id': 1, 'name': 'BEV', 'fuel': 'electricity'},
        ]

    def _extrapolate_years(self, known_values: dict, full_years: list) -> dict:
        """
        Linearly interpolate and extrapolate values for given years.

        Parameters:
        -----------
        known_values : dict
            Dictionary of {year: value}
        full_years : list
            List of all years to cover (can include years outside known)

        Returns:
        --------
        dict
            {year: value} for all years in full_years
        """
        from bisect import bisect_left

        known_years = sorted(known_values.keys())
        result = {}

        for y in sorted(full_years):
            if y in known_values:
                result[y] = known_values[y]
            elif y < known_years[0]:
                # Extrapolate before first known year
                y0, y1 = known_years[0], known_years[1]
                v0, v1 = known_values[y0], known_values[y1]
                slope = (v1 - v0) / (y1 - y0)
                result[y] = float(v0 + slope * (y - y0))
            elif y > known_years[-1]:
                # Extrapolate after last known year
                y0, y1 = known_years[-2], known_years[-1]
                v0, v1 = known_values[y0], known_values[y1]
                slope = (v1 - v0) / (y1 - y0)
                result[y] = float(v1 + slope * (y - y1))
            else:
                # Interpolate between closest known years
                idx = bisect_left(known_years, y)
                y0, y1 = known_years[idx - 1], known_years[idx]
                v0, v1 = known_values[y0], known_values[y1]
                t = (y - y0) / (y1 - y0)
                result[y] = float(v0 + t * (v1 - v0))
        return result

    def _load_electricity_price_data(self):
        """
        Load electricity price data from GENeSYS-MOD CSV and connection costs.
        Matches SM-preprocessing.ipynb notebook cells 59-71.
        """
        if self.elec_prices_df is not None:
            return  # Already loaded

        print("Loading electricity price data from GENeSYS-MOD...")

        # Get unique countries from filtered geographic elements
        countries = set()
        for geo_elem in self.geographic_elements:
            if geo_elem['type'] == 'node':
                country = geo_elem.get('country', '')
                if country:
                    countries.add(country)

        # Load connection costs for electricity tax
        conn_costs_path = self.script_dir / "data" / "electricity data" / "41467_2022_32835_MOESM4_ESM.xlsx"
        if conn_costs_path.exists():
            conn_costs = pd.read_excel(conn_costs_path, sheet_name="Main results", header=1)

            # Filter for CommercialPublic-DC and our countries
            filtered_conn_costs = conn_costs[
                (conn_costs['Option'] == 'CommercialPublic-DC') &
                (conn_costs['Code'].isin(countries))
            ]
            self.av_electricity_tax = filtered_conn_costs["CostElectricityT"].mean()
            print(f"  Average electricity tax: {self.av_electricity_tax:.4f} EUR/kWh")
        else:
            print(f"  [WARN] Connection costs file not found, using default tax: 0.0 EUR/kWh")
            self.av_electricity_tax = 0.0

        # Load GENeSYS-MOD electricity prices
        genesys_path = self.script_dir / "data" / "GENeSYS-MOD_EU-EnVis-2060_v1.2.0_native" / "output_endogenous_fuelcosts.csv"
        if genesys_path.exists():
            excel_data = pd.read_csv(genesys_path)

            # Filter for Power fuel and our countries
            filtered_excel = excel_data[
                (excel_data['Fuel'] == 'Power') &
                (excel_data['Region'].isin(countries))
            ]

            # Select scenario and convert units
            selected_scenario = 'Go RES v1.2'
            elec_price_data = filtered_excel[
                (filtered_excel['Model Version'] == selected_scenario) &
                (filtered_excel['Unit'] == 'Fuel Costs in EUR/MWh')
            ].copy()

            # Convert EUR/MWh to EUR/kWh
            elec_price_data.loc[:, 'elec_price_EURperkWh'] = elec_price_data['Value '] / 1000

            # Rename columns for consistency
            elec_price_data = elec_price_data.rename(columns={'Region': 'NUTS_region', 'Year': 'year'})

            # Create final DataFrame
            self.elec_prices_df = elec_price_data[['NUTS_region', 'year', 'elec_price_EURperkWh']].copy()

            print(f"  Loaded {len(self.elec_prices_df)} electricity price entries")
            print(f"  Countries: {sorted(self.elec_prices_df['NUTS_region'].unique())}")
            print(f"  Years: {sorted(self.elec_prices_df['year'].unique())}")
        else:
            print(f"  [WARN] GENeSYS-MOD file not found at {genesys_path}")
            print(f"  Using fallback: uniform price of 0.25 EUR/kWh")
            self.elec_prices_df = None

    def generate_fuel_params(self, years: List[int] = list(range(2020, 2041))) -> List[Dict]:
        """
        Generate Fuel parameter list.
        IMPORTANT: IDs match notebook - 0=electricity, 1=diesel

        Parameters:
        -----------
        years : list
            Years to include (default: 2020-2040)
        """
        num_years = len(years)
        return [
            {
                'id': 0,
                'name': 'electricity',
                'emission_factor': [0.0] * num_years,  # kg CO2e/kWh
                'cost_per_kWh': [0.0] * num_years,  # EUR/kWh
                'cost_per_kW': [0.0] * num_years,  # EUR/kW
                'fueling_infrastructure_om_costs': [0.0] * num_years,  # EUR/kW/year
            },
            {
                'id': 1,
                'name': 'diesel',
                'emission_factor': [266] * num_years,  # kg CO2e/kWh
                'cost_per_kWh': [0.0] * num_years,  # EUR/kWh
                'cost_per_kW': [0.0] * num_years,  # EUR/kW
                'fueling_infrastructure_om_costs': [0.0] * num_years,  # EUR/kW/year
            },
        ]

    def generate_fuel_cost_params(self, years: List[int] = list(range(2020, 2041))) -> List[Dict]:
        """
        Generate FuelCost parameter list (location-specific fuel costs).
        Matches SM-preprocessing.ipynb notebook cells 71-72 EXACTLY.

        Loads electricity prices from GENeSYS-MOD data and adds electricity tax.
        Uses self.electricity_prices_variable to toggle between location-specific
        and uniform pricing.

        Parameters:
        -----------
        years : list
            Years to include (default: 2020-2040)
        """
        num_years = len(years)
        y_init = years[0]
        Y = len(years)

        # Load electricity price data if needed
        if self.electricity_prices_variable:
            self._load_electricity_price_data()

        # Calculate average electricity prices (used when electricity_prices_variable = False)
        if self.elec_prices_df is not None:
            avg_elec_prices_per_year = self.elec_prices_df.groupby("year")["elec_price_EURperkWh"].mean().reset_index()
            av_elec_price_dict = dict(zip(
                [int(year) for year in avg_elec_prices_per_year["year"].to_list()],
                avg_elec_prices_per_year["elec_price_EURperkWh"].to_list()
            ))
            av_all_elec_prices = self._extrapolate_years(av_elec_price_dict, range(y_init, y_init + Y))
            av_electricity_prices = [float(av_all_elec_prices[y] + self.av_electricity_tax) for y in range(y_init, y_init + Y)]
        else:
            # Fallback if data files not found
            av_electricity_prices = [0.25] * num_years

        fuel_cost_list = []
        fc_id = 0

        # Create fuel costs for each geographic element (matching notebook: ALL geo elements, not just nodes!)
        for geo in self.geographic_elements:
            # Get country code for this geographic element
            country_code = geo.get("country", "")

            # Calculate location-specific electricity prices
            if self.elec_prices_df is not None and country_code:
                extract_elec_prices = self.elec_prices_df[self.elec_prices_df['NUTS_region'] == country_code]
                if not extract_elec_prices.empty:
                    elec_price_dict = dict(zip(
                        [int(item) for item in extract_elec_prices["year"].to_list()],
                        extract_elec_prices["elec_price_EURperkWh"].to_list()
                    ))
                    all_elec_prices = self._extrapolate_years(elec_price_dict, range(y_init, y_init + Y))
                    electricity_prices = [float(all_elec_prices[y] + self.av_electricity_tax) for y in range(y_init, y_init + Y)]
                else:
                    # No data for this country, use average
                    electricity_prices = av_electricity_prices
            else:
                # Use average if no data loaded
                electricity_prices = av_electricity_prices

            # Use electricity_prices_variable parameter to determine which prices to use
            if self.electricity_prices_variable:
                # Use location-specific prices
                cost_per_kWh = electricity_prices
            else:
                # Use uniform average prices for all locations
                cost_per_kWh = av_electricity_prices

            fuel_cost_list.append({
                "id": fc_id,
                "location": geo["id"],
                "fuel": "electricity",
                "cost_per_kWh": cost_per_kWh,
            })
            fc_id += 1

            fuel_cost_list.append({
                "id": fc_id,
                "location": geo["id"],
                "fuel": "diesel",
                "cost_per_kWh": [0.065] * Y,  # Constant diesel price
            })
            fc_id += 1

        pricing_mode = "location-specific" if self.electricity_prices_variable else "uniform (average)"
        print(f"Created {len(fuel_cost_list)} fuel cost entries for {len(self.geographic_elements)} geo elements")
        print(f"Electricity pricing mode: {pricing_mode}")

        return fuel_cost_list

    def generate_fueling_infr_types(self, years: List[int] = list(range(2020, 2041))) -> List[Dict]:
        """
        Generate FuelingInfrTypes parameter list matching SM-preprocessing.ipynb notebook EXACTLY.

        From notebook:
        - Hardware costs: {2025: ~398, 2030: ~370, 2035: ~344, 2040: ~320, 2045: ~298, 2050: ~278} EUR/kW
        - Installation costs: {2025: ~104, 2030: ~96, 2035: ~90, 2040: ~83, 2045: ~78, 2050: ~72} EUR/kW
        - Grid connection: 900/1000 = 0.9 EUR/kW
        - Total cost_per_kW = hardware + installation + grid_connection
        - OM costs: 3% of cost_per_kW per year for electricity, 1% for diesel

        Parameters:
        -----------
        years : list
            Years to include (default: 2020-2040)
        """
        # From notebook - hardware costs from Plözl et al. 2025
        hardware_costs = {2025: (336 + 460)/2, 2030: (303 + 437)/2, 2035: (273 + 415)/2,
                          2040: (245 + 395)/2, 2045: (221 + 375)/2, 2050: (199 + 356)/2}
        installation_costs = {2025: (94.5 + 114)/2, 2030: (85.1 + 108)/2, 2035: (76.5 + 103)/2,
                              2040: (68.9 + 98)/2, 2045: (62 + 93)/2, 2050: (55.8 + 88)/2}
        grid_connection = 900 / 1000  # EUR/kW

        # Calculate total installation costs per kW
        total_install_kW_costs = {year: hardware_costs[year] + installation_costs[year] + grid_connection
                                  for year in hardware_costs.keys()}

        # Extrapolate to all years
        costs_dev_mega = {}
        for year in years:
            if year < 2025:
                costs_dev_mega[year] = total_install_kW_costs[2025]
            elif year > 2050:
                costs_dev_mega[year] = total_install_kW_costs[2050]
            else:
                # Linear interpolation between known points
                for key_year in sorted(total_install_kW_costs.keys()):
                    if year <= key_year:
                        if year == key_year:
                            costs_dev_mega[year] = total_install_kW_costs[key_year]
                        else:
                            # Find previous key_year
                            prev_years = [y for y in sorted(total_install_kW_costs.keys()) if y < year]
                            if prev_years:
                                prev_year = prev_years[-1]
                                # Linear interpolation
                                t = (year - prev_year) / (key_year - prev_year)
                                costs_dev_mega[year] = (1-t) * total_install_kW_costs[prev_year] + t * total_install_kW_costs[key_year]
                            else:
                                costs_dev_mega[year] = total_install_kW_costs[key_year]
                        break

        # Create cost lists
        cost_per_kW_list = [float(costs_dev_mega[year]) for year in years]
        om_costs_elec_list = [0.03 * float(costs_dev_mega[year]) for year in years]
        om_costs_diesel_list = [0.01 * float(costs_dev_mega[year]) for year in years]

        return [
            {
                'id': 1,
                'fuel': 'electricity',
                'fueling_type': 'slow_charging_station',
                'fueling_power': [1000] * len(years),  # kW
                'additional_fueling_time': False,
                'max_occupancy_rate_veh_per_year': 60,  # Shoman et al. (2023)
                'by_route': False,
                'track_detour_time': False,
                'gamma': [0.3] * len(years),
                'cost_per_kW': cost_per_kW_list,
                'cost_per_kWh_network': [0.0] * len(years),
                'om_costs': om_costs_elec_list,  # 3% of investment cost
            },
            {
                'id': 2,
                'fuel': 'electricity',
                'fueling_type': 'fast_charging_station',
                'fueling_power': [100] * len(years),  # kW
                'additional_fueling_time': False,
                'max_occupancy_rate_veh_per_year': 60,  # Shoman et al. (2023)
                'by_route': False,
                'track_detour_time': False,
                'gamma': [0.3] * len(years),
                'cost_per_kW': cost_per_kW_list,
                'cost_per_kWh_network': [0.0] * len(years),
                'om_costs': om_costs_elec_list,  # 3% of investment cost
            },
            {
                'id': 0,
                'fuel': 'diesel',
                'fueling_type': 'conventional_fueling_station',
                'fueling_power': [10000] * len(years),  # kW
                'additional_fueling_time': False,
                'max_occupancy_rate_veh_per_year': 60,  # Shoman et al. (2023)
                'by_route': False,
                'track_detour_time': False,
                'gamma': [0.3] * len(years),
                'cost_per_kW': [0.0] * len(years),
                'cost_per_kWh_network': [0.0] * len(years),
                'om_costs': om_costs_diesel_list,  # 1% of investment cost
            },
        ]

    def generate_mode_params(self, years: List[int] = list(range(2020, 2041))) -> List[Dict]:
        """
        Generate Mode parameter list.
        IMPORTANT: Match notebook exactly - id=1, name="road"

        Parameters:
        -----------
        years : list
            Years to include (default: 2020-2040)
        """
        num_years = len(years)
        return [
            {
                'id': 1,
                'name': 'road',
                'quantify_by_vehs': True,
                'costs_per_ukm': [0] * num_years,
                'emission_factor': [699] * num_years,
                'infrastructure_expansion_costs': [0.0] * num_years,
                'infrastructure_om_costs': [0.1] * num_years,
                'waiting_time': [0.0] * num_years,
            },
        ]

    def generate_vehicletype_params(self) -> List[Dict]:
        """Generate Vehicletype parameter list.
        IMPORTANT: Match notebook exactly - name="long-haul truck"
        """
        return [
            {
                'id': 0,
                'name': 'long-haul truck',
                'mode': 1,
                'product': 'freight',
            },
        ]

    def generate_tech_vehicle_params(self, num_generations: int = 31) -> List[Dict]:
        """
        Generate TechVehicle parameter list matching SM-preprocessing.ipynb notebook EXACTLY.

        Parameters from notebook:
        - occ = 13.6/26
        - L_to_kWh = 9.7 (diesel liters to kWh conversion)
        - Capital costs, maintenance, fuel economy: extrapolated from year-specific dicts
        - Lifetime: 10 years for ALL vehicles
        - AnnualRange: 136750 km for ALL
        - fueling_time: 0.5 hours for ALL

        Parameters:
        -----------
        num_generations : int
            Number of generations to model (default: 31 for G=Y+pre_y=21+10=31)
        """
        # Constants from notebook
        L_to_kWh = 9.7
        occ = 13.6 / 26
        vehicle_tax_ICEV = 561
        vehicle_tax_BEV = 5
        subsidy = 20000

        # ICEV capital costs (extrapolated from notebook capital_cost_dict)
        icev_capital = [105484.0] * 5 + [109159.0] * 5 + [115252.0] * 21

        # BEV capital costs (extrapolated from notebook, with subsidy)
        bev_capital = [417255.0 - subsidy] * 5 + [200006.0 - subsidy] * 5 + [145346.0 - subsidy] * 21

        # ICEV specific consumption: fuel_economy_dict * L_to_kWh
        icev_spec_cons = [29.86 * L_to_kWh] * 5 + [26.67 * L_to_kWh] * 5 + [23.47 * L_to_kWh] * 21

        # BEV specific consumption from notebook fuel_economy_dict
        bev_spec_cons = [1.60] * 5 + [1.41] * 5 + [1.21] * 21

        # BEV peak_fueling: 350 kW for 2020-2034, 900 kW for 2035-2044, 1000 kW for 2045-2050
        bev_peak_fueling = [350.0] * 15 + [900.0] * 10 + [1000.0] * 6

        # ICEV maintenance (generation x age matrix)
        icev_maint_annual = [[20471.0 + vehicle_tax_ICEV] * num_generations for _ in range(num_generations)]

        # BEV maintenance (generation x age matrix)
        bev_maint_annual = [[14359.0 + vehicle_tax_BEV] * num_generations for _ in range(num_generations)]

        return [
            {
                'id': 0,
                'name': 'ICEV',
                'technology': 0,
                'vehicle_type': 'long-haul truck',
                'capital_cost': icev_capital,
                'maintenance_cost_annual': icev_maint_annual,
                'maintenance_cost_distance': [[0.0] * num_generations for _ in range(num_generations)],
                'W': [26.0 * occ] * num_generations,  # 13.6 tons
                'spec_cons': icev_spec_cons,
                'Lifetime': [10] * num_generations,
                'AnnualRange': [136750.0] * num_generations,
                'products': ['freight'],
                'tank_capacity': [570.0 * L_to_kWh] * num_generations,  # 5529 kWh
                'peak_fueling': [28500.0] * num_generations,
                'fueling_time': [0.5] * num_generations,
            },
            {
                'id': 1,
                'name': 'BEV',
                'technology': 1,
                'vehicle_type': 'long-haul truck',
                'capital_cost': bev_capital,
                'maintenance_cost_annual': bev_maint_annual,
                'maintenance_cost_distance': [[0.0] * num_generations for _ in range(num_generations)],
                'W': [26.0 * occ * 0.75] * num_generations,  # 10.2 tons
                'spec_cons': bev_spec_cons,
                'Lifetime': [10] * num_generations,
                'AnnualRange': [136750.0] * num_generations,
                'products': ['freight'],
                'tank_capacity': [1187.0] * num_generations,
                'peak_fueling': bev_peak_fueling,
                'fueling_time': [0.5] * num_generations,
            },
        ]

    def generate_product_params(self) -> List[Dict]:
        """Generate Product parameter list."""
        return [
            {'id': 0, 'name': 'freight'},  # Match Odpair.yaml product names
        ]

    def generate_financial_status_params(self,
                                          years: List[int] = list(range(2020, 2041))) -> List[Dict]:
        """
        Generate FinancialStatus parameter list matching SM-preprocessing.ipynb notebook EXACTLY.

        From notebook (lines 1131-1143):
        - VoT: 0.0 (NOT 30.0!)
        - All budget fields: 0.0

        Parameters:
        -----------
        years : list
            Years to include (default: 2020-2040)
        """
        return [
            {
                'id': 0,
                'name': 'any',
                'VoT': 0.0,  # NOTEBOOK VALUE: 0.0 (NOT 30.0!)
                'monetary_budget_operational': 0.0,
                'monetary_budget_operational_lb': 0.0,
                'monetary_budget_operational_ub': 0.0,
                'monetary_budget_purchase': 0.0,
                'monetary_budget_purchase_lb': 0.0,
                'monetary_budget_purchase_ub': 0.0,
                'monetary_budget_purchase_time_horizon': 0,
            },
        ]

    def generate_regiontype_params(self, years: List[int] = list(range(2020, 2041))) -> List[Dict]:
        """
        Generate Regiontype parameter list.

        Parameters:
        -----------
        years : list
            Years to include (default: 2020-2040)
        """
        num_years = len(years)
        return [
            {
                'id': 0,
                'name': 'highway',
                'costs_var': [0.0] * num_years,  # Variable costs (EUR/ukm)
                'costs_fix': [0.0] * num_years,  # Fixed costs (EUR/year)
            },
            {
                'id': 1,
                'name': 'urban',
                'costs_var': [0.0] * num_years,  # Variable costs (EUR/ukm)
                'costs_fix': [0.0] * num_years,  # Fixed costs (EUR/year)
            },
            {
                'id': 2,
                'name': 'rural',
                'costs_var': [0.0] * num_years,  # Variable costs (EUR/ukm)
                'costs_fix': [0.0] * num_years,  # Fixed costs (EUR/year)
            },
        ]

    def generate_speed_params(self) -> List[Dict]:
        """Generate Speed parameter list (average speeds by mode/region).
        IMPORTANT: Match notebook - vehicle_type="long-haul truck"
        """
        return [
            {
                'id': 0,
                'region_type': 'highway',
                'vehicle_type': 'long-haul truck',
                'travel_speed': 80.0,  # km/h
            },
            {
                'id': 1,
                'region_type': 'urban',
                'vehicle_type': 'long-haul truck',
                'travel_speed': 40.0,  # km/h
            },
            {
                'id': 2,
                'region_type': 'rural',
                'vehicle_type': 'long-haul truck',
                'travel_speed': 60.0,  # km/h
            },
        ]

    def generate_model_params(self) -> Dict:
        """Generate Model parameter dictionary matching SM-preprocessing.ipynb notebook EXACTLY."""
        return {
            'Y': 21,  # Number of years in optimization horizon
            'y_init': 2020,  # Initial year
            'pre_y': 10,  # Years before initial year to consider (prey_y in notebook)
            'gamma': 0.0001,  # NOTEBOOK VALUE: 0.0001 (NOT 0.05!)
            'discount_rate': 0.05,  # Discount rate (5%)
            'budget_penalty_plus': 10000,  # NOTEBOOK VALUE: 10000 (NOT 1000000!)
            'budget_penalty_minus': 10000,  # NOTEBOOK VALUE: 10000 (NOT 1000000!)
            'budget_penalty_yearly_plus': 10000000,  # NOTEBOOK VALUE: 10000000 (NOT 100000!)
            'budget_penalty_yearly_minus': 10000000,  # NOTEBOOK VALUE: 10000000 (NOT 100000!)
            'investment_period': 5,  # NOTEBOOK VALUE: 5 years (NOT 1!)
            'pre_age_sell': False,  # NOTEBOOK VALUE: False (NOT True!)
        }

    def generate_network_connection_costs(self, years: List[int] = list(range(2020, 2041))) -> List[Dict]:
        """
        Generate NetworkConnectionCosts parameter list.

        Format expected by Julia:
        - id: int
        - location: int (geographic element ID - node only!)
        - network_cost_per_kW: array of float (cost per year)
        """
        num_years = len(years)
        # Generate network connection costs for all node geographic elements
        network_costs_list = []
        nc_id = 0

        for geo_elem in self.geographic_elements:
            if geo_elem['type'] == 'node':
                network_costs_list.append({
                    'id': nc_id,
                    'location': geo_elem['id'],  # Use ID (not name) to match GeographicElement!
                    'network_cost_per_kW': [0.1] * num_years,  # EUR/kW connection cost
                })
                nc_id += 1

        return network_costs_list

    def generate_initial_mode_infr(self) -> List[Dict]:
        """
        Generate InitialModeInfr parameter list.

        Format expected by Julia:
        - id: int
        - mode: int (mode ID)
        - allocation: Any (typically -1 for all nodes)
        - installed_ukm: float (installed unit-km capacity)
        """
        return [
            {
                'id': 0,
                'mode': 1,  # road_freight mode (matches Mode.yaml id)
                'allocation': -1,  # -1 = applies to all nodes
                'installed_ukm': 999999.0,  # unlimited capacity
            }
        ]

    def generate_initial_fuel_infr(self) -> List[Dict]:
        """Generate InitialFuelInfr parameter list.
        IMPORTANT: Match notebook - type="conventional_fueling_station"
        """
        # Existing diesel stations everywhere
        infr = []
        for i, geo_elem in enumerate(self.geographic_elements):
            if geo_elem['type'] == 'node':
                infr.append({
                    'id': i,
                    'fuel': 'diesel',
                    'allocation': geo_elem['id'],
                    'installed_kW': 5000.0,  # kW capacity
                    'type': 'conventional_fueling_station',  # References FuelingInfrTypes.fueling_type
                    'by_income_class': False,
                    'income_class': 'any',  # Match FinancialStatus.yaml names
                })
        return infr

    def generate_spatial_flexibility_edges(self, max_flexibility: int = 5) -> List[Dict]:
        """
        Generate SpatialFlexibilityEdges parameter list.

        Creates flexibility ranges for charging infrastructure placement along paths.

        Parameters:
        -----------
        max_flexibility : int
            Maximum flexibility range for infrastructure placement
        """
        # Collect all unique edges from paths
        path_edges = set()
        for path in self.paths:
            seq = path['sequence']
            for i in range(len(seq) - 1):
                edge = (seq[i], seq[i+1])
                path_edges.add(edge)

        # Create spatial flexibility entries
        spatial_flex_list = []
        sf_id = 0

        for from_node, to_node in sorted(path_edges):
            # For each edge, create flexibility range entries
            for flex_range in range(1, max_flexibility + 1):
                spatial_flex_list.append({
                    'id': sf_id,
                    'from': from_node,
                    'to': to_node,
                    'flexibility_range': flex_range,
                })
                sf_id += 1

        return spatial_flex_list

    def _calculate_mandatory_breaks_advanced(self, path, speed=80):
        """
        Calculate mandatory breaks and rest stops along a path, following EU Regulation (EC) No 561/2006.
        Uses advanced algorithm with multi-driver logic and both breaks (B) and rests (R).

        Parameters:
        -----------
        path : dict
            Must contain 'sequence', 'cumulative_distance', 'id', 'length'
        speed : float
            Average travel speed in km/h (default 80)

        Returns:
        --------
        list of dict
            Flat list (one per stop) with all required fields for Julia
        """
        sequence = path['sequence']
        cumulative_distance = path['cumulative_distance']
        path_id = path['id']
        total_length = path['length']

        # 1. Compute total travel time (hours)
        total_driving_time = total_length / speed

        # 2. Determine number of drivers based on EU rule
        #    <= 54h total driving time → 1 driver, else 2 drivers
        num_drivers = 1 if total_driving_time <= 54 else 2

        # 3. Regulatory constants
        SHORT_BREAK_INTERVAL = 4.5       # hours between breaks
        SHORT_BREAK_DURATION = 0.75      # 45 minutes
        DAILY_DRIVING_LIMIT = 9 * num_drivers
        DAILY_REST_DURATION = 9          # hours
        MAX_DRIVING_TIME = DAILY_DRIVING_LIMIT

        # 4. Initialize counters
        break_list = []
        break_number = 0

        # 5. Generate target stop times (in hours of driving)
        target_time = SHORT_BREAK_INTERVAL
        daily_counter = 0.0

        while target_time < total_driving_time + 1e-6:
            # Decide event type
            if daily_counter + SHORT_BREAK_INTERVAL > MAX_DRIVING_TIME:
                # Exceeds daily driving → insert Rest (R)
                event_type = 'R'
                event_name = 'rest'
                event_duration = DAILY_REST_DURATION
                charging_type = 'slow'
                daily_counter = 0.0  # reset after rest
            else:
                # Normal Break (B)
                event_type = 'B'
                event_name = 'break'
                event_duration = SHORT_BREAK_DURATION
                charging_type = 'fast'
                daily_counter += SHORT_BREAK_INTERVAL

            break_number += 1

            # Find corresponding node index for this event
            max_distance_before_event = target_time * speed
            latest_node_idx = None
            latest_geo_id = None
            actual_cum_distance = None

            for i, cum_dist in enumerate(cumulative_distance):
                if cum_dist <= max_distance_before_event:
                    latest_node_idx = i
                    node = sequence[i]
                    latest_geo_id = node['id'] if isinstance(node, dict) else node
                    actual_cum_distance = cum_dist
                else:
                    break

            # Safety fallback
            if latest_node_idx is None and len(sequence) > 0:
                latest_node_idx = len(sequence) - 1
                node = sequence[latest_node_idx]
                latest_geo_id = node['id'] if isinstance(node, dict) else node
                actual_cum_distance = cumulative_distance[-1]

            cumulative_driving_time = actual_cum_distance / speed
            time_with_breaks = cumulative_driving_time + event_duration

            # Append entry
            break_list.append({
                'path_id': path_id,
                'path_length': total_length,
                'total_driving_time': total_driving_time,
                'num_drivers': num_drivers,
                'break_number': break_number,
                'event_type': event_type,
                'event_name': event_name,
                'latest_node_idx': latest_node_idx,
                'latest_geo_id': latest_geo_id,
                'cumulative_distance': actual_cum_distance,
                'cumulative_driving_time': cumulative_driving_time,
                'time_with_breaks': time_with_breaks,
                'charging_type': charging_type
            })

            # Increment target_time and continue
            target_time += SHORT_BREAK_INTERVAL

        return break_list

    def save_all_parameters(self):
        """Generate and save all parameter files."""
        print("="*80)
        print("GENERATING PARAMETER FILES")
        print("="*80)
        print(f"Output: {self.output_dir}")
        print()

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Generate all parameters
        components = {
            "Technology": self.generate_technology_params(),
            "Fuel": self.generate_fuel_params(),
            "FuelCost": self.generate_fuel_cost_params(),
            "FuelingInfrTypes": self.generate_fueling_infr_types(),
            "Mode": self.generate_mode_params(),
            "Vehicletype": self.generate_vehicletype_params(),
            "TechVehicle": self.generate_tech_vehicle_params(),
            "Product": self.generate_product_params(),
            "FinancialStatus": self.generate_financial_status_params(),
            "Regiontype": self.generate_regiontype_params(),
            "Speed": self.generate_speed_params(),
            "Model": self.generate_model_params(),
            "NetworkConnectionCosts": self.generate_network_connection_costs(),
            "InitialModeInfr": self.generate_initial_mode_infr(),
            "InitialFuelInfr": self.generate_initial_fuel_infr(),
            "SpatialFlexibilityEdges": self.generate_spatial_flexibility_edges(),
        }

        # Add preprocessed data
        components["GeographicElement"] = self.geographic_elements
        components["Path"] = self.paths
        components["Odpair"] = self.odpairs

        # Keep all InitialVehicleStock entries (including zero-stock) because OD-pairs reference them by ID
        # NOTE: We initially tried filtering zero-stock entries, but this breaks OD-pair references
        # Julia code (support_functions.jl:483) looks up vehicle stock by ID from odpair["vehicle_stock_init"]
        components["InitialVehicleStock"] = self.initial_vehicle_stock

        # Calculate mandatory breaks using advanced EU regulation algorithm
        # This recalculates breaks properly with multi-driver logic and rest periods
        speed_dict = self.generate_speed_params()
        travel_speed = speed_dict[0]['travel_speed']  # km/h (highway speed)

        all_mandatory_breaks = []
        break_id = 0

        print("\nCalculating mandatory breaks using advanced EU regulations...")
        print(f"  Speed: {travel_speed} km/h")

        for path in self.paths:
            # Calculate breaks for this path using advanced algorithm
            breaks_for_path = self._calculate_mandatory_breaks_advanced(path, speed=travel_speed)

            # Add global ID to each break and append to list
            for break_entry in breaks_for_path:
                break_entry['id'] = break_id
                all_mandatory_breaks.append(break_entry)
                break_id += 1

        # Group breaks by path for summary
        from collections import defaultdict
        breaks_by_path = defaultdict(list)
        for mb in all_mandatory_breaks:
            breaks_by_path[mb['path_id']].append(mb)

        print(f"  Generated {len(all_mandatory_breaks)} mandatory breaks/rests across {len(breaks_by_path)} paths")
        print(f"  Break types: {sum(1 for mb in all_mandatory_breaks if mb['event_type'] == 'B')} breaks (B), "
              f"{sum(1 for mb in all_mandatory_breaks if mb['event_type'] == 'R')} rests (R)")

        components["MandatoryBreaks"] = all_mandatory_breaks

        # Save all components
        for name, data in components.items():
            filepath = self.output_dir / f"{name}.yaml"
            with open(filepath, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

            file_size = filepath.stat().st_size
            print(f"[OK] {name}.yaml ({file_size:,} bytes)")

        print()
        print("="*80)
        print("SUCCESS!")
        print("="*80)
        print(f"\nComplete input data set created in:")
        print(f"  {self.output_dir.relative_to(self.script_dir)}")
        print(f"\nTo use in Julia:")
        print(f'  input_path = joinpath(@__DIR__, "{self.output_dir.relative_to(self.script_dir)}")')
        print()

    def run(self):
        """Run complete preprocessing workflow."""
        self.load_nuts3_data()
        self.save_all_parameters()


def main():
    """Main entry point."""
    import sys

    # Parse command line arguments
    if len(sys.argv) > 1:
        nuts3_data_dir = sys.argv[1]
    else:
        nuts3_data_dir = "input_data/sm_nuts2_international_aggregated"  # TEST CASE: 100 OD-pairs >= 360km
        # nuts3_data_dir = "input_data/sm_nuts3_complete"  # FULL CASE: All OD-pairs

    if len(sys.argv) > 2:
        case_name = sys.argv[2]
    else:
        case_name = None  # Auto-generate

    # Run preprocessing
    preprocessor = SMParameterGenerator(
        nuts3_data_dir=nuts3_data_dir,
        case_name=case_name
    )

    preprocessor.run()

    print("\n[INFO] You can now create different parameter sets by:")
    print("  1. Modifying the generate_*_params() methods")
    print("  2. Running this script again with a different case name")
    print("\nExamples:")
    print("  python SM_preprocessing.py                                    # Uses sm_nuts3_test (default)")
    print("  python SM_preprocessing.py input_data/sm_nuts3_complete       # Use full dataset")
    print("  python SM_preprocessing.py input_data/sm_nuts3_test custom    # Custom case name")


if __name__ == "__main__":
    main()
