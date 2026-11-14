"""
Batch Runner for Uncertainty Analysis
=====================================

Runs the TransComp model for multiple uncertainty scenarios.
Collects results and saves them for analysis.

This script is designed to be run from Julia, calling the main model.
"""

import subprocess
import json
import time
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import yaml


@dataclass
class ScenarioResult:
    """Results from a single scenario run."""
    scenario_id: int
    status: str  # 'SUCCESS', 'FAILED', 'SKIPPED'
    runtime_seconds: float
    objective_value: Optional[float]
    termination_status: Optional[str]
    error_message: Optional[str]
    results_path: Optional[str]

    def to_dict(self) -> Dict:
        return asdict(self)


class BatchRunner:
    """
    Runs TransComp model for multiple uncertainty scenarios.

    This class generates a Julia batch script that runs all scenarios
    sequentially, collecting results from each.
    """

    def __init__(
        self,
        scenario_folders: List[Path],
        results_base_path: Path,
        julia_script_template: Optional[Path] = None
    ):
        """
        Initialize the batch runner.

        Parameters:
        -----------
        scenario_folders : List[Path]
            List of paths to scenario input folders
        results_base_path : Path
            Base path for storing results
        julia_script_template : Path, optional
            Path to Julia script template (default: uses SM_batch.jl as template)
        """
        self.scenario_folders = scenario_folders
        self.results_base_path = Path(results_base_path)
        self.results_base_path.mkdir(parents=True, exist_ok=True)

        self.julia_script_template = julia_script_template

    def generate_julia_batch_script(self, output_path: Path) -> Path:
        """
        Generate a Julia batch script to run all scenarios.

        Returns the path to the generated script.
        """
        scenario_list = ",\n    ".join([f'"{p.name}"' for p in self.scenario_folders])

        script_content = f'''"""
Auto-generated batch script for uncertainty analysis scenarios
Generated: {datetime.now().isoformat()}

Script location: examples/moving_loads_SM/input_data/uncertainty_scenarios/run_uncertainty_analysis.jl
Repository root: ../../../../ (4 levels up)
Working dir: examples/moving_loads_SM/ (2 levels up)
"""

using Pkg
# Script is in input_data/uncertainty_scenarios/, go up 2 levels to examples/moving_loads_SM/
# Use abspath to resolve relative paths properly
working_dir = abspath(joinpath(@__DIR__, "..", ".."))
# Go up 4 levels to repository root (where Project.toml is)
repo_root = abspath(joinpath(@__DIR__, "..", "..", "..", ".."))
Pkg.activate(repo_root)

using YAML, JuMP, Gurobi, Printf, Dates

include(joinpath(repo_root, "src", "TransComp.jl"))
using .TransComp

# ============================================================================
# UNCERTAINTY ANALYSIS SCENARIOS
# ============================================================================

scenario_folders = [
    {scenario_list}
]

# Variables to include
relevant_vars = ["f", "h", "h_plus", "h_exist", "h_minus", "s", "q_fuel_infr_plus", "soc", "travel_time", "extra_break_time"]

# Results storage
results_summary = Dict()

@info "=" ^ 80
@info "UNCERTAINTY ANALYSIS: $(length(scenario_folders)) scenarios"
@info "=" ^ 80

batch_start = time()

for (idx, folder) in enumerate(scenario_folders)
    @info "\\n" * "=" ^ 80
    @info "SCENARIO $idx/$(length(scenario_folders)): $folder"
    @info "=" ^ 80

    scenario_start = time()

    try
        # Scenario folders are in input_data/uncertainty_scenarios/
        input_path = abspath(joinpath(@__DIR__, folder))

        if !isdir(input_path)
            @warn "Folder not found: $input_path - SKIPPING"
            results_summary[folder] = Dict("status" => "SKIPPED", "reason" => "Folder not found")
            continue
        end

        # Generate unique case name
        timestamp = Dates.format(now(), "yyyy-mm-dd_HH-MM-SS")
        case_name = "$(folder)_$timestamp"

        # Load and parse data
        @info "Loading input data..."
        data_dict = get_input_data(input_path)
        data_structures = parse_data(data_dict)

        # Create model
        @info "Creating model..."
        model, data_structures = create_model(data_structures, case_name, include_vars=relevant_vars)

        # Configure solver
        set_optimizer_attribute(model, "Method", 2)
        set_optimizer_attribute(model, "MIPFocus", 1)
        set_optimizer_attribute(model, "Cuts", 1)
        set_optimizer_attribute(model, "MIPGap", 0.01)
        set_optimizer_attribute(model, "NumericFocus", 3)
        set_optimizer_attribute(model, "ScaleFlag", 2)
        set_optimizer_attribute(model, "FeasibilityTol", 1e-5)
        set_optimizer_attribute(model, "OptimalityTol", 1e-5)
        set_optimizer_attribute(model, "Crossover", 0)
        set_optimizer_attribute(model, "BarConvTol", 1e-6)

        # Add constraints
        @info "Adding constraints..."
        constraint_mandatory_breaks(model, data_structures)
        constraint_fueling_infrastructure(model, data_structures)
        constraint_fueling_infrastructure_expansion_shift(model, data_structures)
        constraint_soc_track(model, data_structures)
        constraint_soc_max(model, data_structures)
        constraint_travel_time_track(model, data_structures)
        constraint_mode_shift(model, data_structures)
        if !isempty(data_structures["max_mode_share_list"])
            constraint_max_mode_share(model, data_structures)
        end
        constraint_demand_coverage(model, data_structures)
        constraint_vehicle_sizing(model, data_structures)
        constraint_vehicle_aging(model, data_structures)
        constraint_vehicle_stock_shift(model, data_structures)

        # Add objective
        @info "Adding objective..."
        objective(model, data_structures, false)

        GC.gc()

        # Solve
        @info "Solving..."
        optimize!(model)

        scenario_elapsed = time() - scenario_start

        # Save results (to examples/moving_loads_SM/results/uncertainty_analysis/)
        results_path = abspath(joinpath(working_dir, "results", "uncertainty_analysis", folder))
        @info "Creating results directory: $results_path"
        mkpath(results_path)
        @info "Saving results to: $results_path"
        save_results(model, case_name, data_structures, true, results_path, folder)

        results_summary[folder] = Dict(
            "status" => "SUCCESS",
            "runtime_seconds" => scenario_elapsed,
            "objective_value" => objective_value(model),
            "termination_status" => string(termination_status(model)),
            "results_path" => results_path
        )

        @info "Scenario $folder completed in $(round(scenario_elapsed/60, digits=1)) minutes"
        @info "Objective: $(objective_value(model))"

    catch e
        scenario_elapsed = time() - scenario_start
        @error "FAILED: $folder"
        @error sprint(showerror, e, catch_backtrace())

        results_summary[folder] = Dict(
            "status" => "FAILED",
            "runtime_seconds" => scenario_elapsed,
            "error" => string(e)
        )
    end

    GC.gc()
end

batch_elapsed = time() - batch_start

# Save summary
@info "\\n" * "=" ^ 80
@info "UNCERTAINTY ANALYSIS COMPLETE"
@info "Total time: $(round(batch_elapsed/60, digits=1)) minutes"
@info "=" ^ 80

# Write results summary to YAML
summary_path = abspath(joinpath(working_dir, "results", "uncertainty_analysis", "batch_summary.yaml"))
mkpath(dirname(summary_path))
YAML.write_file(summary_path, results_summary)
@info "Summary saved to: $summary_path"

# Print summary
for (folder, result) in results_summary
    status = result["status"]
    if status == "SUCCESS"
        @info "  $folder: SUCCESS ($(round(result["runtime_seconds"]/60, digits=1))m)"
    elseif status == "FAILED"
        @info "  $folder: FAILED - $(get(result, "error", "Unknown"))"
    else
        @info "  $folder: SKIPPED"
    end
end
'''

        script_path = output_path / "run_uncertainty_analysis.jl"
        with open(script_path, 'w') as f:
            f.write(script_content)

        print(f"Generated Julia batch script: {script_path}")
        return script_path

    def run(self, julia_executable: str = "julia") -> List[ScenarioResult]:
        """
        Run all scenarios using the generated Julia script.

        Parameters:
        -----------
        julia_executable : str
            Path to Julia executable (default: 'julia' in PATH)

        Returns:
        --------
        List[ScenarioResult] : Results from all scenarios
        """
        # Generate the batch script
        script_path = self.generate_julia_batch_script(
            self.scenario_folders[0].parent.parent  # Goes to examples/moving_loads_SM
        )

        print(f"\n=== Running Uncertainty Analysis ===")
        print(f"Scenarios: {len(self.scenario_folders)}")
        print(f"Script: {script_path}")

        # Run Julia script
        start_time = time.time()
        try:
            result = subprocess.run(
                [julia_executable, str(script_path)],
                capture_output=True,
                text=True,
                cwd=script_path.parent
            )

            if result.returncode != 0:
                print(f"Julia script failed with return code {result.returncode}")
                print(f"STDERR: {result.stderr}")

            print(result.stdout)

        except Exception as e:
            print(f"Error running Julia: {e}")
            raise

        elapsed = time.time() - start_time
        print(f"\nTotal runtime: {elapsed/60:.1f} minutes")

        # Load and return results
        summary_path = script_path.parent / "results" / "uncertainty_analysis" / "batch_summary.json"
        if summary_path.exists():
            return self._parse_results(summary_path)
        else:
            print(f"Warning: Summary file not found at {summary_path}")
            return []

    def _parse_results(self, summary_path: Path) -> List[ScenarioResult]:
        """Parse the batch summary JSON into ScenarioResult objects."""
        with open(summary_path, 'r') as f:
            summary = json.load(f)

        results = []
        for folder, data in summary.items():
            # Extract scenario_id from folder name (e.g., "scenario_001")
            try:
                scenario_id = int(folder.split('_')[1])
            except (IndexError, ValueError):
                scenario_id = -1

            result = ScenarioResult(
                scenario_id=scenario_id,
                status=data.get('status', 'UNKNOWN'),
                runtime_seconds=data.get('runtime_seconds', 0.0),
                objective_value=data.get('objective_value'),
                termination_status=data.get('termination_status'),
                error_message=data.get('error'),
                results_path=data.get('results_path')
            )
            results.append(result)

        return sorted(results, key=lambda x: x.scenario_id)


