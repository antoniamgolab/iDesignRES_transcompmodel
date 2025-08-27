# Basque Country
```@id basque-case

## Case study description
* The case study encompasses the federal state *Basque Community* in Spain. This consists of three subregions which is the spatial extent of the case study, considering the trips within the regions and between the three regions. The temporal horizon is 2020-2050 with considering vehicles bought since 1995. 
* Five income levels are considered among with also commercial trips. These are called *First quintile*, *Second quintile*, *Third quintile*, *Fourth quintile*, *Fifth quintile* and *Commercial* in the input data which are defined under `FinancialStatus` and for all corresponding trips in `Odpairs`. The *First quintile* is the consumer group with lowest available budget, while the *Fifth quintile* the one with the highest.
* Also purposes 
* Considered modes are *road* and *public transport*.
* Vehicle types: small passenger cars, medium passenger cars, SUVs and busses.
* considered technologies are internal comubustion engine (ICE) and battery-electric (BE)
* Fuels: diesel and electricity
* For the trip data, a data set is used which contains origin-destination trip data classified by mode and purpose. For the case study, the classification by purpose is introduced by considering different average path lengths. 

## Description of the input data
The input file for this case studdy can be found unter `examples\Basque country\data\basque_country_input.yaml`. The data input is ordered alphabetically after the key name. 
* `GeographicElement` describes all geographic features of the case study, together with the local carbon pricing development which is assumed here to be constant 60 euros/tCO2. The naming of the geographic features follows the [NUTS-3 classification for the European Union](https://ec.europa.eu/eurostat/web/nuts).
* `Mode`, `Technology`, `Vehicletype`, `Fuel` and `TechVehicle` desribe the portfolio for the supply of transport services. The technical developments of the drive-train technologies are included in the key `TechVehicle`, where technical aspects are given for the all generations of vehicles (__Important:__ *A generation is the year in which the vehicle type of a certain technology is released on the market.*). As maintenance costs increase depending on the vehicle's age. Therefore, the parameters related to this are two-dimensional lists and defined for `Generation` $\times$ `Lifetime`. 
* `Odpair`, `Regiontype`,  `FinancialStatus`, `Product` and `Path` encompass all information of the demand side. `Odpair` displays trip magnitudes to be covered, while `Path` the geographic allocation of possible travel paths between origin and destination. The consumer resources and consumer-specific characteristics which are not trip-related are in `FinancialStatus`. Next to the monetary budget and the definition of the purchase horizon which relates to the frequency of the purchase of a new vehicle, the Value of Time (*VoT*) is an important parameter. It assigns a monetary value to the time spend on travel. 
* `InitialVehicleStock`, `InitialFuelingInfr` and `InitialModeInfr` comprise the information of the initial values on infrastructure capacities and vehicle stock for the case study.

## Data sources
Data sources used for transport modes, and cost and performance parameters:
* VoT values are deduced from the publication [1].
* ETISplus [2]: Within the project ETISplus, origin-destination data was calibrated at NUTS-3 resolution for all modes and both, passenger and freight transport. The data specifies also trip pruposes.
* Grube et al., 2021 [3]: The authors provide a cost comparison between different kinds of vehicle types of passenger cars and drivetrain technologies.

References:
[1] Tattini, J., Ramea, K., Gargiulo, M., Yang, C., Mulholland, E., Yeh, S., & Karlsson, K. (2018). Improving the representation of modal choice into bottom-up optimization energy system models – The MoCho-TIMES model. Applied Energy, 212, 265–282. [https://doi.org/10.1016/j.apenergy.2017.12.050](https://doi.org/10.1016/j.apenergy.2017.12.050)

[2] Szimba, E., Kraft, M., Ihrig, J., Schimke, A., Schnell, O., Kawabata, Y., Newton, S., Breemersch, T., Versteegh, R., Meijeren, J., Jin-Xue, H., de Stasio, C., & Fermi, F. (2012). ETISplus Database Content and Methodology. [https://doi.org/10.13140/RG.2.2.16768.25605](https://doi.org/10.13140/RG.2.2.16768.25605)

[3] Grube, T., Kraus, S., Reul, J., & Stolten, D. (2021). Passenger car cost development through 2050. Transportation Research Part D: Transport and Environment, 101, 103110. [https://doi.org/10.1016/j.trd.2021.103110](https://doi.org/10.1016/j.trd.2021.103110)

## Output data
