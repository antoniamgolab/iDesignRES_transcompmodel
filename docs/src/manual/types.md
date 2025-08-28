# Model Types

```@meta
CurrentModule = TransComp
```

This page documents all custom types used in the transport component model. These types define the data structures that represent various components of the transportation system, including geographic elements, transport modes, vehicles, fuels, and infrastructure.

The types are organized into several categories:
- **Geographic Elements**: representing nodes or edges or regions
- **Transport Components**: Modes, vehicles, technologies, and fuels 
- **Infrastructure**: Fueling stations, mode infrastructure, and supply systems
- **Economic & Policy**: Financial parameters, market shares, and constraints
- **Operational**: Speed definitions, emission limits, and subsidies

Each type includes specific fields that capture the essential properties needed for transportation modeling and optimization.

```@docs
GeographicElement
Mode
Product
Path
Fuel
Technology
Vehicletype
TechVehicle
SupplyType
InitialVehicleStock
InitialFuelingInfr
InitialModeInfr
InitialSupplyInfr
InitDetourTime
DetourTimeReduction
FinancialStatus
Regiontype
Odpair
Speed
MarketShares
ModeShares
ModeSharemaxbyyear
ModeShareminbyyear
EmissionLimitbymode
EmissionLimitbyyear
VehicleSubsidy
```
