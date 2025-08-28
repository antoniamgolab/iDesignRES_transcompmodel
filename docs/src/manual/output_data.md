# Output data

The format of the output is also in [YAML](https://yaml.org/). 
For each of the decision variables of the model, a separate output file is generated.
In each file, the keys are the tuple holding the indices of the value.

The output data is:

* `f`: number of trips covered by the following technology and vehicle type of the generation *(year, (product id, odpair id, path id), mode id, vehicle technology id, generation))* 
* `h`: number of vehicles used to cover the trips for an origin-destination pair *(year, odpair id , vehicle technology id, generation)*
* `h_plus`: number of vehicles purchased *(year, odpair id , vehicle technology id, generation)*
* `h_minus`: number of vehicles exiting the vehicle stock *(year, odpair id , vehicle technology id, generation)*
* `h_exist`: number of vehicles at the start of the year before the `h_minus` is subtracted and `h_plus` is added 
* `s`: amount of energy fueled (kWh) indexed by *(year, (product id, odpair id, path id, generation)*
* `q_fuel_infr_plus`: added infrastructure (kW) to the initial fueling capacities by *(year, fuel id, geographic element id)*
* `q_mode_infr_plus`: added infrastructure (pkm/h or Tkm/h) to the initial mode infrastructure capacities by *(year, mode id, geographic element id)*
* `budget_penalty_plus` and `budget_penalty_minus`: reflects on how much (euro) the budgets of the different consumer groups were exceeded (`.._plus`) or undercut (`.._minus`)
