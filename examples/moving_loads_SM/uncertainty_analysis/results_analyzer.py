"""
Results Analyzer for Uncertainty Analysis
==========================================

Collects, parses, and analyzes results from multiple uncertainty scenarios.
Generates summary statistics, sensitivity analysis, and robustness metrics.

Key outputs:
- Technology adoption trajectories across scenarios
- Infrastructure deployment variability
- Objective value sensitivity to parameters
- Robust vs. sensitive decisions identification
"""

import json
import yaml
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import warnings


@dataclass
class ScenarioResults:
    """Results from a single uncertainty scenario."""
    scenario_id: int
    parameters: Dict[str, float]
    objective_value: float
    termination_status: str
    runtime_seconds: float

    # Key output metrics (populated from YAML results)
    total_bev_vehicles: Dict[int, float] = field(default_factory=dict)  # year -> count
    total_charging_capacity: Dict[int, float] = field(default_factory=dict)  # year -> kW
    total_electricity_consumption: Dict[int, float] = field(default_factory=dict)  # year -> kWh
    rail_modal_share: Dict[int, float] = field(default_factory=dict)  # year -> fraction

    # Cost components
    total_vehicle_cost: float = 0.0
    total_fuel_cost: float = 0.0
    total_infrastructure_cost: float = 0.0


