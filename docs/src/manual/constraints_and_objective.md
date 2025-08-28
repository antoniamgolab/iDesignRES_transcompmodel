# Optimization functions

```@meta
CurrentModule = TransComp
```

This page documents all constraint and objective functions that form the mathematical core of the transport component model.

## Overview

The optimization functions are organized into several categories:

- **Model Definition**: Functions for creating the optimization model and defining decision variables
- **Constraints**: Mathematical constraints that ensure feasible and realistic solutions, covering demand coverage, vehicle sizing, infrastructure limitations, and policy restrictions
- **Objective Function**: The cost minimization function that drives the optimization
- **Workflow Runners**: High-level functions that combine constraints and objectives for specific modeling scenarios

Each constraint function adds specific mathematical relationships to the optimization model, allowing users to build models of varying complexity depending on their analysis needs. The workflow runners provide pre-configured combinations of constraints for common use cases, from simple demand coverage to complex multi-modal infrastructure planning.

## Model definition
```@docs
create_model
base_define_variables
```

## Constraints
```@docs
constraint_demand_coverage
constraint_vehicle_sizing
constraint_vehicle_aging
constraint_monetary_budget
constraint_fueling_infrastructure
constraint_supply_infrastructure
constraint_mode_infrastructure
constraint_fueling_demand
constraint_vehicle_stock_shift
constraint_mode_shift
constraint_mode_share
constraint_max_mode_share
constraint_min_mode_share
constraint_market_share
constraint_emissions_by_mode
```

## Objective
```@docs
objective
```

## Workflow Runners
```@docs
run_minimum_viable_case
run_vehicle_stock_sizing
run_vehicle_stock_aging
run_constrained_technology_shift
run_fueling_infrastructure_sizing
run_constrained_mode_shift
run_mode_infrastructure_sizing
```
