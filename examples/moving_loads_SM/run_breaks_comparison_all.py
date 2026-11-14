"""
Generate Mandatory Breaks vs Flexible Charging Comparison - ALL 4 GENeSYS Scenarios
===================================================================================

Creates 8 scenarios total:
- 4 GENeSYS scenarios (Go RES, NECP, REPower, Trinity)
- Each with 2 variants: with_breaks (charging at breaks only) vs without_breaks (charging anywhere)
"""

import sys
import shutil
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
OUTPUT_BASE = script_dir / "input_data" / "breaks_comparison_full"

# 4 GENeSYS scenarios with their carbon prices in 2040
GENESYS_SCENARIOS = [
    ("Go RES v1.2", "go_res", 500),
    ("NECPEssentials v1.2", "necp", 250),
    ("REPowerEU++ v1.2", "repower", 350),
    ("Trinity v1.2", "trinity", 180),
]

# Carbon price trajectories by scenario
CARBON_PRICE_TRAJECTORIES = {
    'Go RES v1.2': {2020: 30, 2024: 73, 2028: 115, 2032: 158, 2036: 329, 2040: 500, 2044: 625, 2048: 750, 2052: 875, 2056: 1000, 2060: 1000},
    'REPowerEU++ v1.2': {2020: 30, 2024: 58, 2028: 85, 2032: 113, 2036: 231, 2040: 350, 2044: 438, 2048: 525, 2052: 613, 2056: 700, 2060: 700},
    'NECPEssentials v1.2': {2020: 30, 2024: 48, 2028: 65, 2032: 83, 2036: 166, 2040: 250, 2044: 313, 2048: 375, 2052: 438, 2056: 500, 2060: 500},
    'Trinity v1.2': {2020: 30, 2024: 43, 2028: 55, 2032: 68, 2036: 124, 2040: 180, 2044: 223, 2048: 265, 2052: 308, 2056: 350, 2060: 350},
}

# Thresholds
VOLUME_THRESHOLD = 500.0  # trucks/year
MIN_PATH_LENGTH = 360.0   # km
CHARGING_MARKUP = 0.30    # 30%

# ============================================================================
# GENERATE SCENARIOS
# ============================================================================

print("=" * 80)
print("BREAKS COMPARISON - ALL 4 GENESYS SCENARIOS")
print("=" * 80)
print(f"Data source: {DATA_SOURCE}")
print(f"Volume threshold: {VOLUME_THRESHOLD} trucks/year")
print(f"Charging markup: {CHARGING_MARKUP*100:.0f}%")
print(f"Scenarios: {len(GENESYS_SCENARIOS)} GENeSYS × 2 breaks variants = 8 total")
print()

OUTPUT_BASE.mkdir(parents=True, exist_ok=True)

created_scenarios = []

for genesys_name, genesys_short, carbon_2040 in GENESYS_SCENARIOS:
    for breaks_variant in ["with_breaks", "without_breaks"]:
        scenario_name = f"{genesys_short}_{breaks_variant}"

        print()
        print("=" * 80)
        print(f"GENERATING: {scenario_name}")
        print(f"  GENeSYS: {genesys_name} (EUR {carbon_2040}/tCO2 in 2040)")
        print(f"  Breaks: {breaks_variant}")
        print("=" * 80)

        output_dir = OUTPUT_BASE / scenario_name

        # Create parameter generator
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
            genesys_scenario=genesys_name
        )

        # Load data
        generator.load_nuts3_data()

        # Generate all parameter files
        generator.save_all_parameters()

        # Apply carbon prices
        geo_file = output_dir / "GeographicElement.yaml"
        if geo_file.exists():
            with open(geo_file, 'r') as f:
                geo_data = yaml.safe_load(f)

            carbon_prices = CARBON_PRICE_TRAJECTORIES[genesys_name]
            if 'geographic_element' in geo_data:
                for elem in geo_data['geographic_element']:
                    elem['carbon_price'] = carbon_prices

            with open(geo_file, 'w') as f:
                yaml.dump(geo_data, f, default_flow_style=False, sort_keys=False)
            print(f"  -> Applied carbon prices for {genesys_name}")

        created_scenarios.append({
            'name': scenario_name,
            'genesys': genesys_name,
            'genesys_short': genesys_short,
            'carbon_2040': carbon_2040,
            'breaks_variant': breaks_variant,
            'use_breaks_constraint': breaks_variant == "with_breaks"
        })

        print(f"\n[SUCCESS] Created: {output_dir}")

