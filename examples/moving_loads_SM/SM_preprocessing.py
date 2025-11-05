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
                 nuts3_data_dir: str = "input_data/fixed_nuts_2",  # FIXED: NUTS2 data with Austria routing
                 # nuts3_data_dir: str = "input_data/sm_nuts3_test",  # TEST CASE: 100 OD-pairs >= 360km
                 # nuts3_data_dir: str = "input_data/sm_nuts3_complete",  # FULL CASE: All OD-pairs
                 output_dir: str = None,
                 case_name: str = None,
                 electricity_prices_variable: bool = True,
                 network_costs_variable: bool = True,
                 reverse_electricity_prices: bool = False,
                 include_rail_mode: bool = False,
                 filter_low_volume: bool = True,
                 min_freight_threshold: float = 1000.0):
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
            If False, use uniform average prices for all locations (default: True)
        network_costs_variable : bool
            If True, use location-specific network connection costs by country
            If False, use uniform average network costs for all locations (default: True)
        reverse_electricity_prices : bool
            If True, reverse the electricity price assignment (highest costs to lowest price countries)
            Only applies when electricity_prices_variable=True (default: False)
        include_rail_mode : bool
            If True, include rail as an additional transport mode (quantify_by_vehs=False)
            If False, only include road mode (default: False)
        filter_low_volume : bool
            If True, filter out OD-pairs with low freight volumes to reduce mandatory breaks
            and overall dataset size. Recommended for large-scale models. (default: True)
        min_freight_threshold : float
            Minimum freight volume (trucks/year) for OD-pair to be included.
            Only applies when filter_low_volume=True. Analysis shows 1,000 trucks/year
            removes 54% of OD-pairs while keeping 99.6% of freight volume. (default: 1000.0)
        """
        self.script_dir = Path(__file__).parent
        self.nuts3_data_dir = self.script_dir / nuts3_data_dir
        self.electricity_prices_variable = electricity_prices_variable
        self.network_costs_variable = network_costs_variable
        self.reverse_electricity_prices = reverse_electricity_prices
        self.include_rail_mode = include_rail_mode
        self.filter_low_volume = filter_low_volume
        self.min_freight_threshold = min_freight_threshold

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
            "NUTS_0": ["DE", "DK", "SE"],
            "NUTS_1": ["ITC", "ITH", "ITI", "ITF"],
            "NUTS_2": ["SE11", "SE12", "SE21", "SE22", "NO08", "NO09", "NO02", "NO0A", "AT33", "AT34", "AT32"],
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

        # Create path lookup dictionary for efficient access
        path_dict = {p['id']: p for p in paths}

        # Calculate initial tkm before any filtering
        initial_tkm = 0.0
        for odpair in odpairs:
            demand = odpair.get('F', [0])[0]  # F[0] is the demand in first year
            path_id = odpair.get('path_id')
            if path_id in path_dict:
                route_length = path_dict[path_id].get('length', 0.0)
                initial_tkm += demand * route_length

        print(f"\n  FREIGHT STATISTICS (Initial):")
        print(f"    Total OD-pairs: {len(odpairs):,}")
        print(f"    Total freight volume: {initial_tkm:,.2f} tkm")

        # Filter geographic elements (nodes) by country
        filtered_nodes = []
        for geo in geographic_elements:
            if geo['type'] == 'node':
                country = geo.get('country', '')
                if country in relevant_countries:
                    filtered_nodes.append(geo)

        # Get IDs of filtered nodes
        filtered_node_ids = {node['id'] for node in filtered_nodes}
        print(f"\n  Found {len(filtered_nodes)} nodes in relevant countries")

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

        # Track tkm removed by different filter types
        local_routes_tkm = 0.0
        geographic_filter_tkm = 0.0
        local_routes_filtered = 0

        # Filter OD-pairs - keep only those where 'from' and 'to' nodes are in filtered nodes
        # and the path_id is in filtered paths
        # ALSO filter out local routes (origin == destination)
        filtered_odpairs = []
        for odpair in odpairs:
            from_node = odpair.get('from')
            to_node = odpair.get('to')
            path_id = odpair.get('path_id')
            demand = odpair.get('F', [0])[0]

            # Calculate tkm for this OD-pair
            if path_id in path_dict:
                route_length = path_dict[path_id].get('length', 0.0)
                odpair_tkm = demand * route_length
            else:
                odpair_tkm = 0.0

            # TEMPORARY FIX: Filter out local routes (origin == destination)
            if from_node == to_node:
                local_routes_filtered += 1
                local_routes_tkm += odpair_tkm
                continue

            # Check if both from and to nodes are in filtered nodes
            # and the path is in filtered paths
            if (from_node in filtered_node_ids and
                to_node in filtered_node_ids and
                path_id in filtered_path_ids):
                filtered_odpairs.append(odpair)
            else:
                geographic_filter_tkm += odpair_tkm

        # Calculate final tkm after filtering
        final_tkm = 0.0
        for odpair in filtered_odpairs:
            demand = odpair.get('F', [0])[0]
            path_id = odpair.get('path_id')
            if path_id in path_dict:
                route_length = path_dict[path_id].get('length', 0.0)
                final_tkm += demand * route_length

        # Calculate total removed and percentages
        total_removed_tkm = initial_tkm - final_tkm
        if initial_tkm > 0:
            local_pct = (local_routes_tkm / initial_tkm) * 100
            geo_pct = (geographic_filter_tkm / initial_tkm) * 100
            total_pct = (total_removed_tkm / initial_tkm) * 100
            retained_pct = (final_tkm / initial_tkm) * 100
        else:
            local_pct = geo_pct = total_pct = retained_pct = 0.0

        print(f"\n  FREIGHT STATISTICS (After filtering):")
        print(f"    Retained OD-pairs: {len(filtered_odpairs):,} ({len(filtered_odpairs)/len(odpairs)*100:.1f}%)")
        print(f"    Retained freight volume: {final_tkm:,.2f} tkm ({retained_pct:.1f}%)")
        print(f"\n  REMOVED FREIGHT BY FILTER TYPE:")
        print(f"    Local routes (O==D): {local_routes_filtered:,} OD-pairs, {local_routes_tkm:,.2f} tkm ({local_pct:.1f}%)")
        print(f"    Geographic filter: {len(odpairs) - len(filtered_odpairs) - local_routes_filtered:,} OD-pairs, {geographic_filter_tkm:,.2f} tkm ({geo_pct:.1f}%)")
        print(f"    TOTAL REMOVED: {total_removed_tkm:,.2f} tkm ({total_pct:.1f}%)")

        return filtered_geographic_elements, filtered_paths, filtered_odpairs

    def _filter_low_volume_odpairs(self, odpairs, paths):
        """
        Filter out OD-pairs with freight volume below threshold.

        This reduces MandatoryBreaks.yaml size significantly while preserving >99% of freight.
        Analysis shows 1,000 trucks/year threshold removes 54% of OD-pairs but only 0.4% of freight.

        Parameters:
        -----------
        odpairs : list
            List of OD-pair dictionaries
        paths : list
            List of path dictionaries (for calculating tkm)

        Returns:
        --------
        filtered_odpairs : list
            OD-pairs meeting the minimum freight threshold
        """
        if not self.filter_low_volume:
            print("\n[SKIP] Low-volume freight filtering disabled")
            return odpairs

        print(f"\n{'='*80}")
        print("LOW-VOLUME FREIGHT FILTERING")
        print(f"{'='*80}")
        print(f"Threshold: {self.min_freight_threshold:,.0f} trucks/year (first year demand)")

        # Create path lookup for tkm calculation
        path_dict = {p['id']: p for p in paths}

        # Calculate initial statistics
        initial_count = len(odpairs)
        initial_freight = sum(od.get('F', [0])[0] for od in odpairs)
        initial_tkm = sum(
            od.get('F', [0])[0] * path_dict.get(od.get('path_id'), {}).get('length', 0.0)
            for od in odpairs
        )

        # Filter by freight volume
        filtered_odpairs = []
        removed_freight = 0.0
        removed_tkm = 0.0

        for odpair in odpairs:
            demand = odpair.get('F', [0])[0]  # First year demand

            if demand >= self.min_freight_threshold:
                filtered_odpairs.append(odpair)
            else:
                removed_freight += demand
                path_id = odpair.get('path_id')
                if path_id in path_dict:
                    route_length = path_dict[path_id].get('length', 0.0)
                    removed_tkm += demand * route_length

        # Calculate final statistics
        final_count = len(filtered_odpairs)
        final_freight = sum(od.get('F', [0])[0] for od in filtered_odpairs)
        final_tkm = sum(
            od.get('F', [0])[0] * path_dict.get(od.get('path_id'), {}).get('length', 0.0)
            for od in filtered_odpairs
        )

        # Calculate percentages
        removed_count = initial_count - final_count
        removed_count_pct = (removed_count / initial_count * 100) if initial_count > 0 else 0.0
        removed_freight_pct = (removed_freight / initial_freight * 100) if initial_freight > 0 else 0.0
        removed_tkm_pct = (removed_tkm / initial_tkm * 100) if initial_tkm > 0 else 0.0
        retained_freight_pct = (final_freight / initial_freight * 100) if initial_freight > 0 else 0.0
        retained_tkm_pct = (final_tkm / initial_tkm * 100) if initial_tkm > 0 else 0.0

        print(f"\nRESULTS:")
        print(f"  Removed OD-pairs: {removed_count:,} ({removed_count_pct:.1f}%)")
        print(f"  Retained OD-pairs: {final_count:,} ({100-removed_count_pct:.1f}%)")
        print(f"\n  Removed freight: {removed_freight:,.0f} trucks/year ({removed_freight_pct:.2f}%)")
        print(f"  Retained freight: {final_freight:,.0f} trucks/year ({retained_freight_pct:.2f}%)")
        print(f"\n  Removed freight volume: {removed_tkm:,.0f} tkm ({removed_tkm_pct:.2f}%)")
        print(f"  Retained freight volume: {final_tkm:,.0f} tkm ({retained_tkm_pct:.2f}%)")

        if removed_count > 0:
            print(f"\n[SUCCESS] Filtered {removed_count:,} low-volume OD-pairs")
            print(f"          This will significantly reduce MandatoryBreaks.yaml size")
            print(f"          while preserving {retained_freight_pct:.2f}% of freight volume")
        else:
            print(f"\n[INFO] No OD-pairs below threshold of {self.min_freight_threshold:,.0f} trucks/year")

        print(f"{'='*80}\n")

        return filtered_odpairs

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

        # Apply low-volume freight filtering (reduces MandatoryBreaks.yaml size)
        self.odpairs = self._filter_low_volume_odpairs(self.odpairs, self.paths)

        # Create set of retained path IDs for filtering paths
        # (mandatory breaks are generated from paths, so we must filter paths too)
        retained_path_ids = {od['path_id'] for od in self.odpairs}

        # Filter paths to only include those used by retained OD-pairs
        if self.filter_low_volume:
            initial_paths = len(self.paths)
            self.paths = [p for p in self.paths if p['id'] in retained_path_ids]
            removed_paths = initial_paths - len(self.paths)
            removed_paths_pct = (removed_paths / initial_paths * 100) if initial_paths > 0 else 0.0

            print(f"\n[FILTERED] Paths by OD-pair filter:")
            print(f"           Removed: {removed_paths:,} ({removed_paths_pct:.1f}%)")
            print(f"           Retained: {len(self.paths):,} ({100-removed_paths_pct:.1f}%)")

        # Load initial vehicle stock
        # NOTE: Vehicle stock entries don't need filtering - they are node-specific by their 'id' field
        # which corresponds to geographic element node IDs. Keep all entries.
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
                all_mandatory_breaks = yaml.safe_load(f)
            print(f"[OK] Loaded {len(all_mandatory_breaks)} mandatory breaks (before filtering)")

            # Filter mandatory breaks to match filtered paths (from retained OD-pairs)
            if self.filter_low_volume:
                initial_breaks = len(all_mandatory_breaks)
                self.mandatory_breaks = [
                    mb for mb in all_mandatory_breaks
                    if mb.get('path_id') in retained_path_ids
                ]
                removed_breaks = initial_breaks - len(self.mandatory_breaks)
                removed_breaks_pct = (removed_breaks / initial_breaks * 100) if initial_breaks > 0 else 0.0

                print(f"[FILTERED] Mandatory breaks by path filter:")
                print(f"           Removed: {removed_breaks:,} ({removed_breaks_pct:.1f}%)")
                print(f"           Retained: {len(self.mandatory_breaks):,} ({100-removed_breaks_pct:.1f}%)")
            else:
                self.mandatory_breaks = all_mandatory_breaks
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

        # Country code mapping (2-letter ISO to full name for Excel file)
        country_name_map = {
            'AT': 'Austria', 'BE': 'Belgium', 'BG': 'Bulgaria', 'HR': 'Croatia',
            'CY': 'Cyprus', 'CZ': 'Czech Republic', 'DK': 'Denmark', 'EE': 'Estonia',
            'FI': 'Finland', 'FR': 'France', 'DE': 'Germany', 'GR': 'Greece',
            'HU': 'Hungary', 'IE': 'Ireland', 'IT': 'Italy', 'LV': 'Latvia',
            'LT': 'Lithuania', 'LU': 'Luxembourg', 'MT': 'Malta', 'NL': 'Netherlands',
            'NO': 'Norway', 'PL': 'Poland', 'PT': 'Portugal', 'RO': 'Romania',
            'SK': 'Slovakia', 'SI': 'Slovenia', 'ES': 'Spain', 'SE': 'Sweden',
            'CH': 'Switzerland', 'GB': 'United Kingdom', 'UK': 'United Kingdom'
        }

        # Get unique countries from filtered geographic elements (2-letter codes)
        country_codes = set()
        for geo_elem in self.geographic_elements:
            if geo_elem['type'] == 'node':
                country = geo_elem.get('country', '')
                if country:
                    country_codes.add(country)

        # Convert to full names for Excel file lookup
        countries = set(country_name_map.get(code, code) for code in country_codes)
        print(f"  Countries (codes): {sorted(country_codes)}")
        print(f"  Countries (names): {sorted(countries)}")

        # Load connection costs for electricity tax and network costs
        conn_costs_path = self.script_dir / "data" / "electricity data" / "41467_2022_32835_MOESM4_ESM.xlsx"
        if conn_costs_path.exists():
            conn_costs = pd.read_excel(conn_costs_path, sheet_name="Main results", header=1)

            # Filter for CommercialPublic-DC and our countries
            filtered_conn_costs = conn_costs[
                (conn_costs['Option'] == 'CommercialPublic-DC') &
                (conn_costs['Country'].isin(countries))
            ].copy()

            # Calculate electricity tax (average across countries)
            self.av_electricity_tax = filtered_conn_costs["CostElectricityT"].mean()
            print(f"  Average electricity tax: {self.av_electricity_tax:.4f} EUR/kWh")

            # Calculate network energy cost per kW (country-specific)
            # Formula: CostElectricityN * ChargingEnergy / reference_cap
            reference_cap = 50  # kW
            filtered_conn_costs["Network_Energy_Cost"] = (
                filtered_conn_costs["CostElectricityN"] *
                filtered_conn_costs["ChargingEnergy"] /
                reference_cap
            )

            # Create mapping: country code -> network cost (EUR/kW)
            self.network_costs_by_country = {}
            for _, row in filtered_conn_costs.iterrows():
                country_name = row['Country']
                # Find country code from name
                country_code = None
                for code, name in country_name_map.items():
                    if name == country_name:
                        country_code = code
                        break
                if country_code:
                    self.network_costs_by_country[country_code] = float(row["Network_Energy_Cost"])

            print(f"  Network costs loaded for {len(self.network_costs_by_country)} countries")
            if self.network_costs_by_country:
                print(self.network_costs_by_country)
                # Calculate average network cost across all countries
                self.average_network_cost = sum(self.network_costs_by_country.values()) / len(self.network_costs_by_country)
                print(f"  Network cost range: {min(self.network_costs_by_country.values()):.2f} - {max(self.network_costs_by_country.values()):.2f} EUR/kW")
                print(f"  Average network cost: {self.average_network_cost:.2f} EUR/kW")
        else:
            print(f"  [WARN] Connection costs file not found, using default values")
            self.av_electricity_tax = 0.0
            self.network_costs_by_country = {}
            self.average_network_cost = 0.1  # Default fallback value

        # Load GENeSYS-MOD electricity prices
        genesys_path = self.script_dir / "data" / "GENeSYS-MOD_EU-EnVis-2060_v1.2.0_native" / "output_endogenous_fuelcosts.csv"
        if genesys_path.exists():
            excel_data = pd.read_csv(genesys_path)

            # Filter for Power fuel and our countries (GENeSYS-MOD uses 2-letter codes)
            filtered_excel = excel_data[
                (excel_data['Fuel'] == 'Power') &
                (excel_data['Region'].isin(country_codes))
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

    def generate_fuel_params(self, years: List[int] = list(range(2020, 2061))) -> List[Dict]:
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

    def generate_fuel_cost_params(self, years: List[int] = list(range(2020, 2061))) -> List[Dict]:
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

        # Always load electricity price data (needed for both electricity prices and network costs)
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

        # Step 1: Collect all country-specific electricity prices (for reversal logic)
        country_to_prices = {}
        if self.electricity_prices_variable and self.reverse_electricity_prices:
            for geo in self.geographic_elements:
                country_code = geo.get("country", "")
                if country_code and country_code not in country_to_prices:
                    if self.elec_prices_df is not None:
                        extract_elec_prices = self.elec_prices_df[self.elec_prices_df['NUTS_region'] == country_code]
                        if not extract_elec_prices.empty:
                            elec_price_dict = dict(zip(
                                [int(item) for item in extract_elec_prices["year"].to_list()],
                                extract_elec_prices["elec_price_EURperkWh"].to_list()
                            ))
                            all_elec_prices = self._extrapolate_years(elec_price_dict, range(y_init, y_init + Y))
                            electricity_prices = [float(all_elec_prices[y] + self.av_electricity_tax) for y in range(y_init, y_init + Y)]
                            country_to_prices[country_code] = electricity_prices

            # Create reversed mapping: sort countries by average price, then reverse assignment
            if country_to_prices:
                # Sort countries by their average price (ascending)
                sorted_countries = sorted(country_to_prices.keys(),
                                        key=lambda c: sum(country_to_prices[c]) / len(country_to_prices[c]))
                sorted_prices = [country_to_prices[c] for c in sorted_countries]

                # Reverse the price assignment: lowest price country gets highest prices
                reversed_prices = sorted_prices[::-1]
                reversed_country_to_prices = dict(zip(sorted_countries, reversed_prices))

                print(f"  Price reversal active:")
                print(f"    Original avg prices: {[f'{c}: {sum(country_to_prices[c])/len(country_to_prices[c]):.4f}' for c in sorted_countries]}")
                print(f"    Reversed avg prices: {[f'{c}: {sum(reversed_country_to_prices[c])/len(reversed_country_to_prices[c]):.4f}' for c in sorted_countries]}")

                country_to_prices = reversed_country_to_prices

        # Step 2: Create fuel costs for each geographic element (matching notebook: ALL geo elements, not just nodes!)
        for geo in self.geographic_elements:
            # Get country code for this geographic element
            country_code = geo.get("country", "")

            # Calculate location-specific electricity prices
            if self.electricity_prices_variable and self.reverse_electricity_prices and country_code in country_to_prices:
                # Use reversed prices
                electricity_prices = country_to_prices[country_code]
            elif self.elec_prices_df is not None and country_code:
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
                # Use location-specific prices (potentially reversed)
                base_elec_cost_per_kWh = electricity_prices
            else:
                # Use uniform average prices for all locations
                base_elec_cost_per_kWh = av_electricity_prices

            # Multiply electricity prices by 1.5 (base multiplier)
            base_elec_cost_per_kWh = [price * 1.5 for price in base_elec_cost_per_kWh]

            # Create separate FuelCost entries for each fueling infrastructure type
            # Slow charging (id=1): 7.5% markup
            fuel_cost_list.append({
                "id": fc_id,
                "location": geo["id"],
                "fuel": "electricity",
                "fueling_infr_type_id": 1,
                "cost_per_kWh": [price * 1.075 for price in base_elec_cost_per_kWh],
            })
            fc_id += 1

            # Fast charging (id=2): 3% discount
            fuel_cost_list.append({
                "id": fc_id,
                "location": geo["id"],
                "fuel": "electricity",
                "fueling_infr_type_id": 2,
                "cost_per_kWh": [price * 0.97 for price in base_elec_cost_per_kWh],
            })
            fc_id += 1

            # Diesel (id=0): No infrastructure type variation
            fuel_cost_list.append({
                "id": fc_id,
                "location": geo["id"],
                "fuel": "diesel",
                "fueling_infr_type_id": 0,
                "cost_per_kWh": [0.065] * Y,  # Constant diesel price
            })
            fc_id += 1

        pricing_mode = "location-specific" if self.electricity_prices_variable else "uniform (average)"
        print(f"Created {len(fuel_cost_list)} fuel cost entries for {len(self.geographic_elements)} geo elements")
        print(f"Electricity pricing mode: {pricing_mode}")

        return fuel_cost_list

    def generate_fueling_infr_types(self, years: List[int] = list(range(2020, 2061))) -> List[Dict]:
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

        # Use _extrapolate_years for consistent linear interpolation/extrapolation
        costs_extrapolated = self._extrapolate_years(total_install_kW_costs, years)

        # Create cost lists
        cost_per_kW_list = [float(costs_extrapolated[year]) for year in years]
        om_costs_elec_list = [0.03 * float(costs_extrapolated[year]) for year in years]
        om_costs_diesel_list = [0.01 * float(costs_extrapolated[year]) for year in years]

        return [
            {
                'id': 1,
                'fuel': 'electricity',
                'fueling_type': 'slow_charging_station',
                'fueling_power': [100] * len(years),  # kW
                'additional_fueling_time': False,
                'max_occupancy_rate_veh_per_year': 60,  # Shoman et al. (2023)
                'by_route': False,
                'track_detour_time': False,
                'gamma': [0.3] * len(years),
                # 'cost_per_kW': cost_per_kW_list,
                'cost_per_kW': [0.0] * len(years),
                'cost_per_kWh': [1.075] * len(years),

                'cost_per_kWh_network': [0.0] * len(years),
                'om_costs': om_costs_elec_list,  # 3% of investment cost
            },
            {
                'id': 2,
                'fuel': 'electricity',
                'fueling_type': 'fast_charging_station',
                'fueling_power': [1000] * len(years),  # kW
                'additional_fueling_time': False,
                'max_occupancy_rate_veh_per_year': 60,  # Shoman et al. (2023)
                'by_route': False,
                'track_detour_time': False,
                'gamma': [0.3] * len(years),
                # 'cost_per_kW': cost_per_kW_list,
                'cost_per_kW': [0.0] * len(years),
                'cost_per_kWh': [0.97] * len(years),

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
                'cost_per_kW': [1] * len(years),
                'cost_per_kWh_network': [0.0] * len(years),
                'om_costs': om_costs_diesel_list,  # 1% of investment cost
            },
        ]

    def generate_mode_params(self, years: List[int] = list(range(2020, 2061))) -> List[Dict]:
        """
        Generate Mode parameter list with 2 modes:
        - Mode 1: Vehicle-based road costs (with vehicle stock optimization)
        - Mode 2: Rail mode (optional, enabled via self.include_rail_mode)

        Mode 1 (Vehicle-based Road):
        - quantify_by_vehs = True (vehicle stock modeling enabled)
        - costs_per_ukm = 0 (costs determined by vehicle fleet)
        - terminal_costs = 0 (no terminal costs for road)

        Mode 2 (Rail) - OPTIONAL:
        - quantify_by_vehs = False (no vehicle stock modeling)
        - costs_per_ukm = 0.05 EUR/tkm (levelized rail freight cost)
        - terminal_costs = 15.0 EUR/tonne (rail terminal handling costs)
        - Typical rail freight: 30-40 gCO2/tkm
        - Controlled by self.include_rail_mode parameter

        Parameters:
        -----------
        years : list
            Years to include (default: 2020-2060)
        """
        num_years = len(years)

        # Mode 1: Vehicle-based road costs (with vehicle stock optimization)
        modes = [
            {
                'id': 1,
                'name': 'road',
                'quantify_by_vehs': True,  # Vehicle stock modeling enabled
                'costs_per_ukm': [0.0] * num_years,  # Costs determined by vehicle fleet
                'emission_factor': [0] * num_years,
                'infrastructure_expansion_costs': [0.0] * num_years,
                'infrastructure_om_costs': [0.1] * num_years,
                'waiting_time': [0.0] * num_years,
                'terminal_cost_per_tonne': [0.0] * num_years,  # No terminal costs for road
            },
        ]

        # Mode 2: Rail mode (optional)
        if self.include_rail_mode:
            # Rail cost assumptions:
            # - Cost per unit-km: 0.05 EUR/tkm (cheaper than road, but has terminal costs)
            # - Terminal costs: 15.0 EUR/tonne (loading/unloading at rail terminals)
            # - Emission factor: 35 gCO2/tkm (European freight rail average)
            # - Infrastructure expansion: 1,000,000 EUR/km (rail track construction)
            # - Infrastructure O&M: 10,000 EUR/km/year (rail track maintenance)
            modes.append({
                'id': 2,
                'name': 'rail',
                'quantify_by_vehs': False,
                'costs_per_ukm': [0.05] * num_years,  # EUR/tkm (levelized rail freight cost)
                'emission_factor': [35.0] * num_years,  # gCO2/tkm (European rail freight average)
                'infrastructure_expansion_costs': [1_000_000.0] * num_years,  # EUR/km (rail track construction)
                'infrastructure_om_costs': [10_000.0] * num_years,  # EUR/km/year (rail track maintenance)
                'waiting_time': [0] * num_years,  # hours (rail freight terminal access time)
                'terminal_cost_per_tonne': [15.0] * num_years,  # EUR/tonne (rail terminal handling costs)
            })

        return modes

    def generate_vehicletype_params(self) -> List[Dict]:
        """Generate Vehicletype parameter list.
        IMPORTANT: Match notebook exactly - name="long-haul truck"
        Vehicle types must be associated with vehicle-based modes (mode 1).
        """
        return [
            {
                'id': 0,
                'name': 'long-haul truck',
                'mode': 1,  # Mode 1 is the vehicle-based road mode
                'product': 'freight',
            },
        ]

    def generate_tech_vehicle_params(self, num_generations: int = 41+12) -> List[Dict]:
        """
        Generate TechVehicle parameter list matching SM-preprocessing.ipynb notebook EXACTLY.

        Parameters from notebook:
        - occ = 13.6/26
        - L_to_kWh = 9.7 (diesel liters to kWh conversion)
        - Capital costs, maintenance, fuel economy: extrapolated from year-specific dicts
        - Lifetime: 12 years for ALL vehicles
        - AnnualRange: 136750 km for ALL
        - fueling_time: 0.5 hours for ALL

        Parameters:
        -----------
        num_generations : int
            Number of generations to model (default: 53 for G=Y+pre_y=41+12=53)
        """
        # Constants from notebook
        L_to_kWh = 9.7
        occ = (13.6 * (1 - 0.25)) / 26
        vehicle_tax_ICEV = 561
        vehicle_tax_BEV = 5
        subsidy = 0
        added_fact = 1.0
        factors = 1.0

        # Two different time dimensions:
        # 1. Years (optimization horizon): 2020-2060 → 41 years (for capital costs)
        # 2. Generations (including pre-years): 2008-2060 → 53 years (for most parameters)
        years_optimization = list(range(2020, 2061))  # 41 years: 2020-2060
        years_generations = list(range(2008, 2061))   # 53 years: 2008-2060 (includes 12 pre-years)

        # ========================================================================
        # BASE DICTIONARIES FROM NOTEBOOK (with linear interpolation/extrapolation)
        # ========================================================================

        # Capital costs (EUR)
        capital_cost_dict = {
            "ICEV": {
                2020: 105484 * added_fact,
                2025: 109159 * added_fact,
                2030: 115252 * added_fact,
                2040: 115252 * added_fact,
                2050: 115252 * added_fact
            },
            "BEV": {
                2020: (417255 - subsidy) * factors,
                2025: (200006 - subsidy) * factors,
                2030: (145346 - subsidy) * factors,
                2040: (145346 - subsidy) * factors,
                2050: (145346 - subsidy) * factors
            },
        }

        # Maintenance annual costs (EUR/year, includes vehicle tax)
        maintenance_annual_cost_dict = {
            "ICEV": {
                2020: 20471 + vehicle_tax_ICEV,
                2025: 20608 + vehicle_tax_ICEV,
                2030: 20608 + vehicle_tax_ICEV,
                2040: 20608 + vehicle_tax_ICEV,
                2050: 20608 + vehicle_tax_ICEV
            },
            "BEV": {
                2020: 14359 + vehicle_tax_BEV,
                2050: 14359 + vehicle_tax_BEV
            },
        }

        # Fuel economy / specific consumption (kWh/km)
        fuel_economy_dict = {
            "ICEV": {
                2020: 29.86 * L_to_kWh,
                2025: 26.67 * L_to_kWh,
                2030: 23.47 * L_to_kWh,
                2040: 23.47 * L_to_kWh,
                2050: 23.47 * L_to_kWh
            },
            "BEV": {
                2020: 1.60,
                2025: 1.41,
                2030: 1.21,
                2040: 1.21,
                2050: 1.21
            },
        }

        # Maintenance distance costs (EUR/km) - currently zero
        maintenance_distance_dict = {
            "ICEV": {2020: 0, 2035: 0, 2050: 0},
            "BEV": {2020: 0, 2035: 0, 2050: 0},
        }

        # Battery/tank capacity (kWh)
        battery_capacity_dict = {
            "ICEV": {2020: 570 * L_to_kWh, 2035: 570 * L_to_kWh, 2050: 570 * L_to_kWh},
            "BEV": {2020: 1187, 2035: 1187, 2050: 1187},
        }

        # Peak charging/fueling power (kW)
        peak_charging_dict = {
            "ICEV": {2020: 28500, 2035: 28500, 2050: 28500},
            "BEV": {2020: 350, 2035: 900, 2050: 1000},
        }

        # Payload capacity W (tons)
        W_dict = {
            "ICEV": {2020: 26 * occ, 2035: 26 * occ, 2050: 26 * occ},
            "BEV": {2020: 26 * occ * 0.5, 2035: 26 * occ * 0.75, 2050: 26 * occ * 1},
        }

        # Annual mileage (km/year)
        annual_mileage_dict = {
            "ICEV": {2020: 136750, 2035: 136750, 2050: 136750},
            "BEV": {2020: 136750, 2035: 136750, 2050: 136750},
        }

        # ========================================================================
        # INTERPOLATE/EXTRAPOLATE ALL PARAMETERS
        # ========================================================================

        # Capital costs (years dimension: 41 elements for 2020-2060)
        icev_capital = [self._extrapolate_years(capital_cost_dict["ICEV"], years_optimization)[y] for y in years_optimization]
        bev_capital = [self._extrapolate_years(capital_cost_dict["BEV"], years_optimization)[y] for y in years_optimization]

        # Specific consumption (generations dimension: 53 elements for 2008-2060)
        icev_spec_cons = [self._extrapolate_years(fuel_economy_dict["ICEV"], years_generations)[y] for y in years_generations]
        bev_spec_cons = [self._extrapolate_years(fuel_economy_dict["BEV"], years_generations)[y] for y in years_generations]

        # Maintenance annual costs (generations × years matrix: 53 × 41)
        icev_maint_annual_gen = [self._extrapolate_years(maintenance_annual_cost_dict["ICEV"], years_generations)[y] for y in years_generations]
        bev_maint_annual_gen = [self._extrapolate_years(maintenance_annual_cost_dict["BEV"], years_generations)[y] for y in years_generations]

        # Create generation x years matrices (53 rows × 41 columns)
        num_years = len(years_optimization)
        icev_maint_annual = [[icev_maint_annual_gen[g]] * num_years for g in range(num_generations)]
        bev_maint_annual = [[bev_maint_annual_gen[g]] * num_years for g in range(num_generations)]

        # Maintenance distance costs (generations × years matrix: 53 × 41)
        icev_maint_distance_gen = [self._extrapolate_years(maintenance_distance_dict["ICEV"], years_generations)[y] for y in years_generations]
        bev_maint_distance_gen = [self._extrapolate_years(maintenance_distance_dict["BEV"], years_generations)[y] for y in years_generations]
        icev_maint_distance = [[icev_maint_distance_gen[g]] * num_years for g in range(num_generations)]
        bev_maint_distance = [[bev_maint_distance_gen[g]] * num_years for g in range(num_generations)]

        # Tank/battery capacity (generations dimension: 53 elements for 2008-2060)
        icev_tank_capacity = [self._extrapolate_years(battery_capacity_dict["ICEV"], years_generations)[y] for y in years_generations]
        bev_tank_capacity = [self._extrapolate_years(battery_capacity_dict["BEV"], years_generations)[y] for y in years_generations]

        # Peak fueling/charging (generations dimension: 53 elements for 2008-2060)
        icev_peak_fueling = [self._extrapolate_years(peak_charging_dict["ICEV"], years_generations)[y] for y in years_generations]
        bev_peak_fueling = [self._extrapolate_years(peak_charging_dict["BEV"], years_generations)[y] for y in years_generations]

        # Payload capacity W (generations dimension: 53 elements for 2008-2060)
        icev_W = [self._extrapolate_years(W_dict["ICEV"], years_generations)[y] for y in years_generations]
        bev_W = [self._extrapolate_years(W_dict["BEV"], years_generations)[y] for y in years_generations]

        # Annual range (generations dimension: 53 elements for 2008-2060)
        icev_annual_range = [self._extrapolate_years(annual_mileage_dict["ICEV"], years_generations)[y] for y in years_generations]
        bev_annual_range = [self._extrapolate_years(annual_mileage_dict["BEV"], years_generations)[y] for y in years_generations]

        return [
            {
                'id': 0,
                'name': 'ICEV',
                'technology': 0,
                'vehicle_type': 'long-haul truck',
                'capital_cost': icev_capital,
                'maintenance_cost_annual': icev_maint_annual,
                'maintenance_cost_distance': icev_maint_distance,
                'W': icev_W,
                'spec_cons': icev_spec_cons,
                'Lifetime': [12] * num_generations,
                'AnnualRange': icev_annual_range,
                'products': ['freight'],
                'tank_capacity': icev_tank_capacity,
                'peak_fueling': icev_peak_fueling,
                'fueling_time': [0.5] * num_generations,
            },
            {
                'id': 1,
                'name': 'BEV',
                'technology': 1,
                'vehicle_type': 'long-haul truck',
                'capital_cost': bev_capital,
                'maintenance_cost_annual': bev_maint_annual,
                'maintenance_cost_distance': bev_maint_distance,
                'W': bev_W,
                'spec_cons': bev_spec_cons,
                'Lifetime': [12] * num_generations,
                'AnnualRange': bev_annual_range,
                'products': ['freight'],
                'tank_capacity': bev_tank_capacity,
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
                                          years: List[int] = list(range(2020, 2061))) -> List[Dict]:
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
                'VoT': 30,  # NOTEBOOK VALUE: 0.0 (NOT 30.0!)
                'monetary_budget_operational': 0.0,
                'monetary_budget_operational_lb': 0.0,
                'monetary_budget_operational_ub': 0.0,
                'monetary_budget_purchase': 0.0,
                'monetary_budget_purchase_lb': 0.0,
                'monetary_budget_purchase_ub': 0.0,
                'monetary_budget_purchase_time_horizon': 0,
            },
        ]

    def generate_regiontype_params(self, years: List[int] = list(range(2020, 2061))) -> List[Dict]:
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

    def generate_max_mode_share_params(self, years: List[int] = list(range(2020, 2061))) -> List[Dict]:
        """
        Generate MaxModeShare parameter list to cap rail freight at 30% of total transport.

        Only generates constraints if rail mode is included.
        Applies constraint to all modeled years.

        Returns:
        --------
        list of dict
            Each dict contains: id, year, mode (mode ID), share (maximum fraction)
        """
        if not self.include_rail_mode:
            # No rail mode, no need for max share constraints
            return []

        # Create one constraint per modeled year (respecting time_step)
        time_step = 4  # From Model parameters
        y_init = years[0]
        y_end = years[-1]
        modeled_years = list(range(y_init, y_end + 1, time_step))

        constraints = []
        for idx, year in enumerate(modeled_years):
            constraints.append({
                'id': idx,
                'year': year,
                'mode': 2,  # Rail mode ID
                'share': 0.30,  # Maximum 30% of total freight
            })

        return constraints

    def generate_model_params(self) -> Dict:
        """Generate Model parameter dictionary matching SM-preprocessing.ipynb notebook EXACTLY."""
        return {
            'Y': 41,  # Number of years in optimization horizon
            'y_init': 2020,  # Initial year
            'pre_y': 12,  # Years before initial year to consider (prey_y in notebook)
            'time_step': 4,  # Temporal resolution (1=annual, 2=biennial, 4=4-year periods, 5=quinquennial, etc.)
            'gamma': 0.0001,  # NOTEBOOK VALUE: 0.0001 (NOT 0.05!)
            'discount_rate': 0.05,  # Discount rate (5%)
            'budget_penalty_plus': 10000,  # NOTEBOOK VALUE: 10000 (NOT 1000000!)
            'budget_penalty_minus': 10000,  # NOTEBOOK VALUE: 10000 (NOT 1000000!)
            'budget_penalty_yearly_plus': 10000000,  # NOTEBOOK VALUE: 10000000 (NOT 100000!)
            'budget_penalty_yearly_minus': 10000000,  # NOTEBOOK VALUE: 10000000 (NOT 100000!)
            'investment_period': 4,  # NOTEBOOK VALUE: 5 years (NOT 1!)
            'pre_age_sell': False,  # NOTEBOOK VALUE: False (NOT True!)
            'alpha_f': 0.01,  # Mode shift rate limit (fraction of total flow) - for constraint_mode_shift
            'beta_f': 0.01,  # Mode shift rate limit (fraction of previous mode flow) - for constraint_mode_shift
            'alpha_h': 0.1,  # Technology shift rate limit (fraction of total stock) - for constraint_vehicle_stock_shift
            'beta_h': 0.1,  # Technology shift rate limit (fraction of previous tech stock) - for constraint_vehicle_stock_shift
        }

    def generate_network_connection_costs(self, years: List[int] = list(range(2020, 2061))) -> List[Dict]:
        """
        Generate NetworkConnectionCosts parameter list.

        Uses self.network_costs_variable to toggle between location-specific
        and uniform (average) network costs across all locations.

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
                # Use either location-specific or average network cost based on flag
                if self.network_costs_variable:
                    # Location-specific: get country-specific network cost
                    country_code = geo_elem.get('country', '')
                    network_cost = self.network_costs_by_country.get(country_code, self.average_network_cost)
                else:
                    # Uniform: use average network cost across all countries
                    network_cost = self.average_network_cost

                network_costs_list.append({
                    'id': nc_id,
                    'location': geo_elem['id'],  # Use ID (not name) to match GeographicElement!
                    'network_cost_per_kW': [network_cost] * num_years,  # EUR/kW, constant over time
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

        # FIX: Reconstruct cumulative_distance for paths with insufficient node detail
        # This handles aggregated paths where sequence is simplified but length is preserved

        # Check if path needs synthetic nodes:
        # 1. Single node paths (len <= 1)
        # 2. Multi-node paths where max gap exceeds one break interval (360km)
        needs_synthetic_nodes = False
        break_interval_km = 4.5 * speed  # 360 km at 80 km/h

        if len(cumulative_distance) <= 1 and total_length > 0:
            needs_synthetic_nodes = True
        elif len(cumulative_distance) >= 2:
            # Check maximum gap between consecutive nodes
            max_gap = max(cumulative_distance[i] - cumulative_distance[i-1]
                         for i in range(1, len(cumulative_distance)))
            if max_gap > break_interval_km:
                needs_synthetic_nodes = True

        if needs_synthetic_nodes and total_length > 0:
            # Path has insufficient detail but positive length
            # Generate synthetic distance points at break intervals for proper break placement
            # NOTE: We only use these for break calculation, NOT saved to path sequence!
            # Julia doesn't need intermediate nodes - breaks just reference destination geo_id
            synthetic_cumulative = [0.0]
            dist = 0.0

            # Add points at each break interval
            while dist + break_interval_km < total_length:
                dist += break_interval_km
                synthetic_cumulative.append(dist)

            # Add final destination
            synthetic_cumulative.append(total_length)

            # Update cumulative_distance for break calculation only
            cumulative_distance = synthetic_cumulative

            # Keep original 2-node sequence - don't add synthetic nodes!
            # Breaks will reference destination geo_id, which already exists in sequence

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
                    # Map synthetic index to actual sequence (for 2-node paths, all breaks map to destination)
                    seq_idx = 0 if i == 0 else min(i, len(sequence) - 1)
                    node = sequence[seq_idx]
                    latest_geo_id = node['id'] if isinstance(node, dict) else node
                    actual_cum_distance = cum_dist
                else:
                    break

            # PRACTICAL ADJUSTMENT: If next node is only slightly over limit, use it instead
            # This handles cases where stopping earlier would be impractical
            # Example: If limit is 4.5h, prev node is 4.3h, next node is 4.6h (only 0.1h over)
            #          -> More practical to stop at 4.6h than 4.3h
            # Tolerance is dynamic: (1/3) of the gap from the last valid node to the limit
            # Rationale: If last valid node is far from limit, allow more flexibility
            if latest_node_idx is not None and latest_node_idx < len(cumulative_distance) - 1:
                next_node_idx = latest_node_idx + 1
                next_cum_dist = cumulative_distance[next_node_idx]
                next_time = next_cum_dist / speed

                # Calculate current node time
                current_time = actual_cum_distance / speed

                # Dynamic tolerance: allow up to 1/3 of the gap from current node to target
                gap_to_limit = target_time - current_time
                tolerance_hours = (1/3) * gap_to_limit if gap_to_limit > 0 else 0

                # If next node is within tolerance, use it instead
                if next_time <= target_time + tolerance_hours:
                    latest_node_idx = next_node_idx
                    # Map synthetic index to actual sequence
                    seq_idx = 0 if next_node_idx == 0 else min(next_node_idx, len(sequence) - 1)
                    node = sequence[seq_idx]
                    latest_geo_id = node['id'] if isinstance(node, dict) else node
                    actual_cum_distance = next_cum_dist

            # Safety fallback
            if latest_node_idx is None and len(sequence) > 0:
                latest_node_idx = len(cumulative_distance) - 1
                # Map to destination (last node in actual sequence)
                seq_idx = len(sequence) - 1
                node = sequence[seq_idx]
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
            "TechVehicle": self.generate_tech_vehicle_params(num_generations=41 + 12),
            "Product": self.generate_product_params(),
            "FinancialStatus": self.generate_financial_status_params(),
            "Regiontype": self.generate_regiontype_params(),
            "Speed": self.generate_speed_params(),
            "Model": self.generate_model_params(),
            "NetworkConnectionCosts": self.generate_network_connection_costs(),
            "InitialModeInfr": self.generate_initial_mode_infr(),
            "InitialFuelInfr": self.generate_initial_fuel_infr(),
            "SpatialFlexibilityEdges": self.generate_spatial_flexibility_edges(),
            "MaxModeShare": self.generate_max_mode_share_params(),
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
        nuts3_data_dir = "input_data/nuts_2_360_complete_test_time_step_2"  # TEST CASE: 100 OD-pairs >= 360km
        # nuts3_data_dir = "input_data/sm_nuts3_complete"  # FULL CASE: All OD-pairs

    # Case name is ALWAYS auto-generated with timestamp
    case_name = None

    # Parse electricity pricing mode
    electricity_prices_variable = True  # Default: location-specific (variable)

    if len(sys.argv) > 2:
        elec_price_arg = sys.argv[2].lower()
        if elec_price_arg in ('true', '1', 'yes', 'variable'):
            electricity_prices_variable = True
        elif elec_price_arg in ('false', '0', 'no', 'uniform', 'average'):
            electricity_prices_variable = False
        else:
            print(f"[ERROR] Invalid electricity pricing mode: '{sys.argv[2]}'")
            print("        Valid values: 'true'/'variable' (location-specific) or 'false'/'uniform' (average)")
            sys.exit(1)

    # Parse network costs mode
    network_costs_variable = True  # Default: location-specific (variable)

    if len(sys.argv) > 3:
        network_cost_arg = sys.argv[3].lower()
        if network_cost_arg in ('true', '1', 'yes', 'variable'):
            network_costs_variable = True
        elif network_cost_arg in ('false', '0', 'no', 'uniform', 'average'):
            network_costs_variable = False
        else:
            print(f"[ERROR] Invalid network cost mode: '{sys.argv[3]}'")
            print("        Valid values: 'true'/'variable' (location-specific) or 'false'/'uniform' (average)")
            sys.exit(1)

    # Parse electricity price reversal option (optional 4th argument)
    reverse_electricity_prices = False  # Default: normal assignment

    if len(sys.argv) > 4:
        reverse_arg = sys.argv[4].lower()
        if reverse_arg in ('true', '1', 'yes', 'reverse', 'reversed'):
            reverse_electricity_prices = True
        elif reverse_arg in ('false', '0', 'no', 'normal'):
            reverse_electricity_prices = False
        else:
            print(f"[ERROR] Invalid electricity price reversal mode: '{sys.argv[4]}'")
            print("        Valid values: 'true'/'reverse' (reversed assignment) or 'false'/'normal' (normal)")
            sys.exit(1)

    # Parse rail mode option (optional 5th argument)
    include_rail_mode = False  # Default: road only

    if len(sys.argv) > 5:
        rail_arg = sys.argv[5].lower()
        if rail_arg in ('true', '1', 'yes', 'rail', 'include'):
            include_rail_mode = True
        elif rail_arg in ('false', '0', 'no', 'road', 'exclude'):
            include_rail_mode = False
        else:
            print(f"[ERROR] Invalid rail mode option: '{sys.argv[5]}'")
            print("        Valid values: 'true'/'rail'/'include' (include rail) or 'false'/'road'/'exclude' (road only)")
            sys.exit(1)

    # Parse low-volume freight filter option (optional 6th argument)
    filter_low_volume = True  # Default: enabled (filters out low-volume OD-pairs)

    if len(sys.argv) > 6:
        filter_arg = sys.argv[6].lower()
        if filter_arg in ('true', '1', 'yes', 'filter', 'enable'):
            filter_low_volume = True
        elif filter_arg in ('false', '0', 'no', 'nofilter', 'disable'):
            filter_low_volume = False
        else:
            print(f"[ERROR] Invalid low-volume filter option: '{sys.argv[6]}'")
            print("        Valid values: 'true'/'filter'/'enable' (filter low volumes) or 'false'/'nofilter'/'disable' (keep all)")
            sys.exit(1)

    # Parse minimum freight threshold (optional 7th argument)
    min_freight_threshold = 1000.0  # Default: 1,000 trucks/year

    if len(sys.argv) > 7:
        try:
            min_freight_threshold = float(sys.argv[7])
            if min_freight_threshold < 0:
                raise ValueError("Threshold must be non-negative")
        except ValueError as e:
            print(f"[ERROR] Invalid freight threshold: '{sys.argv[7]}'")
            print(f"        Must be a non-negative number (e.g., 1000, 2000, 5000)")
            print(f"        Error: {e}")
            sys.exit(1)

    # Display configuration
    print("\n" + "="*80)
    print("SM PARAMETER GENERATOR - CONFIGURATION")
    print("="*80)
    print(f"Input directory:      {nuts3_data_dir}")
    print(f"Case name:            Auto-generated with timestamp")
    elec_mode = 'Location-specific (variable)' if electricity_prices_variable else 'Uniform average (all locations)'
    network_mode = 'Location-specific (variable)' if network_costs_variable else 'Uniform average (all locations)'
    print(f"Electricity pricing:  {elec_mode}")
    print(f"Network costs:        {network_mode}")
    if reverse_electricity_prices:
        print(f"Price reversal:       ENABLED (highest costs assigned to lowest price countries)")
    mode_config = 'Road + Rail (multimodal)' if include_rail_mode else 'Road only'
    print(f"Transport modes:      {mode_config}")
    if filter_low_volume:
        print(f"Low-volume filter:    ENABLED (threshold: {min_freight_threshold:,.0f} trucks/year)")
        print(f"                      Reduces MandatoryBreaks.yaml size while keeping >99% of freight")
    else:
        print(f"Low-volume filter:    DISABLED (all OD-pairs included)")
    print("="*80 + "\n")

    # Run preprocessing
    preprocessor = SMParameterGenerator(
        nuts3_data_dir=nuts3_data_dir,
        case_name=case_name,
        electricity_prices_variable=electricity_prices_variable,
        network_costs_variable=network_costs_variable,
        reverse_electricity_prices=reverse_electricity_prices,
        include_rail_mode=include_rail_mode,
        filter_low_volume=filter_low_volume,
        min_freight_threshold=min_freight_threshold
    )

    preprocessor.run()

    print("\n[INFO] Case successfully generated with timestamp-based name!")
    print("\nUsage:")
    print("  python SM_preprocessing.py [input_dir] [elec_mode] [network_mode] [price_reversal] [rail_mode] [filter_mode] [threshold]")
    print("\nArguments:")
    print("  input_dir       : Path to input data directory (default: nuts_2_360_complete_test_time_step_2)")
    print("  elec_mode       : Electricity pricing mode (default: variable)")
    print("                    - 'true', 'variable', 'yes', '1' → Location-specific (by country)")
    print("                    - 'false', 'uniform', 'average', 'no', '0' → Uniform average")
    print("  network_mode    : Network connection cost mode (default: variable)")
    print("                    - 'true', 'variable', 'yes', '1' → Location-specific (by country)")
    print("                    - 'false', 'uniYform', 'average', 'no', '0' → Uniform average")
    print("  price_reversal  : Reverse electricity price assignment (default: false)")
    print("                    - 'true', 'reverse', 'yes', '1' → Highest costs to lowest price countries")
    print("                    - 'false', 'normal', 'no', '0' → Normal assignment")
    print("  rail_mode       : Include rail as transport mode (default: false)")
    print("                    - 'true', 'rail', 'include', 'yes', '1' → Include rail mode (multimodal)")
    print("                    - 'false', 'road', 'exclude', 'no', '0' → Road only (unimodal)")
    print("  filter_mode     : Low-volume freight filtering (default: true)")
    print("                    - 'true', 'filter', 'enable', 'yes', '1' → Filter low volumes")
    print("                    - 'false', 'nofilter', 'disable', 'no', '0' → Keep all OD-pairs")
    print("                    NOTE: Filtering removes ~54% of OD-pairs but only ~0.4% of freight (tkm)")
    print("                          Significantly reduces MandatoryBreaks.yaml size")
    print("  threshold       : Minimum freight threshold in trucks/year (default: 1000)")
    print("                    Only applies when filter_mode is enabled")
    print("                    Suggested values: 1000 (removes 54% OD-pairs, 0.4% tkm)")
    print("                                      2000 (removes 64% OD-pairs, 0.9% tkm)")
    print("                                      5000 (removes 75% OD-pairs, 2.0% tkm)")
    print("\nExamples:")
    print("  python SM_preprocessing.py")
    print("    → Default: variable prices, road only, WITH LOW-VOLUME FILTER (1000 trucks/year)")
    print("    → Case name: auto-generated (e.g., case_20251104_143015)")
    print()
    print("  python SM_preprocessing.py input_data/fixed_nuts_2")
    print("    → Use fixed_nuts_2 with defaults (variable, road only, filtering enabled)")
    print()
    print("  python SM_preprocessing.py input_data/fixed_nuts_2 variable variable false road true 1000")
    print("    → Explicit: variable prices, road only, with 1000 trucks/year filter")
    print("    → Reduces dataset size while keeping >99% of freight volume")
    print()
    print("  python SM_preprocessing.py input_data/fixed_nuts_2 variable variable false road false")
    print("    → NO FILTERING: Keep all OD-pairs regardless of volume")
    print("    → Larger MandatoryBreaks.yaml but complete freight representation")
    print()
    print("  python SM_preprocessing.py input_data/fixed_nuts_2 variable variable false road true 5000")
    print("    → More aggressive filtering: 5000 trucks/year threshold")
    print("    → Removes 75% of OD-pairs but keeps 98% of freight volume")
    print()
    print("  python SM_preprocessing.py input_data/fixed_nuts_2 variable variable false rail")
    print("    → Variable electricity/network, WITH RAIL MODE, default filtering")
    print("    → Full multimodal optimization with low-volume filtering enabled")


if __name__ == "__main__":
    main()
