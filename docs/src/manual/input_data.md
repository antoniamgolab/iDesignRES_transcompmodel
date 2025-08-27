# Input data
@anchor(input_data)

The input file is defined as one [YAML](https://yaml.org/).

```yaml
Model:
  y_init: 2020          # first year of model horizon
  Y: 31                 # number of modeled years
  pre_y: 25             # number of years before y_init to be considered for generation of the vehicle stock
  gamma: 0.001          # factor for sizing infrastructure (ratio between total yearly demand and peak demand)
  alpha_f: 0.1          # parameter for constraining rate of mode shift (optional) | default: 0.1
  beta_f: 0.1           # parameter for constraining rate of mode shift (optional) | default: 0.1
  alpha_h: 0.1          # parameter for constraining rate of technology shift (optional) | default: 0.1
  beta_h: 0.1           # parameter for constraining rate of technology shift (optional) | default: 0.1
```
For each key in this file, there is a __list of input elements__ for this specific attribute which correspond to defined data structures in the model. 

In this sample file, the optimization is performed for the years 2020 until 2050 with 31 time steps in total. If a stock of vehicles is explicitly considered, `pre_y` indicates the earliest generation of vehicles considered. In this case, the oldest vehicles that are considered have been introduced to the vehicle stock in 1996 as this was chosen as the maximum lifetime here. 

For further explanation of variables `alpha_f`, `beta_f`,`alpha_h`, `beta_h` and `gamma`, please refer to the mathematical formulation of the model.

Other entries of the input file must include data inputs for the following data structures as keys in the input file:

* `GeographicElement`: This includes nodes and connections between the nodes. For connections, it is important to define the fields `from`, `to` and `length`. `carbon_price` is a list of the length `Y` defining the location-dependent carbon price. 
* `Mode` defines the set of mode types - this may be, for example, road, public transport, bike, or, a more specific, train. 
* `Product` is the set of different product types that is considered, for which different types of vehicles are needed. This can include different types of freight goods, passengers etc. 
* `Path`: Paths are sequences or geographic elements in the considered case study. A key parameter for this is their length.
* `Fuel`: This introduces all considered fuel types with corresponding emission factor, energy specific costs, costs investments and O&M costs for fueling infrastructure. The word *fuel* is used here to specify the energy source that powers the vehicles, and, therefore, also includes electricity. 
* `Technology` is the drive-train technology, for which a fuel is defined.
* `Vehicletype` may include f.e. *midi-truck*, *passenger SUV*. Here, the mode for which the vehicle is used must be specified, as weel as, the product that is used for. 
* `TechVehicle` defines a set of combinations of vehicle types and drive-train technologies. Here, all the costs parameters related to this are defined along with technical specifics on the lifetime, load factor, annual range, tank capacity, maximum fueling power and fueling time are specified for each generation.
* `InitialVehicleStock` is a list defining the existing vehicle stock at the beginning of the optimization horizon along with their current age. The oldest vehicles considered must have the maximum age of *pre_y*.
* `InitialFuelingInfr` defines fueling capacities of the exisiting infrastructure per fuel.
* `InitialModeInfr` defines the same for mode infrastructure.
* `FinancialStatus`: To consider groups of different income levels, we define here the monetary budget of transport service consumers and their specific value of time (*VoT*).
* `Regiontype` is for defining differently build environments within the considered regions, f.e. urban, rural, suburban. This is for introducing region-type-specific parameters such as costs (f.e. related to parking fees) and different travel speed.
* `Odpair`: This defines all origin-destination pairs with corresponding trips number which defines the travel demand. Within this, the origin and destination of these trips are defined among with a list of different possible paths that can be travel between the origin and destination. Further, it must include the product that is transported, the consumer group by financial status, the region type and travel time budget.

Specifications for this are in [`Types and functions`](@ref(types_and_functions)). Each value must be defined in each item of a list for a key.

For each of these data types, a list with is added - as in the upcoming 
```yaml
Mode:
- id: 1
  name: road-car
  quantify_by_vehs: true
- id: 2
  name: public_transport
  quantify_by_vehs: false
```
Here, two travel modes are specified. The first one is modeled based on its vehicle stock.
See the example for further an example on this. 

