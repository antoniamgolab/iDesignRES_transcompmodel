# How to use?
@anchor how_to_use

In the following, we describe the purposeful usage of the model.

## Preliminary knowledge for usage
Given the complex nature of transport systems that is highly variable in different spatial environments and geography, the user should have some experience with the formulation and application of optimization models. In preparation to the application, we urge to familiarize yourself with the content of the `Model design` chapter. A mathematical formulation of the model can be found in the repository in `mathematical_formulation-equations/math_formulation.pdf`.

## Design of a case study
In designing and quantifying a case study for the transport component model, the following questions need to be addressed:
* What region is modeled and at which geographic resolution? The model has been previously applied at NUTS-2 and NUTS-3 level (more information on NUTS classification [here](https://ec.europa.eu/eurostat/de/web/nuts)).
* What temporal horizon is modelled? The suggested modeling horizon is at least five years to find implications for modal and technological shift.
* Which transport modes, drivetrain technologies and fuels are part of the analysis? 
* How granular are the modes modeled? Based on vehicle stock investments or using levelized costs representing the total costs of a mode? This decision depends on the desired granularity of the analysis as well as available data.

## Preparing input data

The input data is in [YAML](https://yaml.org/) format. The minimal required input data and its format is defined in `Input data`.
This is read using `get_input_data` and the data is checked and parsed using `parse_data`. 

## Model application

The case study complexity may vary depending on which constraints are applied to the model.

### Minimum viable case - Demand coverage

*Applied functions:*
* `create_model`
* `constraint_demand_coverage` 
* `objective`

__Output:__ Cost-optimal coverage of travel demand by year, odpair, mode, vehicle technology, generation and paths.

### Vehicle stock sizing

*Applied functions:*
* `create_model`
* `constraint_demand_coverage` 
* `constraint_vehicle_sizing`
* `objective`

__Output:__ Cost-optimal coverage of travel demand with sizing of required vehicle stock.

### Vehicle stock aging

*Applied functions:*
* `create_model`
* `constraint_demand_coverage` 
* `constraint_vehicle_sizing`
* `constraint_vehicle_aging`
* `objective`

__Output:__ Cost-optimal coverage of travel demand with sizing of required vehicle stock under the consideration of the age structure of the vehicles

### Constrained technology shift

*Applied functions:*
* `create_model`
* `constraint_demand_coverage` 
* `constraint_vehicle_sizing`
* `constraint_vehicle_aging`
* `constraint_vehicle_stock_shift`
* `objective`

__Output:__ Cost-optimal coverage of travel demand with sizing of required vehicle stock under the consideration of the age structure of the vehicles and limitations on the speed of vehicle stock shift


### Fueling infrastructure sizing

*Applied functions:*
* `create_model`
* `constraint_demand_coverage` 
* `constraint_vehicle_sizing`
* `constraint_fueling_demand`
* `objective`

__Output:__ Cost-optimal coverage of travel demand with sizing of required vehicle stock and expansion of fueling infrastructure


### Constrained mode shift

*Applied functions:*
* `create_model`
* `constraint_demand_coverage` 
* `constraint_vehicle_sizing`
* `constraint_mode_shift`
* `objective`

__Output:__ Cost-optimal coverage of travel demand with sizing of required vehicle stock and constrained mode shift

### Mode infrastructure sizing 

*Applied functions:*
* `create_model`
* `constraint_demand_coverage` 
* `constraint_mode_shift`
* `objective`

__Output:__ Cost-optimal coverage of travel demand under limitation of speed of shift


Save your results with `save_results`. 