class ResultsAnalyzer:
    """
    Analyzes results from multiple uncertainty scenarios.

    Provides:
    - Summary statistics across scenarios
    - Sensitivity analysis (how outputs vary with inputs)
    - Robustness metrics (which decisions are stable)
    - Comparison with base case
    """

    def __init__(self, results_base_path: Path, scenarios_metadata_path: Optional[Path] = None):
        """
        Initialize the analyzer.

        Parameters:
        -----------
        results_base_path : Path
            Path containing scenario result folders (scenario_000, scenario_001, ...)
        scenarios_metadata_path : Path, optional
            Path to scenarios JSON file with parameter values
        """
        self.results_base_path = Path(results_base_path)
        self.scenarios_metadata_path = scenarios_metadata_path
        self.scenario_results: List[ScenarioResults] = []

    def load_all_results(self) -> int:
        """
        Load results from all scenario folders.

        Returns the number of successfully loaded scenarios.
        """
        scenario_folders = sorted(self.results_base_path.glob("scenario_*"))

        if not scenario_folders:
            print(f"No scenario folders found in {self.results_base_path}")
            return 0

        # Load scenario parameters if available
        scenario_params = {}
        if self.scenarios_metadata_path and self.scenarios_metadata_path.exists():
            with open(self.scenarios_metadata_path, 'r') as f:
                scenarios_data = json.load(f)
                for s in scenarios_data.get('scenarios', []):
                    scenario_params[s['scenario_id']] = s

        loaded_count = 0
        for folder in scenario_folders:
            try:
                result = self._load_scenario_result(folder, scenario_params)
                if result:
                    self.scenario_results.append(result)
                    loaded_count += 1
            except Exception as e:
                print(f"  [WARN] Failed to load {folder.name}: {e}")

        print(f"Loaded {loaded_count}/{len(scenario_folders)} scenario results")
        return loaded_count

    def _load_scenario_result(
        self,
        folder: Path,
        scenario_params: Dict
    ) -> Optional[ScenarioResults]:
        """Load results from a single scenario folder."""
        # Extract scenario ID from folder name
        try:
            scenario_id = int(folder.name.split('_')[1])
        except (IndexError, ValueError):
            scenario_id = -1

        # Load scenario metadata if exists
        metadata_path = folder / "scenario_metadata.yaml"
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = yaml.safe_load(f)
                params = metadata.get('parameters', {})
        elif scenario_id in scenario_params:
            params = scenario_params[scenario_id]
        else:
            params = {}

        # Load batch summary for this scenario
        batch_summary_path = self.results_base_path / "batch_summary.json"
        objective_value = 0.0
        termination_status = "UNKNOWN"
        runtime_seconds = 0.0

        if batch_summary_path.exists():
            with open(batch_summary_path, 'r') as f:
                summary = json.load(f)
                if folder.name in summary:
                    s = summary[folder.name]
                    objective_value = s.get('objective_value', 0.0)
                    termination_status = s.get('termination_status', 'UNKNOWN')
                    runtime_seconds = s.get('runtime_seconds', 0.0)

        result = ScenarioResults(
            scenario_id=scenario_id,
            parameters=params,
            objective_value=objective_value,
            termination_status=termination_status,
            runtime_seconds=runtime_seconds
        )

        # Load detailed results from YAML files if available
        self._load_detailed_results(folder, result)

        return result

    def _load_detailed_results(self, folder: Path, result: ScenarioResults):
        """Load detailed results from scenario's output YAML files."""
        # Look for results in typical output locations
        # This depends on how save_results() structures the output

        # Try to find vehicle technology results
        h_file = folder / "h.yaml"
        if h_file.exists():
            self._parse_vehicle_results(h_file, result)

        # Try to find infrastructure results
        q_file = folder / "q_fuel_infr_plus.yaml"
        if q_file.exists():
            self._parse_infrastructure_results(q_file, result)

        # Try to find energy consumption results
        s_file = folder / "s.yaml"
        if s_file.exists():
            self._parse_energy_results(s_file, result)

    def _parse_vehicle_results(self, filepath: Path, result: ScenarioResults):
        """Parse vehicle stock results (h variable)."""
        try:
            with open(filepath, 'r') as f:
                data = yaml.safe_load(f)

            if data is None:
                return

            # Aggregate BEV vehicles by year
            for entry in data:
                year = entry.get('year', entry.get('y'))
                tech = entry.get('technology', entry.get('tech_id'))
                value = entry.get('value', 0)

                # Assuming technology 0 = BEV
                if tech == 0 and year is not None:
                    if year not in result.total_bev_vehicles:
                        result.total_bev_vehicles[year] = 0
                    result.total_bev_vehicles[year] += value
        except Exception as e:
            pass  # Silently skip if parsing fails

    def _parse_infrastructure_results(self, filepath: Path, result: ScenarioResults):
        """Parse infrastructure deployment results."""
        try:
            with open(filepath, 'r') as f:
                data = yaml.safe_load(f)

            if data is None:
                return

            # Aggregate charging capacity by year
            for entry in data:
                year = entry.get('year', entry.get('y'))
                value = entry.get('value', 0)

                if year is not None:
                    if year not in result.total_charging_capacity:
                        result.total_charging_capacity[year] = 0
                    result.total_charging_capacity[year] += value
        except Exception as e:
            pass

    def _parse_energy_results(self, filepath: Path, result: ScenarioResults):
        """Parse energy consumption results (s variable)."""
        try:
            with open(filepath, 'r') as f:
                data = yaml.safe_load(f)

            if data is None:
                return

            # Aggregate electricity consumption by year
            for entry in data:
                year = entry.get('year', entry.get('y'))
                value = entry.get('value', 0)

                if year is not None:
                    if year not in result.total_electricity_consumption:
                        result.total_electricity_consumption[year] = 0
                    result.total_electricity_consumption[year] += value
        except Exception as e:
            pass

    def get_summary_statistics(self) -> pd.DataFrame:
        """
        Generate summary statistics across all scenarios.

        Returns DataFrame with mean, std, min, max, percentiles for key metrics.
        """
        if not self.scenario_results:
            return pd.DataFrame()

        # Extract key metrics
        data = {
            'scenario_id': [],
            'objective_value': [],
            'electricity_price_mult': [],
            'carbon_price': [],
            'charging_markup': [],
            'tech_cost_mult': [],
            'runtime_seconds': []
        }

        for r in self.scenario_results:
            data['scenario_id'].append(r.scenario_id)
            data['objective_value'].append(r.objective_value)
            data['electricity_price_mult'].append(
                r.parameters.get('electricity_price_multiplier', 1.0)
            )
            data['carbon_price'].append(r.parameters.get('carbon_price', 0.0))
            data['charging_markup'].append(r.parameters.get('charging_markup', 0.0))
            data['tech_cost_mult'].append(
                r.parameters.get('tech_cost_multiplier', 1.0)
            )
            data['runtime_seconds'].append(r.runtime_seconds)

        df = pd.DataFrame(data)

        # Add summary statistics
        summary = df.describe(percentiles=[0.05, 0.25, 0.5, 0.75, 0.95])

        return summary

    def compute_sensitivity_indices(self) -> pd.DataFrame:
        """
        Compute sensitivity of objective value to each parameter.

        Uses simple correlation-based sensitivity analysis.
        For more sophisticated analysis (Sobol indices), use SALib.
        """
        if len(self.scenario_results) < 3:
            print("Need at least 3 scenarios for sensitivity analysis")
            return pd.DataFrame()

        # Build data arrays
        params = ['electricity_price_multiplier', 'carbon_price',
                  'charging_markup', 'tech_cost_multiplier']

        X = np.zeros((len(self.scenario_results), len(params)))
        Y = np.zeros(len(self.scenario_results))

        for i, r in enumerate(self.scenario_results):
            for j, p in enumerate(params):
                X[i, j] = r.parameters.get(p, 1.0 if 'mult' in p else 0.0)
            Y[i] = r.objective_value

        # Compute correlations
        correlations = {}
        for j, p in enumerate(params):
            if np.std(X[:, j]) > 0 and np.std(Y) > 0:
                corr = np.corrcoef(X[:, j], Y)[0, 1]
                correlations[p] = {
                    'correlation': corr,
                    'correlation_squared': corr ** 2,
                    'rank': 0  # Will be filled in
                }
            else:
                correlations[p] = {
                    'correlation': 0.0,
                    'correlation_squared': 0.0,
                    'rank': 0
                }

        # Rank by absolute correlation
        sorted_params = sorted(
            correlations.keys(),
            key=lambda x: abs(correlations[x]['correlation']),
            reverse=True
        )
        for rank, p in enumerate(sorted_params, 1):
            correlations[p]['rank'] = rank

        df = pd.DataFrame(correlations).T
        df.index.name = 'parameter'

        return df

    def identify_robust_decisions(self, year: int = 2040) -> Dict[str, Dict]:
        """
        Identify which decisions are robust (stable) across scenarios.

        A decision is robust if its coefficient of variation (CV) is low.

        Returns dict with metrics and robustness classification.
        """
        if not self.scenario_results:
            return {}

        # Collect values for key decisions at specified year
        bev_vehicles = []
        charging_capacity = []
        electricity_consumption = []

        for r in self.scenario_results:
            if year in r.total_bev_vehicles:
                bev_vehicles.append(r.total_bev_vehicles[year])
            if year in r.total_charging_capacity:
                charging_capacity.append(r.total_charging_capacity[year])
            if year in r.total_electricity_consumption:
                electricity_consumption.append(r.total_electricity_consumption[year])

        def compute_robustness(values: List[float], name: str) -> Dict:
            if len(values) < 2:
                return {'name': name, 'n_scenarios': len(values), 'robust': None}

            arr = np.array(values)
            mean = np.mean(arr)
            std = np.std(arr)
            cv = std / mean if mean > 0 else float('inf')

            # Classify robustness (CV < 0.1 = robust, 0.1-0.3 = moderate, >0.3 = sensitive)
            if cv < 0.1:
                classification = 'ROBUST'
            elif cv < 0.3:
                classification = 'MODERATE'
            else:
                classification = 'SENSITIVE'

            return {
                'name': name,
                'n_scenarios': len(values),
                'mean': mean,
                'std': std,
                'cv': cv,
                'min': np.min(arr),
                'max': np.max(arr),
                'p5': np.percentile(arr, 5),
                'p95': np.percentile(arr, 95),
                'classification': classification
            }

        return {
            'bev_vehicles': compute_robustness(bev_vehicles, 'BEV Vehicles'),
            'charging_capacity': compute_robustness(charging_capacity, 'Charging Capacity (kW)'),
            'electricity_consumption': compute_robustness(
                electricity_consumption, 'Electricity Consumption (kWh)'
            )
        }

    def generate_report(self, output_path: Path) -> Path:
        """
        Generate a comprehensive analysis report.

        Saves summary statistics, sensitivity analysis, and robustness metrics.
        """
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)

        report = {
            'n_scenarios': len(self.scenario_results),
            'successful_scenarios': sum(
                1 for r in self.scenario_results
                if r.termination_status in ['OPTIMAL', 'TIME_LIMIT']
            ),
            'failed_scenarios': sum(
                1 for r in self.scenario_results
                if r.termination_status not in ['OPTIMAL', 'TIME_LIMIT', 'UNKNOWN']
            )
        }

        # Summary statistics
        summary_df = self.get_summary_statistics()
        if not summary_df.empty:
            summary_df.to_csv(output_path / 'summary_statistics.csv')
            report['summary_statistics_file'] = 'summary_statistics.csv'

        # Sensitivity analysis
        sensitivity_df = self.compute_sensitivity_indices()
        if not sensitivity_df.empty:
            sensitivity_df.to_csv(output_path / 'sensitivity_analysis.csv')
            report['sensitivity_analysis_file'] = 'sensitivity_analysis.csv'

            # Add top sensitivities to report
            report['most_sensitive_parameter'] = sensitivity_df['correlation'].abs().idxmax()
            report['sensitivity_ranking'] = sensitivity_df['rank'].to_dict()

        # Robustness analysis for key years
        for year in [2030, 2040, 2050]:
            robustness = self.identify_robust_decisions(year)
            if robustness:
                report[f'robustness_{year}'] = robustness

        # Objective value statistics
        obj_values = [r.objective_value for r in self.scenario_results if r.objective_value > 0]
        if obj_values:
            report['objective_value'] = {
                'mean': float(np.mean(obj_values)),
                'std': float(np.std(obj_values)),
                'min': float(np.min(obj_values)),
                'max': float(np.max(obj_values)),
                'cv': float(np.std(obj_values) / np.mean(obj_values)) if np.mean(obj_values) > 0 else 0
            }

        # Save report
        report_path = output_path / 'uncertainty_analysis_report.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        print(f"\n=== Uncertainty Analysis Report ===")
        print(f"Scenarios analyzed: {report['n_scenarios']}")
        print(f"Successful: {report['successful_scenarios']}")
        print(f"Failed: {report['failed_scenarios']}")

        if 'most_sensitive_parameter' in report:
            print(f"\nMost sensitive parameter: {report['most_sensitive_parameter']}")

        if 'objective_value' in report:
            ov = report['objective_value']
            print(f"\nObjective value statistics:")
            print(f"  Mean: {ov['mean']:.2e}")
            print(f"  Std:  {ov['std']:.2e}")
            print(f"  CV:   {ov['cv']:.2%}")

        print(f"\nReport saved to: {report_path}")
        return report_path

    def export_results_table(self, output_path: Path) -> Path:
        """Export all scenario results as a single CSV table."""
        output_path = Path(output_path)

        rows = []
        for r in self.scenario_results:
            row = {
                'scenario_id': r.scenario_id,
                'objective_value': r.objective_value,
                'termination_status': r.termination_status,
                'runtime_seconds': r.runtime_seconds,
                'electricity_price_multiplier': r.parameters.get('electricity_price_multiplier', 1.0),
                'carbon_price': r.parameters.get('carbon_price', 0.0),
                'charging_markup': r.parameters.get('charging_markup', 0.0),
                'tech_cost_multiplier': r.parameters.get('tech_cost_multiplier', 1.0)
            }

            # Add yearly metrics
            for year in sorted(set(r.total_bev_vehicles.keys()) |
                              set(r.total_charging_capacity.keys()) |
                              set(r.total_electricity_consumption.keys())):
                row[f'bev_vehicles_{year}'] = r.total_bev_vehicles.get(year, 0)
                row[f'charging_kW_{year}'] = r.total_charging_capacity.get(year, 0)
                row[f'electricity_kWh_{year}'] = r.total_electricity_consumption.get(year, 0)

            rows.append(row)

        df = pd.DataFrame(rows)
        csv_path = output_path / 'all_scenario_results.csv'
        df.to_csv(csv_path, index=False)
        print(f"Exported {len(rows)} scenarios to {csv_path}")

        return csv_path


