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

## 31.07.2024
### A.1. Demand coverage in regions
_Description_: O-D pairs, nodes, product types, modes, vehicle types, drive-train technologies,; dimensions are times two each.
_Sets_: O-D pairs, nodes, modes, vehicle types, drive-train technology, product types
_Extended description_
    - The geographic extent of the study are two regions
    - There is just transport activity happening isolated within these regions - no between the two regions
    - Two product types are being transported
    - Two vehicle types a two drive-train technologies are considered 
    
    i.e.: The two product types to be distributed within a regions. The two vehicle types are diesel-fueled and battery-electric. 
    nodes N = {1, 2}
    product types P = {1, 2}
    routes R^p = {1, 2} forall p
    vehicle types V^p = {1, 2} : forall p
    with two drivetrain technologies each: T^v = {1, 2} : forall p
    contraints: 2 + 3 + 4;  
    decision variables: f, h
    parameters: L_nk, L_e, W, L^a, F
    terms in objective function: costs for vehicle stock and costs of fuel

    initial state: all fossil with vehicle of type 1 

__01.08.2024__
_How to most efficiently parametrize the model in Julia?_
Excel sheet -> YAML -> Julia -> parametrization.  
How is it done in other projects?
EnergyModelX: uses the abstract types and then ..
I will use structs to define the basic sets that are considered and then create subsets based on this
__02.08.2024__
Parameters are set up ... what now? 
creating test_run.jl
now creating some parametrization.




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