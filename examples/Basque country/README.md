# Basque Country Case Study - TransComp Model

This directory contains the implementation of the TransComp regional transport transition model for the Basque Country (Euskadi), Spain. This README provides comprehensive guidance for new users to understand, run, and extend the model.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Directory Structure](#directory-structure)
4. [Quick Start](#quick-start)
5. [Input Data Format](#input-data-format)
6. [Running the Model](#running-the-model)
7. [Understanding Results](#understanding-results)
8. [Scenario Configuration](#scenario-configuration)
9. [File Reference](#file-reference)
10. [Troubleshooting](#troubleshooting)

---

## Overview

The TransComp model determines the optimal transition pathway to low-emission transport at a regional level. For the Basque Country case study, the model covers:

- **Geographic scope**: Three provinces (NUTS-3 regions)
  - Araba (ES211)
  - Gipuzkoa (ES212)
  - Bizkaia (ES213)
- **Time horizon**: 2020-2060 (configurable)
- **Technologies**: Internal combustion engine (ICE) vehicles and battery electric vehicles (BEVs)
- **Infrastructure**: Public fast charging, public slow charging, home charging, work charging

### What the Model Optimizes

The model minimizes total system costs while meeting transport demand, subject to constraints on:
- Vehicle stock turnover and technology shift rates
- Charging infrastructure expansion limits
- Budget constraints for infrastructure investment
- Detour time penalties for insufficient charging coverage

---

## Prerequisites

### Software Requirements

1. **Julia** (version 1.6 or higher)
   - Download from: https://julialang.org/downloads/

2. **Gurobi Optimizer** (commercial solver, academic licenses available)
   - Download from: https://www.gurobi.com/
   - Obtain a license (free for academics)
   - Set the `GUROBI_HOME` and `GRB_LICENSE_FILE` environment variables

3. **Julia Packages** (installed automatically via Project.toml):
   - YAML
   - JuMP
   - Gurobi
   - Printf
   - ProgressMeter

### Installation Steps

```bash
# 1. Clone the repository
git clone https://github.com/antoniamgolab/iDesignRES_transcompmodel.git
cd iDesignRES_transcompmodel

# 2. Start Julia and activate the project
julia --project=.

# 3. Install dependencies (run once)
julia> using Pkg
julia> Pkg.instantiate()

# 4. Verify Gurobi is working
julia> using Gurobi
julia> Gurobi.Env()  # Should not error
```

---

## Directory Structure

```
examples/Basque country/
├── README.md                    # This documentation file
├── FILE_ORGANIZATION.md         # File categorization guide
├── data/                        # Input data files (YAML)
│   ├── input_rq2_baseline_*.yaml       # RQ2 baseline scenarios
│   ├── td_ONENODE_*.yaml               # Sensitivity analysis inputs
│   └── ...
├── results/                     # Model outputs (auto-generated)
│   └── cs_YYYY-MM-DD_HH-MM-SS/  # Timestamped result folders
├── figures/                     # Generated visualizations (419 PDFs/PNGs)
│   ├── bev_fleet_comparison.pdf
│   ├── SA_*.pdf
│   └── ...
├── basque_cs.jl                 # Main case study script
├── basque_cs_rq2.jl             # Research Question 2 scenarios
├── basque_cs_SA.jl              # Sensitivity analysis script
├── basque_cs_home_charging.jl   # Home charging policy analysis
└── *.ipynb                      # Analysis notebooks (optional)
```

### Essential Files vs Generated Files

| Category | Files | Purpose |
|----------|-------|---------|
| **Essential Scripts** | `basque_cs.jl`, `basque_cs_rq2.jl` | Run the optimization model |
| **Essential Data** | `data/*.yaml` | Input configuration and parameters |
| **Generated Outputs** | `results/` | Model solution files (do not edit) |
| **Generated Figures** | `figures/` | Visualization PDFs/PNGs (419 files) |
| **Analysis Tools** | `*.ipynb`, `*.py` | Post-processing and visualization |

---

## Quick Start

### Run Your First Optimization

```bash
# Navigate to the Basque country example directory
cd examples/Basque\ country

# Run the main case study
julia --project=../.. basque_cs.jl
```

This will:
1. Load input data from `data/td_ONENODE_balanced_expansion_24092025.yaml`
2. Build the optimization model
3. Solve using Gurobi (may take 10-30 minutes)
4. Save results to `results/cs_YYYY-MM-DD_HH-MM-SS/`

### Expected Output

```
Constructed file path: .../data/td_ONENODE_balanced_expansion_24092025.yaml
[ Info: Initialization ...
[ Info: Model created successfully
[ Info: Constraint for slow and fast expansion created successfully
[ Info: Constraint for trip ratio created successfully
...
Solution ....
<Gurobi optimization log>
[ Info: Results saved successfully
[ Info: Model solved successfully
```

---

## Input Data Format

Input files are YAML format with the following main sections:

### Model Configuration

```yaml
Model:
  y_init: 2020          # First year of model horizon
  Y: 41                 # Number of years (2020-2060)
  pre_y: 25             # Vehicle vintage years before y_init
  gamma: 0.001          # Peak demand factor
  alpha_h: 0.1          # Technology shift rate parameter
  beta_h: 0.1           # Technology shift rate parameter
```

### Geographic Elements

```yaml
GeographicElement:
- id: 12
  name: Araba
  node_type: node
- id: 13
  name: Gipuzkoa
  node_type: node
- id: 14
  name: Bizkaia
  node_type: node
```

### Technologies and Vehicles

```yaml
Technology:
- id: 1
  name: diesel
  fuel: 1
- id: 2
  name: electric
  fuel: 2

TechVehicle:
- id: 1
  vehicle_type: 1
  technology: 1
  capital_cost: [25000, 24000, ...]  # per year
  fuel_consumption: 0.06  # kWh/km or L/km
  lifetime: 15
```

### Charging Infrastructure

```yaml
InitialFuelingInfr:
- fuel: electricity
  type: public_fast
  allocation: 12
  installed_kW: 430

MaximumFuelingCapacityByTypeByYear:
- year: 2030
  fueling_type: public_fast
  location: 12
  maximum_capacity: 50000
```

### Complete Data Structure Reference

See `docs/src/manual/input_data.md` for the full specification of all 17+ data structures.

---

## Running the Model

### Basic Model Run

```julia
# basque_cs.jl structure explained:

# 1. Load packages and TransComp module
using YAML, JuMP, Gurobi, Printf, ProgressMeter
include(joinpath(@__DIR__, "../../src/TransComp.jl"))
using .TransComp

# 2. Specify input file
yaml_file_path = normpath(joinpath(@__DIR__, "data/YOUR_INPUT_FILE.yaml"))

# 3. Initialize model
data_dict = get_input_data(yaml_file_path)
data_structures = parse_data(data_dict)
model, data_structures = create_model(data_structures, case_name)

# 4. Add constraints (select which apply)
constraint_vot_dt(model, data_structures)
constraint_vehicle_stock_shift(model, data_structures)
constraint_fueling_demand(model, data_structures)
# ... more constraints as needed

# 5. Set objective and solver options
objective(model, data_structures, false)
set_optimizer_attribute(model, "MIPGap", 0.0001)
set_optimizer_attribute(model, "TimeLimit", 3600 * 30)

# 6. Solve and save
optimize!(model)
save_results(model, case, data_structures, true, results_path)
```

### Available Constraints

| Constraint Function | Purpose |
|---------------------|---------|
| `constraint_vehicle_stock_shift` | Limits rate of technology transition |
| `constraint_fueling_demand` | Ensures charging capacity meets demand |
| `constraint_maximum_fueling_infrastructure` | Caps total infrastructure |
| `constraint_monetary_budget` | Enforces investment budget limits |
| `constraint_detour_time` | Penalizes insufficient charging coverage |
| `constraint_demand_coverage` | Ensures transport demand is met |

### Solver Configuration

Key Gurobi parameters (adjust for your hardware):

```julia
set_optimizer_attribute(model, "MIPGap", 0.0001)     # Optimality gap
set_optimizer_attribute(model, "TimeLimit", 108000)  # 30 hours max
set_optimizer_attribute(model, "Threads", 8)         # CPU threads
set_optimizer_attribute(model, "MIPFocus", 1)        # Focus on feasibility
```

---

## Understanding Results

### Output Files

Each run creates a timestamped folder in `results/` containing:

| File | Description |
|------|-------------|
| `*_h_dict.yaml` | Vehicle stock by (year, od-pair, tech-vehicle, vintage) |
| `*_h_plus_dict.yaml` | New vehicle purchases |
| `*_h_minus_dict.yaml` | Vehicle retirements |
| `*_q_fuel_infr_plus_dict.yaml` | Charging infrastructure additions (kW) |
| `*_detour_time_dict.yaml` | Detour times by location/year |
| `metadata.yaml` | Run configuration and input file reference |

### Key Decision Variables

1. **h (Vehicle Stock)**: Number of vehicles by type, location, and vintage
   - Index: `(year, odpair_id, tech_vehicle_id, vintage_year)`
   - Example: `(2030, 1, 5, 2025): 15000.0` = 15,000 vehicles

2. **q_fuel_infr_plus (Infrastructure)**: Charging capacity additions in kW
   - Index: `(year, (fuel_id, type_id), geography_id)`
   - Example: `(2030, (2, 1), 12): 5000.0` = 5 MW added

3. **detour_time**: Additional travel time due to charging infrastructure gaps
   - Index: `(year, type_id, geography_id)`

### Analyzing Results

Use the provided Jupyter notebooks or create your own:

```python
import yaml

# Load vehicle stock results
with open('results/cs_2024-01-15_10-30-00/h_dict.yaml') as f:
    h_data = yaml.safe_load(f)

# Parse key structure
for key, value in h_data.items():
    year, od_pair, tech_vehicle, vintage = eval(key)
    print(f"Year {year}: {value:.0f} vehicles")
```

---

## Scenario Configuration

### Creating a New Scenario

1. **Copy an existing input file**:
   ```bash
   cp data/input_rq2_baseline_20250906.yaml data/my_scenario.yaml
   ```

2. **Modify key parameters**:
   - `MaximumFuelingCapacityByTypeByYear` - Infrastructure limits
   - `MonetaryBudget` - Investment constraints
   - `Technology` capital costs - Vehicle economics
   - `Demand` - Transport demand projections

3. **Update run script**:
   ```julia
   yaml_file_path = normpath(joinpath(@__DIR__, "data/my_scenario.yaml"))
   ```

### Sensitivity Analysis

The `basque_cs_SA.jl` script demonstrates parameter sweeps:

```julia
# Example: Test different alpha values
for alpha in [1.0, 1.2, 1.4, 1.6, 1.8, 2.0]
    input_file = "data/td_ONENODE_balanced_expansion_alpha_$(alpha).yaml"
    # Run model...
end
```

---

## File Reference

### Scripts (Essential)

| File | Purpose | When to Use |
|------|---------|-------------|
| `basque_cs.jl` | Main model run | Standard analysis |
| `basque_cs_rq2.jl` | RQ2 scenarios | Infrastructure acceleration research |
| `basque_cs_SA.jl` | Sensitivity analysis | Parameter variation studies |
| `basque_cs_home_charging.jl` | Home charging | Policy impact analysis |

### Input Data Files

| Pattern | Description |
|---------|-------------|
| `input_rq2_baseline_*.yaml` | Baseline scenarios for RQ2 |
| `input_rq2_baseline_overshoot_*.yaml` | +30% infrastructure target |
| `td_ONENODE_balanced_expansion_*.yaml` | Balanced infrastructure strategy |
| `td_ONENODE_scenario_*_home_charging_ex.yaml` | Home charging availability scenarios |

### Analysis Notebooks

| Notebook | Purpose |
|----------|---------|
| `final_visualization_rq1.ipynb` | Research Question 1 results |
| `final_visualization_rq2.ipynb` | Research Question 2 results |
| `SA_visualization.ipynb` | Sensitivity analysis plots |
| `h_comparison_mixed_sources.ipynb` | Cross-scenario vehicle fleet comparison |

---

## Troubleshooting

### Common Issues

**1. Gurobi License Error**
```
ERROR: LoadError: Gurobi Error 10009: Failed to obtain a Gurobi license
```
**Solution**: Verify `GRB_LICENSE_FILE` environment variable points to valid license.

**2. Model Infeasible**
```
Model status: INFEASIBLE
```
**Solution**:
- Check demand doesn't exceed available capacity
- Verify budget constraints are realistic
- Review `MaximumFuelingCapacityByTypeByYear` limits

**3. Out of Memory**
```
OutOfMemoryError()
```
**Solution**:
- Reduce time horizon (`Y` parameter)
- Reduce geographic granularity
- Use `set_optimizer_attribute(model, "NodefileStart", 0.5)`

**4. Slow Solution Time**
**Solution**:
- Increase `MIPGap` (e.g., 0.01 instead of 0.0001)
- Set shorter `TimeLimit`
- Use `MIPFocus` = 1 for faster feasible solutions

### Getting Help

1. Check existing documentation: `docs/src/manual/`
2. Review mathematical formulation: `docs/mathematical_formulation-euqations/math_formulation.pdf`
3. Contact: [Repository issues page]

---

## Version Information

- **Model Version**: TransComp v0.1.0
- **Case Study**: Basque Country (Euskadi)
- **Last Updated**: November 2025
- **Julia Compatibility**: 1.6+
- **Solver**: Gurobi 10.0+

---

## Citation

If you use this model in your research, please cite:

```bibtex
@software{transcomp2025,
  author = {Golab, Antonia},
  title = {TransComp: Regional Transport Transition Model},
  year = {2025},
  url = {https://github.com/antoniamgolab/iDesignRES_transcompmodel}
}
```
