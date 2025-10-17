# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

TransComp is a Julia-based optimization model for determining the transition to low-emission transport at sub-national geographic levels. It encompasses vehicle stock modeling, modal shift, and technological substitution. The model is built using JuMP and Gurobi solver, and can be softlinked with energy system and transport models.

Documentation: https://antoniamgolab.github.io/iDesignRES_transcompmodel/docs/build/index.html

## General guidelines

* The core goal is to implement an analysis for a scientific paper. So, while to accuracy of the model formulation is very important, the consistent usage of the data that i define, so please focus on this.
* The role of CLAUDE is to support in implementing 

## Development Commands

### Running Tests
```bash
julia test/runtests.jl
```

Tests are organized by functionality:
- `test_techshift.jl` - Technology shift functionality
- `test_mode_shift.jl` - Modal shift functionality

### Running Examples
```bash
cd examples/[example_name]
julia [example_script].jl
```

Example directories:
- `examples/Basque country/` - Main case study with multiple scenarios
- `examples/moving_loads_SM/` - Moving loads analysis

### Building Documentation
```bash
cd docs
make html
```

Documentation is built with Sphinx and deployed via Read the Docs.

## Architecture

### Core Module Structure

The main module is defined in `src/TransComp.jl` and includes three key files:

1. **`structs.jl`** - Data structure definitions representing the model domain:
   - Geographic elements: `Node`, `Edge`, `GeographicElement`
   - Transport components: `Mode`, `Product`, `Path`, `Vehicletype`
   - Technology components: `Technology`, `Fuel`, `TechVehicle`
   - Infrastructure: `FuelingInfrTypes`, `InitialFuelingInfr`, `InitialModeInfr`
   - Demand/supply: `Odpair` (origin-destination pairs), `FinancialStatus`, `Regiontype`
   - Constraints: Various share and constraint structs for policies

2. **`model_functions.jl`** - Optimization model formulation:
   - `base_define_variables()` - Decision variable definitions
   - Multiple `constraint_*()` functions for model constraints
   - `objective()` - Objective function definition
   - Uses JuMP and Gurobi for mathematical programming

3. **`support_functions.jl`** - Helper functions:
   - `get_input_data()` - YAML input file parsing
   - `parse_data()` - Data structure initialization
   - `create_model()` - Model instantiation
   - `save_results()` - Output serialization
   - Various set creation functions (`create_m_tv_pairs`, `create_p_r_k_set`, etc.)

### Input Data Format

The model reads YAML configuration files that specify:
- Geographic network (nodes, edges, paths)
- Transport modes and vehicle types
- Technologies and fuels
- Demand (origin-destination pairs)
- Policy constraints (emission targets, mode shares, technology shares)
- Financial parameters and budgets
- Infrastructure expansion pathways

### Typical Model Setup Pattern

Examples follow this standard pattern:
1. Include the TransComp module
2. Load YAML input data file using `get_input_data()`
3. Parse data into structures using `parse_data()`
4. Create base model using `create_model()`
5. Add constraints selectively based on scenario requirements
6. Configure Gurobi solver parameters
7. Call `optimize!()` to solve
8. Save results using `save_results()`

Key constraints added conditionally based on scenario:
- `constraint_detour_time()` - For charging infrastructure planning
- `constraint_vehicle_stock_shift()` - For technology transition
- `constraint_mode_shift()` - For modal shift scenarios
- `constraint_maximum_fueling_infrastructure()` - Infrastructure capacity
- `constraint_monetary_budget()` - Budget constraints
- `constraint_market_share()` - Technology adoption policies

### Solver Configuration

Gurobi parameters are typically tuned for large-scale MIP problems:
- `MIPFocus=1` - Prioritize feasibility
- `Presolve=2` - Aggressive presolve
- `Cuts=3` - Aggressive cutting planes
- `MIPGap=0.0000001` - Very tight optimality gap
- `TimeLimit` - Usually 30+ hours for large cases
- `NumericFocus=1` - Enhanced numerical stability

## Key Dependencies

- Julia 1.6+
- JuMP 1.9 - Mathematical optimization modeling
- Gurobi 1.0 - Commercial solver (license required)
- YAML 0.4 - Configuration file parsing
- ProgressMeter - Progress tracking (used in some functions)

## Results and Visualization

Results are saved to case-specific directories (named with timestamp). Python/Jupyter notebooks in example directories provide visualization:
- `results_analysis.ipynb` - General results analysis
- `final_visualization_rq1.ipynb`, `final_visualization_rq2.ipynb` - Research question specific plots
- Results include vehicle stocks, energy demand, infrastructure deployment, emissions, costs

## Working with This Codebase

- All optimization modeling happens in Julia through the TransComp module
- Python notebooks are used only for post-processing and visualization
- The model is designed to be flexible - constraints are added based on the specific use case
- Input YAML files can be large (several MB) as they encode full scenarios
- Examples in `src/` directory (like `densification.ipynb`) appear to be exploratory/development work