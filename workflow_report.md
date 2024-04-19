# Workflow Report
Author: Antonia Golab
Date: 2024-04-18

## 18.04.2024 + 19.04.2024

- Setup of new file structure
    - TransportSecModel.jl
    - constraints_demand_coverage.jl
    - constraints_vehicle_stock_sizing.jl
    - constraints_mode_techn_shift.jl
    - constraints_mode_infra_sizing.jl
    - constraints_fueling_infr.jl
    - constraints_fuelsupply.jl
    - optimization_sets.jl
    - optimization_variables.jl
    - data_functions.jl
    - data_structures.jl
Used for refence: 
- Definition of stylized case studies for testing and validation of the model
- [GENeSYS-MOD](https://github.com/GENeSYS-MOD/GENeSYS_MOD.jl/tree/main)
- [Syntef EnergyModelsBase](https://github.com/EnergyModelsX/EnergyModelsBase.jl/tree/main)
- [OpenEntrance Nomenclature](https://github.com/openENTRANCE/openentrance/tree/main/definitions/variable)
- Outline of structure of input file (Excel-Sheet for now) which contains
    - information on whichb underlying information(explenation) of the indices used for the sets
    - which sets are to be created with all keys/indices that are used throughout the parameter definition
    - parameter values with keys
    - ! settings for model run - information on which modules are used of the model 
- <mark>TODO: check-functions for data reading to make sure that all data is available for the solution, also certain modules need to be activated, depending on what others are activated</mark>

## Stylized case studies

### A.1. Demand coverage in regions
Description: routes, nodes, vehicle types (+diff in drivetraintechnology), modes, product types; dimensions are 2x2x2x2x2 each.
Sets: route, nodes, modes, vehicle types, product types
Extended description:  


## Workflow Overview

[Describe the overall workflow and its purpose.]

## Steps

1. [Describe the first step of the workflow.]

2. [Describe the second step of the workflow.]

3. [Describe the third step of the workflow.]

## Results

[Summarize the results obtained from the workflow.]

## Conclusion

[Provide a conclusion and any final thoughts.]

## Next Steps

[Outline the next steps or future work related to the workflow.]

## References

[Include any references or citations used in the workflow report.]