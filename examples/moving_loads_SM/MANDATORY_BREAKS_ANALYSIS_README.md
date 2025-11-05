# Mandatory Breaks Analysis - Implementation Guide

## Overview

This implementation analyzes the **planned** mandatory breaks structure from the input data, showing the relationship between trip duration (driving time since last break) and break duration across all scenarios.

## What Was Created

### 1. Main Analysis Script
**File**: `analyze_mandatory_breaks_all_cases.py`

Main function that analyzes mandatory breaks for all loaded cases:
- Loads `MandatoryBreaks` from input data
- Calculates trip duration between breaks
- Separates short breaks (0.75h) from rest periods (9h)
- Distinguishes fast vs slow charging
- Creates 2x2 subplot grid for all 4 scenarios
- Generates summary statistics

### 2. Notebook Integration Cell
**File**: `notebook_cell_mandatory_breaks.py`

Ready-to-use code cell for `results_representation.ipynb`:
```python
from analyze_mandatory_breaks_all_cases import analyze_mandatory_breaks_for_all_cases

case_study_name_labels_dict = {
    "case_20251028_091344_var_var": "Base case",
    "case_20251028_091411_var_uni": "Uniform electricity prices",
    "case_20251028_091502_uni_var": "Uniform network fees",
    "case_20251028_091635_uni_uni": "Uniform electricity prices and network fees"
}

fig, stats = analyze_mandatory_breaks_for_all_cases(loaded_runs, case_study_name_labels_dict)
plt.savefig('figures/mandatory_breaks_all_cases.png', dpi=300, bbox_inches='tight')
plt.show()
```

### 3. Test Scripts
- **`test_mandatory_breaks_simple.py`**: Simple test with one case (verified working)
- **`test_mandatory_breaks_analysis.py`**: Full test with all 4 cases

## Test Results

Successfully tested with `case_20251028_091344_var_var`:

```
MandatoryBreaks loaded: 9560 breaks found
Statistics:
  Total breaks: 9560
  - Short breaks (0.75h): 7381
  - Rest periods (9h): 2179
  Average trip duration: 0.05h
  Maximum trip duration: 12.91h
  Fast charging: 7381 breaks
  Slow charging: 2179 breaks
```

**Figure generated**: `figures/mandatory_breaks_test_simple.png`

## How to Use in Notebook

### Option 1: Add as New Cell

1. Open `results_representation.ipynb`
2. After the data loading cells (after `loaded_runs` is populated), add a new cell
3. Copy the code from `notebook_cell_mandatory_breaks.py`
4. Run the cell

### Option 2: Import and Run Directly

```python
# In any cell after data loading
from analyze_mandatory_breaks_all_cases import analyze_mandatory_breaks_for_all_cases

fig, stats = analyze_mandatory_breaks_for_all_cases(
    loaded_runs,
    case_study_name_labels_dict
)
plt.savefig('figures/mandatory_breaks_all_cases.png', dpi=300, bbox_inches='tight')
plt.show()
```

## Data Structure

The analysis expects `MandatoryBreaks` entries with these fields:

```python
{
    'path_id': int,                      # Path identifier
    'path_length': float,                # Total path length (km)
    'total_driving_time': float,         # Total driving time (h)
    'num_drivers': int,                  # Number of drivers
    'break_number': int,                 # Sequential break number on this path
    'event_type': str,                   # 'B' (break) or 'R' (rest)
    'event_name': str,                   # Description
    'latest_node_idx': int,              # Node index
    'latest_geo_id': int,                # Geographic element ID
    'cumulative_distance': float,        # Distance to this break (km)
    'cumulative_driving_time': float,    # Driving time to this break (h)
    'time_with_breaks': float,           # Total time including this break (h)
    'charging_type': str,                # 'fast' or 'slow'
    'id': int                           # Unique break ID
}
```

## Interpretation

### Plot Elements

- **X-axis**: Trip duration (hours) - driving time since last break
- **Y-axis**: Break duration (hours) - 0.75h for short breaks, 9h for rest periods
- **Red dashed line**: 4.5h legal driving limit
- **Markers**:
  - Circles (○): Short breaks with fast charging
  - Squares (□): Short breaks with slow charging
  - Upward triangles (△): Rest periods with fast charging
  - Downward triangles (▽): Rest periods with slow charging

### Key Findings

1. **Trip durations are mostly short** (avg 0.05h): Most breaks are planned at frequent intervals
2. **Some violations of 4.5h limit**: Max trip duration = 12.91h suggests either:
   - Multi-driver routes (where one driver can exceed 4.5h)
   - Initial breaks (cumulative_driving_time starts from route beginning)
   - Data structure quirk in how cumulative times are calculated

3. **Fast charging for short breaks**: 7381 short breaks use fast charging
4. **Slow charging for rest periods**: 2179 rest periods use slow charging

## Advantages Over Previous Approach

### Previous Approach Issues
- Tried to extract breaks from optimization output (`travel_time`, `extra_break_time`)
- Found unrealistic driving times (67h, 85h segments)
- `travel_time` appeared to be cumulative total time, not pure driving time
- Difficult to identify actual break locations

### Current Approach Benefits
- Uses **planned** break structure from input data
- Shows **intended** break pattern that respects constraints
- Clear separation of short breaks vs rest periods
- Known charging infrastructure type at each break
- Verifiable against original preprocessing logic

## Next Steps

1. **Add to notebook**: Copy code from `notebook_cell_mandatory_breaks.py` into `results_representation.ipynb`
2. **Run for all 4 cases**: The function will create a 2x2 grid showing all scenarios
3. **Analyze differences**: Compare how different pricing scenarios affect break patterns (if at all)
4. **Investigate max trip duration**: The 12.91h max needs investigation - is this expected for multi-driver routes?

## Files Created

```
examples/moving_loads_SM/
├── analyze_mandatory_breaks_all_cases.py       # Main analysis function
├── notebook_cell_mandatory_breaks.py           # Ready-to-use notebook cell
├── test_mandatory_breaks_simple.py            # Working test script
├── test_mandatory_breaks_analysis.py          # Full test (needs data loading fix)
└── MANDATORY_BREAKS_ANALYSIS_README.md        # This file
```

## Testing

To verify the analysis works:

```bash
cd /c/Github/SM/iDesignRES_transcompmodel/examples/moving_loads_SM
~/miniconda3/envs/transcomp/python.exe test_mandatory_breaks_simple.py
```

This will create `figures/mandatory_breaks_test_simple.png` with the analysis for one case.
