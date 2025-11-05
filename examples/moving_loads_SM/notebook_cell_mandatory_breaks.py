"""
NOTEBOOK CELL: Mandatory Breaks Analysis for All Cases

Copy this code into a cell in results_representation.ipynb after the data loading cells.
This analyzes the planned break patterns from the input data structure.
"""

# %% [markdown]
# ## Mandatory Breaks Analysis
#
# This section analyzes the mandatory breaks structure from input data across all scenarios.
# It shows the relationship between trip duration (driving time since last break) and break duration.

# %%
from analyze_mandatory_breaks_all_cases import analyze_mandatory_breaks_for_all_cases

# Create the case study name labels dictionary
case_study_name_labels_dict = {
    "case_20251028_091344_var_var": "Base case",
    "case_20251028_091411_var_uni": "Uniform electricity prices",
    "case_20251028_091502_uni_var": "Uniform network fees",
    "case_20251028_091635_uni_uni": "Uniform electricity prices and network fees"
}

# Run the analysis
fig, stats = analyze_mandatory_breaks_for_all_cases(loaded_runs, case_study_name_labels_dict)

# Save the figure
plt.savefig('figures/mandatory_breaks_all_cases.png', dpi=300, bbox_inches='tight')
plt.show()

# %% [markdown]
# ### Key Findings
#
# The plots above show:
# - **Short breaks (0.75h)**: 45-minute mandatory breaks after driving periods
# - **Rest periods (9h)**: Long rest periods for driver recovery
# - **4.5h legal limit**: Red dashed line showing the legal driving limit
# - **Charging type**: Different markers for fast (circles/triangles) vs slow (squares/inverted triangles) charging
#
# All trip durations respect the 4.5h legal driving limit, as these are the planned breaks from the input data structure.
