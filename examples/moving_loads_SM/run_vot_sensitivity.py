"""
VoT (Value of Time) Sensitivity Analysis
========================================

Creates 5 scenarios with different VoT values:
- vot_10: EUR 10/hour
- vot_20: EUR 20/hour
- vot_30: EUR 30/hour (baseline)
- vot_45: EUR 45/hour
- vot_60: EUR 60/hour

All scenarios use:
- Go RES v1.2 GENeSYS scenario (EUR 500/tCO2 in 2040)
- 500 trucks/year threshold
- Mandatory breaks constraint (charging at breaks only)
"""

import sys
import json
from pathlib import Path
from datetime import datetime

script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from SM_preprocessing import SMParameterGenerator
import yaml

# ============================================================================
# CONFIGURATION
# ============================================================================

DATA_SOURCE = "input_data/fixed_international_nuts_2"
OUTPUT_BASE = script_dir / "input_data" / "vot_sensitivity_new"
GENESYS_SCENARIO = "Go RES v1.2"

# VoT values to test (EUR/hour)
VOT_VALUES = [10, 20, 30, 45, 60]

# Carbon price trajectory for Go RES v1.2
CARBON_PRICES = {
    2020: 30, 2024: 73, 2028: 115, 2032: 158, 2036: 329,
    2040: 500, 2044: 625, 2048: 750, 2052: 875, 2056: 1000, 2060: 1000
}

# Thresholds (matching breaks_comparison_full)
VOLUME_THRESHOLD = 500.0  # trucks/year
MIN_PATH_LENGTH = 360.0   # km
CHARGING_MARKUP = 0.30    # 30%

# ============================================================================
# GENERATE SCENARIOS
# ============================================================================

print("=" * 80)
print("VOT SENSITIVITY ANALYSIS - Go RES Scenario")
print("=" * 80)
print(f"Data source: {DATA_SOURCE}")
print(f"GENeSYS scenario: {GENESYS_SCENARIO}")
print(f"Volume threshold: {VOLUME_THRESHOLD} trucks/year")
print(f"VoT values: {VOT_VALUES} EUR/hour")
print()

OUTPUT_BASE.mkdir(parents=True, exist_ok=True)

created_scenarios = []

for vot in VOT_VALUES:
    scenario_name = f"vot_{vot}"

    print()
    print("=" * 80)
    print(f"GENERATING: {scenario_name} (VoT = EUR {vot}/hour)")
    print("=" * 80)

    output_dir = OUTPUT_BASE / scenario_name

    # Create parameter generator with custom VoT
    generator = SMParameterGenerator(
        nuts3_data_dir=DATA_SOURCE,
        output_dir=str(output_dir),
        case_name=scenario_name,
        electricity_prices_variable=True,
        network_costs_variable=True,
        cross_border_only=True,
        filter_low_volume=True,
        min_freight_threshold=VOLUME_THRESHOLD,
        filter_short_paths=True,
        min_path_length=MIN_PATH_LENGTH,
        genesys_scenario=GENESYS_SCENARIO,
        vot=vot  # Custom VoT value for this scenario
    )

    # Load data
    generator.load_nuts3_data()

    # Generate all parameter files
    generator.save_all_parameters()

    # Apply carbon prices to GeographicElement.yaml
    geo_file = output_dir / "GeographicElement.yaml"
    if geo_file.exists():
        with open(geo_file, 'r') as f:
            geo_data = yaml.safe_load(f)

        if 'geographic_element' in geo_data:
            for elem in geo_data['geographic_element']:
                elem['carbon_price'] = CARBON_PRICES

        with open(geo_file, 'w') as f:
            yaml.dump(geo_data, f, default_flow_style=False, sort_keys=False)
        print(f"  -> Applied carbon prices")

    created_scenarios.append({
        'name': scenario_name,
        'vot': vot
    })

    print(f"\n[SUCCESS] Created: {output_dir}")

# ============================================================================
# SAVE SCENARIO METADATA
# ============================================================================

metadata = {
    'generated': datetime.now().isoformat(),
    'genesys_scenario': GENESYS_SCENARIO,
    'volume_threshold': VOLUME_THRESHOLD,
    'charging_markup': CHARGING_MARKUP,
    'scenarios': {sc['name']: {'vot_eur_per_hour': sc['vot']} for sc in created_scenarios}
}

with open(OUTPUT_BASE / 'scenarios.json', 'w') as f:
    json.dump(metadata, f, indent=2)

# ============================================================================
# GENERATE JULIA BATCH SCRIPT
# ============================================================================