# ============================================================================
# GENERATE JULIA BATCH SCRIPT
# ============================================================================

julia_script = '''"""
Breaks Comparison - All 4 GENeSYS Scenarios
============================================

Runs 8 scenarios:
- 4 GENeSYS scenarios (Go RES, NECP, REPower, Trinity)
- Each with/without charging-at-breaks-only constraint
"""

using Pkg
working_dir = abspath(joinpath(@__DIR__, ".."))
repo_root = abspath(joinpath(@__DIR__, "..", "..", ".."))
Pkg.activate(repo_root)

using YAML, JuMP, Gurobi, Printf, Dates

include(joinpath(repo_root, "src", "TransComp.jl"))
using .TransComp

# ============================================================================
# SCENARIOS: (folder_name, use_charging_at_breaks_constraint)
# ============================================================================

scenarios = [
'''

for sc in created_scenarios:
    use_constraint = "true" if sc['use_breaks_constraint'] else "false"
    julia_script += f'    ("{sc["name"]}", {use_constraint}),  # {sc["genesys"]} - EUR{sc["carbon_2040"]}/tCO2\n'

julia_script += ''']

relevant_vars = ["f", "h", "h_plus", "h_exist", "h_minus", "s", "q_fuel_infr_plus", "soc", "travel_time", "extra_break_time"]

results_summary = Dict()

@info "=" ^ 80
@info "BREAKS COMPARISON: $(length(scenarios)) scenarios"
@info "=" ^ 80

batch_start = time()

for (idx, (folder, use_breaks_constraint)) in enumerate(scenarios)
    @info "\\n" * "=" ^ 80
    @info "SCENARIO $idx/$(length(scenarios)): $folder"
    @info "  charging_at_breaks_only = $use_breaks_constraint"
    @info "=" ^ 80

    scenario_start = time()

    try
        input_path = abspath(joinpath(@__DIR__, "breaks_comparison_full", folder))

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

        # BOTH variants get mandatory breaks (for travel time)
        constraint_mandatory_breaks(model, data_structures)

        # KEY DIFFERENCE: Only add charging restriction for "with_breaks" variants
        if use_breaks_constraint
            @info "  -> Adding constraint_charging_at_breaks_only"
            constraint_charging_at_breaks_only(model, data_structures)
        else
            @info "  -> Charging allowed anywhere (no breaks constraint)"
        end

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

        results_path = abspath(joinpath(working_dir, "results", "breaks_comparison_full", folder))
        mkpath(results_path)
        save_results(model, case_name, data_structures, true, results_path, folder)

        results_summary[folder] = Dict(
            "status" => "SUCCESS",
            "runtime_seconds" => scenario_elapsed,
            "objective_value" => objective_value(model),
            "termination_status" => string(termination_status(model)),
            "charging_at_breaks_only" => use_breaks_constraint,
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
@info "BREAKS COMPARISON COMPLETE"
@info "Total time: $(round(batch_elapsed/60, digits=1)) minutes"
@info "=" ^ 80

summary_path = abspath(joinpath(working_dir, "results", "breaks_comparison_full", "batch_summary.yaml"))
mkpath(dirname(summary_path))
YAML.write_file(summary_path, results_summary)
@info "Summary saved to: $summary_path"

for (folder, result) in results_summary
    status = result["status"]
    if status == "SUCCESS"
        breaks_str = get(result, "charging_at_breaks_only", false) ? "breaks-only" : "anywhere"
        @info "  $folder ($breaks_str): SUCCESS - Obj: $(result["objective_value"])"
    elseif status == "FAILED"
        @info "  $folder: FAILED - $(get(result, "error", "Unknown"))"
    else
        @info "  $folder: SKIPPED"
    end
end
'''

julia_path = OUTPUT_BASE.parent / "run_breaks_comparison_full.jl"
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
print(f"Output folder: input_data/breaks_comparison_full/")
print()
print("Created 8 scenarios:")
for sc in created_scenarios:
    constraint = "charging at breaks only" if sc['use_breaks_constraint'] else "charging anywhere"
    print(f"  - {sc['name']}: {sc['genesys']} (EUR{sc['carbon_2040']}/tCO2) - {constraint}")
print()
print("Next step: Run the Julia batch script:")
print("  julia input_data/run_breaks_comparison_full.jl")
print("=" * 80)
