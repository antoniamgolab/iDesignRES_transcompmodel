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
### A.1.
Demand coverage in regions
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

__05.08.2024__
Goals for today:
    - adapt A.1 a bit -- check 
    - A.2 design    --check
    - A.2 implementation    --check
    - B design and implementation -- checke

### A.2. Demand coverage in time
The same as case A.1 but with the time constant, two years are observed: Y=2


### B. Vehicle stock sizing and aging 
Adding vehicle stock sizing
    - years are extended to Y = 10
    - generation index
    - adding aging constraint
    - adding dying constraint
    - TODO here: for testing the functionality of the code: make multiple different lifetime tests 

__06.08.2024__
    - C.1 (technology substitution) design -- check
    - C.1 implementation -- check
    - C.2 design and implementation

### C.1 Technology shift - vehicle costs
Needed adaptions:
    - no new indices
    - but attribute adaptions for cost structure
    - differences in fuel costs and vehicle costs

### C.2 Technology shift - technology costs
    constant vehicle costs, varying technology costs 

__later this week__
    - GOAL: finish all implementation and cases 
    - restructure to a nice layout
    - figure out efficient input and output writing
    - design "Small Basque" country case study (considered modes and vehicle types)
    - have a concrete plan for the data retrievel for the Basque country
    - embed this into a python workflow
    - create basic visualizations 

### C.3 Mode shift
Required changes:
    - add index m (mode) - to decision variables
    - where in the structs: just vehicle types
    - create a case study with multiple modes
    - make two modes each 2 possible vehicles 

__08.08.2024__
    - c.3 design -- check
    - c.3 implementation --check 

### C.4 Gradual shift constraint: technology
Required adaptions:
    - adding the constraint
    - testing it on a long horizon 
    - add inits! 
__09.08.2024__
    - c.4 design
    - c.4 implementation+
### C.5 Gradual shift constraint: mode 

__10.08.2024__
    - c4 implementation -- check
    - c5 design -- check 
    - c5 implementation
    
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