def analyze_uncertainty_results(
    results_path: Path,
    scenarios_json_path: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> ResultsAnalyzer:
    """
    Convenience function to analyze uncertainty results.

    Parameters:
    -----------
    results_path : Path
        Path containing scenario result folders
    scenarios_json_path : Path, optional
        Path to scenarios.json with parameter values
    output_path : Path, optional
        Path for saving analysis outputs (default: results_path/analysis)

    Returns:
    --------
    ResultsAnalyzer : Configured analyzer with loaded results
    """
    analyzer = ResultsAnalyzer(results_path, scenarios_json_path)
    n_loaded = analyzer.load_all_results()

    if n_loaded == 0:
        print("No results to analyze")
        return analyzer

    if output_path is None:
        output_path = results_path / 'analysis'

    analyzer.generate_report(output_path)
    analyzer.export_results_table(output_path)

    return analyzer


if __name__ == "__main__":
    # Example usage
    results_path = Path("results/uncertainty_analysis")
    scenarios_path = Path("input_data/uncertainty_scenarios/scenarios.json")

    if results_path.exists():
        analyzer = analyze_uncertainty_results(
            results_path=results_path,
            scenarios_json_path=scenarios_path if scenarios_path.exists() else None
        )

        print("\n=== Sensitivity Analysis ===")
        sensitivity = analyzer.compute_sensitivity_indices()
        if not sensitivity.empty:
            print(sensitivity.sort_values('rank'))

        print("\n=== Robustness (2040) ===")
        robustness = analyzer.identify_robust_decisions(2040)
        for key, metrics in robustness.items():
            if metrics.get('classification'):
                print(f"  {metrics['name']}: {metrics['classification']} (CV={metrics['cv']:.2%})")
    else:
        print(f"Results path not found: {results_path}")
        print("Run the uncertainty analysis first.")
