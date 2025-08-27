# Optimization functions

```@meta
CurrentModule = TransComp
```

This page documents all constraint and objective functions in the transport component model.

## Constraints
```@docs
TransComp.base_define_variables
TransComp.constraint_demand_coverage
TransComp.constraint_vehicle_sizing
TransComp.constraint_vehicle_aging
TransComp.constraint_monetary_budget
TransComp.constraint_fueling_infrastructure
TransComp.constraint_supply_infrastructure
TransComp.constraint_mode_infrastructure
TransComp.constraint_fueling_demand
TransComp.constraint_vehicle_stock_shift
TransComp.constraint_mode_shift
TransComp.constraint_mode_share
TransComp.constraint_max_mode_share
TransComp.constraint_min_mode_share
TransComp.constraint_market_share
TransComp.constraint_emissions_by_mode
```

## Objective
```@docs
TransComp.objective
```

## Workflow Runners
```@docs
TransComp.run_minimum_viable_case
TransComp.run_vehicle_stock_sizing
TransComp.run_vehicle_stock_aging
TransComp.run_constrained_technology_shift
TransComp.run_fueling_infrastructure_sizing
TransComp.run_constrained_mode_shift
TransComp.run_mode_infrastructure_sizing
```