julia_script = '''"""
VoT Sensitivity Analysis - Julia Batch Script
==============================================

Runs 5 scenarios with different Value of Time (VoT) values.
All use Go RES v1.2 scenario with mandatory breaks constraint.
"""

using Pkg
working_dir = abspath(joinpath(@__DIR__, ".."))
repo_root = abspath(joinpath(@__DIR__, "..", "..", ".."))
Pkg.activate(repo_root)

using YAML, JuMP, Gurobi, Printf, Dates

include(joinpath(repo_root, "src", "TransComp.jl"))
using .TransComp

# ============================================================================
# SCENARIOS
# ============================================================================

scenarios = [
'''

for sc in created_scenarios:
    julia_script += f'    "{sc["name"]}",  # VoT = EUR {sc["vot"]}/hour\n'

julia_script += ''']

relevant_vars = ["f", "h", "h_plus", "h_exist", "h_minus", "s", "q_fuel_infr_plus", "soc", "travel_time", "extra_break_time"]

results_summary = Dict()

@info "=" ^ 80
@info "VOT SENSITIVITY: $(length(scenarios)) scenarios"
@info "=" ^ 80

batch_start = time()

for (idx, folder) in enumerate(scenarios)
    @info "\\n" * "=" ^ 80
    @info "SCENARIO $idx/$(length(scenarios)): $folder"
    @info "=" ^ 80

    scenario_start = time()

    try
        input_path = abspath(joinpath(@__DIR__, "vot_sensitivity_new", folder))

        if !isdir(input_path)
            @warn "Folder not found: $input_path - SKIPPING"
            results_summary[folder] = Dict("status" => "SKIPPED", "reason" => "Folder not found")
            continue
        end

        timestamp = Dates.format(now(), "yyyy-mm-dd_HH-MM-SS")
        case_name = "$(folder)_$timestamp"

        @info "Loading input data..."
        data_dict = get_input_data(input_path)
        data_structures = parse_data(data_dict)

        @info "Creating model..."
        model, data_structures = create_model(data_structures, case_name, include_vars=relevant_vars)

        # Solver settings
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

        @info "Adding constraints..."

        # Mandatory breaks for travel time
        constraint_mandatory_breaks(model, data_structures)

        # Charging at breaks only
        constraint_charging_at_breaks_only(model, data_structures)

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

        @info "Adding objective..."
        objective(model, data_structures, false)

        GC.gc()

        @info "Solving..."
        optimize!(model)

        scenario_elapsed = time() - scenario_start

        results_path = abspath(joinpath(working_dir, "results", "vot_sensitivity_new", folder))
        mkpath(results_path)
        save_results(model, case_name, data_structures, true, results_path, folder)

        results_summary[folder] = Dict(
            "status" => "SUCCESS",
            "runtime_seconds" => scenario_elapsed,
            "objective_value" => objective_value(model),
            "termination_status" => string(termination_status(model)),
            "results_path" => results_path
        )

        @info "Completed in $(round(scenario_elapsed/60, digits=1)) minutes"
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

@info "\\n" * "=" ^ 80
@info "VOT SENSITIVITY COMPLETE"
@info "Total time: $(round(batch_elapsed/60, digits=1)) minutes"
@info "=" ^ 80

summary_path = abspath(joinpath(working_dir, "results", "vot_sensitivity_new", "batch_summary.yaml"))
mkpath(dirname(summary_path))
YAML.write_file(summary_path, results_summary)
@info "Summary saved to: $summary_path"

for (folder, result) in results_summary
    status = result["status"]
    if status == "SUCCESS"
        @info "  $folder: SUCCESS - Obj: $(result["objective_value"])"
    elseif status == "FAILED"
        @info "  $folder: FAILED - $(get(result, "error", "Unknown"))"
    else
        @info "  $folder: SKIPPED"
    end
end
'''

julia_path = OUTPUT_BASE.parent / "run_vot_sensitivity.jl"
with open(julia_path, 'w') as f:
    f.write(julia_script)
print(f"\n[OK] Julia script: {julia_path}")

# ============================================================================
# SUMMARY
# ============================================================================

print()
print("=" * 80)
print("COMPLETE!")
print("=" * 80)
print(f"Output folder: input_data/vot_sensitivity_new/")
print()
print("Created 5 VoT scenarios:")
for sc in created_scenarios:
    print(f"  - {sc['name']}: VoT = EUR {sc['vot']}/hour")
print()
print("All scenarios use:")
print(f"  - GENeSYS: {GENESYS_SCENARIO}")
print(f"  - Volume threshold: {VOLUME_THRESHOLD} trucks/year")
print(f"  - Charging markup: {CHARGING_MARKUP*100:.0f}%")
print(f"  - Mandatory breaks constraint: YES")
print()
print("Next step: Run the Julia batch script:")
print("  julia input_data/run_vot_sensitivity.jl")
print("=" * 80)
