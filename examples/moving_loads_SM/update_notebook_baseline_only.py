import json

# Read the notebook
with open('uncertainty_analysis_results.ipynb', 'r') as f:
    nb = json.load(f)

# Cell 3: Update paths to only use baseline
nb['cells'][3]['source'] = """# Paths
base_path = Path.cwd()

# BASELINE ONLY - results WITHOUT charging-at-breaks constraint
results_path_without = base_path / "results" / "uncertainty_analysis"
results_path = results_path_without  # For backward compatibility

# Results WITH constraint not yet available - set to None
results_path_with = None

input_scenarios_path = base_path / "input_data" / "uncertainty_scenarios"
cases_json_path = input_scenarios_path / "cases.json"

print(f"Base path: {base_path}")
print(f"Results path (BASELINE): {results_path_without}")
print(f"Cases JSON: {cases_json_path}")
""".split('\n')

# Cell 6: Only load baseline results
nb['cells'][6]['source'] = """# Load all scenario results - BASELINE ONLY (without constraint)
all_results_without = {}
all_inputs = {}

print("Loading BASELINE results (WITHOUT charging-at-breaks constraint)...")
for case in cases:
    scenario_id = case['case_id']
    results = load_scenario_results(scenario_id, custom_results_path=results_path_without)
    if results:
        all_results_without[scenario_id] = results

print(f"Loaded {len(all_results_without)} baseline scenarios")

# For backward compatibility
all_results = all_results_without

# Skip loading 'with constraint' results - not yet available
all_results_with = {}  # Empty - will be populated after running with_breaks optimization
print("Note: 'With constraint' results not yet available. Run run_uncertainty_analysis_with_breaks.jl first.")

# Load inputs (just first scenario per GENeSYS scenario)
for case in cases:
    scenario_id = case['case_id']
    if scenario_id % 6 == 0:
        all_inputs[scenario_id] = load_scenario_input(scenario_id)

print(f"Loaded {len(all_inputs)} scenario inputs for reference")
""".split('\n')

# Cell 7: Update markdown to note comparison not available yet
nb['cells'][7]['source'] = """## Constraint Comparison: With vs Without Charging-at-Breaks

**NOTE: Comparison not yet available - 'with constraint' results pending.**

This section will compare results between two runs:
- **Without constraint**: BEVs can charge at any location along the route (AVAILABLE)
- **With constraint**: BEVs can ONLY charge at mandatory break locations (PENDING)

Skip cells 8-13 until 'with constraint' results are ready.
""".split('\n')

# Cell 8: Make it skip gracefully if no 'with' results
nb['cells'][8]['source'] = """# Load batch summaries for objective value comparison
# SKIP if 'with constraint' results not available

if results_path_with is None or not (results_path_with / 'batch_summary.yaml').exists():
    print("SKIPPING: 'With constraint' results not yet available.")
    print("Run 'julia input_data/run_uncertainty_analysis_with_breaks.jl' first.")
    obj_df = pd.DataFrame()  # Empty df for later cells
else:
    import yaml

    # Load batch summaries
    with open(results_path_without / 'batch_summary.yaml', 'r') as f:
        summary_without = yaml.safe_load(f)

    with open(results_path_with / 'batch_summary.yaml', 'r') as f:
        summary_with = yaml.safe_load(f)

    # Extract objective values
    obj_comparison = []
    for scenario_key in summary_without.keys():
        scenario_id = int(scenario_key.replace('scenario_', ''))
        case = next((c for c in cases if c['case_id'] == scenario_id), None)
        if case and scenario_key in summary_with:
            obj_without = summary_without[scenario_key]['objective_value']
            obj_with = summary_with[scenario_key]['objective_value']
            delta = obj_with - obj_without
            delta_pct = (delta / obj_without) * 100
            obj_comparison.append({
                'scenario_id': scenario_id,
                'genesys': case['genesys_scenario'],
                'tech_cost': case['tech_cost_multiplier'],
                'markup': case['charging_markup'],
                'obj_without': obj_without / 1e9,
                'obj_with': obj_with / 1e9,
                'delta_eur': delta / 1e6,
                'delta_pct': delta_pct
            })

    obj_df = pd.DataFrame(obj_comparison).sort_values('scenario_id')
    print('Objective Value Comparison (With vs Without Constraint):')
    print(f'Mean cost increase: {obj_df["delta_pct"].mean():.4f}%')
    obj_df
""".split('\n')

# Cell 9: Skip gracefully
nb['cells'][9]['source'] = """# Visualize objective value differences
# SKIP if no comparison data

if obj_df.empty:
    print("SKIPPING: No comparison data available yet.")
else:
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    ax1 = axes[0]
    ax1.set_title('Cost Impact - comparison not yet available')
    ax2 = axes[1]
    ax2.set_title('Distribution - comparison not yet available')
    plt.tight_layout()
    plt.show()
""".split('\n')

# Cell 10: Skip gracefully
nb['cells'][10]['source'] = """# Compare BEV electrification rates between with and without constraint
# SKIP if no 'with constraint' results

if not all_results_with:
    print("SKIPPING: No 'with constraint' results available for comparison.")
    bev_df = pd.DataFrame()  # Empty df
else:
    print("Comparison available - run full analysis")
""".split('\n')

# Cell 11: Skip gracefully
nb['cells'][11]['source'] = """# Visualize BEV fleet comparison
# SKIP if no comparison data

if 'bev_df' not in dir() or bev_df.empty:
    print("SKIPPING: No BEV comparison data available.")
else:
    print("Visualization available - run full analysis")
""".split('\n')

# Cell 12: Skip gracefully
nb['cells'][12]['source'] = """# Compare total charging energy (s variable)
# SKIP if no 'with constraint' results

if not all_results_with:
    print("SKIPPING: No 'with constraint' results available for comparison.")
    charging_df = pd.DataFrame()  # Empty df
else:
    print("Comparison available - run full analysis")
""".split('\n')

# Cell 13: Skip gracefully
nb['cells'][13]['source'] = """# Print summary of constraint impact
# SKIP if no comparison data

if 'obj_df' not in dir() or obj_df.empty:
    print("SKIPPING SUMMARY: No constraint comparison data available yet.")
    print("Run 'julia input_data/run_uncertainty_analysis_with_breaks.jl' to generate 'with constraint' results.")
    print("Then re-run this notebook to see the comparison.")
else:
    print("Summary available - run full analysis")
""".split('\n')

# Save the notebook
with open('uncertainty_analysis_results.ipynb', 'w') as f:
    json.dump(nb, f, indent=1)

print("Notebook updated successfully!")
print("Cells 3, 6, 7, 8, 9, 10, 11, 12, 13 modified to skip 'with constraint' comparison.")
