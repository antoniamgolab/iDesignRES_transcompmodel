# Input data

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

In this sample file, the optimization is performed for the years 2020 until 2050 with 31 time steps in total. If a stock of vehicles is explicitly considered, `pre_y` indicates the earliest generation of vehicles considered. In this case, the oldest vehicles that are considered have been introduced to the vehicle stock in 1996 as this was chosen as the maximum lifetime here. 

For further explenation of variables `alpha_f`, `beta_f`,`alpha_h`, `beta_h` and `gamma`, please refer to the mathematical formulation of the model.

Other entries of the input file must include data inputs for the following data structures:

* GeographicElement
* Mode
* Product
* Path
* Fuel
* Technology
* Vehicletype
* TechVehicle
* InitialVehicleStock
* InitialFuelingInfr
* InitialModeInfr
* FinancialStatus 
* Regiontype
* Odpair
* Speed
  
Specifations for this are in `manual/types.md`.

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