def create_batch_runner_from_scenarios(
    base_case_path: Path,
    scenarios_path: Path,
    results_path: Path
) -> BatchRunner:
    """
    Create a BatchRunner from an existing scenarios folder.

    Parameters:
    -----------
    base_case_path : Path
        Path to base case (for reference)
    scenarios_path : Path
        Path containing scenario_XXX folders
    results_path : Path
        Path for storing results

    Returns:
    --------
    BatchRunner : Configured batch runner
    """
    scenario_folders = sorted(scenarios_path.glob("scenario_*"))
    print(f"Found {len(scenario_folders)} scenario folders")

    return BatchRunner(
        scenario_folders=scenario_folders,
        results_base_path=results_path
    )


if __name__ == "__main__":
    # Example usage
    from pathlib import Path

    scenarios_path = Path("input_data/uncertainty_scenarios")
    results_path = Path("results/uncertainty_analysis")

    if scenarios_path.exists():
        runner = create_batch_runner_from_scenarios(
            base_case_path=Path("input_data/case_nuts2_complete"),
            scenarios_path=scenarios_path,
            results_path=results_path
        )

        # Generate script only (don't run)
        script = runner.generate_julia_batch_script(Path("."))
        print(f"\nGenerated script: {script}")
        print("To run: julia run_uncertainty_analysis.jl")
    else:
        print(f"Scenarios path not found: {scenarios_path}")
        print("Run the full pipeline first to create scenarios.")
